"""Protected action API tests (UI-07 §§3/5 + HCM-02 journal; RELEASE lane, hermetic).

Covers the four ``/api/v1/screening/actions/*`` routes plus the drafts
reuse contract and the job_runner journal migration, over synthetic
``tmp_path`` workspaces (never workspaces/, never a real workspace). The
terminal act in every flow is ``pairing.begin_pairing`` (the
``approve --begin`` semantics); no route mints or returns a code.

Acceptance map:

* paired identity + binding (ACT-04/06) — ``test_redeem_mints_paired_approval``.
* browser identity ignored (ACT-06-neg) — ``test_browser_identity_ignored``.
* Low-IL refuse (ACT-11) — ``test_redeem_refuses_low_integrity``.
* missing context (ACT-10) — ``test_redeem_refuses_without_context``.
* stale/changed-parents (ACT-09) — ``test_redeem_refuses_stale_*``.
* coverage/duplicate/unresolved (ACT-10/12) — ``test_redeem_refuses_*``.
* override lineage (ACT-13) — ``test_redeem_preserves_override_lineage``.
* defer-voids (ACT-14) — ``test_defer_voids_challenge_and_approvals``.
* audit-fail-closed (ACT-15) — ``test_redeem_audit_failure_rolls_back``,
  ``test_publish_audit_failure_publishes_nothing``.
* idempotent retry + no duplicates (ACT-07/08) —
  ``test_publish_idempotent_retry``.
* CURRENT on success + downstream refusal (ACT-16) —
  ``test_publish_current_and_downstream_refusal``.
* journal shared service + sensitive absent (ACT-17/18) —
  ``test_journal_rows_carry_request_id_without_secrets``,
  ``test_job_runner_journal_*``.
* loopback allow / non-loopback refuse / preflight / GETs (ACT-19/20) —
  ``test_action_origin_*``, ``test_gets_never_mutate``,
  ``test_action_post_routes_reject_get``.
* drafts reuse, no duplicate (spec §6) — ``test_drafts_reuse_posts_decisions``,
  ``test_no_duplicate_drafts_route``.
* real loopback HTTP (ACT-19) — ``test_real_http_loopback_allow_and_refuse``.

No cross-test-file imports: the scaffold mirrors
tests/authority/test_ag04_interaction.py::_scaffold.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scholar_harness.authority.review as review_mod
from scholar_harness.authority.pairing import begin_pairing
from scholar_harness.console import create_app
from scholar_harness.console.runtimes.job_runner import Job, JobRunner, _journal_event
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_harness.screening.worker import run_recommend
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

WS_ID = "WSP-" + "a" * 32
OPERATOR = "ui07-api-operator@example"
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
            title=f"UI-07 API synthetic record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ui07-api-record-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ui07api-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(n_docs)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WS_ID,
        run_id=f"RUN-ui07api-{name}",
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
                    "external_ids": {"doi": f"10.1000/ui07api-{i}"},
                }
                for i, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )
    cmd_prepare(workspace, batch_size=20)
    return workspace, studies


def _write_operator_context(workspace: Path) -> None:
    (workspace / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps(
            {"schema": "harness-operator-context-v1", "operator_identity": OPERATOR}
        ),
        encoding="utf-8",
    )


def _write_decisions(
    workspace: Path, studies: list[dict], decisions: list[str] | None = None
) -> None:
    resolved = decisions if decisions is not None else ["INCLUDE", "EXCLUDE"]
    entries = [
        {
            "workspace_id": study["study_id"],
            "decision": decision,
            "screening_reasoning": f"UI-07 API resolution {i}.",
        }
        for i, (study, decision) in enumerate(zip(studies, resolved))
    ]
    (workspace / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(entries, indent=2), encoding="utf-8"
    )


def _ready(workspace: Path, studies: list[dict]) -> str:
    """Recommend + resolve + stage a challenge; return the terminal code."""
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    return begin_pairing(workspace, 1)["code"]


def _journal_rows(workspace: Path) -> list[dict]:
    path = workspace / "audit" / "journal.jsonl"
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _snapshot(ws: Path) -> dict[str, str]:
    out = {}
    for path in sorted(ws.rglob("*")):
        if path.is_file() and ".harness-console" not in path.parts:
            rel = path.relative_to(ws).as_posix()
            out[rel] = (
                f"{path.stat().st_mtime_ns}:{hashlib.sha256(path.read_bytes()).hexdigest()}"
            )
    return out


# --- approval/publication ------------------------------------------------------ #


def test_redeem_mints_paired_approval(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    before_status = client.get("/api/v1/screening/actions/pairing/status?batch=1")
    assert before_status.status_code == 200
    assert before_status.json()["state"] == "STAGED"

    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code, "request_id": "REQ-API-1"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["shape"] == "screening-action-redeem-v1"
    assert body["request_id"] == "REQ-API-1"
    assert body["operator_identity"] == OPERATOR
    assert body["approval_fingerprint"].startswith("sha256:")
    assert body["snapshot_fingerprint"].startswith("sha256:")
    assert body["journal_event_id"].startswith("EVT-")
    # No code or hash anywhere in the response.
    assert code not in r.text
    assert "salted_hash" not in r.text

    after_status = client.get("/api/v1/screening/actions/pairing/status?batch=1")
    assert after_status.json()["state"] == "CONSUMED"
    # Replay is consumed.
    again = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert again.status_code == 403
    assert again.json()["detail"]["code"] == "PAIRING_CODE_INVALID"


def test_browser_identity_ignored(tmp_path):
    """Forged names/roles/reviewer strings are dropped, never minted."""
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={
            "batch": 1,
            "code": code,
            "reviewer": "Dr. Forged",
            "operator_identity": "evil-operator",
            "role": "admin",
            "actor": "mallory",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["operator_identity"] == OPERATOR
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
    assert "Forged" not in json.dumps(approval) and "mallory" not in json.dumps(
        approval
    )


def test_redeem_refuses_low_integrity(tmp_path, monkeypatch):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    monkeypatch.setattr(review_mod, "_is_low_integrity_process", lambda: True)
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "APPROVAL_NOT_OPERATOR"
    assert (
        client.get("/api/v1/screening/actions/pairing/status?batch=1").json()["state"]
        == "STAGED"
    )


def test_redeem_refuses_without_context(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    (workspace / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps({"operator_identity": OPERATOR}), encoding="utf-8"
    )
    # Stage with a context, then remove it: redeem must refuse, not default.
    code = begin_pairing(workspace, 1)["code"]
    (workspace / "literature" / "screening" / "operator_context.json").unlink()
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "OPERATOR_CONTEXT_MISSING"


def test_redeem_refuses_stale_content(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    _write_decisions(workspace, studies, decisions=["EXCLUDE", "INCLUDE"])
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "STALE_VIEW"
    assert detail["details"]["changed_element"] == "snapshot_content"


def test_redeem_refuses_stale_parents(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
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
    art_path.write_bytes(json.dumps(envelope, indent=2).encode("utf-8"))
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "STALE_VIEW"


def test_redeem_refuses_coverage_and_unresolved(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies, decisions=["MAYBE", "INCLUDE"])
    code = begin_pairing(workspace, 1)["code"]
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "UNRESOLVED_FINALIZE_REFUSED"

    # Coverage: drop one decision, keep one (missing + no extra).
    _write_decisions(workspace, studies[:1], decisions=["INCLUDE"])
    code2 = begin_pairing(workspace, 1)["code"]
    r2 = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code2},
    )
    assert r2.status_code == 422
    assert r2.json()["detail"]["code"] == "COVERAGE_INCOMPLETE"


def test_redeem_refuses_broken_identity_bridge(tmp_path):
    """A verified row without identity refuses typed instead of 500ing."""
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    verified = json.loads(
        (workspace / "literature" / "verified.json").read_text(encoding="utf-8")
    )
    del verified[0]["workspace_id"]
    verified[0].pop("external_ids", None)
    (workspace / "literature" / "verified.json").write_text(
        json.dumps(verified), encoding="utf-8"
    )
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "VERIFICATION_IDENTITY_MISSING_DOI"


def test_redeem_refuses_duplicates(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    entries = [
        {"workspace_id": studies[0]["study_id"], "decision": "INCLUDE"},
        {"workspace_id": studies[0]["study_id"], "decision": "EXCLUDE"},
    ]
    (workspace / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(entries), encoding="utf-8"
    )
    code = begin_pairing(workspace, 1)["code"]
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "DUPLICATE_ENTRY"


def test_redeem_preserves_override_lineage(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 200
    assert r.json()["superseded"] is True
    review_record = json.loads(
        (
            workspace / "literature" / "screening" / "reviews" / "batch_001_review.json"
        ).read_text(encoding="utf-8")
    )
    assert review_record["superseded_by"] == OPERATOR
    assert review_record["supersedes"]


def test_defer_voids_challenge_and_approvals(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))

    # Defer before redeem voids the staged challenge itself.
    d0 = client.post(
        "/api/v1/screening/actions/defer",
        json={"batch": 1, "reason": "awaiting full text"},
    )
    assert d0.status_code == 200, d0.text
    assert d0.json()["pairing_voided"] is True
    assert (
        client.get("/api/v1/screening/actions/pairing/status?batch=1").json()["state"]
        == "CONSUMED"
    )
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
        ).status_code
        == 403
    )

    # Re-stage (a fresh terminal act), redeem, then defer: the staged
    # approvals are voided and nothing stays publishable.
    code2 = begin_pairing(workspace, 1)["code"]
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code2},
        ).status_code
        == 200
    )

    d = client.post(
        "/api/v1/screening/actions/defer",
        json={"batch": 1, "reason": "second look", "request_id": "REQ-DEFER-1"},
    )
    assert d.status_code == 200, d.text
    payload = d.json()
    assert payload["shape"] == "screening-action-defer-v1"
    assert payload["request_id"] == "REQ-DEFER-1"
    assert payload["pairing_voided"] is False  # already consumed by the redeem
    assert payload["cancelled"] is False
    assert not (
        workspace / "literature" / "screening" / "publication_approval.json"
    ).exists()
    # The deferred batch leaves nothing publishable.
    p = client.post("/api/v1/screening/actions/publish", json={})
    assert p.status_code == 409
    assert p.json()["detail"]["code"] == "APPROVAL_MISSING"

    # Reasonless defer refuses typed.
    e = client.post("/api/v1/screening/actions/defer", json={"batch": 1, "reason": " "})
    assert e.status_code == 422
    assert e.json()["detail"]["code"] == "REVIEW_REASON_MISSING"


def test_publish_current_and_downstream_refusal(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
        ).status_code
        == 200
    )
    p = client.post(
        "/api/v1/screening/actions/publish", json={"request_id": "REQ-PUB-1"}
    )
    assert p.status_code == 200, p.text
    payload = p.json()
    assert payload["shape"] == "screening-action-publish-v1"
    assert payload["status"] == "CURRENT"
    assert payload["generation_id"].startswith("GEN-")
    assert payload["request_id"] == "REQ-PUB-1"
    # Downstream refusal is preserved: drift the outputs, the read gate refuses.
    inc = workspace / "literature" / "included.json"
    inc.write_text(inc.read_text(encoding="utf-8") + " ", encoding="utf-8")
    stale = client.get("/api/v1/ui/publication-status").json()
    assert stale["status"] == "STALE"
    assert stale["code"] == "GENERATION_STALE"


def test_publish_idempotent_retry(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
        ).status_code
        == 200
    )
    first = client.post("/api/v1/screening/actions/publish", json={}).json()
    before = (workspace / "literature" / "screening" / "generation.json").read_bytes()
    second = client.post("/api/v1/screening/actions/publish", json={}).json()
    after = (workspace / "literature" / "screening" / "generation.json").read_bytes()
    assert first["generation_id"] == second["generation_id"]
    assert before == after  # identical retry rewrites nothing
    history = list(
        (workspace / "literature" / "screening" / "generations").glob("*.json")
    )
    assert len(history) == 1  # no duplicate generations


def test_full_chain_begin_to_replay_fails(tmp_path):
    """The continuous journey over the wire: begin (terminal) -> STAGED ->
    redeem -> CONSUMED -> publish CURRENT -> replay fails -> publish joins."""
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.get("/api/v1/screening/actions/pairing/status?batch=1").json()["state"]
        == "STAGED"
    )
    redeem = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code, "request_id": "REQ-CHAIN-1"},
    )
    assert redeem.status_code == 200, redeem.text
    assert redeem.json()["request_id"] == "REQ-CHAIN-1"
    assert (
        client.get("/api/v1/screening/actions/pairing/status?batch=1").json()["state"]
        == "CONSUMED"
    )
    first = client.post(
        "/api/v1/screening/actions/publish", json={"request_id": "REQ-CHAIN-2"}
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "CURRENT"
    generation_id = first.json()["generation_id"]
    # The consumed code replays as a refusal, never a second approval.
    replay = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert replay.status_code == 403
    assert replay.json()["detail"]["code"] == "PAIRING_CODE_INVALID"
    # Publishing again joins the same CURRENT generation idempotently.
    second = client.post("/api/v1/screening/actions/publish", json={})
    assert second.status_code == 200
    assert second.json()["generation_id"] == generation_id
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "CURRENT"


def test_publish_drift_refuses_without_earlier_success(tmp_path):
    """Join-or-refuse (spec §3.4): after CURRENT, drifted content refuses on
    publish instead of replaying the earlier success, and the committed
    generation bytes are untouched (fail-closed, nothing published)."""
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
        ).status_code
        == 200
    )
    first = client.post("/api/v1/screening/actions/publish", json={})
    assert first.status_code == 200, first.text
    generation_path = workspace / "literature" / "screening" / "generation.json"
    before = generation_path.read_bytes()
    inc = workspace / "literature" / "included.json"
    inc.write_text(inc.read_text(encoding="utf-8") + " ", encoding="utf-8")
    again = client.post("/api/v1/screening/actions/publish", json={})
    assert again.status_code != 200, again.text
    assert generation_path.read_bytes() == before  # nothing rewritten
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "STALE"


def test_publish_retry_with_broken_audit_still_joins_current(tmp_path, monkeypatch):
    """Prev-generation-preserved: known-CURRENT, then the collector audit
    sink dies. The identical retry joins the same generation (the join path
    performs no new writes), leaving the committed bytes identical and the
    read gate CURRENT — a dead sink cannot corrupt what is committed."""
    import scholar_harness.screening.collector as collector_mod

    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
        ).status_code
        == 200
    )
    first = client.post("/api/v1/screening/actions/publish", json={})
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "CURRENT"
    generation_id = first.json()["generation_id"]
    generation_path = workspace / "literature" / "screening" / "generation.json"
    before = generation_path.read_bytes()

    def _boom(*args, **kwargs):
        raise OSError("synthetic audit failure")

    monkeypatch.setattr(collector_mod, "log_event", _boom)
    retry = client.post("/api/v1/screening/actions/publish", json={})
    assert retry.status_code == 200, retry.text
    assert retry.json()["generation_id"] == generation_id
    assert generation_path.read_bytes() == before
    status = client.get("/api/v1/ui/publication-status").json()
    assert status["status"] == "CURRENT"
    assert status["generation_id"] == generation_id


def test_action_origin_malformed_refused(tmp_path):
    """Malformed and lookalike origins refuse before any state is touched."""
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    for evil in (
        "http://localhost.evil.example",
        "http://127.0.0.1.evil.example",
        "null",
        "not-an-origin",
        "file://localhost",
        "http://localhost:abc",
    ):
        r = client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
            headers={"Origin": evil},
        )
        assert r.status_code == 403, evil
        assert r.json()["detail"]["code"] == "ACTION_ORIGIN_REFUSED", evil
    # The staged challenge survived every refused attempt untouched.
    assert (
        client.get("/api/v1/screening/actions/pairing/status?batch=1").json()["state"]
        == "STAGED"
    )


def test_action_preflight_blocks_post(tmp_path):
    """The single frozen loopback CORS policy answers preflight with GET
    only, including on the action routes (cross-origin POST never allowed)."""
    workspace, _ = _scaffold(tmp_path)
    client = TestClient(create_app(workspace))
    pre = client.options(
        "/api/v1/screening/actions/pairing/redeem",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "POST" not in pre.headers.get("access-control-allow-methods", "")


# --- audit fail-closed --------------------------------------------------------- #


def test_redeem_audit_failure_rolls_back(tmp_path, monkeypatch):
    """A journal OSError at redeem surfaces 500 with the mint rolled back."""
    import scholar_harness.console.api.screening as screening_api

    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)

    def _boom(**kwargs):
        raise OSError("synthetic journal failure")

    monkeypatch.setattr(screening_api, "log_event", _boom)
    client = TestClient(create_app(workspace))
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
    )
    assert r.status_code == 500
    assert r.json()["detail"]["code"] == "ACTION_AUDIT_FAILED"
    # Rollback: the challenge is still staged, no approval residue exists.
    assert (
        client.get("/api/v1/screening/actions/pairing/status?batch=1").json()["state"]
        == "STAGED"
    )
    screening = workspace / "literature" / "screening"
    assert not (screening / "approvals" / "batch_001_approval.json").exists()
    assert not (screening / "publication_approval.json").exists()


def test_publish_audit_failure_publishes_nothing(tmp_path, monkeypatch):
    """An audit-sink failure at publish refuses with nothing consumable left."""
    import scholar_harness.screening.collector as collector_mod

    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
        ).status_code
        == 200
    )

    def _boom(*args, **kwargs):
        raise OSError("synthetic audit failure")

    monkeypatch.setattr(collector_mod, "log_event", _boom)
    r = client.post("/api/v1/screening/actions/publish", json={})
    assert r.status_code == 500
    assert r.json()["detail"]["code"] == "PROMOTION_AUDIT_FAILED"
    assert not (workspace / "literature" / "screening" / "generation.json").exists()
    assert not (workspace / "literature" / "included.json").exists()


def test_journal_rows_carry_request_id_without_secrets(tmp_path):
    """Action rows thread request_id; the code never reaches the journal."""
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code, "request_id": "REQ-J-1"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/screening/actions/publish", json={"request_id": "REQ-J-2"}
        ).status_code
        == 200
    )
    rows = _journal_rows(workspace)
    actions = {row["action"] for row in rows}
    assert "SCREENING_PAIRING_REDEEMED" in actions
    assert "SCREENING_GENERATION_PUBLISHED" in actions
    assert "SCREENING_PUBLISH_COMPLETED" in actions
    by_action = {row["action"]: row for row in rows}
    assert (
        by_action["SCREENING_PAIRING_REDEEMED"]["parameters"]["request_id"] == "REQ-J-1"
    )
    assert (
        by_action["SCREENING_PUBLISH_COMPLETED"]["parameters"]["request_id"]
        == "REQ-J-2"
    )
    blob = (workspace / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert code not in blob
    assert "salted_hash" not in blob


# --- drafts reuse + HTTP surface ------------------------------------------------ #


def test_drafts_reuse_posts_decisions(tmp_path):
    """POST decisions stays the drafts operation: writes drafts, mints nothing."""
    workspace, studies = _scaffold(tmp_path)
    ws_noprep = workspace
    _write_operator_context(ws_noprep)
    run_recommend(ws_noprep, 1, produced_at=NOW)
    client = TestClient(create_app(ws_noprep))
    papers = [{"workspace_id": s["study_id"], "decision": "INCLUDE"} for s in studies]
    r = client.post(
        "/api/v1/screening/batch/1/decisions",
        json={"batch": 1, "reviewed_by": "browser-draft", "decisions": papers},
    )
    assert r.status_code == 200
    screening = workspace / "literature" / "screening"
    assert (screening / "batch_001_decisions.json").is_file()
    assert not (screening / "approvals" / "batch_001_approval.json").exists()
    assert not (screening / "publication_approval.json").exists()
    assert not list(screening.glob("pairing/*.json"))


def test_no_duplicate_drafts_route(tmp_path):
    """There is no /actions/drafts writer: drafts live at the reused route."""
    workspace, _ = _scaffold(tmp_path)
    client = TestClient(create_app(workspace))
    assert client.post("/api/v1/screening/actions/drafts", json={}).status_code == 404


def test_action_origin_refused(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    evil = {"Origin": "https://evil.example"}
    r = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code},
        headers=evil,
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "ACTION_ORIGIN_REFUSED"
    assert (
        client.get(
            "/api/v1/screening/actions/pairing/status?batch=1", headers=evil
        ).status_code
        == 403
    )
    # Loopback origins and absent origins pass the guard.
    assert (
        client.get(
            "/api/v1/screening/actions/pairing/status?batch=1",
            headers={"Origin": "http://localhost:3000"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/screening/actions/pairing/redeem",
            json={"batch": 1, "code": code},
            headers={"Origin": "http://127.0.0.1:8765"},
        ).status_code
        == 200
    )


def test_action_caller_identity_refused(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    r = client.get(
        "/api/v1/screening/actions/pairing/status?batch=1&workspace_id=WSP-ffff"
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "CALLER_IDENTITY_REFUSED"


def test_action_post_routes_reject_get(tmp_path):
    workspace, _ = _scaffold(tmp_path)
    client = TestClient(create_app(workspace))
    assert client.get("/api/v1/screening/actions/pairing/redeem").status_code == 405
    assert client.get("/api/v1/screening/actions/defer").status_code == 405
    assert client.get("/api/v1/screening/actions/publish").status_code == 405


def test_gets_never_mutate(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    before = _snapshot(workspace)
    battery = [
        "/api/v1/screening/actions/pairing/status?batch=1",
        "/api/v1/screening/ui/batches",
        "/api/v1/screening/ui/batch/1/rows",
        "/api/v1/screening/ui/batch/1/review",
        "/api/v1/screening/ui/batch/9/rows",
        "/api/v1/screening/actions/pairing/status?batch=9",
    ]
    for route in battery:
        client.get(route)
    assert _snapshot(workspace) == before


def test_status_absent_and_missing_batch(tmp_path):
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    run_recommend(workspace, 1, produced_at=NOW)
    _write_decisions(workspace, studies)
    client = TestClient(create_app(workspace))
    absent = client.get("/api/v1/screening/actions/pairing/status?batch=1").json()
    assert absent["state"] == "ABSENT"
    assert absent["snapshot_fingerprint"] is None
    assert "salted_hash" not in absent and "code" not in {k.lower() for k in absent} - {
        "snapshot_fingerprint"
    }
    missing = client.get("/api/v1/screening/actions/pairing/status?batch=9")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "BATCH_MISSING"


# --- real loopback HTTP ----------------------------------------------------------- #


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_http(url: str, budget_s: float = 90.0) -> bool:
    deadline = time.monotonic() + budget_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def _http_json(
    method: str, url: str, payload: dict | None = None, origin: str | None = None
) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if origin is not None:
        req.add_header("Origin", origin)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def test_real_http_loopback_allow_and_refuse(tmp_path):
    """The action API answers over real loopback HTTP and refuses evil origins."""
    workspace, studies = _scaffold(tmp_path, name="http-ws")
    code = _ready(workspace, studies)
    port = _free_port()
    origin = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "scholar-harness",
            "serve",
            "--workspace",
            str(workspace),
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert _wait_http(f"{origin}/healthz"), "console did not come up on loopback"
        status, text = _http_json(
            "GET",
            f"{origin}/api/v1/screening/actions/pairing/status?batch=1",
            origin="http://localhost:3000",
        )
        assert status == 200, text
        assert json.loads(text)["state"] == "STAGED"
        status, text = _http_json(
            "POST",
            f"{origin}/api/v1/screening/actions/pairing/redeem",
            {"batch": 1, "code": code},
            origin="http://localhost:3000",
        )
        assert status == 200, text
        assert json.loads(text)["operator_identity"] == OPERATOR
        assert code not in text
        # Evil origin is refused over the wire too.
        status, text = _http_json(
            "POST",
            f"{origin}/api/v1/screening/actions/pairing/redeem",
            {"batch": 1, "code": code},
            origin="https://evil.example",
        )
        assert status == 403, text
        assert json.loads(text)["detail"]["code"] == "ACTION_ORIGIN_REFUSED"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()


# --- HCM-02: job_runner journal migration ------------------------------------------- #


def test_job_runner_journal_delegates_to_shared_service(tmp_path):
    """_journal_event writes through workspace.audit (canonical shape)."""
    ws = tmp_path / "ws"
    ws.mkdir()
    event_id = _journal_event(
        workspace=ws,
        action_id="sync",
        description="sync job job_x finished with state 'success'",
        status="SUCCESS",
        inputs=["sync"],
        outputs=["job_x", "exit=0"],
        metrics={"exit_code": 0},
    )
    assert event_id.startswith("EVT-")
    rows = _journal_rows(ws)
    assert len(rows) == 1
    row = rows[0]
    assert row["event_id"] == event_id
    assert row["action"] == "SYNC"
    assert row["agent_or_tool"] == "scholar-harness-console"
    assert row["status"] == "SUCCESS"
    assert row["metrics"] == {"exit_code": 0}
    assert set(row) == {
        "timestamp",
        "event_id",
        "action",
        "agent_or_tool",
        "description",
        "parameters",
        "inputs",
        "outputs",
        "metrics",
        "status",
    }


def test_job_runner_journal_failure_propagates(tmp_path, monkeypatch):
    """A journal OSError surfaces per the shared contract (never swallowed)."""
    import scholar_harness.workspace.audit as audit_mod

    ws = tmp_path / "ws"
    ws.mkdir()

    def _boom(*args, **kwargs):
        raise OSError("synthetic journal failure")

    monkeypatch.setattr(audit_mod, "append_event", _boom)
    with pytest.raises(OSError):
        _journal_event(
            workspace=ws,
            action_id="sync",
            description="boom",
            status="FAILED",
        )


class _FakeStdout:
    def __init__(self, lines: list[bytes]):
        self._lines = lines

    def __aiter__(self):
        async def _gen():
            for line in self._lines:
                yield line

        return _gen()


class _FakeProc:
    def __init__(self, lines: list[bytes] | None = None, exit_code: int = 0):
        self.stdout = _FakeStdout(lines or [b"hello\n"])
        self._exit = exit_code
        self.pid = 4242
        self.returncode = None

    async def wait(self) -> int:
        self.returncode = self._exit
        return self._exit


def _tracked_job(ws: Path, action_id: str = "sync") -> tuple[JobRunner, Job]:
    runner = JobRunner(ws)
    job = Job(
        job_id="job_tracked_1",
        action_id=action_id,
        command=["fake"],
        cwd=ws,
        timeout_s=60,
    )
    runner.jobs[job.job_id] = job
    runner._active_actions.add(action_id)
    return runner, job


def test_job_runner_completion_journals_and_releases(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    runner, job = _tracked_job(ws)
    asyncio.run(runner._run_to_completion(job, _FakeProc()))
    assert job.state == "success"
    assert job.exit_code == 0
    assert job.journal_event_id and job.journal_event_id.startswith("EVT-")
    assert runner._active_actions == set()
    rows = _journal_rows(ws)
    assert rows[-1]["action"] == "SYNC"
    assert rows[-1]["status"] == "SUCCESS"


def test_job_runner_completion_journal_failure_surfaces_but_releases(
    tmp_path, monkeypatch
):
    import scholar_harness.workspace.audit as audit_mod

    ws = tmp_path / "ws"
    ws.mkdir()
    runner, job = _tracked_job(ws)

    def _boom(*args, **kwargs):
        raise OSError("synthetic journal failure")

    monkeypatch.setattr(audit_mod, "append_event", _boom)
    with pytest.raises(OSError):
        asyncio.run(runner._run_to_completion(job, _FakeProc()))
    assert job.state == "success"  # the job ran; only the journal failed
    assert job.journal_event_id is None
    assert runner._active_actions == set()  # no single-flight leak


def test_job_runner_cancel_journals_and_releases(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    runner, job = _tracked_job(ws)
    job.state = "running"
    done = asyncio.run(runner.cancel(job.job_id))
    assert done.state == "cancelled"
    assert runner._active_actions == set()
    rows = _journal_rows(ws)
    assert rows[-1]["action"] == "SYNC"
    assert rows[-1]["status"] == "PARTIAL"


def test_job_runner_cancel_journal_failure_surfaces_but_releases(tmp_path, monkeypatch):
    import scholar_harness.workspace.audit as audit_mod

    ws = tmp_path / "ws"
    ws.mkdir()
    runner, job = _tracked_job(ws)
    job.state = "running"

    def _boom(*args, **kwargs):
        raise OSError("synthetic journal failure")

    monkeypatch.setattr(audit_mod, "append_event", _boom)
    with pytest.raises(OSError):
        asyncio.run(runner.cancel(job.job_id))
    assert job.state == "cancelled"
    assert runner._active_actions == set()


# --- UI07-ACTIONS-R2 repairs (F-02 API wiring + F-05; appended) ---


def test_redeem_same_request_id_retry_returns_stored_over_http(tmp_path):
    """F-02 (API wiring): same request_id + identical content replays stored success.

    First POST mints; second POST with the same request_id and the same
    (now consumed) code returns the stored fingerprints without re-minting
    (approval bytes identical); a fresh request_id still refuses consumed.
    """
    workspace, studies = _scaffold(tmp_path, name="r2-idem-http")
    code = _ready(workspace, studies)
    client = TestClient(create_app(workspace))
    first = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code, "request_id": "REQ-R2-HTTP-1"},
    )
    assert first.status_code == 200, first.text
    body1 = first.json()
    approval_file = (
        workspace / "literature" / "screening" / "approvals" / "batch_001_approval.json"
    )
    before = approval_file.read_bytes()
    second = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code, "request_id": "REQ-R2-HTTP-1"},
    )
    assert second.status_code == 200, second.text
    body2 = second.json()
    assert body2["approval_fingerprint"] == body1["approval_fingerprint"]
    assert body2["snapshot_fingerprint"] == body1["snapshot_fingerprint"]
    assert approval_file.read_bytes() == before  # no re-mint
    third = client.post(
        "/api/v1/screening/actions/pairing/redeem",
        json={"batch": 1, "code": code, "request_id": "REQ-R2-HTTP-OTHER"},
    )
    assert third.status_code == 403
    assert third.json()["detail"]["code"] == "PAIRING_CODE_INVALID"


def test_job_runner_journal_failure_captured_on_job(tmp_path, monkeypatch):
    """F-05: a failing journal sink leaves error set with a null id (state kept).

    The operation outcome itself is unchanged (state stays success); the
    OSError still surfaces per the shared contract, but pollers now see the
    provenance gap via job.error instead of a clean success with null id.
    """
    import scholar_harness.workspace.audit as audit_mod

    ws = tmp_path / "ws-f05"
    ws.mkdir()
    runner, job = _tracked_job(ws)

    def _boom(*args, **kwargs):
        raise OSError("synthetic journal failure")

    monkeypatch.setattr(audit_mod, "append_event", _boom)
    with pytest.raises(OSError):
        asyncio.run(runner._run_to_completion(job, _FakeProc()))
    assert job.state == "success"  # the job ran; only the journal failed
    assert job.journal_event_id is None
    assert job.error is not None and "journal failed" in job.error
    assert runner._active_actions == set()  # no single-flight leak
