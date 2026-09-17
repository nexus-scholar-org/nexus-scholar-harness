# scholar-agent-kit — Comprehensive Deep Dive Analysis

**Kit:** `scholar-agent-kit` (`tools/scholar-agent-kit/`)
**Version:** 0.1.0
**Source files:** 2 modules (`server.py` = 1257 lines, `calibration.py` = 467 lines)
**Test files:** 2 test modules (`test_server.py` = 151 lines, `test_calibration.py` = 218 lines) + 3 harness-level test modules (`test_mcp_recon.py` = 666 lines, `test_mcp_tools_graph.py` = 619 lines, `conformance/test_mcp_tool_parity.py` = 34 lines)
**Total LOC (kit source):** ~1724 lines
**Date of analysis:** 2026-09-14

---

## Executive Summary

`scholar-agent-kit` is the **MCP front-door** for the entire Nexus Scholar Suite. It wraps 7 other kits behind 19 Model Context Protocol tools, enabling AI agents (Claude Code, Antigravity, etc.) to drive the full systematic literature review pipeline through a single MCP server.

**Key characteristics:**
- **Thin orchestration layer**: zero domain logic; delegates entirely to kit APIs
- **Phase-0.5 recon bridge**: uniquely bridges the harness `scholar_harness.recon` module via a `sys.path` adapter seam, adding 3 recon tools to the 16 `nexus_*` tools
- **Calibration module**: a standalone pre-flight screener calibration system for PRISMA screening bias mitigation
- **Heavily tested**: ~1300 lines of hermetic tests at the harness level + 369 lines in-kit tests

**Strengths:**
- Clean separation of concerns (server is pure delegation)
- Robust path resolution (`_resolve_path` anchors to `NEXUS_MCP_WORKSPACE` / repo root)
- Session persistence with content-addressed artifacts (FAIR memory)
- Comprehensive error handling (every tool wraps in try/except, returns structured JSON)

**Weaknesses:**
- `scholar-verify-kit` imported but not declared as a dependency (shared-venv hidden dep)
- No `__init__.py` in the `scholar_agent` package (relies on `pyproject.toml` entrypoint)
- Inconsistent return types (some JSON strings, some prose strings)
- `calibration.py` not exposed as an MCP tool
- CLI `--help` string is a static copy of the tool registry (drift risk)

---

## 1. Functionalities

### 1.1 Complete Tool Inventory (19 MCP Tools)

| # | Tool | Source Line | Kit Delegation | Return Type |
|---|------|-------------|----------------|-------------|
| 1 | `nexus_protocol_compile` | server.py:168 | scholar-protocol-kit | JSON (`{status, protocol_id, fingerprint, protocol}`) |
| 2 | `nexus_protocol_validate` | server.py:195 | scholar-protocol-kit | JSON (`{status: VALID/INVALID, ...}`) |
| 3 | `nexus_protocol_render_criteria` | server.py:242 | scholar-protocol-kit | Markdown string |
| 4 | `nexus_discover` | server.py:262 | scholar-search-kit | Prose string (success + file path) |
| 5 | `nexus_dedup` | server.py:293 | scholar-search-kit | Prose string |
| 6 | `nexus_screen` | server.py:318 | scholar-search-kit | Prose string |
| 7 | `nexus_extract_pdf` | server.py:375 | scholar-pdf-kit | Prose string |
| 8 | `nexus_rag_index` | server.py:403 | scholar-rag-kit | Prose string |
| 9 | `nexus_rag_query` | server.py:424 | scholar-rag-kit | Prose string |
| 10 | `nexus_rag_synthesize` | server.py:480 | scholar-rag-kit | Prose string |
| 11 | `nexus_matrix_extract` | server.py:511 | scholar-rag-kit + scholar-protocol-kit | Prose string |
| 12 | `nexus_graph_build` | server.py:534 | scholar-graph-kit | Prose string |
| 13 | `nexus_bib_clean` | server.py:574 | scholar-bib-kit | Prose string |
| 14 | `nexus_screen_reconcile` | server.py:604 | scholar-search-kit | JSON (reconciliation result) |
| 15 | `nexus_verify_claims` | server.py:655 | scholar-verify-kit | JSON (`{status, metrics, claims}`) |
| 16 | `nexus_verify_phase4` | server.py:739 | scholar-verify-kit | JSON (`{status, stream, written}`) |
| 17 | `recon_probe` | server.py:934 | scholar-harness.recon | JSON (session + pool + lineage) |
| 18 | `recon_distill` | server.py:1024 | scholar-harness.recon | JSON (terms + purity + pool gate) |
| 19 | `recon_delta` | server.py:1111 | scholar-harness.recon | JSON (merged pool + followups + lineage) |

