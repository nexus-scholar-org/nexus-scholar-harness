"""An assistant reads a draft that has an Explore sample (M10c D2).

The pool and the pool-reading checks reach the assistant as the app holds
them, and the read records nothing (decision item 12). Hermetic: the recon
search seam replaces the providers.
"""

from __future__ import annotations

from pathlib import Path

from test_inception_proposals import (  # noqa: F401 - env is a fixture
    BASE,
    _create,
    env,
    uav_draft,
)
from test_recon_api import _probe

from scholar_harness import assistant
from scholar_harness.recon.session import ReconSessions


def _tree(root: Path) -> dict[str, int]:
    return {str(p.relative_to(root)): p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}


def test_reading_a_probed_draft_returns_its_sample_and_records_nothing(env, tmp_path):  # noqa: F811
    client, root = env
    sid = _create(client, uav_draft(concepts=[{"concept": "weed detection", "synonyms": []}]))["session_id"]
    _probe(client, sid)
    sessions = ReconSessions(root=tmp_path / "recon")
    before_root, before_recon = _tree(root), _tree(tmp_path / "recon")

    answer = assistant.read_draft(root, sid, sessions=sessions)

    pool = answer["pool"]
    assert pool["papers"] and all(p["title"] for p in pool["papers"])
    assert [leg["provider"] for leg in pool["legs"]] == list(pool["providers"])
    ids = {c["check_id"] for c in answer["checks"]["checks"]}
    waiting = {w["check_id"] for w in answer["checks"]["waiting"]}
    assert "CONCEPT_NOT_ANCHORED" not in waiting and "EXPLORE_POOL_THIN" not in waiting
    assert "CONCEPT_TERM_MISSING" in ids
    assert answer["proposals"] == []  # the read made no proposal, though a check recommends one
    assert _tree(root) == before_root and _tree(tmp_path / "recon") == before_recon
    # The app's own checks run then records the proposal; the assistant's read did not.
    client.post(f"{BASE}/drafts/{sid}/checks", json={})
    assert assistant.read_draft(root, sid, sessions=sessions)["proposals"]
