# 16 — First-Run Evaluation → Inception Improvement Backlog (Proposed)

> **Status:** Proposed. Born from the 2026-09-13 first-run evaluation of the grounded inception agent (hallucination/factual-grounding domain) plus recovery experiments. Being validated by a cross-domain multi-agent trial (`evaluation/multi_domain_trial_*.json`).
> **Owner:** harness + inception-agent skill + methodology-copilot. All changes still ship via fork + PR (pull-request gate), never direct push.
> **Purity rule:** every claim below cites the concrete session/artifact that produced it.
> **Trial note (2026-09-13, updated):** cross-domain trial COMPLETE — see §E–F for quantitative results; §B recommendations revised accordingly.

---

## A. Findings

### F1 — Direction selection is the genericness bottleneck (demonstrated)
The wizard's direction ranker (`_grounded_directions_for_terms`) sorts candidates by `(-len(term.split()), -freq, term)`: **word-count first, then frequency**. On every pool so far the longest frequent cluster is the seed phrase family (`large language models`, `language models llms`, `language model llm`). Distinctive ≥2-anchor domain terms lose the top-3 slots purely on the tie-break.

Recovery experiment (this doc): a semantic re-probe seeded only with field vocabulary recovered `citation accuracy` (2 anchors) and `fabricated references` (2 anchors) into the taxonomy — but top-3 directions stayed `large language models / language models llms / digital object identifiers`. **Seed engineering cannot fix direction genericness; the ranker must.**

### F2 — QEI is blind to topical pollution (demonstrated)
`qei` is a lexical echo index over the top taxonomy vs the prompt. A keyword-mode probe engineered to be "novel" scored **0.10** (best-looking yet) while its OpenAlex `topics` revealed an off-topic pool (healthcare, education, climate, COVID). The same seed through semantic mode scored 0.20 and was topically coherent (`Academic integrity and plagiarism`, `Information Retrieval and Search Behavior`). The pollution-detecting signal (`topics`) is already distilled but **never consumed**. QEI alone under- and over-trusts for engineered seeds.

### F3 — Auto `default_concepts` contains venue-scrape noise
Wizard default concepts included `62nd annual meeting`, `computational linguistics volume` — conference-venue strings. Manual curation saved the emitted protocol; it does not scale to ReconBench (50 SLRs × autopilot).

### F4 — Anchor diversity is thin for low-freq concepts
In the emitted intent, concepts 4–8 anchored on a **single DOI** each. APR counts the anchor exists, not the epistemic strength. ≥2 distinct DOIs per concept is the defensible norm.

### F5 — Corpus quality / veracity seams are downstream-only
Pool is preprint-heavy (SSRN/techrxiv) with classifier-scraped noise. `EXC-04 WRONG_POPULATION` etc. mitigate at screening, but the anchor evidence itself is mixed-venue and DOI-liveness is unverified until Phase 4. Not an inception defect — a documented hand-off.

### F6 — RQ/protocol framing mismatch
RQ1–RQ4 (from the source plan) are the harness's own falsifiable claims, but the corpus screens a *literature* about the phenomenon. Corpus can ground related-work + benchmark construction, not answer the plan's RQs directly. Reframe as corpus-answerable before treat-as-freeze, or declare the design-science framing explicitly.

### F7 — Tooling roughness
`recon_delta` first call timed out (`-32001`), recovered at `followups=1`. Parity helper ~8k-line stdout on rich pools (token cost). Neither violated a contract.

### F8 — GAP A ships but is agent-unreachable (demonstrated)
`recon_distill(lexicon_json=...)` declared `str | None`, and the opencode MCP *client* silently decoded the JSON-looking argument into a dict that got Pydantic-rejected — so agent frameworks that auto-parse JSON strings could not reach the seam at all. **Root cause fixed 2026-09-13 (P3):** the tool parameter is now lenient `str | dict`, and a regression test proves the *same* lexicon works via both an already-parsed dict and a JSON string with byte-identical provenance hash (`test_recon_distill_lexicon_json_accepts_already_parsed_dict`). Proven working since the fix in real sessions.

