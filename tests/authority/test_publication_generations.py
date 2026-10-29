"""AG-03C publication-generation tests (shared authorization + coherent generations).

Hermetic and scriptable: every workspace is synthetic ``tmp_path`` bytes, no
network, no provider, no admin rights, no sleeps. Concurrency is exercised
with threads (documented limit: threads on one host, not processes — the lock
file serializes writers that honor this protocol on one host; a writer that
ignores the lock, a second host, and POSIX enforcement are out of scope per
the packet §1). Crash injection uses monkeypatched faults at the three
material boundaries (content staging / generation commit / post-commit audit).

Acceptance map (packet §6 items 1-10):
* AG03C-01 gate-before-write — missing approval writes nothing
  (``test_gate_before_write_*``).
* AG03C-02 coherent generation — hashes/fingerprints agree; authorized bytes
  are byte-identical to the legacy path (``test_coherent_generation_*``).
* AG03C-03 consumer-current — CURRENT generations are consumed/detected, and
  proceed through the pipeline gate (``test_consumer_current_*``).
* AG03C-04 four-state refusal — STALE/SUPERSEDED/MISMATCHED/LEGACY each refuse
  with its typed code (``test_refusal_*``).
* AG03C-05 mixed-generation — outputs assembled across generations refuse
  everywhere (``test_mixed_generation_*``).
* AG03C-06 crash recovery — fault at each material boundary leaves a defined,
  never-falsely-CURRENT state plus a working re-collect (``test_crash_*``).
* AG03C-07 competing writers — one generation wins, no mixed CURRENT
  (``test_competing_writers_*``).
* AG03C-08 retry semantics — identical retry is idempotent, changed retry
  needs a new approval (``test_retry_*``).
* AG03C-09 audit failure — raising sink leaves no consumable output, and a
  failing refusal sink still surfaces the refusal (``test_audit_*``).
* AG03C-10 AG-02 preserved — integrity refusals still fire first through the
  gated collect path (``test_ag02_*``).
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

import scholar_harness.authority.generations as generations
import scholar_harness.pipeline.coordinator as coordinator
from scholar_harness.authority import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_MISSING,
    APPROVAL_SCOPE_MISMATCH,
    COLLECT_LOCK_FILENAME,
    GENERATION_LEGACY_UNVERIFIED,
    GENERATION_LOCKED,
    GENERATION_MISMATCHED,
    GENERATION_STALE,
    GENERATION_SUPERSEDED,
    PROMOTION_AUDIT_FAILED,
    PUBLICATION_OUTPUTS,
    SCREENING_PUBLICATION_POLICY_VERSION,
    AuthorityRefused,
    GenerationRecord,
    GenerationStatus,
    OperatorIdentity,
    build_publication_snapshot,
    content_sha256,
    mint_publication_approval,
    publication_binding,
    publication_file_bytes,
    publish_generation,
    recover_partial,
    require_current_generation,
    resolve_publication_scope,
    write_publication_approval,
)
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.extraction_producer import (
    PublicationRefused,
    _included_records,
)
from scholar_harness.handoff import HandoffPhase, detect_completed_phases
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

WS_ID = "WSP-" + "c" * 32
OTHER_WS_ID = "WSP-" + "d" * 32
RUN_ID = "RUN-ag03c-synthetic"
NOW = "2026-10-13T12:00:00+00:00"
LATER = "2026-10-13T13:00:00+00:00"
POLICY = SCREENING_PUBLICATION_POLICY_VERSION

OPERATOR = OperatorIdentity(
    identity="ag03c-operator", source="publisher-operator-context"
)

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_FIXTURE = (
    ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)
PROTOCOL_RAW = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
PROTOCOL_FP = canonical_fingerprint(ResearchProtocol.model_validate(PROTOCOL_RAW))
CORPUS_FP = "sha256:" + sha256(b"ag03c-synthetic-corpus").hexdigest()


class _SimulatedKill(BaseException):
    """A process kill: bypasses ``except Exception`` cleanup, like SIGKILL."""


def _bindings(n: int = 1) -> list[dict]:
    return [
        {
            "batch_index": i,
            "batch_artifact_id": f"ART-ag03c-batch-{i}",
            "batch_sha256": "sha256:" + sha256(f"batch-{i}".encode()).hexdigest(),
        }
        for i in range(n)
    ]


def _content(marker: str = "v1") -> dict[str, str]:
    return {name: f"ag03c-{marker}:{name}\n" for name in PUBLICATION_OUTPUTS}


def _content_digests(content: dict[str, str]) -> dict[str, str]:
    return {
        name: content_sha256(publication_file_bytes(text))
        for name, text in content.items()
    }


def _mint(
    *,
    content: dict[str, str],
    bindings: list[dict] | None = None,
    workspace_id: str = WS_ID,
    run_id: str = RUN_ID,
    protocol_fp: str = PROTOCOL_FP,
    corpus_fp: str = CORPUS_FP,
    approved_at: str = NOW,
):
    bindings = bindings if bindings is not None else _bindings()
    digests = _content_digests(content)
    snapshot = build_publication_snapshot(
        workspace_id=workspace_id,
        run_id=run_id,
        batch_bindings=bindings,
        protocol_fingerprint=protocol_fp,
        corpus_fingerprint=corpus_fp,
        output_digests=digests,
    )
    binding = publication_binding(
        workspace_id=workspace_id,
        run_id=run_id,
        batch_bindings=bindings,
        protocol_fingerprint=protocol_fp,
        corpus_fingerprint=corpus_fp,
    )
    record = mint_publication_approval(
        operator=OPERATOR,
        binding=binding,
        snapshot_bytes=snapshot,
        approved_at=approved_at,
    )
    return snapshot, binding, record


def _publish(
    workspace: Path,
    content: dict[str, str],
    record,
    snapshot: bytes,
    binding,
    *,
    published_at: str = NOW,
    sink: list | None = None,
    **overrides,
):
    events: list = sink if sink is not None else []
    params = {
        "workspace": workspace,
        "snapshot_bytes": snapshot,
        "binding": binding,
        "record": record,
        "content": content,
        "published_at": published_at,
        "policy_version": POLICY,
        "audit_append": events.append,
    }
    params.update(overrides)
    return publish_generation(**params), events  # type: ignore[arg-type]


def _material_current(
    root: Path,
    name: str = "ws",
    *,
    content: dict[str, str] | None = None,
    workspace_id: str = WS_ID,
    run_id: str = RUN_ID,
    bindings: list[dict] | None = None,
    protocol_fp: str = PROTOCOL_FP,
    corpus_fp: str = CORPUS_FP,
    approved_at: str = NOW,
    published_at: str = NOW,
) -> dict:
    """Build a workspace holding a CURRENT authorized generation."""
    ws = root / name
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "project.json").write_text(
        json.dumps({"project_id": name, "registered_workspace_id": workspace_id}),
        encoding="utf-8",
    )
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL_RAW), encoding="utf-8")
    content = content if content is not None else _content()
    snapshot, binding, record = _mint(
        content=content,
        bindings=bindings,
        workspace_id=workspace_id,
        run_id=run_id,
        protocol_fp=protocol_fp,
        corpus_fp=corpus_fp,
        approved_at=approved_at,
    )
    write_publication_approval(
        ws / "literature" / "screening", record, staged_at=approved_at
    )
    result, events = _publish(
        ws, content, record, snapshot, binding, published_at=published_at
    )
    assert not result.idempotent
    assert len(events) == 1
    status = require_current_generation(ws)
    assert status.status is GenerationStatus.CURRENT, status.message
    return {
        "ws": ws,
        "content": content,
        "snapshot": snapshot,
        "binding": binding,
        "record": record,
        "result": result,
        "events": events,
    }


def _generation_outputs(ws: Path) -> list[Path]:
    lit = ws / "literature"
    return [lit / name for name in PUBLICATION_OUTPUTS] + [
        lit / "screening" / "generation.json"
    ]


# ---------------------------------------------------------------------------
# AG03C-01 gate-before-write
# ---------------------------------------------------------------------------


def test_gate_before_write_missing_approval_writes_nothing(tmp_path: Path) -> None:
    """AG03C-01: ``publish_generation`` with no approval writes NO file."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    content = _content()
    snapshot, binding, _ = _mint(content=content)
    events: list = []
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=None,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=events.append,
        )
    assert excinfo.value.code == APPROVAL_MISSING
    assert events == []
    for path in _generation_outputs(ws):
        assert not path.exists(), f"gate wrote {path.name} without approval"
    assert list((ws / "literature").glob("*.tmp")) == []
    assert list((ws / "literature" / "screening").glob("*.tmp")) == []
    assert require_current_generation(ws).status is (GenerationStatus.LEGACY_UNVERIFIED)


