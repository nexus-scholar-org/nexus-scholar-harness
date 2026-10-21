from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_context_policy.py"
SPEC = importlib.util.spec_from_file_location("check_context_policy", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _facts(**overrides: str) -> dict[str, str]:
    facts = dict(MODULE.REQUIRED_FACTS_KEYS)
    facts.update(overrides)
    return facts


def _policy_text(
    facts: dict[str, str] | None = None,
    *,
    report: str = MODULE.SOURCE_REPORT,
) -> str:
    resolved = facts if facts is not None else _facts()
    body = "\n".join(f"{key}={value}" for key, value in resolved.items())
    return (
        "# Context efficiency policy (fixture)\n\n"
        f"Assessed against the external report {report} on 2026-10-20.\n\n"
        "```text\n"
        f"{MODULE.FACTS_BEGIN}\n{body}\n{MODULE.FACTS_END}\n"
        "```\n"
    )


def _agents_md_text(target_words: int) -> str:
    """An AGENTS.md that carries every invariant marker at an exact word count."""
    markers = " ".join(MODULE.AGENTS_MD_INVARIANTS.values())
    filler = max(target_words - len(markers.split()), 0)
    return " ".join([markers, *["constitution"] * filler]) + "\n"


def _write_root(
    tmp_path: Path,
    *,
    kits: tuple[str, ...] | None = None,
    opencode: dict | None = None,
    agents_words: int = 800,
    policy: str | None = None,
) -> Path:
    """Build a minimal fixture repository that the drift check accepts."""
    root = tmp_path / "repo"
    tools = root / MODULE.KITS_ROOT
    tools.mkdir(parents=True)
    for kit in MODULE.EXPECTED_KITS if kits is None else kits:
        kit_dir = tools / kit
        kit_dir.mkdir(parents=True)
        (kit_dir / "pyproject.toml").write_text(
            f'[project]\nname = "{kit}"\n', encoding="utf-8"
        )
    config = {"mcp": {"nexus-scholar": {"type": "local", "command": ["uv"]}}}
    (root / "opencode.json").write_text(
        json.dumps(opencode if opencode is not None else config, indent=2),
        encoding="utf-8",
    )
    (root / "AGENTS.md").write_text(_agents_md_text(agents_words), encoding="utf-8")
    docs = root / "docs" / "architecture"
    docs.mkdir(parents=True)
    (docs / "context_efficiency_policy.md").write_text(
        policy if policy is not None else _policy_text(), encoding="utf-8"
    )
    return root


def _messages(root: Path) -> list[str]:
    return MODULE.check(root)


def test_real_repository_satisfies_the_policy() -> None:
    """The checked-in repository must match the policy it carries."""
    assert MODULE.check(ROOT) == []


def test_valid_fixture_root_reports_no_failures(tmp_path: Path) -> None:
    """A faithful fixture must not produce false positives."""
    root = _write_root(tmp_path)
    assert MODULE.check(root) == []


def test_missing_kit_is_reported_by_name(tmp_path: Path) -> None:
    kits = tuple(k for k in MODULE.EXPECTED_KITS if k != "scholar-bib-kit")
    root = _write_root(tmp_path, kits=kits)
    messages = _messages(root)
    assert messages
    assert any("scholar-bib-kit" in message for message in messages)


def test_unexpected_legacy_kit_is_reported_by_name(tmp_path: Path) -> None:
    kits = (*MODULE.EXPECTED_KITS, "scholar-monitor-kit")
    root = _write_root(tmp_path, kits=kits)
    messages = _messages(root)
    assert messages
    assert any("scholar-monitor-kit" in message for message in messages)


def test_root_kits_directory_is_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path)
    (root / "kits").mkdir()
    messages = _messages(root)
    assert messages
    assert any("kits/" in message for message in messages)


def test_mcpservers_key_is_rejected(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        opencode={"mcpServers": {"nexus-scholar": {"type": "local"}}},
    )
    messages = _messages(root)
    assert messages
    assert any("mcpServers" in message for message in messages)


def test_mcp_server_without_type_is_rejected(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        opencode={"mcp": {"nexus-scholar": {"command": ["uv"]}}},
    )
    messages = _messages(root)
    assert messages
    assert any("type" in message for message in messages)


def test_agents_md_above_budget_is_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path, agents_words=MODULE.AGENTS_MD_WORD_BUDGET + 1)
    messages = _messages(root)
    assert messages
    assert any("above the declared budget" in message for message in messages)


