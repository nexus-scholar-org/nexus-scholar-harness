# Provisional scoping-review protocol v0.2

## Purpose and question

How do UAV crop/weed mapping studies define and evaluate reliability under
spectral-input degradation and changes in sensor, field or acquisition time?
The scientific objective is a descriptive evidence map. The engineering objective
is an AG screening pilot; these have separate success criteria and evidence.

**Population/unit:** primary empirical crop/weed mapping studies and dataset or
benchmark reports, with report versions linked into study families and evaluation
settings charted separately. Include learning and non-learning mapping methods;
method family is a charting variable, not an unstated eligibility restriction.
**Concept:** reliability/generalization evaluation, including negative and absent
evidence; it is not necessary for every paper to use that terminology.
**Context:** UAV imagery in agricultural field settings, including orchards.
Detection, segmentation and spatial weed mapping are eligible; multispectral
input is charted rather than mandatory, allowing RGB comparison studies.

## Research questions

1. How are spectral degradation, sensor differences and temporal shift evaluated?
2. Which datasets, sensors, dates, fields and split units support generalization claims?
3. How are uncertainty, calibration and failed transfer reported?
4. What gaps remain after distinguishing data diversity, model mechanism and tested external validation?

## Provisional boundaries and assumptions

- Publication window: 2020 through the actual final search date in 2026. No
  search date is claimed yet. Recompile before execution if the window changes.
  Earlier foundational sources are background unless eligibility is amended.
  This recent-window scope answers current practice, not the historical origin
  of UAV mapping; verify recall/overlap and reconsider the boundary during calibration.
- English full text is the initial operational language assumption; language
  coverage and its bias require researcher confirmation before freeze.
- Journal, conference, and substantive preprint reports are eligible and tagged.
  Prefer the most complete current report while retaining linked versions and
  discrepant claims; do not double-count preprint/publication versions as studies.
- Open access is not an eligibility criterion. Unavailable full text is an
  unresolved retrieval state, not scientific evidence of ineligibility.
- Do not require sensor adaptation, temporal testing, uncertainty calibration,
  and spectral corruption experiments simultaneously. Their absence is data.
- Weak random-tile evaluation is charted, not automatically excluded. No generic
  risk-of-bias or trust score cutoff substitutes for protocol-specific appraisal.
- The compiler's pool range (0–1000) is a planning parameter, not a stopping
  rule or permission to truncate retrieval. Six weeks is a provisional estimate,
  not an agreed deadline. No automated pipeline is launched from these defaults.

## Selection, charting and synthesis

Use title/abstract screening then full-text eligibility with criterion-specific
reasons. Missing or ambiguous information advances to full-text/pending review;
it never becomes an inferred exclusion. Link decisions to the exact source and
protocol version. Resolve duplicate reports before counting distinct studies.
Before formal screening, record two independent human reviewers and their
adjudication procedure, or explicitly amend the protocol to a single-reviewer
procedure with its limitation. No second reviewer is claimed assigned today.
A model acting twice is not two human reviewers. Missing acquisition/evaluation
details are charted; missing full text remains pending retrieval. Exclude
abstract-only publication only after verifying that no substantive report exists.

The 13 dimensions in protocol.json produce preliminary narrative notes. Use
[CHARTING_CODEBOOK.md](CHARTING_CODEBOOK.md) and [charting.schema.json](charting.schema.json)
for reviewable study/evaluation rows. Required cells permit explicit unknown
states. Each substantive value needs a source locator and quotation, and a
derivation note when interpretation is required. Structural validation alone
does not establish source acceptance, quote matching, or entailment. Distinguish not
reported, unavailable, conflicting, not applicable and measured zero.
Record field/date/sensor independence, target-domain data use, direct versus
adapted transfer, clean versus stressed performance, class-level metrics, and
calibration separately. Multiple dates do not prove held-out temporal transfer;
learned reliability weights do not prove calibrated predictive uncertainty.

Produce descriptive tables and narrative comparisons; no pooled effect estimate
or cross-dataset leaderboard is planned. Preserve negative results. Dataset papers
may enable an experiment without demonstrating that experiment. Retraction,
correction, funding, code/data and licensing checks are recorded transparently;
an automatic trust score does not establish methodological quality.

## Reporting and amendments

Use [PRISMA-ScR](https://www.prisma-statement.org/scoping) as reporting guidance,
not a quality certificate or a completed registration. The protocol is not
preregistered. Log amendments with reason, old/new fingerprints, date and actor;
re-screen affected records if eligibility changes. Freeze only after the
researcher reviews assumptions and calibration outcomes.

The AvaRel-Fuse draft is motivation. Its bounded robustness claim and reported
transfer failure do not establish the review's novelty or determine exclusions.
Check overlapping reviews and competing evidence before making gap claims.