### F9 — Recon cache root is CWD-scattered
`RECON_CACHE_ROOT` defaults to relative `.cache/inception_recon` resolved against the MCP server's working directory (`tools/scholar-agent-kit/`), so sessions land under **both** `tools/scholar-agent-kit/.cache/` and repo-root `.cache/`. A downstream audit could not find the primary session via the documented path; globs miss dot-dirs too. Lineage hazard, not just annoyance.

### F10 — Loop-B verification step is load-bearing
The GAP-A demo's `Citation Integrity` school pattern matched **0** docs (title/abstract adjacency differs from my n-gram assumption) and the seam reported nothing. `14_agent_loops.md` §3's "verify each pattern ≥1 doc before submit" is thus **required**, not optional — silent 0-match schools otherwise.

---

## B. Proposed fixes

### B.1 Harness (P-series)
- **P1 — Diversity-aware direction selection.** Agglomerate lexically-overlapping term families (shared n-gram ≥1 token), cap ≥1 direction per family, so distinct domain terms (`citation accuracy`, `fabricated references`, `source grounding`) reach the top-3. Same input layers → determinism preserved; old behavior available behind a flag or default when no overlaps.
- **P2 — Topical-coherence gate.** Consume the already-distilled `topics` layer: pool purity (top-topic share) / topic-entropy; mark pools low-purity as probe-invalid **regardless of QEI**. Directly kills the F2 failure mode.
- **P3 — Fix GAP-A at the MCP boundary.** Accept a dict `lexicon_json` (or a lenient str|dict at the tool layer); add an E2E test with an actual lexicon so the seam cannot silently rot again.
- **P4 — Cache-root determinism.** Resolve `RECON_CACHE_ROOT` to one absolute root (configurable env, default repo-root `.cache/inception_recon`); document it; `${SERVER}` logs the resolved path. Kill the tool/scholar-agent-kit split.

### B.2 Agent procedure (A-series)
- **A1 — Pattern-anchor verification before lexicon submit.** Each derived regex must match ≥1 pool DOI; drop/relax otherwise; report 0-match schools explicitly after distill.
- **A2 — Multi-signal convergence.** Gate on **QEI + topics-purity + direction-diversity** jointly; a keyword pool with low purity counts as probe-failed even at qei ≤ 0.3.
- **A3 — Show suppressed candidates.** Present the ranked ≥2-anchor terms that were *not* selected next to the top-3 directions, so the human gate sees ranker-hidden options.

### B.3 Skill (S-series, `inception-agent/SKILL.md`)
- **S1 — "Direction selection & convergence"** section encoding A1–A3.
- **S2 — "Lexicon bootstrap"** subsection: merge semantics (extra-wins), hash provenance, pattern-anchor verification prerequisite, and the F8 string-vs-dict bug + workaround (pass JSON string; shim to harness API until fixed).
- **S3 — Cache-root check** before probing: record the session root the MCP server will use in the RECON event. **Since P4:** the root is the canonical, CWD-independent `NEXUS_RECON_ROOT | <project>/.cache/inception_recon`; the bullet now says to record the actual root into `recon_context` lineage, no longer implying server-CWD scatter.

*Ordering recommendation:* P2 + P1 first (both attack D1/D2 findings, pure harness, testable), then P3, then P4; A/S follow the code they encode.

---

## C. Evidence (this session, all reproducible)

### C.1 Emitted first-run project
`workspaces/grounded-inception-hallucination/` — protocol fingerprint `sha256:c2f5f3b8…81efd40e` (VALID), APR re-audited **100%** (16/16, `apr_audit.py`), QEI 0.30, delta gap `Artificial Intelligence in Law` → `dense` (corpus 660,212).

