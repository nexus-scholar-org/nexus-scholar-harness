# Packet T-K0 — Repair and land the scholar-search-kit tree (kit repo)

**Status:** prepared, **not dispatched** — the publish step needs researcher authorization.
**Date:** 2026-10-20. **Delivery lane:** `RELEASE` (cross-kit: toolkit source + pin + vendored
snapshot). **Predecessor:** `T-D0D2` (harness-only, independent).

> **Position in the queue.** K0 is the hard prerequisite for **B-D1** (near-twin dedup gate)
> and every K1–K6 item in `docs/lessons/2026-10-17_uav_harvest_calibration_lessons.md`.
> Until the toolkit tree is green and pinned, no kit-side packet may be dispatched.

---

## TASK_ID

`T-K0` (toolkit surface; no harness task mapping).

## OBJECTIVE

Make the vendored `scholar-search-kit` tree **green, canonical, and pinned**, and land the
four demo-validated changes it carries through the kit's own contribution gate.

Concretely, four things must become true at the end:

1. `tools/scholar-search-kit/` is **byte-identical** to a merged canonical commit on
   `nexus-scholar-org/scholar-search-kit`.
2. That commit is recorded as the kit's full-SHA `default_rev` in
   `.agents/plugins/nexus-scholar/plugins.json`.
3. `packaging/nexus-scholar/nexus_scholar_pins.json` is regenerated from
   `plugins.json` (never hand-edited).
4. The kit's own test suite is green at that commit, and the harness conformance suite
   is green with the new pin.

---

## OWNER_SURFACE

**Canonical toolkit repository** `nexus-scholar-org/scholar-search-kit`, plus its
vendored snapshot `tools/scholar-search-kit/` inside this repo, plus the harness's pin
and metapackage-pins files.

---

## DEPENDENCIES_AND_EVIDENCE

### Current repository topology (verified 2026-10-20)

| Fact | Value | Verified by |
|---|---|---|
| Canonical upstream | `nexus-scholar-org/scholar-search-kit` | `plugins.json` `repo` |
| Upstream HEAD | `911d864fcb6a706d4c0339f80524a46f591e2cad` | `gh api repos/nexus-scholar-org/scholar-search-kit/commits/main` |
| Pinned `default_rev` | `911d864fcb6a706d4c0339f80524a46f591e2cad` | `plugins.json` — **matches upstream HEAD** ✓ |
| Personal fork | `nexus-scholar/scholar-search-kit` (isFork=true, parent = canonical) **already exists** | `gh repo list nexus-scholar` |
| Fork HEAD | `9af743b66e2429db5e4cd3afa0a0a80d7a6573df` — **stale**, last push 2026-09-24 | `gh api repos/nexus-scholar/scholar-search-kit/commits/main` |
| Vendored tree | **drifted** — 7 modified files vs the pinned SHA | `git status --short` |
| `gh` auth | account `nexus-scholar`, scopes `repo`, `workflow`, `read:org` | `gh auth status` |
| Kit's own CI | present at `tools/scholar-search-kit/.github` | directory check |
| Kit's own suite | **2 failures** against the dirty tree | `uv run pytest tools/scholar-search-kit/tests -q` |
| Harness suite | green at `c10d281` | `uv run pytest -q` |
| Baseline + pin checks | green at `c10d281` | the four `--check` scripts |

### The four demo-validated changes currently carried in the dirty tree

| File | Change | Demo lesson | Verdict |
|---|---|---|---|
| `src/scholar_search/models.py` | PMID namespace normalization (strip URL/scheme forms) | 22 | **keep** — fixes a real DOI-tier merge annulment |
| `src/scholar_search/enrichment.py` | OpenAlex-first hydration, pipe-batch 50 DOIs, S2 `x-api-key` + 403 unauthenticated fallback, DOI lower-casing | 53, 18 | **keep, but fix** — see NC-1/NC-2 |
| `src/scholar_search/providers/arxiv.py` | domain-neutral query compaction knobs (`compact_stoplist`, `compact_stem_families`, empty defaults) | 21 | **keep** — correctly parameterizes domain out of the kit |
| `src/scholar_search/providers/{openalex,pubmed,semanticscholar}.py` | provider-side auth/normalization adjustments | 4, 22 | **keep** — reviewed with the above |

### The one change that must be **decided**, not kept as-is

`src/scholar_search/dedup.py` — `_has_identifier_conflict` was rewritten to:

- allow a preprint/repository DOI to merge with a publisher DOI (deliberate, sound), **and**
- **drop `openalex_id` and `s2_id` from the conflict check entirely.**

