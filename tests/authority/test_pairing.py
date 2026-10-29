"""Pairing-code approval tests (UI-07 §3; RELEASE lane, hermetic).

Exercises the terminal-side challenge staging plus the atomic single-use
redemption around the UNCHANGED AG-03B/AG-04 approval path, on synthetic
``tmp_path`` state only (never workspaces/, never a real workspace).

Acceptance map (task brief pairing behaviors):

* secure creation + floors (ACT-01) — ``test_begin_floors``,
  ``test_begin_refuses_over_cap_lifetime``.
* hash-only store (ACT-02) — ``test_store_is_hash_only``.
* no plaintext anywhere (ACT-03) — ``test_no_plaintext_anywhere``.
* exact binding (ACT-04) — ``test_redeem_binds_exact_snapshot``,
  ``test_cross_batch_replay_fails``.
* expiry / exhaustion / invalid / single-use / cancel / supersede
  invalidation (ACT-05) — ``test_expired_refused``,
  ``test_attempts_exhaust``, ``test_unknown_code_refused``,
  ``test_single_use_flip``, ``test_cancel_voids``,
  ``test_second_begin_supersedes_first``.
* concurrent ≤1 success (ACT-08) — ``test_concurrent_redeem_single_winner``.
* terminal-act gating (ACT-10) — ``test_begin_refuses_low_integrity``,
  ``test_begin_refuses_without_context``, ``test_begin_refuses_unresolved``.
* stale-parent refuse (ACT-09) — ``test_stale_content_voids``,
  ``test_stale_parents_void``.
* override lineage (ACT-13) — ``test_override_lineage_preserved``.
* unresolved preserved (ACT-12) — ``test_unresolved_leaves_challenge_staged``.
* Low-IL preserved at redeem (ACT-11) — ``test_redeem_refuses_low_integrity``.

No cross-test-file imports: the scaffold mirrors
tests/authority/test_ag04_interaction.py::_scaffold (same kits, same shape).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

import scholar_harness.authority.review as review_mod
from scholar_harness.authority.binding import AuthorityRefused, content_sha256
from scholar_harness.authority.pairing import (
    PAIRING_ATTEMPT_CAP,
    PAIRING_CODE_INVALID,
    PAIRING_CODE_LENGTH,
    PAIRING_CODE_LIFETIME_S,
    PAIRING_PBKDF2_ITERATIONS,
    PAIRING_RECORD_KEYS,
    PAIRING_SCHEMA,
    PAIRING_STATE_ABSENT,
    PAIRING_STATE_CONSUMED,
    PAIRING_STATE_EXHAUSTED,
    PAIRING_STATE_EXPIRED,
    PAIRING_STATE_STAGED,
    STALE_VIEW,
    begin_pairing,
    cancel_pairing,
    hash_code,
    mint_code,
    normalize_code,
    pairing_path,
    pairing_status,
    redeem_pairing,
    verify_code,
)
from scholar_harness.authority.review import OPERATOR_CONTEXT_MISSING
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_harness.screening.integrity import ScreeningIntegrityRefused
from scholar_harness.screening.worker import run_recommend
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

WS_ID = "WSP-" + "f" * 32
OPERATOR = "ui07-operator@example"
NOW = "2026-10-13T12:00:00+00:00"

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


def _scaffold(
    tmp_path: Path, name: str = "workspace", n_docs: int = 2
) -> tuple[Path, list[dict]]:
    """Prepare a synthetic single-batch workspace (real prepare path)."""
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
            title=f"UI-07 synthetic record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ui07-record-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ui07-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(n_docs)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WS_ID,
        run_id=f"RUN-ui07-{name}",
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
                    "external_ids": {"doi": f"10.1000/ui07-{i}"},
                }
                for i, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )
    cmd_prepare(workspace, batch_size=20)
    return workspace, studies


def _write_operator_context(workspace: Path) -> None:
    path = workspace / "literature" / "screening" / "operator_context.json"
    path.write_text(
        json.dumps(
            {"schema": "harness-operator-context-v1", "operator_identity": OPERATOR},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_decisions(
    workspace: Path, studies: list[dict], decisions: list[str] | None = None
) -> Path:
    resolved = decisions if decisions is not None else ["INCLUDE", "EXCLUDE"]
    entries = [
        {
            "workspace_id": study["study_id"],
            "decision": decision,
            "method": "HUMAN",
            "screening_reasoning": f"UI-07 researcher resolution {i}.",
        }
        for i, (study, decision) in enumerate(zip(studies, resolved))
    ]
    path = workspace / "literature" / "screening" / "batch_001_decisions.json"
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return path


def _stage(workspace: Path, studies: list[dict]) -> dict:
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    return begin_pairing(workspace, 1, request_id="REQ-TEST-1")


def _stored(workspace: Path) -> dict:
    return json.loads(pairing_path(workspace, 1).read_text(encoding="utf-8"))


# --- ACT-01: floors ---------------------------------------------------------- #


def test_begin_floors(tmp_path: Path) -> None:
    """Codes carry ≥128-bit CSPRNG entropy, 5-minute life, bounded attempts."""
    assert PAIRING_CODE_LIFETIME_S <= 600
    assert PAIRING_CODE_LENGTH * 5 >= 128  # 32-symbol alphabet
    assert PAIRING_ATTEMPT_CAP > 0
    seen = {mint_code() for _ in range(50)}
    assert len(seen) == 50  # CSPRNG: no collisions in a small draw
    for code in seen:
        assert len(code) == PAIRING_CODE_LENGTH
        assert all(c in "ABCDEFGHJKMNPQRSTUVWXYZ23456789" for c in code)
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    record = _stored(workspace)
    assert record["attempt_cap"] == PAIRING_ATTEMPT_CAP
    lifetime = (
        datetime.fromisoformat(record["expires_at"])
        - datetime.fromisoformat(record["staged_at"])
    ).total_seconds()
    assert lifetime == PAIRING_CODE_LIFETIME_S
    assert normalize_code(
        staged["code"].lower().replace("-", "----")
    ) == normalize_code(staged["code"])
    assert verify_code(staged["code"], record["salted_hash"]) is True
    assert verify_code(staged["code"] + "X", record["salted_hash"]) is False
    # Hash parameters are at the recorded strength, parsable and salted.
    scheme, iterations, salt_hex, _ = record["salted_hash"].split("$")
    assert scheme == "pbkdf2-sha256" and int(iterations) >= PAIRING_PBKDF2_ITERATIONS
    assert len(bytes.fromhex(salt_hex)) == 16
    assert hash_code(staged["code"]) != record["salted_hash"]  # fresh salt each mint


def test_begin_refuses_over_cap_lifetime(tmp_path: Path) -> None:
    """A weaker-than-floor configuration is refused, never clamped."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        begin_pairing(workspace, 1, lifetime_s=601)
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert not pairing_path(workspace, 1).exists()


