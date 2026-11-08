"""M3a-discovery D5 / CORE-10: the DOI bridge never merges two studies.

A verifier may return a record that lost its workspace id and carries another
record's DOI. Restoring the id through the DOI bridge would then give two rows
the same id and one study would vanish. The bridge refuses instead
(``VERIFICATION_IDENTITY_BRIDGE_CONFLICT``) and quarantines the row.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path

from scholar_search.models import Document, ExternalIds

from scholar_harness.pipeline import verification as ver_mod
from scholar_harness.verification_identity import (
    QUARANTINE_FILENAME,
    VERIFICATION_IDENTITY_BRIDGE_CONFLICT,
)


def _docs():
    a = Document(title="Alpha study of widgets", year=2020, provider="openalex",
                 external_ids=ExternalIds(doi=None))
    a.workspace_id = "SCI-000001"
    b = Document(title="Beta analysis of gadgets", year=2021, provider="crossref",
                 external_ids=ExternalIds(doi="10.1/b"))
    b.workspace_id = "SCI-000002"
    return [a, b]


class _BorrowingVerifier:
    """Returns A without its id and with B's DOI; B unchanged."""

    async def process_batch(self, docs, verify=True, enrich=True):
        a, b = docs
        a2 = replace(a, external_ids=ExternalIds(doi="10.1/b"))
        a2.workspace_id = None
        return [a2, b], []


def _run(tmp_path: Path, monkeypatch, verifier=_BorrowingVerifier, reverse=False):
    monkeypatch.setattr(ver_mod, "DocumentVerifier", verifier)
    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    (ws / "project.json").write_text(json.dumps({"project_id": "ws", "stats": {}}), encoding="utf-8")
    return ws, asyncio.run(
        ver_mod.run_verification(documents=_docs()[::-1] if reverse else _docs(), literature_dir=ws / "literature", workspace_dir=ws)
    )


def test_bridge_refuses_an_id_already_claimed_in_the_batch(tmp_path, monkeypatch):
    ws, outcome = _run(tmp_path, monkeypatch)
    ids = [d.workspace_id for d in outcome.documents]
    assert len(ids) == len(set(ids)), ids
    assert outcome.refused == 1
    assert outcome.refusal_reasons == {VERIFICATION_IDENTITY_BRIDGE_CONFLICT: 1}
    quarantined = json.loads((ws / "literature" / QUARANTINE_FILENAME).read_text(encoding="utf-8"))
    assert quarantined[0]["code"] == VERIFICATION_IDENTITY_BRIDGE_CONFLICT
    assert "SCI-000002" in quarantined[0]["reason"]


def test_bridge_conflict_does_not_depend_on_order(tmp_path, monkeypatch):
    class _Reversed:
        """Input is [B, A]: the borrowing row now comes after the holder."""

        async def process_batch(self, docs, verify=True, enrich=True):
            b, a = docs
            a2 = replace(a, external_ids=ExternalIds(doi="10.1/b"))
            a2.workspace_id = None
            return [b, a2], []

    _, outcome = _run(tmp_path, monkeypatch, _Reversed, reverse=True)
    assert sorted(d.workspace_id for d in outcome.documents) == ["SCI-000002"]
    assert outcome.refused == 1
