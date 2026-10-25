"""SCR1 template-conformance + schema-debt audit (READ-ONLY over evidence).

The frozen template is normative (canonical row: screening_id, decision,
reason_code, confidence, one_line_support). This audit classifies all 566
decision files into VALID / DEBT / BAD, maps the prompt-SHA era asymmetry,
and writes the structured debt report consumed by reconciliation triage and
the human-lead packets. It never edits decision files and never fabricates
absent fields.

Output: calibration_v03/v03_scr1_schema_debt_report.json
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v03_scr1_schema import load_and_classify  # noqa: E402

SCR = Path(r"workspaces\uav-crop-weed-v03\calibration_v03\screening_scr1")
DEC = SCR / "decisions"
OUT = SCR.parent / "v03_scr1_schema_debt_report.json"


def ranges(lst):
    out, s, p = [], None, None
    for x in sorted(lst):
        if s is None:
            s = p = x
            continue
        if x == p + 1:
            p = x
            continue
        out.append([s, p])
        s = p = x
    if s is not None:
        out.append([s, p])
    return out


report = {
    "contract": {
        "normative_source": "v03_scr1_pass1_prompt_template.txt",
        "template_sha256_prefix": "0c7f129d",
        "criteria_sha256_prefix": "9ae1f97d",
        "canonical_fields": [
            "screening_id",
            "decision",
            "reason_code",
            "confidence",
            "one_line_support",
        ],
        "allowed_extras": ["reason", "criterion_refs", "moderation_*"],
        "policy": (
            "aliases recognized+tagged (never silently coerced); absent fields "
            "are debt (never fabricated); evidence files never mass-mutated"
        ),
    },
    "families": {},
}

print(
    "template-conformance audit | canonical = screening_id, decision, "
    "reason_code, confidence, one_line_support"
)
print("=" * 78)

grand = Counter()
for fam in ("A1", "A2"):
    tiers = Counter()
    tag_hist = Counter()
    debt_files, bad_files = [], []
    present, prompt_attested = [], []
    fam_entries = []
    for n in range(1, 284):
        res = load_and_classify(n, fam, DEC)
        if res["structural"] == ["FILE_MISSING"]:
            tiers["MISSING"] += 1
            fam_entries.append(
                {
                    "batch": n,
                    "tier": "MISSING",
                    "rows": 0,
                    "prompt_sha_attested": False,
                    "debt": [],
                    "structural": ["FILE_MISSING"],
                }
            )
            continue
        tiers[res["tier"]] += 1
        if res["prompt_sha_attested"]:
            prompt_attested.append(n)
        if res["structural"] and res["structural"] != ["FILE_MISSING"]:
            present.append(n)
            bad_files.append(
                {"batch": n, "problems": res["structural"][:6], "rows": res["rows"]}
            )
        elif res["structural"] == ["FILE_MISSING"]:
            pass
        else:
            present.append(n)
        for d in res["debt"]:
            for t in d["debt"]:
                tag_hist[t.split(":")[0]] += 1
            for t in d["advisory"]:
                tag_hist[t.split(":")[0]] += 1
        if res["debt"]:
            debt_files.append(
                {
                    "batch": n,
                    "debt_rows": len(res["debt"]),
                    "tags": sorted(
                        {t.split(":")[0] for d in res["debt"] for t in d["debt"]}
                    ),
                    "prompt_sha_attested": res["prompt_sha_attested"],
                }
            )
        fam_entries.append(
            {
                "batch": n,
                "tier": res["tier"],
                "rows": res["rows"],
                "prompt_sha_attested": res["prompt_sha_attested"],
                "debt": res["debt"],
                "structural": res["structural"],
            }
        )
    missing = [n for n in range(1, 284) if n not in present]
    grand.update(tiers)
    report["families"][fam] = {
        "tiers": dict(tiers),
        "missing_ranges": ranges(missing),
        "prompt_sha_era": {
            "attested_batches": len(prompt_attested),
            "attested_ranges": ranges(prompt_attested),
            "absent_ranges": ranges([n for n in present if n not in prompt_attested]),
            "note": (
                "prompt-SHA pinning was introduced mid-sweep; absence in "
                "pre-pinning waves is era provenance debt, not fabrication"
            ),
        },
        "debt_tag_histogram": dict(tag_hist.most_common()),
        "debt_files": debt_files,
        "bad_files": bad_files,
        "per_batch": fam_entries,
    }
    print(
        f"{fam}: VALID {tiers['VALID']:3d} | DEBT {tiers['DEBT']:3d} | "
        f"BAD {tiers['BAD']:3d} | MISSING {tiers['MISSING']:3d} "
        f"(ranges {ranges(missing) if missing else 'NONE'})"
    )
    print(
        f"    prompt-SHA attested {len(prompt_attested)}/"
        f"{len(present)} batches; absent ranges "
        f"{ranges([n for n in present if n not in prompt_attested])}"
    )
    print(f"    debt tags: {dict(tag_hist.most_common())}")
    for b in bad_files:
        print(f"    BAD batch_{b['batch']:04d}: {b['problems']}")

print("=" * 78)
print(
    f"TOTAL files: VALID {grand['VALID']} | DEBT {grand['DEBT']} | "
    f"BAD {grand['BAD']} | MISSING {grand['MISSING']}"
)

OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"report -> {OUT}")
