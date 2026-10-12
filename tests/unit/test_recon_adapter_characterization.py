"""HCM-05 characterization: MCP recon transport boundary + harness adapter.

Executable map of the ADOPTED boundary (canonical scholar-agent-kit@50c0b3f
vendored; ``plugins.json`` pin bumped; ``nexus_scholar_pins.json`` regen).
Nothing here changes kit code, recon behavior, or public semantics.  All
fixtures live under ``tmp_path`` (never ``workspaces/``); no network (every
probe runs through an injected fake ``search_fn``).

Evidence labels per test:

- OBSERVED-KIT      -- drives the real vendored ``scholar_agent.server``
  tool with fakes; the asserted behavior is the shipped behavior.
- OBSERVED-HARNESS  -- drives the real ``scholar_harness.recon`` machinery.
- OBSERVED-ADAPTER  -- drives the new harness-owned
  ``scholar_harness.recon.adapter`` (harness half of HCM-05).
- SOURCE-TRACE      -- asserts on shipped source text without executing it.
- ADOPTED-KIT       -- asserts the post-merge adopted seam: recon tools drive
  ONLY ``scholar_harness.recon.adapter`` via ``_ensure_harness_recon_loaded``;
  no ``_harness_src`` / ``NEXUS_HARNESS_SRC`` / ``sys.path`` discovery exists.

The adapter section (Part A) performs NO ``scholar_agent`` import at module
level and none inside its tests: those tests pass WITHOUT the kit.  Kit
imports appear only as function-level imports inside Parts B-G tests.
Adoption notes: Part C now proves ABSENCE of the retired discovery seam;
Part D proves the loader is CALLED by every production tool (it binds the
adapter, never mutates ``sys.path``); H01/H02 prove adapter-unavailable maps
into the typed ``{status: error}`` envelope instead of escaping as
``TypeError``.  H03 (test-only ``RECON_CACHE_ROOT=None`` post-load mutation)
and H06 (``TypeError`` raised *by* an injected search_fn) still escape the
``(RuntimeError, ValueError, OSError)`` envelope by design -- the envelope
covers adapter/harness failures, not caller-mutated globals or foreign
``TypeError``s from injected doubles.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path

import pytest

import scholar_harness.recon.adapter as adapter
from scholar_harness.recon.adapter import (
    ReconAdapterDependencyError,
    ReconAdapterInputError,
)


def _fake_doc(doi: str, title: str, abstract: str):
    from scholar_search.models import Document, ExternalIds

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


def _topic_docs():
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


def _topic_search_fn(query, providers):
    return _topic_docs()


def _explode_search_fn(query, providers):
    raise AssertionError("provider probe must not run here (hermetic)")


# ---------------------------------------------------------------------------
# Part A -- harness-owned adapter interface (OBSERVED-ADAPTER, kit-free)
# ---------------------------------------------------------------------------


def test_a01_adapter_version_is_pinned():
    """A01 [OBSERVED-ADAPTER]: the explicit interface is versioned."""
    assert adapter.ADAPTER_VERSION == "1.0"
    assert adapter.adapter_version() == "1.0"
    assert adapter.describe_interface()["adapter_version"] == "1.0"


def test_a02_adapter_has_no_kit_transport_or_discovery_imports():
    """A02 [OBSERVED-ADAPTER, SOURCE-TRACE]: adapter is harness-pure.

    No MCP/kit imports, no sys.path tricks, no NEXUS_HARNESS_SRC handling --
    the exact couplings the kit-half PR must remove server-side.
    """
    src = Path(adapter.__file__).read_text(encoding="utf-8")
    # No runtime dependency on the kit/transport: check the code body, not the
    # module docstring (which names the kit seam it documents; prose is not a
    # dependency).  sys.path / NEXUS_HARNESS_SRC must not be *used* in code.
    body = src.split('"""', 2)[2] if src.startswith('"""') else src
    assert "import scholar_agent" not in body
    assert "from scholar_agent" not in body
    assert "sys.path" not in body
    assert "NEXUS_HARNESS_SRC" not in body
    assert "from mcp" not in body and "import mcp" not in body
    assert "hashlib" not in body  # no algorithm duplication (cache digests)
    assert "import re" not in body  # no lexicon/school pattern duplication


def test_a03_adapter_errors_are_envelope_compatible():
    """A03 [OBSERVED-ADAPTER]: typed errors fit the kit's documented catch.

    The kit catches ``(RuntimeError, ValueError, OSError)``; a future
    adapter-backed tool must map into ``{status: error}``, never escape as
    an uncaught ``TypeError`` (the OBSERVED F1 failure mode).
    """
    assert issubclass(ReconAdapterInputError, RuntimeError)
    assert issubclass(ReconAdapterInputError, ValueError)
    assert issubclass(ReconAdapterDependencyError, RuntimeError)
    assert issubclass(adapter.ReconAdapterError, RuntimeError)


def test_a04_resolve_cache_root_matches_canonical_with_override(tmp_path, monkeypatch):
    """A04 [OBSERVED-ADAPTER]: adapter root == canonical root under env."""
    from scholar_harness.recon import canonical_recon_root

    target = tmp_path / "canonical"
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(target))
    assert adapter.resolve_cache_root() == canonical_recon_root()
    assert adapter.resolve_cache_root() == target.resolve()


def test_a05_resolve_cache_root_matches_canonical_without_override(monkeypatch):
    """A05 [OBSERVED-ADAPTER]: adapter root == canonical root, no env."""
    from scholar_harness.recon import canonical_recon_root

    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    assert adapter.resolve_cache_root() == canonical_recon_root()
    tail = adapter.resolve_cache_root().parts[-2:]
    assert tail == (".cache", "inception_recon")


def test_a06_make_engine_rejects_workspaces_root(tmp_path):
    """A06 [OBSERVED-ADAPTER]: explicit workspaces anchor refused, typed."""
    bad = tmp_path / "workspaces" / "x" / ".cache" / "inception_recon"
    with pytest.raises(ReconAdapterInputError) as caught:
        adapter.make_engine(cache_root=bad, search_fn=_topic_search_fn)
    assert "workspaces" in str(caught.value).casefold()
    assert not (tmp_path / "workspaces" / "x" / ".cache").exists()


def test_a07_make_engine_rejects_non_callable_search_fn(tmp_path):
    """A07 [OBSERVED-ADAPTER]: non-callable injected dep -> typed, not TypeError."""
    with pytest.raises(ReconAdapterDependencyError):
        adapter.make_engine(
            cache_root=tmp_path / "r",
            search_fn="not-a-callable",  # type: ignore[arg-type]
        )


def test_a08_missing_symbol_raises_typed_not_typeerror(monkeypatch):
    """A08 [OBSERVED-ADAPTER]: None dependency -> DependencyError (cf. kit F1)."""
    monkeypatch.setattr(adapter, "_ReconEngine", None)
    with pytest.raises(ReconAdapterDependencyError):
        adapter.make_engine(search_fn=_topic_search_fn)
    monkeypatch.setattr(adapter, "_distill_pool", None)
    with pytest.raises(ReconAdapterDependencyError):
        adapter.distill_terms({"docs": []})


def test_a09_invalid_inputs_raise_typed_input_errors():
    """A09 [OBSERVED-ADAPTER]: malformed caller inputs are typed."""
    with pytest.raises(ReconAdapterInputError):
        adapter.build_cache_key("   ")
    with pytest.raises(ReconAdapterInputError):
        adapter.build_cache_key("q", providers=[])
    with pytest.raises(ReconAdapterInputError):
        adapter.distill_terms("not-a-dict")  # type: ignore[arg-type]
    with pytest.raises(ReconAdapterInputError):
        adapter.plan_candidates({}, "not-a-dict")  # type: ignore[arg-type]
    with pytest.raises(ReconAdapterInputError):
        adapter.merge_pool_list("not-a-list")  # type: ignore[arg-type]
    with pytest.raises(ReconAdapterInputError):
        adapter.pool_gate(-1)
    with pytest.raises(ReconAdapterInputError):
        adapter.topic_gate("not-a-list")  # type: ignore[arg-type]
    with pytest.raises(ReconAdapterInputError):
        asyncio.run(adapter.probe_topic("   ", search_fn=_topic_search_fn))


def test_a10_cache_key_roundtrip_matches_engine():
    """A10 [OBSERVED-ADAPTER]: key build/parse delegates byte-identically."""
    from scholar_harness.recon import cache_key, parse_cache_key

    key = adapter.build_cache_key("Edge Inference", ["openalex"], 2020, None)
    assert key == cache_key("Edge Inference", ["openalex"], 2020, None)
    assert adapter.parse_key(key) == parse_cache_key(key)
    assert adapter.normalize_text("  Edge Inference... ") == "edge inference"
    assert adapter.default_providers() == [
        "openalex",
        "semanticscholar",
        "crossref",
        "arxiv",
    ]
    assert adapter.saturation_for(-1) == "unknown"
    assert adapter.saturation_for(0) == "scant"


def test_a11_probe_is_idempotent_and_cache_addressed(tmp_path):
    """A11 [OBSERVED-ADAPTER]: same query reuses the pool (one search call)."""
    calls: list[str] = []

    def counting(query, providers):
        calls.append(query.text)
        return _topic_docs()

    root = tmp_path / ".cache" / "inception_recon"
    first_path, first_n = asyncio.run(
        adapter.probe_topic("drone crop disease", cache_root=root, search_fn=counting)
    )
    second_path, second_n = asyncio.run(
        adapter.probe_topic("drone crop disease", cache_root=root, search_fn=counting)
    )
    assert first_n == second_n == 3
    assert first_path == second_path
    assert len(calls) == 1
    payload = json.loads(first_path.read_text(encoding="utf-8"))
    assert payload["cache_key"].startswith("v1/")
    # OBSERVED: adapter.probe_topic defaults year_min=2000 (engine default);
    # the same explicit window must be passed to build_cache_key for parity.
    again = adapter.build_cache_key(
        "drone crop disease",
        ["openalex", "semanticscholar", "crossref", "arxiv"],
        2000,
        None,
    )
    assert again == payload["cache_key"]


def test_a12_distill_and_gates_delegate_byte_identically(tmp_path):
    """A12 [OBSERVED-ADAPTER]: distill/merge/gates match direct engine calls."""
    from scholar_harness.recon import distill_pool, merge_pools
    from scholar_harness.recon.gates import (
        compute_pool_sufficiency,
        compute_topic_purity,
    )

    root = tmp_path / ".cache" / "inception_recon"
    pool_path, _n = asyncio.run(
        adapter.probe_topic(
            "edge inference", cache_root=root, search_fn=_topic_search_fn
        )
    )
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    via_adapter = adapter.distill_terms(pool, query_text="edge inference")
    via_direct = distill_pool(pool, query_text="edge inference")
    assert via_adapter == via_direct
    assert adapter.distill_terms(pool) == distill_pool(pool)
    assert adapter.plan_candidates(via_adapter, pool) == adapter.plan_candidates(
        via_direct, pool
    )
    assert adapter.merge_pool_list([pool, pool]) == merge_pools([pool, pool])
    assert adapter.pool_gate(3) == compute_pool_sufficiency(3)
    assert adapter.topic_gate([]) == compute_topic_purity([])
    assert (
        adapter.merge_lexicon(adapter.default_lexicon(), adapter.default_lexicon())
        is not None
    )


def test_a13_run_followups_matches_direct_engine_result(tmp_path):
    """A13 [OBSERVED-ADAPTER]: adaptive horizon delegates with same shape."""
    import json as _json

    from scholar_harness.recon import ReconEngine, distill_pool
    from scholar_harness.recon.adaptive import execute_followups

    root = tmp_path / ".cache" / "inception_recon"
    engine = ReconEngine(cache_root=root, search_fn=_topic_search_fn)
    pool_path, _n = asyncio.run(engine.probe("edge inference"))
    pool = _json.loads(pool_path.read_text(encoding="utf-8"))
    distilled = distill_pool(pool)
    via_adapter = asyncio.run(
        adapter.run_followups(
            pool, distilled, cache_root=root, search_fn=_topic_search_fn
        )
    )
    engine2 = ReconEngine(cache_root=root, search_fn=_topic_search_fn)
    via_direct = asyncio.run(execute_followups(pool, distilled, engine2))
    assert via_adapter["dropped_n"] == via_direct["dropped_n"]
    assert via_adapter["cache_keys_merged"] == via_direct["cache_keys_merged"]
    assert [f["term"] for f in via_adapter["followups"]] == [
        f["term"] for f in via_direct["followups"]
    ]


# ---------------------------------------------------------------------------
# Kit-side helpers (function-level kit imports only)
# ---------------------------------------------------------------------------


def _kit_server():
    from scholar_agent import server

    server._ensure_harness_recon_loaded()
    return server


def _kit_isolated(server, monkeypatch, tmp_path, search_fn=_topic_search_fn):
    monkeypatch.setattr(
        server, "RECON_CACHE_ROOT", tmp_path / ".cache" / "inception_recon"
    )
    monkeypatch.setattr(server, "RECON_SEARCH_FN", search_fn)
    return server


def _saved_loader_state(server):
    return {
        "adapter": server._recon_adapter,
        "lexicon": server.DomainLexicon,
        "cache_root": server.RECON_CACHE_ROOT,
        "search_fn": server.RECON_SEARCH_FN,
        "loaded": server._harness_recon_loaded,
    }


def _restore_loader_state(server, saved):
    server._recon_adapter = saved["adapter"]
    server.DomainLexicon = saved["lexicon"]
    server.RECON_CACHE_ROOT = saved["cache_root"]
    server.RECON_SEARCH_FN = saved["search_fn"]
    server._harness_recon_loaded = saved["loaded"]


def _reset_loader_state(server):
    server._recon_adapter = None
    server.DomainLexicon = None
    server.RECON_CACHE_ROOT = None
    server._harness_recon_loaded = False


def _block_harness_imports(monkeypatch):
    """Force adapter-unavailable regardless of environment.

    Setting the sys.modules entries to None makes any
    ``from scholar_harness... import ...`` raise ImportError, so the
    loader returns False and the tools report the typed envelope.
    """
    import sys

    for name in (
        "scholar_harness",
        "scholar_harness.recon",
        "scholar_harness.recon.adapter",
        "scholar_harness.recon.lexicon",
    ):
        monkeypatch.setitem(sys.modules, name, None)


# ---------------------------------------------------------------------------
# Part B -- live tool signatures + envelopes (OBSERVED-KIT)
# ---------------------------------------------------------------------------


def test_b01_three_recon_tools_registered(tmp_path, monkeypatch):
    """B01 [OBSERVED-KIT]: exactly recon_probe/distill/delta on the MCP surface."""
    server = _kit_server()
    names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    assert {"recon_probe", "recon_distill", "recon_delta"} <= names


def test_b02_tool_signatures_are_exact(tmp_path, monkeypatch):
    """B02 [OBSERVED-KIT, SOURCE-TRACE]: exact parameter names/defaults."""
    server = _kit_server()
    assert list(inspect.signature(server.recon_probe).parameters) == [
        "topic",
        "session_id",
        "start_year",
        "limit",
        "semantic",
    ]
    probe_defaults = inspect.signature(server.recon_probe).parameters
    assert probe_defaults["session_id"].default is None
    assert probe_defaults["start_year"].default == 2020
    assert probe_defaults["limit"].default == 10
    assert probe_defaults["semantic"].default is False
    assert list(inspect.signature(server.recon_distill).parameters) == [
        "session_id",
        "lexicon_json",
    ]
    assert list(inspect.signature(server.recon_delta).parameters) == [
        "session_id",
        "followups",
    ]
    assert inspect.signature(server.recon_delta).parameters["followups"].default == 3


def test_b03_probe_envelope_and_session_artifacts(tmp_path, monkeypatch):
    """B03 [OBSERVED-KIT]: probe_ok envelope + session.json + pool artifact."""
    server = _kit_isolated(_kit_server(), monkeypatch, tmp_path)
    result = json.loads(server.recon_probe(topic="drone crop disease detection"))
    assert result["status"] == "probe_ok"
    assert result["session_id"].startswith("rec_")
    assert result["cache_key"].startswith("v1/")
    assert result["n_docs"] == 3
    assert Path(result["pool_path"]).is_file()
    session_file = (
        tmp_path
        / ".cache"
        / "inception_recon"
        / "sessions"
        / result["session_id"]
        / "session.json"
    )
    assert session_file.is_file()
    session = json.loads(session_file.read_text(encoding="utf-8"))
    assert session["cache_keys"] == [result["cache_key"]]


def test_b04_distill_envelope_and_delta_lineage(tmp_path, monkeypatch):
    """B04 [OBSERVED-KIT]: distill terms + delta merged lineage, cache-reused."""
    mapping = {
        "drone crop disease detection": _topic_docs(),
        "edge inference": [
            _fake_doc(
                "10.1000/fu-1", "Edge Inference Benchmarks", "edge inference devices."
            )
        ],
    }

    def search_fn(query, providers):
        return mapping.get(query.text.strip().casefold(), [])

    server = _kit_isolated(_kit_server(), monkeypatch, tmp_path, search_fn=search_fn)
    probe = json.loads(server.recon_probe(topic="drone crop disease detection"))
    dist = json.loads(server.recon_distill(session_id=probe["session_id"]))
    assert dist["cache_key"] == probe["cache_key"]
    assert Path(dist["terms_path"]).is_file()
    assert dist["micro_taxonomy_top"]
    delta = json.loads(server.recon_delta(session_id=probe["session_id"]))
    assert delta["merged_cache_keys"][0] == probe["cache_key"]
    assert delta["pool_size_before"] == 3
    assert Path(delta["pool_path"]).is_file()
    assert Path(delta["terms_path"]).is_file()


def test_b05_semantic_mode_segments_cache_key(tmp_path, monkeypatch):
    """B05 [OBSERVED-KIT]: semantic=True threads through + segments the key."""
    captured: dict[str, object] = {}

    def search_fn(query, providers):
        captured["semantic"] = query.semantic
        return _topic_docs()

    server = _kit_isolated(_kit_server(), monkeypatch, tmp_path, search_fn=search_fn)
    sem = json.loads(server.recon_probe(topic="edge inference", semantic=True))
    assert captured["semantic"] is True
    assert "/m/semantic/" in sem["cache_key"]
    kw = json.loads(server.recon_probe(topic="edge inference"))
    assert captured["semantic"] is False
    assert "/m/semantic/" not in kw["cache_key"]
    assert sem["cache_key"] != kw["cache_key"]


# ---------------------------------------------------------------------------
# Part C -- discovery-seam ABSENCE (ADOPTED-KIT, SOURCE-TRACE + runtime)
#
# Canonical scholar-agent-kit@50c0b3f deleted the dynamic seam: there is no
# ``_harness_src`` helper, no ``NEXUS_HARNESS_SRC`` read, no ``sys.path``
# mutation, and no ``find_spec``/parent-walk anywhere in shipped kit source.
# ---------------------------------------------------------------------------


def test_c01_harness_src_env_override_has_no_effect(monkeypatch):
    """C01 [ADOPTED-KIT]: the retired NEXUS_HARNESS_SRC override is inert."""
    import sys

    server = _kit_server()
    assert not hasattr(server, "_harness_src")
    monkeypatch.setenv("NEXUS_HARNESS_SRC", "/tmp/custom-harness-src")
    before = list(sys.path)
    server._ensure_harness_recon_loaded()
    assert list(sys.path) == before
    assert "/tmp/custom-harness-src" not in sys.path


def test_c02_no_discovery_helper_and_no_path_mutation(monkeypatch):
    """C02 [ADOPTED-KIT]: no discovery helper exists; loading never mutates path."""
    import sys

    server = _kit_server()
    assert not hasattr(server, "_harness_src")
    assert not hasattr(server, "_HARNESS_SRC")
    monkeypatch.delenv("NEXUS_HARNESS_SRC", raising=False)
    before = list(sys.path)
    assert server._ensure_harness_recon_loaded() is True
    assert list(sys.path) == before
    # The adapter is a plain importable binding, not a discovered path.
    assert server._recon_adapter is not None


def test_c03_adapter_bound_by_guarded_import_without_syspath_insert():
    """C03 [ADOPTED-KIT, SOURCE-TRACE]: loader binds the adapter, never sys.path."""
    server = _kit_server()
    src = inspect.getsource(server)
    assert "_harness_src" not in src
    assert "_HARNESS_SRC" not in src
    assert "NEXUS_HARNESS_SRC" not in src
    assert "sys.path" not in src
    assert "find_spec" not in src
    assert "import sys" not in src
    loader_src = inspect.getsource(server._ensure_harness_recon_loaded)
    assert "from scholar_harness.recon import adapter as _recon_adapter" in loader_src
    assert (
        "from scholar_harness.recon.lexicon import DomainLexicon as _DomainLexicon"
        in loader_src
    )


def test_c04_module_level_adapter_names_start_none():
    """C04 [ADOPTED-KIT, SOURCE-TRACE]: lazy adapter globals start None.

    The retired per-symbol globals (``ReconEngine``, ``canonical_recon_root``,
    ``distill_pool``, ``execute_followups``) are ABSENT; the adopted seam
    binds exactly ``_recon_adapter`` + ``DomainLexicon`` + ``RECON_CACHE_ROOT``
    (+ the ``RECON_SEARCH_FN`` injection seam) on first tool call.
    """
    server = _kit_server()
    src = inspect.getsource(server)
    for name in (
        "_recon_adapter = None",
        "DomainLexicon = None",
        "RECON_CACHE_ROOT = None",
        "RECON_SEARCH_FN = None",
    ):
        assert name in src
    for retired in (
        "ReconEngine = None",
        "canonical_recon_root = None",
        "distill_pool = None",
        "execute_followups = None",
        "ReconEngine(",
    ):
        assert retired not in src


# ---------------------------------------------------------------------------
# Part D -- loader-called-by-tools proof (ADOPTED-KIT, SOURCE-TRACE + runtime)
#
# The adopted loader is LIVE: every recon tool calls it first; it binds the
# adapter via a plain guarded import and resolves RECON_CACHE_ROOT through
# the adapter (never a snapshot of individual engine symbols).
# ---------------------------------------------------------------------------


def test_d01_production_tools_call_loader_first():
    """D01 [ADOPTED-KIT, SOURCE-TRACE]: the adapter binder runs atop every tool."""
    import scholar_harness.recon.adapter as adopted

    server = _kit_server()
    assert server._recon_adapter is adopted
    for fn in (server.recon_probe, server.recon_distill, server.recon_delta):
        assert "_ensure_harness_recon_loaded" in inspect.getsource(fn)
    assert "_recon_adapter is None" in inspect.getsource(server.recon_probe)


def test_d02_cache_root_resolved_via_adapter_inside_loader():
    """D02 [ADOPTED-KIT, SOURCE-TRACE]: RECON_CACHE_ROOT comes from the adapter."""
    server = _kit_server()
    loader_src = inspect.getsource(server._ensure_harness_recon_loaded)
    assert "RECON_CACHE_ROOT = _recon_adapter.resolve_cache_root()" in loader_src
    module_src = inspect.getsource(server)
    assert module_src.count("RECON_CACHE_ROOT = ") >= 2  # None default + loader assign
    assert "RECON_CACHE_ROOT = canonical_recon_root()" not in module_src
    assert "canonical_recon_root" not in module_src


# ---------------------------------------------------------------------------
# Part E -- cache-root agreement CLI vs MCP (OBSERVED-KIT + OBSERVED-HARNESS)
# ---------------------------------------------------------------------------


def test_e01_env_override_unifies_cli_and_mcp(tmp_path, monkeypatch):
    """E01 [OBSERVED]: NEXUS_RECON_ROOT unifies engine default and MCP root."""
    from scholar_harness.recon import ReconEngine, canonical_recon_root

    server = _kit_server()
    target = tmp_path / "canonical"
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(target))
    monkeypatch.setattr(server, "_harness_recon_loaded", False)
    monkeypatch.setattr(server, "RECON_CACHE_ROOT", None, raising=False)
    server._ensure_harness_recon_loaded()
    assert server.RECON_CACHE_ROOT == canonical_recon_root() == target.resolve()
    assert ReconEngine(cache_root=None).cache_root == target.resolve()
    assert ReconEngine().cache_root == target.resolve()


def test_e02_repo_anchored_default_without_env(monkeypatch):
    """E02 [OBSERVED-HARNESS]: no env -> CWD-independent repo-anchored root."""
    from scholar_harness.recon import canonical_recon_root

    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    root = canonical_recon_root()
    assert root.parts[-2:] == (".cache", "inception_recon")
    assert root.is_absolute()


def test_e03_main_workspace_flag_sets_recon_root():
    """E03 [OBSERVED-KIT, SOURCE-TRACE]: server main() -w pins NEXUS_RECON_ROOT."""
    server = _kit_server()
    src = inspect.getsource(server.main)
    assert 'os.environ["NEXUS_RECON_ROOT"]' in src
    assert '".cache" / "inception_recon"' in src or '".cache", "inception_recon"' in src


# ---------------------------------------------------------------------------
# Part F -- RECON_SEARCH_FN classification (OBSERVED-KIT, SOURCE-TRACE)
# ---------------------------------------------------------------------------


def test_f01_search_fn_is_test_only_seam():
    """F01 [ADOPTED-KIT, SOURCE-TRACE]: production only READS the seam.

    The single module-level ``RECON_SEARCH_FN = None`` assignment is the only
    write in shipped kit code; every other assignment site is a test file.
    The adopted server threads it into ``make_engine`` (probe + delta) and
    ``run_followups`` (delta) -- three read sites, zero writes.
    """
    server = _kit_server()
    src = inspect.getsource(server)
    assert src.count("RECON_SEARCH_FN = None") == 1
    assert src.count("RECON_SEARCH_FN =") == 1
    assert "search_fn=RECON_SEARCH_FN" in src
    assert src.count("search_fn=RECON_SEARCH_FN") == 3  # probe + delta x2


def test_f02_injected_search_fn_never_touches_network(tmp_path, monkeypatch):
    """F02 [OBSERVED]: injected fn => hermetic; corpus_count degrades to -1."""
    from scholar_harness.recon import ReconEngine

    async def _check():
        engine = ReconEngine(cache_root=tmp_path / "r", search_fn=_explode_search_fn)
        assert engine.search_fn is not None
        assert await engine.corpus_count("anything") == -1

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# Part G -- inception parity (OBSERVED-KIT + OBSERVED-HARNESS, SOURCE-TRACE)
# ---------------------------------------------------------------------------


def test_g01_wizard_drives_same_engine_and_distiller():
    """G01 [SOURCE-TRACE]: the CLI wizard uses ReconEngine + distill_pool."""
    from scholar_harness.inception import grounded as wizard_grounded

    src = Path(wizard_grounded.__file__).read_text(encoding="utf-8")
    assert "ReconEngine" in src
    assert "distill_pool" in src
    assert "engine.probe" in src


def test_g02_skill_helper_imports_wizard_directly_without_discovery():
    """G02 [SOURCE-TRACE]: grounded_directions.py has no discovery seam."""
    from scholar_harness.inception import grounded as wizard_grounded

    helper = (
        Path(wizard_grounded.__file__).parent.parent.parent.parent
        / ".agents"
        / "skills"
        / "inception-agent"
        / "scripts"
        / "grounded_directions.py"
    )
    if not helper.is_file():
        helper = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "inception-agent"
            / "scripts"
            / "grounded_directions.py"
        )
    src = helper.read_text(encoding="utf-8")
    assert "scholar_harness.inception" in src
    assert "_grounded_directions_for_terms" in src
    assert "_harness_src" not in src
    assert "sys.path" not in src
    assert "NEXUS_HARNESS_SRC" not in src


def test_g03_mcp_drives_adapter_entry_points():
    """G03 [ADOPTED-KIT, SOURCE-TRACE]: MCP tools call the adapter, not engine fns."""
    server = _kit_server()
    assert "_recon_adapter.make_engine(" in inspect.getsource(server.recon_probe)
    assert "engine.probe(" in inspect.getsource(server.recon_probe)
    assert "_recon_adapter.distill_terms(" in inspect.getsource(server.recon_distill)
    assert "_recon_adapter.merge_lexicon(" in inspect.getsource(server.recon_distill)
    assert "_recon_adapter.distill_terms(" in inspect.getsource(server.recon_delta)
    assert "_recon_adapter.run_followups(" in inspect.getsource(server.recon_delta)
    assert "_recon_adapter.pool_gate(" in inspect.getsource(server.recon_distill)
    assert "_recon_adapter.topic_gate(" in inspect.getsource(server.recon_distill)
    for fn in (server.recon_probe, server.recon_distill, server.recon_delta):
        fn_src = inspect.getsource(fn)
        assert "ReconEngine(" not in fn_src
        assert "distill_pool(" not in fn_src
        assert "execute_followups(" not in fn_src


def test_g04_same_query_same_cache_key_across_engine_and_mcp(tmp_path, monkeypatch):
    """G04 [OBSERVED]: engine.probe and recon_probe share the cache address.

    OBSERVED default divergence: ``ReconEngine.probe`` defaults
    ``year_min=2000`` while MCP ``recon_probe`` defaults ``start_year=2020``,
    so parity requires an explicit shared window (2020 here).  The adapter
    keeps the engine default (2000); a kit-half consumer must pass the window
    through explicitly rather than relying on matching defaults.
    """
    from scholar_harness.recon import ReconEngine

    topic = "edge inference parity check"
    root = tmp_path / ".cache" / "inception_recon"
    engine = ReconEngine(cache_root=root, search_fn=_topic_search_fn)
    pool_path, _n = asyncio.run(engine.probe(topic, year_min=2020))
    engine_key = json.loads(pool_path.read_text(encoding="utf-8"))["cache_key"]

    server = _kit_isolated(_kit_server(), monkeypatch, tmp_path)
    probe = json.loads(server.recon_probe(topic=topic))
    assert probe["cache_key"] == engine_key
    assert (
        adapter.build_cache_key(
            topic,
            ["openalex", "semanticscholar", "crossref", "arxiv"],
            2020,
            None,
        )
        == engine_key
    )


def test_g05_skill_helper_matches_wizard_directions():
    """G05 [OBSERVED-HARNESS]: helper reuses the wizard's direction function."""
    from scholar_harness.inception.grounded import _grounded_directions_for_terms

    terms = {
        "micro_taxonomy": [
            {"term": "edge inference", "freq": 3, "anchor_dois": ["a", "b", "c"]},
            {"term": "crop disease", "freq": 2, "anchor_dois": ["a", "b"]},
        ]
    }
    assert _grounded_directions_for_terms(terms) == _grounded_directions_for_terms(
        dict(terms)
    )
    assert all(
        len(d["anchor_dois"]) >= 2 for d in _grounded_directions_for_terms(terms)
    )


