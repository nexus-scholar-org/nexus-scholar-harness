"""Focused HCM-04b tests for the neutral discovery stage.

Stage 1 (protocol-query compile -> search -> raw-result publication) lives in
``scholar_harness.pipeline.discovery``; the orchestrator delegates. Every test
is hermetic (``tmp_path`` only, faked engine, real protocol compiler) and
asserts: byte-identical raw files, identical provider resolution, preserved
overrides/edge cases, exactly one canonical ``DISCOVERY_SEARCH`` audit event
(T-TRUTH-COUNTS-01), no registry writes, and an honest status (an empty or
degraded harvest is never reported as ``SUCCESS``).
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import coordinator as coord_mod
from scholar_harness.pipeline import discovery as disc


def _write_protocol(ws: Path, slug: str = "discovery-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "discovery-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Discovery Stage Parity",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "What is the pipeline throughput?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark",
            }
        ],
        "core_concepts": [{"concept": "Pipeline", "synonyms": ["orchestrator"]}],
        "inclusion_criteria": [
            {"criterion": "Reports benchmark pass rates", "maps_to_rqs": ["RQ1"]}
        ],
        "exclusion_criteria": [
            {
                "criterion": "Non-English",
                "reason_category": "LANGUAGE",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "matrix_dimensions": [
            {
                "id": "throughput",
                "name": "Throughput",
                "description": "Operations per second",
            }
        ],
    }
    intent = IntentPacket.model_validate(data)
    proto = json.loads(canonical_json(compile_protocol(intent)).decode("utf-8"))
    p = ws / "protocol.json"
    p.write_text(json.dumps(proto), encoding="utf-8")
    return p


SEEN_QUERIES: list[tuple[object, bool]] = []
ENGINE_INSTANCES: list[object] = []


def _make_docs():
    from scholar_search.models import Document, ExternalIds

    return [
        Document(
            title="First Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="First abstract.",
        ),
        Document(
            title="Second Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Second abstract.",
        ),
    ]


class _FakeEngine:
    def __init__(self, providers=None):
        self.providers = providers
        self.closed = False
        ENGINE_INSTANCES.append(self)

    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        return list(_make_docs())

    async def close(self):
        self.closed = True


class _EmptyEngine(_FakeEngine):
    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        return []


class _FailingEngine(_FakeEngine):
    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        raise RuntimeError("provider boom")

    async def close(self):  # pragma: no cover - close is never reached
        self.closed = True


class _GoodProvider:
    """A provider that yields documents (like the kit's real providers)."""

    name = "openalex"

    async def search(self, query):
        for doc in _make_docs():
            yield doc


class _BadProvider:
    """A provider that raises -- the kit swallows it, the harness must not."""

    name = "crossref"

    async def search(self, query):
        raise RuntimeError("crossref exploded")
        yield  # pragma: no cover - unreachable, keeps this an async generator


class _MixedEngine:
    """Mimics the kit's engine: per-provider failures are caught and skipped."""

    def __init__(self, providers=None):
        self.providers = [_GoodProvider(), _BadProvider()]
        self.closed = False

    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        results = []
        for provider in self.providers:
            try:
                async for doc in provider.search(query):
                    results.append(doc)
            except Exception:  # noqa: BLE001 - the kit's swallow behavior
                continue
        return results

    async def close(self):
        self.closed = True


class _AllFailEngine:
    """Every provider fails: the harvest produced nothing and broke."""

    def __init__(self, providers=None):
        self.providers = [_BadProvider()]
        self.closed = False

    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        results = []
        for provider in self.providers:
            try:
                async for doc in provider.search(query):
                    results.append(doc)
            except Exception:  # noqa: BLE001 - the kit's swallow behavior
                continue
        return results

    async def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_captures():
    SEEN_QUERIES.clear()
    ENGINE_INSTANCES.clear()
    yield
    SEEN_QUERIES.clear()
    ENGINE_INSTANCES.clear()


def _golden_text(docs) -> str:
    return json.dumps(
        [asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in docs],
        indent=2,
        default=str,
    )


def _stub_screening_prepare(monkeypatch):
    # Mirror tests/pipeline/test_orchestrator_fidelity.py: Stage 4's real
    # batch preparation refuses without an accepted corpus snapshot, which is
    # downstream of discovery and out of scope here.
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def test_raw_files_are_byte_identical_and_match_golden(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)
    lit = ws / "literature"

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.count == 2
    assert len(outcome.documents) == 2
    raw_bytes = (lit / "raw_search.json").read_bytes()
    combined_bytes = (lit / "all_raw_search.json").read_bytes()
    assert raw_bytes == combined_bytes
    # Text-mode read reverses the platform newline translation that
    # Path.write_text applies on write (verbatim orchestrator behavior);
    # the content must equal the golden serialization exactly.
    assert (lit / "raw_search.json").read_text(encoding="utf-8") == _golden_text(
        outcome.documents
    )
    # The fake engine saw the verbatim call shape and was closed.
    assert SEEN_QUERIES and SEEN_QUERIES[-1][1] is False
    assert ENGINE_INSTANCES and ENGINE_INSTANCES[-1].closed is True


def test_orchestrator_path_matches_direct_stage_bytes(tmp_path, monkeypatch):
    # Legacy seam: the orchestrator delegates, and the stage honors the
    # pipeline-namespace fake engine.
    monkeypatch.setattr(disc, "SearchEngine", _EmptyEngine)
    _stub_screening_prepare(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["stages"]["discovery"] == 0
    orch_bytes = (ws / "literature" / "raw_search.json").read_bytes()
    assert orch_bytes == (ws / "literature" / "all_raw_search.json").read_bytes()
    assert (ws / "literature" / "raw_search.json").read_text(
        encoding="utf-8"
    ) == _golden_text([])

    direct_lit = tmp_path / "direct" / "literature"
    outcome = asyncio.run(
        disc.run_discovery(
            protocol_path=ws / "protocol.json", literature_dir=direct_lit
        )
    )
    assert outcome.count == 0
    assert (direct_lit / "raw_search.json").read_bytes() == orch_bytes


def test_provider_resolution_identical_via_shim():
    assert orch._resolve_providers is disc._resolve_providers
    assert orch._PROVIDER_MAP is disc._PROVIDER_MAP

    from scholar_search.providers import OpenAlexProvider, SemanticScholarProvider

    resolved = disc._resolve_providers(["openalex", "crossref"])
    assert len(resolved) == 2
    assert isinstance(resolved[0], OpenAlexProvider)
    # Unknown names are dropped (warning, not failure).
    assert disc._resolve_providers(["openalex", "not-a-provider"]) is not None
    assert disc._resolve_providers(["not-a-provider"]) is None
    assert disc._resolve_providers([]) is None
    assert disc._resolve_providers(None) is None
    # Normalization is verbatim: case/space/dash variants resolve.
    normalized = disc._resolve_providers(["Semantic Scholar", "semantic-scholar"])
    assert len(normalized) == 2
    assert all(isinstance(p, SemanticScholarProvider) for p in normalized)
    # Existing instances pass through untouched.
    existing = OpenAlexProvider()
    mixed = disc._resolve_providers([existing, "crossref"])
    assert mixed[0] is existing


def test_max_search_results_override(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)

    asyncio.run(
        disc.run_discovery(
            protocol_path=proto,
            literature_dir=ws / "lit-a",
            max_search_results=7,
        )
    )
    assert SEEN_QUERIES[-1][0].max_results == 7

    SEEN_QUERIES.clear()
    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "lit-b"))
    from scholar_search.protocol_adapter import compile_protocol_search

    default_query, _ = compile_protocol_search(proto)
    assert SEEN_QUERIES[-1][0].max_results == default_query.max_results

    # Falsy overrides preserve the original `if max_search_results:` semantics.
    SEEN_QUERIES.clear()
    asyncio.run(
        disc.run_discovery(
            protocol_path=proto, literature_dir=ws / "lit-c", max_search_results=0
        )
    )
    assert SEEN_QUERIES[-1][0].max_results == default_query.max_results


