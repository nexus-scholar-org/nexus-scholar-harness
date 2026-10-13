"""AG-04 worker/review/approve/defer interaction tests (RELEASE lane, hermetic).

Exercices the complete supported Windows workflow on synthetic ``tmp_path``
state only — prepare, worker recommendation, researcher review,
override-with-supersession, operator approval, gated publication, and
CURRENT downstream consumption — plus focused negatives. Reuses the
AG-03A/B/C primitives and the AG-02 gates; no AG-03 negative is duplicated
here (only AG-04 surfaces: worker scope, review display, per-batch
approval, deferral, Low-IL invocation).

Acceptance map (packet sections 2/3/5):

* AG04-01 worker-scoped-writes — ``test_demo_full_supported_flow``,
  ``test_worker_writes_only_recommendations_dir``,
  ``test_worker_refuses_foreign_destination``.
* AG04-02 review-displays-snapshot — ``test_demo_full_supported_flow``,
  ``test_review_displays_snapshot_bytes``, ``test_review_is_read_only``.
* AG04-03 approve-binds-exact-content — ``test_demo_full_supported_flow``,
  ``test_approve_binds_exact_content``.
* AG04-04 override-supersedes — ``test_demo_full_supported_flow``,
  ``test_override_supersedes_preserves_original``.
* AG04-05 stale-approval-refused — ``test_stale_approval_refused``.
* AG04-06 unresolved-or-defer — ``test_unresolved_refuses_approve_unless_deferred``,
  ``test_pending_rows_never_approvable``.
* AG04-07 cancel-defer-states — ``test_defer_and_cancel_leave_nothing_publishable``,
  ``test_cli_wiring`` (defer-then-approve lift).
* AG04-08 tamper-refused — ``test_display_approval_tamper_refused``.
* AG04-09 current-generation-published — ``test_demo_full_supported_flow``,
  ``test_current_generation_published_downstream``.
* AG04-10 worker-cannot-approve — ``test_worker_cannot_approve_low_integrity``,
  ``test_forged_identity_never_trusted``,
  ``test_low_il_worker_process_windows``.

Explicit non-claims: POSIX enforcement unproven (Windows MIC remains the
proven deployment; the Low-IL unit refusal is monkeypatched
cross-platform and the real Low-IL run is Windows-only); no audit events
are emitted (synthetic state only); single-screener flow only.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace as _replace_binding
from datetime import UTC, datetime
from pathlib import Path

import pytest

import scholar_harness.authority.review as review_mod
from scholar_harness.authority import isolation
from scholar_harness.authority.binding import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_MISSING,
    APPROVAL_NOT_OPERATOR,
    APPROVAL_SCOPE_MISMATCH,
    ApprovalBinding,
    AuthorityRefused,
    OperatorIdentity,
    canonical_json_bytes,
    content_sha256,
    mint_approval,
    verify_approval,
)
from scholar_harness.authority.generations import (
    PUBLICATION_OUTPUTS,
    GenerationStatus,
    require_current_generation,
)
from scholar_harness.authority.lifecycle import capture_snapshot, supersede
from scholar_harness.authority.review import (
    OPERATOR_CONTEXT_MISSING,
    REVIEW_INVALID_DECISIONS,
    REVIEW_POLICY_VERSION,
    UNRESOLVED_FINALIZE_REFUSED,
    ReviewRefused,
    approve_command,
    defer_command,
    load_operator_context,
    load_review_snapshot,
    show_review,
)
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.extraction_producer import _included_records
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_harness.screening.integrity import ScreeningIntegrityRefused
from scholar_harness.screening.worker import (
    PENDING_DECISION,
    RECOMMENDATION_SCHEMA,
    WORKER_BATCH_MISSING,
    WORKER_DESTINATION_REFUSED,
    WORKER_INVALID_BATCH,
    WORKER_PARENT_UNRESOLVED,
    WorkerRefused,
    recommendation_path,
    run_recommend,
)
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

WS_ID = "WSP-" + "e" * 32
OPERATOR = "ag04-operator@example"
NOW = "2026-10-13T12:00:00+00:00"
LATER = "2026-10-13T13:00:00+00:00"
FORGED_ACTOR = "Dr. Forged Human Reviewer"

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


# --- synthetic workspace scaffold -------------------------------------------- #


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
            title=f"AG-04 synthetic record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ag04-record-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ag04-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(n_docs)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WS_ID,
        run_id=f"RUN-ag04-{name}",
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
                    "external_ids": {"doi": f"10.1000/ag04-{i}"},
                }
                for i, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )
    cmd_prepare(workspace, batch_size=20)
    return workspace, studies


def _write_operator_context(workspace: Path) -> Path:
    path = workspace / "literature" / "screening" / "operator_context.json"
    path.write_text(
        json.dumps(
            {
                "schema": "harness-operator-context-v1",
                "operator_identity": OPERATOR,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_decisions(
    workspace: Path,
    studies: list[dict],
    decisions: list[str] | None = None,
    **fields: object,
) -> Path:
    """Write researcher-resolved legacy decisions for batch 1."""
    resolved = decisions if decisions is not None else ["INCLUDE", "EXCLUDE"]
    entries = [
        {
            "workspace_id": study["study_id"],
            "decision": decision,
            "method": "HUMAN",
            "screener_id": OPERATOR,
            "screening_reasoning": f"AG-04 researcher resolution {i}.",
            **fields,
        }
        for i, (study, decision) in enumerate(zip(studies, resolved))
    ]
    path = workspace / "literature" / "screening" / "batch_001_decisions.json"
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return path


def _recommend(workspace: Path) -> Path:
    return run_recommend(workspace, 1, produced_at=NOW)


def _approve(workspace: Path, **kwargs: object) -> dict:
    params: dict[str, object] = {"approved_at": NOW}
    params.update(kwargs)
    return approve_command(workspace, 1, **params)  # type: ignore[arg-type]


def _publication_paths(workspace: Path) -> list[Path]:
    lit = workspace / "literature"
    return [lit / name for name in PUBLICATION_OUTPUTS] + [
        lit / "screening" / "generation.json"
    ]


def _base_fingerprint(recommendation_bytes: bytes, review_record: dict) -> str:
    """Recompute the revision-1 base fingerprint a superseding revision links.

    The approval stamps ``captured_at`` deterministically (the approval
    moment), so the preserved-original link is exactly re-derivable here.
    """
    base_binding = _replace_binding(
        ApprovalBinding(**review_record["binding"]), recommendation_revision=1
    )
    base = capture_snapshot(
        recommendation_bytes,
        recommendation_bytes,
        base_binding,
        captured_at=review_record["reviewed_at"],
    )
    return base.fingerprint()


# --- AG04-01/02/03/04/09: the complete supported flow ------------------------- #


def test_demo_full_supported_flow(tmp_path: Path) -> None:
    """AG04-01/02/03/04/09: prepare, worker, review, override, approve, publish, CURRENT."""
    workspace, studies = _scaffold(tmp_path)
    assert len(studies) == 2
    _write_operator_context(workspace)

    # Step 1 (prepare) happened in the scaffold: bound batch + manifest exist.
    assert (workspace / "literature" / "screening" / "batch_001.json").is_file()

    # Step 2 (worker): draft rows land ONLY in the recommendations dir, pending.
    rec_path = _recommend(workspace)
    assert rec_path == recommendation_path(workspace, 1)
    payload = json.loads(rec_path.read_text(encoding="utf-8"))
    assert payload["schema"] == RECOMMENDATION_SCHEMA
    assert payload["worker"]["method"] == "DETERMINISTIC_CLI"
    assert payload["workspace_id"] == WS_ID
    assert {row["study_id"] for row in payload["rows"]} == {
        study["study_id"] for study in studies
    }
    for row in payload["rows"]:
        assert row["decision"] == PENDING_DECISION
        assert row["reasons"] == []
        assert row["uncertainty"]
        assert row["criterion_refs"]["inclusion"]
        assert row["source_locators"]["doi"] is not None

    # Step 3 (review): the display reads the exact snapshot bytes.
    snapshot, rec_bytes, final_none = load_review_snapshot(workspace, 1)
    assert final_none is None  # nothing resolved yet
    text = show_review(snapshot)
    assert snapshot.recommendation_sha256 == content_sha256(rec_bytes)
    assert snapshot.recommendation_sha256 in text
    assert snapshot.fingerprint() in text
    assert WS_ID in text and "Protocol parents:" in text
    for study in studies:
        assert study["study_id"] in text

    # Step 4 (researcher override): resolved content differs from the draft.
    _write_decisions(workspace, studies)
    _, _, final_bytes = load_review_snapshot(workspace, 1)
    assert final_bytes is not None and final_bytes != rec_bytes

    # Step 5 (approve): superseding revision preserves the original.
    before = rec_path.read_bytes()
    result = _approve(workspace, message="AG-04 demo approval.")
    assert result["superseded"] is True
    assert rec_path.read_bytes() == before
    assert result["binding"]["recommendation_revision"] == 2
    assert result["operator_identity"] == OPERATOR
    review_record = json.loads(Path(result["review_path"]).read_text("utf-8"))
    assert review_record["supersedes"] == _base_fingerprint(before, review_record)
    assert review_record["superseded_by"] == OPERATOR
    assert review_record["message"] == "AG-04 demo approval."

    # Step 6 (publish): the existing collect gate consumes the staged approval.
    cmd_collect(workspace)

    # Step 7 (CURRENT downstream): generation coherent, consumer current.
    status = require_current_generation(workspace)
    assert status.status is GenerationStatus.CURRENT, status.message
    generation = json.loads(
        (workspace / "literature" / "screening" / "generation.json").read_text("utf-8")
    )
    for name in PUBLICATION_OUTPUTS:
        on_disk = (workspace / "literature" / name).read_bytes()
        assert content_sha256(on_disk) == generation["outputs"][name]
    assert (
        generation["approval_fingerprint"] == result["publication_approval_fingerprint"]
    )
    assert generation["operator_identity"] == OPERATOR


def test_worker_writes_only_recommendations_dir(tmp_path: Path) -> None:
    """AG04-01: the worker run adds exactly one file, inside recommendations/."""
    workspace, _ = _scaffold(tmp_path)
    before = {
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    out = _recommend(workspace)
    after = {
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert after - before == {
        "literature/screening/recommendations/batch_001_recommendation.json"
    }
    assert out.relative_to(workspace).as_posix() == (
        "literature/screening/recommendations/batch_001_recommendation.json"
    )


def test_worker_refuses_foreign_destination(tmp_path: Path) -> None:
    """AG04-01: any destination outside recommendations/ refuses typed, writing nothing."""
    workspace, _ = _scaffold(tmp_path)
    digests_before = {
        path: content_sha256(path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    }
    for foreign in (
        workspace / "literature" / "screening" / "batch_001_decisions.json",
        workspace / "literature" / "screening" / "publication_approval.json",
        workspace / "audit" / "journal.jsonl",
        workspace / "literature" / "included.json",
    ):
        with pytest.raises(WorkerRefused) as excinfo:
            run_recommend(workspace, 1, output_path=foreign, produced_at=NOW)
        assert excinfo.value.code == WORKER_DESTINATION_REFUSED
    digests_after = {
        path: content_sha256(path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    }
    # Nothing created, nothing modified — pre-existing files are untouched.
    assert digests_before == digests_after
    assert not (workspace / "literature" / "screening" / "recommendations").exists()


def test_worker_missing_batch_refuses_with_nothing_published(tmp_path: Path) -> None:
    """AG04-01/negative: no assigned batch means a typed error, no publication."""
    workspace, _ = _scaffold(tmp_path)
    with pytest.raises(WorkerRefused) as excinfo:
        run_recommend(workspace, 2, produced_at=NOW)
    assert excinfo.value.code == WORKER_BATCH_MISSING
    for path in _publication_paths(workspace):
        assert not path.exists()


@pytest.mark.parametrize(
    "mutate",
    ["corrupt-json", "empty-papers", "no-criteria"],
    ids=["corrupt-json", "empty-papers", "no-criteria"],
)
def test_worker_invalid_batch_refuses(tmp_path: Path, mutate: str) -> None:
    """AG04-01/negative: invalid batch input refuses typed, publishing nothing."""
    workspace, _ = _scaffold(tmp_path)
    batch_file = workspace / "literature" / "screening" / "batch_001.json"
    if mutate == "corrupt-json":
        batch_file.write_text("{not json", encoding="utf-8")
    else:
        payload = json.loads(batch_file.read_text(encoding="utf-8"))
        if mutate == "empty-papers":
            payload["papers"] = []
        else:
            payload["protocol"]["screening_criteria"] = {
                "inclusion": [],
                "exclusion": [],
            }
        batch_file.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(WorkerRefused) as excinfo:
        run_recommend(workspace, 1, produced_at=NOW)
    assert excinfo.value.code == WORKER_INVALID_BATCH
    for path in _publication_paths(workspace):
        assert not path.exists()


@pytest.mark.parametrize(
    "remove", ["verified", "registry"], ids=["verified", "registry"]
)
def test_worker_unresolved_parents_refuse(tmp_path: Path, remove: str) -> None:
    """AG04-01/negative: missing verified material or registry refuses typed."""
    workspace, _ = _scaffold(tmp_path)
    if remove == "verified":
        (workspace / "literature" / "verified.json").unlink()
    else:
        (workspace / "audit" / "artifact_registry.json").unlink()
    with pytest.raises(WorkerRefused) as excinfo:
        run_recommend(workspace, 1, produced_at=NOW)
    assert excinfo.value.code == WORKER_PARENT_UNRESOLVED
    for path in _publication_paths(workspace):
        assert not path.exists()


# --- AG04-02: review displays the snapshot ------------------------------------- #


def test_review_displays_snapshot_bytes(tmp_path: Path) -> None:
    """AG04-02: display carries decision/reasons/uncertainty/refs/hashes of the hashed bytes."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    snapshot, rec_bytes, final_bytes = load_review_snapshot(workspace, 1)
    assert final_bytes is not None
    assert snapshot.bytes_for("parse") is snapshot.bytes_for("hash")
    assert snapshot.bytes_for("hash") is snapshot.bytes_for("display")
    text = show_review(snapshot)
    assert snapshot.recommendation_sha256 == content_sha256(rec_bytes)
    assert snapshot.final_decision_sha256 == content_sha256(final_bytes)
    assert snapshot.recommendation_sha256 in text
    assert snapshot.final_decision_sha256 in text
    assert snapshot.binding.protocol_fingerprint in text
    assert snapshot.binding.corpus_fingerprint in text
    assert "AG-04 researcher resolution 0." in text
    assert "Uncertainty:" in text