# ---------------------------------------------------------------------------
# Part H -- failure modes, each labeled OBSERVED
# ---------------------------------------------------------------------------


def test_h01_missing_adapter_returns_typed_envelope(tmp_path, monkeypatch):
    """H01 [ADOPTED-KIT]: adapter unavailable -> typed envelope, never TypeError.

    Adoption fix for the retired failure mode (``ReconEngine=None`` raising
    uncaught ``TypeError`` outside ``(RuntimeError, ValueError, OSError)``):
    the tools guard on ``_recon_adapter is None`` FIRST, so even with
    ``RECON_CACHE_ROOT=None`` no path is touched before the envelope reply.
    """
    server = _kit_server()
    saved = _saved_loader_state(server)
    try:
        _block_harness_imports(monkeypatch)
        _reset_loader_state(server)
        monkeypatch.setattr(server, "RECON_SEARCH_FN", _topic_search_fn)
        try:
            result = json.loads(server.recon_probe(topic="anything"))
        except TypeError:
            raise AssertionError("probe raised TypeError instead of typed envelope")
        assert result["status"] == "error"
        assert result["cache_key"] is None
        assert "harness recon adapter unavailable" in result["message"]
        assert "scholar_harness.recon.adapter" in result["message"]
    finally:
        _restore_loader_state(server, saved)