### 1.2 Kit-to-Tool Delegation Map

```
scholar-protocol-kit  -->  nexus_protocol_compile, nexus_protocol_validate, nexus_protocol_render_criteria
scholar-search-kit    -->  nexus_discover, nexus_dedup, nexus_screen, nexus_screen_reconcile
scholar-pdf-kit       -->  nexus_extract_pdf
scholar-rag-kit       -->  nexus_rag_index, nexus_rag_query, nexus_rag_synthesize, nexus_matrix_extract
scholar-graph-kit     -->  nexus_graph_build
scholar-bib-kit       -->  nexus_bib_clean
scholar-verify-kit    -->  nexus_verify_claims, nexus_verify_phase4
scholar-harness.recon -->  recon_probe, recon_distill, recon_delta
```

### 1.3 Calibration Module (Not MCP-exposed)

The `calibration.py` module (467 lines) provides a standalone pre-flight screener calibration system:

| Component | Function | Purpose |
|-----------|----------|---------|
| Checklist schema builder | `build_checklist_schema()` | Converts protocol criteria into structured boolean checklist |
| Decision derivator | `checklist_to_decision()` | Deterministic INCLUDE/EXCLUDE from filled checklist |
| Calibration batch builder | `build_preflight_calibration()` | Samples 20 gold-labeled papers for pre-flight calibration |
| Calibration evaluator | `evaluate_calibration()` | Computes sensitivity, specificity, accuracy, inclusion-rate drift |

### 1.4 Data Models and Schemas

**Session state** (`session.json`):
```json
{
  "session_id": "rec_<hex>",
  "topic": "<string>",
  "cache_keys": ["v1/..."],
  "pools": ["<absolute_path>/pool_<sha>.json"],
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>"
}
```

**Pool artifact** (`pool_<sha>.json`):
```json
{
  "cache_key": "v1/...",
  "docs": [<Document objects>],
  "merged_from_cache_keys": ["..."]
}
```

**Distilled artifact** (`distilled_<sha>.json` or `distilled_lx<sha>_<...>.json`):
```json
{
  "cache_key": "...",
  "qei": <float>,
  "metrics": {"<label>": <count>},
  "datasets": {"<label>": <count>},
  "schools": [{"label": "...", "n": <int>, "anchor_dois": [...]}],
  "micro_taxonomy": [...],
  "topics": [{"label": "...", "n": <int>, "anchor_dois": [...], "score": <float>}]
}
```

**Calibration report** (`CalibrationReport` dataclass):
```python
@dataclass
class CalibrationReport:
    total: int
    inclusion_rate: float
    gold_inclusion_rate: float
    inclusion_rate_delta: float
    sensitivity: float | None
    specificity: float | None
    accuracy: float
    verdict: Literal["PASS", "FLAG"]
    reasons: list[str]
    per_criterion: dict[str, dict[str, float]]
```

### 1.5 Integration Points

1. **Harness recon adapter** (`_harness_src()`, server.py:81-101): Walks up directory tree to find `scholar_harness.recon` and injects it onto `sys.path`. Uses `NEXUS_HARNESS_SRC` env override.
2. **MCP anchor resolution** (`_mcp_anchor()`, server.py:135-149): Resolves relative paths against `NEXUS_MCP_WORKSPACE` or nearest `.git` ancestor.
3. **RECON_SEARCH_FN seam** (server.py:114): Global `None`-able callable injected by tests to replace real search in `ReconEngine`.
4. **RECON_CACHE_ROOT** (server.py:126): CWD-independent cache root from `canonical_recon_root()`.
5. **Content-addressed artifact persistence** (`_persist_artifact()`, server.py:924-931): SHA-1 based dedup of pool/distilled artifacts.

---

## 2. Improvements

### 2.1 Code Quality Issues