def test_gate_forged_human_fields_confer_no_approval(tmp_path: Path) -> None:
    """AG03C-01/matrix: forged actor/method/confidence without approval refuses."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    # Self-reported human-looking fields live inside the content; they change
    # bytes but can never substitute for the operator approval record.
    content = dict(_content())
    content["included.json"] = json.dumps(
        [{"actor": "Dr. Human Reviewer", "method": "HUMAN", "confidence": 0.99}]
    )
    snapshot, binding, _ = _mint(content=content)
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=None,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=lambda event: None,
        )
    assert excinfo.value.code == APPROVAL_MISSING
    assert not (ws / "literature" / "included.json").exists()


def test_gate_cross_scope_replay_refuses_without_writing(tmp_path: Path) -> None:
    """AG03C-01/matrix: an approval minted for another scope refuses cleanly."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    content = _content()
    _, _, foreign_record = _mint(content=content, workspace_id=OTHER_WS_ID)
    snapshot, binding, _ = _mint(content=content)
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=foreign_record,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=lambda event: None,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH
    for path in _generation_outputs(ws):
        assert not path.exists()


def test_gate_changed_parents_refuse_without_writing(tmp_path: Path) -> None:
    """AG03C-01/matrix: changed protocol/corpus parents refuse (scope)."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    content = _content()
    snapshot, binding, _ = _mint(content=content)
    _, stale_binding, stale_record = _mint(
        content=content, corpus_fp="sha256:" + "e" * 64
    )
    assert stale_binding.as_dict() != binding.as_dict()
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=stale_record,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=lambda event: None,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH
    for path in _generation_outputs(ws):
        assert not path.exists()


# ---------------------------------------------------------------------------
# AG03C-02 coherent generation
# ---------------------------------------------------------------------------


def test_coherent_generation_record_matches_all_outputs(tmp_path: Path) -> None:
    """AG03C-02: generation.json agrees with every output hash + fingerprints."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    record = mat["result"].record
    assert record.schema == "harness-screening-generation-v1"
    assert record.generation_id.startswith("GEN-")
    for name in PUBLICATION_OUTPUTS:
        on_disk = (ws / "literature" / name).read_bytes()
        assert content_sha256(on_disk) == record.output_digests[name]
    assert record.snapshot_fingerprint == content_sha256(mat["snapshot"])
    assert record.approval_fingerprint == mat["record"].fingerprint()
    assert record.operator_identity == "ag03c-operator"
    assert record.policy_version == POLICY
    assert record.supersedes is None
    stored = json.loads(
        (ws / "literature" / "screening" / "generation.json").read_text("utf-8")
    )
    assert GenerationRecord.from_dict(stored).as_dict() == record.as_dict()


# ---------------------------------------------------------------------------
# AG03C-04 four-state refusal (require_current_generation)
# ---------------------------------------------------------------------------


def test_refusal_stale_after_content_change(tmp_path: Path) -> None:
    """AG03C-04: changed output bytes report STALE with a typed code."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    (ws / "literature" / "excluded.json").write_text(
        '{"tampered": true}\n', encoding="utf-8"
    )
    result = require_current_generation(ws)
    assert result.status is GenerationStatus.STALE
    assert result.code == GENERATION_STALE
    assert result.details["output"] == "excluded.json"


def test_refusal_stale_when_approval_unresolvable(tmp_path: Path) -> None:
    """AG03C-04: a generation whose resident approval vanished reports STALE."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    (ws / "literature" / "screening" / "publication_approval.json").unlink()
    result = require_current_generation(ws)
    assert result.status is GenerationStatus.STALE
    assert result.code == GENERATION_STALE


def test_refusal_stale_when_protocol_parent_changes(tmp_path: Path) -> None:
    """AG03C-04: an unreadable protocol parent reports STALE, never CURRENT."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    (ws / "protocol.json").unlink()
    result = require_current_generation(ws)
    assert result.status is GenerationStatus.STALE
    assert result.code == GENERATION_STALE


def test_refusal_mismatched_across_workspace(tmp_path: Path) -> None:
    """AG03C-04: a generation published for another workspace reports MISMATCHED."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "registered_workspace_id": WS_ID})
    )
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL_RAW))
    content = _content()
    # Minted for another workspace, published into this one: the on-disk
    # generation names a workspace that is not this one.
    snapshot, binding, record = _mint(content=content, workspace_id=OTHER_WS_ID)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=NOW)
    result, _ = _publish(ws, content, record, snapshot, binding)
    assert not result.idempotent
    status = require_current_generation(ws)
    assert status.status is GenerationStatus.MISMATCHED
    assert status.code == GENERATION_MISMATCHED


