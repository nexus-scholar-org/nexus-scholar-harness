# scholar-verify-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-verify-kit`). Scope: `tools/scholar-verify-kit/src/scholar_verify/` (9 modules, ~2.0k lines: `retraction.py` 287, `trust_context.py` 380, `coi.py` 304, `open_science.py` 276, `risk_of_bias.py` 266, `cli.py` 272, `verbatim.py` 179, `http_client.py` 47) and `tests/` (6 files, ~0.86k lines); harness consumers in `src/scholar_harness/` (`console/runtimes/actions.py:124-160`). Method: read every source module in full; ran `uv run --no-sync pytest tools/scholar-verify-kit/tests -q` (63 passed); wrote offline reproductions with stubbed HTTP (no network) against the installed package; kit README, `.agents/skills/scholar-verify-kit/SKILL.md` and `docs/kits_surface_matrix.md` were treated as claims only.

## 1. Verdict

The kit does not do what its name and its skill promise ("certify that the evidence base feeding a synthesis is safe to quote"). Its most consequential output, the per-cluster trust label, can say `STRONG` for a cluster that contains a retracted study, or one whose retraction lookup failed, because unknown and missing evidence is silently treated as clean (VER-01, VER-02). The "QUADAS-2/PROBAST" risk-of-bias scorer is a hard-coded heuristic for one UAV weed-segmentation review: it has no signalling questions and no applicability judgements, and any other review gets every study rated High (VER-04). The verbatim verifier marks quotes with a changed number or an added negation as verified (VER-05), and the `verbatim-claims` CLI crashes on any real input (VER-06). The code is small and readable, and the reports carry honest caveat text, but those caveats do not reach the machine-readable labels that downstream steps use.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Weak | Readable single-purpose modules, but project-specific constants are hard-coded in a "generic" kit, library code raises `SystemExit`, there is dead code, an unimported `re` crashes the CLI, and the verbatim module has no tests |
| Correctness & bugs | Failing | Two Critical defects, both reproduced: retraction lookup errors read as "not flagged", and the trust ladder ignores unaudited and retracted studies |
| Research-method fitness | Failing | RoB borrows QUADAS-2/PROBAST names without their structure; "unknown" falls through to "pass" at three layers; the verbatim check is not verbatim |

## 2. Architecture and code quality

- **Shape.** There are five independent streams (`retraction`, `open_science`, `coi`, `risk_of_bias`, `trust_context`) plus `verbatim`. Each takes plain dicts and returns a `{run_metadata, summary, results}` envelope. `trust_context` joins them. This decomposition is sound, and the pure-function shape makes the streams easy to test.
- **Project-specific code shipped as a generic kit.** `risk_of_bias.py:23-28` hard-codes weed and UAV dataset names (`weedsgalore|weedmap|phenobench|…`). `:34` hard-codes segmentation metrics (`mIoU`, `weed_F1`, `crop_F1`). `:44-45` and `:118` read a project-specific record schema (`segmentation.dataset`, `edge`). `:66` returns the text "outside RQ scope". The report prose names "RQ2 (embedded edge inference)" (`:252-254`). `coi.py` (report text) cites BASF/Bayer seed donations. In short, the kit is one review's Phase-4 scripts promoted into a package.
- **Library code exits the process.** `risk_of_bias.run` raises `SystemExit` (`risk_of_bias.py:147-149`), and so do `coi.load_chunks` and `coi.run` (`coi.py:127-128`, `:147-151`). An MCP server or harness that imports these functions has its process terminated instead of receiving an exception.
- **Duplication and dead code.** Four identical `save_results` functions (`retraction.py:282`, `open_science.py:272`, `coi.py:300`, `risk_of_bias.py:262`) are never called; the CLI uses its own `_write` (`cli.py:43-48`). `_FLAG_REASON_SENSITIVE` (`trust_context.py:40`) is unused. `rate_d3`'s last two branches (`risk_of_bias.py:112-114`) cannot be reached because `:108` already handled their condition. `import time` sits inside the per-record loop (`retraction.py:56`).
- **Error handling.** `typer.Exit(f"...")` (`cli.py:38,40`) passes a string as an exit code; it works only because Click forwards it to `sys.exit`. `run_date_utc` is local time with an offset, not UTC (`retraction.py:64`, likewise in the other streams).
- **Tests.** 63 tests pass, but none covers `verbatim.py` or the `verbatim-claims` command. None covers retraction behaviour when every lookup fails. None covers trust-level cases with partial coverage. The tests pin the current heuristics rather than any external standard.
- **Harness coupling.** The harness only shells out: `actions.py:127` runs `scholar-verify trust-context`, and `actions.py:156` runs `scholar-verify risk-of-bias` under the action label **"Methodology critique"** (`critique_methodology`). There are no Python imports of `scholar_verify` in `src/scholar_harness/`.

