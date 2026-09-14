# Phase 6: Scientific Trust, Verifiable Provenance & DeepSeek Harness (DSH) Bridge

**Specification & Implementation Blueprint for Top-Tier Scientific Reliability**
*Document Version: 1.0.0 · Date: 2026-09-09*

---

## 1. Executive Summary & Epistemological Justification

The empirical validation across 58 academic studies (`ai-research-harnesses-trust`) proved two critical truths:
1. **Unchecked LLM Generation is Fundamentally Unscientific**: LLMs hallucinate citations at 78–98% under deployment constraints (Zhao et al., 2026). Generic semantic similarity metrics (BERTScore, ROUGE) frequently judge negated, counter-factual scientific conclusions as semantically identical to verified truths.
2. **True Reliability Demands Byte-Level Grounding & Cryptographic Audit Trails**: A scientific research harness cannot treat LLM outputs as authoritative without deterministic verification gates. Every claim in the literature synthesis must be backed by byte-exact verbatim evidence quotes, and all screening/extraction workflows must be mathematically audited.

Phase 6 implements the **Scientific Rigor Architecture** and connects Nexus Scholar's deterministic toolkits to modern external agent harnesses (DeepSeek Harness `dsh`, OpenCode) via standard Model Context Protocol (MCP) bindings.

---

## 2. Core Pillars of Phase 6

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DEEPSEEK HARNESS (DSH)                          │
│                   Web UI / Creator Mode / Node Pipeline Graph               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │  Model Context Protocol (stdio / MCP)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    SCHOLAR AGENT KIT (FastMCP Server)                       │
│  nexus_screen_reconcile │ nexus_verify_claims │ nexus_rag_query │ ...       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
┌───────────────┐              ┌───────────────┐                ┌───────────────┐
│ SEARCH KIT    │              │ VERIFY KIT    │                │ RAG & GRAPH   │
│ Multi-Rater κ │              │ Verbatim      │                │ Scoped AST    │
│ Adjudication  │              │ Attribution   │                │ Indexing      │
└───────┬───────┘              └───────┬───────┘                └───────┬───────┘
        │                              │                                │
        └──────────────────────────────┼────────────────────────────────┘
                                       ▼
                     ┌───────────────────────────────────┐
                     │     CANONICAL WORKSPACE CONTRACT   │
                     │  protocol.json | included.json    │
                     │  claims.json   | audit/journal    │
                     └───────────────────────────────────┘