def test_refusal_legacy_without_generation(tmp_path: Path) -> None:
    """AG03C-04: outputs without a generation record report LEGACY_UNVERIFIED."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "included.json").write_text("[]")
    result = require_current_generation(ws)
    assert result.status is GenerationStatus.LEGACY_UNVERIFIED
    assert result.code == GENERATION_LEGACY_UNVERIFIED


def test_downgrade_manifest_lineage_without_generation_reports_mismatched(
    tmp_path: Path,
) -> None:
    """F-01b(i): MANIFEST accepted lineage with no generation → MISMATCHED.

    A refused (no-approval) collect still records review lineage — MANIFEST
    accepted rows plus registry screening_decisions entries — so an absent
    generation beside that lineage is a downgrade, never true-legacy, and
    the production consumer refuses it.
    """
    workspace, studies = _collect_ws(tmp_path)
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    manifest = json.loads(
        (workspace / "literature" / "screening" / "MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )
    assert any("decision_file_sha256" in b for b in manifest["batches"])
    result = require_current_generation(workspace)
    assert result.status is GenerationStatus.MISMATCHED
    assert result.code == GENERATION_MISMATCHED
    assert "manifest-lineage" in result.details["downgrade_evidence"]
    with pytest.raises(PublicationRefused) as excinfo:
        _included_records(workspace)
    assert excinfo.value.code == GENERATION_MISMATCHED


def test_downgrade_staged_approval_without_generation_reports_mismatched(
    tmp_path: Path,
) -> None:
    """F-01b(ii): a staged approval file with no generation → MISMATCHED.

    Deleting generation.json after authorization must never silently convert
    the workspace into consumable LEGACY: the surviving staged approval (and,
    after a real publish, the surviving review lineage) keeps it MISMATCHED
    and every consumer refuses.
    """
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    content = _content()
    _, _, record = _mint(content=content)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=NOW)
    result = require_current_generation(ws)
    assert result.status is GenerationStatus.MISMATCHED
    assert result.code == GENERATION_MISMATCHED
    assert "staged-approval" in result.details["downgrade_evidence"]

    # Same outcome when a published generation is deleted after authorization.
    mat = _material_current(tmp_path, name="ws-published")
    (mat["ws"] / "literature" / "screening" / "generation.json").unlink()
    deleted = require_current_generation(mat["ws"])
    assert deleted.status is GenerationStatus.MISMATCHED
    assert deleted.code == GENERATION_MISMATCHED
    with pytest.raises(PublicationRefused) as excinfo:
        _included_records(mat["ws"])
    assert excinfo.value.code == GENERATION_MISMATCHED


def test_refusal_superseded_presented_old_record(tmp_path: Path) -> None:
    """AG03C-04: presenting a superseded generation reports SUPERSEDED."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    old_record = mat["result"].record
    v2 = _content("v2")
    snapshot2, binding2, record2 = _mint(content=v2, approved_at=LATER)
    write_publication_approval(
        ws / "literature" / "screening", record2, staged_at=LATER
    )
    result2, _ = _publish(ws, v2, record2, snapshot2, binding2, published_at=LATER)
    assert not result2.idempotent
    assert result2.supersedes == old_record.fingerprint()
    assert require_current_generation(ws).status is GenerationStatus.CURRENT
    superseded = require_current_generation(ws, presented=old_record.as_dict())
    assert superseded.status is GenerationStatus.SUPERSEDED
    assert superseded.code == GENERATION_SUPERSEDED
    assert superseded.details["current_generation_id"] == result2.generation_id
    assert (
        require_current_generation(ws, presented=result2.record).status
        is GenerationStatus.CURRENT
    )


def test_refusal_superseded_reverted_manifest_detected(tmp_path: Path) -> None:
    """AG03C-04: a reverted manifest is SUPERSEDED when the newer record is shown."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    gen_n = mat["result"].record
    gen_n_bytes = (ws / "literature" / "screening" / "generation.json").read_bytes()
    gen_n_outputs = {
        name: (ws / "literature" / name).read_bytes() for name in PUBLICATION_OUTPUTS
    }
    v2 = _content("v2")
    snapshot2, binding2, record2 = _mint(content=v2, approved_at=LATER)
    write_publication_approval(
        ws / "literature" / "screening", record2, staged_at=LATER
    )
    result2, _ = _publish(ws, v2, record2, snapshot2, binding2, published_at=LATER)
    # Revert every published file to generation N (disk verifies as N again).
    write_publication_approval(
        ws / "literature" / "screening", mat["record"], staged_at=NOW
    )
    (ws / "literature" / "screening" / "generation.json").write_bytes(gen_n_bytes)
    for name, data in gen_n_outputs.items():
        (ws / "literature" / name).write_bytes(data)
    assert require_current_generation(ws).status is GenerationStatus.CURRENT
    reverted = require_current_generation(ws, presented=result2.record)
    assert reverted.status is GenerationStatus.SUPERSEDED
    assert reverted.details["newer_generation_id"] == result2.generation_id


# ---------------------------------------------------------------------------
# AG03C-05 mixed-generation assembly
# ---------------------------------------------------------------------------


def test_mixed_generation_assembly_refuses(tmp_path: Path) -> None:
    """AG03C-05: outputs mixed across N/N+1 report MISMATCHED (not silent)."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    old_id = mat["result"].generation_id
    v2 = _content("v2")
    snapshot2, binding2, record2 = _mint(content=v2, approved_at=LATER)
    write_publication_approval(
        ws / "literature" / "screening", record2, staged_at=LATER
    )
    _publish(ws, v2, record2, snapshot2, binding2, published_at=LATER)
    # Assemble a mixed generation: N's included.json inside N+1's workspace.
    (ws / "literature" / "included.json").write_text(
        mat["content"]["included.json"], encoding="utf-8"
    )
    result = require_current_generation(ws)
    assert result.status is GenerationStatus.MISMATCHED
    assert result.code == GENERATION_MISMATCHED
    assert result.details["matched_generation_id"] == old_id
    with pytest.raises(PublicationRefused) as excinfo:
        _included_records(ws)
    assert excinfo.value.code == GENERATION_MISMATCHED


# ---------------------------------------------------------------------------
# AG03C-06 crash recovery
# ---------------------------------------------------------------------------


def test_crash_before_content_renames_leaves_nothing_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AG03C-06/boundary-1: kill during staging leaves nothing consumable."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "registered_workspace_id": WS_ID})
    )
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL_RAW))
    content = _content()
    snapshot, binding, record = _mint(content=content)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=NOW)
    real_write = generations._write_tmp_text
    calls = {"n": 0}

    def _kill_after_first(path: Path, text: str) -> None:
        calls["n"] += 1
        if calls["n"] >= 2:
            raise _SimulatedKill()
        real_write(path, text)

    monkeypatch.setattr(generations, "_write_tmp_text", _kill_after_first)
    events: list = []
    with pytest.raises(_SimulatedKill):
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=record,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=events.append,
        )
    # One tmp staged, no final renamed, lock released by the finally clause.
    assert not (ws / "literature" / "screening" / "generation.json").exists()
    assert not (ws / "literature" / "included.json").exists()
    assert not (ws / "literature" / "screening" / COLLECT_LOCK_FILENAME).exists()
    # The kill struck after the approval was staged but before any commit, so
    # surviving authorized material without a generation is a downgrade, not
    # true-legacy: MISMATCHED (never CURRENT, never consumable LEGACY).
    assert require_current_generation(ws).status is GenerationStatus.MISMATCHED
    recovered = recover_partial(ws)
    assert recovered["removed"] == ["included.json.tmp"]
    assert list((ws / "literature").glob("*.tmp")) == []
    # An authorized re-collect after recovery publishes cleanly.
    monkeypatch.undo()
    result, _ = _publish(ws, content, record, snapshot, binding)
    assert not result.idempotent
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


