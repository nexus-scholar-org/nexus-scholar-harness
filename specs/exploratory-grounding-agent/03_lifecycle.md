# 03 — Reconnaissance & Grounding Lifecycle

> The 5-step loop that converts curiosity into grounded research directions. Everything below happens **before** any `workspaces/` scaffold exists.

## Step 1 — Intent Clarification (Human-in-the-loop, LLM)

**Goal:** Narrow fuzzy curiosity into probe-able axes. **Not** screening criteria yet.

- Ask: *roughly what context* (domain), *what boundary* (e.g., edge vs cloud), *what outcome* (e.g., yield detection vs process analysis).
- Produce an ordered list of **semantic probe queries** (natural-language, NOT finalized boolean strings).
- Record the conversation format so that the same session can be re-played for auditability.

**Exit gate:** the researcher has selected one primary probe axis (or explicitly bracketed the uncertainty).

## Step 2 — Empirical Surface Scan (Sandbox, Deterministic + Search-computed)

**Goal:** discover the *actual* corpus shape under the probe.

- Fire the probe queries via `SearchEngine.search_all(Query(text=..., max_results=..., year_min=...))` against an OpenAlex-first provider order.
- Dedup via `scholar_search.dedup.Deduplicator` (PID clustering + title similarity).
- **Cap** the working pool: **10-25 candidate abstracts** kept; optionally fetch **2-3 Open Access full texts** for the top-ranked items.
- Each document retains full provenance: provider, ID/DOI, title, abstract, year, citations, OA URL.
- Token budget discipline: do not exceed ~15k tokens of pool content per probe so downstream distillation stays cheap and fast.

## Step 3 — Micro-Extraction / Distillation (harness distiller over the pool)

**Goal:** extract the *prevailing demonstrated vocabulary* — the terms researchers actually use.

- **Micro-taxonomy**: dominate terms & their frequencies (pure-Python term-frequency distiller provides the baseline — no external ML deps).
- **Metrics**: mAP@0.5, IoU, F1, Exact Match, BLEU/CodeBLEU, pass@k (must be observed in the pool before being offered).
- **Datasets**: PlantVillage, RoCoLe, MBPP, HumanEval, SWE-bench, etc. (again: observed in the pool).
- **Sub-schools**: distinct research threads revealed by clustering similar abstracts / shared citations.
- Output is a JSON structure (`recon_terms_<session>.json`) where every term carries `anchor_docs: [doi, ...]`.

**Exit gate:** the distiller produced at least one terms file **with anchor-doc evidence** per probe. No evidence → term dropped.

## Step 4 — Grounded Direction Proposal (LLM + human validation)

**Goal:** 2-3 candidate research directions with citations, so the researcher can react to something real.

- Compose directions from (a) observed metrics/datasets + (b) observed gaps (thin sub-clusters, ≤2 papers).
- Every direction is anchored: each claim inside a direction references pool documents by DOI/ID.
- Present trade-offs (*"Direction A: YOLO-on-UAV-edge is crowded (coverage ~30 papers); Direction B: multispectral early-stage disease at field scale is thin (~3 papers)"*).
- The researcher validates one direction (or asks for a delta probe to vary a free parameter).

## Step 5 — Refinement & High-Fidelity Intent (grounded, validated)

**Goal:** produce a `protocol.json` whose vocabulary was validated against the literature, not guessed.

- **Delta probe** on the validated direction: fire a targeted follow-up query against cached hits to settle ambiguity (e.g., "instead of visible-light only, multispectral-band coverage").
- Consolidate validated terms into the final `IntentPacket` fields: concepts, synonyms, exclusions, gold-standard proof proxy.
- Emit through `scholar-protocol-kit` → `protocol.json` + `SCREENING_CRITERIA.md` (deterministic).
- `workspace-manager` scaffolds `workspaces/<slug>/` and writes the `GENESIS` event including a **provenance hash of the recon session** (cache keys used, pool size, anchor DOIs).

## Traceability invariant

Every term that survives into the final protocol must be traceable to a real `Document` retrieved in Steps 2-4. The mapping is kept in `recon_terms_<session>.json` and summarized in the GENESIS audit event. If a chosen synonym has no anchor, recon re-runs a targeted probe for it before emission — *the flag `--resume` for caching across wizard runs is a planned extension, not part of the first milestone.*