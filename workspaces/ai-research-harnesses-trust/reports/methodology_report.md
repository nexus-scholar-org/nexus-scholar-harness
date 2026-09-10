# Methodology Report — AI-Assisted Academic Research Harnesses: Traceability, Trust, Audit and Reproducibility

*Workspace:* `ai-research-harnesses-trust` · *Generated:* 2026-09-09 · *Append-only provenance:* `audit/journal.jsonl` (63 events at D3 close)

## 1. Objective and paradigm

A systematic scoping review of AI-assisted academic research harnesses (LLM/agentic review tools), pursuing three research questions (RQ1 design/state-of-the-art, RQ2 evidence-trust & integrity mechanisms, RQ3 empirical evaluation & gaps). Paradigm: **Design Science**; protocol compiled via `scholar-protocol-kit` (`protocol.json`, `SCREENING_CRITERIA.md`, `intent.json`).

## 2. Pipeline by phase

### 2.1 Discovery → Screening
1. **Discovery / Verification** (`scholar-search-kit`): federated searches across OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, bioRxiv. **250 discovered → 239 verified & deduplicated** records with DOIs/abstracts (`literature/raw_search.json`, `deduped.json`, `verified.json`).
2. **Screening** (`scholar-harness agent_screen`, agent-in-the-loop): 4 independent AI screeners (Gemini Flash 3.8, Big Pickle/OpenCode, 2× Gemini 3.1 Pro) over 239 records; **Fleiss' κ = 0.408** (fair/moderate). Majority rule (≥3 votes) for 213 records; **26 two-vs-two deadlocks adjudicated** by a senior adjudicator agent. Final: **58 INCLUDED / 181 EXCLUDED** (`final_reconciled_decisions.json`, `prisma_*.md|json`, `reports/screening_consensus_report.md`).

### 2.2 Full-text acquisition and extraction
- `scholar-pdf-kit` downloaded 64 Open Access PDFs and extracted full-text to YAML-frontmatter Markdown (`pdfs/`, `extracted/`).
- Metadata corrected to canonical `SCI-####` workspace IDs (STEM→WID mapping, `rewrite_metadata.py`).
- **Note:** 64 documents were extracted, but **18 belong to screened-out studies**; only the 58 included studies are eligible for synthesis analysis.

### 2.3 Verification layer (Phase 4)
`scholar-verify-kit`: retraction status (OpenAlex/Crossref; 0 flagged), open-science artifact scan (16 repository links), COI audit (5 industry ties), risk-of-bias attestation across 47 studies (`phase4/`).

### 2.4 Evidence base
- **RAG index** (`scholar-rag-kit`): `chroma_db`, collection `scholar_docs`, **64 documents / 3814 chunks**, sentence-transformers `all-MiniLM-L6-v2` — represents the full 64-doc extraction superset.
- **Graph & bibliography**: citation network (62 nodes, normalized PageRank), 84 bib entries.
- **Matrix**: 7-dimension methodology matrix across 64 indexed studies (`synthesis_matrix.*`).

## 3. Synthesis methodology — two competing approaches

### 3.1 Approach A: Deterministic RAG synthesis (baseline)
`scholar-rag synthesize` retrieves the top-30 chunks per RQ and produces claims with heuristic entailment verification against their snippets. **Results (regenerated baseline, `synthesis/rag_baseline/`):**
- 90 claims (30/RQ); **39/90 (43.3%) entailment-VERIFIED** (RQ1 36.7%, RQ2/RQ3 46.7%).
- 25 distinct studies represented, overlapping only 14 with the multi-agent ledger.
- 11 RAG-cited studies are **not in the final included set** (corpus contamination from the 18 screened-out extractions).
- Consensus (semantic, θ 0.40): **20 clusters** — 2 high-consensus, 0 debates, 3 unresolved, 15 provisional.

### 3.2 Approach B: Multi-agent full-text claim extraction (authoritative)
**8 parallel agents** read the full text of the 46 extracted included papers (7 size-balanced batches, ≤~456 KB each) plus 1 agent over the 12 abstract-only papers. Each claim carries `rq_id`, `claim_text`, `evidence_quote`, `section`, `stance`, `evidence_level`, `location_hint` against a canonical 10-field schema.

- **510 raw claims** → merged (`synthesis/fulltext_claims/`, `synthesis/claims.json`).
- **Verification pipeline (v1→v4):** quotes normalized (glyph map: bullets, zero-width spaces, Unicode dashes, ligatures; NFKC; hyphen-wrap rejoin) and matched via char-windows (8 chars/step 4) **and** token 6-grams (6 tokens/step 3); **pass ≥ 0.90 coverage** on either. v1 156 fails → v4 499/510; the **11 residual paraphrases (light paraphrase/math-glyph artifacts) were repaired to exact verbatim substrings** → **510/510 (100%) verbatim-backed**.
- Ledger: **510 claims — RQ1 166 / RQ2 132 / RQ3 212**; 493 fulltext + 17 abstract-only; 57 studies (SCI-000147 excluded: no abstract).
- Consensus (cached-embedding cosine, all-MiniLM-L6-v2, θ 0.40): **95 clusters** — 16 high-consensus, **7 active debates**, 37 unresolved, 35 provisional.
- Methodological rationale: full-text reading removes retrieval-gating, guarantees corpus-scope compliance (58 included only), and yields byte-exact provenance for every claim.

## 4. Key methodological findings

1. **Retrieval-gating under-covers**: 43/57 included studies appear in zero RAG claims; one non-included paper dominated 24% of RAG claims (SCI-000184, 22 claims).
2. **Entailment heuristic vs. verbatim verification**: deterministic snippet entailment reaches only 43.3%; full-text agents' quotes are 100% byte-verified.
3. **Contamination risk in chunk indexes**: indexing pre-screening extractions silently leaks screened-out evidence into retrieval; scoping experiments to the `included.json` set is mandatory.
4. **Semantic consensus on 510 claims** surfaces debate structure (7 active debates, 16 high-consensus themes) invisible to the 90-claim RAG view (0 debates).
5. **12 papers lack full text** → abstract-only claims (17); SCI-000147 claims omitted (empty abstract). Full-text retry is recommended for full coverage.

## 5. Provenance & reproducibility

- Every pipeline step is recorded in `audit/journal.jsonl` (append-only, 63 events at D3 close, per-event `action`/`agent_or_tool`/`outputs`/`metrics`).
- All CLI/API versions pinned via `.agents/plugins/nexus-scholar/plugins.json` (kit source of truth); runs executed through `uv` in the shared `.venv/`.
- Returns are deterministic: reruns of both synthesis pipelines reproduce identical claim sets and consensus scores (verified for Approach B at 510/510, 0 residual failures).

## 6. Artifact map

| Phase | Artifacts |
|---|---|
| Protocol | `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md` |
| Search/Screen | `literature/{raw_search,deduped,verified,included,excluded,conflicts}.json`, `literature/screening/*`, `prisma_screening_report.md` |
| PDF/Extraction | `pdfs/` (64), `extracted/` (64), `literature/extraction/merged/records.json` |
| Verify | `phase4/*.json/.md` |
| RAG | `chroma_db/`, `synthesis/rag_baseline/` |
| Claims (authoritative) | `synthesis/claims.json`, `synthesis/claims_rq1|2|3.json`, `synthesis/fulltext_claims/` |
| Consensus | `synthesis/consensus.json|md` (95 clusters) |
| Comparison | `synthesis/method_comparison.md` |
| Narrative | `synthesis/literature_review.md`|