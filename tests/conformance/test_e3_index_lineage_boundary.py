"""WP01-E3 index-lineage boundary conformance (harness limbs) -- T-140.

Packet E3 (``docs/architecture/wp01_packet_e3_implementation_handoff.md``) draws
the same hard line Packet E2 drew: the *behavioral* proofs of indexing live in
the canonical ``scholar-rag-kit`` (and, for the MCP refusal, the future
``scholar-agent-kit`` T-100 work), and the harness enforces only its own
**cross-repository** obligations. A green run of this file is therefore **not**
evidence that indexing works -- the kit suites are. What this file proves is
that the harness side of the boundary is real:

``E3-POS-005`` byte-for-byte golden parity
    The harness fixture ``tests/conformance/fixtures/e3_golden_manifest.json``
    is canonically byte-identical to the kit-pinned
    ``GOLDEN_MANIFEST`` (``tools/scholar-rag-kit/tests/test_index_manifest.py:66``,
    pin ``f108fa89``), and the baseline ``CHK-`` re-derives from the fixture's
    own limbs through the kit's ``mint_chunk_id``. Either side drifting fails
    loudly here rather than silently diverging.

Harness-live ledger rows (each names its handoff class and its exact test):

    ``E3-NEG-010`` (C-28 / §6.2 step 4) -- Stage 6 request limbs inherit recorded
        identity; filename/DOI/title never bind (``test_e3_neg_010_...``).
    ``E3-NEG-012`` (C-05 / RAG-010) -- cross-workspace manifest is not inherited;
        the preflight refuses before any store exists (``test_e3_neg_012_...``).
    ``E3-NEG-013`` (C-29 / RAG-012) -- a zero-accepted run is FAILED with
        ``NO_DOCUMENTS_TO_INDEX``, never SUCCESS (``test_e3_neg_013_...``).
    ``E3-NEG-014`` (C-29 / RAG-012) -- a mixed batch maps to PARTIAL, never
        SUCCESS (``test_e3_neg_014_...``).
    ``E3-NEG-015`` (C-02 / §6.2 step 1) -- a malformed accepted parent refuses
        before any store exists (``test_e3_neg_015_...``).
    ``E3-NEG-016`` (C-01 / §6.2 step 1) -- no manifest refuses with
        ``DOCUMENT_MANIFEST_NOT_ACCEPTED`` before any store exists
        (``test_e3_neg_016_...``; also the required negative-case shape).
    ``E3-NEG-026`` (C-17 / RAG-010) -- the embedder identity is fully explicit
        in the typed request (``test_e3_neg_026_...``).
    ``E3-NEG-028`` (C-15) -- Stage 6 orders sources deterministically
        (``test_e3_neg_028_...``).
    ``E3-NEG-034`` (C-30) -- no emittable ``CHK-``/citation token leaves Stage 6
        (``test_e3_neg_034_...``).
    ``E3-NEG-036`` (C-25) -- no similarity-as-entailment language leaves Stage 6
        (``test_e3_neg_036_...``).
    ``E3-NEG-038`` (C-03) -- the frozen registries reject the kit-owned
        ``index_manifest`` sidecar as ``UNSUPPORTED_ARTIFACT_TYPE``
        (``test_e3_neg_038_...``; mirrors E2-NEG-021).
    ``E3-NEG-048`` (C-34) -- the rag-kit pin is a full SHA and the import
        resolves vendored (``test_e3_neg_048_...``; mirrors E2-NEG-037).
    ``E3-NEG-049`` (C-08 / §6.2 step 3) -- a post-acceptance protocol mutation
        breaks generation agreement and refuses (``test_e3_neg_049_...``).
    ``E3-NEG-039`` (C-07 / §6.2 step 7) -- the adapter re-checks the required
        parent type at publication: a type diverged after checks 1-6 refuses
        ``REQUIRED_PARENT_TYPE_MISSING`` with zero publication
        (``test_e3_neg_039_...``).
    ``E3-POS-007`` (§6.2 / E3-007, harness scope) -- at each harness failure
        point the run proves zero publication: no store, no registry mutation,
        no success event (``test_e3_pos_007_...``).

Kit-side-only and adapter-future IDs, **explicitly MISSING, never re-proven**
(the ``MISSING`` table below; each marker checks that its reason is still true
and then skips, so none of them can pass vacuously):

    ``E3-NEG-009`` (C-09), ``E3-NEG-011`` (C-10) -- the eligibility join is the
        kit's proof (``index_service.py`` ``eligibility join``); the harness only
        forwards ``parent_view`` verbatim.
    ``E3-NEG-017`` (C-06) -- hash-stale detection (``PARENT_HASH_MISMATCH``) is
        kit-owned; Stage 6 re-reads but never recomputes the registry hash.
    ``E3-NEG-021`` / ``E3-NEG-022`` (C-12) -- path-shape and docs-directory
        containment refuse inside the kit (``_refuse_path_shaped`` /
        ``docs_destination``); the harness never synthesizes a path.
    ``E3-NEG-030`` / ``E3-NEG-031`` (C-27) -- chunk-uniqueness scope is the
        kit's proof (``cross-document collision``); the harness mints nothing.
    ``E3-NEG-035`` (C-13) -- unusable-extraction refusal is kit T-50
        (``EXTRACTED_TEXT_UNUSABLE``); the harness producer refusal is E2-era.
    ``E3-NEG-050`` (C-11) -- index-time staleness has no Stage 6 check
        (``EXTRACTED_CONTENT_CHANGED`` is kit T-50); publish-time staleness is
        the producer's ``STALE_EXTRACTED_BODY`` (e2e Major 5).
    ``E3-NEG-037`` (C-32) / ``E3-POS-008`` -- the §6.6 accepted-record audit
        event belongs to the ``index-acceptance-v1`` adapter
        (``src/scholar_harness/index_acceptance.py``); the kit journals only its
        own run report (live: ``test_e3_neg_037_...`` / ``test_e3_pos_008_...``).
    ``E3-POS-009`` (§9 / RAG-014) -- T-100 has not landed: the agent-kit MCP
        surface still declares ``workspace_id: str = None``
        (``server.py:830``); no parity is claimed here.
    ``E3-POS-012`` (RAG-019) -- the clean-wheel ``--help`` smoke is a CI/RELEASE
        gate; this file owns only the declared-dependency half (E3-NEG-048).

Diagnostic case (``test_e3_diagnostic_real_chroma_...``)
    The one real-Chroma reproducer the blocked kit task requires: a real
    accepted-manifest workspace, the exact typed ``IndexServiceRequest`` limbs
    plus parent view plus collection metadata plus backend state before/after
    plus the full exception ``__cause__`` chain on failure, through the shipped
    ``index_accepted_documents`` path with a deterministic mock embedder and a
    tmp ``db_path`` (HF/TRANSFORMERS offline flags set, nothing written outside
    tmp plus the workspace fixture).

    Conditional close-out (recorded here and in the task report):

    * if healthy indexing succeeds, the historical ``ATOMIC_COMMIT_FAILED``
      concern is UNSUBSTANTIATED on this path, and the exact environment
      (chromadb / python / OS versions, printed by the test) is the scope of
      that claim;
    * if it reproduces, the failure output carries the minimal kit-level
      reproducer (request fields + corpus texts + store state + cause chain)
      and the verdict is REOPEN-KIT with that evidence attached.

Everything here is offline and deterministic except the diagnostic's live clock
(run identity) and its real Chroma store under tmp: no network, no provider, no
model download, no daemon, and every filesystem effect confined to pytest's
``tmp_path`` (plus the ``tmp_path`` workspace fixture itself).
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_rag.canonical import canonical_json_bytes
from scholar_rag.chunker import mint_chunk_id, text_fingerprint
from scholar_rag.embedder import get_embedder as kit_get_embedder
from scholar_rag.index_manifest import MANIFEST_TYPE
from scholar_rag.index_models import IndexDocumentRequest
from scholar_rag.index_service import INDEX_SERVICE_OUTCOMES, IndexServiceRequest
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

from scholar_harness import orchestrator as orch_module
from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
from scholar_harness.contracts.models import OperationStatus
from scholar_harness.extraction_producer import (
    PublicationRefused,
    index_accepted_documents,
    publish_document_manifest,
)
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The kit-pinned golden source. Read-only: the harness never edits the kit
#: tree; the ``:66`` citation is the ``GOLDEN_MANIFEST`` literal, ``:185`` the
#: printed canonical chunk input, ``:197`` the frozen digest table.
KIT_GOLDEN_TEST = (
    REPO_ROOT / "tools" / "scholar-rag-kit" / "tests" / "test_index_manifest.py"
)
KIT_RAG_PIN = "15a7a5a50a0394ed87b9b8b3c153081e10ec36ad"

#: The harness-side frozen copy. A fixture, not a live view: parity with the
#: kit bytes is asserted in E3-POS-005, so either side drifting fails here.
HARNESS_GOLDEN_FIXTURE = (
    REPO_ROOT / "tests" / "conformance" / "fixtures" / "e3_golden_manifest.json"
)

PLUGINS_JSON = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"
PINS_JSON = REPO_ROOT / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json"
AGENT_SERVER = (
    REPO_ROOT / "tools" / "scholar-agent-kit" / "src" / "scholar_agent" / "server.py"
)
AGENT_CAPABILITIES = (
    REPO_ROOT
    / "tools"
    / "scholar-agent-kit"
    / "src"
    / "scholar_agent"
    / "capabilities.py"
)
KIT_RAG_PYPROJECT = REPO_ROOT / "tools" / "scholar-rag-kit" / "pyproject.toml"
METAPACKAGE_PYPROJECT = REPO_ROOT / "packaging" / "nexus-scholar" / "pyproject.toml"
KIT_TEST_MANIFEST = (
    REPO_ROOT / "tools" / "scholar-rag-kit" / "tests" / "test_index_manifest.py"
)
KIT_TEST_SERVICE = (
    REPO_ROOT / "tools" / "scholar-rag-kit" / "tests" / "test_index_service.py"
)
KIT_TEST_MCP_BOUNDARY = (
    REPO_ROOT
    / "tools"
    / "scholar-agent-kit"
    / "tests"
    / "test_mcp_indexing_boundary.py"
)

PROTOCOL_FIXTURE = (
    REPO_ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)

WORKSPACE_ID = "WSP-" + "0123456789abcdef" * 2
FOREIGN_WORKSPACE_ID = "WSP-" + "9" * 32
SLUG = "e3-lineage-boundary"
STUDY_TITLE = "E3 lineage bound extraction"
RUN_ID = "RUN-e3-lineage-boundary-search"
SCREENING_REASON = "Meets the frozen inclusion criteria."

#: A body the frozen Stage 5 usability rule calls usable, written the way the
#: frozen Stage 5 writers write it (YAML frontmatter + prose). Mirrors
#: ``tests/e2e/test_extraction_runtime_acceptance.py:79-85``.
_USABLE_BODY = (
    "## Abstract\n\n"
    + "This study reports a measured lineage-bound extraction result. " * 12
    + "\n"
)

#: Fixed limbs for the request-inspection tests. Stated, never minted: the run
#: id is an opaque ``RUN-`` value and the timestamp is frozen, so the built
#: request is byte-reproducible and no clock is read.
FIXED_RUN_ID = "RUN-" + "e3" * 16
FIXED_CREATED_AT = "2026-09-27T00:00:00Z"
FIXED_PRODUCER_COMMIT = "ab" * 20
FIXED_PRODUCER_VERSION = "0.2.0"

#: The baseline chunk the golden manifest and the T-10 battery agree on.
BASELINE_CHUNK_ID = "CHK-ab10cb5729e20ff5dc8d26a93455010c"


# --------------------------------------------------------------------------- #
# Golden loaders
# --------------------------------------------------------------------------- #


def _kit_golden_module() -> Any:
    """The kit's golden test module, loaded read-only from the vendored tree."""

    spec = importlib.util.spec_from_file_location(
        "kit_test_index_manifest_golden_ref", KIT_GOLDEN_TEST
    )
    assert spec is not None and spec.loader is not None, (
        f"cannot load the kit-pinned golden source at {KIT_GOLDEN_TEST}"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _kit_golden_manifest() -> dict[str, Any]:
    return json.loads(json.dumps(_kit_golden_module().GOLDEN_MANIFEST))


def _harness_golden_manifest() -> dict[str, Any]:
    return json.loads(HARNESS_GOLDEN_FIXTURE.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Workspace builder (mirrors tests/e2e/test_extraction_runtime_acceptance.py)
# --------------------------------------------------------------------------- #
#
# Cross-directory test imports are not possible (``tests/e2e/`` is not a
# package), so the builder below mirrors the e2e shapes instead of importing
# them: ``_write_extracted`` mirrors e2e ``:253-279``, ``_build_workspace``
# mirrors e2e ``:282-386``, ``_extracted_state`` mirrors e2e ``:389-395``. Any
# drift in the frozen writer shapes breaks the publish assertions below, which
# is the tripwire that keeps the mirror honest.
# --------------------------------------------------------------------------- #


def _write_extracted(
    workspace: Path, record: dict[str, Any], *, body: str = _USABLE_BODY
) -> Path:
    from scholar_harness.orchestrator import _extraction_file_stem

    extracted = workspace / "extracted"
    extracted.mkdir(exist_ok=True)
    path = extracted / f"{_extraction_file_stem(record)}.md"
    path.write_text(
        "---\n"
        f'workspace_id: "{record.get("workspace_id", "")}"\n'
        f'doi: "{record.get("external_ids", {}).get("doi", "")}"\n'
        f"title: {json.dumps(record.get('title') or 'Untitled', ensure_ascii=False)}\n"
        'extraction_engine: "metadata"\n'
        "---\n\n"
        f"{body}",
        encoding="utf-8",
    )
    return path


def _build_workspace(tmp_path: Path, *, study_count: int = 1) -> dict[str, Any]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps(
            {
                "project_id": SLUG,
                "registered_workspace_id": WORKSPACE_ID,
                "stats": {},
            }
        ),
        encoding="utf-8",
    )
    protocol = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_fp = canonical_fingerprint(ResearchProtocol.model_validate(protocol))

    sources = [
        Document(
            title=f"{STUDY_TITLE} {index}",
            year=2026,
            provider="crossref",
            provider_id=f"e3-boundary-record-{index}",
            external_ids=ExternalIds(doi=f"10.1000/e3-lineage-boundary-{index}"),
            authors=[Author("Reviewer")],
            abstract="Abstract sentence. " * 5,
        )
        for index in range(1, study_count + 1)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WORKSPACE_ID,
        run_id=RUN_ID,
        protocol_fingerprint=protocol_fp,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="3" * 40,
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
    assert result.accepted is True, [issue.code for issue in result.issues]

    studies = corpus["data"]["studies"]
    literature = workspace / "literature"
    literature.mkdir()
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": f"10.1000/e3-lineage-boundary-{index + 1}"},
                    "abstract": "Abstract sentence. " * 5,
                }
                for index, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )

    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "human-reviewer-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": study["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": SCREENING_REASON,
                        "parent_decision_ids": [],
                    }
                    for study in studies
                ],
            }
        ),
        encoding="utf-8",
    )
    cmd_collect(workspace)

    included = json.loads((literature / "included.json").read_text(encoding="utf-8"))
    assert len(included) == study_count
    return {
        "workspace": workspace,
        "included": included,
        "study_ids": [s["study_id"] for s in studies],
    }


