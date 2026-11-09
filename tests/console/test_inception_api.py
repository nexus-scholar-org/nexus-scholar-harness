"""Inception HTTP routes (M4a): drafts, steps, compile-preview and genesis.

Screens 00 and 08: a draft is created, saved, listed, resumed and discarded,
with one `rec_<hex>` session id, under `<workspaces root>/.drafts/`. Screen 06:
the preview writes nothing; genesis is the only write and goes through the
overwrite guard.
"""

from __future__ import annotations

import json
import re

import pytest
from conftest import E2E_ANSWERS
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.inception.intent import CriterionDraft
from scholar_harness.workspace import catalog

DESKTOP, PHONE = "desk-token", "phone-token"
BASE = "/api/v1/inception"
SLUG = "on-device-weed-detection-for-embedded-agriculture"


def _draft() -> dict:
    a = E2E_ANSWERS
    proof_id = CriterionDraft("inclusion", f"Reports the gold-standard proof — {a[5]}", "proof").id
    return {
        "topic": a[0], "paradigm": a[1], "playbook": a[2], "unit_of_analysis": a[4], "proof": a[5],
        "out_of_scope": [s.strip() for s in a[6].split(",")], "rqs": [a[8]],
        "concepts": [{"concept": "weed detection"}, {"concept": "on-device inference"}],
        "criteria_decisions": {proof_id: True},
        "title": "On-Device Weed Detection for Embedded Agriculture", "lead_researcher": "Dr. Mouadh",
    }


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "root"
    folder.mkdir()
    return folder


def _client(root, current=None):
    app = create_app(current, token=DESKTOP, phone_tokens={PHONE}, workspaces_root=root)
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


def _tree(path):
    return sorted(p.relative_to(path).as_posix() for p in path.rglob("*"))


def test_draft_lifecycle_with_no_workspace_open(root):
    client = _client(root)
    created = client.post(f"{BASE}/drafts", json={"draft": {"topic": "edge AI"}})
    assert created.status_code == 201, created.text
    sid = created.json()["session_id"]
    assert re.fullmatch(r"rec_[0-9a-f]{32}", sid)
    assert (root / ".drafts" / sid / "draft.json").is_file()

    listed = client.get(f"{BASE}/drafts").json()["items"]
    assert [i["session_id"] for i in listed] == [sid] and listed[0]["topic"] == "edge AI"

    record = client.get(f"{BASE}/drafts/{sid}").json()
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": {"topic": "edge AI on drones"}, "base_updated_at": record["updated_at"]})
    assert saved.status_code == 200 and saved.json()["draft"]["topic"] == "edge AI on drones"

    stale = client.put(f"{BASE}/drafts/{sid}", json={"draft": {"topic": "x"}, "base_updated_at": record["updated_at"]})
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "DRAFT_CONFLICT"

    assert client.delete(f"{BASE}/drafts/{sid}").status_code == 204
    assert client.get(f"{BASE}/drafts/{sid}").status_code == 404


def test_drafts_do_not_appear_as_workspaces(root):
    client = _client(root)
    client.post(f"{BASE}/drafts", json={"draft": {}})
    listing = catalog.listing(root, "test", None, include_invalid=True)
    assert listing["items"] == [] and listing["skipped_count"] == 0


def test_a_malformed_draft_or_id_is_refused(root):
    client = _client(root)
    bad = client.post(f"{BASE}/drafts", json={"draft": {"surprise": True}})
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "DRAFT_INVALID"
    bad_id = client.get(f"{BASE}/drafts/..%2Fescape")
    assert bad_id.status_code in (404, 422)
    assert client.get(f"{BASE}/drafts/rec_zz").json()["detail"]["code"] == "DRAFT_ID_INVALID"


def test_steps_answer_statelessly(root):
    client = _client(root)
    out = client.post(f"{BASE}/steps/scope", json={"draft": {"topic": E2E_ANSWERS[0]}})
    assert out.status_code == 200 and out.json()["recommended_paradigm"] == "Design Science"
    missing = client.post(f"{BASE}/steps/shape", json={"draft": {"topic": "x"}})
    assert missing.status_code == 422 and missing.json()["detail"]["details"]["missing"] == ["paradigm"]
    assert client.post(f"{BASE}/steps/nope", json={"draft": {}}).status_code == 404
    assert _tree(root) == []