**2.1.1 Missing `__init__.py`**
The `src/scholar_agent/` directory has no `__init__.py`. While the package builds via `pyproject.toml` and setuptools, this can cause issues with some tooling (mypy, IDEs, certain import patterns).

**2.1.2 Static CLI help string (server.py:1201-1221)**
The `main()` function hardcodes the tool list in `epilog`. This is a drift risk -- the `conformance/test_mcp_tool_parity.py` test catches it, but the string should ideally be generated from the registered tools.

**2.1.3 Inconsistent return types**
- Protocol tools return JSON strings: `json.dumps({"status": "SUCCESS", ...})`
- Discovery/screening tools return prose strings: `"Search completed: N papers..."`
- This forces consumers to parse differently per tool. A uniform envelope would improve agent integration.

**2.1.4 Unused import: `Time` (server.py:21)**
`time` is imported and used only for timestamping cache filenames. Minor but present.

**2.1.5 Dead code path in `nexus_verify_phase4` (server.py:769-773)**
The `retraction` stream's `recs = verify_cli._merged_records(ws)` call before `inc = verify_cli._load(...)` suggests `recs` should be used, but `retraction.RetractionChecker.check(recs, inc)` takes both. This is correct but the variable naming is unclear.

### 2.2 Missing Features / Capabilities

**2.2.1 `calibration.py` not exposed via MCP**
The pre-flight calibration system is a sophisticated, well-tested module that should be accessible to agents. Adding `nexus_calibration_build` and `nexus_calibration_evaluate` MCP tools would enable agents to self-calibrate before screening.

**2.2.2 No `nexus_protocol_extraction_schema` or `nexus_protocol_extraction_prompt` tools**
The protocol kit's `build_extraction_model` and extraction prompt generation have no MCP surface (noted in kits_surface_matrix.md). Agents cannot dynamically generate extraction schemas from protocols.

**2.2.3 No batch discover/search tool**
`nexus_discover` does single-query search. A batch search tool (multiple queries, multi-provider matrix) would improve research efficiency.

**2.2.4 No PDF download tool**
The PDF kit's `AsyncPDFDownloader` has no MCP surface. Agents must use CLI for downloading.

**2.2.5 No consensus/consensus-matrix tool**
`scholar-rag-kit`'s `ConsensusCartographer` has no MCP surface.

### 2.3 API Design Improvements

**2.3.1 Unified return envelope**
All tools should return:
```json
{
  "status": "SUCCESS|ERROR",
  "tool": "<tool_name>",
  "data": { ... },
  "error": null | "<message>"
}
```
Currently, some return `{"status": "SUCCESS", "protocol": ...}` while others return prose strings.

**2.3.2 Type-safe `lexicon_json` parameter**
`recon_distill` accepts `str | dict | None` for `lexicon_json` (server.py:1026). While this handles agent framework quirks, it violates MCP's type system. A cleaner approach: always accept string, document that agents should `json.dumps()` dicts.

**2.3.3 `nexus_screen_reconcile` file-name parsing (server.py:619-623)**
Screener key derivation from `batch_*_decisions*.json` file stems is fragile:
```python
parts = f.stem.split("_decisions")
screener_key = parts[1].strip("_") if len(parts) > 1 and parts[1] else "screener1"
```
This breaks for filenames like `batch_001_decisions_screener_a.json` where the key becomes `screener_a` but the split is on `_decisions`.

### 2.4 Error Handling Gaps

**2.4.1 `nexus_discover` does not handle provider failures gracefully**
If all providers fail (network error), the exception propagates as a generic string. Per-provider error swallowing in the search kit means the agent sees an empty result set with no indication of failure.

**2.4.2 `nexus_graph_build` silent DOI failure**
If `asyncio.run(builder.build_graph(dois))` fails, the outer try/except catches it, but intermediate errors during DOI resolution are silently consumed by the graph kit.

**2.4.3 No timeout on `nexus_rag_index`**
Large document directories could hang indefinitely. No timeout parameter exists.

**2.4.4 `recon_delta` hard cap 3 followups (server.py:1139)**
The budget is `max(0, min(int(followups), 3))`. This is documented but could silently confuse agents that pass `followups=10`.

### 2.5 Documentation Needs

**2.5.1 No module docstring for `calibration.py` purpose in MCP context**
The module documents itself well, but there's no guidance on how it connects to the MCP server (it doesn't -- it's standalone).

