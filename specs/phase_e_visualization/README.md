# Phase E: Enhanced Visualization & PRISMA Diagrams

**Specification Version:** 1.1.0  
**Status:** READY FOR IMPLEMENTATION  
**Target System:** `scholar-graph-kit` (visualization), `scholar-search-kit` (PRISMA), `scholar-protocol-kit` (checklist)  
**Estimated Duration:** 2 days (Days 19–20)  
**Success Gates:** Interactive graph renders < 5s for 1000 nodes; PRISMA diagram consumes existing `PrismaFlowReport`; 0 regressions

---

## 1. Executive Summary

Phase E adds **community-aware graph coloring**, **Mermaid/PlantUML PRISMA diagrams**, and **PRISMA 2020 compliance scoring** as enhancements to existing code. Instead of creating parallel systems, this phase extends existing classes (`GraphVisualizer`, `PrismaFlowReport`, `validate_protocol`).

### 1.1 Features Overview

| # | Feature | Kit | Impact | Effort |
|---|---------|-----|--------|--------|
| E1 | Enhanced Graph Visualization | scholar-graph-kit | High | Low |
| E2 | PRISMA Flow Diagrams (Mermaid/PlantUML) | scholar-search-kit | Medium | Low |
| E3 | PRISMA 2020 Compliance Scoring | scholar-protocol-kit | Medium | Low |

> **Dropped: RIS/CSL-JSON Protocol Export.** RIS and CSL-JSON are citation metadata formats designed for individual publications, not research protocols. Phase A already specifies RIS/CSL-JSON export for `Document` objects (A1) and BibTeX entries (A2). Exporting a `ResearchProtocol` to these formats produces meaningless entries in reference managers.

### 1.2 Methodological Value

- **Community-Aware Visualization:** Color nodes by Louvain community (from Phase B3) for citation pattern discovery
- **PRISMA 2020 Compliance:** Automated checklist scoring leverages existing `validate_protocol()` infrastructure
- **Multi-Format Diagrams:** Mermaid and PlantUML output from existing `PrismaFlowReport` data

---

## 2. Feature Specifications

### 2.1 E1: Enhanced Graph Visualization

**Goal:** Enhance existing `GraphVisualizer` to support community-aware node coloring and configurable sizing.

#### 2.1.1 Design Rationale

`tools/scholar-graph-kit/src/scholar_graph/visualizer.py` already exists (59 lines) with a working `GraphVisualizer` class that:
- Takes `output_path` in constructor
- Has `generate_html(G)` method that uses PyVis with physics simulation
- Sizes nodes by citations (`data["value"] = citations + 5`)
- Has tooltips with DOI, title, year, citations

