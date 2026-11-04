"""M1a end to end: the 30 golden records screened through the API.

A copy of `workspaces/golden-uav-30` (frozen v0.3 protocol, accepted corpus) is
prepared, every record is decided through `POST /decisions/events`, every
batch is approved, the collector publishes, and
`scripts/check_golden_workspace.py` must pass all three checks.

The outcomes here are SYNTHETIC, assigned in a fixed pattern only to exercise
the pipeline; they are not screening judgements. The real golden run, with the
researcher's own decisions, is the M5-slim gate.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.authority.review import approve_command
from scholar_harness.console import create_app
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "workspaces" / "golden-uav-30"
BASE = "/api/v1/screening"
TOKEN = "golden-e2e-token"

_SPEC = importlib.util.spec_from_file_location("check_golden_workspace", ROOT / "scripts" / "check_golden_workspace.py")
checker = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = checker
_SPEC.loader.exec_module(checker)


@pytest.mark.slow
def test_golden_records_screened_through_the_api_pass_the_golden_checker(tmp_path):
    ws = tmp_path / "golden-uav-30"
    shutil.copytree(GOLDEN, ws)
    (ws / "literature" / "screening" / "operator_context.json").parent.mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps({"schema": "harness-operator-context-v1", "operator_identity": "e2e-researcher"}),
        encoding="utf-8",
    )
    cmd_prepare(ws, batch_size=10)

    client = TestClient(
        create_app(ws, token=TOKEN), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    screener = client.get(f"{BASE}/settings").json()["screener_id"]
    exclusion = sorted(
        c["id"] for c in json.loads((ws / "protocol.json").read_text(encoding="utf-8"))["screening_criteria"]["exclusion"]
    )[0]
    studies = []
    cursor = 0
    while cursor is not None:
        page = client.get(f"{BASE}/queue", params={"view": "needs_you", "cursor": cursor, "limit": 50}).json()
        studies += [item["study_id"] for item in page["items"]]
        cursor = page["next_cursor"]
    assert len(studies) == 30

    pattern = ["INCLUDE"] * 10 + ["EXCLUDE"] * 15 + ["MAYBE"] * 5  # synthetic, see module docstring
    events = []
    for study, outcome in zip(studies, pattern):
        binding = client.get(f"{BASE}/records/{study}").json()["binding"]
        events.append(
            {
                "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"golden-e2e:{study}")),
                "study_id": study,
                "screener_id": screener,
                "method": "HUMAN",
                "outcome": outcome,
                "reason_code": exclusion if outcome == "EXCLUDE" else None,
                "note": "Synthetic e2e decision.",
                "criteria": [],
                "decided_at": "2026-11-04T15:00:00.000Z",
                "device": "desktop",
                "supersedes": None,
                "proposal_shown": None,
                "binding": binding,
            }
        )
    results = client.post(f"{BASE}/decisions/events", json={"events": events}).json()["results"]
    assert {r["result"] for r in results} == {"accepted"}

    preview = client.get(f"{BASE}/prisma/preview").json()
    assert (preview["included"], preview["unclear_to_full_text"], preview["excluded"]["total"]) == (10, 5, 15)
    assert all(check["ok"] for check in preview["checks"])

    batches = sorted(json.loads((ws / "literature" / "screening" / "MANIFEST.json").read_text(encoding="utf-8"))["batches"],
                     key=lambda b: b["batch_index"])
    for position, batch in enumerate(batches, start=1):
        result = approve_command(ws, batch["batch_index"], approved_at=f"2026-11-04T16:0{position}:00+00:00")
        assert result["source"] == "decision-events"
    assert result["publication_staged"] is True

    cmd_collect(ws)

    verdict = {r.name: r for r in checker.run_checks(ws)}
    assert all(r.ok for r in verdict.values()), {n: r.problems for n, r in verdict.items()}
