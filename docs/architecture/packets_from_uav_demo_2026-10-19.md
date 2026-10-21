# Packet drafts from the UAV v03 demo — 2026-10-19

Draft ticket packets converting the UAV-HARVEST demo findings (lessons 44–54,
artifacts under `workspaces/uav-crop-weed-v03/`) into compass-§11-format
assignments. **Draft only** — none of these is dispatched; each needs the
mandatory start procedure (baseline/schemas/pins checks) before a coder sees it.
Priority order: B-D1 (dedup gate), D-1 (verification lane), D-2 (alias-map
validator), D-3 (prior ban), then A-1, C-1, AG-1, AG-2, HCM-1, X-1.

---

## B-D1 — Near-twin dedup gate in Packet B (kit: scholar-search-kit)

```text
Goal:
  Add a near-twin detection pass to the search-kit dedup stage and expose a
  typed result so Packet B corpus snapshots can fail closed on split pairs.

Immutable parents:
  Packet B corpus snapshot artifact (fingerprinted); document records with
  provider/source provenance.

Output:
  - `scholar_search.dedup` near-twin pass: exact-normalized-title +
    token-Jaccard>=0.9 candidates that were NOT merged.
  - Corpus snapshot manifest field: near_twin_summary {pairs_total,
    merged_ok, split_include_excluded, per_provider_pair_labels}.
  - Typed hard-failure condition: a candidate pair where one member would
    land on an INCLUDE lane and the other on an EXCLUDE/PENDING lane must
    block corpus acceptance until resolved.

Must preserve:
  - Existing dedup behavior unchanged when no near-twins are found.
  - Provider/source provenance per pair (crossref|crossref vs crossref|openalex
    mix changes remediation strategy).
  - No mutation of upstream raw artifacts.

Must reject:
  - Merging when persistent identifiers conflict non-empty (existing rule).
  - Silent merge of near-twins; the pass DETECTS and gates, it does not merge
    without explicit policy.

Tests:
  - Round-trip: known twin pairs detected (fixture from UAV: titles differing
    only by capitalization; 2 include-split examples).
  - Negative: no false merge of distinct works sharing Jaccard>=0.9 boilerplate.
  - Determinism: identical corpus -> identical pair set.
  - No-publication: include-split detection blocks snapshot acceptance.

Out of scope:
  - Screening lanes/decisions (Packet D owns those); provider query filters.

Evidence anchors:
  workspaces/uav-crop-weed-v03/calibration_v03/v03_scr1_neartwin_probe.json,
  _drivers/v03_scr1_neartwin_probe.py (algorithm reference), lesson 52.
  Pre-44 continuity: lesson 7 (dedup-run-local IDs are not study identities),
  8 (title match is not identity), 15 (Deduplicator mutates representatives
  in place — the near-twin pass must not repeat this), 16 (duplicate
  detection must run against the full pool, not just representatives —
  design constraint for the pass), 17 (dedup rate is not a constant —
  4.85% v0.2 vs 1.8% v0.3 was the anomaly that made the probe suspicious),
  23 (sentinel fixtures must encode identity edge cases — the twin fixtures
  belong in the sentinel set).
Delivery lane: RELEASE (cross-kit: search-kit + harness acceptance).
```

---

## D-1 — Verification-sample lane in Packet D (harness + agent-kit)

