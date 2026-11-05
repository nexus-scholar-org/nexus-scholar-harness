"""The console refusal set and the screening API contract §7 stay in step."""

from __future__ import annotations

import re
from pathlib import Path

from scholar_harness.console import refusals

CONTRACT = Path(__file__).resolve().parents[2] / "docs" / "architecture" / "screening-api-contract.md"


def _proposed_codes() -> set[str]:
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split("**Proposed here**", 1)[1].split("## 8.", 1)[0]
    return set(re.findall(r"^\| `([A-Z_]+)` \|", section, flags=re.M))


def test_every_contract_code_is_in_the_console_set():
    proposed = _proposed_codes()
    assert len(proposed) >= 9  # anti-vacuity: the table parsed
    engine_codes = proposed - {"ENGINE_UNREACHABLE"}  # client-side only
    assert engine_codes == set(refusals.CONTRACT_ADDED)


def test_codes_are_their_own_names():
    for code in refusals.CONSOLE_REFUSALS:
        assert re.fullmatch(r"[A-Z][A-Z_]+", code)
    assert refusals.CONTRACT_ADDED <= refusals.CONSOLE_REFUSALS
