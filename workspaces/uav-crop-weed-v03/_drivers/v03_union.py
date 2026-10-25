"""v0.3 union + hydration + dedup driver (UAV-HARVEST-V03-PATCHED-20261017).

Adapted from the proven Temp driver `uav_mp_union.py`. Changes:
- ROOT = demo clone; SOURCES = the 5 v03 raw files from Phase 1.
- Outputs into workspaces/uav-crop-weed-v03/calibration_v03/
  (v03_20261017_union_raw.json / v03_20261017_union_hydrated.json /
  v03_20261017_deduped.json).
- Hydration via patched AbstractHydrator (OpenAlex pipe-batch 50; S2 batch
  with x-api-key when keyed).
- Dedup via patched Deduplicator (preprint/repo-DOI XOR logic).

Config ONLY from process env. Never prints or persists secret values.
"""

import asyncio
import json
import os
import re
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"

DATE_TAG = "20261017"
SESSION = "UAV-HARVEST-V03-PATCHED-20261017"

# SOURCES: the 5 v03 raw filenames from Phase 1.
SOURCES = [
    ("openalex-full", f"v03_{DATE_TAG}_raw_openalex.json"),
    ("semanticscholar", f"v03_{DATE_TAG}_raw_semanticscholar.json"),
    ("crossref-full", f"v03_{DATE_TAG}_raw_crossref.json"),
    ("arxiv-full", f"v03_{DATE_TAG}_raw_arxiv.json"),
    ("pubmed", f"v03_{DATE_TAG}_raw_pubmed.json"),
]

DOI_RE = re.compile(r"doi=(?:'([^']*)'|\"([^\"]*)\"|None)")
ARXIV_RE = re.compile(r"arxiv_id=(?:'([^']*)'|\"([^\"]*)\"|None)")
PUBMED_RE = re.compile(r"pubmed_id=(?:'([^']*)'|\"([^\"]*)\"|None)")
OA_RE = re.compile(r"openalex_id=(?:'([^']*)'|\"([^\"]*)\"|None)")
S2_RE = re.compile(r"s2_id=(?:'([^']*)'|\"([^\"]*)\"|None)")
AUTHOR_RE = re.compile(
    r"Author\(family_name=(?:'([^']*)'|\"([^\"]*)\"|None),\s*"
    r"given_name=(?:'([^']*)'|\"([^\"]*)\"|None),\s*"
    r"orcid=(?:'([^']*)'|\"([^\"]*)\"|None)\)"
)


def clean(v):
    if v is None or v == "None" or v == "":
        return None
    return v


def pick(m):
    if not m:
        return None
    for g in m.groups():
        if g is not None:
            return clean(g)
    return None


def parse_external_ids(s):
    from scholar_search.models import ExternalIds

    if isinstance(s, dict):
        return ExternalIds(
            doi=clean(s.get("doi")),
            arxiv_id=clean(s.get("arxiv_id")),
            pubmed_id=clean(s.get("pubmed_id")),
            openalex_id=clean(s.get("openalex_id")),
            s2_id=clean(s.get("s2_id")),
        )
    s = str(s or "")
    return ExternalIds(
        doi=pick(DOI_RE.search(s)),
        arxiv_id=pick(ARXIV_RE.search(s)),
        pubmed_id=pick(PUBMED_RE.search(s)),
        openalex_id=pick(OA_RE.search(s)),
        s2_id=pick(S2_RE.search(s)),
    )


def parse_authors(raw):
    from scholar_search.models import Author

    authors = []
    if not raw:
        return authors
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        for a in raw:
            try:
                authors.append(
                    Author(
                        family_name=str(a.get("family_name", "?")),
                        given_name=a.get("given_name"),
                        orcid=a.get("orcid"),
                    )
                )
            except Exception:
                continue
        return authors
    for item in raw if isinstance(raw, list) else [raw]:
        if not isinstance(item, str):
            continue
        for m in AUTHOR_RE.finditer(item):
            fam = m.group(1) if m.group(1) is not None else m.group(2)
            giv = m.group(3) if m.group(3) is not None else m.group(4)
            orc = m.group(5) if m.group(5) is not None else m.group(6)
            try:
                authors.append(
                    Author(
                        family_name=fam or "?", given_name=clean(giv), orcid=clean(orc)
                    )
                )
            except Exception:
                continue
    return authors


