"""M5b: the corpus import over the screening API (`/screening/corpus`).

The Import screen stages one RIS export per database, previews the counts the
snapshot will have, removes a staged export, and accepts. The engine
(`scholar_harness.corpus_accept`) does the work; these tests hold the route
shapes, the refusal codes and the desktop-only scope.
"""

from __future__ import annotations

import base64
import hashlib
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


def _stage(client: TestClient, label: str, content: str | bytes, **extra):
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return client.post(
        f"{BASE}/sources",
        json={"label": label, "file_name": f"{label}.ris", "content_base64": base64.b64encode(raw).decode("ascii"), **extra},
    )


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
    response = _client(ws).post(f"{BASE}/sources", json={"label": "S", "file_name": "s.ris", "content_base64": "", "path": "/etc/passwd"})
    assert response.status_code == 422


def test_a_phone_token_reaches_no_corpus_route(ws):
    phone = _client(ws, PHONE)
    for response in (phone.get(BASE), _stage(phone, "Scopus", SCOPUS), phone.post(f"{BASE}/accept")):
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"
    assert not (ws / "literature" / "raw").exists()


def test_the_stored_copy_is_the_uploaded_bytes(ws):
    """Review finding 4: a BOM or a non-UTF-8 export is kept exactly, and its sha256 is of those bytes."""
    raw = b"\xef\xbb\xbfTY  - JOUR\r\nTI  - Caf\xe9 weeds\r\nPY  - 2024\r\nER  - \r\n"
    body = _stage(_client(ws), "Web of Science", raw).json()
    stored = ws / "literature" / "raw" / "ris" / f"{body['sources'][0]['id']}.ris"
    assert stored.read_bytes() == raw
    staged = json.loads((ws / "literature" / "raw" / "ris" / "sources.json").read_text(encoding="utf-8"))["sources"][0]
    assert staged["sha256"] == hashlib.sha256(raw).hexdigest()
    assert body["sources"][0]["records"] == 1


def test_content_that_is_not_base64_is_refused(ws):
    response = _client(ws).post(f"{BASE}/sources", json={"label": "S", "file_name": "s.ris", "content_base64": "not base64!"})
    assert (response.status_code, response.json()["detail"]["code"]) == (422, "SOURCE_NOT_RIS")


# M7-method review finding 1: an invalid method block refuses every corpus
# write with 409 PROTOCOL_METHOD_INVALID before anything is written.
def _break_method(ws: Path) -> None:
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["method"] = {
        "dedup": {"doi": True, "title_similarity": 0.5, "first_author": True, "year_tolerance": 1},
        "rules_version": "screening-rules-v1",
        "not_reported": "unclear",
        "blinding": "reveal_after_decision",
    }
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")


def test_an_invalid_method_block_refuses_staging_before_anything_is_written(ws):
    _break_method(ws)
    client = _client(ws)
    response = _stage(client, "Lens", SCOPUS)
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "PROTOCOL_METHOD_INVALID"
    assert not (ws / "literature" / "raw").exists()  # nothing staged
    assert (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8") == ""  # nothing journaled


def test_an_invalid_method_block_refuses_removal_and_acceptance(ws):
    client = _client(ws)
    staged = _stage(client, "Scopus", SCOPUS)
    assert staged.status_code == 201, staged.text
    source_id = staged.json()["sources"][0]["id"]
    _break_method(ws)
    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    for response in (client.post(f"{BASE}/sources/{source_id}/remove"), client.post(f"{BASE}/accept")):
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "PROTOCOL_METHOD_INVALID"
    assert (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8") == journal  # nothing changed
    assert (ws / "literature" / "raw" / "ris" / f"{source_id}.ris").is_file()  # the staged file stays


# M5c-nbib: a PubMed MEDLINE export is staged beside the RIS exports.
NBIB_FIXTURE = ROOT / "tests" / "fixtures" / "pubmed" / "pubmed_uav_weeds.nbib"


def test_a_pubmed_nbib_upload_is_staged_as_nbib(ws):
    client = _client(ws)
    raw = NBIB_FIXTURE.read_bytes()
    response = client.post(
        f"{BASE}/sources",
        json={"label": "PubMed", "file_name": "pubmed-set.nbib", "content_base64": base64.b64encode(raw).decode("ascii")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    source = body["sources"][0]
    assert (source["label"], source["file_name"], source["format"], source["records"]) == ("PubMed", "pubmed-set.nbib", "nbib", 5)
    assert body["preview"] == {"identified": 5, "duplicates": 0, "unique_studies": 5}
    stored = ws / "literature" / "raw" / "ris" / f"{source['id']}.nbib"
    assert stored.read_bytes() == raw
    staged = json.loads((ws / "literature" / "raw" / "ris" / "sources.json").read_text(encoding="utf-8"))["sources"][0]
    assert (staged["format"], staged["sha256"]) == ("nbib", hashlib.sha256(raw).hexdigest())

    # The RIS twin of the first PubMed record is one study across the two databases.
    twin = _stage(client, "IEEE Xplore", "TY  - CONF\nAU  - Rossi, M.\nTI  - Deep learning-based weed detection\nPY  - 2024\nDO  - 10.1000/M5C-1\nER  - \n")
    assert twin.status_code == 201, twin.text
    assert twin.json()["preview"] == {"identified": 6, "duplicates": 1, "unique_studies": 5}
    assert [(d["label"], d["records"]) for d in twin.json()["databases"]] == [("PubMed", 5), ("IEEE Xplore", 1)]


FIXTURES = ROOT / "tests" / "kits" / "search" / "fixtures" / "imports"


@pytest.mark.parametrize(("name", "kept"), [("rejections.ris", 4), ("rejections.nbib", 4)])
def test_a_staged_export_lists_its_rejected_lines_and_the_limits_applied(ws, name, kept):
    """E3 (M3d-engine, packet §4.4): the rejected lines and the limits travel with the staged row."""
    client = _client(ws)
    raw = (FIXTURES / name).read_bytes()
    limits = "Article, Review; English; 2018-2025; subject area: Agricultural and Biological Sciences"
    response = client.post(f"{BASE}/sources", json={
        "label": "Scopus", "file_name": name, "content_base64": base64.b64encode(raw).decode("ascii"),
        "searched_on": "2026-11-10", "query": "uav AND weed", "limits": limits,
    })
    assert response.status_code == 201, response.text
    (source,) = response.json()["sources"]
    assert source["records"] == kept
    assert source["limits"] == limits
    assert sorted(r["code"] for r in source["rejected"]) == ["IMPORT_BAD_TAG", "IMPORT_BAD_YEAR", "IMPORT_NO_TITLE"]
    assert all(set(r) == {"line", "code", "reason"} for r in source["rejected"])
    assert client.get(BASE).json()["sources"][0]["rejected"] == source["rejected"]
    staged = json.loads((ws / "literature" / "raw" / "ris" / "sources.json").read_text(encoding="utf-8"))
    assert staged["sources"][0]["limits"] == limits and len(staged["sources"][0]["rejected"]) == 3
    event = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()][-1]
    assert event["action"] == "CORPUS_SOURCE_STAGED"
    assert event["parameters"]["limits"] == limits and event["metrics"]["rejected"] == 3


def test_a_clean_export_has_no_rejections_and_no_limits(ws):
    client = _client(ws)
    (source,) = _stage(client, "Scopus", SCOPUS).json()["sources"]
    assert source["rejected"] == [] and source["limits"] is None
