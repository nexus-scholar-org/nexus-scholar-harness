# Codebook pilot assessment — 2 full texts (2026-10-13)

**Scope:** Pilot `CHARTING_CODEBOOK.md` v0.2 + `charting.schema.json`
(`profile_version 0.2`, protocol fingerprint
`sha256:a1fd8d2a…73451`) on WeedsGalore arXiv v1 and SemiWeedNet Vor.
No accepted rows were created (acceptance gate unsatisfied — see
`SOURCE_REGISTER.md` §5). This assessment tests whether the codebook *can*
express the observed evaluation designs, not whether extraction is accurate
(single researcher, no second extractor, no adjudication — agent critique is
not a second human).

## 1. Verdict: codebook sufficient for pilot; NO semantic amendment

The v0.2 taxonomy expressed all four preliminary settings without new values:

- **Study vs evaluation separation held.** WeedsGalore required 1 study + 3
  settings (clean benchmark / calibration / combined OOD); SemiWeedNet 1 + 1.
  Grouping repeated seeds/conditions (RGB×MSI, labelled proportions) within a
  setting worked; no cross-dataset leaderboard was implied.
- **Combined shift + definition note held.** WG-E3 (field + year + cover +
  growth-stage + class-prior) coded `shift_axes combined` with an explicit
  axis list in `setting_definition`. No isolated sensor/temporal effect was
  claimable — exactly the safeguard the codebook was designed to enforce.
- **Temporal vocabulary held.** `multiple_dates_no_heldout` (WG-E1/E2) vs
  `heldout_date`-within-combined (WG-E3) vs `not_reported` (SWN, no date
  evidence) distinguished multitemporal data from held-out testing. No new
  temporal value needed.
- **Target-data-use guard held.** SemiWeedNet unlabelled-from-same-pool coded
  `none` with derivation note, not `unlabeled_adaptation`. The codebook’s
  “explicitly distinct evaluation target + assignment evidence” bar prevented
  the semi-supervised = adaptation collapse.
- **Sensor honesty held.** `band_availability` (WG RGB-vs-MSI) vs `none`
  (SWN RGB-only despite multispectral inventory) separated evaluated channels
  from inventory. No new sensor value needed.
- **Uncertainty vocabulary held.** `calibration_evaluated` (WG-E2 ECE) vs
  `none` (WG-E1 benchmark) vs `not_reported` (SWN, SWN-OOD absent) separated
  measured calibration from attention/consistency display. No new value.
- **Evidence-state discipline held.** `reported` (quote + locator) /
  `not_reported` (sections checked, note records scope) / `unavailable`
  (source/section uninspectable, e.g. IEEE final, Phase-4, full Tab.7) /
  `conflicting` (reserved; preprint-vs-publisher delta retained narratively,
  not forced) covered all cases. `not_applicable` unused in pilot (correct —
  no inapplicable axis arose).

**Consequence:** No semantic protocol or codebook change is proposed. No
`AMENDMENTS.md` entry, no fingerprint change, no re-screening trigger.
`protocol.json` re-validated VALID (0 errors/warnings) and fingerprint
recomputed identical (`sha256:a1fd8d2a…73451`) on 2026-10-13. Charting schema
structural check from calibration (`verification.json`: 0 errors) still
stands; no new synthetic cases were needed for this assessment. If a future
full-text forces a taxonomy change, it must be logged with old/new
fingerprints + reason per PROTOCOL.md — not regenerated to conceal mismatch.

## 2. What the pilot proved (and did not prove)

- **Proved (formative):** the codebook can separate clean vs stressed vs
  calibration settings; combined-shift notes prevent isolated-effect claims;
  RGB-vs-inventory and semi-supervised-vs-adaptation guards fire on real text;
  per-cell locators + verbatim quotes are collectable from convenience
  extractions (pending E1/E2 re-verification).
- **Did NOT prove:** charting speed, accuracy, inter-extractor agreement,
  calibration of ECE claims, OOD Tab.7 completeness (partial), IEEE-final
  equivalence, or any prevalence/gap claim. Two papers cannot power a review.
  All `not_reported`/`unavailable` cells are missing-source discipline only.

## 3. Relational / lineage / link checks (pre-acceptance)

- Unique study keys (`STU-PRELIM-WG/SWN`) and setting keys (WG-E1/E2/E3,
  SWN-E1) are unique by construction in notes; no accepted linkage exists to
  check against a registry (0 accepted rows — check vacuously passes, not as
  evidence of a corpus).
- Every substantive preliminary value carries a locator + verbatim quote;
  derived values (e.g. SWN `target_data_use none`) carry a derivation note +
  supporting inputs. Schema-validity ≠ entailment is preserved: notes are NOT
  presented as `charting.schema.json` rows.
- Links verified: `github.com/GFZ/weedsgalore` (claimed, not fetched);
  Frontiers/SemiWeedNet DOI resolves; arXiv `2502.13103v1` single-version
  confirmed via API; OpenAlex/Crossref dates reconciled (§SOURCE_REGISTER).
  MDPI 403 disclosed as provider failure. No link is claimed verified beyond
  what was fetched.

## 4. Supported vs prohibited interpretations (from this pilot)

**Supported (source-grounded):** WG in-domain MSI > RGB with class-level
heterogeneity + small-weed failure modes; WG probabilistic ECE improvement
(in-domain, K=5, DeepLabv3+ only); WG OOD direct-transfer advantage on
Maize2024 (52.55% mIoU, +23.22 pp) **as a combined-shift result** with
preserved comparator failures; SWN in-domain semi-supervised competitiveness
at 20% labels with matched controls + preserved comparator instabilities;
SWN evaluation limits (random image split, RGB-only, single subset).

**Prohibited (listed in CHARTING_PILOT_NOTES.md §Prohibited, enforced):**
preprint = published; diversity = validation; multitemporal = held-out;
inventory = evaluated channels; semi-supervised = adaptation; combined =
isolated effect; attention = calibration; schema pass = entailment; sentinels
= held-out performance; background probes in denominators.

## 5. Remaining codebook risks

1. **Small-n OOD quantification** (6 patches) has no interval guidance in the
   codebook — future charting should record patch-level n explicitly (done
   here) and resist post-hoc CIs.
2. **Split-unit edge:** WG-E3 `field` + patch-scoring note worked, but a
   future multi-field OOD may need `multiple` + definition — allowed, with
   explanation, per codebook.
3. **`none` vs `not_reported` for uncertainty** will recur; the pilot’s rule
   (silence after checking relevant sections = `not_reported`; explicit
   “no UQ” statement = reported `none`) should be kept as a coding convention,
   not a schema change.
4. **IEEE-final reconciliation** is the top provenance risk: accepted charting
   must re-verify every WG quote against E1/E2 bytes of the *published*
   report (or explicitly scope to the preprint family with contradiction
   retained).

## 6. Freeze status

Protocol remains **provisional v0.2, NOT frozen** (researcher review of
assumptions + calibration outcomes pending; final search date, reviewer
assignments, and accepted lineage still open). This pilot does not authorise
freezing.