### C.2 Recovery probes
| Session | Seed | Mode | QEI | Verdict |
| :-- | :-- | :-- | --: | :-- |
| `rec_05893e9f…` | vocab-constructed | keyword | 0.10 | topically polluted → F2 |
| `rec_2b054b57…` | vocab-constructed | semantic | 0.20 | coherent; domain terms recovered, directions still generic → F1 |

### C.3 GAP-A seam (harness-side, `gap_a_demo.py` on `rec_d1aa…/pool_cea554…`)
- Baseline schools: `language model/LLM(17)` only; metrics `{accuracy, precision}`; datasets `{}`.
- With domain lexicon: schools `{language model/LLM(17), Hallucination & Faithfulness(12), Factual Consistency & Grounding(4), Source-Grounded Generation(3), Trustworthy LLM Agents(3), Zero-Resource Detection(1)}`; metrics +`citation error rate`; datasets +`QAMPARI`, `SimpleQA`; QEI unchanged 0.2; **directions unchanged** (micro-taxonomy-only derivation, confirming F1). `Citation Integrity` pattern = 0 matches → F10.
- MCP boundary failure reproduced twice before dropping to the harness API → F8.

---

## D. Open questions for the multi-domain trial
1. Does P1-family genericness reproduce across domains (i.e., is it structural, not domain-specific)?
2. Does topic purity separate good/medium/bad pools better than QEI across domains?
3. Do the default lexicon's CV/LLM biases corrupt non-ML domains the most (worst school taxonomy)?
4. Anchor diversity per concept — is single-anchor thinness common (F4 is not a one-off)?
5. Cross-domain: which composition (semantic vs keyword) and which start-year behaves best per discipline?

---

## E. Cross-domain trial results (2026-09-13)

Six parallel inception agents probed six domains (semantic, y2022–2026, limit 10). Sessions:
`rec_a0d5ffda…` (oncology), `rec_e72d63932a0…` (robotics), `rec_b2b1a7e12b…` (climate), `rec_f224bba66f…` (fintech), `rec_f8f76f4fa4…` (education), `rec_c8e80e02fd…` (materials). Full JSON in `evaluation/multi_domain_trial_2026-09-13.json`.

| Domain | n_docs | QEI | schools | top topic (purity) | directions (anchors) |
| :-- | --: | --: | :-- | :-- | :-- |
| oncology | 25 | 0.90 | deep learning(3)… | Pancreatic & Hepatic Oncology (5, 0.98) | pancreatic cancer pc(6); pancreatic ductal adenocarcinoma(5); ductal adenocarcinoma pdac(4) |
| robotics | 25 | 0.40 | language model/LLM(13)… | Multi-modal ML(4, 0.96); Robot Manipulation & Learning(3, 0.99) | large language model(4); large language models(4); **vision-language-action vla models(4)** |
| climate | 25 | 0.70 | **∅** | Climate variability & models(6, 0.94) | anthropogenic climate change(10); extreme precipitation events(5); extreme weather events(4) |
| fintech | 8 | 0.70 | **∅** | **∅** (no topics) | credit risk assessment(4); credit scoring models(2); **"reduces default probability"(2)** |
| education | 25 | 0.80 | **∅** | Online Learning & Analytics(5, 0.95) | learning analytics dashboards(10); self-regulated learning srl(8); learning analytics dashboard(5) |
| materials | 6 | 0.70 | **∅** | **∅** (no topics) | interatomic potentials mlips(4); machine-learned interatomic potentials(4); **"11 kcal mol"(2)** |

### E.1 What the trial proves