def test_crash_between_content_and_generation_rename_is_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AG03C-06/boundary-2: new contents without the commit record are not CURRENT."""
    mat = _material_current(tmp_path, name="ws")
    ws = mat["ws"]
    v2 = _content("v2")
    snapshot2, binding2, record2 = _mint(content=v2, approved_at=LATER)
    write_publication_approval(
        ws / "literature" / "screening", record2, staged_at=LATER
    )
    real_rename = generations._rename_tmp

    def _fail_at_commit(tmp: Path, final: Path) -> None:
        if final.name == "generation.json":
            raise _SimulatedKill()
        real_rename(tmp, final)

    monkeypatch.setattr(generations, "_rename_tmp", _fail_at_commit)
    events: list = []
    with pytest.raises(_SimulatedKill):
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot2,
            binding=binding2,
            record=record2,
            content=v2,
            published_at=LATER,
            policy_version=POLICY,
            audit_append=events.append,
        )
    # New content files landed but the commit record did not. The v2 history
    # was staged before the commit point (packet ordering), so the workspace
    # reads as a mixed assembly — v2 bytes and v2 history against v1's
    # manifest — and reports MISMATCHED: never CURRENT either way. The
    # uncommitted manifest tmp is swept by recovery.
    assert (ws / "literature" / "included.json").read_text(encoding="utf-8") == v2[
        "included.json"
    ]
    mixed = require_current_generation(ws)
    assert mixed.status is GenerationStatus.MISMATCHED
    assert mixed.code == GENERATION_MISMATCHED
    recovered = recover_partial(ws)
    assert recovered["removed"] == ["generation.json.tmp"]
    monkeypatch.undo()
    result, _ = _publish(ws, v2, record2, snapshot2, binding2, published_at=LATER)
    assert not result.idempotent
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


def test_crash_after_commit_without_audit_stays_current_without_provenance(
    tmp_path: Path,
) -> None:
    """AG03C-06/boundary-3: a kill after the commit leaves CURRENT files, no event."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    v2 = _content("v2")
    snapshot2, binding2, record2 = _mint(content=v2, approved_at=LATER)
    write_publication_approval(
        ws / "literature" / "screening", record2, staged_at=LATER
    )

    def _killed_audit(event: dict) -> None:
        raise _SimulatedKill()

    with pytest.raises(_SimulatedKill):
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot2,
            binding=binding2,
            record=record2,
            content=v2,
            published_at=LATER,
            policy_version=POLICY,
            audit_append=_killed_audit,
        )
    # The commit point landed, so the generation is CURRENT — but the kill
    # skipped both cleanup and the audit event (exactly one gap, honestly few).
    assert require_current_generation(ws).status is GenerationStatus.CURRENT
    assert not (ws / "literature" / "screening" / COLLECT_LOCK_FILENAME).exists()


# ---------------------------------------------------------------------------
# AG03C-07 competing writers
# ---------------------------------------------------------------------------


def test_competing_writers_one_generation_wins(tmp_path: Path) -> None:
    """AG03C-07: two genuinely concurrent identical publishes agree, no mixing.

    Limit (packet §5): threads on one host, not processes — both writers run
    this protocol, so the lock serializes them; the test asserts coherence
    whatever the interleaving (winner publishes, loser joins idempotent).
    """
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "registered_workspace_id": WS_ID})
    )
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL_RAW))
    content = _content()
    snapshot, binding, record = _mint(content=content)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=NOW)
    barrier = threading.Barrier(2)
    outcomes: list = []

    def _attempt(sink: list) -> None:
        barrier.wait(timeout=30)
        result, _ = _publish(ws, content, record, snapshot, binding, sink=sink)
        outcomes.append((result.generation_id, result.idempotent, len(sink)))

    sinks = ([], [])
    threads = [threading.Thread(target=_attempt, args=(sinks[i],)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert all(not thread.is_alive() for thread in threads)
    assert len(outcomes) == 2
    assert outcomes[0][0] == outcomes[1][0]
    assert sorted(outcome[1] for outcome in outcomes) == [False, True]
    assert sum(outcome[2] for outcome in outcomes) == 1
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


def test_competing_writers_held_lock_refuses(tmp_path: Path) -> None:
    """AG03C-07: a second publisher against a held lock refuses (no mixing)."""
    ws = tmp_path / "ws"
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True)
    content = _content()
    snapshot, binding, record = _mint(content=content)
    (screening / generations.COLLECT_LOCK_FILENAME).write_bytes(b"holder")
    events: list = []
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=record,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=events.append,
            lock_timeout_s=0.2,
        )
    assert excinfo.value.code == GENERATION_LOCKED
    for path in _generation_outputs(ws):
        assert not path.exists()
    recovered = recover_partial(ws)
    assert generations.COLLECT_LOCK_FILENAME in recovered["removed"]
    result, _ = _publish(ws, content, record, snapshot, binding)
    assert not result.idempotent


def test_lock_permission_error_refuses_locked_not_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows reports ``ERROR_ACCESS_DENIED`` for a contended lock path.

    ``os.open(O_CREAT | O_EXCL)`` raises ``FileExistsError`` on POSIX whenever
    the path exists, but Windows raises ``PermissionError`` when the path is an
    existing directory or a file another process holds without sharing. An
    unhandled ``PermissionError`` would crash the publisher before the named
    refusal; the acquisition must treat it as contention and end in
    ``GENERATION_LOCKED`` within the timeout.
    """
    lock_path = tmp_path / generations.COLLECT_LOCK_FILENAME
    real_open = os.open

    def deny_lock(path, flags, *args, **kwargs):
        if Path(path) == lock_path:
            raise PermissionError(13, "Access is denied", str(path))
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", deny_lock)
    with pytest.raises(AuthorityRefused) as excinfo:
        generations._acquire_lock(lock_path, 0.05)
    assert excinfo.value.code == GENERATION_LOCKED
    assert "access denied" in excinfo.value.message.lower()
    assert not lock_path.exists()


def test_competing_writers_tampered_second_writer_refuses(tmp_path: Path) -> None:
    """AG03C-07: a concurrent tampered publish refuses; the winner stands."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    before = (ws / "literature" / "screening" / "generation.json").read_bytes()
    tampered = dict(mat["content"])
    tampered["included.json"] = '{"forged": true}\n'
    refusals: list = []
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=mat["snapshot"],
            binding=mat["binding"],
            record=mat["record"],
            content=tampered,
            published_at=LATER,
            policy_version=POLICY,
            audit_append=lambda event: None,
            refusal_sink=refusals.append,
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED
    assert len(refusals) == 1
    assert refusals[0]["code"] == APPROVAL_CONTENT_CHANGED
    assert (ws / "literature" / "screening" / "generation.json").read_bytes() == before
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


