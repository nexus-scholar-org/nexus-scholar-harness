"""SCR1 inventory v3 — three-tier, frozen-template-normative, debt-aware.

History: v1 checked only JSON-parse + row count (false green on 7 defective
files). v2 demanded later-era extras (`reason`, `criterion_refs`) as required
(false red on template-conformant files). v3 takes the FROZEN TEMPLATE as
normative via v03_scr1_schema.load_and_classify:

  BAD    structural: unparseable, header unattested (screener_id / criteria
         sha), wrong row count, ID/order mismatch vs view, missing
         screening_id/decision, decision out of vocabulary.
  DEBT   decision-complete but a canonical field is absent / alias-named /
         non-numeric confidence / rationale only in `reason`. Reconcilable;
         per-row debt recorded; never fabricated or silently coerced.
  VALID  every canonical field present and well-formed.

prompt_template_sha256 absence in pre-pinning waves is era provenance debt
(reported), not a validity failure.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v03_scr1_schema import load_and_classify  # noqa: E402

SCR = Path(r"workspaces\uav-crop-weed-v03\calibration_v03\screening_scr1")
DEC = SCR / "decisions"


def ranges(l):
    out, s, p = [], None, None
    for x in sorted(l):
        if s is None:
            s = p = x
            continue
        if x == p + 1:
            p = x
            continue
        out.append((s, p))
        s = p = x
    if s is not None:
        out.append((s, p))
    return out


for fam in ("A1", "A2"):
    valid, debt, bad, missing = [], [], [], []
    for n in range(1, 284):
        res = load_and_classify(n, fam, DEC)
        t = res["tier"]
        if t == "VALID":
            valid.append(n)
        elif t == "DEBT":
            debt.append(n)
        elif res["structural"] == ["FILE_MISSING"]:
            missing.append(n)
        else:
            bad.append((n, res["structural"][:3]))
    print(
        f"{fam}: VALID {len(valid)} | DEBT {len(debt)} | BAD {len(bad)} | "
        f"MISSING {ranges(missing) if missing else 'NONE'}"
    )
    if bad:
        for n, probs in bad:
            print(f"  BAD batch_{n:04d}: {probs}")
    if debt:
        print(f"  DEBT batches: {ranges(debt)}")