def test_h02_missing_adapter_distill_returns_typed_envelope(tmp_path, monkeypatch):
    """H02 [ADOPTED-KIT]: distill without adapter -> typed envelope, never TypeError."""
    server = _kit_server()
    saved = _saved_loader_state(server)
    try:
        _block_harness_imports(monkeypatch)
        _reset_loader_state(server)
        try:
            result = json.loads(server.recon_distill(session_id="rec_abc123"))
        except TypeError:
            raise AssertionError("distill raised TypeError instead of typed envelope")
        assert result["status"] == "error"
        assert result["cache_key"] is None
        assert "harness recon adapter unavailable" in result["message"]
        try:
            delta = json.loads(server.recon_delta(session_id="rec_abc123"))
        except TypeError:
            raise AssertionError("delta raised TypeError instead of typed envelope")
        assert delta["status"] == "error"
        assert delta["cache_key"] is None
    finally:
        _restore_loader_state(server, saved)


def test_h03_none_cache_root_escapes_envelope_as_typeerror(tmp_path, monkeypatch):
    """H03 [OBSERVED-KIT]: RECON_CACHE_ROOT=None -> uncaught TypeError.

    Correction of the naive hypothesis ("None root falls back via
    NEXUS_RECON_ROOT"): the session helper ``_session_root`` divides the
    snapshot global directly (``RECON_CACHE_ROOT / "sessions"``), so a None
    snapshot raises TypeError OUTSIDE the documented envelope before the
    engine (which *would* fall back) is ever constructed.  Adoption keeps this
    shape: the loader binds a live adapter root on every tool call, so ``None``
    here is reachable only as a test-only post-load mutation of the module
    global -- production always carries the adapter-resolved root.  The adapter
    never snapshots: ``resolve_cache_root`` always delegates live (A04/A05).
    """
    server = _kit_server()
    target = tmp_path / "fallback"
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(target))
    monkeypatch.setattr(server, "RECON_CACHE_ROOT", None, raising=False)
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _topic_search_fn)
    with pytest.raises(TypeError):
        server.recon_probe(topic="edge inference")


