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
    # H-run-small-fixes (finding 1): beside other inclusions the proof writes no criterion,
    # so the protocol's criterion stays as a typed inclusion: every inclusion is kept.
    assert body["draft"]["extra_inclusions"][0] == first
    assert len(body["draft"]["extra_inclusions"]) == 4


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


def test_a_replacement_from_an_imported_draft_puts_a_full_stop_before_started_from(root):
    """Part A review round 2, P3 (deferred to Part B): the replacement's GENESIS row read
    "... (backup at audit/replaced/...) Started from ..." with no full stop between."""
    client = _client(root)
    body = _import(client, {"kind": "workspace", "slug": "uav"}).json()
    fingerprint = body["source"]["protocol_fingerprint"]
    paths = []
    for _ in range(2):
        created = _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=fingerprint).json()
        sid = created["session_id"]
        draft = {**created["draft"], "topic": "UAV crop-weed mapping", "title": "UAV weed mapping, second review"}
        client.put(f"{BASE}/drafts/{sid}", json={"draft": draft, "base_updated_at": created["updated_at"]})
        made = client.post(f"{BASE}/drafts/{sid}/genesis", json={"replace": bool(paths)})
        assert made.status_code == 201, made.text
        paths.append(Path(made.json()["path"]))
    rows = [json.loads(line) for line in (paths[1] / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    description = [r for r in rows if r.get("action") == "GENESIS"][-1]["description"]
    assert "REPLACED protocol fingerprint" in description
    assert "). Started from uav, protocol sha256:" in description


def test_the_two_routes_are_in_the_allowlist():
    assert any(p.fullmatch("api/v1/inception/drafts/import") for p in POST_PATHS)
    assert any(p.fullmatch("api/v1/inception/drafts/rec_0123abcd/origin/checked") for p in POST_PATHS)


def test_a_column_named_like_a_suggestion_is_ticked_and_a_changed_wording_is_listed(root):
    """Review of Part A, finding 1: such a column was ticked silently, or (other case) refused later."""
    proto = _protocol()
    proto["playbook_type"] = "PRISMA_SLR"
    unit = proto["epistemology"]["unit_of_analysis"]
    old = {
        "id": "sample_size", "name": "Sample Size", "description": f"Number of {unit} sampled / evaluated",
        "target_section_category": "methodology", "data_type": "numeric", "required": True, "fallback_value": "Not Reported",
    }
    other_case = {**old, "id": "n", "name": "sample size"}
    for dim in (old, other_case):
        proto["matrix_dimensions"] = [dim]
        client = _client(root)
        body = _import(client, _file("protocol.json", proto)).json()
        assert body["draft"]["matrix_columns"] == ["Sample Size"]
        assert "custom_matrix_columns" not in body["draft"]
        assert {"what": "matrix_default", "name": "Sample Size"} in body["lost"]
        draft = {**body["draft"], "topic": "UAV"}
        assert client.post(f"{BASE}/steps/matrix", json={"draft": draft}).status_code == 200
        assert client.post(f"{BASE}/preview", json={"draft": draft}).status_code == 200


def test_the_draft_lock_keeps_a_save_that_arrives_during_a_side_write(root):
    """09 tests: a PUT landing between the mark's read and write is kept (the per-draft lock)."""
    import threading

    from scholar_harness.inception.drafts import DraftStore

    store = DraftStore(root)
    record = store.create({"topic": "first"}, extra={"origin": {"kind": "import", "checked": {"shape": False}}})
    sid = record["session_id"]
    started, go = threading.Event(), threading.Event()
    saved: dict = {}

    def mark(origin):
        started.set()
        go.wait(5)
        return {**origin, "checked": {"shape": True}}

    marker = threading.Thread(target=lambda: store.update_side(sid, "origin", mark))
    marker.start()
    assert started.wait(5)
    saver = threading.Thread(target=lambda: saved.update(store.save(sid, {"topic": "second"}, base_updated_at=record["updated_at"])))
    saver.start()
    saver.join(0.3)
    assert saver.is_alive()  # the save waits for the side write
    go.set()
    marker.join(5)
    saver.join(5)
    final = store.load(sid)
    assert final["draft"] == {"topic": "second"}
    assert final["origin"]["checked"]["shape"] is True


def test_protocol_origin_is_inception_for_a_plain_draft_and_on_a_replacement(root):
    client = _client(root)
    body = _import(client, {"kind": "workspace", "slug": "uav"}).json()
    created = _import(client, {"kind": "workspace", "slug": "uav"}, dry_run=False, expect_fingerprint=body["source"]["protocol_fingerprint"]).json()
    draft = {**created["draft"], "topic": "UAV crop-weed mapping", "title": "UAV weed mapping, third review"}
    client.put(f"{BASE}/drafts/{created['session_id']}", json={"draft": draft, "base_updated_at": created["updated_at"]})
    made = client.post(f"{BASE}/drafts/{created['session_id']}/genesis", json={}).json()
    ws = Path(made["path"])
    assert json.loads((ws / "project.json").read_text(encoding="utf-8"))["protocol_origin"] == "import"

    plain = client.post(f"{BASE}/drafts", json={"draft": draft}).json()
    replaced = client.post(f"{BASE}/drafts/{plain['session_id']}/genesis", json={"replace": True})
    assert replaced.status_code == 201, replaced.text
    assert json.loads((ws / "project.json").read_text(encoding="utf-8"))["protocol_origin"] == "inception"
    rows = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert rows.count("Started from uav") == 1  # only the imported genesis names a source


def test_an_oversized_file_is_the_engines_413_not_a_body_refusal(root):
    answer = _import(_client(root), _file("p.json", b"{" + b" " * (2 * 1024 * 1024) + b"}"))
    assert answer.status_code == 413 and answer.json()["detail"]["code"] == "IMPORT_SOURCE_TOO_LARGE"
