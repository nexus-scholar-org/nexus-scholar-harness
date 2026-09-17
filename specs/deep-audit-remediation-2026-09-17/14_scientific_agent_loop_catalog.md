# Proposed Scientific Agent Loop Catalog

**Version:** 0.1.0-proposal  
**Status:** Design backlog — none are executable merely because they are listed  
**Companion:** `13_scientific_agent_loop_framework.md`

> **Registry note (2026-09-17 remediation):** the `SCI-LOOP-*` / `LOOP-*`
> identifiers and the `loops/<loop-id>/<run-id>/` artifact tree used here are
> proposals. They are not yet part of the canonical identifier or artifact
> registries in `10_cross_kit_contracts.md` (XC-001, XC-006) and become normative
> only after that registry is extended. See `13_scientific_agent_loop_framework.md`
> §15 registry note.

## 1. Catalog overview

The following proposals compose Nexus Scholar capabilities around scientific
tasks rather than package boundaries. Each loop is bounded, artifact-driven, and
explicit about human authority and permitted claims.

| ID | Scientific task | Principal kit composition | Human gate |
|---|---|---|---|
| SCI-LOOP-01 | Grounded topic inception | agent + search + harness recon + protocol | Select direction |
| SCI-LOOP-02 | Epistemology/method alignment | methodology role + protocol | Approve paradigm |
| SCI-LOOP-03 | Protocol hostile review | protocol + critic | Freeze/amend protocol |
| SCI-LOOP-04 | RQ and extraction-matrix co-design | protocol + search probes | Approve RQs/dimensions |
| SCI-LOOP-05 | Golden-seed query calibration | protocol + search | Accept recall strategy |
| SCI-LOOP-06 | Federated discovery resilience | search + audit | Accept degraded search |
| SCI-LOOP-07 | Adaptive terminology/gap probing | recon + search | Select bounded expansion |
| SCI-LOOP-08 | Citation snowball frontier | search + graph | Stop/continue frontier |
| SCI-LOOP-09 | Metadata fusion and dedup adjudication | search + bib | Resolve ambiguous clusters |
| SCI-LOOP-10 | Screening calibration pilot | protocol + search screening | Approve rubric/readiness |
| SCI-LOOP-11 | Dual-screening reconciliation | search screening + harness | Adjudicate conflicts |
| SCI-LOOP-12 | Full-text retrieval coverage rescue | pdf + search metadata | Accept unresolved roster |
| SCI-LOOP-13 | Extraction quality control | pdf + RAG chunk preview | Accept/re-extract/exclude |
| SCI-LOOP-14 | Protocol-driven evidence matrix | protocol + RAG | Review missing/ambiguous cells |
| SCI-LOOP-15 | Citation-network structural analysis | graph + search | Approve interpretation |
| SCI-LOOP-16 | RQ-grounded synthesis | RAG + graph + protocol | Approve claim set |
| SCI-LOOP-17 | Contradiction and debate cartography | RAG consensus + critic | Confirm stance/debate |
| SCI-LOOP-18 | Claim-evidence verification | RAG + verify | Accept/revise/drop claims |
| SCI-LOOP-19 | Methodological risk critique | verify + protocol matrix | Approve domain ratings |
| SCI-LOOP-20 | Open-science and reproducibility audit | verify + PDF/RAG | Resolve ambiguous statements |
| SCI-LOOP-21 | Trust-weighted consensus | verify + RAG consensus | Approve interpretation |
| SCI-LOOP-22 | Manuscript claim ledger | RAG + verify + bib | Approve paper-facing claims |
| SCI-LOOP-23 | Living-review update | all phase owners | Approve corpus/version update |
| SCI-LOOP-24 | Retraction/correction response | verify + RAG lineage | Approve revised conclusions |
| SCI-LOOP-25 | Evidence gap to experiment protocol | search + RAG + protocol | Approve proposed experiment |
| SCI-LOOP-26 | Replication prioritization | verify + graph + RAG | Select studies to replicate |

## 2. Inception and protocol loops

### SCI-LOOP-01 — Grounded topic inception

**Objective:** Convert an exploratory topic into a literature-anchored direction
without prematurely asserting novelty.

**Composition:** `recon_probe` → `recon_distill` → bounded `recon_delta`;
scholar-search provides papers, harness recon provides persistent sessions, and
protocol-kit receives only the selected direction.