def test_h04_workspaces_anchor_refused_with_no_writes(tmp_path, monkeypatch):
    """H04 [OBSERVED-KIT]: sessions under workspaces/ refuse inside the envelope."""
    server = _kit_server()
    ws_root = tmp_path / "Workspaces"
    ws_root.mkdir()
    monkeypatch.setattr(
        server, "RECON_CACHE_ROOT", ws_root / ".cache" / "inception_recon"
    )
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _explode_search_fn)
    result = json.loads(server.recon_probe(topic="anything"))
    assert result["status"] == "error"
    assert "workspaces" in result["message"].casefold()
    assert "cache_key" in result
    assert not (ws_root / ".cache").exists()


def test_h05_failing_search_fn_maps_to_envelope(tmp_path, monkeypatch):
    """H05 [OBSERVED-KIT]: RuntimeError from search -> {status: error}."""
    server = _kit_server()

    def _boom(query, providers):
        raise RuntimeError("provider transport down (controlled double)")

    monkeypatch.setattr(
        server, "RECON_CACHE_ROOT", tmp_path / ".cache" / "inception_recon"
    )
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _boom)
    result = json.loads(server.recon_probe(topic="edge inference"))
    assert result["status"] == "error"
    assert "transport down" in result["message"]
    assert result["cache_key"] is None


