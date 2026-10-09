"""E4 sealed golden fixture builder + seal check (harness-owned test code only).

Packet E4 (``docs/architecture/wp01_packet_e4_negative_proof_handoff.md``) needs
one small deterministic fixture workspace that already holds a complete,
accepted E1 -> E2 -> E3 chain.  Individual mutation tests copy this sealed
source tree to ``tmp_path``; no test ever mutates the sealed source.

What the fixture holds (handoff section 4):

* a registered protocol and corpus snapshot;
* accepted screening decisions;
* at least two accepted documents with distinct study/document identities;
* acquired PDF bytes and their recorded checksums;
* accepted E2 ``document_manifest`` records and extracted Markdown bytes;
* the E3 candidate sidecar, accepted index record, canonical audit event, and
  a queryable backend snapshot;
* a manifest of relative paths, canonical checksums, and expected outcomes.

How it is built (public surfaces only):

* protocol/corpus via the public ``scholar-protocol-kit`` /
  ``scholar-search-kit`` APIs (``ResearchProtocol``,
  ``build_corpus_snapshot_artifact``) plus the frozen acceptance gate
  (``accept_artifact``) -- the same honest composition the runtime-acceptance
  e2e suite uses;
* screening via the public harness agent-in-the-loop handoff
  (``cmd_prepare`` / ``cmd_collect``);
* extracted Markdown + PDF bytes written with fixed content (LF line endings
  forced via ``newline="\\n"`` so the seal is cross-platform for the bytes
  this builder owns);
* E2 via the public harness producer (``publish_document_manifest``);
* E3 via the public harness Stage 6 (``index_accepted_documents``) with the
  kit's documented hermetic embedder (``get_embedder("mock")``, pinned to
  dimension 384) and ``HF_HUB_OFFLINE`` / ``TRANSFORMERS_OFFLINE`` set, into a
  throwaway Chroma directory *outside* the workspace (tmp only, never
  ``workspace/rag/chroma_db``);
* backend snapshot via the kit's typed read-only verification surface
  (``ChromaVisibleSetReader``: ``visible_ids`` / ``visible_count`` /
  ``read_collection_metadata``) -- never a file open, never a row count from
  disk by this builder beyond that typed query.

Determinism note (explicit, not hidden): the bytes this builder writes are
fixed and sorted, but several *recorded* fields use wall-clock time at
generation (screening-batch ``created_at``, journal ``timestamp`` /
``event_id``, E3 sidecar ``run_id`` / ``created_at``, accepted-record
``accepted_at``).  Those fields are fixed the moment this fixture is generated
and are verified byte-for-byte by the seal afterwards.  The seal test does NOT
rebuild-from-scratch and compare bytes (fresh builds differ in those clock
fields); it verifies the committed tree matches its own ``seal_manifest.json``
(self-consistency, catches accidental edits) and the control tests prove
*replay* determinism (copy + re-run public entries yields the same
artifact/manifest/fingerprint identities via idempotent reuse).  Content
identities (study/document/chunk/manifest/fingerprint) are stable across
replays because the E2 payload hash and the E3 deterministic projection
exclude run/clock fields.

This module never imports a private helper (no ``_extraction_file_stem``,
no ``orchestrator._build_*``, no ``index_service._build_*``) and never
re-implements kit internals (no chunking, embedding, retrieval, or scoring
logic lives here).  The on-disk filename stem rule below is filesystem
resolution only (mirrors ``src/scholar_harness/orchestrator.py:122-139`` in
one line, cited, not imported): identity is always inherited from the
accepted manifest at use time, never read back out of a filename.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SEALED_SOURCE_DIR = REPO_ROOT / "tests" / "e2e" / "fixtures" / "e4_golden"

SEAL_VERSION = "e4-seal-v1"

WORKSPACE_ID = "WSP-" + "0123456789abcdef" * 2
SLUG = "evidence-synthesis"
CORPUS_RUN_ID = "RUN-e4-sealed-corpus"
SCREENING_REVIEWER = "human-reviewer-1"
SCREENING_TIMESTAMP = "2026-09-21T12:00:00Z"
CORPUS_CREATED_AT = datetime(2026, 9, 21, tzinfo=UTC)
CORPUS_COMMIT = "3" * 40

PROTOCOL_FIXTURE = (
    REPO_ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)

STUDY_SPECS: tuple[dict[str, str], ...] = (
    {
        "suffix": "1",
        "title": "Contract bound extraction alpha",
        "doi": "10.1000/e4-sealed-1",
    },
    {
        "suffix": "2",
        "title": "Contract bound extraction beta",
        "doi": "10.1000/e4-sealed-2",
    },
)

USABLE_BODY = (
    "## Abstract\n\n"
    + "This study reports a measured contract-bound extraction result. " * 12
    + "\n"
)

PDF_TEMPLATE = b"%PDF-1.7 e4 sealed bytes for "
PDF_PADDING = b"A" * 256 + b"\n"

SEALED_EXPECTED_COUNTS = {
    "accepted_documents": 2,
    "rejected_documents": 0,
    "visible_chunks": 2,
}

# Files/directories that are never part of the seal (runtime caches, bytecode,
# or the throwaway build store which lives outside the workspace anyway).
# Append-only/derived logs are also excluded: audit/journal.jsonl grows on
# every public entry (even idempotent replays log), INDEX.md is a derived
# workspace index refreshed on every log append, and run-reports/ gains one
# kit run report per indexing run.  The harness-side E2 publication record
# (literature/extraction_publications/) is excluded for the same reason: an
# idempotent replay rewrites it with idempotent=True while the accepted
# Contract artifact, registry entry, and E3 record stay byte-identical.
# project.json is excluded because every journal append refreshes its
# wall-clock updated_at (workspace identity itself stays sealed via the
# registry/manifest/accepted expected values).
# Sealing those bytes would make any replay fail the seal even though no
# evidence changed; their truthfulness is asserted separately per case
# (no new SUCCESS for altered chains).
_SEAL_IGNORE_PREFIXES = (
    "__pycache__/",
    ".pytest_cache/",
    "run-reports/",
    "literature/extraction_publications/",
)
_SEAL_IGNORE_NAMES = {".DS_Store", "Thumbs.db"}
_SEAL_IGNORE_EXACT = frozenset({"audit/journal.jsonl", "INDEX.md", "project.json"})


def _stem_of(record: dict[str, Any]) -> str:
    """Filesystem stem only (mirrors orchestrator.py:122-139, not imported).

    Prefers the included record's ``workspace_id`` (which carries the study
    id) over ``study_id``; never an identity source, only a filename.
    """

    idv = str(record.get("workspace_id") or record.get("study_id") or "")
    return (idv or "doc").replace("/", "_").replace(":", "_")


def _write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _sealable_files(workspace: Path) -> list[Path]:
    out: list[Path] = []
    for path in sorted(workspace.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(workspace).as_posix()
        if rel.startswith(_SEAL_IGNORE_PREFIXES):
            continue
        if rel in _SEAL_IGNORE_EXACT:
            continue
        if path.name in _SEAL_IGNORE_NAMES:
            continue
        # The throwaway real-Chroma build store never lives inside the
        # workspace (the builder indexes into a sibling tmp dir), but if a
        # caller points compute_seal at a workspace that does contain one,
        # its binary/unordered files are not sealed content.
        if rel == "rag/chroma_db" or rel.startswith("rag/chroma_db/"):
            continue
        if rel == "chroma_db" or rel.startswith("chroma_db/"):
            continue
        out.append(path)
    return out


def compute_seal(workspace: Path) -> dict[str, Any]:
    """Return ``{"files": {rel: sha}, "expected": {...}}`` for *workspace*."""

    workspace = Path(workspace).resolve()
    files = {
        p.relative_to(workspace).as_posix(): _file_sha256(p)
        for p in _sealable_files(workspace)
    }
    expected: dict[str, Any] = {}
    # Expected outcomes are read through public artifact shapes only; a
    # missing E2/E3 simply leaves those keys absent (control asserts presence).
    registry_path = workspace / "audit" / "artifact_registry.json"
    if registry_path.is_file():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            manifests = {
                artifact_id: entry
                for artifact_id, entry in (registry.get("artifacts") or {}).items()
                if isinstance(entry, dict)
                and entry.get("artifact_type") == "document_manifest"
            }
            if manifests:
                # The sealed fixture holds exactly one E2 manifest; if a
                # mutation legitimately added a second (E4-NEG-001's new E2),
                # the seal still records the sealed one via seal_manifest.json
                # (the copy under test is compared file-by-file, not by
                # "exactly one manifest" here).
                first_id = sorted(manifests)[0]
                expected["e2_artifact_ids"] = sorted(manifests)
                manifest_path = workspace / str(manifests[first_id].get("path", ""))
                if manifest_path.is_file():
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    expected["e2_artifact_id"] = str(
                        manifest.get("artifact_id", first_id)
                    )
                    expected["workspace_id"] = str(manifest.get("workspace_id", ""))
                    expected["protocol_fingerprint"] = str(
                        manifest.get("protocol_fingerprint", "")
                    )
                    expected["corpus_fingerprint"] = str(
                        manifest.get("corpus_fingerprint", "")
                    )
                    docs = (manifest.get("data") or {}).get("documents") or []
                    expected["document_ids"] = sorted(
                        str(d.get("document_id", "")) for d in docs
                    )
                    expected["study_ids"] = sorted(
                        str(d.get("study_id", "")) for d in docs
                    )
        except (OSError, UnicodeDecodeError, ValueError):
            pass
    accepted_path = workspace / "rag" / "index" / "accepted.json"
    if accepted_path.is_file():
        try:
            accepted = json.loads(accepted_path.read_text(encoding="utf-8"))
            for key in (
                "manifest_id",
                "index_fingerprint",
                "chunk_set_fingerprint",
                "configuration_fingerprint",
                "production_fingerprint",
            ):
                if isinstance(accepted.get(key), str):
                    expected[key] = str(accepted[key])
            if isinstance(accepted.get("counts"), dict):
                expected["counts"] = dict(accepted["counts"])
            if isinstance(accepted.get("parent_artifact_ref"), dict):
                expected["parent_artifact_ref"] = dict(accepted["parent_artifact_ref"])
        except (OSError, UnicodeDecodeError, ValueError):
            pass
    snapshot_path = workspace / "rag" / "backend_snapshot.json"
    if snapshot_path.is_file():
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            if isinstance(snapshot.get("visible_ids"), list):
                expected["visible_ids"] = sorted(
                    str(v) for v in snapshot["visible_ids"]
                )
                expected["visible_count"] = int(
                    snapshot.get("visible_count", len(snapshot["visible_ids"]))
                )
        except (OSError, UnicodeDecodeError, ValueError):
            pass
    return {"seal_version": SEAL_VERSION, "files": files, "expected": expected}


def check_seal(workspace: Path, seal: dict[str, Any] | None = None) -> dict[str, Any]:
    """Verify *workspace* matches *seal* (or its own seal_manifest.json).

    Returns the seal on success; raises ``AssertionError`` naming the first
    missing/mismatched/extra-sealed path on failure.  Extra *uncelebrated*
    files (e.g. a mutation's new E2 sidecar for NEG-001) do not fail this
    check -- per-case assertions own the "no partial E3 publication" claim.
    """

    workspace = Path(workspace).resolve()
    if seal is None:
        manifest_path = workspace / "seal_manifest.json"
        if not manifest_path.is_file():
            raise AssertionError(f"no seal_manifest.json at {manifest_path}")
        seal = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(seal, dict) or seal.get("seal_version") != SEAL_VERSION:
        raise AssertionError(
            f"unknown seal version: {seal.get('seal_version') if isinstance(seal, dict) else type(seal)}"
        )
    sealed_files = seal.get("files")
    if not isinstance(sealed_files, dict) or not sealed_files:
        raise AssertionError("seal carries no files")
    current = {
        p.relative_to(workspace).as_posix(): _file_sha256(p)
        for p in _sealable_files(workspace)
    }
    for rel, digest in sorted(sealed_files.items()):
        if rel not in current:
            raise AssertionError(f"sealed path missing: {rel}")
        if current[rel] != digest:
            raise AssertionError(f"sealed path changed: {rel}")
    return seal


def copy_sealed_to(destination: Path) -> Path:
    """Copy the sealed source tree to *destination* (never mutate the source).

    Verifies the source seal first so a test that runs against a dirty source
    fails loudly instead of proving nothing.
    """

    if not SEALED_SOURCE_DIR.is_dir():
        raise AssertionError(
            f"sealed source missing: {SEALED_SOURCE_DIR} (run e4_sealed_fixture build first)"
        )
    check_seal(SEALED_SOURCE_DIR)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / "ws"
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(SEALED_SOURCE_DIR, target, symlinks=False)
    return target


def make_live_reader(
    payload: dict[str, Any], visible_ids: list[str] | None = None
) -> Any:
    """Build an in-memory read-only verification reader for *payload*.

    Uses only the kit's typed ``VisibleRow`` surface (no Chroma files, no row
    counts from disk, no embedder, no writes).  *visible_ids* defaults to the
    payload's full declared set; pass a subset to model a corrupted backend
    (E4-NEG-006) without touching any file.
    """

    from scholar_rag.index_verifier import VisibleRow

    run_id = str(payload.get("run_id", ""))
    try:
        dimension = int((payload.get("embedder") or {}).get("dimension", 384))
    except (TypeError, ValueError):
        dimension = 384
    space = str((payload.get("backend") or {}).get("hnsw_space", "cosine"))
    wanted = set(visible_ids) if visible_ids is not None else None
    rows = []
    for chunk in payload.get("visible_chunks", []) or []:
        if not isinstance(chunk, dict):
            continue
        chunk_id = str(chunk.get("chunk_id", ""))
        if wanted is not None and chunk_id not in wanted:
            continue
        rows.append(
            VisibleRow(
                row_key=f"{run_id}#{chunk_id}",
                chunk_id=chunk_id,
                document_id=str(chunk.get("document_id", "")),
                study_id=str(chunk.get("study_id", "")),
                embedding_dimension=dimension,
                stored_text=None,
            )
        )

    class _InMemoryReader:
        def __init__(self, rows: list[Any], space: str) -> None:
            self._rows = list(rows)
            self._space = space

        def visible_ids(self) -> list[str]:
            return sorted(row.chunk_id for row in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    return _InMemoryReader(rows, space)


def build_sealed_fixture(dest: Path) -> dict[str, Any]:
    """Build the sealed E1->E2->E3 workspace at *dest* (public surfaces only).

    Hermetic: deterministic mock embedder, ``HF_HUB_OFFLINE`` /
    ``TRANSFORMERS_OFFLINE`` forced, all filesystem effects confined to *dest*
    plus one throwaway sibling Chroma build dir (removed afterwards; only its
    typed snapshot is sealed).  Returns the seal dict.
    """

    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.identity import build_corpus_snapshot_artifact
    from scholar_search.models import Author, Document, ExternalIds

    from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
    from scholar_harness.extraction_producer import (
        index_accepted_documents,
        publish_document_manifest,
    )
    from scholar_harness.screening.batcher import cmd_prepare
    from scholar_harness.screening.collector import cmd_collect

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    dest = Path(dest).resolve()
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    workspace = dest

    _write_text_lf(
        workspace / "project.json",
        json.dumps(
            {"project_id": SLUG, "registered_workspace_id": WORKSPACE_ID, "stats": {}},
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    protocol = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    _write_text_lf(
        workspace / "protocol.json",
        json.dumps(protocol, indent=2, sort_keys=True) + "\n",
    )
    protocol_fp = canonical_fingerprint(ResearchProtocol.model_validate(protocol))

    sources = [
        Document(
            title=spec["title"],
            year=2026,
            provider="crossref",
            provider_id=f"e4-sealed-record-{spec['suffix']}",
            external_ids=ExternalIds(doi=spec["doi"]),
            authors=[Author("Reviewer")],
            abstract="Abstract sentence. " * 5,
        )
        for spec in STUDY_SPECS
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WORKSPACE_ID,
        run_id=CORPUS_RUN_ID,
        protocol_fingerprint=protocol_fp,
        created_at=CORPUS_CREATED_AT,
        commit=CORPUS_COMMIT,
    )
    corpus = built.artifact
    result = accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=WORKSPACE_ID,
            protocol_fingerprint=protocol_fp,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    )
    if not result.accepted:
        raise AssertionError(
            f"sealed corpus not accepted: {[i.code for i in result.issues]}"
        )

    studies = corpus["data"]["studies"]
    literature = workspace / "literature"
    literature.mkdir(parents=True, exist_ok=True)
    _write_text_lf(
        literature / "verified.json",
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": spec["doi"]},
                    "abstract": "Abstract sentence. " * 5,
                }
                for study, spec in zip(studies, STUDY_SPECS)
            ],
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    _write_text_lf(
        screening / "batch_001_decisions.json",
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": SCREENING_REVIEWER,
                "timestamp": SCREENING_TIMESTAMP,
                "decisions": [
                    {
                        "workspace_id": study["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": "Meets the frozen inclusion criteria.",
                        "parent_decision_ids": [],
                    }
                    for study in studies
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    cmd_collect(workspace)

    included = json.loads((literature / "included.json").read_text(encoding="utf-8"))
    if len(included) != len(STUDY_SPECS):
        raise AssertionError(
            f"sealed screening admitted {len(included)}, expected {len(STUDY_SPECS)}"
        )

    pdfs = workspace / "pdfs"
    pdfs.mkdir(parents=True, exist_ok=True)
    for record in included:
        stem = _stem_of(record)
        (pdfs / f"{stem}.pdf").write_bytes(
            PDF_TEMPLATE + stem.encode("utf-8") + b"\n" + PDF_PADDING
        )

    extracted = workspace / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)
    for record in included:
        stem = _stem_of(record)
        _write_text_lf(
            extracted / f"{stem}.md",
            "---\n"
            f'workspace_id: "{record.get("workspace_id", "")}"\n'
            f'doi: "{(record.get("external_ids") or {}).get("doi", "")}"\n'
            f"title: {json.dumps(record.get('title') or 'Untitled', ensure_ascii=False)}\n"
            'extraction_engine: "metadata"\n'
            "---\n\n" + USABLE_BODY,
        )

    outcome = publish_document_manifest(workspace)
    if not outcome.accepted:
        raise AssertionError(f"sealed E2 not accepted: {outcome.refusal}")

    import scholar_harness.orchestrator as orch_module
    from scholar_rag.embedder import get_embedder as kit_get_embedder

    mock = kit_get_embedder("mock")
    mock.dimension = 384
    previous = orch_module.get_embedder
    orch_module.get_embedder = lambda **_: mock  # type: ignore[assignment]
    import tempfile

    build_chroma = Path(tempfile.mkdtemp(prefix="e4-seal-build-chroma-"))
    try:
        index_result = index_accepted_documents(workspace, chroma_dir=build_chroma)
    finally:
        orch_module.get_embedder = previous  # type: ignore[assignment]
    if str(index_result.get("status")) != "SUCCESS":
        raise AssertionError(f"sealed E3 not SUCCESS: {index_result}")
    acceptance = index_result.get("acceptance") or {}
    if not acceptance.get("accepted"):
        raise AssertionError(f"sealed E3 not accepted: {acceptance}")

    # Typed backend snapshot (read-only verification surface only).
    from scholar_rag.index_verifier import ChromaVisibleSetReader

    reader = ChromaVisibleSetReader(
        db_path=str(build_chroma), collection_name="scholar_docs"
    )
    try:
        visible_ids = sorted(str(v) for v in reader.visible_ids())
        visible_count = int(reader.visible_count())
        try:
            metadata = dict(reader.read_collection_metadata() or {})
        except Exception:
            metadata = {}
    finally:
        shutil.rmtree(build_chroma, ignore_errors=True)

    sidecars = sorted((workspace / "rag" / "index").rglob("IDX-*.json"))
    if len(sidecars) != 1:
        raise AssertionError(f"sealed E3 sidecars: {[str(p) for p in sidecars]}")
    sidecar_payload = json.loads(sidecars[0].read_text(encoding="utf-8"))
    sidecar_visible = sorted(
        str(c.get("chunk_id", ""))
        for c in sidecar_payload.get("visible_chunks", []) or []
    )
    if visible_ids != sidecar_visible:
        raise AssertionError(f"live set {visible_ids} != sidecar {sidecar_visible}")

    _write_text_lf(
        workspace / "rag" / "backend_snapshot.json",
        json.dumps(
            {
                "snapshot_version": "e4-backend-snapshot-v1",
                "note": (
                    "Hermetic queryable backend snapshot (typed verification surface only). "
                    "Not authoritative state; the accepted record plus sidecar govern. "
                    "Tests rebuild an in-memory reader from this file, never Chroma files."
                ),
                "collection": "scholar_docs",
                "visible_ids": visible_ids,
                "visible_count": visible_count,
                "collection_metadata": metadata,
                "manifest_id": str(sidecar_payload.get("manifest_id", "")),
                "index_fingerprint": str(sidecar_payload.get("index_fingerprint", "")),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    seal = compute_seal(workspace)
    _write_text_lf(
        workspace / "seal_manifest.json",
        json.dumps(
            {
                "seal_version": SEAL_VERSION,
                "note": (
                    "E4 sealed-fixture seal (harness-owned test helper, not authoritative "
                    "evidence). Files map relative POSIX paths to sha256 digests; expected "
                    "carries the normal-run identities/outcomes the control test replays."
                ),
                "files": seal["files"],
                "expected": seal["expected"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    # Re-read so the seal covers itself deterministically for the check below.
    seal = compute_seal(workspace)
    _write_text_lf(
        workspace / "seal_manifest.json",
        json.dumps(
            {
                "seal_version": SEAL_VERSION,
                "note": (
                    "E4 sealed-fixture seal (harness-owned test helper, not authoritative "
                    "evidence). Files map relative POSIX paths to sha256 digests; expected "
                    "carries the normal-run identities/outcomes the control test replays."
                ),
                "files": {
                    k: v for k, v in seal["files"].items() if k != "seal_manifest.json"
                },
                "expected": seal["expected"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    check_seal(workspace)
    return check_seal(workspace)


if __name__ == "__main__":  # pragma: no cover - explicit fixture generation only
    import argparse

    parser = argparse.ArgumentParser(description="Build the E4 sealed golden fixture.")
    parser.add_argument("--dest", default=str(SEALED_SOURCE_DIR))
    args = parser.parse_args()
    build_sealed_fixture(Path(args.dest))
    print(f"sealed fixture built at {args.dest}")
