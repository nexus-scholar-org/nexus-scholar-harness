"""Hermetic tests for the M0.5 recon MCP surface (T5.1-T5.6).

Drives ``scholar_agent.server``'s ``recon_probe``/``recon_distill``/
``recon_delta`` tools with an injected fake ``search_fn`` (the same shape as
``tests/test_inception_grounded.py`` drives through ``ReconEngine``), so no
provider network is ever touched.  Every check goes through the tool
functions directly (they return JSON strings) and verifies the structured
contract: FAIR session state on disk under
``.cache/inception_recon/sessions/<id>/session.json`` (T5.4), content-
addressed ``pool_<sha>.json``/``distilled_<sha>.json`` artifacts, lineage
``cache_key`` fields (T5.5), the reason/confidence mapping (M0.4), and the
``workspaces/`` root refusal (case-insensitive part-match).
"""

import asyncio
import json
from pathlib import Path

import pytest
from scholar_agent import server
from scholar_search.models import Document, ExternalIds, Query

TOPIC = "drone crop disease detection"
THIN_TERM = "edge inference"


def _fake_doc(doi: str, title: str, abstract: str) -> Document:
    return Document(
        title=title,
        year=2023,
        provider="openalex",
        provider_id="W" + doi.replace("/", "").replace(":", "")[:20],
        external_ids=ExternalIds(doi=doi),
        abstract=abstract,
        citations_count=4,
        url=f"https://example.org/{doi}",
    )


def _topic_docs() -> list[Document]:
    """Three docs; two anchor the thin ``edge inference`` school (n<=2)."""
    return [
        _fake_doc(
            "10.1000/edge-a",
            "Edge Inference Disease Detection",
            "We run edge inference on embedded hardware.",
        ),
        _fake_doc(
            "10.1000/edge-b",
            "Real-Time Edge Inference in Orchards",
            "Edge inference detects crop disease with a small CNN.",
        ),
        _fake_doc(
            "10.1000/robot-c",
            "Field Survey Robots",
            "An inference pipeline for orchard robots using visible-light cameras.",
        ),
    ]


def _followup_docs() -> list[Document]:
    """Brand-new follow-up evidence for the thin-school term."""
    return [
        _fake_doc(
            "10.1000/fu-1",
            "Edge Inference Benchmarks",
            "Comparing edge inference frameworks for on-device vision.",
        ),
        _fake_doc(
            "10.1000/fu-2",
            "Edge Inference Acceleration",
            "Hardware acceleration for edge inference workloads.",
        ),
        _fake_doc(
            "10.1000/fu-3",
            "Embedded Inference Systems",
            "A system survey of embedded inference for field robots.",
        ),
    ]


def _topic_search_fn(query: Query, providers: list[str]) -> list[Document]:
    return _topic_docs()


def _explode_search(query: Query, providers: list[str]):
    raise AssertionError(
        "a provider probe must not run here; fake search_fn was set to explode"
    )


def _probe(monkeypatch, tmp_path, search_fn=_topic_search_fn) -> dict:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(server, "RECON_SEARCH_FN", search_fn)
    return json.loads(server.recon_probe(topic=TOPIC))


# ---------------------------------------------------------------------------
# T5.1/T5.6: tools are registered on the mcp instance
# ---------------------------------------------------------------------------


def test_three_recon_tools_registered_on_mcp():
    names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    assert {"recon_probe", "recon_distill", "recon_delta"} <= names
    # The 15 existing nexus_* tools are untouched.
    assert len(names) == 18
    assert "nexus_discover" in names


# ---------------------------------------------------------------------------
# T5.1: recon_probe -- machine-readable result + session.json on disk
# ---------------------------------------------------------------------------


def test_recon_probe_returns_structured_json_and_persists_session(tmp_path, monkeypatch):
    result = _probe(monkeypatch, tmp_path)

    assert result["status"] == "probe_ok"
    assert result["session_id"].startswith("rec_")
    assert result["cache_key"].startswith("v1/")
    assert result["n_docs"] == 3
    assert Path(result["pool_path"]).is_file()

    session_dir = (
        tmp_path / ".cache" / "inception_recon" / "sessions" / result["session_id"]
    )
    session_file = session_dir / "session.json"
    assert session_file.is_file()

    session = json.loads(session_file.read_text(encoding="utf-8"))
    assert session["session_id"] == result["session_id"]
    assert session["topic"] == TOPIC
    assert session["cache_keys"] == [result["cache_key"]]
    assert session["pools"] == [result["pool_path"]]
    assert session["created_at"]
    assert session["updated_at"]

    # Exactly one content-addressed pool artifact next to session.json.
    assert len(list(session_dir.glob("pool_*.json"))) == 1