def test_h06_typeerror_search_fn_escapes_envelope(tmp_path, monkeypatch):
    """H06 [OBSERVED-KIT]: TypeError from search escapes the documented catch."""
    server = _kit_server()

    def _boom_typed(query, providers):
        raise TypeError("bad search_fn shape (controlled double)")

    monkeypatch.setattr(
        server, "RECON_CACHE_ROOT", tmp_path / ".cache" / "inception_recon"
    )
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _boom_typed)
    with pytest.raises(TypeError):
        server.recon_probe(topic="edge inference")


def test_h07_malformed_inputs_stay_inside_envelope(tmp_path, monkeypatch):
    """H07 [OBSERVED-KIT]: bad session/lexicon/followups -> structured errors."""
    server = _kit_isolated(_kit_server(), monkeypatch, tmp_path)
    bad_probe = json.loads(server.recon_probe(topic="x", session_id="../../evil"))
    assert bad_probe["status"] == "error"
    assert "cache_key" in bad_probe

    bad_dist = json.loads(server.recon_distill(session_id="not-a-rec-session"))
    assert bad_dist["status"] == "error"
    assert bad_dist["cache_key"] is None

    probe = json.loads(server.recon_probe(topic="edge inference"))
    bad_lex = json.loads(
        server.recon_distill(session_id=probe["session_id"], lexicon_json="not-json")
    )
    assert bad_lex["status"] == "error"
    bad_follow = json.loads(
        server.recon_delta(session_id=probe["session_id"], followups="nope")  # type: ignore[arg-type]
    )
    assert bad_follow["status"] == "error"

    missing = json.loads(server.recon_distill(session_id="rec_deadbeef01"))
    assert missing["status"] == "error"
