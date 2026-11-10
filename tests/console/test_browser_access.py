"""The packaged UI's access to the console (M5-slim; `console/browser.py`).

The static UI is served from the console process; the browser reaches the API
under `/api/console` with a session cookie set by a one-time launch link, and
only through the same allowlist as the development proxy (`route.ts`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import E2E_ANSWERS
from fastapi.testclient import TestClient

from scholar_harness.console import browser, create_app
from scholar_harness.inception.intent import CriterionDraft
from scholar_harness.workspace import catalog

TOKEN, SESSION = "desk-token", "session-secret"
ROUTE_TS = Path(__file__).resolve().parents[2] / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts"


@pytest.fixture
def ws(tmp_path):
    catalog.create(tmp_path / "root", "Review")
    return tmp_path / "root" / "review"


@pytest.fixture
def ui(tmp_path):
    folder = tmp_path / "ui"
    (folder / "en").mkdir(parents=True)
    (folder / "en" / "index.html").write_text("<html>overview</html>", encoding="utf-8")
    (folder / "404.html").write_text("<html>not here</html>", encoding="utf-8")
    return folder


def _app(ws, ui, codes=None):
    codes = codes or browser.LaunchCodes(SESSION)
    app = create_app(ws, token=TOKEN, browser_session=SESSION, launch_codes=codes, ui_dir=ui, workspaces_root=ws.parent)
    return app, codes


def _browser(app):
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    client.cookies.set(browser.SESSION_COOKIE, SESSION)
    return client


def _proxy_patterns(name):
    text = ROUTE_TS.read_text(encoding="utf-8")
    block = re.search(rf"const {name}: ReadonlyArray<RegExp> = \[(.*?)\];", text, re.S).group(1)
    return {m.replace("\\/", "/") for m in re.findall(r"/\^(.*?)\$/", block)}


def test_the_allowlist_equals_the_development_proxys():
    assert {p.pattern for p in browser.POST_PATHS} == _proxy_patterns("POST_PATHS")
    assert {p.pattern for p in browser.PUT_PATHS} == _proxy_patterns("PUT_PATHS")


def test_a_launch_code_sets_the_session_once(ws, ui):
    app, codes = _app(ws, ui)
    client = TestClient(app, base_url="http://127.0.0.1:8765", follow_redirects=False)
    assert client.get("/launch", params={"code": "guess"}).json()["detail"]["code"] == "LAUNCH_CODE_INVALID"
    code = codes.issue()
    landed = client.get("/launch", params={"code": code, "next": "/en/screening/home/"})
    assert landed.status_code == 303 and landed.headers["location"] == "/en/screening/home/"
    cookie = landed.headers["set-cookie"].lower()
    assert f"{browser.SESSION_COOKIE}={SESSION}".lower() in cookie and "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/launch", params={"code": code}).status_code == 401  # single use
    other = codes.issue()
    assert client.get("/launch", params={"code": other, "next": "https://evil.example/"}).headers["location"] == "/en/"


def test_the_browser_needs_the_session_and_the_api_still_needs_the_token(ws, ui):
    app, _ = _app(ws, ui)
    bare = TestClient(app, base_url="http://127.0.0.1:8765")
    assert bare.get("/api/console/api/v1/workspace/meta").json()["detail"]["code"] == "TOKEN_REQUIRED"
    client = _browser(app)
    meta = client.get("/api/console/api/v1/workspace/meta")
    assert meta.status_code == 200 and meta.json()["workspace"] == str(ws.resolve())
    # The cookie opens only the browser surface, not /api/v1 itself.
    assert client.get("/api/v1/workspace/meta").json()["detail"]["code"] == "TOKEN_REQUIRED"
    direct = TestClient(app, base_url="http://127.0.0.1:8765", headers={"Authorization": f"Bearer {TOKEN}"})
    assert direct.get("/api/v1/workspace/meta").status_code == 200


def test_writes_follow_the_allowlist_and_need_this_origin(ws, ui):
    client = _browser(_app(ws, ui)[0])
    same = {"Origin": "http://127.0.0.1:8765"}
    job = client.post("/api/console/api/v1/jobs", json={}, headers=same)
    assert (job.status_code, job.json()["detail"]["code"]) == (405, "CONSOLE_METHOD_REFUSED")
    foreign = client.post("/api/console/api/v1/workspaces", json={"title": "x"}, headers={"Origin": "http://127.0.0.1:3000"})
    assert (foreign.status_code, foreign.json()["detail"]["code"]) == (403, "CONSOLE_ORIGIN_REFUSED")
    created = client.post("/api/console/api/v1/workspaces", json={"title": "Second"}, headers=same)
    assert created.status_code == 201 and (ws.parent / "second" / "protocol.json").is_file()
    for bad in ("/api/console/api/v1/workspace/meta.json", "/api/console/api/v2/workspace/meta", "/api/console/static/x"):
        refused = client.get(bad)
        assert (refused.status_code, refused.json()["detail"]["code"]) == (400, "CONSOLE_PATH_REFUSED"), bad
    delete = client.delete("/api/console/api/v1/workspaces", headers=same)
    assert delete.json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED"


def test_the_draft_is_read_only_from_this_apps_pages(ws, ui):
    client = _browser(_app(ws, ui)[0])
    cross = client.get("/api/console/api/v1/screening/records/S-1/proposal", headers={"Sec-Fetch-Site": "cross-site"})
    assert (cross.status_code, cross.json()["detail"]["code"]) == (403, "CONSOLE_ORIGIN_REFUSED")


def _inception_draft() -> dict:
    a = E2E_ANSWERS
    proof_id = CriterionDraft("inclusion", f"Reports the gold-standard proof — {a[5]}", "proof").id
    return {
        "topic": a[0], "paradigm": a[1], "playbook": a[2], "unit_of_analysis": a[4], "proof": a[5],
        "out_of_scope": [s.strip() for s in a[6].split(",")], "rqs": [a[8]],
        "concepts": [{"concept": "weed detection"}, {"concept": "on-device inference"}],
        "criteria_decisions": {proof_id: True},
        "title": "On-Device Weed Detection for Embedded Agriculture", "lead_researcher": "Dr. Mouadh",
    }


def test_the_inception_flow_reaches_the_engine_from_the_browser(ws, ui):
    """M4b: the inception screens use drafts, steps, preview and genesis through the allowlist."""
    client = _browser(_app(ws, ui)[0])
    same = {"Origin": "http://127.0.0.1:8765"}
    base = "/api/console/api/v1/inception"
    created = client.post(f"{base}/drafts", json={"draft": {"topic": "edge AI"}}, headers=same)
    assert created.status_code == 201, created.text
    record = created.json()
    sid = record["session_id"]
    assert client.get(f"{base}/drafts").json()["items"][0]["session_id"] == sid
    saved = client.put(f"{base}/drafts/{sid}", json={"draft": _inception_draft(), "base_updated_at": record["updated_at"]}, headers=same)
    assert saved.status_code == 200, saved.text
    stale = client.put(f"{base}/drafts/{sid}", json={"draft": {}, "base_updated_at": record["updated_at"]}, headers=same)
    assert stale.json()["detail"]["code"] == "DRAFT_CONFLICT"
    for step in ("scope", "shape", "criteria", "matrix"):
        assert client.post(f"{base}/steps/{step}", json={"draft": _inception_draft()}, headers=same).status_code == 200, step
    preview = client.post(f"{base}/preview", json={"draft": _inception_draft()}, headers=same)
    assert preview.status_code == 200 and preview.json()["written"] == []
    made = client.post(f"{base}/drafts/{sid}/genesis", json={}, headers=same)
    assert made.status_code == 201, made.text
    assert (ws.parent / made.json()["slug"] / "protocol.json").is_file()


def test_inception_writes_need_this_origin_and_discard_is_not_carried(ws, ui):
    client = _browser(_app(ws, ui)[0])
    same = {"Origin": "http://127.0.0.1:8765"}
    base = "/api/console/api/v1/inception"
    foreign = client.post(f"{base}/drafts", json={"draft": {}}, headers={"Origin": "http://127.0.0.1:3000"})
    assert (foreign.status_code, foreign.json()["detail"]["code"]) == (403, "CONSOLE_ORIGIN_REFUSED")
    sid = client.post(f"{base}/drafts", json={"draft": {}}, headers=same).json()["session_id"]
    foreign_put = client.put(f"{base}/drafts/{sid}", json={"draft": {}}, headers={"Origin": "http://127.0.0.1:3000"})
    assert foreign_put.json()["detail"]["code"] == "CONSOLE_ORIGIN_REFUSED"
    for path in (f"{base}/steps/emit", f"{base}/drafts/{sid}/emitted", f"{base}/genesis"):
        refused = client.post(path, json={}, headers=same)
        assert (refused.status_code, refused.json()["detail"]["code"]) == (405, "CONSOLE_METHOD_REFUSED"), path
    assert client.put(f"{base}/drafts/{sid}/genesis", json={}, headers=same).json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED"
    discard = client.delete(f"{base}/drafts/{sid}", headers=same)
    assert discard.json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED"
    assert (ws.parent / ".drafts" / sid / "draft.json").is_file()


def test_recon_reaches_the_engine_from_the_browser(ws, ui, tmp_path):
    """M4c: probe (a job), its events, distill, directions and bind through the allowlist."""
    from scholar_search.models import Document, ExternalIds

    def search_fn(query, providers):
        return [
            Document(title=f"Weed detection on embedded boards {i}", year=2023, provider="openalex",
                     provider_id=f"W{i}", external_ids=ExternalIds(doi=f"10.1/b{i}"), abstract="weed detection")
            for i in range(13)
        ]

    app = _app(ws, ui)[0]
    app.state.recon_root, app.state.recon_search_fn = tmp_path / "recon", search_fn
    same = {"Origin": "http://127.0.0.1:8765"}
    base = "/api/console/api/v1/inception"
    with _browser(app) as client:
        sid = client.post(f"{base}/drafts", json={"draft": _inception_draft()}, headers=same).json()["session_id"]
        recon = f"{base}/drafts/{sid}/recon"
        foreign = client.post(f"{recon}/probe", json={}, headers={"Origin": "http://127.0.0.1:3000"})
        assert foreign.json()["detail"]["code"] == "CONSOLE_ORIGIN_REFUSED"
        job = client.post(f"{recon}/probe", json={}, headers=same)
        assert job.status_code == 202, job.text
        job_id = job.json()["job"]["job_id"]
        with client.stream("GET", f"{recon}/jobs/{job_id}/events") as stream:
            frames = [line for line in stream.iter_lines() if line.startswith("event: ")]
        assert frames[0] == "event: snapshot" and frames[-1] == "event: done"
        assert client.post(f"{recon}/distill", json={}, headers=same).status_code == 200
        labels = [d["label"] for d in client.get(f"{recon}/directions").json()["directions"]]
        bound = client.post(f"{recon}/bind", json={"direction": labels[0]}, headers=same)
        assert bound.status_code == 200 and bound.json()["grounding"]["pool"]["fingerprint"].startswith("sha256:")
        assert client.post(f"{recon}/jobs/{job_id}/cancel", json={}, headers=same).json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED"


def test_discovery_reaches_the_engine_from_the_browser(ws, ui, monkeypatch):
    """M3b-api (packet §5): the two job starts, cancel and the methods text pass the
    allowlist and reach their routes; nothing else of discovery is writable, and
    the generic job start stays closed."""
    from scholar_search.config import settings

    monkeypatch.setattr(settings, "mailto", None)
    app = _app(ws, ui)[0]
    same = {"Origin": "http://127.0.0.1:8765"}
    base = "/api/console/api/v1/discovery"
    with _browser(app) as client:
        foreign = client.post(f"{base}/runs", json={}, headers={"Origin": "http://127.0.0.1:3000"})
        assert foreign.json()["detail"]["code"] == "CONSOLE_ORIGIN_REFUSED"
        # Reached the route: it refuses before any request, as the packet says.
        run = client.post(f"{base}/runs", json={}, headers=same)
        assert (run.status_code, run.json()["detail"]["code"]) == (409, "MAILTO_NOT_SET")
        seeds = {"seeds": [{"id": "10.1000/x", "kind": "doi", "source": "you"}]}
        recall = client.post(f"{base}/recall", json=seeds, headers=same)
        assert (recall.status_code, recall.json()["detail"]["code"]) == (409, "MAILTO_NOT_SET")
        cancel = client.post(f"{base}/jobs/djob_0123456789abcdef/cancel", json={}, headers=same)
        assert (cancel.status_code, cancel.json()["detail"]["code"]) == (404, "DISCOVERY_JOB_NOT_FOUND")
        methods = client.put(f"{base}/report/methods", json={"text": "x"}, headers=same)
        assert (methods.status_code, methods.json()["detail"]["code"]) == (404, "RUN_NOT_FOUND")
        assert client.get(f"{base}/runs").json()["shape"] == "discovery.runs-v1"
        for path in ("plan", "report", "runs/run_001", "jobs/djob_1/events"):
            refused = client.post(f"{base}/{path}", json={}, headers=same)
            assert refused.json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED", path
        refused = client.put(f"{base}/report", json={}, headers=same)
        assert refused.json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED"
        start = client.post("/api/console/api/v1/jobs/start", json={"action_id": "discovery"}, headers=same)
        assert (start.status_code, start.json()["detail"]["code"]) == (405, "CONSOLE_METHOD_REFUSED")


def test_a_phone_token_reaches_no_discovery_route(ws):
    """Discovery is desktop-only, like inception (packet §5)."""
    app = create_app(ws, token=TOKEN, phone_tokens={"phone-token"}, workspaces_root=ws.parent)
    client = TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": "Bearer phone-token"})
    for method, path in (("GET", "plan"), ("GET", "runs"), ("POST", "runs"), ("GET", "handoff")):
        response = client.request(method, f"/api/v1/discovery/{path}", json={} if method == "POST" else None)
        assert (response.status_code, response.json()["detail"]["code"]) == (403, "TOKEN_SCOPE_REFUSED"), path


def test_the_static_ui_is_served_with_a_root_redirect_and_a_404_page(ws, ui):
    app, _ = _app(ws, ui)
    client = TestClient(app, base_url="http://127.0.0.1:8765", follow_redirects=False)
    root = client.get("/")
    assert root.status_code == 307 and root.headers["location"] == "/en/"
    page = client.get("/en/")
    assert page.status_code == 200 and "overview" in page.text  # no session needed: the UI holds no data
    missing = client.get("/nowhere")
    assert missing.status_code == 404 and "not here" in missing.text
    assert client.get("/api/v1/nowhere").json()["detail"]["code"] == "TOKEN_REQUIRED"


def test_without_the_packaged_options_nothing_changes(ws, tmp_path):
    app = create_app(ws, token=TOKEN)
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    assert client.get("/api/console/api/v1/workspace/meta").json()["detail"]["code"] == "CONSOLE_PATH_REFUSED"
    assert client.get("/en/").json()["detail"]["code"] == "TOKEN_REQUIRED"
    with pytest.raises(ValueError):
        create_app(ws, token=TOKEN, ui_dir=tmp_path)


def test_pages_are_revalidated_and_hashed_assets_cached_for_good(ws, ui):
    # A rebuilt app must reach the browser: with no Cache-Control a browser may
    # reuse an old page for a tenth of its age (the golden run saw the previous
    # build after a reinstall). Next's hashed assets never change content.
    chunk = ui / "_next" / "static" / "chunks"
    chunk.mkdir(parents=True)
    (chunk / "abc123.js").write_text("// built", encoding="utf-8")
    client = _browser(_app(ws, ui)[0])
    page = client.get("/en/")
    assert page.status_code == 200 and page.headers["cache-control"] == "no-cache"
    again = client.get("/en/", headers={"if-none-match": page.headers["etag"]})
    assert again.status_code == 304 and again.headers["cache-control"] == "no-cache"
    asset = client.get("/_next/static/chunks/abc123.js")
    assert asset.status_code == 200 and asset.headers["cache-control"] == "public, max-age=31536000, immutable"