# ---------------------------------------------------------------------------
# AG03C-08 retry semantics
# ---------------------------------------------------------------------------


def test_retry_identical_is_idempotent_without_rewrite(tmp_path: Path) -> None:
    """AG03C-08: an identical retry rewrites nothing and appends no audit."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    before = {path.name: path.read_bytes() for path in _generation_outputs(ws)}
    result, events = _publish(
        ws, mat["content"], mat["record"], mat["snapshot"], mat["binding"]
    )
    assert result.idempotent
    assert events == []
    after = {path.name: path.read_bytes() for path in _generation_outputs(ws)}
    assert before == after
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


def test_retry_changed_content_needs_new_approval(tmp_path: Path) -> None:
    """AG03C-08: changed bytes under the old approval refuse; winner intact."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    changed = _content("v2")
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=mat["snapshot"],
            binding=mat["binding"],
            record=mat["record"],
            content=changed,
            published_at=LATER,
            policy_version=POLICY,
            audit_append=lambda event: None,
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED
    assert (ws / "literature" / "included.json").read_bytes() == (
        publication_file_bytes(mat["content"]["included.json"])
    )
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


def test_retry_changed_content_with_new_approval_supersedes(tmp_path: Path) -> None:
    """AG03C-08: changed bytes with a fresh approval publish a new generation."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    old_fp = mat["result"].record.fingerprint()
    changed = _content("v2")
    snapshot2, binding2, record2 = _mint(content=changed, approved_at=LATER)
    write_publication_approval(
        ws / "literature" / "screening", record2, staged_at=LATER
    )
    result, _ = _publish(ws, changed, record2, snapshot2, binding2, published_at=LATER)
    assert not result.idempotent
    assert result.supersedes == old_fp
    assert result.generation_id == mat["result"].generation_id
    assert require_current_generation(ws).status is GenerationStatus.CURRENT


# ---------------------------------------------------------------------------
# AG03C-09 audit failure
# ---------------------------------------------------------------------------


def test_audit_failure_removes_staged_outputs(tmp_path: Path) -> None:
    """AG03C-09: a raising audit sink leaves no consumable output."""
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    content = _content()
    snapshot, binding, record = _mint(content=content)

    def _failing_sink(event: dict) -> None:
        raise OSError("sink down")

    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=record,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=_failing_sink,
        )
    assert excinfo.value.code == PROMOTION_AUDIT_FAILED
    for path in _generation_outputs(ws):
        assert not path.exists(), f"audit failure left {path.name}"
    assert list((ws / "literature").glob("*.tmp")) == []
    assert list((ws / "literature" / "screening").glob("*.tmp")) == []
    assert require_current_generation(ws).status is (GenerationStatus.LEGACY_UNVERIFIED)


def test_refusal_sink_failure_still_surfaces_refusal(tmp_path: Path) -> None:
    """AG03C-09: a failing refusal sink never masquerades as success."""

    def _failing_refusal(record: dict) -> None:
        raise OSError("refusal sink down")

    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    content = _content()
    snapshot, binding, _ = _mint(content=content)
    with pytest.raises(AuthorityRefused) as excinfo:
        publish_generation(
            workspace=ws,
            snapshot_bytes=snapshot,
            binding=binding,
            record=None,
            content=content,
            published_at=NOW,
            policy_version=POLICY,
            audit_append=lambda event: None,
            refusal_sink=_failing_refusal,
        )
    assert excinfo.value.code == APPROVAL_MISSING
    assert excinfo.value.details.get("audit_error") == "OSError"
    for path in _generation_outputs(ws):
        assert not path.exists()


# ---------------------------------------------------------------------------
# AG03C-03 consumer-current (+ AG03C-04 consumer limbs, AG03C-05 consumers)
# ---------------------------------------------------------------------------


def test_consumer_current_included_records_readable(tmp_path: Path) -> None:
    """AG03C-03: the production consumer reads a CURRENT generation's outputs."""
    mat = _material_current(tmp_path)
    ws = mat["ws"]
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"study_id": "STU-1", "title": "current study"}])
    )
    # Re-publish over the edited included.json so the generation is CURRENT
    # for exactly these bytes (reviews-then-publish order, honestly staged).
    content = dict(mat["content"])
    content["included.json"] = (ws / "literature" / "included.json").read_text(
        encoding="utf-8"
    )
    snapshot, binding, record = _mint(content=content, approved_at=LATER)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=LATER)
    _publish(ws, content, record, snapshot, binding, published_at=LATER)
    assert require_current_generation(ws).status is GenerationStatus.CURRENT
    records = _included_records(ws)
    assert records == [{"study_id": "STU-1", "title": "current study"}]


