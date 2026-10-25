# Search strategy — v0.3 (PROVISIONAL; nothing executed from this workspace)

## Boolean structure (compiled protocol `search_strategy.core_concepts`)

Three OR-clusters joined by AND:

- Cluster 1 (platform) `OR`: UAS, drone, drones, unmanned aerial vehicle(s), unmanned
  aircraft system, uncrewed aerial vehicle, remotely piloted aircraft, aerial imagery,
  orthomosaic.
- Cluster 2 (task target) `OR`: weeds, crop weed, crop-weed, crop and weed,
  site-specific weed management, precision weeding, herbicide prescription.
- Cluster 3 (operation) `OR`: detection, segmentation, classification, monitoring,
  localization, identification, discrimination.

Known harness-lifecycle notes for the v0.2-era runs (unchanged until a patch lands):

- Not-yet-patched kit behavior: OpenAlex boolean truncation degraded synonym
  coverage; records under `../uav-crop-weed-reliability/calibration/` were produced
  under that behavior. A patch exists in the demo clone (uncommitted, canonical-repo
  stream parked) — if it runs, label it `search_implementation=patched_post-L1L6`
  and log a validation event; never overwrite v0.2-era artifacts.
- Databases: openalex, semanticscholar, crossref, arxiv, pubmed (5-provider set per
  protocol).
- Window: 2020–2026. Final search cutoff date still NOT claimed by the researcher
  (pending `RESEARCHER_DECISIONS`); the definitive demo run date 2026-10-16 is
  recorded in the demo ledger but is not a frozen cutoff.
- Languages: en. Pool: 0–1000. OA not preferred.

## Golden seeds (recall sentinels)

The deterministic compiler drops `golden_seeds` from intent (by design; keeps the
pure intent→protocol determinism). The 7 seed DOIs therefore live here:

1. `10.1109/wacv61041.2025.00467` (S1)
2. `10.3389/fpls.2022.927368` (S2 expected miss — in-window, unseeded in OpenAlex etc.)
3. `10.3390/rs15215165`
4. `10.3390/rs18060915`
5. `10.48550/arxiv.2609.05762`
6. `10.1186/s13007-023-01060-8`
7. `10.1016/j.compag.2022.107388`

Run recall checks with `uv run scholar-search validate-query "<query>" --seed <doi> …`
per `scholar-search-kit` skill. Verified sentinel histories: pilot
`../uav-crop-weed-reliability/calibration/SENTINELS.md` (5 dois, 2 failed guesses
discarded) and demo harvest 4/4 in-window recall (2026-10-16, unpatched code).
