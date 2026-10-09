"""WP01-E4 adversarial evidence-currentness proof (harness-owned, black-box).

Proves the completed E1 -> E3 chain fails closed under mutation: six
single-boundary external mutations (E4-NEG-001..006) against a sealed golden
fixture, each driven through PUBLIC harness entry points (CLI/API composition)
plus the kit typed verification surface -- never private helpers, never
duplicated kit internals.

Public entries exercised here (all public, all typed):

* harness E2: ``scholar_harness.extraction_producer.publish_document_manifest``
* harness E3 Stage 6: ``scholar_harness.extraction_producer.index_accepted_documents``
* harness E3 adapter: ``scholar_harness.index_acceptance.accept_index_candidate``
  (+ ``read_accepted_record``)
* kit typed verification surface: ``scholar_rag.index_manifest.compute_fingerprints``,
  ``scholar_rag.index_manifest.IndexManifest``,
  ``scholar_rag.index_verifier.verify_backend`` / ``VisibleRow``,
  ``scholar_rag.chunker.text_fingerprint``,
  ``scholar_rag.embedder.get_embedder("mock")`` (documented hermetic provider)

Hermeticity: deterministic mock embedder, ``HF_HUB_OFFLINE`` /
``TRANSFORMERS_OFFLINE`` forced, every filesystem effect confined to pytest
``tmp_path`` plus the copied fixture.  Tests copy the sealed source tree and
NEVER mutate it (``e4_sealed_fixture.copy_sealed_to`` verifies the source seal
first).

Acceptance mapping (handoff sections 5/6/8):

* E4-001: sealed baseline reproduces an accepted current index (control).
* E4-002: each section-5 mutation isolated and independently detected.
* E4-003: no mutation leaves a new accepted record or success event claiming
  the altered evidence is current (asserted per case).
* E4-004: legitimate-change rebuild yields explicit new lineage-bound result.
* E4-005: public composition + kit typed surface (this module imports no
  private helper and re-implements no kit logic -- enforced by
  ``test_e4_005_no_private_helpers``).
* E4-006: every demonstrated defect routes to its owner (assertion messages
  name the owner repo + path; no expected-failure is called a pass).
* E4-007: unmodified replay remains deterministic.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:  # pragma: no cover - test-only import seam
    sys.path.insert(0, str(TEST_DIR))
import e4_sealed_fixture as sealed

from scholar_harness.extraction_producer import (
    index_accepted_documents,
    publish_document_manifest,
)
from scholar_harness.index_acceptance import ACCEPTED_RELPATH, read_accepted_record

# --------------------------------------------------------------------------- #
# Small read-only helpers (stdlib + public file shapes only)
# --------------------------------------------------------------------------- #


def _workspace_files(workspace: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(workspace.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(workspace).as_posix()
        if rel.startswith("__pycache__/"):
            continue
        digest = hashlib.sha256()
        with open(path, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        out[rel] = "sha256:" + digest.hexdigest()
    return out


def _journal(workspace: Path) -> list[dict[str, Any]]:
    path = workspace / "audit" / "journal.jsonl"
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rag_built_events(workspace: Path) -> list[dict[str, Any]]:
    return [e for e in _journal(workspace) if e.get("action") == "RAG_INDEX_BUILT"]


def _sidecars(workspace: Path) -> list[Path]:
    return (
        sorted((workspace / "rag" / "index").rglob("IDX-*.json"))
        if (workspace / "rag" / "index").is_dir()
        else []
    )


def _sidecar_payload(workspace: Path) -> tuple[Path, dict[str, Any]]:
    cands = _sidecars(workspace)
    assert len(cands) == 1, (
        f"sealed E3 must hold exactly one sidecar, found {[str(p) for p in cands]}"
    )
    return cands[0], json.loads(cands[0].read_text(encoding="utf-8"))


def _hermetic(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Documented hermetic embedder (kit public ``get_embedder("mock")``)."""

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    import scholar_harness.orchestrator as orch_module
    from scholar_rag.embedder import get_embedder as kit_get_embedder

    mock = kit_get_embedder("mock")
    mock.dimension = 384
    monkeypatch.setattr(orch_module, "get_embedder", lambda **_: mock)
    return mock