def test_review_is_read_only(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """AG04-02: review displays to stdout and writes nothing."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    digests_before = {
        path: content_sha256(path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    }
    from scholar_harness.agent_screen import main as agent_main

    argv = ["agent_screen", "review", str(workspace), "--batch", "1"]
    old_argv = sys.argv
    sys.argv = argv
    try:
        agent_main()
    finally:
        sys.argv = old_argv
    out = capsys.readouterr().out
    assert "Screening review" in out
    digests_after = {
        path: content_sha256(path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    }
    assert digests_before == digests_after


# --- AG04-03/04: approval binds exact content; override supersedes ------------- #


def test_approve_binds_exact_content(tmp_path: Path) -> None:
    """AG04-03: the minted approval fingerprints the exact snapshot buffers."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(
        workspace,
        studies,
        actor=FORGED_ACTOR,
        method="HUMAN",
        confidence=0.99,
        reviewer="professor-x",
    )
    result = _approve(workspace)
    rec_bytes = (recommendation_path(workspace, 1)).read_bytes()
    final_bytes = (
        workspace / "literature" / "screening" / "batch_001_decisions.json"
    ).read_bytes()
    assert result["recommendation_sha256"] == content_sha256(rec_bytes)
    assert result["final_decision_sha256"] == content_sha256(final_bytes)
    approval_payload = json.loads(Path(result["approval_path"]).read_text("utf-8"))
    assert approval_payload["schema"] == "harness-screening-batch-approval-v1"
    record_dict = approval_payload["approval"]
    assert record_dict["operator_identity"] == OPERATOR
    assert record_dict["recommendation_sha256"] == content_sha256(rec_bytes)
    assert record_dict["final_decision_sha256"] == content_sha256(final_bytes)
    assert result["approval_fingerprint"] == content_sha256(
        canonical_json_bytes(record_dict)
    )
    # Forged worker/reviewer labels confer nothing and leak nowhere.
    record_json = json.dumps(record_dict, sort_keys=True)
    assert FORGED_ACTOR not in record_json
    assert "professor-x" not in record_json
    assert result["binding"]["policy_version"] == REVIEW_POLICY_VERSION


