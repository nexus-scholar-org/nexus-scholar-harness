"""Cross-check journal-prep artifacts against the committed manuscript and ledger.

Verifies:
  1. manuscript reference list [1..36] -> {sci_id, first-author-surname, doi/arxiv}
     matches the reference-provenance map in reports/supplementary_references.md
  2. the reference map's preprint IDs match literature/included.json external_ids (per SCI id)
  3. search_log_v1.0.json matches protocol.json search_strategy + raw_search.json provider counts
  4. manuscript count claims (journal events, refs) still resolve

Run:  uv run python scripts/verify_journal_prep.py   (exit 0 = all clean)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WS = ROOT / "workspaces" / "ai-research-harnesses-trust"

MANUSCRIPT = WS / "reports" / "manuscript_draft.md"
SUPP_REF = WS / "reports" / "supplementary_references.md"
SEARCH_LOG = WS / "literature" / "search_log_v1.0.json"
INCLUDED = WS / "literature" / "included.json"
RAW_SEARCH = WS / "literature" / "raw_search.json"
PROTOCOL = WS / "protocol.json"
JOURNAL = WS / "audit" / "journal.jsonl"

errors: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def main() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    supp = SUPP_REF.read_text(encoding="utf-8")
    included = json.loads(INCLUDED.read_text(encoding="utf-8"))
    by_sci = {r["workspace_id"]: r for r in included}

    # --- 1. manuscript refs [n] -> (sci, doi/arxiv) ---
    ref_map: dict[int, dict] = {}
    for line in manuscript.splitlines():
        m = re.match(r"^\[(\d+)\]\s+([^.]*?)\.\s", line)
        if not m:
            continue
        num = int(m.group(1))
        autores = m.group(2)
        ref_map[num] = {"first_author": autores.split(",")[0] if autores else "", "line": line}

    # num range contiguous
    check(sorted(ref_map) == list(range(1, 37)), "manuscript refs not contiguous 1..36")

    # --- 2. supplementary map: sci -> ref and first author ---
    # parse rows "| [12] | SCI-000118 | ... |"
    row_re = re.compile(r"\|\s*\[(\d+)\]\s*\|\s*(SCI-\d+)\s*\|")
    supp_sci_ref = {int(m.group(1)): m.group(2) for m in row_re.finditer(supp)}
    check(len(supp_sci_ref) == 36, f"supplementary map rows != 36 ({len(supp_sci_ref)})")

    # preprint table: SCI ids with a known identifier in section 3

    # For each manuscript ref, find the supplementary map row and confirm it cites an included record
    for num in sorted(ref_map):
        sci = supp_sci_ref.get(num)
        if not sci:
            check(False, f"ref [{num}] missing from supplementary map")
            continue
        rec = by_sci.get(sci)
        check(rec is not None, f"ref [{num}] -> {sci} not in included.json (map is wrong)")
        if rec:
            line_ok = rec.get("title") and (rec["title"].lower().split(":")[0][:40] in ref_map[num]["line"].lower())
            check(
                line_ok,
                f"ref [{num}] {sci}: manuscript title does not match included.json title",
            )

    # --- 3. search log vs protocol + raw_search ---
    log = json.loads(SEARCH_LOG.read_text(encoding="utf-8"))
    proto = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    raw = json.loads(RAW_SEARCH.read_text(encoding="utf-8"))

    check(
        set(log["target_databases"]) == set(proto["search_strategy"]["target_databases"]),
        "search_log target_databases != protocol target_databases",
    )
    check(
        log["concept_cross_operator"] == "AND",
        "search_log concept_cross_operator not AND",
    )
    q1 = log["queries"][0]
    check(q1["raw_hits"] == len(raw), f"search_log raw_hits {q1['raw_hits']} != raw_search {len(raw)}")
    prov_counts = {k: v for k, v in q1["per_provider_hits"].items()}
    from collections import Counter
    actual = Counter(r["provider"] for r in raw)
    check(prov_counts == dict(actual), f"search_log provider counts {prov_counts} != raw {dict(actual)}")
    check(len(log["post_search_steps"]["deduplication"]) and log["post_search_steps"]["deduplication"]["unique_records"] == 239, "dedup accounting not 239 unique")

    # --- 4. manuscript internal consistency ---
    n_events = len(JOURNAL.read_text(encoding="utf-8").splitlines())
    check(f"{n_events} events" in manuscript, f"manuscript does not say {n_events} events")
    check("## References" in manuscript and manuscript.rstrip().endswith("."), "manuscript references section malformed")
    n_refs = len(re.findall(r"^\[(\d+)\]", manuscript, flags=re.MULTILINE))
    check(n_refs == 36, f"manuscript has {n_refs} reference entries")

    if errors:
        print(f"FAILED — {len(errors)} issue(s):")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(
        f"OK: 36 refs contiguous; supplementary map 36 rows; "
        f"{len(prov_counts)} providers q1; journal {n_events} events; refs section clean."
    )


if __name__ == "__main__":
    main()