**Inputs:** topic statement, researcher constraints, optional seed DOI/terms.

**Artifacts:** recon session, source pool, term taxonomy, three direction cards,
gap/saturation assessment, decision packet, selected direction.

**Loop:** probe → distill → critic checks anchors/diversity → at most three gap
probes → rank directions by evidence density, feasibility, and distinction.

**Stop:** sufficient anchored directions; three delta probes; or marginal new-term
gain below threshold. Lack of a clear gap terminates `INCONCLUSIVE`, not “novel.”

**Human gate:** researcher selects/rejects a direction and records rationale.

**Allowed claim:** “The probe identified these literature-anchored directions.”
**Forbidden claim:** “No prior work exists” or “the direction is novel.”

### SCI-LOOP-02 — Epistemology and method alignment

**Objective:** Align research questions, unit of analysis, evidence type, and
evaluation logic with an explicit epistemological stance.

**Composition:** methodology-copilot role + protocol-kit intent models and
playbook presets; optional search probes only to test terminology.

**Inputs:** selected direction, intended contribution, constraints, candidate RQs.

**Artifacts:** paradigm decision, rationale, rejected alternatives, rigor criteria,
revised RQs, method-risk register.

**Loop:** elicit assumptions → propose 2–3 paradigms → adversarial comparison →
revise questions/evidence requirements once → human choice.

**Stop:** coherent mapping or unresolved methodological conflict.

**Human gate:** lead researcher approves paradigm and acceptable rigor criteria.

**Allowed claim:** “The protocol adopts X because…”  
**Forbidden claim:** “X is objectively the best methodology.”

### SCI-LOOP-03 — Protocol hostile-reviewer loop

**Objective:** Prevent a structurally valid but scientifically incoherent protocol
from becoming the frozen control plane.

**Composition:** protocol compile/validate/fingerprint/render plus a critic that
checks RQ references, selection bias, construct coverage, leakage, feasibility,
and post-hoc flexibility.

**Inputs:** intent packet and any pilot evidence explicitly labeled exploratory.

**Artifacts:** compiled candidate, validation report, hostile-review report,
amendments, final fingerprint or unresolved issues.

**Loop:** compile → full structural/cross-field validation → critic rubric → one
revision cycle → repeat validation.

**Stop:** zero blocking findings; two revision rounds; or researcher chooses to
accept a documented limitation.

**Human gate:** protocol freeze or amendment approval.

**Allowed claim:** “The frozen protocol passed the stated checks.”  
**Forbidden claim:** “The protocol eliminates all bias.”

### SCI-LOOP-04 — Research-question and extraction-matrix co-design

**Objective:** Ensure each RQ can be answered by explicit extractable evidence and
that each matrix dimension maps to at least one RQ.

**Composition:** protocol-kit models/extraction schema + small search sample + RAG
only for preview extraction, never final results.

**Inputs:** candidate RQs, concept clusters, pilot sample, evidence-type rules.

**Artifacts:** RQ-to-dimension map, typed extraction schema, pilot missingness
report, revised definitions and controlled vocabularies.

**Loop:** build schema → extract from 3–5 pilot papers → measure ambiguity and
missingness → revise dimension wording/type once → validate.

**Stop:** dimensions are interpretable and answerable, or evidence availability is
too weak and the RQ returns for redesign.

**Human gate:** approve RQ/dimension semantics before protocol freeze.

**Allowed claim:** “The pilot suggests these fields are extractable.”  
**Forbidden claim:** pilot-derived substantive review conclusions.

## 3. Discovery and corpus-construction loops

### SCI-LOOP-05 — Golden-seed query calibration

**Objective:** Test whether a protocol query recovers known landmark studies while
preserving a documented candidate-pool scope.

**Composition:** protocol golden seeds + search query compilation,
`validate-query`, provider translators, and structured provider outcomes.

**Inputs:** frozen concepts/date/language bounds, 2–5 justified seed identifiers.

**Artifacts:** provider-specific queries, seed recall table, failed-provider table,
query revisions, final calibration decision.

**Loop:** compile → run bounded search → inspect missed seeds → revise synonyms or
syntax, never criteria → maximum three revisions.

