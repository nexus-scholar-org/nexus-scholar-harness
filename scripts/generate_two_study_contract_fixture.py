"""Generate the closed two-study WP-01 cross-kit handoff fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scholar_harness.contracts import canonical_fingerprint, corpus_snapshot_fingerprint

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "contracts"
    / "v1"
    / "two_study_artifact_chain.json"
)

WORKSPACE_ID = "WSP-two-study"
PROTOCOL_FP = "sha256:" + "a" * 64
COMMIT = "4" * 40


def _producer(package: str) -> dict[str, str]:
    return {"package": package, "version": "1.0.0", "commit": COMMIT}


def _input(artifact: dict[str, Any]) -> dict[str, str]:
    return {
        "artifact_id": artifact["artifact_id"],
        "sha256": canonical_fingerprint(artifact),
    }


def _envelope(
    *,
    artifact_type: str,
    artifact_id: str,
    run_id: str,
    package: str,
    created_at: str,
    corpus_fingerprint: str,
    inputs: list[dict[str, str]],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "created_at": created_at,
        "producer": _producer(package),
        "workspace_id": WORKSPACE_ID,
        "run_id": run_id,
        "protocol_fingerprint": PROTOCOL_FP,
        "corpus_fingerprint": corpus_fingerprint,
        "inputs": inputs,
        "data": data,
    }


def build_fixture() -> dict[str, Any]:
    corpus_data = {
        "corpus_id": "COR-two-study",
        "identity_algorithm_version": "identity-v1",
        "studies": [
            {
                "study_id": "STU-alpha",
                "source_record_ids": ["REC-alpha-doi", "REC-alpha-arxiv"],
                "alias_ids": ["SCI-000001"],
                "external_ids": {
                    "doi": ["10.1000/alpha"],
                    "arxiv": ["2401.00001"],
                },
                "title": "Shared short title",
                "publication_year": 2020,
            },
            {
                "study_id": "STU-beta",
                "source_record_ids": ["REC-beta-doi"],
                "alias_ids": ["SCI-000002"],
                "external_ids": {"doi": ["10.1000/beta"]},
                "title": "Shared short title",
                "publication_year": 2024,
            },
        ],
        "record_to_study": {
            "REC-alpha-doi": "STU-alpha",
            "REC-alpha-arxiv": "STU-alpha",
            "REC-beta-doi": "STU-beta",
        },
    }
    corpus_fp = corpus_snapshot_fingerprint(corpus_data)
    corpus = _envelope(
        artifact_type="corpus_snapshot",
        artifact_id="ART-corpus-two-study",
        run_id="RUN-discovery-two-study",
        package="scholar-search-kit",
        created_at="2026-09-18T10:00:00Z",
        corpus_fingerprint=corpus_fp,
        inputs=[],
        data=corpus_data,
    )

    binding = {
        "screening_run_id": "RUN-screening-two-study",
        "protocol_fingerprint": PROTOCOL_FP,
        "corpus_fingerprint": corpus_fp,
        "criteria_renderer_version": "1.0.0",
        "dedup_configuration_hash": "sha256:" + "c" * 64,
        "preparation_run_id": "RUN-screening-prepare-two-study",
    }
    batch = _envelope(
        artifact_type="screening_batch",
        artifact_id="ART-screening-batch-two-study",
        run_id="RUN-screening-two-study",
        package="nexus-scholar-harness",
        created_at="2026-09-18T10:01:00Z",
        corpus_fingerprint=corpus_fp,
        inputs=[_input(corpus)],
        data={
            "binding": binding,
            "batch_id": "batch-000",
            "batch_index": 0,
            "candidates": [
                {"study_id": "STU-alpha", "title": "Shared short title"},
                {"study_id": "STU-beta", "title": "Shared short title"},
            ],
        },
    )
    decisions = _envelope(
        artifact_type="screening_decisions",
        artifact_id="ART-screening-decisions-two-study",
        run_id="RUN-screening-two-study",
        package="nexus-scholar-harness",
        created_at="2026-09-18T10:02:00Z",
        corpus_fingerprint=corpus_fp,
        inputs=[_input(batch)],
        data={
            "binding": binding,
            "batch_id": "batch-000",
            "decisions": [
                {
                    "decision_id": "SCR-alpha-human",
                    "study_id": "STU-alpha",
                    "screener_id": "reviewer-1",
                    "method": "HUMAN",
                    "decision": "INCLUDE",
                    "reason": "Meets frozen criteria.",
                    "decided_at": "2026-09-18T10:01:30Z",
                },
                {
                    "decision_id": "SCR-beta-human",
                    "study_id": "STU-beta",
                    "screener_id": "reviewer-1",
                    "method": "HUMAN",
                    "decision": "INCLUDE",
                    "reason": "Meets frozen criteria.",
                    "decided_at": "2026-09-18T10:01:40Z",
                },
            ],
        },
    )
    documents = _envelope(
        artifact_type="document_manifest",
        artifact_id="ART-documents-two-study",
        run_id="RUN-extraction-two-study",
        package="scholar-pdf-kit",
        created_at="2026-09-18T10:03:00Z",
        corpus_fingerprint=corpus_fp,
        inputs=[_input(decisions)],
        data={
            "documents": [
                {
                    "document_id": "DOC-alpha-pdf",
                    "study_id": "STU-alpha",
                    "source_hash": "sha256:" + "d" * 64,
                    "content_status": "VALID",
                    "extracted_path": "extracted/STU-alpha.md",
                    "extraction_method": "DETERMINISTIC_RULE",
                },
                {
                    "document_id": "DOC-beta-pdf",
                    "study_id": "STU-beta",
                    "source_hash": "sha256:" + "e" * 64,
                    "content_status": "VALID",
                    "extracted_path": "extracted/STU-beta.md",
                    "extraction_method": "DETERMINISTIC_RULE",
                },
            ]
        },
    )
    claims = _envelope(
        artifact_type="claims_ledger",
        artifact_id="ART-claims-two-study",
        run_id="RUN-synthesis-two-study",
        package="scholar-rag-kit",
        created_at="2026-09-18T10:04:00Z",
        corpus_fingerprint=corpus_fp,
        inputs=[_input(documents)],
        data={
            "claims": [
                {
                    "claim_id": "CLM-alpha-effect",
                    "claim_text": "Alpha reports an effect.",
                    "claim_kind": "finding",
                    "study_ids": ["STU-alpha"],
                    "evidence_ids": ["EV-alpha-effect"],
                    "citation_tokens": [
                        "[rag:v2:WSP-two-study:STU-alpha:CHK-alpha-0001]"
                    ],
                    "generation_method": "LLM",
                },
                {
                    "claim_id": "CLM-beta-null",
                    "claim_text": "Beta reports a null result.",
                    "claim_kind": "finding",
                    "study_ids": ["STU-beta"],
                    "evidence_ids": ["EV-beta-null"],
                    "citation_tokens": [
                        "[rag:v2:WSP-two-study:STU-beta:CHK-beta-0001]"
                    ],
                    "generation_method": "LLM",
                },
            ],
            "evidence": [
                {
                    "evidence_id": "EV-alpha-effect",
                    "study_id": "STU-alpha",
                    "document_id": "DOC-alpha-pdf",
                    "locator": "page 4",
                    "quote": "An effect was observed.",
                    "extraction_method": "DETERMINISTIC_RULE",
                    "source_hash": "sha256:" + "d" * 64,
                },
                {
                    "evidence_id": "EV-beta-null",
                    "study_id": "STU-beta",
                    "document_id": "DOC-beta-pdf",
                    "locator": "page 7",
                    "quote": "No effect was observed.",
                    "extraction_method": "DETERMINISTIC_RULE",
                    "source_hash": "sha256:" + "e" * 64,
                },
            ],
        },
    )
    return {
        "fixture_version": "1.0.0",
        "case_id": "WP01-TWO-STUDY-CHAIN",
        "description": (
            "Two same-title studies remain distinct through corpus, screening, "
            "documents, and claims with exact parent hashes."
        ),
        "artifacts": [corpus, batch, decisions, documents, claims],
    }


def render_fixture() -> str:
    return json.dumps(build_fixture(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render_fixture()
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else None
        if actual != expected:
            print(f"stale or missing: {OUTPUT.relative_to(REPO_ROOT)}")
            return 1
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
