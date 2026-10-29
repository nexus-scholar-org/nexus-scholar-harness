"""Check that the context-efficiency policy still matches this repository.

The policy (``docs/architecture/context_efficiency_policy.md``) records which
context-engineering mechanisms this harness already implements, which claims
from the external report *Optimizing Coding Harness Token Usage* are false
here, which are unverified vendor marketing, and which mechanisms are adopted,
rejected, or deferred. This module turns the policy's factual claims into
executable checks so the document cannot rot silently.

Scope of the forbidden-token scan
---------------------------------
The three false invariants (``kits/scholar-``, ``scholar-monitor-kit`` and
``sqlite``) are banned from the machine-checked facts block only. The prose
sections of the policy must name those tokens in order to reject them, so a
document-wide ban would contradict the policy's own purpose.

Usage::

    uv run python scripts/check_context_policy.py --check
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POLICY_REL = Path("docs") / "architecture" / "context_efficiency_policy.md"
FACTS_BEGIN = "<!-- facts:begin -->"
FACTS_END = "<!-- facts:end -->"

KITS_ROOT = "tools"
LEGACY_KITS_ROOT = "kits"
EXPECTED_KITS = (
    "scholar-agent-kit",
    "scholar-bib-kit",
    "scholar-graph-kit",
    "scholar-pdf-kit",
    "scholar-protocol-kit",
    "scholar-rag-kit",
    "scholar-search-kit",
    "scholar-verify-kit",
)

AGENTS_MD_WORD_FLOOR = 600
AGENTS_MD_WORD_BUDGET = 1500

# The invariants the root constitution must keep. Each entry maps one enumerated
# invariant to a distinctive marker that must remain present in ``AGENTS.md``.
# The size band cannot detect the deletion of an invariant, so this check does.
AGENTS_MD_INVARIANTS = {
    "contract-v1 baseline gate": "generate_contract_baseline.py --check",
    "fork and PR contribution gate": "pull-request-gate",
    "toolkit three-invariant sync rule": "The three invariants change together, never alone",
    "workspace and audit-ledger convention": "audit/journal.jsonl",
    "uv run-only rule": "Never rely on a system Python",
    "kit skills and MCP front-door pointer": "mcp_config.json",
}

SOURCE_REPORT = "Optimizing Coding Harness Token Usage"

MCP_SERVER_TYPES = ("local", "remote")

# The doc <-> script binding: these keys and values must appear verbatim in the
# policy's facts block. A mismatch is a failure in either direction.
REQUIRED_FACTS_KEYS = {
    "kit_root": KITS_ROOT,
    "kits": ",".join(EXPECTED_KITS),
    "agents_md_word_floor": str(AGENTS_MD_WORD_FLOOR),
    "agents_md_word_budget": str(AGENTS_MD_WORD_BUDGET),
    "source_report": SOURCE_REPORT,
}

FORBIDDEN_FACTS_TOKENS = ("kits/scholar-", "scholar-monitor-kit", "sqlite")


def count_words(text: str) -> int:
    """Whitespace-delimited word count (the measure the policy declares)."""
    return len(text.split())


def _read_text(path: Path, failures: list[str], label: str) -> str | None:
    """Read a UTF-8 text file, reporting (not raising) a decode failure.

    A malformed file must be reported as a check failure, never as a traceback.
    The failure is recorded once per file even when several checks read it.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        if not any(label in message for message in failures):
            failures.append(
                f"{label} is not valid UTF-8 ({exc.reason}); expected UTF-8 text"
            )
        return None


def discover_kits(root: Path) -> set[str]:
    """Return the directories under ``tools/`` that carry a ``pyproject.toml``."""
    tools = root / KITS_ROOT
    if not tools.is_dir():
        return set()
    return {
        child.name
        for child in tools.iterdir()
        if child.is_dir() and (child / "pyproject.toml").is_file()
    }


def extract_facts_block(text: str) -> str:
    """Return the raw text between the facts markers."""
    if FACTS_BEGIN not in text:
        raise ValueError(f"missing {FACTS_BEGIN} marker")
    if FACTS_END not in text:
        raise ValueError(f"missing {FACTS_END} marker")
    start = text.index(FACTS_BEGIN) + len(FACTS_BEGIN)
    end = text.index(FACTS_END, start)
    return text[start:end]


