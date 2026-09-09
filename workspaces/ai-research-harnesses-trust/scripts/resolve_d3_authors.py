"""Resolve author metadata for D3 preprint references from arXiv and OpenAlex.

Reads the 23 pending-author records identified in the D3 framing decision
(reports/D3_FRAMING_DECISION.md) plus any record already cached, fetches
author lists from the arXiv API (for arxiv-provider records) or the OpenAlex
works API (for openalex-provider records), and merges results into
synthesis/_manuscript_authors_cache.json.

Usage:
    uv run python scripts/resolve_d3_authors.py [--refresh]

Deterministic, network-only (no LLM). Skips records already cached unless
--refresh is given. Writes a summary line per record and a final count.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

WS = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness\workspaces\ai-research-harnesses-trust")
INCLUDED = WS / "literature" / "included.json"
CACHE = WS / "synthesis" / "_manuscript_authors_cache.json"

UA = {"User-Agent": "nexus-scholar-harness/1.0 (academic meta-review; mailto:zertal.soumia@univ-oeb.dz)"}

# The 23 pending-author records from the D3 draft (SCI IDs, all preprint-track).
PENDING_AUTHOR_SCI_IDS = (
    "SCI-000182 SCI-000144 SCI-000159 SCI-000126 SCI-000137 SCI-000106 SCI-000099 "
    "SCI-000102 SCI-000118 SCI-000135 SCI-000142 SCI-000096 SCI-000127 SCI-000100 "
    "SCI-000138 SCI-000110 SCI-000140 SCI-000108 SCI-000151 SCI-000111 SCI-000141 "
    "SCI-000115 SCI-000117"
).split()


def http_get(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def arxiv_authors(arxiv_id: str) -> list[str]:
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": arxiv_id})
    xml = http_get(url)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    entry = root.find("a:entry", ns)
    if entry is None:
        return []
    return [a.text or "" for a in entry.findall("a:author/a:name", ns)]


def openalex_authors(work_id: str) -> list[str]:
    url = "https://api.openalex.org/works/" + urllib.parse.quote_plus(work_id)
    data = json.loads(http_get(url))
    return [a["author"]["display_name"] for a in data.get("authorships", [])]


def source_of(record: dict):
    src = record.get("sources")
    if isinstance(src, list):
        for s in src:
            if isinstance(s, dict):
                return s
    return None


def resolve(record: dict):
    src = source_of(record)
    if not src:
        return []
    provider = src.get("provider") or ""
    rid = src.get("id") or ""
    if "arxiv" in provider:
        return arxiv_authors(rid)
    if "openalex" in provider or rid.startswith("https://openalex.org/"):
        return openalex_authors(rid)
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-resolve even if already cached")
    args = ap.parse_args()

    included = json.loads(INCLUDED.read_text(encoding="utf-8"))
    records = {r["workspace_id"]: r for r in included}

    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        cache = {}

    targets = [sid for sid in PENDING_AUTHOR_SCI_IDS if sid in records]
    fetched = 0
    skipped = 0
    failed = []

    for sid in targets:
        if not args.refresh and cache.get(sid, {}).get("authors"):
            skipped += 1
            continue
        rec = records[sid]
        try:
            authors = resolve(rec)
            if authors:
                cache.setdefault(sid, {})
                cache[sid].setdefault("year", rec.get("year"))
                cache[sid]["authors"] = authors
                cache[sid]["source"] = (source_of(rec) or {}).get("provider", "")
                fetched += 1
                print(f"  [ok]   {sid} ({', '.join(authors[:2])}… {len(authors)} authors)")
            else:
                failed.append(sid)
                print(f"  [miss] {sid} — no authors returned")
        except Exception as exc:  # noqa: BLE001
            failed.append(sid)
            print(f"  [err]  {sid} — {type(exc).__name__}: {str(exc)[:120]}")
        time.sleep(0.4)  # polite rate limiting (arXiv API etiquette)

    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    still_pending = [sid for sid in targets if not cache.get(sid, {}).get("authors")]
    print(f"\nfetched={fetched} cached-before={skipped} failures={len(failed)}")
    if still_pending:
        print(f"REMAINING WITHOUT AUTHORS ({len(still_pending)}): {', '.join(still_pending)}")
        return 1
    print(f"all {len(targets)} target records now carry author metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())