**Stop:** threshold met; no improvement; or provider limitation documented.

**Human gate:** approve search strategy and any provider-specific exception.

**Allowed claim:** “The query recovered N/M predefined seeds under this setup.”  
**Forbidden claim:** “The search has complete recall.”

### SCI-LOOP-06 — Federated discovery resilience loop

**Objective:** Produce a candidate corpus while distinguishing genuine empty
results from provider outages and partial coverage.

**Composition:** search engine/providers + structured retry/outcome service +
harness audit.

**Inputs:** frozen protocol query, provider roster, retry/time budget.

**Artifacts:** per-provider outcome, raw provider records, merged corpus,
missing-provider impact assessment.

**Loop:** parallel bounded provider calls → retry retryable failures → normalize →
critic checks unexpected zeros/distribution → optionally rerun failed providers
once.

**Stop:** all providers terminal; retry budget exhausted; or human accepts a
degraded corpus.

**Human gate:** required if a protocol-mandated provider remains unavailable.

**Allowed claim:** provider-specific counts and explicit partial status.  
**Forbidden claim:** interpreting outage-driven zero as absence of literature.

### SCI-LOOP-07 — Adaptive terminology and gap probing

**Objective:** Detect underrepresented terminology or schools without mutating the
frozen eligibility criteria.

**Composition:** recon distillation + search probes + dedup + protocol amendment
mechanism when material changes are proposed.

**Inputs:** initial corpus, term taxonomy, frozen protocol.

**Artifacts:** terminology gaps, bounded follow-up queries, incremental unique
studies, amendment recommendation.

**Loop:** identify thin taxonomy branch → one bounded probe per branch → merge and
dedup → calculate eligible incremental yield → critic checks topic drift.

**Stop:** three rounds, no eligible gain, or purity falls below threshold.

**Human gate:** any material search-strategy amendment creates a new protocol/run.

**Allowed claim:** “These follow-ups added X eligible records.”  
**Forbidden claim:** post-hoc criteria change without amendment provenance.

### SCI-LOOP-08 — Citation snowball frontier

**Objective:** Expand a screened seed corpus through bounded forward/backward
citation traversal and assess saturation.

**Composition:** search snowball/chain + graph + dedup + screening preparation.

**Inputs:** included seed IDs, depth/node/document limits, direction policy.

**Artifacts:** frontier graph, newly discovered records by hop/direction, dedup
aliases, screening batches, marginal-yield curve.

**Loop:** expand one hop → dedup → screen new candidates → measure new inclusion
yield → continue within hard depth/size bounds.

**Stop:** configured depth, frontier cap, two rounds without new inclusion, or
provider capability failure.

**Human gate:** approve expansion beyond preregistered bounds.

**Allowed claim:** “Snowballing reached saturation under the declared bounds.”  
**Forbidden claim:** universal citation-network saturation.

### SCI-LOOP-09 — Metadata fusion and dedup adjudication

**Objective:** Construct a canonical study roster without merging distinct works
or retaining identifier-bridged duplicates.

**Composition:** search dedup + bib parsing/resolution + deterministic identity
components + human adjudication for ambiguous clusters.

**Inputs:** normalized provider records and optional bibliography.

**Artifacts:** connected components, elected representatives, alias/lineage map,
ambiguous-pair queue, adjudications.

**Loop:** normalize identifiers → union exact identities → fuzzy candidate
generation → conservative merge rules → critic inspects low-margin decisions →
human adjudicates ambiguity.

**Stop:** no unresolved high-risk cluster or adjudication deferred explicitly.

**Human gate:** merge/split ambiguous records that affect study counts.

**Allowed claim:** transparent unique-record count with merge rules.  
**Forbidden claim:** treating fuzzy title similarity alone as proven identity.

## 4. Screening and full-text loops

### SCI-LOOP-10 — Screening calibration pilot

**Objective:** Establish whether criteria and reviewer instructions yield adequate
agreement before full screening.

**Composition:** protocol criteria renderer + search screening batcher + human/LLM
reviewers + calibration metrics.

**Inputs:** frozen protocol, stratified pilot batch including difficult cases.

**Artifacts:** independent decisions, reason-category confusion matrix, agreement
metrics, rubric ambiguities, revision/amendment decision.

