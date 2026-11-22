"""M12a Part F: open-access copies fetched into the charting table (DoD F1 to F7, engine side).

The workspace is Part A's published screening (two kept records), with its
kept set widened by a test seam to three records: one with a DOI, one with
only an arXiv id, one with neither. Nothing leaves the machine:

- the PDF hosts are a stub server on 127.0.0.1 (run in its own thread, since
  the run's worker calls ``asyncio.run`` from the request);
- Unpaywall and OpenAlex are a fake lookup client keyed by host and DOI;
- arXiv's API is a fake client answering a hand-made Atom feed (in the API's
  documented shape; never recorded) whose ``pdf`` link points at the stub;
- the suite's socket guard fails any connection off the loopback address.
"""

from __future__ import annotations

import asyncio
import dataclasses
import importlib.util
import io
import json
import sys
import threading
import uuid
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from scholar_harness.charting import fetch as fx
from scholar_harness.charting import table as tb
from scholar_harness.console import create_app

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_export_api_helpers_fetch", _HERE / "test_export_api.py")
tea = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tea)
_STUB = importlib.util.spec_from_file_location(
    "_pdf_stub_server_fetch", _HERE.parent / "kits" / "pdf" / "stub_server.py"
)
stub = importlib.util.module_from_spec(_STUB)
sys.modules[_STUB.name] = stub  # its dataclasses look their module up
_STUB.loader.exec_module(stub)

TOKEN = "desk-token"
BASE = "/api/v1/charting"
WHO = "researcher:local"
CONTACT = "fetch-tests@example.org"
SECRET_KEY = "fetch-test-openalex-key-NEVER-WRITTEN"
DOI = "10.1234/doi-record"
ARXIV_DOI = "10.1234/journal.2021.001"
NEITHER = "STU-neither0000000000000000000000"


def pdf_bytes(mark: str = "x") -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.add_metadata({"/Description": mark * 11000})
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


PDF_A, PDF_B = pdf_bytes("a"), pdf_bytes("b")


# --------------------------------------------------------------------------- stubs


class ThreadedStub:
    """``StubPdfHost`` served from its own thread and event loop."""

    def __init__(self, routes):
        self.host = stub.StubPdfHost(routes)
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self.host.__aenter__(), self.loop).result(10)
        return self.host

    def __exit__(self, *exc):
        asyncio.run_coroutine_threadsafe(self.host.__aexit__(None, None, None), self.loop).result(10)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)


class FakeLookups:
    """Unpaywall and OpenAlex, by host and DOI; any other host is a KeyError."""

    def __init__(self, answers: dict[tuple[str, str], dict], on_call=None):
        self.answers, self.on_call = answers, on_call
        self.calls: list[tuple[str, dict]] = []

    async def get(self, url, params=None, headers=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        if self.on_call is not None:
            self.on_call(url)
        parts = urlsplit(url)
        doi = parts.path.split("/v2/", 1)[-1] if parts.hostname == "api.unpaywall.org" else parts.path.split("doi.org/", 1)[-1]
        answer = self.answers.get((parts.hostname, doi))
        response = MagicMock()
        if answer is None:
            response.status_code = 404
            return response
        response.status_code = 200
        response.json.return_value = answer
        return response

    async def close(self):
        return None


def unpaywall(url: str, version: str = "publishedVersion", licence: str | None = "cc-by") -> dict:
    return {"is_oa": True, "journal_name": "Invented Journal",
            "best_oa_location": {"url_for_pdf": url, "version": version, "host_type": "publisher", "license": licence},
            "oa_locations": []}


CLOSED_OPENALEX = {"open_access": {"is_oa": False}}


def arxiv_feed(pdf_url: str, *, doi: str | None = None) -> bytes:
    """A hand-made answer of ``export.arxiv.org/api/query?id_list=2101.01234`` (not recorded)."""
    doi_xml = f"<arxiv:doi>{doi}</arxiv:doi>" if doi else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
        "<entry><id>http://arxiv.org/abs/2101.01234v3</id><title>An arXiv-only record</title>"
        f"{doi_xml}<link title=\"pdf\" href=\"{pdf_url}\" rel=\"related\" type=\"application/pdf\"/></entry>"
        "</feed>"
    ).encode("utf-8")