The second half is a contract-relevant weakening. `DEVELOPER_COMPASS.md` §3 (Identity):
*"Conflicting non-empty identifiers must not be silently merged."* Prohibited shortcut:
*"merge records that carry conflicting persistent identifiers."* The Tier-2 fuzzy-merge
path (`dedup.py:94`) and `_fuzzy_match` (`dedup.py:212`) rely on that check to stop
title+year matches from merging records that carry conflicting provider IDs.

**Decision required (see DECISIONS below):** restore the `openalex_id`/`s2_id`
dimensions, or record an explicit, reviewed decision to relax them with a
narrowness condition and a conformance test.

---

## GOVERNING_REQUIREMENTS

### G1 — Three invariants change together, never alone

Per `AGENTS.md`: a toolkit change requires **all three** of (1) merge through the kit's
fork + canonical PR, (2) `plugins.json` `default_rev` bumped to the resulting **full
commit SHA** (never a floating branch), (3) the vendored `tools/<kit>/` tree
re-synchronized to that SHA, then (4) `nexus_scholar_pins.json` regenerated.

### G2 — Never patch only the vendored copy

`tools/scholar-search-kit/` is a **vendored snapshot**. Editing it without the canonical
merge is the prohibited shortcut. This is exactly the state the tree is in now.

### G3 — No direct push to the canonical repo's `main`

The change ships as: fork branch → PR → canonical merge → pin bump → vendor sync. The
harness repo's own `pull-request-gate` skill applies to the harness; the **same** rule
governs the kit repo (fork + PR), and `scripts/push_tools.py` — which clones the
canonical repo and pushes straight to `origin main` — **must not be used** for this
packet.

### G4 — Do not weaken Contract v1 identity semantics for adapter convenience

Any change to dedup identity behavior must preserve: distinct identity namespaces,
conflict detection for conflicting non-empty identifiers, and the rule that missing
identifiers remain compatible.

### G5 — The kit's own suite must be green, and the gates must be made to fail before they are believed

The two currently-failing tests must be repaired such that they assert the **new**
behavior, and at least one mutation-style negative control must prove the repaired gate
can fail.

### G6 — Domain configuration stays out of the kit

The arXiv compaction knobs must remain constructor parameters with **empty defaults**;
no domain token may appear in kit source.

---

## ALLOWED_PATHS

**In this repo (vendored snapshot + pins):**

```
tools/scholar-search-kit/src/scholar_search/dedup.py
tools/scholar-search-kit/src/scholar_search/enrichment.py
tools/scholar-search-kit/src/scholar_search/models.py
tools/scholar-search-kit/src/scholar_search/providers/arxiv.py
tools/scholar-search-kit/src/scholar_search/providers/openalex.py
tools/scholar-search-kit/src/scholar_search/providers/pubmed.py
tools/scholar-search-kit/src/scholar_search/providers/semanticscholar.py
tools/scholar-search-kit/tests/**                          (new/updated kit tests)
tools/scholar-search-kit/.github/**                        (only if a gate must be added)
.agents/plugins/nexus-scholar/plugins.json                  (default_rev bump only)
packaging/nexus-scholar/nexus_scholar_pins.json            (regenerated only)
```

**In the kit repository (external, via fork branch → PR):**

```
scholar-search-kit/**   (a branch on nexus-scholar/scholar-search-kit)
```

**In a scratch location (temporary clone, removed afterwards):**

```
<temp>/scholar-search-kit/**
```

## FORBIDDEN_PATHS

```
src/scholar_harness/**                 no harness change in this packet
src/scholar_harness/contracts/**       frozen Contract v1
workspaces/**                          READ-ONLY; write nothing
apps/**                                no UI change
docs/**                                no doc change in this packet
specs/**                               no spec change
```

**Pre-existing dirty files that must not be modified or absorbed:**

```
apps/research-ui/AGENTS.md
docs/README.md
docs/lessons/**                                (untracked)
docs/architecture/packets_from_uav_demo_2026-10-19.md   (untracked)
workspaces/uav-pilot-demo/**                   (staged)
workspaces/uav-crop-weed-v03/**                (untracked)
```

---

## INPUTS

