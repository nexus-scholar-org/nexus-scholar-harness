"""H-run-small-fixes Part A: approve every decided batch in one action (finding 38).

The acceptance run of 2026-11-20 had 54 batches of 20. Approval was one batch
at a time, each with its own one-time code printed in the engine's terminal:
54 codes, and the terminal was not visible to a researcher for whom the app
was started. These tests drive the console over HTTP only.

What does not change (CON-02/03, contract §9.1, spec 09 decision 1): each
batch generation still gets its own fresh one-time code, the pairing store
still holds one salted hash per batch, and each approval still binds one
batch's bytes. The new action stages the codes of every decided batch at
once, shows them together on this computer (terminal, and a desktop window
when the app was started for the researcher), and redeems them from one paste.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scholar_harness.authority import pairing as pairing_mod
from scholar_harness.console import create_app
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening.batcher import cmd_prepare
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "e" * 32
BASE = "/api/v1/screening"
DESKTOP, PHONE = "desktop-token", "phone-token"


@pytest.fixture(autouse=True)
def _fast_hash(monkeypatch):
    """Fewer PBKDF2 rounds keep 54 batches quick; the floor test pins the real value."""
    monkeypatch.setattr(pairing_mod, "PAIRING_PBKDF2_ITERATIONS", 1_000)


def _workspace(root: Path, records: int, batch_size: int) -> Path:
    ws = root / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps({"project_id": "bulk", "registered_workspace_id": WS_ID}), encoding="utf-8")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").touch()
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    docs = [
        Document(
            title=f"Bulk record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"bulk-{i}",
            external_ids=ExternalIds(doi=f"10.1000/bulk-{i}"),
            abstract=f"Abstract {i} about UAV weed mapping.",
            authors=[Author("Reviewer")],
            workspace_id=f"SCI-{i:06d}",
        )
        for i in range(records)
    ]
    corpus = build_corpus_snapshot_artifact(
        docs,
        workspace_id=WS_ID,
        run_id="RUN-bulk",
        protocol_fingerprint=fingerprint,
        created_at=datetime(2026, 11, 20, tzinfo=UTC),
        commit="4" * 40,
    ).artifact
    assert accept_artifact(
        ws,
        corpus,
        expected=AcceptanceContext(
            workspace_id=WS_ID, protocol_fingerprint=fingerprint, corpus_fingerprint=corpus["corpus_fingerprint"]
        ),
    ).accepted
    (ws / "literature").mkdir()
    (ws / "literature" / "verified.json").write_text(
        json.dumps([{"workspace_id": d.workspace_id, "title": d.title, "abstract": d.abstract} for d in docs]),
        encoding="utf-8",
    )
    cmd_prepare(ws, batch_size=batch_size)
    (ws / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps({"schema": "harness-operator-context-v1", "operator_identity": "Test Researcher"}), encoding="utf-8"
    )
    return ws


class _Window:
    """Stands in for the desktop window: records what it was asked to show."""

    def __init__(self, shown: bool = True) -> None:
        self.calls: list[dict[str, Any]] = []
        self.shown = shown

    def __call__(self, **kwargs: Any) -> bool:
        self.calls.append(kwargs)
        return self.shown


def _client(ws: Path, window: _Window | None = None) -> TestClient:
    kwargs: dict[str, Any] = {"token": DESKTOP, "phone_tokens": {PHONE}}
    if window is not None:
        kwargs["code_window"] = window
    return TestClient(
        create_app(ws, **kwargs), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"}
    )


def _decide(client: TestClient, studies: list[str], outcome: str = "INCLUDE") -> None:
    """Decide the studies; a second decision on a study supersedes the first.

    The last event per study is kept on the client itself. A module-level table keyed by
    ``id(client)`` handed a new client the stale ids of a collected one whenever Python
    reused the address, and the intake then refused the events.
    """
    last: dict[str, str] = client.__dict__.setdefault("_last_decision", {})
    events = []
    for study in studies:
        binding = client.get(f"{BASE}/records/{study}").json()["binding"]
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "study_id": study,
                "screener_id": "researcher:local",
                "method": "HUMAN",
                "outcome": outcome,
                "reason_code": "EXC-01" if outcome == "EXCLUDE" else None,
                "note": None,
                "criteria": [],
                "decided_at": "2026-11-20T10:00:00.000Z",
                "device": "desktop",
                "supersedes": last.get(study),
                "proposal_shown": None,
                "binding": binding,
            }
        )
        last[study] = events[-1]["event_id"]
    for start in range(0, len(events), 200):
        response = client.post(f"{BASE}/decisions/events", json={"events": events[start : start + 200]})
        assert response.status_code == 200, response.text
        assert all(r["result"] == "accepted" for r in response.json()["results"]), response.text


def _studies_by_batch(client: TestClient) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    cursor = None
    while True:
        params: dict[str, Any] = {"view": "needs_you", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        page = client.get(f"{BASE}/queue", params=params).json()
        for item in page["items"]:
            out.setdefault(int(item["batch_index"]), []).append(item["study_id"])
        cursor = page.get("next_cursor")
        if not cursor:
            return out


def _bundle(printed: str) -> str:
    """The block of codes the engine printed (the researcher copies it)."""
    lines = printed.splitlines()
    start = next(i for i, line in enumerate(lines) if "approval codes for" in line)
    return "\n".join(line for line in lines[start + 1 :] if line.strip().startswith("batch "))


def _approvals(ws: Path) -> dict[int, dict]:
    folder = ws / "literature" / "screening" / "approvals"
    out = {}
    for path in sorted(folder.glob("batch_*_approval.json")) if folder.is_dir() else []:
        out[int(path.name.split("_")[1])] = json.loads(path.read_text(encoding="utf-8"))
    return out


def _journal(ws: Path) -> list[dict]:
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]


def test_finding_38_one_action_approves_54_decided_batches(tmp_path, capsys):
    """Reproduction: 54 decided batches of 20 needed 54 begin calls and 54 typed codes.

    Now one begin-all stages all 54, one paste of the printed block redeems
    them, and each approval still binds its own batch.
    """
    ws = _workspace(tmp_path, records=54 * 3, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    assert len(by_batch) == 54
    _decide(client, [s for studies in by_batch.values() for s in studies])
    capsys.readouterr()

    begun = client.post(f"{BASE}/actions/pairing/begin-all", json={})
    assert begun.status_code == 200, begun.text
    body = begun.json()
    assert [b["batch_index"] for b in body["batches"]] == list(range(1, 55))
    assert body["skipped"] == []
    printed = capsys.readouterr().out
    bundle = _bundle(printed)
    assert len(bundle.splitlines()) == 54
    # The codes never travel over HTTP.
    for line in bundle.splitlines():
        assert line.split(":", 1)[1].strip() not in begun.text

    redeemed = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle})
    assert redeemed.status_code == 200, redeemed.text
    result = redeemed.json()
    assert [r["batch_index"] for r in result["approved"]] == list(range(1, 55))
    assert result["refused"] == []
    assert result["publication_approval_fingerprint"]

    # One approval per batch, each binding only that batch's decision bytes (CON-03).
    approvals = _approvals(ws)
    assert sorted(approvals) == list(range(1, 55))
    from scholar_harness.authority.binding import content_sha256

    for index, record in approvals.items():
        decisions = ws / "literature" / "screening" / f"batch_{index:03d}_decisions.json"
        assert record["approval"]["final_decision_sha256"] == content_sha256(decisions.read_bytes())
    # The journal keeps its per-batch shape: one redeem row per batch.
    rows = [r for r in _journal(ws) if r["action"] == "SCREENING_PAIRING_REDEEMED"]
    assert sorted(r["parameters"]["batch_index"] for r in rows) == list(range(1, 55))
    assert all(r["parameters"]["bulk"] is True for r in rows)
    # Every code is used once: a second paste approves nothing.
    again = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle})
    assert again.status_code == 403 and again.json()["detail"]["code"] == "PAIRING_CODE_INVALID"


def test_only_decided_not_yet_approved_batches_get_a_code(tmp_path, capsys):
    ws = _workspace(tmp_path, records=12, batch_size=3)  # four batches
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, by_batch[1] + by_batch[2] + by_batch[3] + by_batch[4][:1])  # batch 4 half decided
    # Batch 1 approved one at a time first (the per-batch path stays).
    assert client.post(f"{BASE}/actions/pairing/begin", json={"batch": 1}).status_code == 200
    code = capsys.readouterr().out.split("approval code for batch 1: ")[1].split()[0]
    assert client.post(f"{BASE}/actions/pairing/redeem", json={"batch": 1, "code": code}).status_code == 200
    # Batch 3 deferred with a reason.
    assert client.post(f"{BASE}/actions/defer", json={"batch": 3, "reason": "check two records"}).status_code == 200
    capsys.readouterr()

    body = client.post(f"{BASE}/actions/pairing/begin-all", json={}).json()
    assert [b["batch_index"] for b in body["batches"]] == [2]
    assert {s["batch_index"]: s["reason"] for s in body["skipped"]} == {
        1: "ALREADY_APPROVED",
        3: "DEFERRED",
        4: "NOT_DECIDED",
    }
    assert len(_bundle(capsys.readouterr().out).splitlines()) == 1


def test_a_decision_changed_after_approval_makes_the_batch_need_a_code_again(tmp_path, capsys):
    """The staleness rule is unchanged: a changed decision needs a fresh approval."""
    ws = _workspace(tmp_path, records=6, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, by_batch[1] + by_batch[2])
    client.post(f"{BASE}/actions/pairing/begin-all", json={})
    bundle = _bundle(capsys.readouterr().out)
    assert client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle}).status_code == 200
    first = _approvals(ws)[2]["approval"]["final_decision_sha256"]

    _decide(client, by_batch[2][:1], outcome="EXCLUDE")  # a change of mind in batch 2
    capsys.readouterr()
    body = client.post(f"{BASE}/actions/pairing/begin-all", json={}).json()
    assert [b["batch_index"] for b in body["batches"]] == [2]
    bundle = _bundle(capsys.readouterr().out)
    assert client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle}).status_code == 200
    assert _approvals(ws)[2]["approval"]["final_decision_sha256"] != first


def test_a_batch_changed_between_the_code_and_the_paste_is_refused_alone(tmp_path, capsys):
    ws = _workspace(tmp_path, records=9, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, [s for studies in by_batch.values() for s in studies])
    capsys.readouterr()
    client.post(f"{BASE}/actions/pairing/begin-all", json={})
    bundle = _bundle(capsys.readouterr().out)
    _decide(client, by_batch[2][:1], outcome="EXCLUDE")  # changes after the code was shown

    result = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle}).json()
    assert [r["batch_index"] for r in result["approved"]] == [1, 3]
    assert [(r["batch_index"], r["code"]) for r in result["refused"]] == [(2, "STALE_VIEW")]
    assert result["publication_approval_fingerprint"] is None
    assert sorted(_approvals(ws)) == [1, 3]


def test_a_wrong_paste_approves_nothing(tmp_path, capsys):
    ws = _workspace(tmp_path, records=6, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, by_batch[1] + by_batch[2])
    client.post(f"{BASE}/actions/pairing/begin-all", json={})
    capsys.readouterr()

    nothing = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": "hello"})
    assert nothing.status_code == 403 and nothing.json()["detail"]["code"] == "PAIRING_CODE_INVALID"
    wrong = "batch 1: " + "A" * 26 + "\nbatch 2: " + "B" * 26
    response = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": wrong})
    assert response.status_code == 403 and response.json()["detail"]["code"] == "PAIRING_CODE_INVALID"
    assert _approvals(ws) == {}


def test_a_paste_that_lost_its_line_breaks_still_reads(tmp_path, capsys):
    """A single-line field drops line breaks; the codes have a fixed length."""
    ws = _workspace(tmp_path, records=6, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, by_batch[1] + by_batch[2])
    client.post(f"{BASE}/actions/pairing/begin-all", json={})
    bundle = _bundle(capsys.readouterr().out).replace("\n", "")
    result = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle.lower()}).json()
    assert [r["batch_index"] for r in result["approved"]] == [1, 2]


def test_nothing_to_approve_is_a_refusal_not_an_empty_success(tmp_path, capsys):
    ws = _workspace(tmp_path, records=3, batch_size=3)
    client = _client(ws)
    response = client.post(f"{BASE}/actions/pairing/begin-all", json={})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "APPROVAL_MISSING"
    assert "approval codes for" not in capsys.readouterr().out


def test_begin_all_needs_the_approver_name(tmp_path):
    ws = _workspace(tmp_path, records=3, batch_size=3)
    (ws / "literature" / "screening" / "operator_context.json").unlink()
    client = _client(ws)
    response = client.post(f"{BASE}/actions/pairing/begin-all", json={})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "OPERATOR_CONTEXT_MISSING"


def test_the_desktop_window_shows_the_codes_when_the_app_was_started_for_the_researcher(tmp_path, capsys):
    """The window belongs to the engine's own process on this computer, like the terminal.

    Nothing about the codes goes over HTTP; the response only says where they are.
    """
    ws = _workspace(tmp_path, records=6, batch_size=3)
    window = _Window()
    client = _client(ws, window)
    by_batch = _studies_by_batch(client)
    _decide(client, by_batch[1] + by_batch[2])
    capsys.readouterr()

    body = client.post(f"{BASE}/actions/pairing/begin-all", json={}).json()
    assert body["code_shown_on"] == "desktop"
    assert len(window.calls) == 1
    shown = window.calls[0]
    printed = _bundle(capsys.readouterr().out)
    assert shown["codes"] == printed
    assert shown["batches"] == [1, 2] and shown["expires_at"] == body["code_expires_at"]
    # The per-batch path shows its code in the window too.
    single = client.post(f"{BASE}/actions/pairing/begin", json={"batch": 1}).json()
    assert single["code_shown_on"] == "desktop" and window.calls[-1]["batches"] == [1]


def test_without_a_window_the_codes_stay_on_the_terminal(tmp_path, capsys):
    ws = _workspace(tmp_path, records=3, batch_size=3)
    window = _Window(shown=False)  # e.g. no display available
    client = _client(ws, window)
    _decide(client, _studies_by_batch(client)[1])
    body = client.post(f"{BASE}/actions/pairing/begin-all", json={}).json()
    assert body["code_shown_on"] == "terminal"
    assert "approval codes for 1 batch" in capsys.readouterr().out


@pytest.mark.parametrize("path", ["begin-all", "redeem-all"])
def test_a_phone_token_cannot_reach_the_bulk_approval(tmp_path, path):
    ws = _workspace(tmp_path, records=3, batch_size=3)
    client = _client(ws)
    response = client.post(
        f"{BASE}/actions/pairing/{path}", json={"codes": "x"}, headers={"Authorization": f"Bearer {PHONE}"}
    )
    assert response.status_code == 403 and response.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def test_a_foreign_origin_cannot_redeem(tmp_path):
    ws = _workspace(tmp_path, records=3, batch_size=3)
    client = _client(ws)
    response = client.post(
        f"{BASE}/actions/pairing/redeem-all", json={"codes": "x"}, headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403


# --- the desktop window (console/code_window.py) ---------------------------


def test_the_window_words_never_carry_a_code_and_the_title_is_fixed():
    from scholar_harness.console import code_window

    words = code_window.message([3, 4, 5], "2026-11-20T10:05:00+00:00")
    assert "batches 3, 4, 5" in words and "expire" in words
    assert code_window.TITLE == "Nexus Scholar: approval"
    assert code_window.message([7], "not-a-time").startswith("Approval codes for batch 7.")


def test_the_window_can_be_turned_off(monkeypatch):
    from scholar_harness.console import code_window

    monkeypatch.setenv(code_window.WINDOW_ENV, "0")
    assert code_window.enabled() is False
    assert code_window.reveal(codes="batch 1: X", batches=[1], expires_at="2026-11-20T10:05:00+00:00") is False


def test_a_window_that_fails_leaves_the_codes_on_the_terminal(tmp_path, capsys):
    ws = _workspace(tmp_path, records=3, batch_size=3)

    def broken(**_: Any) -> bool:
        raise RuntimeError("no display")

    client = _client(ws, broken)  # type: ignore[arg-type]
    _decide(client, _studies_by_batch(client)[1])
    body = client.post(f"{BASE}/actions/pairing/begin-all", json={}).json()
    assert body["code_shown_on"] == "terminal"
    assert "approval codes for 1 batch" in capsys.readouterr().out


def test_the_packaged_app_passes_the_desktop_window(tmp_path):
    """`nexus-scholar ui` is the app started for the researcher: it shows the window."""
    from scholar_harness.console import code_window, launcher

    ui = tmp_path / "ui"
    (ui / "en").mkdir(parents=True)
    (ui / "en" / "index.html").write_text("<html></html>", encoding="utf-8")
    app = launcher.Launcher(root=tmp_path, workspace=None, ui_dir=ui, open_browser=False, say=lambda _m: None)
    assert app.build_app(None).state.code_window is code_window.reveal


# --- review round 1 repairs -------------------------------------------------


def test_review_one_broken_batch_does_not_block_the_others(tmp_path, capsys):
    """A batch whose parent file is gone is listed with its refusal; the others get codes."""
    ws = _workspace(tmp_path, records=9, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, [s for studies in by_batch.values() for s in studies])
    (ws / "literature" / "screening" / "batch_003.json").unlink()
    capsys.readouterr()

    response = client.post(f"{BASE}/actions/pairing/begin-all", json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert [b["batch_index"] for b in body["batches"]] == [1, 2]
    assert [s["batch_index"] for s in body["skipped"]] == [3]
    assert body["skipped"][0]["reason"] not in ("ALREADY_APPROVED", "DEFERRED", "NOT_DECIDED")
    bundle = _bundle(capsys.readouterr().out)
    result = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle}).json()
    assert [r["batch_index"] for r in result["approved"]] == [1, 2]


def test_review_a_journal_failure_mid_paste_is_a_500_that_names_every_batch(tmp_path, capsys, monkeypatch):
    from scholar_harness.console.api import screening as screening_api

    ws = _workspace(tmp_path, records=9, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, [s for studies in by_batch.values() for s in studies])
    capsys.readouterr()
    client.post(f"{BASE}/actions/pairing/begin-all", json={})
    bundle = _bundle(capsys.readouterr().out)

    real = screening_api._journal_action
    calls = {"n": 0}

    def flaky(*args: Any, **kwargs: Any) -> dict:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        return real(*args, **kwargs)

    monkeypatch.setattr(screening_api, "_journal_action", flaky)
    response = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle})
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail["code"] == "ACTION_AUDIT_FAILED"
    assert [a["batch_index"] for a in detail["details"]["approved"]] == [1]
    assert [(r["batch_index"], r["code"]) for r in detail["details"]["refused"]] == [
        (2, "ACTION_AUDIT_FAILED"),
        (3, "NOT_ATTEMPTED"),
    ]
    # Batch 2 was rolled back; batch 1 keeps its approval and its journal row.
    assert sorted(_approvals(ws)) == [1]
    rows = [r for r in _journal(ws) if r["action"] == "SCREENING_PAIRING_REDEEMED"]
    assert [r["parameters"]["batch_index"] for r in rows] == [1]


def test_review_a_long_run_of_digits_is_read_quickly():
    import time

    start = time.perf_counter()
    assert pairing_mod.parse_code_block("9" * 64_000) == []
    assert time.perf_counter() - start < 2.0


def test_review_the_codes_are_nowhere_but_the_terminal_after_a_bulk_run(tmp_path, capsys):
    """No code in the redeem-all answer, the journal, or any file of the workspace."""
    ws = _workspace(tmp_path, records=9, batch_size=3)
    client = _client(ws)
    by_batch = _studies_by_batch(client)
    _decide(client, [s for studies in by_batch.values() for s in studies])
    capsys.readouterr()
    begun = client.post(f"{BASE}/actions/pairing/begin-all", json={})
    bundle = _bundle(capsys.readouterr().out)
    codes = [line.split(":", 1)[1].strip() for line in bundle.splitlines()]
    # One wrong line too, so a refusal message is in the answer.
    redeemed = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": bundle + "\nbatch 9: " + "C" * 26})
    assert redeemed.status_code == 200
    for code in codes:
        assert code not in begun.text and code not in redeemed.text
        for path in ws.rglob("*"):
            if path.is_file():
                assert code not in path.read_text(encoding="utf-8", errors="ignore"), path


def test_review_the_window_gets_the_codes_on_stdin_never_on_its_command_line(monkeypatch):
    """The window is a child process (Tk off the engine's main thread aborts on macOS)."""
    import subprocess

    from scholar_harness.console import code_window

    seen: dict[str, Any] = {}

    class FakeChild:
        def __init__(self, args, **kwargs):
            seen["args"], seen["kwargs"] = args, kwargs
            import io

            self.stdin = io.StringIO()
            self.stdout = io.StringIO("ready\n")
            seen["stdin"] = self.stdin
            self.stdin.close = lambda: seen.setdefault("payload", self.stdin.getvalue())  # type: ignore[method-assign]

        def poll(self):
            return None

        def kill(self):
            seen["killed"] = True

    monkeypatch.setenv(code_window.WINDOW_ENV, "1")
    monkeypatch.setattr(subprocess, "Popen", FakeChild)
    code = "batch 1: " + "D" * 26
    assert code_window.reveal(codes=code, batches=[1], expires_at="2026-11-20T10:05:00+00:00") is True
    assert seen["args"][1] == "-I" and seen["args"][2].endswith("code_window.py")
    assert all("D" * 26 not in str(a) for a in seen["args"])
    assert json.loads(seen["payload"])["codes"] == code


def test_review_a_child_that_cannot_show_a_window_leaves_the_terminal(monkeypatch):
    import io
    import subprocess

    from scholar_harness.console import code_window

    class Unavailable:
        def __init__(self, *_a, **_k):
            self.stdin, self.stdout = io.StringIO(), io.StringIO("unavailable\n")

        def poll(self):
            return 0

        def kill(self):
            pass

    monkeypatch.setenv(code_window.WINDOW_ENV, "1")
    monkeypatch.setattr(subprocess, "Popen", Unavailable)
    assert code_window.reveal(codes="batch 1: X", batches=[1], expires_at="2026-11-20T10:05:00+00:00") is False


def test_review_the_window_script_imports_the_standard_library_only():
    """The child runs the file alone (`python -I`): it must not need the package."""
    import ast
    import sys as _sys

    from scholar_harness.console import code_window

    tree = ast.parse(Path(code_window.__file__).read_text(encoding="utf-8"))
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert names <= set(_sys.stdlib_module_names) | {"__future__"}, names


def test_review_the_window_says_which_batches_and_to_close_it_if_not_asked():
    from scholar_harness.console import code_window

    words = code_window.message(list(range(1, 55)), "2026-11-20T10:05:00+00:00")
    assert "batches 1, 2, 3" in words and "and 42 more" in words
    assert "If you did not just ask for codes on the Publish screen, close this window" in words


# --- M13 Part A: the installed app has no terminal ---------------------------


def _client_without_terminal(ws: Path, window: Any) -> TestClient:
    app = create_app(ws, token=DESKTOP, code_window=window, codes_on_terminal=False)
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


def test_installed_app_the_codes_never_reach_its_log_file(tmp_path, monkeypatch):
    """Review of M13 Part A, P1: the installed app's standard output is its log file.

    The pairing rule (``authority/pairing.py``) is that a plaintext code is never
    stored or logged: with no terminal the codes go to the desktop window only.
    """
    import sys

    from scholar_harness.console import desktop

    ws = _workspace(tmp_path, records=6, batch_size=3)
    window = _Window()
    client = _client_without_terminal(ws, window)
    by_batch = _studies_by_batch(client)
    _decide(client, by_batch[1] + by_batch[2])
    log = desktop.open_log(tmp_path / "logs")
    monkeypatch.setattr(sys, "stdout", log)
    monkeypatch.setattr(sys, "stderr", log)

    whole = client.post(f"{BASE}/actions/pairing/begin-all", json={})
    single = client.post(f"{BASE}/actions/pairing/begin", json={"batch": 1})
    monkeypatch.undo()
    log.close()

    assert whole.status_code == 200 and single.status_code == 200, (whole.text, single.text)
    assert whole.json()["code_shown_on"] == "desktop" and single.json()["code_shown_on"] == "desktop"
    block = window.calls[0]["codes"]
    codes = [line.split(":", 1)[1].strip() for line in block.splitlines()]
    codes.append(window.calls[1]["codes"].split(":", 1)[1].strip())
    assert len(codes) == 3 and all(codes)
    text = log.path.read_text(encoding="utf-8")
    assert "approval code" not in text
    for code in codes:
        assert code not in text
    # The window's codes still approve.
    redeemed = client.post(f"{BASE}/actions/pairing/redeem-all", json={"codes": window.calls[-1]["codes"]})
    assert redeemed.status_code == 200 and [r["batch_index"] for r in redeemed.json()["approved"]] == [1]


@pytest.mark.parametrize("route", ["begin", "begin-all"])
def test_installed_app_without_a_window_refuses_instead_of_hiding_the_codes(tmp_path, capsys, route):
    ws = _workspace(tmp_path, records=3, batch_size=3)
    client = _client_without_terminal(ws, _Window(shown=False))
    _decide(client, _studies_by_batch(client)[1])
    capsys.readouterr()
    body = {"batch": 1} if route == "begin" else {}
    answer = client.post(f"{BASE}/actions/pairing/{route}", json=body)
    assert answer.status_code == 409
    assert answer.json()["detail"]["code"] == "APPROVAL_WINDOW_UNAVAILABLE"
    assert "approval code" not in capsys.readouterr().out


def test_the_installed_start_runs_its_engine_without_a_terminal_for_codes(tmp_path):
    from scholar_harness.console import launcher

    ui = tmp_path / "ui"
    (ui / "en").mkdir(parents=True)
    (ui / "en" / "index.html").write_text("<html></html>", encoding="utf-8")
    quiet = {"root": tmp_path, "workspace": None, "ui_dir": ui, "open_browser": False, "say": lambda _m: None}
    assert launcher.Launcher(**quiet).build_app(None).state.codes_on_terminal is True  # `nexus-scholar ui`
    assert launcher.Launcher(**quiet, codes_on_terminal=False).build_app(None).state.codes_on_terminal is False