**2.5.2 SKILL.md mentions 16 tools in CLI help but 19 are registered**
The SKILL.md (line 60) says "lists 16 tools" but the conformance test enforces 19. The help text string is accurate (lists all 19), but the SKILL.md comment is stale.

**2.5.3 No API reference for `CalibrationBatch.write()`**
The batch writer is tested but not documented for external consumers.

---

## 3. Problems

### 3.1 Known Bugs / Issues

**3.1.1 Undeclared `scholar-verify-kit` dependency**
`server.py` imports `from scholar_verify.verbatim import VerbatimClaimVerifier` (line 53) and `from scholar_verify import cli as verify_cli` (line 54), but `pyproject.toml` does not list `scholar-verify-kit` as a dependency. This works only because the shared venv install (`scripts/install_plugins.py`) makes it available. A standalone `uv sync` would fail.

**3.1.2 `import re` inside function body (server.py:703-708)**
In `nexus_verify_claims`, `re` is imported at module level (line 18) but re-imported at line 703 inside a `for` loop body. This is harmless but indicates code that was likely copy-pasted.

**3.1.3 `_validate_session_id` does not enforce max hex length (server.py:844)**
The regex `^rec_[0-9a-f]{6,64}$` accepts 6-64 hex chars. UUID4 generates 32 hex chars. The upper bound of 64 is arbitrary and not documented.

### 3.2 Edge Cases Not Handled

**3.2.1 `nexus_extract_pdf` with non-existent engine**
If `engine` is neither "grobid" nor "docling" (case-insensitive), it falls back to PyMuPDF (server.py:392-393). The fallback is silent and undocumented. An unrecognized engine name should error.

**3.2.2 `recon_probe` with `session_id=None` and no session dir**
When `session_id` is None, a new ID is generated (server.py:955). But if the generated ID collides with an existing session (astronomically unlikely with UUID4), the session would be silently overwritten because `load_session` is only called if `session.json` exists.

**3.2.3 `nexus_bib_clean` in-place overwrite**
When `output_bib_path` is None, the tool writes back to `input_bib_path` (server.py:585). This silently destroys the original file. No confirmation or backup.

**3.2.4 `nexus_screen` empty input**
If the input JSON file contains an empty list, the tool reports "Screening complete: 0 included, 0 excluded, 0 conflicts" as success. This is correct but could be confusing.

### 3.3 Limitations in Current Implementation

**3.3.1 No multi-turn state for `nexus_*` tools**
Unlike `recon_*` tools which maintain session state across calls, the `nexus_*` tools are stateless. Each call is independent. There's no way to build on previous search results incrementally.

**3.3.2 No streaming or progress callbacks**
All tools are synchronous (except `nexus_discover` which is async internally but the tool itself is not truly streaming). Long operations (RAG indexing, graph building, PDF extraction) block with no progress indication.

**3.3.3 `nexus_rag_query` limited to single `boost_doi`**
Despite accepting a list parameter `boost_dois` in `ScholarRetriever.query`, the MCP tool wraps only a single `boost_doi` string (server.py:447-448).

### 3.4 Technical Debt

**3.4.1 `_harness_src()` adapter seam (server.py:81-101)**
This function walks up the directory tree to find `scholar_harness.recon`. It's documented as a temporary adapter but has persisted since M0.5. The proper fix is to declare `scholar-harness` as a dependency.

**3.4.2 `RECON_SEARCH_FN` global mutable state (server.py:114)**
Test seam is a module-level global. This makes the server non-reentrant and could cause issues in concurrent test execution.

**3.4.3 Static tool list in `main()` epilog (server.py:1201-1221)**
Must be manually updated whenever tools are added/removed. The conformance test catches drift, but auto-generation would be better.

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

**4.1.1 `nexus_discover` sequential provider queries**
The `SearchEngine.search_all()` method (delegated to scholar-search-kit) runs providers sequentially. Parallel provider queries would reduce wall-clock time from `sum(provider_times)` to `max(provider_times)`.

**4.1.2 `nexus_graph_build` blocking `asyncio.run()` (server.py:563)**
The tool is synchronous but calls `asyncio.run(builder.build_graph(dois))`. If the MCP server is already running an event loop, this would fail. The `asyncio.run()` call creates a new loop each time.

