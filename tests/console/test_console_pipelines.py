"""Hermetic tests for the M5.2 read observability surface.

Covers the synthesis/phase4 indexes, safe file serving, the harvest corpus
browser, the graph asset as HTML, and the global change-tick SSE primitive.
No network or kit CLIs involved.
"""

from __future__ import annotations

import asyncio
import json
import os

from fastapi.testclient import TestClient

from scholar_harness.console import create_app


def _bootstrap(tmp):
    ws = tmp / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "synthesis").mkdir(parents=True)
    (ws / "phase4").mkdir(parents=True)
    (ws / "pdfs").mkdir(parents=True)
    (ws / "extracted").mkdir(parents=True)
    (ws / "audit").mkdir(parents=True)

    (ws / "synthesis" / "literature_review.md").write_text("# Review", encoding="utf-8")
    (ws / "synthesis" / "consensus.md").write_text("## Consensus", encoding="utf-8")
    (ws / "synthesis" / "claims_rq1.json").write_text('{"claims": []}', encoding="utf-8")
    (ws / "synthesis" / "rag_rq1_review.md").write_text("RQ1", encoding="utf-8")

    (ws / "phase4" / "trust_consensus.md").write_text("# Trust", encoding="utf-8")
    (ws / "phase4" / "coi_audit.md").write_text("# COI", encoding="utf-8")

    (ws / "pdfs" / "a.pdf").write_bytes(b"%PDF-1.4 test")
    (ws / "pdfs" / "b.pdf").write_bytes(b"%PDF-1.4 test")
    (ws / "extracted" / "a.md").write_text("fulltext a", encoding="utf-8")

    (ws / "literature" / "knowledge_graph.html").write_text("<html><body>graph</body></html>", encoding="utf-8")
    (ws / "INDEX.md").write_text("# INDEX", encoding="utf-8")
    (ws / "project.json").write_text(json.dumps({"title": "Test WS", "stats": {}}), encoding="utf-8")
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# synthesis / phase4 indexes and safe serving
# ---------------------------------------------------------------------------

def test_synthesis_index(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    body = client.get("/api/v1/synthesis").json()
    names = {f["name"] for f in body["files"]}
    assert names == {"literature_review.md", "consensus.md", "claims_rq1.json", "rag_rq1_review.md"}
    by_name = {f["name"]: f for f in body["files"]}
    assert by_name["consensus.md"]["kind"] == "consensus"
    assert by_name["consensus.md"]["is_markdown"] is True
    assert by_name["claims_rq1.json"]["kind"] == "other"
    assert by_name["rag_rq1_review.md"]["kind"] == "rq_review"
    assert by_name["rag_rq1_review.md"]["size_bytes"] > 0


def test_phase4_index(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    body = client.get("/api/v1/phase4").json()
    by_name = {f["name"]: f for f in body["files"]}
    assert by_name["trust_consensus.md"]["kind"] == "trust"
    assert by_name["coi_audit.md"]["kind"] == "coi"


def test_synthesis_and_phase4_file_content(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    assert client.get("/api/v1/synthesis/consensus.md").json()["content"] == "## Consensus"
    assert client.get("/api/v1/synthesis/nope.md").status_code == 404
    assert client.get("/api/v1/phase4/trust_consensus.md").json()["content"] == "# Trust"


def test_file_serving_rejects_traversal(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    for bad in (
        "/api/v1/synthesis/../project.json",
        "/api/v1/synthesis/..%2F..%2Fproject.json",
        "/api/v1/phase4/%2e%2e/project.json",
    ):
        assert client.get(bad).status_code in (400, 404), bad


# ---------------------------------------------------------------------------
# harvest corpus + graph asset
# ---------------------------------------------------------------------------

def test_harvest_corpus(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    body = client.get("/api/v1/harvest/corpus").json()
    assert body["pdf_count"] == 2
    assert body["extracted_count"] == 1
    assert {p["name"] for p in body["pdfs"]} == {"a.pdf", "b.pdf"}
    assert [e["name"] for e in body["extracted"]] == ["a.md"]
    assert all(p["size_bytes"] > 0 for p in body["pdfs"])


def test_assets_graph_serves_html(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/assets/graph")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/html; charset=utf-8"
    assert "<body>graph</body>" in r.text


def test_assets_graph_missing_404(tmp_path):
    ws = _bootstrap(tmp_path)
    (ws / "literature" / "knowledge_graph.html").unlink()
    client = TestClient(create_app(ws))
    assert client.get("/api/v1/assets/graph").status_code == 404


# ---------------------------------------------------------------------------
# change-tick SSE primitive (hermetic generator, bounded reads)
# ---------------------------------------------------------------------------

def test_tick_primitive_emits_initial_and_fires_on_change(tmp_path):
    from scholar_harness.console.api.streams import gen_ticks

    ws = _bootstrap(tmp_path)

    async def scenario():
        gen = gen_ticks(ws, interval=0.02)
        frames = []

        async def collect():
            async for frame in gen:
                frames.append(frame)
                if len(frames) >= 10:
                    break

        collector = asyncio.create_task(collect())

        # First frame is the initial tick.
        await asyncio.sleep(0.05)
        assert frames and "event: tick" in frames[0]

        # No change yet -> keepalives only.
        before = list(frames)
        await asyncio.sleep(0.07)
        assert all(": keepalive" in f for f in frames[len(before):])

        # Touch INDEX.md -> new tick must arrive.
        index = ws / "INDEX.md"
        os.utime(index, (index.stat().st_atime, index.stat().st_mtime + 2))
        await asyncio.sleep(0.1)
        changed = [f for f in frames if "event: tick" in f]
        assert len(changed) >= 2, frames

        collector.cancel()
        try:
            await collector
        except asyncio.CancelledError:
            pass
        return len(changed) >= 2

    assert asyncio.run(scenario())


def test_tick_heartbeat_falls_back_to_projectjson(tmp_path):
    from scholar_harness.console.api.streams import _heartbeat_mtime

    ws = _bootstrap(tmp_path)
    (ws / "INDEX.md").unlink()
    assert _heartbeat_mtime(ws) == (ws / "project.json").stat().st_mtime


def test_tick_sse_frame_shape():
    from scholar_harness.console.api.streams import _tick_sse

    frame = _tick_sse(1234.5, 3)
    assert frame == 'event: tick\ndata: {"ts": 1234.5, "n": 3}\n\n'
    assert _tick_sse(None, 0).startswith("event: tick\n")