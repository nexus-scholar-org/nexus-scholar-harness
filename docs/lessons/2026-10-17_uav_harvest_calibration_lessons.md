# Lessons learned — UAV multi-provider harvest (v0.2 pilot + v0.3 calibration)

Created 2026-10-17 from the completed UAV crop/weed harvest calibration work.
Purpose: persist the harvest's operational, methodological, and toolkit
lessons **for future harness and toolkit development**, not as research
findings. Every lesson is anchored to concrete artifacts so later readers can
re-derive it.

Evidence anchors:

- **v0.2**: `workspaces/uav-pilot-demo/calibration/*` (harvest 2026-10-16;
  sentinel verification 2026-10-12/13; protocol rev 0.2; kit surface of that
  date), journal `workspaces/uav-pilot-demo/audit/journal.jsonl`.
- **v0.3**: `workspaces/uav-crop-weed-v03/calibration_v03/*` (rounds
  r0→r3e, 2026-10-17; final search date 2026-10-17 UTC),
  journal `workspaces/uav-crop-weed-v03/audit/journal.jsonl` (EVT chain
  through `EVT-20261017215930-c32acb`),
  drivers `workspaces/uav-crop-weed-v03/_drivers/*`.

> Round-citation rule carried over from the workspace decision log: only final
> rounds (v0.3: r3b/r3c/r3d/r3e) are citable for corpus counts; superseded
> rounds are provenance, not evidence.

---

## 1. v0.2 pilot lessons (2026-10-12 → 2026-10-16)

1. **Never submit literal boolean text to relevance endpoints.** The three-cluster
   boolean had to be translated to a keyword string (`calibration/QUERIES.md`
   Q1/Q2); the boolean text was NOT sent literally because no provider-side
   boolean AND is observable from the kit surface. This drove the persistent
   research-layer query translator (`_drivers/uav_query_translator.py` in v0.3).
   Evidence: `calibration/HARVEST_MULTIPROVIDER.md` (Executed query section).
2. **A constructed-guess DOI is not a sentinel.** A guessed DOI for the
   SemiWeedNet paper could not be verified (`Untitled`) and a wrong-paper match
   occurred for another constructed guess. Sentinels must come from verified
   retrieval output, never hand construction. Evidence:
   `calibration/SENTINELS.md` (Failed / rejected candidates).
3. **Honest under-cap returns are legitimate provider behavior.** Keyed S2
   returned 10/500, arXiv 153/200, PubMed 2/200 — recorded verbatim, never
   padded; earlier zero passes (0/500 HTTP 429) were superseded without
   deletion. Evidence: `calibration/HARVEST_MULTIPROVIDER.md` per-provider table.
4. **Auth state changes provider behavior and must be recorded per pass.**
   OpenAlex keyed → clean 1000/1000 cursor paging; keyless → 200/1000 on
   HTTP 401. Exact auth channel per provider per pass belongs in the report.
5. **Provider date semantics leak across window boundaries.** Crossref returned
   2027-dated records under year-max 2026 (e-pub-ahead-of-print); the same
   paper can carry different years per provider (S5: 2025 OpenAlex vs 2026
   Crossref). Eligibility must anchor to the recorded final search date, not
   displayed years.
6. **Hydration accounting has a known double-map artifact.** Kit reported
   `hydrated: 89`; net file gain was +83 because the hydrator applies the
   abstract map to every document sharing a hydrated DOI. Expect and explain
   this gap rather than hiding it. (In v0.3 the same accounting became the
   declared "pre-dedup snapshot basis".)
7. **Dedup-run-local IDs are not study identities.** v0.2 assigned
   `SCI-%06d` ids local to each dedup run — later imposed the explicit
   identity-mint step (`COR-*`/`STU-*`) as a separate, gated phase.
8. **Title match is not identity.** 45 title mentions of the out-of-window
   WeedMap sentinel yielded 0 DOI matches — title probes are kept separate
   from PID identity in all sentinel memo code since.
9. **Relevance-ranked retrieval supports no completeness claim.** v0.2 was
   explicitly framed as a bounded calibration probe "not an exhaustive
   systematic search" — the honest completion language that v0.3 then made
   real with strict-filter OpenAlex and partition sweeps.
10. **Supersession must be explicit.** The v0.2 report names the stale
    200-cap pass, the 1355-record repair pass, and the 2155-record pass as
    superseded with journal EVTs — "superseded and must not be cited".