**4.1.3 `nexus_rag_index` no incremental indexing**
The `ScholarIndexer.index_directory()` re-indexes all files. For large directories, differential indexing (skip unchanged files) would save time.

### 4.2 Memory Usage Issues

**4.2.1 Full document loading in `nexus_verify_claims` (server.py:698-709)**
All `*.md` files in the extracted directory are loaded into memory as `source_texts` dict. For large corpora (hundreds of fulltext papers), this could consume significant RAM.

**4.2.2 `nexus_rag_query` over-fetching (4x n_results)**
When graph boosting is active, the retriever fetches `4 * n_results` chunks (per scholar-rag-kit documentation). For `n_results=5`, this fetches 20 chunks from ChromaDB.

### 4.3 Caching Opportunities

**4.3.1 Protocol validation cache**
`nexus_protocol_validate` re-parses the protocol JSON on every call. For agents that repeatedly validate the same protocol, a memoization cache keyed on content hash would help.

**4.3.2 `nexus_bib_clean` caching**
If the input file hasn't changed, the lint+dedup pipeline could be skipped. Content hash comparison would enable this.

### 4.4 Parallelization Potential

**4.4.1 `nexus_verify_phase4` stream parallelization**
The Phase-4 streams (retraction, open-science, coi, risk-of-bias, trust-context) are independent. Running them in parallel (using `asyncio.gather` or `concurrent.futures`) would reduce total time, especially for the network-bound retraction check.

**4.4.2 `nexus_extract_pdf` batch mode**
Currently processes one PDF at a time. A batch mode with concurrent extraction engines would improve throughput.

---

## 5. Scientific Correction

### 5.1 MCP Protocol Compliance

**5.1.1 Tool naming convention**
All tools use `snake_case` which is MCP-compliant. The `recon_*` prefix correctly separates the harness-bridged tools from the kit tools.

**5.1.2 Return type inconsistency (protocol violation)**
MCP tools should return structured content. Currently:
- Protocol tools return JSON objects (compliant)
- Recon tools return JSON objects (compliant)
- Discovery/screening tools return unstructured prose (partially non-compliant)

**5.1.3 `recon_distill` dual-type parameter (server.py:1026)**
```python
def recon_distill(session_id: str, lexicon_json: str | dict | None = None) -> str:
```
MCP tool parameters should be JSON-serializable types only. `dict` in the type annotation is a Python convenience, not an MCP schema type. The MCP schema generator may produce incorrect JSON Schema for this parameter.

### 5.2 Tool Design Correctness

**5.2.1 `nexus_screen` bypasses agent-in-the-loop pattern**
The tool runs heuristic screening in-process. The real PRISMA contract is the batch handoff via `agent_screen.py`. The MCP tool is a shortcut that may produce lower-quality decisions.

**5.2.2 `nexus_verify_phase4` reuses CLI internal helpers**
The tool calls `verify_cli._merged_records()`, `verify_cli._load()`, `verify_cli._write()` (server.py:769-818). These are private API (`_`-prefixed) of the verify kit. Breaking changes in the verify kit would silently break this tool.

**5.2.3 `recon_delta` budget hard cap**
The 3-followup cap (server.py:1139) is documented but the parameter still accepts any integer. A cleaner API would reject values > 3 with an error.

### 5.3 Agent Interaction Patterns

**5.3.1 No tool chaining guidance**
The SKILL.md lists tools but doesn't provide recommended tool chains (e.g., "protocol compile -> discover -> screen -> extract -> index -> query"). Agent frameworks would benefit from workflow templates.

**5.3.2 No conversation state management**
The `recon_*` tools maintain state via `session_id`, but the `nexus_*` tools are stateless. Agents must manually thread file paths between calls. A session abstraction for the full pipeline would improve UX.

### 5.4 Academic Workflow Alignment

**5.4.1 PRISMA compliance**
The `nexus_screen` tool outputs `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json`, and `prisma_screening_report.md`. This aligns with PRISMA 2020 flow diagram requirements.

**5.4.2 Calibration for bias mitigation**
The `calibration.py` module addresses a real academic problem (screener bias, Kappa ~0.115). Its 20-paper pre-flight calibration is a sound methodological approach.

