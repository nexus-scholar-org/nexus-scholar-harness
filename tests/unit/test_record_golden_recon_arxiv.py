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


def test_the_splice_replaces_only_the_arxiv_interactions():
    rec = _script()
    golden = _golden()
    updated = rec.splice(golden, NEW_ARXIV)
    _h, old, _t = rec.split_interactions(golden)
    head, new, tail = rec.split_interactions(updated)
    assert [b for b in old if not rec.is_arxiv(b)] == [b for b in new if not rec.is_arxiv(b)]
    assert sum(map(rec.is_arxiv, old)) == 2 and sum(map(rec.is_arxiv, new)) == 1
    assert "all%3AUAV+AND+all%3Acrop" in updated
    assert "all%3AUAV+all%3Acrop+all%3Aweed" not in updated
    assert updated.startswith(head) and updated.endswith(tail) and tail.startswith("version:")


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