def strip_facts_block(text: str) -> str:
    """Return the policy text with the machine-checked facts block removed."""
    try:
        extract_facts_block(text)
    except ValueError:
        return text
    start = text.index(FACTS_BEGIN)
    end = text.index(FACTS_END, start) + len(FACTS_END)
    return text[:start] + text[end:]


def parse_facts(block: str) -> dict[str, str]:
    """Parse ``key=value`` lines; every non-empty line must be a pair."""
    facts: dict[str, str] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"facts line is not key=value: {line!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        if key in facts:
            raise ValueError(f"duplicate facts key: {key!r}")
        facts[key] = value.strip()
    return facts


def _check_kit_inventory(root: Path, failures: list[str]) -> None:
    if not (root / KITS_ROOT).is_dir():
        failures.append(f"the kit root '{KITS_ROOT}/' is missing from the repository")
        return
    found = discover_kits(root)
    for kit in sorted(set(EXPECTED_KITS) - found):
        failures.append(f"declared kit '{kit}' is missing from {KITS_ROOT}/")
    for kit in sorted(found - set(EXPECTED_KITS)):
        failures.append(
            f"undeclared kit directory '{kit}' exists in {KITS_ROOT}/ "
            f"(expected exactly: {', '.join(EXPECTED_KITS)})"
        )


def _check_repository_layout(root: Path, failures: list[str]) -> None:
    if (root / LEGACY_KITS_ROOT).exists():
        failures.append(
            f"a root '{LEGACY_KITS_ROOT}/' directory exists; the kits of this "
            f"repository live under '{KITS_ROOT}/'"
        )


def _check_mcp_entries(
    entries: dict[str, object], label: str, failures: list[str]
) -> bool:
    """Validate one mapping of name -> server config; return False when empty."""
    if not isinstance(entries, dict) or not entries:
        failures.append(f"opencode.json {label} must be a non-empty object of MCP servers")
        return False
    for name, config in entries.items():
        if not isinstance(config, dict):
            failures.append(f"opencode.json MCP server '{name}' must be an object")
            continue
        kind = config.get("type")
        if kind not in MCP_SERVER_TYPES:
            failures.append(
                f"opencode.json MCP server '{name}' must declare type "
                f"{' or '.join(repr(item) for item in MCP_SERVER_TYPES)} (found {kind!r})"
            )
    return True


