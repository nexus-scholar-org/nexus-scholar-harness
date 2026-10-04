"""Runtime producer for the accepted Contract v1 ``document_manifest``.

Why this module exists
----------------------
The pipeline writes ``extracted/<stem>.md`` (Stage 5) and indexes *accepted*
documents (Stage 6), but nothing ever published the manifest in between. Stage 6
inherits both of its identity limbs from an accepted ``document_manifest``, so with
no manifest it refused every document and reported ``FAILED`` for a workspace whose
extraction had actually succeeded. This module is the missing runtime link::

    Stage 5 output -> candidate -> frozen acceptance gate -> accepted manifest ->
    Stage 6

What it is allowed to do
------------------------
It *reads* real workspace state, *builds* one Contract v1
``document_manifest`` candidate from it, and hands that candidate to the frozen
:func:`scholar_harness.extraction_adapter.accept_extraction_candidate`. Every
registry mutation, ``artifacts/<type>/<id>.json`` publication, idempotency
decision, rejection record, and acceptance audit event belongs to the frozen gate;
this module adds no second write path. Its only own write is a harness-side
provenance record (:func:`_write_publication_record`) and one audit event, both
after acceptance.

The trust boundary (A5)
-----------------------
Every limb of the :class:`~scholar_harness.contracts.acceptance.AcceptanceContext`
is derived from **recorded workspace state**, never from the candidate:

* ``workspace_id`` -- the ``registered_workspace_id`` recorded in ``project.json``
  at inception, validated with the frozen identifier registry. A workspace with no
  recorded identity is refused: this module never mints one and never substitutes
  the project slug, because a workspace is not a study and a slug is a label.
* ``protocol_fingerprint`` -- recomputed from the workspace's own ``protocol.json``
  with the same canonical call ``scholar_harness.screening.batcher`` uses, then
  cross-checked against the accepted corpus snapshot's own fingerprint.
* ``corpus_fingerprint`` -- recomputed with the **frozen**
  ``corpus_snapshot_fingerprint(...)`` over a ``CorpusSnapshotData`` validated from
  the *accepted* ``corpus_snapshot`` payload, whose frozen validator independently
  asserts the recorded fingerprint matches its own identity graph.

A candidate carrying a different workspace/protocol/corpus fingerprint is refused by
the gate (``*_MISMATCH``), which is why no fingerprint is read back out of a
candidate. The fingerprints *are* copied into the candidate this module builds --
from the trusted context, never from a caller.

Identity rules honoured here
----------------------------
* a path is a location, not identity: ``extracted/<stem>.md`` is resolved with the
  orchestrator's own :func:`_extraction_file_stem` rule (the single rule Stage 5
  wrote with) and is then cross-checked against the file's own recorded
  frontmatter, so a mis-named file is refused rather than published;
* ``document_id`` is the canonical PDF-kit identity
  (:func:`scholar_pdf.canonical.deterministic_document_id`) over
  ``(workspace_id, study_id, source_hash)`` -- never a filename, title, or DOI;
* ``study_id`` resolves against the **accepted corpus snapshot** by study id,
  registered alias, or recorded DOI, and must carry an accepted ``INCLUDE``
  decision in an accepted ``screening_decisions`` artifact;
* ``source_hash`` is the SHA-256 of the exact source bytes the record describes: the
  workspace's own PDF when one exists, otherwise the canonical JSON of the source
  record a metadata-only extraction was derived from. Which rule applied is recorded
  in the publication record, never left to a reader's guess;
* ``VALID`` is claimed only for a body the PDF kit's own
  :func:`measure_extracted_body` / :func:`is_legacy_stub` rules call usable. A stub,
  frontmatter-only, or below-threshold body is refused, because the frozen
  ``DocumentRecord`` has no field in which to explain a ``PARTIAL`` record.

Determinism
-----------
``artifact_id``, ``created_at``, and ``producer`` are derived from recorded state
rather than wall-clock time, so an exact replay reproduces a byte-identical payload
and the gate recognises it as idempotent instead of reporting
``IDEMPOTENCY_CONFLICT``. An already-registered payload keeps its own recorded
``producer``, so replaying after a harness commit is still byte-identical.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from scholar_pdf.canonical import deterministic_document_id
from scholar_pdf.extraction_models import extraction_method_for_engine
from scholar_pdf.frontmatter import (
    FrontmatterError,
    is_legacy_stub,
    measure_extracted_body,
    parse_bound_frontmatter,
    sha256_bytes,
)
from scholar_protocol.canonical import canonical_fingerprint as protocol_fingerprint
from scholar_protocol.models import ResearchProtocol

from scholar_harness.console.api.audit import log_event
from scholar_harness.contracts.acceptance import (
    AcceptanceContext,
    ArtifactRegistry,
    RegistryEntry,
)
from scholar_harness.contracts.canonical import (
    canonical_json_bytes,
    corpus_snapshot_fingerprint,
    deterministic_id,
)
from scholar_harness.contracts.identifiers import IdentifierKind
from scholar_harness.contracts.models import (
    ArtifactReference,
    CorpusSnapshotArtifact,
    DocumentManifestArtifact,
    OperationStatus,
    ScreeningDecisionsArtifact,
)
from scholar_harness.extraction_adapter import accept_extraction_candidate
from scholar_harness.inception.genesis import (
    RegisteredWorkspaceIdentityMissingError,
    validate_registered_workspace_id,
)
from scholar_harness.orchestrator import _extraction_file_stem, _study_doi, _study_pdf
from scholar_harness.screening.batcher import _harness_commit

logger = logging.getLogger(__name__)

__all__ = [
    "Candidate",
    "PublicationOutcome",
    "PublicationRefused",
    "build_acceptance_context",
    "build_document_manifest_candidate",
    "index_accepted_documents",
    "publication_status",
    "publish_document_manifest",
]

_REGISTRY_RELPATH = "audit/artifact_registry.json"
_PROJECT_RELPATH = "project.json"
_PROTOCOL_RELPATH = "protocol.json"
_INCLUDED_RELPATH = "literature/included.json"
_EXTRACTED_RELPATH = "extracted"
_PDFS_RELPATH = "pdfs"
_PUBLICATION_DIR_RELPATH = "literature/extraction_publications"
_DEFAULT_CHROMA_RELPATH = "rag/chroma_db"

#: A body must reach this many whitespace-collapsed characters before a record may
#: claim ``VALID``. This is the same usefulness threshold the PDF kit applies to a
#: committed extraction, and below it the frozen ``DocumentRecord`` has no way to
#: express "we got a file but not its text".
_USABLE_BODY_CHARACTERS = 200

#: The harness-side publication record is NOT the PDF kit's
#: ``pdf-extraction-manifest-v1`` sidecar and must never be presented as one: that
#: sidecar is kit-owned (``SIDECAR_STORAGE_PREFIX = literature/extraction``) and its
#: schema is the kit's. This record carries the per-document provenance the frozen
#: ``DocumentRecord`` has no field for (engine, source kind, body checksum) so the
#: accepted manifest can be audited without a contract change.
_PUBLICATION_RECORD_TYPE = "harness_document_manifest_publication"
_PUBLICATION_RECORD_VERSION = "1.0.0"

_PRODUCER_PACKAGE = "nexus-scholar-harness"
_PRODUCER_VERSION = "1.0.0"
_ACTOR = "scholar-harness-extraction-producer"

_ACCEPTANCE_REFUSED = "ACCEPTANCE_REFUSED"

#: A registered accepted artifact that cannot be read at all is treated as an absence
#: while scanning for a screening parent. Every other refusal code -- notably the
#: containment codes -- is re-raised, because a registry whose recorded location is not
#: inside the workspace is a compromised registry, not a missing file.
_UNUSABLE_PAYLOAD_CODES = frozenset(
    {"ACCEPTED_ARTIFACT_UNREADABLE", "ACCEPTED_ARTIFACT_INVALID"}
)


class _SkipLog:
    """Registry entries this producer declined to use, and why.

    A skip is always fail-closed -- no skip can let a manifest publish without a
    genuinely accepted parent -- but silence is not honesty. An operator reading the
    ledger must be able to see that a *registered* artifact was passed over and how
    far it got, otherwise a corrupt entry from another generation looks like an
    entry that never existed.
    """

    __slots__ = ("_entries",)

    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def note(self, artifact_id: str, reason: str) -> None:
        """Record the first reason an artifact was skipped (idempotent by id)."""

        self._entries.setdefault(artifact_id, reason)

    def merge(self, other: _SkipLog) -> None:
        for artifact_id, reason in other._entries.items():
            self.note(artifact_id, reason)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def as_dict(self) -> dict[str, str]:
        return {artifact_id: self._entries[artifact_id] for artifact_id in self.ids}

    def __bool__(self) -> bool:
        return bool(self._entries)


class PublicationRefused(RuntimeError):
    """A typed, actionable refusal to publish a document manifest.

    Every refusal names what could not be derived from real workspace state and
    what the operator must do about it. ``code`` is stable and machine-readable so a
    caller can branch on the failure; ``message`` is the human half.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


