"""Harness-owned E3 index-acceptance adapter (T-131, handoff section 6).

Packet E3 (``docs/architecture/wp01_packet_e3_implementation_handoff.md`` section 6)
splits indexing into two jobs: the ``scholar-rag-kit`` produces a **candidate**
(``IndexService`` ``T-90`` over ``T-50`` sidecar construction, ``T-60``
replacement ``R1``-``R7``, ``T-80`` backend verification), and this harness
adapter **decides** whether that candidate becomes the accepted E3 record. Neither
may do the other's job (``G-9``).

The seven ordered checks (section 6.2) are fail-fast: a failure at step *k*
means steps *k+1*..*7* never run, which is what makes "zero authoritative
publication" checkable rather than aspirational. Checks 1-3 and 5 are pure
verification over immutable inputs and a file. Check 4 adds the eligibility
join (adapter share only, see below). Check 6 is the only backend touch and is
a **read** through the kit's typed verification query. Check 7 is the only
writer (``rag/index/accepted.json`` plus one journal line, then intent removal).

Ownership (section 6.1):

* the kit may read the accepted parent through the harness-supplied reference,
  chunk, embed, stage, replace in the backend, and write the sidecar, the commit
  intent, and its own run report. It may not import ``scholar_harness``, write
  ``audit/journal.jsonl``, write any Contract v1 registry, claim its candidate
  was accepted, or mint a non-``CHK-`` identity.
* this adapter may load the parent through the frozen registry, re-verify
  identity/lineage/config, recompute every fingerprint, interrogate the backend,
  and write the accepted record plus the canonical audit event. It may not
  re-implement chunking, embedding, retrieval, or scoring; repair the candidate
  instead of rejecting it; or publish a ``PARTIAL`` candidate as complete.

Check 4 kit-share boundary (explicit):

* kit-owned (``tools/scholar-rag-kit/src/scholar_rag/index_service.py``
  ``eligibility join``; ``index_manifest.py`` ``PARENT_HASH_MISMATCH``,
  ``EXTRACTED_TEXT_UNUSABLE``, ``EXTRACTED_CONTENT_CHANGED``,
  ``cross-document collision``; ``_refuse_path_shaped`` /
  ``docs_destination``): the chunk-level join of ``extracted_content_sha256``,
  path-shape and docs-directory containment, usability and staleness, and
  per-study versus collection-global uniqueness. The harness only forwards
  ``parent_view`` verbatim and never re-derives those facts.
* adapter-owned (this module): every indexed and every rejected
  ``document_id``/``study_id`` is eligible in the accepted parent with
  byte-identical values, and no document's own metadata re-bound its identity.
  A filename, DOI, title, or provider id never binds; only the parent's own
  ``document_id``/``study_id`` limbs do.

Backend discipline (section 6.1): the adapter interrogates the backend **only**
through the kit's typed verification query
(:func:`scholar_rag.index_verifier.verify_backend` over the
:class:`~scholar_rag.index_verifier.VerifiableBackend` protocol). It never opens
a Chroma file, never counts rows from disk, never supplies an embedder, and
never writes, stages, switches, or deletes a row. Check 6 is a read.

Publication (sections 6.3-6.4): the accepted E3 record is adapter-owned and
non-Contract (``rag/index/accepted.json``, schema ``index-acceptance-v1``;
never registered, never a parent, never a ``data`` payload). Step 7 is a single
transaction over exactly two durable writes plus one delete: the accepted
record and one appended journal line, then commit-intent removal. If the audit
append fails the record is rolled back and the run reports
``ATOMIC_COMMIT_FAILED`` with the last known complete index still visible. A
partially written ``accepted.json`` is detected by its own ``artifact_checksum``
and treated as absent, never as a truncated truth.

Rejection (section 6.5): no accepted record, no success event, no registry
mutation, previous index intact, typed refusal through the same result model as
a success. ``PARTIAL`` may be recorded but is never reported complete.

Idempotency (sections 6.3, 7.2): a replay of the same ``index_fingerprint``
under the same ``manifest_id`` is a deterministic no-op (no write, no event).
A different payload under the same ``manifest_id`` is ``IDEMPOTENCY_CONFLICT``,
never an overwrite. Supersession by a different ``manifest_id`` is the only
implicit replacement; otherwise removal is explicit or by teardown.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from scholar_rag.index_manifest import (
    IndexManifest,
    IndexManifestError,
    compute_fingerprints,
    rederive_chunk_identities,
)
from scholar_rag.index_verifier import verify_backend
from scholar_rag.replacement import ReplacementError

from scholar_harness.console.api.audit import log_event
from scholar_harness.contracts.acceptance import ArtifactRegistry
from scholar_harness.contracts.canonical import (
    canonical_fingerprint,
    canonical_json_bytes,
)
from scholar_harness.contracts.models import ArtifactReference, DocumentManifestArtifact

logger = logging.getLogger(__name__)

__all__ = [
    "ACCEPTANCE_SCHEMA_VERSION",
    "ACCEPTED_RELPATH",
    "ACCEPTED_SCHEMA_VERSION",
    "IndexAcceptanceResult",
    "accept_index_candidate",
    "build_acceptance_event",
    "build_accepted_record",
    "read_accepted_record",
]

#: The adapter-owned accepted-record schema. The tripwire in
#: ``tests/conformance/test_e3_index_lineage_boundary.py`` (``E3-NEG-037`` /
#: ``E3-POS-008``) asserts this string appears under ``src/scholar_harness/``;
#: its absence meant the adapter did not exist yet.
ACCEPTANCE_SCHEMA_VERSION = "index-acceptance-v1"

#: Backwards-compatible alias for the same schema token.
ACCEPTED_SCHEMA_VERSION = ACCEPTANCE_SCHEMA_VERSION

#: One file per workspace, outside ``artifacts/``, so it can never be mistaken
#: for a published Contract artifact; sibling to the per-run sidecars.
ACCEPTED_RELPATH = "rag/index/accepted.json"

#: Registry location (frozen Contract v1 registry, read-only for this adapter).
_REGISTRY_RELPATH = "audit/artifact_registry.json"

#: Canonical audit actions (section 6.6). ``RAG_INDEX_BUILT`` is already in use;
#: ``RAG_INDEX_REJECTED`` is the refusal spelling in the same uppercase
#: convention, never a new ``status`` vocabulary. This adapter writes ``BUILT``
#: on success only; refusals at steps 1-6 write no journal line (step 7 never
#: runs), and the kit's own run report carries the refusal detail.
ACTION_BUILT = "RAG_INDEX_BUILT"
ACTION_REJECTED = "RAG_INDEX_REJECTED"

_ACTOR = "scholar-harness-index-acceptance-adapter"

#: Contract v1 artifact types (frozen ``_ARTIFACT_MODELS`` keys). Anything else
#: offered as a parent is ``UNSUPPORTED_ARTIFACT_TYPE`` (C-03).
_KNOWN_CONTRACT_TYPES = frozenset(
    {
        "claims_ledger",
        "corpus_snapshot",
        "document_manifest",
        "run_manifest",
        "screening_batch",
        "screening_decisions",
    }
)

#: The required parent type for the accepted chain position (C-07).
_REQUIRED_PARENT_TYPE = "document_manifest"

#: The six digests check 5 recomputes by the section 5.2 stage order, plus the
#: per-chunk re-derivation by the section 5.1 rule.
_FINGERPRINT_FIELDS = (
    "manifest_id",
    "artifact_checksum",
    "chunk_set_fingerprint",
    "configuration_fingerprint",
    "production_fingerprint",
    "index_fingerprint",
)


@dataclass(frozen=True)
class IndexAcceptanceResult:
    """One typed acceptance outcome, for success and refusal alike.

    A client never has to tell an exception from a refusal or a refusal from a
    partial success: ``accepted`` is the verdict, ``failing_step`` (1-7) plus
    ``code`` names the refusal, and ``reused`` marks the deterministic no-op.
    ``complete`` is true only for an accepted ``SUCCESS`` manifest, so a
    ``PARTIAL`` candidate is recorded but never reported complete.
    """

    accepted: bool
    manifest_id: str | None = None
    index_fingerprint: str | None = None
    status: str | None = None
    complete: bool = False
    failing_step: int | None = None
    code: str | None = None
    detail: str | None = None
    reused: bool = False
    event_id: str | None = None
    accepted_path: str | None = None
    counts: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "manifest_id": self.manifest_id,
            "index_fingerprint": self.index_fingerprint,
            "status": self.status,
            "complete": self.complete,
            "failing_step": self.failing_step,
            "code": self.code,
            "detail": self.detail,
            "reused": self.reused,
            "event_id": self.event_id,
            "accepted_path": self.accepted_path,
            "counts": dict(self.counts),
        }


class _Refusal(Exception):
    """Internal fail-fast signal: one ordered step refused with one code."""

    def __init__(self, step: int, code: str, detail: str) -> None:
        super().__init__(f"step {step} {code}: {detail}")
        self.step = step
        self.code = code
        self.detail = detail[:500]


def _resolve_inside(workspace: Path, relative: str) -> Path:
    """Resolve *relative* inside *workspace*, or raise a step-1 refusal."""

    try:
        ArtifactReference.portable_workspace_path(relative)
    except ValueError as exc:
        raise _Refusal(
            1, "VALIDATION_ERROR", f"{relative!r} is not portable ({exc})"
        ) from exc
    try:
        resolved = (workspace / PurePosixPath(relative)).resolve()
        resolved.relative_to(workspace)
    except (OSError, ValueError) as exc:
        raise _Refusal(
            1, "VALIDATION_ERROR", f"{relative!r} escapes workspace ({exc})"
        ) from exc
    return resolved


def _parent_hash(payload: Mapping[str, Any]) -> str:
    """The registry hash of an accepted parent payload (frozen gate rule)."""

    return canonical_fingerprint(dict(payload))


def _check_manifest_shape(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise _Refusal(1, "VALIDATION_ERROR", "index candidate must be a JSON object")
    return dict(payload)


def _load_registry(workspace: Path) -> ArtifactRegistry:
    path = workspace / _REGISTRY_RELPATH
    if not path.is_file():
        raise _Refusal(1, "NOT_FOUND", f"no registry at {_REGISTRY_RELPATH}")
    try:
        return ArtifactRegistry.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise _Refusal(1, "VALIDATION_ERROR", f"registry unreadable ({exc})") from exc


def _load_parent_payload(
    workspace: Path, artifact_id: str, entry: Any
) -> dict[str, Any]:
    resolved = _resolve_inside(workspace, str(entry.path))
    if not resolved.is_file():
        raise _Refusal(1, "NOT_FOUND", f"parent {artifact_id} has no file")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _Refusal(
            1, "VALIDATION_ERROR", f"parent {artifact_id} unreadable ({exc})"
        ) from exc
    if not isinstance(payload, dict):
        raise _Refusal(1, "VALIDATION_ERROR", f"parent {artifact_id} not an object")
    return payload


def _accepted_checksum(record: Mapping[str, Any]) -> str:
    """Seal an accepted record the way a sidecar seals itself (section 6.3)."""

    return canonical_fingerprint({**dict(record), "artifact_checksum": None})


def read_accepted_record(workspace: Path) -> tuple[bytes | None, dict[str, Any] | None]:
    """Return ``(raw bytes, parsed record)`` for the current accepted record.

    A partially written file (checksum mismatch) is treated as absent and
    returns ``(bytes, None)``: the bytes are preserved for rollback, but no
    caller may read them as truth.
    """

    path = workspace / ACCEPTED_RELPATH
    if not path.is_file():
        return None, None
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        try:
            return path.read_bytes(), None
        except OSError:
            return None, None
    if not isinstance(parsed, dict):
        return raw, None
    if parsed.get("schema_version") != ACCEPTANCE_SCHEMA_VERSION:
        return raw, None
    expected = parsed.get("artifact_checksum")
    if not isinstance(expected, str) or _accepted_checksum(parsed) != expected:
        return raw, None
    return raw, parsed


def build_accepted_record(
    *,
    workspace_id: str,
    parent_artifact_id: str,
    parent_artifact_type: str,
    parent_artifact_sha256: str,
    parent_lineage_sha256: str,
    manifest_id: str,
    manifest_path: str,
    artifact_checksum: str,
    index_fingerprint: str,
    chunk_set_fingerprint: str,
    configuration_fingerprint: str,
    production_fingerprint: str,
    status: str,
    counts: Mapping[str, Any],
    accepted_at: str,
    accepted_by: str,
) -> dict[str, Any]:
    """Build the adapter-owned accepted record (section 6.3, exact field set)."""

    record: dict[str, Any] = {
        "schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "workspace_id": workspace_id,
        "parent_artifact_ref": {
            "artifact_id": parent_artifact_id,
            "artifact_type": parent_artifact_type,
            "sha256": parent_artifact_sha256,
        },
        "parent_lineage_sha256": parent_lineage_sha256,
        "manifest_id": manifest_id,
        "manifest_path": manifest_path,
        "artifact_checksum": None,
        "index_fingerprint": index_fingerprint,
        "chunk_set_fingerprint": chunk_set_fingerprint,
        "configuration_fingerprint": configuration_fingerprint,
        "production_fingerprint": production_fingerprint,
        "status": status,
        "counts": {
            "accepted_documents": int(counts["accepted_documents"]),
            "rejected_documents": int(counts["rejected_documents"]),
            "visible_chunks": int(counts["visible_chunks"]),
        },
        "accepted_at": accepted_at,
        "accepted_by": accepted_by,
    }
    record["artifact_checksum"] = _accepted_checksum(record)
    return record


def build_acceptance_event(
    *,
    action: str,
    workspace_id: str,
    run_id: str,
    parent_artifact_id: str,
    parent_artifact_sha256: str,
    manifest_id: str,
    manifest_path: str,
    artifact_checksum: str,
    index_fingerprint: str,
    chunk_set_fingerprint: str,
    configuration_fingerprint: str,
    production_fingerprint: str,
    protocol_fingerprint: str,
    corpus_fingerprint: str,
    counts: Mapping[str, Any],
    rejected_documents: list[dict[str, str]],
    embedding_identity: Mapping[str, Any],
    configuration: Mapping[str, Any],
    failing_step: int | None = None,
    code: str | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Build the canonical section 6.6 event body (exact field set).

    Returns ``(description, parameters, metrics)`` for the journal append. The
    description is machine-written from codes and counts only: no absolute
    path, no ``db_path``, no secret, no environment value, and no free-text
    success claim (no ``verified``/``entailed``/similarity language).
    """

    if action == ACTION_REJECTED:
        description = (
            f"{action} manifest_id={manifest_id} step={failing_step} code={code} "
            f"accepted={counts.get('accepted_documents', 0)} "
            f"rejected={counts.get('rejected_documents', 0)} "
            f"chunks={counts.get('visible_chunks', 0)}"
        )
    else:
        description = (
            f"{action} manifest_id={manifest_id} "
            f"accepted={counts.get('accepted_documents', 0)} "
            f"rejected={counts.get('rejected_documents', 0)} "
            f"chunks={counts.get('visible_chunks', 0)}"
        )
    parameters: dict[str, Any] = {
        "workspace_id": workspace_id,
        "run_id": run_id,
        "parent_artifact_id": parent_artifact_id,
        "parent_artifact_sha256": parent_artifact_sha256,
        "manifest_id": manifest_id,
        "manifest_path": manifest_path,
        "artifact_checksum": artifact_checksum,
        "index_fingerprint": index_fingerprint,
        "chunk_set_fingerprint": chunk_set_fingerprint,
        "configuration_fingerprint": configuration_fingerprint,
        "production_fingerprint": production_fingerprint,
        "protocol_fingerprint": protocol_fingerprint,
        "corpus_fingerprint": corpus_fingerprint,
        "counts": {
            "accepted_documents": int(counts["accepted_documents"]),
            "rejected_documents": int(counts["rejected_documents"]),
            "visible_chunks": int(counts["visible_chunks"]),
        },
        "rejected_documents": [
            {"document_id": str(item["document_id"]), "code": str(item["code"])}
            for item in rejected_documents
        ],
        "embedding_identity": {
            "provider": str(embedding_identity["provider"]),
            "model": str(embedding_identity["model"]),
            "dimension": int(embedding_identity["dimension"]),
            "distance_metric": str(embedding_identity["distance_metric"]),
        },
        "configuration": dict(configuration),
    }
    if failing_step is not None or code is not None:
        parameters["failing_step"] = failing_step
        parameters["code"] = code
    metrics = {
        "accepted_documents": int(counts["accepted_documents"]),
        "rejected_documents": int(counts["rejected_documents"]),
        "visible_chunks": int(counts["visible_chunks"]),
    }
    return description, parameters, metrics


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex[:8]}")
    with open(temp, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _restore_accepted(path: Path, previous: bytes | None) -> None:
    if previous is None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        # Remove now-empty parent dirs up to the workspace rag/ boundary is left
        # to the caller; an empty dir is not authoritative state.
        return
    _atomic_write(path, previous)


def accept_index_candidate(
    workspace: Path,
    manifest: Mapping[str, Any] | IndexManifest,
    *,
    run_id: str,
    manifest_path: str,
    reader: Any,
    intent_path: str | None = None,
    accepted_by: str = _ACTOR,
    journal_append: Callable[..., Any] | None = None,
    accepted_at: str | None = None,
) -> IndexAcceptanceResult:
    """Decide one kit-produced candidate through the seven ordered checks.

    *workspace* is the stated workspace root. *manifest* is the kit's
    candidate sidecar (a mapping or a typed :class:`IndexManifest`); it is
    never repaired, only re-verified. *run_id* is the indexing run.
    *manifest_path* is the workspace-relative sidecar reference recorded in the
    accepted record. *reader* is the kit's typed verification backend
    (:class:`~scholar_rag.index_verifier.VerifiableBackend`); it is the only
    backend touch and only check 6 uses it. *intent_path* is the
    workspace-relative commit intent removed after a durable commit.
    *journal_append* overrides the journal write for fault-injection tests; it
    must raise ``OSError`` to simulate an unwritable ledger.
    """

    workspace = Path(workspace).resolve()
    if not isinstance(run_id, str) or not run_id.strip():
        return IndexAcceptanceResult(
            accepted=False,
            failing_step=1,
            code="VALIDATION_ERROR",
            detail="run_id must be a non-empty string",
        )
    try:
        _resolve_inside(workspace, manifest_path)
    except _Refusal as refusal:
        return IndexAcceptanceResult(
            accepted=False,
            failing_step=refusal.step,
            code="VALIDATION_ERROR",
            detail=f"manifest_path refused: {refusal.detail}",
        )
    if intent_path is not None:
        try:
            _resolve_inside(workspace, intent_path)
        except _Refusal as refusal:
            return IndexAcceptanceResult(
                accepted=False,
                failing_step=1,
                code="VALIDATION_ERROR",
                detail=f"intent_path refused: {refusal.detail}",
            )

    # Fail-fast chain: each step raises _Refusal(step, code, detail).
    payload: dict[str, Any] = {}
    try:
        if isinstance(manifest, IndexManifest):
            payload = manifest.canonical_payload()  # type: ignore[attr-defined]
        else:
            payload = _check_manifest_shape(manifest)
        # -- check 1: load the parent through the frozen registry ------------
        parent_ref = payload.get("parent_artifact_ref")
        if not isinstance(parent_ref, Mapping):
            raise _Refusal(
                1, "VALIDATION_ERROR", "candidate has no parent_artifact_ref"
            )
        parent_id = parent_ref.get("artifact_id")
        parent_sha = parent_ref.get("sha256")
        parent_type_declared = parent_ref.get("artifact_type")
        if not isinstance(parent_id, str) or not parent_id.strip():
            raise _Refusal(1, "VALIDATION_ERROR", "parent artifact_id missing")
        if not isinstance(parent_sha, str) or not parent_sha.strip():
            raise _Refusal(1, "VALIDATION_ERROR", "parent sha256 missing")
        registry = _load_registry(workspace)
        entry = registry.artifacts.get(parent_id)
        if entry is None:
            raise _Refusal(1, "NOT_FOUND", f"parent {parent_id} not in registry")
        if entry.artifact_type not in _KNOWN_CONTRACT_TYPES:
            raise _Refusal(
                1,
                "UNSUPPORTED_ARTIFACT_TYPE",
                f"parent type {entry.artifact_type!r} is not a Contract type",
            )
        parent_payload = _load_parent_payload(workspace, parent_id, entry)
        try:
            parent = DocumentManifestArtifact.model_validate(parent_payload)
        except ValueError as exc:
            raise _Refusal(
                1, "VALIDATION_ERROR", f"parent fails frozen model ({exc})"
            ) from exc

        # -- check 2: parent identity and hash against the registry entry -----
        recomputed_parent_hash = _parent_hash(parent_payload)
        if str(parent_ref.get("artifact_id")) != parent_id:
            raise _Refusal(2, "PARENT_HASH_MISMATCH", "parent artifact_id disagrees")
        if (
            str(parent_sha) != str(entry.sha256)
            or str(parent_sha) != recomputed_parent_hash
        ):
            raise _Refusal(
                2, "PARENT_HASH_MISMATCH", "parent hash stale against registry"
            )

        # -- check 3: generation agreement and required parent type ----------
        if (
            str(entry.artifact_type) != _REQUIRED_PARENT_TYPE
            or str(parent_type_declared) != _REQUIRED_PARENT_TYPE
        ):
            raise _Refusal(
                3, "REQUIRED_PARENT_TYPE_MISSING", "parent is not a document_manifest"
            )
        if str(payload.get("workspace_id")) != str(parent.workspace_id):
            raise _Refusal(
                3, "WORKSPACE_NAMESPACE_MISMATCH", "workspace disagrees with parent"
            )
        if str(payload.get("protocol_fingerprint")) != str(parent.protocol_fingerprint):
            raise _Refusal(
                3, "PROTOCOL_FINGERPRINT_MISMATCH", "protocol disagrees with parent"
            )
        if str(payload.get("corpus_fingerprint")) != str(parent.corpus_fingerprint):
            raise _Refusal(
                3, "CORPUS_FINGERPRINT_MISMATCH", "corpus disagrees with parent"
            )

        # -- check 4: adapter share of the eligibility join ------------------
        # Kit-share (not re-implemented here): extracted_content_sha256 join,
        # path-shape / docs-directory containment, usability / staleness, and
        # per-study versus collection-global uniqueness via
        # ``index_service.py`` (``eligibility join``) and ``index_manifest.py``
        # (``PARENT_HASH_MISMATCH`` / ``EXTRACTED_TEXT_UNUSABLE`` /
        # ``EXTRACTED_CONTENT_CHANGED`` / ``cross-document collision`` /
        # ``_refuse_path_shaped`` / ``docs_destination``). The harness forwards
        # ``parent_view`` verbatim for those proofs.
        parent_by_document = {
            record.document_id: record for record in parent.data.documents
        }
        for section in ("documents", "rejected_documents"):
            entries = payload.get(section) or []
            if not isinstance(entries, list):
                raise _Refusal(4, "VALIDATION_ERROR", f"{section} is not a list")
            for item in entries:
                if not isinstance(item, Mapping):
                    raise _Refusal(
                        4, "VALIDATION_ERROR", f"{section} entry not an object"
                    )
                document_id = item.get("document_id")
                study_id = item.get("study_id")
                if not isinstance(document_id, str) or not document_id:
                    raise _Refusal(
                        4, "VALIDATION_ERROR", f"{section} without document_id"
                    )
                if not isinstance(study_id, str) or not study_id:
                    raise _Refusal(4, "VALIDATION_ERROR", f"{section} without study_id")
                parent_record = parent_by_document.get(document_id)
                if parent_record is None:
                    raise _Refusal(
                        4,
                        "VALIDATION_ERROR",
                        f"{document_id!r} not eligible in the accepted parent",
                    )
                # Byte-identical values: no normalization, no alias resolution,
                # no DOI / title / filename re-binding. The parent's own limbs
                # are the only identity source.
                if study_id != parent_record.study_id:
                    raise _Refusal(
                        4,
                        "VALIDATION_ERROR",
                        f"{document_id!r} re-binds study identity",
                    )
                if section == "documents" and isinstance(
                    item.get("extracted_path"), str
                ):
                    if item["extracted_path"] != parent_record.extracted_path:
                        raise _Refusal(
                            4,
                            "VALIDATION_ERROR",
                            f"{document_id!r} re-binds extracted_path",
                        )

        # -- idempotency gate (section 7.2, before any backend touch) ----
        # Same manifest_id plus same index_fingerprint is a deterministic
        # no-op (no write, no event, no backend read). The same manifest_id
        # with a different declared payload is IDEMPOTENCY_CONFLICT, never an
        # overwrite -- checked here (on declared fields) so a conflicting
        # manifest_id is reported as a conflict even when its digests would
        # also fail check 5. A corrupt previous record is treated as absent.
        _previous_bytes, _previous_record = read_accepted_record(workspace)
        _declared_manifest_id = payload.get("manifest_id")
        _declared_index_fp = payload.get("index_fingerprint")
        if (
            isinstance(_declared_manifest_id, str)
            and _previous_record is not None
            and _previous_record.get("manifest_id") == _declared_manifest_id
        ):
            if (
                isinstance(_declared_index_fp, str)
                and _previous_record.get("index_fingerprint") == _declared_index_fp
            ):
                return IndexAcceptanceResult(
                    accepted=True,
                    manifest_id=str(_declared_manifest_id),
                    index_fingerprint=str(_declared_index_fp),
                    status=str(_previous_record.get("status")),
                    complete=str(_previous_record.get("status")) == "SUCCESS",
                    reused=True,
                    accepted_path=ACCEPTED_RELPATH,
                    counts=dict(_previous_record.get("counts") or {}),
                )
            raise _Refusal(
                7,
                "IDEMPOTENCY_CONFLICT",
                f"{_declared_manifest_id} already accepted with another payload",
            )

        # -- check 5: recompute every fingerprint, re-derive every chunk -----
        try:
            typed: IndexManifest = (
                manifest
                if isinstance(manifest, IndexManifest)
                else IndexManifest.from_payload(payload)
            )
        except IndexManifestError as exc:
            code = getattr(exc, "code", "VALIDATION_ERROR")
            if code not in ("VALIDATION_ERROR", "CHUNK_IDENTITY_COLLISION"):
                code = "VALIDATION_ERROR"
            raise _Refusal(
                5, code, f"sidecar invalid [{getattr(exc, 'code', '?')}]: {exc}"
            ) from exc
        try:
            recomputed = compute_fingerprints(typed.canonical_payload())
        except IndexManifestError as exc:
            raise _Refusal(
                5, "VALIDATION_ERROR", f"fingerprint recompute refused: {exc}"
            ) from exc
        for dotted in _FINGERPRINT_FIELDS:
            # Nested dotted fields (none in the six) are read via the payload;
            # the six top-level digests compare directly.
            declared = typed.canonical_payload().get(dotted)
            if recomputed.get(dotted) != declared:
                raise _Refusal(5, "VALIDATION_ERROR", f"{dotted} does not re-derive")
        try:
            rederive_chunk_identities(typed.canonical_payload())
        except IndexManifestError as exc:
            raise _Refusal(
                5, "CHUNK_IDENTITY_COLLISION", f"chunk identity: {exc}"
            ) from exc

        manifest_id = str(typed.manifest_id)
        index_fingerprint = str(typed.index_fingerprint)
        status = str(typed.status)
        if status not in ("SUCCESS", "PARTIAL"):
            raise _Refusal(
                5, "VALIDATION_ERROR", f"status {status!r} cannot be accepted"
            )
        counts = {
            "accepted_documents": int(typed.counts.accepted_documents),
            "rejected_documents": int(typed.counts.rejected_documents),
            "visible_chunks": int(typed.counts.visible_chunks),
        }

        # -- check 6: live backend holds exactly the declared set ------------
        # The only backend touch, and a read: the kit's typed query, never a
        # file open. A raised read is a refusal; a well-read disagreement is a
        # returned mismatch with the kit's own codes.
        try:
            verification = verify_backend(typed, reader)
        except ReplacementError as exc:
            code = getattr(exc, "code", None) or "BACKEND_STATE_INCONSISTENT"
            if code not in (
                "BACKEND_STATE_INCONSISTENT",
                "EMBEDDING_IDENTITY_CHANGED",
                "CONFIGURATION_INEFFECTIVE",
            ):
                code = "BACKEND_STATE_INCONSISTENT"
            raise _Refusal(
                6, code, f"backend unreadable: {type(exc).__name__}"
            ) from exc
        except (ValueError, TypeError) as exc:
            raise _Refusal(
                6, "BACKEND_STATE_INCONSISTENT", f"backend unreadable: {exc}"
            ) from exc
        if not verification.matches:
            code = str((verification.codes or ("BACKEND_STATE_INCONSISTENT",))[0])
            raise _Refusal(
                6, code, f"live set disagrees: {verification.detail or code}"
            )

        # -- check 7: atomic publication (the only writer) --------------------
        accepted_path = workspace / ACCEPTED_RELPATH
        previous_bytes, previous_record = _previous_bytes, _previous_record

        stamp = accepted_at or datetime.now(UTC).isoformat()
        record = build_accepted_record(
            workspace_id=str(typed.workspace_id),
            parent_artifact_id=str(typed.parent_artifact_ref.artifact_id),
            parent_artifact_type=str(typed.parent_artifact_ref.artifact_type),
            parent_artifact_sha256=str(typed.parent_artifact_ref.sha256),
            parent_lineage_sha256=str(typed.parent_lineage_sha256),
            manifest_id=manifest_id,
            manifest_path=manifest_path,
            artifact_checksum=str(typed.artifact_checksum),
            index_fingerprint=index_fingerprint,
            chunk_set_fingerprint=str(typed.chunk_set_fingerprint),
            configuration_fingerprint=str(typed.configuration_fingerprint),
            production_fingerprint=str(typed.production_fingerprint),
            status=status,
            counts=counts,
            accepted_at=stamp,
            accepted_by=accepted_by,
        )
        rejected_refs = [
            {"document_id": str(item.document_id), "code": str(item.code)}
            for item in typed.rejected_documents
        ]
        description, parameters, metrics = build_acceptance_event(
            action=ACTION_BUILT,
            workspace_id=str(typed.workspace_id),
            run_id=run_id,
            parent_artifact_id=str(typed.parent_artifact_ref.artifact_id),
            parent_artifact_sha256=str(typed.parent_artifact_ref.sha256),
            manifest_id=manifest_id,
            manifest_path=manifest_path,
            artifact_checksum=str(typed.artifact_checksum),
            index_fingerprint=index_fingerprint,
            chunk_set_fingerprint=str(typed.chunk_set_fingerprint),
            configuration_fingerprint=str(typed.configuration_fingerprint),
            production_fingerprint=str(typed.production_fingerprint),
            protocol_fingerprint=str(typed.protocol_fingerprint),
            corpus_fingerprint=str(typed.corpus_fingerprint),
            counts=counts,
            rejected_documents=rejected_refs,
            embedding_identity={
                "provider": str(typed.embedder.provider),
                "model": str(typed.embedder.model),
                "dimension": int(typed.embedder.dimension),
                "distance_metric": str(typed.embedder.distance_metric),
            },
            configuration=dict(typed.chunker.configuration),
        )
        # Both prepared, then committed: the record first, then the event. A
        # journal failure rolls the record back; the intent is removed only
        # after both are durable.
        _atomic_write(accepted_path, (canonical_json_bytes(record) + b"\n"))
        try:
            if journal_append is not None:
                appended = journal_append(
                    workspace,
                    ACTION_BUILT,
                    description,
                    parameters=parameters,
                    metrics=metrics,
                    status=status,
                    run_id=run_id,
                    manifest_id=manifest_id,
                )
                event_id = (
                    appended.get("event_id") if isinstance(appended, Mapping) else None
                )
            else:
                event = log_event(
                    workspace,
                    ACTION_BUILT,
                    description,
                    agent=accepted_by,
                    inputs=[str(registry.artifacts[parent_id].path)],
                    outputs=[ACCEPTED_RELPATH, manifest_path],
                    parameters=parameters,
                    metrics=metrics,
                    status=status,
                    refresh_index=False,
                )
                event_id = event.get("event_id")
        except OSError as exc:
            _restore_accepted(accepted_path, previous_bytes)
            raise _Refusal(
                7, "ATOMIC_COMMIT_FAILED", f"journal unwritable ({type(exc).__name__})"
            ) from exc
        except Exception as exc:  # noqa: BLE001 - an unexpected journal fault still rolls back
            _restore_accepted(accepted_path, previous_bytes)
            raise _Refusal(
                7, "ATOMIC_COMMIT_FAILED", f"journal fault ({type(exc).__name__})"
            ) from exc

        if intent_path is not None:
            try:
                candidate = _resolve_inside(workspace, intent_path)
                candidate.unlink(missing_ok=True)
            except OSError:
                logger.warning(
                    "accepted %s but intent %s not removed",
                    manifest_id,
                    intent_path,
                    exc_info=True,
                )

        return IndexAcceptanceResult(
            accepted=True,
            manifest_id=manifest_id,
            index_fingerprint=index_fingerprint,
            status=status,
            complete=(status == "SUCCESS"),
            event_id=event_id,
            accepted_path=ACCEPTED_RELPATH,
            counts=counts,
        )
    except _Refusal as refusal:
        payload_counts: dict[str, int] = {}
        try:
            raw_counts = payload.get("counts") if isinstance(payload, Mapping) else None
            if isinstance(raw_counts, Mapping):
                payload_counts = {
                    str(k): int(v) for k, v in raw_counts.items() if isinstance(v, int)
                }
        except (TypeError, ValueError):
            payload_counts = {}
        return IndexAcceptanceResult(
            accepted=False,
            manifest_id=str(payload.get("manifest_id"))
            if isinstance(payload.get("manifest_id"), str)
            else None,
            index_fingerprint=str(payload.get("index_fingerprint"))
            if isinstance(payload.get("index_fingerprint"), str)
            else None,
            status=None,
            complete=False,
            failing_step=refusal.step,
            code=refusal.code,
            detail=refusal.detail,
            counts=payload_counts,
        )


def _unused_secret_scan_guard() -> (
    None
):  # pragma: no cover - documents the never-fields
    """The accepted record and the section 6.6 event never carry these."""

    raise AssertionError(
        "never an absolute path, a db_path, a secret, a bearer token, "
        "an environment value, a timestamp-derived identity, or a free-text claim"
    )