def _assert_single_file_changed(
    before: dict[str, str], after: dict[str, str], expected_rel: str | None
) -> None:
    if expected_rel is None:
        assert before == after, (
            "backend-only mutation must leave every file byte-identical"
        )
        return
    assert before.get(expected_rel) != after.get(expected_rel), (
        f"{expected_rel} must differ"
    )
    for rel, digest in before.items():
        if rel == expected_rel:
            continue
        assert after.get(rel) == digest, (
            f"only {expected_rel} may change, but {rel} moved"
        )
    for rel in after:
        if rel == expected_rel:
            continue
        assert rel in before, f"only {expected_rel} may change, but {rel} is new"


# --------------------------------------------------------------------------- #
# E4-005: no private helpers, no duplicated kit internals (static tripwire)
# --------------------------------------------------------------------------- #


def test_e4_005_public_surfaces_only() -> None:
    """E4-005: this module composes public entries + kit typed surface only.

    Forbidden private/helper names are stored base64-encoded so this tripwire
    cannot match its own source text.  A "use" is an attribute access
    (``.name``), a call (`` name(`` with leading space, to skip the decoder
    line itself), or an import of that name.
    """

    import base64 as _b64

    text = Path(__file__).read_text(encoding="utf-8")
    encoded = [
        "X2V4dHJhY3Rpb25fZmlsZV9zdGVt",
        "X2J1aWxkX3BhcmVudF92aWV3",
        "X2J1aWxkX2luZGV4X3NlcnZpY2VfcmVxdWVzdA==",
        "X2J1aWxkX2NhbmRpZGF0ZV9tYW5pZmVzdA==",
        "X2FjY2VwdGVkX2RvY3VtZW50X3JlY29yZHM=",
        "Q2hyb21hUmVwbGFjZW1lbnRWaWV3",
        "U2Nob2xhckluZGV4ZXI=",
    ]
    for code in encoded:
        name = _b64.b64decode(code.encode()).decode()
        assert f".{name}" not in text, f"E4 must not touch private helper"
        assert f"import {name}" not in text, f"E4 must not import private helper"
    impl_encoded = [
        "ZGVmIG1pbnRfY2h1bmtfaWQ=",
        "ZGVmIHRleHRfZmluZ2VycHJpbnQ=",
        "Y2xhc3MgU2Nob2xhckluZGV4ZXI=",
        "ZGVmIGluZGV4X21hcmtkb3du",
    ]
    for code in impl_encoded:
        snippet = _b64.b64decode(code.encode()).decode()
        assert snippet not in text, "E4 must not re-implement kit logic"
    fixture_text = (TEST_DIR / "e4_sealed_fixture.py").read_text(encoding="utf-8")
    for code in encoded[:5]:
        name = _b64.b64decode(code.encode()).decode()
        assert f"import {name}" not in fixture_text, (
            "fixture builder must not import private helper"
        )
        assert f" {name}(" not in fixture_text.replace("def _stem_of", "").replace(
            "_stem_of(", ""
        ), "fixture builder must not call private helper"


# --------------------------------------------------------------------------- #
# Seal (E4-001/E4-007 groundwork)
# --------------------------------------------------------------------------- #