def test_recon_probe_reuses_cache_within_session(tmp_path, monkeypatch):
    calls = []

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        return _topic_docs()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(server, "RECON_SEARCH_FN", search_fn)
    first = json.loads(server.recon_probe(topic=TOPIC))
    second = json.loads(
        server.recon_probe(topic=TOPIC, session_id=first["session_id"])
    )

    assert len(calls) == 1  # second probe was an engine cache hit, zero calls
    assert second["session_id"] == first["session_id"]
    assert second["cache_key"] == first["cache_key"]
    assert second["pool_path"] == first["pool_path"]
    assert second["n_docs"] == first["n_docs"]


# ---------------------------------------------------------------------------
# T5.2: recon_distill -- terms file + structured summaries
# ---------------------------------------------------------------------------


def test_recon_distill_returns_terms_file_and_anchored_schools(tmp_path, monkeypatch):
    probe = _probe(monkeypatch, tmp_path)
    result = json.loads(server.recon_distill(session_id=probe["session_id"]))

    assert result["session_id"] == probe["session_id"]
    assert result["cache_key"] == probe["cache_key"]
    assert Path(result["terms_path"]).is_file()

    terms = json.loads(Path(result["terms_path"]).read_text(encoding="utf-8"))
    assert terms["cache_key"] == probe["cache_key"]
    assert terms["micro_taxonomy"]
    assert isinstance(result["metrics"], list)
    assert isinstance(result["datasets"], list)
    assert result["micro_taxonomy_top"]
    assert result["micro_taxonomy_top"][0]["anchor_dois"]

    # The thin school is surfaced with its anchor DOIs (DoD M0.5.2).
    schools = {school["label"]: school for school in result["schools"]}
    assert THIN_TERM in schools
    assert schools[THIN_TERM]["n"] == 2
    assert set(schools[THIN_TERM]["anchor_dois"]) == {"10.1000/edge-a", "10.1000/edge-b"}


# ---------------------------------------------------------------------------
# T5.4: session survives across copilot turns on disk -- no re-probe
# ---------------------------------------------------------------------------


def test_recon_distill_after_probe_uses_persisted_session(tmp_path, monkeypatch):
    probe = _probe(monkeypatch, tmp_path)

    # "Turn 2": recon_distill must work purely from session.json on disk.
    # A search fn that explodes proves no re-probe happens on this turn.
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _explode_search)
    result = json.loads(server.recon_distill(session_id=probe["session_id"]))

    assert result["cache_key"] == probe["cache_key"]
    assert Path(result["terms_path"]).is_file()

    session = json.loads(
        (
            tmp_path
            / ".cache"
            / "inception_recon"
            / "sessions"
            / probe["session_id"]
            / "session.json"
        ).read_text(encoding="utf-8")
    )
    assert session["session_id"] == probe["session_id"]


# ---------------------------------------------------------------------------
# T5.3: recon_delta -- thin-school trigger, reason+confidence, merged lineage
# ---------------------------------------------------------------------------