## 2. v0.3 lessons (2026-10-17, rounds r0 → r3e)

11. **A strict per-provider filter creates a provable universe.** OpenAlex
    strict boolean: 1,343 fetched vs probed universe 1,344 (below cap) — the
    only leg on which "exhaustive" was ever claimed, and it stayed the
    invariant primary claim across all rounds. Translate per provider; a
    strict engine carries the completeness claim, relevance engines carry
    supplements.
12. **Caps hide universes.** The full-range Crossref leg reported "1000
    cap-bound" for three rounds before a year-partitioned sweep revealed the
    leg's true universe (~13,096 under this leg's semantics). Any cap-bound
    count is a lower bound with unknown distance; disclose it as such and
    plan partition sweeps (year → quarter; every quarter landed 104–843, far
    below the cap; fetch == universe == 13,096 → leg COMPLETE).
    Evidence: `v03_r3c_20261017_CROSSREF_YEAR_SWEEP.md`,
    `v03_r3d_20261017_CROSSREF_COMPLETION.md`.
13. **Sum-of-parts reconciliation catches arithmetic slips.** Per-year quarter
    sums matched r3c year totals exactly (1521/1685/1691/1938/2395/2319/1547),
    which exposed an earlier mis-added coverage figure (12,096 vs 13,096;
    53.5% not 58%) that was corrected in the journal rather than rewritten.
    Partition manifests should always be designed so their sums reconcile
    against the previous layer's totals.
14. **Kit search() granularity gaps are solved by harness-level composition,
    not kit edits.** The kit's Crossref fetch only supports year granularity;
    the quarter sweep composed the provider's `query=` params explicitly and
    reused the kit `_normalize_document` parser at the driver. Zero kit
    changes; documented in the driver docstring. (If this composition becomes
    a kit feature later, it goes through the canonical-repo gates.)
15. **The Deduplicator mutates representatives in place.**
    `_merge_metadata` (longer abstract wins, PID/source/OA merge) mutates
    cluster reps during clustering — a driver that snapshots the pool after
    dedup captures post-mutation state and silently corrupts provenance.
    The r3b defect (PASS-1 snapshot order, caught + fixed + journaled) became
    the standing rule: **serialize the pool before dedup; declare the
    coverage basis** (pre-dedup snapshot). Evidence: `dedup.py`,
    `v03_r3b_20261017_S2_REUSE_ADDENDUM.md`.
16. **Duplicate detection must run against the full pool, not just reps.**
    A fetched record matching a non-representative pool member is also a
    duplicate; PID-set + title/year-signature sets are built from every pool
    record (drivers `v03_r3c/_r3d/_r3e`).
17. **Dedup rate is not a constant and need not be alarming.** v0.2 4.85% →
    v0.3 pool-build rounds 7.2–7.7% → 1.8–2.4% for sweep-heavy rounds; PID-
    centric clustering stayed identity-stable throughout (sentinels 7/7 in
    every dedup).
18. **Retrying a burned per-IP quota does not buy records.** S2 unauth tier
    429's persisted across r3 hydration, r3b>r3c>r3d/r3e misses, and a full
    bounded retry (2,659 attempted → 64 recovered → 2,595 failed). Dedup-rate
    the retry window first; a failed leg is never padded and a quota debt is
    disclosed, not silently dropped (`v03_r3e_20261017_REHYDRATION_RETRY.md`).
19. **Quota-state-aware, idempotent top-up machinery beats one-shot drivers.**
    The parked `v03_r3_s2_topup*.py` design (dry-quota aware, no-op when the
    window is dry) is the pattern for any quota-governed provider leg.
20. **Keyless-first is the default standing discipline.** Every driver
    hard-asserts `SCHOLAR_S2_KEY` absence and aborts otherwise; keyed runs are
    explicit researcher decisions; key values are never read, printed, or
    persisted (env-name references only). One observing process carried the
    variable once — value never read; all children launched with it removed.
21. **Domain configuration must live outside the kit.** arXiv compaction
    stoplists/stem families and screening domain signals were genericized
    into constructor params (empty domain-free defaults) with domain values at
    the research layer (`_drivers/uav_query_translator.py`), plus a standing
    byte-parity probe proving the generic implementation reproduces the
    recorded emitted string (`genericity_probe.py`, 3/3). The kit's
    `screening.py` domain block remains an upstream genericization item — kit
    code carries zero domain tokens (7 dirty files verified domain-token-free).
