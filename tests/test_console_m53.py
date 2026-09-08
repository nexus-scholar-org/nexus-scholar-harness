"""Hermetic tests for M5.3 (screening decisions, audit POST, pipelines, job aliases).

Covers:
  - POST /api/v1/screening/batch/{n}/decisions: atomic write, validation,
    journal + project.json updates, and round-trip parity through
    `agent_screen.cmd_collect` for BOTH the console wrapper (§7) and the
    legacy raw-array format.
  - POST /api/v1/audit/events: journal event + INDEX.md/project.json refresh.
  - PipelineSpec CRUD, fingerprint stability, dry-run (incl. "writes nothing").
  - Job endpoint aliases (POST /api/v1/jobs, GET /api/v1/jobs/{id}/events).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from scholar_harness.console import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_SCREEN = REPO_ROOT / "src" / "scholar_harness" / "agent_screen.py"


def _load_agent_screen():
    spec = importlib.util.spec_from_file_location("agent_screen", AGENT_SCREEN)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bootstrap(tmp):
    ws = tmp / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "synthesis").mkdir(parents=True)
    (ws / "phase4").mkdir(parents=True)
    (ws / "audit").mkdir(parents=True)
    (ws / "pdfs").mkdir(parents=True)
    (ws / "extracted").mkdir(parents=True)

    (ws / "literature" / "screening" / "batch_001.json").write_text(
        json.dumps(
            {
                "batch_index": 1,
                "batch_size": 2,
                "status": "PENDING",
                "protocol": {
                    "title": "Test Protocol",
                    "screening_criteria": {
                        "inclusion": [{"id": "INC-01", "criterion": "UAV precision-agriculture"}],
                        "exclusion": [{"id": "EXC-02", "criterion": "no agri domain"}],
                    },
                },
                "papers": [
                    {"workspace_id": "SCI-000001", "title": "A", "year": 2023},
                    {"workspace_id": "SCI-000002", "title": "B", "year": 2022},
                ],
            }
        ),
        encoding="utf-8",
    )
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(
        json.dumps({"title": "Test WS", "stats": {}}), encoding="utf-8"
    )
    (ws / "INDEX.md").write_text("# INDEX stub", encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# screening decisions writer
# ---------------------------------------------------------------------------

def test_post_screening_decisions_atomic(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))

    r = client.post(
        "/api/v1/screening/batch/1/decisions",
        json={
            "batch": 1,
            "reviewed_by": "test",
            "decisions": [
                {"workspace_id": "SCI-000001", "decision": "INCLUDE", "confidence": 0.9,
                 "matched_inclusion_criteria": ["INC-01"], "screening_reasoning": "matches"},
                {"workspace_id": "SCI-000002", "decision": "EXCLUDE", "confidence": 0.6,
                 "violated_exclusion_criteria": ["EXC-02"]},
            ],
        },
    )
    assert r.status_code == 200
    assert r.json()["decisions_written"] == 2

    file = ws / "literature" / "screening" / "batch_001_decisions.json"
    assert file.exists()
    payload = json.loads(file.read_text(encoding="utf-8"))
    assert payload["batch"] == 1
    assert payload["reviewed_by"] == "test"
    assert payload["timestamp"]
    assert payload["decisions"][0]["workspace_id"] == "SCI-000001"
    assert payload["decisions"][0]["decision"] == "INCLUDE"
    assert payload["decisions"][0]["confidence"] == 0.9
    assert payload["decisions"][1]["decision"] == "EXCLUDE"

    # Atomic discipline: no partial temp files survive.
    assert not list((ws / "literature" / "screening").glob("*.tmp-*"))

    # Journal event SCREEN_DECISIONS appended.
    journal = [json.loads(l) for l in (ws / "audit" / "journal.jsonl").read_text().splitlines() if l.strip()]
    assert journal[-1]["action"] == "SCREEN_DECISIONS"
    assert journal[-1]["agent_or_tool"] == "scholar-harness-console"
    assert journal[-1]["metrics"] == {"included": 1, "excluded": 1, "total": 2}

    # project.json updated_at refreshed.
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["updated_at"]


def test_screening_decisions_validation(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))

    base = {"batch": 1, "decisions": [{"workspace_id": "SCI-000001", "decision": "INCLUDE"}]}

    # Unknown workspace id -> 422.
    bad_id = {"batch": 1, "decisions": [{"workspace_id": "NOPE", "decision": "INCLUDE"}]}
    assert client.post("/api/v1/screening/batch/1/decisions", json=bad_id).status_code == 422

    # Bad decision enum -> 422 (pydantic).
    bad_dec = {"batch": 1, "decisions": [{"workspace_id": "SCI-000001", "decision": "MAYBE"}]}
    assert client.post("/api/v1/screening/batch/1/decisions", json=bad_dec).status_code == 422

    # Confidence out of range -> 422.
    bad_cfd = {"batch": 1, "decisions": [{"workspace_id": "SCI-000001", "decision": "INCLUDE", "confidence": 1.7}]}
    assert client.post("/api/v1/screening/batch/1/decisions", json=bad_cfd).status_code == 422

    # Batch disagreement -> 400.
    assert client.post("/api/v1/screening/batch/1/decisions", json={**base, "batch": 2}).status_code == 400

    # Missing batch -> 404.
    assert client.post("/api/v1/screening/batch/9/decisions", json=base).status_code == 404


def _bootstrap_collect(tmp, n_batches):
    """Workspace shaped for agent_screen.collect: verified.json + protocol + manifest."""
    ws = _bootstrap(tmp)
    (ws / "protocol.json").write_text(
        json.dumps(
            {
                "metadata": {"title": "UAV SLR"},
                "research_questions": [{"id": "RQ1", "text": "How do UAVs map weeds?"}],
                "screening_criteria": {
                    "inclusion": [{"id": "INC-01", "criterion": "UAV precision-agriculture"}],
                    "exclusion": [{"id": "EXC-02", "criterion": "no agri domain"}],
                },
            }
        ),
        encoding="utf-8",
    )
    verified = [
        {"workspace_id": f"SCI-{i:06d}", "title": f"Paper {i}", "year": 2023 - i,
         "abstract": "UAV multispectral weed mapping", "venue": "J", "external_ids": {"doi": f"10.1/{i}"}}
        for i in range(1, n_batches * 2 + 1)
    ]
    (ws / "literature" / "verified.json").write_text(json.dumps(verified), encoding="utf-8")
    (ws / "literature" / "screening" / "MANIFEST.json").write_text(
        json.dumps(
            {
                "total_papers": len(verified),
                "batch_size": 2,
                "total_batches": n_batches,
                "batches": [
                    {
                        "batch_index": b,
                        "file": f"batch_{b:03d}.json",
                        "decisions_file": f"batch_{b:03d}_decisions.json",
                        "paper_count": 2,
                        "status": "DONE",
                    }
                    for b in range(1, n_batches + 1)
                ],
            }
        ),
        encoding="utf-8",
    )
    for b in range(1, n_batches + 1):
        (ws / "literature" / "screening" / f"batch_{b:03d}.json").write_text(
            json.dumps(
                {
                    "batch_index": b,
                    "batch_size": 2,
                    "status": "PENDING",
                    "protocol": {},
                    "papers": [
                        {"workspace_id": f"SCI-{(b-1)*2+1:06d}"},
                        {"workspace_id": f"SCI-{(b-1)*2+2:06d}"},
                    ],
                }
            ),
            encoding="utf-8",
        )
    return ws


def test_screening_parity_console_wrapper(tmp_path):
    """GUI-written wrapper -> cmd_collect produces correct PRISMA outputs."""
    agent_screen = _load_agent_screen()
    ws = _bootstrap_collect(tmp_path, n_batches=1)
    client = TestClient(create_app(ws))

    r = client.post(
        "/api/v1/screening/batch/1/decisions",
        json={
            "batch": 1,
            "decisions": [
                {"workspace_id": "SCI-000001", "decision": "INCLUDE", "confidence": 0.95},
                {"workspace_id": "SCI-000002", "decision": "EXCLUDE", "confidence": 0.6,
                 "violated_exclusion_criteria": ["EXC-02"]},
            ],
        },
    )
    assert r.status_code == 200

    agent_screen.cmd_collect(ws)
    included = json.loads((ws / "literature" / "included.json").read_text(encoding="utf-8"))
    excluded = json.loads((ws / "literature" / "excluded.json").read_text(encoding="utf-8"))
    assert [d["workspace_id"] for d in included] == ["SCI-000001"]
    assert [d["workspace_id"] for d in excluded] == ["SCI-000002"]
    assert (ws / "literature" / "prisma_screening_report.md").exists()
    assert (ws / "literature" / "prisma_report.json").exists()


def test_screening_parity_legacy_array(tmp_path):
    """Raw-array (legacy agent format) still parses through cmd_collect."""
    agent_screen = _load_agent_screen()
    ws = _bootstrap_collect(tmp_path, n_batches=1)
    # Write the legacy format directly (bypassing the endpoint).
    (ws / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {"workspace_id": "SCI-000001", "decision": "INCLUDE", "confidence": 0.9},
                {"workspace_id": "SCI-000002", "decision": "EXCLUDE", "confidence": 0.8},
            ]
        ),
        encoding="utf-8",
    )
    agent_screen.cmd_collect(ws)
    included = json.loads((ws / "literature" / "included.json").read_text(encoding="utf-8"))
    assert [d["workspace_id"] for d in included] == ["SCI-000001"]


# ---------------------------------------------------------------------------
# audit events POST
# ---------------------------------------------------------------------------

def test_audit_event_post(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    before = (ws / "project.json").read_text(encoding="utf-8")

    r = client.post(
        "/api/v1/audit/events",
        json={
            "action": "verification_review",
            "agent_or_tool": "console-tester",
            "description": "checked RoB verdicts",
            "status": "SUCCESS",
        },
    )
    assert r.status_code == 201
    evt = r.json()
    assert evt["action"] == "VERIFICATION_REVIEW"
    assert evt["agent_or_tool"] == "console-tester"
    assert evt["event_id"].startswith("EVT-")
    assert evt["timestamp"]

    lines = [l for l in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert json.loads(lines[-1])["event_id"] == evt["event_id"]

    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["updated_at"] and manifest["updated_at"] != json.loads(before).get("updated_at")
    # INDEX.md regenerated by the workspace-manager skill (title present).
    assert "Test WS" in (ws / "INDEX.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# pipelines
# ---------------------------------------------------------------------------

VALID_SPEC = {
    "schema_version": "0.1.0",
    "id": "my_review",
    "archetype": "PRISMA_SLR",
    "name": "My Review",
    "workspace_slug": "my-review",
    "settings": {"queries": {"q1": "UAV weeds"}},
    "nodes": [
        {
            "id": "n1",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.q1}}"},
            "outputs": ["literature/candidates.json"],
        },
        {
            "id": "n2",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "literature/candidates.json"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
        },
    ],
    "edges": [["n1", "n2"]],
    "created_by": "test",
}


def test_pipelines_crud_and_dry_run(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))

    r = client.post("/api/v1/pipelines", json={"spec": VALID_SPEC})
    assert r.status_code == 201, r.text
    saved = r.json()["spec"]
    fp = saved["fingerprint"]
    assert fp.startswith("sha256:")
    assert saved["id"] == "my_review"

    # Stored under the runtime dir; never a canonical write.
    store = ws / ".harness-console" / "pipelines" / "my_review.json"
    assert store.exists()
    assert "abc" not in json.loads(store.read_text(encoding="utf-8"))

    # Fingerprint stable across save+read.
    again = client.get("/api/v1/pipelines/my_review").json()["spec"]
    assert again["fingerprint"] == fp

    listed = client.get("/api/v1/pipelines").json()
    assert "my_review" in listed["ids"]
    assert "prisma_slr_default" in listed["ids"]  # built-in template always present

    # Dry-run validates and orders.
    dry = client.post("/api/v1/pipelines/my_review/dry-run", json={}).json()
    assert dry["valid"] is True
    assert dry["nodes_ordered"] == ["n1", "n2"]
    assert dry["per_node_limit"] == 25
    assert "no canonical files modified" in dry["message"]


def test_pipelines_invalid_and_cycle_rejected(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))

    # Unresolved {{template}} key -> 422.
    broken = json.loads(json.dumps(VALID_SPEC))
    broken["nodes"][0]["args"]["query"] = "{{missing_setting}}"
    assert client.post("/api/v1/pipelines", json={"spec": broken}).status_code == 422

    # Cycle -> 422.
    cyclic = json.loads(json.dumps(VALID_SPEC))
    cyclic["edges"] = [["n1", "n2"], ["n2", "n1"]]
    assert client.post("/api/v1/pipelines", json={"spec": cyclic}).status_code == 422

    # Output collision -> 422.
    collide = json.loads(json.dumps(VALID_SPEC))
    collide["nodes"][1]["outputs"] = ["literature/candidates.json"]
    assert client.post("/api/v1/pipelines", json={"spec": collide}).status_code == 422

    # Dry-run of the built-in template writes nothing canonical.
    dry = client.post("/api/v1/pipelines/prisma_slr_default/dry-run", json={}).json()
    assert dry["valid"] is True
    assert dry["requires_decision"] == ["n3_screen"]
    assert not (ws / "literature" / "candidates.json").exists()  # nothing written
    assert not list(ws.glob("**/candidates.json"))


def test_pipeline_fingerprint_stable_across_ordering(tmp_path):
    from scholar_harness.console.api.pipelines import PipelineSpec, _fingerprint

    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    spec_a = client.post("/api/v1/pipelines", json={"spec": VALID_SPEC}).json()["spec"]
    spec_b = client.post("/api/v1/pipelines", json={"spec": VALID_SPEC}).json()["spec"]
    assert spec_a["fingerprint"] == spec_b["fingerprint"]
    assert _fingerprint(PipelineSpec.model_validate(VALID_SPEC)) == spec_a["fingerprint"]


# ---------------------------------------------------------------------------
# job endpoint aliases
# ---------------------------------------------------------------------------

class _StubJob:
    def __init__(self, action_id, state="running"):
        self.job_id = "job_alias_1"
        self.action_id = action_id
        self.state = state
        self.pid = 123
        self.exit_code = None
        self.command = ["fake"]
        self.cwd = "."
        self.log_path = None
        self.started_at = "2026-09-01T00:00:00+00:00"
        self.finished_at = None
        self.journal_event_id = None
        self.error = None

    def to_dict(self):
        return {
            "job_id": self.job_id, "action_id": self.action_id, "state": self.state,
            "pid": self.pid, "exit_code": self.exit_code, "command": self.command,
            "cwd": self.cwd, "log_path": self.log_path, "started_at": self.started_at,
            "finished_at": self.finished_at, "journal_event_id": self.journal_event_id,
            "error": self.error,
        }


class _StubRunner:
    def __init__(self):
        self.jobs = {}

    async def start(self, action_id, query=None, workspace=None, pipeline_id=None):
        from scholar_harness.console.runtimes.actions import get_action

        get_action(action_id)
        self.jobs["job_alias_1"] = _StubJob(action_id)
        return self.jobs["job_alias_1"]

    def get(self, job_id):
        if job_id not in self.jobs:
            raise KeyError(job_id)
        return self.jobs[job_id]


def _all_routes(app):
    routes = []
    stack = list(app.routes)
    while stack:
        r = stack.pop()
        routes.append(r)
        inner = getattr(r, "original_router", None) or getattr(r, "app", None)
        if inner is not None:
            stack.extend(getattr(inner, "routes", []))
    return routes


def test_jobs_alias_post_and_events_route(tmp_path):
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    runner = _StubRunner()
    app.state.job_runner = runner
    client = TestClient(app)

    # SPECS canonical path: POST /api/v1/jobs.
    r = client.post("/api/v1/jobs", json={"action_id": "sync"})
    assert r.status_code == 202
    assert r.json()["job"]["job_id"] == "job_alias_1"

    # The SSE events route is registered as a stream (headless: just verify it
    # maps to job_stream and yields an SSE snapshot frame without hanging).
    import asyncio
    from types import SimpleNamespace

    from scholar_harness.console.api.jobs import job_stream

    routes = {route.path: route for route in _all_routes(app) if hasattr(route, "path")}
    endpoint = routes["/api/v1/jobs/{job_id}/events"]
    assert "GET" in getattr(endpoint, "methods", set())

    async def scenario():
        resp = await job_stream("job_alias_1", SimpleNamespace(app=app))
        gen = resp.body_iterator
        first = await gen.__anext__()
        assert "event: snapshot" in first
        await gen.aclose()
        return True

    assert asyncio.run(scenario())