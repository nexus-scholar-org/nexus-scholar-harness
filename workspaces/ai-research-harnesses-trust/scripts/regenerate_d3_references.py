"""Regenerate the D3 manuscript reference list with resolved author metadata.

Replaces every "Corpus preprint (author metadata pending curation)" entry in
reports/manuscript_draft.md with authors from
synthesis/_manuscript_authors_cache.json, and any "Corpus preprint (author
metadata pending curation)" (2026). entry / (Workspace: SCI-xxx) references
with the resolved author list. Also adds arXiv/DOI identifiers inline where
the record carries one.

Usage:
    uv run python scripts/regenerate_d3_references.py

Idempotent; only edits the References section.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

WS = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness\workspaces\ai-research-harnesses-trust")
DRAFT = WS / "reports" / "manuscript_draft.md"
CACHE = WS / "synthesis" / "_manuscript_authors_cache.json"
INCLUDED = WS / "literature" / "included.json"


def fmt_authors(auths: list[str]) -> str:
    out = []
    for a in auths:
        a = (a or "").strip().rstrip(",").strip()
        if not a:
            continue
        if "," in a:
            last, first = a.split(",", 1)
            out.append(f"{first.strip()} {last.strip()}")
        else:
            out.append(a)
    return ", ".join(out)


def main() -> int:
    draft = DRAFT.read_text(encoding="utf-8")
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    included = json.loads(INCLUDED.read_text(encoding="utf-8"))
    byid = {r["workspace_id"]: r for r in included}

    head, sep, refs = draft.partition("## References")

    pattern = re.compile(
        r"\[(\d+)\] Corpus preprint \(author metadata pending curation\)\. "
        r"\*([^*]+)\*(?: \*([^*]+)\*)? \(([\d]{4})\)(?:.*?)\. Workspace: (SCI-\d+)"
    )

    replacements = 0
    unresolved = []

    def repl(m: re.Match) -> str:
        nonlocal replacements
        num, title, venue, year, sid = m.groups()
        if sid not in cache or not cache[sid].get("authors"):
            unresolved.append(sid)
            return m.group(0)
        auths = fmt_authors(cache[sid]["authors"])
        replacements += 1
        rec = byid.get(sid, {})
        src = rec.get("sources")
        src = src[0] if isinstance(src, list) and src else {}
        ids = []
        if src and src.get("provider") == "arxiv" and src.get("id"):
            ids.append(f"arXiv:{src['id']}")
        ext = rec.get("external_ids") or {}
        if ext.get("doi"):
            ids.append(f"DOI: {ext['doi']}")
        ids_str = (" " + "; ".join(ids) + ".") if ids else ""
        venue_str = f" *{venue}*" if venue else ""
        return (f"[{num}] {auths}. *{title}*{venue_str} ({year}).{ids_str} Workspace: {sid}")

    new_refs, _ = pattern.subn(repl, refs)
    new_draft = head + sep + new_refs

    DRAFT.write_text(new_draft, encoding="utf-8")
    print(f"references rewritten: {replacements}")
    if unresolved:
        print(f"STILL UNRESOLVED ({len(unresolved)}): {', '.join(sorted(unresolved))}")
        return 1
    print("all placeholder author-metadata references now carry resolved authors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())