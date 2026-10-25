"""r2 harvest driver (UAV-HARVEST-R3-20261017, verification pass).

Same proven structure as v03_harvest.py; changes:
- Outputs: v03_r3_20261017_raw_<provider>.json + v03_r3_run_manifest.json.
- PLAN per researcher decision (b): openalex cap 1000 -> 2000 (strict
  title_and_abstract.search universe = 1344, exhausts below cap); other
  caps unchanged (crossref 1000, arxiv 200, pubmed 200, s2 200).
- Runs against the 4-fix-patched kit (pubmed scoped IDs, openalex strict
  filter, S2 403 downgrade, arxiv compaction, OA-first hydration).
"""

import asyncio
import json
import os
import time
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"
PROTOCOL = ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json"

DATE_TAG = "20261017"
SESSION = "UAV-HARVEST-R3-20261017"
CODE_LABEL = "patched_post-L1L6+r2fixes+pubmednorm+stemlex"
YEAR_MIN, YEAR_MAX = 2020, 2026


def build_query():
    proto = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cc = proto["search_strategy"]["core_concepts"]
    clusters = []
    for c in cc:
        ops = (c.get("boolean_operator") or "OR").upper()
        terms = [c["concept"]] + list(c["synonyms"])
        clusters.append((" " + ops + " ").join(f'"{t}"' for t in terms))
    return "(" + ") AND (".join(clusters) + ")"


QUERY = build_query()

# PLAN: (label, provider class name, cap, timeout_s, progress_every)
PLAN = [
    ("openalex", "OpenAlexProvider", 2000, 420, 200),
    ("crossref", "CrossrefProvider", 1000, 300, 100),
    ("arxiv", "ArxivProvider", 200, 300, 20),
    ("pubmed", "PubMedProvider", 200, 240, 10),
    ("semanticscholar", "SemanticScholarProvider", 200, 420, 20),
]


def ser_doc(doc):
    try:
        return dict(doc.__dict__)
    except Exception:
        return {"repr": str(doc)}


async def harvest_one(label, provider_cls_name, cap, timeout_s, progress_every):
    from scholar_search import providers as prov_mod
    from scholar_search.models import Query

    provider = getattr(prov_mod, provider_cls_name)()
    q = Query(
        text=QUERY,
        id="Q-R3-" + label,
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
        language="en",
        max_results=cap,
    )
    docs = []

    def progress_callback(provider_name, count):
        if count == 1 or count % progress_every == 0:
            print(f"[{label}] {provider_name}: {count} records", flush=True)

    async def run_gen():
        n = 0
        async for doc in provider.search(q):
            docs.append(doc)
            n += 1
            progress_callback(provider.name, n)

    t0 = time.perf_counter()
    error_note = None
    status = "SUCCESS"
    try:
        await asyncio.wait_for(run_gen(), timeout=timeout_s)
    except asyncio.TimeoutError:
        error_note = f"TIMEOUT after {timeout_s}s watchdog; partial kept"
        status = "PARTIAL"
    except Exception as e:  # noqa: BLE001
        error_note = f"{type(e).__name__}: {str(e)[:500]}"
        status = "PARTIAL"
    wall = round(time.perf_counter() - t0, 2)
    print(
        f"[{label}] DONE count={len(docs)} wall={wall}s status={status} error={error_note!r}",
        flush=True,
    )
    return docs, wall, status, error_note


async def main():
    keyed = os.environ.get("SCHOLAR_S2_KEY") is not None
    print(f"FULL QUERY (27 terms):\n{QUERY}", flush=True)
    print(f"KEYED(presence)={keyed}", flush=True)
    manifest = {
        "run_identity": {
            "session": SESSION,
            "date": DATE_TAG,
            "code_label": CODE_LABEL,
            "keyed": "yes" if keyed else "no",
            "note": "definitive; cumulative fixes a+b+pubmednorm+stemlex; keyed=no (env var removed for child processes)",
        },
        "protocol_fingerprint": "sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755",
        "query": QUERY,
        "providers": {},
    }
    for label, cls_name, cap, timeout_s, every in PLAN:
        docs, wall, status, error_note = await harvest_one(
            label, cls_name, cap, timeout_s, every
        )
        out = {
            "executed_query": QUERY,
            "provider": label,
            "year_min": YEAR_MIN,
            "year_max": YEAR_MAX,
            "max_results": cap,
            "dedup": False,
            "search_implementation": CODE_LABEL,
            "wall_seconds": wall,
            "status": status,
            "count": len(docs),
            "documents": [ser_doc(d) for d in docs],
        }
        if error_note:
            out["error_note"] = error_note
        fp = CAL / f"v03_r3_{DATE_TAG}_raw_{label}.json"
        fp.write_text(
            json.dumps(out, default=str, ensure_ascii=False), encoding="utf-8"
        )
        print(f"WROTE {fp.name} count={len(docs)} status={status}", flush=True)
        manifest["providers"][label] = {
            "count": len(docs),
            "elapsed_s": wall,
            "status": status,
            "partial": status == "PARTIAL",
            "cap": cap,
            "error_note": error_note,
        }
    total = sum(m["count"] for m in manifest["providers"].values())
    manifest["total_raw_records"] = total
    manifest["run_status"] = "FAILED_EMPTY" if total == 0 else "SUCCESS"
    (DRIVERS / "v03_r3_run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"WROTE v03_r3_run_manifest.json total_raw={total}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

