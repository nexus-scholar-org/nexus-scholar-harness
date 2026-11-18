"""Start an inception draft from an existing protocol (M10b, ``09-start-from-protocol``).

On 2026-11-13 the researcher had a finished protocol (the UAV scoping review)
and retyped all of it into the inception steps. The import maps a workspace's
``protocol.json`` (or a picked ``protocol.json`` / ``intent.json``) onto a new
draft as the researcher's own earlier text, lists what cannot come across, and
never writes the source. The UAV workspace is copied to ``tmp_path`` first.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.console.browser import POST_PATHS
from scholar_harness.inception import steps

DESKTOP = "desk-token"
BASE = "/api/v1/inception"
REPO = Path(__file__).resolve().parents[2]
UAV = REPO / "workspaces" / "uav-crop-weed-v03"


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "root"
    folder.mkdir()
    shutil.copy2(UAV / "protocol.json", (folder / "uav").mkdir() or folder / "uav" / "protocol.json")
    shutil.copy2(UAV / "intent.json", folder / "uav" / "intent.json")
    return folder


def _client(root):
    app = create_app(None, token=DESKTOP, workspaces_root=root)
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


def _protocol() -> dict:
    return json.loads((UAV / "protocol.json").read_text(encoding="utf-8"))


def _file(name: str, data: object | bytes) -> dict:
    raw = data if isinstance(data, bytes) else json.dumps(data).encode("utf-8")
    return {"kind": "file", "file_name": name, "content_base64": base64.b64encode(raw).decode("ascii")}


def _import(client, source, **extra):
    return client.post(f"{BASE}/drafts/import", json={"source": source, **extra})


def _hashes(folder: Path) -> dict[str, tuple[str, int]]:
    return {p.name: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in folder.iterdir()}


def test_import_rebuilds_uav_draft(root):
    client = _client(root)
    report = _import(client, {"kind": "workspace", "slug": "uav"})
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["needs_you"] == ["topic"]
    assert {e["what"] for e in body["lost"]} == {"facets", "rationale", "preset", "grounding"}
    assert body["source"]["read"] == "protocol" and body["source"]["protocol_fingerprint"].startswith("sha256:")
    assert not (root / ".drafts").exists()  # a dry run stores nothing

    created = _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"])
    assert created.status_code == 201, created.text
    record = created.json()
    assert record["origin"]["kind"] == "import" and record["origin"]["checked"]["shape"] is False
    draft = {**record["draft"], "topic": "UAV crop-weed mapping"}  # the one answer the report names

    criteria = client.post(f"{BASE}/steps/criteria", json={"draft": draft}).json()
    assert "proof" not in {c["source"] for c in criteria["criteria"]}
    assert criteria["undecided"] == [] and criteria["missing_sides"] == []

    preview = client.post(f"{BASE}/preview", json={"draft": draft})
    assert preview.status_code == 200, preview.text
    protocol, source = preview.json()["protocol"], _protocol()
    assert [rq["text"] for rq in protocol["research_questions"]] == [rq["text"] for rq in source["research_questions"]]
    assert [c["criterion"] for c in protocol["screening_criteria"]["inclusion"]] == [c["criterion"] for c in source["screening_criteria"]["inclusion"]]
    assert [(c["criterion"], c["reason_category"]) for c in protocol["screening_criteria"]["exclusion"]] == [
        (c["criterion"], c["reason_category"]) for c in source["screening_criteria"]["exclusion"]
    ]
    assert [r["reason_category"] for r in protocol["screening_criteria"]["exclusion"]] == ["WRONG_PLATFORM", "WRONG_TASK", "WRONG_REPORT_TYPE", "OUTSIDE_DATE_LANGUAGE"]
    assert protocol["search_strategy"]["core_concepts"] == source["search_strategy"]["core_concepts"]
    assert protocol["search_strategy"]["date_range"] == source["search_strategy"]["date_range"]
    assert protocol["search_strategy"]["languages"] == source["search_strategy"]["languages"]
    assert protocol["matrix_dimensions"] == source["matrix_dimensions"]  # all 13, every field


def test_import_never_touches_source(root):
    before = _hashes(root / "uav")
    client = _client(root)
    body = _import(client, {"kind": "workspace", "slug": "uav"}).json()
    _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"])
    assert _hashes(root / "uav") == before


def test_the_fingerprint_is_the_discovery_routes_one(root):
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol

    body = _import(_client(root), {"kind": "workspace", "slug": "uav"}).json()
    assert body["source"]["protocol_fingerprint"] == canonical_fingerprint(ResearchProtocol.model_validate(_protocol()))


def test_import_wizard_protocol_recovers_proof(root):
    proto = _protocol()
    first = "Reports the gold-standard proof — field-validated weed maps"
    proto["screening_criteria"]["inclusion"].insert(0, {"id": "INC-00", "criterion": first, "maps_to_rqs": ["RQ1", "RQ2", "RQ3", "RQ4"]})
    body = _import(_client(root), _file("protocol.json", proto)).json()
    assert body["draft"]["proof"] == "field-validated weed maps"
    assert first not in body["draft"]["extra_inclusions"]
    assert len(body["draft"]["extra_inclusions"]) == 3


def test_import_intent_file(root):
    intent = json.loads((UAV / "intent.json").read_text(encoding="utf-8"))
    from_intent = _import(_client(root), _file("intent.json", intent)).json()
    from_protocol = _import(_client(root), {"kind": "workspace", "slug": "uav"}).json()
    assert from_intent["source"]["read"] == "intent" and from_intent["source"]["protocol_fingerprint"] is None
    assert from_intent["draft"]["rqs"] == from_protocol["draft"]["rqs"]
    assert from_intent["draft"]["extra_exclusions"] == from_protocol["draft"]["extra_exclusions"]


@pytest.mark.parametrize(
    ("source", "code", "status"),
    [
        ({"kind": "workspace", "slug": "nope"}, "IMPORT_SOURCE_NOT_FOUND", 404),
        ({"kind": "file", "file_name": "p.json", "content_base64": "%%%"}, "IMPORT_SOURCE_UNREADABLE", 422),
        (_file("p.json", b"\xff\xfe\x00bad"), "IMPORT_SOURCE_UNREADABLE", 422),
        (_file("p.json", b"not json"), "IMPORT_SOURCE_UNREADABLE", 422),
        (_file("p.json", [1, 2]), "IMPORT_SOURCE_UNREADABLE", 422),
        (_file("p.json", b"{" + b" " * (1024 * 1024) + b"}"), "IMPORT_SOURCE_TOO_LARGE", 413),
        (_file("p.json", {"title": "x"}), "IMPORT_NOT_A_PROTOCOL", 422),
        ({"kind": "workspace", "slug": "../x"}, "WORKSPACE_PATH_REFUSED", 422),
    ],
)
def test_each_refusal(root, source, code, status):
    answer = _import(_client(root), source)
    assert answer.status_code == status, answer.text
    assert answer.json()["detail"]["code"] == code


def test_version_unsupported_and_invalid(root):
    proto = _protocol()
    proto["$schema"] = "schemas/v2/protocol.schema.json"
    answer = _import(_client(root), _file("protocol.json", proto))
    assert answer.json()["detail"]["code"] == "IMPORT_PROTOCOL_VERSION_UNSUPPORTED"
    proto = _protocol()
    del proto["research_questions"][0]["text"]
    answer = _import(_client(root), _file("protocol.json", proto))
    assert answer.status_code == 422 and answer.json()["detail"]["code"] == "PROTOCOL_INVALID"
    assert "input" not in json.dumps(answer.json()["detail"]["details"]["errors"])


def test_a_value_over_a_draft_limit_is_refused_not_cut(root):
    proto = _protocol()
    proto["screening_criteria"]["inclusion"][0]["criterion"] = "x" * 2001
    answer = _import(_client(root), _file("protocol.json", proto))
    assert answer.json()["detail"]["code"] == "DRAFT_TOO_LARGE"
    assert answer.json()["detail"]["details"]["limits"] == steps.DRAFT_LIMITS


def test_source_changed_between_report_and_create(root):
    client = _client(root)
    body = _import(client, {"kind": "workspace", "slug": "uav"}).json()
    proto = _protocol()
    proto["metadata"]["title"] = "Another title"
    (root / "uav" / "protocol.json").write_text(json.dumps(proto), encoding="utf-8")
    answer = _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"])
    assert answer.status_code == 409 and answer.json()["detail"]["code"] == "IMPORT_SOURCE_CHANGED"
    assert not (root / ".drafts").exists()


def test_import_lossy_lines(root):
    proto = _protocol()
    proto["search_strategy"]["core_concepts"][0]["boolean_operator"] = "AND"
    proto["screening_criteria"]["inclusion"][0]["maps_to_rqs"] = ["RQ1"]
    proto["screening_criteria"]["exclusion"][0]["reason_category"] = None
    proto["verification"]["minimum_trust_score_threshold"] = 4.5
    proto["search_strategy"]["golden_seeds"] = ["10.1000/ok", "not-a-doi"]
    proto["matrix_dimensions"][1]["id"] = proto["matrix_dimensions"][0]["id"]
    lost = _import(_client(root), _file("protocol.json", proto)).json()["lost"]
    kinds = {e["what"] for e in lost}
    assert {"operator", "maps", "category", "threshold", "seeds", "matrix_id"} <= kinds
    assert [e for e in lost if e["what"] == "seeds"][0]["count"] == 1


def test_import_normalises_a_reason_code_and_lists_it(root):
    proto = _protocol()
    proto["screening_criteria"]["exclusion"][0]["reason_category"] = "wrong platform"
    proto["screening_criteria"]["exclusion"][1]["reason_category"] = "x"
    proto["screening_criteria"]["exclusion"][2]["reason_category"] = "A" * 50
    client = _client(root)
    body = _import(client, _file("protocol.json", proto)).json()
    codes = [e["reason_category"] for e in body["draft"]["extra_exclusions"]]
    assert codes[:3] == ["WRONG_PLATFORM", "OUT_OF_SCOPE", "A" * 40]
    originals = {e["original"] for e in body["lost"] if e["what"] == "reason_code"}
    assert originals == {"wrong platform", "x", "A" * 50}
    created = _import(client, _file("protocol.json", proto), dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"]).json()
    saved = client.put(f"{BASE}/drafts/{created['session_id']}", json={"draft": created["draft"], "base_updated_at": created["updated_at"]})
    assert saved.status_code == 200, saved.text


def test_origin_checked_keeps_updated_at_and_a_save_keeps_origin(root):
    client = _client(root)
    body = _import(client, {"kind": "workspace", "slug": "uav"}).json()
    created = _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"]).json()
    sid, stamp = created["session_id"], created["updated_at"]
    for _ in range(2):  # idempotent
        marked = client.post(f"{BASE}/drafts/{sid}/origin/checked", json={"step": "shape"})
        assert marked.status_code == 200 and marked.json()["origin"]["checked"]["shape"] is True
    assert client.get(f"{BASE}/drafts/{sid}").json()["updated_at"] == stamp
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": {**created["draft"], "topic": "UAV"}, "base_updated_at": stamp})
    assert saved.status_code == 200, saved.text
    assert saved.json()["origin"]["checked"]["shape"] is True
    assert client.post(f"{BASE}/drafts/{sid}/origin/checked", json={"step": "explore"}).json()["detail"]["code"] == "STEP_UNKNOWN"
    listing = client.get(f"{BASE}/drafts").json()["items"]
    assert listing[0]["origin_label"] == "uav"


def test_genesis_names_origin_and_project_records_it(root):
    client = _client(root)
    body = _import(client, {"kind": "workspace", "slug": "uav"}).json()
    created = _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"]).json()
    sid = created["session_id"]
    draft = {**created["draft"], "topic": "UAV crop-weed mapping", "title": "UAV weed mapping, second review"}
    client.put(f"{BASE}/drafts/{sid}", json={"draft": draft, "base_updated_at": created["updated_at"]})
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    ws = Path(made.json()["path"])
    assert json.loads((ws / "project.json").read_text(encoding="utf-8"))["protocol_origin"] == "import"
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    genesis = [r for r in rows if r.get("action") == "GENESIS"]
    assert genesis, rows
    text = json.dumps(genesis[-1])
    assert "Phase-0 Inception: 'UAV weed mapping, second review'" in text
    assert "Started from uav, protocol sha256:" in text


def test_the_two_routes_are_in_the_allowlist():
    assert any(p.fullmatch("api/v1/inception/drafts/import") for p in POST_PATHS)
    assert any(p.fullmatch("api/v1/inception/drafts/rec_0123abcd/origin/checked") for p in POST_PATHS)
