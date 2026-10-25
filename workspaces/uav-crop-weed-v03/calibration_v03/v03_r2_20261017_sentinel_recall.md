# r2 sentinel recall — UAV-HARVEST-R2-20261017

Recall base: `v03_r2_20261017_deduped.json` (2356 representatives). Tier-1 = Canonical PID equality (doi OR arxiv_id, crosswalk PIDs marked OBSERVED from live artifacts). Title containment is reported separately and is NOT identity. Provider arrivals from the raw union.

| Seed | Tier-1 PIDs (seed) | DOI-exact | arxiv_id-exact | Title-only | SCI-id(s) | Arrivals (providers) | Verdict |
|------|--------------------|-----------|----------------|------------|-----------|----------------------|---------|
| S1 | `10.1109/wacv61041.2025.00467` + arxiv_id=2502.13103 (OBSERVED) | 1 | 0 | 0 | SCI-000128 | openalex; semanticscholar | PID HIT (doi-exact) |
| S2 | `10.3389/fpls.2022.927368` | 1 | 0 | 0 | SCI-000224 | crossref; openalex; pubmed | PID HIT (doi-exact) |
| S3 | `10.3390/rs15215165` | 1 | 0 | 0 | SCI-000178 | openalex; semanticscholar | PID HIT (doi-exact) |
| S4 | `10.3390/rs18060915` + arxiv_id=2603.01932 (OBSERVED) | 1 | 0 | 0 | SCI-000188 | openalex; semanticscholar | PID HIT (doi-exact) |
| S5 | `10.48550/arxiv.2609.05762` + arxiv_id=2609.05762 (OBSERVED) | 0 | 0 | 0 | — | none | MISS |
| S6 | `10.1186/s13007-023-01060-8` | 2 | 0 | 0 | SCI-000193; SCI-002331 | openalex; pubmed | PID HIT (doi-exact) |
| S7 | `10.1016/j.compag.2022.107388` | 1 | 0 | 0 | SCI-000186 | openalex | PID HIT (doi-exact) |

Baseline anchors: 2026-10-16 unpatched run 4/4 in-window on its 5-sentinel table (S1 doi 2, SemiWeedNet 2, rs15215165 2, j.atech 1); v03 patched run 4/7 (1 DOI-exact + 3 title-only; S3/S5/S7 MISS). r2 rows above show the post-fix (strict filter, scoped pubmed IDs, PID axis) behavior.

## Summary — Tier-1 PID recall: 6/7
- S1: PID HIT (doi-exact)
- S2: PID HIT (doi-exact)
- S3: PID HIT (doi-exact)
- S4: PID HIT (doi-exact)
- S5: MISS
- S6: PID HIT (doi-exact)
- S7: PID HIT (doi-exact)