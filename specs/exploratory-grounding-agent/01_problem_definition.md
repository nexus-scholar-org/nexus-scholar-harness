# 01 — Problem Definition

## 1. The cold-inception gap

The Socratic inception wizard (`scholar_harness.inception`, `docs/phase_0/04_socratic_inception_protocol.md`) is deterministic and rigorous **once the researcher can answer its questions well**. Its inputs are:

- *What is your unit of analysis?*
- *What is your gold-standard proof?*
- *What are your search concepts and synonyms?*
- *What is strictly out of scope?*

For a researcher with a **messy, vague, or nascent curiosity**, these questions are unanswerable at first contact:

> *"I want to explore how drones and AI detect crop diseases."*

Three compounding failures:

### 1.1 The unknown-unknown problem
The user cannot supply accurate synonyms (`early foliar disease detection`, `low-altitude unmanned aerial vehicles`), baseline datasets (`PlantVillage`, `RoCoLe`, `Sugar Beet Dataset`), or gold-standard metrics (`mAP@0.5`, `FPS`, `F1`) because they have not yet surveyed the landscape. Asking for these at t=0 yields textbook guesses that may not match the literature at all.

### 1.2 Parametric hallucination risk
A language-model-only answer draws on training-time knowledge: names of benchmark datasets and model families can be outdated, invented, or renamed. A search-computed answer has a live, verifiable citation chain behind every term it proposes.

### 1.3 Premature protocol freezing
`protocol.json` is the **universal downstream contract** (search, screening, PDF harvest, extraction, synthesis all consume it). Freezing it before confirming the literature exists under the frozen terms has two failure modes downstream:
- **Zero-hit risk**: an execution query nobody published against → empty Phase-1 corpus.
- **Drift risk**: generic terms pull thousands of irrelevant papers → wasted screening effort.

## 2. Requirement statement

> Design an autonomous reconnaissance component that, given raw researcher curiosity, returns **grounded, citation-backed research directions and a vocabulary** that a *researcher then validates*, and that feeds the validated vocabulary into the existing deterministic inception → protocol pipeline.

## 3. Non-goals (explicit exclusions)

- **Not** a full systematic review: it samples a micro-corpus; it does not PRISMA-screen thousands of papers.
- **Not** a synthesis engine: it does not answer the RQ; it defines which RQs are answerable and under what vocabulary.
- **Not** a replacement for the Socratic interview: it *pre-groups* and *pre-distills*, it does not re-draw the paradigm refraction grid.
- **Not** a workspace creator: it must never write into `workspaces/`.

## 4. Guarantees the design must preserve

1. **Zero workspace pollution**: all scratch state lives under `workspaces`-excluded path (`.cache/inception_recon/`).
2. **Deterministic downstream emission**: whatever the recon agent returns still flows through `IntentPacket` → `compile_protocol` → `protocol.json` (the existing deterministic compiler).
3. **Cite-ability**: every term or direction offered to the researcher must trace to a real retrieved `Document` (DOI/ID).
4. **Human-in-the-loop**: the researcher approves the final intent before anything is written to `workspaces/`.

## 5. Acceptance posture

The feature is acceptable only if both of the following hold at once:
- A researcher with a vague prompt can reach a *specific, literature-validated* set of 2-3 directions without answering screening-criteria questions first.
- Every element of the final `IntentPacket` (concepts, synonyms, exclusions, proof) is traceable to a retrieved document, not only to model priors.