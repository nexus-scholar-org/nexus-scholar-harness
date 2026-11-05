"""The packaged UI's access to the console (M5-slim; `console/browser.py`).

The static UI is served from the console process; the browser reaches the API
under `/api/console` with a session cookie set by a one-time launch link, and
only through the same allowlist as the development proxy (`route.ts`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import browser, create_app
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
    landed = client.get("/launch", params={"code": code, "next": "/en/screening/"})
    assert landed.status_code == 303 and landed.headers["location"] == "/en/screening/"
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
