# Academic Literature Search Queries & Provider Translations

**Protocol ID**: `proto-20260903-uav-cv-precision-agriculture`  
**Target Venue**: *Computers and Electronics in Agriculture* / *IEEE T-GRS*  
**Date Bounds**: 2018 – 2026  
**Language**: English (`en`)  
**Target Candidate Pool**: 500 – 2,000 papers  

---

## 1. Multi-Stream Query Strategy Overview

To prevent **Search Conjunction Recall Collapse** (where requiring all 4 concepts in a single `AND` query drops valid vision-only or embedded-only papers), the discovery pipeline executes **three complementary query streams**:

1. **Stream A (Algorithmic Vision Benchmark / RQ1)**: Targets deep learning architectures (CNNs, Transformers, Hybrids) evaluated for crop/weed pixel segmentation on UAV imagery.
2. **Stream B (Edge Deployment & Hardware Efficiency / RQ2)**: Targets UAV deep learning segmentation models deployed on embedded/edge hardware platforms with reported throughput/latency.
3. **Stream C (Joint Benchmark Synthesis)**: Targets end-to-end publications that simultaneously benchmark accuracy and profile edge hardware inference.

---

## 2. Canonical Boolean Specifications

### Stream A (Algorithmic / RQ1)
```text
("UAV" OR "drone" OR "unmanned aerial vehicle" OR "UAS") 
AND ("precision agriculture" OR "weed detection" OR "crop monitoring" OR "weed segmentation" OR "crop-weed discrimination") 
AND ("semantic segmentation" OR "instance segmentation" OR "CNN" OR "Vision Transformer" OR "ViT" OR "SegFormer")
```

### Stream B (Edge Deployment / RQ2)
```text
("UAV" OR "drone" OR "unmanned aerial vehicle" OR "UAS") 
AND ("semantic segmentation" OR "weed segmentation" OR "crop segmentation") 
AND ("edge device" OR "Jetson" OR "embedded" OR "real-time inference" OR "FPS" OR "latency" OR "TensorRT")
```

### Stream C (Joint Benchmark)
```text
("UAV" OR "drone" OR "unmanned aerial vehicle" OR "UAS") 
AND ("precision agriculture" OR "weed detection" OR "crop monitoring") 
AND ("semantic segmentation" OR "instance segmentation") 
AND ("edge device" OR "Jetson" OR "real-time" OR "FPS")
```

---

## 3. Translated Provider-Specific Queries

### 3.1 OpenAlex API
- **Endpoint**: `https://api.openalex.org/works`
- **Filter**: `from_publication_date:2018-01-01,to_publication_date:2026-12-31,language:en`
- **Pagination**: Cursor-based (`per-page=200`)

```text
[Stream A - OpenAlex search parameter]:
( "UAV" "drone" "unmanned aerial vehicle" "UAS" ) ( "precision agriculture" "weed detection" "crop monitoring" "weed segmentation" "crop-weed discrimination" ) ( "semantic segmentation" "instance segmentation" "CNN" "Vision Transformer" "ViT" "SegFormer" )

[Stream B - OpenAlex search parameter]:
( "UAV" "drone" "unmanned aerial vehicle" "UAS" ) ( "semantic segmentation" "weed segmentation" "crop segmentation" ) ( "edge device" "Jetson" "embedded" "real-time inference" "FPS" "latency" "TensorRT" )

[Stream C - OpenAlex search parameter]:
( "UAV" "drone" "unmanned aerial vehicle" "UAS" ) ( "precision agriculture" "weed detection" "crop monitoring" ) ( "semantic segmentation" "instance segmentation" ) ( "edge device" "Jetson" "real-time" "FPS" )
```

---

### 3.2 Semantic Scholar API
- **Endpoint**: `https://api.semanticscholar.org/graph/v1/paper/search/bulk`
- **Parameters**: `year=2018-2026`, `fields=paperId,externalIds,title,abstract,year,authors,venue,url,referenceCount,citationCount`
- **Syntax**: `+` for AND, `|` for OR, `-` for NOT

```text
[Stream A - Semantic Scholar query]:
( "UAV" | "drone" | "unmanned aerial vehicle" | "UAS" ) + ( "precision agriculture" | "weed detection" | "crop monitoring" | "weed segmentation" | "crop-weed discrimination" ) + ( "semantic segmentation" | "instance segmentation" | "CNN" | "Vision Transformer" | "ViT" | "SegFormer" )

[Stream B - Semantic Scholar query]:
( "UAV" | "drone" | "unmanned aerial vehicle" | "UAS" ) + ( "semantic segmentation" | "weed segmentation" | "crop segmentation" ) + ( "edge device" | "Jetson" | "embedded" | "real-time inference" | "FPS" | "latency" | "TensorRT" )

[Stream C - Semantic Scholar query]:
( "UAV" | "drone" | "unmanned aerial vehicle" | "UAS" ) + ( "precision agriculture" | "weed detection" | "crop monitoring" ) + ( "semantic segmentation" | "instance segmentation" ) + ( "edge device" | "Jetson" | "real-time" | "FPS" )
```

---

### 3.3 Crossref REST API
- **Endpoint**: `https://api.crossref.org/works`
- **Filter**: `from-pub-date:2018-01-01,until-pub-date:2026-12-31`
- **Syntax**: `+` for AND, space for OR

