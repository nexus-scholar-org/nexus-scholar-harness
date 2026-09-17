# Inter-Phase Data Contract

**Version:** 1.0.0  
**Created:** 2026-09-15  
**Purpose:** Define the data models, schemas, and flow contracts between all phases (A–E) to prevent drift and ensure cohesive system behavior.

---

## 1. Shared Data Models

These are the canonical data types that flow between phases. All phases MUST use these exact types.

### 1.1 `Document` (scholar-search-kit)

```python
@dataclass
class Document:
    workspace_id: str | None = None
    title: str | None = None
    abstract: str | None = None
    authors: list[Author] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    citations_count: int | None = None
    external_ids: ExternalIds = field(default_factory=ExternalIds)
    url: str | None = None
    provider: str = "unknown"
    provider_id: str | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    is_retracted: bool = False

@dataclass
class ExternalIds:
    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    openalex_id: str | None = None
    s2_id: str | None = None

@dataclass
class Author:
    given_name: str = ""
    family_name: str = ""
    orcid: str | None = None
    affiliation: str | None = None
```

**Used by:** A1 (RIS export), A3 (completeness scoring), A4 (abstract backfilling), B4 (screen-compare), B5 (golden seed), C2 (extraction)

### 1.2 `ScreeningDecision` (scholar-search-kit)

```python
@dataclass
class ScreeningDecision:
    workspace_id: str
    decision: Literal["INCLUDE", "EXCLUDE"]  # NO UNCERTAIN STATE
    confidence: float
    screening_reasoning: str
    matched_inclusion_criteria: list[str] = field(default_factory=list)
    violated_exclusion_criteria: list[str] = field(default_factory=list)
    relevant_rqs: list[str] = field(default_factory=list)
    document_title: str = ""
    doi: str | None = None
```

**Used by:** B4 (screen-compare), D1 (LLM screening), E2 (PRISMA diagrams)

### 1.3 `PrismaFlowReport` (scholar-search-kit)

```python
@dataclass
class PrismaFlowReport:
    total_identified: int
    duplicates_removed: int
    records_screened: int
    records_excluded: int
    records_included: int
    conflicts_flagged: int
    exclusion_reasons_breakdown: dict[str, int] = field(default_factory=dict)
    
    def to_markdown(self) -> str: ...
    def to_mermaid(self) -> str: ...  # Added by Phase E2
    def to_plantuml(self) -> str: ...  # Added by Phase E2
```

**Used by:** E2 (PRISMA diagrams)

### 1.4 `ResearchProtocol` (scholar-protocol-kit)

```python
class ResearchProtocol(BaseModel):
    protocol_id: str
    created_at: str
    project_slug: str
    playbook_type: PlaybookType
    metadata: Dict[str, Any]  # {"title": ..., "lead_researcher": ..., "funding": ...}
    epistemology: EpistemologyConfig  # {"epistemological_rationale": ..., "primary_paradigm": ...}
    research_questions: List[ResearchQuestion]  # [{"id": "RQ1", "text": "..."}]
    search_strategy: SearchStrategy
    screening_criteria: ScreeningCriteria
    matrix_dimensions: List[MatrixDimension]
    verification: VerificationConfig
```

**Used by:** E3 (PRISMA compliance scoring)

### 1.5 `SearchStrategy` (scholar-protocol-kit)

```python
class SearchStrategy(BaseModel):
    core_concepts: List[ConceptCluster]  # [{"concept": "...", "synonyms": [...]}]
    target_databases: List[str]
    date_range: Dict[str, Optional[int]]
    languages: List[str]
    open_access_preferred: bool
    target_candidate_pool_size: Dict[str, int]
    golden_seeds: list[str] = []  # Added by Phase B5
```

**Used by:** B5 (golden seed validation)

### 1.6 `DocumentCluster` (scholar-search-kit)

```python
@dataclass
class DocumentCluster:
    cluster_id: str
    representative: Document  # Elected by completeness score
    members: list[Document] = field(default_factory=list)  # NOT "duplicates"
    merge_confidence: float = 0.0
```