@dataclass(frozen=True)
class Candidate:
    """One real ``document_manifest`` candidate and the state it was derived from.

    ``payload`` is what the frozen gate sees. ``documents`` is the harness-side
    provenance the frozen ``DocumentRecord`` cannot carry. ``parents`` is the
    accepted ``screening_decisions`` input set, with the hashes the registry
    recorded for each -- the manifest's only scientific lineage.

    ``context`` is the *trusted* ``AcceptanceContext`` -- derived from recorded
    workspace state alone -- and it is carried here so the caller has exactly one
    source for the expected limbs. It must never be reconstructed from ``payload``:
    the gate model-validates the very payload it is handed, so an ``expected`` read
    back out of it would agree with itself and no mismatch branch could ever fire.
    ``skipped_registry_entries`` discloses every registered artifact the derivation
    passed over, with the reason.
    """

    payload: dict[str, Any]
    context: AcceptanceContext
    documents: list[dict[str, Any]]
    parents: list[dict[str, str]]
    corpus_artifact_id: str
    screening_run_id: str
    skipped_registry_entries: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicationOutcome:
    """The real outcome of one publication attempt, never an assumed success."""

    status: str
    accepted: bool
    artifact_id: str | None = None
    published_path: str | None = None
    rejection_path: str | None = None
    idempotent: bool = False
    documents: int = 0
    parent_artifact_ids: tuple[str, ...] = ()
    record_path: str | None = None
    issues: tuple[dict[str, Any], ...] = ()
    refusal: dict[str, Any] | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    #: Registered artifacts this derivation passed over, and why. Disclosed on the
    #: outcome -- not only in the record file -- so a caller that prints the outcome
    #: cannot report a clean run over a registry it had to skip entries in.
    skipped_registry_entries: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "accepted": self.accepted,
            "artifact_id": self.artifact_id,
            "published_path": self.published_path,
            "rejection_path": self.rejection_path,
            "idempotent": self.idempotent,
            "documents": self.documents,
            "parent_artifact_ids": list(self.parent_artifact_ids),
            "record_path": self.record_path,
            "issues": list(self.issues),
            "refusal": self.refusal,
            "provenance": self.provenance,
            "skipped_registry_entries": self.skipped_registry_entries,
        }


# ---------------------------------------------------------------------------
# Workspace-state readers (read-only, typed, fail-closed)
# ---------------------------------------------------------------------------


def _resolve_inside(workspace: Path, relative: str) -> Path:
    """Resolve *relative* inside *workspace*, or refuse.

    Both the portable-path rule (the frozen ``ArtifactReference`` validator) and a
    resolved-path containment check are applied, so ``..``, an absolute path, a drive
    letter, and a symlinked escape are all refused before any read or write.
    """

    try:
        ArtifactReference.portable_workspace_path(relative)
    except ValueError as exc:
        raise PublicationRefused(
            "PATH_NOT_WORKSPACE_RELATIVE",
            f"{relative!r} is not a portable workspace-relative POSIX path ({exc}).",
            path=relative,
        ) from exc
    try:
        resolved = (workspace / PurePosixPath(relative)).resolve()
        resolved.relative_to(workspace)
    except (OSError, ValueError) as exc:
        raise PublicationRefused(
            "PATH_ESCAPES_WORKSPACE",
            f"{relative!r} resolves outside the workspace root ({exc}).",
            path=relative,
        ) from exc
    return resolved


def _relative(workspace: Path, path: Path) -> str:
    """Return *path* as a workspace-relative POSIX string (for messages and events)."""

    try:
        return Path(path).resolve().relative_to(workspace).as_posix()
    except (OSError, ValueError):  # pragma: no cover - defensive only
        return str(path)


def _load_registry(workspace: Path) -> ArtifactRegistry:
    """Read the Contract v1 registry through the frozen model.

    An absent or unparseable registry is an *absence*, never a licence to infer: both
    are refusals, which is the fail-closed direction.
    """

    path = _resolve_inside(workspace, _REGISTRY_RELPATH)
    if not path.is_file():
        raise PublicationRefused(
            "ARTIFACT_REGISTRY_MISSING",
            f"No accepted Contract v1 artifact registry at {_REGISTRY_RELPATH}. Run "
            "the screening handoff first (`python src/scholar_harness/agent_screen.py "
            "prepare <workspace>`, then `collect`) so a corpus snapshot and its "
            "screening decisions are accepted before a document manifest can be "
            "published.",
            registry_path=_REGISTRY_RELPATH,
        )
    try:
        return ArtifactRegistry.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise PublicationRefused(
            "ARTIFACT_REGISTRY_INVALID",
            f"{_REGISTRY_RELPATH} does not validate as a Contract v1 ArtifactRegistry "
            f"({exc}). Repair or remove it; an unusable registry is never coerced "
            "into an empty one.",
            registry_path=_REGISTRY_RELPATH,
        ) from exc


def _load_accepted_payload(
    workspace: Path, artifact_id: str, entry: RegistryEntry
) -> dict[str, Any]:
    """Load one accepted artifact payload with containment and typing.

    The registry entry is the recorded proof of what was accepted, so its path is
    validated with the frozen portable-path rule and re-checked against the resolved
    workspace root before a single byte is read.
    """

    resolved = _resolve_inside(workspace, entry.path)
    if not resolved.is_file():
        raise PublicationRefused(
            "ACCEPTED_ARTIFACT_UNREADABLE",
            f"accepted artifact {artifact_id} is registered at {entry.path!r} but no "
            "file is there. The registry and the published payload must agree.",
            artifact_id=artifact_id,
        )
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicationRefused(
            "ACCEPTED_ARTIFACT_UNREADABLE",
            f"accepted artifact {artifact_id} cannot be loaded from {entry.path!r} "
            f"({exc}).",
            artifact_id=artifact_id,
        ) from exc
    if not isinstance(payload, dict):
        raise PublicationRefused(
            "ACCEPTED_ARTIFACT_INVALID",
            f"accepted artifact {artifact_id} at {entry.path!r} is not a JSON object.",
            artifact_id=artifact_id,
        )
    return payload


def _recorded_workspace_id(workspace: Path) -> str:
    """Read the registered workspace identity recorded at inception.

    Records and re-reads only. It never mints, never falls back to the project slug,
    and never accepts a malformed value -- an unregistered workspace would make every
    published artifact unusable downstream, so it is a refusal whose message carries
    the repair.
    """

    path = workspace / _PROJECT_RELPATH
    recorded: Any = None
    project_id: Any = None
    if path.is_file():
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PublicationRefused(
                "WORKSPACE_MANIFEST_UNREADABLE",
                f"cannot read the recorded workspace identity from {path} ({exc}). "
                "Repair or re-create project.json.",
            ) from exc
        if not isinstance(manifest, dict):
            raise PublicationRefused(
                "WORKSPACE_MANIFEST_INVALID", f"{path} is not a JSON object."
            )
        recorded = manifest.get("registered_workspace_id")
        project_id = manifest.get("project_id")

    if not isinstance(recorded, str) or not recorded.strip():
        raise PublicationRefused(
            "WORKSPACE_IDENTITY_NOT_RECORDED",
            f"{path} records no 'registered_workspace_id'. A document manifest is "
            "published under the workspace identity minted at inception; the project "
            f"slug ({project_id!r}) is a label, not an identity, and this producer will "
            "not mint a replacement. Fix: re-create the workspace (nexus-scholar init "
            f'<title>) or add \'registered_workspace_id": "WSP-<32 hex>" to {path}.',
            project_id=project_id,
        )
    try:
        return validate_registered_workspace_id(recorded)
    except (TypeError, ValueError, RegisteredWorkspaceIdentityMissingError) as exc:
        raise PublicationRefused(
            "WORKSPACE_IDENTITY_NOT_REGISTERED",
            f"{path} records 'registered_workspace_id' ({recorded!r}) which is not a "
            f"registered workspace identity ({exc}). Replace it with a value of the "
            "form WSP-<32 lowercase hex>.",
        ) from exc


