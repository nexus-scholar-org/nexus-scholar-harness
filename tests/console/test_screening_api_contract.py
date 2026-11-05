"""The engine produces the shared screening API fixtures (contract §8).

`tests/fixtures/screening_api/*.json` are the request/response pairs the M1b
UI uses as its mock data. This test regenerates them from the real console and
requires the committed files to match byte for byte, then spells out the
contract meaning each key fixture pins, so a change shows up as a named
assertion, not only as a diff.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "screening_api"
_SPEC = importlib.util.spec_from_file_location(
    "generate_screening_api_fixtures", ROOT / "scripts" / "generate_screening_api_fixtures.py"
)
generator = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = generator
_SPEC.loader.exec_module(generator)


@pytest.fixture(scope="module")
def produced() -> dict[str, dict]:
    return generator.generate()


def _committed(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_the_committed_fixtures_are_what_the_engine_produces(produced):
    committed = {p.name for p in FIXTURES.glob("*.json")}
    assert committed == set(produced), "run scripts/generate_screening_api_fixtures.py and review the diff"
    for name, fixture in produced.items():
        on_disk = (FIXTURES / name).read_bytes().replace(b"\r\n", b"\n")
        assert on_disk == generator._bytes(fixture), f"{name} is stale"


def _result(name: str) -> list[str]:
    return [r["result"] for r in _committed(name)["response"]["body"]["results"]]


def _code(name: str) -> str:
    return _committed(name)["response"]["body"]["detail"]["code"]


def test_intake_results_cover_every_state():
    assert _result("events_accepted.json") == ["accepted"]
    assert _result("events_duplicate.json") == ["duplicate"]
    assert _result("events_conflict.json") == ["conflict"]
    refused = _committed("events_refused_reason_code.json")["response"]["body"]["results"][0]
    assert refused["refusal"]["code"] == "REASON_CODE_INVALID"
    stale = _committed("events_refused_stale_binding.json")["response"]["body"]["results"][0]
    assert stale["refusal"]["code"] == "STALE_BINDING"


def test_blinding_and_scope_refusals():
    assert _committed("proposal_hidden.json")["response"]["status"] == 403
    assert _code("proposal_hidden.json") == "PROPOSAL_HIDDEN"
    revealed = _committed("proposal_revealed.json")["response"]["body"]["proposal"]
    assert revealed["derived_outcome"] == "INCLUDE" and revealed["validators"]
    assert _code("phone_scope_refused.json") == "TOKEN_SCOPE_REFUSED"
    assert _code("prepare_snapshot_not_accepted.json") == "SNAPSHOT_NOT_ACCEPTED"


def test_conflict_listed_then_resolved():
    items = _committed("conflicts_open.json")["response"]["body"]["items"]
    assert len(items) == 1 and len(items[0]["events"]) == 2
    assert _result("conflict_resolved.json") == ["accepted"]


def test_queue_never_reveals_the_agent_outcome():
    queue = _committed("queue_needs_you.json")["response"]["body"]
    assert len(queue["items"]) == 3 and "derived_outcome" not in json.dumps(queue)
    assert _committed("queue_decided_empty.json")["response"]["body"]["items"] == []
    assert any(i["flags"] == ["title_only"] for i in queue["items"])


def test_prisma_preview_counts_unclear_apart():
    preview = _committed("prisma_preview.json")["response"]["body"]
    assert preview["included"] == 1
    assert preview["unclear_to_full_text"] == 1
    assert preview["excluded"]["total"] == 1
    assert preview["not_yet_decided"] == 0
    assert all(check["ok"] for check in preview["checks"])