def test_preview_writes_nothing(root):
    client = _client(root)
    out = client.post(f"{BASE}/preview", json={"draft": _draft()})
    assert out.status_code == 200, out.text
    body = out.json()
    assert body["written"] == [] and body["target"]["exists"] is False
    assert "Reports the gold-standard proof" in body["screening_criteria"]
    assert _tree(root) == []


def test_genesis_creates_the_workspace_once(root):
    client = _client(root)
    sid = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    assert made.json()["slug"] == SLUG and made.json()["replaced"] is False
    ws = root / SLUG
    assert (ws / "protocol.json").is_file()
    assert catalog.validity(ws)[0]
    journal = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert journal[-1]["action"] == "GENESIS" and journal[-1]["agent_or_tool"] == "nexus-scholar/ui"

    record = client.get(f"{BASE}/drafts/{sid}").json()
    assert record["emitted"]["slug"] == SLUG
    again = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert again.status_code == 409 and again.json()["detail"]["code"] == "DRAFT_EMITTED"
    locked = client.put(f"{BASE}/drafts/{sid}", json={"draft": {}})
    assert locked.status_code == 409 and locked.json()["detail"]["code"] == "DRAFT_EMITTED"


def test_genesis_refuses_an_existing_workspace_without_replace(root):
    client = _client(root)
    first = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    client.post(f"{BASE}/drafts/{first}/genesis", json={})
    protocol = (root / SLUG / "protocol.json").read_bytes()

    second = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    refused = client.post(f"{BASE}/drafts/{second}/genesis", json={})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "WORKSPACE_EXISTS"
    assert (root / SLUG / "protocol.json").read_bytes() == protocol

    preview = client.post(f"{BASE}/preview", json={"draft": _draft()}).json()
    assert preview["target"]["exists"] is True and preview["target"]["screening"]["bound"] is False

    replaced = client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True})
    assert replaced.status_code == 201 and replaced.json()["replaced"] is True
    assert (root / SLUG / "audit" / "replaced").is_dir()


def test_genesis_refuses_undecided_criteria(root):
    client = _client(root)
    draft = _draft()
    draft["criteria_decisions"] = {}
    sid = client.post(f"{BASE}/drafts", json={"draft": draft}).json()["session_id"]
    refused = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "CRITERIA_UNDECIDED"
    assert not (root / SLUG).exists()


def test_the_phone_cannot_reach_inception(root):
    app = create_app(None, token=DESKTOP, phone_tokens={PHONE}, workspaces_root=root)
    phone = TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {PHONE}"})
    assert phone.post(f"{BASE}/drafts", json={"draft": {}}).status_code in (401, 403)


def test_genesis_refuses_a_folder_that_is_not_a_workspace_and_keeps_it(root):
    """Review P1: a foreign folder named like the slug is never written or removed."""
    (root / SLUG).mkdir()
    (root / SLUG / "my_notes.txt").write_text("mine", encoding="utf-8")
    client = _client(root)
    sid = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    refused = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "WORKSPACE_EXISTS"
    assert _tree(root / SLUG) == ["my_notes.txt"]


def test_a_failed_genesis_removes_only_the_folder_it_created(root, monkeypatch):
    import scholar_harness.inception.steps as steps_mod

    def boom(_target):
        raise OSError("disk full")

    monkeypatch.setattr(steps_mod, "install_workspace_support_files", boom)
    client = _client(root)
    sid = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    failed = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert failed.status_code == 409 and failed.json()["detail"]["code"] == "WORKSPACE_ROOT_UNAVAILABLE"
    assert not (root / SLUG).exists()
    assert client.get(f"{BASE}/drafts/{sid}").json()["emitted"] is None


