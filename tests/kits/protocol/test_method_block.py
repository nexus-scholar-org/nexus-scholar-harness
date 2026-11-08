"""M7-method M1/M2: the optional ``method`` block in the protocol.

Decision 2026-11-08 ("Method parameters move into the protocol"): the dedup
tiers, the rule-table version, the not-reported policy and blinding may be
written into ``protocol.json``. The block is optional and, when absent, left
out of the canonical JSON, so a protocol without it keeps its exact
fingerprint (every existing workspace's decisions stay bound). When present,
its values are hashed, so the signed protocol covers them.
"""

from __future__ import annotations

import copy
import json
import pathlib

import pytest
from pydantic import ValidationError

from scholar_protocol.canonical import canonical_fingerprint, canonical_json
from scholar_protocol.models import KNOWN_RULES_VERSIONS, MethodConfig, ResearchProtocol

CANONICAL = pathlib.Path(__file__).parent / "fixtures" / "canonical"
BASE = json.loads((CANONICAL / "identity_base.json").read_text(encoding="utf-8"))
BASE_FINGERPRINT = (CANONICAL / "identity_base.json.sha256").read_text(encoding="utf-8").split()[0]

DEFAULT_BLOCK = {
    "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
    "rules_version": "screening-rules-v1",
    "not_reported": "unclear",
    "blinding": "reveal_after_decision",
}


def _with(block: dict | None) -> ResearchProtocol:
    raw = copy.deepcopy(BASE)
    if block is not None:
        raw["method"] = block
    return ResearchProtocol.model_validate(raw)


def test_a_protocol_without_the_block_keeps_its_exact_fingerprint() -> None:
    protocol = _with(None)
    assert protocol.method is None
    assert b'"method"' not in canonical_json(protocol)
    assert canonical_fingerprint(protocol) == BASE_FINGERPRINT


def test_the_block_is_hashed_and_its_values_count() -> None:
    with_defaults = _with(DEFAULT_BLOCK)
    assert canonical_fingerprint(with_defaults) != BASE_FINGERPRINT
    body = json.loads(canonical_json(with_defaults))
    assert body["method"] == DEFAULT_BLOCK
    looser = copy.deepcopy(DEFAULT_BLOCK)
    looser["dedup"]["title_similarity"] = 0.95
    assert canonical_fingerprint(_with(looser)) != canonical_fingerprint(with_defaults)


def test_the_defaults_are_todays_values() -> None:
    assert MethodConfig().model_dump(mode="json") == DEFAULT_BLOCK


def test_an_integer_similarity_hashes_like_its_float() -> None:
    """1 and 1.0 are the same threshold; they must not give two fingerprints."""
    one = copy.deepcopy(DEFAULT_BLOCK)
    one["dedup"]["title_similarity"] = 1
    one_float = copy.deepcopy(DEFAULT_BLOCK)
    one_float["dedup"]["title_similarity"] = 1.0
    assert canonical_fingerprint(_with(one)) == canonical_fingerprint(_with(one_float))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("dedup", "title_similarity"), 0.89),
        (("dedup", "title_similarity"), 1.01),
        (("dedup", "year_tolerance"), -1),
        (("dedup", "year_tolerance"), 3),
        (("dedup", "year_tolerance"), True),
        (("dedup", "title_similarity"), 0.975),  # review 2: printed as 0.97
        (("dedup", "title_similarity"), 0.999),  # review 2: printed as 1.00
        (("dedup", "doi"), False),
        (("rules_version",), "screening-rules-v9"),
        (("not_reported",), "include"),
        (("blinding",), "hidden"),
    ],
)
def test_values_outside_the_checked_limits_are_refused(path: tuple[str, ...], value: object) -> None:
    block = copy.deepcopy(DEFAULT_BLOCK)
    target = block
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        _with(block)


def test_unknown_keys_in_the_block_are_refused() -> None:
    """A misspelt key would otherwise be dropped silently and its value never applied."""
    block = copy.deepcopy(DEFAULT_BLOCK)
    block["not_reportd"] = "exclude"
    with pytest.raises(ValidationError):
        _with(block)
    block = copy.deepcopy(DEFAULT_BLOCK)
    block["dedup"]["year_tolerence"] = 0
    with pytest.raises(ValidationError):
        _with(block)


def test_the_engine_knows_every_rules_version_the_protocol_accepts() -> None:
    from scholar_harness.screening.proposals import RULES_VERSION

    assert RULES_VERSION in KNOWN_RULES_VERSIONS