| Path | Use |
|---|---|
| `tools/scholar-search-kit/src/scholar_search/dedup.py` | The file carrying the decision to make. Read lines 150–245 carefully. |
| `tools/scholar-search-kit/src/scholar_search/enrichment.py` | The file carrying the two failing tests' subject. |
| `tools/scholar-search-kit/tests/test_enrichment.py` | The two failing tests (lines ~181 and ~321) and their fixtures. |
| `tools/scholar-search-kit/tests/test_dedup.py`, `test_dedup_scoring.py` | Existing dedup behavior tests that must not regress. |
| `docs/lessons/2026-10-17_uav_harvest_calibration_lessons.md` §2 (lessons 15–23) | The evidence behind each change. |
| `docs/architecture/DEVELOPER_COMPASS.md` §3, §8 | Hard invariants and the toolkit synchronization rule. |
| `AGENTS.md` | The three-invariant rule and the "if you touch kit source, report which kit repo(s) it belongs to" requirement. |

---

## OUTPUTS

1. **A fork branch on `nexus-scholar/scholar-search-kit`** containing the repaired and
   decided change set, with kit tests green.
2. **A pull request** to `nexus-scholar-org/scholar-search-kit` describing each change
   with its demo evidence anchor (lesson number) and its test.
3. **The merged canonical commit SHA** on `nexus-scholar-org/scholar-search-kit`.
4. **`.agents/plugins/nexus-scholar/plugins.json`** — `default_rev` for
   `scholar-search-kit` set to that full SHA.
5. **`tools/scholar-search-kit/`** re-synchronized so the vendored tree equals the
   merged commit byte-for-byte.
6. **`packaging/nexus-scholar/nexus_scholar_pins.json`** regenerated via
   `uv run python scripts/generate_nexus_scholar_pins.py`.
7. **Validation evidence** for the kit suite, the harness suite, and all four baseline
   checks at the new pin.

---

## ACCEPTANCE_CRITERIA

| ID | Criterion |
|---|---|
| AC-1 | The kit's own suite is green at the merged commit: `uv run pytest tools/scholar-search-kit/tests -q` → 0 failures. |
| AC-2 | `test_hydrate_from_openalex_success` and `test_hydrate_missing_abstracts_fallback_to_openalex` are repaired to assert the **new** OpenAlex-first behavior, and a negative control proves each repaired assertion can fail. |
| AC-3 | The `_has_identifier_conflict` decision is implemented and covered: either (a) `openalex_id`/`s2_id` conflict dimensions restored, with a test proving two records with conflicting OpenAlex IDs are **not** merged; or (b) the relaxation retained under an explicit reviewed decision, with a test proving the relaxation is **narrow** (preprint-vs-publisher DOI only) and that same-namespace conflicts still block a merge. |
| AC-4 | The preprint↔publisher DOI allowance has its own test: a preprint DOI merges with its publisher counterpart, and two **different** non-preprint DOIs still conflict. |
| AC-5 | No domain token appears in kit source (no `UAV`, `weed`, `crop`, `crossref`/`openalex` domain constants, no hardcoded instrument SHA). A test or grep assertion covers it. |
| AC-6 | The arXiv compaction knobs keep **empty defaults**, and a test asserts the default output is byte-identical to the pre-change single-token translation. |
| AC-7 | The kit's own CI workflow runs the kit suite and is green on the PR. |
| AC-8 | The PR to `nexus-scholar-org/scholar-search-kit` is merged; the merged commit SHA is recorded. |
| AC-9 | `plugins.json` `default_rev` for `scholar-search-kit` equals the merged full SHA (40 hex chars), not a branch. |
| AC-10 | `tools/scholar-search-kit/` is byte-identical to the merged commit: `git status --short` shows **no** modification under `tools/scholar-search-kit/`. |
| AC-11 | `uv run python scripts/generate_nexus_scholar_pins.py --check` → `[OK]`; the pins file was **regenerated**, never hand-edited. |
| AC-12 | All four baseline checks remain green: `generate_contract_baseline.py --check`, `generate_contract_schemas.py --check`, `generate_two_study_contract_fixture.py --check`, `generate_nexus_scholar_pins.py --check`. |
| AC-13 | `uv run pytest -q` (harness) is green with the new pin, and the previously-passing test count does not decrease. |
| AC-14 | `uv run ruff check scripts/` passes. |
| AC-15 | The PR description maps each change to its demo lesson and names the canonical kit repo it belongs to. |
| AC-16 | No push was made directly to `nexus-scholar-org/scholar-search-kit` `main` or to the harness's `origin`. |

---

## NEGATIVE_CASES

1. **Conflicting provider IDs must still block a merge.** Two records with the same
   title/year but different `openalex_id` values must not silently merge (unless the
   reviewed relaxation in AC-3(b) explicitly covers that case, and then only narrowly).
