"""Focused HCM-04g tests for the neutral extraction stage.

Stage 5 (fulltext extraction over included studies, no invented prose) lives
in ``scholar_harness.pipeline.extraction``; the orchestrator delegates and
maps the outcome identically. Every test is hermetic (``tmp_path`` only, no
network; the PDF engine is faked or used for its static shape only) and
asserts zero behavior change: verbatim stem/DOI/PDF helpers, byte-identical
frontmatter template and filenames, existing-file skip idempotence,
engine-failure warning fallthrough, no audit or registry writes, and
identical results mapping.

Mapping to the HCM-04g packet:

- HCM4G-01 helper shim identity (``orch.X is stage.X`` for all three)
- HCM4G-02 engine path unchanged (same ``PyMuPDFEngine`` object, no seam)
- HCM4G-03 filename parity (workspace/study/DOI/doc precedence + sanitizing)
- HCM4G-04 PDF locator precedence (slug, DOI, prefix glob, miss)
- HCM4G-05 frontmatter byte parity (golden, incl. ``ensure_ascii=False``)
- HCM4G-06 no invented prose (verbatim abstract or placeholder; no
  Methodology/Results/Limitations)
- HCM4G-07 skip-existing idempotence (rerun leaves bytes alone)
- HCM4G-08 fallback on engine failure (warning + frontmatter, no raise)
- HCM4G-09 PDF success path (engine return recorded, not frontmatter-only)
- HCM4G-10 no audit or registry from the stage
- HCM4G-11 results mapping identical (orchestrator delegates + maps)
- HCM4G-12 move-not-duplicate (Stage 5 region has no inline loop)
- HCM4G-13 minimal signature + outcome names + transport guard

Negatives are the mutation halves:

- NEG-01 restore-inline-loop -> move-not-duplicate guard fails
- NEG-02 alter-template -> golden fails
- NEG-03 drop-skip -> idempotence fails
- NEG-04 force-raise-on-engine-failure -> fallback test fails
- NEG-05 suppress-warning -> log-capture test fails
- NEG-06 byte-divergence -> orchestrator/stage byte-parity probe fails

Carry-forward debt TD-HCM-TEST-SEAMS: the ``SearchEngine`` /
``Deduplicator`` / ``DocumentVerifier`` orchestrator-namespace shims stay
(fidelity stubs patch them). This packet adds NO fourth broad seam: the
class-level ``PyMuPDFEngine.extract_markdown`` patch works regardless of
import site and fidelity never reaches Stage 5 with a live engine, so no
``orchestrator.__dict__`` fallback is added (proven by HCM4G-02/C16-style
static-shape checks below).
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from pathlib import Path

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import extraction as ext_mod

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_workspace_identity(ws: Path, project_id: str) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": project_id, "registered_workspace_id": FIXTURE_WORKSPACE_ID}
        ),
        encoding="utf-8",
    )


def _write_protocol(ws: Path, slug: str = "extraction-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "extraction-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Extraction Stage Parity",
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


def _run_stage(docs, pdfs_dir, extracted_dir, **kw):
    return ext_mod.run_extraction(
        included_documents=docs, pdfs_dir=pdfs_dir, extracted_dir=extracted_dir, **kw
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


# ---------------------------------------------------------------------------
# HCM4G-01 shim identity + HCM4G-02 engine path (NEG-01 companion)
# ---------------------------------------------------------------------------


def test_helper_shim_identity_all_three_helpers():
    """HCM4G-01: orchestrator names ARE the stage objects (move, not copy)."""
    assert orch._study_doi is ext_mod._study_doi
    assert orch._extraction_file_stem is ext_mod._extraction_file_stem
    assert orch._study_pdf is ext_mod._study_pdf
    assert orch.run_extraction is ext_mod.run_extraction
    assert orch.ExtractionOutcome is ext_mod.ExtractionOutcome


def test_engine_path_unchanged_and_no_orchestrator_seam():
    """HCM4G-02: same PyMuPDFEngine object; no broad orchestrator fallback."""
    import scholar_pdf.extract as pdf_extract

    assert ext_mod.PyMuPDFEngine is pdf_extract.PyMuPDFEngine
    # The static shape is what hermetic tests patch: class-level
    # PyMuPDFEngine.extract_markdown works regardless of import site.
    assert isinstance(
        inspect.getattr_static(ext_mod.PyMuPDFEngine, "extract_markdown"),
        staticmethod,
    )
    # No fourth broad seam: the stage never consults orchestrator.__dict__.
    # Repair-1 pattern: import-statement guard (prose may mention it).
    text = Path(ext_mod.__file__).read_text(encoding="utf-8")
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
    assert not any("orchestrator" in s for s in out)
    assert "__dict__.get(" not in text
    assert "_REAL_" not in text
    # The orchestrator no longer binds the kit engine directly.
    orch_text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_pdf.extract import" not in orch_text


# ---------------------------------------------------------------------------
# HCM4G-03 filename parity (NEG-02 companion: precedence/sanitizing)
# ---------------------------------------------------------------------------


def test_stem_precedence_workspace_study_doi_doc():
    assert (
        ext_mod._extraction_file_stem(
            {"workspace_id": "SCI-000009", "external_ids": {"doi": "10.1/aa/bb"}}
        )
        == "SCI-000009"
    )
    # workspace_id wins over study_id (filename only, never identity).
    assert (
        ext_mod._extraction_file_stem(
            {
                "workspace_id": "SCI-000009",
                "study_id": "STU-1",
                "external_ids": {"doi": "10.1/aa/bb"},
            }
        )
        == "SCI-000009"
    )
    # Empty workspace_id falls back to study_id.
    assert (
        ext_mod._extraction_file_stem(
            {
                "workspace_id": "",
                "study_id": "STU-000007",
                "external_ids": {"doi": "10.1/aa/bb"},
            }
        )
        == "STU-000007"
    )
    # DOI fallback with / and : sanitized.
    assert (
        ext_mod._extraction_file_stem({"external_ids": {}, "doi": "10.1/aa:b"})
        == "10.1_aa_b"
    )
    assert ext_mod._study_doi({"external_ids": {"doi": "10.1/x"}, "doi": "10.9/y"}) == (
        "10.1/x"
    )
    # Nothing -> "doc".
    assert ext_mod._extraction_file_stem({}) == "doc"
    # Shim parity: orchestrator names agree (same objects, same outputs).
    assert orch._extraction_file_stem({}) == "doc"
    assert orch._study_doi({}) == ""


# ---------------------------------------------------------------------------
# HCM4G-04 PDF locator precedence
# ---------------------------------------------------------------------------


def test_study_pdf_precedence_slug_doi_prefix_miss(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    doc = {"workspace_id": "SCI-000009", "external_ids": {"doi": "10.1/aa/bb"}}
    # Miss first.
    assert ext_mod._study_pdf(pdf_dir, doc) is None

    # Slug candidate wins over DOI candidate.
    slug_hit = pdf_dir / "SCI-000009.pdf"
    slug_hit.write_bytes(b"%PDF-1.4")
    doi_hit = pdf_dir / "10.1_aa_bb.pdf"
    doi_hit.write_bytes(b"%PDF-1.4")
    assert ext_mod._study_pdf(pdf_dir, doc) == slug_hit

    # Without the slug file, the DOI candidate is used.
    slug_hit.unlink()
    assert ext_mod._study_pdf(pdf_dir, doc) == doi_hit

    # Without exact candidates, a DOI-prefix glob hit is used.
    doi_hit.unlink()
    prefixed = pdf_dir / "10.1_aa_bb-v2.pdf"
    prefixed.write_bytes(b"%PDF-1.4")
    assert ext_mod._study_pdf(pdf_dir, doc) == prefixed

    # No DOI and no files -> None.
    assert (
        ext_mod._study_pdf(pdf_dir, {"workspace_id": "SCI-000999", "doi": "x"}) is None
    )


# ---------------------------------------------------------------------------
# HCM4G-05 frontmatter byte parity (golden) + NEG-02 alter-template
# ---------------------------------------------------------------------------


GOLDEN_DOC = {
    "workspace_id": "SCI-000001",
    "title": "Real Study Title",
    "doi": None,
    "external_ids": {},
    "abstract": "Empirically measured latency under load.",
    "authors": [{"family_name": "Doe", "given_name": "Jane"}],
    "year": 2024,
}

GOLDEN_BYTES = (
    "---\n"
    'workspace_id: "SCI-000001"\n'
    'doi: ""\n'
    'title: "Real Study Title"\n'
    'authors: [{"family_name": "Doe", "given_name": "Jane"}]\n'
    "year: 2024\n"
    'extraction_engine: "metadata"\n'
    "---\n"
    "\n"
    "## Abstract\n"
    "\n"
    "Empirically measured latency under load.\n"
)


def test_frontmatter_byte_parity_golden(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"

    outcome = _run_stage([dict(GOLDEN_DOC)], pdfs, ext)

    assert outcome.count == 1
    assert len(outcome.documents) == 1
    md = ext / "SCI-000001.md"
    assert outcome.documents[0] == md
    assert md.read_text(encoding="utf-8") == GOLDEN_BYTES
    assert outcome.metadata_frontmatter_only == [str(md)]


def test_frontmatter_preserves_unicode_ensure_ascii_false(tmp_path):
    """The template uses json.dumps(..., ensure_ascii=False): raw unicode."""
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    doc = {
        "workspace_id": "SCI-000002",
        "title": "Étude sur l’extraction — naïve",
        "external_ids": {"doi": "10.1/ünï"},
        "abstract": "Résumé véritatif.",
        "authors": [{"family_name": "Müller", "given_name": "Zoë"}],
        "year": 2023,
    }

    _run_stage([doc], pdfs, ext)

    text = (ext / "SCI-000002.md").read_text(encoding="utf-8")
    assert "Étude sur l’extraction — naïve" in text
    assert "Müller" in text
    assert "\\u" not in text.split("authors:")[1].split("\n")[0]


def test_year_none_renders_raw_and_missing_title_untitled(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    doc = {"workspace_id": "SCI-000003", "external_ids": {}, "year": None}

    _run_stage([doc], pdfs, ext)

    text = (ext / "SCI-000003.md").read_text(encoding="utf-8")
    assert 'title: "Untitled"' in text
    assert "year: None\n" in text
    assert "## Abstract\n\nNo abstract provided.\n" in text


# ---------------------------------------------------------------------------
# HCM4G-06 no invented prose
# ---------------------------------------------------------------------------


def test_no_invented_prose_verbatim_or_placeholder(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    docs = [
        {
            "workspace_id": "SCI-000010",
            "title": "T1",
            "external_ids": {},
            "abstract": "Measured verbatim abstract.",
            "authors": [],
            "year": 2024,
        },
        {
            "workspace_id": "SCI-000011",
            "title": "T2",
            "external_ids": {},
            "authors": [],
            "year": 2024,
        },
    ]

    _run_stage(docs, pdfs, ext)

    for stem, body in (
        ("SCI-000010", "Measured verbatim abstract."),
        ("SCI-000011", "No abstract provided."),
    ):
        text = (ext / f"{stem}.md").read_text(encoding="utf-8")
        assert body in text
        without_abstract_heading = text.replace("## Abstract", "")
        assert "Methodology" not in without_abstract_heading
        assert "Results" not in without_abstract_heading
        assert "Limitations" not in without_abstract_heading
        assert (
            "Evaluated using standard benchmarks and controlled baseline comparisons."
            not in text
        )


# ---------------------------------------------------------------------------
# HCM4G-07 skip-existing idempotence (NEG-03 drop-skip)
# ---------------------------------------------------------------------------


def test_skip_existing_is_idempotent_and_not_frontmatter_only(tmp_path):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    ext.mkdir()
    sentinel = ext / "SCI-000020.md"
    sentinel.write_text("SENTINEL -- do not rewrite\n", encoding="utf-8")

    doc = {
        "workspace_id": "SCI-000020",
        "title": "Changed Title",
        "external_ids": {},
        "abstract": "Changed abstract.",
        "authors": [],
        "year": 2025,
    }

    first = _run_stage([doc], pdfs, ext)
    assert sentinel.read_text(encoding="utf-8") == "SENTINEL -- do not rewrite\n"
    assert first.documents == [sentinel]
    # A skipped file is NOT recorded as metadata-frontmatter-only.
    assert first.metadata_frontmatter_only == []

    second = _run_stage([doc], pdfs, ext)
    assert sentinel.read_text(encoding="utf-8") == "SENTINEL -- do not rewrite\n"
    assert second.documents == [sentinel]
    assert second.metadata_frontmatter_only == []


# ---------------------------------------------------------------------------
# HCM4G-08 fallback on engine failure (NEG-04 force-raise + NEG-05 warning)
# ---------------------------------------------------------------------------


def test_fallback_on_engine_failure_warns_and_writes_frontmatter(
    tmp_path, monkeypatch, caplog
):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    doc = {
        "workspace_id": "SCI-000030",
        "title": "PDF Study",
        "external_ids": {"doi": "10.1/fallback"},
        "abstract": "Verbatim fallback abstract.",
        "authors": [],
        "year": 2024,
    }
    (pdfs / "SCI-000030.pdf").write_bytes(b"%PDF-1.4 fake")

    def _boom(pdf, out_dir, metadata=None):
        raise RuntimeError("pymupdf boom")

    monkeypatch.setattr(ext_mod.PyMuPDFEngine, "extract_markdown", staticmethod(_boom))

    with caplog.at_level(logging.WARNING, logger="scholar_harness.pipeline.extraction"):
        outcome = _run_stage([doc], pdfs, ext)

    # No raise: warning + frontmatter fallback.
    assert outcome.count == 1
    md = ext / "SCI-000030.md"
    assert outcome.documents == [md]
    assert outcome.metadata_frontmatter_only == [str(md)]
    text = md.read_text(encoding="utf-8")
    assert 'extraction_engine: "metadata"' in text
    assert "Verbatim fallback abstract." in text
    assert any(
        "PyMuPDF extraction failed for SCI-000030" in r.message
        and "pymupdf boom" in r.message
        for r in caplog.records
    )


def test_warning_suppression_mutation_detected_by_caplog(tmp_path, monkeypatch, caplog):
    """NEG-05: if the warning call is deleted, no warning record exists.

    This test pins the positive (warning IS emitted); deleting the
    ``logger.warning`` line makes it fail, which is the mutation signal.
    """
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    doc = {
        "workspace_id": "SCI-000031",
        "title": "Warn Study",
        "external_ids": {},
        "abstract": "A.",
        "authors": [],
        "year": 2024,
    }
    (pdfs / "SCI-000031.pdf").write_bytes(b"%PDF-1.4 fake")

    def _warn_boom(pdf, out_dir, metadata=None):
        raise RuntimeError("warn boom")

    monkeypatch.setattr(
        ext_mod.PyMuPDFEngine, "extract_markdown", staticmethod(_warn_boom)
    )

    with caplog.at_level(logging.WARNING, logger="scholar_harness.pipeline.extraction"):
        _run_stage([doc], pdfs, ext)

    assert [
        r
        for r in caplog.records
        if "PyMuPDF extraction failed for SCI-000031" in r.message
    ] != []


# ---------------------------------------------------------------------------
# HCM4G-09 PDF success path
# ---------------------------------------------------------------------------


def test_pdf_success_path_records_engine_output(tmp_path, monkeypatch):
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    ext = tmp_path / "extracted"
    doc = {
        "workspace_id": "SCI-000040",
        "title": "Engine Study",
        "external_ids": {"doi": "10.1/eng"},
        "abstract": "Should not be used.",
        "authors": [{"family_name": "A", "given_name": "B"}],
        "year": 2022,
    }
    pdf = pdfs / "SCI-000040.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    seen: list[dict] = []

    def _fake_extract(pdf_path, out_dir, metadata=None):
        seen.append({"pdf": pdf_path, "out": out_dir, "metadata": dict(metadata or {})})
        target = Path(out_dir) / "SCI-000040.md"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        target.write_text("ENGINE OUTPUT\n", encoding="utf-8")
        return target

    monkeypatch.setattr(
        ext_mod.PyMuPDFEngine, "extract_markdown", staticmethod(_fake_extract)
    )

    outcome = _run_stage([doc], pdfs, ext)

    assert outcome.documents == [ext / "SCI-000040.md"]
    assert outcome.metadata_frontmatter_only == []
    assert (ext / "SCI-000040.md").read_text(encoding="utf-8") == "ENGINE OUTPUT\n"
    assert len(seen) == 1
    assert seen[0]["pdf"] == pdf
    assert seen[0]["out"] == ext
    assert seen[0]["metadata"] == {
        "workspace_id": "SCI-000040",
        "doi": "10.1/eng",
        "title": "Engine Study",
        "authors": [{"family_name": "A", "given_name": "B"}],
        "year": 2022,
    }


# ---------------------------------------------------------------------------
# HCM4G-10 no audit or registry from the stage
# ---------------------------------------------------------------------------


def test_stage_emits_no_audit_and_no_registry(tmp_path):
    ws = tmp_path / "ws"
    pdfs = ws / "pdfs"
    pdfs.mkdir(parents=True)
    ext = ws / "extracted"

    _run_stage([dict(GOLDEN_DOC)], pdfs, ext)

    assert _journal_rows(ws) == []
    assert list(ws.rglob("journal.jsonl")) == []
    assert list(ws.rglob("artifact_registry.json")) == []
    assert sorted(p.name for p in ext.iterdir()) == ["SCI-000001.md"]


# ---------------------------------------------------------------------------
# HCM4G-12 move-not-duplicate + HCM4G-13 signature/guard (NEG-01/NEG-06)
# ---------------------------------------------------------------------------


def test_stage_5_region_has_no_inline_extraction_loop():
    """HCM4G-12: orchestrator delegates; the loop lives in the stage."""
    source = Path(orch.__file__).read_text(encoding="utf-8")
    region = source.split("Stage 5: Fulltext Extraction", 1)[1]
    region = region.split("Stage 6:", 1)[0]
    body = region.split('results["stages"]["extraction"]', 1)[0]
    # No inline loop code in the delegation half (prose in the HCM-04g
    # comment names the moved concepts; only code patterns break parity).
    assert "for doc_item in" not in body
    assert "PyMuPDFEngine(" not in body
    assert "extract_markdown(" not in body
    assert "frontmatter = (" not in body
    assert "_study_pdf(" not in body
    assert "_extraction_file_stem(" not in body
    assert ".write_text(" not in body
    assert "metadata_frontmatter_only.append" not in body
    assert "run_extraction(" in body
    assert "extraction_outcome" in body
    # The mapping half still maps identically.
    mapping = region.split('results["stages"]["extraction"]', 1)[1]
    assert '"DONE"' in mapping
    assert "len(extracted_files)" in mapping
    assert "metadata_frontmatter_only" in mapping


def test_orchestrator_source_has_no_direct_pdf_engine_import():
    """NEG-01b: the orchestrator must not rebind the kit engine at module top."""
    text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_pdf.extract import" not in text
    assert "from ..scholar_pdf" not in text


def test_signature_minimal_and_outcome_names():
    """HCM4G-13: minimal keyword-only trio; outcome carries the three names."""
    sig = inspect.signature(ext_mod.run_extraction)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == [
        "included_documents",
        "pdfs_dir",
        "extracted_dir",
    ]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)
    assert all(p.default is inspect.Parameter.empty for p in params)
    import dataclasses

    assert sorted(f.name for f in dataclasses.fields(ext_mod.ExtractionOutcome)) == [
        "documents",
        "metadata_frontmatter_only",
    ]
    assert isinstance(
        ext_mod.ExtractionOutcome(documents=[], metadata_frontmatter_only=[]).count, int
    )
    assert ext_mod.ExtractionOutcome(documents=[Path("a.md")]).count == 1


def test_stage_has_no_console_transport_import():
    """HCM4G-13: neutral stage imports no console/FastAPI transport."""
    text = Path(ext_mod.__file__).read_text(encoding="utf-8")
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
    # Extraction stage calls the PDF kit (stage-rule producer import).
    assert any("scholar_pdf" in s and "scholar_harness" not in s for s in out), (
        "stage must import the scholar-pdf kit"
    )


# ---------------------------------------------------------------------------
# HCM4G-11 orchestrator/stage byte parity + results mapping (NEG-06)
# ---------------------------------------------------------------------------


class _FakeEngine:
    def __init__(self, providers=None):
        self.providers = providers or []

    async def search_all(self, query, dedup=False):
        return []

    async def close(self):
        pass


class _FakeDedup:
    def deduplicate(self, docs):
        return []


class _FakeVerifier:
    async def process_batch(self, docs, verify=True, enrich=True):
        return [], []


def _stub_upstream(monkeypatch):
    from types import SimpleNamespace

    import networkx as nx

    class _RecorderRetriever:
        def __init__(self, **kwargs):
            self.kw = kwargs

    class _FakeMatrix:
        def __init__(self, protocol=None, retriever=None, **kw):
            self.retriever = retriever

        def extract_all(self, output_dir):
            from pathlib import Path as _P

            out = _P(output_dir)
            return [], out / "synthesis_matrix.csv", out / "synthesis_matrix.json"

    class _FakeSynth:
        def __init__(self, retriever=None, **kw):
            self.retriever = retriever

        def synthesize(self, **kw):
            return SimpleNamespace(
                synthesis_markdown="# Synthesis\n",
                verified_claims_count=0,
                claims=[],
                entailment_rate=0.0,
            )

    class _FakeGraph:
        def __init__(self, client):
            self.client = client

        async def build_graph(self, dois):
            G = nx.DiGraph()
            for d in dois:
                G.add_node(d, label=d)
            return G

        @staticmethod
        def compute_pagerank(G):
            ranks = {n: 1.0 / max(len(G), 1) for n in G.nodes}
            nx.set_node_attributes(G, ranks, "pagerank")
            return ranks

        def export_json(self, G, path):
            import json as _j

            path.write_text(
                _j.dumps({"nodes": list(G.nodes), "links": list(G.edges)}),
                encoding="utf-8",
            )

    class _FakeVis:
        def __init__(self, html_path):
            self.html_path = html_path

        def generate_html(self, G):
            from pathlib import Path as _P

            _P(self.html_path).write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "Deduplicator", _FakeDedup)
    monkeypatch.setattr(orch, "DocumentVerifier", _FakeVerifier)
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _FakeMatrix)
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeSynth)
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def test_orchestrator_mapping_matches_direct_stage_bytes(tmp_path, monkeypatch):
    """HCM4G-11/NEG-06: orch delegation maps identically; bytes agree."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "extraction-stage-test")

    included = [
        {
            "workspace_id": "SCI-000001",
            "title": "Real Study Title",
            "doi": None,
            "external_ids": {},
            "abstract": "Empirically measured latency under load.",
            "authors": [{"family_name": "Doe", "given_name": "Jane"}],
            "year": 2024,
        },
        {
            "workspace_id": "SCI-000002",
            "title": "Second Study",
            "external_ids": {"doi": "10.1000/bbb"},
            "abstract": "Second abstract.",
            "authors": [],
            "year": 2023,
        },
    ]
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps(included), encoding="utf-8"
    )

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    mapping = results["stages"]["extraction"]
    assert mapping["status"] == "DONE"
    assert mapping["documents"] == 2
    assert len(mapping["metadata_frontmatter_only"]) == 2

    # Byte-identical probe: direct stage over the same inputs reproduces the
    # orchestrator's files byte for byte.
    direct_ext = tmp_path / "direct-extracted"
    direct_pdfs = tmp_path / "direct-pdfs"
    direct_pdfs.mkdir()
    direct_outcome = _run_stage([dict(d) for d in included], direct_pdfs, direct_ext)
    assert direct_outcome.count == mapping["documents"]
    assert direct_outcome.metadata_frontmatter_only != []
    for doc in included:
        stem = ext_mod._extraction_file_stem(doc)
        orch_bytes = (ws / "extracted" / f"{stem}.md").read_bytes()
        direct_bytes = (direct_ext / f"{stem}.md").read_bytes()
        assert orch_bytes == direct_bytes
    # The golden doc's orchestrator bytes equal the golden vector.
    assert (ws / "extracted" / "SCI-000001.md").read_text(
        encoding="utf-8"
    ) == GOLDEN_BYTES
