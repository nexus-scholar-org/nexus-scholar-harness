# Search strategy draft — not executed

**Initialization date:** 2026-10-12. **Last executed search:** none.
Record actual query syntax, source, filters, timestamp, pagination, counts,
provider errors and exports for each future run. Never call a capped first page
an exhaustive search. Provider coverage and access must be tested before freeze.

## Broad recall query

Translate this conceptual query to each source's supported syntax:

```text
(UAV OR UAS OR drone OR "unmanned aerial vehicle" OR "aerial imagery")
AND (weed OR weeds OR "crop weed" OR "crop-weed")
AND (mapping OR detection OR segmentation OR monitoring)
```

Do not AND all reliability/sensor/temporal terms into the mandatory query.
Use separate supplemental queries for missing bands, multispectral fusion,
misregistration, sensor transfer, domain shift, uncertainty, calibration,
multitemporal imagery and held-out seasons. Log each refinement and evaluate
recall against independently verified seeds, not just result count.

## Sources and access

Planned API sources: OpenAlex, Semantic Scholar, Crossref and arXiv.
Assess complementary IEEE Xplore and Scopus/Web of Science access for the formal
review; these are not claimed connected or searched. Use publisher records and
backward/forward citation tracing to supplement and verify, retaining provenance.
Check existing scoping/systematic reviews for overlap, but keep them outside
the primary empirical corpus and use them for context/citation tracing.

## Seed candidates and provenance

- WeedsGalore, WACV 2025, DOI `10.1109/WACV61041.2025.00467`: candidate recall
  sentinel from prior reconnaissance, not a screened inclusion. Reverify its
  metadata/full text before freezing a golden-seed set.
- WeedMap: foundational candidate from the user's draft; bibliographic details
  must be verified. Do not fabricate a DOI or treat older work as in-window.
- The user's AvaRel-Fuse draft: local motivation, not an independent seed that
  guarantees a research gap. See source_context.json for file checksum.

No provider results, completed search log, corpus or inclusion decisions exist
yet. A 30–50-record development sample is not a limit on the review search.
