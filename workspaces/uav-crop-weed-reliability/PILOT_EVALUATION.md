# AG pilot evaluation plan â€” provisional

## Two evaluations

1. Software: synthetic fixtures test assignment coverage, duplicates, unresolved
   states, exact bytes, approval bypass, revision, audit and publication failures.
2. Science/workflow: real records test eligibility reasoning, source anchors,
   missed eligible studies, abstention, corrections and time including verification.

Prepare 30â€“50 deliberately varied development records including clear inclusion,
clear exclusion and boundary cases. Human reviewers decide independently before
seeing model outputs; record the actual reviewer arrangement and adjudication.
Use this set to improve criteria/skill, not to estimate production performance.

Freeze a separate held-out evaluation set and its human reference labels after
calibration. Choose its size and acceptable error/cost thresholds before inspecting
agent performance. Measure false exclusions, unsupported reasons, quotation
accuracy, uncertainty, overrides, total review time and suggestion bias. Report
denominators and uncertainty. Two agents agreeing is not independent validation.

Do not pool scientific evaluation with software pass counts. Do not claim
efficiency from gross generation speed or reliability from agreement alone.
Researcher review can be procedural while AG-03 is unproven; label it honestly.
No automatic exclusions, trained models or crop experiments are part of this init.

Proceed/revise/stop thresholds, second reviewer, access coverage and held-out
sample design remain open and must be recorded before an evaluation run.

## Operational design required before evaluation

Record reviewer identities, independence/blinding and adjudication; no reviewers
are assigned by this draft. Reference labels precede model exposure. A disagreement
is retained until adjudicated, not counted as model error against an arbitrary label.
Development records may be enriched for boundary cases; label that sampling explicitly.
Held-out performance uses a separately frozen sampling rule and reports eligible/
ineligible/uncertain denominators, rather than borrowing development prevalence.

Define false exclusion against adjudicated eligible records and report abstentions
separately. Count an incorrect criterion or unsupported evidence anchor separately
from a correct final label. Time includes source checking, corrections and resolution.
For assistance effects, use separate or counterbalanced record allocations to avoid
memory from repeated screening; preserve reviewer assignments and order. Predefine
proceed/revise/stop thresholds and sample-size rationale before observing results.
No thresholds or powered reliability claim are invented in this revision.