22. **Identity normalization is shared critical path.** The PMID namespace went
    bare everywhere only after the `pubmed_id` URL/scheme strip in
    `models.py` (8th kit patch); namespace mixes (URL vs bare vs prose) are a
    recurring PID dedup hazard — audit all ID fields for scheme leakage, not
    just DOI.
23. **Sentinel sets must encode identity edge cases.** The 7-seed set includes
    an arXiv-native sentinel (no DOI; Tier-1 satisfied via observed arxiv_id
    crosswalk), a pubmednorm-chain sentinel, and single-rep cases — each
    defends a different identity path. Sentinel memo code is Tier-1 PID exact
    (doi OR arxiv_id), title kept as a separate probe (lesson 8 holds).
24. **One dedup-isolated + hydrate-isolated error policy per driver.**
    Split-fallback on unexpected dedup exceptions and watdoged provider calls
    keep one bad batch from killing a round while recording the error note
    verbatim (`dedup_error_note`).
25. **New-file-per-round + append-only journal is the mutation discipline.**
    Every round writes brand-new `v03_*` artifacts; the journal carries the
    full chain with canonical actions, real actor names, meaningful
    inputs/outputs, and the workspace stats reconcile against physical files
    (example gap: the summary-counts-vs-artifact-counts drift class caught
    during early v0.2 work → orchestrators reconcile, never trust one
    registry).
26. **Frozen-protocol fingerprint re-verification is a cheap gate.** The 27-term
    boolean fingerprint (`sha256:f81e6c58…f755`) was re-asserted in every round
    artifact; a fingerprint drift would auto-invalidate the round.

## 3. Development backlog this implies (proposals, not commitments)

> Kit items flow through the canonical-repo contribution gates
> (`BLOCKED_CANONICAL_REPO`; fork + PR to `nexus-scholar-org/scholar-*-kit`),
> never by editing vendored `tools/` alone. Harness items stay in this repo.

### Toolkit (scholar-search-kit, upstream PR material)

- **K1 — Dedup copy-semantics.** Expose/document the in-place mutation
  contract (`copy_semantics='in_place'|'copy'` on `Deduplicator`, or an
  explicit documented warning + a provided `snapshot()` helper) so drivers
  cannot silently capture post-mutation state (lessons 15–16).
- **K2 — Universe probes + date-partition iteration as first-class API.**
  A public `count()`/meta-probe and a `search_windowed(window)` iterator
  would replace the private `_normalize_document`/explicit-params
  composition used for the quarter sweep (lessons 12–14).
- **K3 — Genericize remaining domain knobs.** Port the arxiv-module pattern
  (domain-free defaults + parity probe) across all providers; resolve the
  upstream-HEAD `screening.py` domain block the same way (lesson 21).
- **K4 — Hydrator quota-circuit-breaker + provider-leg stats.** Stop batching
  a dead 429 window after N consecutive failures (the retry burned 229 s for
  64 returns); surface per-provider-channel hydrated/failed counts in stats;
  stable hydrator instance naming (lesson 18–20 cosmetics).
- **K5 — ID normalizer sweep.** One shared normalizer for DOI/PMID/arXiv
  namespaces (URL stripping, case) validated by conformance tests
  (lesson 22).
- **K6 — Sentinel seeds as kit conformance fixtures.** The 7-seed
  identity-edge set is a ready-made regression corpus for provider parsers
  and dedup identity (lesson 23).

### Harness (this repo)

- **H1 — Factored harvest-driver library.** The per-round drivers duplicate
  `dedup_isolated`, `hydrate_isolated`, `ser`, PID extraction, sentinel
  memo, monkey-safety asserts; factor into one shared module under the
  workspace `_drivers/` pattern so rounds differ only in strategy
  (lessons 15–17, 24).
- **H2 — Partitioned-search planner.** Given a baseline leg report, plan and
  execute disjoint date partitions with automatic sum-of-parts
  reconciliation and cap-bound disclosure fields in the manifest
  (lessons 12–13).
- **H3 — Credential assert helper.** A single `assert_env_absent(...)`
  primitive used by every driver (lesson 20).
- **H4 — PRISMA accounting generator.** Emit the stratified per-database
  identification table and flow counts directly from round summaries +
  manifests, with the reconcile-vs-physical-files check enforced
  (lessons 9, 12, 25).