## 3. Correctness and bugs

**VER-01 — Critical — Reproduced. The trust ladder ignores retracted and unaudited studies, so a cluster with a retracted supporter can be `STRONG`.**
`annotate_group` defines `present` only as studies that have a risk-of-bias or COI row (`trust_context.py:154`). `trust_level` then evaluates only `present` (`:156`), including the retraction check (`:133`). A study that is flagged in the retraction stream but has no RoB/COI row (for example, outside `_manifest.json`) is therefore invisible. Coverage of at least 0.5 is also enough for `STRONG` (`:137`), so up to half of a cluster's supporters can be completely unaudited.
Reproduction (stubbed inputs): a cluster supported by `SCI-1` (RoB L, public data link) and `SCI-9` (retraction row `flagged: True, flag_reasons: ["openalex:retracted"]`, no RoB/COI row) gives `level: STRONG  flags: []  coverage: 0.5`.
Impact: the label that tells the reviewer a consensus finding is safe to quote can be wrong in exactly the case it exists to catch.

**VER-02 — Critical — Reproduced. A failed retraction lookup is indistinguishable from "not retracted" in every downstream signal.**
When OpenAlex or Crossref returns an error, `is_retracted` is `None` and `update_to` is `[]` (`retraction.py:133-134`, `:148-149`). `flagged` is computed only from positive evidence (`:160-164`). The Markdown report prints `## Flagged studies` / `None.` (`:247`). `trust_context` copies only `flagged` (`trust_context.py:107`) and never consults the error state.
Reproduction: with an HTTP stub that always returns `{"_error": "ConnectionError: offline"}`, two studies give `flagged_any: 0, api_errors: 2` and the report contains `Flagged studies … None.`. Feeding that row into `trust_context` with otherwise clean data gives `level: STRONG`.
Impact: an offline run, a rate-limited run, or a study with no DOI, arXiv id or OpenAlex id (`:130-132` produces `{"_status": 404}`) all yield a clean bill of health. Errors are counted in `api_errors`, but no gate uses that count.

**VER-03 — High — Reproduced (code path) / Static (Crossref semantics). The Crossref check reads only `update-to` on the study's own record.**
`retraction.py:153` reads `message["update-to"]`. In Crossref metadata, `update-to` is deposited on the *notice* (the retraction or correction DOI) and points at the original. The original article's record links forward via the separate `updated-by` relation (Crossref exposes this field, including Retraction Watch-sourced entries); the code never reads it. Reproduction: a Crossref stub returning `{"message": {"updated-by": [{"type": "retraction", "source": "retraction-watch"}]}}` gives `flagged: False, crossref: {'update_to': []}`.
Impact: Crossref effectively contributes no retraction signal for included articles, and `flagged` rests on OpenAlex `is_retracted` alone. The field semantics should be confirmed against the live API; this assessment made no network calls.

**VER-04 — Critical (for any review other than the original UAV one) — Reproduced. The RoB scorer rates every generic study High.**
A record without the project schema (`{"workspace_id": "X", "study": {"title": "An RCT of drug Y"}}`) scores `d1: H, d2: H, d3: H, d4: n/a, overall: H`. D1 rates non-UAV as High (`risk_of_bias.py:65-66`), D2 rates "no segmentation metric" as High (`:81-82`), and D3 rates non-UAV without the keywords as High (`:110-111`). No warning is emitted, so the output is a fully populated, plausible-looking RoB table. See also §4.

**VER-05 — High — Reproduced. The "verbatim" verifier accepts altered numbers and inserted negations.**
`verify_quote` takes the **max** of two lenient coverage scores (`verbatim.py:104-107`). The character score counts 8-character windows sampled every 4 characters (`:36-55`), so a single changed digit removes only about two windows out of dozens.
Against a source that says "82.3 percent … real-time weed segmentation is feasible":

| Quote (abridged) | Result |
|---|---|
| "…mean intersection over union of **92.3** percent while running at 25 frames per second…" | verified, char 0.949 / token 0.75 |
| "…real-time weed segmentation is **not** feasible on UAV platforms" | verified, char 0.967 |
| `"82"` | verified (quotes of 8 characters or fewer are substring checks, `:44-45`, so this matches "82.3") |

