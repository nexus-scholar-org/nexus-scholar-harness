"""Generate or verify the frozen Contract v1/WP-00 implementation baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "architecture" / "contract_v1_baseline.json"
ANCHOR_COMMIT = "384b2ae2564ac63cfa78e5935a86f35c856cd36e"

EXPLICIT_PATHS = (
    "scripts/generate_contract_baseline.py",
    "docs/architecture/contract_v1_baseline.md",
    "tests/conformance/test_contract_baseline.py",
    "specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md",
    "specs/deep-audit-remediation-2026-09-17/12_execution_roadmap.md",
    "docs/architecture/cross_kit_contract_v1.md",
    "docs/architecture/wp01_contract_adoption_handoff.md",
    ".agents/skills/doer-contract/SKILL.md",
    ".agents/skills/critic-contract/SKILL.md",
    ".agents/plugins/nexus-scholar/skills/doer-contract/SKILL.md",
    ".agents/plugins/nexus-scholar/skills/critic-contract/SKILL.md",
    ".opencode/agent/orchestrator.md",
    ".opencode/agent/coder.md",
    ".opencode/agent/reviewer.md",
    ".opencode/agent/screener.md",
    ".opencode/agent/screening-critic.md",
    ".opencode/agent/extractor-a.md",
    ".opencode/agent/extractor-b.md",
    ".opencode/agent/extraction-critic.md",
    ".opencode/agent/adjudicator.md",
)

GLOBS = (
    "src/scholar_harness/contracts/*.py",
    "src/scholar_harness/contracts/schemas/v1/*.json",
    "tests/fixtures/contracts/v1/*.json",
    "tests/test_cross_kit_contracts.py",
    "tests/test_contract_artifact_chain.py",
    "tests/conformance/test_opencode_dev_agents.py",
    "tests/conformance/test_scientific_opencode_agents.py",
)


def _locked_paths() -> list[str]:
    paths = {path for path in EXPLICIT_PATHS}
    for pattern in GLOBS:
        paths.update(path.relative_to(ROOT).as_posix() for path in ROOT.glob(pattern))
    missing = [path for path in sorted(paths) if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"baseline paths missing: {missing}")
    return sorted(paths)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_baseline() -> dict[str, object]:
    locked = _locked_paths()
    return {
        "baseline_id": "contract-v1-wp00",
        "baseline_version": "1.0.0",
        "anchor": {
            "pull_request": 37,
            "merge_commit": ANCHOR_COMMIT,
            "merged_at": "2026-09-19T13:11:18Z",
        },
        "state": {
            "wp00": "FROZEN_REFERENCE_IMPLEMENTATION",
            "wp01": "OPEN_NOT_ADOPTED",
            "legacy_workspaces": "UNMIGRATED",
            "toolkit_producers": "UNMIGRATED",
            "harness_consumers": "UNMIGRATED",
        },
        "wp01_packets": {
            "A_protocol_identity_producer": {
                "status": "READY",
                "repository": "nexus-scholar-org/scholar-protocol-kit",
                "depends_on": ["contract-v1-wp00"],
            },
            "B_search_corpus_snapshot_producer": {
                "status": "READY",
                "repository": "nexus-scholar-org/scholar-search-kit",
                "depends_on": ["contract-v1-wp00"],
            },
            "C_harness_artifact_acceptance_gate": {
                "status": "READY",
                "repository": "nexus-scholar-org/nexus-scholar-harness",
                "depends_on": ["contract-v1-wp00"],
            },
            "D_screening_producer_migration": {
                "status": "BLOCKED_BY_A_B_C",
                "repository": "nexus-scholar-org/nexus-scholar-harness",
                "depends_on": [
                    "A_protocol_identity_producer",
                    "B_search_corpus_snapshot_producer",
                    "C_harness_artifact_acceptance_gate",
                ],
            },
            "E_downstream_adapter_stubs": {
                "status": "BLOCKED_BY_A_B",
                "repositories": [
                    "nexus-scholar-org/scholar-pdf-kit",
                    "nexus-scholar-org/scholar-rag-kit",
                ],
                "depends_on": [
                    "A_protocol_identity_producer",
                    "B_search_corpus_snapshot_producer",
                ],
            },
        },
        "non_goals": [
            "No toolkit is migrated merely because its vendored copy imports Contract v1.",
            "No legacy workspace is implicitly Contract v1.",
            "No title-only identity merge is permitted.",
            "No schema or golden-fixture weakening is permitted to unblock an adapter.",
            "No unrelated SYS finding is folded into WP-01 without its owning work package.",
        ],
        "locked_files": [
            {"path": path, "sha256": _sha256(ROOT / path)} for path in locked
        ],
    }


def _render(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = _render(build_baseline())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            print(f"Contract baseline drifted: regenerate {OUTPUT.relative_to(ROOT)}")
            return 1
        print(f"Contract baseline current: {OUTPUT.relative_to(ROOT)}")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
