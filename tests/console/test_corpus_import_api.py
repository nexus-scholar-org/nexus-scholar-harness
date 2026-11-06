"""M5b: the corpus import over the screening API (`/screening/corpus`).

The Import screen stages one RIS export per database, previews the counts the
snapshot will have, removes a staged export, and accepts. The engine
(`scholar_harness.corpus_accept`) does the work; these tests hold the route
shapes, the refusal codes and the desktop-only scope.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console.serve import create_app

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
BASE = "/api/v1/screening/corpus"
DESKTOP, PHONE = "desktop-token", "phone-token"

SCOPUS = (
    "TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV weed mapping in maize\nPY  - 2024\nDO  - 10.1000/m5b-1\nER  - \n"
    "TY  - JOUR\nAU  - Chen, L.\nTI  - Drone crop scouting with deep learning\nPY  - 2022\nDO  - 10.1000/m5b-2\nER  - \n"
)
WOS = (
    "TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV Weed Mapping in Maize\nPY  - 2024\nDO  - 10.1000/M5B-1\nER  - \n"
    "TY  - JOUR\nAU  - Okafor, N.\nTI  - Site-specific herbicide prescription maps\nPY  - 2023\nER  - \n"
)


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(
        json.dumps({"project_id": "corpus-api", "registered_workspace_id": "WSP-" + "c" * 32}), encoding="utf-8"
    )
    (ws / "protocol.json").write_text(PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")
    return ws


def _client(ws: Path, token: str = DESKTOP) -> TestClient:
    return TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {token}"},
    )


def _stage(client: TestClient, label: str, content: str, **extra):
    return client.post(f"{BASE}/sources", json={"label": label, "file_name": f"{label}.ris", "content": content, **extra})


def test_stage_preview_remove_and_accept(ws):
    client = _client(ws)
    empty = client.get(BASE).json()
    assert (empty["state"], empty["sources"], empty["accepted"]) == ("EMPTY", [], None)
    assert empty["limits"]["max_source_bytes"] == 50 * 1024 * 1024

    first = _stage(client, "Scopus", SCOPUS, searched_on="2026-11-06", query="uav AND weed")
    assert first.status_code == 201, first.text
    staged = _stage(client, "Web of Science", WOS).json()
    assert staged["state"] == "STAGED"
    assert [(s["label"], s["records"]) for s in staged["sources"]] == [("Scopus", 2), ("Web of Science", 2)]
    assert [s["id"].rsplit("-", 1)[0] for s in staged["sources"]] == ["scopus", "web-of-science"]
    assert [(d["label"], d["records"], d["search_details_missing"]) for d in staged["databases"]] == [
        ("Scopus", 2, False), ("Web of Science", 2, True)
    ]
    assert staged["preview"] == {"identified": 4, "duplicates": 1, "unique_studies": 3}
    assert not (ws / "literature" / "verified.json").exists()

    extra = _stage(client, "IEEE", "TY  - JOUR\nTI  - Extra\nER  - \n").json()["sources"][-1]["id"]
    after = client.post(f"{BASE}/sources/{extra}/remove").json()
    assert [s["label"] for s in after["sources"]] == ["Scopus", "Web of Science"]

    accepted = client.post(f"{BASE}/accept")
    assert accepted.status_code == 200, accepted.text
    body = accepted.json()
    assert body["state"] == "ACCEPTED"
    assert {k: body["accepted"][k] for k in ("records", "studies", "duplicates")} == {"records": 4, "studies": 3, "duplicates": 1}
    assert body["accepted"]["artifact_id"].startswith("ART-corpus-")

    scopus_id = body["sources"][0]["id"]
    for response in (_stage(client, "PubMed", WOS), client.post(f"{BASE}/sources/{scopus_id}/remove"), client.post(f"{BASE}/accept")):
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "CORPUS_ALREADY_ACCEPTED"

    actions = [json.loads(line)["action"] for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert actions.count("CORPUS_SOURCE_STAGED") == 3
    assert actions.count("CORPUS_SOURCE_REMOVED") == 1
    assert "CORPUS_IMPORTED" in actions


@pytest.mark.parametrize(
    ("label", "content", "extra", "status", "code"),
    [
        ("Copy", SCOPUS, {}, 409, "SOURCE_DUPLICATE_FILE"),
        ("Notes", "not a RIS file\n", {}, 422, "SOURCE_NOT_RIS"),
        ("../etc", WOS, {}, 422, "SOURCE_LABEL_INVALID"),
        ("WoS", WOS, {"searched_on": "yesterday"}, 422, "SOURCE_DATE_INVALID"),
    ],
)
def test_staging_refusals_are_typed(ws, label, content, extra, status, code):
    client = _client(ws)
    _stage(client, "Scopus", SCOPUS)
    response = _stage(client, label, content, **extra)
    assert response.status_code == status, response.text
    assert response.json()["detail"]["code"] == code


def test_accept_with_nothing_staged_and_remove_unknown(ws):
    client = _client(ws)
    response = client.post(f"{BASE}/accept")
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "NOTHING_STAGED")
    response = client.post(f"{BASE}/sources/scopus-00000000/remove")
    assert (response.status_code, response.json()["detail"]["code"]) == (404, "SOURCE_NOT_FOUND")


def test_unknown_fields_are_refused(ws):
    response = _client(ws).post(f"{BASE}/sources", json={"label": "S", "file_name": "s.ris", "content": SCOPUS, "path": "/etc/passwd"})
    assert response.status_code == 422


def test_a_phone_token_reaches_no_corpus_route(ws):
    phone = _client(ws, PHONE)
    for response in (phone.get(BASE), _stage(phone, "Scopus", SCOPUS), phone.post(f"{BASE}/accept")):
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"
    assert not (ws / "literature" / "raw").exists()
