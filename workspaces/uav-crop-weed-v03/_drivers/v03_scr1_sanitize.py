"""SCR1 sanitize — repair trailing-comma JSON written by rate-limited agents.

Removes trailing commas before ] or } inside decision files, then validates
decision counts against the source batches. Idempotent; only touches
byte-identically broken files; never overwrites valid ones.
"""

import json
import re
from pathlib import Path

SCR = Path(r"workspaces\uav-crop-weed-v03\calibration_v03\screening_scr1")
DEC = SCR / "decisions"
TRAIL = re.compile(r",(\s*[\]}])")


def clean_text(t: str) -> str:
    return TRAIL.sub(r"\1", t)


fixed = []
for fp in sorted(DEC.glob("batch_*_decisions_*.json")):
    raw = fp.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except Exception:
        try:
            data = json.loads(clean_text(raw))
        except Exception as e:
            print("STILL BROKEN", fp.name, str(e)[:60])
            continue
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        fixed.append(fp.name)
    n = int(re.match(r"batch_(\d+)_decisions_", fp.name).group(1))
    want = json.loads((SCR / f"batch_{n:04d}.json").read_text(encoding="utf-8"))[
        "n_records"
    ]
    got = len(data.get("decisions", []))
    print(
        fp.name,
        "parsed" if not fixed or fp.name not in fixed else "FIXED",
        f"{got}/{want}",
        "OK" if got == want else "COUNT-MISMATCH",
    )
print("fixed:", fixed)