**Used by:** A1 (RIS export), A3 (completeness scoring)

### 1.7 `ScreeningComparisonReport` (scholar-search-kit)

```python
@dataclass
class ScreeningComparisonReport:
    total_compared: int
    agreement_count: int
    agreement_rate: float
    transition_matrix: dict[str, dict[str, int]]  # {"INCLUDE": {"EXCLUDE": 3, "INCLUDE": 42}}
    discrepancies: list[dict[str, Any]]
    regression_count: int  # INCLUDE -> EXCLUDE
    progression_count: int  # EXCLUDE -> INCLUDE
```

**Used by:** B4 (screen-compare)

### 1.8 `CalibrationReport` (scholar-agent-kit)

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

**Used by:** D1 (LLM screening calibration)

---

## 2. Phase Output Contracts

What each phase PRODUCES that other phases may consume.

### Phase A Outputs

| Output | Type | Consumed By | Format |
|--------|------|-------------|--------|
| A1: RIS file | `Path` | External (Rayyan, Covidence) | Tagged RIS text |
| A2: CSL-JSON file | `Path` | External (Zotero, Pandoc) | CSL-JSON |
| A3: Completeness score | `int` (0-10) | A4 (triggers backfill) | Integer |
| A3: `DocumentCluster` with elected representative | `DocumentCluster` | A1 (RIS export) | Dataclass |
| A4: Enriched `Document` with backfilled abstract | `Document` | D1 (LLM screening) | Dataclass |
| A5: GEXF file | `Path` | External (Gephi, yEd) | GEXF XML |
| A5: GraphML file | `Path` | External (yEd) | GraphML XML |

### Phase B Outputs

| Output | Type | Consumed By | Format |
|--------|------|-------------|--------|
| B1: HITS scores | `dict[str, float]` (hubs, authorities) | B2, E1 (enrichment) | Dict |
| B2: Co-citation/coupling edges | `nx.DiGraph` edges | E1 (visualization) | NetworkX |
| B3: Community assignments | `G.nodes[node]["community"]` attribute | E1 (node coloring) | Int attribute |
| B3: `community` + `group` attributes | `int` on graph nodes | E1 (coloring) | NetworkX node attrs |
| B4: `ScreeningComparisonReport` | `ScreeningComparisonReport` | D1 (comparison) | Dataclass |
| B5: Golden seed validation result | `dict` with recall metrics | D1 (search validation) | Dict |

### Phase C Outputs

| Output | Type | Consumed By | Format |
|--------|------|-------------|--------|
| C1: Indexed ChromaDB | `Path` (db directory) | C2, D2 (retrieval) | ChromaDB |
| C2: Extracted `MethodologyMetadata` | `MethodologyMetadata` | D2 (pipeline) | Pydantic model |
| C2: PII-redacted content | `dict` | - | Dict |
| C3: Gemini embeddings | `list[list[float]]` | C1 (indexing) | List |

### Phase D Outputs

| Output | Type | Consumed By | Format |
|--------|------|-------------|--------|
| D1: `ScreeningDecision` list | `list[ScreeningDecision]` | E2 (PRISMA diagrams) | Dataclass list |
| D1: `prisma_report.json` | `Path` | E2 (diagram generation) | JSON file |
| D1: `included.json` | `Path` | D2, E2 | JSON file |
| D1: `excluded.json` | `Path` | E2 | JSON file |
| D1: `conflicts.json` | `Path` | E2 | JSON file |
| D2: Pipeline execution result | `dict` with stage completion | - | Dict |

### Phase E Outputs

| Output | Type | Consumed By | Format |
|--------|------|-------------|--------|
| E1: Interactive HTML | `Path` | External (browser) | HTML |
| E2: Mermaid diagram | `str` | External (renderers) | Mermaid syntax |
| E2: PlantUML diagram | `str` | External (renderers) | PlantUML syntax |
| E3: PRISMA compliance score | `dict` with score and checklist | External (reporting) | Dict |

---

## 3. Phase Input Contracts

What each phase CONSUMES from other phases or external sources.

### Phase A Inputs