**Loop:** independent pilot → reconcile only after decisions freeze → analyze
disagreements → revise instructions once if permitted → second pilot.

**Stop:** preregistered agreement threshold; two pilots; or protocol ambiguity
requires amendment.

**Human gate:** approve readiness and any criteria/instruction amendment.

**Allowed claim:** “Pilot agreement was X under this rubric.”  
**Forbidden claim:** using agreement alone as validity proof.

### SCI-LOOP-11 — Dual-screening reconciliation

**Objective:** Reconcile independent eligibility decisions while preserving each
screener's judgment and adjudication lineage.

**Composition:** harness batch handoff + search reconciliation + human adjudicator.

**Inputs:** fingerprint-matched batches and two independent decision sets.

**Artifacts:** agreement statistics, conflict roster, adjudication decisions,
included/excluded/conflict files, PRISMA counts.

**Loop:** validate coverage → compute agreement → auto-accept exact agreements →
prepare conflict packets → adjudicate → regenerate corpus atomically.

**Stop:** every study has a valid terminal decision; otherwise remain
`WAITING_FOR_DECISION`.

**Human gate:** every conflict unless protocol explicitly defines a deterministic
rule.

**Allowed claim:** observed agreement and reconciled counts.  
**Forbidden claim:** silently replacing missing decisions with heuristics.

### SCI-LOOP-12 — Full-text retrieval coverage rescue

**Objective:** Maximize legal full-text coverage without mislabeling unresolved
access as confirmed paywall status.

**Composition:** PDF OA resolution/download + search metadata/identifiers + manual
ingest option.

**Inputs:** included study roster, legal OA sources, optional institutional gateway
configuration.

**Artifacts:** per-study resolution attempts, valid PDFs, unresolved reasons,
manual-retrieval queue, coverage report.

**Loop:** canonical DOI/ID resolution → OA cascade → validated download → one
metadata repair retry → optional manual ingest → final unresolved state.

**Stop:** every study terminal or retrieval budget/date reached.

**Human gate:** manual source selection and licensing/access decisions.

**Allowed claim:** “No legal OA full text was resolved by configured sources.”  
**Forbidden claim:** “Paywalled” without affirmative evidence.

### SCI-LOOP-13 — Extraction quality-control loop

**Objective:** Ensure only usable, identity-preserving full text enters indexing.

**Composition:** PDF extraction engines + structural/content checks + RAG chunk
preview + human spot check.

**Inputs:** validated PDFs, canonical study/document metadata.

**Artifacts:** extraction outputs, engine/fallback provenance, content-quality
metrics, sampled render/text comparison, exclusion/retry queue.

**Loop:** primary extraction → schema/frontmatter validation → content checks →
chunk preview → fallback engine only with explicit partial provenance → sample
human review.

**Stop:** accepted extraction, explicit abstract-only state, or failed/unextractable.

**Human gate:** low-content, OCR-heavy, table-critical, or conflicting extraction.

**Allowed claim:** extraction coverage by status/engine.  
**Forbidden claim:** counting stub or abstract-only artifacts as full text.

## 5. Evidence analysis and synthesis loops

### SCI-LOOP-14 — Protocol-driven evidence matrix

**Objective:** Populate typed RQ-linked study fields with source-level provenance
and explicit missingness.

**Composition:** protocol extraction model + RAG scoped retrieval/extraction +
critic validation.

**Inputs:** frozen protocol, accepted extractions, canonical study roster.

**Artifacts:** one row per `study_id`, typed cells, evidence locators/quotes,
confidence/method, missing/ambiguous queue.

**Loop:** retrieve within one study → extract dimensions → validate types and
quotes → critic checks cross-study contamination → retry ambiguous cells once.

**Stop:** every cell populated, `NOT_REPORTED`, `NOT_APPLICABLE`, or unresolved.

**Human gate:** ambiguous high-impact cells and derived/computed interpretations.

**Allowed claim:** matrix values with cited provenance.  
**Forbidden claim:** invented domain defaults for missing cells.

### SCI-LOOP-15 — Citation-network structural analysis

**Objective:** Describe the internal citation structure of the selected corpus and
identify hubs, bridges, and communities without treating centrality as quality.

**Composition:** graph builder + PageRank/HITS/betweenness/community operations +
search metadata.

**Inputs:** canonical included corpus with normalized DOI/OpenAlex identities.

