# Literature Discovery & Screening Strategy

Before we launch the automated pipeline, here is exactly how we will tackle the literature discovery, dataset aggregation, filtering, and systematic screening for the `uav-cv-precision-agriculture` project. We will use the `scholar-search-kit`, which operates deterministically based on the canonical `protocol.json` we just compiled.

## 1. Federated Discovery (Search Strategy)

The first step is a federated search across massive academic datasets. We will not use manual search queries; instead, the search kit will dynamically compile a query block from our `protocol.json`.

- **Datasets & APIs**: We will query **OpenAlex**, **Semantic Scholar**, **Crossref**, **PubMed**, and **arXiv**. OpenAlex and Semantic Scholar are particularly strong for computer science and agriculture intersections.
- **Search Logic**: The engine combines our `core_concepts` and their `synonyms` via Boolean logic:
  `(UAV OR drone OR UAS ...) AND ("precision agriculture" OR "weed detection" ...) AND ("semantic segmentation" OR CNN OR ViT ...) AND ("edge device" OR "Jetson" ...)`
- **Configured Bounds**: 
  - **Date Range**: 2018 to 2026 (ensuring we capture modern deep learning and edge SOCs).
  - **Language**: English only.
  - **Corpus Limit**: Between 500 (`pool_min`) and 2000 (`pool_max`) initial candidates to balance exhaustiveness with processing limits.

## 2. 2-Tier Deduplication & Canonicalization

Academic APIs frequently return overlapping records (e.g., an arXiv preprint and its final IEEE publication). Before doing any screening, we run a rigorous deduplication process:
- **Tier 1 (Hard IDs)**: Merges records sharing identical DOIs, PMIDs, arXiv IDs, or OpenAlex IDs.
- **Tier 2 (Fuzzy Matching)**: Performs Jaro-Winkler fuzzy string matching ($\ge 97\%$ similarity) on paper titles, validated against publication year and author overlaps, to catch variations in titles or missing DOIs.
- **Result**: Every unique paper receives a canonical Workspace ID (e.g., `SCI-1A2B3C`) to ensure perfect traceability.

## 3. Abstract Hydration & Authenticity Verification

To ensure zero hallucinations and high-quality metadata for screening:
- The `scholar-search-kit` will run a verification pass against Crossref/OpenAlex.
- It strips out noisy formatting (like `<jats:p>` XML tags) from abstracts.
- It attempts to hydrate missing abstracts by pinging secondary APIs (like Semantic Scholar) if OpenAlex didn't provide the full text abstract.

## 4. Systematic Screening (PRISMA 2020)

Once we have a clean, verified pool of unique candidates, we run the automated heuristic screening engine. The engine evaluates every title and abstract strictly against the criteria you defined in `intent.json`:

**Inclusion Enforcement (Must have ALL)**:
- Must focus on deep learning architectures on UAV imagery for crop/weed pixel segmentation.
- Must report quantitative pixel-wise metrics (mIoU, F1).
- Must report or allow inference of on-device hardware execution metrics (FPS, power).

**Exclusion Enforcement (If ANY, reject)**:
- Excludes satellite/ground-only setups.
- Excludes bounding-box only detection.
- Excludes traditional ML (SVMs, Otsu) without deep features.
- Excludes secondary reviews/surveys.

**Outputs**: The screening partitions the data into `included.json`, `excluded.json` (with rejection reasons), and generates a standard PRISMA 2020 Flow diagram documenting exactly how many papers were filtered at each stage.

## 5. Snowballing (If Necessary)

If the strict PRISMA screening results in too few included papers (e.g., under 20), we will execute **Citation Snowballing**. We take the highest-quality included papers and use OpenAlex to crawl:
- **Forward**: Papers that cited our seed papers.
- **Backward**: Papers referenced in the bibliography of our seed papers.
We then run those new candidates through the same deduplication and screening pipeline.

---

> [!IMPORTANT]
> **User Review Required**
> Are you comfortable with this 5-step automated workflow? If this search strategy aligns with your vision for a top-tier review, click "Proceed" and I will execute the discovery phase!
