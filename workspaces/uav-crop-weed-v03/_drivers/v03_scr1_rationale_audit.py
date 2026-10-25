"""Deterministic rationale-grounding audit for SCR1 Pass-1 decisions.

WHAT IT VERIFIES (all deterministic, no LLM):
  1. Token grounding: the content tokens of each decision's `reason` +
     `one_line_support` must appear (case-insensitive) in the evidence text the
     screener actually saw — the MODERATION VIEW text for view-era shards, and
     the original batch text for original-era waves. Reason about "path
     planning" in a text about wheat segmentation flags instantly.
  2. Category assertions per reason_code:
       INCLUDE                      -> platform token AND task token in text
       EXCLUDE WRONG_PLATFORM       -> text lacks platform token OR has
                                       ground/satellite/lab token
       EXCLUDE WRONG_TASK           -> >=1 task token in text (the reason must
                                       argue from something visible)
       EXCLUDE WRONG_REPORT_TYPE    -> report-type marker in text
       GUARDRAIL_TITLE_ONLY_UAV_WEED-> abstract effectively null AND title has
                                       platform AND crop/weed token
       MODERATION_TITLE_ONLY_EXCLUDE-> decision must rest on title tokens only
  3. Identity: screening_id in the decision file exists in the batch, and the
     decision's evidence text belongs to THAT id (join integrity).

HONEST LIMIT (printed in the output): this is lexical grounding, NOT semantic
entailment. A decision can be lexically grounded and still semantically wrong;
an ungrounded flag is a routing signal to the boundary/human lane, never an
automatic verdict against the screener.

Output: calibration_v03/v03_scr1_rationale_audit.json + printed summary.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
SCR = CAL / "screening_scr1"
DEC = SCR / "decisions"
VIEWS = SCR / "moderation_views"
OUT = CAL / "v03_scr1_rationale_audit.json"

STOP = set(
    """the a an and or of in on for with from by to as is are was were be been
    this that these those it its their our we he she they study studies paper
    using use used based novel new approach method methods result results
    show shows shown demonstrate demonstrates present presents however
    there here which who whom while during over under between about across
    via per one two three four five high low many several various different
    data set sets model models detection detect detections""".split()
)

PLATFORM = {
    "uav",
    "uas",
    "drone",
    "drones",
    "unmanned",
    "aerial",
    "rpa",
    "rpas",
    "sua",
    "multirotor",
    "quadcopter",
    "quadrotor",
    "hexacopter",
    "helicopter",
    "aircraft",
    "airplane",
    "fixedwing",
    "sua",
    "airborne",
    "ohs",
}
CROP_WEED = {
    "crop",
    "crops",
    "weed",
    "weeds",
    "agriculture",
    "agricultural",
    "farming",
    "field",
    "fields",
    "orchard",
    "vineyard",
    "pasture",
    "plant",
    "plants",
    "plantation",
    "canopy",
    "seedling",
    "maize",
    "corn",
    "wheat",
    "rice",
    "soybean",
    "cotton",
    "tomato",
    "potato",
    "sugarcane",
    "olive",
    "barley",
    "vegetable",
    "vegetables",
    "herbicide",
    "agronomy",
    "phenotyping",
    "ndvi",
    "salvinia",
    "hyacinth",
    "ryegrass",
    "clover",
    "lentil",
    "bean",
    "beans",
}
GROUND_SAT = {
    "ground",
    "satellite",
    "satellites",
    "terrestrial",
    "proximal",
    "handheld",
    "tractor",
    "laboratory",
    "lab",
    "greenhouse",
    "plot",
    "plots",
    "se",
    "sentinel",
    "landsat",
    "worldview",
    "planet",
    "modis",
    "spot",
    "ikonic",
}
REPORT_TYPE = {
    "review",
    "survey",
    "surveys",
    "chapter",
    "editorial",
    "corrigendum",
    "correction",
    "retraction",
    "comment",
    "preface",
    "proceedings",
    "workshop",
    "abstract",
    "book",
    "thesis",
    "dissertation",
    "metaanalysis",
    "bibliometric",
    "bibliometrics",
    "frontmatter",
}

TOKEN = re.compile(r"[a-z]+")


def toks(text: str) -> list[str]:
    return [
        t for t in TOKEN.findall((text or "").lower()) if len(t) >= 3 and t not in STOP
    ]


def content_tokens(reason: str, support: str) -> set[str]:
    return set(toks(reason)) | set(toks(support))


def evidence_text(record: dict) -> str:
    return f"{record.get('title') or ''} {record.get('abstract') or ''}"


def main() -> None:
    manifest = json.loads(
        (SCR.parent / "v03_scr1_prep_manifest.json").read_text(encoding="utf-8")
    )
    n_batches = manifest["n_batches"]

    # Load per-batch: original records and view records, keyed by screening_id.
    batches: dict[int, dict[str, dict]] = {}
    views: dict[int, dict[str, dict]] = {}
    for n in range(1, n_batches + 1):
        b = json.loads((SCR / f"batch_{n:04d}.json").read_text(encoding="utf-8"))
        batches[n] = {r["screening_id"]: r for r in b["records"]}
        vp = VIEWS / f"batch_{n:04d}.view.json"
        if vp.is_file():
            v = json.loads(vp.read_text(encoding="utf-8"))
            views[n] = {r["screening_id"]: r for r in v["records"]}

    per_family = defaultdict(Counter)
    per_code = defaultdict(Counter)
    flagged: list[dict] = []
    code_checks = Counter()
    n_files = 0
    n_records = 0

    for fam in ("A1", "A2"):
        for n in range(1, n_batches + 1):
            fp = DEC / f"batch_{n:04d}_decisions_{fam}.json"
            if not fp.is_file():
                continue
            n_files += 1
            doc = json.loads(fp.read_text(encoding="utf-8"))
            rows = doc["decisions"] if "decisions" in doc else doc["rows"]
            view = views.get(n, batches[n])
            for row in rows:
                n_records += 1
                sid = row["screening_id"]
                code = str(row.get("reason_code", "UNKNOWN"))
                rec = view.get(sid)
                if rec is None:
                    per_family[fam]["missing_id_in_evidence"] += 1
                    flagged.append(
                        {
                            "family": fam,
                            "batch": n,
                            "screening_id": sid,
                            "decision": row["decision"],
                            "reason_code": code,
                            "flag": "MISSING_ID_IN_EVIDENCE",
                        }
                    )
                    continue
                text = evidence_text(rec)
                etext = set(toks(text))
                content = content_tokens(
                    row.get("reason", ""), row.get("one_line_support", "")
                )
                present = content & etext
                missing = content - present
                ratio = (len(present) / len(content)) if content else 1.0

                # Category assertions (deterministic, evidence-token based).
                problems = []
                code_checks[code] += 1
                plat = etext & PLATFORM
                crop = etext & CROP_WEED
                ground = etext & GROUND_SAT
                report = etext & REPORT_TYPE
                if row["decision"] == "INCLUDE" and not (plat and crop):
                    problems.append("INCLUDE_MISSING_PLATFORM_OR_TASK_TOKENS")
                if code == "WRONG_PLATFORM" and plat and not ground:
                    problems.append("WRONG_PLATFORM_BUT_PLATFORM_TOKEN_PRESENT")
                if code == "WRONG_TASK" and not (crop or plat or report):
                    problems.append("WRONG_TASK_WITHOUT_VISIBLE_TASK_ANCHOR")
                if code == "WRONG_REPORT_TYPE" and not report:
                    problems.append("WRONG_REPORT_TYPE_WITHOUT_MARKER")
                if code == "GUARDRAIL_TITLE_ONLY_UAV_WEED":
                    abst = rec.get("abstract") or ""
                    nullish = (
                        (not abst.strip())
                        or rec.get("abstract_effectively_null")
                        or abst.startswith("[ABSTRACT WITHHELD")
                    )
                    title = set(toks(rec.get("title", "")))
                    if not (nullish and (title & PLATFORM) and (title & CROP_WEED)):
                        problems.append("GUARDRAIL_PRECONDITIONS_NOT_MET")
                if code == "MODERATION_TITLE_ONLY_EXCLUDE":
                    title = set(toks(rec.get("title", "")))
                    if not title:
                        problems.append("TITLE_ONLY_EXCLUDE_WITHOUT_TITLE_TOKENS")
                    # the reason must not pretend to quote withheld abstract text
                    if missing and not (title & missing):
                        problems.append("TITLE_ONLY_EXCLUDE_CITES_NON_TITLE_TOKENS")

                if ratio < 0.5:
                    bucket = "UNGROUND"
                elif missing:
                    bucket = "PARTIAL"
                else:
                    bucket = "FULL"
                per_family[fam][bucket] += 1
                per_code[code][bucket] += 1
                if problems or ratio < 0.5:
                    flagged.append(
                        {
                            "family": fam,
                            "batch": n,
                            "screening_id": sid,
                            "decision": row["decision"],
                            "reason_code": code,
                            "grounding_ratio": round(ratio, 3),
                            "missing_tokens": sorted(missing)[:12],
                            "problems": problems,
                        }
                    )

    total = sum(sum(c.values()) for c in per_family.values())
    print(f"files={n_files} decision_rows={n_records} (incl. missing-id flags)")
    for fam in ("A1", "A2"):
        c = per_family[fam]
        full, partial, unground = c["FULL"], c["PARTIAL"], c["UNGROUND"]
        ok = full + partial + unground
        print(
            f"{fam}: FULL {full} ({100 * full / ok:.1f}%) | PARTIAL {partial} "
            f"({100 * partial / ok:.1f}%) | UNGROUND {unground} ({100 * unground / ok:.1f}%) "
            f"| missing-ids {c['missing_id_in_evidence']}"
        )
    print("\nper reason_code (FULL/PARTIAL/UNGROUND):")
    for code, c in sorted(per_code.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"  {code:38s} {c['FULL']:5d} / {c['PARTIAL']:4d} / {c['UNGROUND']:4d}")
    prob_counts = Counter(p for f in flagged for p in f.get("problems", []))
    if prob_counts:
        print("\ncategory-assertion problems:", dict(prob_counts))
    print(f"\nflagged rows: {len(flagged)}")
    print(
        "HONEST LIMIT: lexical grounding, NOT semantic entailment - a flagged "
        "row routes to the boundary/human lane; it never overrides a screener "
        "by itself."
    )
    OUT.write_text(
        json.dumps(
            {
                "schema": "uav-scr1-rationale-audit-v1",
                "files": n_files,
                "rows": n_records,
                "per_family": {k: dict(v) for k, v in per_family.items()},
                "per_code": {k: dict(v) for k, v in per_code.items()},
                "problem_counts": dict(prob_counts),
                "flagged": flagged,
                "limit": "lexical grounding, not semantic entailment",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"WROTE {OUT}")


if __name__ == "__main__":
    main()
