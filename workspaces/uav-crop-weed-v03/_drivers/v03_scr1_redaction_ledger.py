# -*- coding: utf-8 -*-
"""Task #3: moderation-redaction burden by provider (scr1 calibration).

Sources of truth for abstract-withheld records:
  (a) screening_scr1/moderation_views/*.view.json   (records with moderation_redacted: true)
  (b) screening_scr1/verification_lane/packs/pack_*.view3.json (per-record moderation_redacted flags)

Candidate redaction set = union of (a) and (b) flagged SCI ids, excluding
explicit disagreements (record present in both sources where exactly one
flags moderation_redacted true). Disagreements are reported separately.

Output: calibration_v03/v03_scr1_redaction_ledger.json (utf-8 no BOM, indent 1)
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "calibration_v03"
SCR1 = BASE / "screening_scr1"
CORPUS = BASE / "v03_r3e_20261017_deduped.json"
OUT = BASE / "v03_scr1_redaction_ledger.json"
RE_SCI = re.compile(r"SCI-(\d+)")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    corpus = load_json(CORPUS)
    docs = corpus["documents"]

    # SCI-N -> documents[N-1] (verified mapping)
    n_docs = len(docs)
    corpus_by_num = {i + 1: docs[i] for i in range(n_docs)}

    # ---- (a) moderation_views ----
    views_flagged = {}  # sci_num -> dict(meta)
    views_seen = set()  # all sci ids seen in moderation_views
    for p in sorted((SCR1 / "moderation_views").glob("*.view.json")):
        d = load_json(p)
        for rec in d.get("records", []):
            m = RE_SCI.match(rec.get("screening_id", ""))
            if not m:
                continue
            num = int(m.group(1))
            views_seen.add(num)
            flags = bool(rec.get("moderation_redacted"))
            terms = rec.get("moderation_terms") or []
            if flags:
                views_flagged[num] = {
                    "terms": terms,
                    "abstract_effectively_null": bool(
                        rec.get("abstract_effectively_null")
                    ),
                }

    # ---- (b) T4 ver.3 pack flags ----
    pack_flagged = {}
    pack_seen = {}
    for p in sorted((SCR1 / "verification_lane" / "packs").glob("pack_*.view3.json")):
        d = load_json(p)
        for rec in d.get("records", []):
            m = RE_SCI.match(rec.get("screening_id", ""))
            if not m:
                continue
            num = int(m.group(1))
            pack_seen[num] = bool(rec.get("moderation_redacted"))
            if pack_seen[num]:
                pack_flagged[num] = {"terms": rec.get("moderation_terms") or []}

    # ---- reconcile ----
    both_flagged = sorted(set(views_flagged) & set(pack_flagged))
    views_only = sorted(set(views_flagged) - set(pack_seen))
    pack_only = sorted(set(pack_flagged) - set(views_seen))
    conflicts = sorted(
        n
        for n in (set(views_seen) & set(pack_seen))
        if bool(views_flagged.get(n)) != pack_seen[n]
    )

    candidate = sorted(set(views_flagged) | set(pack_flagged))
    agree_set = both_flagged

    # ---- decisions A1/A2 -> lanes ----
    dec = {}  # num -> {screener: (decision, reason_code)}
    for p in sorted((SCR1 / "decisions").glob("*_decisions_*.json")):
        d = load_json(p)
        screener = d.get("screener_id")
        for row in d.get("decisions", []):
            m = RE_SCI.match(row.get("screening_id", ""))
            if not m:
                continue
            dec.setdefault(int(m.group(1)), {})[screener] = (
                row.get("decision", "").upper(),
                row.get("reason_code", ""),
            )

    def lane(num):
        rows = dec.get(num, {})
        a1 = rows.get("A1", (None, None))[0]
        a2 = rows.get("A2", (None, None))[0]
        vals = [v for v in (a1, a2) if v]
        if all(v == "INCLUDE" for v in vals) and len(vals) == 2:
            return "mutual_include"
        if all(v == "EXCLUDE" for v in vals) and len(vals) == 2:
            return "mutual_exclude"
        if any(v == "PENDING" for v in vals) or len(vals) < 2:
            return "pending_or_missing"
        if len(set(vals)) > 1:
            return "conflict"
        return "pending_or_missing"

    lane_names = ["mutual_include", "mutual_exclude", "pending_or_missing", "conflict"]

    # ---- provider grouping + stats ----
    def prov_of(num):
        doc = corpus_by_num.get(num)
        return doc["provider"] if doc else "UNKNOWN"

    corp_provider_count = Counter(d["provider"] for d in docs)
    corp_provider_empty_abs = Counter(
        d["provider"] for d in docs if not (d.get("abstract") or "").strip()
    )

    # raw corpus: no moderation marker in moderation_views and empty abstract field
    raw_empty_ids = sorted(
        num
        for num, doc in corpus_by_num.items()
        if num not in views_flagged and not (doc.get("abstract") or "").strip()
    )
    raw_empty_by_provider = Counter(prov_of(n) for n in raw_empty_ids)

    red_by_provider = Counter(prov_of(n) for n in candidate)
    red_year = Counter(
        (corpus_by_num[n].get("year") if n in corpus_by_num else None)
        for n in candidate
    )

    lane_dist = Counter(lane(n) for n in candidate)
    red_lane_members = defaultdict(list)
    for n in candidate:
        red_lane_members[lane(n)].append(n)

    # reason codes of redacted records in exclusion lanes (either screener row EXCLUDE)
    reason_counts = Counter()
    moderation_title_only = Counter()
    exclusion_lane_ids = [
        n for n in candidate if lane(n) in ("mutual_exclude", "conflict")
    ]
    for n in exclusion_lane_ids:
        seen_for_num = set()
        for screener, (decision, reason) in dec.get(n, {}).items():
            if decision == "EXCLUDE" and reason:
                reason_counts[reason] += 1
                if reason.startswith("MODERATION_TITLE_ONLY"):
                    moderation_title_only[screener] += 1

    provs = sorted(corp_provider_count)
    provider_section = {}
    for pv in provs:
        total = corp_provider_count[pv]
        red = red_by_provider.get(pv, 0)
        provider_section[pv] = {
            "corpus_docs": total,
            "redacted_count": red,
            "redacted_share_of_provider": round(red / total, 4) if total else None,
            "raw_corpus_abstract_empty_count_no_moderation": raw_empty_by_provider.get(
                pv, 0
            ),
            "raw_corpus_abstract_empty_share_no_moderation": round(
                raw_empty_by_provider.get(pv, 0) / total, 4
            )
            if total
            else None,
        }

    result = {
        "task": "v03 scr1 moderation-redaction burden by provider",
        "corpus_size": n_docs,
        "sources": {
            "moderation_views_flagged": len(views_flagged),
            "t4_view3_pack_flagged": len(pack_flagged),
            "agreement_both_flagged": len(both_flagged),
            "views_only_not_in_packs": len(views_only),
            "pack_only": len(pack_only),
            "explicit_disagreements": len(conflicts),
            "candidate_set_union_minus_conflicts": len(candidate),
        },
        "disagreement_ids": conflicts,
        "views_only_ids": views_only,
        "pack_only_ids": pack_only,
        "provider_stats": provider_section,
        "corpus_provider_totals": dict(corp_provider_count),
        "raw_corpus_abstract_empty_count_no_moderation": sum(
            raw_empty_by_provider.values()
        ),
        "redacted_lane_distribution": {
            ln: {
                "count": lane_dist.get(ln, 0),
                "share": round(lane_dist.get(ln, 0) / len(candidate), 4)
                if candidate
                else None,
            }
            for ln in lane_names
        },
        "redacted_lane_members": {
            ln: red_lane_members.get(ln, []) for ln in lane_names
        },
        "exclusion_lane_reason_codes": {
            "exclusion_lane_redacted_ids": exclusion_lane_ids,
            "reason_code_counts": dict(reason_counts.most_common()),
            "MODERATION_TITLE_ONLY": {
                "total": moderation_title_only.get("A1", 0)
                + moderation_title_only.get("A2", 0),
                "by_screener": {
                    "A1": moderation_title_only.get("A1", 0),
                    "A2": moderation_title_only.get("A2", 0),
                },
            },
        },
        "redacted_counts_by_year": {
            str(y): c
            for y, c in sorted(red_year.items(), key=lambda kv: (kv[0] is None, kv[0]))
        },
    }

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print("=== v03 scr1 moderation-redaction ledger ===")
    print(
        f"candidate redacted set: {len(candidate)} "
        f"(views={len(views_flagged)}, packs={len(pack_flagged)}, both={len(both_flagged)}, "
        f"conflicts={len(conflicts)})"
    )
    for pv in provs:
        s = provider_section[pv]
        print(
            f"  {pv:12s} corpus={s['corpus_docs']:6d} redacted={s['redacted_count']:4d} "
            f"share={s['redacted_share_of_provider']:.4f} "
            f"raw_empty(no mod)={s['raw_corpus_abstract_empty_count_no_moderation']:6d} "
            f"({s['raw_corpus_abstract_empty_share_no_moderation']:.4f})"
        )
    print("lanes:", {ln: lane_dist.get(ln, 0) for ln in lane_names})
    print("exclusion-lane reason codes:", dict(reason_counts.most_common()))
    print(
        "MODERATION_TITLE_ONLY:",
        result["exclusion_lane_reason_codes"]["MODERATION_TITLE_ONLY"],
    )
    print(
        "years:", {k: v for k, v in sorted(result["redacted_counts_by_year"].items())}
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