- **E.Q1 — QEI gate is inverted for well-scoped semantic seeds (falsifies its use as a pass/fail gate).** All six pools look topically coherent (oncology/robotics/climate/education have strong on-topic OpenAlex topics) yet *every* QEI is 0.4–0.90, far above the ≤0.3 "pass". The echo index scores *scoped* pools as "failure". The earlier hallucination run only "passed" at 0.30 because its seed mixed a generic phrase. **QEI measures seed-tightness, not inquiry quality.**
- **E.Q2 — Topic purity is the signal that separates pools** (as F2 predicted): coherent pools have a dominant in-field topic (`Pancreatic & Hepatic Oncology` 5@0.98; `Online Learning & Analytics` 5@0.95); the weak pools (fintech 8 docs, materials 6 docs) have **no topics at all**. n_docs ≤ 8 ⇒ topics layer absent ⇒ purity unavailable ⇒ small-pool failure mode (see P5).
- **E.Q3 — Default lexicon is a cross-domain liability (F3 generalized).** `schools` empty for **4/6** domains (climate, fintech, education, materials); `metrics` only CV/LLM defaults (`accuracy`, `precision`, `F1`) everywhere; `datasets` empty 6/6. The CV/LLM `DEFAULT_LEXICON` contributes nothing outside ML/tech. GAP A's broken seam (F8) is therefore the critical blocker, plus the lexicon itself needs non-CV domain patterns or agent-side coverage.
- **E.Q1b — Default direction ranker produces same-family synonyms (F1 generalizes).** 5/6 domains' top-3 directions are near-duplicates of one family (oncology: PC/PDA/PDAC; education: dashboards ×2 + SRL; materials: MLIPs ×2 + a numeric unit). Only robotics surfaced a genuinely distinct 3rd direction (`vision-language-action vla models`) and climate's 2nd/3rd are method-adjacent (`extreme precipitation events`, `extreme weather events`). The word-length→frequency ranker keeps winning with the seed phrase family.
- **E.Q4 — Junk directions emerge on thin pools.** fintech 3rd direction is an abstract sentence fragment (`reduces default probability`); materials' is a numeric unit (`11 kcal mol`). Small pools (6–8 docs) also produce empty topics → no purity signal. A pool-size floor is needed before directions are proposed.
- **E.Q5 — Anchor count confirms F4's generality only for small pools.** Oncology/education/climate concepts carry rich anchors (10–20); the thin pools collapse to single-doc evidence. Diversity risk is a size problem, not a cross-domain constant.

### E.2 Trial 2 — controlled re-run after P5+P2+P1+P3 (2026-09-13)

Same six topics and params; content-addressed pools guaranteed byte-identical, so every delta is downstream harness behaviour. Full JSON: `evaluation/multi_domain_trial2_2026-09-13.json`. Six parallel agents, one per domain.

| Domain | n_docs | pool gate | purity gate | junk purged | family-dup dropped | new term surfaced |
| :-- | --: | :-- | :-- | :-- | :-- | :-- |
| oncology | 25 | sufficient | coherent (0.80) | — | ductal adenocarcinoma pdac | machine learning ml |
| robotics | 25 | sufficient | coherent (0.53) | — | large language models | task success rate |
| climate | 25 | sufficient | coherent (0.78) | — | extreme weather events | contiguous united states |
| fintech | 8 | **thin** | indeterminate | **reduces default probability** | — | causal inference |
| education | 25 | sufficient | coherent (0.75) | — | learning analytics dashboard | qualitative content analysis |
| materials | 6 | **thin** | indeterminate | **11 kcal mol** | machine-learned interatomic potentials | absolute solvation free; alchemical relative free |

- **P5:** fired on exactly fintech (8) and materials (6) → `thin`; 4/4 normal pools → `sufficient`. Zero false positives.
- **P2:** 4/4 topic-bearing pools → `coherent` (0.53–0.80); 2/2 topic-less pools → `indeterminate` (never a false `fragmented`/0) — the gap E.Q2 identified is now an explicit, correctly-typed signal.
- **P1 junk:** purged both known fragments (`reduces default probability`, `11 kcal mol`).
- **P1 diversity:** family duplicates removed wherever they existed (4/4 domains), each replaced by a distinct, more informative term. Notably `self-regulated learning srl` was **kept** distinct from `learning analytics dashboards` (only the singular dashboard twin merged) — the plural-normalized rule discriminates correctly.
- **Residual (unchanged by design):** materials still yields fragmentary off-topic terms (`absolute solvation free`, `alchemical relative free`) because the *pool* is thin/off-topic (6 docs, 0 topics) — now loudly flagged `thin` rather than silently presented. That is a retrieval-quality limit, not a ranker defect, and is the case P6 (lexicon breadth) + a pre-validate delta/probe-refine step target.

