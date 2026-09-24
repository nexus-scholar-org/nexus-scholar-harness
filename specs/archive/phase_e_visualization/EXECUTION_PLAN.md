# Phase E Execution Plan

**Spec:** `specs/phase_e_visualization/README.md` v1.1.0
**Total Effort:** 10h (E1: 3.5h, E2: 3h, E3: 2.5h, E4: 1h)
**Principle:** Enhance existing classes -- never create parallel systems.

---

## Feature E1: Enhanced Graph Visualization (3.5h)

### Task 1: Enhance `GraphVisualizer.__init__` with configurable parameters [INDEPENDENT]
**Description:** Add optional constructor parameters (`physics_enabled`, `height`, `width`, `bgcolor`, `font_color`) to the existing `GraphVisualizer.__init__`, preserving backward compatibility.
**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/visualizer.py`

### Execution Checklist
- [ ] Add `physics_enabled: bool = True`, `height: str = "800px"`, `width: str = "100%"`, `bgcolor: str = "#ffffff"`, `font_color: str = "#333333"` parameters to `__init__` after `output_path`
- [ ] Store all new parameters as `self.*` instance attributes
- [ ] Keep `output_path: str | Path` as the sole required parameter (backward compat)

### Testing Strategy
- Existing test `test_graph_visualizer_html` calls `GraphVisualizer(out_html)` with one arg -- must still pass unchanged.
- New unit test: `GraphVisualizer(path, physics_enabled=False, height="600px")` constructs without error and stores attributes.

### Definition of Done (DoD)
- `uv run pytest tools/scholar-graph-kit/tests/test_visualizer.py` passes with 0 failures; old single-arg constructor still works.

---

### Task 2: Implement `_compute_node_colors()`, `_compute_node_sizes()`, `_build_tooltip()` [INDEPENDENT]
**Description:** Add three private helper methods to `GraphVisualizer` for computing normalized node sizes, community-based color mapping, and HTML tooltips from a NetworkX graph.
**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/visualizer.py`

### Execution Checklist
- [ ] Add `_compute_node_sizes(self, G, attr, min_size=10, max_size=30) -> dict[str, int]` -- normalizes `attr` values across nodes to `[min_size, max_size]`; returns uniform size when all values equal or graph empty
- [ ] Add `_compute_node_colors(self, G, attr) -> dict[str, str]` -- maps unique `attr` values to a 20-color palette using modular indexing; handles missing attributes gracefully
- [ ] Add `_build_tooltip(self, node, attrs) -> str` -- builds HTML tooltip string with DOI, title, year, citations, community, pagerank fields using `<b>` and `<br>` tags

### Testing Strategy
- Unit test with a 3-node graph: verify `_compute_node_sizes` returns ints within `[10, 30]`
- Unit test with `community` attribute: verify `_compute_node_colors` returns a hex color per node, deterministic for same inputs
- Unit test `_build_tooltip`: verify output contains `<b>` and expected field names

### Definition of Done (DoD)
- Methods return correct types; sizes normalized; colors deterministic; tooltip contains expected HTML structure.

---

### Task 3: Rewrite `generate_html()` to use new helpers and support `node_color_attr`
**Description:** Refactor the existing `generate_html` method to accept `node_color_attr`, use the new helper methods, and support configurable physics/size/color via constructor.
**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/visualizer.py`

### Execution Checklist
- [ ] Add parameters: `node_size_attr: str = "citations"`, `node_color_attr: str | None = None`, `title: str = "Citation Network"` to `generate_html()`
- [ ] Compute `node_sizes = self._compute_node_sizes(G, node_size_attr)` and `node_colors = self._compute_node_colors(G, node_color_attr) if node_color_attr else {}`
- [ ] Replace inline tooltip with `self._build_tooltip(node, data)`
- [ ] Use `self.physics_enabled` to call `net.toggle_physics(True/False)` conditionally
- [ ] Pass `self.height`, `self.width`, `self.bgcolor`, `self.font_color` to `Network()` constructor
- [ ] Replace `net.from_nx(G)` with manual node/edge iteration using `net.add_node(...)` and `net.add_edge(...)` to inject computed size/color/tooltip per node
- [ ] Call `net.set_title(title)` before saving
- [ ] Call `self._inject_custom_css(self.output_path)` after `net.save_graph()`
- [ ] Return `self.output_path`

### Testing Strategy
- Existing `test_graph_visualizer_html` (no `node_color_attr`) must still pass -- backward compat.
- New test: graph with `community` attribute, call `generate_html(G, node_color_attr="community")`, verify HTML written and file contains node labels.

### Definition of Done (DoD)
- `uv run pytest tools/scholar-graph-kit/tests/test_visualizer.py` -- all tests pass; HTML output contains expected node content.

---

### Task 4: Inject custom CSS via `_inject_custom_css()`
**Description:** Add a method that injects a custom `<style>` block into the generated HTML for better visual presentation.
**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/visualizer.py`