**Artifacts:** citation graph, fetch diagnostics, metrics, clusters, isolated-node
roster, narrative draft.

**Loop:** build graph → validate node/edge coverage → calculate declared metrics →
critic checks metadata retention and overinterpretation → optional sensitivity run
across community resolution.

**Stop:** valid graph/metrics or insufficient resolvable edges.

**Human gate:** approve thematic labels and substantive interpretation.

**Allowed claim:** “Within this corpus, paper X has higher centrality.”  
**Forbidden claim:** “X is higher quality” or field-wide influence without scope.

### SCI-LOOP-16 — RQ-grounded retrieval and synthesis

**Objective:** Produce a claim set answering one RQ with atomic study/evidence
attribution.

**Composition:** RAG retrieval with optional graph boost + synthesis + protocol RQ
scope + critic.

**Inputs:** one RQ, indexed accepted extractions, graph optional, retrieval policy.

**Artifacts:** retrieval set, candidate claims, evidence tokens/quotes, semantic
support scores, unresolved gaps, synthesis draft.

**Loop:** retrieve → draft atomic claims → attach evidence → critic checks scope,
negation, quantities, and study identity → revise once or drop claim.

**Stop:** all retained claims have valid evidence or RQ remains incompletely
answered and is labeled so.

**Human gate:** approve scientific interpretation and claim wording.

**Allowed claim:** evidence-bounded synthesis for the specified RQ.  
**Forbidden claim:** unqualified “verified” based on embedding similarity.

### SCI-LOOP-17 — Contradiction and debate cartography

**Objective:** Identify supported agreement, contradiction, conditional effects,
and unresolved differences across studies.

**Composition:** RAG claim ledger + consensus cartographer + matrix moderators +
human/critic stance validation.

**Inputs:** atomic claims with study IDs and evidence, optional moderator fields.

**Artifacts:** semantic claim clusters, stance assignments, contested clusters,
moderator hypotheses, sensitivity results across clustering thresholds.

**Loop:** filter nonclaims → semantic cluster → classify stance → critic reviews
negation/comparator context → threshold sensitivity → human confirms key debates.

**Stop:** stable interpretable clusters or output remains an unclustered claim
ledger.

**Human gate:** stance correction and labeling of high-impact debate clusters.

**Allowed claim:** “These studies report differing findings under these contexts.”  
**Forbidden claim:** majority count as proof of truth.

### SCI-LOOP-18 — Claim-evidence verification

**Objective:** Evaluate separate dimensions of a manuscript or synthesis claim:
source identity, verbatim support, semantic support, entailment, and trust context.

**Composition:** RAG claim/evidence ledger + verify verbatim matching + optional
NLI/critic + Phase-4 context.

**Inputs:** claims with evidence locators and accepted source hashes.

**Artifacts:** per-claim multi-axis verdict, failure reasons, revision suggestions,
aggregate coverage that retains item-level results.

**Loop:** resolve source → verify quote → assess semantic support → assess
entailment using approved method/human → attach trust context → revise/drop.

**Stop:** each claim accepted, revised, dropped, or unresolved.

**Human gate:** all causal, novelty, safety, numerical, and contradictory claims.

**Allowed claim:** axis-qualified verdicts.  
**Forbidden claim:** collapsing all axes to generic `VERIFIED`.

### SCI-LOOP-19 — Methodological risk critique

**Objective:** Apply an explicit domain-appropriate risk rubric consistently and
expose uncertainty rather than manufacture precise quality scores.

**Composition:** protocol methodology fields + verify risk-of-bias + extracted
evidence + critic/human review.

**Inputs:** accepted study roster, extraction matrix, chosen framework/profile.

**Artifacts:** per-domain judgments, evidence/rationale, missing-information
flags, disagreements, overall rule result.

**Loop:** deterministic prefill → critic checks evidence/rubric fit → human reviews
uncertain/high-impact domains → recompute overall outcome.

**Stop:** complete roster with explicit unknowns; never fill unknown from absence.

**Human gate:** domain ratings requiring interpretation and framework adaptation.

**Allowed claim:** rubric-specific risk judgments.  
**Forbidden claim:** universal study-quality score.

### SCI-LOOP-20 — Open-science and reproducibility audit