**Verdict:** all four changes behaved as specified on real pools; P5/P2 decide trustworthiness and P1 cleans the top-3 when the pool is trustworthy. The only remaining failure mode is surfaced, not hidden.

## F. Revised recommendations (post-trial)

Priority (P-series, pruned from §B by evidence):

1. **P5 — Pool-size floor (NEW).** Warn/treat-as-invalid when `n_docs < ~12` (fintech 8, materials 6 → junk directions + no topics). Recommend raising `limit` or a delta pass before proposing directions. Directly kills E→junky-direction failures.
2. **P2 — Topical-coherence gate (was 2nd, now 1st alongside P5).** The trial shows purity that QEI can't capture and *absence* of topics is the small-pool flag. Reject only low-purity; never gate on QEI alone.
3. **P1 — Diversity-aware direction selection + junk filter.** Ranker must (a) dedupe same-family synonyms within top-3 and (b) filter non-vocabulary anchors (numeric patterns like `11 kcal mol`, sentence fragments like `reduces default probability`, venue/title noise). Robotics' VLA recovery proves distinct terms exist at ≥4 anchors and only lose on the tie-break.
4. **P3 — Fix GAP-A seam FIRST as an economic prerequisite.** Schools/metrics/datasets are empty or wrong in 4/6 domains solely because the lexicon cannot be injected. This is now the #1 tooling defect (bigger than F1/F2 in practice).
5. **P6 — Default-lexicon breadth (NEW).** Even a small non-CV default (climate/health/finance/social-science patterns) would give `schools`/`metrics` signal on day one for non-tech domains. Either broaden `DEFAULT_LEXICON` or (preferred) make arrival on GAP A mandatory; both are cheap and testable.
6. **QEI reframing (dependency of P2).** Change `13_evaluation.md`'s gate from "QEI ≤ 0.3" to a two-axis rule (QEI × topic purity) with the documented inversion behavior. Do **not** delete QEI — it is a valid *dispersion* signal (very low QEI on low-purity pools = F2's pollution case); use the pair.

Agent procedures (A-series) and skill updates (S-series) from §B stand, with A2 rewritten over the two-axis gate (P2/P6) and the new P5 warning; S1 gains the pool-size gate and the QEI-inversion note.

**Proposed next execution order:** (1) P5 + P2 (harness, low risk, testable against this trial corpus), (2) P1 + junk filter, (3) P3 (GAP-A boundary fix + E2E), (4) P6, then rebase → A/S skill updates. All via fork + PR.

## F.1 Implementation status (2026-09-13)

**P5 + P2 DONE** (harness + MCP + wizard advisory + tests + contracts):

- `src/scholar_harness/recon/gates.py` — `compute_pool_sufficiency` (`POOL_THIN_FLOOR = 12`) and `compute_topic_purity` (`TOPIC_COHERENCE_TOP3_SHARE = 0.50`; labels `coherent|fragmented|indeterminate`, exposes `top1_share`/`top3_share`/`threshold`). APR gates untouched.
- `tools/scholar-agent-kit/src/scholar_agent/server.py` — `recon_distill` reply now carries `pool` and `purity`; tool docstring documents the QEI-inversion caveat. `lexicon_json` behavior unchanged (byte-identical default path preserved).
- `src/scholar_harness/inception.py` — `_present_pool_assessment` prints an advisory "Pool assessment:" line before directions (thin/fragmented/indeterminate + the QEI-on-coherent note); advisory only, human gate intact, headless path unaffected.
- Tests: `tests/recon/test_gates.py` (+6 hermetic gate tests incl. trial-calibrated boundaries) and `tests/test_mcp_recon.py` (+2 tool-surface tests). Full suite at the change: **239 passed, 3 skipped**; `ruff check scripts/` clean.
- End-to-end on real trial data through the MCP path: climate `rec_b2b1a7e1…` → `pool=sufficient`, `purity=coherent 0.78`; materials `rec_c8e80e02f…` → `pool=thin`, `purity=indeterminate`. Thresholds calibrated on the trial corpus (oncology 0.80 / climate 0.78 / education 0.75 / robotics 0.53 / fintech materials 0-topics).
- Contract locations: `13_evaluation.md` §3.5 + §7 row; this doc §E/F; wizard advisory; MCP tool docstring.

