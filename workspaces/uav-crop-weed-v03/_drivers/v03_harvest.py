"""v0.3 multi-provider harvest driver (UAV-HARVEST-V03-PATCHED-20261017).

Adapted from the proven Temp driver `uav_mp_harvest.py` (UAV-HARVEST-20261015-FULL-MP).

Changes vs proven driver:
- ROOT = demo clone; CAL = workspaces/uav-crop-weed-v03/calibration_v03
- QUERY built deterministically from protocol.json search_strategy.core_concepts
  (full v0.3 synonym set; passed whole to the patched kit).
- PLAN: openalex 1000/420s/100 | crossref 1000/300s/50 | arxiv 200/240s/10 |
  pubmed 200/240s/10 | semanticscholar 200/420s/50 (keyed last).
- Order: openalex -> crossref -> arxiv -> pubmed -> semanticscholar.
- Watchdog: per-provider direct generator capture; on hard error/timeout the
  partial docs are KEPT, the file is written with a PARTIAL manifest record.

Config ONLY from process env. Never prints or persists secret values.
"""

import asyncio
import json
import os
import time
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
PROTOCOL = ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"

DATE_TAG = "20261017"
SESSION = "UAV-HARVEST-V03-PATCHED-20261017"
CODE_LABEL = "patched_post-L1L6"
YEAR_MIN = 2020
YEAR_MAX = 2026


# --- deterministic query from protocol.json -------------------------------
def build_query():
    proto = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cc = proto["search_strategy"]["core_concepts"]
    dr = proto["search_strategy"]["date_range"]
    global YEAR_MIN, YEAR_MAX
    YEAR_MIN = dr["start_year"]
    YEAR_MAX = dr["end_year"]
    term_count = 0
    clusters = []
    for c in cc:
        ops = (c.get("boolean_operator") or "OR").upper()
        terms = [c["concept"]] + list(
            c["synonyms"]
        )  # concept label is part of the full v0.3 set
        term_count += len(terms)
        quoted = [f'"{t}"' for t in terms]
        clusters.append((" " + ops + " ").join(quoted))
    query = "(" + ") AND (".join(clusters) + ")"
    return query, term_count


QUERY, TERM_COUNT = build_query()

# --- PLAN: (label, provider class name, cap, timeout_s, progress_every) ----
# Change caps ONLY by editing this PLAN line before launch, never mid-run.
PLAN = [
    ("openalex", "OpenAlexProvider", 1000, 420, 100),
    ("crossref", "CrossrefProvider", 1000, 300, 50),
    ("arxiv", "ArxivProvider", 200, 240, 10),
    ("pubmed", "PubMedProvider", 200, 240, 10),
    ("semanticscholar", "SemanticScholarProvider", 200, 420, 50),  # keyed last
]


def ser_doc(doc):
    try:
        d = dict(doc.__dict__)
    except Exception:
        d = {"repr": str(doc)}
    return d


def selftest_serialization():
    from scholar_search.models import Document, ExternalIds, Author

    docs = [
        Document(
            title="Probe A",
            year=2024,
            provider="probe",
            provider_id="p1",
            external_ids=ExternalIds(doi="10.1234/probe.a"),
            abstract="Abstract text here.",
            authors=[Author(family_name="Doe", given_name="Jane")],
            venue="Probe Venue",
            url="https://example.org/a",
        ),
        Document(title="Probe B (no abstract, no doi)", year=2025, provider="probe"),
    ]
    payload = {"count": len(docs), "documents": [ser_doc(d) for d in docs]}
    s = json.dumps(payload, default=str, ensure_ascii=False)
    back = json.loads(s)
    assert back["count"] == 2 and len(back["documents"]) == 2
    assert back["documents"][0]["title"] == "Probe A"
    print("SERIALIZER_SELFTEST: PASS (2 records round-trip)", flush=True)


async def harvest_one(label, provider_cls_name, cap, timeout_s, progress_every):
    """Direct provider-generator harvest with watchdog partial capture."""
    from scholar_search import providers as prov_mod
    from scholar_search.models import Query

    provider = getattr(prov_mod, provider_cls_name)()
    q = Query(
        text=QUERY,
        id="Q-V03-" + label,
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
        language="en",
        max_results=cap,
    )

    docs = []
    state = {"count": 0}

    def progress_callback(provider_name, count):
        state["count"] = count
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
    except Exception as e:  # noqa: BLE001 - isolation: one provider must never abort others
        error_note = f"{type(e).__name__}: {str(e)[:500]}"
        status = "PARTIAL"
    wall = round(time.perf_counter() - t0, 2)
    print(
        f"[{label}] DONE count={len(docs)} wall={wall}s status={status} error={error_note!r}",
        flush=True,
    )
    return docs, wall, status, error_note


async def main():
    from scholar_search.models import Document  # noqa: F401 - import check

    mailto = os.environ.get("SCHOLAR_MAILTO")
    oakey = os.environ.get("SCHOLAR_OPENALEX_KEY")
    s2key = os.environ.get("SCHOLAR_S2_KEY")
    print(
        f"ENV(presence only): SCHOLAR_MAILTO={'set' if mailto else 'MISSING'} "
        f"SCHOLAR_OPENALEX_KEY={'set' if oakey else 'MISSING'} "
        f"SCHOLAR_S2_KEY={'set' if s2key else 'MISSING'}",
        flush=True,
    )
    print(f"FULL QUERY (term_count={TERM_COUNT}):\n{QUERY}", flush=True)
    selftest_serialization()

    manifest = {
        "run_identity": {
            "session": SESSION,
            "date": DATE_TAG,
            "code_label": CODE_LABEL,
            "search_implementation": CODE_LABEL,
            "keyed": "yes" if s2key else "no",
        },
        "protocol_fingerprint": "sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755",
        "query": QUERY,
        "query_term_count": TERM_COUNT,
        "providers": {},
        "openalex_checkpoint": None,
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
        fp = CAL / f"v03_{DATE_TAG}_raw_{label}.json"
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
        if label == "openalex" and status != "SUCCESS":
            # OPENALEX CHECKPOINT: never fall back to a keyword form silently.
            manifest["openalex_checkpoint"] = {
                "triggered": True,
                "reason": error_note or "",
                "count": len(docs),
                "exact_query": QUERY,
            }
            print(
                f"OPENALEX_CHECKPOINT: full boolean query yielded count={len(docs)} "
                f"status={status}; NOT silently falling back. Exact query recorded "
                "in manifest for human decision.",
                flush=True,
            )

    # Empty-result guard: an all-empty run is FAILED, not a pass.
    total = sum(m["count"] for m in manifest["providers"].values())
    manifest["total_raw_records"] = total
    manifest["run_status"] = "FAILED_EMPTY" if total == 0 else "SUCCESS"
    mf = DRIVERS / "v03_run_manifest.json"
    mf.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"WROTE {mf.name} total_raw={total} run_status={manifest['run_status']}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
