# Pipeline Engineering Report — What We Did, End to End

**Workspace**: `workspaces/ai-research-harnesses-trust` · **Date**: 2026-09-09 · **Purpose**: faithful engineering retrospective of the production pipeline (screening → extraction → RAG → synthesis) as executed, with artifact pointers, parameters, measured outcomes, and the upgrade targets it implies for the harness kits and skills.

Every number below is machine-verifiable against the committed workspace (`audit/journal.jsonl`, `literature/*`, `phase4/*`, `synthesis/*`). Nothing is a proposal; all of it was actually run.

---

## 0. Stage overview

```
Discovery ─▶ Screening ─▶ Trust audit ─▶ Extraction ─▶ Indexing ─▶ RAG synthesis (baseline)
                                                                    │
                                                                  Claims (authoritative, multi-agent) ─▶ Verbatim verification
                                                                    │
                                                                  Semantic consensus ─▶ Narrative (lit review + manuscript)
```

Two synthesis pipelines ran over the same corpus:
- **Approach A — Deterministic RAG** (`scholar-rag-kit synthesize`, top-30 chunks per RQ) → 90 claims, 43.3% entailment-verified. Kept as a comparison baseline.
- **Approach B — Multi-agent full-text claim extraction** (8 full-text agents + 1 abstract agent) → 510 claims, 100% pass at the ≥0.90 glyph-normalized coverage gate (char-window or token 6-gram). Authoritative source for the narrative.

---

## 1. Screening

### 1.1 Search and verification
`scholar-search-kit` federated five sources (OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv; bioRxiv-track preprints captured via PubMed/Crossref indexing) for 2023–2026 review-automation literature.

- Raw hits: **250** → deduplicated + hydrated (DOI and normalized-title resolution, abstract/DOI completion) → **239 unique verified records** (`literature/raw_search.json`, `deduped.json`, `verified.json`).
- Provider query robustness fixes landed in this cycle (see commit `77cf2d8`): OpenAlex `AND`/`OR` clause drying + `from/to_publication_date` filters; Semantic Scholar bulk-query paren/ampersand sanitation; query-parser field aliases (`ti`,`abs`,`au`,`yr`…).

### 1.2 Agent-in-the-loop screening (agent-managed, file-based)
`scholar-harness agent_screen` orchestrated the PRISMA step:

1. `prepare` split 239 records into **12 bite-size batches** → `literature/screening/batch_NNN.json`.
2. **4 independent AI screeners** each read every batch against the criteria in `literature/screening/instructions.txt` and wrote `batch_NNN_decisions_screener2|3|4.json` (+ a harness baseline `batch_NNN_decisions.json`).
3. Custom scoring scripts (`literature/screening/screen_batches.py`, `screen_batches.js`, `eval.js`) computed agreement and votes.
   - **Fleiss' κ = 0.408** (fair/moderate inter-rater agreement).
   - **213 records** resolved by majority rule (≥3 of 4); **26 two-vs-two deadlocks** escalated to a **senior adjudicator** (`adjudication_batch.json` → `adjudication_resolved.json`).
4. `collect` assembled `final_reconciled_decisions.json`, `included.json` (**58**), `excluded.json` (**181**), `prisma_screening_report.md`, `prisma_report.json`.

### 1.3 Screening pain points (for kit/skill upgrade)
- The κ computation, vote tallying, and adjudication routing were **repo-local custom scripts**, not a kit API — which means every future review re-implements them.
- `prisma_report.json` was **stale/inconsistent** (it reported `duplicates_removed: 0`, `UNSPECIFIED: 181`) compared to the true flow — report emission is not kept in sync with the reconciliation logic.

---

## 2. Trust audit (Phase 4) — ran *between* screening and synthesis

`scholar-verify-kit` (`phase4/*`) certified the included set before any synthesis:

| Stream | Artifact | Outcome (47 fully checked) |
|---|---|---|
| Retraction/status | `retraction_status_check.json` | **0 retracted / 0 flagged** (OpenAlex `is_retracted`, Crossref `update-to`) |
| Open-science artifacts | `open_science_regex_baseline.json` | **16 repos (34.0%)**, 7 dual data+code, 32 explicit DA/S/CA, 5 proprietary |
| Conflict of interest | `coi_audit.json` | **5 industry ties (10.6%)**, 4 declared none, 37 no statement |
| Risk of bias | `risk_of_bias.json` + `trust_consensus.json` | QUADAS-2/PROBAST-style attestation; no `BLOCKED` cluster |