**5.4.3 Verbatim claim verification**
The `nexus_verify_claims` tool correctly bridges RAG synthesis claims to verbatim quote matching, addressing the reproducibility crisis in systematic reviews.

---

## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent or Skill Be Created?

**Recommendation: YES — a `calibration-agent` skill should be created, and the existing `scholar-agent-kit` skill should be split.**

### 6.2 Rationale

The `scholar-agent-kit` currently serves two distinct roles:
1. **MCP tool registry** (how to call tools)
2. **Calibration system** (how to ensure screening quality)

These should be separated:

**Skill A: `scholar-agent-kit` (existing, refined)**
- Focus: MCP tool documentation, usage patterns, tool chains
- Narrow scope: 19 MCP tools, their parameters, return types, and integration patterns
- Evaluation metrics: tool call success rate, parameter validation, error handling

**Skill B: `calibration-agent` (new)**
- Focus: Pre-flight screener calibration, checklist management, bias detection
- Narrow scope: 4 calibration functions + MCP tool wrappers
- Evaluation metrics: Kappa improvement, sensitivity/specificity thresholds, inclusion-rate drift detection

### 6.3 Evaluation Metrics for Agent Evaluation

| Metric | Definition | Target | Source |
|--------|------------|--------|--------|
| **Tool call success rate** | % of MCP tool calls returning `status: SUCCESS` | >= 95% | All tools |
| **Parameter validation rate** | % of calls where all params are valid types | 100% | All tools |
| **Inclusion-rate drift** | |agent_inclusion_rate - gold_inclusion_rate| | < 0.15 | calibration.py:438 |
| **Sensitivity** | TP / (TP + FN) for gold-INCLUDE papers | >= 0.80 | calibration.py:444 |
| **Specificity** | TN / (TN + FP) for gold-EXCLUDE papers | >= 0.70 | calibration.py:450 |
| **Calibration verdict** | PASS or FLAG | PASS | calibration.py:436 |
| **Session persistence** | session.json survives across calls | 100% | recon tools |
| **Content-addressed dedup** | Same payload -> same artifact filename | 100% | `_persist_artifact()` |
| **CWD independence** | Relative paths anchor to workspace, not kit dir | 100% | `_resolve_path()` |

### 6.4 Critic Capabilities Needed

1. **Schema validator critic**: Validates MCP tool parameters against JSON Schema before execution
2. **Calibration critic**: Compares agent screening decisions against gold standard, flags drift
3. **Workflow critic**: Validates tool chain ordering (e.g., protocol before screening, index before query)
4. **Path safety critic**: Validates all file paths are within workspace boundaries

### 6.5 Agent-in-the-Loop Opportunities

1. **Calibration loop**: Agent fills checklist -> evaluator compares to gold -> agent re-screens flagged papers -> re-evaluate -> iterate until PASS
2. **Screening reconciliation loop**: Multiple agents screen independently -> reconcile -> adjudicate conflicts -> re-screen borderline cases
3. **Grounded recon loop**: probe -> distill -> delta (gap follow-ups) -> re-distill until purity is "coherent"

### 6.6 Automation Potential

| Workflow | Current State | Automation Potential |
|----------|---------------|---------------------|
| Protocol compile + validate | Manual two-step | HIGH: auto-validate after compile |
| Discover + dedup + screen | Three separate calls | HIGH: chain into single workflow |
| Extract + index + query | Three separate calls | HIGH: pipeline automation |
| Calibration + screening | Not connected | HIGH: auto-calibrate before screening |
| Graph build + RAG query with boosting | Manual parameter threading | MEDIUM: auto-construct graph_source path |

---

## 7. Priority-Ranked Improvement Suggestions

### Priority 1: Critical (Blocks correctness)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P1.1 | Declare `scholar-verify-kit` as dependency | pyproject.toml:6-14 | Add `"scholar-verify-kit"` to `dependencies` |
| P1.2 | Remove duplicate `import re` inside loop | server.py:703 | Remove `import re` (already at line 18) |
| P1.3 | `_resolve_path` should not treat all non-JSON strings as paths | server.py:156 | Add file existence check before path resolution |