| Input | Source | Type | Required? |
|-------|--------|------|-----------|
| Documents for export | `nexus_discover` or `nexus_screen` | `list[Document]` | Yes |
| Graph for GEXF/GraphML | `nexus_graph_build` | `nx.DiGraph` | Yes |
| BibTeX entries | `nexus_bib_clean` | `list[Entry]` | Yes (A2) |

### Phase B Inputs

| Input | Source | Type | Required? |
|-------|--------|------|-----------|
| Citation graph | `nexus_graph_build` | `nx.DiGraph` | Yes (B1-B3) |
| Screening decisions (Run A) | `nexus_screen` or D1 | `list[ScreeningDecision]` | Yes (B4) |
| Screening decisions (Run B) | `nexus_screen` or D1 | `list[ScreeningDecision]` | Yes (B4) |
| Protocol with `golden_seeds` | `nexus_protocol_compile` | `ResearchProtocol` | Yes (B5) |
| Search results for seed validation | `nexus_discover` | `list[Document]` | Yes (B5) |

### Phase C Inputs

| Input | Source | Type | Required? |
|-------|--------|------|-----------|
| Markdown documents | A4 (abstract backfill), PDF extraction | `Path` (directory) | Yes (C1) |
| BibTeX metadata | `nexus_bib_clean` | `Path` | No (C1) |
| Documents for extraction | A4 (enriched documents) | `list[Document]` | Yes (C2) |
| Gemini API key | Environment variable | `str` | Yes (C2, C3) |

### Phase D Inputs

| Input | Source | Type | Required? |
|-------|--------|------|-----------|
| Papers JSON | `nexus_discover`, `nexus_dedup` | `Path` | Yes (D1) |
| Protocol JSON | `nexus_protocol_compile` | `Path` | Yes (D1) |
| Gemini API key | Environment variable | `str` | Yes (D1) |
| Workspace directory | User-provided | `Path` | Yes (D2) |

### Phase E Inputs

| Input | Source | Type | Required? |
|-------|--------|------|-----------|
| Graph JSON | `nexus_graph_build` (B1-B3 enriched) | `Path` | Yes (E1) |
| `community` attribute on nodes | B3 (Louvain) | `int` | No (E1, default green) |
| `prisma_report.json` | D1 (`nexus_screen_llm`) or `nexus_screen` | `Path` | Yes (E2) |
| Protocol JSON | `nexus_protocol_compile` | `Path` | Yes (E3) |

---

## 4. Data Flow Diagrams

### 4.1 Primary Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL INPUT                           │
│                    (User query, protocol)                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE A: INTEROP                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ A1: RIS  │  │ A2: CSL  │  │ A3: Score│  │ A4: Back │        │
│  │ Export   │  │ Export   │  │ (0-10)   │  │ fill     │        │
│  └──────────┘  └──────────┘  └────┬─────┘  └────┬─────┘        │
│                                   │              │               │
│                                   ▼              ▼               │
│                            Score triggers    Enriched            │
│                            backfill if <8    Documents           │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE B: SCIENTOMETRICS                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ B1: HITS │  │ B2: CoCit│  │ B3: Comm │  │ B4: Comp │        │
│  │          │  │          │  │ Detect   │  │ are      │        │
│  └──────────┘  └──────────┘  └────┬─────┘  └──────────┘        │
│                                   │                              │
│                                   ▼                              │
│                            G.nodes["community"]                  │
│                            attribute set                         │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE C: RAG                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ C1: Chrom│  │ C2: Extr │  │ C3: Emb  │                      │
│  │ aDB      │  │ act      │  │ ed       │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE D: AGENT                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐     │
│  │ D1: LLM Screening       │  │ D2: Pipeline             │     │
│  │ (nexus_screen_llm)      │  │ (nexus_pipeline_run)     │     │
│  └────────────┬─────────────┘  └──────────────────────────┘     │
│               │                                                  │
│               ▼                                                  │
│        prisma_report.json                                        │
│        included.json                                             │
│        excluded.json                                             │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE E: VISUALIZATION                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ E1: Graph│  │ E2: PRIS │  │ E3: PRIS │                      │
│  │ Visual   │  │ MA Diagr │  │ MA Score │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Key Data Flow Chains

