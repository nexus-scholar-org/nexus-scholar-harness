# Literature Discovery Remediation & Corpus Quality Audit Report

- **Protocol ID**: `proto-20260903-uav-cv-precision-agriculture`
- **Canonical Protocol Fingerprint**: `sha256:e1bbcb791d9108b2277fa468982f59cbdc611a66288556c5f4812fde34f1b077`
- **Remediation Timestamp**: `2026-09-03T23:16:30+01:00`
- **Lead Reviewer**: AI Pair-Programming Assistant
- **Workspace**: `uav-cv-precision-agriculture`
- **Target Guidelines**: PRISMA 2020 Flow Compliance

---

## 1. Executive Summary & Remediation Highlights

Following the initial discovery audit, a targeted remediation pass was executed to eliminate identified data gaps, resolve provider syntax mismatches, and enrich incomplete bibliographic records.

```mermaid
flowchart TD
    subgraph S1 [Gap Remediation]
        S2_FAIL["S2 Stream B (0 Results)"] -->|Query Tuning| S2_FIX["S2 Stream B: 339 Records Recovered"]
        MISS_ABS["317 Missing Abstracts (26.1%)"] -->|Batch S2 + OpenAlex| HYDRATED["186 Abstracts Hydrated (90.0% Coverage)"]
    end

    subgraph S2 [Corpus Expansion & Re-Deduplication]
        S2_FIX --> RE_DEDUP["Re-Deduplication across 1,837 Raw Records"]
        RE_DEDUP --> FINAL_CORPUS["Final Screenable Corpus: 1,488 Papers (+274 Net Inclusions)"]
    end

    subgraph S3 [Quality Metrics]
        FINAL_CORPUS --> DOI_RATE["DOI Rate: 97.72% (1,454)"]
        FINAL_CORPUS --> ABS_RATE["Abstract Rate: 89.99% (1,339)"]
        FINAL_CORPUS --> CONF_RATE["Conference Papers: 369 (24.8%)"]
    end
```

### Remediation Achievements:
1. **Semantic Scholar Stream B Recovered**: Resolved the HTTP 500 error caused by overly nested boolean operators on `/graph/v1/paper/search/bulk`. Recovered **339 empirical records** directly targeting edge deployment and embedded inference.
2. **Dense Abstract Hydration**: Batch-queried Semantic Scholar (`POST /graph/v1/paper/batch`) and OpenAlex to hydrate missing abstracts using verified DOIs. Successfully recovered **186 abstracts**, driving abstract completeness from **73.9% to 90.0%** (1,339 / 1,488).
3. **Corpus Expansion**: Total raw harvested records increased from **1,498 to 1,837**, yielding **1,488 unique verified documents** (a net increase of **+274 primary studies**).
4. **Conference & Robotics Enrichment**: Captured 122 additional conference proceeding papers (from 247 to 369), significantly reinforcing hardware profiling (Jetson, TensorRT, FPS) from robotics conferences.

---

## 2. Before vs. After Remediation Comparison

| Quality Dimension | Pre-Remediation Baseline | Post-Remediation Result | Absolute Delta | Percentage Shift |
| :--- | :---: | :---: | :---: | :---: |
| **Total Raw Harvested Records** | 1,498 | **1,837** | +339 | +22.6% |
| **Unique Verified Documents** | 1,214 | **1,488** | +274 | +22.6% |
| **Duplicates Merged** | 284 | **349** | +65 | — |
| **Rich Abstracts Available** | 897 (73.89%) | **1,339 (89.99%)** | **+442** | **+16.10%** |
| **Missing / Minimal Abstracts** | 317 (26.11%) | **149 (10.01%)** | **-168** | **-16.10%** |
| **DOI Completeness** | 1,164 (95.88%) | **1,454 (97.72%)** | +290 | +1.84% |
| **Direct Web Locator (URL)** | 1,214 (100%) | **1,488 (100%)** | +274 | 100.0% |
| **Semantic Scholar External IDs** | 286 (23.56%) | **614 (41.26%)** | **+328** | **+17.70%** |
| **arXiv External IDs** | 70 (5.77%) | **90 (6.05%)** | +20 | +0.28% |
| **PubMed External IDs (PMID)** | 205 (16.89%) | **223 (14.99%)** | +18 | — |

---

## 3. Detailed Provider Contribution & Query Log

With Semantic Scholar Stream B restored, all 5 target databases now provide multi-stream coverage across the research questions:

| Database Provider | Stream A (RQ1: Algo) | Stream B (RQ2: Edge) | Stream C (Joint Benchmark) | Total Harvested | Provenance File |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **OpenAlex** | 200 | 200 | 100 | **500** | `literature/raw/openalex_raw_*.json` |
| **Crossref REST** | 200 | 200 | 100 | **500** | `literature/raw/crossref_raw_*.json` |
| **Semantic Scholar** | 200 | **339** *(Remediated)* | 100 | **639** | `literature/raw/semanticscholar_raw_*.json` |
| **PubMed (NCBI)** | 47 | 12 | 63 | **122** | `literature/raw/pubmed_raw_*.json` |
| **arXiv API** | 21 | 35 | 20 | **76** | `literature/raw/arxiv_raw_*.json` |
| **Total Raw Pool** | **668** | **786** | **383** | **1,837** | Staged in `literature/raw_search.json` |

### Streamlined Semantic Scholar Stream B Query:
- **Raw API Query String**:
  ```text
  ("UAV" | "drone") + ("semantic segmentation" | "weed segmentation") + ("edge" | "Jetson" | "real-time")
  ```