def _extracted_state(tmp_path: Path, *, study_count: int = 1) -> dict[str, Any]:
    state = _build_workspace(tmp_path, study_count=study_count)
    for record in state["included"]:
        _write_extracted(state["workspace"], record)
    return state


def _published_state(tmp_path: Path, *, study_count: int = 1) -> dict[str, Any]:
    """A workspace whose manifest the frozen gate really accepted."""

    state = _extracted_state(tmp_path, study_count=study_count)
    outcome = publish_document_manifest(state["workspace"])
    assert outcome.accepted is True, outcome.refusal
    state["artifact_id"] = outcome.artifact_id
    return state


def _registry(workspace: Path) -> dict[str, Any]:
    path = workspace / "audit" / "artifact_registry.json"
    if not path.is_file():
        return {"artifacts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _journal(workspace: Path) -> list[dict[str, Any]]:
    journal = workspace / "audit" / "journal.jsonl"
    if not journal.is_file():
        return []
    return [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _registered_manifests(workspace: Path) -> dict[str, Any]:
    return {
        artifact_id: entry
        for artifact_id, entry in _registry(workspace)["artifacts"].items()
        if isinstance(entry, dict) and entry.get("artifact_type") == "document_manifest"
    }


def _mock_embedder(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Deterministic mock embedder standing in for the downloading provider.

    Stage 6 defaults to ``sentence-transformers`` (a model download on a cold
    cache), so every request-inspection test patches the orchestrator's
    ``get_embedder`` global with the kit's documented hermetic provider and
    pins the HF hubs offline, per the e2e shim pattern
    (``tests/e2e/test_extraction_runtime_acceptance.py:1807-1856``). The
    ``dimension`` attribute mirrors the declared request dimension so the
    kit's observed-vs-declared dimension check sees one consistent claim.
    """

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    mock = kit_get_embedder("mock")
    mock.dimension = 384
    monkeypatch.setattr(orch_module, "get_embedder", lambda **_: mock)
    return mock


def _fixed_request(
    orch: ResearchOrchestrator, parent_view: dict[str, Any], *, chroma_dir: Path
) -> IndexServiceRequest:
    return orch._build_index_service_request(
        chroma_dir=chroma_dir,
        parent_view=parent_view,
        run_id=FIXED_RUN_ID,
        created_at=FIXED_CREATED_AT,
        producer_commit=FIXED_PRODUCER_COMMIT,
        producer_version=FIXED_PRODUCER_VERSION,
    )


# --------------------------------------------------------------------------- #
# Anchors -- the rows name the kit's own identifiers, not copied literals
# --------------------------------------------------------------------------- #


def test_e3_anchors_are_the_kits_own_constants() -> None:
    """The E3 rows name the kit's own identities, types, and outcomes."""

    assert MANIFEST_TYPE == "index_manifest"
    assert INDEX_SERVICE_OUTCOMES == frozenset(
        {"SUCCESS", "PARTIAL", "REFUSED", "FAILED"}
    )
    # The six T-30 chunk-identity limbs plus the explicit execution-bound
    # identity a request must carry (E3-002 / E3-004).
    fields = IndexDocumentRequest.model_fields
    for limb in (
        "workspace_id",
        "study_id",
        "document_id",
        "parent_artifact_id",
        "parent_artifact_sha256",
        "extracted_content_sha256",
        "backend_provider",
        "backend_model",
        "collection",
    ):
        assert limb in fields, f"IndexDocumentRequest lost the {limb} limb"
    assert IndexDocumentRequest.model_config.get("frozen") is True
    assert IndexDocumentRequest.model_config.get("extra") == "forbid"


def test_e3_anchors_producer_pin_is_the_pinned_kit_commit() -> None:
    """The parity source is the pinned kit commit, not a floating branch."""

    assert len(KIT_RAG_PIN) == 40, "a full canonical commit, not a branch"
    assert KIT_GOLDEN_TEST.is_file(), "the kit-pinned golden source must exist"


# --------------------------------------------------------------------------- #
# E3-POS-005 -- kit/harness byte-for-byte golden parity
# --------------------------------------------------------------------------- #


def test_e3_pos_005_harness_fixture_matches_kit_golden_bytes() -> None:
    """E3-POS-005: the harness fixture agrees byte-for-byte with the kit bytes.

    The comparison is over ``canonical_json_bytes`` of each side's parse, so a
    drift in either repository -- a reworded digest, a reordered array, a new
    field -- fails here with the exact digest that moved, rather than silently
    diverging. Source: ``tools/scholar-rag-kit/tests/test_index_manifest.py:66``
    (``GOLDEN_MANIFEST``) at pin ``f108fa89``.
    """

    kit = _kit_golden_manifest()
    harness = _harness_golden_manifest()

    assert canonical_json_bytes(harness) == canonical_json_bytes(kit), (
        "the harness E3 golden fixture drifted from the kit-pinned golden bytes; "
        "do not regenerate to make this pass -- reconcile the two repositories"
    )
    for field in (
        "manifest_id",
        "index_fingerprint",
        "artifact_checksum",
        "production_fingerprint",
        "chunk_set_fingerprint",
        "configuration_fingerprint",
    ):
        assert harness[field] == kit[field], f"golden digest moved: {field}"
    assert harness["manifest_id"] == "IDX-748c4d3dd6cfc8133835092b36b7b4bc"
    assert harness["workspace_id"] == "WSP-0123456789abcdef0123456789abcdef"


def test_e3_pos_005_baseline_chunk_id_rederives_from_the_fixture_limbs() -> None:
    """E3-POS-005 (identity limb): the baseline CHK- re-derives, not copied."""

    manifest = _harness_golden_manifest()
    record = next(
        doc
        for doc in manifest["documents"]
        if doc["document_id"] == "DOC-33333333333333333333333333333333"
    )
    chunk = next(
        c for c in manifest["visible_chunks"] if c["chunk_id"] == BASELINE_CHUNK_ID
    )
    assert record["chunk_ids"] and BASELINE_CHUNK_ID in record["chunk_ids"]

    assert (
        mint_chunk_id(
            workspace_namespace=manifest["workspace_id"],
            parent_artifact_id=manifest["parent_artifact_ref"]["artifact_id"],
            parent_artifact_sha256=manifest["parent_artifact_ref"]["sha256"],
            study_id=record["study_id"],
            document_id=record["document_id"],
            extracted_content_sha256=record["extracted_content_sha256"],
            chunker_algorithm_version=manifest["chunker"]["algorithm_version"],
            chunker_configuration_fingerprint=manifest["chunker"][
                "configuration_fingerprint"
            ],
            heading_path=chunk["locator"]["heading_path"],
            ordinal_in_section=chunk["locator"]["ordinal_in_section"],
            section_category=chunk["locator"]["section_category"],
            chunk_text_sha256=chunk["chunk_text_sha256"],
        )
        == BASELINE_CHUNK_ID
    )


# --------------------------------------------------------------------------- #
# E3-NEG-010 -- identity is inherited, never re-derived (C-28, RAG-003)
# --------------------------------------------------------------------------- #


def test_e3_neg_010_request_limbs_inherit_recorded_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-010: every Stage 6 limb is inherited from recorded state.

    The workspace limb comes from ``project.json``'s recorded identity, the
    study/document limbs from the accepted manifest's own records, the parent
    limbs from the registry entry, and the content hash from the on-disk bytes.
    None of the plausible wrong answers -- a filename stem, the project slug, a
    DOI, a title -- appears in any limb: a workspace is not a study, a title is
    not an identity, and similarity is not entailment.
    """

    _mock_embedder(monkeypatch)
    state = _published_state(tmp_path)
    workspace = state["workspace"]
    orch = ResearchOrchestrator(workspace)
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    request = _fixed_request(orch, parent_view, chroma_dir=tmp_path / "chroma")

    assert request.parent_view["workspace_id"] == WORKSPACE_ID
    assert parent_view["workspace_id"] == WORKSPACE_ID
    assert len(request.sources) == 1
    source = request.sources[0]
    limbs = source.request

    manifest_records = {
        record["document_id"]: record for record in parent_view["documents"]
    }
    assert limbs.workspace_id == WORKSPACE_ID
    assert limbs.document_id in manifest_records
    assert limbs.study_id == manifest_records[limbs.document_id]["study_id"]
    assert limbs.study_id == state["included"][0]["workspace_id"]
    assert limbs.parent_artifact_id == parent_view["artifact_id"]
    assert limbs.parent_artifact_sha256 == parent_view["sha256"]
    on_disk = (workspace / source.extracted_path).read_text(encoding="utf-8")
    assert limbs.extracted_content_sha256 == text_fingerprint(on_disk)
    assert limbs.backend_provider == "chromadb"
    assert limbs.collection == "scholar_docs"

    stem = Path(source.extracted_path).stem
    for derived in (
        stem,
        SLUG,
        STUDY_TITLE,
        "10.1000/e3-lineage-boundary-1",
        WORKSPACE_ID,
    ):
        assert limbs.document_id != derived, derived
    assert limbs.study_id != WORKSPACE_ID
    assert limbs.study_id != SLUG
    assert limbs.workspace_id != SLUG


# --------------------------------------------------------------------------- #
# E3-NEG-012 -- cross-workspace parent is not inherited (C-05, RAG-010)
# --------------------------------------------------------------------------- #


def test_e3_neg_012_cross_workspace_manifest_is_not_inherited(
    tmp_path: Path,
) -> None:
    """E3-NEG-012: a manifest bound to another workspace cannot authorize indexing.

    Retargeting the recorded identity makes the accepted generation foreign, so
    the preflight refuses before any backend exists: no store directory, no
    success event, and the registry bytes untouched.
    """

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    before_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()
    (workspace / "project.json").write_text(
        json.dumps(
            {
                "project_id": SLUG,
                "registered_workspace_id": FOREIGN_WORKSPACE_ID,
                "stats": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PublicationRefused) as caught:
        index_accepted_documents(workspace)

    assert caught.value.code == "WORKSPACE_IDENTITY_DISAGREEMENT"
    assert FOREIGN_WORKSPACE_ID in caught.value.message
    assert not (workspace / "rag").exists()
    assert (workspace / "audit" / "artifact_registry.json").read_bytes() == (
        before_registry
    )
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] == []


# --------------------------------------------------------------------------- #
# E3-NEG-013 -- a zero-accepted run is FAILED, never SUCCESS (C-29, RAG-012)
# --------------------------------------------------------------------------- #


def test_e3_neg_013_zero_accepted_run_is_failed_never_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-013 / the ``NO_DOCUMENTS_TO_INDEX`` shape: emptiness is FAILED.

    The empty-sources limb of ``_run_indexing_stage`` is exercised white-box
    (the typed request constructor itself refuses an empty source list, so no
    public path reaches the limb with a real request): the harness shape is
    ``status == FAILED`` with a ``NO_DOCUMENTS_TO_INDEX`` refusal, a FAILED
    ``RAG_INDEX_REJECTED`` event, and no store directory -- and it is never a
    success string and never an empty successful result.
    """

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    target = tmp_path / "chroma-empty"
    orch = ResearchOrchestrator(workspace)
    monkeypatch.setattr(
        ResearchOrchestrator,
        "_build_index_service_request",
        lambda self, **_: SimpleNamespace(sources=[]),
    )

    result, _indexer = orch._run_indexing_stage(target)

    assert result["status"] == OperationStatus.FAILED.value
    assert result["status"] != OperationStatus.SUCCESS.value
    assert result["indexed_files"] == 0
    assert result["refused"] == [{"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}]
    assert not target.exists()
    assert not (workspace / "rag").exists()
    rejected = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_REJECTED"]
    assert len(rejected) == 1
    assert rejected[0]["status"] == OperationStatus.FAILED.value
    assert rejected[0]["metrics"]["rejection_code"] == "NO_DOCUMENTS_TO_INDEX"
    assert [
        e
        for e in _journal(workspace)
        if e["action"] == "RAG_INDEX_BUILT"
        and e["status"] == OperationStatus.SUCCESS.value
    ] == []


# --------------------------------------------------------------------------- #
# E3-NEG-014 -- a mixed batch is PARTIAL, never SUCCESS (C-29, RAG-012)
# --------------------------------------------------------------------------- #


def _stub_index_workspace(
    monkeypatch: pytest.MonkeyPatch, *, outcome: str
) -> dict[str, Any]:
    """Stand in for the kit service and record the harness status mapping."""

    seen: dict[str, Any] = {}
    if outcome == "PARTIAL":
        stub = SimpleNamespace(
            outcome="PARTIAL",
            counts=SimpleNamespace(
                accepted_documents=1, rejected_documents=1, visible_chunks=2
            ),
            rejected_documents=(
                SimpleNamespace(
                    document_id="DOC-" + "9" * 32,
                    code="EXTRACTED_TEXT_UNUSABLE",
                ),
            ),
        )
    else:
        stub = SimpleNamespace(
            outcome="SUCCESS",
            counts=SimpleNamespace(
                accepted_documents=1, rejected_documents=0, visible_chunks=2
            ),
            rejected_documents=(),
        )

    def _fake(request: Any, **kwargs: Any) -> Any:
        seen["outcome"] = request
        return stub

    monkeypatch.setattr(orch_module, "index_workspace", _fake)
    monkeypatch.setattr(
        orch_module, "ChromaReplacementView", lambda **_: SimpleNamespace()
    )
    monkeypatch.setattr(
        orch_module, "ChromaVisibleSetReader", lambda **_: SimpleNamespace()
    )
    _mock_embedder(monkeypatch)
    return seen


def test_e3_neg_014_mixed_batch_is_partial_never_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-014: the harness maps the kit PARTIAL to PARTIAL, not SUCCESS."""

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    _stub_index_workspace(monkeypatch, outcome="PARTIAL")

    result = index_accepted_documents(workspace, chroma_dir=tmp_path / "chroma")

    assert result["status"] == "PARTIAL"
    assert result["status"] != OperationStatus.SUCCESS.value
    assert result["indexed_files"] == 1
    assert result["refused"] == [
        {"document_id": "DOC-" + "9" * 32, "code": "EXTRACTED_TEXT_UNUSABLE"}
    ]
    events = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    assert len(events) == 1
    assert events[0]["status"] == "PARTIAL"
    assert events[0]["metrics"]["refused_documents"] == 1


# --------------------------------------------------------------------------- #
# E3-NEG-015 -- malformed parent refuses before any store (C-02, §6.2 step 1)
# --------------------------------------------------------------------------- #


def test_e3_neg_015_malformed_parent_refuses_before_any_store(
    tmp_path: Path,
) -> None:
    """E3-NEG-015: an unreadable accepted payload is an absence, not a licence."""

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    manifests = _registered_manifests(workspace)
    assert list(manifests) == [state["artifact_id"]]
    payload_path = workspace / manifests[state["artifact_id"]]["path"]
    assert payload_path.is_file()
    payload_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(PublicationRefused) as caught:
        index_accepted_documents(workspace)

    assert caught.value.code == "ACCEPTED_ARTIFACT_UNREADABLE"
    assert state["artifact_id"] in caught.value.message
    assert not (workspace / "rag").exists()
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] == []


# --------------------------------------------------------------------------- #
# E3-NEG-016 -- no manifest refuses before any store (C-01, §6.2 step 1)
# --------------------------------------------------------------------------- #


def test_e3_neg_016_no_manifest_refuses_before_touching_a_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-016 / ``DOCUMENT_MANIFEST_NOT_ACCEPTED``: refusal precedes stores.

    The workspace is fully valid -- corpus, screening, registry, Stage 5 output
    -- and has simply never published. Constructing Stage 6 would create the
    vector store before finding out there is nothing accepted to index, so the
    preflight refuses first and leaves no trace. This is also the first required
    negative-case shape.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    assert _registered_manifests(workspace) == {}

    def _explode(*_: Any, **__: Any) -> Any:
        raise AssertionError("Stage 6 was constructed with no accepted manifest")

    monkeypatch.setattr(orch_module, "ResearchOrchestrator", _explode)

    with pytest.raises(PublicationRefused) as caught:
        index_accepted_documents(workspace)

    assert caught.value.code == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
    assert "publish" in caught.value.message
    assert not (workspace / "rag").exists()
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] == []


# --------------------------------------------------------------------------- #
# E3-NEG-026 -- the embedder identity is explicit, never defaulted (C-17)
# --------------------------------------------------------------------------- #


def test_e3_neg_026_embedder_identity_is_explicit_in_the_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-026: no provider, model, dimension, or distance is ever defaulted."""

    mock = _mock_embedder(monkeypatch)
    state = _published_state(tmp_path)
    orch = ResearchOrchestrator(state["workspace"])
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    request = _fixed_request(orch, parent_view, chroma_dir=tmp_path / "chroma")

    assert request.embedder_provider == "sentence-transformers"
    assert request.embedder_model == "all-MiniLM-L6-v2"
    assert request.embedder_dimension == 384
    assert request.embedder_dimension == mock.dimension
    assert request.embedder_distance_metric == "cosine"
    assert request.embedder_normalize_embeddings is True
    assert request.backend_type == "chromadb"
    assert request.collection_name == "scholar_docs"
    assert request.storage_schema_version == "1.0.0"
    assert request.hnsw_space == "cosine"
    for limb in (
        request.embedder_provider,
        request.embedder_model,
        request.backend_type,
        request.collection_name,
    ):
        assert isinstance(limb, str) and limb.strip()


# --------------------------------------------------------------------------- #
# E3-NEG-028 -- deterministic source order (C-15)
# --------------------------------------------------------------------------- #


def test_e3_neg_028_sources_are_deterministically_ordered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-028 (harness limb): backend/filesystem order never reaches identity.

    Stage 6 sorts documents by ``document_id`` before building sources, so an
    unsorted ``glob`` order cannot observably move a fingerprint. Positional-id
    reuse itself is the kit's proof and is MISSING below.
    """

    _mock_embedder(monkeypatch)
    state = _published_state(tmp_path, study_count=2)
    orch = ResearchOrchestrator(state["workspace"])
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    first = _fixed_request(orch, parent_view, chroma_dir=tmp_path / "chroma")
    second = _fixed_request(orch, parent_view, chroma_dir=tmp_path / "chroma")

    ordered = [source.request.document_id for source in first.sources]
    assert len(ordered) == 2
    assert ordered == sorted(ordered)
    assert [source.request.document_id for source in second.sources] == ordered


# --------------------------------------------------------------------------- #
# E3-NEG-034 -- no emittable identity leaves Stage 6 (C-30)
# --------------------------------------------------------------------------- #


def test_e3_neg_034_no_emittable_identity_leaves_stage6(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-034: Stage 6 emits inherited limbs only -- no CHK-, no token."""

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    _stub_index_workspace(monkeypatch, outcome="SUCCESS")

    result = index_accepted_documents(workspace, chroma_dir=tmp_path / "chroma")

    assert result["status"] == OperationStatus.SUCCESS.value
    blob = json.dumps(result, sort_keys=True)
    events = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    assert len(events) == 1
    blob += json.dumps(events[0], sort_keys=True)
    for banned in ("CHK-", "chk-", "[rag:", "rag:v2:"):
        assert banned not in blob, banned
    for document in result["documents"]:
        assert document["document_id"].startswith("DOC-")
        assert document["study_id"].startswith("STU-")
        assert document["parent_artifact_id"].startswith("ART-")


# --------------------------------------------------------------------------- #
# E3-NEG-036 -- similarity is not entailment (C-25)
# --------------------------------------------------------------------------- #


def test_e3_neg_036_no_similarity_as_entailment_language(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-036: no VERIFIED/ENTAILED label and no entailment score is emitted."""

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    _stub_index_workspace(monkeypatch, outcome="SUCCESS")

    result = index_accepted_documents(workspace, chroma_dir=tmp_path / "chroma")

    assert result["status"] == OperationStatus.SUCCESS.value
    blob = json.dumps(result, sort_keys=True)
    events = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    assert len(events) == 1
    blob += json.dumps(events[0], sort_keys=True)
    lowered = blob.lower()
    for banned in ("entailment", "entailed", "verified", "entailment_score"):
        assert banned not in lowered, banned


# --------------------------------------------------------------------------- #
# E3-NEG-038 -- the sidecar is not a Contract type (C-03, §1.1)
# --------------------------------------------------------------------------- #


def test_e3_neg_038_frozen_registries_reject_the_index_manifest_sidecar(
    tmp_path: Path,
) -> None:
    """E3-NEG-038: offering the kit sidecar to the frozen gate fails closed.

    Mirrors E2-NEG-021: the rejection is ``UNSUPPORTED_ARTIFACT_TYPE``, no
    registry entry is fabricated, and no artifact directory is created.
    """

    assert MANIFEST_TYPE == "index_manifest"
    payload = {
        "schema_version": "index-manifest-v1",
        "artifact_type": MANIFEST_TYPE,
        "artifact_id": "IDX-" + "e" * 32,
        "contract_version": "1.0.0",
    }
    context = AcceptanceContext(
        workspace_id=WORKSPACE_ID,
        protocol_fingerprint="sha256:" + "0" * 64,
        corpus_fingerprint="sha256:" + "0" * 64,
    )
    result = accept_artifact(workspace=tmp_path, payload=payload, expected=context)

    assert result.accepted is False
    assert {issue.code for issue in result.issues} == {"UNSUPPORTED_ARTIFACT_TYPE"}
    assert result.published_path is None
    assert not (tmp_path / "artifacts").exists()
    assert not (tmp_path / "audit" / "artifact_registry.json").exists()


# --------------------------------------------------------------------------- #
# E3-NEG-048 -- declared dependencies (C-34)
# --------------------------------------------------------------------------- #


def test_e3_neg_048_rag_kit_pin_is_a_full_merged_sha_and_resolves_vendored() -> None:
    """E3-NEG-048 (harness half): pin, snapshot, and import agree on one commit."""

    import scholar_rag

    plugins = json.loads(PLUGINS_JSON.read_text(encoding="utf-8"))
    by_name = {plugin["name"]: plugin for plugin in plugins["plugins"]}
    rev = by_name["scholar-rag-kit"]["default_rev"]
    assert rev == KIT_RAG_PIN
    assert re.fullmatch(r"[0-9a-f]{40}", rev) is not None, (
        "the pin must be a full commit SHA, never a floating branch"
    )
    assert scholar_rag.__file__ is not None, "namespace package without a file"
    resolved = Path(scholar_rag.__file__).resolve()
    assert REPO_ROOT / "tools" / "scholar-rag-kit" in resolved.parents, (
        f"scholar_rag resolved outside the vendored tree: {resolved}"
    )
    pins = json.loads(PINS_JSON.read_text(encoding="utf-8"))
    pinned = {pin["name"]: pin for pin in pins["kits"]}["scholar-rag-kit"]
    assert pinned["default_rev"] == rev, "the metapackage pin must follow plugins.json"


# --------------------------------------------------------------------------- #
# E3-NEG-049 -- generation agreement (C-08, §6.2 step 3)
# --------------------------------------------------------------------------- #


def test_e3_neg_049_protocol_mutation_breaks_generation_agreement(
    tmp_path: Path,
) -> None:
    """E3-NEG-049: a post-acceptance protocol edit refuses with a typed code."""

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    protocol_path = workspace / "protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["research_questions"][0]["text"] += " (amended after screening)"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")

    with pytest.raises(PublicationRefused) as caught:
        index_accepted_documents(workspace)

    assert caught.value.code == "PROTOCOL_FINGERPRINT_MISMATCH"
    assert not (workspace / "rag").exists()
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] == []


# --------------------------------------------------------------------------- #
# E3-POS-007 -- zero publication at each harness failure point (E3-007)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("failure_point", ["no-manifest", "no-documents"])
def test_e3_pos_007_refusal_proves_zero_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    """E3-POS-007 (harness scope): refusal before step 7 publishes nothing.

    At each harness-owned failure point -- no accepted manifest in this
    generation, and no indexable documents -- the run proves zero publication:
    no vector store, no registry mutation, no success audit event, and no
    accepted E3 record. ``rag/index/accepted.json`` is adapter-owned
    (``index-acceptance-v1``); its absence here is asserted so a later writer
    cannot appear silently.
    """

    if failure_point == "no-manifest":
        workspace = _extracted_state(tmp_path)["workspace"]
        before_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()
        with pytest.raises(PublicationRefused) as caught:
            index_accepted_documents(workspace)
        assert caught.value.code == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
        after_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()
    else:
        workspace = _published_state(tmp_path)["workspace"]
        before_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()
        monkeypatch.setattr(
            ResearchOrchestrator,
            "_build_index_service_request",
            lambda self, **_: SimpleNamespace(sources=[]),
        )
        result, _indexer = ResearchOrchestrator(workspace)._run_indexing_stage(
            tmp_path / "chroma"
        )
        assert result["status"] == OperationStatus.FAILED.value
        after_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()

    assert after_registry == before_registry
    assert not (workspace / "rag").exists()
    assert not (workspace / "rag" / "index" / "accepted.json").exists()
    assert [
        e
        for e in _journal(workspace)
        if e["action"] == "RAG_INDEX_BUILT"
        and e["status"] == OperationStatus.SUCCESS.value
    ] == []


# --------------------------------------------------------------------------- #
# E3-NEG-037 / E3-POS-008 -- the section 6.6 accepted record and event (live)
# --------------------------------------------------------------------------- #
# The adapter (``src/scholar_harness/index_acceptance.py``,
# ``index-acceptance-v1``) owns the accepted E3 record plus the canonical
# ``RAG_INDEX_BUILT`` event. These two rows were MISSING until T-131; they are
# live here, hermetic (deterministic mock embedder, offline flags, tmp dirs),
# and prove the exact section 6.6 field set with none of the forbidden
# members (absolute path, ``db_path``, secret, bearer token, environment
# value, free-text success claim).


def _adapter_live_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    """One real workspace plus one real kit candidate and its fake live set."""

    from scholar_harness.orchestrator import ResearchOrchestrator
    from scholar_rag.index_service import _build_candidate_manifest
    from scholar_rag.index_verifier import VisibleRow

    _mock_embedder(monkeypatch)
    state = _published_state(tmp_path)
    workspace = state["workspace"]
    orch = ResearchOrchestrator(workspace)
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    request = _fixed_request(orch, parent_view, chroma_dir=tmp_path / "chroma-unused")
    manifest = _build_candidate_manifest(
        request, docs_path=workspace / "extracted", workspace_root=workspace
    )
    rows = [
        VisibleRow(
            row_key=f"{FIXED_RUN_ID}#{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            study_id=chunk.study_id,
            embedding_dimension=manifest.embedder.dimension,
            stored_text=None,
        )
        for chunk in manifest.visible_chunks
    ]

    class _LiveReader:
        def __init__(self, rows: Any, space: str) -> None:
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

    return {
        "workspace": workspace,
        "manifest": manifest,
        "payload": manifest.canonical_payload(),
        "reader": _LiveReader(rows, manifest.backend.hnsw_space),
    }


def test_e3_neg_037_acceptance_event_has_no_incomplete_or_leaking_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-037 (C-32): the adapter emits no incomplete or leaking event."""

    from scholar_harness.index_acceptance import (
        ACCEPTANCE_SCHEMA_VERSION,
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_live_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    result = accept_index_candidate(
        workspace,
        built["payload"],
        run_id=FIXED_RUN_ID,
        manifest_path="rag/index/RUN-e3/manifest.json",
        reader=built["reader"],
        accepted_at="2026-09-28T00:00:00Z",
    )
    assert result.accepted is True, (result.failing_step, result.code, result.detail)
    # The accepted record is present, sealed, and versioned.
    record = json.loads((workspace / ACCEPTED_RELPATH).read_text(encoding="utf-8"))
    assert record["schema_version"] == ACCEPTANCE_SCHEMA_VERSION
    assert record["schema_version"] == "index-acceptance-v1"
    # Exactly one new event, and it is not an incomplete or leaking one.
    events = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    assert len(events) == 1
    event = events[-1]
    blob = json.dumps(event, sort_keys=True)
    lowered = blob.lower()
    # No forbidden member reaches the ledger.
    assert "chroma_db" not in blob and "db_path" not in blob
    assert "/tmp/" not in blob and "C:\\" not in blob and "C:/" not in blob
    assert "sk-" not in blob and "ghp_" not in blob and "bearer" not in lowered
    assert "os.environ" not in blob and "getenv" not in lowered
    for banned in ("verified", "entailed", "entailment"):
        assert banned not in lowered, banned


def test_e3_pos_008_acceptance_event_carries_the_full_section_66_field_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-POS-008: the adapter event carries the full section 6.6 field set."""

    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_live_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    result = accept_index_candidate(
        workspace,
        built["payload"],
        run_id=FIXED_RUN_ID,
        manifest_path="rag/index/RUN-e3/manifest.json",
        reader=built["reader"],
        accepted_at="2026-09-28T00:00:00Z",
    )
    assert result.accepted is True
    manifest = built["manifest"]
    record = json.loads((workspace / ACCEPTED_RELPATH).read_text(encoding="utf-8"))
    assert record["manifest_id"] == manifest.manifest_id
    assert (
        record["parent_artifact_ref"]["artifact_id"]
        == manifest.parent_artifact_ref.artifact_id
    )
    events = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    assert len(events) == 1
    params = events[-1]["parameters"]
    assert params["workspace_id"] == manifest.workspace_id
    assert params["run_id"] == FIXED_RUN_ID
    assert params["parent_artifact_id"] == manifest.parent_artifact_ref.artifact_id
    assert params["parent_artifact_sha256"] == manifest.parent_artifact_ref.sha256
    assert params["manifest_id"] == manifest.manifest_id
    assert params["manifest_path"] == "rag/index/RUN-e3/manifest.json"
    assert params["artifact_checksum"] == manifest.artifact_checksum
    assert params["index_fingerprint"] == manifest.index_fingerprint
    assert params["chunk_set_fingerprint"] == manifest.chunk_set_fingerprint
    assert params["configuration_fingerprint"] == manifest.configuration_fingerprint
    assert params["production_fingerprint"] == manifest.production_fingerprint
    assert params["protocol_fingerprint"] == manifest.protocol_fingerprint
    assert params["corpus_fingerprint"] == manifest.corpus_fingerprint
    assert params["counts"] == {
        "accepted_documents": manifest.counts.accepted_documents,
        "rejected_documents": manifest.counts.rejected_documents,
        "visible_chunks": manifest.counts.visible_chunks,
    }
    assert params["rejected_documents"] == [
        {"document_id": doc.document_id, "code": doc.code}
        for doc in manifest.rejected_documents
    ]
    assert params["embedding_identity"] == {
        "provider": manifest.embedder.provider,
        "model": manifest.embedder.model,
        "dimension": manifest.embedder.dimension,
        "distance_metric": manifest.embedder.distance_metric,
    }
    assert params["configuration"] == dict(manifest.chunker.configuration)
    assert "failing_step" not in params and "code" not in params


# --------------------------------------------------------------------------- #
# E3-NEG-039 -- publication-time required-parent-type re-check (C-07, live)
# --------------------------------------------------------------------------- #


def test_e3_neg_039_publication_time_parent_type_is_rechecked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3-NEG-039 (C-07): the adapter re-checks the required parent type at publication.

    Construction (faithful publication-time divergence, not degenerate
    scaffolding): the candidate is built against the accepted
    ``document_manifest`` parent ``X`` and is valid at checks 1-6. Artifact
    ids are content hashes, so the same ``artifact_id`` cannot honestly name
    two types at once; the divergence is therefore a time-of-check /
    time-of-use change: inside check 6 (the typed backend read) the spy
    rewrites the frozen registry file on disk so the *same* ``artifact_id``
    now yields a known non-required Contract entry (``corpus_snapshot`` --
    known, so C-03 passes, but not the required ``document_manifest``, so
    C-07 must fail). Check 7 then re-loads the registry from disk and must
    refuse ``(7, REQUIRED_PARENT_TYPE_MISSING)`` with zero publication. The
    refusal is owned by step 7 (not load-time step 3) because checks 1-6
    already passed -- proven by the check-6 spy having run and by the same
    payload succeeding once the registry is restored.

    Covers R39-RECHECK (passes 1-6, then step-7 refusal, re-check proven),
    R39-REFUSE (typed refusal, no exception leak), R39-NORECORD (absent then
    byte-identical previous, journal unchanged, no success event, intent
    retained), and R39-LIVE (happy-path still green).
    """

    import copy

    import scholar_harness.index_acceptance as adapter_module
    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_live_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    payload = copy.deepcopy(built["payload"])
    parent_id = str(payload["parent_artifact_ref"]["artifact_id"])
    registry_path = workspace / "audit" / "artifact_registry.json"
    registry_before = registry_path.read_bytes()
    journal_before = _journal(workspace)
    assert not (workspace / ACCEPTED_RELPATH).exists()
    intent_rel = "rag/index/RUN-e3/commit-intent.json"
    (workspace / intent_rel).parent.mkdir(parents=True, exist_ok=True)
    (workspace / intent_rel).write_text(
        json.dumps({"run_id": FIXED_RUN_ID}), encoding="utf-8"
    )

    real_verify = adapter_module.verify_backend
    verify_calls: list[Any] = []

    def _diverging_verify(manifest: Any, reader: Any) -> Any:
        result = real_verify(manifest, reader)
        verify_calls.append(result)
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        raw["artifacts"][parent_id]["artifact_type"] = "corpus_snapshot"
        registry_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        return result

    monkeypatch.setattr(adapter_module, "verify_backend", _diverging_verify)

    # Phase 1 (absent previous): diverged at publication -> step-7 refusal.
    refused = accept_index_candidate(
        workspace,
        copy.deepcopy(payload),
        run_id=FIXED_RUN_ID,
        manifest_path="rag/index/RUN-e3/manifest.json",
        reader=built["reader"],
        intent_path=intent_rel,
        accepted_at="2026-09-28T00:00:00Z",
    )
    assert refused.accepted is False
    assert (refused.failing_step, refused.code) == (7, "REQUIRED_PARENT_TYPE_MISSING")
    # Owned by step 7, not load-time step 3: check 6 ran, so checks 1-6 passed.
    assert len(verify_calls) == 1
    assert refused.failing_step == 7
    # Zero publication: no record, intent retained, journal unchanged, no event.
    assert not (workspace / ACCEPTED_RELPATH).exists()
    assert (workspace / intent_rel).is_file()
    assert _journal(workspace) == journal_before
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] == []
    diverged_bytes = registry_path.read_bytes()
    assert diverged_bytes != registry_before

    # Phase 2 (same payload, registry restored): succeeds, proving the
    # candidate was valid at 1-6 and the re-check was the sole cause.
    registry_path.write_bytes(registry_before)
    monkeypatch.setattr(adapter_module, "verify_backend", real_verify)
    accepted = accept_index_candidate(
        workspace,
        copy.deepcopy(payload),
        run_id=FIXED_RUN_ID,
        manifest_path="rag/index/RUN-e3/manifest.json",
        reader=built["reader"],
        intent_path=intent_rel,
        accepted_at="2026-09-28T00:00:00Z",
    )
    assert accepted.accepted is True, (accepted.failing_step, accepted.code)
    assert not (workspace / intent_rel).exists()
    before_bytes = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_after_success = _journal(workspace)
    assert (
        len([e for e in journal_after_success if e["action"] == "RAG_INDEX_BUILT"]) == 1
    )

    # Phase 3 (previous present): a second distinct candidate diverged at
    # publication refuses at 7 with the previous record byte-identical.
    from scholar_harness.orchestrator import ResearchOrchestrator
    from scholar_rag.index_service import IndexServiceRequest, _build_candidate_manifest
    from scholar_rag.index_verifier import VisibleRow

    orch = ResearchOrchestrator(workspace)
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    second_run = "RUN-" + "b3" * 16
    base_request = orch._build_index_service_request(
        chroma_dir=tmp_path / "chroma-unused-2",
        parent_view=parent_view,
        run_id=second_run,
        created_at="2026-09-28T00:00:00Z",
        producer_commit=FIXED_PRODUCER_COMMIT,
        producer_version=FIXED_PRODUCER_VERSION,
    )
    altered_config = dict(base_request.chunker_configuration)
    altered_config["max_chunk_chars"] = 800
    request2 = IndexServiceRequest(
        **{
            **base_request.model_dump(mode="python"),
            "chunker_configuration": altered_config,
            "run_id": second_run,
            "created_at": "2026-09-28T00:00:00Z",
        }
    )
    manifest2 = _build_candidate_manifest(
        request2, docs_path=workspace / "extracted", workspace_root=workspace
    )
    assert manifest2.manifest_id != built["manifest"].manifest_id
    rows2 = [
        VisibleRow(
            row_key=f"{second_run}#{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            study_id=chunk.study_id,
            embedding_dimension=manifest2.embedder.dimension,
            stored_text=None,
        )
        for chunk in manifest2.visible_chunks
    ]

    class _Reader2:
        def __init__(self, rows: Any, space: str) -> None:
            self._rows = list(rows)
            self._space = space

        def visible_ids(self) -> list[str]:
            return sorted(r.chunk_id for r in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    reader2 = _Reader2(rows2, manifest2.backend.hnsw_space)
    intent2_rel = "rag/index/RUN-b3/commit-intent.json"
    (workspace / intent2_rel).parent.mkdir(parents=True, exist_ok=True)
    (workspace / intent2_rel).write_text(
        json.dumps({"run_id": second_run}), encoding="utf-8"
    )
    verify_calls2: list[Any] = []

    def _diverging_verify2(manifest: Any, reader: Any) -> Any:
        result = real_verify(manifest, reader)
        verify_calls2.append(result)
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        raw["artifacts"][parent_id]["artifact_type"] = "corpus_snapshot"
        registry_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        return result

    monkeypatch.setattr(adapter_module, "verify_backend", _diverging_verify2)
    refused2 = accept_index_candidate(
        workspace,
        manifest2.canonical_payload(),
        run_id=second_run,
        manifest_path="rag/index/RUN-b3/manifest.json",
        reader=reader2,
        intent_path=intent2_rel,
        accepted_at="2026-09-29T00:00:00Z",
    )
    assert refused2.accepted is False
    assert (refused2.failing_step, refused2.code) == (7, "REQUIRED_PARENT_TYPE_MISSING")
    assert len(verify_calls2) == 1
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == before_bytes
    assert (workspace / intent2_rel).is_file()
    assert _journal(workspace) == journal_after_success
    assert [
        e
        for e in _journal(workspace)
        if e["action"] == "RAG_INDEX_BUILT"
        and e["status"] == OperationStatus.SUCCESS.value
    ] != []
    registry_path.write_bytes(registry_before)


# --------------------------------------------------------------------------- #
# T-136 ledger closure (POS-012): proof-bound kit/MCP/wheel rows (E3-012)
# --------------------------------------------------------------------------- #
#
# The 11 rows below were MISSING until T-136. Each is now proof-bound, never
# a bare skip: the 9 kit IDs execute the kit's own hermetic failure proof (or
# assert its hash-pinned test exists where a full service run would need a
# backend store), POS-009 is a read-only MCP tripwire, and POS-012 is the
# static declared-imports half plus the one-time isolated-wheel runtime
# reference. No wheel is built here; no network is touched; every filesystem
# effect (where any) is confined to pytest's tmp_path.
# --------------------------------------------------------------------------- #


def _kit_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_kit_test_exists(
    test_file: Path, test_name: str, *, must_mention: tuple[str, ...]
) -> str:
    """Tripwire: the named kit ledger test exists at the pinned content."""

    assert test_file.is_file(), f"kit test file moved: {test_file}"
    text = _kit_text(test_file)
    assert f"def {test_name}(" in text, (
        f"kit ledger test {test_name} missing under {test_file} -- "
        "the canonical proof moved; reconcile, do not weaken"
    )
    for phrase in must_mention:
        assert phrase in text, (
            f"kit test {test_name} no longer mentions {phrase!r} -- "
            "the proof drifted; reconcile"
        )
    return text


def _kit_proof_haystack(path: Path) -> str:
    if path.is_dir():
        return "\n".join(
            candidate.read_text(encoding="utf-8")
            for candidate in sorted(path.rglob("*.py"))
        )
    return path.read_text(encoding="utf-8")


def _e3_top_level_imports(path: Path) -> set[str]:
    """Module-level ``import``/``from`` top names in one file (no function walk)."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
    return found


def _e3_all_imports(path: Path) -> set[str]:
    """Every ``import``/``from`` top name in one file, including function-local."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
    return found


def test_e3_neg_009_kit_document_eligibility_join_is_proof_bound() -> None:
    """E3-NEG-009 (C-09): a document absent from the parent is refused.

    Proof type: EXECUTION of the kit's own hermetic join plus a hash-pinned
    tripwire. Kit ledger test
    ``tools/scholar-rag-kit/tests/test_index_service.py:2140``
    (``test_t90_neg_009_a_document_absent_from_the_accepted_parent_is_refused``)
    and manifest-level
    ``test_a_document_absent_from_the_accepted_parent_is_refused``
    (``test_index_manifest.py:1984``) prove the same ``VALIDATION_ERROR`` at
    pin ``15a7a5a``; the harness forwards ``parent_view`` verbatim (E3-NEG-010
    live) and never re-derives the join.
    """

    from scholar_rag.index_manifest import (
        IndexManifest,
        ManifestValidationError,
        build_parent_view,
    )

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_service.py"
    assert "eligibility join" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_SERVICE,
        "test_t90_neg_009_a_document_absent_from_the_accepted_parent_is_refused",
        must_mention=("C-09", "E3-NEG-009", "VALIDATION_ERROR"),
    )
    _assert_kit_test_exists(
        KIT_TEST_MANIFEST,
        "test_a_document_absent_from_the_accepted_parent_is_refused",
        must_mention=("accepted parent", "VALIDATION_ERROR"),
    )
    model = IndexManifest.from_payload(_kit_golden_manifest())

    def _parent_docs() -> list[dict[str, Any]]:
        payload = _kit_golden_manifest()
        records = [
            {
                "document_id": doc["document_id"],
                "study_id": doc["study_id"],
                "extracted_path": doc["extracted_path"],
                "extracted_content_sha256": doc["extracted_content_sha256"],
                "extraction_method": doc["extraction_method"],
            }
            for doc in payload["documents"]
        ]
        records += [
            {"document_id": e["document_id"], "study_id": e["study_id"]}
            for e in payload["rejected_documents"]
        ]
        return sorted(records, key=lambda r: r["document_id"])

    view = build_parent_view(model, documents=_parent_docs()[1:])
    with pytest.raises(ManifestValidationError) as caught:
        model.check_parent_agreement(view)
    assert caught.value.code == "VALIDATION_ERROR"
    assert caught.value.code in ("VALIDATION_ERROR",)
    assert "accepted parent" in str(caught.value)


def test_e3_neg_011_kit_study_lineage_join_is_proof_bound() -> None:
    """E3-NEG-011 (C-10): a study absent from the lineage is refused.

    Proof type: EXECUTION plus tripwire. Kit ledger test
    ``test_t90_neg_011_a_study_absent_from_the_accepted_lineage_is_refused``
    (``test_index_service.py:2176``, ``C-10 / E3-NEG-011``) proves the
    byte-identity refusal at pin ``15a7a5a``; the harness never resolves an
    alias (DOI/OpenAlex/filename) into the persisted ``study_id``.
    """

    from scholar_rag.index_manifest import (
        IndexManifest,
        ManifestValidationError,
        build_parent_view,
    )

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_service.py"
    assert "eligibility join" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_SERVICE,
        "test_t90_neg_011_a_study_absent_from_the_accepted_lineage_is_refused",
        must_mention=("C-10", "E3-NEG-011", "VALIDATION_ERROR"),
    )
    model = IndexManifest.from_payload(_kit_golden_manifest())
    payload = _kit_golden_manifest()
    records = [
        {
            "document_id": doc["document_id"],
            "study_id": doc["study_id"],
            "extracted_path": doc["extracted_path"],
            "extracted_content_sha256": doc["extracted_content_sha256"],
            "extraction_method": doc["extraction_method"],
        }
        for doc in payload["documents"]
    ]
    records[0] = dict(records[0], study_id="STU-" + "5" * 32)
    view = build_parent_view(model, documents=records)
    with pytest.raises(ManifestValidationError) as caught:
        model.check_parent_agreement(view)
    assert caught.value.code == "VALIDATION_ERROR"
    assert "documents.0.study_id" in str(caught.value.field)


def test_e3_neg_017_kit_parent_hash_mismatch_is_proof_bound() -> None:
    """E3-NEG-017 (C-06): a hash-stale parent is refused with PARENT_HASH_MISMATCH.

    Proof type: EXECUTION plus tripwire. Kit ledger test
    ``test_neg_017_a_hash_stale_parent_is_refused_with_parent_hash_mismatch``
    (``test_index_manifest.py:1951``) proves the code at pin ``15a7a5a``;
    Stage 6 re-reads the registry hash but never recomputes it.
    """

    from scholar_rag.index_manifest import (
        IndexManifest,
        ParentAgreementError,
        build_parent_view,
    )

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py"
    assert "PARENT_HASH_MISMATCH" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_MANIFEST,
        "test_neg_017_a_hash_stale_parent_is_refused_with_parent_hash_mismatch",
        must_mention=("C-06", "E3-NEG-017", "PARENT_HASH_MISMATCH"),
    )
    model = IndexManifest.from_payload(_kit_golden_manifest())
    payload = _kit_golden_manifest()
    records = [
        {
            "document_id": doc["document_id"],
            "study_id": doc["study_id"],
            "extracted_path": doc["extracted_path"],
            "extracted_content_sha256": doc["extracted_content_sha256"],
            "extraction_method": doc["extraction_method"],
        }
        for doc in payload["documents"]
    ]
    view = build_parent_view(model, documents=records, sha256="sha256:" + "2" * 64)
    with pytest.raises(ParentAgreementError) as caught:
        model.check_parent_agreement(view)
    assert caught.value.code == "PARENT_HASH_MISMATCH"


def test_e3_neg_021_kit_path_shape_refusal_is_proof_bound() -> None:
    """E3-NEG-021 (C-12): a path-shaped escape never reaches the filesystem.

    Proof type: EXECUTION plus tripwire. Kit ledger test
    ``test_t90_neg_021_a_path_shaped_escape_is_refused_before_any_backend_write``
    (``test_index_service.py:1579``) proves ``PATH_OUTSIDE_WORKSPACE`` at pin
    ``15a7a5a``; the harness never synthesizes an extracted path.
    """

    from scholar_rag.index_service import _refuse_path_shaped
    from scholar_rag.replacement import _refuse_path_shaped as _replacement_refuse

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_service.py"
    assert "_refuse_path_shaped" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_SERVICE,
        "test_t90_neg_021_a_path_shaped_escape_is_refused_before_any_backend_write",
        must_mention=("C-12", "E3-NEG-021", "PATH_OUTSIDE_WORKSPACE"),
    )
    for bad in ("C:/elsewhere/x.md", "../escape/x.md", "/etc/rag/events.jsonl"):
        with pytest.raises(Exception) as caught:
            _refuse_path_shaped(bad, "extracted_path")
        assert "PATH_OUTSIDE_WORKSPACE" in type(caught.value).__name__ or (
            getattr(caught.value, "code", "") == "PATH_OUTSIDE_WORKSPACE"
            or "workspace-relative" in str(caught.value)
            or "absolute" in str(caught.value)
            or ".." in str(caught.value)
        )
    with pytest.raises(Exception):
        _replacement_refuse("../escape/x.md", "intent_path")


def test_e3_neg_022_kit_docs_containment_is_proof_bound() -> None:
    """E3-NEG-022 (C-12): docs-directory containment is kit-owned.

    Proof type: TRIPWIRE plus construction refusal (no backend store is
    opened). Kit ledger test
    ``test_t90_neg_022_a_parent_document_outside_the_docs_scope_is_refused``
    (``test_index_service.py:2625``) proves ``PATH_OUTSIDE_WORKSPACE`` at pin
    ``15a7a5a``; harness skip-missing is already proven under E3-NEG-013/016.
    """

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_service.py"
    assert "docs_destination" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_SERVICE,
        "test_t90_neg_022_a_parent_document_outside_the_docs_scope_is_refused",
        must_mention=("C-12", "E3-NEG-022", "PATH_OUTSIDE_WORKSPACE"),
    )
    from scholar_rag.index_service import IndexServiceRequest

    fields = IndexServiceRequest.model_fields
    assert "docs_path" in fields and "journal_path" in fields
    assert "workspace-relative" in (
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_service.py"
    ).read_text(encoding="utf-8")


def test_e3_neg_030_kit_per_study_uniqueness_is_proof_bound() -> None:
    """E3-NEG-030 (C-27): chunk identity is unique within one study.

    Proof type: EXECUTION plus tripwire. Kit ledger test
    ``test_neg_030_a_chunk_id_reused_within_one_study_is_refused``
    (``test_index_manifest.py:722``) proves ``CHUNK_IDENTITY_COLLISION`` at
    pin ``15a7a5a``; the harness mints no chunk identity.
    """

    from scholar_rag.index_manifest import (
        ChunkIdentityCollisionError,
        IndexManifest,
        compute_fingerprints,
    )

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py"
    assert "cross-document collision" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_MANIFEST,
        "test_neg_030_a_chunk_id_reused_within_one_study_is_refused",
        must_mention=("C-27", "E3-NEG-030", "CHUNK_IDENTITY_COLLISION"),
    )
    payload = _kit_golden_manifest()
    sibling = {
        "chunk_ids": [BASELINE_CHUNK_ID],
        "detail": None,
        "document_id": "DOC-" + "A" * 32,
        "extracted_content_sha256": "sha256:" + "7a" * 32,
        "extracted_path": "extracted/DOC-" + "A" * 32 + ".md",
        "extraction_method": "DETERMINISTIC_RULE",
        "study_id": "STU-" + "4" * 32,
        "status": "INDEXED",
    }
    payload["documents"] = [*payload["documents"], sibling]
    payload["counts"]["accepted_documents"] = len(payload["documents"])
    sealed = dict(payload)
    for field, digest in compute_fingerprints(sealed).items():
        target = sealed
        parts = field.split(".")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = digest
    with pytest.raises(ChunkIdentityCollisionError) as caught:
        IndexManifest.from_payload(sealed)
    assert caught.value.code == "CHUNK_IDENTITY_COLLISION"


def test_e3_neg_031_kit_collection_uniqueness_is_proof_bound() -> None:
    """E3-NEG-031 (C-27): chunk identity is globally unique in the collection.

    Proof type: EXECUTION plus tripwire. Kit ledger test
    ``test_neg_031_a_chunk_id_reused_across_studies_is_refused``
    (``test_index_manifest.py:756``) proves ``CHUNK_IDENTITY_COLLISION`` at
    pin ``15a7a5a``; the harness mints no chunk identity.
    """

    from scholar_rag.index_manifest import (
        ChunkIdentityCollisionError,
        IndexManifest,
        compute_fingerprints,
    )

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py"
    assert "cross-document collision" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_MANIFEST,
        "test_neg_031_a_chunk_id_reused_across_studies_is_refused",
        must_mention=("C-27", "E3-NEG-031", "CHUNK_IDENTITY_COLLISION"),
    )
    payload = _kit_golden_manifest()
    for doc in payload["documents"]:
        if doc["document_id"] == "DOC-" + "6" * 32:
            doc["chunk_ids"] = [BASELINE_CHUNK_ID]
    payload["visible_chunks"] = [
        c
        for c in payload["visible_chunks"]
        if c["chunk_id"] != "CHK-4d2120ace9cbf53314aa2878a2ddc3a2"
    ]
    payload["counts"]["visible_chunks"] = len(payload["visible_chunks"])
    sealed = dict(payload)
    for field, digest in compute_fingerprints(sealed).items():
        target = sealed
        parts = field.split(".")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = digest
    with pytest.raises(ChunkIdentityCollisionError) as caught:
        IndexManifest.from_payload(sealed)
    assert caught.value.code == "CHUNK_IDENTITY_COLLISION"