def test_consumer_legacy_without_generation_remains_readable(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AG03C-03/compat: pre-authorization outputs stay readable (LEGACY file path).

    Migration exception (2026-10-13, bounded): true-legacy workspaces keep
    existing collect consumers byte-compatible, but the consumption REPORTS
    the typed LEGACY_UNVERIFIED code explicitly — never silent, never blessed
    as authorized-current.
    """
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "included.json").write_text(json.dumps([{"study_id": "STU-9"}]))
    with caplog.at_level("WARNING"):
        assert _included_records(ws) == [{"study_id": "STU-9"}]
    assert GENERATION_LEGACY_UNVERIFIED in caplog.text


def test_consumer_stale_and_mismatched_refuse_with_typed_codes(
    tmp_path: Path,
) -> None:
    """AG03C-04: production consumer refuses STALE/MISMATCHED with typed codes."""
    mat = _material_current(tmp_path, name="ws-stale")
    (mat["ws"] / "literature" / "included.json").write_text(
        "tampered\n", encoding="utf-8"
    )
    with pytest.raises(PublicationRefused) as excinfo:
        _included_records(mat["ws"])
    assert excinfo.value.code == GENERATION_STALE

    other = tmp_path / "ws-mismatch"
    (other / "literature" / "screening").mkdir(parents=True)
    (other / "project.json").write_text(
        json.dumps({"project_id": "m", "registered_workspace_id": WS_ID})
    )
    (other / "protocol.json").write_text(json.dumps(PROTOCOL_RAW))
    content = _content()
    snapshot, binding, record = _mint(content=content, workspace_id=OTHER_WS_ID)
    write_publication_approval(
        other / "literature" / "screening", record, staged_at=NOW
    )
    _publish(other, content, record, snapshot, binding)
    (other / "literature" / "included.json").write_text(json.dumps([{"a": 1}]))
    with pytest.raises(PublicationRefused) as excinfo2:
        _included_records(other)
    assert excinfo2.value.code == GENERATION_MISMATCHED


def _coordinator_fakes(ws: Path) -> dict:
    async def _discovery(**kwargs):
        return SimpleNamespace(documents=[], count=0)

    def _dedup(**kwargs):
        return SimpleNamespace(representatives=[], unique=0, duplicates_removed=0)

    async def _hydration(**kwargs):
        return SimpleNamespace(documents=[])

    async def _verification(**kwargs):
        return SimpleNamespace(
            documents=[],
            status="SUCCESS",
            verified=0,
            refused=0,
            preserved=0,
            bridge_restored=0,
            refusal_reasons=[],
            quarantine=None,
        )

    def _prepare(**kwargs):
        return SimpleNamespace(total_batches=1)

    def _extract(**kwargs):
        return SimpleNamespace(documents=[], metadata_frontmatter_only=0)

    async def _graph(**kwargs):
        return SimpleNamespace(nodes=0, edges=0)

    def _matrix(**kwargs):
        return SimpleNamespace(rows=[], retriever=object())

    def _synth(**kwargs):
        return SimpleNamespace(
            review_path=ws / "synthesis" / "literature_review.md",
            verified_claims=0,
            total_claims=0,
            entailment_rate=0.0,
        )

    def _index(chroma_dir):
        return ({"status": "DONE"}, object())

    return {
        "run_discovery": _discovery,
        "run_deduplication": _dedup,
        "run_hydration": _hydration,
        "run_verification": _verification,
        "run_screening_preparation": _prepare,
        "run_extraction": _extract,
        "run_graph": _graph,
        "run_matrix": _matrix,
        "run_synthesis": _synth,
        "indexing_fn": _index,
    }


def _patch_coordinator(monkeypatch: pytest.MonkeyPatch, ws: Path):
    fakes = _coordinator_fakes(ws)
    for name in (
        "run_discovery",
        "run_deduplication",
        "run_hydration",
        "run_verification",
        "run_extraction",
        "run_graph",
        "run_matrix",
        "run_synthesis",
    ):
        monkeypatch.setattr(coordinator, name, fakes[name])
    monkeypatch.setattr(
        "scholar_harness.pipeline.screening_prepare.run_screening_preparation",
        fakes["run_screening_preparation"],
    )
    return fakes["indexing_fn"]


def _coordinator_ws(root: Path, name: str) -> Path:
    ws = root / name
    (ws / "literature").mkdir(parents=True)
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL_RAW), encoding="utf-8")
    return ws


def test_coordinator_stale_generation_skips_stages_with_named_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AG03C-04/05: coordinator keeps stages 5-9 SKIPPED/PENDING on STALE."""
    ws = _coordinator_ws(tmp_path, "ws")
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "registered_workspace_id": WS_ID})
    )
    content = _content()
    (ws / "literature" / "included.json").write_text(
        content["included.json"], encoding="utf-8"
    )
    for name in PUBLICATION_OUTPUTS[1:]:
        (ws / "literature" / name).write_text(content[name], encoding="utf-8")
    snapshot, binding, record = _mint(content=content)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=NOW)
    _publish(ws, content, record, snapshot, binding)
    (ws / "literature" / "excluded.json").write_text("tampered\n", encoding="utf-8")
    indexing_fn = _patch_coordinator(monkeypatch, ws)
    results = asyncio.run(
        coordinator.run_pipeline(workspace_dir=ws, indexing_fn=indexing_fn)
    )
    assert results["status"] == "PENDING_AGENT_REVIEW"
    for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
        assert results["stages"][stage]["status"] == "SKIPPED"
        assert "STALE" in results["stages"][stage]["reason"]
    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in journal


def test_coordinator_current_generation_proceeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AG03C-03: coordinator proceeds past the gate on a CURRENT generation."""
    ws = _coordinator_ws(tmp_path, "ws")
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "registered_workspace_id": WS_ID})
    )
    content = _content()
    # The coordinator parses included.json past the gate (stages are faked,
    # but the handoff read is real), so it carries a JSON list here.
    content["included.json"] = json.dumps(
        [{"workspace_id": "SCI-000001", "title": "Proceed study"}]
    )
    (ws / "literature" / "included.json").write_text(
        content["included.json"], encoding="utf-8"
    )
    for name in PUBLICATION_OUTPUTS[1:]:
        (ws / "literature" / name).write_text(content[name], encoding="utf-8")
    snapshot, binding, record = _mint(content=content)
    write_publication_approval(ws / "literature" / "screening", record, staged_at=NOW)
    _publish(ws, content, record, snapshot, binding)
    indexing_fn = _patch_coordinator(monkeypatch, ws)
    results = asyncio.run(
        coordinator.run_pipeline(workspace_dir=ws, indexing_fn=indexing_fn)
    )
    assert results["stages"]["extraction"]["status"] == "DONE"
    assert results["status"] == "SUCCESS"


def test_handoff_screening_trigger_requires_current_when_authorized(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AG03C-03/04: SCREENING trigger needs CURRENT once authorized material exists."""
    legacy = tmp_path / "legacy"
    (legacy / "literature").mkdir(parents=True)
    (legacy / "literature" / "included.json").write_text("[]")
    # Migration exception (2026-10-13, bounded): true-legacy keeps
    # file-existence tracking, but REPORTS the typed LEGACY_UNVERIFIED code.
    with caplog.at_level("WARNING"):
        assert HandoffPhase.SCREENING in detect_completed_phases(legacy)
    assert GENERATION_LEGACY_UNVERIFIED in caplog.text

    mat = _material_current(tmp_path, name="ws")
    assert HandoffPhase.SCREENING in detect_completed_phases(mat["ws"])

    (mat["ws"] / "literature" / "included.json").write_text(
        "tampered\n", encoding="utf-8"
    )
    assert HandoffPhase.SCREENING not in detect_completed_phases(mat["ws"])

    # A deleted generation after authorization is a downgrade, never legacy:
    # the trigger stays incomplete until an authorized re-collect.
    (mat["ws"] / "literature" / "screening" / "generation.json").unlink()
    assert HandoffPhase.SCREENING not in detect_completed_phases(mat["ws"])


# ---------------------------------------------------------------------------
# Collector integration (real cmd_prepare / cmd_collect scaffold)
# ---------------------------------------------------------------------------


def _collect_ws(
    tmp_path: Path, name: str = "workspace", n_docs: int = 1
) -> tuple[Path, list[dict]]:
    workspace = tmp_path / name
    workspace.mkdir(exist_ok=True)
    (workspace / "project.json").write_text(
        json.dumps({"project_id": name, "registered_workspace_id": WS_ID}),
        encoding="utf-8",
    )
    (workspace / "protocol.json").write_text(json.dumps(PROTOCOL_RAW), encoding="utf-8")
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(PROTOCOL_RAW))
    sources = [
        Document(
            title=f"AG-03C synthetic record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ag03c-record-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ag03c-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(n_docs)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WS_ID,
        run_id=f"RUN-ag03c-{name}",
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 10, 13, tzinfo=UTC),
        commit="0" * 40,
    )
    corpus = built.artifact
    result = accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=corpus["workspace_id"],
            protocol_fingerprint=protocol_hash,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    )
    assert result.accepted
    studies = list(corpus["data"]["studies"])
    literature = workspace / "literature"
    literature.mkdir(exist_ok=True)
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": f"10.1000/ag03c-{i}"},
                }
                for i, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )
    cmd_prepare(workspace, batch_size=20)
    return workspace, studies


