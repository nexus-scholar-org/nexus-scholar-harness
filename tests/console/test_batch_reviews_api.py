"""``GET /ui/batches/review``: every batch's review state in one request (H-screening-read-performance).

The Publish screen asked ``/ui/batch/{n}/review`` once per batch; the new route
answers what those requests answer, in the order of ``/ui/batches``.
"""

from __future__ import annotations

from test_export_api import BASE, client_for, published_workspace


def _two_batches(tmp_path):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "_br_events_helpers", Path(__file__).resolve().parents[1] / "test_screening_events.py"
    )
    se = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(se)
    return se._two_batch_workspace(tmp_path)


def test_one_request_answers_what_the_per_batch_requests_answer(tmp_path):
    ws = _two_batches(tmp_path)
    client = client_for(ws)
    batches = client.get(f"{BASE}/ui/batches").json()["batches"]
    assert len(batches) == 2
    body = client.get(f"{BASE}/ui/batches/review").json()
    assert body["shape"] == "ui07.batch-reviews-v1"
    assert body["count"] == 2
    expected = [client.get(f"{BASE}/ui/batch/{b['batch_index']}/review").json() for b in batches]
    assert body["reviews"] == expected


def test_a_published_workspace_reviews_match_too(tmp_path):
    ws, _ids = published_workspace(tmp_path)
    client = client_for(ws)
    body = client.get(f"{BASE}/ui/batches/review").json()
    singles = [
        client.get(f"{BASE}/ui/batch/{b['batch_index']}/review").json()
        for b in client.get(f"{BASE}/ui/batches").json()["batches"]
    ]
    assert body["reviews"] == singles and singles


def test_the_reviews_follow_the_batch_list_and_a_refused_batch_carries_its_refusal(tmp_path, monkeypatch):
    from fastapi import HTTPException

    from scholar_harness.console.api import screening as api

    ws = _two_batches(tmp_path)
    (ws / "literature" / "screening" / "batch_002.json").unlink()  # the batch list leaves it out
    client = client_for(ws)
    listed = [b["batch_index"] for b in client.get(f"{BASE}/ui/batches").json()["batches"]]
    body = client.get(f"{BASE}/ui/batches/review").json()
    assert [r["batch_index"] for r in body["reviews"]] == listed

    real = api._ui07_batch_review

    def refuse_one(ws_, n):
        if n == listed[0]:
            raise HTTPException(status_code=500, detail={"code": "UNPARSEABLE_JSON", "message": "m", "details": {}})
        return real(ws_, n)

    monkeypatch.setattr(api, "_ui07_batch_review", refuse_one)
    body = client.get(f"{BASE}/ui/batches/review").json()
    assert body["reviews"][0] == {
        "batch_index": listed[0], "status": 500,
        "detail": {"code": "UNPARSEABLE_JSON", "message": "m", "details": {}},
    }


def test_no_prepared_batches_answer_an_empty_list(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    body = client_for(ws).get(f"{BASE}/ui/batches/review").json()
    assert body == {"shape": "ui07.batch-reviews-v1", "count": 0, "reviews": []}