# --- ACT-02/03: hash-only, no plaintext -------------------------------------- #


def test_store_is_hash_only(tmp_path: Path) -> None:
    """The pending store holds ONLY the salted hash plus binding metadata."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    record = _stored(workspace)
    assert set(record) == PAIRING_RECORD_KEYS
    assert record["schema"] == PAIRING_SCHEMA
    assert set(record["action_binding"]) == {
        "binding",
        "recommendation_sha256",
        "final_decision_sha256",
        "parent_artifact_id",
        "parent_sha256",
    }
    raw = pairing_path(workspace, 1).read_bytes()
    assert staged["code"].encode("ascii") not in raw
    assert normalize_code(staged["code"]).encode("ascii") not in raw
    # Key names aside, no code-shaped value leaks: the only long hex runs are
    # the salt, the hash, and the snapshot/parent fingerprints.
    assert b"salted_hash" in raw


def test_no_plaintext_anywhere(tmp_path: Path) -> None:
    """No file, status, or result surface carries the code or its hash."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    code = staged["code"]
    _ = redeem_pairing(workspace, 1, code, request_id="REQ-TEST-1")
    # Every workspace file: the code appears nowhere.
    for path in workspace.rglob("*"):
        if path.is_file():
            assert code.encode("ascii") not in path.read_bytes(), path
    status = pairing_status(workspace, 1)
    assert "code" not in json.dumps(status).lower().replace(
        "snapshot_fingerprint", ""
    ).replace("salted", "")
    assert "salted_hash" not in status and "code" not in {k.lower() for k in status} - {
        "snapshot_fingerprint"
    }