## F.2 P1 implementation status (2026-09-13)

**P1 DONE** (junk filter + diversity-aware direction selection, both fault modes shown live):

- `src/scholar_harness/inception.py` — `_is_junk_term_label` (leading numeric/ordinal tokens, verb-led fragments, venue-noise tokens), `_family_tokens`/`_same_direction_family` (plural-normalized; collision on ≥2 shared tokens or token-subset), `_select_diverse_directions` (greedy rank-order, ≥1 direction per family, deterministic → legacy output when no overlaps), and the junk filter wired into `_grounded_default_concepts` (F3 venue-scrape site).
- Live retrogression across the 7 real sessions (6-domain trial + recovery-sem), old → new top-3:
  - fintech: `reduces default probability` (junk) → **`causal inference`** ✓
  - robotics: `large language models` duplicate → **`task success rate`** ✓ (LLM twin family-capped; VLA kept)
  - education: unchanged reps + **`qualitative content analysis`** ✓ (`self-regulated learning srl` correctly kept distinct from `learning analytics dashboards`)
  - materials: `11 kcal mol` (junk) gone — remaining fragments (`achieves excellent internal` → now verb-blocked; `absolute solvation free`) persist because the pool is `thin` (n=6) and the **P5 advisory flags it** as fragmentary, exactly the layered intent.
- Singular/plural family merging verified live: `large language model` + `vision language models` + `large language models` collapse to one family; `vision-language-action vla models` and `self-regulated learning srl` stay distinct.
- Tests: +6 in `tests/test_inception_grounded.py` (junk table, family identities, plural normalization, sparse-pool merge, defaults junk-drop). Full suite: **245 passed, 3 skipped**; ruff on touched files clean (pre-existing B008 only, out of CI scope).
- No change to `recon/distiller.py`; `grounded_directions.py` parity helper reuses the same functions, so agent-side directions match the wizard by construction.

## F.3 P3 implementation status (2026-09-13)

**P3 DONE** (GAP-A boundary fix + E2E regression test):

- `tools/scholar-agent-kit/src/scholar_agent/server.py` — `recon_distill` parameter is now lenient `lexicon_json: str | dict | None` (normalizes a dict directly, JSON string via `json.loads`; both validate to a JSON object). Docstring documents the F8 failure mode and the fix.
- Tests: `tests/test_mcp_recon.py::test_recon_distill_lexicon_json_accepts_already_parsed_dict` — same lexicon via dict and string must yield the same `CNN-Compact` metric **and the same salted artifact name** (provenance hash identical across both transports). Full suite: **246 passed, 3 skipped**; ruff clean (no new findings vs HEAD).
- The GAP-A seam is now reachable by every agent framework including the opencode client that triggered F8.

Still open (unchanged): the remaining **A-series** updates (A2 multi-signal convergence is partially encoded in `_present_pool_assessment` + SKILL.md Stage-3; A7 QEI reframing is documented in §F.1/13_evaluation §3.5 — see the F.1 note).

## F.4 P4 implementation status (2026-09-13)

**P4 DONE** (canonical recon root — kills the CLI/MCP cache-root CWD-scatter):