class FakeArxiv:
    def __init__(self, content: bytes):
        self.content, self.calls = content, []

    async def get(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        response = MagicMock()
        response.content = self.content
        response.text = self.content.decode("utf-8")
        return response

    async def close(self):
        return None


# --------------------------------------------------------------------------- the workspace


@pytest.fixture
def world(tmp_path, monkeypatch):
    from scholar_pdf import config as pdf_config
    from scholar_search import config as search_config

    monkeypatch.setattr(search_config.settings, "mailto", CONTACT)
    monkeypatch.setattr(search_config.settings, "openalex_key", SECRET_KEY)
    monkeypatch.setattr(pdf_config.settings, "mailto", "")
    ws, ids = tea.published_workspace(tmp_path)
    doi_id, arxiv_sid = ids["included"], ids["unclear"]
    real = tb.read_kept

    def widened(path, *, remember=True):
        state = real(path, remember=remember)
        records = []
        for record in state.records:
            if record.study_id == doi_id:
                records.append(dataclasses.replace(record, doi=DOI, arxiv_id=None, title="The DOI record"))
            elif record.study_id == arxiv_sid:
                records.append(dataclasses.replace(record, doi=None, arxiv_id="2101.01234", title="An arXiv-only record"))
            else:
                records.append(record)
        if records:
            records.append(dataclasses.replace(records[0], study_id=NEITHER, doi=None, arxiv_id=None, title="No id"))
        state.records = records
        return state

    monkeypatch.setattr(tb, "read_kept", widened)
    app = create_app(ws, token=TOKEN)
    app.state.fetch_executor = lambda fn: fn()  # the run in the request, so a test reads its end
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield {"client": client, "ws": ws, "app": app, "doi": doi_id, "arxiv": arxiv_sid}


def deps(lookups, arxiv, *, downloader=None) -> fx.Deps:
    return fx.Deps(lookup_client=lambda: lookups, arxiv_client=lambda: arxiv,
                   pacer=lambda on_wait: fx.HostPacer(on_wait, pause=0.0), downloader=downloader)


def manifest(ws: Path) -> list[dict]:
    return fx.read_manifest(ws)


def journal(ws: Path, action: str) -> list[dict]:
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("action") == action]


def row_of(client, study: str) -> dict:
    return next(r for r in client.get(BASE).json()["rows"] if r["study_id"] == study)


def event(study: str, kind: str, value, **extra) -> dict:
    return {"event_id": str(uuid.uuid4()), "study_id": study, "screener_id": WHO,
            "at": "2026-11-22T10:00:00Z", "kind": kind, "value": value, **extra}


def standard_run(world, host, *, arxiv_doi=None, ids=None):
    lookups = FakeLookups({
        ("api.unpaywall.org", DOI): unpaywall(host.url("/doi.pdf")),
        ("api.openalex.org", DOI): CLOSED_OPENALEX,
        ("api.unpaywall.org", ARXIV_DOI): unpaywall(host.url("/journal.pdf")),
        ("api.openalex.org", ARXIV_DOI): CLOSED_OPENALEX,
    })
    arxiv = FakeArxiv(arxiv_feed(host.url("/pdf/2101.01234v3"), doi=arxiv_doi))
    world["app"].state.fetch_deps = deps(lookups, arxiv)
    body = {"confirm": True} if ids is None else {"confirm": True, "ids": ids}
    response = world["client"].post(f"{BASE}/fetch", json=body)
    return response, lookups, arxiv


ROUTES = {"/doi.pdf": [stub.Answer(body=PDF_A)], "/pdf/2101.01234v3": [stub.Answer(body=PDF_B)],
          "/journal.pdf": [stub.Answer(body=PDF_B)]}


# --------------------------------------------------------------------------- DoD F1: the e-mail, the OpenAlex key


def test_without_the_contact_email_the_plan_and_the_start_are_refused_before_any_request(world, monkeypatch):
    from scholar_search import config as search_config

    monkeypatch.setattr(search_config.settings, "mailto", None)
    built = []
    world["app"].state.fetch_deps = fx.Deps(lookup_client=lambda: built.append("lookups"),
                                            arxiv_client=lambda: built.append("arxiv"),
                                            session=lambda: built.append("session"))
    client = world["client"]
    for response in (client.get(f"{BASE}/fetch/plan"), client.post(f"{BASE}/fetch", json={"dry": True}),
                     client.post(f"{BASE}/fetch", json={"confirm": True})):
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "MAILTO_NOT_SET"
        assert "total" not in response.json()["detail"]  # no counts with the refusal
    assert built == []  # no client, no session, so no socket
    assert not journal(world["ws"], fx.STARTED)


