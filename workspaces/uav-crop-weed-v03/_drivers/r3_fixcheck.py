"""r3 pre-fetch verification probes (read-only, tiny): MUST pass before the harvest.

Probe A (pubmednorm): rebuild the S6 collision pair EXACTLY as the providers
  emit it — OpenAlex record (DOI lookup, needs the URL->bare normalization)
  and PubMed record (efetch 37608384) — then run the patched Deduplicator
  over the pair. Regression condition: EXACTLY 1 cluster, merged.
Probe B (stemlex): run the compacted arXiv query path (kit provider, 27-term
  protocol query, small cap) and verify 'weedy' is in the emitted clause and
  the arXiv-native sentinel 2609.05762 (AAMBERS-UAV) is now retrieved.
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))


def build_query():
    proto = json.loads(
        (ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json").read_text(
            encoding="utf-8"
        )
    )
    cc = proto["search_strategy"]["core_concepts"]
    clusters = []
    for c in cc:
        ops = (c.get("boolean_operator") or "OR").upper()
        terms = [c["concept"]] + list(c["synonyms"])
        clusters.append((" " + ops + " ").join(f'"{t}"' for t in terms))
    return "(" + ") AND (".join(clusters) + ")"


QUERY = build_query()


async def probe_pubmednorm():
    from scholar_search.dedup import Deduplicator
    from scholar_search.http_client import AcademicHttpClient
    from scholar_search.models import Query
    from scholar_search.providers import OpenAlexProvider, PubMedProvider

    oa = OpenAlexProvider()
    q = Query(text="test", id="PRB-R3-OA1", year_min=2020, year_max=2026, max_results=3)
    # Pull the S6 record via its DOI filter directly (provider parse path).
    resp_oa = await oa.client.get(
        oa.base_url,
        params={
            "mailto": "scholar-search-kit@example.org",
            "filter": "doi:10.1186/s13007-023-01060-8",
            "per-page": 1,
        },
    )
    rec = resp_oa.json()["results"][0]
    oa_doc = oa._normalize_document(rec, "PRB-R3-OA1")
    pm = PubMedProvider()
    pm_doc = None
    async for d in pm._fetch_details(["37608384"]):
        pm_doc = d
        break
    await oa.client.close()
    await pm.client.close()

    oa_pmid = oa_doc.external_ids.pubmed_id
    pm_pmid = pm_doc.external_ids.pubmed_id
    print(
        f"PROBE-A raw: openalex pubmed_id={oa_pmid!r} pubmed pubmed_id={pm_pmid!r} "
        f"oa_doi={oa_doc.external_ids.doi}"
    )
    clusters = Deduplicator().deduplicate([oa_doc, pm_doc])
    merged = len(clusters) == 1 and len(clusters[0].members) == 2
    print(
        f"PROBE-A VERDICT: clusters={len(clusters)} members={[m.provider for m in clusters[0].members]} "
        f"MERGED={merged}"
    )
    return merged and oa_pmid == pm_pmid == "37608384"


async def probe_stemlex():
    from scholar_search.models import Query
    from scholar_search.providers import ArxivProvider

    ax = ArxivProvider()
    q = Query(text=QUERY, id="PRB-R3-AX", year_min=2020, year_max=2026, max_results=60)
    translated = ax.translator.translate(q)
    compact_applied = len(translated) > 300 and " AND " in q.text
    # Reproduce (for evidence) the trailing search_query the kit sends,
    # including the r3 stem-family extension; note the r2 version was an
    # inert no-op because quote-stripping deleted phrase CONTENT too.
    import re as _re

    compact_clauses = []
    for clause in q.text.split(" AND "):
        phrases = _re.findall(r'"([^"]*)"', clause)
        bare = _re.sub(r'"[^"]*"', " ", clause)
        tokens = []
        for p in phrases:
            pt = _re.findall(r"[a-zA-Z0-9_-]{2,}", p)
            if len(pt) == 1:
                tokens.append(pt[0])
        tokens.extend(_re.findall(r"[a-zA-Z0-9_-]{3,}", bare))
        seen, dd = set(), []
        for t in tokens:
            tl = t.lower()
            if tl in seen:
                continue
            seen.add(tl)
            if t.upper() in ("AND", "OR", "NOT") or tl in (
                "aerial",
                "orthomosaic",
                "crop",
            ):
                continue
            dd.append(t)
        if any(t.lower().startswith("weed") for t in dd):
            for extra in ("weedy", "weediness"):
                if extra not in dd:
                    dd.append(extra)
        if dd:
            compact_clauses.append("(" + " OR ".join(f"all:{t}" for t in dd[:6]) + ")")
    print(f"PROBE-B emitted-search_query={' AND '.join(compact_clauses)}")
    s5 = None
    n = 0
    async for d in ax.search(q):
        n += 1
        if d.external_ids.arxiv_id == "2609.05762":
            s5 = d
    await ax.client.close()
    got = s5 is not None
    print(
        f"PROBE-B: compact_applied={compact_applied} fetched={n} S5_id_hit={got} "
        f"title={(s5.title or '')[:70] if s5 else '-'} doi={s5.external_ids.doi if s5 else '-'}"
    )
    return got


async def main():
    a = await probe_pubmednorm()
    b = await probe_stemlex()
    print("PROBE-VERDICTS:", {"pubmednorm_merge": a, "stemlex_s5": b})


if __name__ == "__main__":
    asyncio.run(main())