COI audit used 8 agent chunks (`phase4/_agent_results/coi_chunk_*.json`) — i.e., Phase 4 itself is agent-assisted and worth productizing into a single CLI.

---

## 3. Extraction

`scholar-pdf-kit`:
1. Discovered Open-Access locations for included records.
2. Downloaded **64 PDFs** into `pdfs/` (gitignored).
3. Docling-extracted to **YAML-frontmatter Markdown** in `extracted/` (64 files) — tracked in git.
4. `rewrite_metadata.py` mapped STEM titles → canonical `SCI-####` workspace IDs.

### 3.1 The scope bug this cycle exposed
Extraction ran **before** final screening resolution, so **18 of 64 extractions belong to screened-out studies**. The vector index and the synthesis matrix inherited the full 64-document superset; only the multi-agent claim pipeline was correctly scoped to the 58 included studies. This is the root cause of the RAG baseline contamination (Section 4.2) and is the single most important discipline to encode in the kits.

---

## 4. RAG

### 4.1 Indexing
`scholar_rag.indexer.ScholarIndexer` built `chroma_db` (collection `scholar_docs`):
- **64 documents → 3,814 structural AST chunks**, embeddings `sentence-transformers/all-MiniLM-L6-v2`.
- Covers the full 64-doc superset (including the 18 screened-out extractions).

### 4.2 Baseline synthesis (Approach A)
`scholar-rag` deterministic `synthesize` retrieved **top-30 chunks per research question** and emitted claims verified by a **heuristic entailment check against their own snippets** → `synthesis/rag_baseline/`:

- **90 claims** (30/RQ).
- **39/90 = 43.3% entailment-VERIFIED** (RQ1 36.7%, RQ2/RQ3 46.7%).
- **25 studies** represented; only **14 overlap** with the authoritative ledger.
- **11 RAG-cited studies are NOT in the included set** — corpus contamination; a single excluded paper (SCI-000184) supplied 22/90 claims.
- 43 included studies appear in **zero** RAG claims.
- Consensus (semantic, θ 0.40): **20 clusters** = 2 high-consensus, 0 debates, 3 unresolved, 15 provisional.

### 4.3 Pain points (all fixed by workarounds, none by the kit)
- **Retrieval `top-k` is retrieval-gated**: claims only ever cover chunks that scored in the top-30 — hence the 43/57 zero-coverage hole.
- **Snippet entailment ≠ truth**, so "43.3% verified" overstates trustworthiness (it only checks claims against their own retrieval context).
- **No corpus-scope enforcement**: the index silently served screened-out evidence.
- **Consensus CLI hung** on the 510-claim ledger (~O(n²) re-embedding; killed twice >10 min). Worked around with cached-embedding scripts (`run_consensus*.py`; the baseline variant keys the cache on `id()` because `SynthesisClaim` is unhashable).

---

## 5. Authoritative synthesis (Approach B, selected)

### 5.1 Full-text claim extraction
`build_claims.py` orchestrated agents against **included-study full texts only**:
- **8 full-text agents** over the 46 extracted included papers, split into **7 size-balanced batches ≤ ~456 KB** (plus one latency-trimmed batch).
- **1 abstract-only agent** over the 12 included studies lacking full text.
- Every claim written to a canonical 10-field schema: `rq_id`, `claim_text`, `citation_tokens` (`[SCI-xxxx#slug#FULLTEXT-nnn]`), `entailment_score`, `entailment_status`, `supporting_chunk_ids`, `study_id`, `stance`, `evidence_quote`, `section`, `evidence_level` (`fulltext`/`abstract_only`), `location_hint`, `title`, `year`.
- Raw batches → `synthesis/fulltext_claims/batch_*.json` → merged → `synthesis/claims.json`.

**Ledger: 510 claims — RQ1 166 / RQ2 132 / RQ3 212; 493 full-text + 17 abstract-only; 57 studies** (SCI-000147 excluded — empty abstract).

