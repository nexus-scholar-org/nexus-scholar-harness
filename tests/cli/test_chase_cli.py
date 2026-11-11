"""M3g-citation-chasing: ``nexus-scholar chase run|status`` (offline, fake databases)."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.pipeline import discovery as disc

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_chase_helpers", _HERE.parent / "pipeline" / "test_citation_chase.py")
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)

runner = CliRunner()
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    return helpers.build_ws(tmp_path)


def _install(monkeypatch, *providers) -> None:
    by_name = {p.name: p for p in providers}
    monkeypatch.setattr(disc, "_resolve_providers", lambda names: [by_name[n] for n in names if n in by_name] or None)


def test_chase_help_answers_on_the_base_install():
    result = runner.invoke(app, ["chase", "--help"])
    assert result.exit_code == 0
    assert "run" in result.output and "status" in result.output
    run_help = runner.invoke(app, ["chase", "run", "--help"])
    assert run_help.exit_code == 0 and "--cap-per-seed" in _plain(run_help.output)


def test_chase_run_writes_the_run_and_status_lists_it(ws, monkeypatch):
    doc = helpers._doc("Cited work", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    _install(monkeypatch, helpers.FakeChaseProvider("openalex", citations={helpers.W_INCLUDE: [doc]}))

    result = runner.invoke(app, ["chase", "run", str(ws), "--providers", "openalex", "--directions", "forward", "--note", "cli"])
    out = _plain(result.output)
    assert result.exit_code == 0, out
    assert "SUCCESS chase_001" in out and "new 1" in out
    assert "chase accept" in out
    manifest = json.loads((ws / "literature" / "citation_chase" / "chase_001" / "chase.json").read_text(encoding="utf-8"))
    assert manifest["directions"] == ["forward"] and manifest["providers"] == ["openalex"]
    assert manifest["notes"] == ["cli"] and manifest["forward_cap"] == 500 and manifest["run_ceiling"] == 5000

    status = runner.invoke(app, ["chase", "status", str(ws)])
    assert status.exit_code == 0
    plain = _plain(status.output)
    assert "chase_001" in plain and "SUCCESS" in plain


def test_chase_run_passes_caps_and_seeds_and_exits_nonzero_when_every_database_fails(ws, monkeypatch):
    from scholar_search.exceptions import ProviderError

    citing = [helpers._doc(f"C{i}", provider="openalex", pid=f"W{i}", doi=f"10.2/{i}", openalex=f"W{i}") for i in range(4)]
    _install(monkeypatch, helpers.FakeChaseProvider("openalex", citations={helpers.W_INCLUDE: citing}))
    result = runner.invoke(app, [
        "chase", "run", str(ws), "--providers", "openalex", "--cap-per-seed", "2", "--ceiling", "1",
        "--seeds", "included+unclear",
    ])
    assert result.exit_code == 0, _plain(result.output)
    manifest = json.loads((ws / "literature" / "citation_chase" / "chase_001" / "chase.json").read_text(encoding="utf-8"))
    assert manifest["forward_cap"] == 2 and manifest["run_ceiling"] == 1 and manifest["seed_source"] == "included+unclear"
    assert manifest["status"] == "PARTIAL" and manifest["counts"]["new"] == 1
    assert "PARTIAL chase_001" in _plain(result.output)

    _install(monkeypatch, helpers.FakeChaseProvider("openalex", fail=ProviderError("openalex", "no key", status_code=403)))
    failed = runner.invoke(app, ["chase", "run", str(ws), "--providers", "openalex"])
    assert failed.exit_code == 1
    out = _plain(failed.output)
    assert "FAILED chase_002" in out and "PROVIDER_REFUSED" in out


def test_chase_run_refuses_without_a_published_screening_and_on_bad_options(ws, monkeypatch):
    _install(monkeypatch, helpers.FakeChaseProvider("openalex"))
    bad = runner.invoke(app, ["chase", "run", str(ws), "--directions", "sideways"])
    assert bad.exit_code == 2 and "both, forward or backward" in _plain(bad.output)

    (ws / "literature" / "included.json").unlink()
    result = runner.invoke(app, ["chase", "run", str(ws), "--providers", "openalex"])
    assert result.exit_code == 1
    assert "SCREENING_NOT_PUBLISHED" in _plain(result.output)
    assert not (ws / "literature" / "citation_chase").exists()

    empty = runner.invoke(app, ["chase", "status", str(ws)])
    assert empty.exit_code == 0 and "No citation chase" in _plain(empty.output)