2. **Different non-preprint DOIs must conflict** — the preprint allowance must not become
   a general DOI-difference bypass.
3. **A missing identifier stays compatible** — a record with a DOI and a record with only
   an arXiv ID remain merge-eligible (unchanged behavior).
4. **A rejected S2 key must not be reported as success.** The 403-unauthenticated
   fallback must degrade honestly; a failed hydration is not an empty success.
5. **An OpenAlex response that does not echo the requested DOI must not be silently
   attributed.** If the map is keyed by the echoed DOI, an unmatched work must be
   recorded as unmatched, not credited to the requested DOI.
6. **A non-numeric or out-of-range confidence is not coerced** — no value is invented.
7. **Default kit behavior must be unchanged for a caller that passes no domain config**
   (the arXiv compaction must be a no-op at defaults).
8. **The pin must be a full SHA, never a branch name.** A validation must reject a
   non-hex `default_rev`.
9. **The vendored tree must not be edited independently of the canonical merge** — a
   check must fail if `tools/scholar-search-kit/` diverges from the pinned SHA.
10. **No direct push to canonical `main`** — the pre-push gate (or its equivalent
    verification) must block it.

---

## VALIDATION_COMMANDS

```powershell
# kit suite
uv run pytest tools/scholar-search-kit/tests -q

# harness suite (with the new pin)
uv run pytest -q

# drift / pin checks
uv run python scripts/generate_nexus_scholar_pins.py --check
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check

# lint
uv run ruff check scripts/

# vendored-tree drift
git status --short tools/scholar-search-kit/
```

---

## TOOLKIT_SYNC_AND_PIN_PLAN

This packet **is** the toolkit-sync plan. The ordered sequence:

1. Repair + decide in a **temporary clone** of the fork.
2. Green kit suite in the clone; open the PR to the canonical repo.
3. Merge → record the canonical full SHA.
4. Bump `plugins.json` `default_rev` to that SHA.
5. Replace `tools/scholar-search-kit/` with the merged tree so it is byte-identical.
6. `uv run python scripts/generate_nexus_scholar_pins.py` (regenerate, never hand-edit).
7. `uv run python scripts/generate_nexus_scholar_pins.py --check` → `[OK]`.
8. Full harness suite + the four baseline checks.

---

## WORKSPACE_AUDIT_EVENT

**None.** This packet does not mutate any workspace under `workspaces/`. The workspace
audit ledger is not a sink for repository-level changes; the PR, the pin bump, and the
validation output are the record.

---

## DECISIONS REQUIRED FROM THE RESEARCHER (before dispatch)

| # | Decision | Recommendation |
|---|---|---|
| D-1 | **Fix-forward or revert-then-reapply** for the dirty kit tree? | **Fix-forward.** The four changes are demo-validated and lessons-backed; reverting discards evidence and re-derives it. |
| D-2 | **`_has_identifier_conflict`:** restore the `openalex_id`/`s2_id` conflict dimensions, or retain the relaxation under an explicit reviewed decision? | **Restore them**, and keep only the preprint↔publisher DOI allowance (AC-3(a) / AC-4). The relaxation as written removes two identity-conflict dimensions with no narrowness condition, which conflicts with `DEVELOPER_COMPASS.md` §3. |
| D-3 | **Publication authorization.** May the agent push a branch to `nexus-scholar/scholar-search-kit` and open a PR to `nexus-scholar-org/scholar-search-kit`? | **Authorize the fork branch + PR**, but require the researcher to **merge the PR themselves**, so the canonical merge is an explicit human act. The agent stops after the PR is open and CI is green, and reports the PR URL + SHA for the reviewer to check. |
| D-4 | **Harness pin bump** — bump `plugins.json` in the same PR as the kit merge, or in a follow-up harness PR? | **Follow-up harness PR.** Keep the kit PR and the harness pin/vendored-sync in separate PRs so the kit diff is reviewable on its own, per "No packet may mix a kit change, a contract version change, and an internal refactor." |

## FOLLOW-UPS (not in this packet)

- **B-D1** — the near-twin dedup pass, with the gate relocated per the orchestrator
  review (detection at dedup stage; lane-split gate as a separate screening-stage
  packet **D-4**).
- **K1–K6** — the lessons backlog for the kit.
- **`scripts/push_tools.py`** — its current clone-canonical-and-push-to-`origin main`
  behavior does not satisfy the fork+PR gate for kit repos and should be corrected or
  retired. Separate docs/tooling task.