Impact: the check is meant to catch fabricated or misquoted evidence, and it passes exactly the edits that change a finding: numbers and polarity. Ligatures (`ﬁ`) and hyphenated line breaks are handled correctly (reproduced: True/True).

**VER-06 — High — Reproduced. `scholar-verify verbatim-claims` crashes with `NameError` on any extracted directory that contains a `.md` file.**
`cli.py:247` and `:251` call `re.search`, but `re` is never imported (`cli.py:15-22`). A CliRunner run with one `SCI-1.md` gives `exit: 1 NameError name 're' is not defined`. No test exercises the command. Only the MCP wrapper path (which is not in this kit) can reach `VerbatimClaimVerifier`.

**VER-07 — High — Reproduced. Open-science classification reports "public+link" for statements that say the data is unavailable.**
`classify` returns `explicitly-unavailable` only when there is a negation **and no positive hit** (`open_science.py:111`). The section header "Data Availability" is itself a positive pattern (`:20`), so a negated statement is almost never classified as negated. Repository links are collected from the whole document, including related work and references (`:93-101`), and are shared between DAS and CAS (`:134-135`).
Reproduction: "Data Availability Statement: The data … are **not publicly available** … YOLOv5 (https://github.com/ultralytics/yolov5) was used as a baseline." gives `das: public+link, cas: public+link`.
Impact: `public+link` is the sole open-science condition for trust `STRONG` (`trust_context.py:125-126,139`), so this inflates trust levels.

**VER-08 — Medium — Reproduced. The trust ladder reads COI entities and ignores the COI label.**
`_industry_money` checks for an entity with `kind == "funding"` (`trust_context.py:117-118`). `_industry_any` treats *any* entity, including `tooling`, as an industry tie (`:121-122`). Reproduced: (a) a study labelled `industry-money` whose entity has kind `affiliation` gives `ADEQUATE`, not `WEAK`; (b) a `declared-no-conflict` study with a `tooling` entity (which COI explicitly says "does NOT raise the label") is blocked from `STRONG`. The two modules disagree on what an industry tie is.

**VER-09 — Medium — Reproduced. The COI relabel turns any funding statement into "academic-or-public".**
`coi.py:100-102` relabels `no-statement` plus a non-empty funding statement to `academic-or-public` without reading the funder. Reproduced: funding statement "This work was funded by Bayer AG." gives `academic-or-public`. Industry money is hidden whenever the analyst did not also tag an entity.

**VER-10 — Medium — Reproduced. `unresolved_lookups` contains the wrong studies.**
`_summarize` excludes rows that have an error (`retraction.py:182-186`). It therefore lists only studies that OpenAlex *did* resolve but returned without an `is_retracted` field. The report heading claims "could not be resolved to an OpenAlex work (no DOI / arXiv id / OpenAlex id matched)" (`:225`). Reproduced: with all lookups failing, `unresolved_lookups: []`; with a 200 response lacking `is_retracted`, `unresolved: ['SCI-1']`.

**VER-11 — Medium — Reproduced (CLI) / Static (harness). Re-running a stream non-interactively aborts at the overwrite prompt.**
`_confirm_overwrite` (`cli.py:63-66`) has no `--yes` bypass on `open-science`, `coi` or `risk-of-bias` (`:106,122,138`). Reproduced: a re-run with closed stdin prints `Overwrite existing risk_of_bias.json? [Y/n]:Aborted.` and exits 1. The console job runner starts the CLI with inherited stdin (`job_runner.py:162-166`), so the "Methodology critique" action either aborts or waits on a prompt the user cannot see.

**VER-12 — Low — Reproduced. Corrections block a cluster.**
`correction`, `addendum` and `correction-addendum` set `flagged` (`retraction.py:22-28`), and any flag gives `BLOCKED` (`trust_context.py:133`). Reproduced: `crossref:correction` gives `BLOCKED`. The kit's own report says corrections are "low-severity", and the intended sensitivity filter `_FLAG_REASON_SENSITIVE` is dead code. This over-blocks; it is the safe direction, but it is noisy.

**VER-13 — Low — Reproduced. An empty claims ledger reports a 100% verification rate** (`verbatim.py:176`: `1.0 if total == 0`).

**VER-14 — Low — Static. DOIs are neither normalised nor URL-encoded before lookup.**
A DOI stored as `https://doi.org/10.…` goes into `api.crossref.org/works/https://doi.org/…` (`retraction.py:103`). It also bypasses the `10.48550/` arXiv short-circuit (`:101`), and DOIs containing `#`, `?` or `;` truncate the URL. The failure lands in VER-02 (silent).

