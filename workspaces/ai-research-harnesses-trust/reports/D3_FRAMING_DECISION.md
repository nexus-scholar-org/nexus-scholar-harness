# D3 Framing Decision — Early-Evidence / Living Scoping Review vs. PID-Tightened Review

**Date**: 2026-09-09
**Status**: Decision memo — recommended option pre-vetted; user adoption pending
**Workspace**: `workspaces/ai-research-harnesses-trust` · D3 deliverable | co-track A | thesis ch.4 + instrument validation
**Source of truth for all numbers**: `literature/included.json` (58 records), `literature/screening/final_reconciled_decisions.json`, `synthesis/claims.json`, `reports/manuscript_draft.md` (36 refs)

---

## 1. The decision

D3's draft (`synthesis/literature_review.md` 4,198 words; `reports/manuscript_draft.md` 4,048 words, 36 refs) was written as a *systematic scoping review*. Two structural facts clash with that framing and will be probed by any reviewer:

- **Over half the corpus is preprint-track**: 32/58 included records (55%) are arXiv/bioRxiv/preprint-venue items.
- **23 of 36 references (64%) lack resolved author metadata** (marked "Corpus preprint (author metadata pending curation)" in the draft).

**Two options:**

| Option | What it means | Cost / risk |
|---|---|---|
| **A. Early-evidence / living scoping review** (recommended) | Keep the full 58-study corpus; name the review as intentionally capturing the fast-moving, mostly-preprint frontier; specify a living-update protocol (re-run cadence, preprint policy, versioning) as a paper appendix | ~1–2 days: rewrite title + §2.1/§3 abstract+methods framing, add living-review protocol appendix; must resolve authors anyway for a clean reference list |
| **B. Tighten inclusion to verifiable PIDs** | Keep only records with stable PIDs (journal DOI / indexed OpenAlex work); drop arXiv-only items without DOIs | Loses 18–20 records including several load-bearing ones (SCI-000144 Zhao, SCI-000159 OpenScholar — both arXiv-only); under-represents the exact 2026 frontier; requires full re-screening and re-synthesis of a shrunken corpus |

**Recommendation: Option A**, with author-metadata resolution executed as a deterministic API task (all 23 pending records have arXiv IDs or OpenAlex IDs — resolution is a script, not a judgment call).

---

## 2. Evidence for the "early-evidence / living" diagnosis

The corpus itself contains the numbers that justify, and almost demand, Option A:

**Temporal concentration.** 2026 alone is >half of the corpus.

| Year | Included | Preprint-track | Share preprint |
|---|---|---|---|
| 2023 | 2 | 2 | 100% |
| 2024 | 8 | 6 | 75% |
| 2025 | 18 | 7 | 39% |
| 2026 | 30 | 17 | 57% |
| **Total** | **58** | **32** | **55%** |

The V-shape is the story: the field started (2023–24) almost entirely as preprints, got consolidated into published venues in 2025, and the 2026 wave returned to preprint dominance — because the space is moving faster than publication can capture. A review that excludes these records would be systematically censoring the newest evidence — precisely the cohort whose trust properties the review exists to characterize.

**Preprint share is a feature of the field, not a sampling artifact.** arXiv is the natural home of LLM/agentic systems work (30 of 58 records). bioRxiv and institutional repositories add 2 more. A "verifiable PID only" corpus would describe the 2023–24 state of the art, not the 2026 one.

**Author metadata is a plumbing problem, not a validity problem.** All 23 pending-author records carry resolvable IDs:
- arXiv IDs: 12 records (e.g., SCI-000144 `2603.07287`, SCI-000126 `2605.05985`, SCI-000108 `2405.14445`)
- OpenAlex work IDs: 11 records (e.g., SCI-000159 `W4404652287…`, SCI-000111 `W438584…`)

Fetching author lists from these registries is a deterministic batch job (run-once script, cache to `synthesis/_manuscript_authors_cache.json`, re-run to fill 23 gaps). No human curation loop required for most; a small remainder may need disambiguation (arXiv author-name variants), which the living protocol's versioned updates naturally absorb.

**The instrument itself already implements living-review machinery.** The pipeline (federated discovery → screening → extraction → verbatim verification → audit journal) is re-runnable end-to-end; `audit/journal.jsonl` already records every run, and the corpus is versioned in git. A "living review" is not a retrofit here — it is the honest description of what the tooling already is.

---

## 3. What Option A changes in the manuscript

Concretely, adopting Option A means:

1. **Title** — add explicit temporal commitment, e.g.:
   > *"AI-Assisted Research Harnesses for Systematic Review: An Early-Evidence Living Scoping Review of Traceability, Trust, and Reproducibility (2023–2026, Version 1.0)"*
2. **Abstract + §1** — one sentence naming the review as early-evidence/living because the field is preprint-dominated and publication-lagging; state the corpus-finalization date as a version stamp.
3. **§2.1 / §3 Methods** — add a **living-review protocol** subsection (target of re-run cadence, e.g., quarterly federated re-run; explicit preprint-inclusion policy; versioning scheme for future updates; statement that reported aggregates are as-of the v1.0 corpus-finalization date).
4. **§7 / Declarations** — add protocol availability + re-run instructions pointing at the committed pipeline; corpus version stamp.
5. **Reference list** — resolve the 23 pending author sets via the API batch; mark arXiv records with their arXiv IDs and version numbers rather than "preprint (metadata pending)".

All five changes are text edits; none require re-screening or re-synthesis.

---

## 4. Numbers to cite in the living-review framing

- 58 included / 181 excluded from 239 deduplicated records (250 raw hits); six federated sources; 2023–2026.
- 32/58 (55%) preprint-track; 2026 = 30/58 (52%) of the corpus.
- 510 verbatim-backed claims (RQ1 166 / RQ2 132 / RQ3 212) across 57 studies; 95 consensus clusters (16 HC / 7 debates / 37 unresolved / 35 provisional); γ-like Phase-4 audit (0 retractions, 16 repos, 5 COI ties).
- 23/36 draft refs author-pending → all resolvable via arXiv/OpenAlex (12 arXiv IDs / 11 OpenAlex IDs).
- Audit journal: 50 events (append-only; re-runnable).

---

## 5. What this decision unblocks

Adopting Option A:
- **Unblocks D3 submission** (BMC *Systematic Reviews* living-review tracks, *Research Synthesis Methods*) with a defensible, protocol-honest framing.
- **Preserves the thesis arc** — D3 becomes meta-evidence that the tool class under study is under-audited, *including at the level of evidence being generated faster than it is published*.
- **Deterministically removes the "author metadata pending" smell** via the resolution script.

Adopting Option B instead would shrink the corpus to ~38–40 records, drop 2 load-bearing citations used in D1/D2 (§SCI-000144, §SCI-000159), and contradict the review's own raison d'être (characterizing the newest, most trust-critical evidence).

---

## 6. Recommended approval line

> Approve **Option A — early-evidence / living scoping review**, Version 1.0 with corpus-finalization date. Author-metadata resolution runs as a deterministic arXiv/OpenAlex batch; a small disambiguation remainder is versioned into the living protocol's next update. Title, abstract, methods protocol subsection, and declarations updated accordingly.

On your approval, the memo's §3 changes are applied to `reports/manuscript_draft.md` and the 23 author sets are fetched, then a full D3 v2 is assembled.