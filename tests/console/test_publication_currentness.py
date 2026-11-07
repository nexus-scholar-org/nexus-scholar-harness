"""M6-beta "published means current" (review T-P1-1, decision 2026-11-07).

`require_current_generation` binds the batch files and the published outputs,
not the decision files, so a decision made after publish left the status
CURRENT on every surface except export and methods, which added their own
check. One wrapper, `screening_currentness`, now runs that check for every
caller that reports the status.
"""

from __future__ import annotations

from test_export_api import BASE, change_after_publish, client_for, published_workspace

from scholar_harness.authority.generations import GENERATION_STALE, GenerationStatus
from scholar_harness.screening.currentness import screening_currentness


def test_a_decision_after_publish_makes_the_status_stale_everywhere(tmp_path):
    ws, ids = published_workspace(tmp_path)
    client = client_for(ws)
    assert screening_currentness(ws).status is GenerationStatus.CURRENT
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "CURRENT"

    change_after_publish(ws, ids["included"])

    result = screening_currentness(ws)
    assert (result.status, result.code) == (GenerationStatus.STALE, GENERATION_STALE)
    status = client.get("/api/v1/ui/publication-status").json()
    assert (status["status"], status["code"]) == ("STALE", GENERATION_STALE)
    assert status["details"]["changed"] == 1
    for path in (f"{BASE}/methods", f"{BASE}/export?format=csv&set=included"):
        response = client.get(path)
        assert (response.status_code, response.json()["detail"]["code"]) == (409, GENERATION_STALE), path


def test_an_unchanged_publication_stays_current(tmp_path):
    ws, _ids = published_workspace(tmp_path)
    assert screening_currentness(ws).status is GenerationStatus.CURRENT