def test_genesis_over_http_needs_the_typed_slug_for_a_bound_workspace(root):
    client = _client(root)
    first = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    made = client.post(f"{BASE}/drafts/{first}/genesis", json={}).json()
    screening = root / SLUG / "literature" / "screening"
    screening.mkdir(parents=True, exist_ok=True)
    (screening / "generation.json").write_text("{}", encoding="utf-8")

    second = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    bound = client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True})
    assert bound.status_code == 409
    assert bound.json()["detail"]["code"] == "SCREENING_BOUND"
    assert bound.json()["detail"]["details"]["published"] is True

    wrong = client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True, "confirm_discard_screening_binding": "yes"})
    assert wrong.status_code == 422 and wrong.json()["detail"]["code"] == "CONFIRMATION_MISMATCH"

    ok = client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True, "confirm_discard_screening_binding": SLUG})
    assert ok.status_code == 201, ok.text
    assert ok.json()["previous_fingerprint"] == made["protocol_fingerprint"]
    genesis = [json.loads(line) for line in (root / SLUG / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()][-1]
    assert "screening binding discarded" in genesis["description"]


def test_every_inception_refusal_code_is_registered():
    """The codes the inception routes raise are in the console refusal set (and the contract §7 table)."""
    import re
    from pathlib import Path

    from scholar_harness.console import refusals

    src = Path(__file__).resolve().parents[2] / "src" / "scholar_harness"
    files = [src / "console" / "api" / "inception.py"] + [src / "inception" / f for f in ("steps.py", "drafts.py", "emit.py")]
    raised = set()
    for path in files:
        raised |= set(re.findall(r'(?:Refused|GenesisRefused)\(\s*"([A-Z_]+)"', path.read_text(encoding="utf-8")))
    assert len(raised) >= 14  # anti-vacuity
    assert raised <= refusals.CONSOLE_REFUSALS, raised - refusals.CONSOLE_REFUSALS


def _written(ws, before=None):
    """Every file under `ws` that is new or changed since `before`, in the preview's spelling.

    Skills under `.agents/skills/` and one replacement backup collapse to their folder.
    """
    out = {}
    for path in ws.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ws).as_posix()
        if rel.startswith(".agents/skills/"):
            rel = ".agents/skills/"
        elif rel.startswith("audit/replaced/"):
            rel = "audit/replaced/<UTC stamp>/"
        out.setdefault(rel, set()).add(path.read_bytes())
    if before is None:
        return set(out)
    return {rel for rel, contents in out.items() if before.get(rel) != contents}


def test_preview_names_every_file_genesis_writes(root):
    """M4b (researcher, 2026-11-09): the write gate lists exactly what genesis writes."""
    client = _client(root)
    planned = client.post(f"{BASE}/preview", json={"draft": _draft()}).json()["files"]
    sid = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    assert client.post(f"{BASE}/drafts/{sid}/genesis", json={}).status_code == 201
    ws = root / SLUG
    assert set(planned) == _written(ws)

    snapshot: dict[str, set[bytes]] = {}
    for path in ws.rglob("*"):
        if path.is_file():
            rel = path.relative_to(ws).as_posix()
            rel = ".agents/skills/" if rel.startswith(".agents/skills/") else rel
            snapshot.setdefault(rel, set()).add(path.read_bytes())
    # A changed answer, so every rewritten file differs from the first genesis.
    changed = {**_draft(), "out_of_scope": ["pre-2020 studies"]}
    replan = client.post(f"{BASE}/preview", json={"draft": changed}).json()["files"]
    second = client.post(f"{BASE}/drafts", json={"draft": changed}).json()["session_id"]
    assert client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True}).status_code == 201
    assert set(replan) == _written(ws, snapshot)


def test_a_replacement_records_its_backup_on_the_draft(root):
    """M4b (researcher, 2026-11-09): Done reads the backup and previous fingerprint after a reload."""
    client = _client(root)
    first = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    client.post(f"{BASE}/drafts/{first}/genesis", json={})
    assert set(client.get(f"{BASE}/drafts/{first}").json()["emitted"]) >= {"slug", "path", "protocol_fingerprint", "replaced"}
    assert "backup_dir" not in client.get(f"{BASE}/drafts/{first}").json()["emitted"]

    second = client.post(f"{BASE}/drafts", json={"draft": _draft()}).json()["session_id"]
    made = client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True}).json()
    emitted = client.get(f"{BASE}/drafts/{second}").json()["emitted"]
    assert emitted["backup_dir"] == made["backup_dir"] and emitted["previous_fingerprint"] == made["previous_fingerprint"]
    assert emitted["previous_fingerprint"].startswith("sha256:")


def test_preview_tells_a_workspace_from_a_folder_that_is_not_one(root):
    """M4b review #3: the checks and the file list follow what genesis decides on, the markers."""
    client = _client(root)
    (root / SLUG).mkdir()
    (root / SLUG / "my_notes.txt").write_text("mine", encoding="utf-8")
    target = client.post(f"{BASE}/preview", json={"draft": _draft()}).json()["target"]
    assert target["exists"] is True and target["workspace"] is False and target["screening"] is None
    assert "project.json" in client.post(f"{BASE}/preview", json={"draft": _draft()}).json()["files"]
