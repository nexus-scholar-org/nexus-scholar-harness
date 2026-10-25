"""Moderation-safe triage views for SCR1 Pass-1.

WHY: the provider filters requests containing certain terms (military / illicit
text that legitimately occurs in this UAV corpus — e.g. "air defense target",
"terrorist attacks ... weapons, drugs", "C4IRS ... combat operations").  A
single flagged record inside a batch kills the whole model call, so those
records are isolated into a redacted-view copy while the originals stay
immutable in `batch_NNNN.json`:

  screening_scr1\\moderation_views\\batch_NNNN.view.json

Rules (conservative, documented):
  - a record is REDACTED when title or abstract matches any MODERATION_TOKEN
    (word-boundary, case-insensitive);
  - redacted record keeps the original screening_id and a *masked* title
    (flagged tokens replaced with [REDACTED]); its abstract is replaced by an
    explicit withholding notice naming the tokens;
  - all other records are copied verbatim;
  - the view carries `moderation_redacted: true` / `moderation_terms` per
    record and a top-level `moderation_notice`; counters are printed.

Protocol consequence (journaled): a redacted record may only be PENDING or a
title-level EXCLUDE when the visible title already clearly leaves the review
domain; it is NEVER silently excluded for the withheld text.  Every redacted
record is listed in the run report for human-lead verification against the
original batch file.

The driver is idempotent and never touches `batch_NNNN.json` or decisions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCR = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03" / "screening_scr1"
OUT = SCR / "moderation_views"

MANIFEST = json.loads(
    (SCR.parent / "v03_scr1_prep_manifest.json").read_text(encoding="utf-8")
)

# Evidence-driven list: military / illicit terms observed in the corpus.
# Deliberately EXCLUDES agronomic usage ("herbicides kill the weeds"): earlier
# waves screened such text fine, so redacting it would distort the substrate
# without evidence that it trips the provider filter.
TOKENS = [
    "weapon",
    "weapons",
    "terror",
    "terrorist",
    "terrorism",
    "drug",
    "drugs",
    "narcotic",
    "cocaine",
    "heroin",
    "marijuana",
    "cannabis",
    "opium",
    "bomb",
    "bombing",
    "explosive",
    "explosives",
    "combat",
    "military",
    "sabotage",
    "suicide",
    "anthrax",
    "bioweapon",
]
PATTERN = re.compile(r"\b(" + "|".join(TOKENS) + r")\b", re.IGNORECASE)

WITHHELD = (
    "[ABSTRACT WITHHELD BY PROVIDER MODERATION - original retained in the "
    "immutable batch file; screen on the visible title only; mark PENDING "
    "unless the title already clearly leaves the review domain]"
)


def mask(text: str) -> tuple[str, list[str]]:
    terms = sorted({m.group(1).lower() for m in PATTERN.finditer(text or "")})
    if not terms:
        return text or "", []
    return PATTERN.sub("[REDACTED]", text or ""), terms


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    total_redacted = 0
    affected_batches = 0
    per_batch = []
    for n in range(1, MANIFEST["n_batches"] + 1):
        src = SCR / f"batch_{n:04d}.json"
        batch = json.loads(src.read_text(encoding="utf-8"))
        records = []
        redacted_here = 0
        for r in batch["records"]:
            title = r.get("title") or ""
            abstract = r.get("abstract") or ""
            safe_title, title_terms = mask(title)
            _, abs_terms = mask(abstract)
            terms = sorted(set(title_terms) | set(abs_terms))
            if terms:
                redacted_here += 1
                records.append(
                    {
                        **r,
                        "title": safe_title,
                        "abstract": WITHHELD,
                        "abstract_effectively_null": True,
                        "moderation_redacted": True,
                        "moderation_terms": terms,
                    }
                )
            else:
                records.append(r)
        view = {
            **{k: v for k, v in batch.items() if k != "records"},
            "moderation_notice": (
                "Records flagged moderation_redacted have withheld text: the "
                "original is in the immutable batch file; decide PENDING unless "
                "the visible title clearly leaves the review domain."
            ),
            "records": records,
        }
        (OUT / f"batch_{n:04d}.view.json").write_text(
            json.dumps(view, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        total_redacted += redacted_here
        if redacted_here:
            affected_batches += 1
            per_batch.append((n, redacted_here))
        print(f"batch_{n:04d}: {redacted_here:2d} redacted / {len(records)} records")

    print()
    print(f"REDACTED RECORDS: {total_redacted} across {affected_batches} batches")
    print(f"VIEWS: {OUT}")


if __name__ == "__main__":
    main()