def test_the_plan_sends_nothing_and_counts_by_doi_by_arxiv_id_and_neither(world):
    built = []
    world["app"].state.fetch_deps = fx.Deps(lookup_client=lambda: built.append(1))
    plan = world["client"].get(f"{BASE}/fetch/plan").json()
    assert (plan["total"], plan["asked"], plan["with_doi"], plan["with_arxiv_only"], plan["neither"]) == (3, 3, 1, 1, 1)
    assert plan["email"] == CONTACT and plan["openalex_key_set"] is True
    assert plan["services"] == {"unpaywall": "asked", "openalex": "asked", "arxiv": "asked"}
    assert SECRET_KEY not in json.dumps(plan)
    dry = world["client"].post(f"{BASE}/fetch", json={"dry": True}).json()
    assert dry == plan
    assert built == [] and not journal(world["ws"], fx.STARTED)


def test_without_the_openalex_key_openalex_is_not_asked_and_the_plan_says_so(world, monkeypatch):
    from scholar_search import config as search_config

    monkeypatch.setattr(search_config.settings, "openalex_key", None)
    plan = world["client"].get(f"{BASE}/fetch/plan").json()
    assert plan["services"]["openalex"] == "not_asked" and plan["openalex_key_set"] is False
    assert any("SCHOLAR_OPENALEX_KEY" in note for note in plan["notes"])
    with ThreadedStub(ROUTES) as host:
        response, lookups, _ = standard_run(world, host)
    assert response.status_code == 202
    assert all(urlsplit(url).hostname != "api.openalex.org" for url, _ in lookups.calls)
    [started] = journal(world["ws"], fx.STARTED)
    assert started["parameters"]["openalex_key_set"] is False
    assert started["parameters"]["providers"] == ["unpaywall", "arxiv"]


# --------------------------------------------------------------------------- DoD F2: a row for every record reached


def test_every_record_reached_has_a_manifest_row_and_no_file_is_without_one(world):
    with ThreadedStub(ROUTES) as host:
        response, lookups, arxiv = standard_run(world, host)
    assert response.status_code == 202, response.text
    ws = world["ws"]
    rows = manifest(ws)
    by_study = {r["study_id"]: r for r in rows}
    assert set(by_study) == {world["doi"], world["arxiv"], NEITHER}
    run_id = response.json()["run_id"]
    assert all(r["run_id"] == run_id and r["row_id"].startswith("FMR-") for r in rows)
    assert by_study[NEITHER]["outcome"] == fx.SKIPPED_NO_ID and by_study[NEITHER]["file"] is None
    assert by_study[world["doi"]]["outcome"] == "ACQUIRED" and by_study[world["arxiv"]]["outcome"] == "ACQUIRED"
    named = {fx.stored_file(ws, r) for r in rows if r.get("file")}
    on_disk = set((ws / fx.FETCHED_DIR).glob("*.pdf"))
    assert on_disk and {p.resolve() for p in on_disk} == {p for p in named if p}
    # Nothing written where the legacy pipeline looks.
    assert not (ws / "literature" / "pdf_manifest.json").exists()
    assert not list((ws / "pdfs").glob("*.pdf"))  # nothing at pdfs/<study_id>.pdf before a confirm


def test_a_failed_record_has_its_row_too(world):
    with ThreadedStub({"/pdf/2101.01234v3": [stub.Answer(body=PDF_B)]}) as host:  # /doi.pdf answers 404
        standard_run(world, host)
        assert host.hits["/doi.pdf"] == 1  # a 404 is asked once
    row = next(r for r in manifest(world["ws"]) if r["study_id"] == world["doi"])
    assert row["outcome"] == "PDF_NOT_FETCHED" and row["file"] is None
    assert row["requests"][0]["http_status"] == 404