#### Chain 1: Screening → PRISMA Diagram
```
D1 (nexus_screen_llm)
  ↓
ScreeningDecision list
  ↓
partition_screening_results()
  ↓
PrismaFlowReport
  ↓
prisma_report.json
  ↓
E2 (prisma-diagram command)
  ↓
Mermaid / PlantUML output
```

#### Chain 2: Community Detection → Visualization
```
B3 (Louvain community detection)
  ↓
G.nodes[node]["community"] = int
  ↓
E1 (visualize command with --node-color community)
  ↓
Community-colored HTML visualization
```

#### Chain 3: Completeness Scoring → Abstract Backfilling
```
A3 (compute_completeness_score)
  ↓
score: int (0-10)
  ↓
IF score < 8 (missing abstract likely)
  ↓
A4 (backfill_abstract)
  ↓
Enriched Document with abstract
  ↓
Improved A3 score on re-evaluation
```

#### Chain 4: Golden Seed Validation → Search Quality
```
B5 (golden_seed_recall)
  ↓
recall_score: float (0.0-1.0)
  ↓
IF recall < 1.0
  ↓
B5 (heal_query - expand terms)
  ↓
New search query with better recall
  ↓
Re-run nexus_discover
```

---

## 5. Schema Contracts

### 5.1 `prisma_report.json` Contract

This file is produced by `nexus_screen` / `nexus_screen_llm` and consumed by E2.

```json
{
  "total_identified": 1000,
  "duplicates_removed": 200,
  "records_screened": 800,
  "records_excluded": 200,
  "records_included": 150,
  "conflicts_flagged": 5,
  "exclusion_reasons_breakdown": {
    "Wrong population": 100,
    "Wrong intervention": 50,
    "Wrong outcome": 30,
    "Wrong study design": 20
  }
}
```

**Producers:** `partition_screening_results()` in `screening.py`  
**Consumers:** E2 `prisma-diagram` command

### 5.2 `included.json` / `excluded.json` Contract

These files are produced by `nexus_screen` / `nexus_screen_llm` and contain `Document` objects.

```json
[
  {
    "workspace_id": "SCI-000001",
    "title": "Paper Title",
    "abstract": "...",
    "authors": [{"given_name": "John", "family_name": "Doe"}],
    "year": 2024,
    "venue": "Journal Name",
    "external_ids": {"doi": "10.1000/example"},
    "provider": "openalex"
  }
]
```

**Producers:** `nexus_screen`, `nexus_screen_llm`  
**Consumers:** D2 (pipeline), E2 (PRISMA diagrams)

### 5.3 `calibration_batch.json` Contract

This file is produced by `build_preflight_calibration()` and consumed by the LLM screening agent.

```json
{
  "batch_index": 0,
  "is_calibration": true,
  "total_batches": 1,
  "batch_size": 20,
  "status": "PENDING",
  "protocol": {
    "title": "...",
    "research_questions": [...],
    "screening_criteria": {...}
  },
  "papers": [
    {
      "workspace_id": "CAL-0001",
      "title": "...",
      "abstract": "...",
      "year": 2024
    }
  ],
  "checklist_schema": [
    {
      "criterion_id": "INC-01",
      "criterion_type": "inclusion",
      "description": "...",
      "field_name": "inc_01"
    }
  ]
}
```

**Producers:** `build_preflight_calibration()` in `calibration.py`  
**Consumers:** D1 (LLM screening calibration)

---

## 6. Dependency Rules

### 6.1 Hard Dependencies (must be satisfied)

| Rule | Description |
|------|-------------|
| DR-1 | E1 MUST have B3's `community` attribute on graph nodes for community coloring |
| DR-2 | E2 MUST have `prisma_report.json` from D1 or `nexus_screen` for diagram generation |
| DR-3 | D1 MUST have `protocol.json` with `screening_criteria` for LLM screening |
| DR-4 | C1 MUST have Markdown documents from A4 or PDF extraction for indexing |
| DR-5 | A3 MUST have `Document` objects with `external_ids` for completeness scoring |

