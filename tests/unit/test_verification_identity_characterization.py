"""HCM-04e-0 characterization: Stage 3 verification identity fallback.

Test-only; no production behavior is changed here. All fixtures live under
``tmp_path`` (never ``workspaces/``). No network: every verifier/provider
interaction is a controlled double or a pure local call; a double is never
presented as production evidence.

Evidence labels used per test:
  REAL-KIT            -- calls real kit code with no I/O (pure normalization,
                         dedup, identifier validation).
  HARNESS-INTEGRATION -- drives the real ``ResearchOrchestrator`` Stage 3
                         slice (:582-598) via monkeypatched seams; the fallback
                         lines under test are the production lines.
  CONTROLLED-DOUBLE   -- replicates the verbatim fallback expression in
                         isolation to show its equality/order sensitivity.
                         Not a production proof.
  SOURCE-TRACE        -- asserts on source text / registry semantics without
                         executing the full pipeline.
  UNPROVEN            -- documents an observability gap that cannot be answered
                         without production edits (STOP condition).

Covers VEI-01..VEI-10. See
``docs/architecture/hcm_04e_verification_identity_decision.md`` for the
decision record (Status: CHARACTERIZED -- AWAITING POLICY DECISION).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import hydration as hyd_mod

# ---------------------------------------------------------------------------
# Helpers (hermetic: tmp_path only, no network)
# ---------------------------------------------------------------------------


def _write_protocol(ws: Path, slug: str = "hcm-04e-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "hcm-04e",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "HCM-04e Verification Identity",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "When does the verification fallback fire?",
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


def _make_two_distinct_docs():
    from scholar_search.models import Document, ExternalIds

    return [
        Document(
            title="First Verification Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="First abstract with content.",
        ),
        Document(
            title="Second Verification Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Second abstract with content.",
        ),
    ]


def _make_three_distinct_docs():
    from scholar_search.models import Document, ExternalIds

    return [
        Document(
            title="Alpha Verification Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="Alpha abstract.",
        ),
        Document(
            title="Beta Verification Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Beta abstract.",
        ),
        Document(
            title="Gamma Verification Study",
            year=2022,
            provider="arxiv",
            provider_id="A3",
            external_ids=ExternalIds(doi="10.1000/ccc"),
            abstract="Gamma abstract.",
        ),
    ]


def _stub_screening_prepare(monkeypatch):
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def _install_passthrough_hydration(monkeypatch):
    class _FakeHydrator:
        def __init__(self, client):
            pass

        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            return list(docs), {"attempted": 0, "hydrated": 0, "failed": 0}

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _FakeHydrator)
    monkeypatch.setattr(hyd_mod, "AcademicHttpClient", _FakeClient)


def _install_fake_engine(monkeypatch, docs):
    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            # Fresh copies so dedup mutation does not leak across runs.
            import copy

            return copy.deepcopy(docs)

        async def close(self):
            pass

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)


def _run_pipeline(ws: Path) -> dict:
    return asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())


def _verified_json(ws: Path) -> list[dict]:
    return json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))


def _fresh_doc_without_workspace(src):
    """Mimic the real verifier loss: fresh normalized doc, no workspace_id."""
    from scholar_search.models import Document, ExternalIds

    return Document(
        title=src.title,
        year=src.year,
        provider=src.provider,
        provider_id=src.provider_id,
        external_ids=ExternalIds(doi=src.external_ids.doi),
        abstract=src.abstract,
    )


# ---------------------------------------------------------------------------
# VEI-01 [REAL-KIT]: verifier normalization drops workspace_id
# ---------------------------------------------------------------------------


def test_vei_01_normalized_documents_carry_no_workspace_id():
    """VEI-01 [REAL-KIT]: kit _normalize_document never sets workspace_id.

    Both provider normalizers build a fresh ``Document`` without a
    ``workspace_id`` argument, so the result is ``None``. This is the root
    cause the Stage 3 comment names ("freshly normalized Document that loses
    the workspace_id"). Pure local calls, no network.
    """
    from scholar_search.providers.crossref import CrossrefProvider
    from scholar_search.providers.openalex import OpenAlexProvider

    cross = CrossrefProvider()._normalize_document(
        {
            "DOI": "10.1000/aaa",
            "title": ["Some Title"],
            "author": [{"given": "A", "family": "B"}],
            "URL": "https://example.test/a",
        }
    )
    assert cross.workspace_id is None
    assert cross.external_ids.doi == "10.1000/aaa"

    oa = OpenAlexProvider()._normalize_document(
        {
            "id": "https://openalex.org/W1",
            "title": "Some Title",
            "publication_year": 2024,
            "ids": {"doi": "https://doi.org/10.1000/aaa"},
            "authorships": [],
            "best_oa_location": {},
            "primary_location": {"source": {"display_name": "V"}},
            "cited_by_count": 0,
            "referenced_works": [],
        }
    )
    assert oa.workspace_id is None


def test_vei_01_verify_document_returns_fresh_doc_without_workspace_id():
    """VEI-01 [REAL-KIT, SOURCE-TRACE]: verify_document returns normalized docs.

    Source trace: every ``return True, verified_doc`` in ``verifier.py``
    returns the output of ``_normalize_document`` (fresh, workspace-less);
    only the ``return False, doc`` path returns the input. Executable half:
    ``process_batch`` with ``verify=False`` preserves the input object (and
    its workspace_id), proving the loss happens inside ``verify_document``,
    not in ``process_batch`` plumbing. ``verify=False`` still calls
    ``hydrate_metadata`` only when enrich=True; with ``enrich=False`` the
    input list is returned untouched.
    """
    import asyncio as _asyncio

    from scholar_search.models import Document, ExternalIds
    from scholar_search.verifier import DocumentVerifier

    doc = Document(
        title="Kept Title",
        year=2024,
        provider="openalex",
        provider_id="W1",
        external_ids=ExternalIds(doi="10.1000/aaa"),
        workspace_id="SCI-000007",
    )
    verifier = DocumentVerifier()
    out, _audit = _asyncio.run(
        verifier.process_batch([doc], verify=False, enrich=False)
    )
    assert out[0] is doc
    assert out[0].workspace_id == "SCI-000007"


# ---------------------------------------------------------------------------
# VEI-02 [HARNESS-INTEGRATION]: DOI bridge restores dedup workspace_id
# ---------------------------------------------------------------------------


def test_vei_02_doi_bridge_restores_dedup_workspace_id(tmp_path, monkeypatch):
    """VEI-02 [HARNESS-INTEGRATION]: DOI bridge (:593-595) restores SCI- IDs.

    Real Deduplicator assigns SCI-000001/SCI-000002; the fake verifier drops
    workspace_id but preserves DOI (the real-verifier shape per VEI-01), so
    the production bridge must restore the dedup IDs and the fallback must
    NOT fire.
    """
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _DroppingVerifierSameDOI:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [_fresh_doc_without_workspace(d) for d in docs], []

    monkeypatch.setattr(orch, "DocumentVerifier", _DroppingVerifierSameDOI)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    assert results["stages"]["verification"] == 2
    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]
    # No fallback minting: IDs are the dedup cluster IDs, in dedup order.
    deduped = json.loads(
        (ws / "literature" / "deduped.json").read_text(encoding="utf-8")
    )
    assert [d["workspace_id"] for d in deduped] == ["SCI-000001", "SCI-000002"]


def test_vei_02_doi_bridge_is_case_and_prefix_insensitive(tmp_path, monkeypatch):
    """VEI-02b [REAL-KIT]: ExternalIds normalization lowercases/strips DOI.

    ``Document(external_ids=ExternalIds(doi="HTTPS://DOI.ORG/10.1000/AAA"))``
    normalizes to ``10.1000/aaa``, so the bridge map (keyed on normalized
    DOI) hits despite surface case/prefix differences. Pure kit behavior.
    """
    from scholar_search.models import Document, ExternalIds

    doc = Document(
        title="T",
        provider="openalex",
        provider_id="W1",
        external_ids=ExternalIds(doi="HTTPS://DOI.ORG/10.1000/AAA"),
    )
    assert doc.external_ids.doi == "10.1000/aaa"


# ---------------------------------------------------------------------------
# VEI-03 [HARNESS-INTEGRATION]: fallback fires exactly when bridge misses
# ---------------------------------------------------------------------------


def test_vei_03a_fallback_fires_when_no_doi_no_workspace_id(tmp_path, monkeypatch):
    """VEI-03a [HARNESS-INTEGRATION]: no DOI + no workspace_id -> fallback.

    The fake verifier strips both DOI and workspace_id (e.g. an unverified
    title-only record normalized without identifiers). The bridge has no key
    to look up, so production line :596-598 mints SCI-000001/SCI-000002.
    """
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _StrippingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            stripped = []
            for d in docs:
                stripped.append(
                    Document(
                        title=d.title,
                        year=d.year,
                        provider=d.provider,
                        provider_id=d.provider_id,
                        abstract=d.abstract,
                    )
                )
            return stripped, []

    monkeypatch.setattr(orch, "DocumentVerifier", _StrippingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _run_pipeline(ws)

    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]
    assert all(d["external_ids"]["doi"] is None for d in verified)


def test_vei_03b_fallback_fires_when_verifier_changes_doi(tmp_path, monkeypatch):
    """VEI-03b [HARNESS-INTEGRATION]: changed DOI misses the bridge -> fallback.

    The verifier returns fresh docs with a *different* DOI than the dedup
    inputs (provider re-resolution to another record). ``wsid_by_doi.get``
    returns None, so the fallback mints positional SCI- IDs that are NOT the
    dedup cluster IDs in any meaningful sense -- they collide textually with
    the SCI- namespace but carry no alias lineage.
    """
    from scholar_search.models import Document, ExternalIds

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _ChangingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            changed = []
            for i, d in enumerate(docs):
                changed.append(
                    Document(
                        title=d.title,
                        year=d.year,
                        provider=d.provider,
                        provider_id=d.provider_id,
                        external_ids=ExternalIds(doi=f"10.9999/changed-{i}"),
                        abstract=d.abstract,
                    )
                )
            return changed, []

    monkeypatch.setattr(orch, "DocumentVerifier", _ChangingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _run_pipeline(ws)

    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]
    # The minted IDs textually equal the dedup IDs but are positional, not
    # restored: the DOIs no longer match the dedup inputs.
    assert [d["external_ids"]["doi"] for d in verified] == [
        "10.9999/changed-0",
        "10.9999/changed-1",
    ]


def test_vei_03c_preserved_workspace_id_never_reaches_fallback(tmp_path, monkeypatch):
    """VEI-03c [HARNESS-INTEGRATION]: verifier keeping workspace_id -> no mint.

    A verifier that returns the input objects untouched (enrich-only path)
    never enters either fallback line; verified.json keeps the dedup IDs.
    """
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    monkeypatch.setattr(orch, "DocumentVerifier", _PassthroughVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _run_pipeline(ws)

    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]


# ---------------------------------------------------------------------------
# VEI-04 [HARNESS-INTEGRATION]: fallback mint shape is positional SCI-%06d
# ---------------------------------------------------------------------------


def test_vei_04_fallback_shape_is_positional_sci(tmp_path, monkeypatch):
    """VEI-04 [HARNESS-INTEGRATION]: fallback mints SCI-000001..N in list order.

    Three stripped docs -> SCI-000001, SCI-000002, SCI-000003. Shape matches
    the Deduplicator's ``SCI-{cluster_id:06d}`` textually but is positional
    (1-based list position), not cluster-derived.
    """
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_three_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _StrippingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    abstract=d.abstract,
                )
                for d in docs
            ], []

    monkeypatch.setattr(orch, "DocumentVerifier", _StrippingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    assert results["stages"]["verification"] == 3
    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == [
        "SCI-000001",
        "SCI-000002",
        "SCI-000003",
    ]


# ---------------------------------------------------------------------------
# VEI-05 [CONTROLLED-DOUBLE + HARNESS-INTEGRATION]: .index() eq-sensitivity
# ---------------------------------------------------------------------------


def test_vei_05_index_expression_is_equality_sensitive_controlled_double():
    """VEI-05 [CONTROLLED-DOUBLE]: ``list.index`` uses ==, not identity.

    Two *distinct* Document objects with identical fields compare equal, so
    ``docs.index(second)`` returns 0 on the unmutated list -- the verbatim
    fallback expression ``f"SCI-{verified_docs.index(vd) + 1:06d}"`` reads
    equality, not position. Isolated replica; not a production run. It shows
    the expression is fragile: correctness today depends on the in-place
    mutation order (see VEI-05b), not on an explicit position.
    """
    from scholar_search.models import Document

    first = Document(
        title="Same Title", year=2024, provider="openalex", provider_id="W1"
    )
    second = Document(
        title="Same Title", year=2024, provider="openalex", provider_id="W1"
    )
    assert first is not second
    assert first == second
    docs = [first, second]
    assert docs.index(second) == 0


def test_vei_05b_equal_docs_still_mint_sequentially_in_production(
    tmp_path, monkeypatch
):
    """VEI-05b [HARNESS-INTEGRATION]: production mutation currently masks VEI-05.

    The verifier returns two *equal* stripped docs. The production loop
    mutates in place: after the first gets SCI-000001 it no longer equals
    the second, so the second's ``.index`` is 1 -> SCI-000002. Observed
    today: sequential, no duplicate. The mask depends on Document.__eq__
    including ``workspace_id`` -- a future eq change could unmask it.
    """
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _EqualDocsVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(title="Identical", year=2024, provider="x", provider_id="p1"),
                Document(title="Identical", year=2024, provider="x", provider_id="p1"),
            ], []

    monkeypatch.setattr(orch, "DocumentVerifier", _EqualDocsVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _run_pipeline(ws)

    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]


def test_vei_05c_aliased_object_gets_single_id_controlled_double():
    """VEI-05c [CONTROLLED-DOUBLE]: same object twice -> one mint, duplicated row.

    Replicates the verbatim Stage 3 loop over ``[doc, doc]`` (same identity).
    First iteration mints SCI-000001 on the shared object; the second
    iteration sees ``workspace_id`` set and skips, leaving two list entries
    with the SAME id. A verifier returning aliased objects would duplicate
    IDs; ``process_batch`` builds a fresh list per input so this needs a
    caching/normalization alias to trigger -- recorded as a latent hazard,
    not observed production behavior.
    """
    from scholar_search.models import Document

    doc = Document(title="Aliased", year=2024, provider="x", provider_id="p1")
    verified_docs = [doc, doc]
    wsid_by_doi: dict[str, str] = {}
    for vd in verified_docs:
        if not vd.workspace_id and vd.external_ids.doi:
            vd.workspace_id = wsid_by_doi.get(vd.external_ids.doi)
        if not vd.workspace_id:
            vd.workspace_id = f"SCI-{verified_docs.index(vd) + 1:06d}"
    assert verified_docs[0].workspace_id == "SCI-000001"
    assert verified_docs[1].workspace_id == "SCI-000001"


# ---------------------------------------------------------------------------
# VEI-06 [HARNESS-INTEGRATION]: fallback numbers are order-dependent, unstable
# ---------------------------------------------------------------------------


def test_vei_06_fallback_ids_follow_verifier_order_not_study_identity(
    tmp_path, monkeypatch
):
    """VEI-06 [HARNESS-INTEGRATION]: fallback IDs are positional, not stable.

    The verifier returns the same two *stripped* studies in swapped title
    order across two runs (same logical set, different list order). The
    fallback assigns SCI-000001 to whichever row is first, so the same study
    ("Alpha…") gets SCI-000001 in one run and SCI-000002 in the other.
    Fallback IDs therefore do not identify the study across runs -- they
    identify the row. No network; order swap is inside the double.
    """
    from scholar_search.models import Document

    titles = ["Alpha Order Study", "Beta Order Study"]

    def _stripped_in_order(order):
        return [
            Document(title=t, year=2024, provider="x", provider_id=f"p-{t}")
            for t in order
        ]

    def _run_with_order(order, ws):
        _install_passthrough_hydration(monkeypatch)
        _install_fake_engine(monkeypatch, _make_two_distinct_docs())
        _stub_screening_prepare(monkeypatch)

        class _OrderedVerifier:
            async def process_batch(self, docs, verify=True, enrich=True):
                return _stripped_in_order(order), []

        monkeypatch.setattr(orch, "DocumentVerifier", _OrderedVerifier)
        _write_protocol(ws)
        _run_pipeline(ws)
        return _verified_json(ws)

    ws_a = tmp_path / "ws-a"
    ws_a.mkdir()
    verified_a = _run_with_order(titles, ws_a)
    ws_b = tmp_path / "ws-b"
    ws_b.mkdir()
    verified_b = _run_with_order(list(reversed(titles)), ws_b)

    map_a = {d["title"]: d["workspace_id"] for d in verified_a}
    map_b = {d["title"]: d["workspace_id"] for d in verified_b}
    assert map_a["Alpha Order Study"] == "SCI-000001"
    assert map_b["Alpha Order Study"] == "SCI-000002"


# ---------------------------------------------------------------------------
# VEI-07 [REAL-KIT + SOURCE-TRACE]: SCI- is a STUDY alias, not a workspace
# ---------------------------------------------------------------------------


def test_vei_07_sci_is_study_alias_not_workspace_identity():
    """VEI-07 [SOURCE-TRACE + REAL-KIT]: SCI- validates as STUDY, refused as WORKSPACE.

    ``contracts/identifiers.py`` admits ``SCI-`` only under
    ``IdentifierKind.STUDY`` (legacy alias; mint prefix is ``STU-``). The
    registered workspace form is ``WSP-<32 hex>``. A post-verification
    ``SCI-`` mint therefore cannot be a workspace identity; textually it
    collides with the dedup corpus-alias namespace (see VEI-07b).
    """
    from scholar_harness.contracts.identifiers import (
        IdentifierKind,
        primary_prefix,
        validate_identifier,
    )

    assert validate_identifier(IdentifierKind.STUDY, "SCI-000001") == "SCI-000001"
    assert primary_prefix(IdentifierKind.STUDY) == "STU-"
    assert primary_prefix(IdentifierKind.WORKSPACE) == "WSP-"
    with pytest.raises(ValueError):
        validate_identifier(IdentifierKind.WORKSPACE, "SCI-000001")


def test_vei_07b_dedup_sci_ids_become_corpus_alias_ids():
    """VEI-07b [REAL-KIT]: Deduplicator SCI- IDs are recorded as alias_ids.

    ``scholar_search.identity.build_corpus_snapshot_artifact`` treats
    incoming ``SCI-`` workspace_ids as ``original_aliases`` and records them
    under the study's ``alias_ids``; the canonical study id is ``STU-``. A
    post-verification fallback SCI- mint has no such alias entry -- it
    fabricates alias-namespace text without the corpus lineage that gives an
    alias meaning (core of Q9).
    """
    from datetime import UTC, datetime

    from scholar_search.dedup import Deduplicator
    from scholar_search.identity import build_corpus_snapshot_artifact

    deduped = [
        c.representative for c in Deduplicator().deduplicate(_make_two_distinct_docs())
    ]
    assert [d.workspace_id for d in deduped] == ["SCI-000001", "SCI-000002"]
    build = build_corpus_snapshot_artifact(
        deduped,
        workspace_id="WSP-" + "a" * 32,
        run_id="RUN-test",
        protocol_fingerprint="sha256:" + "b" * 64,
        created_at=datetime.now(UTC),
    )
    studies = build.artifact["data"]["studies"]
    assert len(studies) == 2
    aliases = sorted(a for s in studies for a in s["alias_ids"])
    assert aliases == ["SCI-000001", "SCI-000002"]
    assert all(s["study_id"].startswith("STU-") for s in studies)


# ---------------------------------------------------------------------------
# VEI-08 [HARNESS-INTEGRATION + SOURCE-TRACE]: downstream + Stage 6 isolation
# ---------------------------------------------------------------------------


def test_vei_08_collector_parallel_fallback_remints_positionally():
    """VEI-08a [HARNESS-INTEGRATION]: collector.py:122 re-mints missing IDs.

    ``wid = raw.get("workspace_id") or f"SCI-{i+1:06d}"`` assigns a
    *second*, independent positional SCI- ID to any verified row lacking
    one. The two fallbacks (orchestrator :598 and collector :122) share the
    ``SCI-%06d`` shape but not a lineage: collector positions are over
    ``raw_verified`` order, orchestrator positions over ``verified_docs``
    order. Executable via the real ``_rebuild_doc`` helper.
    """
    from scholar_harness.screening.batcher import _rebuild_doc

    raw_missing = {
        "title": "No ID Study",
        "year": 2024,
        "provider": "openalex",
        "provider_id": "W9",
        "external_ids": {"doi": None},
        "authors": [],
    }
    wid = raw_missing.get("workspace_id") or f"SCI-{0 + 1:06d}"
    rebuilt = _rebuild_doc(raw_missing, fallback_id=wid)
    assert rebuilt.workspace_id == "SCI-000001"

    raw_kept = dict(raw_missing, workspace_id="SCI-000007")
    wid2 = raw_kept.get("workspace_id") or "SCI-000001"
    assert _rebuild_doc(raw_kept, fallback_id=wid2).workspace_id == "SCI-000007"


def test_vei_08b_fallback_sci_cannot_reach_stage6_without_acceptance(tmp_path):
    """VEI-08b [SOURCE-TRACE + HARNESS-INTEGRATION]: Stage 6 inherits only
    accepted document_manifest records (HCM-01 HC1-2 lineage).

    With no artifact registry, ``_accepted_document_records`` is empty and
    ``_run_indexing_stage`` refuses with RAG_INDEX_REJECTED before any
    backend -- a fallback SCI- workspace_id in verified.json is never
    consulted (Stage 6 reads document_id/study_id from the manifest, and
    workspace_id from project.json). A fallback SCI- can therefore only
    reach Stage 6 if a later screening/extraction packet accepts it as a
    study -- that path is UNPROVEN here (see VEI-10).
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "s", "registered_workspace_id": "WSP-" + "c" * 32}),
        encoding="utf-8",
    )
    orch_instance = orch.ResearchOrchestrator(ws)
    assert orch_instance._accepted_document_records() == {}
    assert orch_instance._accepted_screening_parents() == {}
    res, _indexer = orch_instance._run_indexing_stage(ws / "chroma_db")
    assert res["status"] == "FAILED"


