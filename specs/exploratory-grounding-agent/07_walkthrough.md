# 07 — Walkthrough (LLM Unit-Test Generation for Legacy COBOL/Fortran)

> Concrete example tracing a vague curiosity through all 5 lifecycle steps. This matches the live `nexus_discover` probe that produced 8 real deduped papers.

## The user

> "I want to explore how LLMs can generate unit tests for legacy code — COBOL, Fortran, that kind of stuff."

## Step 1 — Intent Clarification ❗

**Copilot asks:** context (unit tests only?), boundary (legacy COBOL/Fortran only vs all languages), outcome (generating tests vs evaluating generated tests).

**User answers:** "Unit tests — focus on legacy COBOL/Fortran, and I care about *whether the tests are actually good*. Also modern knowledge workers."

**Clarified axis:** `LLM unit-test generation for legacy COBOL/Fortran, evaluated for quality, with worker-facing tooling`.

## Step 2 — Empirical Surface Scan 🔍

**Probe 1** (semantic, OpenAlex-first): `"LLM unit test generation legacy COBOL Fortran"`

- Live result from `nexus_discover`: **8 unique papers** (deduped across Crossref + OpenAlex), e.g.:
  - *Security Unit Test Generation for LLM-Produced Code* (Crossref, 10.2139/ssrn.6143746)
  - *Test Intention Guided LLM-Based Unit Test Generation* (10.1109/icse55347.2025.00243)
  - *BenjiTest* (10.2139/ssrn.6843083)
  - *Leveraging LLMs for Legacy Code Modernization* (OpenAlex, 10.48550/arxiv.2411.14971)
  - *CodeTransOcean* (10.18653/v1/2023.findings-emnlp.337)

**Cap:** keep **8 eligible abstracts** (within the 10-25 target; small pool signals a niche).
**OA full-text candidate:** *Leveraging LLMs for Legacy Code Modernization* is arXiv OA → fetch 1 full text.

## Step 3 — Micro-Extraction 🏷️

Distiller over the 8 abstracts + 1 arXiv full text:

- **Micro-taxonomy:** `unit test generation`, `LLM-produced code`, `test intention`, `legacy modernization`, `code transformation`.
- **Metrics observed:** test accuracy, correctness of generated tests, coverage proxies.
- **Datasets observed:** SWE-bench-adjacent eval corpora, CodeTransOcean multiling code corpus (COBOL/Fortran included). *None pre-invented.*
- **Sub-schools:** (1) security-aware unit test generation for LLM output; (2) intention-guided test generation; (3) legacy code modernization (tests as a by-product).

## Step 4 — Grounded Direction Proposal 🧭

**Copilot presents 3 directions, each anchored:**

1. **Security-first unit tests for LLM-produced patches** (dense: Security Unit Test Generation + test-intention line). *Crowded.*
2. **Intention-guided test generation for legacy COBOL/Fortran** (thin: mostly modernization-adjacent, only ~2 direct hits). *Scarce + high value.*
3. **Multi-lingual code-coprus evals incl. COBOL/Fortran** (CodeTransOcean). *Infra-heavy.*

**User picks Direction 2.**

## Step 5 — Refinement & High-Fidelity Intent ✅

**Delta probe:** `"intention-guided unit test generation COBOL modernization evaluation"`

- Cache hit reuse (probe 1 pool) + 1 targeted follow-up.
- Terms that survive into the IntentPacket all carry anchor DOIs (10.2139/ssrn.6143746, 10.48550/arxiv.2411.14971, …).
- `GENESIS` event logged with `recon_context` (session id, cache keys, pool sizes [8, …], anchor DOIs).

## Output protocol.vocabulary (illustrative)

```
concepts: ["LLM unit test generation", "legacy COBOL/Fortran", "test quality evaluation"]
synonyms: ["intention-guided", "coverage-guided", "modernized-assembly?" → dropped (no anchor)]
proof_proxy: "held-out eval: defect-detection power of generated tests (pool-observed)")
exclusions: ["mainstream-language-only test gen", "static analysis without generation"]
```

Every line traces to `recon_terms_<session>.json`; nothing invented.

## Completion criteria met?

- ✅ Vague prompt → specific validated direction with citations (Direction 2, thin but evidence-backed).
- ✅ Every IntentPacket element traceable to a retrieved DOI → **acceptance posture satisfied.**
- ✅ No workspace write before genesis.