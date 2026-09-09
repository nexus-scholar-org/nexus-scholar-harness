# Lessons from the Corpus for Harness Development + Method-Paper Reading List

**Workspace**: `ai-research-harnesses-trust` · **Date**: 2026-09-09 · **Purpose**: (A) what the 58-study corpus teaches us about building the Nexus Scholar harness itself, and (B) which method papers to read next. All lessons are grounded in the verbatim-backed claim ledger (`synthesis/claims.json`) and the 95-cluster consensus (`synthesis/consensus.json`). Study evidence is cited as `SCI-xxxx`.

---

## Part A — Lessons for the harness

### L1. Verifiability is the binding constraint, not generation quality
Across **17,443 generated citations**, no model exceeded a citation-existence rate of **0.475**, and outputs stayed format-compliant ("compliance without substance"). LLMs under deployment constraints hallucinate citations at 78–98%; retrieval-grounded LMs reached zero hallucinated papers.
→ Our mandatory standard: **no claim leaves the pipeline without a byte-verifiable quote.** Retrieval grounding alone is not enough — the verifier must be attached to claim generation.
*Evidence: SCI-000144, SCI-000154, SCI-000159.*

### L2. Grounded retrieval works; ungrounded generation does not
OpenScholar-8B produced zero hallucinated cited papers vs baseline LLMs' **92.1% (CS) / 97.6% (Bio)**; knowledge-graph integration also reduced hallucinations. But grounding is fragile: every tested model synthesized *negated* abstracts into coherent false conclusions, and BERTScore rated the false conclusions as semantically equivalent to correct ones.
→ **Semantic-similarity metrics are not reliability proxies.** Use verbatim coverage and human-anchored agreement (Cohen's κ), not BERTScore/ROUGE, to certify synthesis.
*Evidence: SCI-000159, SCI-000082, SCI-000127.*

### L3. Corpus-scope discipline is a correctness property
This review's own RAG baseline cited **11 screened-out studies** (22 claims) because the index contained pre-scoping extractions; 43/57 included studies were invisible to it. Our method-pipeline bug, not the corpus's.
→ The harness must enforce reconciliation (`included.json`) at every downstream step — index, synthesis, retrieval. This is now upgrade target U2.

### L4. Deterministic decoding + model openness are the reproducibility levers
Temperature-0 with fixed penalties produces repeatable runs (2,880 runs → 17,443 citations); open-weights selection is done "explicitly to enhance reproducibility"; closed hosted models "cannot be guaranteed to reproduce original outputs because the underlying models and web interfaces are externally controlled."
→ Pin decoding params, prefer open-weights where possible, and record model+version per run (our JSON API logs already do).
*Evidence: SCI-000108, SCI-000144, SCI-000164, SCI-000151, SCI-000137.*

### L5. Aggregate similarity conceals item-level instability
Two nominally identical runs of the same review workflow agreed on **91.7% of records** but **disagreed on 94 individual records, including 29 verified-eligible records retained by only one run**. Temporal drift of **−1.9%/day** was measured in one system's evaluation window.
→ Publish item-level deltas, not just summary agreement; snapshot evaluation dates (avoid the drift trap); treat "reproducible in aggregate" as failing.
*Evidence: SCI-000137, SCI-000100.*

### L6. Prompt fragility is a quantified, avoidable failure mode
Subtle format variations produced accuracy swings of up to **76 points**; a "prompt compilation" workflow packages the final prompt as a verifiable digital artefact precisely to neutralize this. Cross-model behavior diverges under identical prompts.
→ **Prompt compilation + pinned prompt artefacts as checked-in files** (not inline strings), plus model pinning.
*Evidence: SCI-000106.*

### L7. Multi-agent benefit is phase-dependent
Multi-agent orchestration **hurts screening** but is **essential for extraction**, producing **5.7× more poolable analyses**. Model ranking is domain- and task-dependent (one system: 98% screening but 40% extraction; another 90% both).
→ Route by phase: cheaper models for high-volume screening gates, capable models for judgment/extraction steps; never assume a single "best" model.
*Evidence: SCI-000118, SCI-000129.*

### L8. Structured field extraction beats naive chunking
Schema-constrained extraction reached **100% recall / 97.9% precision / 98.9% F1** on a ketamine benchmark, and hybrid KG+vector retrieval beat PDF chunking by **+35.1%** semantic similarity (p < 0.000001, 643 observations). Conservative missingness handling ("NR") is used deliberately to avoid fabrication.
→ Structured extraction with explicit "not reported" semantics is a generation-quality multiplier — matches our YAML-frontmatter full-text schema.
*Evidence: SCI-000090, SCI-000100.*

### L9. Auditable provenance is achieved, not aspirational
Systems already ship append-only logs, deterministic IDs for idempotent behavior, content-hashed "commitment cards", and immutable run bundles. This is a concrete pattern language we can copy directly into the harness.
→ Adopt content-hashed event entries and idempotency keys in `audit/journal.jsonl` (upgrade target U6+).
*Evidence: SCI-000140, SCI-000179, SCI-000099.*

### L10. Screening performance is strong but heterogeneous — and so is its evaluation
Pooled sensitivity **0.92**, specificity **0.94**, AUC **0.98** for LLM screening, but with I² = **95.8%**; domain-dependent AUCs span **0.77–0.95**; Cohen's κ at our own screening step was **0.408**. Benchmarks can be contaminated (many predate LLM pretraining).
→ Never certify a screening/eval from aggregate metrics alone; report per-domain performance and inter-rater agreement; keep gold standards contamination-aware.
*Evidence: SCI-000088, SCI-000096, SCI-000164.*

### L11. Don't trust the model chain implicitly; trust the label pipeline audit
The 3-way Existing/Unresolved/Fabricated citation labeler achieved **Cohen's κ = 0.63** against human labels, but *Unresolved* precision was only **0.43** and its dominant error was Unresolved→Fabricated — so reported fabrication rates are **underestimates**.
→ Design for audit trails of the *verification* process itself, and report precision by label, not just accuracy.
*Evidence: SCI-000144.*

### L12. Evaluate the whole pipeline, or don't call it validated
None of the 58 studies supplies an end-to-end, externally validated, multi-domain benchmark jointly covering screening, extraction, synthesis quality, verifiability, and cost. Validations are proof-of-concept against published reviews, single-model, and unblinded.
→ This is the field's open gap and our product opportunity: build an end-to-end evaluation harness (upgrade target U8).
*Evidence: SCI-000090, SCI-000142, SCI-000164, SCI-000135.*

---

## Part B — Method papers worth reading next

Priority-ordered for harness development. Corpus papers have `SCI-xxxx` ids (full text is in `workspaces/ai-research-harnesses-trust/extracted/`); metadata is as resolved from Crossref/arXiv; a few canonical external method references are listed last.

### B1. Corpus method papers (full text available in-workspace)

| # | Paper | Authors (yr) | DOI / venue | Why it matters for the harness |
|---|---|---|---|---|
| 1 | **Do Deployment Constraints Make LLMs Hallucinate Citations?** | Zhao et al. (2026) · `SCI-000144` | arXiv preprint | The definitive citation-verifiability study: 17,443 citations, 3-way labeling, κ=0.63, label-precision pitfalls. Blueprint for our verification layer (L11). |
| 2 | **Synthesizing scientific literature with retrieval-augmented language models** | Asai et al. (2026) · `SCI-000154` | Nature · 10.1038/s41586-025-10072-4 | Training-free retrieval grounding at production scale; the architecture that yields citation-backed answers (L2). |
| 3 | **OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs** | Asai et al. (2024) · `SCI-000159` | arXiv 2411.14199 | OpenScholar-8B, iterative self-feedback retrieval, zero hallucinated papers; the concrete open implementation. |
| 4 | **HySemRAG: Hybrid Semantic Retrieval-Augmented Generation** | Godinez et al. (2025) · `SCI-000100` | arXiv 2508.05666 | KG + vector dual infrastructure; quantifies structured-vs-naive chunking (+35.1%) and temporal drift (−1.9%/day) (L8, L5). |
| 5 | **LUMEN: Cost-Transparent Multi-Agent Pipeline** | (2026) · `SCI-000118` | arXiv | Model routing by phase, end-to-end cost anatomy ($19.51–$29.04/review), and the phase-dependence of multi-agent benefit (L7). |
| 6 | **Compiling Prompts, Not Crafting Them** | Sušnjak (2025) · `SCI-000106` | arXiv | Prompt compilation as a verifiable digital artefact; quantifies prompt fragility (up to 76 accuracy points) (L6). |
| 7 | **Evaluating human and LLM screening workflows in a scoping review** | (2026) · `SCI-000137` | arXiv | The run-to-run item-level instability study (91.7% agreement / 94 disagreements / 29 one-run-only eligible records) (L5). |
| 8 | **Bringing analytic rigor to agentic AI: The Brain Researcher platform** | Chen et al. (2026) · `SCI-000140` | arXiv | Content-hashed commitment cards + immutable run bundles; the provenance pattern to productize (L9). |
| 9 | **LGAR: Zero-Shot LLM-Guided Neural Ranking for Abstract Screening** | Jaumann et al. (2025) · `SCI-000164` | Findings of ACL 2025 · 10.18653/v1/2025.findings-acl.412 | Open-weights screening; benchmark-contamination discussion (L4, L10). |
| 10 | **Performance of LLMs in Automated Medical Literature Screening (meta-analysis)** | Xie et al. (2026) · `SCI-000088` | (via Crossref) | How to meta-analyze screening performance honestly: pooled sens/spec/AUC, I²=95.8%, PROBAST+AI/QUADAS-2 application (L10). |
| 11 | **Benchmarking a Local Schema-Constrained LLM Pipeline** | Serretti (2026) · `SCI-000090` | Cureus · 10.7759/cureus.111193 | Fully-local zero-API pipeline; 100%/97.9%/98.9% extraction; conservative "NR" missingness (L8). |
| 12 | **AutoSynthesis: an agentic system for automated meta-analysis** | Taherinezhad et al. (2026) · `SCI-000135` | arXiv | End-to-end meta-analysis automation: ROBINS-I, PRISMA 2020, funnel plots (methodology playbook). |
| 13 | **meta-pipe: LLM-agent pipeline for automated systematic review and meta-analysis** | Lin et al. (2026) · `SCI-000142` | arXiv | 10-chained skill modules with inter-stage contracts + 5 human gates; honest "no validation data" admission (L12). |
| 14 | **MedMeta: Benchmark for Synthesizing Meta-Analysis Conclusions** | (2026) · `SCI-000127` | arXiv | Benchmark-construction pitfalls; BERTScore failure as reliability proxy (L2). |
| 15 | **Knowledge Synthesis Review Framework: Task-Level Benchmarking** | Shafqat et al. (2026) · `SCI-000115` | arXiv | Task-level benchmarking methodology incl. inter-rater anchors (κ=0.804) — model for our U8 evaluator. |
| 16 | **Biomedical reasoning in action (M-Reason)** | Wysocki et al. (2025) · `SCI-000099` | arXiv 2510.05335 | Deterministic orchestrator with token/runtime logging and agent anti-hallucination prompts (L4, L9). |
| 17 | **TIB AIssistant: Towards AI-Supported Research** | Auer et al. (2025) · `SCI-000141` | arXiv | Vision + human-machine collaboration design; useful for product positioning (part of C34 consensus). |
| 18 | **Large language models for full-text methods assessment (mediation analysis case study)** | Zhang et al. (2026) · `SCI-000124` | JAMIA · 10.1093/jamia/ocag108 | LLM-vs-human precision on full-text methods (0.15–0.30 vs 0.89) — calibrates what to automate vs. escalate. |
| 19 | **LatteReview** | Rouzrokh et al. (2025) · `SCI-000096` | arXiv 2501.05468 | RAG-inside-multi-agent review; SYNERGY benchmark exposure (domain-dependent AUCs). |
| 20 | **Accelerating clinical evidence synthesis with LLMs** | Wang et al. (2025) · `SCI-000109` | npj Digital Medicine · 10.1038/s41746-025-01840-7 | PRISMA-compliant pipeline implementation with real clinical workflow constraints. |

### B2. Canonical external method references (read-only gate: verify before citing)

| Paper | Why |
|---|---|
| Page et al. (2021), *PRISMA 2020 statement*. BMJ 372:n71 | Current reporting gold standard we output to; cite carefully. |
| Tricco et al. (2018), *PRISMA extension for Scoping Reviews (PRISMA-ScR)*. Ann Intern Med 169(7) | Our declared framework; used for the flow diagram. |
| Whiting et al. (2011), *QUADAS-2*. Ann Intern Med 155(8) · Wolff et al. (2019), *PROBAST*. Ann Intern Med 170(1) | Risk-of-bias instruments the Phase-4 stream and corpus L10 rely on. |
| Scells et al., *Systematic Review Corpus / test collections for review retrieval* | Gold-standard test sets for our screening/retrieval evaluation harness (U8). |

---

*Convenience index:* papers are extractable/readable under `workspaces/ai-research-harnesses-trust/extracted/` (look up `SCI-xxxx` in `literature/included.json` for the file). Author metadata for preprint entries marked "(2026) / arXiv" is pending Crossref/arXiv curation in `reports/manuscript_draft.md`.