# --- ACT-04/05: binding, expiry, exhaustion, single-use, voiding ------------ #


def test_redeem_binds_exact_snapshot(tmp_path: Path) -> None:
    """A genuine code mints via AG-03B with the publisher-owned identity."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    result = redeem_pairing(workspace, 1, staged["code"], request_id="REQ-TEST-1")
    assert result["operator_identity"] == OPERATOR
    assert result["snapshot_fingerprint"] == staged["snapshot_fingerprint"]
    assert result["snapshot_fingerprint"].startswith("sha256:")
    assert result["request_id"] == "REQ-TEST-1"
    assert result["superseded"] is True  # researcher content != worker draft
    screening = workspace / "literature" / "screening"
    assert (screening / "approvals" / "batch_001_approval.json").is_file()
    assert (screening / "publication_approval.json").is_file()
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED


def test_single_use_flip(tmp_path: Path) -> None:
    """A replayed code fails as consumed; the approval is minted exactly once."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    first = redeem_pairing(workspace, 1, staged["code"])
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "consumed"
    # Approval still the first mint (no second mint happened).
    approval = json.loads(
        (
            workspace
            / "literature"
            / "screening"
            / "approvals"
            / "batch_001_approval.json"
        ).read_text(encoding="utf-8")
    )
    assert approval["approval"]["operator_identity"] == OPERATOR
    assert first["approval_fingerprint"].startswith("sha256:")


def test_unknown_code_refused(tmp_path: Path) -> None:
    """No staged challenge (or a foreign code) refuses without side effects."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, mint_code())
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "unknown"
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_ABSENT
    assert not (
        workspace / "literature" / "screening" / "approvals" / "batch_001_approval.json"
    ).exists()


def test_expired_refused(tmp_path: Path) -> None:
    """An expired code — even the genuine one — refuses and mints nothing."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    staged = begin_pairing(workspace, 1, lifetime_s=-5)
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_EXPIRED
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "expired"
    assert not (
        workspace / "literature" / "screening" / "approvals" / "batch_001_approval.json"
    ).exists()


def test_attempts_exhaust(tmp_path: Path) -> None:
    """Bounded attempts: wrong codes consume budget, then even the genuine fails."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    staged = begin_pairing(workspace, 1, attempt_cap=2)
    wrong = mint_code()
    assert wrong != staged["code"]
    with pytest.raises(AuthorityRefused):
        redeem_pairing(workspace, 1, wrong)
    status = pairing_status(workspace, 1)
    assert status["state"] == PAIRING_STATE_STAGED
    assert status["attempts_remaining"] == 1
    with pytest.raises(AuthorityRefused):
        redeem_pairing(workspace, 1, wrong)
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_EXHAUSTED
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "exhausted"


def test_cancel_voids(tmp_path: Path) -> None:
    """Cancelling (the defer path) voids the challenge; the code must begin again."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    assert cancel_pairing(workspace, 1) is True
    assert cancel_pairing(workspace, 1) is False  # already void: idempotent
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.details["reason"] == "consumed"


def test_second_begin_supersedes_first(tmp_path: Path) -> None:
    """Two competing begins: the first code dies, the second mints."""
    workspace, studies = _scaffold(tmp_path)
    first = _stage(workspace, studies)
    second = begin_pairing(workspace, 1)
    assert second["code"] != first["code"]
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, first["code"])
    assert excinfo.value.code == PAIRING_CODE_INVALID
    result = redeem_pairing(workspace, 1, second["code"])
    assert result["operator_identity"] == OPERATOR


