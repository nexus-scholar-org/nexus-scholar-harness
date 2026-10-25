"""r2 pre-launch probe of the 4 patched code paths (read-only, tiny queries).

Probes:
  1. OpenAlex strict boolean filter (title_and_abstract.search) — no 500,
     cap-5 results relevance-tight.
  2. PubMed EFetch of PMID 37608384 — external doi must be the article's own
     DOI (10.1186/s13007-023-01060-8), not a reference-list DOI.
  3. arXiv compacted boolean query — parses and returns docs.
  4. S2 bulk search — documents 403-with-key and the unauthenticated
     downgrade behavior.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))

import re


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


async def probe_openalex():
    from scholar_search.models import Query
    from scholar_search.providers import OpenAlexProvider

    p = OpenAlexProvider()
    params = p._build_params(
        Query(text=QUERY, id="PRB-OA", year_min=2020, year_max=2026, max_results=5)
    )
    assert "search" not in params, "boolean must NOT go to full-text search"
    assert any(
        "title_and_abstract.search:" in str(f) for f in params["filter"].split(",")
    ), "boolean must sit in the filter list"
    resp = await p.client.get(p.base_url, params=params)
    meta = resp.json().get("meta", {})
    titles = [r.get("title", "")[:70] for r in resp.json().get("results", [])[:5]]
    print(f"PROBE-OA: http={resp.status_code} total_matches={meta.get('count')}")
    for t in titles:
        print(f"  OA-TITLE: {t}")
    df = [f for f in params["filter"].split(",") if "title_and_abstract" in f][0]
    print(f"  OA-FILTER-USED: {df[:90]}...")
    await p.client.close()
    return resp.status_code == 200


async def probe_pubmed():
    from scholar_search.providers import PubMedProvider

    p = PubMedProvider()
    docs = []
    async for d in p._fetch_details(["37608384"]):
        docs.append(d)
    await p.client.close()
    assert docs, "efetch returned nothing"
    ext = docs[0].external_ids
    ok = (ext.doi or "").lower() == "10.1186/s13007-023-01060-8"
    print(f"PROBE-PM: title={docs[0].title[:60]!r} doi={ext.doi} correct={ok}")
    return ok


async def probe_arxiv():
    from scholar_search.models import Query
    from scholar_search.providers import ArxivProvider

    p = ArxivProvider()
    q = Query(text=QUERY, id="PRB-AX", year_min=2020, year_max=2026, max_results=12)
    # Reproduce the compaction decision for logging
    translated = p.translator.translate(q)
    compact = len(translated) > 300 and " AND " in q.text
    docs = []
    async for d in p.search(q):
        docs.append(d)
    print(
        f"PROBE-AX: compact_applied={compact} docs={len(docs)} "
        f"sample={[(d.title or '')[:45] for d in docs[:3]]}"
    )
    await p.client.close()
    return len(docs) > 0


async def probe_s2():
    from scholar_search.models import Query
    from scholar_search.providers import SemanticScholarProvider

    p = SemanticScholarProvider()
    q = Query(
        text='("UAV") AND ("weed") AND ("detection")',
        id="PRB-S2",
        year_min=2020,
        year_max=2026,
        max_results=5,
    )
    msgs = []
    try:
        docs = [d async for d in p.search(q)]
        print(f"PROBE-S2: docs={len(docs)} (downgrade path exercised ok)")
        await p.client.close()
        return True
    except Exception as e:  # noqa: BLE001
        msgs.append(f"{type(e).__name__}: {str(e)[:160]}")
        print(f"PROBE-S2: FAIL-EVEN-AFTER-DOWNGRADE {msgs}")
        await p.client.close()
        return False


async def main():
    keyed = os.environ.get("SCHOLAR_S2_KEY") is not None
    print(f"PROBE-ENV: SCHOLAR_S2_KEY present={keyed} (value unread)")
    r = await asyncio.gather(
        probe_openalex(), probe_pubmed(), probe_arxiv(), probe_s2()
    )
    names = ["openalex_filter", "pubmed_ids", "arxiv_compact", "s2_downgrade"]
    print("PROBE-VERDICTS:", dict(zip(names, r)))


if __name__ == "__main__":
    asyncio.run(main())
