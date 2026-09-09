"""Regenerate the manuscript reference list in Vancouver/ICMJE style.

Reads the current reference section of reports/manuscript_draft.md, keeps every
factual element (title, venue, year, DOI/arXiv identifier, numbering), and
rebuilds only the AUTHOR backbone from synthesis/_manuscript_authors_cache.json
as "Surname AB, Surname CD, ... , et al." (first 6 authors then "et al." per
ICMJE/Vancouver), strips the "Workspace: SCI-xxxx" provenance tokens (moved to
reports/supplementary_references.md), and normalizes venue strings.

Usage:
    uv run python scripts/restyle_references_vancouver.py            # review (prints)
    uv run python scripts/restyle_references_vancouver.py --write   # apply to manuscript
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WS = ROOT / "workspaces" / "ai-research-harnesses-trust"
MANUSCRIPT = WS / "reports/manuscript_draft.md"
CACHE = WS / "synthesis/_manuscript_authors_cache.json"

HEADER = "## References\n\n"

RE_REF = re.compile(
    r"^\[(?P<num>\d+)\]\s*(?P<body>.*)$"
)
RE_DOI = re.compile(r"DOI:\s*(10\.\S+?)\s*[.\s]*(?:Workspace|$)")
RE_ARXIV = re.compile(r"arXiv:\s*([0-9]{4}\.[0-9]{4,5})")
RE_YEAR = re.compile(r"\((\d{4})\)")
RE_WORKSPACE = re.compile(r"Workspace:\s*(SCI-\d+)")
RE_ITALS = re.compile(r"\*([^*]+)\*")


def initials(given: str) -> str:
    """Given-name initials in Vancouver form (no periods, hyphen-preserved)."""
    out: list[str] = []
    for token in given.replace("-", " ").replace("‐", " ").split():
        token = token.strip("., ")
        if not token:
            continue
        if token in {"Md", "MD", "md"} or token.lower() == "mohammed":
            continue
        out.append(token[0].upper())
    return "".join(out)


def casify(token: str) -> str:
    """Preserve camel-case / Mc-prefixed surnames; fall back to title case only for ALL-CAPS."""
    if token.isupper() and len(token) > 1:
        return token.title()
    return token


def name_to_vancouver(raw: str) -> str:
    """One cache entry -> 'Surname AB'. Handles 'Surname, Given' and 'Given Surname'."""
    raw = raw.strip().strip(",")
    if not raw:
        return ""
    if raw == "Md Aidul Islam":
        return "Islam MA"
    if "," in raw:
        fam, _, given = raw.partition(",")
        return f"{casify(fam.strip())} {initials(given)}".rstrip()
    # Given-name sequence ending in the surname (arXiv/OpenAlex display order).
    tokens = raw.split()
    if len(tokens) == 1:
        return casify(tokens[0])
    given = " ".join(tokens[:-1])
    fam = casify(tokens[-1])
    return f"{fam} {initials(given)}".rstrip()


def vancouver_authors(names: list[str]) -> str:
    authors = [n for n in (name_to_vancouver(x) for x in names) if n]
    if len(authors) <= 6:
        return ", ".join(authors) + "."
    return ", ".join(authors[:6]) + ", et al."


def venue_norm(venue: str) -> str:
    venue = venue.strip(".").strip()
    if venue in {"arXiv Preprint", "arXiv (Cornell University)"}:
        return "arXiv"
    if venue == "bioRxiv (Cold Spring Harbor Laboratory)":
        return "bioRxiv"
    return venue


def parse_ref(line: str) -> dict:
    body = RE_REF.match(line).group("body")
    m = RE_WORKSPACE.search(body)
    sci = m.group(1) if m else None
    if m:
        body = body[: m.start()].rstrip()
    mm = RE_ITALS.findall(body)
    title = ""
    venue = ""
    year = None
    if len(mm) >= 2:
        title = mm[0].strip()
        venue = mm[-1].strip()
    else:
        title = body.strip()
    ym = RE_YEAR.search(body)
    if ym:
        year = ym.group(1)
    doi_m = RE_DOI.search(body)
    arxiv_m = RE_ARXIV.search(body)
    return {
        "num": int(RE_REF.match(line).group("num")),
        "sci": sci,
        "title": title,
        "venue": venue,
        "year": year,
        "doi": doi_m.group(1).rstrip(".") if doi_m else None,
        "arxiv": arxiv_m.group(1) if arxiv_m else None,
    }


def build(mapping: dict[int, dict], cache: dict) -> str:
    lines = [HEADER]
    for num in sorted(mapping):
        r = mapping[num]
        sci = r["sci"]
        authors = []
        if sci and sci in cache:
            authors = vancouver_authors(cache[sci].get("authors", []))
        body_parts = []
        if authors:
            body_parts.append(authors)
        body_parts.append(r["title"] + ".")
        body_parts.append(venue_norm(r["venue"]) + ".")
        body_parts.append(f"({r['year']}).")
        if r["arxiv"]:
            body_parts.append(f"arXiv:{r['arxiv']}.")
        elif r["doi"]:
            body_parts.append(f"doi: {r['doi']}.")
        if r["sci"] == "SCI-000159":
            body_parts.append("(preprint version of ref [5]. doi: 10.1038/s41586-025-10072-4)")
        lines.append(f"[{num}] " + " ".join(body_parts))
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply to manuscript")
    args = ap.parse_args()

    text = MANUSCRIPT.read_text(encoding="utf-8")
    idx = text.index(HEADER)
    body = text[:idx]
    ref_lines = text[idx + len(HEADER):].splitlines()
    entries = [ln for ln in ref_lines if RE_REF.match(ln)]
    mapping = {parse_ref(ln)["num"]: parse_ref(ln) for ln in entries}
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    new_tail = build(mapping, cache)

    missing = [n for n, r in mapping.items() if r["sci"] not in cache]
    if missing:
        print(f"WARN: no cache authors for refs {missing}", file=sys.stderr)

    if args.write:
        MANUSCRIPT.write_text(body + new_tail, encoding="utf-8")
        print(f"Wrote {len(mapping)} references to {MANUSCRIPT}")
    else:
        print(new_tail)
        print(f"\n--- {len(mapping)} refs, cache lookups: {sum(1 for r in mapping.values() if r['sci'] in cache)}/36", file=sys.stderr)


if __name__ == "__main__":
    main()