def test_a_cancel_stops_between_records_and_the_records_reached_keep_their_rows(world):
    ws = world["ws"]
    with ThreadedStub(ROUTES) as host:
        lookups = FakeLookups({("api.unpaywall.org", DOI): unpaywall(host.url("/doi.pdf")),
                               ("api.openalex.org", DOI): CLOSED_OPENALEX},
                              on_call=lambda url: fx.cancel(ws))  # the researcher cancels during the first record
        world["app"].state.fetch_deps = deps(lookups, FakeArxiv(arxiv_feed(host.url("/pdf/2101.01234v3"))))
        # The DOI record first, so the cancel comes while it is in hand.
        response = world["client"].post(f"{BASE}/fetch", json={"confirm": True,
                                                                "ids": [world["doi"], NEITHER, world["arxiv"]]})
    assert response.status_code == 202, response.text
    rows = manifest(ws)
    assert [r["study_id"] for r in rows] == [world["doi"]]  # the record in hand finished; the others not reached
    state = world["client"].get(f"{BASE}/fetch").json()
    assert state["state"] == "cancelled" and state["reached"] == 1 and state["not_reached"] == 2
    [finished] = journal(ws, fx.FINISHED)
    assert finished["parameters"]["cancelled"] is True and finished["metrics"]["not_reached"] == 2


# --------------------------------------------------------------------------- DoD F3: the checks, at the app's level


def test_a_body_over_the_limit_is_cut_and_fails(world, monkeypatch):
    monkeypatch.setattr(fx, "MAX_BYTES", 4096)
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host, ids=[world["doi"]])
    [row] = manifest(world["ws"])
    assert row["file"] is None and row["outcome"] == "PDF_NOT_FETCHED"
    assert "over the limit of 4096 bytes" in row["message"]
    assert world["client"].get(f"{BASE}/fetch").json()["failed_checks"] == 1


def test_redirects_are_recorded_and_a_sixth_is_refused(world):
    routes = {f"/r{n}": [stub.Answer(redirect_to=f"/r{n + 1}")] for n in range(6)}
    routes["/r6"] = [stub.Answer(body=PDF_A)]
    with ThreadedStub(routes) as host:
        lookups = FakeLookups({("api.unpaywall.org", DOI): unpaywall(host.url("/r0")),
                               ("api.openalex.org", DOI): CLOSED_OPENALEX})
        world["app"].state.fetch_deps = deps(lookups, FakeArxiv(b""))
        world["client"].post(f"{BASE}/fetch", json={"confirm": True, "ids": [world["doi"]]})
        assert host.hits["/r6"] == 0
    [row] = manifest(world["ws"])
    assert row["file"] is None and row["requests"][0]["error"] == "too many redirects"
    assert len(row["requests"][0]["redirects"]) == 6


def test_html_named_pdf_fails_its_checks(world):
    routes = {"/doi.pdf": [stub.Answer(body=b"%PDF-1.4\n<html>Sign in</html>" * 600, content_type="application/pdf")]}
    with ThreadedStub(routes) as host:
        standard_run(world, host, ids=[world["doi"]])
    [row] = manifest(world["ws"])
    assert row["file"] is None and row["outcome"] == "PDF_NOT_FETCHED"
    assert row["requests"][0]["http_status"] == 200 and row["requests"][0]["error"]  # it answered; the checks said no
    assert world["client"].get(f"{BASE}/fetch").json()["failed_checks"] == 1
    assert not list((world["ws"] / "pdfs" / "fetched").glob("*.pdf"))


def test_a_429_that_asks_too_long_ends_as_try_later(world):
    routes = {"/doi.pdf": [stub.Answer(status=429, body=b"later", content_type="text/plain",
                                       headers={"Retry-After": "3600"})]}
    with ThreadedStub(routes) as host:
        standard_run(world, host, ids=[world["doi"]])
        assert host.hits["/doi.pdf"] == 1
    state = world["client"].get(f"{BASE}/fetch").json()
    assert state["try_later"] == 1
    assert row_of(world["client"], world["doi"])["fulltext"]["last_lookup"]["try_later"] is True


def test_the_same_bytes_for_two_records_are_warned_on_both_rows(world):
    routes = {"/doi.pdf": [stub.Answer(body=PDF_A)], "/pdf/2101.01234v3": [stub.Answer(body=PDF_A)]}
    with ThreadedStub(routes) as host:
        standard_run(world, host)
    doi_row, arxiv_row = row_of(world["client"], world["doi"]), row_of(world["client"], world["arxiv"])
    assert doi_row["fulltext"]["pending_fetch"]["duplicate_of"] == [world["arxiv"]]
    assert arxiv_row["fulltext"]["pending_fetch"]["duplicate_of"] == [world["doi"]]