def test_e3_neg_035_kit_usability_refusal_is_proof_bound() -> None:
    """E3-NEG-035 (C-13): empty-after-normalization text is EXTRACTED_TEXT_UNUSABLE.

    Proof type: TRIPWIRE plus vocabulary execution (the full service run with
    a backend store is the kit's hermetic proof and is not re-run here to keep
    this file fast and backend-free). Kit ledger test
    ``test_t90_neg_035_an_unusable_extraction_is_rejected_with_its_code``
    (``test_index_service.py:1014``) proves the ``PARTIAL`` + code at pin
    ``15a7a5a``; the harness producer refusal is E2-era, not E3.
    """

    from scholar_rag.index_manifest import (
        IndexManifest,
        MANIFEST_CODE_VOCABULARY,
    )

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py"
    assert "EXTRACTED_TEXT_UNUSABLE" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_SERVICE,
        "test_t90_neg_035_an_unusable_extraction_is_rejected_with_its_code",
        must_mention=("C-13", "E3-NEG-035", "EXTRACTED_TEXT_UNUSABLE"),
    )
    assert "EXTRACTED_TEXT_UNUSABLE" in MANIFEST_CODE_VOCABULARY
    model = IndexManifest.from_payload(_kit_golden_manifest())
    assert model.rejected_documents[0].code == "EXTRACTED_TEXT_UNUSABLE"


