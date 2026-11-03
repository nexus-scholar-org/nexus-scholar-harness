# Phase 3 extraction and synthesis: UX review and wireframes (2026-11-02)

UX and methodology review of the pipeline from title/abstract includes to a written synthesis:
the harness stages `src/scholar_harness/pipeline/extraction.py` (stage 5), `indexing.py` (6),
`matrix.py` (7), `graph.py` (8) and `synthesis.py` (9), and the kit code they call in
`tools/scholar-rag-kit/src/scholar_rag/matrix.py` and `synthesis.py`. Full-text retrieval and
full-text eligibility are included because they belong between Phase 2 and extraction and are
currently missing.

Status: **proposal**. Code-reading review by an AI reviewer (Claude); no user testing.
Line references point to the code as of 2026-11-02. Previous phase: [Phase 2 screening](../phase2-screening/README.md).

## Where things are

| Item | Live (private, share from its Share menu) | Source in this folder |
| :-- | :-- | :-- |
| Wireframe canvas, 7 boards + 10 finding notes | https://claude.ai/artifact/1EA6KZLjdRUvLEvErEym3G | [`wireframes/`](wireframes/) (`canvas.json` + one `.dc.html` per board) |

Figures on the boards are one consistent worked example that continues the Phase 2 numbers
(276 reports sought). Titles, DOIs and quotes are placeholders. Boards rendered and checked on 2026-11-02.

## Boards

| # | File | Shows |
| :-- | :-- | :-- |
| 1 | `Main.dc.html` | Six steps (Retrieve, Eligibility, Extract text, Index, Data, Synthesis), two of them new |
| 2 | `Retrieval.dc.html` | 276 sought, open access / uploaded / missing, reasons, PDF upload, PRISMA "not retrieved" |
| 3 | `Eligibility.dc.html` | Full-text criteria drafted with page quotes, exclusion reasons, reports linked to studies |
| 4 | `Quality.dc.html` | Per-report text quality: scanned, columns mixed, tables missing; abstract-only count |
| 5 | `Matrix.dc.html` | Study × column grid with Verified / Edited / Not reported / Draft cells, source quote per cell |
| 6 | `Synthesis.dc.html` | One draft per research question; each claim's support, contradiction or missing passage |
| 7 | `States.dc.html` | No full text, scanned PDF, index out of date, no extraction model, thin evidence, citation lookup failed |

## Findings

| # | Finding | Code / evidence | Severity |
| :-- | :-- | :-- | :-- |
| X1 | No full-text step: no retrieval accounting and no full-text eligibility with reasons, both required by PRISMA 2020 | `pipeline/coordinator.py` stage order | Major |
| X2 | Missing PDF or failed parse becomes an abstract-only document, counted as extracted, no journal event, then used as evidence | `extraction.py:171`, `extraction.py:33` | Major |
| X3 | No LLM is passed to the matrix, so each cell is the first sentence of the top passage, cut at the first "." ("97.3%" → "97"); no verification step | `pipeline/matrix.py:104`; rag `matrix.py:213` | Major |
| X4 | The fallback retrieval repeats the identical query; LLM extraction errors are swallowed | rag `matrix.py:197-204`, `matrix.py:229` | Moderate |
| X5 | "Entailment" is rescaled cosine similarity (cosine 0.7 = VERIFIED; unrelated = 0.5); without an LLM the synthesis is the passages themselves, so the check is circular; no claims = rate 1.0 | rag `synthesis.py:139`, `:309-318` | Major |
| X6 | Synthesis covers only the first research question, from 5 passages, written as `literature_review.md` | `pipeline/synthesis.py:107`; rag `synthesis.py:275` | Major |
| X7 | Citation graph is built but unused (no `boost_dois`), despite "PageRank-boosted retrieval" in the architecture table; a graph error stops the run before synthesis | `pipeline/graph.py:37`, `pipeline/synthesis.py:21` | Moderate |
| X8 | A stale-extraction rejection at indexing raises `TypeError` with no journal row (known, preserved on purpose) | `indexing.py:42` | Moderate |
| X9 | Embedding model fixed in code (all-MiniLM-L6-v2, 384 dims), not per protocol or language | `indexing.py:28` | Minor |
| X10 | Strengths: no invented prose, per-cell citation token, retrieval scoped to one study, identity from the accepted manifest, failures propagate without fabricated success | rag `matrix.py:195`; `extraction.py` | Keep |

## Where fixes belong

- **Harness (this repo):** X1 retrieval and full-text eligibility stages and their audit events,
  X2 flag abstract-only documents and keep them out of evidence by default, X6 one synthesis per
  RQ, X7 make the graph stage non-blocking, X8 repair the audit call so the refusal is readable.
- **scholar-rag-kit (canonical repo, fork + PR):** X3 leave cells empty as "to extract" without
  a model instead of the first sentence, X4, X5 replace similarity with a real support check and
  stop scoring snippets against themselves, X9 configurable embedder.
- **scholar-pdf-kit:** OCR and text-quality checks for board 4.
- **Contract v1 gate:** new stage artifacts (retrieval record, full-text decisions, verified
  extraction cells) need typed contract models before code.
