"""M11b part A, DoD 2: every reader of the screening criteria uses the one function.

The criteria in force are the signed list plus the amendments
(``scholar_harness.screening.criteria.criteria_in_force``). A place that reads
``screening_criteria`` from a protocol itself would screen or report against
the signed wording after a revision, with no error. This test lists every
source file that names ``screening_criteria`` and fails on one that is not
allow-listed here with its reason. Adding a reader means moving it to the
function, or adding it below with the reason it may read the signed list.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

#: file -> why it may name ``screening_criteria`` (read the signed list, or write one).
ALLOWED: dict[str, str] = {
    # The one reader and its helpers.
    "scholar_harness/screening/criteria.py": "the criteria in force: reads the signed list and applies the amendments",
    # The protocol kit: the model, the compiler, the renderer and the schema of the signed protocol.
    "scholar_protocol/*": "the protocol kit defines, compiles, validates and renders the signed protocol",
    # Inception writes or imports the signed protocol before any batch exists (no amendment can apply).
    "scholar_harness/inception/genesis.py": "genesis writes the signed protocol",
    "scholar_harness/inception/importer.py": "imports a protocol before genesis",
    "scholar_harness/inception/steps.py": "the Inception preview of the protocol to be signed",
    # The batch file embeds the signed wording on purpose: it is hashed into every binding.
    "scholar_harness/screening/batcher.py": "prepare embeds the signed wording in the batch file, hashed into bindings",
    # The file hand-off worker reads that embedded wording, and refuses once the criteria are amended
    # (decision 2026-11-21, M11b part A, item 1).
    "scholar_harness/screening/worker.py": "reads the batch file's signed wording; refuses when the criteria version > 1",
    # A caller passes the protocol in force (agent runs, the estimate); the task reads what it is given.
    "scholar_agent/tasks/screening/__init__.py": "builds the prompt from the protocol dict its caller passes (in force)",
    "scholar_harness/screening/proposals.py": "Criteria.from_protocol, kept for callers outside the screening engine",
    # Command-line measurement of the signed protocol (decision 2026-11-21, M11b part A, item 2).
    "scholar_agent/calibration.py": "the command-line calibration measures the signed protocol (item 2)",
    "scholar_agent/measure.py": "`prompt-gate measure` measures the signed protocol (item 2; out of scope in the record)",
    # The prompt and its schema are built from the protocol dict the caller passes: the agent run
    # and the estimate pass the criteria in force; `prompt-gate measure` passes the signed one.
    "scholar_agent/prompt_gate.py": "run_spec builds from the protocol dict its caller passes (in force from the engine)",
    # MCP: the protocol-rendering tool renders a protocol file given by path, not a workspace's criteria.
    "scholar_agent/server.py": "render_screening_criteria of a protocol file given by path (the record tool reads in force)",
    # The legacy kit heuristic screener, not used by the screening engine.
    "scholar_search/screening.py": "the search kit's heuristic pre-screen over a protocol it is given; not the engine",
}

#: Files that must NOT name ``screening_criteria`` any more: they read the criteria in force.
MOVED = (
    "scholar_harness/screening/events.py",
    "scholar_harness/screening/agent_runs.py",
    "scholar_harness/screening/export.py",
    "scholar_harness/console/api/screening_v1.py",
)


def _allowed(rel: str) -> bool:
    return any(rel == key or (key.endswith("/*") and rel.startswith(key[:-1])) for key in ALLOWED)


#: The ways code reads the criteria of a protocol itself (review round 1, F3): the key as a
#: string, the attribute on the model, the proposals helper, and the agent kit's helper (called
#: with a protocol; the harness's ``criteria_from_protocol(workspace, ...)`` is the one reader).
READER_PATTERNS = (
    r"""["']screening_criteria["']""",
    r"\.screening_criteria\b",
    r"\bCriteria\.from_protocol\(",
    r"\bcriteria_from_protocol\(protocol",
)


def _readers() -> list[str]:
    found = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(re.search(pattern, text) for pattern in READER_PATTERNS):
            found.append(path.relative_to(SRC).as_posix())
    return found


def test_each_pattern_finds_a_known_reader():
    """Anti-vacuity: every pattern matches at least one allow-listed file."""
    for pattern in READER_PATTERNS:
        assert any(
            re.search(pattern, path.read_text(encoding="utf-8", errors="replace"))
            for path in SRC.rglob("*.py")
        ), pattern


def test_every_reader_of_screening_criteria_is_allow_listed_with_its_reason():
    readers = _readers()
    assert readers, "anti-vacuity: the scan found the known readers"
    unexpected = [r for r in readers if not _allowed(r)]
    assert not unexpected, (
        "these files read `screening_criteria` themselves; read the criteria in force "
        f"(screening.criteria.criteria_in_force) or allow-list them with a reason: {unexpected}"
    )


def test_the_moved_readers_no_longer_read_the_protocol_list():
    readers = set(_readers())
    assert not readers & set(MOVED), sorted(readers & set(MOVED))


def test_the_mcp_record_tool_reads_the_criteria_in_force():
    text = (SRC / "scholar_agent" / "server.py").read_text(encoding="utf-8")
    record_tool = text.split("def nexus_screening_record", 1)[1].split("\ndef ", 1)[0]
    assert "screening_criteria" not in record_tool and "context.criteria" in record_tool


def test_the_allow_list_names_only_files_that_exist():
    for key in ALLOWED:
        target = SRC / key.rstrip("*").rstrip("/")
        assert target.exists(), key