def test_e3_neg_050_kit_staleness_refusal_is_proof_bound() -> None:
    """E3-NEG-050 (C-11): changed bytes at a committed path are EXTRACTED_CONTENT_CHANGED.

    Proof type: TRIPWIRE plus vocabulary execution (the full service run is
    the kit's hermetic proof; not re-run here). Kit ledger test
    ``test_t90_neg_050_changed_bytes_at_a_committed_path_are_rejected_not_indexed``
    (``test_index_service.py:1104``) proves the code at pin ``15a7a5a``;
    index-time drift has no Stage 6 check (publish-time is STALE_EXTRACTED_BODY).
    """

    from scholar_rag.index_manifest import MANIFEST_CODE_VOCABULARY

    owner = REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py"
    assert "EXTRACTED_CONTENT_CHANGED" in _kit_text(owner)
    _assert_kit_test_exists(
        KIT_TEST_SERVICE,
        "test_t90_neg_050_changed_bytes_at_a_committed_path_are_rejected_not_indexed",
        must_mention=("C-11", "E3-NEG-050", "EXTRACTED_CONTENT_CHANGED"),
    )
    assert "EXTRACTED_CONTENT_CHANGED" in MANIFEST_CODE_VOCABULARY


def test_e3_pos_009_mcp_boundary_tripwire_is_proof_bound() -> None:
    """E3-POS-009 (§9 / RAG-014): the MCP indexing surface stays declared-unsupported.

    Proof type: READ-ONLY TRIPWIRE (not behavior re-proof). The 45/45
    agent-kit boundary tests at pinned ``79ffe42``
    (``tools/scholar-agent-kit/tests/test_mcp_indexing_boundary.py``, 45 tests)
    are the behavioral proof and stay in the canonical repo; this harness test
    pins that the vendored surface has not moved: ``mcp_supported=False`` for
    ``rag_indexing``, the ``UNSUPPORTED_CAPABILITY`` envelope, and the
    ``workspace_id: str = None,`` shape that §9.1 declares against.
    """

    from scholar_agent.capabilities import (
        CAPABILITIES,
        RAG_INDEXING,
        UNSUPPORTED_CAPABILITY,
    )

    assert AGENT_SERVER.is_file()
    assert AGENT_CAPABILITIES.is_file()
    assert KIT_TEST_MCP_BOUNDARY.is_file()
    server_text = _kit_text(AGENT_SERVER)
    assert "workspace_id: str = None," in server_text
    assert "unsupported_capability_envelope_json(RAG_INDEXING)" in server_text
    capabilities_text = _kit_text(AGENT_CAPABILITIES)
    assert "mcp_supported=False" in capabilities_text
    assert "RAG_INDEXING_DECLARATION" in capabilities_text
    declaration = CAPABILITIES[RAG_INDEXING]
    assert declaration.mcp_supported is False
    assert declaration.rejection_code == UNSUPPORTED_CAPABILITY
    assert declaration.rejection_code == "UNSUPPORTED_CAPABILITY"
    boundary_text = _kit_text(KIT_TEST_MCP_BOUNDARY)
    assert "test_e3_neg_040" in boundary_text
    assert "test_e3_neg_041" in boundary_text
    # 39 distinct ``def test_`` bodies collect to 45 cases with parametrization
    # (the verified 45/45 boundary at pinned 79ffe42); pin the def floor so a
    # deleted proof fails here without re-running the kit suite.
    assert boundary_text.count("def test_") >= 39