```text
Goal:
  Make the demo's T4 wave a first-class, re-runnable harness feature: a
  systematic verification sample over any closed decision lane with
  blinding-neutralized packs and an exclusion-side agreement audit.

Immutable parents:
  Accepted screening batch artifacts + parent decision artifacts
  (fingerprinted, Packet D); corpus snapshot for stratification metadata.

Output:
  - Sample generator (systematic-k) producing pack manifests with counts and
    checksums (reference: v03_scr1_verify_sample.py).
  - Blinding-neutralized pack views (moderation_redacted flags, no
    role/decision strings) with a pre-dispatch leak check.
  - Verification lane decisions schema: screener tag, both frozen SHAs,
    canonical row fields (screening_id, decision, reason, reason_code,
    criterion_refs, confidence, one_line_support).
  - Audit artifact: agreement counts, exclusion-side agreement rate,
    PENDING-preservation rate, exceptions routed to human adjudication —
    with the standing rule that a verification suggestion NEVER overturns a
    closed decision.

Must preserve:
  - Closed-lane decisions immutable under verification.
  - Blinding: packs carry no decisions/reasons/confidences from other lanes.
  - Option C semantics (human confirms; suggestions only).

Must reject:
  - Pack files with role-string leaks or BOM/encoding defects (strict utf-8
    no-BOM, pre-dispatch check — lesson 39).
  - Count mismatches vs manifest (pack N declared N records — lesson 41).

Tests:
  - Round-trip on a fixture workspace; negative: leaked role string detected;
    negative: missing decisions vs manifest; determinism of sample IDs.

Out of scope:
  - Prior/noise-prior text (D-3); fulltext arbitration routing.

Evidence anchors:
  v03_scr1_verify_sample_manifest.json, verification_lane tree,
  v03_scr1_t4_audit.py, lessons 40-43, 54.
  Pre-44 continuity: lesson 19 (quota-state-aware idempotent machinery —
  the wave/ladder discipline's producer-side twin), 25 (new-file-per-round +
  append-only journal — the lane's artifact discipline), 32 (dispatch
  prompts pin row schema verbatim — what makes the strict validation
  meaningful), 33 (agent self-validation is not the orchestrator gate —
  the reason D-1 validates independently).
Delivery lane: STANDARD (harness-owned, no contract change).
```

---

## D-2 — Alias-tolerant decision reader with debt tags (harness screening)

```text
Goal:
  Replace ad-hoc schema handling with the demo-proven reader: canonical row
  fields plus a tagged alias map for variant producers, recording debt
  instead of coercing or failing.

Immutable parents:
  Screening decision files (producer output), schema v1 canonical template.

Output:
  - `load_and_classify`-style reader: canonical fields first, tagged aliases
    (exclusion_reason_code, pending_reason_code, inclusion_hint, reason_CODE,
    reason-as-object) recognized by explicit map; unknown keys preserved and
    tagged UNKNOWN.
  - Three-tier inventory outcome: VALID / DEBT (tagged) / BAD.
  - Debt ledger artifact (per-file, per-tag counts) consumable by reports.

Must preserve:
  - Never silently coerce variant codes; absent fields are recorded debt,
    never fabricated.
  - No mutation of producer files (alias-in-reader only).

Must reject:
  - Files with no canonical or alias-decodable fields -> BAD (not DEBT).
  - Decisions missing lineage at collection time (existing Packet D rule).

Tests:
  - Fixture rows per alias class; negative mutation -> DEBT not crash;
    determinism; BAD file blocks collection.

Out of scope:
  - Producer-side prompt fixes (agents emitting variants is upstream debt).

Evidence anchors:
  _drivers/v03_scr1_schema.py, v03_scr1_inventory.py (v3 three-tier),
  v03_scr1_schema_debt_report.json, lessons 27-38 block.
  Pre-44 continuity: lesson 25 (new-file-per-round discipline — reader adds
  no mutation, writes only NEW sidecars), 31 (absent fields are recorded
  debt, never fabricated — the reader's founding rule), 33 (agent
  self-validation is not the orchestrator gate — reader IS the gate side).
Delivery lane: RELEASE (decision contract surface).
```

---

## D-3 — Screening prompt hygiene: outcome-prior ban (harness + agent-kit)

```text
Goal:
  Encode lesson 54 as a contract + conformance test: screening prompts must
  not disclose outcome statistics (expected exclusion rates, pack
  composition priors) to judgment/pending-capable shards; PENDING
  preservation under any prior is an audited invariant.

Immutable parents:
  Frozen prompt template (Packet A instrument); verification lane (D-1).

Output:
  - Lint-style checker on dispatch prompts (flag disclosed priors).
  - Optional A/B harness command pair replicating
    v03_scr1_t5_ab_noise_prior_protocol.md (dispatch informed + blind arms,
    paired concordance, PENDING-preservation audit).
  - Documentation: priors allowed only for non-judgment classification
    passes, never alongside abstract-null/guardrail rules.

Must preserve:
  - Blinding rules (D-1); Option C.

Must reject:
  - Prompt bundles whose hash matches a known prior-tainted template
    (registry check).

Tests:
  - Fixture informed prompt -> checker FAIL; clean prompt -> PASS;
    PENDING-preservation audit on the T5 fixture reproduces the violation
    (SCI-008686) and quarantines arm output.

Out of scope:
  - Provider rate-limit ladder (AG track).

Evidence anchors:
  v03_scr1_t5_ab_noise_prior_protocol.md, v03_scr1_ab_noise_prior.json,
  lesson 54.
  Pre-44 continuity: lesson 1 (provider endpoint semantics embed context the
  model cannot see — why prior statistics do not belong in record-level
  prompts at all), 32 (dispatch prompts pinned verbatim — the lint must
  diff against the pinned template, not free text).
Delivery lane: STANDARD.
```