# --------------------------------------------------------------------------- DoD F4: the kit as a library; no proxy, no guessed URL


def test_the_run_calls_the_kits_downloader_with_no_proxy_and_asks_only_listed_addresses(world, monkeypatch):
    import subprocess

    from scholar_pdf import config as pdf_config
    from scholar_pdf.downloader import AsyncPDFDownloader

    monkeypatch.setattr(pdf_config.settings, "proxy_url", "http://proxy.invalid:3128")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("no command is run"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("no command is run"))
    made = []

    def downloader(**kwargs):
        made.append(AsyncPDFDownloader(**kwargs))
        return made[-1]

    with ThreadedStub(ROUTES) as host:
        lookups = FakeLookups({("api.unpaywall.org", DOI): unpaywall(host.url("/doi.pdf")),
                               ("api.openalex.org", DOI): CLOSED_OPENALEX})
        arxiv = FakeArxiv(arxiv_feed(host.url("/pdf/2101.01234v3")))
        world["app"].state.fetch_deps = deps(lookups, arxiv, downloader=downloader)
        response = world["client"].post(f"{BASE}/fetch", json={"confirm": True})
        asked = set(host.hits)
    assert response.status_code == 202
    [kit] = made
    assert type(kit) is AsyncPDFDownloader
    assert kit.institutional_gateway_url == "" and kit.forward_proxy_url == ""
    assert (kit.max_bytes, kit.max_redirects) == (100 * 1024 * 1024, 5)
    assert kit.manifest_path == world["ws"] / "charting" / "fetch_manifest.jsonl"
    assert kit.output_dir == world["ws"] / "pdfs" / "fetched"
    # Every PDF address asked was one a provider listed (no guessed URL); the files came through.
    assert asked == {"/doi.pdf", "/pdf/2101.01234v3"}
    assert all(r["route"] in (None, "open_location") for r in manifest(world["ws"]))
    assert {r["outcome"] for r in manifest(world["ws"])} == {"ACQUIRED", fx.SKIPPED_NO_ID}


def test_the_default_session_trusts_no_proxy_from_the_environment():
    async def go():
        session = fx._default_session()
        try:
            return session.trust_env
        finally:
            await session.close()

    assert asyncio.run(go()) is False


# --------------------------------------------------------------------------- DoD F5: to confirm, confirm, discard, undo