def rebuild(raw, skipped):
    from scholar_search.models import Document

    try:
        doc = Document(
            title=raw.get("title") or "Untitled",
            year=raw.get("year"),
            provider=raw.get("provider") or "unknown",
            provider_id=raw.get("provider_id") or "",
            external_ids=parse_external_ids(raw.get("external_ids")),
            abstract=raw.get("abstract"),
            authors=parse_authors(raw.get("authors")),
            venue=raw.get("venue"),
            url=raw.get("url"),
            workspace_id=raw.get("workspace_id"),
            sources=list(raw.get("sources") or []),
            oa_locations=list(raw.get("oa_locations") or []),
            citations_count=raw.get("citations_count"),
            references_count=raw.get("references_count"),
            citation_intents=list(raw.get("citation_intents") or []),
            mesh_terms=list(raw.get("mesh_terms") or []),
            tldr=raw.get("tldr"),
            topics=raw.get("topics"),
            query_id=raw.get("query_id"),
            retrieved_at=raw.get("retrieved_at"),
            cluster_id=raw.get("cluster_id"),
            raw_data=raw.get("raw_data"),
        )
        return doc
    except Exception as e:  # noqa: BLE001 - isolate bad record, keep going
        skipped.append(str(e)[:200])
        return None


def ser_doc(doc):
    try:
        return dict(doc.__dict__)
    except Exception:
        return {"repr": str(doc)}


def has_abstract(d):
    a = d.get("abstract") if isinstance(d, dict) else getattr(d, "abstract", None)
    return bool((a or "").strip())


def has_doi(d):
    ext = (
        d.get("external_ids")
        if isinstance(d, dict)
        else getattr(d, "external_ids", None)
    )
    doi = ext.get("doi") if isinstance(ext, dict) else getattr(ext, "doi", None)
    return bool(clean(doi))


async def hydrate_isolated(hydrator, docs):
    """Try whole-list hydration; on raise, split recursively to isolate bad records."""
    try:
        return await hydrator.hydrate_missing_abstracts(docs, batch_size=50)
    except Exception as e:  # noqa: BLE001
        if len(docs) <= 1:
            return docs, {
                "attempted": len(docs),
                "hydrated": 0,
                "failed": len(docs),
                "isolated_error": str(e)[:200],
            }
        mid = len(docs) // 2
        d1, s1 = await hydrate_isolated(hydrator, docs[:mid])
        d2, s2 = await hydrate_isolated(hydrator, docs[mid:])
        merged = {
            "attempted": s1.get("attempted", 0) + s2.get("attempted", 0),
            "hydrated": s1.get("hydrated", 0) + s2.get("hydrated", 0),
            "failed": s1.get("failed", 0) + s2.get("failed", 0),
            "isolated_splits": True,
        }
        return d1 + d2, merged


def dedup_isolated(dedup, docs):
    try:
        return dedup.deduplicate(docs), None
    except Exception as e:  # noqa: BLE001
        if len(docs) <= 1:
            return [], str(e)[:200]
        mid = len(docs) // 2
        c1, e1 = dedup_isolated(dedup, docs[:mid])
        c2, e2 = dedup_isolated(dedup, docs[mid:])
        note = "; ".join(x for x in [e1, e2] if x) or "split-fallback"
        return c1 + c2, f"dedup split fallback used: {note}"