E1 **enhances** this class (does not replace it) to add:
- `node_color_attr` parameter for community coloring (uses B3's `community` attribute)
- `_compute_node_colors()` method with configurable palette
- `_inject_custom_css()` for better styling
- Backward-compatible API (existing `generate_html()` still works)

#### 2.1.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-graph-kit/src/scholar_graph/visualizer.py` | **ENHANCE** existing `GraphVisualizer` class |
| `tools/scholar-graph-kit/src/scholar_graph/cli.py` | Add `visualize` command for loading graph JSON |

> **No new files created.** E1 modifies existing files only.

#### 2.1.3 Implementation Details

```python
# tools/scholar-graph-kit/src/scholar_graph/visualizer.py
# ENHANCE the existing class (do NOT replace)
from __future__ import annotations
from typing import Any
from pathlib import Path

if __name__ != "__main__":
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        import networkx as nx


class GraphVisualizer:
    """Creates interactive HTML visualizations of citation networks.
    
    Enhanced version with community coloring and configurable sizing.
    Backward-compatible: existing generate_html(G) still works.
    """
    
    def __init__(
        self,
        output_path: str | Path,
        physics_enabled: bool = True,
        height: str = "800px",
        width: str = "100%",
        bgcolor: str = "#ffffff",
        font_color: str = "#333333",
    ):
        self.output_path = Path(output_path)
        self.physics_enabled = physics_enabled
        self.height = height
        self.width = width
        self.bgcolor = bgcolor
        self.font_color = font_color
    
    def generate_html(
        self,
        G: nx.DiGraph,
        node_size_attr: str = "citations",
        node_color_attr: str | None = None,
        title: str = "Citation Network",
    ) -> Path:
        """Generate an interactive HTML visualization using PyVis.
        
        Args:
            G: NetworkX directed graph
            node_size_attr: Node attribute for size scaling (default: "citations")
            node_color_attr: Node attribute for color mapping (None = default green)
            title: Visualization title
            
        Returns:
            Path to generated HTML file
        """
        from pyvis.network import Network  # Deferred (P7.7)
        
        # Compute node sizes and colors
        node_sizes = self._compute_node_sizes(G, node_size_attr)
        node_colors = self._compute_node_colors(G, node_color_attr) if node_color_attr else {}
        
        # Create PyVis network
        net = Network(
            height=self.height,
            width=self.width,
            bgcolor=self.bgcolor,
            font_color=self.font_color,
            directed=G.is_directed(),
        )
        
        # Configure physics
        if self.physics_enabled:
            net.toggle_physics(True)
            net.set_options("""
            {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08
                },
                "solver": "forceAtlas2Based",
                "stabilization": {
                  "enabled": true,
                  "iterations": 1000
                }
              }
            }
            """)
        else:
            net.toggle_physics(False)
        
        # Add nodes with sizing, coloring, and tooltips
        for node, data in G.nodes(data=True):
            size = node_sizes.get(node, 15)
            color = node_colors.get(node, "#4CAF50")
            tooltip = self._build_tooltip(node, data)
            
            net.add_node(
                node,
                label=data.get("title", str(node))[:30],
                title=tooltip,
                size=size,
                color=color,
            )
        
        # Add edges
        for u, v, data in G.edges(data=True):
            weight = data.get("weight", 1.0)
            net.add_edge(
                u, v,
                width=weight * 2,
                title=f"Weight: {weight:.2f}",
            )
        
        # Add title
        net.set_title(title)
        
        # Save HTML
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(str(self.output_path))
        
        # Inject custom CSS for better styling
        self._inject_custom_css(self.output_path)
        
        return self.output_path
    
    def _compute_node_sizes(
        self,
        G: nx.DiGraph,
        attr: str,
        min_size: int = 10,
        max_size: int = 30,
    ) -> dict[str, int]:
        """Compute node sizes based on attribute (normalized to min/max range)."""
        values = [G.nodes[n].get(attr, 0) for n in G.nodes()]
        
        if not values or max(values) == min(values):
            return {n: (min_size + max_size) // 2 for n in G.nodes()}
        
        min_val = min(values)
        max_val = max(values)
        
        return {
            n: int(min_size + ((G.nodes[n].get(attr, 0) - min_val) / (max_val - min_val)) * (max_size - min_size))
            for n in G.nodes()
        }
    
    def _compute_node_colors(
        self,
        G: nx.DiGraph,
        attr: str,
    ) -> dict[str, str]:
        """Compute node colors based on attribute (e.g. community from B3)."""
        palette = [
            "#4CAF50", "#2196F3", "#FF9800", "#E91E63",
            "#9C27B0", "#00BCD4", "#FF5722", "#607D8B",
            "#8BC34A", "#3F51B5", "#FFC107", "#795548",
            "#CDDC39", "#009688", "#FFEB3B", "#9E9E9E",
            "#F44336", "#03A9F4", "#827717", "#5D4037"
        ]
        
        values = [G.nodes[n].get(attr, 0) for n in G.nodes()]
        unique_values = list(set(values))
        
        return {
            n: palette[unique_values.index(G.nodes[n].get(attr, 0)) % len(palette)]
            for n in G.nodes()
        }
    
    def _build_tooltip(self, node: str, attrs: dict[str, Any]) -> str:
        """Build HTML tooltip for node."""
        lines = [f"<b>{attrs.get('title', node)}</b>"]
        for key in ["year", "citations", "doi", "community", "pagerank"]:
            if key in attrs:
                lines.append(f"{key.title()}: {attrs[key]}")
        return "<br>".join(lines)
    
    def _inject_custom_css(self, html_path: Path) -> None:
        """Inject custom CSS into HTML file for better styling."""
        content = html_path.read_text(encoding="utf-8")
        custom_css = """
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            #mynetwork { width: 100%; height: 100vh; }
        </style>
        """
        if "</head>" in content:
            content = content.replace("</head>", custom_css + "</head>")
            html_path.write_text(content, encoding="utf-8")
```

#### 2.1.4 CLI Integration

```python
# tools/scholar-graph-kit/src/scholar_graph/cli.py
# ADD new command after existing build/pagerank commands

@app.command("visualize")
def visualize_cmd(
    graph_file: Path = typer.Argument(..., help="Path to graph JSON file (from build --json-output)"),
    output: Path = typer.Option("graph.html", "--output", "-o", help="Output HTML file"),
    title: str = typer.Option("Citation Network", "--title", "-t", help="Visualization title"),
    physics: bool = typer.Option(True, "--physics/--no-physics", help="Enable physics simulation"),
    node_size: str = typer.Option("citations", "--node-size", help="Node attribute for size"),
    node_color: str = typer.Option(None, "--node-color", help="Node attribute for color (e.g. community)"),
):
    """Create interactive HTML visualization from a graph JSON file."""
    import networkx as nx  # Deferred (P7.7)
    
    data = json.loads(graph_file.read_text(encoding="utf-8"))
    G = nx.node_link_graph(data)
    
    vis = GraphVisualizer(output, physics_enabled=physics)
    result_path = vis.generate_html(
        G,
        node_size_attr=node_size,
        node_color_attr=node_color,
        title=title,
    )
    
    console.print(f"[green]Visualization saved to {result_path}[/green]")
    console.print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
```

#### 2.1.5 Integration Points

| Existing Code | Location | How E1 Uses It |
|---------------|----------|----------------|
| `GraphVisualizer.__init__(output_path)` | `visualizer.py:10` | Preserved for backward compatibility |
| `GraphVisualizer.generate_html(G)` | `visualizer.py:13` | Enhanced with optional `node_color_attr` |
| `build` CLI command | `cli.py:29-91` | Continues to work unchanged |
| B3 `enrich_graph_with_communities()` | (Phase B3) | Sets `community` attribute for E1's coloring |

---

### 2.2 E2: PRISMA Flow Diagrams (Mermaid/PlantUML)

**Goal:** Add `to_mermaid()` and `to_plantuml()` methods to existing `PrismaFlowReport` for multi-format PRISMA diagrams.

#### 2.2.1 Design Rationale

`tools/scholar-search-kit/src/scholar_search/screening.py` already has `PrismaFlowReport` (lines 31-73) with `to_markdown()`. The `nexus_screen` MCP tool already outputs `prisma_screening_report.md`.

E2 **extends** this class (does not create a new one) to add:
- `to_mermaid()` method for Mermaid diagram output
- `to_plantuml()` method for PlantUML diagram output
- CLI command `prisma-diagram` in `scholar-search-kit` to generate diagrams from `prisma_report.json`

#### 2.2.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-search-kit/src/scholar_search/screening.py` | **ADD** `to_mermaid()` and `to_plantuml()` to existing `PrismaFlowReport` |
| `tools/scholar-search-kit/src/scholar_search/cli.py` | Add `prisma-diagram` command |

> **No new files created.** E2 modifies existing files only.

#### 2.2.3 Implementation Details

```python
# ADD TO: tools/scholar-search-kit/src/scholar_search/screening.py
# After the existing PrismaFlowReport.to_markdown() method (around line 73)

class PrismaFlowReport:
    # ... existing fields and to_markdown() ...
    
    def to_mermaid(self) -> str:
        """Generate PRISMA 2020 flow diagram in Mermaid format."""
        lines = ["```mermaid", "graph TD", ""]
        
        # Nodes
        lines.append(f'    A["Records identified<br>(n={self.total_identified})"]')
        lines.append(f'    B["Records screened<br>(n={self.records_screened})"]')
        lines.append(f'    C["Records excluded<br>(n={self.records_excluded})"]')
        lines.append(f'    D["Full-text assessed<br>(n={self.records_included})"]')
        lines.append(f'    E["Studies included<br>(n={self.records_included})"]')
        
        lines.append("")
        lines.append("    A --> B")
        lines.append("    B --> C")
        lines.append("    B --> D")
        lines.append("    D --> E")
        
        # Exclusion reasons
        if self.exclusion_reasons_breakdown:
            lines.append("")
            for i, (reason, count) in enumerate(self.exclusion_reasons_breakdown.items(), 1):
                node_id = f"EX{i}"
                lines.append(f'    {node_id}["{reason}<br>(n={count})"]')
                lines.append(f"    C --> {node_id}")
        
        lines.append("```")
        return "\n".join(lines)
    
    def to_plantuml(self) -> str:
        """Generate PRISMA 2020 flow diagram in PlantUML format."""
        lines = ["@startuml", "", "start"]
        
        lines.append(f":Records identified (n={self.total_identified});")
        lines.append(f":Records screened (n={self.records_screened});")
        
        lines.append("if (Any excluded?) then (yes)")
        lines.append(f"  :Records excluded (n={self.records_excluded});")
        
        if self.exclusion_reasons_breakdown:
            notes = [f"{r} (n={c})" for r, c in self.exclusion_reasons_breakdown.items()]
            notes_str = "\\n".join(notes)
            lines.append(f"  note right: {notes_str}")
        
        lines.append("else (no)")
        lines.append(f"  :Studies included (n={self.records_included});")
        lines.append("endif")
        
        lines.append("stop", "@enduml")
        return "\n".join(lines)
```

#### 2.2.4 CLI Integration

```python
# tools/scholar-search-kit/src/scholar_search/cli.py
# ADD new command

@app.command("prisma-diagram")
def prisma_diagram(
    prisma_report: Path = typer.Argument(..., help="Path to prisma_report.json"),
    format: str = typer.Option("mermaid", "--format", "-f", help="Diagram format: mermaid, plantuml"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
):
    """Generate PRISMA flow diagram from screening report."""
    import json
    
    data = json.loads(prisma_report.read_text(encoding="utf-8"))
    
    report = PrismaFlowReport(
        total_identified=data.get("total_identified", 0),
        duplicates_removed=data.get("duplicates_removed", 0),
        records_screened=data.get("records_screened", 0),
        records_excluded=data.get("records_excluded", 0),
        records_included=data.get("records_included", 0),
        conflicts_flagged=data.get("conflicts_flagged", 0),
        exclusion_reasons_breakdown=data.get("exclusion_reasons_breakdown", {}),
    )
    
    if format == "mermaid":
        diagram = report.to_mermaid()
        suffix = ".mermaid.md"
    elif format == "plantuml":
        diagram = report.to_plantuml()
        suffix = ".puml"
    else:
        raise typer.BadParameter(f"Unknown format: {format}. Options: mermaid, plantuml")
    
    if output:
        output.write_text(diagram, encoding="utf-8")
        typer.echo(f"PRISMA diagram saved to {output}")
    else:
        typer.echo(diagram)
```

#### 2.2.5 Data Flow

```
D1 (nexus_screen_llm) or nexus_screen
    ↓
partition_screening_results()
    ↓
PrismaFlowReport (with total_identified, records_screened, etc.)
    ↓
prisma_report.json (written by nexus_screen/nexus_screen_llm)
    ↓
E2 (prisma-diagram command)
    ↓
Mermaid or PlantUML output
```

#### 2.2.6 Integration Points

| Existing Code | Location | How E2 Uses It |
|---------------|----------|----------------|
| `PrismaFlowReport` dataclass | `screening.py:31-73` | Extended with `to_mermaid()` and `to_plantuml()` |
| `partition_screening_results()` | `screening.py:343-408` | Produces `PrismaFlowReport` from screening decisions |
| `nexus_screen` MCP tool | `server.py:319-355` | Already writes `prisma_report.json` |

---

### 2.3 E3: PRISMA 2020 Compliance Scoring

**Goal:** Add PRISMA 2020 compliance scoring to existing `validate_protocol()` infrastructure.

#### 2.3.1 Design Rationale

`tools/scholar-protocol-kit/src/scholar_protocol/validate.py` already validates protocols against the `ResearchProtocol` schema. E3 extends this to produce a PRISMA 2020 compliance checklist, leveraging the existing validation infrastructure rather than creating a parallel system.

#### 2.3.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-protocol-kit/src/scholar_protocol/validate.py` | **ADD** `prisma_compliance()` function |
| `tools/scholar-protocol-kit/src/scholar_protocol/cli.py` | Add `prisma-check` command |

> **No new files created.** E3 modifies existing files only.

#### 2.3.3 Implementation Details

```python
# ADD TO: tools/scholar-protocol-kit/src/scholar_protocol/validate.py
# After the existing validate_protocol() function

# PRISMA 2020 checklist mapping: section → list of (item_id, check_function)
# All check functions accept a ResearchProtocol instance and return bool
_PRISMA_CHECKS = {
    "TITLE": [
        ("1.1", lambda p: bool(p.metadata.get("title")), "Identify as systematic review"),
        ("1.2", lambda p: bool(p.research_questions), "State research questions"),
    ],
    "ABSTRACT": [
        ("2.1", lambda p: bool(p.metadata.get("title")), "Structured summary"),
    ],
    "INTRODUCTION": [
        ("3.1", lambda p: bool(p.epistemology.epistemological_rationale), "Rationale"),
        ("3.2", lambda p: bool(p.research_questions), "Objectives"),
    ],
    "METHODS": [
        ("4.1", lambda p: bool(p.screening_criteria), "Eligibility criteria"),
        ("4.2", lambda p: bool(p.search_strategy.target_databases), "Information sources"),
        ("4.3", lambda p: bool(p.search_strategy.core_concepts), "Search strategy"),
        ("4.4", lambda p: bool(p.screening_criteria), "Selection process"),
        ("4.5", lambda p: bool(p.matrix_dimensions), "Data collection process"),
        ("4.6", lambda p: bool(p.matrix_dimensions), "Data items"),
        ("4.7", lambda p: p.verification.retraction_check_required or p.verification.coi_and_funding_audit_required, "Risk of bias assessment"),
        ("4.8", lambda p: bool(p.research_questions), "Synthesis methods"),
    ],
    "RESULTS": [
        ("5.1", lambda p: False, "TODO: Study selection (requires execution state)"),
        ("5.2", lambda p: False, "TODO: Study characteristics (requires execution state)"),
        ("5.3", lambda p: False, "TODO: Risk of bias results (requires execution state)"),
        ("5.4", lambda p: False, "TODO: Synthesis results (requires execution state)"),
    ],
    "DISCUSSION": [
        ("6.1", lambda p: False, "TODO: Limitations (requires synthesis state)"),
        ("6.2", lambda p: False, "TODO: Interpretation (requires synthesis state)"),
    ],
    "OTHER": [
        ("7.1", lambda p: bool(p.metadata.get("funding")), "Funding"),
    ],
}


def prisma_compliance(protocol: ResearchProtocol) -> dict[str, Any]:
    """Score PRISMA 2020 compliance for a protocol.
    
    Returns a dict with:
    - total_items: int
    - addressed_items: int
    - compliance_score: float (0.0-1.0)
    - sections: dict mapping section → list of {id, description, addressed, notes}
    """
    sections = {}
    total = 0
    addressed = 0
    
    for section, checks in _PRISMA_CHECKS.items():
        items = []
        for item_id, check_fn, description in checks:
            is_addressed = check_fn(protocol)
            items.append({
                "id": item_id,
                "description": description,
                "addressed": is_addressed,
                "notes": "" if is_addressed else "Not addressed in protocol",
            })
            total += 1
            if is_addressed:
                addressed += 1
        sections[section] = items
    
    return {
        "total_items": total,
        "addressed_items": addressed,
        "compliance_score": addressed / total if total > 0 else 0.0,
        "sections": sections,
    }
```

#### 2.3.4 CLI Integration

```python
# tools/scholar-protocol-kit/src/scholar_protocol/cli.py
# ADD new command

@app.command("prisma-check")
def prisma_check(
    path: pathlib.Path = typer.Argument(..., help="Path to protocol.json"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Score PRISMA 2020 compliance for a protocol."""
    from scholar_protocol.validate import prisma_compliance
    
    protocol = _load_protocol(path)
    result = prisma_compliance(protocol)
    
    if output_json:
        print(json.dumps(result, indent=2))
    else:
        score_pct = result["compliance_score"] * 100
        console.print(f"\n[bold]PRISMA 2020 Compliance: {score_pct:.0f}%[/bold]")
        console.print(f"  Addressed: {result['addressed_items']}/{result['total_items']} items\n")
        
        for section, items in result["sections"].items():
            section_score = sum(1 for i in items if i["addressed"])
            console.print(f"[bold]{section}[/bold] ({section_score}/{len(items)})")
            for item in items:
                status = "[green]✓[/green]" if item["addressed"] else "[red]✗[/red]"
                console.print(f"  {status} {item['id']}: {item['description']}")
```

#### 2.3.5 Integration Points

| Existing Code | Location | How E3 Uses It |
|---------------|----------|----------------|
| `validate_protocol()` | `validate.py` | E3 extends validation with PRISMA scoring |
| `ResearchProtocol` model | `models.py` | E3 reads typed fields, not raw dicts |
| `_load_protocol()` | `cli.py:79-86` | E3 uses existing pattern for loading |

---

## 3. Testing Strategy

### 3.1 Testing Principles

1. **Hermetic Tests:** No network calls, no real API invocations
2. **Isolated Workspaces:** Use `tmp_path` fixture for all file I/O
3. **Reuse Existing Fixtures:** Use existing test infrastructure
4. **Backward Compatibility:** Verify existing `generate_html()` still works

### 3.2 Test Categories

#### 3.2.1 Unit Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| E1: Enhanced visualization | `tools/scholar-graph-kit/tests/test_visualizer.py` | Backward compat, community coloring, sizing |
| E2: Mermaid/PlantUML | `tools/scholar-search-kit/tests/test_screening.py` | `to_mermaid()`, `to_plantuml()` output validity |
| E3: PRISMA scoring | `tools/scholar-protocol-kit/tests/test_validate.py` | `prisma_compliance()` scoring, section mapping |

### 3.3 Test Fixtures

```python
# Reuse existing fixtures from each kit's test infrastructure
# E1: sample_graph from existing graph tests
# E2: PrismaFlowReport with known values
# E3: ResearchProtocol fixture from existing validation tests
```

### 3.4 Test Execution Commands

```bash
# Run E1 tests
uv run pytest tools/scholar-graph-kit/tests/ -v

# Run E2 tests
uv run pytest tools/scholar-search-kit/tests/ -k "prisma" -v

# Run E3 tests
uv run pytest tools/scholar-protocol-kit/tests/ -v

# Run all tests
uv run pytest -v
```

---

## 4. Task List

### 4.1 Feature E1: Enhanced Graph Visualization

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| E1.1 | Enhance `GraphVisualizer` with community coloring | None | 1 |
| E1.2 | Add `_compute_node_colors()` and `_compute_node_sizes()` | E1.1 | 0.5 |
| E1.3 | Add `_inject_custom_css()` | E1.1 | 0.5 |
| E1.4 | Add `visualize` CLI command | E1.1 | 0.5 |
| E1.5 | Write unit tests (backward compat, coloring) | E1.1, E1.2, E1.3 | 1 |
| **Total** | | | **3.5** |

### 4.2 Feature E2: PRISMA Flow Diagrams

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| E2.1 | Add `to_mermaid()` to `PrismaFlowReport` | None | 1 |
| E2.2 | Add `to_plantuml()` to `PrismaFlowReport` | None | 0.5 |
| E2.3 | Add `prisma-diagram` CLI command | E2.1, E2.2 | 0.5 |
| E2.4 | Write unit tests for diagrams | E2.1, E2.2 | 1 |
| **Total** | | | **3** |

### 4.3 Feature E3: PRISMA 2020 Compliance Scoring

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| E3.1 | Add `prisma_compliance()` to `validate.py` | None | 1 |
| E3.2 | Add `prisma-check` CLI command | E3.1 | 0.5 |
| E3.3 | Write unit tests for compliance scoring | E3.1 | 1 |
| **Total** | | | **2.5** |

### 4.4 Total Estimated Effort

| Feature | Hours |
|---------|-------|
| E1: Enhanced Graph Visualization | 3.5 |
| E2: PRISMA Flow Diagrams | 3 |
| E3: PRISMA 2020 Compliance Scoring | 2.5 |
| E4: Monorepo Sync (post-implementation) | 1 |
| **Total** | **10** |

---

## 4.5 Monorepo Governance (Post-Implementation)

> **CRITICAL:** Per AGENTS.md, changes to kit files must be synced to external repos.

### 4.5.1 Kit Sync Requirements

```bash
# Sync kit changes to external repos
python scripts/push_tools.py

# Regenerate metapackage pins
python scripts/generate_nexus_scholar_pins.py --check
python scripts/generate_nexus_scholar_pins.py
```

### 4.5.2 Conformance Test Updates

New CLI commands (`visualize`, `prisma-diagram`, `prisma-check`) must be registered in their respective Typer apps:

```bash
uv run pytest tests/conformance/test_actions_cli_parity.py -v
```

### 4.5.3 Skill Updates

- `.agents/skills/scholar-graph-kit/SKILL.md` - Add community-aware visualization docs
- `.agents/skills/scholar-search-kit/SKILL.md` - Add PRISMA diagram docs
- `.agents/skills/scholar-protocol-kit/SKILL.md` - Add PRISMA compliance scoring docs

---

## 5. Definition of Done (DoD)

### 5.1 Feature-Level DoD

For each feature to be considered complete:

- [ ] **Code Complete:** All implementation tasks finished
- [ ] **Tests Passing:** All unit and integration tests pass (`uv run pytest`)
- [ ] **Code Coverage:** New code has ≥90% test coverage
- [ ] **Lint Clean:** `uv run ruff check scripts/` passes (CI scope)
- [ ] **Type Clean:** No type errors in new code
- [ ] **Documentation:** Docstrings for all public functions/classes
- [ ] **Backward Compatible:** No breaking changes to existing APIs

### 5.2 Feature-Specific DoD

#### E1: Enhanced Graph Visualization
- [ ] Existing `generate_html(G)` still works unchanged
- [ ] Community coloring works when `node_color_attr="community"` is passed
- [ ] `visualize` CLI command loads graph JSON and renders HTML
- [ ] Physics simulation uses existing defaults (not changed)

#### E2: PRISMA Flow Diagrams
- [ ] `to_mermaid()` produces valid Mermaid syntax
- [ ] `to_plantuml()` produces valid PlantUML syntax
- [ ] `prisma-diagram` CLI command works with `prisma_report.json`
- [ ] Existing `to_markdown()` still works unchanged

#### E3: PRISMA 2020 Compliance Scoring
- [ ] `prisma_compliance()` returns correct score for valid protocol
- [ ] `prisma-check` CLI command shows checklist with ✓/✗
- [ ] JSON output mode works
- [ ] Uses `ResearchProtocol` model fields (not raw dicts)

### 5.3 Phase-Level DoD

For Phase E to be considered complete:

- [ ] All 3 features implemented and tested
- [ ] All feature-specific DoD criteria met
- [ ] All unit tests pass: `uv run pytest -v`
- [ ] No regressions in existing functionality
- [ ] Monorepo sync completed (kit repos updated, pins regenerated)

### 5.4 Acceptance Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| Visualization Performance | Render 1000-node graph | < 5 seconds |
| Mermaid Diagram | Render in Mermaid viewer | 100% correct |
| PlantUML Diagram | Render in PlantUML viewer | 100% correct |
| PRISMA Compliance | Score valid protocol | ≥ 80% |
| No Regressions | Existing test suite | 0 failures |

---

## 6. Dependencies & Constraints

### 6.1 External Dependencies

| Dependency | Version | Used By | Notes |
|------------|---------|---------|-------|
| `pyvis` | >=0.3.0 | E1 | Already a dependency of `scholar-graph-kit` |

### 6.2 Internal Dependencies

| Dependency | Kit | Location | Notes |
|------------|-----|----------|-------|
| `GraphVisualizer` | scholar-graph-kit | `visualizer.py` | E1 enhances this class |
| `PrismaFlowReport` | scholar-search-kit | `screening.py:31-73` | E2 adds methods to this class |
| `validate_protocol()` | scholar-protocol-kit | `validate.py` | E3 extends with PRISMA scoring |
| `ResearchProtocol` | scholar-protocol-kit | `models.py` | E3 uses typed model fields |
| B3 community detection | scholar-graph-kit | (Phase B3) | E1 uses `community` attribute for coloring |
| D1 screening output | scholar-search-kit | (Phase D1) | E2 consumes `prisma_report.json` from D1 |

### 6.3 Constraints

1. **No breaking changes:** All existing APIs must remain backward compatible
2. **P7.7 lazy imports:** All heavy dependencies must remain deferred inside function/method bodies
3. **Windows compatibility:** All file paths must handle Windows path separators
4. **UTF-8 encoding:** All file I/O must use UTF-8 encoding
5. **No network in tests:** All tests must be hermetic

---

## 7. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PyVis performance on large graphs | Low | Medium | Physics simulation handles large graphs |
| Mermaid syntax variations | Low | Low | Test with official Mermaid renderer |
| PRISMA checklist completeness | Medium | Medium | Leverage existing `validate_protocol()` |

---

## 8. Changes from v1.0.0

| Change | Reason |
|--------|--------|
| Dropped RIS/CSL-JSON Protocol Export | RIS/CSL-JSON are citation formats, not research plan formats. Phase A already covers RIS/CSL-JSON for papers/bibliography. |
| E1 enhanced instead of recreated | `visualizer.py` already exists (59 lines). E1 adds community coloring, not a new class. |
| E2 moved to `scholar-search-kit` | `PrismaFlowReport` already lives in `screening.py`. E2 adds methods there, not in `scholar-protocol-kit`. |
| E3 leverages existing validation | `validate_protocol()` already validates protocols. E3 adds PRISMA scoring, not a new module. |
| Updated effort from 20.5h to 10h | ~50% reduction by reusing existing code instead of reimplementing. |
| Added cross-phase dependencies | E1 depends on B3 (community), E2 depends on D1 (screening stats). |

---

*Specification created by opencode (mimo-v2.5-free) on 2026-09-15*
*Source: Phase E requirements from ecosystem analysis documents*
*Post-review v1.1.0: 2-agent review found E1/E2/E3 all BLOCKED due to existing code overwriting, format misuse, and parallel systems. Rewrote to enhance existing classes and extend existing validation infrastructure.*
