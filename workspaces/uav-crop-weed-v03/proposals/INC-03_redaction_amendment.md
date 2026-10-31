# INC-03 redaction / consent — draft amendment (NOT APPLIED)

**Status:** draft for researcher decision. Nothing in this file has been applied:
`protocol.json`, `SCREENING_CRITERIA.md`, the 283 decision artifacts and the
signed `HumanConfirmation@1` are byte-identical to the frozen state.

**Raised by:** `AMENDMENTS.md` §5 item 5 and the `INC-03` row of the v0.3 freeze
table.

## The defect

The frozen INC-03 text is one sentence of *eligibility* and one sentence of
*screening administration*, with three personal names in it:

> Published from 2020 through the recorded final search cutoff, inclusive;
> English full text in scope. Older foundational UAV datasets remain
> background/provenance sources unless a logged amendment expands eligibility.
> Screened under Option C (single lead reviewer Mouadh Bekhouche confirming all
> agent triage suggestions, with independent ~10% random sample plus
> boundary-exclude verification by Soumia Zertal and Fadhila Djenba).

Two independent problems:

1. **Unconsented personal data.** `Soumia Zertal` and `Fadhila Djenba` are named
   as co-reviewers without recorded consent, in an artifact headed for a
   public-bound branch.
2. **Workflow text inside an eligibility criterion.** INC-03 answers "which
   records are eligible"; the Option C sentence describes *who screened and
   how*. A change of screening staff would then be a change of eligibility
   criteria — the wrong coupling, and it makes the instrument look like it
   changed when only the process did.

## What is frozen, and what names it

| Artifact | Hash / identity | Contains the names |
| :--- | :--- | :--- |
| `protocol.json` (compiled instrument) | `sha256:f81e6c58…f755` | yes (via INC-03) |
| `SCREENING_CRITERIA.md` (rendered criteria) | `9ae1f97d…b86f` | yes |
| 283 `literature/screening/batch_NNN_decisions.json` | hashed in `HUMAN_CONFIRMATION.json` | **yes** — the criteria text is embedded in every batch |
| `literature/screening/HUMAN_CONFIRMATION.json` | fingerprint `e1f51ffe…f876800` | no (reviewer + hashes only) |
| `intent.json` | — | yes (criterion source) |

The important consequence: **the names are not only in the public-bound
sentence.** Editing INC-03 in `protocol.json` and re-rendering the criteria
changes the criteria hash and rewrites every one of the 283 decision artifacts,
which invalidates the signature. A "quick find-and-replace" is therefore not
available.

## Option A — obtain consent (unredacted publication)

**What it needs:** written consent from Soumia Zertal and Fadhila Djenba to be
named as co-reviewers in the published protocol text, recorded in
`AMENDMENTS.md` with date and scope (and separately in the journal).

**Effect:** the frozen bytes stay as they are; the publication block lifts
because the names are no longer unconsented. No hash changes, no re-signing.

**Cost:** external dependency; the pilot cannot publish until both respond.

**Residual:** the workflow-in-eligibility problem remains. Consent fixes the
personal-data issue, not the criterion/process coupling.

## Option B — redacted publication rendering (recommended)

Publish a **separate rendering** of the criteria in which INC-03 carries only
the eligibility sentence, and the screening design moves to a "Screening
conduct" note expressed in roles, not names:

> **INC-03 (published rendering).** Published from 2020 through the recorded
> final search cutoff, inclusive; English full text in scope. Older foundational
> UAV datasets remain background/provenance sources unless a logged amendment
> expands eligibility.
>
> **Screening conduct (not an eligibility criterion).** Agent triage suggestions
> were confirmed by a single lead reviewer; a ~10% random sample and all
> boundary-exclude decisions were independently verified by two co-reviewers.

**Hard rules for this option:**

1. **Do not edit the frozen instrument.** `protocol.json`,
   `SCREENING_CRITERIA.md` and the 283 batch files keep their bytes. The redacted
   text exists only in the publication rendering.
2. **Never present the redacted hash as the screening instrument.** The
   rendering must state, in its own header:
   - screening was conducted against the frozen criteria
     `9ae1f97d…b86f` / protocol `sha256:f81e6c58…f755`;
   - the rendering is redacted for publication and is **not** the instrument
     the decisions attest;
   - the confirmation fingerprint is `e1f51ffe…f876800`.
3. **Say "redacted", not "amended".** An editorial redaction of a publication
   copy does not supersede a frozen instrument.
4. **Do not copy the rendering back** into `SCREENING_CRITERIA.md`. If it ever
   becomes the instrument, that is a new freeze with a new fingerprint, new
   rendered criteria and a re-confirmation — not a silent edit.

**Effect:** unblocks publication without consent, because no personal data is
published. No hash changes. No re-signing. The workflow/eligibility separation
is fixed in the published text.

**Residual:** the internal workspace still holds the names (unavoidable: they
are in the hashed batches). If that internal tree is ever published as-is, the
consent question returns — so the publication set must be explicit about which
files it includes.

## Recommendation

**Option B**, with a written note that the frozen instrument retains the names
and that publication uses a redacted rendering. It is the only option that
publishes without waiting on third parties, and it does not touch the signed
evidence chain. Option A remains valid if the co-reviewers want to be credited
by name.

## What must never happen (both options)

- Editing or regenerating `SCREENING_CRITERIA.md` / `protocol.json` to remove
  names and calling the result "the same instrument".
- Rewriting `batch_*_decisions.json` to strip names — it breaks all 283 hashes
  and the signature.
- Re-signing `HumanConfirmation@1` as if the criteria had changed when only a
  publication copy was redacted.

## Verification once applied

- `sha256` of `protocol.json`, `SCREENING_CRITERIA.md` and every batch file
  unchanged from the values recorded in `HUMAN_CONFIRMATION.json`.
- `validate(HUMAN_CONFIRMATION, verify_artifacts=True)` still passes.
- The publication rendering contains none of the three names; a grep over the
  publication directory is the check.
- The rendering's header carries both instrument hashes and the confirmation
  fingerprint.

## Decision requested

Pick **A** or **B**. If **B**, confirm the role labels ("single lead reviewer",
"two co-reviewers") for the published "Screening conduct" note.
