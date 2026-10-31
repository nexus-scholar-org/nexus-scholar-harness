#!/usr/bin/env python3
"""Verify that every verbatim claim in the pilot synthesis exists in an extract.

Each entry is (study_id, quoted fragment). The fragment must appear as a
whitespace-normalised substring of that study's extracted Markdown, and must
also appear in `synthesis/literature_review.md`. A failure is a real problem:
either the quote was altered or the synthesis drifted from its evidence.

Run: uv run python workspaces/uav-crop-weed-v03/_drivers/v03_pilot_synthesis_check.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

WS = Path(__file__).resolve().parents[1]
MANIFEST = WS / "extracted" / "_pilot_manifest.json"
SYNTHESIS = WS / "synthesis" / "literature_review.md"
OUT = WS / "synthesis" / "_quote_check.json"

QUOTES = [
    ("SCI-000372", "Motion blur disproportionately affects fine-detail segmentation accuracy by smearing edges and textures"),
    ("SCI-000372", "ResNet-34 achieves the highest mean Dice Score of 0.9198 and that accuracy does not increase with depth"),
    ("SCI-000041", "achieves a segmentation accuracy (mean IoU) of 78.88%, outperforming RGB-only models by 15.8 percentage points"),
    ("SCI-000291", "fine-tuned MobileNetV2 achieved the highest accuracy (96.40%)"),
    ("SCI-000006", "an average accuracy of 90% when 80% of training data was unlabeled"),
    ("SCI-000736", "Models trained under these conditions tend to generalize poorly when deployed in new fields, seasons, or to different crops"),
    ("SCI-000736", "few-shot fine-tuning with as few as 25 labeled target examples outperforms unsupervised DAOD in our cross-crop comparison"),
    ("SCI-000041", "The dataset is spatially split into 109 training (70%), 23 validation (15%), and 24 test (15%) tiles, ensuring no spatial overlap between splits"),
    ("SCI-000291", "the train_test_split function, with 80% of the data allocated for training and 20% for testing"),
    ("SCI-000044", "were divided randomly into two sets: the training set, and testing set"),
    ("SCI-000291", "importance of sensor calibration prior to data acquisition"),
    ("SCI-000372", "jointly calibrated"),
    ("SCI-000607", "did not perform as effectively as real plant instance-based synthetic images"),
]


def norm(text: str) -> str:
    return unicodedata.normalize("NFKC", re.sub(r"\s+", " ", text)).strip()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    docs = {
        rec["study_id"]: norm(Path(WS / rec["extracted_path"]).read_text(encoding="utf-8"))
        for rec in manifest["records"]
        if rec["status"] == "EXTRACTED_VALID"
    }
    synthesis = norm(SYNTHESIS.read_text(encoding="utf-8"))

    results = []
    for study_id, quote in QUOTES:
        q = norm(quote)
        in_extract = q in docs.get(study_id, "")
        in_synthesis = q in synthesis
        results.append({
            "study_id": study_id,
            "quote": quote,
            "found_in_extract": in_extract,
            "found_in_synthesis": in_synthesis,
            "status": "PASS" if in_extract and in_synthesis else "FAIL",
        })

    failed = [r for r in results if r["status"] != "PASS"]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "synthesis": str(SYNTHESIS.relative_to(WS)),
        "records": results,
        "summary": {
            "quotes": len(results),
            "verified": len(results) - len(failed),
            "failed": len(failed),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    for r in results:
        print(f"{r['status']:4} {r['study_id']} {r['quote'][:70]}")
    print("\n" + json.dumps(payload["summary"]))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
