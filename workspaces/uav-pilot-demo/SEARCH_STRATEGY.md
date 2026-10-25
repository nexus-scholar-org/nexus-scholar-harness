# Search strategy v0.2 — draft, not executed

The following OR clusters match intent.json and protocol.json. Combine the
three clusters with AND for the broad recall query, translating syntax to each
provider and recording the exact executed expression and filters:

```text
(UAV OR UAS OR drone OR drones OR "unmanned aerial vehicle" OR
 "unmanned aerial vehicles" OR "unmanned aircraft system" OR "aerial imagery")
AND (weed OR weeds OR "crop weed" OR "crop-weed" OR "crop and weed")
AND (mapping OR detection OR segmentation OR monitoring OR localization)
```

Providers may tokenize, restrict boolean syntax or match title/abstract differently.
Do not assume the compiler submits this expression identically. Test translated
queries against verified seeds and export complete paginated results and errors.
If the task cluster lowers recall, test and log a two-cluster supplement rather
than silently modifying the frozen query. Reliability/sensor/temporal terms are
supplements, never simultaneous mandatory AND conditions.

## Coverage and dates

API sources planned: openalex, semanticscholar, crossref, arxiv. Complementary
IEEE Xplore and Scopus/Web of Science access remains unconfirmed; document
actual access or limitations before freeze. Trace references and citations and
verify publisher records. Check overlapping reviews for scope, dates and sources.
Open access is not eligibility. A cap/pagination failure is incomplete retrieval,
never a complete search. The pool_max=1000 configuration is not a stopping rule.
Year filters are coarse; enforce the actual final cutoff date on verified reports.
Initialization was 2026-10-12; no executed search date is claimed.

## Seeds and recall calibration

WeedsGalore (candidate DOI 10.1109/WACV61041.2025.00467) and WeedMap are
provisional leads from prior discussion, not independently reverified here.
Verify metadata and in-window eligibility and select 2–5 independent sentinels,
including boundary cases, before claiming recall. Older foundations can guide
terms without becoming in-window recall requirements. The user's draft supplies
motivation, not proof of novelty or a mandatory positive-control inclusion.

golden_seeds remains empty in the compiled draft: the current IntentPacket
compiler does not expose a seed passthrough. Do not hand-edit protocol.json or
claim seed enforcement. Record verified sentinels in the calibration log and
perform an explicit recall check; a compiler enhancement is a separate kit task.
No search results, exclusions or provider availability are fabricated here.