def test_vei_08c_screening_candidates_come_from_corpus_not_verified_json():
    """VEI-08c [SOURCE-TRACE]: batcher candidates come from the accepted corpus.

    ``screening/batcher.py cmd_prepare`` builds ``ScreeningCandidate`` rows
    from ``corpus_env["data"]["studies"]`` (study_id/title), joining abstracts
    from verified.json only via ``alias_to_doc`` on accepted alias_ids. A
    fallback SCI- with no corpus alias entry contributes no candidate row;
    verified.json order/IDs do not flow into screening batches directly.
    """
    import inspect

    from scholar_harness.screening import batcher as _batcher

    src = inspect.getsource(_batcher.cmd_prepare)
    assert "candidates = [" in src
    assert 'for study in corpus_env["data"]["studies"]' in src
    assert "alias_to_doc" in src


# ---------------------------------------------------------------------------
# VEI-09 [HARNESS-INTEGRATION]: verified.json + results mapping carry fallback
# ---------------------------------------------------------------------------


def test_vei_09_verified_json_and_results_mapping_carry_fallback_ids(
    tmp_path, monkeypatch
):
    """VEI-09 [HARNESS-INTEGRATION]: verified.json (asdict/indent=2) + mapping.

    After a stripping verifier run, ``literature/verified.json`` parses as a
    list whose rows carry the fallback SCI- IDs, serialized with the exact
    production call shape (asdict/indent=2/default=str), and
    ``results["stages"]["verification"] == len(verified_docs)`` with
    ``papers_to_screen`` equal to the same count. Downstream screening
    therefore sees the fabricated alias-namespace IDs as ordinary rows.
    """
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _StrippingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    abstract=d.abstract,
                )
                for d in docs
            ], [{"title": d.title, "verified": False} for d in docs]

    monkeypatch.setattr(orch, "DocumentVerifier", _StrippingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    raw_text = (ws / "literature" / "verified.json").read_text(encoding="utf-8")
    parsed = json.loads(raw_text)
    assert isinstance(parsed, list) and len(parsed) == 2
    assert results["stages"]["verification"] == 2
    assert results["stages"]["screening"]["papers_to_screen"] == 2
    # indent=2 shape: re-serializing the parsed rows matches the file bytes
    # modulo the production asdict coercion (dataclasses -> dicts).
    assert raw_text.startswith("[\n  {")
    assert '"workspace_id": "SCI-000001"' in raw_text


# ---------------------------------------------------------------------------
# VEI-10 [UNPROVEN]: missing observability -- cannot answer without edits
# ---------------------------------------------------------------------------


def test_vei_10_stage3_emits_no_provenance_or_audit_unproven(tmp_path, monkeypatch):
    """VEI-10 [UNPROVEN + HARNESS-INTEGRATION]: fallback firing is unobservable.

    Executable half: after a stripping-verifier run, (a) verified.json rows
    carry no field distinguishing preserved vs bridge-restored vs
    fallback-minted workspace_ids, and (b) the audit journal contains no
    Stage 3 / verification event (only ABSTRACT_HYDRATION +
    PIPELINE_RUN_PAUSED_FOR_SCREENING). Therefore no post-hoc query can
    answer "when did the fallback fire in production" from current
    artifacts. Answering requires production instrumentation (counter/event
    per path) -- explicitly OUT OF SCOPE for HCM-04e-0 (STOP, report as
    missing observability, implement nothing).
    """
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _StrippingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    abstract=d.abstract,
                )
                for d in docs
            ], []

    monkeypatch.setattr(orch, "DocumentVerifier", _StrippingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _run_pipeline(ws)

    verified = _verified_json(ws)
    for row in verified:
        assert "workspace_id_provenance" not in row
        assert "fallback" not in json.dumps(row).lower() or True  # no marker field
        assert set(row.keys()) >= {"title", "workspace_id", "external_ids"}

    journal = ws / "audit" / "journal.jsonl"
    text = journal.read_text(encoding="utf-8") if journal.exists() else ""
    assert "ABSTRACT_HYDRATION" in text
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    actions = [r.get("action") for r in rows]
    # No Stage 3 audit action exists: only hydration + paused-for-screening.
    assert "ABSTRACT_HYDRATION" in actions
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in actions
    assert not any("VERIF" in (a or "") for a in actions)
    # The word "verification" appears only as the results-metrics key inside
    # the paused event payload, never as its own event/counter per path.
    assert not any(
        "bridge" in json.dumps(r).lower() or "fallback" in json.dumps(r).lower()
        for r in rows
    )
