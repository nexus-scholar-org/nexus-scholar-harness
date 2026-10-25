"""SCR1 → console exporter — surface the SCR1 screening run in the existing UI.

Maps the SCR1 Pass-1 batches into the CANONICAL console layout the existing
research-ui already reads (`/api/v1/screening/ui/*`, HCM-06/UI-07), writing
ONLY to `literature/screening/` in the workspace:

  - literature/screening/MANIFEST.json        (console envelope, screening_run_id)
  - literature/screening/batch_NNN.json       (papers: workspace_id/title/year/
                                               abstract/venue/doi, NO artifact_id
                                               → coverage INCOMPLETE «
                                               NO_DECISIONS_YET until a human
                                               writes decisions — Option C:
   agent decisions stay SUGGESTIONS, never seeded as canonical include/exclude.)

The A1/A2 Pass-1 suggestion files (decisions/) are NOT exported as canonical
decisions: the console only accepts INCLUDE/EXCLUDE rows written by the human
lead (reviewed_by surface) and `TERMINAL_DECISIONS = {INCLUDE, EXCLUDE}` is the
decision authority; seeding suggestions as canonical rows would convert
suggestions into decisions without the lead's confirmation, which the protocol
forbids.

Nothing prior-round is overwritten: literature/ was empty in this workspace.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
SCR = CAL / "screening_scr1"
OUT = ROOT / "workspaces" / "uav-crop-weed-v03" / "literature" / "screening"

MANIFEST = json.loads((CAL / "v03_scr1_prep_manifest.json").read_text(encoding="utf-8"))

PROTOCOL_SUMMARY = {
    "fingerprint": MANIFEST.get("criteria_frozen_sha256"),
    "source": "SCREENING_CRITERIA.md (frozen ref: v03_scr1_SCREENING_CRITERIA_frozen_ref.md)",
    "playbook": "SCOPING_REVIEW",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n_batches = MANIFEST["n_batches"]
    rows = []
    for n in range(1, n_batches + 1):
        b = json.loads((SCR / f"batch_{n:04d}.json").read_text(encoding="utf-8"))
        papers = []
        for r in b["records"]:
            papers.append(
                {
                    "workspace_id": r["screening_id"],
                    "title": r.get("title") or "",
                    "year": r.get("year"),
                    "abstract": (r.get("abstract") or "No abstract available."),
                    "venue": None,
                    "doi": r.get("doi"),
                }
            )
        batch_data = {
            "batch_index": n,
            "total_batches": n_batches,
            "batch_size": len(papers),
            "status": "PENDING",
            "scr1_session": b["session"],
            "criteria_sha256": b["criteria_sha256"],
            "prompt_template_sha256": b["prompt_template_sha256"],
            "protocol": PROTOCOL_SUMMARY,
            "papers": papers,
            "agent_instructions": (
                "SCR1 Pass-1 suggestions are maintained OUTSIDE the console in "
                "calibration_v03/screening_scr1/decisions/ (A1/A2 family files). "
                "The console decisions file is written ONLY by the human research "
                "lead (Option C: 100% confirmation). Abstract-null records with "
                "UAV + crop/weed titles are under the PENDING guardrail (never "
                "auto-exclude)."
            ),
        }
        (OUT / f"batch_{n:03d}.json").write_text(
            json.dumps(batch_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        rows.append(
            {
                "batch_index": n,
                "file": f"batch_{n:03d}.json",
                "decisions_file": f"batch_{n:03d}_decisions.json",
                "paper_count": len(papers),
                "status": "PENDING",
                "source": "SCR1 exporter (calibration_v03/screening_scr1 batches)",
            }
        )
    (OUT / "MANIFEST.json").write_text(
        json.dumps(
            {
                "screening_run_id": MANIFEST["session"],
                "total_papers": MANIFEST["n_compacted"],
                "batch_size": MANIFEST["batch_size"],
                "total_batches": n_batches,
                "shuffle_seed": MANIFEST["shuffle_seed"],
                "criteria_frozen_sha256": MANIFEST["criteria_frozen_sha256"],
                "prompt_template_sha256": MANIFEST["prompt_template_sha256"],
                "batches": rows,
                "note": "SCR1 Pass-1 (suggestions) runs in calibration_v03/screening_scr1; console decisions files appear only as the human lead confirms batches via the UI (Option C).",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"EXPORTED {n_batches} canonical batches + MANIFEST to {OUT}")


if __name__ == "__main__":
    main()
