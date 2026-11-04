"""``nexus-scholar accept-corpus``: the entry path into screening (M0).

``prepare`` needs an accepted Contract-v1 ``corpus_snapshot`` in the artifact
registry, but no runtime code built one (CORE-07), so screening could not
start on a fresh workspace. This command builds the snapshot from the
workspace's verified records with the search kit's own builder
(``scholar_search.identity.build_corpus_snapshot_artifact``) and publishes it
through the harness acceptance gate, which validates it against the frozen
Contract-v1 schema and journals the acceptance. Full Packet B adoption in the
discovery stage is M3; this is the minimal bridge.

Sources: ``literature/verified.json`` (what discovery writes), or a RIS export
(Scopus, Web of Science, Zotero), which is first written to ``verified.json``
with record-derived ``SCI-`` ids so a re-import yields the same ids.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_protocol.canonical import canonical_fingerprint as protocol_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.importers import RISImporter
from scholar_search.models import Document

from .contracts import AcceptanceContext, accept_artifact
from .contracts.canonical import canonical_fingerprint, deterministic_id
from .contracts.identifiers import IdentifierKind
from .screening.batcher import _rebuild_doc
from .workspace.audit import append_event


class AcceptCorpusRefused(Exception):
    """A precondition or the acceptance gate refused; nothing was published."""


@dataclass(frozen=True)
class AcceptCorpusResult:
    artifact_id: str
    study_count: int
    record_count: int
    already_accepted: bool


def _workspace_id(ws: Path) -> str:
    try:
        manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AcceptCorpusRefused(f"project.json is missing or unreadable in {ws}") from exc
    value = manifest.get("registered_workspace_id") if isinstance(manifest, dict) else None
    if not isinstance(value, str) or not value.startswith("WSP-"):
        raise AcceptCorpusRefused(
            "project.json records no registered_workspace_id (WSP-...). Create the "
            "workspace with `nexus-scholar init` or `scholar-harness inception`."
        )
    return value


def _protocol_fingerprint(ws: Path) -> str:
    path = ws / "protocol.json"
    if not path.is_file():
        raise AcceptCorpusRefused(f"protocol.json not found in {ws}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return protocol_fingerprint(ResearchProtocol.model_validate(raw))


def _stable_sci_id(document: Document) -> str:
    """A record-derived ``SCI-`` id: the same record always gets the same id."""
    identity = {
        "title": document.title,
        "year": document.year,
        "doi": document.external_ids.doi,
        "authors": [a.family_name for a in document.authors],
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    return f"SCI-{int(digest[:12], 16):015d}"


def _verified_row(document: Document) -> dict[str, Any]:
    """The ``verified.json`` shape that ``batcher._rebuild_doc`` reads back."""
    eids = document.external_ids
    return {
        "workspace_id": document.workspace_id,
        "title": document.title,
        "year": document.year,
        "provider": document.provider,
        "provider_id": document.provider_id,
        "external_ids": {
            key: value
            for key, value in {
                "doi": eids.doi,
                "arxiv_id": eids.arxiv_id,
                "pubmed_id": eids.pubmed_id,
                "openalex_id": eids.openalex_id,
                "s2_id": eids.s2_id,
            }.items()
            if value
        },
        "abstract": document.abstract,
        "authors": [
            {"family_name": a.family_name, "given_name": a.given_name} for a in document.authors
        ],
        "venue": document.venue,
        "url": document.url,
    }


def import_ris(ws: Path, ris_path: Path) -> int:
    """Write ``literature/verified.json`` from a RIS export; return the row count."""
    verified = ws / "literature" / "verified.json"
    if verified.exists():
        raise AcceptCorpusRefused(
            f"{verified} already exists; remove it first to replace the corpus with {ris_path.name}"
        )
    if not ris_path.is_file():
        raise AcceptCorpusRefused(f"RIS file not found: {ris_path}")
    rows: dict[str, dict[str, Any]] = {}
    for document in RISImporter().parse(ris_path):
        document.workspace_id = _stable_sci_id(document)
        rows.setdefault(document.workspace_id, _verified_row(document))
    if not rows:
        raise AcceptCorpusRefused(f"{ris_path.name} contains no records")
    verified.parent.mkdir(parents=True, exist_ok=True)
    verified.write_text(json.dumps(list(rows.values()), indent=2), encoding="utf-8")
    append_event(
        ws,
        "CORPUS_IMPORTED",
        f"Imported {len(rows)} records from {ris_path.name} into literature/verified.json",
        inputs=[str(ris_path)],
        outputs=["literature/verified.json"],
        parameters={"format": "ris"},
        metrics={"records": len(rows)},
    )
    return len(rows)


def accept_corpus(
    workspace: Path | str,
    *,
    ris: Path | None = None,
    now: datetime | None = None,
) -> AcceptCorpusResult:
    """Build and accept the corpus snapshot for ``workspace``.

    Preconditions are checked before anything is written. Re-running on the
    same records and protocol is idempotent: the deterministic artifact id is
    already in the registry, and nothing new is published.
    """
    ws = Path(workspace).resolve()
    workspace_id = _workspace_id(ws)
    fingerprint = _protocol_fingerprint(ws)
    if ris is not None:
        import_ris(ws, Path(ris))

    verified = ws / "literature" / "verified.json"
    if not verified.is_file():
        raise AcceptCorpusRefused(
            f"{verified} not found; run discovery first or pass --ris <export.ris>"
        )
    rows = json.loads(verified.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise AcceptCorpusRefused(f"{verified} has no records")
    documents = [_rebuild_doc(row, f"SCI-{i:06d}") for i, row in enumerate(rows, start=1)]

    run_id = deterministic_id(
        IdentifierKind.RUN,
        workspace_id,
        {
            "operation": "accept-corpus",
            "protocol_fingerprint": fingerprint,
            "records_sha256": canonical_fingerprint(rows),
        },
    )
    built = build_corpus_snapshot_artifact(
        documents,
        workspace_id=workspace_id,
        run_id=run_id,
        protocol_fingerprint=fingerprint,
        created_at=now or datetime.now(UTC),
    )
    artifact = built.artifact
    registry = ws / "audit" / "artifact_registry.json"
    if registry.is_file():
        entries = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {})
        if artifact["artifact_id"] in entries:
            return AcceptCorpusResult(
                artifact["artifact_id"],
                len(artifact["data"]["studies"]),
                len(documents),
                already_accepted=True,
            )

    result = accept_artifact(
        ws,
        artifact,
        expected=AcceptanceContext(
            workspace_id=workspace_id,
            protocol_fingerprint=fingerprint,
            corpus_fingerprint=artifact["corpus_fingerprint"],
        ),
        actor="nexus-scholar-accept-corpus",
    )
    if not result.accepted:
        issues = "; ".join(f"{i.code}: {i.message}" for i in result.issues) or "no detail"
        raise AcceptCorpusRefused(f"the acceptance gate refused the snapshot ({issues})")
    return AcceptCorpusResult(
        artifact["artifact_id"],
        len(artifact["data"]["studies"]),
        len(documents),
        already_accepted=False,
    )