**Objective:** Determine what data/code/material availability is explicitly
reported and whether linked artifacts are resolvable.

**Composition:** verify DAS/CAS classifier + extracted sections + optional safe link
metadata check + critic for negation/proximity.

**Inputs:** accepted extraction, source hash, host whitelist/policy.

**Artifacts:** typed statements, local evidence spans, associated links, resolution
status, ambiguities.

**Loop:** find statements → classify with negation precedence → associate nearby
typed links → optionally check link availability → critic reviews ambiguous cases.

**Stop:** each study has explicit label plus evidence or `NOT_STATED`.

**Human gate:** ambiguous or conflicting availability statements.

**Allowed claim:** reported availability status at audit time.  
**Forbidden claim:** reproducibility proven solely by presence of a link.

### SCI-LOOP-21 — Trust-weighted consensus

**Objective:** Contextualize consensus clusters with retraction, risk-of-bias,
COI, and open-science evidence without discarding study-level detail.

**Composition:** RAG consensus + all verify streams + trust-context join.

**Inputs:** consensus clusters, canonical study IDs, complete/partial Phase-4
artifacts with stream coverage.

**Artifacts:** cluster trust context, per-study details, coverage by stream,
block/warning reasons, sensitivity report.

**Loop:** validate identity join → annotate each stream independently → apply
documented trust policy → critic checks missingness and retraction severity → human
reviews consequential downgrades.

**Stop:** every cluster has coverage accounting and a policy result or remains
`UNVERIFIED`.

**Human gate:** interpretation of mixed or domain-sensitive trust signals.

**Allowed claim:** policy-specific trust context.  
**Forbidden claim:** no flags means trustworthy.

## 6. Publication, maintenance, and research-planning loops

### SCI-LOOP-22 — Manuscript claim ledger

**Objective:** Build a paper-facing ledger where every substantive sentence maps
to supporting evidence, verification state, and approved scope.

**Composition:** RAG claims + verify axes + bib curation + manuscript section map.

**Inputs:** synthesis claims, figures/tables, bibliography, target manuscript.

**Artifacts:** claim IDs, manuscript locations, study/evidence links, citation
keys, allowed wording, status, reviewer notes.

**Loop:** parse candidate claims → link evidence/citations → verify axes → critic
checks overclaim and negative evidence → revise manuscript/ledger together.

**Stop:** every substantive claim is supported, qualified, explicitly speculative,
or removed.

**Human gate:** final paper-facing wording and novelty/contribution statements.

**Allowed claim:** exactly the ledger-approved wording.  
**Forbidden claim:** stronger prose than the stored evidence boundary.

### SCI-LOOP-23 — Living-review update

**Objective:** Update a frozen review with new literature while preserving prior
decisions and exposing what changed.

**Composition:** protocol version check + incremental search + dedup + screening +
PDF/RAG/graph/verify recomputation by dependency.

**Inputs:** prior run manifest, protocol, provider cursors/date cutoff, prior
canonical corpus.

**Artifacts:** incremental candidate set, changed metadata, new screening run,
artifact impact graph, revised synthesis/trust outputs, version diff.

**Loop:** validate prior state → incremental discovery → dedup against aliases →
screen only new/changed studies → recompute affected downstream artifacts → critic
checks conclusion drift.

**Stop:** all affected artifacts committed or update remains partial with explicit
unresolved items.

**Human gate:** protocol amendment, changed inclusion, or conclusion revision.

**Allowed claim:** changes relative to a named prior version.  
**Forbidden claim:** silently replacing the historical review.

### SCI-LOOP-24 — Retraction/correction response

**Objective:** Re-evaluate a review when a supporting study receives a retraction,
expression of concern, correction, or addendum.

**Composition:** verify retraction stream + artifact lineage + RAG claims/consensus
and manuscript ledger.

**Inputs:** publication-status event, affected study ID, current dependency graph.

**Artifacts:** affected claims/clusters/tables, severity classification, recomputed
outputs, decision packet, corrected release/version.

**Loop:** verify event → classify approved severity → traverse dependents → remove
or annotate evidence → recompute claims/consensus/trust → critic assesses whether
conclusions change.

**Stop:** all affected artifacts revised or blocked pending clarification.

**Human gate:** approve conclusion/manuscript/public notice changes.