- **H5 — Identity mint pipeline.** The planned `COR-*`/`STU-*` mint on the
  final deduped artifact (r3e) operationalizes lesson 7 permanently.
- **H6 — Retry-window policy.** Before any quota-governed retry, probe the
  window's quota state first (cheap single request) and skip when dead —
  the r3e retry executed a full pass to learn a mostly-known negative
  (lesson 18–19).

## 4. Verification anchors (spot-check list)

- v0.2 five-provider table + hydration double-map gap:
  `workspaces/uav-pilot-demo/calibration/HARVEST_MULTIPROVIDER.md`.
- v0.2 sentinel verification + rejected constructed-guess DOIs:
  `workspaces/uav-pilot-demo/calibration/SENTINELS.md`.
- v0.3 definitive harvest report + coverage chain:
  `workspaces/uav-crop-weed-v03/calibration_v03/v03_r3_20261017_HARVEST_MULTIPROVIDER.md`.
- v0.3 r3b defect correction (snapshot-before-dedup):
  `workspaces/uav-crop-weed-v03/calibration_v03/v03_r3b_20261017_S2_REUSE_ADDENDUM.md`.
- v0.3 r3c/r3d/r3e round reports (both cited in §2 above).
- Standing probes: `_drivers/genericity_probe.py` (3/3),
  `_drivers/r3b_fixcheck.py` (8/8).
- Journal reconciliation: `workspaces/uav-crop-weed-v03/audit/journal.jsonl`
  (through `EVT-20261018222513-29987e`).

## 5. SCR1 Pass-1 screening lessons (2026-10-18)

27. **A coarse inventory validator false-greens exactly the defects that
    matter.** The v1 inventory checked only JSON-parse + row count and passed
    7 structurally defective files (a wrong screening_id, two reorders, three
    headerless reduced-schema files, three wrong-named files). Validity must be
    backed by a written contract — header attestation (screener_id + frozen
    SHAs), required row fields, ID-order 1:1 vs the view, filename canonicity —
    not by an existence check. Evidence: `_drivers/v03_scr1_schema.py`
    (`load_and_classify`), decisions_repair quarantine.
28. **The frozen prompt template is normative for what agents must produce.**
    A second validator flagged hundreds of template-conformant files because it
    demanded later-era extras (`reason`, `criterion_refs`) the frozen PASS-1
    template never requires, while omitting `one_line_support`, which the
    template DOES require. Over-constraining invents defects; derive required
    fields from the frozen instrument, not from what the last agents happened
    to write. Evidence: `v03_scr1_pass1_prompt_template.txt` lines 43–45.
29. **Filename canonicity is part of the contract; `int()`-parsing of names
    hides drift.** A2 batches 0240–0242 existed as `batch_00024X_…` (6-digit
    padding) from the early morning wave; every glob+int validator silently
    matched them to 240 and reported 283/283. The 4-digit-canonical rewrite of
    the inventory surfaced them instantly. Renamed after strict re-validation.
30. **Quarantine-not-mutate for content defects; alias-map-not-mutate for
    schema drift.** Decision files are evidence. Content defects (typo, reorder)
    are repaired mechanically with decisions-identical assertions and the
    original preserved in `decisions_repair/`. Schema drift (variant reason-code
    keys like `exclusion_reason_code`/`inclusion_hint`, string confidences
    `'high'`) is handled by a read-side alias map that TAGS every coercion —
    never silently coerced, never replayed into the artifact.
31. **Absent fields are recorded as debt, never fabricated.** Whole shards
    omitted `confidence` (T1/T7-era) or rationale-key parity; the reports return
    `None` with an explicit debt tag and a `v03_scr1_schema_debt_report.json`
    that triage can consume. Fabricating numbers or synthesizing criterion
    refs to "pass" a validator would be protocol fabrication.
32. **Dispatch prompts must pin the exact row schema verbatim from the frozen
    template.** Paraphrase produced per-shard drift: ~850 rows carrying
    rationale only under `reason`, ~950 missing `confidence`, alias keys,
    embedded-in-text codes. Agent self-reports are not eradicated by intent —
    each shard faithfully validated a *different* field set.
33. **Agent self-validation is not the orchestrator gate.** Multiple shards
    reported "all required fields present" while the template-canonical audit
    found gaps; the orchestrator re-validates every file independently against
    the frozen contract (twice, and computes totals from files, not reports).