def _protocol_fingerprint(workspace: Path) -> str:
    """Recompute the protocol fingerprint from the workspace's own protocol."""

    path = workspace / _PROTOCOL_RELPATH
    if not path.is_file():
        raise PublicationRefused(
            "PROTOCOL_ARTIFACT_MISSING",
            f"No {_PROTOCOL_RELPATH} in the workspace. A document manifest is bound "
            "to one protocol generation; run the pipeline's inception or protocol "
            "compile step first.",
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicationRefused(
            "PROTOCOL_ARTIFACT_INVALID",
            f"{_PROTOCOL_RELPATH} cannot be read ({exc}). Repair or remove it.",
        ) from exc
    if not isinstance(raw, dict):
        raise PublicationRefused(
            "PROTOCOL_ARTIFACT_INVALID", f"{_PROTOCOL_RELPATH} is not a JSON object."
        )
    try:
        protocol = ResearchProtocol.model_validate(raw)
    except ValueError as exc:
        raise PublicationRefused(
            "PROTOCOL_ARTIFACT_INVALID",
            f"{_PROTOCOL_RELPATH} cannot be validated as a ResearchProtocol ({exc}). "
            "A manifest is never published against an unreadable protocol.",
        ) from exc
    return protocol_fingerprint(protocol)


def _accepted_corpus(
    workspace: Path, registry: ArtifactRegistry, skips: _SkipLog | None = None
) -> tuple[str, CorpusSnapshotArtifact]:
    """Return the newest accepted, valid ``corpus_snapshot`` and its artifact id.

    The payload is re-validated through the frozen ``CorpusSnapshotArtifact``, which
    itself asserts ``corpus_fingerprint == corpus_snapshot_fingerprint(data)``. The
    returned fingerprint is recomputed from that validated data rather than read out
    of the payload, so a registry whose recorded fingerprint and identity graph
    disagree is refused rather than trusted.

    A *newer* registered snapshot that fails validation is passed over in favour of an
    older valid one -- but it is recorded in *skips*, because silently falling back
    would hide a corrupt generation from the ledger.
    """

    skips = skips if skips is not None else _SkipLog()
    candidates = sorted(
        (
            (artifact_id, entry)
            for artifact_id, entry in registry.artifacts.items()
            if entry.artifact_type == "corpus_snapshot"
        ),
        key=lambda item: (item[1].accepted_at, item[0]),
    )
    if not candidates:
        raise PublicationRefused(
            "CORPUS_SNAPSHOT_NOT_ACCEPTED",
            "No accepted corpus_snapshot in the Contract v1 registry. Screening "
            "decisions and therefore every document manifest are bound to an accepted "
            "corpus identity; accept one first (run the search/deduplication stages, "
            "then the screening handoff).",
        )
    failures: list[str] = []
    for artifact_id, entry in reversed(candidates):
        try:
            artifact = CorpusSnapshotArtifact.model_validate(
                _load_accepted_payload(workspace, artifact_id, entry)
            )
        except PublicationRefused as refusal:
            failures.append(f"{artifact_id}: {refusal.message}")
            skips.note(artifact_id, refusal.code)
            continue
        except ValueError as exc:
            failures.append(f"{artifact_id}: {exc}")
            skips.note(artifact_id, "CORPUS_SNAPSHOT_INVALID")
            continue
        if artifact.artifact_id != artifact_id:
            failures.append(
                f"{artifact_id}: payload declares artifact_id {artifact.artifact_id!r}"
            )
            skips.note(artifact_id, "CORPUS_SNAPSHOT_ID_MISMATCH")
            continue
        recomputed = corpus_snapshot_fingerprint(artifact.data)
        if recomputed != artifact.corpus_fingerprint:
            failures.append(
                f"{artifact_id}: recomputed corpus fingerprint {recomputed!r} differs "
                f"from the recorded {artifact.corpus_fingerprint!r}"
            )
            skips.note(artifact_id, "CORPUS_FINGERPRINT_MISMATCH")
            continue
        return artifact_id, artifact
    raise PublicationRefused(
        "CORPUS_SNAPSHOT_UNUSABLE",
        "No accepted corpus_snapshot payload validates as a CorpusSnapshotArtifact: "
        + " | ".join(failures),
    )


@dataclass(frozen=True)
class _Generation:
    """The trusted generation: the ``AcceptanceContext`` limbs and their sources.

    The validated corpus and the registry that was read are carried along so a caller
    never has to re-read (or re-validate) them: one derivation, one answer.
    """

    context: AcceptanceContext
    corpus_artifact_id: str
    screening_run_id: str = ""
    corpus: CorpusSnapshotArtifact | None = None
    registry: ArtifactRegistry | None = None
    skips: _SkipLog = field(default_factory=_SkipLog)


def build_acceptance_context(workspace: Path) -> AcceptanceContext:
    """Build the trusted ``AcceptanceContext`` from recorded workspace state only.

    Raises :class:`PublicationRefused` when any limb cannot be derived. Nothing here
    reads a candidate payload, and nothing mints, guesses, or defaults a fingerprint
    or an identity.
    """

    generation = _build_generation(workspace)
    return generation.context


def _build_generation(workspace: Path, skips: _SkipLog | None = None) -> _Generation:
    """Derive the trusted generation, including the screening run id.

    The run id is read from an **accepted** ``screening_decisions`` binding, never
    minted: it is the run the admitted documents were screened under, which is the
    run a manifest bound to those documents belongs to.

    Registered artifacts this scan passes over are collected in *skips* rather than
    dropped, so the caller can disclose them.
    """

    workspace = Path(workspace).resolve()
    skips = skips if skips is not None else _SkipLog()
    registry = _load_registry(workspace)
    workspace_id = _recorded_workspace_id(workspace)
    protocol_fp = _protocol_fingerprint(workspace)
    corpus_artifact_id, corpus = _accepted_corpus(workspace, registry, skips)

    if corpus.workspace_id != workspace_id:
        raise PublicationRefused(
            "WORKSPACE_IDENTITY_DISAGREEMENT",
            f"The recorded workspace identity ({workspace_id}) disagrees with the "
            f"accepted corpus snapshot {corpus_artifact_id} ({corpus.workspace_id}). "
            "Every artifact in one generation must share one workspace identity; "
            "re-run the pipeline in a single workspace or re-scope the corpus.",
            recorded_workspace_id=workspace_id,
            corpus_workspace_id=corpus.workspace_id,
            corpus_artifact_id=corpus_artifact_id,
        )
    if corpus.protocol_fingerprint != protocol_fp:
        raise PublicationRefused(
            "PROTOCOL_FINGERPRINT_MISMATCH",
            f"{_PROTOCOL_RELPATH} fingerprints to {protocol_fp!r} but the accepted "
            f"corpus snapshot {corpus_artifact_id} was accepted under "
            f"{corpus.protocol_fingerprint!r}. The workspace protocol changed after "
            "the corpus was accepted; re-run search/deduplication and screening so the "
            "corpus is rebuilt for this protocol generation.",
            protocol_fingerprint=protocol_fp,
            corpus_protocol_fingerprint=corpus.protocol_fingerprint,
            corpus_artifact_id=corpus_artifact_id,
        )

    run_ids = sorted(
        {
            run_id
            for run_id in _accepted_screening_run_ids(
                workspace, registry, corpus, skips
            )
        }
    )
    if not run_ids:
        raise PublicationRefused(
            "SCREENING_GENERATION_ABSENT",
            "No accepted screening_decisions artifact matches this workspace's "
            "generation. A document manifest's only scientific parent is the accepted "
            "screening decision, so nothing can be published yet. Fix: run the "
            "agent-in-the-loop handoff (`python src/scholar_harness/agent_screen.py "
            "prepare <workspace>` -> screen the batches -> `collect <workspace>`).",
        )
    if len(run_ids) > 1:
        raise PublicationRefused(
            "SCREENING_GENERATION_INCONSISTENT",
            "The accepted screening_decisions artifacts in this workspace span more "
            f"than one screening run ({run_ids}), so no single recorded run binds this "
            "manifest. Resolve the screening history (re-run `agent_screen.py collect` "
            "for one generation) before publishing a document manifest.",
            screening_run_ids=run_ids,
        )

    return _Generation(
        context=AcceptanceContext(
            workspace_id=workspace_id,
            protocol_fingerprint=protocol_fp,
            corpus_fingerprint=corpus.corpus_fingerprint,
        ),
        corpus_artifact_id=corpus_artifact_id,
        screening_run_id=run_ids[0],
        corpus=corpus,
        registry=registry,
        skips=skips,
    )


def _generation_matches(payload: dict[str, Any], context: AcceptanceContext) -> bool:
    """True when an accepted payload belongs to *context*'s generation."""

    return (
        payload.get("workspace_id") == context.workspace_id
        and payload.get("protocol_fingerprint") == context.protocol_fingerprint
        and payload.get("corpus_fingerprint") == context.corpus_fingerprint
    )


def _accepted_screening_artifacts(
    workspace: Path,
    registry: ArtifactRegistry,
    context: AcceptanceContext,
    skips: _SkipLog | None = None,
) -> list[tuple[str, ScreeningDecisionsArtifact]]:
    """Every accepted ``screening_decisions`` in *context*'s generation, validated.

    A payload that does not validate as the frozen model, or that cannot be read, is
    skipped rather than coerced: for the purpose of finding a parent it is an absence.
    A registered *location* that is non-portable or escapes the workspace is not
    skipped, though -- a tampered registry entry is a compromised registry, and this
    producer is about to write a manifest whose parent lineage comes from that
    registry, so it refuses rather than quietly continuing past it.

    Every skip is recorded in *skips* with its reason, including a registered
    ``screening_decisions`` that belongs to a *different* generation: passing that over
    is correct, but it must not be invisible, or a second generation in the registry
    looks like a single one.
    """

    skips = skips if skips is not None else _SkipLog()
    found: list[tuple[str, ScreeningDecisionsArtifact]] = []
    for artifact_id, entry in sorted(registry.artifacts.items()):
        if entry.artifact_type != "screening_decisions":
            continue
        try:
            payload = _load_accepted_payload(workspace, artifact_id, entry)
        except PublicationRefused as refusal:
            if refusal.code not in _UNUSABLE_PAYLOAD_CODES:
                raise
            skips.note(artifact_id, refusal.code)
            continue
        if not _generation_matches(payload, context):
            skips.note(artifact_id, "OTHER_GENERATION")
            continue
        try:
            artifact = ScreeningDecisionsArtifact.model_validate(payload)
        except ValueError:
            skips.note(artifact_id, "SCREENING_DECISIONS_INVALID")
            continue
        if artifact.artifact_id != artifact_id:
            skips.note(artifact_id, "ARTIFACT_ID_MISMATCH")
            continue
        found.append((artifact_id, artifact))
    return found


def _accepted_screening_run_ids(
    workspace: Path,
    registry: ArtifactRegistry,
    corpus: CorpusSnapshotArtifact,
    skips: _SkipLog | None = None,
) -> set[str]:
    """Every screening run id recorded by an accepted, matching decision artifact."""

    context = AcceptanceContext(
        workspace_id=corpus.workspace_id,
        protocol_fingerprint=corpus.protocol_fingerprint,
        corpus_fingerprint=corpus.corpus_fingerprint,
    )
    return {
        artifact.data.binding.screening_run_id
        for _artifact_id, artifact in _accepted_screening_artifacts(
            workspace, registry, context, skips
        )
    }


# ---------------------------------------------------------------------------
# Study resolution against the accepted corpus
# ---------------------------------------------------------------------------


def _corpus_indexes(
    corpus: CorpusSnapshotArtifact,
) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]]]:
    """Build study-id / alias / DOI indexes over the accepted corpus identity graph."""

    by_study: dict[str, str] = {}
    by_alias: dict[str, str] = {}
    by_doi: dict[str, list[str]] = {}
    for study in corpus.data.studies:
        by_study[study.study_id] = study.study_id
        for alias in study.alias_ids:
            by_alias[alias] = study.study_id
        for doi in study.external_ids.get("doi", []):
            by_doi.setdefault(_normalize_doi(doi), []).append(study.study_id)
    return by_study, by_alias, by_doi


