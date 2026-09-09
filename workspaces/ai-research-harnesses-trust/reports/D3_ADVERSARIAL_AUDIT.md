# D3 Adversarial Audit — Findings and Resolution Log

**Date**: 2026-09-09
**Manuscript**: `reports/manuscript_draft.md` (Version 1.0, Review draft, "Early-Evidence Living Scoping Review")
**Method**: two parallel sub-agent passes — (1) adversarial peer review of the manuscript; (2) artifact truth-check of every living-review/protocol promise against committed workspace files.
**Result**: manuscript revised to v3 (Draft v3, post-adversarial audit). All resolved items below applied unless marked "DEFERRED".

---

## 1. Arithmetic / factual blockers verified against ledgers

| # | Finding | Verdict | Fix applied |
|---|---|---|---|
| B-1 | COI partition 5+4+37 = 46 ≠ 47 | **Reviewer miscount** — actual `coi_audit.json` labels are 37 (no-statement) + 5 (industry) + 1 (academic-or-public) + 4 (declared-none) = **47**. The manuscript omitted the "academic-or-public" class. | §4.1 + §4.7 now state 5 industry + 4 declared-none + 1 academic-or-public + 37 none, of 47 scanned |
| B-2 | "covered 43 included studies not at all" | **Confirmed** — 58 − 14 in-scope RAG-covered = **44**; 43 only if the 57 claim-bearing denominator is used. Sibling `manuscript_d2.md` says 44/58. | §4.6 → "covered 44 included studies not at all", denominator made explicit |
| B-3 | Audit-event count (44/48/50/55 across dossier) | Current journal = **55** (verified). Supporting reports are stale snapshots, not errors in the manuscript. | Kept 55 in §3 + §7; note re-sync of supporting reports |
| B-4 | No author/funding/CRediT block | **Confirmed** — journal office would desk-reject. | Author block (Bekhouche/Zertal, aligned with D2), Authors' contributions, Funding = none, added to front matter + §7 |
| B-5 | "verbatim"/"byte-exact"/"word-for-word" outrun the ≥0.90 coverage gate | **Confirmed** — method gates at ≥0.90 coverage on char-window/token-6-gran, not byte-identity. | Detailed above; changed to "≥90% glyph-normalized coverage on char-window or token 6-grams"; removed byte-exact / word-for-word / "100% verbatim grounding" in abstract/§1/§3.5/§5.2/§6/§3.7 |

## 2. Major referee-trigger items

| # | Issue | Fix |
|---|---|---|
| M-1 | Living-window contradiction: §3 "shut at frontier" vs §3.8 "re-run same strings" | §3 = "frozen for Version 1.0"; §3.8 qualifies "each run advances the trailing publication-date boundary" |
| M-2 | Abstract mislocated the 4-stream audit onto the 64-doc superset | Abstract now: "58 included studies (47 fully Phase-4 certified)" |
| M-3 | 47/58 Phase-4 coverage unexplained | §3.4 breaks out 47/48/11; §5.3 Limitations sentence added |
| M-4 | "Registered protocol" (self-registration) | §3 + §7 → "hash-pinned protocol"; §7 explicitly notes not externally registered at v1.0, OSF planned |
| M-5 | "PRISMA-ScR compliant" + nonexistent "living extension" | → "reported in line with PRISMA-ScR and living-(systematic-)review guidance adapted to a scoping design"; front matter softened |
| M-6 | Search strings not reported | §3.1 names concept/synonym Boolean structure + points to `protocol.json` `search_strategy` and supplementary search-log |
| M-7 | Dead path refs (`synthesis/consensus.md`, `method_comparison.md`, `uv run` invocation, "§front matter") | → "supplementary consensus file", "supplementary method-comparison table"; removed `uv run …` + "§front matter" |
| M-8 | [5]/[6] same study double-counted (Nature OpenScholar = arXiv preprint) | [6] re-labeled "preprint version of [5]" (matches §3.8 preprint policy); §2 cites " [5] (preprint version: [6]) " |
| M-9 | Ref-list formatting (Workspace tokens, "et al." inconsistency, ALL-CAPS names, U+2010 hyphen, doubled publisher) | [1] Tampere dedup; [2] "Paulraj, N. J."; [12] U+2010→ASCII; [33] normal case. Full Vancouver restyle = DEFERRED to journal-prep; Workspace tokens retained as lab provenance |
| M-10 | "throwaway prompts" vs "deterministic re-runnable" | Front matter: "agent prompts versioned with the pipeline"; §7 describes real entry points + `scholar-verify verbatim-claims` gate |
| M-11 | Categorical overclaims ("not defensible", "demonstrates… today", "mandatory") | §5.1/§5.2/§6 hedged to corpus-conditional claims |
| M-12 | "audit-grade artifacts" unearned | §7 → "versioned, hash-pinned artifacts" |

## 3. Artifact truth-check gaps (§3.8 promises vs committed files)

| Promise | Verdict | Action |
|---|---|---|
| Crossref `update-to` / OpenAlex status for preprint→published supersession | **NOT SUPPORTED** — `retraction_status_check.json` update events empty, 28/48 API errors; mechanism skips DataCite DOIs | §7 "Preprints and updates" now discloses fields were empty at v1.0; living protocol is the mechanism |
| Search-log appendix with per-run queries/window/threshold | **NOT SUPPORTED** — only placeholder `Q001` committed | §3.1 + §3.8 point to `search_strategy` + per-version `search_log_<version>.json` as **supplementary deliverables still to be generated** (journ-prep TODO) |
| Append-only authoritative claim ledger | **NOT SUPPORTED** — `claims.json` rewritten in place; git shows single add | §3.8 Diff discipline → "versioned under git and regenerated deterministically from committed extraction inputs" |
| Re-run instructions (`uv run ...`) | **PARTIAL** — stage CLIs exist; no committed regenerator for Approach-B claims | §7 Code availability rewritten to real CLIs incl. `scholar-verify verbatim-claims` |
| Protocol fingerprint | **WRONG — the UAV project's hash** `e1bbcb…` was in §7 | §7 now cites the recorded compile fingerprint `sha256:9646d5ec6902c8f7687dfcb6568e473e1e01b78f666b20b74ec901f9703bf55c` (audit journal EVT-04) |
| 55 audit events | VERIFIED | unchanged |
| Author-resolution scripts | VERIFIED | unchanged |

## 4. Deferred (journal-prep, not manuscript-defect)

1. **Full Vancouver restyle** of all 36 references (uniform author order, "et al." cutoffs, DOI-all policy); strip `Workspace: SCI-xxxx` tokens.
2. **PRISMA-ScR flow diagram** (data already available from screening ledger; PRISMA 2020 flowchart pattern used in D1).
3. **Supplementary search-log + preprint→published version table** (named in §3.8 as deliverables of each living version).
4. **OSF protocol registration** (disclosed as planned; PRISMA-ScR item 24).
5. **Re-sync stale supporting reports** (`pipeline_engineering_report.md` "13 resolved / 23 pending" language; 44 vs 55 event counts).

## 5. Anchors verified clean (no action)

58+181=239; 2023/24/25/26 = 2/8/18/30 = 58; 166+132+212 = 510; 493+17 = 510; 16+7+37+35 = 95; 213+26 = 239; 32/58 = 55%; 30/58 = 52%; 90 claims/43.3%; 17,443 citations/0.475; 0.92/0.94, I² = 95.8%; −1.9%/day; 76-point; 5.7×; 0/48 retractions (48 scanned); 16/7/32 open-science tallies against `open_science_regex_baseline.json`.