- **Execution Endpoint**: `https://api.semanticscholar.org/graph/v1/paper/search/bulk`
- **Fields Retrieved**: `paperId,title,abstract,year,authors,venue,externalIds,url,citationCount,referenceCount`
- **Response**: `HTTP 200 OK` (339 records retrieved in 3.5s)

---

## 4. Post-Remediation Corpus Demographics (N = 1,488)

### 4.1 Publication Types
The addition of Semantic Scholar Stream B restored balance between journal literature and applied engineering conference papers:

```text
Journal Articles           | ██████████████████████████████████████ (556, 37.4%)
Journal / Publications     | ██████████████████████████ (390, 26.2%)
Conference / Proceedings   | █████████████████████████ (369, 24.8%)
Preprints (arXiv)          | ███████ (101, 6.8%)
Unspecified / Tech Reports | █████ (72, 4.8%)
```

### 4.2 Top 20 Publication Outlets
Leading academic venues representing the core of agricultural vision and edge computing:

| Rank | Venue | Count | Domain Scope |
| :---: | :--- | :---: | :--- |
| 1 | *arXiv Preprint* | 70 | Deep learning architectures & early benchmark releases |
| 2 | *Remote Sensing* (MDPI) | 69 | UAV orthomosaics, multispectral segmentation |
| 3 | *IEEE Access* | 40 | Edge computing, neural network optimization |
| 4 | *Agriculture* (MDPI) | 39 | Precision agriculture, crop management |
| 5 | *Sensors* / *Sensors (Basel)* | 57 | Drone payloads, onboard edge computer vision |
| 6 | *Agronomy* (MDPI) | 31 | Crop-weed discrimination & field robotics |
| 7 | *Frontiers in Plant Science* | 46 | Automated phenotyping & field vision |
| 8 | *Journal of Crop and Weed* | 25 | Agronomic weed ecology |
| 9 | *SSRN Electronic Journal* | 25 | Applied AI field trials |
| 10 | *Computers and Electronics in Agriculture* | 21 | **Core Tier-1 benchmark reference** |
| 11 | *Drones* (MDPI) | 21 | UAS telemetry, onboard payload constraints |
| 12 | *Scientific Reports* (Nature) | 36 | Empirical comparative trials |
| 13 | *Applied Sciences* | 19 | Applied neural network inference |
| 14 | *IEEE JSTARS* | 14 | Geoscience & high-altitude UAV segmentation |
| 15 | *AgriEngineering* | 13 | Autonomous agricultural machinery & robotics |
| 16 | *Italian National Conference on Sensors* | 9 | Embedded sensing & hardware benchmarking |
| 17 | *Precision Agriculture* (Springer) | 7 | Site-specific management & spot spraying |
| 18 | *Plant Methods* (BMC) | 7 | Vision-based plant trait extraction |
| 19 | *Artificial Intelligence in Agriculture* | 6 | Specialized deep learning benchmarks |
| 20 | *Smart Agricultural Technology* | 5 | Edge computing & robotics in farming |

---

### 4.3 Chronological Profile (2018 – 2026)
Chronological trends show that the dataset captures the modern transition from heavy CNN backbones (ResNet/VGG) to lightweight Transformers (SegFormer, MobileViT) and edge TensorRT optimization:

| Publication Year | Record Count | Percentage | Cumulative Share |
| :---: | :---: | :---: | :---: |
| **2026 (YTD)** | 268 | 18.01% | 18.01% |
| **2025** | 407 | 27.35% | 45.36% |
| **2024** | 214 | 14.38% | **59.74% (Last 2.5 Years)** |
| **2023** | 171 | 11.49% | 71.24% |
| **2022** | 115 | 7.73% | 78.97% |
| **2021** | 124 | 8.33% | 87.30% |
| **2020** | 83 | 5.58% | 92.88% |
| **2019** | 73 | 4.91% | 97.78% |
| **2018** | 32 | 2.15% | 99.93% |
| **2027 (Pre-print/Advance)** | 1 | 0.07% | 100.00% |

---

## 5. Screening Readiness Assessment

With **90.0% abstract coverage** and **97.7% DOI coverage** across **1,488 candidate papers**, the corpus is in prime condition for systematic screening:
1. **Semantic Screening Fidelity**: 1,339 papers have full text abstracts enabling deep LLM/subagent evaluation of model architectures, datasets, and edge platforms.
2. **Abstract-Less Subset Strategy**: The remaining 149 papers (10.0%) will be assessed using their verified titles, publication venues, and author keywords. If an abstract-less candidate's title suggests a primary UAV benchmark, it will be retained for full-text recovery rather than arbitrarily excluded.
3. **Traceability**: All 1,488 records possess canonical identifiers (`SCI-000001` through `SCI-001488`) logged in [`literature/verified.json`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/workspaces/uav-cv-precision-agriculture/literature/verified.json).

---

## 6. Audit & File Catalog Update

- **Primary Staging File**: [`literature/verified.json`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/workspaces/uav-cv-precision-agriculture/literature/verified.json) (1,488 verified documents)
- **Provenance Manifest**: [`literature/raw/provenance_manifest.json`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/workspaces/uav-cv-precision-agriculture/literature/raw/provenance_manifest.json)
- **Initial Discovery Audit**: [`reports/discovery_report_20260903_230800.md`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/workspaces/uav-cv-precision-agriculture/reports/discovery_report_20260903_230800.md)
- **Remediation Audit**: [`reports/discovery_remediation_report_20260903_231630.md`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/workspaces/uav-cv-precision-agriculture/reports/discovery_remediation_report_20260903_231630.md)
