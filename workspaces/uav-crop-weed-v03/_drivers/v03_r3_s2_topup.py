"""S2 TOP-UP fetch — v03_r3 (researcher decision (i), later window).

S2-only, cap 200, honest keyed=no (env hard-stripped in this process), output
workspaces/uav-crop-weed-v03/calibration_v03/v03_r3_20261017_s2_topup.json (new file,
nothing overwritten). Bounded: kit-side retries + backoff; if the unauthenticated
tier stays dry (429s), records count=0 with quota_state=DRY — a legitimate
PRISMA disclosure, not an error. Fetch happens ONLY if no previous top-up file
exists unless --force is passed (idempotent).
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))

DATE_TAG = "20261017"
OUT = CAL / f"v03_r3_{DATE_TAG}_s2_topup.json"
CAP = 200
FORCE = "--force" in sys.argv


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


QUERY = build_query()


def ser_doc(doc):
    try:
        return dict(doc.__dict__)
    except Exception:
        return {"repr": str(doc)}


async def main():
    assert os.environ.get("SCHOLAR_S2_KEY") is None, (
        "top-up must run strictly keyed=no; SCHOLAR_S2_KEY is set in this process"
    )
    if OUT.exists() and not FORCE:
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        print(
            f"TOPUP-ALREADY-DONE: {OUT.name} count={prev.get('count')} "
            f"quota_state={prev.get('quota_state')} (use --force to redo)"
        )
        return

    from scholar_search.models import Query
    from scholar_search.providers import SemanticScholarProvider
    from scholar_search.exceptions import RateLimitExceededError

    p = SemanticScholarProvider()  # unauthenticated (no key in env)
    q = Query(
        text=QUERY,
        id="Q-R3-S2TOPUP",
        year_min=2020,
        year_max=2026,
        language="en",
        max_results=CAP,
    )
    docs, wall, quota_state, error = [], 0.0, "OK", None
    t0 = time.perf_counter()
    try:

        async def run():
            n = 0
            async for d in p.search(q):
                docs.append(d)
                n += 1
                if n == 1 or n % 20 == 0:
                    print(f"[s2-topup] {n} records", flush=True)

        await asyncio.wait_for(run(), timeout=420)
    except asyncio.TimeoutError:
        error = "TIMEOUT after 420s watchdog; partial kept"
        quota_state = "PARTIAL_TIMEOUT"
    except RateLimitExceededError:
        error = "RateLimitExceededError: unauthenticated tier quota DRY (per-IP shared pool)"
        quota_state = "DRY"
    except Exception as e:  # noqa: BLE001
        error = f"{type(e).__name__}: {str(e)[:300]}"
        quota_state = "ERROR"
    wall = round(time.perf_counter() - t0, 2)

    payload = {
        "executed_query": QUERY,
        "provider": "semanticscholar-topup",
        "search_implementation": "patched_post-L1L6+r2fixes+pubmednorm+stemlex",
        "keyed": "no",
        "year_min": 2020,
        "year_max": 2026,
        "max_results": CAP,
        "dedup": False,
        "wall_seconds": wall,
        "status": "SUCCESS"
        if (docs and quota_state == "OK")
        else ("DRY" if quota_state == "DRY" else "PARTIAL"),
        "quota_state": quota_state,
        "count": len(docs),
        "documents": [ser_doc(d) for d in docs],
    }
    if error:
        payload["error_note"] = error
    OUT.write_text(
        json.dumps(payload, default=str, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"WROTE {OUT.name} count={len(docs)} quota_state={quota_state} wall={wall}s "
        f"error={error!r}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