def test_empty_results_preserve_count_and_files(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _EmptyEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)
    lit = ws / "literature"

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.count == 0
    assert outcome.documents == []
    assert (lit / "raw_search.json").read_text(encoding="utf-8") == _golden_text([])
    assert (lit / "all_raw_search.json").read_text(encoding="utf-8") == _golden_text([])


def test_stage_emits_one_canonical_discovery_event_and_no_registry_writes(
    tmp_path, monkeypatch
):
    """AC-5: the stage publishes exactly one canonical DISCOVERY_SEARCH event.

    The event is written through ``scholar_harness.workspace.audit`` (the sole
    owner of the append-only journal discipline) -- never by hand-appending a
    line to ``journal.jsonl``.
    """
    calls: list[dict] = []
    import scholar_harness.pipeline.discovery as disc_mod

    real_append = disc_mod.append_event

    def _spy(workspace, action, description, **kwargs):
        calls.append({"workspace": workspace, "action": action, **kwargs})
        return real_append(workspace, action, description, **kwargs)

    monkeypatch.setattr(disc_mod, "append_event", _spy)
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(ws)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature")
    )

    # The canonical writer was used (no hand-append).
    assert len(calls) == 1
    assert calls[0]["action"] == "DISCOVERY_SEARCH"

    journal = ws / "audit" / "journal.jsonl"
    lines = [
        line
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["action"] == "DISCOVERY_SEARCH"
    assert event["event_id"].startswith("EVT-")
    assert event["agent_or_tool"] == "scholar-harness"
    assert event["inputs"], "the event must name its inputs"
    assert any("protocol.json" in item for item in event["inputs"])
    assert any("raw_search.json" in item for item in event["outputs"])
    assert event["metrics"]["raw_hits"] == outcome.count == 2
    assert event["status"] == "SUCCESS"
    # m3: the provenance method is recorded (COMPASS section 3).
    assert event["parameters"]["method"] == "EXTERNAL_PROVIDER"
    # The audit outcome is explicit on the outcome object.
    assert outcome.audit_status == "WRITTEN"
    assert outcome.audit_workspace
    assert outcome.audit_reason

    # No registry/acceptance state is written by the stage.
    assert list(ws.rglob("artifact_registry.json")) == []


def test_discovery_status_is_never_success_for_an_empty_result(tmp_path, monkeypatch):
    """N-7 / AC-6: a zero-result harvest is never reported as SUCCESS."""
    monkeypatch.setattr(disc, "SearchEngine", _EmptyEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(ws)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature")
    )

    assert outcome.count == 0
    assert outcome.status != "SUCCESS"
    assert outcome.status == "EMPTY_RESULT"
    assert outcome.reason, "a non-success outcome must carry a reason"

    event = json.loads(
        [
            line
            for line in (ws / "audit" / "journal.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ][0]
    )
    assert event["status"] != "SUCCESS"
    assert event["status"] == "EMPTY_RESULT"
    assert event["metrics"]["raw_hits"] == 0


def test_discovery_reports_partial_when_a_provider_fails(tmp_path, monkeypatch):
    """N-6 / AC-6: a failing provider degrades the run to PARTIAL."""
    monkeypatch.setattr(disc, "SearchEngine", _MixedEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(ws)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature")
    )

    assert outcome.count == 2
    assert outcome.status == "PARTIAL"
    assert "crossref" in outcome.reason
    assert outcome.providers_failed == ("crossref",)
    assert outcome.provider_errors["crossref"]

    event = json.loads(
        [
            line
            for line in (ws / "audit" / "journal.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ][0]
    )
    assert event["status"] == "PARTIAL"
    assert event["metrics"]["providers_failed"] == 1
    assert event["metrics"]["failed_providers"] == ["crossref"]
    assert event["metrics"]["raw_hits"] == 2


def test_discovery_docstring_states_the_actual_provider_behavior():
    """AC-7: the docstring must not claim the kit propagates provider errors."""
    source = Path(disc.__file__).read_text(encoding="utf-8")
    assert "Provider failure propagates" not in source
    assert "does **not** propagate" in source or "does not propagate" in source
    assert "swallow" in source.lower()
    # The module no longer claims to emit no audit event.
    assert "emits **no** audit event" not in source


def test_stage_writes_no_registry_state(tmp_path, monkeypatch):
    """The stage writes no registry/acceptance state, and a missing owning
    workspace is an EXPLICIT outcome, never a silent skip (T-TRUTH-COUNTS-01).

    This test proves the intended property (not "no workspace happened to be
    found"): the outcome states that no audit event was written and why, and
    no ledger is created anywhere in the tree.
    """
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=ws / "lit")
    )

    # No registry/acceptance state is ever written by the stage.
    assert list(ws.rglob("artifact_registry.json")) == []
    # The missing owning workspace is reported explicitly.
    assert outcome.audit_status == "NOT_WRITTEN"
    assert outcome.audit_reason
    assert outcome.audit_workspace == ""
    # ... and no ledger was created anywhere (not in the workspace, not next
    # to the literature directory).
    assert not (ws / "audit").exists()
    assert not (ws / "lit" / "audit").exists()
    assert not (ws / "literature" / "audit").exists()
    assert list(ws.rglob("journal.jsonl")) == []
    written = sorted(p.name for p in (ws / "lit").iterdir())
    assert written == ["all_raw_search.json", "raw_search.json"]


def test_nested_workspace_never_writes_into_an_unrelated_parents_ledger(
    tmp_path, monkeypatch
):
    """M2: a nested workspace without its own ``project.json`` must not have
    its discovery row appended to an unrelated parent project's ledger."""
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    parent = tmp_path / "parent"
    parent.mkdir()
    (parent / "project.json").write_text(
        json.dumps({"project_id": "parent", "title": "P", "stats": {}}),
        encoding="utf-8",
    )
    nested = parent / "nested"
    nested.mkdir()
    proto = _write_protocol(nested)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=nested / "literature")
    )

    assert outcome.audit_status == "NOT_WRITTEN"
    assert outcome.audit_reason
    # The parent's ledger is untouched: no fabricated history in another
    # project.
    parent_journal = parent / "audit" / "journal.jsonl"
    assert not parent_journal.exists()
    assert list(parent.rglob("journal.jsonl")) == []


def test_failed_harvest_publishes_no_authoritative_corpus_artifact(
    tmp_path, monkeypatch
):
    """M1 / COMPASS section 7: a failed harvest publishes no corpus artifact."""
    monkeypatch.setattr(disc, "SearchEngine", _AllFailEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(ws)
    lit = ws / "literature"

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.status == "FAILED"
    assert outcome.count == 0
    assert outcome.published is False
    assert not (lit / "raw_search.json").exists()
    assert not (lit / "all_raw_search.json").exists()

    event = json.loads(
        [
            line
            for line in (ws / "audit" / "journal.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ][0]
    )
    assert event["status"] == "FAILED"
    assert event["metrics"]["corpus_published"] is False
    assert event["outputs"] == []


def test_stage_1_region_has_no_direct_kit_use():
    # HCM-04l: glue moved to the neutral coordinator; the region now lives
    # in coordinator.py (orchestrator delegates). Same no-inline-kit guard.
    source = Path(coord_mod.__file__).read_text(encoding="utf-8")
    stage1 = source.split("Stage 1: Protocol Query Compilation & Search", 1)[1]
    stage1 = stage1.split("Stage 2:", 1)[0]
    assert "SearchEngine" not in stage1
    assert "compile_protocol_search" not in stage1
    assert "run_discovery" in stage1


def test_missing_protocol_raises_before_engine_or_files(tmp_path, monkeypatch):
    constructed: list[bool] = []

    class _SpyEngine(_FakeEngine):
        def __init__(self, providers=None):
            constructed.append(True)
            super().__init__(providers)

    monkeypatch.setattr(disc, "SearchEngine", _SpyEngine)
    lit = tmp_path / "lit"

    with pytest.raises(FileNotFoundError):
        asyncio.run(
            disc.run_discovery(
                protocol_path=tmp_path / "no-such-protocol.json",
                literature_dir=lit,
            )
        )

    assert constructed == []
    assert not lit.exists()


def test_provider_failure_propagates_without_empty_success(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FailingEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)
    lit = ws / "literature"

    with pytest.raises(RuntimeError, match="provider boom"):
        asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    # Failure closes over nothing: no fabricated raw files survive.
    assert not (lit / "raw_search.json").exists()
    assert not (lit / "all_raw_search.json").exists()
    assert ENGINE_INSTANCES and ENGINE_INSTANCES[-1].closed is False


def test_invalid_protocol_fails_without_fabricated_files(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    bad = ws / "protocol.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    lit = ws / "literature"

    with pytest.raises(Exception):
        asyncio.run(disc.run_discovery(protocol_path=bad, literature_dir=lit))

    assert not (lit / "raw_search.json").exists()
    assert not (lit / "all_raw_search.json").exists()


def test_mock_mode_signature_and_behavior_unchanged(tmp_path, monkeypatch):
    sig = inspect.signature(orch.ResearchOrchestrator.run_pipeline_async)
    assert "mock_mode" in sig.parameters
    assert sig.parameters["mock_mode"].default is False

    # mock_mode is accepted but unused: identical outcomes either way.
    monkeypatch.setattr(disc, "SearchEngine", _EmptyEngine)
    _stub_screening_prepare(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    plain = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert plain["stages"]["discovery"] == 0
    first = (ws / "literature" / "raw_search.json").read_bytes()

    flagged = asyncio.run(
        orch.ResearchOrchestrator(ws).run_pipeline_async(mock_mode=True)
    )
    assert flagged["stages"]["discovery"] == 0
    assert (ws / "literature" / "raw_search.json").read_bytes() == first


def test_transitional_seam_removed(tmp_path, monkeypatch):
    """HCM-04m tripwire (SEAM-01): no sentinel/resolver; old patch inert."""

    assert not hasattr(disc, "_REAL_SEARCH_ENGINE")
    assert not hasattr(disc, "_search_engine_class")
    text = Path(disc.__file__).read_text(encoding="utf-8")
    assert "_REAL_SEARCH_ENGINE" not in text
    assert "_search_engine_class" not in text
    assert "orchestrator.__dict__" not in text
    assert not hasattr(orch, "SearchEngine")

    class _BoomEngine:
        def __init__(self, *a, **k):
            raise AssertionError("orchestrator-namespace fake must be inert")

    monkeypatch.setattr(disc, "SearchEngine", _EmptyEngine)
    monkeypatch.setattr(orch, "SearchEngine", _BoomEngine, raising=False)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=ws / "lit")
    )
    assert outcome.count == 0


# ---------------------------------------------------------------------------
# T-TRUTH-COUNTS-01 (final narrow repair): owner resolution, stale artifacts,
# proxy delegation
# ---------------------------------------------------------------------------


def test_relative_literature_dir_still_writes_the_canonical_row(tmp_path, monkeypatch):
    """F-3: a relative ``literature_dir`` must not lose the discovery row.

    Before the repair the owner was resolved from the *unresolved* literature
    path (``Path(".")/..``) while the protocol was resolved, so
    ``relative_to`` raised ``ValueError`` and a legitimate workspace with a
    ``project.json`` silently lost its ``DISCOVERY_SEARCH`` row.
    """
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(ws)

    # The harness is called from the workspace's parent directory with a
    # RELATIVE literature directory.
    monkeypatch.chdir(tmp_path)
    outcome = asyncio.run(
        disc.run_discovery(
            protocol_path=proto, literature_dir=os.path.join("ws", "literature")
        )
    )

    assert outcome.audit_status == "WRITTEN", outcome.audit_reason
    assert Path(outcome.audit_workspace) == ws.resolve()
    journal = ws / "audit" / "journal.jsonl"
    rows = [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [r["action"] for r in rows] == ["DISCOVERY_SEARCH"]
    assert rows[0]["status"] == "SUCCESS"


def test_protocol_outside_the_owning_workspace_is_an_explicit_outcome(
    tmp_path, monkeypatch
):
    """F-4: a protocol outside the owning workspace is never a silent loss.

    The literature owner is a real workspace, but the protocol lives
    elsewhere: the owner cannot vouch for the harvest, so no row is written
    -- and the outcome says so explicitly (``NOT_WRITTEN`` + a reason).
    """
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    external = tmp_path / "external"
    external.mkdir()
    (external / "project.json").write_text(
        json.dumps({"project_id": "ext", "title": "E", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(external)

    outcome = asyncio.run(
        disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature")
    )

    assert outcome.audit_status == "NOT_WRITTEN"
    assert outcome.audit_reason
    assert outcome.audit_workspace == ""
    # No ledger was polluted (neither the owner nor the protocol's project).
    assert not (ws / "audit" / "journal.jsonl").exists()
    assert not (external / "audit" / "journal.jsonl").exists()


def test_literature_dir_without_a_manifest_falls_back_to_the_protocol_workspace(
    tmp_path, monkeypatch
):
    """F-4 (owner fallback): the protocol's own workspace owns the row.

    The literature directory has no ``project.json`` of its own, but the
    protocol lives in a real workspace -- that workspace authorised the
    harvest, so it owns the canonical row (never an unrelated ancestor).
    """
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    owner = tmp_path / "owner"
    owner.mkdir()
    (owner / "project.json").write_text(
        json.dumps({"project_id": "owner", "title": "O", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(owner)
    lit = tmp_path / "unmanaged" / "literature"

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.audit_status == "WRITTEN", outcome.audit_reason
    assert Path(outcome.audit_workspace) == owner.resolve()
    rows = [
        json.loads(line)
        for line in (owner / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert [r["action"] for r in rows] == ["DISCOVERY_SEARCH"]


def test_failed_harvest_reports_pre_existing_artifacts_instead_of_deleting_them(
    tmp_path, monkeypatch
):
    """F-5: a failed harvest never deletes the artifacts of an earlier run.

    Deleting a researcher's data would destroy evidence, so the artifacts
    stay on disk -- but they must never be mistaken for this run's corpus:
    the outcome and the audit row name them explicitly.
    """
    monkeypatch.setattr(disc, "SearchEngine", _AllFailEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    proto = _write_protocol(ws)
    lit = ws / "literature"
    lit.mkdir()
    earlier = '[{"title": "Earlier run"}]'
    (lit / "raw_search.json").write_text(earlier, encoding="utf-8")
    (lit / "all_raw_search.json").write_text(earlier, encoding="utf-8")

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.status == "FAILED"
    assert outcome.published is False
    # The earlier run's evidence is NOT deleted ...
    assert (lit / "raw_search.json").read_text(encoding="utf-8") == earlier
    assert (lit / "all_raw_search.json").read_text(encoding="utf-8") == earlier
    # ... but it is reported as stale, not as this run's corpus.
    assert outcome.stale_artifacts_present is True
    assert len(outcome.stale_artifacts) == 2
    assert all("raw_search.json" in item for item in outcome.stale_artifacts)

    event = json.loads(
        [
            line
            for line in (ws / "audit" / "journal.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ][0]
    )
    assert event["metrics"]["stale_artifacts_present"] is True
    assert event["parameters"]["stale_artifacts_present"] is True
    assert "NOT this run's corpus" in event["description"]


def test_observed_proxy_exposes_the_provider_client_for_the_engine_cleanup():
    """F-11: the proxy must delegate ``client``/``close`` to the provider.

    The kit's ``SearchEngine.close()`` calls ``hasattr(provider, "client")``
    on the *wrapped* provider; a regression in the proxy's delegation would
    break the real engine's cleanup with no test failing.
    """
    from scholar_search.engine import SearchEngine

    closed: list[str] = []

    class _Client:
        async def close(self):
            closed.append("client")

    class _Provider:
        name = "openalex"

        def __init__(self):
            self.client = _Client()

        async def close(self):
            closed.append("provider")

        async def search(self, query):
            if False:  # pragma: no cover - never iterated
                yield

    provider = _Provider()
    probe = disc._ProviderProbe()
    proxy = disc._ObservedProvider(provider, probe)

    # The proxy exposes the wrapped provider's client and close.
    assert proxy.client is provider.client
    assert proxy.close == provider.close

    # ... so the real engine's cleanup reaches the wrapped client.
    engine = SearchEngine(providers=[proxy])
    asyncio.run(engine.close())
    assert closed == ["client"]