### Execution Checklist
- [ ] Add `_inject_custom_css(self, html_path: Path) -> None` that reads HTML, inserts CSS before `</head>`, writes back
- [ ] CSS should set `body { font-family: Arial; margin: 0; padding: 0; }` and `#mynetwork { width: 100%; height: 100vh; }`
- [ ] Guard: only inject if `</head>` is present in content
- [ ] Ensure `generate_html` calls this method after `net.save_graph()` (done in Task 3)

### Testing Strategy
- Unit test: generate HTML, read file, assert `<style>` block present and contains `#mynetwork`.

### Definition of Done (DoD)
- Generated HTML file contains the injected `<style>` block with expected CSS rules.

---

### Task 5: Add `visualize` CLI command [INDEPENDENT]
**Description:** Add a `visualize` command to the `scholar-graph-kit` Typer app that loads a graph JSON file and renders an interactive HTML visualization.
**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/cli.py`

### Execution Checklist
- [ ] Add `@app.command("visualize")` function `visualize_cmd` with args: `graph_file: Path`, `--output` (default "graph.html"), `--title` (default "Citation Network"), `--physics/--no-physics`, `--node-size` (default "citations"), `--node-color` (default None)
- [ ] Defer `import networkx as nx` and `import json` inside function body (P7.7)
- [ ] Load graph: `data = json.loads(graph_file.read_text(encoding="utf-8"))` then `G = nx.node_link_graph(data)`
- [ ] Instantiate `GraphVisualizer(output, physics_enabled=physics)` and call `vis.generate_html(G, node_size_attr=node_size, node_color_attr=node_color, title=title)`
- [ ] Print success via `console.print` with node/edge counts

### Testing Strategy
- Integration test via `CliRunner`: write a small graph JSON fixture to `tmp_path`, invoke `["visualize", str(graph_file), "-o", str(out_html)]`, assert exit code 0 and output file exists.
- Verify command appears in `--help` output.

### Definition of Done (DoD)
- `uv run scholar-graph-kit visualize --help` shows the command; test invokes it on fixture with exit code 0.

---

### Task 6: Write unit tests for E1
**Description:** Create comprehensive tests covering backward compatibility, community coloring, sizing normalization, CSS injection, and the CLI command.
**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_visualizer.py` (update)

### Execution Checklist
- [ ] Add `test_graph_visualizer_backward_compat` -- call `GraphVisualizer(path).generate_html(G)`, verify HTML written
- [ ] Add `test_graph_visualizer_community_coloring` -- graph with `community` attr, call `generate_html(G, node_color_attr="community")`, verify HTML
- [ ] Add `test_graph_visualizer_no_physics` -- call with `physics_enabled=False`, verify HTML
- [ ] Add `test_compute_node_sizes_normalization` -- 3 nodes with different citations, verify sizes in range
- [ ] Add `test_compute_node_colors_deterministic` -- same graph called twice produces identical colors
- [ ] Add `test_build_tooltip_content` -- verify tooltip contains expected fields
- [ ] Add `test_inject_custom_css` -- verify `<style>` block in output HTML
- [ ] Add `test_visualize_cli_command` -- CliRunner integration test (from Task 5)

### Testing Strategy
- All tests hermetic: use `tmp_path` fixture, no network calls.
- Run: `uv run pytest tools/scholar-graph-kit/tests/test_visualizer.py -v`

### Definition of Done (DoD)
- All new and existing tests pass; `uv run pytest tools/scholar-graph-kit/tests/ -v` green.

---

## Feature E2: PRISMA Flow Diagrams (3h)