**Allowed claim:** exact effect of the event on this review.  
**Forbidden claim:** treating every correction as a retraction or ignoring it.

### SCI-LOOP-25 — Evidence gap to experiment protocol

**Objective:** Convert a supported evidence gap into a fair, testable experiment
proposal rather than treating absence in the corpus as novelty proof.

**Composition:** RAG matrix/claims + graph/search gap check + protocol compiler +
methodology critic.

**Inputs:** gap claim, supporting corpus, limitations, available resources.

**Artifacts:** gap evidence map, alternative explanations, scoped hypothesis,
baselines/controls, dataset/evaluation plan, falsification criteria, preregistered
protocol draft.

**Loop:** state gap → targeted disconfirmation search → map nearest work → propose
experiment → hostile fairness review → revise once.

**Stop:** defensible experiment, gap disproven, or infeasible/inconclusive.

**Human gate:** approve novelty wording, resources, ethics, and final protocol.

**Allowed claim:** “The reviewed evidence motivates testing X under Y.”  
**Forbidden claim:** “X is novel” solely from bounded search absence.

### SCI-LOOP-26 — Replication prioritization

**Objective:** Rank candidate studies for replication using transparent scientific
criteria rather than citation count alone.

**Composition:** verify trust streams + graph structural context + RAG claim
importance/uncertainty + protocol feasibility fields.

**Inputs:** study roster, important claims, RoB/COI/open-science/retraction context,
resource constraints.

**Artifacts:** multi-criteria table, criterion weights, Pareto set, sensitivity
analysis, ranked recommendation with uncertainties.

**Loop:** define criteria/weights → compute transparent components → sensitivity
across reasonable weights → critic checks popularity/availability bias → human
selects target.

**Stop:** stable Pareto candidates or ranking remains weight-sensitive and is
reported as such.

**Human gate:** select replication target and approve feasibility/ethics.

**Allowed claim:** “Under these criteria and weights, these are priorities.”  
**Forbidden claim:** “Highest PageRank study is most important to replicate.”

## 7. Composition patterns reused across loops

### Pattern A — Generate, criticize, commit

Use for protocol, matrix, synthesis, and manuscript artifacts. Generation never
writes canonical output directly; critic approval precedes atomic publication.

### Pattern B — Parallel item workers, deterministic aggregator

Use for provider search, PDF retrieval, extraction, and per-study verification.
Workers emit item outcomes; aggregation sorts by canonical ID and preserves every
failure.

### Pattern C — Adaptive bounded frontier

Use for recon, query calibration, and snowballing. Each round records marginal
gain, drift, and budget; maximum rounds are hard limits.

### Pattern D — Human adjudication queue

Use for screening conflicts, ambiguous dedup, extraction ambiguity, risk ratings,
and claim wording. Automated components prepare a compact evidence packet but do
not silently resolve the queue.

### Pattern E — Dependency-triggered recomputation

Use for living reviews and retraction responses. Artifact lineage identifies the
minimal affected subgraph; unaffected artifacts remain immutable.

## 8. Suggested implementation order

1. Implement framework schema and artifact layout.
2. Pilot SCI-LOOP-03, SCI-LOOP-10, and SCI-LOOP-14 because they exercise
   protocol, human gates, and study identity without requiring every live service.
3. Implement SCI-LOOP-06 and SCI-LOOP-13 to establish structured partial/failure
   outcomes.
4. Implement SCI-LOOP-16, SCI-LOOP-18, and SCI-LOOP-21 only after canonical
   study/claim/evidence contracts are fixed.
5. Add SCI-LOOP-23/24 after run manifests and dependency lineage are stable.
6. Keep SCI-LOOP-25/26 advisory until hostile-review and human-decision studies
   demonstrate useful, non-inflated recommendations.

## 9. Catalog acceptance criteria

Before any proposal is marked `IMPLEMENTED`:

- it has a versioned executable loop spec;
- every named capability exists in the pinned tool versions;
- entry/exit schemas and human gates are tested;
- success, partial, inconclusive, failed, and revision fixtures exist;
- iteration bounds are mechanically enforced;
- its allowed/prohibited claims pass hostile-review tests;
- audit and artifact lineage satisfy the cross-kit contracts;
- the UI/CLI labels it experimental until field validation is complete.

