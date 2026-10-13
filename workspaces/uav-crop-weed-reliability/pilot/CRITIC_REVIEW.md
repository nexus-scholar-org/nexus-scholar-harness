# Independent critic review — codebook pilot (2026-10-13)

**Critic:** extraction-critic subagent `ses_ecb3667dcffehT6j1S6sH7l4cJ`
(artifact-read-only; no files written, no repairs).
**Doer:** senior-researcher assistant (preliminary notes, single researcher —
not a second extractor).
**Scope:** `pilot/CHARTING_PILOT_NOTES.md` + `pilot/SOURCE_REGISTER.md` +
`pilot/PILOT_ASSESSMENT.md` (no-amendment claim) against immutable convenience
sources (`extracted_prelim/*.md`, `pdfs/*.pdf` SHA256 in register),
`PROTOCOL.md` v0.2 / `CHARTING_CODEBOOK.md` v0.2 / `charting.schema.json`
(profile 0.2, fingerprint `sha256:a1fd8d2a…73451`), and claim-scope safeguards.

## Verdict: PASS (0 critical, 0 major, 3 minor)

Anchoring spot-checks 7/7 SUPPORTED verbatim (modulo PyMuPDF hyphenation):
WG sensor bands (DJI P4 5-ch + RGB vs MSI); WG spatial 70:15:15 patch split;
WG `multiple_dates_no_heldout`; WG-E2 ECE Tab.6 (RGB 0.0058→0.0041, MSI
0.0048→0.0018, K=5, pd=0.5); WG-E3 OOD (6 patches 90 m2 1000×1100px, 52.55%
mIoU +23.22 pp, combined field/year/cover/growth axes, MaizeOrWeed failure,
same drone); SWN RGB-only 289 images 000–004 8:2 + `target_data_use none`
derivation (same-pool xl/xu). Negative evidence preserved (8%/13% errors,
quickweed→amaranth 28%, comparator instabilities). Counts consistent (0
accepted / 2 prelim studies / 4 prelim settings / 1 unresolved / 2
background). No invented DOC IDs, no schema rows fabricated, no E1/E2 claim,
no preprint=published equivalence, no sentinel-as-performance.

## Findings and disposition (critic did NOT repair; doer records here)

- **F-01 minor (uncertainty `none` vs `not_reported`):** WG-E1 codes
  `reported none` for benchmark UQ absence while assessment proposes
  silence=`not_reported`. *Disposition:* RETAINED transparently as
  preliminary; convention to be clarified before freeze (assessors §5 risk 3).
  No accepted row affected (0 accepted). Not escalated.
- **F-02 minor (WG-E3 `sensor_awareness band_availability` train-side):**
  OOD value inherits train-side RGB/MSI contrast not ablated on OOD target.
  *Disposition:* RETAINED with explicit “no OOD sensor claim” note;
  convention (OOD = `none`/`not_reported` unless band ablation on target,
  modality in definition only) deferred to pre-freeze coding convention, not
  a schema change. Not escalated.
- **F-03 minor (`shift none` + `temporal not_reported` coherence):**
  SWN `shift_axes none` with unknown dates needs one-line convention.
  *Disposition:* RETAINED; implied rule (`none` = no shift experiment in
  inspected scope, compatible with date-unknown) to be made explicit before
  freeze. Not escalated.

## Unresolved (correctly retained, not failures)

IEEE-final Tab.7 diff + full capture; S4 bytes (MDPI 403 provider failure);
Phase-4 streams; final search date; reviewer/adjudicator assignment; protocol
freeze; inter-extractor agreement. Assessment §§2/6 explicitly disclaims
accuracy/speed/agreement/prevalence and does not authorise freezing.

**Agent critique ≠ second human extractor.** No independent human labeling is
claimed. Formal evaluation remains gated (see `PROSPECTIVE_EVALUATION_DESIGN.md` §9).