34. **The rationale-grounding audit is a routing signal, never a verdict.**
    Deterministic token-coverage of reason/support vs visible title/abstract
    classified ~81% of rationales as grounded (FULL 11–13%, PARTIAL ~68–70%)
    and flagged ~6,041 rows (of 28,300) — including 51 INCLUDEs lacking
    platform/task anchors — that route to the boundary/human lane; the audit
    explicitly never overrides a screener, and lexical grounding is stated to
    be NOT semantic entailment. Evidence: `_drivers/v03_scr1_rationale_audit.py`,
    `v03_scr1_rationale_audit.json` (+ `_pre_repair.json` round 1).
35. **Cohen's κ collapses under extreme prevalence even at 91% raw
    agreement.** With ~90% EXCLUDE base rate, κ = 0.216 despite 91.48% raw
    agreement; interpretation policy (report raw agreement as the interpretable
    figure and name the prevalence paradox explicitly) should be decided
    BEFORE results arrive, not reverse-engineered after.
36. **Concurrent agent writes make mid-flight counts non-reproducible.**
    Read-only scans during shard rewrites transiently reported 563/566 files
    and stale cross-tabs; completed counts must be re-taken after writes settle
    and reconciled against physical file counts (lesson 25 generalizes from
    harvest rounds to screening lanes).
37. **Moderation substrate asymmetry is now recorded, not just applied.**
    The view lane (redacted) was ALWAYS safer than the original lane (0 filter
    or rate deaths across ~60+ batches at 6-concurrent vs 4 deaths on
    originals); the prompt-SHA era map (`attested 71/283` per family) now makes
    the pre-pinning wave visible as provenance debt instead of invisible luck.
38. **Blinded repair re-screen beats schema coercion for unattested files.**
    Files with no header at all (family/instrument provenance unverifiable from
    the artifact) are re-screened from scratch by a blinded repair shard (R1,
    150 records, zero failures, full canonical schema) rather than post-hoc
    re-attributed — Option C human confirmation stays intact across the repair.
39. **PowerShell `Set-Content -Encoding UTF8` silently emits a BOM.** A tooling
    fix executed via a PowerShell one-liner (blinding role-string neutralization
    on the 25 T4 verification packs) prepended `EF BB BF` and broke strict
    `json.loads` for every downstream validator while agents (more lenient
    reads) sailed through — the defect was invisible until the orchestrator
    gate ran. Rule: any artifact consumed by strict JSON parsers must be
    rewritten by Python (`encoding='utf-8'`, no BOM), never by PowerShell
    UTF8 rewrites; detect with a leading-byte check. Evidence: EVT-20261018225339,
    `_drivers/v03_scr1_t4_audit.py` strict header validation.
40. **Orchestration-level rate limits interact with total recent session
    volume, not per-lane concurrency.** The T3 wave had run stably at
    6-concurrent; minutes later, all six T4 round-1 shards died instantly
    with provider "Rate limit exceeded" BEFORE any read/write (distinct from
    the screening-kit filter/rate deaths — nothing to salvage). Standing
    ladder response (fall back ≤4) worked immediately: rounds 2–3 at 4 shards
    concurrent completed ~1,220 records with zero provider failures. Lesson:
    treat a wave-close-to-wave-dispatch gap as rate-budget debt — wait or
    relaunch at a lower rung; log the ladder decision as its own event.
    Evidence: EVT-20261018224713 (fallback), EVT-20261018230338 (wave close).
41. **The pack/manifest, not the dispatch prompt, is the count authority.**
    A round-1 dispatch prompt claimed pack_0019 held 36 records; the pack
    actually holds 50 (sample arithmetic 1,235 = 24×50 + 35 → packs 1–24
    full, pack_0025 holds 35). The shard screened all 50 and flagged the
    discrepancy — correct behavior. Prompt-draft figures are hints; validators
    must diff decisions against pack manifests, and count myths must be
    corrected in the record without touching artifacts. Evidence: T4-2F report,
    pack_0019 strict validation.
42. **A zero-INCLUDE third-rater signer is hygiene, not a validity gate.**
    With the sample drawn entirely from the closed mutual-EXCLUDE pool, 0/1,235
    INCLUDE is expected composition, not coincidence proof. Don't celebrate it
    as "agreement"; report it as a directional check and put the error-rate
    weight on the 98.7% EXCLUDE agreement + 16 PENDING routes. Evidence:
    `v03_scr1_t4_audit.json` (zero_include_signer block).