def test_cross_batch_replay_fails(tmp_path: Path) -> None:
    """A code staged for batch 1 is not presentable for any other batch."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 2, staged["code"])
    assert excinfo.value.code == PAIRING_CODE_INVALID
    # And the genuine batch-1 challenge is untouched by the foreign attempt.
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
    assert redeem_pairing(workspace, 1, staged["code"])["operator_identity"] == OPERATOR


# --- ACT-08: concurrency ------------------------------------------------------ #


def test_concurrent_redeem_single_winner(tmp_path: Path) -> None:
    """Eight racing redeems of one code yield exactly one minted approval."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    outcomes: list[str] = []
    lock = threading.Lock()

    def _try() -> None:
        try:
            redeem_pairing(workspace, 1, staged["code"])
            with lock:
                outcomes.append("success")
        except AuthorityRefused as exc:
            with lock:
                outcomes.append(exc.details.get("reason", exc.code))

    threads = [threading.Thread(target=_try) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count("success") == 1
    assert set(outcomes) <= {"success", "consumed"}
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED


# --- ACT-09: stale-view ------------------------------------------------------- #


def test_stale_content_voids(tmp_path: Path) -> None:
    """Editing decisions after begin voids the code (STALE_VIEW), publishing nothing."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    _write_decisions(workspace, studies, decisions=["EXCLUDE", "INCLUDE"])
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.code == STALE_VIEW
    assert excinfo.value.details["changed_element"] == "snapshot_content"
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED
    for name in ("included.json", "generation.json"):
        assert not (workspace / "literature" / name).exists()
        assert not (workspace / "literature" / "screening" / name).exists()


def test_stale_parents_void(tmp_path: Path) -> None:
    """Superseding the registered parent envelope after begin voids the code."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    registry_path = workspace / "audit" / "artifact_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    art_id = next(
        aid
        for aid, entry in registry["artifacts"].items()
        if entry.get("artifact_type") == "screening_batch"
    )
    art_path = workspace / registry["artifacts"][art_id]["path"]
    envelope = json.loads(art_path.read_bytes().decode("utf-8"))
    envelope["data"]["candidates"].append(
        {"study_id": "SCI-999999", "title": "late arrival"}
    )
    art_path.write_bytes(json.dumps(envelope, indent=2, sort_keys=True).encode("utf-8"))
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.code == STALE_VIEW
    assert excinfo.value.details["changed_element"] == "batch_parents"


# --- ACT-10/11/12/13: AG-04 preserved ---------------------------------------- #


def test_begin_refuses_low_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The terminal act refuses at worker integrity, staging nothing."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    monkeypatch.setattr(review_mod, "_is_low_integrity_process", lambda: True)
    with pytest.raises(AuthorityRefused) as excinfo:
        begin_pairing(workspace, 1)
    from scholar_harness.authority.binding import APPROVAL_NOT_OPERATOR

    assert excinfo.value.code == APPROVAL_NOT_OPERATOR
    assert not pairing_path(workspace, 1).exists()


def test_begin_refuses_without_context(tmp_path: Path) -> None:
    """No publisher context means no challenge, never a default."""
    workspace, studies = _scaffold(tmp_path)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    with pytest.raises(Exception) as excinfo:
        begin_pairing(workspace, 1)
    assert getattr(excinfo.value, "code", None) == OPERATOR_CONTEXT_MISSING
    assert not pairing_path(workspace, 1).exists()


def test_begin_refuses_unresolved(tmp_path: Path) -> None:
    """Nothing resolved to approve means nothing staged to approve."""
    workspace, _ = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    with pytest.raises(AuthorityRefused) as excinfo:
        begin_pairing(workspace, 1)
    from scholar_harness.authority.binding import APPROVAL_MISSING

    assert excinfo.value.code == APPROVAL_MISSING
    assert not pairing_path(workspace, 1).exists()


def test_redeem_refuses_low_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Low-IL redeem refuses via the AG-03B path and leaves the code staged."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    monkeypatch.setattr(review_mod, "_is_low_integrity_process", lambda: True)
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    from scholar_harness.authority.binding import APPROVAL_NOT_OPERATOR

    assert excinfo.value.code == APPROVAL_NOT_OPERATOR
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
    assert not (
        workspace / "literature" / "screening" / "approvals" / "batch_001_approval.json"
    ).exists()


def test_unresolved_leaves_challenge_staged(tmp_path: Path) -> None:
    """MAYBE rows refuse approval (AG-02); the staged code survives for re-begin."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies, decisions=["MAYBE", "INCLUDE"])
    staged = begin_pairing(workspace, 1)
    with pytest.raises(ScreeningIntegrityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert excinfo.value.code == "UNRESOLVED_FINALIZE_REFUSED"
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
    assert not (
        workspace / "literature" / "screening" / "publication_approval.json"
    ).exists()


def test_override_lineage_preserved(tmp_path: Path) -> None:
    """Redeem after a researcher override keeps the supersede chain verbatim."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    before = (
        workspace
        / "literature"
        / "screening"
        / "recommendations"
        / "batch_001_recommendation.json"
    ).read_bytes()
    result = redeem_pairing(workspace, 1, staged["code"])
    assert result["superseded"] is True
    review_record = json.loads(
        (
            workspace / "literature" / "screening" / "reviews" / "batch_001_review.json"
        ).read_text(encoding="utf-8")
    )
    assert review_record["superseded_by"] == OPERATOR
    assert review_record["supersedes"]
    assert (
        workspace
        / "literature"
        / "screening"
        / "recommendations"
        / "batch_001_recommendation.json"
    ).read_bytes() == before
    # The staged publication approval verifies at the existing collect gate.
    cmd_collect(workspace)
    from scholar_harness.authority.generations import (
        GenerationStatus,
        require_current_generation,
    )

    assert require_current_generation(workspace).status is GenerationStatus.CURRENT