- Before: `ReconEngine`-default and `server.RECON_CACHE_ROOT` were both CWD-relative (`.cache/inception_recon`), so the wizard (repo-root CWD) cached under `<repo>/.cache/` while the MCP server (launched `--directory tools/scholar-agent-kit`) cached under `<repo>/tools/scholar-agent-kit/.cache/` — two roots, empty caches across processes.
- After: `src/scholar_harness/recon/engine.py` gains `canonical_recon_root()` — `NEXUS_RECON_ROOT` (resolved) wins, else `<project-root>/.cache/inception_recon` where project-root is walked up from the source tree (pyproject.toml), never `Path.cwd()`. `ReconEngine` default is now `cache_root=None` → `canonical_recon_root()`. `tools/scholar-agent-kit/.../server.py` imports the same helper, so MCP and CLI share one root by construction in any deployment.
- Tests: `tests/recon/test_engine.py::test_default_recon_root_is_repo_anchored_not_cwd` (launch from a foreign dir → still `<repo/.cache/inception_recon`, absolute, no tmp scatter); `tests/test_mcp_recon.py` gains an autouse fixture pinning `RECON_CACHE_ROOT` to `tmp_path/.cache/inception_recon` (hermetic probes must not touch the checkout cache), the workspaces-refusal test now drives the root via the patched constant, and the env-root fallback assertion was re-based to the repo-anchored default (was the CWD-relative string). Full suite: **248 passed, 3 skipped** (was 247); ruff clean (server.py still exactly its 31 pre-existing findings vs HEAD).
- Contract locations: `13_evaluation.md` §3.6 + §7 row; SKILL.md S3 bullet rewritten (cache root is canonical, not server-CWD-dependent).

## F.6 P6 implementation status (2026-09-13)

**P6 DONE** (default-lexicon breadth — non-CV `schools`/`metrics`/`datasets` on day one):

- `src/scholar_harness/recon/lexicon.py` — `DEFAULT_LEXICON` now ships the CV/LLM core **plus** a curated cross-domain core (P6): 18 new school patterns (climate science, global warming, precipitation, drought, hydrology, oncology, immunotherapy, clinical trial, MRI, credit risk, causal inference, econometrics, learning analytics, self-regulated learning, qualitative research, DFT, molecular dynamics, interatomic potentials), 8 new metrics (RMSE, MAE, AUC, R2, MCC, p-value, confidence interval, odds ratio), 4 new datasets (ERA5, CMIP, TCGA, MIMIC). Module docstring updated; `distill_pool` docstring reworded accordingly.
- Scope discipline: `micro_taxonomy` and `qei` never consult the lexicon (distiller.py:261), so P6 touches only `metrics`/`datasets`/`schools` — the pool/purity/QEI gates are untouched.
- Tests: `tests/recon/test_lexicon.py` — coverage contract extended (every shipped pattern carries a fixture; now 25 schools / 19 metrics / 20 datasets); the oncology-default test re-based to the new contract (default catches broad `oncology`/`immunotherapy`/`TCGA` signals, still requires the custom registry for `OS`/`DFS`/`checkpoint inhibitor`); new `test_default_lexicon_surfaces_cross_domain_signal_without_any_lexicon_json` proves the P6 goal (climate/finance/education pool gets schools + datasets + metrics with **no** lexicon injection). Full suite: **247 passed, 3 skipped** (was 246); ruff on touched files clean.
- Byte-identical determinism promise (repeated `recon_distill` with no lexicon) is unchanged — only the composition of the shipped default broadened, so historical trial artifacts are stale baselines by design (trial-2 §E.2 already predates this and stays valid as a *harness* comparison; the `schools: ∅` rows it records for non-CV domains are precisely the gap P6 closes).
- Live distillation of the byte-identical trial pools with the new default (no lexicon injection): fintech → `causal inference / credit risk / econometrics`; climate → `climate science / drought / global warming / hydrology / precipitation` (+ datasets `CMIP`/`ERA5`); materials → `DFT / interatomic potentials / molecular dynamics`. The trial-1 `schools: ∅ ×4` record is gone on real data.