def test_override_supersedes_preserves_original(tmp_path: Path) -> None:
    """AG04-04: a differing reviewed file burns revision 2, original byte-identical."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    rec_path = _recommend(workspace)
    original = rec_path.read_bytes()
    _write_decisions(workspace, studies)
    result = _approve(workspace)
    assert result["superseded"] is True
    assert rec_path.read_bytes() == original
    assert result["binding"]["recommendation_revision"] == 2
    review_record = json.loads(Path(result["review_path"]).read_text("utf-8"))
    assert review_record["supersedes"] == _base_fingerprint(original, review_record)
    assert review_record["superseded_by"] == OPERATOR


def test_stale_approval_refused(tmp_path: Path) -> None:
    """AG04-05: post-review content change refuses; old revision approval never covers new."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    result = _approve(workspace)
    assert result["superseded"] is True

    # Unit limb: the revision-1 approval does not cover the revision-2 binding.
    binding_v1 = ApprovalBinding(
        workspace_id=WS_ID,
        run_id="RUN-stale",
        batch_id="BATCH-001",
        protocol_fingerprint="sha256:" + "b" * 64,
        corpus_fingerprint="sha256:" + "c" * 64,
        recommendation_revision=1,
        policy_version=REVIEW_POLICY_VERSION,
    )
    reviewed = canonical_json_bytes({"batch_id": "BATCH-001", "rows": []})
    final_v1 = canonical_json_bytes({"batch_id": "BATCH-001", "revision": 1})
    record_v1 = mint_approval(
        operator=OperatorIdentity(
            identity=OPERATOR, source="publisher-operator-context"
        ),
        binding=binding_v1,
        reviewed_bytes=reviewed,
        final_decision_bytes=final_v1,
        approved_at=NOW,
    )
    snapshot_v1 = capture_snapshot(reviewed, final_v1, binding_v1)
    snapshot_v2 = supersede(
        snapshot_v1,
        canonical_json_bytes({"batch_id": "BATCH-001", "revision": 2}),
        OperatorIdentity(identity=OPERATOR, source="publisher-operator-context"),
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_approval(
            record=record_v1,
            expected_binding=snapshot_v2.binding,
            reviewed_bytes=snapshot_v2.bytes_for("hash"),
            final_decision_bytes=snapshot_v2.final_bytes_for("hash"),
            policy_version=REVIEW_POLICY_VERSION,
            now=NOW,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH

    # Gate limb: swapping the underlying evidence after approval refuses at collect.
    verified_path = workspace / "literature" / "verified.json"
    rows = json.loads(verified_path.read_text(encoding="utf-8"))
    rows[0]["title"] = "Post-review swapped title"
    verified_path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(AuthorityRefused) as excinfo2:
        cmd_collect(workspace)
    assert excinfo2.value.code == APPROVAL_CONTENT_CHANGED
    for path in _publication_paths(workspace):
        assert not path.exists()


# --- AG04-06/07: unresolved-or-defer; cancel/defer states ---------------------- #


@pytest.mark.parametrize("value", ["MAYBE", "CONFLICT"], ids=["maybe", "conflict"])
def test_unresolved_refuses_approve_unless_deferred(tmp_path: Path, value: str) -> None:
    """AG04-06: MAYBE/CONFLICT refuse approval; deferral with reason is the way out."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies, decisions=[value, "INCLUDE"])
    with pytest.raises(ScreeningIntegrityRefused) as excinfo:
        _approve(workspace)
    assert excinfo.value.code == UNRESOLVED_FINALIZE_REFUSED
    screening = workspace / "literature" / "screening"
    assert not (screening / "publication_approval.json").exists()
    for path in _publication_paths(workspace):
        assert not path.exists()
    out = defer_command(workspace, 1, reason="awaiting full text", recorded_at=NOW)
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["cancelled"] is False
    assert record["reason"] == "awaiting full text"


def test_pending_rows_never_approvable(tmp_path: Path) -> None:
    """AG04-06: worker-pending rows and non-decision payloads refuse approval."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    rec_path = _recommend(workspace)
    decisions_path = workspace / "literature" / "screening" / "batch_001_decisions.json"

    # A raw pending list is not a terminal resolution.
    decisions_path.write_text(
        json.dumps(
            [
                {"workspace_id": study["study_id"], "decision": PENDING_DECISION}
                for study in studies
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ScreeningIntegrityRefused) as excinfo:
        _approve(workspace)
    assert excinfo.value.code == UNRESOLVED_FINALIZE_REFUSED

    # The recommendation payload itself is not a decisions file.
    decisions_path.write_bytes(rec_path.read_bytes())
    with pytest.raises(ReviewRefused) as excinfo2:
        _approve(workspace)
    assert excinfo2.value.code == REVIEW_INVALID_DECISIONS
    assert not (
        workspace / "literature" / "screening" / "publication_approval.json"
    ).exists()


@pytest.mark.parametrize(
    "reason", ["awaiting full text", "CANCELLED"], ids=["defer", "cancel"]
)
def test_defer_and_cancel_leave_nothing_publishable(
    tmp_path: Path, reason: str
) -> None:
    """AG04-07: defer/cancel records state with reason; collect publishes nothing."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    out = defer_command(workspace, 1, reason=reason, recorded_at=NOW)
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["reason"] == reason
    assert record["cancelled"] is (reason == "CANCELLED")
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING
    for path in _publication_paths(workspace):
        assert not path.exists()
    status = require_current_generation(workspace)
    assert status.status is GenerationStatus.MISMATCHED


def test_defer_voids_staged_approval(tmp_path: Path) -> None:
    """AG04-07: deferring after approval voids the staged approval; collect refuses."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    _approve(workspace)
    staged = workspace / "literature" / "screening" / "publication_approval.json"
    assert staged.is_file()
    record = json.loads(
        defer_command(workspace, 1, reason="second look", recorded_at=NOW).read_text(
            encoding="utf-8"
        )
    )
    assert not staged.exists()
    assert record["voided_approvals"]
    with pytest.raises(AuthorityRefused) as excinfo:
        cmd_collect(workspace)
    assert excinfo.value.code == APPROVAL_MISSING


def test_defer_requires_reason(tmp_path: Path) -> None:
    """AG04-07/negative: a reasonless defer refuses typed."""
    workspace, _ = _scaffold(tmp_path)
    with pytest.raises(ReviewRefused) as excinfo:
        defer_command(workspace, 1, reason="  ", recorded_at=NOW)
    assert excinfo.value.code == "REVIEW_REASON_MISSING"


# --- AG04-08: tamper refused ---------------------------------------------------- #


def test_display_approval_tamper_refused(tmp_path: Path) -> None:
    """AG04-08: bytes changed between display and approval invalidate the approval."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    snapshot, _, _ = load_review_snapshot(workspace, 1)
    displayed = show_review(snapshot)
    assert snapshot.recommendation_sha256 in displayed

    record = mint_approval(
        operator=OperatorIdentity(
            identity=OPERATOR, source="publisher-operator-context"
        ),
        binding=snapshot.binding,
        reviewed_bytes=snapshot.bytes_for("hash"),
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        approved_at=NOW,
    )
    tampered = bytearray(snapshot.bytes_for("hash"))
    tampered[10] ^= 0x01
    assert bytes(tampered) != snapshot.bytes_for("display")
    assert content_sha256(bytes(tampered)) != snapshot.recommendation_sha256
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_approval(
            record=record,
            expected_binding=snapshot.binding,
            reviewed_bytes=bytes(tampered),
            final_decision_bytes=snapshot.final_bytes_for("hash"),
            policy_version=REVIEW_POLICY_VERSION,
            now=NOW,
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED


# --- AG04-09: current-generation publication + downstream ----------------------- #


def test_current_generation_published_downstream(tmp_path: Path) -> None:
    """AG04-09: the authorized generation is CURRENT and the consumer reads it."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    _approve(workspace)
    cmd_collect(workspace)
    assert require_current_generation(workspace).status is GenerationStatus.CURRENT
    records = _included_records(workspace)
    assert [record["workspace_id"] for record in records] == [studies[0]["study_id"]]


# --- AG04-10: worker cannot approve ---------------------------------------------- #


def test_worker_cannot_approve_low_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AG04-10: approve refuses when this process runs at worker (Low) integrity."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    monkeypatch.setattr(review_mod, "_is_low_integrity_process", lambda: True)
    with pytest.raises(AuthorityRefused) as excinfo:
        _approve(workspace)
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR
    screening = workspace / "literature" / "screening"
    assert not (screening / "publication_approval.json").exists()
    assert not (screening / "approvals" / "batch_001_approval.json").exists()
    assert not (screening / "reviews" / "batch_001_review.json").exists()


def test_missing_operator_context_refused(tmp_path: Path) -> None:
    """AG04-10/negative: no publisher context means no approval, never a default."""
    workspace, studies = _scaffold(tmp_path)
    _recommend(workspace)
    _write_decisions(workspace, studies, reviewed_by="professor-x", method="HUMAN")
    with pytest.raises(ReviewRefused) as excinfo:
        _approve(workspace)
    assert excinfo.value.code == OPERATOR_CONTEXT_MISSING
    assert not (
        workspace / "literature" / "screening" / "publication_approval.json"
    ).exists()


@pytest.mark.parametrize(
    "identity",
    ["", "unknown", "agent-unknown"],
    ids=["empty", "unknown", "agent-unknown"],
)
def test_forged_identity_never_trusted(tmp_path: Path, identity: str) -> None:
    """AG04-10: forged/empty context identities never become the approver."""
    workspace, studies = _scaffold(tmp_path)
    _recommend(workspace)
    _write_decisions(workspace, studies)
    context_path = workspace / "literature" / "screening" / "operator_context.json"
    context_path.write_text(
        json.dumps(
            {"schema": "harness-operator-context-v1", "operator_identity": identity}
        ),
        encoding="utf-8",
    )
    if identity == "":
        with pytest.raises(ReviewRefused) as excinfo:
            load_operator_context(workspace)
        assert excinfo.value.code == OPERATOR_CONTEXT_MISSING
    else:
        with pytest.raises(AuthorityRefused) as excinfo2:
            load_operator_context(workspace)
        assert excinfo2.value.code == APPROVAL_NOT_OPERATOR
    with pytest.raises((ReviewRefused, AuthorityRefused)):
        _approve(workspace)


def test_load_operator_context_reads_publisher_file(tmp_path: Path) -> None:
    """AG04-10: the context identity loads only from the publisher-owned file."""
    workspace, _ = _scaffold(tmp_path)
    _write_operator_context(workspace)
    identity = load_operator_context(workspace)
    assert identity.identity == OPERATOR
    assert identity.source == "publisher-operator-context"


WORKER_LOW_TEMPLATE = """
import json, pathlib, sys

sys.path.insert(0, r"{src}")
for _p in pathlib.Path(r"{root}").glob("tools/*/src"):
    sys.path.insert(0, str(_p))

from scholar_harness.authority.review import approve_command
from scholar_harness.screening.worker import run_recommend

ws = pathlib.Path(r"{ws}")
inbox = pathlib.Path(r"{inbox}")
res = {{}}

try:
    approve_command(ws, 1, approved_at="2026-10-13T12:00:00+00:00")
    res["approve"] = "WROTE"
except Exception as exc:  # noqa: BLE001 - report, never raise
    res["approve"] = "REFUSED:" + type(exc).__name__ + ":" + getattr(exc, "code", "?")

try:
    run_recommend(ws, 1, produced_at="2026-10-13T12:00:00+00:00")
    res["recommend"] = "WROTE"
except Exception as exc:  # noqa: BLE001 - report, never raise
    res["recommend"] = "DENIED:" + type(exc).__name__ + ":" + getattr(exc, "code", "?")

(inbox / "ag04_report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
"""


@pytest.mark.skipif(
    not isolation.available(),
    reason="Windows MIC isolation unavailable on this host",
)
def test_low_il_worker_process_windows(tmp_path: Path) -> None:
    """AG04-10 (Windows): a real Low-IL worker cannot approve; inbox write is its limit.

    Reuses the AG-03A isolation boundary without duplicating its file-write
    matrix: only the AG-04 surfaces (approve invocation, recommendation
    destination) are attempted from the Low process.
    """
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)

    pub = tmp_path / "publisher"
    inbox = tmp_path / "inbox"
    isolation.provision_publisher_store(pub)
    isolation.provision_worker_inbox(inbox)
    script = tmp_path / "ag04_low_worker.py"
    script.write_text(
        WORKER_LOW_TEMPLATE.format(
            src=ROOT / "src", root=ROOT, ws=workspace, inbox=inbox
        )
        .replace("{{", "{")
        .replace("}}", "}"),
        encoding="utf-8",
    )
    exit_code = isolation.run_low_integrity(script, cwd=tmp_path)
    assert exit_code == 0, f"worker process failed to run (exit {exit_code})"
    report = json.loads((inbox / "ag04_report.json").read_text(encoding="utf-8"))
    assert report["approve"] == "REFUSED:AuthorityRefused:APPROVAL_NOT_OPERATOR", report
    assert report["recommend"].startswith("DENIED:"), report
    assert report["recommend"] != "WROTE"
    # The Low worker left no approval state behind.
    screening = workspace / "literature" / "screening"
    assert not (screening / "publication_approval.json").exists()
    assert not (screening / "approvals" / "batch_001_approval.json").exists()


# --- CLI wiring ------------------------------------------------------------------ #


def test_cli_wiring(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """AG04-07/CLI: recommend/review/approve/defer/collect through agent_screen main."""
    from scholar_harness.agent_screen import main as agent_main

    workspace, studies = _scaffold(tmp_path, name="cli-ws")
    _write_operator_context(workspace)

    def _run(*argv: str) -> str:
        old_argv = sys.argv
        sys.argv = ["agent_screen", *argv]
        try:
            agent_main()
        finally:
            sys.argv = old_argv
        return capsys.readouterr().out

    out = _run("recommend", str(workspace), "--batch", "1")
    assert "batch_001_recommendation.json" in out
    out = _run("review", str(workspace), "--batch", "1")
    assert "Screening review" in out
    _write_decisions(workspace, studies)
    out = _run("approve", str(workspace), "--batch", "1", "--message", "cli approval")
    assert OPERATOR in out
    assert (
        workspace / "literature" / "screening" / "publication_approval.json"
    ).is_file()

    # Defer voids the staged approval; approving again lifts the deferral.
    out = _run("defer", str(workspace), "--batch", "1", "--reason", "second look")
    assert "deferred" in out
    assert not (
        workspace / "literature" / "screening" / "publication_approval.json"
    ).exists()
    _run("approve", str(workspace), "--batch", "1")
    assert not (
        workspace / "literature" / "screening" / "deferrals" / "batch_001_deferral.json"
    ).exists()
    _run("collect", str(workspace))
    assert require_current_generation(workspace).status is GenerationStatus.CURRENT


def test_approve_accepts_custom_decisions_file(tmp_path: Path) -> None:
    """CLI option: approve --decisions-file binds the given reviewed file."""
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    custom = workspace / "literature" / "screening" / "researcher_resolved.json"
    custom.write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "decision": decision,
                    "method": "HUMAN",
                    "screening_reasoning": "Custom path resolution.",
                }
                for study, decision in zip(studies, ["INCLUDE", "EXCLUDE"])
            ]
        ),
        encoding="utf-8",
    )
    result = approve_command(workspace, 1, decisions_file=custom, approved_at=NOW)
    assert result["final_decision_sha256"] == content_sha256(custom.read_bytes())
    # Deliver the reviewed bytes to the default path collect consumes, then
    # the staged approval verifies and the generation is CURRENT.
    (workspace / "literature" / "screening" / "batch_001_decisions.json").write_bytes(
        custom.read_bytes()
    )
    cmd_collect(workspace)
    assert require_current_generation(workspace).status is GenerationStatus.CURRENT