**VER-15 — Low — Static. `coi.load_chunks` hard-codes exactly eight chunk files** (`coi.py:122`). A corpus split into fewer chunks raises `SystemExit`; additional chunks are ignored (and then caught as "missing" by `run`). Duplicate detection ignores the `id` key that `normalize` accepts (`:81` vs `:145`).

## 4. Research-method fitness

**Risk of bias is not QUADAS-2 or PROBAST.** The method string calls it an "adaptation of QUADAS-2/PROBAST risk-of-bias domains" (`risk_of_bias.py:180`), and the CLI help says "Score deterministic QUADAS-2/PROBAST" (`cli.py` docstring and `risk-of-bias` help). Against the tools as published:
- **No signalling questions.** QUADAS-2 and PROBAST derive each domain judgement from explicit signalling questions answered from the full text. Here each domain is a handful of boolean or regex rules over LLM-extracted metadata (`:60-131`).
- **No applicability assessment.** Both tools rate applicability separately (QUADAS-2 for three domains, PROBAST for three). None exists here.
- **Domains are renamed onto unrelated constructs.** D4 "Runtime/efficiency claim completeness" is mapped to QUADAS-2 "flow & timing" (`:212`). Flow and timing concerns the interval between index test and reference standard and whether all participants were analysed; it has nothing to do with runtime reporting. D2 scores the *extraction pipeline's* inter-route agreement and confidence (`:83-97`), which measures the review team's extraction reliability, not bias in the primary study. D1 rates non-UAV studies High because they are "outside RQ scope" (`:65-66`), which is an eligibility decision, not risk of bias.
- **Keyword presence decides "Low".** D3 is Low if the dataset note contains "label", "annotat", "benchmark" or "already published" (`:23-30`, `:108-109`). Reproduced: the note "we did not label anything carefully" gives `d3: L`.
- **Missing information gives High, not Unclear.** QUADAS-2 uses "unclear" when reporting is insufficient. D2 assigns High when no metric was extracted (`:81-82`).
- **Overall = worst domain** (`:161-162`) matches the QUADAS-2 convention. This is the one structurally faithful element.

The report's scoping note is honest ("reporting and verifiability risk … does not substitute for a human full-text appraisal", `:10-11`, `:214`). But the JSON field is `overall_risk`, the harness action is "Methodology critique" (`actions.py:153-158`), and the trust ladder consumes `overall_risk` as if it were a RoB judgement. If a manuscript cites this as "risk of bias was assessed with QUADAS-2", a peer reviewer can rightly challenge it. Recommended wording: "reporting-completeness heuristic informed by QUADAS-2 domains", with a human QUADAS-2/PROBAST (or PROBAST+AI) appraisal performed separately.

**"Unknown" falls through to "pass" at three layers.**
1. Retraction: an error yields `flagged=False` (VER-02).
2. Open science: missing extractions are dropped by default (`open_science.py:145,159-176`). The study then has no `das`, which only prevents `STRONG`; it never lowers a level.
3. Trust: studies without RoB/COI rows are excluded from every check (VER-01). Coverage of 0.5 suffices for `STRONG`, and a missing retraction file disables `BLOCKED` entirely (`trust_context.py:375-378` loads only the files that exist).

The ladder is therefore asymmetric: positive evidence of a problem lowers the level, while absence of evidence never does, except at coverage below 0.5. For a sole reviewer relying on the label, `UNVERIFIED`/`WEAK` should be the default whenever any supporting study lacks a completed retraction lookup.

**Is "trust" defensible?** Only as a triage flag, and only after VER-01, VER-02 and VER-07 are fixed. `STRONG` currently means: at least half of the supporters are audited, all audited ones are L or n/a on a heuristic, nobody tagged an entity, and one study has a link anywhere in its PDF. That is not a property of the evidence a reader would call "strong". GRADE-style certainty language would be inappropriate; a neutral name (`flags: none found`) would be more honest.

**COI.** The kit does not classify COI; LLM subagents do, and the kit aggregates and relabels (`coi.py` docstring; `run_metadata.method`). This is stated honestly. The deterministic relabel can, however, *downgrade* industry funding (VER-09), and the severity ordering is never validated against the entities.

**Open science.** The regex scan is labelled a "baseline … intended for manual verification" (`open_science.py:263`), which is appropriate. The problem is that its label is consumed automatically by trust (VER-07).