def test_e4_seal_valid_hermetic_and_two_studies(tmp_path: Path) -> None:
    """E4-001 groundwork: the sealed source is self-consistent and complete."""

    source = sealed.SEALED_SOURCE_DIR
    assert source.is_dir(), (
        "sealed source missing (owner: harness tests/e2e/e4_sealed_fixture.py)"
    )
    manifest = sealed.check_seal(source)
    expected = manifest["expected"]
    assert expected["workspace_id"] == sealed.WORKSPACE_ID
    assert expected["counts"] == {
        "accepted_documents": 2,
        "rejected_documents": 0,
        "visible_chunks": 2,
    }
    assert (
        len(expected["document_ids"]) == 2 and len(set(expected["document_ids"])) == 2
    )
    assert all(str(v).startswith("DOC-") for v in expected["document_ids"])
    assert len(expected["study_ids"]) == 2 and len(set(expected["study_ids"])) == 2
    assert all(str(v).startswith("STU-") for v in expected["study_ids"])
    assert expected["workspace_id"] not in expected["study_ids"], (
        "a workspace is not a study"
    )
    assert str(expected["manifest_id"]).startswith("IDX-")
    assert str(expected["e2_artifact_id"]).startswith("ART-")
    for key in (
        "index_fingerprint",
        "chunk_set_fingerprint",
        "configuration_fingerprint",
        "production_fingerprint",
    ):
        assert str(expected[key]).startswith("sha256:"), key
    assert expected["visible_count"] == 2
    assert all(str(v).startswith("CHK-") for v in expected["visible_ids"])
    # No leaking members in the accepted record or its event (E3-NEG-037 shape).
    accepted = json.loads((source / ACCEPTED_RELPATH).read_text(encoding="utf-8"))
    blob = json.dumps(accepted, sort_keys=True)
    assert "chroma_db" not in blob and "db_path" not in blob
    assert "/tmp/" not in blob and "C:\\" not in blob and "C:/" not in blob
    events = _rag_built_events(source)
    assert len(events) == 1 and events[0]["status"] == "SUCCESS"
    assert "verified" not in json.dumps(events[0]).lower()
    # The copy helper never mutates the source.
    before = dict(manifest["files"])
    sealed.copy_sealed_to(tmp_path)
    assert sealed.check_seal(source)["files"] == before


# --------------------------------------------------------------------------- #
# Control + replay determinism (E4-001, E4-007)
# --------------------------------------------------------------------------- #