async def main():
    from scholar_search.dedup import Deduplicator
    from scholar_search.enrichment import AbstractHydrator
    from scholar_search.http_client import AcademicHttpClient

    keyed = "yes" if os.environ.get("SCHOLAR_S2_KEY") else "no"
    print(f"KEYED={keyed} (presence only)", flush=True)

    per_source_counts, raw_docs_all, file_counts = {}, [], {}
    for label, fname in SOURCES:
        payload = json.loads((CAL / fname).read_text(encoding="utf-8"))
        docs = payload.get("documents", [])
        file_counts[label] = payload.get("count")
        per_source_counts[label] = len(docs)
        raw_docs_all.extend(docs)
        print(
            f"READ {fname}: count-field={payload.get('count')} docs={len(docs)}",
            flush=True,
        )

    union_count = len(raw_docs_all)
    cov_before = sum(1 for d in raw_docs_all if has_abstract(d))
    doi_before = sum(1 for d in raw_docs_all if has_doi(d))
    in_window = sum(
        1
        for d in raw_docs_all
        if isinstance(d.get("year"), int) and 2020 <= d.get("year") <= 2026
    )
    raw_out = {
        "sources": [label for label, _ in SOURCES],
        "per_source_counts": per_source_counts,
        "file_count_fields": file_counts,
        "union_count": union_count,
        "abstract_coverage_before": {
            "with_abstract": cov_before,
            "without_abstract": union_count - cov_before,
        },
        "doi_less": union_count - doi_before,
        "in_window_2020_2026": in_window,
        "documents": raw_docs_all,
    }
    (CAL / f"v03_{DATE_TAG}_union_raw.json").write_text(
        json.dumps(raw_out, default=str, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"WROTE raw union={union_count} (sum={sum(per_source_counts.values())}) "
        f"abstracts={cov_before} doi-less={union_count - doi_before}",
        flush=True,
    )

    skipped = []
    live = [d for d in (rebuild(r, skipped) for r in raw_docs_all) if d is not None]
    print(f"REBUILT live={len(live)} skipped={len(skipped)}", flush=True)

    needs = [d for d in live if not has_abstract(d)]
    print(f"HYDRATION attempting: {len(needs)} records missing abstract", flush=True)
    hydrator_client = AcademicHttpClient(name="abstract-hydrator", rate_limit=1.0)
    hydrator = AbstractHydrator(hydrator_client)
    live_h, hstats = await hydrate_isolated(hydrator, live)
    try:
        await hydrator_client.close()
    except Exception:
        pass
    cov_after = sum(1 for d in live_h if (d.abstract or "").strip())
    hyd_out = {
        "hydration_stats": hstats,
        "abstract_coverage_before": {
            "with_abstract": cov_before,
            "without_abstract": union_count - cov_before,
        },
        "abstract_coverage_after": {
            "with_abstract": cov_after,
            "without_abstract": len(live_h) - cov_after,
        },
        "reconstruction_skipped": len(skipped),
        "documents": [ser_doc(d) for d in live_h],
    }
    (CAL / f"v03_{DATE_TAG}_union_hydrated.json").write_text(
        json.dumps(hyd_out, default=str, ensure_ascii=False), encoding="utf-8"
    )
    print(f"HYDRATION stats={hstats} coverage {cov_before}->{cov_after}", flush=True)

    dedup = Deduplicator()
    clusters, derr = dedup_isolated(dedup, live_h)
    stats = (
        dedup.get_statistics(clusters)
        if clusters
        else {
            "total_documents": 0,
            "unique_documents": 0,
            "duplicates": 0,
            "duplicate_rate": 0.0,
        }
    )
    singletons = sum(1 for c in clusters if getattr(c, "size", len(c.members)) == 1)
    clus_ser = []
    for c in clusters:
        try:
            members = []
            for m in c.members:
                ext = m.external_ids
                members.append(
                    {
                        "title": (m.title or "")[:120],
                        "year": m.year,
                        "provider": m.provider,
                        "doi": ext.doi if ext else None,
                    }
                )
            clus_ser.append(
                {
                    "cluster_id": c.cluster_id,
                    "size": len(c.members),
                    "representative_title": (c.representative.title or "")[:150],
                    "members": members,
                }
            )
        except Exception as e:  # noqa: BLE001
            clus_ser.append(
                {
                    "cluster_id": getattr(c, "cluster_id", None),
                    "serialization_error": str(e)[:200],
                }
            )
    ded_out = {
        "dedup_stats": stats,
        "cluster_count": len(clusters),
        "singleton_count": singletons,
        "dedup_error_note": derr,
        "reconstruction_skipped": len(skipped),
        "documents": [ser_doc(c.representative) for c in clusters],
        "clusters": clus_ser,
    }
    (CAL / f"v03_{DATE_TAG}_deduped.json").write_text(
        json.dumps(ded_out, default=str, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"DEDUP stats={stats} clusters={len(clusters)} singletons={singletons} err={derr!r}",
        flush=True,
    )

    # Drivers-side count summary for the report/journal.
    summary = {
        "session": SESSION,
        "keyed": keyed,
        "per_provider_docs": per_source_counts,
        "union_total": union_count,
        "reconstruction_skipped": len(skipped),
        "hydration": {
            "attempted": hstats.get("attempted"),
            "hydrated": hstats.get("hydrated"),
            "failed": hstats.get("failed"),
        },
        "abstract_coverage": {
            "before": cov_before,
            "after": cov_after,
            "still_no_abstract": len(live_h) - cov_after,
            "hydrated_pool_size": len(live_h),
        },
        "doi_less_union": union_count - doi_before,
        "dedup": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "merged": stats.get("duplicates"),
            "error_note": derr,
        },
        "in_window_2020_2026": in_window,
    }
    (DRIVERS / "v03_union_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE v03_union_summary.json", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