**Verbatim.** Character n-gram coverage is fuzzy matching, not verbatim matching. For an SLR evidence trail, numbers and negations are the content that matters, and they are exactly what the score tolerates (VER-05).

## 5. Doc drift

- `SKILL.md:12`, "certify that the evidence base … is safe to quote: no retracted records": refuted by VER-01 and VER-02.
- `SKILL.md:92`, "3 retries with exponential backoff": the backoff is linear, `sleep_s * (attempt + 1)` (`http_client.py:46`).
- `SKILL.md:91` and `README.md:45`, "Deterministic: same inputs → identical JSON, always": every envelope embeds `datetime.now()` (`retraction.py:64`, `open_science.py:189`, `coi.py:187`, `risk_of_bias.py:179`).
- `SKILL.md` (Verbatim section), "The CLI `verbatim-claims` … maps sources by stem / `workspace_id:` frontmatter / `SCI-xxxx` filename": the command crashes before mapping (VER-06).
- `SKILL.md` (Verbatim section), "batch verification is self-rate-limiting (sleeps `sleep_s` per record)": `verbatim.py` has no sleep; that text describes `RetractionChecker`.
- `README.md:10` describes the `retraction` stream as checking that "No study is retracted": it cannot assert this when lookups fail (VER-02), and the Crossref half reads the wrong relation (VER-03).

## 6. Prioritized recommendations

All source fixes belong in `nexus-scholar-org/scholar-verify-kit`, followed by a `plugins.json` `default_rev` bump and a re-vendor of `tools/scholar-verify-kit/`, per AGENTS.md.

| ID | Severity | Effort | Action |
|---|---|---|---|
| VER-01 | Critical | S | Evaluate `flagged` over *all* supporting studies, not `present`; require a completed retraction lookup for every supporter before any level above `WEAK`; treat a missing retraction file as `UNVERIFIED` |
| VER-02 | Critical | S | Add a tri-state `retraction_status: retracted / clear / unknown`; mark `unknown` on any error or missing id; report "N studies NOT checked" prominently; make trust treat `unknown` as non-clear |
| VER-04 | Critical | M | Rename the output and CLI to "reporting-completeness heuristic"; move UAV-specific regexes and metrics into a per-review config; refuse to score (exit non-zero) when the expected schema is absent instead of emitting all-High |
| VER-05 | High | M | Require exact normalised substring match (after NFKC, whitespace and hyphen normalisation), or at least require every numeric token and negator in the quote to appear in the matched span; drop `max()` of the two scores |
| VER-06 | High | S | `import re` in `cli.py`; add CLI tests for `verbatim-claims` and unit tests for `verbatim.py` |
| VER-03 | High | S | Read `updated-by` (and keep `update-to`) from Crossref; confirm against a known retracted DOI before relying on it |
| VER-07 | High | M | Scope the DAS/CAS search to the availability section; let negation inside that section win; only count links within the matched section |
| VER-08 | Medium | S | Derive trust COI flags from `coi_label`; exclude `tooling` from `_industry_any` |
| VER-09 | Medium | S | Do not relabel to `academic-or-public` without an explicit non-industry funder signal; otherwise leave as `no-statement` for human review |
| VER-10 | Medium | S | Redefine `unresolved_lookups` to include error rows, or fix the report text |
| VER-11 | Medium | S | Add `--yes` to all streams and pass it from the harness actions |
| VER-12 | Low | S | Use `_FLAG_REASON_SENSITIVE` to separate `BLOCKED` (retraction/EoC) from a `CORRECTED` advisory |
| VER-13–15 | Low | S | Empty ledger gives rate `None`; normalise and URL-encode DOIs; glob chunk files; raise exceptions instead of `SystemExit` in library code; delete dead `save_results` |

## 7. Limits of this assessment

- No network calls were made. Retraction behaviour was exercised only with stubs, and the claim that Crossref's `updated-by` is the relation present on original articles is from knowledge of the Crossref schema, not a live check.
- The MCP wrappers (`nexus_verify_claims`, `nexus_verify_phase4` in `scholar-agent-kit`) were not read. The MCP verbatim path may avoid VER-06 but inherits VER-05.
- No real workspace was available (workspaces were emptied), so VER-04 and VER-07 were shown on synthetic records, not measured on a corpus. Their prevalence in a real review is unknown.
- Methodological statements about QUADAS-2 and PROBAST refer to the published tools (Whiting et al. 2011; Wolff et al. 2019) as generally described. Instrument texts were not re-read for this assessment.