def test_pairing_file_hash_stable_bytes(tmp_path: Path) -> None:
    """Store bytes carry the pbkdf2 envelope and a sha256: snapshot fingerprint."""
    workspace, studies = _scaffold(tmp_path)
    _stage(workspace, studies)
    record = _stored(workspace)
    assert record["snapshot_fingerprint"].startswith("sha256:")
    assert len(record["snapshot_fingerprint"]) == len("sha256:") + 64
    digest = hashlib.sha256(pairing_path(workspace, 1).read_bytes()).hexdigest()
    assert len(digest) == 64


def test_challenge_state_survives_restart(tmp_path: Path) -> None:
    """The pending store is file-backed: a fresh call stack (a restart) sees
    the same staged/expired states; nothing lives only in memory."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    # "Restart": drop every in-memory handle and re-read from disk only.
    del staged
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
    # Time passes across the restart: the stored expiry is now in the past.
    record = _stored(workspace)
    record["expires_at"] = "2020-01-01T00:00:00+00:00"
    pairing_path(workspace, 1).write_text(
        json.dumps(record, indent=2, sort_keys=True), encoding="utf-8"
    )
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_EXPIRED
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, mint_code())
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "expired"


def test_gate_refusal_recovers_after_context_restored(tmp_path: Path) -> None:
    """A non-drift gate refusal leaves the challenge staged, and the SAME
    code mints once the operator context is restored (recoverable)."""
    workspace, studies = _scaffold(tmp_path)
    staged = _stage(workspace, studies)
    (workspace / "literature" / "screening" / "operator_context.json").unlink()
    with pytest.raises(Exception) as excinfo:
        redeem_pairing(workspace, 1, staged["code"])
    assert getattr(excinfo.value, "code", None) == OPERATOR_CONTEXT_MISSING
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
    _write_operator_context(workspace)
    result = redeem_pairing(workspace, 1, staged["code"])
    assert result["operator_identity"] == OPERATOR


# --- UI07-ACTIONS-R1: approve --begin CLI wrapper ---------------------------- #


def _begin_via_cli(workspace: Path, capsys: pytest.CaptureFixture) -> tuple[str, str]:
    """Run the operator CLI staging path; return (stdout, extracted code)."""
    import re as _re

    review_mod.cmd_approve(workspace, 1, begin=True)
    out = capsys.readouterr().out
    match = _re.search(
        r"Pairing code for batch 1:\s*([ABCDEFGHJKMNPQRSTUVWXYZ23456789]{26})",
        out,
    )
    assert match is not None, f"CLI output carries no well-formed code: {out!r}"
    return out, match.group(1)


def test_begin_cli_prints_code_once_and_hides_plaintext(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """CLI begin prints one well-formed code exactly once; stdout is its only home."""
    workspace, studies = _scaffold(tmp_path, name="begin-cli-once")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    out, code = _begin_via_cli(workspace, capsys)
    assert len(code) == PAIRING_CODE_LENGTH
    assert all(c in "ABCDEFGHJKMNPQRSTUVWXYZ23456789" for c in code)
    assert out.count(code) == 1  # printed EXACTLY ONCE
    record = _stored(workspace)
    assert verify_code(code, record["salted_hash"]) is True
    for path in workspace.rglob("*"):
        if path.is_file():
            assert code.encode("ascii") not in path.read_bytes(), path
    status = pairing_status(workspace, 1)
    assert code not in json.dumps(status)


def test_begin_cli_output_carries_expiry_and_fingerprint(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """CLI begin output carries the expiry plus the snapshot fingerprint."""
    workspace, studies = _scaffold(tmp_path, name="begin-cli-meta")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    out, code = _begin_via_cli(workspace, capsys)
    record = _stored(workspace)
    assert record["expires_at"] in out
    assert record["snapshot_fingerprint"] in out
    assert record["snapshot_fingerprint"].startswith("sha256:")
    assert (
        pairing_status(workspace, 1)["snapshot_fingerprint"]
        == record["snapshot_fingerprint"]
    )
    assert out.count(code) == 1


def test_begin_cli_refuses_low_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """CLI begin at worker integrity refuses APPROVAL_NOT_OPERATOR, staging nothing."""
    from scholar_harness.authority.binding import APPROVAL_NOT_OPERATOR

    workspace, studies = _scaffold(tmp_path, name="begin-cli-low")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    monkeypatch.setattr(review_mod, "_is_low_integrity_process", lambda: True)
    with pytest.raises(AuthorityRefused) as excinfo:
        review_mod.cmd_approve(workspace, 1, begin=True)
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR
    assert "Pairing code" not in capsys.readouterr().out
    assert not pairing_path(workspace, 1).exists()


def test_begin_cli_refuses_without_context(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """CLI begin with no publisher context refuses OPERATOR_CONTEXT_MISSING."""
    workspace, studies = _scaffold(tmp_path, name="begin-cli-noctx")
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    with pytest.raises(Exception) as excinfo:
        review_mod.cmd_approve(workspace, 1, begin=True)
    assert getattr(excinfo.value, "code", None) == OPERATOR_CONTEXT_MISSING
    assert "Pairing code" not in capsys.readouterr().out
    assert not pairing_path(workspace, 1).exists()


def test_begin_cli_refuses_unresolved(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """CLI begin with nothing resolved refuses APPROVAL_MISSING, staging nothing."""
    from scholar_harness.authority.binding import APPROVAL_MISSING

    workspace, _ = _scaffold(tmp_path, name="begin-cli-unresolved")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    with pytest.raises(AuthorityRefused) as excinfo:
        review_mod.cmd_approve(workspace, 1, begin=True)
    assert excinfo.value.code == APPROVAL_MISSING
    assert "Pairing code" not in capsys.readouterr().out
    assert not pairing_path(workspace, 1).exists()


def test_begin_cli_end_to_end_redeem_single_use(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """CLI begin -> redeem with the printed code mints; replay refuses (single-use)."""
    workspace, studies = _scaffold(tmp_path, name="begin-cli-e2e")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    out, code = _begin_via_cli(workspace, capsys)
    assert record_fingerprint_in_output(workspace, out)
    result = redeem_pairing(workspace, 1, code, request_id="REQ-BEGIN-CLI")
    assert result["operator_identity"] == OPERATOR
    assert result["snapshot_fingerprint"].startswith("sha256:")
    screening = workspace / "literature" / "screening"
    assert (screening / "approvals" / "batch_001_approval.json").is_file()
    assert (screening / "publication_approval.json").is_file()
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, code)
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "consumed"
    assert code not in str(excinfo.value)
    for path in workspace.rglob("*"):
        if path.is_file():
            assert code.encode("ascii") not in path.read_bytes(), path


def record_fingerprint_in_output(workspace: Path, out: str) -> bool:
    """The printed fingerprint matches the staged challenge (browser comparison point)."""
    record = json.loads(pairing_path(workspace, 1).read_text(encoding="utf-8"))
    return record["snapshot_fingerprint"] in out


def test_begin_cli_agent_screen_wiring(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """agent_screen approve --begin stages via the CLI wrapper; no --code input exists."""
    import sys as _sys

    from scholar_harness.agent_screen import main as _agent_main

    workspace, studies = _scaffold(tmp_path, name="begin-cli-wiring")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    old_argv = _sys.argv
    _sys.argv = [
        "agent_screen",
        "approve",
        str(workspace),
        "--batch",
        "1",
        "--begin",
    ]
    try:
        _agent_main()
    finally:
        _sys.argv = old_argv
    out = capsys.readouterr().out
    assert out.count("Pairing code for batch 1:") == 1
    import re as _re

    codes = _re.findall(r"[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{26}", out)
    assert len(codes) == 1
    assert verify_code(codes[0], _stored(workspace)["salted_hash"]) is True
    # Codes are output-only, never input: the approve subcommand takes no
    # code argument, so presenting one is an argparse error (SystemExit),
    # never a staged or minted approval.
    _sys.argv = [
        "agent_screen",
        "approve",
        str(workspace),
        "--batch",
        "1",
        "--code",
        codes[0],
    ]
    try:
        with pytest.raises(SystemExit):
            _agent_main()
    finally:
        _sys.argv = old_argv
    _err = capsys.readouterr()
    assert "Pairing code" not in _err.out
    for path in workspace.rglob("*"):
        if path.is_file():
            assert codes[0].encode("ascii") not in path.read_bytes(), path


# --- UI07-ACTIONS-R2 repairs (F-01..F-04; appended, existing tests untouched) ---


def test_cli_defer_voids_pairing_redeem_refuses_consumed(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """F-01: CLI defer voids the staged pairing; the genuine code then refuses.

    Closes the defer-then-redeem-still-mints path: ``cmd_defer`` owns the
    CLI teardown (``defer_command`` voids via ``cancel_pairing`` and records
    ``pairing_voided`` beside ``voided_approvals``).
    """
    workspace, studies = _scaffold(tmp_path, name="r2-f01")
    staged = _stage(workspace, studies)
    code = staged["code"]
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
    review_mod.cmd_defer(workspace, 1, "second look")
    capsys.readouterr()
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED
    record = json.loads(
        (
            workspace
            / "literature"
            / "screening"
            / "deferrals"
            / "batch_001_deferral.json"
        ).read_text(encoding="utf-8")
    )
    assert record["pairing_voided"] is True
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, code)
    assert excinfo.value.code == PAIRING_CODE_INVALID
    assert excinfo.value.details["reason"] == "consumed"
    assert code not in str(excinfo.value)


def test_redeem_same_key_retry_returns_stored_without_remint(
    tmp_path: Path,
) -> None:
    """F-02a: identical (request stem + content hashes) retry returns stored success."""
    from scholar_harness.authority.pairing import idempotency_path

    workspace, studies = _scaffold(tmp_path, name="r2-f02a")
    staged = _stage(workspace, studies)
    first = redeem_pairing(workspace, 1, staged["code"], request_id="REQ-R2-IDEM-1")
    approval_file = (
        workspace / "literature" / "screening" / "approvals" / "batch_001_approval.json"
    )
    before = approval_file.read_bytes()
    second = redeem_pairing(workspace, 1, staged["code"], request_id="REQ-R2-IDEM-1")
    assert second["approval_fingerprint"] == first["approval_fingerprint"]
    assert second["snapshot_fingerprint"] == first["snapshot_fingerprint"]
    assert second["operator_identity"] == OPERATOR
    assert second.get("idempotent") is True
    assert approval_file.read_bytes() == before  # no re-mint
    # Honesty: the idempotency record holds hashes + ids only, never the code.
    idem_raw = idempotency_path(workspace, 1).read_bytes()
    assert staged["code"].encode("ascii") not in idem_raw
    assert b"REQ-R2-IDEM-1" in idem_raw  # the correlation stem, not a secret


def test_redeem_same_stem_different_content_refuses(tmp_path: Path) -> None:
    """F-02b: same request stem with different content refuses (no stale replay)."""
    workspace, studies = _scaffold(tmp_path, name="r2-f02b")
    staged = _stage(workspace, studies)
    first = redeem_pairing(workspace, 1, staged["code"], request_id="REQ-R2-IDEM-2")
    assert first["operator_identity"] == OPERATOR
    _write_decisions(workspace, studies, decisions=["EXCLUDE", "INCLUDE"])
    with pytest.raises(AuthorityRefused) as excinfo:
        redeem_pairing(workspace, 1, staged["code"], request_id="REQ-R2-IDEM-2")
    assert excinfo.value.code == STALE_VIEW
    # A fresh stem proceeds normally: the consumed code still refuses consumed
    # (absent key -> normal path, not a replay).
    with pytest.raises(AuthorityRefused) as excinfo2:
        redeem_pairing(workspace, 1, staged["code"], request_id="REQ-R2-IDEM-OTHER")
    assert excinfo2.value.code == PAIRING_CODE_INVALID
    assert excinfo2.value.details["reason"] == "consumed"


def test_begin_with_note_or_file_refuses_before_staging(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """F-03: --begin + --decisions-file/--message refuses, staging nothing.

    Rationale (in code): the staged binding must equal operator intent;
    silently dropping the note/file would be a bypass-shaped surprise.
    """
    from scholar_harness.authority.review import REVIEW_BEGIN_ARGS_REFUSED

    workspace, studies = _scaffold(tmp_path, name="r2-f03")
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    decisions = _write_decisions(workspace, studies)
    with pytest.raises(review_mod.ReviewRefused) as excinfo:
        review_mod.cmd_approve(workspace, 1, decisions_file=str(decisions), begin=True)
    assert excinfo.value.code == REVIEW_BEGIN_ARGS_REFUSED
    assert "Pairing code" not in capsys.readouterr().out
    assert not pairing_path(workspace, 1).exists()
    with pytest.raises(review_mod.ReviewRefused) as excinfo2:
        review_mod.cmd_approve(workspace, 1, message="a note", begin=True)
    assert excinfo2.value.code == REVIEW_BEGIN_ARGS_REFUSED
    assert not pairing_path(workspace, 1).exists()
    screening = workspace / "literature" / "screening"
    assert not (screening / "approvals" / "batch_001_approval.json").exists()
    assert not (screening / "publication_approval.json").exists()


def test_pairing_file_lock_contention_refuses_locked(tmp_path: Path) -> None:
    """F-04: held lock file -> defined locked refusal, not a double mint.

    The pre-existing ``test_concurrent_redeem_single_winner`` still pins the
    two-threads single-winner property; this test pins the inter-process
    file lock (``.pairing.lock``, AG-03C semantics): contention refuses with
    ``PAIRING_LOCKED`` and mints nothing, and releasing the lock lets the
    genuine code mint exactly once.
    """
    from scholar_harness.authority.pairing import PAIRING_LOCKED

    workspace, studies = _scaffold(tmp_path, name="r2-f04")
    staged = _stage(workspace, studies)
    lock_path = pairing_path(workspace, 1).parent / ".pairing.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("4242", encoding="utf-8")  # simulate a live writer
    try:
        with pytest.raises(AuthorityRefused) as excinfo:
            redeem_pairing(workspace, 1, staged["code"], lock_timeout_s=0.05)
        assert excinfo.value.code == PAIRING_LOCKED
        assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_STAGED
        assert not (
            workspace
            / "literature"
            / "screening"
            / "approvals"
            / "batch_001_approval.json"
        ).exists()
    finally:
        lock_path.unlink(missing_ok=True)
    result = redeem_pairing(workspace, 1, staged["code"])
    assert result["operator_identity"] == OPERATOR
    assert pairing_status(workspace, 1)["state"] == PAIRING_STATE_CONSUMED
    assert not lock_path.exists()  # released after the mint


def test_pairing_lock_permission_error_refuses_locked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows access-denied on the lock path is contention, not a crash.

    The pairing mirror of ``generations._acquire_lock`` must map
    ``PermissionError`` (Windows: existing directory / exclusively opened
    file) to the same typed ``PAIRING_LOCKED`` refusal instead of letting the
    exception escape.
    """
    from scholar_harness.authority import pairing as pairing_mod
    from scholar_harness.authority.pairing import PAIRING_LOCKED

    workspace = tmp_path / "ws"
    lock_path = pairing_mod._pairing_lock_path(workspace)
    real_open = os.open

    def deny_lock(path, flags, *args, **kwargs):
        if Path(path) == lock_path:
            raise PermissionError(13, "Access is denied", str(path))
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", deny_lock)
    with pytest.raises(AuthorityRefused) as excinfo:
        pairing_mod._acquire_pairing_lock(workspace, 0.05)
    assert excinfo.value.code == PAIRING_LOCKED
    assert "access denied" in excinfo.value.message.lower()
    assert not lock_path.exists()