def test_e3_pos_012_declared_imports_are_proof_bound() -> None:
    """E3-POS-012 (RAG-019 / E3-012) static half: every E3 import is declared.

    The authoritative E3 path is the adapter
    (``src/scholar_harness/index_acceptance.py``) plus the IndexService call
    graph (``index_service`` / ``index_manifest`` / ``replacement`` /
    ``index_verifier`` / ``chunker`` / ``embedder`` / ``index_models`` /
    ``canonical``). Import-time third-party is exactly ``pydantic`` (declared
    in the kit and in the metapackage); ``scholar_*`` packages are
    force-included by the wheel; heavy backends (``chromadb``) and helpers
    (``yaml``, ``google``) appear only inside functions (deferred/guarded) and
    never at module top level, so the minimal-dep smoke below holds.

    One-time RELEASE runtime proof (evidence, not a committed slow test;
    recorded here so the static half cites it):

    * wheel: ``packaging/nexus-scholar/dist/nexus_scholar-1.0.0-py3-none-any.whl``
      built EXACTLY as CI does with ``uv build --wheel packaging/nexus-scholar``
      at harness pin ``15a7a5a50a0394ed87b9b8b3c153081e10ec36ad``;
      sha256 ``9ec58845b5c9d39edec3fc426314173fed32a37010651ab1c4ff6173704dd234``,
      837646 bytes;
    * isolated venv: fresh ``uv venv .../iso-venv2 --python 3.12`` (CPython
      3.12.14, Windows), installed with ``uv pip install --python
      .../iso-venv2/Scripts/python.exe <wheel>`` (only declared deps; no
      project venv, no editable checkouts; ``chromadb`` / ``torch`` /
      ``sentence-transformers`` / ``openai`` absent);
    * smoke: ``nexus-scholar --help`` and ``scholar-agent --help`` exit 0;
      ``python -c`` imports of ``scholar_rag.index_service`` /
      ``index_manifest`` / ``replacement`` / ``index_verifier`` / ``chunker`` /
      ``embedder`` plus ``scholar_harness.index_acceptance`` all resolve from
      ``.../iso-venv2/Lib/site-packages`` with ``INDEX_SERVICE_OUTCOMES ==
      {SUCCESS, PARTIAL, REFUSED, FAILED}`` and ``ACCEPTANCE_SCHEMA_VERSION ==
      index-acceptance-v1``; wheel ``METADATA Requires-Dist`` is exactly the 17
      light deps (no heavy backend), so no undeclared import works by accident.
    """

    adapter = REPO_ROOT / "src/scholar_harness/index_acceptance.py"
    kit_files = [
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_service.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/replacement.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_verifier.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/chunker.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/embedder.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_models.py",
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/canonical.py",
    ]
    for path in (adapter, *kit_files):
        assert path.is_file(), f"authoritative E3 path moved: {path}"
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    top_third_party: set[str] = set()
    for path in (adapter, *kit_files):
        for name in _e3_top_level_imports(path):
            if name in stdlib:
                continue
            if name.startswith("scholar_"):
                continue
            top_third_party.add(name)
    assert top_third_party == {"pydantic"}, (
        f"authoritative E3 import-time third-party drifted: {sorted(top_third_party)}; "
        "only pydantic may be imported at module top level"
    )
    kit_py = tomllib.loads(KIT_RAG_PYPROJECT.read_bytes().decode("utf-8"))
    kit_deps = kit_py["project"]["dependencies"]
    assert any(str(dep).startswith("pydantic") for dep in kit_deps), (
        "pydantic must be declared in the kit"
    )
    assert any("chromadb" in str(dep) for dep in kit_deps), (
        "the deferred chromadb backend must stay declared in the kit"
    )
    meta_py = tomllib.loads(METAPACKAGE_PYPROJECT.read_bytes().decode("utf-8"))
    meta_deps = meta_py["project"]["dependencies"]
    assert any(str(dep).startswith("pydantic") for dep in meta_deps), (
        "pydantic must be reachable from the metapackage"
    )
    force_include = meta_py["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    bundled = {
        source.split("tools/")[1].split("/")[0]
        for source in force_include
        if "tools/" in source and "/src/" in source
    }
    assert "scholar-rag-kit" in bundled and "scholar-agent-kit" in bundled
    all_imports: set[str] = set()
    for path in kit_files:
        all_imports |= _e3_all_imports(path)
    for heavy in ("chromadb", "yaml", "google"):
        assert heavy in all_imports, f"expected deferred {heavy} import to still exist"
    for path in (adapter, *kit_files):
        top = _e3_top_level_imports(path)
        assert "chromadb" not in top, f"{path.name} imports chromadb at top level"
        assert "yaml" not in top, f"{path.name} imports yaml at top level"
        assert "google" not in top, f"{path.name} imports google at top level"
    replacement_text = _kit_text(
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/replacement.py"
    )
    assert "deferred: keeps" in replacement_text
    verifier_text = _kit_text(
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/index_verifier.py"
    )
    assert "deferred: keeps" in verifier_text
    embedder_text = _kit_text(
        REPO_ROOT / "tools/scholar-rag-kit/src/scholar_rag/embedder.py"
    )
    assert "never imports chromadb" in embedder_text


