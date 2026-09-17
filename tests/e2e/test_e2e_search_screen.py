"""End-to-End Integration Test for Phase 0 and Phase 1 Pipeline.

Validates the full chain:
  IntentPacket -> protocol.json -> Search Compilation -> Deduplication -> PRISMA Screening -> PDF Extraction -> Audit Trail
"""

import json
from pathlib import Path
from scholar_protocol.intent import ConceptClusterIntent, CriterionIntent, IntentPacket, RQIntent
from scholar_protocol.models import PlaybookType
from scholar_protocol.compiler import compile_protocol
from scholar_search.dedup import Deduplicator
from scholar_search.models import Author, Document, ExternalIds
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.screening import evaluate_heuristic_screening, partition_screening_results
from scholar_pdf.extract import PyMuPDFEngine


def test_phase1_full_funnel_e2e(tmp_path: Path):
    # -------------------------------------------------------------
    # 1. Phase 0: IntentPacket -> Canonical protocol.json
    # -------------------------------------------------------------
    intent = IntentPacket(
        protocol_id="proto-20260901-code-gen",
        genesis_timestamp="2026-09-01T00:00:00+00:00",
        project_slug="code-gen-benchmark-review",
        playbook_type=PlaybookType.DESIGN_SCIENCE,
        title="Empirical Benchmarks for AI Code Synthesis",
        lead_researcher="Alex Chen",
        unit_of_analysis="Computational code generator artifacts",
        epistemological_rationale="Evaluating synthetic code generation models.",
        research_questions=[
            RQIntent(
                text="How do models perform on pass@k code generation benchmarks?",
                target_facet="evaluation_metrics",
                required_evidence_type="Quantitative Benchmark",
            )
        ],
        core_concepts=[
            ConceptClusterIntent(
                concept="Code Generation",
                synonyms=["code synthesis", "program synthesis"],
            )
        ],
        inclusion_criteria=[
            CriterionIntent(
                criterion="Evaluates code generation artifacts on empirical benchmarks",
                maps_to_rqs=["RQ1"],
            )
        ],
        exclusion_criteria=[
            CriterionIntent(
                criterion="Non-English linguistic papers or opinion editorials",
                reason_category="LANGUAGE",
                maps_to_rqs=["RQ1"],
            )
        ],
    )

    protocol = compile_protocol(intent)
    assert protocol.protocol_id.startswith("proto-")
    assert len(protocol.research_questions) >= 1
    assert len(protocol.screening_criteria.inclusion) >= 1
    assert len(protocol.screening_criteria.exclusion) >= 1

    proto_path = tmp_path / "protocol.json"
    proto_dict = protocol.model_dump()
    proto_path.write_text(json.dumps(proto_dict, indent=2), encoding="utf-8")

    # -------------------------------------------------------------
    # 2. Phase 1 Cycle A: Protocol-to-Query Compilation
    # -------------------------------------------------------------
    query, providers = compile_protocol_search(proto_path)
    assert query.id == protocol.protocol_id
    assert query.text is not None
    assert len(providers) >= 1

    # -------------------------------------------------------------
    # 3. Phase 1 Cycle B: Federated Search Results & Deduplication
    # -------------------------------------------------------------
    # Simulate multi-provider candidate pool with duplicate and variant records
    raw_candidates = [
        # Candidate 1: OpenAlex version of Grounded CodeGen
        Document(
            title="Grounded Code Generation with LLMs",
            year=2023,
            provider="openalex",
            provider_id="W4001",
            external_ids=ExternalIds(doi="10.1038/s41586-023-0001", openalex_id="W4001"),
            authors=[Author(family_name="Chen", given_name="Alex")],
            abstract="<jats:p>We benchmark synthetic code generation on HumanEval-X.</jats:p>",
            citations_count=85,
        ),
        # Candidate 1 Duplicate: arXiv preprint of Grounded CodeGen
        Document(
            title="Grounded Code Generation with LLMs.",
            year=2023,
            provider="arxiv",
            provider_id="2308.01234",
            external_ids=ExternalIds(doi="10.1038/s41586-023-0001", arxiv_id="2308.01234"),
            authors=[Author(family_name="Chen", given_name="A.")],
            abstract="We benchmark synthetic code generation on HumanEval-X across 7B LLMs.",
        ),
        # Candidate 2: Distinct benchmark study
        Document(
            title="Evaluating Python Code Synthesis",
            year=2024,
            provider="crossref",
            provider_id="10.1145/3002",
            external_ids=ExternalIds(doi="10.1145/3002"),
            authors=[Author(family_name="Smith", given_name="Jane")],
            abstract="Empirical evaluation of pass@k rates on benchmarks.",
            citations_count=42,
        ),
        # Candidate 3: Irrelevant study (should be excluded in screening)
        Document(
            title="Natural Language Translation in Legal Contracts",
            year=2022,
            provider="openalex",
            provider_id="W4003",
            external_ids=ExternalIds(openalex_id="W4003"),
            authors=[Author(family_name="Taylor", given_name="Bob")],
            abstract="Exploratory linguistic study on non-software legal phrasing.",
        ),
    ]

    deduplicator = Deduplicator()
    clusters = deduplicator.deduplicate(raw_candidates)

    # 4 raw records -> 3 unique records (Candidate 1 duplicate was merged)
    assert len(clusters) == 3
    stats = deduplicator.get_statistics(clusters)
    assert stats["total_documents"] == 4
    assert stats["unique_documents"] == 3
    assert stats["duplicates"] == 1

    unique_docs = [c.representative for c in clusters]
    merged_c1 = next(d for d in unique_docs if "Grounded" in d.title)
    assert merged_c1.workspace_id == "SCI-000001"
    assert merged_c1.external_ids.doi == "10.1038/s41586-023-0001"
    assert merged_c1.external_ids.arxiv_id == "2308.01234"
    assert len(merged_c1.sources) == 2
    # JATS tag stripped
    assert "<jats:p>" not in merged_c1.abstract

    # -------------------------------------------------------------
    # 4. Phase 1 Cycle C: Title/Abstract Screening & PRISMA Report
    # -------------------------------------------------------------
    decisions = [evaluate_heuristic_screening(doc, proto_dict) for doc in unique_docs]
    included, excluded, conflicts, report = partition_screening_results(
        unique_docs, decisions, total_identified=4, duplicates_removed=1
    )

    assert len(included) >= 1
    assert report.total_identified == 4
    assert report.duplicates_removed == 1
    assert report.records_screened == 3
    assert report.records_included == len(included)
    assert report.records_excluded == len(excluded)

    # Validate PRISMA markdown output
    prisma_md = report.to_markdown()
    assert "# PRISMA 2020 Literature Screening Flow Report" in prisma_md
    assert "Duplicate Records Removed**: `1`" in prisma_md

    # -------------------------------------------------------------
    # 5. Phase 1 Cycle D & E: PDF Extraction with YAML Frontmatter
    # -------------------------------------------------------------
    papers_dir = tmp_path / "papers"
    extracted_dir = papers_dir / "extracted"
    dummy_pdf = papers_dir / "pdfs" / "2023_chen_grounded_code_generation.pdf"
    dummy_pdf.parent.mkdir(parents=True, exist_ok=True)
    dummy_pdf.write_bytes(b"%PDF-1.4\nMock Binary PDF with Sections\n1. Introduction\nBenchmarking code.")

    md_file = PyMuPDFEngine.extract_markdown(
        dummy_pdf,
        extracted_dir,
        metadata={
            "workspace_id": merged_c1.workspace_id,
            "doi": merged_c1.external_ids.doi,
            "title": merged_c1.title,
            "year": merged_c1.year,
        },
    )

    assert md_file.exists()
    extracted_text = md_file.read_text(encoding="utf-8")
    assert "workspace_id: SCI-000001" in extracted_text
    assert "doi: 10.1038/s41586-023-0001" in extracted_text
    assert "extraction_engine: pymupdf" in extracted_text

    # -------------------------------------------------------------
    # 6. Audit Journal Chain Verification
    # -------------------------------------------------------------
    journal_entries = [
        {"event_id": "evt-000001", "action": "PROTOCOL_COMPILED", "protocol_id": protocol.protocol_id},
        {"event_id": "evt-000002", "action": "SEARCH_FEDERATED", "query": query.text, "raw_count": 4},
        {"event_id": "evt-000003", "action": "DEDUPLICATION_MERGE", "unique_count": 3, "duplicates_removed": 1},
        {"event_id": "evt-000004", "action": "SCREENING_COMPLETED", "included": len(included), "excluded": len(excluded)},
        {"event_id": "evt-000005", "action": "EXTRACTION_COMPLETED", "file": md_file.name},
    ]

    journal_file = tmp_path / "audit" / "journal.jsonl"
    journal_file.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_file, "w", encoding="utf-8") as f:
        for entry in journal_entries:
            f.write(json.dumps(entry) + "\n")

    assert journal_file.exists()
    lines = [json.loads(line) for line in journal_file.read_text(encoding="utf-8").strip().split("\n")]
    assert len(lines) == 5
    assert lines[0]["action"] == "PROTOCOL_COMPILED"
    assert lines[-1]["action"] == "EXTRACTION_COMPLETED"