```text
[Stream A - Crossref query]:
( "UAV" "drone" "unmanned aerial vehicle" "UAS" ) + ( "precision agriculture" "weed detection" "crop monitoring" "weed segmentation" "crop-weed discrimination" ) + ( "semantic segmentation" "instance segmentation" "CNN" "Vision Transformer" "ViT" "SegFormer" )

[Stream B - Crossref query]:
( "UAV" "drone" "unmanned aerial vehicle" "UAS" ) + ( "semantic segmentation" "weed segmentation" "crop segmentation" ) + ( "edge device" "Jetson" "embedded" "real-time inference" "FPS" "latency" "TensorRT" )

[Stream C - Crossref query]:
( "UAV" "drone" "unmanned aerial vehicle" "UAS" ) + ( "precision agriculture" "weed detection" "crop monitoring" ) + ( "semantic segmentation" "instance segmentation" ) + ( "edge device" "Jetson" "real-time" "FPS" )
```

---

### 3.4 arXiv API
- **Endpoint**: `http://export.arxiv.org/api/query`
- **Syntax**: Explicit Boolean `AND`/`OR` prefixed with `all:`

```text
[Stream A - arXiv query]:
( all:"UAV" OR all:"drone" OR all:"unmanned aerial vehicle" OR all:"UAS" ) AND ( all:"precision agriculture" OR all:"weed detection" OR all:"crop monitoring" OR all:"weed segmentation" OR all:"crop-weed discrimination" ) AND ( all:"semantic segmentation" OR all:"instance segmentation" OR all:"CNN" OR all:"Vision Transformer" OR all:"ViT" OR all:"SegFormer" )

[Stream B - arXiv query]:
( all:"UAV" OR all:"drone" OR all:"unmanned aerial vehicle" OR all:"UAS" ) AND ( all:"semantic segmentation" OR all:"weed segmentation" OR all:"crop segmentation" ) AND ( all:"edge device" OR all:"Jetson" OR all:"embedded" OR all:"real-time inference" OR all:"FPS" OR all:"latency" OR all:"TensorRT" )

[Stream C - arXiv query]:
( all:"UAV" OR all:"drone" OR all:"unmanned aerial vehicle" OR all:"UAS" ) AND ( all:"precision agriculture" OR all:"weed detection" OR all:"crop monitoring" ) AND ( all:"semantic segmentation" OR all:"instance segmentation" ) AND ( all:"edge device" OR all:"Jetson" OR all:"real-time" OR all:"FPS" )
```

---

### 3.5 PubMed API (NCBI E-utilities)
- **Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` & `efetch.fcgi`
- **Syntax**: Native Boolean `AND`/`OR` grouping

```text
[Stream A - PubMed query]:
( "UAV" OR "drone" OR "unmanned aerial vehicle" OR "UAS" ) AND ( "precision agriculture" OR "weed detection" OR "crop monitoring" OR "weed segmentation" OR "crop-weed discrimination" ) AND ( "semantic segmentation" OR "instance segmentation" OR "CNN" OR "Vision Transformer" OR "ViT" OR "SegFormer" )

[Stream B - PubMed query]:
( "UAV" OR "drone" OR "unmanned aerial vehicle" OR "UAS" ) AND ( "semantic segmentation" OR "weed segmentation" OR "crop segmentation" ) AND ( "edge device" OR "Jetson" OR "embedded" OR "real-time inference" OR "FPS" OR "latency" OR "TensorRT" )

[Stream C - PubMed query]:
( "UAV" OR "drone" OR "unmanned aerial vehicle" OR "UAS" ) AND ( "precision agriculture" OR "weed detection" OR "crop monitoring" ) AND ( "semantic segmentation" OR "instance segmentation" ) AND ( "edge device" OR "Jetson" OR "real-time" OR "FPS" )
```

---

## 4. Provenance & Reproducible Storage Architecture

Every executed query and raw payload is isolated before normalization:

```text
workspaces/uav-cv-precision-agriculture/literature/
├── SEARCH_QUERIES.md                     # Master query catalog and translation audit
├── SCREENING_PROMPT_TEMPLATE.md          # PRISMA batched screening prompt template
├── raw/                                  # Immutable provider responses
│   ├── provenance_manifest.json          # Search execution ledger (timestamp, URL, status)
│   ├── openalex_raw_streamA.json
│   ├── openalex_raw_streamB.json
│   ├── semanticscholar_raw_streamA.json
│   ├── semanticscholar_raw_streamB.json
│   ├── crossref_raw_streamA.json
│   ├── crossref_raw_streamB.json
│   ├── arxiv_raw_streamA.json
│   └── arxiv_raw_streamB.json
├── raw_search.json                       # Normalized combined candidate pool
├── deduped.json                          # Deduplicated pool with canonical SCI-XXXXXX IDs
├── verified.json                         # Crossref/OpenAlex hydrated rich abstracts
├── included.json                         # PRISMA screened inclusions
├── excluded.json                         # PRISMA screened exclusions with reason codes
├── conflicts.json                        # Borderline candidates for human/adjudication audit
└── prisma_screening_report.md            # PRISMA 2020 flow accounting report
```