def _write_decisions(
    workspace: Path, studies: list[dict], *, decision: str = "INCLUDE", **fields
) -> None:
    screening = workspace / "literature" / "screening"
    entries = [
        {
            "workspace_id": study["study_id"],
            "decision": decision,
            "method": "LLM",
            "screening_reasoning": "AG-03C synthetic review.",
            **fields,
        }
        for study in studies
    ]
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(entries), encoding="utf-8"
    )


def _read_outputs(workspace: Path) -> dict[str, bytes]:
    return {
        name: (workspace / "literature" / name).read_bytes()
        for name in PUBLICATION_OUTPUTS
    }


class _CapturePublish(Exception):
    """Test-only sentinel carrying the content a collect would publish."""


def _review_content(workspace: Path) -> dict[str, str]:
    """Return the exact partition content the next collect would publish.

    Runs the real ``cmd_collect`` with ``publish_generation`` stubbed to
    capture (never write) its content argument: partition, serialization,
    scope, and digest inputs are production code, so an approval staged over
    the captured bytes binds exactly what the authorized re-collect verifies.
    The capturing run writes no publication output (the stub raises before
    any staging); per-batch review records are re-accepted idempotently.
    """
    real_publish = generations.publish_generation

    def _capture(**kwargs: object) -> None:
        content = kwargs["content"]
        assert isinstance(content, dict)
        raise _CapturePublish(content)

    generations.publish_generation = _capture  # type: ignore[method-assign]
    try:
        try:
            cmd_collect(workspace)
        except _CapturePublish as captured:
            assert isinstance(captured.args[0], dict)
            return dict(captured.args[0])
    finally:
        generations.publish_generation = real_publish  # type: ignore[method-assign]
    raise AssertionError("capturing collect returned without reaching the gate")


def _stage_approval_for_collected(workspace: Path, **binding_overrides):
    """Review-then-stage: mint an approval over the just-reviewed outputs.

    No-approval collects publish nothing (F-01a gate), so the review content
    is captured from the production partition path (see ``_review_content``),
    not read back from published files: the staged approval binds exactly
    what the authorized re-collect will verify.
    """
    scope = resolve_publication_scope(workspace)
    outputs = _review_content(workspace)
    digests = _content_digests(outputs)
    kwargs = {
        "workspace_id": scope.workspace_id,
        "run_id": scope.run_id,
        "batch_bindings": [dict(b) for b in scope.batch_bindings],
        "protocol_fingerprint": scope.protocol_fingerprint,
        "corpus_fingerprint": scope.corpus_fingerprint,
    }
    kwargs.update(binding_overrides)
    snapshot = build_publication_snapshot(
        workspace_id=kwargs["workspace_id"],
        run_id=kwargs["run_id"],
        batch_bindings=kwargs["batch_bindings"],
        protocol_fingerprint=kwargs["protocol_fingerprint"],
        corpus_fingerprint=kwargs["corpus_fingerprint"],
        output_digests=digests,
    )
    binding = publication_binding(
        workspace_id=kwargs["workspace_id"],
        run_id=kwargs["run_id"],
        batch_bindings=kwargs["batch_bindings"],
        protocol_fingerprint=kwargs["protocol_fingerprint"],
        corpus_fingerprint=kwargs["corpus_fingerprint"],
    )
    record = mint_publication_approval(
        operator=OPERATOR,
        binding=binding,
        snapshot_bytes=snapshot,
        approved_at=NOW,
    )
    write_publication_approval(
        workspace / "literature" / "screening", record, staged_at=NOW
    )
    return snapshot, binding, record, outputs