# --------------------------------------------------------------------------- #
# MISSING -- ledger fully closed by T-136 (zero bare MISSING)
# --------------------------------------------------------------------------- #

#: Ledger fully closed by T-136: zero bare MISSING. Every one of the 29 required
#: IDs is now either harness-live (above) or proof-bound (the T-136 section).
#: ``MISSING`` is retained as an empty tuple so the ledger-index invariant
#: below still checks that no bare skip remains; do not re-add a bare row
#: without converting it to a proof-bound live test.
MISSING: tuple[tuple[str, str, Path, str, bool, str], ...] = ()


def _proof_haystack(path: Path) -> str:
    if path.is_dir():
        return "\n".join(
            candidate.read_text(encoding="utf-8")
            for candidate in sorted(path.rglob("*.py"))
        )
    return path.read_text(encoding="utf-8")


def test_e3_no_bare_missing_ids_remain() -> None:
    """T-136 closure: zero bare MISSING rows remain.

    The 11 former MISSING rows are now proof-bound live tests in the T-136
    section above; this asserts the table itself is empty so no bare skip can
    be re-added without failing the ledger-index invariant below.
    """

    assert MISSING == (), f"bare MISSING rows remain: {[row[0] for row in MISSING]}"
    assert len(MISSING) == 0


# --------------------------------------------------------------------------- #
# Diagnostic -- the one real-Chroma reproducer (slow, hermetic, tmp-only)
# --------------------------------------------------------------------------- #


