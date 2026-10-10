"""Focused HCM-04d tests for the neutral hydration stage.

Stage 2.5 (abstract backfill -> ABSTRACT_HYDRATION audit -> client close)
lives in ``scholar_harness.pipeline.hydration``; the orchestrator delegates.
Every test is hermetic (``tmp_path`` only, fake hydrator/client, no network)
and asserts zero behavior change: missing-abstract passthrough to Stage 3,
ALL-docs hydration semantics, exact client arguments, verbatim stats
mapping, byte-compatible legacy audit bytes, hard hydrate->audit->close
ordering, close on every path, and failure propagation with no fabricated
documents, audit rows, or success claims.

Mapping to the HCM-04d packet:

- HCM4D-01 missing-abstract passthrough to Stage 3
- HCM4D-02 all-present passthrough (stats zeros, audit still written)
- HCM4D-03 ALL documents reach the hydrator (subset mutation detected)
- HCM4D-04 exact client args (name/rate_limit mutation detected)
- HCM4D-05 verbatim stats mapping (identity + pre-hydration count)
- HCM4D-06 legacy audit bytes preserved (deleted-audit mutation detected)
- HCM4D-07 console-import guard + Stage 2.5 region has no direct kit use
- HCM4D-08 orchestrator<->stage equivalence
- HCM4D-09 hydration-exception -> no success event + close still called
- HCM4D-10 audit-exception propagates + close still called;
  close-exception preserves hydrate+audit-before-escape
- HCM4D-11 ORDERED hydrate->audit->close trace (audit-after-close detected)

Negatives NEG-01..NEG-10 are the mutation/failure halves of the above:
subset input, client args, deleted audit, audit-after-close order, hydration
exception (stage + orchestrator level), audit exception, close exception,
console transport import, orchestrator/stage divergence.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import hydration


def _make_docs_missing_abstracts():
    """3 docs in: 2 missing abstracts (shared DOI -> dedup to 1), 1 present."""
    from scholar_search.models import Author, Document, ExternalIds

    return [
        Document(
            title="Grounded Code Generation with LLMs",
            year=2023,
            provider="openalex",
            provider_id="W4001",
            external_ids=ExternalIds(doi="10.1000/hyd"),
            authors=[Author(family_name="Chen", given_name="Alex")],
            abstract=None,
        ),
        Document(
            title="Grounded Code Generation with LLMs.",
            year=2023,
            provider="arxiv",
            provider_id="2308.01234",
            external_ids=ExternalIds(doi="10.1000/hyd", arxiv_id="2308.01234"),
            authors=[Author(family_name="Chen", given_name="A.")],
            abstract=None,
        ),
        Document(
            title="Evaluating Python Code Synthesis",
            year=2024,
            provider="crossref",
            provider_id="10.1145/3002",
            external_ids=ExternalIds(doi="10.1145/3002"),
            authors=[Author(family_name="Smith", given_name="Jane")],
            abstract="Distinct study abstract.",
        ),
    ]


def _make_docs_all_present():
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


def _write_protocol(ws: Path, slug: str = "hydration-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "hydration-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Hydration Stage Parity",
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


def _stub_screening_prepare(monkeypatch):
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def _journal_rows(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _hydration_rows(ws: Path) -> list[dict]:
    return [r for r in _journal_rows(ws) if r.get("action") == "ABSTRACT_HYDRATION"]


class _FakeScope:
    """Per-test capture for the fake hydrator/client seam."""

    def __init__(self):
        self.order: list[str] = []
        self.received: list[list] = []
        self.client_args: list[tuple] = []
        self.client_kwargs: list[dict] = []
        self.stats: dict | None = None


def _install_fakes(monkeypatch, scope, *, fail_hydrate=None, fail_close=None):
    """Patch the pipeline.hydration namespace (no network, tmp_path only)."""

    class _FakeHydrator:
        def __init__(self, client):
            self.client = client

        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            scope.order.append("hydrate")
            scope.received.append(list(docs))
            if fail_hydrate is not None:
                raise fail_hydrate
            missing = [d for d in docs if not d.abstract]
            for d in missing:
                d.abstract = f"Backfilled abstract for {d.title}."
            stats = {
                "attempted": len(missing),
                "hydrated": len(missing),
                "failed": 0,
            }
            scope.stats = stats
            return list(docs), stats

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            scope.client_args.append(args)
            scope.client_kwargs.append(kwargs)

        async def close(self):
            scope.order.append("close")
            if fail_close is not None:
                raise fail_close

    monkeypatch.setattr(hydration, "AbstractHydrator", _FakeHydrator)
    monkeypatch.setattr(hydration, "AcademicHttpClient", _FakeClient)
    return _FakeHydrator, _FakeClient


def _install_audit_tracer(monkeypatch, scope):
    """Wrap the real legacy audit writer so order is observable, bytes real."""
    real = hydration.append_legacy_event

    def _recording(*args, **kwargs):
        scope.order.append("audit")
        return real(*args, **kwargs)

    monkeypatch.setattr(hydration, "append_legacy_event", _recording)


def _run_stage(docs, ws, **kw):
    return asyncio.run(hydration.run_hydration(documents=docs, workspace_dir=ws, **kw))


# ---------------------------------------------------------------------------
# HCM4D-01 missing-abstract passthrough (NEG-09 counterpart at orch level)
# ---------------------------------------------------------------------------


def test_missing_abstracts_backfilled_and_returned(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    _install_audit_tracer(monkeypatch, scope)
    ws = tmp_path / "ws"
    docs = _make_docs_missing_abstracts()

    outcome = _run_stage(docs, ws)

    assert len(outcome.documents) == 3
    assert all(d.abstract for d in outcome.documents)
    assert outcome.stats == {"attempted": 2, "hydrated": 2, "failed": 0}
    assert scope.order == ["hydrate", "audit", "close"]


def test_hydrated_documents_flow_to_stage_3_verifier(tmp_path, monkeypatch):
    """Orchestrator level: Stage 3 receives the hydrated documents."""
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    seen_verify: list[list] = []

    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            return _make_docs_missing_abstracts()

        async def close(self):
            pass

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            seen_verify.append(list(docs))
            return list(docs), []

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "DocumentVerifier", _PassthroughVerifier)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    # Dedup merged the shared-DOI pair; the verifier saw hydrated unique docs.
    assert len(seen_verify) == 1
    assert len(seen_verify[0]) == 2
    assert all(d.abstract for d in seen_verify[0])


# ---------------------------------------------------------------------------
# HCM4D-02 all-present passthrough
# ---------------------------------------------------------------------------


def test_all_present_returns_same_docs_with_zero_stats(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    _install_audit_tracer(monkeypatch, scope)
    ws = tmp_path / "ws"
    docs = _make_docs_all_present()

    outcome = _run_stage(docs, ws)

    assert [d.title for d in outcome.documents] == [d.title for d in docs]
    assert outcome.stats == {"attempted": 0, "hydrated": 0, "failed": 0}
    # The audit event is still written and the client still closed.
    rows = _hydration_rows(ws)
    assert len(rows) == 1
    assert rows[0]["metrics"] == {"attempted": 0, "hydrated": 0, "failed": 0}
    assert scope.order == ["hydrate", "audit", "close"]


def test_empty_input_still_audits_and_closes(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    _install_audit_tracer(monkeypatch, scope)
    ws = tmp_path / "ws"

    outcome = _run_stage([], ws)

    assert outcome.documents == []
    assert outcome.stats == {"attempted": 0, "hydrated": 0, "failed": 0}
    rows = _hydration_rows(ws)
    assert len(rows) == 1
    assert rows[0]["description"] == "Hydrated missing abstracts for 0 documents"
    assert scope.order == ["hydrate", "audit", "close"]


# ---------------------------------------------------------------------------
# HCM4D-03 ALL documents reach the hydrator (NEG-01 subset mutation)
# ---------------------------------------------------------------------------


def test_all_documents_reach_hydrator_not_subset(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    ws = tmp_path / "ws"
    docs = _make_docs_missing_abstracts()

    _run_stage(docs, ws)

    assert len(scope.received) == 1
    # The stage passed ALL input docs, never a subset/slice.
    assert len(scope.received[0]) == 3
    assert scope.received[0] == docs


# ---------------------------------------------------------------------------
# HCM4D-04 exact client args (NEG-02 client-args mutation)
# ---------------------------------------------------------------------------


def test_client_built_with_exact_hydration_args(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    ws = tmp_path / "ws"

    _run_stage(_make_docs_all_present(), ws)

    assert len(scope.client_kwargs) == 1
    assert scope.client_args[0] == ()
    assert scope.client_kwargs[0] == {"name": "hydration", "rate_limit": 10}


# ---------------------------------------------------------------------------
# HCM4D-05 verbatim stats mapping
# ---------------------------------------------------------------------------


def test_stats_mapping_is_verbatim_and_count_is_pre_hydration(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    ws = tmp_path / "ws"
    docs = _make_docs_missing_abstracts()

    outcome = _run_stage(docs, ws)

    # No normalize/rename: the outcome carries the hydrator's stats object.
    assert outcome.stats is scope.stats
    rows = _hydration_rows(ws)
    assert len(rows) == 1
    assert rows[0]["metrics"] is not None
    assert rows[0]["metrics"] == scope.stats
    # Description uses the pre-hydration input count (3), not hydrated count.
    assert rows[0]["description"] == "Hydrated missing abstracts for 3 documents"


# ---------------------------------------------------------------------------
# HCM4D-06 legacy audit bytes preserved (NEG-03 deleted audit)
# ---------------------------------------------------------------------------


def test_legacy_audit_event_bytes_preserved(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    ws = tmp_path / "ws"

    _run_stage(_make_docs_missing_abstracts(), ws)

    rows = _hydration_rows(ws)
    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "ABSTRACT_HYDRATION"
    assert row["agent_or_tool"] == "scholar-harness"
    assert row["description"] == "Hydrated missing abstracts for 3 documents"
    assert row["inputs"] == []
    assert row["outputs"] == []
    assert row["metrics"] == {"attempted": 2, "hydrated": 2, "failed": 0}
    assert row["status"] == "SUCCESS"
    assert row["event_id"].startswith("EVT-")
    assert row["timestamp"]
    # No uppercasing/projection/refresh side effects: only the journal row.
    assert sorted(row.keys()) == sorted(
        [
            "timestamp",
            "event_id",
            "action",
            "agent_or_tool",
            "description",
            "parameters",
            "inputs",
            "outputs",
            "metrics",
            "status",
        ]
    )
    # No projection/refresh side effects: the stage writes only the journal row.
    assert sorted(
        p.relative_to(ws).as_posix() for p in ws.rglob("*") if p.is_file()
    ) == ["audit/journal.jsonl"]
    assert list(ws.rglob("artifact_registry.json")) == []


def test_deleted_audit_call_leaves_no_hydration_row(tmp_path, monkeypatch):
    """NEG-03: if the audit call is deleted, no ABSTRACT_HYDRATION row exists."""
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    monkeypatch.setattr(hydration, "append_legacy_event", lambda *a, **k: None)
    ws = tmp_path / "ws"

    outcome = _run_stage(_make_docs_missing_abstracts(), ws)

    assert outcome.stats == {"attempted": 2, "hydrated": 2, "failed": 0}
    assert _hydration_rows(ws) == []


# ---------------------------------------------------------------------------
# HCM4D-07 console-import guard + Stage 2.5 region has no direct kit use
# (NEG-08 console transport)
# ---------------------------------------------------------------------------


def test_stage_has_no_console_transport_import():
    # Repair-1 pattern: import-statement guard (prose may mention "console").
    text = Path(hydration.__file__).read_text(encoding="utf-8")
    lines = text.splitlines()
    out, buf, depth = [], "", 0
    for line in lines:
        stripped = line.strip()
        if not buf and not stripped.startswith(("from ", "import ")):
            continue
        buf += line + "\n"
        depth += line.count("(") - line.count(")")
        if line.rstrip().endswith("\\"):
            continue
        if depth <= 0:
            out.append(buf)
            buf, depth = "", 0
    if buf:
        out.append(buf)
    for stmt in out:
        low = stmt.lower()
        assert "console" not in low
        assert "fastapi" not in low
        assert "uvicorn" not in low
    # Hydration stage calls the search kit (Repair-1 pattern).
    assert any("scholar_search" in s and "scholar_harness" not in s for s in out), (
        "stage must import the scholar-search kit"
    )


def test_stage_2_5_region_has_no_direct_kit_use():
    source = Path(orch.__file__).read_text(encoding="utf-8")
    stage = source.split("Stage 2.5: Abstract Hydration", 1)[1]
    stage = stage.split("Stage 3:", 1)[0]
    # No direct construction or direct hydrate call in the region.
    assert "AbstractHydrator(" not in stage
    assert "AcademicHttpClient(" not in stage
    assert "hydrate_missing_abstracts" not in stage
    assert "run_hydration" in stage


# ---------------------------------------------------------------------------
# HCM4D-08 orchestrator<->stage equivalence (NEG-09 divergence)
# ---------------------------------------------------------------------------


def test_shim_preserves_hydration_identity():
    assert orch.run_hydration is hydration.run_hydration
    assert orch.HydrationOutcome is hydration.HydrationOutcome


def test_orchestrator_path_matches_direct_stage_outcome(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)

    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            return _make_docs_missing_abstracts()

        async def close(self):
            pass

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "DocumentVerifier", _PassthroughVerifier)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    # Orchestrator dedup mapping preserved; hydration audited the unique count.
    # (The shared-DOI pair merged to one representative, so 1 of the 2
    # unique docs needed backfill.)
    assert results["stages"]["deduplication"] == {"unique": 2, "duplicates_removed": 1}
    rows = _hydration_rows(ws)
    assert len(rows) == 1
    assert rows[0]["description"] == "Hydrated missing abstracts for 2 documents"
    assert rows[0]["metrics"] == {"attempted": 1, "hydrated": 1, "failed": 0}

    # Direct dedup->hydration over equivalent fresh docs reaches the
    # identical outcome and audit shape.
    from scholar_harness.pipeline.deduplication import (
        run_deduplication as _run_dedup,
    )

    direct_scope = _FakeScope()
    _install_fakes(monkeypatch, direct_scope)
    dedup_outcome = _run_dedup(
        discovered_documents=_make_docs_missing_abstracts(),
        literature_dir=tmp_path / "direct-lit",
    )
    assert dedup_outcome.unique == 2
    direct_ws = tmp_path / "direct-ws"
    direct_outcome = _run_stage(dedup_outcome.representatives, direct_ws)

    assert direct_outcome.stats == rows[0]["metrics"]
    direct_rows = _hydration_rows(direct_ws)
    assert len(direct_rows) == 1
    for key in (
        "action",
        "agent_or_tool",
        "description",
        "metrics",
        "inputs",
        "outputs",
        "status",
    ):
        assert direct_rows[0][key] == rows[0][key], key


# ---------------------------------------------------------------------------
# HCM4D-09 hydration exception: no success event, close still called
# (NEG-05 stage level; NEG-10 orchestrator level)
# ---------------------------------------------------------------------------


def test_hydration_exception_propagates_without_success_event(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope, fail_hydrate=RuntimeError("hydrate boom"))
    ws = tmp_path / "ws"

    with pytest.raises(RuntimeError, match="hydrate boom"):
        _run_stage(_make_docs_missing_abstracts(), ws)

    # Failure publishes nothing: no fabricated docs, no success audit row --
    # but the client close is still attempted.
    assert _hydration_rows(ws) == []
    assert not (ws / "audit" / "journal.jsonl").exists()
    assert scope.order == ["hydrate", "close"]


def test_orchestrator_hydration_failure_propagates_without_success(
    tmp_path, monkeypatch
):
    """NEG-10: orchestrator-level kit failure propagates with no success row."""

    class _FailingHydrator:
        def __init__(self, client):
            pass

        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            raise RuntimeError("hydrate boom")

    class _DummyClient:
        def __init__(self, *a, **k):
            pass

        async def close(self):
            pass

    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            return _make_docs_all_present()

        async def close(self):
            pass

    monkeypatch.setattr(hydration, "AbstractHydrator", _FailingHydrator)
    monkeypatch.setattr(hydration, "AcademicHttpClient", _DummyClient)
    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    with pytest.raises(RuntimeError, match="hydrate boom"):
        asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert _hydration_rows(ws) == []


# ---------------------------------------------------------------------------
# HCM4D-10 audit/close exceptions (NEG-06 audit; NEG-07 close)
# ---------------------------------------------------------------------------


def test_audit_exception_propagates_and_close_still_called(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)

    def _raising_audit(*args, **kwargs):
        scope.order.append("audit")
        raise RuntimeError("audit boom")

    monkeypatch.setattr(hydration, "append_legacy_event", _raising_audit)
    ws = tmp_path / "ws"

    with pytest.raises(RuntimeError, match="audit boom"):
        _run_stage(_make_docs_missing_abstracts(), ws)

    assert scope.order == ["hydrate", "audit", "close"]
    assert _hydration_rows(ws) == []


def test_close_exception_preserves_hydrate_and_audit_before_escape(
    tmp_path, monkeypatch
):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope, fail_close=RuntimeError("close boom"))
    ws = tmp_path / "ws"

    with pytest.raises(RuntimeError, match="close boom"):
        _run_stage(_make_docs_missing_abstracts(), ws)

    # Hydration and the audit completed before the close failure escaped.
    assert scope.order == ["hydrate", "close"]
    rows = _hydration_rows(ws)
    assert len(rows) == 1
    assert rows[0]["metrics"] == {"attempted": 2, "hydrated": 2, "failed": 0}


# ---------------------------------------------------------------------------
# HCM4D-11 ORDERED hydrate->audit->close trace (NEG-04 audit-after-close)
# ---------------------------------------------------------------------------


def test_ordered_trace_hydrate_before_audit_before_close(tmp_path, monkeypatch):
    scope = _FakeScope()
    _install_fakes(monkeypatch, scope)
    _install_audit_tracer(monkeypatch, scope)
    ws = tmp_path / "ws"

    _run_stage(_make_docs_missing_abstracts(), ws)

    # Exact order: audit inside try BEFORE finally-close, so a close failure
    # can never suppress a recorded success. Any audit-after-close move
    # breaks this trace.
    assert scope.order == ["hydrate", "audit", "close"]
    assert scope.order.index("hydrate") < scope.order.index("audit")
    assert scope.order.index("audit") < scope.order.index("close")