43. **The T4 rule held under pressure: a suggestion never overturns a closure.**
    All 16 T4 PENDING exceptions (incl. SCI-007054 — title-only UAV+herbicide
    guardrail fired correctly on a redacted record and SCI-003341, a redacted
    in-domain-adjacent title) routed to the human adjudication sheet; no closed
    exclusion was flipped. This preserved the Option C invariant while still
    measuring the exclusion-side error rate. Evidence:
    `calibration_v03/v03_scr1_t4_audit.json` (exceptions_to_human).
44. **Provider precision differs by ~70x; treat OpenAlex as the probe and
    Crossref as the recall net.** In `v03_r3e_20261017_deduped.json` (14,150):
    Crossref supplied 12,799 (90.4%) at a mutual-include yield of 5.4/1,000 vs
    OpenAlex 1,330 records yielding 385.7/1,000. Crossref records were 96.3%
    of the mutual-EXCLUDE lines and dominated by WRONG_TASK (10,578 — generic
    UAV engineering, conference proceedings: ICUAS/ICUAS-style DOIs visible in
    the raw sample), while OpenAlex's exclusions skew WRONG_REPORT_TYPE
    (reviews). Lesson: OpenAlex's concept/tag-ranked search is a precision
    probe; Crossref's bibliographic match is an unfiltered recall net —
    expect that ratio, budget compute accordingly.
45. **Uncapped Crossref recall was worth it — but only because screening is
    the part that scales, not the human.** The 69 include-lean records unique
    to Crossref (verified: none of their `sources` carry any other provider)
    include a 169-citation UAS/deep-learning strategy item and other real
    method studies (median 4 citations, sum 733). With Option C routing, human
    effort scales with include-lean/pending mass only; exclusions are closed
    by agent lanes and verified on a sample (98.7% T4 agreement). So the cost
    of a 70x-lower-yield provider stayed at agent-token/wall-time level, and
    recall maximization won. If the harness ever adds per-exclusion human
    review, this tradeoff collapses — the cap decision must be revisited then.
46. **Provider yield is a query-shape artifact, not a truth artifact.**
    Crossref's excess came from `type` filtering being absent (bibliographic
    match over the whole UAV engineering corpus; proceedings chapters) — the
    same queries on OpenAlex carried concept/date semantics. A
    harness-level fix (document type filter `journal-article,
    proceedings-article`; DOI dedup before screening; per-provider precision
    dashboards in the harvest report) would cut Crossref volume far below
    12.8k with most of the same unique recall. Evidence:
    `v03_scr1_provider_uniqueness.json` (excludes dominated by single
    crossref sources), `v03_r3e_20261017_crossref_year_sweep.json` design.
47. **Crossref date semantics leak even inside a "final" corpus.** 18
    2027-year rows survived into the screened corpus (e-pub-ahead-of-print
    style), i.e., even the r3c/r3d yearly sweep did not constrain them —
    eligibility must re-anchor at screening export time; the screening layer
    may keep them but the PRISMA report must re-derive in-window counts.
    Evidence: 14:1,417-2026 crossref exclude-year ledger in
    `v03_scr1_provider_investigation.json`; lesson 5 (v0.2).
48. **Provider quality belongs in every screening-side report and skill.**
    `screening-agent`/`workspace-manager` skills should surface
    per-provider stats (records, unique-source share, include rate/1k,
    no-abstract share — Crossref 15.4% vs OpenAlex 2.9% abstract-nulls)
    because a reviewer who sees only aggregate numbers cannot judge whether
    retrieve-side noise is devouring screening budget. Agent-side, pack
    builders should not assume uniform provider mix; agent skills for
    screeners can warn "this pack is 90% off-domain noise — expect
    exclusion-heavy returns" so shards calibrate expectations without
    breaking blinding (counts of codes per pack are already in
    `v03_scr1_pass1_prompt_template.txt` scope, not decisions).
