"""M10a: the arXiv re-record splice keeps every other recorded interaction byte for byte."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CASSETTE = ROOT / "tests" / "fixtures" / "cassettes" / "golden_recon_probe.yaml"


def _script():
    spec = importlib.util.spec_from_file_location("record_golden_recon_arxiv", ROOT / "scripts" / "record_golden_recon_arxiv.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _golden() -> str:
    with CASSETTE.open(encoding="utf-8", newline="") as fh:
        return fh.read()


NEW_ARXIV = """interactions:
- request:
    body: ''
    headers: {}
    method: GET
    uri: https://export.arxiv.org/api/query?max_results=25&search_query=all%3AUAV+AND+all%3Acrop&start=0
  response:
    body:
      string: new
    status:
      code: 200
      message: OK
version: 1
"""


def _old_arxiv_block(start: int, eol: str) -> str:
    """An arXiv interaction as recorded before M10a (terms joined by a space, read as OR)."""
    lines = [
        "- request:",
        "    body: ''",
        "    headers: {}",
        "    method: GET",
        f"    uri: https://export.arxiv.org/api/query?max_results=25&search_query=all%3AUAV+all%3Acrop+all%3Aweed&start={start}",
        "  response:",
        "    body:",
        "      string: old",
        "    status:",
        "      code: 200",
        "      message: OK",
    ]
    return "".join(line + eol for line in lines)


def _golden_with_two_old_arxiv(rec) -> str:
    """The golden cassette with its arXiv interactions replaced by two pre-M10a ones.

    The real cassette holds whatever arXiv answer was recorded last (one
    interaction since the 2026-11-15 re-record), so the splice is tested on a
    fixed starting point built from the real non-arXiv interactions. As in the
    pre-M10a recording, the two arXiv pages are apart: another database's
    interaction sits between them.
    """
    golden = _golden()
    eol = "\r\n" if "\r\n" in golden else "\n"
    head, blocks, tail = rec.split_interactions(golden)
    first = next(i for i, b in enumerate(blocks) if rec.is_arxiv(b))
    others = [b for b in blocks if not rec.is_arxiv(b)]
    assert len(others) > first, "a non-arXiv interaction follows the first arXiv slot"
    order = others[:first] + [_old_arxiv_block(0, eol), others[first], _old_arxiv_block(25, eol)] + others[first + 1 :]
    return head + "".join(order) + tail


def test_the_splice_replaces_only_the_arxiv_interactions():
    rec = _script()
    before = _golden_with_two_old_arxiv(rec)
    updated = rec.splice(before, NEW_ARXIV)
    _h, old, _t = rec.split_interactions(before)
    head, new, tail = rec.split_interactions(updated)
    assert [b for b in old if not rec.is_arxiv(b)] == [b for b in new if not rec.is_arxiv(b)]
    assert sum(map(rec.is_arxiv, old)) == 2 and sum(map(rec.is_arxiv, new)) == 1
    flags = [rec.is_arxiv(b) for b in old]
    assert not flags[flags.index(True) + 1], "the two old arXiv pages are apart, as recorded before M10a"
    # The new arXiv interaction takes the place of the first old one.
    assert [rec.is_arxiv(b) for b in new].index(True) == flags.index(True)
    assert "all%3AUAV+AND+all%3Acrop" in updated
    assert "all%3AUAV+all%3Acrop+all%3Aweed" not in updated
    assert updated.startswith(head) and updated.endswith(tail) and tail.startswith("version:")


def test_the_golden_cassette_holds_the_arxiv_answer_to_the_and_query():
    """Decision 3a: the recorded arXiv request joins the terms with AND."""
    rec = _script()
    _h, blocks, _t = rec.split_interactions(_golden())
    arxiv = [b for b in blocks if rec.is_arxiv(b)]
    assert arxiv and all("+AND+" in b for b in arxiv)


def test_the_splice_refuses_a_recording_of_another_database():
    rec = _script()
    other = NEW_ARXIV.replace("export.arxiv.org/api/query", "api.crossref.org/works")
    with pytest.raises(ValueError):
        rec.splice(_golden(), other)


def test_recording_without_a_contact_address_is_refused(monkeypatch, capsys):
    rec = _script()
    monkeypatch.delenv("SCHOLAR_MAILTO", raising=False)
    assert rec.main([]) == 2
    assert "SCHOLAR_MAILTO" in capsys.readouterr().err


# --------------------------------------------------------------------------- M3h-c: the search cassette, the date clause

SEARCH = ROOT / "tests" / "fixtures" / "cassettes" / "golden_uav_search.yaml"
OK_LEG = {
    "status": "ok",
    "fetched": 12,
    "reported_total": 40,
    "executed_query": "(all:uav) AND submittedDate:[202001010000 TO 202612312359]",
}


def test_the_splice_replaces_only_the_arxiv_interaction_of_the_search_cassette():
    rec = _script()
    with SEARCH.open(encoding="utf-8", newline="") as fh:
        golden = fh.read()
    updated = rec.splice(golden, NEW_ARXIV)
    _h, old, _t = rec.split_interactions(golden)
    head, new, tail = rec.split_interactions(updated)
    assert [b for b in old if not rec.is_arxiv(b)] == [b for b in new if not rec.is_arxiv(b)]
    assert sum(map(rec.is_arxiv, new)) == 1
    assert [rec.is_arxiv(b) for b in new] == [rec.is_arxiv(b) for b in old], "the new answer takes the old one's place"
    assert updated.startswith(head) and updated.endswith(tail) and tail.startswith("version:")


def test_a_recording_is_checked_before_it_is_spliced():
    rec = _script()
    assert rec.check_recording("fine", OK_LEG, "me@example.org") == []
    assert any("contact address" in p for p in rec.check_recording("to me@example.org", OK_LEG, "me@example.org"))
    assert any("not 'ok'" in p for p in rec.check_recording("x", {**OK_LEG, "status": "failed", "error": "429"}))
    assert any("no record" in p for p in rec.check_recording("x", {**OK_LEG, "fetched": 0}))
    assert any("submittedDate" in p for p in rec.check_recording("x", {**OK_LEG, "executed_query": "all:uav"}))
    feed = "<id>http://arxiv.org/api/errors#incorrect_id_format</id>"
    assert any("error feed" in p for p in rec.check_recording(feed, OK_LEG))
    assert rec.check_recording("x", {}) != []


def test_the_script_knows_both_golden_cassettes():
    rec = _script()
    assert set(rec.CASSETTES) == {"recon", "search"}
    assert all(path.is_file() for path in rec.CASSETTES.values())


def test_the_open_ended_check_needs_a_contact_address_too(monkeypatch, capsys):
    rec = _script()
    monkeypatch.delenv("SCHOLAR_MAILTO", raising=False)
    assert rec.main(["--check-open-ended"]) == 2
    assert "SCHOLAR_MAILTO" in capsys.readouterr().err