### Task 7: Add `to_mermaid()` to `PrismaFlowReport` [INDEPENDENT]
**Description:** Add a `to_mermaid()` method to the existing `PrismaFlowReport` dataclass that generates a PRISMA 2020 flow diagram in Mermaid syntax.
**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/screening.py`

### Execution Checklist
- [ ] Add `to_mermaid(self) -> str` method to `PrismaFlowReport` after the existing `to_markdown()`
- [ ] Generate Mermaid `graph TD` with nodes A (Records identified), B (Records screened), C (Records excluded), D (Full-text assessed), E (Studies included) using `n=` counts from `self.*` fields
- [ ] Add edges: `A --> B`, `B --> C`, `B --> D`, `D --> E`
- [ ] If `self.exclusion_reasons_breakdown` is non-empty, add sub-nodes `EX1`, `EX2`, etc. linked from `C` with reason text and counts
- [ ] Wrap in ```` ```mermaid ``` ```` fences
- [ ] Return the complete string

### Testing Strategy
- Unit test: construct `PrismaFlowReport(total_identified=100, ..., exclusion_reasons_breakdown={"OOS": 5})`, call `to_mermaid()`, assert output contains `graph TD`, `A[`, `-->`, `EX1`
- Unit test with empty `exclusion_reasons_breakdown`: verify no `EX` nodes appear

### Definition of Done (DoD)
- `to_mermaid()` returns valid Mermaid syntax; test asserts structural correctness.

---

### Task 8: Add `to_plantuml()` to `PrismaFlowReport` [INDEPENDENT]
**Description:** Add a `to_plantuml()` method to `PrismaFlowReport` that generates a PRISMA 2020 flow diagram in PlantUML activity-diagram syntax.
**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/screening.py`

### Execution Checklist
- [ ] Add `to_plantuml(self) -> str` method after `to_mermaid()`
- [ ] Generate `@startuml` / `@enduml` activity diagram with `start`, `:Records identified (n=X);`, `:Records screened (n=X);`, conditional `if (Any excluded?)` with exclusion notes, `:Studies included (n=X);`, `stop`
- [ ] If `exclusion_reasons_breakdown` non-empty, add `note right` with reason lines
- [ ] Return the complete string

### Testing Strategy
- Unit test: construct same `PrismaFlowReport`, call `to_plantuml()`, assert output contains `@startuml`, `@enduml`, `n=100`
- Unit test: verify conditional branch and exclusion notes appear when breakdown is non-empty

### Definition of Done (DoD)
- `to_plantuml()` returns valid PlantUML syntax; tests pass.

---

### Task 9: Add `prisma-diagram` CLI command [DEPENDS on Tasks 7, 8]
**Description:** Add a `prisma-diagram` command to the `scholar-search-kit` Typer app that reads `prisma_report.json` and outputs Mermaid or PlantUML diagrams.
**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/cli.py`

### Execution Checklist
- [ ] Add `@app.command("prisma-diagram")` function `prisma_diagram` with args: `prisma_report: Path`, `--format/-f` (default "mermaid", choices "mermaid"/"plantuml"), `--output/-o` (default None = stdout)
- [ ] Defer `import json` inside function body (P7.7)
- [ ] Load JSON: `data = json.loads(prisma_report.read_text(encoding="utf-8"))`
- [ ] Construct `PrismaFlowReport` from `data` dict fields
- [ ] Branch on `format`: call `report.to_mermaid()` or `report.to_plantuml()`
- [ ] If `output` provided, write diagram string to file; else print to stdout via `typer.echo`
- [ ] Raise `typer.BadParameter` for unknown format

### Testing Strategy
- Integration test via `CliRunner`: write a small `prisma_report.json` to `tmp_path`, invoke `["prisma-diagram", str(report_path), "-f", "mermaid"]`, assert exit code 0, stdout contains `graph TD`
- Same for `"-f", "plantuml"`, assert stdout contains `@startuml`
- Test with `-o` flag: assert output file created with correct content

### Definition of Done (DoD)
- `uv run scholar-search-kit prisma-diagram --help` shows the command; tests pass for both formats.

---

### Task 10: Write unit tests for E2
**Description:** Create comprehensive tests for `to_mermaid()`, `to_plantuml()`, and the `prisma-diagram` CLI command.
**Files to Touch:**
- `tools/scholar-search-kit/tests/test_screening.py` (update)

### Execution Checklist
- [ ] Add `test_prisma_to_mermaid` -- construct `PrismaFlowReport`, verify Mermaid structure
- [ ] Add `test_prisma_to_mermaid_with_exclusions` -- non-empty breakdown, verify EX nodes
- [ ] Add `test_prisma_to_mermaid_empty_exclusions` -- empty breakdown, no EX nodes
- [ ] Add `test_prisma_to_plantuml` -- construct `PrismaFlowReport`, verify PlantUML structure
- [ ] Add `test_prisma_to_plantuml_with_exclusions` -- non-empty breakdown, verify note
- [ ] Add `test_prisma_diagram_cli_mermaid` -- CliRunner integration test
- [ ] Add `test_prisma_diagram_cli_plantuml` -- CliRunner integration test
- [ ] Add `test_prisma_diagram_cli_output_file` -- verify file write
- [ ] Add `test_existing_to_markdown_unchanged` -- verify `to_markdown()` still works (regression)

### Testing Strategy
- All hermetic: construct `PrismaFlowReport` with known values, no network calls.
- Run: `uv run pytest tools/scholar-search-kit/tests/test_screening.py -v`

### Definition of Done (DoD)
- All new and existing screening tests pass; `uv run pytest tools/scholar-search-kit/tests/ -v` green.

---

## Feature E3: PRISMA 2020 Compliance Scoring (2.5h)

### Task 11: Add `prisma_compliance()` to `validate.py` [INDEPENDENT]
**Description:** Add a `prisma_compliance()` function that scores a `ResearchProtocol` against the PRISMA 2020 checklist, returning a structured compliance report.
**Files to Touch:**
- `tools/scholar-protocol-kit/src/scholar_protocol/validate.py`

### Execution Checklist
- [ ] Define `_PRISMA_CHECKS` dict mapping section names (TITLE, ABSTRACT, INTRODUCTION, METHODS, RESULTS, DISCUSSION, OTHER) to lists of `(item_id, check_fn, description)` tuples
- [ ] Each `check_fn` accepts a `ResearchProtocol` instance and returns `bool`
- [ ] TITLE: 1.1 (bool(metadata.title)), 1.2 (bool(research_questions))
- [ ] ABSTRACT: 2.1 (bool(metadata.title))
- [ ] INTRODUCTION: 3.1 (bool(epistemology.epistemological_rationale)), 3.2 (bool(research_questions))
- [ ] METHODS: 4.1-4.8 checking screening_criteria, search_strategy fields, matrix_dimensions, verification flags
- [ ] RESULTS: 5.1-5.4 all return `False` (TODO: require execution state)
- [ ] DISCUSSION: 6.1-6.2 all return `False` (TODO: require synthesis state)
- [ ] OTHER: 7.1 (bool(metadata.funding))
- [ ] Implement `prisma_compliance(protocol: ResearchProtocol) -> dict[str, Any]` returning `{total_items, addressed_items, compliance_score, sections}`

### Testing Strategy
- Unit test with a fully-populated valid protocol fixture: verify `compliance_score > 0.8`
- Unit test with a minimal protocol: verify `compliance_score` reflects missing fields
- Unit test: verify `RESULTS` and `DISCUSSION` sections always report `False` items
- Unit test: verify `total_items == addressed_items + (total - addressed)` arithmetic

### Definition of Done (DoD)
- `prisma_compliance()` returns correct structure and scores; no import errors.

---

### Task 12: Add `prisma-check` CLI command [DEPENDS on Task 11]
**Description:** Add a `prisma-check` command to the `scholar-protocol-kit` Typer app that loads a `protocol.json` and prints a PRISMA 2020 compliance checklist with scores.
**Files to Touch:**
- `tools/scholar-protocol-kit/src/scholar_protocol/cli.py`

### Execution Checklist
- [ ] Add `@app.command("prisma-check")` function `prisma_check` with args: `path: pathlib.Path`, `--json` (default False)
- [ ] Use existing `_load_protocol(path)` helper to load the protocol
- [ ] Import `prisma_compliance` from `scholar_protocol.validate` (deferred or top-level)
- [ ] Call `result = prisma_compliance(protocol)`
- [ ] If `--json`: print `json.dumps(result, indent=2)` to stdout
- [ ] Else: print summary with Rich formatting -- overall score percentage, section-by-section breakdown with green checkmark / red cross per item
- [ ] Update module docstring at top of `cli.py` to document the new command

### Testing Strategy
- Integration test via `CliRunner`: use a valid fixture from `tests/fixtures/valid/`, invoke `["prisma-check", str(fixture_path)]`, assert exit code 0, stdout contains compliance percentage
- Test `--json` flag: assert stdout is valid JSON with expected keys
- Test with non-existent path: assert exit code 2

### Definition of Done (DoD)
- `uv run scholar-protocol prisma-check --help` shows the command; tests pass.

---

### Task 13: Write unit tests for E3
**Description:** Create comprehensive tests for `prisma_compliance()` scoring and the `prisma-check` CLI command.
**Files to Touch:**
- `tools/scholar-protocol-kit/tests/test_validate.py` (update)

### Execution Checklist
- [ ] Add `test_prisma_compliance_full_protocol` -- load `prisma_slr_full.json`, verify score >= 0.8
- [ ] Add `test_prisma_compliance_min_protocol` -- load `design_science_min.json`, verify score > 0
- [ ] Add `test_prisma_compliance_returns_all_sections` -- verify all 7 section keys present
- [ ] Add `test_prisma_compliance_results_are_todo` -- verify RESULTS items always `addressed=False`
- [ ] Add `test_prisma_compliance_discussion_are_todo` -- verify DISCUSSION items always `addressed=False`
- [ ] Add `test_prisma_compliance_score_range` -- verify 0.0 <= score <= 1.0
- [ ] Add `test_prisma_compliance_total_equals_sum` -- verify `total_items` matches sum of all section items
- [ ] Add `test_prisma_check_cli` -- CliRunner: invoke with valid fixture, assert exit 0
- [ ] Add `test_prisma_check_cli_json` -- CliRunner with `--json`, assert valid JSON output
- [ ] Add `test_prisma_check_cli_nonexistent` -- assert exit code 2

### Testing Strategy
- All hermetic: use existing fixtures from `tests/fixtures/valid/`, no network calls.
- Run: `uv run pytest tools/scholar-protocol-kit/tests/test_validate.py -v`

### Definition of Done (DoD)
- All new and existing validation tests pass; `uv run pytest tools/scholar-protocol-kit/tests/ -v` green.

---

## Feature E4: Monorepo Sync & Governance (1h)

### Task 14: Sync kit changes to external repos and regenerate pins [DEPENDS on Tasks 6, 10, 13]
**Description:** Push modified kit source to their canonical repos, bump `plugins.json` revs, and regenerate metapackage pins.
**Files to Touch:**
- `plugins.json` (via `scripts/push_tools.py`)
- `packaging/nexus-scholar/nexus_scholar_pins.json` (via `scripts/generate_nexus_scholar_pins.py`)

### Execution Checklist
- [ ] Run `python scripts/push_tools.py` to copy dirty tool dirs to their repos
- [ ] Run `python scripts/generate_nexus_scholar_pins.py --check` to verify freshness
- [ ] Run `python scripts/generate_nexus_scholar_pins.py` to regenerate pins if needed
- [ ] Run `uv run pytest tests/conformance/test_actions_cli_parity.py -v` to verify new CLI commands are registered

### Testing Strategy
- Conformance tests verify CLI parity between Typer app commands and the kit's declared actions.
- Pin freshness check: `--check` exits 0 if already fresh.

### Definition of Done (DoD)
- `scripts/push_tools.py` exits 0; pin freshness check passes; conformance tests green.

---

## Execution Order & Dependency Graph

```
E1 (Independent)          E2 (Independent)          E3 (Independent)
  T1 __init__ [I]           T7 to_mermaid() [I]       T11 prisma_compliance() [I]
  T2 helpers [I]            T8 to_plantuml() [I]      T12 prisma-check CLI [D: T11]
  T3 generate_html [D:T1,T2,T4]
  T4 CSS injection [I]      T9 prisma-diagram [D:T7,T8]
  T5 CLI command [I]        T10 E2 tests [D:T7,T8,T9]
  T6 E1 tests [D:T1-T5]                                 T13 E3 tests [D:T11,T12]
                                │
                                ▼
                          T14 Monorepo sync [D: T6,T10,T13]
```

**Parallelism window:** Tasks T1, T2, T5, T7, T8, T11 are all `[INDEPENDENT]` and can be executed in parallel across features. The critical path is:

```
T1/T2 -> T3 -> T4 -> T6 -> T14
T7/T8 -> T9 -> T10 -> T14
T11 -> T12 -> T13 -> T14
```

---

## Acceptance Criteria Summary

| Feature | Criterion | Measurement | Target |
|---------|-----------|-------------|--------|
| E1 | Visualization performance | Render 1000-node graph | < 5 seconds |
| E1 | Backward compat | Old `generate_html(G)` call | No error |
| E2 | Mermaid output | Render in Mermaid viewer | Valid syntax |
| E2 | PlantUML output | Render in PlantUML viewer | Valid syntax |
| E3 | Compliance score | Score valid PRISMA SLR protocol | >= 80% |
| E3 | CLI `--json` | Valid JSON with expected keys | Correct |
| All | No regressions | `uv run pytest -v` | 0 failures |

---

*Execution plan generated from Phase E spec v1.1.0 on 2026-09-17*