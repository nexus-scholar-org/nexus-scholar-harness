"""r3 OpenAlex universe re-probe: strict title_and_abstract.search meta count.

Captures the live filter universe at r3 time to quantify REFERENCE-DRIFT
against the r2-time probe (1344) and the r3 fetched 1342/1343.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))


def build_query():
    import json

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


async def main():
    from scholar_search.http_client import AcademicHttpClient
    from scholar_search.config import settings
    import re

    q = build_query()
    p = AcademicHttpClient(name="r3-universe-probe", rate_limit=2.0)
    params = {
        "mailto": settings.mailto,
        "per-page": 1,
        "filter": f"from_publication_date:2020-01-01,to_publication_date:2026-12-31,title_and_abstract.search:{q}",
    }
    if settings.openalex_key:
        params["api_key"] = settings.openalex_key
    r = await p.get("https://api.openalex.org/works", params=params)
    meta = r.json().get("meta", {})
    print(
        f"R3-UNIVERSE-PROBE: http={r.status_code} title_and_abstract.search total={meta.get('count')} "
        f"(r2-time probe=1344; r3 fetched=1343)"
    )
    await p.close()


if __name__ == "__main__":
    asyncio.run(main())
