"""M11b part C, the engine side the screens need (follow-ups of the part A and B reviews).

- The browser may POST to the new routes (the console's list and the development proxy's
  list stay equal; ``test_browser_access.py`` checks the parity).
- ``GET /screening/criteria`` does not offer a revision that every call would refuse.
- The hand-off refusal does not promise a way out that does not exist.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import browser, create_app
from scholar_harness.screening import criteria as cr


@pytest.mark.parametrize(
    ("path", "allowed"),
    [
        ("api/v1/screening/criteria/amendments", True),
        ("api/v1/screening/pilot", True),
        ("api/v1/screening/pilot/pilot_001/decisions", True),
        ("api/v1/screening/pilot/pilot_012/close", True),
        ("api/v1/screening/pilot/pilot_1/close", False),
        ("api/v1/screening/pilot/pilot_001/result", False),  # a read, never a POST
        ("api/v1/screening/pilot/../criteria/amendments", False),
    ],
)
def test_the_browser_may_post_to_the_new_routes_only(path, allowed):
    assert any(p.fullmatch(path) for p in browser.POST_PATHS) is allowed


def _handoff_workspace(tmp_path):
    import test_screening_actions as sa

    workspace, _studies = sa._scaffold(tmp_path)
    sa.run_recommend(workspace, 1, produced_at=sa.NOW)
    return workspace


def test_the_criteria_route_offers_no_revision_while_a_handoff_batch_exists(tmp_path):
    workspace = _handoff_workspace(tmp_path)
    client = TestClient(create_app(workspace, token="t"), base_url="http://127.0.0.1",
                        headers={"Authorization": "Bearer t"})
    body = client.get("/api/v1/screening/criteria").json()
    assert (body["can_amend"], body["handoff_batches"], body["batches_prepared"]) == (False, [1], True)


def test_the_handoff_refusal_names_the_only_way_to_revised_criteria(tmp_path):
    workspace = _handoff_workspace(tmp_path)
    inc = cr.criteria_in_force(workspace).inclusion[0].id
    with pytest.raises(cr.AmendmentRefused) as refused:
        cr.amend_criteria(workspace, op="reword", side="inclusion", ids=[inc], text="x", reason_category=None,
                          reason_category_given=False, reason="r", confirm=False, amended_by="r",
                          amended_at="2026-11-21T10:00:00Z")
    message = refused.value.message
    assert "start a new screening from this protocol" in message and "Triage" not in message
