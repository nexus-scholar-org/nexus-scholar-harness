from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "architecture" / "contract_v1_baseline.json"


def test_contract_baseline_is_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_contract_baseline.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_baseline_hash_is_line_ending_independent(tmp_path: Path) -> None:
    sha256 = runpy.run_path(str(ROOT / "scripts" / "generate_contract_baseline.py"))[
        "_sha256"
    ]
    lf = tmp_path / "lf.txt"
    crlf = tmp_path / "crlf.txt"
    lf.write_bytes(b"one\ntwo\n")
    crlf.write_bytes(b"one\r\ntwo\r\n")
    assert sha256(lf) == sha256(crlf)


def test_baseline_does_not_claim_runtime_adoption() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    state = baseline["state"]
    assert state == {
        "harness_consumers": "CONSUMER_GATED_REFERENCE",
        "legacy_workspaces": "UNMIGRATED",
        "toolkit_producers": "UNMIGRATED",
        "wp00": "FROZEN_REFERENCE_IMPLEMENTATION",
        "wp01": "OPEN_NOT_ADOPTED",
    }


def test_packet_c_is_reference_and_screening_remains_dependency_blocked() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    packet_c = baseline["wp01_packets"]["C_harness_artifact_acceptance_gate"]
    assert packet_c["status"] == "CONSUMER_GATED_REFERENCE"
    packet = baseline["wp01_packets"]["D_screening_producer_migration"]
    assert packet["status"] == "BLOCKED_BY_A_B"
    assert packet["depends_on"] == [
        "A_protocol_identity_producer",
        "B_search_corpus_snapshot_producer",
        "C_harness_artifact_acceptance_gate",
    ]
