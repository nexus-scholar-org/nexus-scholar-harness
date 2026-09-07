# Retraction & Publication-Status Check

**Corpus**: 94 studies (post-audit); **run**: 2026-09-07T02:09:14.038528+01:00
**Sources**: OpenAlex `is_retracted`/`last_status_in_oa` + Crossref `update-to`

## Summary

| Metric | Value |
|---|---|
| Studies checked | 94 |
| Flagged (any retraction/correction/EoC signal) | 0 |
| Retracted (OpenAlex) | 0 |
| Crossref update-to events | none |
| OpenAlex provenance (`last_status_in_oa`) | not populated for this corpus |
| Unresolved lookups | 0 |

## Flagged studies

None.

## arXiv-only records (no formal retraction channel)

The following studies have no DOI and are arXiv-tracked; OpenAlex was consulted through a DOI-independent lookup (arXiv id → title/year match → OpenAlex id):

| ID | Title | OpenAlex retracted |
|---|---|---|
| SCI-000010 | Semi-supervised GAN for Classification of Multispectral Imagery Acquired by UAVs | False |
| SCI-000013 | Self-supervised training for high-resolution close-range multispectral remote sensing imagery | False |
| SCI-000810 | AgriJetsonBench: External-Power-Referenced TensorRT Benchmarking of Agricultural Vision Models on Jetson Edge Platforms | False |

## Methodological note

- Correction markers from Crossref may be self-published errata; treat as low-severity unless `type == retraction` or `expression-of-concern`.
- OpenAlex `is_retracted` reflects the current metadata snapshot, not publisher live status.
- All per-study rows are in the JSON output; regenerate with `scholar-verify retraction --workspace <dir>`.