def test_recon_delta_thin_school_trigger_with_reason_and_confidence(tmp_path, monkeypatch):
    calls = []
    mapping = {
        TOPIC.casefold(): _topic_docs(),
        THIN_TERM: _followup_docs(),
    }

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        return mapping.get(query.text.strip().casefold(), [])

    probe = _probe(monkeypatch, tmp_path, search_fn=search_fn)
    assert len(calls) == 1

    result = json.loads(server.recon_delta(session_id=probe["session_id"]))

    assert result["session_id"] == probe["session_id"]
    assert result.get("status") != "error"

    # The thin school was followed up: max 3 probes, cache-reused.
    assert [c for c in calls] == [TOPIC, THIN_TERM]
    assert len(result["followups"]) == 1
    followup = result["followups"][0]
    assert followup["term"] == THIN_TERM
    # M0.4 reason surfaced VERBATIM under both conventions.
    assert followup["reason"] == "2 direct hits, 1 adjacent"
    assert followup["confidence"] == {
        "label": "gap",
        "detail": "2 direct hits, 1 adjacent",
    }
    assert followup["school_n"] == 2

    # T5.5 delta lineage: base pool key first, then the follow-up probe key.
    assert result["merged_cache_keys"][0] == probe["cache_key"]
    assert len(result["merged_cache_keys"]) == 2
    assert result["merged_cache_keys"][1].startswith("v1/")
    assert result["merged_cache_keys"][1] != probe["cache_key"]

    # Merge semantics: 3 originals + 3 follow-up docs, cap 25 held.
    assert result["pool_size_before"] == 3
    assert result["pool_size_after"] == 6
    assert result["pool_size_after"] <= 25
    assert result["dropped_n"] == 0
    assert Path(result["pool_path"]).is_file()
    assert Path(result["terms_path"]).is_file()

    merged_pool = json.loads(Path(result["pool_path"]).read_text(encoding="utf-8"))
    assert len(merged_pool["docs"]) == 6
    assert merged_pool["cache_key"] == probe["cache_key"]
    assert merged_pool["merged_from_cache_keys"] == [result["merged_cache_keys"][1]]

    # Session lineage grew on disk.
    session = json.loads(
        (
            tmp_path
            / ".cache"
            / "inception_recon"
            / "sessions"
            / probe["session_id"]
            / "session.json"
        ).read_text(encoding="utf-8")
    )
    assert session["cache_keys"] == result["merged_cache_keys"]
    assert len(session["pools"]) == 2


def test_recon_delta_no_thin_school_is_cheap(tmp_path, monkeypatch):
    def search_fn(query: Query, providers: list[str]):
        return [
            _fake_doc(
                f"10.1000/drone-{i:02d}",
                f"Orchard Survey {i}",
                "We counted trees using fixed-wing drones over large orchards.",
            )
            for i in range(5)
        ]

    probe = _probe(monkeypatch, tmp_path, search_fn=search_fn)
    result = json.loads(server.recon_delta(session_id=probe["session_id"]))

    assert result["followups"] == []
    assert result["merged_cache_keys"] == [probe["cache_key"]]
    assert result["pool_size_before"] == result["pool_size_after"] == 5
    assert result["dropped_n"] == 0


# ---------------------------------------------------------------------------
# Hygiene: workspaces/ root refusal (case-insensitive) + structured errors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dir_name", ["Workspaces", "workspaces", "WORKSPACES"])
def test_recon_probe_refuses_sessions_under_workspaces(tmp_path, monkeypatch, dir_name):
    ws_root = tmp_path / dir_name
    ws_root.mkdir()
    monkeypatch.chdir(ws_root)
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _explode_search)

    result = json.loads(server.recon_probe(topic="anything"))

    assert result["status"] == "error"
    assert "workspaces" in result["message"].casefold()
    assert "cache_key" in result
    # Nothing was ever written into the workspaces root.
    assert not (ws_root / ".cache").exists()


def test_invalid_session_id_returns_structured_error(monkeypatch):
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _explode_search)

    probe = json.loads(server.recon_probe(topic="x", session_id="../../evil"))
    assert probe["status"] == "error"
    assert "session" in probe["message"].casefold()
    assert "cache_key" in probe

    dist = json.loads(server.recon_distill(session_id="not-a-rec-session"))
    assert dist["status"] == "error"
    assert dist["message"]
    assert dist["cache_key"] is None


# ---------------------------------------------------------------------------
# T5.5: every successful result carries its lineage cache_key
# ---------------------------------------------------------------------------


def test_every_result_has_cache_key_lineage(tmp_path, monkeypatch):
    probe = _probe(monkeypatch, tmp_path)
    assert "cache_key" in probe and probe["cache_key"].startswith("v1/")

    dist = json.loads(server.recon_distill(session_id=probe["session_id"]))
    assert "cache_key" in dist and dist["cache_key"] == probe["cache_key"]

    delta = json.loads(server.recon_delta(session_id=probe["session_id"]))
    assert "merged_cache_keys" in delta
    assert delta["merged_cache_keys"] and delta["merged_cache_keys"][0] == probe["cache_key"]