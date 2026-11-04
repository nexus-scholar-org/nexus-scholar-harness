"""INC-01: the console refuses callers that are not the local research UI.

Four parts, one test group each: a per-launch bearer token, a Host check
(DNS rebinding), an Origin check, and a command allowlist for pipelines and
jobs. ``serve`` is checked for loopback-only binding and for wiring the token.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from scholar_harness.console import create_app
from scholar_harness.pipeline import PipelineSpec, validate_spec

TOKEN = "per-launch-token"
LOOPBACK = "http://127.0.0.1"


@pytest.fixture
def ws(tmp_path):
    workspace = tmp_path / "ws"
    (workspace / "audit").mkdir(parents=True)
    (workspace / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    return workspace


def _client(ws, **kwargs) -> TestClient:
    return TestClient(create_app(ws, **kwargs), base_url=LOOPBACK)


# --- bearer token ------------------------------------------------------------


def test_api_routes_require_the_launch_token(ws):
    client = _client(ws, token=TOKEN)
    assert client.get("/api/v1/jobs").status_code == 401
    refused = client.get("/api/v1/jobs", headers={"Authorization": "Bearer wrong"})
    assert refused.status_code == 401
    assert refused.json()["detail"]["code"] == "TOKEN_REQUIRED"
    ok = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {TOKEN}"})
    assert ok.status_code == 200


def test_mutations_require_the_launch_token(ws):
    client = _client(ws, token=TOKEN)
    response = client.post("/api/v1/jobs/start", json={"action_id": "status"})
    assert response.status_code == 401


def test_healthz_needs_no_token(ws):
    assert _client(ws, token=TOKEN).get("/healthz").status_code == 200


# --- Host --------------------------------------------------------------------


def test_foreign_host_is_refused(ws):
    client = _client(ws)
    response = client.get("/healthz", headers={"Host": "evil.example"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "HOST_REFUSED"


def test_loopback_hosts_with_ports_are_accepted(ws):
    client = _client(ws)
    for host in ("127.0.0.1:8765", "localhost:8765", "[::1]:8765"):
        assert client.get("/healthz", headers={"Host": host}).status_code == 200, host


def test_explicit_trusted_hosts_drop_the_test_host(ws):
    client = TestClient(create_app(ws, trusted_hosts=("127.0.0.1",)))
    assert client.get("/healthz").status_code == 400  # Host: testserver


# --- Origin ------------------------------------------------------------------


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_foreign_origin_is_refused(ws, method):
    client = _client(ws)
    response = client.request(
        method, "/api/v1/jobs", headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ACTION_ORIGIN_REFUSED"


def test_loopback_origin_and_no_origin_are_accepted(ws):
    client = _client(ws)
    assert client.get("/api/v1/jobs", headers={"Origin": "http://localhost:3000"}).status_code == 200
    assert client.get("/api/v1/jobs").status_code == 200


# --- command allowlist -------------------------------------------------------


def _spec(command: list[str]) -> dict:
    return {
        "id": "evil",
        "nodes": [{"id": "n1", "kit": "x", "command": command, "args": {}}],
        "edges": [],
    }


@pytest.mark.parametrize(
    "command",
    [
        ["python", "-c", "print(1)"],
        ["bash", "-c", "id"],
        ["scholar-harness", "serve"],
        ["uv", "run", "anything"],
        ["python", "src/scholar_harness/other.py"],
        ["scholar-search/../../python"],
    ],
)
def test_pipeline_commands_outside_the_allowlist_are_invalid(command):
    errors = validate_spec(PipelineSpec.model_validate(_spec(command)))["errors"]
    assert any("COMMAND_NOT_ALLOWED" in error for error in errors), errors


@pytest.mark.parametrize(
    "command",
    [
        ["scholar-search", "run"],
        ["scholar-pdf", "download"],
        ["scholar-rag", "matrix"],
        ["python", "src/scholar_harness/agent_screen.py", "prepare"],
    ],
)
def test_pipeline_commands_in_the_allowlist_are_valid(command):
    errors = validate_spec(PipelineSpec.model_validate(_spec(command)))["errors"]
    assert not any("COMMAND_NOT_ALLOWED" in error for error in errors), errors


def test_console_refuses_to_store_a_pipeline_with_arbitrary_code(ws):
    response = _client(ws).post(
        "/api/v1/pipelines", json={"spec": _spec(["python", "-c", "print(1)"])}
    )
    assert response.status_code == 422
    assert "COMMAND_NOT_ALLOWED" in response.text
    assert not (ws / ".harness-console" / "pipelines" / "evil.json").exists()


def test_job_workspace_must_be_the_served_workspace(ws, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    response = _client(ws).post(
        "/api/v1/jobs/start", json={"action_id": "status", "workspace": str(elsewhere)}
    )
    assert response.status_code == 400
    assert "WORKSPACE_MISMATCH" in response.text


# --- serve -------------------------------------------------------------------


def test_serve_refuses_a_non_loopback_bind(ws, monkeypatch):
    import uvicorn

    from scholar_harness.cli import app

    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: pytest.fail("must not start"))
    result = CliRunner().invoke(app, ["serve", "--workspace", str(ws), "--host", "0.0.0.0"])
    assert result.exit_code == 1
    assert "loopback" in result.stdout.lower()


def test_serve_requires_the_token_from_the_environment(ws, monkeypatch):
    import uvicorn

    from scholar_harness.cli import app

    served = {}
    monkeypatch.setenv("NEXUS_CONSOLE_TOKEN", TOKEN)
    monkeypatch.setattr(uvicorn, "run", lambda application, **k: served.update(app=application))
    result = CliRunner().invoke(app, ["serve", "--workspace", str(ws)])
    assert result.exit_code == 0, result.stdout
    assert TOKEN not in result.stdout

    client = TestClient(served["app"], base_url=LOOPBACK)
    assert client.get("/api/v1/jobs").status_code == 401
    assert client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    assert TestClient(served["app"]).get("/healthz").status_code == 400  # testserver not trusted


def test_serve_generates_a_token_when_none_is_set(ws, monkeypatch):
    import uvicorn

    from scholar_harness.cli import app

    served = {}
    monkeypatch.delenv("NEXUS_CONSOLE_TOKEN", raising=False)
    monkeypatch.setattr(uvicorn, "run", lambda application, **k: served.update(app=application))
    result = CliRunner().invoke(app, ["serve", "--workspace", str(ws)])
    assert result.exit_code == 0, result.stdout
    assert "NEXUS_CONSOLE_TOKEN=" in result.stdout
    token = result.stdout.split("NEXUS_CONSOLE_TOKEN=")[1].split()[0]
    assert len(token) >= 32
    client = TestClient(served["app"], base_url=LOOPBACK)
    assert client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"}).status_code == 200
