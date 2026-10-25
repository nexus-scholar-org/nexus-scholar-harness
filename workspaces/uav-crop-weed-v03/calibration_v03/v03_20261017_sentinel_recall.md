# v0.3 sentinel recall — UAV-HARVEST-V03-PATCHED-20261017

Recall base: `v03_20261017_deduped.json` (2060 representatives); arrivals traced against `v03_20261017_union_raw.json` (2115 raw records). DOI match = case-insensitive containment on external_ids; title match = normalized-title containment fallback ONLY when the DOI axis missed; the two axes are kept separate. Title containment is NOT identity and is NOT counted as a DOI hit.

| Seed | DOI | Title (short) | DOI-exact hits | Title-fallback hits | Hit provenance (SCI | provider | year | recorded DOI) | Raw arrivals | Verdict/Note |
|------|-----|---------------|----------------|--------------------|---------------------|--------------|--------------|
| S1 | `10.1109/wacv61041.2025.00467` | WeedsGalore (A Multispectral and Multitemporal UAV-Ba) | 0 | 1 | SCI-001956 | arxiv | 2025 | doi=None | note: record lacks the seed DOI (e.g., arXiv DOI-less twin); title axis only | title-axis: arxiv | TITLE-FALLBACK HIT.  |
| S2 | `10.3389/fpls.2022.927368` | Semi-supervised Learning for Weed and Crop Segme (...) | 1 | 0 | SCI-001516 | crossref | 2022 | doi=10.3389/fpls.2022.927368 | crossref | DOI-EXACT HIT.  |
| S3 | `10.3390/rs15215165` | Transformer in UAV Image-Based Weed Mapping (...) | 0 | 0 | — | none | MISS. no raw record carries the seed DOI or its exact normalized title; consistent with relevance-rank shift + cap truncation under the expanded 27-term v0.3 query (providers are relevance-ranked, cap-bounded) — human decision required |
| S4 | `10.3390/rs18060915` | BAWSeg (A UAV Multispectral Benchmark for Barley) | 0 | 1 | SCI-001955 | arxiv | 2026 | doi=None | note: record lacks the seed DOI (e.g., arXiv DOI-less twin); title axis only | title-axis: arxiv | TITLE-FALLBACK HIT.  |
| S5 | `10.48550/arxiv.2609.05762` | AAMBERS-UAV (Acquisition-Aware Multimodal Backbone Ev) | 0 | 0 | — | none | MISS. no raw record carries the seed DOI or its exact normalized title; consistent with relevance-rank shift + cap truncation under the expanded 27-term v0.3 query (providers are relevance-ranked, cap-bounded) — human decision required |
| S6 | `10.1186/s13007-023-01060-8` | Improved weed segmentation in UAV imagery of sor (...) | 0 | 1 | SCI-002030 | pubmed | 2023 | doi=10.7717/peerj.453 | WARNING: same title, recorded DOI differs from seed DOI — possible provider ArticleId mis-parse or genuine title collision; NOT counted as DOI-exact | title-axis: pubmed | TITLE-FALLBACK HIT (DOI MISMATCH on record — see note).  |
| S7 | `10.1016/j.compag.2022.107388` | Deep learning-based early weed segmentation usin (...) | 0 | 0 | — | none | MISS. no raw record carries the seed DOI or its exact normalized title; consistent with relevance-rank shift + cap truncation under the expanded 27-term v0.3 query (providers are relevance-ranked, cap-bounded) — human decision required |

## Summary — DOI-exact: 1/7 | title-fallback only: 2/7 | total recalled: 4/7

Baseline anchor (2026-10-16 unpatched, 5-sentinel table): S1 DOI-exact 2 (openalex+crossref), WeedMap S2' MISS out-of-window, SemiWeedNet DOI-exact 2, rs15215165 DOI-exact 2, j.atech HIT 1 — 4/4 in-window.

Key deltas (headline findings for human interpretation):
- S1: baseline DOI-exact (crossref copy); this run DOI axis missed — same paper arrives title-exact via arXiv as a DOI-less twin (arxiv_id 2502.13103). Cross-provider identity alternative present, DOI crosswalk absent.
- S2 SemiWeedNet: DOI-exact HIT via crossref (baseline had openalex+crossref copies). This seed was historically an expected miss; its appearance under the patched run is patched-code/expanded-synonym behavior, verified against live raw records, not assumed.
- S3 rs15215165: baseline DOI-exact 2; this run MISS (no raw record with DOI or exact title) — consistent with relevance-rank shift + cap truncation under the expanded query.
- S4 BAWSeg: arrives title-exact via arXiv DOI-less twin (arxiv_id 2603.01932); seed DOI 10.3390/rs18060915 absent from all raw files.
- S5 AAMBERS (arxiv 2609.05762): MISS — arXiv leg returned 39/cap records; seed not among them.
- S6 s13007-023-01060-8: identical-title pubmed record carries DOI 10.7717/peerj.453 ≠ seed DOI; possible PubMed ArticleId mis-parse or genuine title collision; flagged, NOT counted as DOI-exact.
- S7 compag.2022.107388: MISS.