def test_e4_control_unmutated_succeeds_and_replays_deterministically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-001/E4-007: unmutated fixture replays to the same accepted index."""

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    manifest = sealed.check_seal(workspace)
    expected = manifest["expected"]
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    built_before = _rag_built_events(workspace)
    assert len(built_before) == 1

    first = publish_document_manifest(workspace)
    assert first.accepted is True, first.refusal
    assert first.artifact_id == expected["e2_artifact_id"], (
        "replay must be idempotent on the sealed E2"
    )
    assert first.idempotent is True

    sc_path, payload = _sidecar_payload(workspace)
    reader = sealed.make_live_reader(payload)
    from scholar_harness.index_acceptance import accept_index_candidate

    decision = accept_index_candidate(
        workspace,
        copy.deepcopy(payload),
        run_id=str(payload.get("run_id", "")),
        manifest_path=sc_path.relative_to(workspace).as_posix(),
        reader=reader,
    )
    assert decision.accepted is True, (
        decision.failing_step,
        decision.code,
        decision.detail,
    )
    assert decision.reused is True, "exact replay is a deterministic no-op"
    assert decision.manifest_id == expected["manifest_id"]
    assert decision.index_fingerprint == expected["index_fingerprint"]
    # Second replay is byte-identical in outcome (no new write, no new event).
    decision2 = accept_index_candidate(
        workspace,
        copy.deepcopy(payload),
        run_id=str(payload.get("run_id", "")),
        manifest_path=sc_path.relative_to(workspace).as_posix(),
        reader=sealed.make_live_reader(payload),
    )
    assert (decision2.manifest_id, decision2.index_fingerprint, decision2.reused) == (
        decision.manifest_id,
        decision.index_fingerprint,
        True,
    )
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before, (
        "reuse writes nothing"
    )
    assert len(_rag_built_events(workspace)) == len(built_before), (
        "reuse emits no event"
    )
    assert sealed.check_seal(workspace)["expected"] == expected


# --------------------------------------------------------------------------- #
# E4-NEG-001: flip one acquired PDF byte post-E1
# --------------------------------------------------------------------------- #


def test_e4_neg_001_pdf_byte_flip_is_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-NEG-001: one flipped PDF byte yields new E2 lineage; old E3 not current.

    Observable: the changed source produces a NEW ``ART-`` (different
    ``source_hash``/``document_id``); the follow-up Stage 6 over the now
    two-manifest generation REFUSES (``VALIDATION_ERROR``: duplicate study
    across old+new manifests); ``rag/index/accepted.json`` never moves.
    """

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    expected = sealed.check_seal(workspace)["expected"]
    files_before = _workspace_files(workspace)
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    built_success_before = [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ]
    assert len(built_success_before) == 1
    sidecars_before = {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    }
    pdfs = sorted((workspace / "pdfs").glob("*.pdf"))
    assert len(pdfs) == 2
    target = pdfs[0]
    raw = target.read_bytes()
    target.write_bytes(raw[:10] + bytes([raw[10] ^ 0x01]) + raw[11:])
    assert len(target.read_bytes()) == len(raw)
    assert sum(1 for a, b in zip(raw, target.read_bytes()) if a != b) == 1
    changed_rel = target.relative_to(workspace).as_posix()
    _assert_single_file_changed(files_before, _workspace_files(workspace), changed_rel)

    second = publish_document_manifest(workspace)
    assert second.accepted is True, (
        second.refusal
    )  # new source => new lineage (not a refusal at E2)
    assert second.artifact_id != expected["e2_artifact_id"], (
        "OWNER nexus-scholar-org/nexus-scholar-harness "
        "src/scholar_harness/extraction_producer.py::_source_fingerprint: "
        "a flipped PDF byte must change source_hash/document_id/artifact_id"
    )
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before, (
        "E4-003: no new E3 for the altered chain"
    )
    assert {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    } == sidecars_before
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before

    follow = index_accepted_documents(workspace, chroma_dir=tmp_path / "chroma-neg001")
    assert str(follow.get("status")) == "FAILED", (
        "OWNER nexus-scholar-org/nexus-scholar-harness "
        "src/scholar_harness/orchestrator.py::_run_indexing_stage + "
        "nexus-scholar-org/scholar-rag-kit tools/scholar-rag-kit/src/scholar_rag/index_service.py::index_workspace: "
        f"duplicate-study generation after a PDF change must not index as current: {follow}"
    )
    envelope_codes: list[str] = []
    try:  # the kit run report carries the typed refusal when present
        reports = (
            (workspace / "run-reports" / "rag-index.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        last = json.loads(reports[-1]) if reports else {}
        if isinstance(last, dict) and last.get("action") == "RAG_INDEX_RUN_REJECTED":
            envelope_codes = ["REFUSED"]
    except (OSError, ValueError):
        pass
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before, (
        "E4-003: failed re-index publishes nothing"
    )
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before, (
        "E4-003: prior SUCCESS must not be re-presented, and no new SUCCESS may claim the altered chain"
    )
    assert {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    } == sidecars_before
    assert envelope_codes == ["REFUSED"] or str(follow.get("status")) == "FAILED"


# --------------------------------------------------------------------------- #
# E4-NEG-002: change one accepted extracted-Markdown byte post-E2
# --------------------------------------------------------------------------- #


def test_e4_neg_002_extracted_byte_change_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-NEG-002: one changed extracted byte refuses with STALE_EXTRACTED_BODY."""

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    expected = sealed.check_seal(workspace)["expected"]
    files_before = _workspace_files(workspace)
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    built_success_before = [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ]
    registry_before = (workspace / "audit" / "artifact_registry.json").read_bytes()
    sidecars_before = {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    }

    mds = sorted((workspace / "extracted").glob("*.md"))
    assert len(mds) == 2
    target = mds[0]
    text = target.read_text(encoding="utf-8")
    assert text.rstrip().endswith(".") or len(text) > 100
    target.write_text(text + "X", encoding="utf-8")  # exactly one appended body byte
    changed_rel = target.relative_to(workspace).as_posix()
    _assert_single_file_changed(files_before, _workspace_files(workspace), changed_rel)

    outcome = publish_document_manifest(workspace)
    assert outcome.accepted is False, (
        "OWNER nexus-scholar-org/nexus-scholar-harness "
        "src/scholar_harness/extraction_producer.py::_refuse_if_extracted_body_changed: "
        "a changed body under the same artifact id must refuse, never republish as idempotent"
    )
    assert (
        outcome.refusal is not None
        and outcome.refusal["code"] == "STALE_EXTRACTED_BODY"
    )
    details = outcome.refusal["details"]
    assert details["artifact_id"] == expected["e2_artifact_id"]
    assert {entry["field"] for entry in details["drifted"]} == {
        "extracted_sha256",
        "extracted_file_sha256",
    }
    for entry in details["drifted"]:
        assert entry["published"] != entry["current"]

    # E4-003 observables: no new E3 of any kind.
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before
    assert (
        workspace / "audit" / "artifact_registry.json"
    ).read_bytes() == registry_before
    assert {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    } == sidecars_before
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before
    refusals = [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_REFUSED"
    ]
    assert len(refusals) == 1 and refusals[0]["status"] == "FAILED"

    # The old E3 is stale for the new bytes (kit content binding, public surface).
    from scholar_rag.chunker import text_fingerprint

    _, payload = _sidecar_payload(workspace)
    sealed_doc = next(
        d
        for d in payload["documents"]
        if d["document_id"] == details["drifted"][0]["document_id"]
    )
    assert (
        text_fingerprint(target.read_text(encoding="utf-8"))
        != sealed_doc["extracted_content_sha256"]
    ), (
        "the altered bytes no longer match the sidecar's recorded content hash: "
        "the sealed index is historical, never current, for the altered chain"
    )


# --------------------------------------------------------------------------- #
# E4-NEG-003: change one effective chunker config value
# --------------------------------------------------------------------------- #


def test_e4_neg_003_chunker_config_change_moves_fingerprints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-NEG-003: ``max_chunk_chars`` 1200 -> 800 changes index fingerprints.

    Representative value: ``max_chunk_chars`` directly bounds chunk length, so
    it is effective on every workspace (unlike ``min_chunk_chars``, inert per
    E3 R-7); any other effective key (overlap, heading levels, whitespace,
    sentence pattern, frontmatter stripping) would move the same fingerprints.
    """

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    expected = sealed.check_seal(workspace)["expected"]
    files_before = _workspace_files(workspace)
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = (workspace / "audit" / "journal.jsonl").read_bytes()
    built_success_before = [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ]

    _, payload = _sidecar_payload(workspace)
    assert payload["chunker"]["configuration"]["max_chunk_chars"] == 1200
    mutated = copy.deepcopy(payload)
    mutated["chunker"]["configuration"]["max_chunk_chars"] = (
        800  # exactly one effective value
    )

    from scholar_rag.index_manifest import compute_fingerprints

    recomputed = compute_fingerprints(
        mutated
    )  # kit typed surface (adapter check-5 rule)
    assert (
        recomputed["configuration_fingerprint"] != payload["configuration_fingerprint"]
    ), (
        "OWNER nexus-scholar-org/scholar-rag-kit "
        "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py::compute_fingerprints: "
        "an effective config change must move the configuration fingerprint"
    )
    assert recomputed["index_fingerprint"] != payload["index_fingerprint"], (
        "same owner: an effective config change must move the index fingerprint; "
        "the sealed fingerprint must never be reported as current for the new config"
    )
    assert recomputed["index_fingerprint"] != expected["index_fingerprint"]

    # E4-003: fingerprint computation publishes nothing.
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before
    assert (workspace / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before
    assert _workspace_files(workspace) == files_before, (
        "compute-only proof writes no files"
    )
    from scholar_rag.index_verifier import IndexManifest as _TypedManifest
    from scholar_rag.index_verifier import verify_backend as _verify

    reader = sealed.make_live_reader(payload)
    assert _verify(_TypedManifest.from_payload(payload), reader).matches is True


# --------------------------------------------------------------------------- #
# E4-NEG-004: change embedding identity
# --------------------------------------------------------------------------- #


def test_e4_neg_004_embedding_identity_change_moves_fingerprints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-NEG-004: embedder model change moves index fingerprints.

    Representative limb: ``model`` (provider/model/revision/dimension/distance
    all feed the embedder section + fingerprints + backend dimension check; a
    model upgrade is the narrowest realistic single-value identity change --
    provider or distance would be coarser, dimension alone would also mismatch
    the stored vectors).
    """

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    expected = sealed.check_seal(workspace)["expected"]
    files_before = _workspace_files(workspace)
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = (workspace / "audit" / "journal.jsonl").read_bytes()
    built_success_before = [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ]

    _, payload = _sidecar_payload(workspace)
    assert payload["embedder"]["model"] == "all-MiniLM-L6-v2"
    mutated = copy.deepcopy(payload)
    mutated["embedder"]["model"] = "all-MiniLM-L12-v2"  # exactly one identity limb

    from scholar_rag.index_manifest import compute_fingerprints

    recomputed = compute_fingerprints(mutated)
    assert recomputed["index_fingerprint"] != payload["index_fingerprint"], (
        "OWNER nexus-scholar-org/scholar-rag-kit "
        "tools/scholar-rag-kit/src/scholar_rag/index_manifest.py::compute_fingerprints: "
        "an embedding-identity change must move the index fingerprint; "
        "the old backend must never be queried as compatible"
    )
    assert recomputed["index_fingerprint"] != expected["index_fingerprint"]

    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before, (
        "E4-003: no new acceptance"
    )
    assert (workspace / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before
    assert _workspace_files(workspace) == files_before


# --------------------------------------------------------------------------- #
# E4-NEG-005: alter parent lineage (representative: protocol fingerprint)
# --------------------------------------------------------------------------- #


def test_e4_neg_005_protocol_lineage_mismatch_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-NEG-005: a one-char protocol-fingerprint change refuses at step 3.

    Representative sub-case: ``protocol_fingerprint`` is the narrowest
    generation-binding limb, checked at adapter step 3 before any backend
    touch and before the idempotency gate.  Workspace/corpus alterations
    exercise the same step-3 gate with more file context; artifact-id/checksum
    alterations exercise steps 1-2 with the same fail-closed semantics.  The
    protocol limb therefore proves parent/lineage binding with exactly one
    changed value.
    """

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    files_before = _workspace_files(workspace)
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = (workspace / "audit" / "journal.jsonl").read_bytes()
    built_success_before = [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ]
    sidecars_before = {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    }

    sc_path, payload = _sidecar_payload(workspace)
    mutated = copy.deepcopy(payload)
    old_fp = str(mutated["protocol_fingerprint"])
    assert old_fp.startswith("sha256:")
    mutated["protocol_fingerprint"] = (
        "sha256:" + ("0" if old_fp[7] != "0" else "1") + old_fp[8:]
    )
    assert mutated["protocol_fingerprint"] != old_fp
    assert len(mutated["protocol_fingerprint"]) == len(old_fp)

    from scholar_harness.index_acceptance import accept_index_candidate

    reader = sealed.make_live_reader(payload)
    result = accept_index_candidate(
        workspace,
        mutated,
        run_id=str(payload.get("run_id", "")),
        manifest_path=sc_path.relative_to(workspace).as_posix(),
        reader=reader,
    )
    assert result.accepted is False, (
        "OWNER nexus-scholar-org/nexus-scholar-harness "
        "src/scholar_harness/index_acceptance.py::accept_index_candidate step 3: "
        "a protocol-lineage mismatch must refuse, never coerce or re-derive the parent"
    )
    assert result.failing_step == 3 and result.code == "PROTOCOL_FINGERPRINT_MISMATCH"
    assert result.manifest_id == payload["manifest_id"]
    assert "protocol" in (result.detail or "").lower()

    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before, (
        "E4-003: lineage refusal publishes nothing"
    )
    assert (workspace / "audit" / "journal.jsonl").read_bytes() == journal_before, (
        "adapter steps 1-6 refuse without a journal line; the kit run report carries the detail"
    )
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before
    assert {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    } == sidecars_before
    current = _workspace_files(workspace)
    assert current == files_before, (
        "the attempted accept must write no files (mutation was in-memory only)"
    )


# --------------------------------------------------------------------------- #
# E4-NEG-006: remove/add/corrupt visible backend chunks/metadata
# --------------------------------------------------------------------------- #


def test_e4_neg_006_missing_backend_chunk_is_inconsistent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-NEG-006: one removed visible chunk reports BACKEND_STATE_INCONSISTENT.

    Representative corruption: removal of a single declared chunk (no file
    changes at all).  Addition would need fabricated chunk ids and metadata
    corruption would need a second store with altered collection metadata;
    removal is the narrowest single-element visible-set change and already
    forces the typed verifier's inconsistent-state path.
    """

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    files_before = _workspace_files(workspace)
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = (workspace / "audit" / "journal.jsonl").read_bytes()
    built_success_before = [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ]

    _, payload = _sidecar_payload(workspace)
    from scholar_rag.index_manifest import IndexManifest
    from scholar_rag.index_verifier import verify_backend

    typed = IndexManifest.from_payload(payload)
    full_reader = sealed.make_live_reader(payload)
    baseline = verify_backend(typed, full_reader)
    assert baseline.matches is True and not baseline.codes, (
        "sealed live set must verify before mutation"
    )
    before_ids = full_reader.visible_ids()
    assert len(before_ids) == 2

    mutated_reader = sealed.make_live_reader(payload, visible_ids=before_ids[:-1])
    after_ids = mutated_reader.visible_ids()
    assert len(after_ids) == 1 and set(after_ids) < set(before_ids)
    missing = sorted(set(before_ids) - set(after_ids))
    assert len(missing) == 1 and missing[0].startswith("CHK-")

    verdict = verify_backend(typed, mutated_reader)  # kit typed verification surface
    assert verdict.matches is False, (
        "OWNER nexus-scholar-org/scholar-rag-kit "
        "tools/scholar-rag-kit/src/scholar_rag/index_verifier.py::verify_backend: "
        "a missing visible chunk must report an inconsistent state, never a count-only success"
    )
    assert "BACKEND_STATE_INCONSISTENT" in list(verdict.codes or []), verdict.codes
    assert (
        verdict.manifest_id == payload["manifest_id"]
        if hasattr(verdict, "manifest_id")
        else True
    )
    assert missing[0] in list(getattr(verdict, "missing_chunk_ids", ()) or ()), (
        "the typed report must carry the missing chunk identity"
    )

    # E4-003: verification publishes nothing.
    assert _workspace_files(workspace) == files_before, (
        "backend mutation was reader-only; every file byte-identical"
    )
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == accepted_before
    assert (workspace / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert [
        e for e in _rag_built_events(workspace) if e["status"] == "SUCCESS"
    ] == built_success_before


# --------------------------------------------------------------------------- #
# E4-004: legitimate-change rebuild yields explicit new lineage
# --------------------------------------------------------------------------- #


def test_e4_rebuild_after_input_change_yields_new_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E4-004: one added sentence re-indexes to explicit new lineage (not reuse)."""

    _hermetic(monkeypatch)
    workspace = sealed.copy_sealed_to(tmp_path)
    expected = sealed.check_seal(workspace)["expected"]
    accepted_before = (workspace / ACCEPTED_RELPATH).read_bytes()
    sidecars_before = {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    }

    mds = sorted((workspace / "extracted").glob("*.md"))
    target = mds[0]
    target.write_text(
        target.read_text(encoding="utf-8")
        + "A legitimate added sentence for rebuild.\n",
        encoding="utf-8",
    )

    rebuilt = index_accepted_documents(
        workspace, chroma_dir=tmp_path / "chroma-rebuild"
    )
    assert str(rebuilt.get("status")) == "SUCCESS", rebuilt
    acceptance = rebuilt.get("acceptance") or {}
    assert acceptance.get("accepted") is True and acceptance.get("reused") is False
    assert acceptance.get("manifest_id") != expected["manifest_id"], (
        "new bytes => new manifest identity"
    )
    assert acceptance.get("index_fingerprint") != expected["index_fingerprint"]
    assert str(acceptance.get("manifest_id", "")).startswith("IDX-")

    accepted_after = json.loads((workspace / ACCEPTED_RELPATH).read_bytes())
    assert accepted_after["manifest_id"] == acceptance["manifest_id"]
    assert accepted_after["index_fingerprint"] == acceptance["index_fingerprint"]
    assert (workspace / ACCEPTED_RELPATH).read_bytes() != accepted_before
    # Both sidecars remain: the sealed one as history, the rebuilt one current.
    assert len(_sidecars(workspace)) == 2
    assert {
        p.relative_to(workspace).as_posix() for p in _sidecars(workspace)
    } > sidecars_before
    events = _rag_built_events(workspace)
    assert len([e for e in events if e["status"] == "SUCCESS"]) == 2
    assert events[-1]["parameters"]["manifest_id"] == acceptance["manifest_id"]
    _, raw = read_accepted_record(workspace)
    assert raw is not None and raw["manifest_id"] == acceptance["manifest_id"]