def test_a_fetched_file_waits_and_the_prisma_counts_do_not_move(world):
    before = world["client"].get(BASE).json()["counts"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
    after = world["client"].get(BASE).json()["counts"]
    assert after["prisma"] == before["prisma"] and after["retrieved"] == before["retrieved"] == 0
    assert after["to_confirm"] == 2 and after["to_get"] == before["to_get"] - 2
    assert after["kept"] == after["to_get"] + after["requested"] + after["retrieved"] + after["not_retrieved"] + after["to_confirm"]
    row = row_of(world["client"], world["doi"])
    assert row["fulltext"]["status"] == "to_get" and row["no_full_text"] is True
    pending = row["fulltext"]["pending_fetch"]
    assert (pending["source"], pending["version"], pending["licence"]) == ("Unpaywall", "publishedVersion", "cc-by")
    assert pending["manifest_row"].startswith("FMR-") and pending["identity"]
    arxiv = row_of(world["client"], world["arxiv"])["fulltext"]["pending_fetch"]
    assert (arxiv["source"], arxiv["version_label"], arxiv["licence"]) == (
        "arXiv", "preprint (arXiv v3)", "arXiv; licence not given")


def _waiting(world, study):
    return row_of(world["client"], study)["fulltext"]["pending_fetch"]


def test_confirm_attaches_the_file_with_origin_fetched_and_sets_retrieved_and_undo_takes_it_back(world):
    ws, client, study = world["ws"], world["client"], world["doi"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
    waiting = _waiting(world, study)
    confirm = event(study, "fetched_confirm", {"manifest_row": waiting["manifest_row"]})
    answer = client.post(f"{BASE}/events", json={"events": [confirm]}).json()
    assert [r["result"] for r in answer["results"]] == ["accepted"] * 3
    assert sum(1 for r in answer["results"] if r.get("added_by_engine")) == 2
    row = row_of(client, study)
    attachment = row["fulltext"]["attachment"]
    assert attachment["origin"] == "fetched" and attachment["manifest_row"] == waiting["manifest_row"]
    assert attachment["sha256"] == waiting["sha256"] and attachment["path"] == f"pdfs/{study}.pdf"
    assert row["fulltext"]["status"] == "retrieved" and row["fulltext"]["pending_fetch"] is None
    assert (ws / "pdfs" / f"{study}.pdf").read_bytes() == PDF_A
    counts = client.get(BASE).json()["counts"]
    assert counts["prisma"]["retrieved"] == 1 and counts["to_confirm"] == 1
    assert any("Confirmed the fetched PDF" in j["description"] for j in journal(ws, "CHARTING_EVENTS_RECEIVED"))

    undo = event(study, "fetched_confirm", None, supersedes=confirm["event_id"])
    client.post(f"{BASE}/events", json={"events": [undo]})
    row = row_of(client, study)
    assert row["fulltext"]["status"] == "to_get" and row["fulltext"]["attachment"] is None
    assert row["fulltext"]["pending_fetch"]["manifest_row"] == waiting["manifest_row"]
    assert not (ws / "pdfs" / f"{study}.pdf").exists()
    assert list((ws / "pdfs" / "replaced").glob(f"{study}.*.pdf"))  # nothing deleted


def test_discard_needs_one_reason_keeps_the_file_and_can_be_undone(world):
    client, study = world["client"], world["doi"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
    waiting = _waiting(world, study)
    for value in ({"manifest_row": waiting["manifest_row"]},
                  {"manifest_row": waiting["manifest_row"], "reason": "other"}):
        result = client.post(f"{BASE}/events", json={"events": [event(study, "fetched_discard", value)]}).json()["results"][0]
        assert result["refusal"]["code"] == "DISCARD_REASON_REQUIRED"
    discard = event(study, "fetched_discard", {"manifest_row": waiting["manifest_row"], "reason": "wrong_paper"})
    assert client.post(f"{BASE}/events", json={"events": [discard]}).json()["results"][0]["result"] == "accepted"
    row = row_of(client, study)
    assert row["fulltext"]["pending_fetch"] is None and row["fulltext"]["status"] == "to_get"
    assert row["fulltext"]["discarded_fetch"]["reason"] == "wrong_paper"
    assert fx.stored_file(world["ws"], next(r for r in manifest(world["ws"]) if r["row_id"] == waiting["manifest_row"])).is_file()
    client.post(f"{BASE}/events", json={"events": [event(study, "fetched_discard", None, supersedes=discard["event_id"])]})
    assert _waiting(world, study)["manifest_row"] == waiting["manifest_row"]


def test_confirm_or_discard_with_nothing_waiting_is_fetch_not_pending(world):
    client, study = world["client"], world["doi"]
    for kind, value in (("fetched_confirm", {"manifest_row": "FMR-none"}),
                        ("fetched_discard", {"manifest_row": "FMR-none", "reason": "unreadable"})):
        result = client.post(f"{BASE}/events", json={"events": [event(study, kind, value)]}).json()["results"][0]
        assert result["refusal"]["code"] == "FETCH_NOT_PENDING"
    response = client.get(f"{BASE}/records/{study}/fetched")
    assert response.status_code == 409 and response.json()["detail"]["code"] == "FETCH_NOT_PENDING"


def test_a_decision_status_or_attachment_on_a_waiting_row_asks_for_the_confirmation_first(world):
    client, study = world["client"], world["doi"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
    include = event(study, "fulltext_decision", {"outcome": "INCLUDE"})
    status = event(study, "fulltext_status", {"status": "requested"})
    results = [client.post(f"{BASE}/events", json={"events": [e]}).json()["results"][0] for e in (include, status)]
    assert [r["refusal"]["code"] for r in results] == ["FETCH_FILE_WAITING"] * 2
    upload = client.post(f"{BASE}/records/{study}/attachment", content=PDF_B,
                         headers={"Content-Type": "application/pdf"})
    assert upload.status_code == 409 and upload.json()["detail"]["code"] == "FETCH_FILE_WAITING"
    # Confirm and decide in one request: the two take one step.
    confirm = event(study, "fetched_confirm", {"manifest_row": _waiting(world, study)["manifest_row"]})
    include = event(study, "fulltext_decision", {"outcome": "INCLUDE"})
    results = client.post(f"{BASE}/events", json={"events": [confirm, include]}).json()["results"]
    assert all(r["result"] == "accepted" for r in results)
    assert row_of(client, study)["ft_decision"]["outcome"] == "INCLUDE"


def test_the_waiting_file_is_served_inline_and_what_was_tried_is_readable(world):
    client, study = world["client"], world["doi"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
    response = client.get(f"{BASE}/records/{study}/fetched")
    assert response.status_code == 200 and response.content == PDF_A
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-disposition"].startswith("inline")
    tried = client.get(f"{BASE}/records/{study}/fetch").json()
    assert [r["outcome"] for r in tried["rows"]] == ["ACQUIRED"]
    assert {"lookups", "requests", "checks", "version", "license"} <= set(tried["rows"][0])


# --------------------------------------------------------------------------- DoD F6: one run, a second run, the journal


def test_one_run_per_workspace(world):
    held = []
    world["app"].state.fetch_executor = held.append  # the worker does not start yet
    with ThreadedStub(ROUTES) as host:
        first, _, _ = standard_run(world, host)
        assert first.status_code == 202 and first.json()["state"] == "running"
        second, _, _ = standard_run(world, host)
        assert second.status_code == 409 and second.json()["detail"]["code"] == "FETCH_ALREADY_ACTIVE"
        assert world["client"].get(f"{BASE}/fetch").json()["state"] == "running"
        held[0]()  # the worker runs and finishes
    assert world["client"].get(f"{BASE}/fetch").json()["state"] == "finished"


def test_a_second_run_skips_records_with_a_waiting_or_confirmed_file(world):
    client = world["client"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
        confirm = event(world["doi"], "fetched_confirm", {"manifest_row": _waiting(world, world["doi"])["manifest_row"]})
        client.post(f"{BASE}/events", json={"events": [confirm]})
        plan = client.get(f"{BASE}/fetch/plan", params={"ids": f"{world['doi']},{world['arxiv']},{NEITHER}"}).json()
        assert (plan["already_have_file"], plan["waiting"], plan["asked"]) == (1, 1, 1)
        rows_before = len(manifest(world["ws"]))
        response, _, _ = standard_run(world, host, ids=[world["doi"], world["arxiv"], NEITHER])
    assert response.status_code == 202
    new = manifest(world["ws"])[rows_before:]
    assert [r["study_id"] for r in new] == [NEITHER]


def test_a_discarded_file_is_not_offered_again_and_the_record_is_left_out_unless_selected(world):
    client, study = world["client"], world["doi"]
    with ThreadedStub(ROUTES) as host:
        standard_run(world, host)
        waiting = _waiting(world, study)
        client.post(f"{BASE}/events", json={"events": [event(study, "fetched_discard",
                                                               {"manifest_row": waiting["manifest_row"], "reason": "wrong_paper"})]})
        assert client.get(f"{BASE}/fetch/plan").json()["discarded"] == 1
        standard_run(world, host, ids=[study])  # selected on purpose: asked again, the same bytes come back
    row = row_of(client, study)
    assert row["fulltext"]["pending_fetch"] is None  # never the same file again
    assert row["fulltext"]["last_lookup"]["outcome"] == "ACQUIRED"
    assert row["fulltext"]["last_lookup"]["same_as_discarded"] is True


def test_the_journal_rows_carry_the_counts_and_never_the_key(world):
    with ThreadedStub(ROUTES) as host:
        response, _, _ = standard_run(world, host)
    ws = world["ws"]
    [started], [finished] = journal(ws, fx.STARTED), journal(ws, fx.FINISHED)
    assert started["parameters"]["email"] == CONTACT and started["parameters"]["openalex_key_set"] is True
    assert started["metrics"] == {"records_asked": 3, "with_doi": 1, "with_arxiv_only": 1, "neither": 1,
                                  "already_have_file": 0, "waiting": 0, "discarded": 0}
    m = finished["metrics"]
    assert (m["asked"], m["reached"], m["found"], m["downloaded"], m["skipped"], m["errors"]) == (3, 3, 2, 2, 1, 0)
    for path in (ws / "audit" / "journal.jsonl", ws / "charting" / "fetch_manifest.jsonl",
                 ws / "charting" / "fetch_runs" / f"{response.json()['run_id']}.json"):
        assert SECRET_KEY not in path.read_text(encoding="utf-8")


def test_a_run_this_console_did_not_finish_reads_as_interrupted_without_a_write(world):
    ws = world["ws"]
    folder = ws / "charting" / "fetch_runs"
    folder.mkdir(parents=True, exist_ok=True)
    record = {"run_id": "FR-" + "0" * 24, "state": "running", "started_at": "2026-11-22T09:00:00Z", "total": 3}
    (folder / f"{record['run_id']}.json").write_text(json.dumps(record), encoding="utf-8")
    before = (folder / f"{record['run_id']}.json").read_text(encoding="utf-8")
    assert world["client"].get(f"{BASE}/fetch").json()["state"] == "interrupted"
    assert (folder / f"{record['run_id']}.json").read_text(encoding="utf-8") == before
    assert world["client"].get(BASE).status_code == 200


# --------------------------------------------------------------------------- DoD F7 at the app's level


def test_an_arxiv_only_record_is_asked_of_arxiv_and_fetched_from_the_link_arxiv_gives(world):
    with ThreadedStub(ROUTES) as host:
        _, lookups, arxiv = standard_run(world, host)
        assert host.hits["/pdf/2101.01234v3"] == 1
    assert arxiv.calls == [("https://export.arxiv.org/api/query", {"id_list": "2101.01234", "max_results": 1})]
    row = next(r for r in manifest(world["ws"]) if r["study_id"] == world["arxiv"])
    assert row["address"].endswith("/pdf/2101.01234v3") and row["version_label"] == "preprint (arXiv v3)"
    assert row["arxiv_id"] == "2101.01234" and row["arxiv_version"] == "v3"
    assert [lk["service"] for lk in row["lookups"]] == ["arxiv"]
    # The arXiv-only record never reaches the DOI services.
    assert all("2101.01234" not in url for url, _ in lookups.calls)


def test_a_journal_doi_in_arxivs_answer_goes_to_the_services_and_the_best_copy_wins(world):
    with ThreadedStub(ROUTES) as host:
        _, lookups, _ = standard_run(world, host, arxiv_doi=ARXIV_DOI, ids=[world["arxiv"]])
        assert host.hits["/journal.pdf"] == 1 and host.hits["/pdf/2101.01234v3"] == 0
    [row] = manifest(world["ws"])
    assert row["doi"] == ARXIV_DOI and row["arxiv_doi"] == ARXIV_DOI and row["version"] == "publishedVersion"
    assert [lk["service"] for lk in row["lookups"]] == ["arxiv", "openalex", "unpaywall"]
    assert any(ARXIV_DOI in url for url, _ in lookups.calls)


def test_arxiv_requests_share_one_budget_of_one_every_three_seconds(monkeypatch):
    waits: list[str] = []

    class Budget:
        rate = 1 / 3

        async def wait(self):
            waits.append("arxiv")

    asked = []
    monkeypatch.setattr("scholar_search.http_client.host_budget", lambda url: asked.append(url) or Budget())
    slept: list[float] = []

    async def sleep(seconds):
        slept.append(seconds)

    clock = iter([0.0, 0.2, 0.2]).__next__
    pacer = fx.HostPacer(pause=1.0, clock=clock, sleep=sleep)

    async def go():
        await pacer("http://arxiv.org/pdf/2101.01234v3")
        await pacer("https://www.example.org/a.pdf")
        await pacer("https://www.example.org/b.pdf")

    asyncio.run(go())
    assert waits == ["arxiv"] and asked == ["https://export.arxiv.org/api/query"]  # the API's own budget
    assert slept == [pytest.approx(0.8)]  # the same host again within the pause


def test_the_fetch_post_routes_are_on_the_browser_allow_list():
    from scholar_harness.console.browser import POST_PATHS

    for path in ("api/v1/charting/fetch", "api/v1/charting/fetch/cancel"):
        assert any(p.fullmatch(path) for p in POST_PATHS), path
    route = (_HERE.parents[1] / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts")
    assert r"/^api\/v1\/charting\/fetch(\/cancel)?$/," in route.read_text(encoding="utf-8")
