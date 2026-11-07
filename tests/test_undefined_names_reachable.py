"""M6-beta (review T-P1-3): code paths that used names never defined or imported.

`ruff check src/ --select F821` found them; CI never linted `src/`, so each
crashed only when someone reached it. One test per path that a user can run.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "workspaces" / "golden-uav-30"


def test_calibration_without_a_gold_file_builds_the_batch(tmp_path):
    """`agent_screen.py calibrate` without `--gold` raised NameError (`_rebuild_doc`)."""
    from scholar_harness.screening.report import cmd_calibration

    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    shutil.copy(GOLDEN / "literature" / "verified.json", ws / "literature" / "verified.json")
    shutil.copy(GOLDEN / "protocol.json", ws / "protocol.json")
    cmd_calibration(ws, sample_size=5)
    batch = json.loads((ws / "literature" / "screening" / "calibration_batch_000.json").read_text(encoding="utf-8"))
    assert len(batch["papers"]) == 5


def test_verbatim_claims_reads_the_extracted_files(tmp_path):
    """`scholar-verify verbatim-claims` raised NameError (`re` not imported)."""
    from scholar_verify.cli import app

    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "paper.md").write_text("---\nworkspace_id: SCI-000001\n---\nUAV imagery maps weeds in maize fields.\n", encoding="utf-8")
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps([{"claim_id": "C1", "text": "UAV imagery maps weeds in maize fields.", "source_ids": ["SCI-000001"]}]), encoding="utf-8")
    result = CliRunner().invoke(app, ["verbatim-claims", "--claims", str(claims), "--extracted", str(extracted)])
    assert not isinstance(result.exception, NameError), result.exception
    assert result.exit_code == 0, result.output