49. **One query dominated; nine queries screened for nothing.** Per-query_id
    yield (from `v03_scr1_yield_investigation.json`): Q-R3-openalex alone
    produced 513/588 include-lean (385.7/1k); all Crossref queries yielded
    3.6–17.9/1k; and nine R3D quarterly slices (~1,622 records) produced ZERO
    include-lean — pure screening waste (~28 near-dead slices shipped ~6,200
    records for 8 includes). The harness should compute per-query yield
    DURING the harvest and stop/rank depleted query slices early rather than
    completing a fixed sweep plan.
50. **Caps are a weak cost lever; query shape is the strong one.** The cap
    replay (within-query file-order rank proxy) shows recall decays almost
    linearly: cap 100/query keeps 33% of the 69 crossref-unique include-lean,
    250 → 57%, 500 → 77%, ∞ → 100%. Crossref's bibliographic ordering does
    not rank relevant material first, so truncation buys volume reduction at
    nearly proportional recall loss. The real lever is query construction
    (type filter + DOI dedup + platform gates), not cap arithmetic.
51. **Two noise species need two different filters.** Of crossref's
    WRONG_TASK exclusions (10,659 rows): ~34% are comms/hardware/navigation
    engineering proceedings (fixable by a Crossref type filter) but a second
    species — topical agronomy with NO UAV platform — is invisible to type
    filters and needs an abstract-level platform gate. `v03_scr1_wrongtask_taxonomy.json`
    holds the 13-bucket first cut; 50% remains a long tail to be bucketed
    before the next harvest.
52. **Dedup must run a near-twin pass — and it missed 100% of them.** The
    probe found 356 near-twin pairs on screened lanes (284 exact-normalized
    title + 72 Jaccard>=0.9) with ZERO merged (263 merges / 1.8% dedup rate
    was the visible anomaly). Damage: 310 both-exclude pairs (inflated
    denominator), 6 double-includes, and 2 INCLUDE-SPLIT pairs = a work
    counted on BOTH the include and exclude lanes = PRISMA count corruption
    class; one example cluster 1346 vs 7947 differ only by title
    capitalization. Fix: exact-normalized + 0.9-Jaccard pass BEFORE
    screening; include-split pairs must be a hard validator failure. Evidence:
    `v03_scr1_neartwin_probe.json`. Bonus catch escalated to the human
    adjudication sheet: a split-pair include member uses PlanetScope
    satellite imagery — probable wrong-platform include-lean screener miss
    in a UAV-scoped review.
53. **Moderation-redaction is a Crossref metadata-quality tax — pay it
    upstream.** Ledger: 709 redacted records (97.6% crossref, 5.4% of crossref
    corpus + 18.0% raw abstract-empty; openalex 1.3%); 677 of 709 exited
    mutually-excluded, 263 via the MODERATION_TITLE_ONLY tag. The redaction
    band costs screening clarity twice (guardrail pendings + title-only
    exits). Fix: hydrate crossref DOIs via openalex BEFORE screening so
    abstract coverage gates retrieval ordering. Evidence:
    `v03_scr1_redaction_ledger.json` (views/pack flag agreement 709/71, zero
    disagreements).
54. **Disclosed noise priors break the judgment lanes — make blinding a
    measured property, not folklore.** The T5 A/B control held everything
    constant (same packs, model, frozen instrument) except one disclosed
    "this pack is ~95–100% exclusion" paragraph. Pack_0001 (clean noise):
    49/50 concordant with the blind baseline, the single shift was
    CONSERVATIVE (EXC→PEND), no mean-confidence inflation. Pack_0015
    (guardrail cases): both blind-held PENDINGs flipped to EXCLUDE — including
    a live guardrail violation on SCI-008686 (redacted title with
    UAV+crop-protection terms excluded WRONG_TASK @0.7) — firing the
    PRE-REGISTERED void condition. Verdict (policy 3): priors are inert on
    clean noise but act specifically on the PENDING/judgment class; "warn the
    shard" is rejected for judgment lanes. Arm-A pack_0015 decisions were
    QUARANTINED (never joined to lane totals; Option C surface unchanged —
    T4 remains the binding third-rater evidence and 008686 was already routed
    to the human sheet). Protocol: `v03_scr1_t5_ab_noise_prior_protocol.md`;
    results: `v03_scr1_ab_noise_prior.json`. Standing guidance: (1) never
    disclose outcome statistics to judgment/pending shards; (2) any proposed
    prior must pass the same A/B test before adoption; (3) mean-confidence
    deltas under-detect this failure mode — audit the PENDING-preservation
    rate explicitly.

