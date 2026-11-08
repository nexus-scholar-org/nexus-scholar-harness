"""M7-method M3/M4: one reader for the method values, and corpus acceptance uses it."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_harness.screening.method import PROTOCOL_METHOD_INVALID, MethodInvalid, effective_method

BLOCK = {
    "dedup": {"doi": True, "title_similarity": 0.93, "first_author": True, "year_tolerance": 0},
    "rules_version": "screening-rules-v1",
    "not_reported": "exclude",
    "blinding": "show",
}


def _ws(tmp_path: Path, protocol: dict | None) -> Path:
    if protocol is not None:
        (tmp_path / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    return tmp_path


def test_no_protocol_or_no_block_gives_the_defaults(tmp_path: Path) -> None:
    for protocol in (None, {"protocol_id": "p"}):
        method = effective_method(_ws(tmp_path, protocol))
        assert method.source == "defaults"
        assert method.config.dedup.title_similarity == 0.97
        assert method.config.not_reported == "unclear"
        assert method.config.blinding == "reveal_after_decision"


def test_the_block_is_read_as_written(tmp_path: Path) -> None:
    method = effective_method(_ws(tmp_path, {"protocol_id": "p", "method": BLOCK}))
    assert method.source == "protocol"
    assert method.as_dict() == {"source": "protocol", **BLOCK}
    dedup = method.deduplicator()
    assert (dedup.title_similarity, dedup.first_author, dedup.year_tolerance) == (0.93, True, 0)


def test_an_invalid_block_is_refused_never_replaced_by_defaults(tmp_path: Path) -> None:
    bad = {**BLOCK, "not_reported": "include"}
    with pytest.raises(MethodInvalid) as raised:
        effective_method(_ws(tmp_path, {"protocol_id": "p", "method": bad}))
    assert raised.value.code == PROTOCOL_METHOD_INVALID
    assert "not_reported" in str(raised.value)