---

## A-1 — Instrument amendment record (Packet A, harness contracts)

```text
Goal:
  Add a typed amendment record to the protocol artifact so mid-review
  instrument changes (e.g., adopting multi-agent screening) are registered
  with lineage instead of living only in journals.

Immutable parents: existing protocol artifact + fingerprint.

Output: protocol amendment {amended_instrument, reason, prior_sha,
  new_sha, decided_by, decided_at} — versioned, appended, never overwritten.

Must preserve: fingerprint continuity; no silent template swap.
Must reject: amendment referencing unknown prior SHA; out-of-order chains.
Tests: round-trip; negative: wrong prior; determinism.
Out of scope: criteria content itself.
Evidence anchors: pending Step-2 amendment need; journal chain usage in demo.
  Pre-44 continuity: lesson 26 (frozen-protocol fingerprint re-verification
  is the existing cheap gate this amendment record extends).
Delivery lane: RELEASE (protocol identity surface).
```

---

## C-1 — DEBT outcome tier (Packet C acceptance vocabulary)

```text
Goal: extend acceptance outcomes with an explicit DEBT tier (degraded but
  explained) alongside SUCCESS/FAILED, backed by structured debt tags.

Output: acceptance records carrying debt_tags[]; reports render debt without
  failing publication when policy allows.
Must reject: DEBT without tags; SUCCESS with debt.
Tests: per-tag fixtures; no-publication on BAD; determinism.
Evidence anchors: v03_scr1_schema_debt_report.json; BOM incident
  (malformed artifact stopped at orchestrator gate).
  Pre-44 continuity: lesson 3 (honest under-cap returns — a sibling of
  "degraded but explained"), 6 (hydration double-map artifact — degradation
  that must be explained, not hidden), 10 (supersession must be explicit —
  DEBT's ancestor in outcome vocabulary).
Delivery lane: STANDARD.
```

---

## AG-1 / AG-2 — Agent-controls runtime policies (AG track)

```text
AG-1 (rate ladder): codify provider/orchestration rate-limit handling as a
  dispatch-layer policy: start concurrency per lane evidence, on
  provider-level failure fall back (6->4->2), cool down between wave closes,
  journal ladder decisions. Evidence: lessons 40, EVT-20261018224713.
  Pre-44 continuity: lessons 18 (retrying burned quotas buys nothing),
  19 (quota-state-aware idempotent machinery beats one-shot drivers),
  20 (keyless-first standing discipline) — same resilience family,
  provider-side; the ladder generalizes it to the dispatch layer.
AG-2 (AG-03A fixture): the UAV human-lead packet (626 include-lean +
  506 pending + 41 ties + 16 T4 exceptions + 8 pre-read escalations +
  adjudication sheet) becomes the real fixture for the protected-publisher
  pilot instead of synthetic data.
Delivery lane: AG-1 STANDARD; AG-2 per AG-03A feasibility doc.
```

## HCM-1 / X-1 — Track ratifications

```text
HCM-1: ratify the promotion rule — a workspace _drivers/ script graduates to
  kit (search/agent) or harness only when its domain constants are
  parameterizable away; else it remains provenance. Adopted as HCM guidance.
X-1 (cross-kit): coordinated minor contract-version decision for shared
  types introduced by D-1/D-2/C-1 (alias map, debt tags, verification lane)
  — one decision document, one schema regeneration, one fixture wave.
  Pre-44 continuity: lesson 22 (identity normalization is shared critical
  path — PMID namespace collision was caught pre-contract), 23 (sentinel
  sets must encode identity edge cases) — the shared-type decision should
  extend, not reinvent, the sentinel discipline.
Delivery lanes: HCM-1 docs-only; X-1 RELEASE.
```

---

## Ordering note

B-D1 and D-2 are prerequisites for trusting D-1's audit semantics on
historical data (aliases/twins corrupt counts). D-3 depends on D-1's
PENDING-preservation audit existing. A-1/X-1 are contract-version decisions —
they gate regeneration of schemas/fixtures/pins and must not be hand-run.
