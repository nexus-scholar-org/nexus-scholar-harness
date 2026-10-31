# INC-03 — co-reviewer consent and Option C conduct (recorded 2026-10-31)

**Record type: researcher attestation.** This is not an independently verified
consent record. The consent emails and any verification working papers are
retained by the researcher and are deliberately **not** copied into this
repository (they contain personal data). What follows is what the named
researcher attests, dated, with its limits stated.

## Consent

| Field | Recorded value |
| :--- | :--- |
| Who | **Soumia Zertal** and **Fadhila Djenba** |
| Date | **2026-10-31** (both) |
| Channel | Email; the messages are retained by Mouadh BEKHOUCHE |
| Scope | Named as **co-reviewers, with their role**, in the published protocol text |
| Not included in the scope | Email addresses and affiliations are **not** published |
| Covers | The frozen protocol text and any public rendering of it |
| Does **not** cover | Publishing the derived `batch_*_json` artifacts or the audit journal, which also contain the names |
| Withdrawal | Consent can be withdrawn at any time; withdrawal re-blocks publication of the names and changes nothing about the screening |

## Option C conduct (asserted, not machine-verified)

Mouadh BEKHOUCHE attests, on 2026-10-31, that the review described in INC-03 was
**executed**, not merely designed: the independent ~10% random sample and the
boundary-exclude verification were performed by the two named co-reviewers.

**Limits of this record.** No sampling frame, checklist, or per-record
verification file is stored in this workspace, and the exact sample size and
review dates were not supplied. The conduct claim is therefore recorded as
*attested by the lead researcher*, not as independently verified. This matters
because INC-03 is published as frozen: a reader is entitled to know that the
evidence for the conduct sentence is the researcher's attestation, not an
artifact in the repository.

## Effect on the publication block

- The publication/export block on the frozen protocol text is **lifted**
  (Option A of `proposals/INC-03_redaction_amendment.md`).
- **No frozen byte changed.** `protocol.json` `sha256:f81e6c58…f755` and the
  rendered criteria `9ae1f97d…b86f` are untouched; the 283 decision artifacts
  and their hashes are untouched; the confirmation fingerprint
  `e1f51ffe…f876800` is unchanged.
- INC-03 still mixes screening administration into an eligibility criterion.
  That remains a recorded **quality** limitation, not a publication blocker.

## What this record does not establish

- It does not make the review "independent third-party review" of the whole
  corpus. The signer of `HumanConfirmation@1` is the lead researcher; the
  co-reviewer sample is a separate process claim.
- It does not verify the eligibility decisions themselves beyond the signed
  confirmation.
- It does not authorize publishing the internal derived artifacts that embed
  the names; that needs separate consent or a redacted publication set.

## Verification

- `sha256(protocol.json)`, `sha256(SCREENING_CRITERIA.md)` and every
  `batch_*_decisions.json` hash still match the values bound in
  `literature/screening/HUMAN_CONFIRMATION.json`.
- `validate(HUMAN_CONFIRMATION, verify_artifacts=True)` passes.
- `export_gate(workspace)` passes.