def test_collect_gate_before_write_staged_without_approval(tmp_path: Path) -> None:
    """AG03C-01 (collect limb): a staged-but-empty approval writes NO output."""
    workspace, studies = _collect_ws(tmp_path)
    _write_decisions(workspace, studies)
    (workspace / "literature" / "screening" / "publication_approval.json").write_text(
        json.dumps(
            {
                "schema": "harness-screening-publication-approval-v1",
                "approval": None,
                "policy_version": POLICY,
                "staged_at": NOW,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()
    assert not (workspace / "literature" / "screening" / "generation.json").exists()


def test_collect_forged_actor_without_approval_refuses(tmp_path: Path) -> None:
    """AG03C-01/matrix (collect limb): forged HUMAN labels confer no approval."""
    workspace, studies = _collect_ws(tmp_path)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "professor-x",
                "timestamp": "2026-10-13T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": studies[0]["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "confidence": 0.99,
                        "screening_reasoning": "Forged attribution.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (screening / "publication_approval.json").write_text(
        json.dumps(
            {
                "schema": "harness-screening-publication-approval-v1",
                "approval": None,
                "policy_version": POLICY,
                "staged_at": NOW,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()


def test_collect_gated_publish_is_byte_identical_and_current(
    tmp_path: Path,
) -> None:
    """AG03C-02 (collect limb): no-approval collect refuses; authorized outputs match reviewed bytes + CURRENT.

    F-01a: the pre-authorization legacy write path is removed, so the first
    collect refuses with APPROVAL_MISSING and writes nothing; the reference
    bytes are the production partition content captured for review, and the
    authorized re-collect must publish exactly those bytes.
    """
    workspace, studies = _collect_ws(tmp_path)
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()
    assert not (workspace / "literature" / "screening" / "generation.json").exists()
    snapshot, _, record, reviewed = _stage_approval_for_collected(workspace)
    cmd_collect(workspace)
    authorized = _read_outputs(workspace)
    for name in PUBLICATION_OUTPUTS:
        assert authorized[name] == publication_file_bytes(reviewed[name])
    generation_path = workspace / "literature" / "screening" / "generation.json"
    assert generation_path.is_file()
    stored = GenerationRecord.from_dict(
        json.loads(generation_path.read_text(encoding="utf-8"))
    )
    for name in PUBLICATION_OUTPUTS:
        assert stored.output_digests[name] == content_sha256(authorized[name])
    assert stored.snapshot_fingerprint == content_sha256(snapshot)
    assert stored.approval_fingerprint == record.fingerprint()
    assert require_current_generation(workspace).status is GenerationStatus.CURRENT


def test_collect_changed_bytes_after_approval_refuses(tmp_path: Path) -> None:
    """AG03C-01/matrix (collect limb): post-review content change refuses cleanly.

    The swap targets the underlying evidence (verified.json titles flow into
    included.json), not the decision file — decision-file tampering is AG-02's
    layer and refuses first (pinned by the AG03C-10 tests); the authorization
    gate catches content that AG-02 already accepted.
    """
    workspace, studies = _collect_ws(tmp_path)
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    _stage_approval_for_collected(workspace)
    verified_path = workspace / "literature" / "verified.json"
    rows = json.loads(verified_path.read_text(encoding="utf-8"))
    rows[0]["title"] = "Post-review swapped title"
    verified_path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()
    assert not (workspace / "literature" / "screening" / "generation.json").exists()


def test_collect_cross_workspace_replay_refuses(tmp_path: Path) -> None:
    """AG03C-01/matrix (collect limb): an approval from run A fails in run B."""
    workspace_a, studies_a = _collect_ws(tmp_path, name="workspace-a")
    _write_decisions(workspace_a, studies_a)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace_a)
    assert excinfo.value.code == APPROVAL_MISSING
    _, _, record_a, _ = _stage_approval_for_collected(workspace_a)

    workspace_b, studies_b = _collect_ws(tmp_path, name="workspace-b")
    _write_decisions(workspace_b, studies_b)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace_b)
    assert excinfo.value.code == APPROVAL_MISSING
    # Replay A's approval file verbatim beside B's collected scope.
    write_publication_approval(
        workspace_b / "literature" / "screening", record_a, staged_at=NOW
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace_b)
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace_b / "literature" / name).exists()


def test_collect_changed_parents_refuse(tmp_path: Path) -> None:
    """AG03C-01/matrix (collect limb): approval under old parents refuses."""
    workspace, studies = _collect_ws(tmp_path)
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    _stage_approval_for_collected(workspace, corpus_fingerprint="sha256:" + "e" * 64)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()


@pytest.mark.parametrize(
    "decisions",
    [
        [{"decision": "MAYBE"}],
        [{"decision": "INCLUDE"}, {"decision": "INCLUDE"}],
    ],
    ids=["unresolved", "duplicate"],
)
def test_ag02_refusals_fire_first_through_gated_collect(
    tmp_path: Path, decisions: list[dict]
) -> None:
    """AG03C-10: AG-02 integrity gates precede the authorization gate."""
    workspace, studies = _collect_ws(tmp_path)
    entries = []
    for i, decision in enumerate(decisions):
        entry = {
            "workspace_id": studies[0]["study_id"],
            "method": "LLM",
            "screening_reasoning": "AG-03C AG-02 pin.",
        }
        entry.update(decision)
        entries.append(entry)
    (workspace / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(entries), encoding="utf-8"
    )
    # A staged (dummy-scope) approval must not rescue an integrity refusal.
    snapshot, binding, record = _mint(content=_content())
    write_publication_approval(
        workspace / "literature" / "screening", record, staged_at=NOW
    )
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()
    assert not (workspace / "literature" / "screening" / "generation.json").exists()


def test_ag02_coverage_refusal_fires_first_through_gated_collect(
    tmp_path: Path,
) -> None:
    """AG03C-10: incomplete coverage refuses before any publication attempt."""
    workspace, studies = _collect_ws(tmp_path, n_docs=2)
    assert len(studies) == 2
    (workspace / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": studies[0]["study_id"],
                    "decision": "INCLUDE",
                    "method": "LLM",
                    "screening_reasoning": "Only the first candidate screened.",
                }
            ]
        ),
        encoding="utf-8",
    )
    snapshot, binding, record = _mint(content=_content())
    write_publication_approval(
        workspace / "literature" / "screening", record, staged_at=NOW
    )
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)
    for name in PUBLICATION_OUTPUTS:
        assert not (workspace / "literature" / name).exists()
    assert not (workspace / "literature" / "screening" / "generation.json").exists()


# ---------------------------------------------------------------------------
# AG-03C-R2 pin: coordinator legacy disposition (migration exception)
# ---------------------------------------------------------------------------


def test_coordinator_legacy_without_generation_reports_explicitly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AG-03C-R2: a true-legacy workspace proceeds with an explicit LEGACY report.

    Migration exception (packet §2, bounded): a workspace with outputs present
    but no generation record and no authorized material anywhere is
    true-legacy. The coordinator logs the typed GENERATION_LEGACY_UNVERIFIED
    code explicitly (never silent) and proceeds on the pre-authorization file
    path — mirroring the extraction pin
    (``test_consumer_legacy_without_generation_remains_readable``) and the
    handoff pin (``test_handoff_screening_trigger_requires_current_when_authorized``),
    which likewise proceed-with-warning rather than skip. (SKIPPED/PENDING
    with a named reason is the non-legacy non-current behavior, already pinned
    by ``test_coordinator_stale_generation_skips_stages_with_named_reason``.)
    """
    ws = _coordinator_ws(tmp_path, "ws-legacy")
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws-legacy", "registered_workspace_id": WS_ID})
    )
    # Outputs present, no generation.json, no staged approval, no registry or
    # MANIFEST lineage: true-legacy, not a downgrade.
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001", "title": "Legacy study"}]),
        encoding="utf-8",
    )
    for name in PUBLICATION_OUTPUTS[1:]:
        (ws / "literature" / name).write_text(_content()[name], encoding="utf-8")
    assert require_current_generation(ws).status is GenerationStatus.LEGACY_UNVERIFIED
    indexing_fn = _patch_coordinator(monkeypatch, ws)
    with caplog.at_level("WARNING"):
        results = asyncio.run(
            coordinator.run_pipeline(workspace_dir=ws, indexing_fn=indexing_fn)
        )
    assert GENERATION_LEGACY_UNVERIFIED in caplog.text
    assert results["stages"]["extraction"]["status"] == "DONE"
    assert results["status"] == "SUCCESS"


def test_downgrade_detail_flags_distinguish_unapproved_lineage_from_deletion(
    tmp_path: Path,
) -> None:
    """AG-03C-R2/R3: the absent-generation MISMATCHED details name which absence.

    The ``_downgrade_evidence`` branch fires both for never-approved-but-reviewed
    workspaces (review lineage exists pre-gate, no generation ever published)
    and for post-authorization deletion. Both still refuse as MISMATCHED —
    only the detail flags differ: ``lineage_without_generation`` when no prior
    generation is recorded anywhere, ``prior_generation_deleted`` when a
    generation fingerprint survives (history record, PUBLISHED journal event,
    or registry generation entry).
    """
    # Case A: unapproved review lineage without a generation.
    workspace, studies = _collect_ws(tmp_path, name="workspace-a")
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    lineage = require_current_generation(workspace)
    assert lineage.status is GenerationStatus.MISMATCHED
    assert lineage.code == GENERATION_MISMATCHED
    assert lineage.details["lineage_without_generation"] is True
    assert lineage.details["prior_generation_deleted"] is False

    # Case B: post-authorization deletion of a published generation.
    mat = _material_current(tmp_path, name="ws-published")
    (mat["ws"] / "literature" / "screening" / "generation.json").unlink()
    deleted = require_current_generation(mat["ws"])
    assert deleted.status is GenerationStatus.MISMATCHED
    assert deleted.code == GENERATION_MISMATCHED
    assert deleted.details["prior_generation_deleted"] is True
    assert deleted.details["lineage_without_generation"] is False