```

### Pillar 1: Deterministic Multi-Screener Adjudication (`scholar-search-kit`)
* **Multi-Rater Fleiss' $\kappa$**: Formal inter-rater agreement computation replacing subjective single-agent screening.
* **Strict Majority & Deadlock Escalation**: Automatically partitions $n$-rater decisions ($n \ge 3$); isolates deadlocks (e.g. 2-vs-2) into dedicated `adjudication_batch.json` files for Senior Adjudicator resolution.
* **Deterministic PRISMA 2020 Synchronization**: Emits `prisma_screening_report.md` and `prisma_report.json` in exact synchrony with reconciliation matrices.

### Pillar 2: Verbatim Evidence Verification (`scholar-verify-kit`)
* **Byte & Token Verifier (`VerbatimClaimVerifier`)**:
  * Dual-pass sliding character-window (8-char, step 4) and token $n$-gram (6-token, step 3) search.
  * Unicode NFKC normalization, typography/hyphenation repair, and quote standardizations.
  * Rejects claims failing coverage threshold ($\ge 0.90$).
* **Elimination of "LLM-as-a-judge"**: Trust is anchored in source documents, not secondary model evaluations.

### Pillar 3: Corpus-Scope Isolation & Whitelist Enforcing (`scholar-rag-kit`)
* **Whitelisted Ingestion**: `ScholarIndexer` strictly requires `included.json` before indexing full texts into ChromaDB.
* **Pollution Elimination**: Quarantines excluded papers to prevent contaminated baseline citations.

### Pillar 4: DeepSeek Harness (DSH) & External Agent Bridge (`scholar-agent-kit`)
* Exposes all research capabilities via FastMCP (`nexus-scholar` server).
* Enables researchers to operate DeepSeek Harness in **Creator Mode** with strict tool gating.

---

## 3. DeepSeek Harness (DSH) Integration Guide

### Step 1: Register the Nexus Scholar MCP Server
DeepSeek Harness natively supports standard Model Context Protocol (MCP) clients over `stdio`.

1. Launch your DeepSeek Harness workspace or web server:
   ```bash
   npx @deepseek-ai/dsh web
   ```
2. Navigate to **Settings ➔ MCP Servers ➔ Add Custom Server**.
3. Configure the stdio transport to point to the repository virtual environment:
   * **Server Name**: `nexus-scholar`
   * **Transport Type**: `stdio`
   * **Command**: `uv`
   * **Arguments**: `["run", "--directory", "tools/scholar-agent-kit", "scholar-agent"]`
4. Confirm connection. DSH will introspect and register all tools:
   * `nexus_protocol_compile`
   * `nexus_protocol_validate`
   * `nexus_screen_reconcile` *(New)*
   * `nexus_verify_claims` *(New)*
   * `nexus_rag_synthesize`
   * `nexus_matrix_extract`

### Step 2: Configure Creator Mode Agent Preset
To guarantee academic integrity, prevent external models from calling generic unverified web tools or modifying file arbitrary paths outside the workspace contract:

1. In DSH, open **Agent Presets ➔ Create Preset**.
2. Name: `Nexus Academic Protocol Engine`.
3. **Tool Access Rules**:
   * *Disable*: Default Web Search, Default Shell/Terminal, Direct Python Repl.
   * *Enable*: All `nexus_*` MCP tools.
4. **System Instruction Injection**:
   ```markdown
   You are an audited research agent operating inside the Nexus Scholar framework.
   You must NEVER synthesize claims without evidence quotes verifiable against source documents.
   Every step must adhere strictly to protocol.json and produce artifacts compatible with audit/journal.jsonl.
   ```

### Step 3: File-Contract Routing in DSH
* Mount the active workspace folder (`workspaces/<project-slug>/`) into DSH.
* All generated batches (`batch_NNN.json`), screening adjudications (`adjudication_resolved.json`), and synthesis claim manifests (`claims.json`) remain local, git-tracked, and audited.

---

## 4. Verification & Validation Metrics

Phase 6 introduces four quantifiable validation gates before any literature review is certified:

| Metric | Target | Verification Method |
|---|---|---|
| **Inter-Rater Reliability** | Fleiss' $\kappa \ge 0.40$ (screening) | `calculate_fleiss_kappa()` in `scholar_search.screening` |
| **Claim Verifiability** | $\ge 95\%$ byte-verbatim coverage | `VerbatimClaimVerifier` in `scholar_verify.verbatim` |
| **Corpus Purity** | 0% screened-out citations | Indexer whitelist validation against `included.json` |
| **Audit Completeness** | 100% stage event logging | Append-only verification in `audit/journal.jsonl` |

---

## 5. Architectural Deliverables Completed in this Cycle

- [x] **`tools/scholar-verify-kit/src/scholar_verify/verbatim.py`**: Exported `VerbatimClaimVerifier` with NFKC normalization, character window, and token $n$-gram matching.
- [x] **`scholar-verify verbatim-claims` CLI**: Subcommand to verify claims ledgers against extracted Markdown folders.
- [x] **`tools/scholar-search-kit/src/scholar_search/screening.py`**: Implemented `calculate_fleiss_kappa` and `reconcile_multi_screener_decisions`.
- [x] **`tools/scholar-agent-kit/src/scholar_agent/server.py`**: Registered `nexus_screen_reconcile` and `nexus_verify_claims` as standard FastMCP tools.
- [x] **Unit Test Suite**: `tests/test_rigor_upgrades.py` passing with 100% test coverage.

