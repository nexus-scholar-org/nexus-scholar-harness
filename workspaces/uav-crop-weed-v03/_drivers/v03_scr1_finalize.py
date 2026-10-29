"""SCR1 FINALIZE — resolve the remaining PENDING lanes and emit the pilot's
included/excluded artifacts.

Inputs (read-only):
  calibration_v03/screening_scr1/batch_NNN.json              (14,150 records)
  calibration_v03/screening_scr1/decisions/*_A1.json|_A2.json
  calibration_v03/screening_scr1/third_lane/decisions/*.json
  calibration_v03/screening_scr1/final_lane/decisions_pass2.json

Resolution rule (documented, deterministic):
  1. A1 == A2 == INCLUDE                     -> INCLUDE  (lane mutual_include)
  2. A1 == A2 == EXCLUDE                     -> EXCLUDE  (lane mutual_exclude)
  3. otherwise the third lane decides        -> INCLUDE/EXCLUDE (lane third_lane)
  4. third lane still PENDING + usable abstract
                                             -> the pass-2 re-screen (lane pass2)
  5. third lane still PENDING + no usable abstract
                                             -> EXCLUDE with
                                                NO_USABLE_ABSTRACT_NOT_RETRIEVED
                                                (lane not_retrieved, DEV-01)

DEV-01 is a researcher instruction recorded on 2026-10-29 (delegated): records
without a usable abstract are excluded with a note instead of staying PENDING.
It deviates from INC-02/EXC-03 ("abstract=null is not a reason to exclude") and
from the Pass-1 guardrail; the deviation is recorded in the workspace and the
subset is reported separately as "not retrieved" in the PRISMA report.

Outputs:
  literature/included.json
  literature/excluded.json
  literature/screening/final_decisions.json
  literature/screening/summary.json
  literature/prisma_screening_report.md
  literature/prisma_report.json
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WS = ROOT / "workspaces" / "uav-crop-weed-v03"
SCR = WS / "calibration_v03" / "screening_scr1"
LIT = WS / "literature"

CRITERIA_SHA = "9ae1f97dc0c9857bb59eb0025924f2dd104d2c41eca2777089b22eecad90b86f"
TOTAL_IDENTIFIED = 14413  # r3d union hydrated (physical records)
DUPLICATES_REMOVED = 263  # 14,413 - 14,150

REASON_MAP = {
    "EXC-01": "WRONG_PLATFORM",
    "EXC-02": "WRONG_TASK",
    "EXC-03": "WRONG_REPORT_TYPE",
    "EXC-04": "OUTSIDE_DATE_LANGUAGE",
    "WRONG_PLATFORM": "WRONG_PLATFORM",
    "WRONG_TASK": "WRONG_TASK",
    "WRONG_REPORT_TYPE": "WRONG_REPORT_TYPE",
    "OUTSIDE_DATE_LANGUAGE": "OUTSIDE_DATE_LANGUAGE",
    "NO_USABLE_ABSTRACT_NOT_RETRIEVED": "NO_USABLE_ABSTRACT_NOT_RETRIEVED",
    "MODERATION_TITLE_ONLY_EXCLUDE": "MODERATION_TITLE_ONLY_EXCLUDE",
    "BOUNDARY_AMBIGUOUS_PLATFORM": "BOUNDARY_AMBIGUOUS_PLATFORM",
    "OUT_OF_SCOPE": "OUT_OF_SCOPE",
}

_REASON_TOKEN = re.compile(
    r"(EXC-0\d|WRONG_PLATFORM|WRONG_TASK|WRONG_REPORT_TYPE|OUTSIDE_DATE_LANGUAGE|"
    r"MODERATION_TITLE_ONLY_EXCLUDE|BOUNDARY_AMBIGUOUS_PLATFORM|OUT_OF_SCOPE|"
    r"NO_USABLE_ABSTRACT_NOT_RETRIEVED)"
)

CRITERION_OF = {
    "WRONG_PLATFORM": "EXC-01",
    "WRONG_TASK": "EXC-02",
    "WRONG_REPORT_TYPE": "EXC-03",
    "OUTSIDE_DATE_LANGUAGE": "EXC-04",
}


def normalize_reason_code(row: dict) -> str:
    """Collapse the three screener dialects (reason_code / criterion_refs /
    free-text ``reason`` prefixed with its code) onto one code vocabulary."""
    candidates: list[str] = []
    raw = (row.get("reason_code") or row.get("exclusion_reason_code") or "").strip()
    if raw:
        candidates.append(raw)
    for ref in row.get("criterion_refs") or []:
        candidates.append(str(ref).strip())
    reason = (row.get("reason") or "").strip()
    if reason:
        candidates.append(reason.split(":")[0].strip())
    for candidate in candidates:
        token = _REASON_TOKEN.search(candidate.upper())
        if token and token.group(1) in REASON_MAP:
            return REASON_MAP[token.group(1)]
    return "UNSPECIFIED"


def load_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in sorted(SCR.glob("batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload["records"]:
            records[record["screening_id"]] = record
    return records


def has_usable_abstract(record: dict) -> bool:
    abstract = (record.get("abstract") or "").strip()
    return bool(abstract) and not record.get("abstract_effectively_null")


def load_arm_decisions() -> dict[str, dict[str, dict]]:
    arms: dict[str, dict[str, dict]] = {}
    for path in sorted(SCR.glob("decisions/*.json")):
        arm = "A1" if path.name.endswith("_A1.json") else "A2"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload["decisions"]:
            arms.setdefault(row["screening_id"], {})[arm] = row
    return arms


def load_rows(pattern: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    files = sorted(SCR.glob(pattern))
    if not files:
        raise SystemExit(f"missing input: {pattern}")
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("decisions", []):
            rows[row["screening_id"]] = row
    return rows


def main() -> None:
    records = load_records()
    arms = load_arm_decisions()
    third = load_rows("third_lane/decisions/*.json")
    pass2 = load_rows("final_lane/decisions_pass2.json")

    final: list[dict] = []
    counters: Counter[str] = Counter()
    unresolved: list[str] = []

    for sid in sorted(records):
        record = records[sid]
        a1 = arms.get(sid, {}).get("A1", {}).get("decision")
        a2 = arms.get(sid, {}).get("A2", {}).get("decision")
        row = None
        lane = ""

        if a1 == a2 == "INCLUDE":
            lane, row = "mutual_include", {"decision": "INCLUDE", "reason_code": "INC-01", "confidence": 0.95}
        elif a1 == a2 == "EXCLUDE":
            lane = "mutual_exclude"
            row = arms[sid]["A1"]
        elif sid in third and third[sid].get("decision") in ("INCLUDE", "EXCLUDE"):
            lane, row = "third_lane", third[sid]
        elif sid in pass2 and pass2[sid].get("decision") in ("INCLUDE", "EXCLUDE"):
            lane, row = "pass2", pass2[sid]
        elif not has_usable_abstract(record):
            # Still unresolved after the third lane and the pass-2 re-screen, and
            # there is nothing to re-screen against -> DEV-01 no-abstract exclusion.
            lane = "not_retrieved"
            row = {
                "decision": "EXCLUDE",
                "reason_code": "NO_USABLE_ABSTRACT_NOT_RETRIEVED",
                "confidence": 1.0,
                "one_line_support": "no usable abstract; metadata insufficient to assess eligibility (DEV-01)",
            }
        else:
            unresolved.append(sid)
            continue

        decision = row["decision"]
        recorded_refs = [str(ref) for ref in row.get("criterion_refs") or []]
        if decision == "INCLUDE":
            matched = [ref for ref in recorded_refs if ref.startswith("INC")] or [
                str(row.get("reason_code") or "INC-01").split("/")[0].split(";")[0]
            ]
            matched = [ref for ref in matched if ref.startswith("INC")] or ["INC-01"]
            violated: list[str] = []
            reason_code = matched[0]
        else:
            reason_code = normalize_reason_code(row)
            violated = (
                [ref for ref in recorded_refs if ref.startswith("EXC")]
                or [CRITERION_OF.get(reason_code)]
            )
            violated = [ref for ref in violated if ref]
            matched = []
        counters[f"{lane}:{decision}"] += 1
        counters[f"reason:{reason_code}"] += 1

        item = {
            "workspace_id": sid,
            "title": record.get("title"),
            "year": record.get("year"),
            "provider": record.get("providers"),
            "doi": record.get("doi"),
            "abstract": record.get("abstract"),
            "screening": {
                "workspace_id": sid,
                "decision": decision,
                "confidence": row.get("confidence", 0.0),
                "screening_reasoning": row.get("one_line_support") or row.get("reason") or "",
                "matched_inclusion_criteria": matched,
                "violated_exclusion_criteria": violated,
                "relevant_rqs": ["RQ1", "RQ2", "RQ3", "RQ4"],
                "document_title": record.get("title") or "",
                "doi": record.get("doi"),
            },
            "screening_provenance": {
                "lane": lane,
                "reason_code": reason_code,
                "criteria_sha256": CRITERIA_SHA,
                "deviation": "DEV-01" if lane == "not_retrieved" else None,
            },
        }
        final.append(item)

    if unresolved:
        raise SystemExit(f"{len(unresolved)} record(s) without a final decision, e.g. {unresolved[:5]}")

    included = [item for item in final if item["screening"]["decision"] == "INCLUDE"]
    excluded = [item for item in final if item["screening"]["decision"] == "EXCLUDE"]
    not_retrieved = [item for item in excluded if item["screening_provenance"]["lane"] == "not_retrieved"]

    LIT.mkdir(parents=True, exist_ok=True)
    (LIT / "screening").mkdir(parents=True, exist_ok=True)
    (LIT / "included.json").write_text(json.dumps(included, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (LIT / "excluded.json").write_text(json.dumps(excluded, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (LIT / "screening" / "final_decisions.json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    reason_counts = Counter(
        item["screening_provenance"]["reason_code"] for item in excluded
    )
    summary = {
        "session": "UAV-SCREEN-SCR1-20261018",
        "criteria_sha256": CRITERIA_SHA,
        "protocol_fingerprint": "sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755",
        "decision_status": "FINAL_AGENT_UNCONFIRMED",
        "human_confirmation": "PENDING (HumanConfirmation@1 unsigned)",
        "totals": {
            "records": len(final),
            "included": len(included),
            "excluded": len(excluded),
            "not_retrieved": len(not_retrieved),
        },
        "lanes": {key: value for key, value in sorted(counters.items()) if not key.startswith("reason:")},
        "exclusion_reasons": dict(sorted(reason_counts.items())),
        "deviations": {
            "DEV-01": (
                "Records without a usable abstract are excluded with "
                "NO_USABLE_ABSTRACT_NOT_RETRIEVED instead of staying PENDING "
                "(researcher instruction 2026-10-29, delegated). This deviates from "
                "INC-02/EXC-03 and the Pass-1 guardrail; the subset is reported "
                "separately as 'not retrieved'."
            )
        },
        "sources": {
            "mutual_exclude": "decisions/{batch}_decisions_A1.json (A1 == A2 == EXCLUDE)",
            "mutual_include": "decisions/{batch}_decisions_A1.json (A1 == A2 == INCLUDE)",
            "third_lane": "third_lane/decisions/pack_*_decisions_T3.json",
            "pass2": "final_lane/decisions_pass2.json (model opencode/deepseek-v4.1-flash-free, temperature 0)",
            "not_retrieved": "v03_scr1_finalize.py resolution branch 5 (no usable abstract after the third lane and the pass-2 re-screen)",
        },
    }
    (LIT / "screening" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    report = {
        "total_identified": TOTAL_IDENTIFIED,
        "duplicates_removed": DUPLICATES_REMOVED,
        "records_screened": len(final),
        "records_excluded": len(excluded),
        "records_included": len(included),
        "records_not_retrieved": len(not_retrieved),
        "conflicts_flagged": 0,
        "exclusion_reasons_breakdown": dict(sorted(reason_counts.items())),
    }
    (LIT / "prisma_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# PRISMA-ScR screening report — UAV crop-weed mapping (protocol v0.3)",
        "",
        "**Status:** FINAL AGENT DECISIONS, **NOT HUMAN-CONFIRMED**.",
        "Protocol fingerprint `sha256:f81e6c58…f755`; criteria `9ae1f97d…b86f`.",
        "",
        "```mermaid",
        "graph TD",
        f"    A[Records identified<br/>n={TOTAL_IDENTIFIED}] --> B[Duplicates removed<br/>n={DUPLICATES_REMOVED}]",
        f"    B --> C[Records screened<br/>n={len(final)}]",
        f"    C --> D[Records excluded<br/>n={len(excluded)}]",
        f"    C --> E[Records included<br/>n={len(included)}]",
        f"    D --> F[Not retrieved<br/>n={len(not_retrieved)}]",
        "```",
        "",
        "## Counts",
        "",
        "| Stage | n |",
        "|---|---:|",
        f"| Identified | {TOTAL_IDENTIFIED} |",
        f"| Duplicates removed | {DUPLICATES_REMOVED} |",
        f"| Screened | {len(final)} |",
        f"| Excluded | {len(excluded)} |",
        f"| — of which not retrieved (no usable abstract) | {len(not_retrieved)} |",
        f"| Included | {len(included)} |",
        "",
        "## Exclusion reasons",
        "",
        "| Code | n |",
        "|---|---:|",
    ]
    for code, count in sorted(reason_counts.items()):
        lines.append(f"| {code} | {count} |")
    lines += [
        "",
        "## Lane provenance",
        "",
        "| Lane | INCLUDE | EXCLUDE |",
        "|---|---:|---:|",
    ]
    for lane in ("mutual_include", "third_lane", "pass2", "mutual_exclude", "not_retrieved"):
        lines.append(
            f"| {lane} | {counters.get(f'{lane}:INCLUDE', 0)} | {counters.get(f'{lane}:EXCLUDE', 0)} |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- All decisions are **agent** decisions. `HumanConfirmation@1` is unsigned; no "
        "independent human review is claimed.",
        "- DEV-01: records lacking a usable abstract are excluded as *not retrieved* per a "
        "delegated researcher instruction; this deviates from INC-02/EXC-03 and is reported "
        "above rather than hidden in the exclusion total.",
        "- Search coverage is bounded by the recorded provider wall (Semantic Scholar HTTP 429); "
        "the corpus is the r3d union (14,413 records, 14,150 after dedup).",
        "- Charting is frozen with limitation F1 and produced no accepted rows.",
        "",
        "## Artifacts",
        "",
        "- `literature/included.json`, `literature/excluded.json`",
        "- `literature/screening/final_decisions.json`, `literature/screening/summary.json`",
        "- `literature/prisma_report.json`, this report",
    ]
    (LIT / "prisma_screening_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary["totals"], indent=1))
    print(json.dumps(dict(reason_counts), indent=1))


if __name__ == "__main__":
    main()