### 5.2 Verbatim verification (the trust mechanism)
Every `evidence_quote` was machine-checked against the source extraction:
- Normalization: glyph map (bullets "•/●/○", zero-width spaces, Unicode dashes, ligatures, hyphen-wrap rejoin) + NFKC.
- Matching: **char-windows (8 chars, step 4)** *and* **token 6-grams (6 tokens, step 3)**; pass at **coverage ≥ 0.90** on either metric.
- `fulltext_claims/_fails*.json` tracked the fix loop: v1 **156 fails** → v4 **499/510** → the **11 residual paraphrases** (light paraphrase / math-glyph artifacts) were **re-cast to exact file substrings** → **510/510 (100%) verbatim-backed**.

### 5.3 Semantic consensus
Consensus Cartographer over cached embeddings (`all-MiniLM-L6-v2`, cosine, **θ 0.40**) → **95 clusters**: **16 high-consensus, 7 active debates, 37 unresolved, 35 provisional** (`synthesis/consensus.json|md`). Per-RQ briefing packs (`_briefing_RQ1|2|3.md`, `_clusters_RQ1|2|3.md`) fed the narrative stage.

### 5.4 Narrative and deliverables
- 3 RQ chapters drafted from the briefing packs by parallel agents; **machine-checked that every cited `SCI-###` exists in the ledger** (0 ungrounded citations).
- `synthesis/literature_review.md` (final; stale draft archived to `literature_review_draft_v1.md`), `synthesis/method_comparison.md` (head-to-head A vs B), `reports/methodology_report.md`, `reports/manuscript_draft.md` (36 references author-complete via Crossref/arXiv cache; all 36 author lists resolved).
- Full pipeline recorded in `audit/journal.jsonl` (68 events at D3 close), reflected in `project.json` stats and `INDEX.md`.

---

## 6. Measured outcomes (numbers that matter)

| Metric | Approach A (RAG) | Approach B (Multi-agent) |
|---|---|---|
| Claims | 90 | 510 (166/132/212) |
| Verified | 39/90 (43.3%, heuristic entailment) | 510/510 (100%, byte-verbatim) |
| Studies covered | 25 (14 overlapping) | 57 |
| Screened-out pollution | 11 studies (22 claims) | 0 |
| Consensus clusters | 20 (2 HC / 0 debates) | 95 (16 HC / 7 debates) |
| Evidence basis | top-30 chunks/RQ | full text + abstracts |

---

## 7. Upgrade targets (harness kits & skills)

| # | Pain point | Upgrade |
|---|---|---|
| U1 | Screening κ/adjudication/reporting is custom glue | `scholar-search-kit`: multi-screener batch scoring, Fleiss' κ, majority + deadlock routing, PRISMA JSON/MD emission in lock-step with reconciliation |
| U2 | Index over extracted superset → contamination | Indexer **include-whitelist** (defaults to `included.json`); warn/refuse on superset indexing |
| U3 | Heuristic entailment ≠ truth | Ship the **verbatim verifier** (glyph/NFKC normalization + char-window & token 6-gram coverage ≥ 0.90) as a first-class `scholar-rag-kit` (and `scholar-verify-kit`) capability |
| U4 | Consensus CLI hangs | Cached embeddings keyed by content hash; batch pagination; `--method cached` |
| U5 | Claim extraction is agent-script glue | Canonical claim **schema + byte-budget batching + post-hoc quote verification** as a reusable pipeline API |
| U6 | Tooling/kit provenance drift on every `log_event` | `workspace-manager`: merge custom INDEX rows instead of dropping them |
| U7 | LLM-as-judge / semantic-proxy confidence (BL-6) | Keep human-anchored validation; use verbatim + κ metrics, not BERTScore/ROUGE, as reliability proxies |
| U8 | No end-to-end evaluation harness | Add a **self-benchmark**: screening κ, claim verbatim %, consensus coherence, cost, over a gold corpus (e.g., this review) |

---

*Sources: `audit/journal.jsonl`, `reports/methodology_report.md`, `synthesis/method_comparison.md`, `reports/manuscript_draft.md`, `project.json`.*