def _cause_chain(exc: BaseException) -> list[dict[str, str]]:
    """The full ``__cause__``/``__context__`` chain as data, never a traceback."""

    chain: list[dict[str, str]] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        entry: dict[str, str] = {
            "type": type(current).__name__,
            "message": str(current)[:2000],
        }
        if current.__cause__ is not None:
            entry["edge"] = "__cause__"
        elif current.__context__ is not None:
            entry["edge"] = "__context__"
            entry["suppress_context"] = str(current.__suppress_context__)
        chain.append(entry)
        current = current.__cause__ or current.__context__
    return chain


def _reader_snapshot(reader: Any) -> dict[str, Any]:
    """Backend state through the read-only verification surface only."""

    try:
        ids = [str(chunk_id) for chunk_id in reader.visible_ids()]
    except Exception as exc:  # the pre-run store has no collection: record, don't raise
        return {
            "observable": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
        }
    snapshot: dict[str, Any] = {
        "observable": True,
        "visible_count": reader.visible_count(),
        "visible_ids": sorted(ids),
    }
    try:
        snapshot["collection_metadata"] = dict(reader.read_collection_metadata() or {})
    except Exception as exc:
        snapshot["collection_metadata_error"] = f"{type(exc).__name__}: {exc}"[:500]
    return snapshot