### 6.2 Soft Dependencies (improve quality)

| Rule | Description |
|------|-------------|
| SR-1 | D1 quality improves if A4 has been run (abstracts available for LLM) |
| SR-2 | A3 score improves if A4 has been run (abstracts backfilled) |
| SR-3 | E1 visualization improves if B1/B2 have enriched graph with HITS/coupling scores |
| SR-4 | C2 extraction quality improves if C1 has been indexed (context available) |

### 6.3 Independence Rules

| Rule | Description |
|------|-------------|
| IR-1 | Phase A is independent of B, C, D, E |
| IR-2 | Phase B is independent of A, C, D, E (except E1 depends on B3) |
| IR-3 | Phase C is independent of A, B, D, E |
| IR-4 | Phase D is independent of A, B, C, E (wraps existing code) |
| IR-5 | Phase E depends on B3 (community) and D1 (PRISMA report) |

---

## 7. Schema Evolution Rules

When adding new fields to shared data models, follow these rules:

### 7.1 Adding Fields to `ResearchProtocol`

1. New fields MUST have default values (backward compatible)
2. New fields MUST be added at the END of the model (serialization order)
3. New fields MUST be documented in this contract
4. `plugins.json` `default_rev` MUST be bumped after schema change

### 7.2 Adding Fields to `ScreeningDecision`

1. New fields MUST have default values (backward compatible)
2. The `decision` field MUST remain `Literal["INCLUDE", "EXCLUDE"]` (no new states)
3. New fields MUST be documented in this contract

### 7.3 Adding Fields to `Document`

1. New fields MUST have default values (backward compatible)
2. New fields MUST be added to the `Document` dataclass in `scholar-search-kit`
3. All exporters (A1, A2) MUST handle new fields gracefully (ignore if not applicable)

---

## 8. Validation Rules

### 8.1 Data Integrity Checks

| Check | Phase | Description |
|-------|-------|-------------|
| DI-1 | All | `ScreeningDecision.decision` MUST be "INCLUDE" or "EXCLUDE" |
| DI-2 | All | `Document.external_ids.doi` MUST be `str` or `None` |
| DI-3 | All | `PrismaFlowReport.total_identified` MUST be ≥ `records_screened` |
| DI-4 | All | `PrismaFlowReport.records_included` + `records_excluded` + `conflicts_flagged` MUST equal `records_screened` |
| DI-5 | B3 | `G.nodes[node]["community"]` MUST be `int` (0-indexed) |

### 8.2 Contract Validation Commands

```bash
# Validate protocol schema
uv run scholar-protocol validate protocol.json

# Validate screening decisions format
python -c "from scholar_search.screening import ScreeningDecision; [ScreeningDecision(**d) for d in decisions]"

# Validate PRISMA report structure
python -c "import json; r = json.load(open('prisma_report.json')); assert 'total_identified' in r"

# Run conformance tests (validates MCP tool contracts)
uv run pytest tests/conformance/ -v
```

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **Document** | A scholarly paper with metadata (title, authors, abstract, DOI, etc.) |
| **ScreeningDecision** | A binary INCLUDE/EXCLUDE decision for a document against protocol criteria |
| **PrismaFlowReport** | Accounting of documents through the PRISMA screening pipeline |
| **ResearchProtocol** | The master research plan with questions, criteria, and search strategy |
| **DocumentCluster** | A group of duplicate documents with one elected representative |
| **Completeness Score** | 0-10 score measuring metadata quality of a Document |
| **Golden Seed** | A landmark paper DOI that must appear in search results (recall validation) |
| **Community** | A thematic cluster of papers identified by Louvain community detection |
| **HITS Hub** | A comprehensive review paper (high out-degree to authorities) |
| **HITS Authority** | A seminal empirical paper (high in-degree from hubs) |

---

*Contract created by opencode (mimo-v2.5-free) on 2026-09-15*
*Purpose: Prevent inter-phase drift by defining canonical data models and flow contracts*
*Update this document when adding new shared data models or modifying phase interfaces*
