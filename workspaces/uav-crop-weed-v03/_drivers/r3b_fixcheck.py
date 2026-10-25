"""r3b verification probe: models-level PMID normalization + merge regression.

Probe M (models): ExternalIds.__post_init__ strips URL/scheme prefixes for
  pubmed_id across importer paths (any provider or cached JSON).
Probe A (regression): the r2 S6 pair still merges (OpenAlex DOI-lookup record +
  PubMed efetch 37608384 -> exactly 1 cluster).
Read-only, tiny, no writes outside stdout.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))


def probe_models():
    from scholar_search.models import ExternalIds

    cases = [
        ("https://pubmed.ncbi.nlm.nih.gov/37608384", "37608384"),
        (
            "https://www.ncbi.nlm.nih.gov/pubmed/37608384/",
            "37608384",
        ),
        ("pmid:37608384", "37608384"),
        ("PMID:37608384", "37608384"),
        ("37608384", "37608384"),
        ("", None),
        (None, None),
    ]
    ok = True
    for raw, expected in cases:
        e = ExternalIds(pubmed_id=raw)
        result = e.pubmed_id
        good = result == expected
        ok = ok and good
        print(
            f"PROBE-M pubmed_id={raw!r} -> {result!r} expected={expected!r} {'PASS' if good else 'FAIL'}"
        )
    return ok


async def probe_merge():
    from scholar_search.dedup import Deduplicator
    from scholar_search.models import Query
    from scholar_search.providers import OpenAlexProvider, PubMedProvider

    oa = OpenAlexProvider()
    q = Query(
        text="test", id="PRB-R3B-OA1", year_min=2020, year_max=2026, max_results=3
    )
    resp = await oa.client.get(
        oa.base_url,
        params={
            "mailto": "scholar-search-kit@example.org",
            "filter": "doi:10.1186/s13007-023-01060-8",
            "per-page": 1,
        },
    )
    rec = resp.json()["results"][0]
    oa_doc = oa._normalize_document(rec, "PRB-R3B-OA1")
    pm = PubMedProvider()
    pm_doc = None
    async for d in pm._fetch_details(["37608384"]):
        pm_doc = d
        break
    await oa.client.close()
    await pm.client.close()
    clusters = Deduplicator().deduplicate([oa_doc, pm_doc])
    merged = len(clusters) == 1 and len(clusters[0].members) == 2
    print(
        f"PROBE-A VERDICT: clusters={len(clusters)} "
        f"members={[m.provider for m in clusters[0].members]} MERGED={merged}"
    )
    return merged


async def main():
    m = probe_models()
    a = await probe_merge()
    print("PROBE-VERDICTS:", {"models_pmid_norm": m, "merge_regression": a})
    if not (m and a):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