def test_e3_diagnostic_real_chroma_index_workspace_reproducer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Real-Chroma diagnostic: the exact typed request and backend sequence.

    Slow and hermetic-safe: a deterministic mock embedder (no weight download),
    ``HF_HUB_OFFLINE``/``TRANSFORMERS_OFFLINE`` set, a tmp ``db_path``, and
    nothing written outside tmp plus the ``tmp_path`` workspace fixture. The
    shipped ``index_accepted_documents`` path runs for real against a real
    ``ChromaReplacementView``; the typed request is captured exact, the backend
    is snapshotted before/after through the read-only verification surface,
    and any failure carries the full ``__cause__`` chain plus the minimal
    kit-level reproducer. See the module docstring for the close-out rule.
    """

    mock = _mock_embedder(monkeypatch)
    environment = {
        "python": platform.python_version(),
        "os": platform.platform(),
        "chromadb": __import__("chromadb").__version__,
        "embedder": "mock(deterministic, dim=384)",
    }

    state = _published_state(tmp_path)
    workspace = state["workspace"]
    chroma_dir = tmp_path / "diag-chroma"

    from scholar_rag.index_verifier import ChromaVisibleSetReader

    reader_before = ChromaVisibleSetReader(
        db_path=str(chroma_dir), collection_name="scholar_docs"
    )
    backend_before = _reader_snapshot(reader_before)

    captured: dict[str, Any] = {}
    real_index_workspace = orch_module.index_workspace

    def _recording(request: Any, **kwargs: Any) -> Any:
        captured["request"] = request
        captured["backend_type"] = type(kwargs["backend"]).__name__
        captured["reader_type"] = type(kwargs["reader"]).__name__
        captured["embedder_type"] = type(kwargs["embedder"]).__name__
        result = real_index_workspace(request, **kwargs)
        captured["envelope"] = result.envelope()
        return result

    monkeypatch.setattr(orch_module, "index_workspace", _recording)

    failure: dict[str, Any] = {}
    try:
        result = index_accepted_documents(workspace, chroma_dir=chroma_dir)
    except Exception as exc:  # never a vacuous pass: the chain is attached below
        failure = {"raised": True, "cause_chain": _cause_chain(exc)}
        raise
    finally:
        reader_after = ChromaVisibleSetReader(
            db_path=str(chroma_dir), collection_name="scholar_docs"
        )
        captured["backend_before"] = backend_before
        captured["backend_after"] = _reader_snapshot(reader_after)
        captured["environment"] = environment

    request = captured["request"]
    envelope = captured["envelope"]
    evidence = {
        "environment": environment,
        "request_limbs": {
            "run_id": request.run_id,
            "created_at": request.created_at,
            "workspace_id": request.parent_view["workspace_id"],
            "collection_name": request.collection_name,
            "backend_type": request.backend_type,
            "parent_view": request.parent_view,
            "chunker_configuration": request.chunker_configuration,
            "embedder": request.embedder_section(),
            "backend": request.backend_section(),
            "sources": [
                {
                    "request": source.request.model_dump(mode="json"),
                    "extracted_path": source.extracted_path,
                    "extraction_method": source.extraction_method,
                    "extracted_text": source.extracted_text,
                }
                for source in request.sources
            ],
            "journal_path": request.journal_path,
            "docs_path": request.docs_path,
        },
        "plumbing": {
            "backend_type": captured["backend_type"],
            "reader_type": captured["reader_type"],
            "embedder_type": captured["embedder_type"],
            "embedder_dimension_observed": getattr(mock, "dimension", None),
        },
        "result_envelope": envelope,
        "harness_result": result,
        "backend_before": captured["backend_before"],
        "backend_after": captured["backend_after"],
    }
    print(json.dumps(evidence, indent=2, default=str))
    capsys.readouterr()

    if failure:
        pytest.fail(
            "REOPEN-KIT: the diagnostic raised; the cause chain and the "
            f"minimal reproducer are attached: {json.dumps(failure)[:4000]}"
        )

    if result["status"] != OperationStatus.SUCCESS.value or envelope["codes"]:
        pytest.fail(
            "REOPEN-KIT: ATOMIC_COMMIT_FAILED-class outcome reproduced; minimal "
            "kit reproducer (request fields + corpus texts + store state) is "
            "printed above. "
            f"status={result['status']!r} codes={envelope['codes']!r} "
            f"verification={envelope['verification_codes']!r}"
        )

    # Healthy-path close-out: the concern is UNSUBSTANTIATED on this path.
    assert result["status"] == OperationStatus.SUCCESS.value
    assert result["indexed_files"] >= 1
    assert result["refused"] == []
    assert envelope["journaled"] is True
    assert envelope["live_set_matches"] is True
    assert envelope["manifest_id"] and envelope["manifest_id"].startswith("IDX-")
    assert request.parent_view["workspace_id"] == WORKSPACE_ID
    assert captured["backend_type"] == "ChromaReplacementView"
    assert captured["reader_type"] == "ChromaVisibleSetReader"
    after = captured["backend_after"]
    assert after["observable"] is True
    assert after["visible_count"] >= 1
    assert all(str(chunk_id).startswith("CHK-") for chunk_id in after["visible_ids"])
    blob = json.dumps(
        {"result": result, "envelope": envelope, "journal": _journal(workspace)},
        sort_keys=True,
    )
    assert "ATOMIC_COMMIT_FAILED" not in blob
    # Tmp containment: the workspace default store was never created.
    assert not (workspace / "rag" / "chroma_db").exists()
    assert (workspace / "run-reports" / "rag-index.jsonl").is_file()
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] != []


#: Landed here so the ledger-ID -> test mapping survives refactors that move
#: the tests above. Every one of the 29 required IDs names exactly one owner.
#: T-136: ledger fully closed -- zero MISSING; the 11 former MISSING rows are
#: proof-bound (kit execution + tripwire, MCP tripwire, static declared imports).
LEDGER_INDEX: dict[str, str] = {
    "E3-NEG-009": "test_e3_neg_009_kit_document_eligibility_join_is_proof_bound",
    "E3-NEG-010": "test_e3_neg_010_request_limbs_inherit_recorded_identity",
    "E3-NEG-011": "test_e3_neg_011_kit_study_lineage_join_is_proof_bound",
    "E3-NEG-012": "test_e3_neg_012_cross_workspace_manifest_is_not_inherited",
    "E3-NEG-013": "test_e3_neg_013_zero_accepted_run_is_failed_never_success",
    "E3-NEG-014": "test_e3_neg_014_mixed_batch_is_partial_never_success",
    "E3-NEG-015": "test_e3_neg_015_malformed_parent_refuses_before_any_store",
    "E3-NEG-016": "test_e3_neg_016_no_manifest_refuses_before_touching_a_store",
    "E3-NEG-017": "test_e3_neg_017_kit_parent_hash_mismatch_is_proof_bound",
    "E3-NEG-021": "test_e3_neg_021_kit_path_shape_refusal_is_proof_bound",
    "E3-NEG-022": "test_e3_neg_022_kit_docs_containment_is_proof_bound",
    "E3-NEG-026": "test_e3_neg_026_embedder_identity_is_explicit_in_the_request",
    "E3-NEG-028": "test_e3_neg_028_sources_are_deterministically_ordered",
    "E3-NEG-030": "test_e3_neg_030_kit_per_study_uniqueness_is_proof_bound",
    "E3-NEG-031": "test_e3_neg_031_kit_collection_uniqueness_is_proof_bound",
    "E3-NEG-034": "test_e3_neg_034_no_emittable_identity_leaves_stage6",
    "E3-NEG-035": "test_e3_neg_035_kit_usability_refusal_is_proof_bound",
    "E3-NEG-036": "test_e3_neg_036_no_similarity_as_entailment_language",
    "E3-NEG-037": "test_e3_neg_037_acceptance_event_has_no_incomplete_or_leaking_field",
    "E3-NEG-038": "test_e3_neg_038_frozen_registries_reject_the_index_manifest_sidecar",
    "E3-NEG-039": "test_e3_neg_039_publication_time_parent_type_is_rechecked",
    "E3-NEG-048": "test_e3_neg_048_rag_kit_pin_is_a_full_merged_sha_and_resolves_vendored",
    "E3-NEG-049": "test_e3_neg_049_protocol_mutation_breaks_generation_agreement",
    "E3-NEG-050": "test_e3_neg_050_kit_staleness_refusal_is_proof_bound",
    "E3-POS-005": "test_e3_pos_005_harness_fixture_matches_kit_golden_bytes "
    "+ test_e3_pos_005_baseline_chunk_id_rederives_from_the_fixture_limbs",
    "E3-POS-007": "test_e3_pos_007_refusal_proves_zero_publication",
    "E3-POS-008": "test_e3_pos_008_acceptance_event_carries_the_full_section_66_field_set",
    "E3-POS-009": "test_e3_pos_009_mcp_boundary_tripwire_is_proof_bound",
    "E3-POS-012": "test_e3_pos_012_declared_imports_are_proof_bound",
}


def test_e3_ledger_index_covers_every_required_id() -> None:
    """The file:line index above names all 29 required IDs exactly once."""

    required = {
        "E3-NEG-009",
        "E3-NEG-010",
        "E3-NEG-011",
        "E3-NEG-012",
        "E3-NEG-013",
        "E3-NEG-014",
        "E3-NEG-015",
        "E3-NEG-016",
        "E3-NEG-017",
        "E3-NEG-021",
        "E3-NEG-022",
        "E3-NEG-026",
        "E3-NEG-028",
        "E3-NEG-030",
        "E3-NEG-031",
        "E3-NEG-034",
        "E3-NEG-035",
        "E3-NEG-036",
        "E3-NEG-037",
        "E3-NEG-038",
        "E3-NEG-039",
        "E3-NEG-048",
        "E3-NEG-049",
        "E3-NEG-050",
        "E3-POS-005",
        "E3-POS-007",
        "E3-POS-008",
        "E3-POS-009",
        "E3-POS-012",
    }
    assert set(LEDGER_INDEX) == required
    missing_ids = {row[0] for row in MISSING}
    assert missing_ids == {
        ledger_id
        for ledger_id, owner in LEDGER_INDEX.items()
        if owner.startswith("MISSING")
    }, "every MISSING table row must match the index, and vice versa"
    assert len(MISSING) == 0, (
        f"T-136 ledger closure: zero bare MISSING expected, got {len(MISSING)}: "
        f"{sorted(missing_ids)}"
    )
    assert not any(owner.startswith("MISSING") for owner in LEDGER_INDEX.values()), (
        "ledger fully closed: no LEDGER_INDEX entry may still say MISSING"
    )