### Priority 2: High (Improves reliability)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P2.1 | `nexus_extract_pdf` silent fallback for unknown engine | server.py:392 | Error on unrecognized engine names |
| P2.2 | `nexus_bib_clean` in-place overwrite without backup | server.py:585 | Add `.bak` backup or document behavior |
| P2.3 | Static CLI help string drift risk | server.py:1201-1221 | Generate from registered tools |
| P2.4 | Expose calibration module via MCP tools | calibration.py | Add `nexus_calibration_build`, `nexus_calibration_evaluate` |

### Priority 3: Medium (Improves UX)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P3.1 | Inconsistent return types (JSON vs prose) | server.py:all | Standardize all tools to JSON envelope |
| P3.2 | `nexus_rag_query` single boost_doi limit | server.py:447 | Accept list of DOIs |
| P3.3 | No batch discover tool | N/A | Add `nexus_discover_batch` |
| P3.4 | No PDF download tool via MCP | N/A | Add `nexus_pdf_download` |

### Priority 4: Low (Cleanup / tech debt)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P4.1 | Missing `__init__.py` | src/scholar_agent/ | Add empty `__init__.py` |
| P4.2 | `_harness_src()` adapter is long-lived tech debt | server.py:81-101 | Properly declare harness dependency |
| P4.3 | `RECON_SEARCH_FN` global mutable state | server.py:114 | Consider contextvar or fixture pattern |
| P4.4 | `recon_distill` dual-type parameter | server.py:1026 | Document MCP limitation, keep for compat |
| P4.5 | SKILL.md stale tool count comment | SKILL.md:60 | Update to "19 tools" |

---

## Appendix A: File Structure

```
tools/scholar-agent-kit/
  pyproject.toml              # Package definition, deps (MISSING: scholar-verify-kit)
  .gitignore                  # Standard ignores
  uv.lock                     # Lockfile
  src/
    scholar_agent/
      server.py               # MCP server, 19 tools, 1257 lines
      calibration.py           # Pre-flight calibration, 467 lines
      __pycache__/
  tests/
    test_server.py            # 151 lines, 3 test functions
    test_calibration.py       # 218 lines, 11 test functions
  .cache/
    mcp/                      # Cached discover results
    inception_recon/          # FAIR recon session cache
      sessions/               # Session state (session.json + pool/distilled artifacts)
      pools/                  # Content-addressed pool artifacts
    hishel/                   # HTTP cache
  .venv/                      # Kit-local venv (not shared)
```

## Appendix B: Key Code References

| Concept | File | Lines |
|---------|------|-------|
| MCP server instance | server.py | 132 |
| Harness adapter seam | server.py | 81-106 |
| MCP path anchor | server.py | 135-161 |
| Content-addressed persistence | server.py | 910-931 |
| Session state management | server.py | 836-908 |
| Session ID validation | server.py | 844-851 |
| Workspaces root safety guard | server.py | 854-862 |
| Checklist schema builder | calibration.py | 29-58 |
| Checklist-to-decision logic | calibration.py | 65-128 |
| Calibration batch builder | calibration.py | 154-283 |
| Calibration evaluator | calibration.py | 342-467 |
| CLI entrypoint | server.py | 1194-1257 |
| MCP config (launch) | .agents/plugins/nexus-scholar/mcp_config.json | 1-13 |
| SKILL.md | .agents/skills/scholar-agent-kit/SKILL.md | 1-128 |
| Kit surface matrix entry | docs/kits_surface_matrix.md | 295-314 |

## Appendix C: Test Coverage Summary

| Test Module | Lines | Test Count | Focus |
|-------------|-------|------------|-------|
| `tests/test_server.py` | 151 | 3 | Protocol compile/validate/render, dedup+screen, RAG+matrix |
| `tests/test_calibration.py` | 218 | 11 | Checklist schema, decision derivation, calibration build/evaluate |
| `tests/test_mcp_recon.py` | 666 | 18 | recon_probe/distill/delta, session persistence, lexicon merge, purity gates, workspaces safety |
| `tests/test_mcp_tools_graph.py` | 619 | ~20 | Graph HTTP client, PDF metadata, bib clean, screen artifacts, verify claims normalization, protocol validation parity, RAG graph boosting |
| `tests/conformance/test_mcp_tool_parity.py` | 34 | 2 | Action table MCP references, --help registry drift |

**Total test coverage:** ~1688 lines, ~54 test functions across 5 modules.