def test_agents_md_below_floor_is_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path, agents_words=MODULE.AGENTS_MD_WORD_FLOOR - 1)
    messages = _messages(root)
    assert messages
    assert any("below the declared floor" in message for message in messages)


@pytest.mark.parametrize("token", MODULE.FORBIDDEN_FACTS_TOKENS)
def test_forbidden_false_invariant_token_in_facts_block_is_rejected(
    tmp_path: Path, token: str
) -> None:
    facts = _facts()
    facts["kits"] = f"{facts['kits']},{token}"
    root = _write_root(tmp_path, policy=_policy_text(facts))
    messages = _messages(root)
    assert messages
    assert any(
        "forbidden false-invariant token" in message and token in message
        for message in messages
    )


def test_policy_without_source_report_citation_is_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path, policy=_policy_text(report=""))
    messages = _messages(root)
    assert messages
    assert any(MODULE.SOURCE_REPORT in message for message in messages)


def test_facts_block_disagreeing_with_constants_is_rejected(tmp_path: Path) -> None:
    facts = _facts(kits="scholar-agent-kit,scholar-bib-kit")
    root = _write_root(tmp_path, policy=_policy_text(facts))
    messages = _messages(root)
    assert messages
    assert any(
        "declares kits=" in message and "check script declares" in message
        for message in messages
    )


def test_facts_block_with_missing_key_is_rejected(tmp_path: Path) -> None:
    facts = _facts()
    del facts["agents_md_word_budget"]
    root = _write_root(tmp_path, policy=_policy_text(facts))
    messages = _messages(root)
    assert messages
    assert any("missing required keys" in message for message in messages)


def test_policy_document_missing_is_rejected(tmp_path: Path) -> None:
    root = _write_root(tmp_path)
    (root / "docs" / "architecture" / "context_efficiency_policy.md").unlink()
    messages = _messages(root)
    assert messages
    assert any("policy document is missing" in message for message in messages)


def test_missing_agents_md_invariant_is_reported_by_name(tmp_path: Path) -> None:
    """The invariant check must detect a deleted invariant, not just a size drop."""
    root = _write_root(tmp_path)
    path = root / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    marker = MODULE.AGENTS_MD_INVARIANTS["contract-v1 baseline gate"]
    assert marker in text
    path.write_text(text.replace(marker, "REDACTED"), encoding="utf-8")
    messages = _messages(root)
    assert messages
    assert any(
        "contract-v1 baseline gate" in message and "AGENTS.md is missing" in message
        for message in messages
    )


@pytest.mark.parametrize(
    ("label", "marker"),
    list(MODULE.AGENTS_MD_INVARIANTS.items()),
)
def test_every_agents_md_invariant_is_checked(
    tmp_path: Path, label: str, marker: str
) -> None:
    """Removing any single invariant marker must be detected."""
    root = _write_root(tmp_path)
    path = root / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    assert marker in text
    path.write_text(text.replace(marker, "REDACTED"), encoding="utf-8")
    messages = _messages(root)
    assert messages
    assert any(label in message for message in messages)


def test_invalid_utf8_agents_md_is_reported_not_raised(tmp_path: Path) -> None:
    """A malformed AGENTS.md must be a reported failure, never a traceback."""
    root = _write_root(tmp_path)
    (root / "AGENTS.md").write_bytes(b"\xff\xfe\x00broken bytes")
    messages = _messages(root)
    assert messages
    assert any(
        "AGENTS.md" in message and "not valid UTF-8" in message for message in messages
    )


def test_invalid_utf8_policy_document_is_reported_not_raised(tmp_path: Path) -> None:
    """A malformed policy document must be a reported failure, never a traceback."""
    root = _write_root(tmp_path)
    (root / "docs" / "architecture" / "context_efficiency_policy.md").write_bytes(
        b"\xff\xfe\x00broken bytes"
    )
    messages = _messages(root)
    assert messages
    assert any(
        "context_efficiency_policy.md" in message and "not valid UTF-8" in message
        for message in messages
    )


def test_nested_virtual_environment_is_an_advisory_not_a_failure(
    tmp_path: Path,
) -> None:
    root = _write_root(tmp_path)
    (root / MODULE.KITS_ROOT / "scholar-agent-kit" / ".venv").mkdir()
    assert MODULE.check(root) == []
    notes = MODULE.advisories(root)
    assert notes
    assert any(".venv" in note for note in notes)