def _normalize_doi(value: Any) -> str:
    """Normalize a DOI for comparison only. Never an identity."""

    doi = str(value or "").strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "doi:",
    ):
        doi = doi.removeprefix(prefix)
    return doi.strip()


def _resolve_study_id(
    record: dict[str, Any],
    by_study: dict[str, str],
    by_alias: dict[str, str],
    by_doi: dict[str, list[str]],
) -> str:
    """Resolve one included record to an accepted corpus ``study_id``.

    Resolution order is deliberately conservative: a recorded study id, then a
    registered alias id, then a recorded DOI. A title, a filename, or a provider id is
    never used -- those are labels, and a label that resolved to a study would be an
    identity inference the contract forbids. An ambiguous DOI resolves to nothing.

    The historical ``workspace_id`` field on an included record carries the *study*
    identity (see ``scholar_harness.screening.collector``); it is read only as a
    candidate study id or alias and never as a workspace.
    """

    for key in ("study_id", "workspace_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            if value in by_study:
                return by_study[value]
            if value in by_alias:
                return by_alias[value]
    doi = _normalize_doi(_study_doi(record))
    if doi:
        matches = by_doi.get(doi, [])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise PublicationRefused(
                "STUDY_IDENTITY_AMBIGUOUS",
                f"DOI {doi!r} is recorded on more than one accepted corpus study "
                f"({sorted(matches)}), so the included record cannot be bound to one "
                "study identity. Re-run deduplication for this corpus.",
                doi=doi,
                study_ids=sorted(matches),
            )
    raise PublicationRefused(
        "STUDY_IDENTITY_UNRESOLVED",
        f"The included record {record.get('title')!r} (workspace_id="
        f"{record.get('workspace_id')!r}, doi={doi or None!r}) does not resolve to "
        "any study in the accepted corpus snapshot. Identity is resolved from the "
        "accepted corpus only; a document manifest never admits a study the accepted "
        "corpus does not contain.",
        workspace_id=record.get("workspace_id"),
        doi=doi or None,
    )


# ---------------------------------------------------------------------------
# Extracted-output reader
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_fingerprint(
    workspace: Path, record: dict[str, Any]
) -> tuple[str, str, str]:
    """Return ``(source_hash, source_kind, source_locator)`` for one record.

    The hash always describes bytes that were really read: the workspace's own PDF
    when one exists for the study, otherwise the canonical JSON of the source record a
    metadata-only extraction was derived from. The rule that applied is returned so the
    publication record states it instead of leaving a reader to guess what
    ``source_hash`` covers.
    """

    pdf = _study_pdf(_resolve_inside(workspace, _PDFS_RELPATH), record)
    if pdf is not None:
        # The hit is re-checked through the same containment rule as every other read:
        # a file inside ``pdfs/`` that is a symlink out of the workspace must not be
        # hashed, let alone cited as ``source_kind="workspace_pdf"``.
        try:
            pdf.relative_to(workspace)
        except ValueError as exc:
            raise PublicationRefused(
                "PATH_ESCAPES_WORKSPACE",
                f"{pdf} resolves outside the workspace root, so its bytes are not "
                "this workspace's evidence. The PDF for this study is reached through "
                "a link that leaves the workspace; re-harvest it inside the workspace "
                "or remove the link.",
                path=str(pdf),
            ) from exc
        return f"sha256:{_sha256_file(pdf)}", "workspace_pdf", _relative(workspace, pdf)
    return (
        f"sha256:{sha256(canonical_json_bytes(record)).hexdigest()}",
        "canonical_source_record",
        _INCLUDED_RELPATH,
    )


def _normalized_text(raw: bytes) -> tuple[str, bool]:
    """Return *raw* as text with LF line endings, and whether a change was made.

    The PDF kit's frontmatter grammar is defined over bare ``\\n`` (``_FRONTMATTER_RE``),
    while ``Path.write_text`` on Windows commits CRLF -- which is exactly how the
    frozen Stage 5 writers emit an extracted file. Normalizing here is a byte-level
    step, not a second frontmatter implementation: the kit's own parser and body
    measurer still decide what the file says. Both the raw file digest and the
    normalized-body digest are recorded, so nothing about the on-disk bytes is lost.
    """

    text = raw.decode("utf-8")
    if "\r\n" in text:
        return text.replace("\r\n", "\n"), True
    return text, False


def _read_extracted_document(
    workspace: Path,
    record: dict[str, Any],
    study_id: str,
    workspace_id: str,
    aliases: frozenset[str],
) -> dict[str, Any]:
    """Read one real extracted markdown file and bind it to *study_id*.

    Returns the frozen ``DocumentRecord`` fields plus the harness-side provenance the
    frozen record has no field for. Every refusal here is a truthfulness failure: a
    missing file, an unusable body, an unreadable frontmatter block, or a file whose
    own recorded identity names a different study.
    """

    stem = _extraction_file_stem(record)
    extracted_rel = f"{_EXTRACTED_RELPATH}/{stem}.md"
    extracted = _resolve_inside(workspace, extracted_rel)
    if not extracted.is_file():
        raise PublicationRefused(
            "EXTRACTED_OUTPUT_MISSING",
            f"No extracted markdown at {extracted_rel!r} for study {study_id!r}. A "
            "document manifest is built from real extraction output: run the "
            "pipeline's extraction stage (scholar-harness run) so the file exists, or "
            f"remove the record from {_INCLUDED_RELPATH}. A document that was never "
            "extracted is not published as VALID.",
            study_id=study_id,
            extracted_path=extracted_rel,
        )
    raw = extracted.read_bytes()
    try:
        text, normalized = _normalized_text(raw)
    except UnicodeDecodeError as exc:
        raise PublicationRefused(
            "EXTRACTED_FRONTMATTER_UNREADABLE",
            f"{extracted_rel!r} is not valid UTF-8 ({exc}), so it cannot be read as an "
            f"extraction. Nothing is published for study {study_id!r}.",
            study_id=study_id,
            extracted_path=extracted_rel,
        ) from exc
    try:
        frontmatter, body = parse_bound_frontmatter(text.encode("utf-8"))
    except FrontmatterError as exc:
        raise PublicationRefused(
            "EXTRACTED_FRONTMATTER_UNREADABLE",
            f"{extracted_rel!r} is not a committed extraction ({exc}). Stage 5 writes a "
            "YAML frontmatter block naming the record's identity; a file without one "
            f"cannot be attributed to a study, so nothing is published for "
            f"{study_id!r}.",
            study_id=study_id,
            extracted_path=extracted_rel,
            detail=str(exc),
        ) from exc

    measurement = measure_extracted_body(text)
    if is_legacy_stub(body):
        raise PublicationRefused(
            "EXTRACTED_CONTENT_IS_STUB",
            f"{extracted_rel!r} contains only the legacy 'Extracted content from ...' "
            "parse-failure stub. A stub is not extracted text, so no VALID record can "
            f"be published for study {study_id!r}. Re-extract the document's source.",
            study_id=study_id,
            extracted_path=extracted_rel,
        )
    if measurement.character_count < _USABLE_BODY_CHARACTERS:
        raise PublicationRefused(
            "EXTRACTED_CONTENT_NOT_USABLE",
            f"{extracted_rel!r} has {measurement.character_count} usable body "
            f"characters, below the {_USABLE_BODY_CHARACTERS}-character usefulness "
            "threshold the frozen PDF kit applies. The frozen DocumentRecord has no "
            "field in which a PARTIAL record could explain a degradation, so study "
            f"{study_id!r} is refused rather than published as VALID.",
            study_id=study_id,
            extracted_path=extracted_rel,
            character_count=measurement.character_count,
        )

    # The file on disk states which record it came from. Cross-checking it against
    # the resolved study is what stops one study's text being published under another
    # study's identity when a filename is reused or a stem rule changes.
    bound = str(frontmatter.get("workspace_id") or "").strip()
    if bound and bound not in {study_id, *aliases}:
        raise PublicationRefused(
            "EXTRACTED_FRONTMATTER_MISMATCH",
            f"{extracted_rel!r} records workspace_id {bound!r}, which is neither the "
            f"resolved study identity {study_id!r} nor one of its registered aliases. "
            "The file on disk does not belong to this study, so publishing it would "
            "bind one study's text to another study's identity.",
            study_id=study_id,
            extracted_path=extracted_rel,
            frontmatter_workspace_id=bound,
        )
    bound_doi = _normalize_doi(frontmatter.get("doi"))
    record_doi = _normalize_doi(_study_doi(record))
    if bound_doi and record_doi and bound_doi != record_doi:
        raise PublicationRefused(
            "EXTRACTED_FRONTMATTER_MISMATCH",
            f"{extracted_rel!r} records doi {bound_doi!r} but the included record for "
            f"study {study_id!r} records {record_doi!r}.",
            study_id=study_id,
            extracted_path=extracted_rel,
            frontmatter_doi=bound_doi,
        )

    engine = str(frontmatter.get("extraction_engine") or "").strip()
    method = extraction_method_for_engine(engine or None)
    source_hash, source_kind, source_locator = _source_fingerprint(workspace, record)
    document_id = deterministic_document_id(
        study_id=study_id,
        source_hash=source_hash,
        workspace_id=workspace_id,
    )
    return {
        "record": {
            "document_id": document_id,
            "study_id": study_id,
            "source_hash": source_hash,
            "content_status": "VALID",
            "extracted_path": extracted_rel,
            "extraction_method": str(method.value),
        },
        "provenance": {
            "study_id": study_id,
            "document_id": document_id,
            "extracted_path": extracted_rel,
            "extracted_file_sha256": sha256_bytes(raw),
            "extracted_sha256": sha256_bytes(body.encode("utf-8")),
            "line_endings_normalized": normalized,
            "extracted_character_count": measurement.character_count,
            "extraction_engine": engine or None,
            "extraction_method": str(method.value),
            "source_hash": source_hash,
            "source_kind": source_kind,
            "source_locator": source_locator,
        },
    }


# ---------------------------------------------------------------------------
# Candidate construction
# ---------------------------------------------------------------------------


def _accepted_include_parents(
    workspace: Path,
    registry: ArtifactRegistry,
    context: AcceptanceContext,
    study_ids: set[str],
    skips: _SkipLog | None = None,
) -> dict[str, str]:
    """Map each *study_id* to the accepted ``screening_decisions`` that admitted it.

    Only an accepted artifact whose payload validates as a
    ``ScreeningDecisionsArtifact`` and carries an ``INCLUDE`` decision counts. A study
    with no accepted ``INCLUDE`` is absent from the result and the caller then refuses
    it -- it is never bound to an artifact that was never accepted.
    """

    parents: dict[str, str] = {}
    for artifact_id, artifact in _accepted_screening_artifacts(
        workspace, registry, context, skips
    ):
        for decision in artifact.data.decisions:
            if decision.decision.value.upper() != "INCLUDE":
                continue
            if decision.study_id in study_ids:
                parents.setdefault(decision.study_id, artifact_id)
    missing = sorted(study_ids - set(parents))
    if missing:
        raise PublicationRefused(
            "NO_ACCEPTED_SCREENING_PARENT",
            f"No accepted screening_decisions artifact carries an INCLUDE decision for "
            f"study/studies {missing}. A document manifest's only scientific parent is "
            "the accepted screening decision; a document with no accepted INCLUDE is "
            "refused rather than published against an inferred parent.",
            study_ids=missing,
        )
    return parents


def _included_records(workspace: Path) -> list[dict[str, Any]]:
    """Read the real ``literature/included.json`` the screening handoff produced."""

    path = _resolve_inside(workspace, _INCLUDED_RELPATH)
    if not path.is_file():
        raise PublicationRefused(
            "INCLUDED_RECORDS_MISSING",
            f"No {_INCLUDED_RELPATH} in the workspace. Those records are the real "
            "output of the PRISMA handoff and are what Stage 5 extracted, so a document "
            "manifest cannot be built without them. Fix: run "
            "`python src/scholar_harness/agent_screen.py collect <workspace>`.",
        )
    try:
        raw_records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicationRefused(
            "INCLUDED_RECORDS_INVALID", f"{_INCLUDED_RELPATH} cannot be read ({exc})."
        ) from exc
    if not isinstance(raw_records, list) or not raw_records:
        raise PublicationRefused(
            "INCLUDED_RECORDS_EMPTY",
            f"{_INCLUDED_RELPATH} records no included study. A document manifest needs "
            "at least one document (the frozen DocumentManifestData requires a "
            "non-empty list), so nothing is published over an empty run.",
        )
    if not all(isinstance(item, dict) for item in raw_records):
        raise PublicationRefused(
            "INCLUDED_RECORDS_INVALID",
            f"{_INCLUDED_RELPATH} contains a non-object record.",
        )
    return raw_records


def _manifest_created_at(
    workspace: Path, registry: ArtifactRegistry, parent_ids: list[str]
) -> str:
    """Return a deterministic, UTC ``created_at`` for the manifest.

    It is the newest accepted parent creation time. Wall-clock time is deliberately
    not used: an exact replay must reproduce the same payload hash so the gate
    recognises it as idempotent instead of reporting ``IDEMPOTENCY_CONFLICT`` over a
    re-publication.
    """

    stamps: list[datetime] = []
    for artifact_id in parent_ids:
        payload = _load_accepted_payload(
            workspace, artifact_id, registry.artifacts[artifact_id]
        )
        raw = payload.get("created_at")
        if isinstance(raw, str):
            try:
                stamps.append(datetime.fromisoformat(raw))
            except ValueError:  # pragma: no cover - the frozen model parsed it
                continue
    if not stamps:  # pragma: no cover - a parent always exists here
        raise PublicationRefused(
            "PARENT_TIMESTAMP_ABSENT",
            "No accepted screening parent carries a usable created_at, so the manifest "
            "cannot state a recorded creation time.",
        )
    return max(stamps).astimezone(UTC).isoformat()


def build_document_manifest_candidate(workspace: Path) -> Candidate:
    """Build the real ``document_manifest`` candidate from recorded workspace state.

    The candidate's ``workspace_id``/fingerprints are copied from the trusted
    generation, never from anything a caller supplied. The payload is parsed through
    the frozen model *before* it can reach the gate, so a payload the contract would
    reject cannot surface as a mere acceptance-level rejection code.
    """

    workspace = Path(workspace).resolve()
    skips = _SkipLog()
    generation = _build_generation(workspace, skips)
    # One derivation, one answer: the validated corpus and the registry that produced
    # it come from the generation, never from a second scan that could disagree.
    assert generation.corpus is not None and generation.registry is not None
    corpus = generation.corpus
    registry = generation.registry

    records = _included_records(workspace)
    by_study, by_alias, by_doi = _corpus_indexes(corpus)
    resolved: list[tuple[str, dict[str, Any]]] = [
        (_resolve_study_id(record, by_study, by_alias, by_doi), record)
        for record in records
    ]

    seen: set[str] = set()
    duplicates: set[str] = set()
    for study_id, _record in resolved:
        if study_id in seen:
            duplicates.add(study_id)
        seen.add(study_id)
    if duplicates:
        raise PublicationRefused(
            "DUPLICATE_STUDY_RECORDS",
            f"{sorted(duplicates)} appear more than once in {_INCLUDED_RELPATH}. One "
            "study cannot own two documents in one manifest; re-run deduplication so "
            "each study appears once.",
            study_ids=sorted(duplicates),
        )

    aliases_by_study = {
        study.study_id: frozenset(study.alias_ids) for study in corpus.data.studies
    }
    parents = _accepted_include_parents(
        workspace, registry, generation.context, seen, skips
    )

    documents: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for study_id, record in sorted(resolved):
        read = _read_extracted_document(
            workspace,
            record,
            study_id,
            generation.context.workspace_id,
            aliases_by_study.get(study_id, frozenset()),
        )
        documents.append(read["record"])
        provenance.append(read["provenance"])
    documents.sort(key=lambda item: item["document_id"])

    parent_ids = sorted({parents[study] for study in seen})
    parent_refs = [
        {"artifact_id": artifact_id, "sha256": registry.artifacts[artifact_id].sha256}
        for artifact_id in parent_ids
    ]
    created_at = _manifest_created_at(workspace, registry, parent_ids)
    payload = {
        "schema_version": "1.0.0",
        "artifact_id": deterministic_id(
            IdentifierKind.ARTIFACT,
            generation.context.workspace_id,
            {
                "kind": "document-manifest",
                "run_id": generation.screening_run_id,
                "protocol_fingerprint": generation.context.protocol_fingerprint,
                "corpus_fingerprint": generation.context.corpus_fingerprint,
                "parents": parent_refs,
                "documents": documents,
            },
        ),
        "artifact_type": "document_manifest",
        "workspace_id": generation.context.workspace_id,
        "protocol_fingerprint": generation.context.protocol_fingerprint,
        "corpus_fingerprint": generation.context.corpus_fingerprint,
        "run_id": generation.screening_run_id,
        "created_at": created_at,
        "producer": {
            "package": _PRODUCER_PACKAGE,
            "version": _PRODUCER_VERSION,
            "commit": _harness_commit(),
        },
        "inputs": parent_refs,
        "data": {"documents": documents},
    }
    # An already-registered payload keeps its own recorded producer, so a replay after
    # a harness commit stays byte-identical and therefore idempotent at the gate.
    existing = registry.artifacts.get(payload["artifact_id"])
    if existing is not None:
        registered = _load_accepted_payload(workspace, payload["artifact_id"], existing)
        producer = registered.get("producer")
        if isinstance(producer, dict) and producer:
            payload["producer"] = producer

    DocumentManifestArtifact.model_validate(payload)
    return Candidate(
        payload=payload,
        context=generation.context,
        documents=provenance,
        parents=parent_refs,
        corpus_artifact_id=generation.corpus_artifact_id,
        screening_run_id=generation.screening_run_id,
        skipped_registry_entries=skips.as_dict(),
    )


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------


def _write_publication_record(
    workspace: Path, candidate: Candidate, outcome: PublicationOutcome
) -> str:
    """Atomically write the harness-side publication record.

    This is the provenance the frozen ``DocumentRecord`` cannot carry. It is written
    only after the gate accepted, and with a temp-file + ``os.replace`` commit so a
    reader never sees a half-written record. The temp file is removed in a ``finally``
    so a failed write cannot leave ``*.tmp-*`` litter beside the real record.
    """

    relative = f"{_PUBLICATION_DIR_RELPATH}/{candidate.payload['artifact_id']}.json"
    destination = _resolve_inside(workspace, relative)
    record = {
        "record_type": _PUBLICATION_RECORD_TYPE,
        "record_version": _PUBLICATION_RECORD_VERSION,
        "note": (
            "Harness-side provenance for an accepted Contract v1 document manifest. "
            "This is NOT the PDF kit's pdf-extraction-manifest-v1 sidecar and must not "
            "be presented as one."
        ),
        "artifact_id": candidate.payload["artifact_id"],
        "published_path": outcome.published_path,
        "payload_hash": outcome.provenance.get("payload_hash"),
        "workspace_id": candidate.payload["workspace_id"],
        "protocol_fingerprint": candidate.payload["protocol_fingerprint"],
        "corpus_fingerprint": candidate.payload["corpus_fingerprint"],
        "run_id": candidate.payload["run_id"],
        "idempotent": outcome.idempotent,
        "parents": candidate.parents,
        "documents": candidate.documents,
        "skipped_registry_entries": candidate.skipped_registry_entries,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(f"{destination.name}.tmp-{uuid.uuid4().hex[:8]}")
    try:
        temp.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
    return relative


def _publication_record_path(workspace: Path, artifact_id: str) -> Path | None:
    """Return the existing publication record for *artifact_id*, if there is one."""

    relative = f"{_PUBLICATION_DIR_RELPATH}/{artifact_id}.json"
    try:
        path = _resolve_inside(workspace, relative)
    except PublicationRefused:  # pragma: no cover - the id is producer-generated
        return None
    return path if path.is_file() else None


def _refuse_if_extracted_body_changed(workspace: Path, candidate: Candidate) -> None:
    """Refuse a replay whose extracted body no longer matches what was published.

    The frozen ``DocumentRecord`` has no field for the body, so a document whose
    *text* changed while its study, source bytes, and lineage stayed the same yields
    the **same** ``artifact_id`` and a byte-identical payload. The gate therefore
    reports an idempotent replay -- correctly, for the payload it can see -- while the
    bytes behind ``extracted_path`` have silently changed.

    That is a truthfulness hole in the harness's own provenance, so it is closed here
    instead of being papered over with ``idempotent=False``: the already-published
    record is the recorded truth, a divergence from it is refused, and an existing
    record is never overwritten in place.
    """

    artifact_id = candidate.payload["artifact_id"]
    path = _publication_record_path(workspace, artifact_id)
    if path is None:
        return
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        # An unreadable record is not evidence of a changed body; the gate's own
        # idempotency decision stands and this run rewrites the record.
        return
    if not isinstance(recorded, dict):
        return
    previous = {
        str(item.get("document_id")): item
        for item in recorded.get("documents") or []
        if isinstance(item, dict)
    }
    drifted: list[dict[str, str]] = []
    for item in candidate.documents:
        document_id = str(item.get("document_id"))
        was = previous.get(document_id)
        if was is None:
            continue
        for checksum in ("extracted_sha256", "extracted_file_sha256"):
            before, after = was.get(checksum), item.get(checksum)
            if before is not None and after is not None and before != after:
                drifted.append(
                    {
                        "document_id": document_id,
                        "field": checksum,
                        "published": str(before),
                        "current": str(after),
                    }
                )
    if not drifted:
        return
    raise PublicationRefused(
        "STALE_EXTRACTED_BODY",
        f"{artifact_id} was already published from a different extracted body "
        f"({len(drifted)} checksum(s) changed, e.g. {drifted[0]['field']} for document "
        f"{drifted[0]['document_id']}). The frozen DocumentRecord carries no body "
        "field, so the artifact id cannot express this change: republishing it would "
        "report an idempotent replay over bytes that were never the accepted ones, and "
        f"overwrite {path.name} in place. Fix: re-run the extraction stage so the "
        "committed body matches the published one, or start a new review generation "
        "(re-run search/screening) so the changed text lands under a different "
        "artifact id.",
        artifact_id=artifact_id,
        publication_record=path.name,
        drifted=drifted,
    )


def _log_publication_event(
    workspace: Path,
    outcome: PublicationOutcome,
    *,
    inputs: list[str],
    skipped: dict[str, str] | None = None,
    record_error: str | None = None,
) -> None:
    """Append one canonical audit event for this attempt.

    ``status`` is the observed outcome, never a constant: a refusal or an empty run
    records ``FAILED`` so the ledger cannot be read as progress. The frozen gate
    separately records its own ``ARTIFACT_ACCEPTED``/``ARTIFACT_REJECTED`` event, which
    is the record of the acceptance decision itself.

    ``skipped`` and ``record_error`` are disclosed rather than swallowed: an operator
    must be able to see which registered artifacts this run passed over, and that the
    publication record could not be written even though the manifest was accepted.
    """

    action = (
        "DOCUMENT_MANIFEST_PUBLISHED"
        if outcome.accepted
        else "DOCUMENT_MANIFEST_REFUSED"
    )
    outputs = [item for item in (outcome.published_path, outcome.record_path) if item]
    description = (
        f"Published {outcome.documents} accepted document record(s) as "
        f"{outcome.artifact_id}"
        if outcome.accepted
        else "Refused to publish a document manifest: "
        + str((outcome.refusal or {}).get("code"))
    )
    try:
        log_event(
            workspace,
            action,
            description,
            agent=_ACTOR,
            inputs=inputs,
            outputs=outputs,
            parameters={
                "artifact_id": outcome.artifact_id,
                "parent_artifact_ids": list(outcome.parent_artifact_ids),
                "refusal": (outcome.refusal or {}).get("code"),
                "skipped_registry_entries": skipped or {},
                "publication_record_error": record_error,
            },
            metrics={
                "documents": outcome.documents,
                "idempotent": outcome.idempotent,
            },
            status=outcome.status,
        )
    except OSError:  # pragma: no cover - the ledger must not mask the outcome
        logger.warning("could not append the publication audit event", exc_info=True)


def _refused_outcome(
    workspace: Path, refusal: PublicationRefused, *, inputs: list[str]
) -> PublicationOutcome:
    """Record a refusal and return it as a typed outcome. Publishes nothing."""

    outcome = PublicationOutcome(
        status=OperationStatus.FAILED.value,
        accepted=False,
        refusal=refusal.as_dict(),
        provenance={"refused_stage": "pre_acceptance"},
    )
    _log_publication_event(workspace, outcome, inputs=inputs)
    return outcome


def publish_document_manifest(workspace: Path) -> PublicationOutcome:
    """Publish the accepted document manifest for a workspace's real extraction.

    Build -> accept -> publish, with no partial state on refusal:

    * a refusal before acceptance writes **no** manifest, **no** registry entry, and
      **no** index, and returns a typed outcome whose ``status`` comes from the frozen
      ``OperationStatus`` vocabulary;
    * an acceptance-level refusal is the frozen gate's: this function writes nothing
      beyond the gate's own ``audit/rejections`` record and reports the gate's issue
      codes;
    * an acceptance publishes the manifest and its registry entry together (the gate's
      own atomic commit) and only then the publication record.

    The audit event carries the true ``OperationStatus``: a refused or empty run is
    never recorded as ``SUCCESS``.

    The ``expected`` context handed to the gate is ``candidate.context`` -- the trusted
    limbs derived from recorded workspace state during the build. It is deliberately
    *not* rebuilt from ``candidate.payload``: the gate model-validates the payload it is
    handed, so an expectation read back out of it would agree with itself by
    construction and every fingerprint/identity mismatch branch would be dead code.
    """

    workspace = Path(workspace).resolve()
    inputs = [_INCLUDED_RELPATH]
    try:
        candidate = build_document_manifest_candidate(workspace)
        inputs = [ref["artifact_id"] for ref in candidate.parents]
        _refuse_if_extracted_body_changed(workspace, candidate)
    except PublicationRefused as refusal:
        return _refused_outcome(workspace, refusal, inputs=inputs)

    result = accept_extraction_candidate(
        workspace,
        candidate.payload,
        expected=candidate.context,
        actor=_ACTOR,
    )
    base: dict[str, Any] = {
        "artifact_id": result.artifact_id,
        "rejection_path": result.rejection_path,
        "idempotent": result.idempotent,
        "documents": len(candidate.payload["data"]["documents"]),
        "parent_artifact_ids": tuple(ref["artifact_id"] for ref in candidate.parents),
        "issues": tuple(issue.model_dump(mode="json") for issue in result.issues),
        "skipped_registry_entries": dict(candidate.skipped_registry_entries),
        "provenance": {
            "payload_hash": result.payload_hash,
            "corpus_artifact_id": candidate.corpus_artifact_id,
            "screening_run_id": candidate.screening_run_id,
            "workspace_id": candidate.payload["workspace_id"],
            "protocol_fingerprint": candidate.payload["protocol_fingerprint"],
            "corpus_fingerprint": candidate.payload["corpus_fingerprint"],
            "skipped_registry_entries": candidate.skipped_registry_entries,
        },
    }
    if not result.accepted:
        outcome = PublicationOutcome(
            status=OperationStatus.FAILED.value,
            accepted=False,
            refusal={
                "code": _ACCEPTANCE_REFUSED,
                "message": (
                    "The frozen acceptance gate refused the document manifest "
                    "candidate; nothing was published and no registry entry was "
                    f"written. See {result.rejection_path or 'audit/rejections/'} for "
                    "the bounded diagnostics."
                ),
                "details": {
                    "issue_codes": [issue.code for issue in result.issues],
                    "rejection_path": result.rejection_path,
                    "event_id": result.event_id,
                },
            },
            **base,
        )
        _log_publication_event(
            workspace,
            outcome,
            inputs=inputs,
            skipped=candidate.skipped_registry_entries,
        )
        return outcome

    outcome = PublicationOutcome(
        status=OperationStatus.SUCCESS.value,
        accepted=True,
        published_path=result.published_path,
        **base,
    )
    # The gate has already committed the manifest, its registry entry, and its own
    # ARTIFACT_ACCEPTED event. A failure to write *our* provenance must therefore still
    # be recorded as an accepted publication -- silently dropping the ledger line, or
    # letting a bare traceback escape, would hide a publication that really happened.
    try:
        record_path = _write_publication_record(workspace, candidate, outcome)
    except OSError as exc:
        _log_publication_event(
            workspace,
            outcome,
            inputs=inputs,
            skipped=candidate.skipped_registry_entries,
            record_error=f"{type(exc).__name__}: {exc}",
        )
        raise PublicationRefused(
            "PUBLICATION_RECORD_UNWRITABLE",
            f"The document manifest was ACCEPTED and registered as "
            f"{outcome.artifact_id} at {outcome.published_path}, but the harness "
            "publication record could not be written "
            f"({type(exc).__name__}: {exc}). The manifest and its registry entry are "
            "committed and the ledger records the acceptance; only the per-document "
            "provenance (engine, source kind, body checksums) is missing. Fix: make "
            f"{_PUBLICATION_DIR_RELPATH} writable and re-run publish -- the frozen gate "
            "will report this as an idempotent replay, not a new publication.",
            artifact_id=outcome.artifact_id,
            published_path=outcome.published_path,
        ) from exc
    outcome = dataclasses.replace(outcome, record_path=record_path)
    _log_publication_event(
        workspace,
        outcome,
        inputs=inputs,
        skipped=candidate.skipped_registry_entries,
    )
    return outcome


# ---------------------------------------------------------------------------
# Stage 6 handoff and status
# ---------------------------------------------------------------------------


def _accepted_manifest_ids(
    workspace: Path, registry: ArtifactRegistry, context: AcceptanceContext
) -> list[str]:
    """Ids of accepted ``document_manifest`` artifacts in *context*'s generation.

    Read-only, and deliberately narrow: Stage 6 stays the only surface that interprets
    a manifest, so this exists purely to answer "is there anything to index?" without
    constructing an indexer.
    """

    found: list[str] = []
    for artifact_id, entry in sorted(registry.artifacts.items()):
        if entry.artifact_type != "document_manifest":
            continue
        payload = _load_accepted_payload(workspace, artifact_id, entry)
        if not _generation_matches(payload, context):
            continue
        DocumentManifestArtifact.model_validate(payload)
        found.append(artifact_id)
    return found


def index_accepted_documents(
    workspace: Path, chroma_dir: Path | None = None
) -> dict[str, Any]:
    """Run Stage 6 over the accepted manifest and return its real result.

    Stage 6 is the only surface that builds a typed indexing request, and it is frozen
    for this packet: this function **delegates** to the orchestrator's Stage 6 rather
    than reimplementing identity binding, so document/study identity is still inherited
    from the accepted ``document_manifest`` and the workspace limb still comes from the
    recorded ``registered_workspace_id``. Its ``status`` is the canonical
    ``OperationStatus`` the run actually reached, and Stage 6 writes its own
    ``RAG_INDEX_BUILT`` ledger event.

    A pre-flight runs *before* the orchestrator is constructed. Without it, indexing a
    workspace that has no accepted manifest still creates the vector store on disk (and
    downloads an embedding model) before Stage 6 refuses -- a real side effect over a
    run that indexed nothing. Refusing first keeps "indexing nothing" free of
    artifacts.
    """

    from scholar_harness.orchestrator import ResearchOrchestrator

    workspace = Path(workspace).resolve()
    target = (
        Path(chroma_dir).resolve()
        if chroma_dir is not None
        else workspace / _DEFAULT_CHROMA_RELPATH
    )

    context = build_acceptance_context(workspace)
    manifest_ids = _accepted_manifest_ids(workspace, _load_registry(workspace), context)
    if not manifest_ids:
        raise PublicationRefused(
            "DOCUMENT_MANIFEST_NOT_ACCEPTED",
            f"No accepted Contract v1 document_manifest matches this workspace's "
            f"generation ({context.workspace_id} / {context.corpus_fingerprint}). "
            "Stage 6 indexes the *accepted* manifest, not a file on disk, so there is "
            "nothing to index and no index is created. Fix: run "
            "`scholar-harness extract publish <workspace>` first; `extract status` "
            "reports what is recorded.",
            workspace_id=context.workspace_id,
            corpus_fingerprint=context.corpus_fingerprint,
        )

    try:
        result, _indexer = ResearchOrchestrator(workspace)._run_indexing_stage(target)
    except RegisteredWorkspaceIdentityMissingError as exc:
        raise PublicationRefused(
            "WORKSPACE_IDENTITY_NOT_RECORDED",
            f"Stage 6 refused to index: {exc}",
        ) from exc
    status = str(result.get("status") or "")
    if status not in {member.value for member in OperationStatus}:
        raise PublicationRefused(
            "INDEXING_STATUS_NOT_CANONICAL",
            f"Stage 6 reported status {status!r}, which is not a canonical "
            "OperationStatus.",
            status=status,
        )
    return result


def publication_status(workspace: Path) -> dict[str, Any]:
    """Report what is recorded, without publishing or indexing anything."""

    workspace = Path(workspace).resolve()
    extracted_dir = workspace / _EXTRACTED_RELPATH
    report: dict[str, Any] = {
        "workspace": str(workspace),
        "extracted_files": (
            sorted(
                path.relative_to(workspace).as_posix()
                for path in extracted_dir.glob("*.md")
            )
            if extracted_dir.is_dir()
            else []
        ),
        "recordings": {},
    }
    skips = _SkipLog()
    try:
        generation = _build_generation(workspace, skips)
    except PublicationRefused as refusal:
        report["recordings"] = {
            "refusal": refusal.as_dict(),
            "skipped_registry_entries": skips.as_dict(),
        }
        report["ready_to_publish"] = False
        return report

    registry = generation.registry
    assert registry is not None
    report["recordings"] = {
        "workspace_id": generation.context.workspace_id,
        "protocol_fingerprint": generation.context.protocol_fingerprint,
        "corpus_fingerprint": generation.context.corpus_fingerprint,
        "corpus_artifact_id": generation.corpus_artifact_id,
        "screening_run_id": generation.screening_run_id,
        "document_manifests": sorted(
            artifact_id
            for artifact_id, entry in registry.artifacts.items()
            if entry.artifact_type == "document_manifest"
        ),
        "skipped_registry_entries": skips.as_dict(),
        "registry_path": _REGISTRY_RELPATH,
    }
    report["ready_to_publish"] = True
    return report