def _check_opencode_config(root: Path, failures: list[str]) -> None:
    path = root / "opencode.json"
    if not path.is_file():
        failures.append("opencode.json is missing from the repository root")
        return
    raw = _read_text(path, failures, "opencode.json")
    if raw is None:
        return
    if "mcpServers" in raw:
        failures.append(
            "opencode.json contains the invalid 'mcpServers' key; OpenCode expects 'mcp'"
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        failures.append(f"opencode.json is not valid JSON: {exc}")
        return
    if not isinstance(data, dict):
        failures.append("opencode.json must contain a JSON object")
        return
    if "mcp" not in data:
        failures.append("opencode.json is missing the 'mcp' key")
        return
    servers = data["mcp"]
    if not isinstance(servers, dict) or not servers:
        failures.append("opencode.json 'mcp' must be a non-empty object of MCP servers")
        return
    # OpenCode V2 nests servers under ``mcp.servers``; earlier configs list them
    # directly under ``mcp`` (still read by V2). Both shapes are accepted, but
    # ``servers`` is a container, never an MCP server itself.
    flat = {name: config for name, config in servers.items() if name != "servers"}
    nested = servers.get("servers")
    present = False
    if flat:
        present = True
        _check_mcp_entries(flat, "'mcp'", failures)
    if nested is not None:
        present = True
        _check_mcp_entries(nested, "'mcp.servers'", failures)
    if not present:
        failures.append("opencode.json 'mcp' must be a non-empty object of MCP servers")


def _check_agents_md(root: Path, failures: list[str]) -> None:
    path = root / "AGENTS.md"
    if not path.is_file():
        failures.append("AGENTS.md is missing from the repository root")
        return
    text = _read_text(path, failures, "AGENTS.md")
    if text is None:
        return
    words = count_words(text)
    if words < AGENTS_MD_WORD_FLOOR:
        failures.append(
            f"AGENTS.md has {words} words, below the declared floor of {AGENTS_MD_WORD_FLOOR}"
        )
    elif words > AGENTS_MD_WORD_BUDGET:
        failures.append(
            f"AGENTS.md has {words} words, above the declared budget of {AGENTS_MD_WORD_BUDGET}"
        )


def _check_agents_md_invariants(root: Path, failures: list[str]) -> None:
    """Verify the six invariants the root constitution must keep.

    The word-count band is a size proxy and cannot detect the deletion of an
    invariant, so this check tests the invariant markers themselves.
    """
    path = root / "AGENTS.md"
    if not path.is_file():
        failures.append(
            "AGENTS.md is missing from the repository root; its invariants cannot be verified"
        )
        return
    text = _read_text(path, failures, "AGENTS.md")
    if text is None:
        return
    haystack = text.casefold()
    for label, marker in AGENTS_MD_INVARIANTS.items():
        if marker.casefold() not in haystack:
            failures.append(
                f"AGENTS.md is missing the {label} (expected marker: {marker!r})"
            )


def _check_policy_facts(root: Path, failures: list[str]) -> None:
    path = root / POLICY_REL
    if not path.is_file():
        failures.append(f"the policy document is missing at {POLICY_REL.as_posix()}")
        return
    text = _read_text(path, failures, POLICY_REL.as_posix())
    if text is None:
        return
    try:
        block = extract_facts_block(text)
    except ValueError as exc:
        failures.append(f"the policy facts block is malformed: {exc}")
        return
    for token in FORBIDDEN_FACTS_TOKENS:
        if token.casefold() in block.casefold():
            failures.append(
                f"the policy facts block contains the forbidden false-invariant token {token!r}"
            )
    try:
        facts = parse_facts(block)
    except ValueError as exc:
        failures.append(f"the policy facts block is malformed: {exc}")
        return
    missing = sorted(set(REQUIRED_FACTS_KEYS) - set(facts))
    unknown = sorted(set(facts) - set(REQUIRED_FACTS_KEYS))
    if missing:
        failures.append(
            f"the policy facts block is missing required keys: {', '.join(missing)}"
        )
    if unknown:
        failures.append(
            f"the policy facts block declares unexpected keys: {', '.join(unknown)}"
        )
    for key, expected in REQUIRED_FACTS_KEYS.items():
        if key in facts and facts[key] != expected:
            failures.append(
                f"the policy facts block declares {key}={facts[key]!r} "
                f"but the check script declares {expected!r}"
            )


def _check_policy_provenance(root: Path, failures: list[str]) -> None:
    path = root / POLICY_REL
    if not path.is_file():
        failures.append(f"the policy document is missing at {POLICY_REL.as_posix()}")
        return
    text = _read_text(path, failures, POLICY_REL.as_posix())
    if text is None:
        return
    prose = strip_facts_block(text)
    if SOURCE_REPORT not in prose:
        failures.append(
            f"the policy document must cite the source report '{SOURCE_REPORT}' "
            "in its prose (not only inside the machine-checked facts block)"
        )


CHECKS = (
    ("kit inventory", _check_kit_inventory),
    ("repository layout", _check_repository_layout),
    ("opencode.json MCP configuration", _check_opencode_config),
    ("AGENTS.md word budget", _check_agents_md),
    ("AGENTS.md invariants", _check_agents_md_invariants),
    ("policy facts block", _check_policy_facts),
    ("policy provenance", _check_policy_provenance),
)


def check(root: Path) -> list[str]:
    """Return the failure messages for ``root``; an empty list means pass."""
    failures: list[str] = []
    for _label, checker in CHECKS:
        checker(root, failures)
    return failures


def advisories(root: Path) -> list[str]:
    """Return non-blocking observations (nested virtual environments)."""
    notes: list[str] = []
    tools = root / KITS_ROOT
    if not tools.is_dir():
        return notes
    for child in sorted(tools.iterdir()):
        if (child / ".venv").is_dir():
            notes.append(
                f"{child.name}/.venv exists - gitignored, but it sits inside a tracked kit "
                f"tree; scope repository searches to {KITS_ROOT}/{child.name}/src "
                "instead of recursing from the repository root"
            )
    return notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the context-efficiency policy against this repository."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="run the drift check (the default and only behaviour)",
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="repository root to inspect"
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    for note in advisories(root):
        print(f"[ADVISORY] {note}")

    failures: list[str] = []
    for label, checker in CHECKS:
        before = len(failures)
        checker(root, failures)
        for message in failures[before:]:
            print(f"[FAIL] {label}: {message}")
        if len(failures) == before:
            print(f"[OK] {label}")

    if failures:
        print(f"[FAIL] context-policy drift check failed: {len(failures)} problem(s)")
        return 1
    print("[OK] context-policy drift check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
