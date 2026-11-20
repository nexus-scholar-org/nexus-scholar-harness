"""H-screening-drafts item 6: a candidate prompt version, `screen-v2`, measured before any use.

Its only change from `screen-v1` is guidance to answer yes or no when the abstract
gives reasonable grounds; the quote rule and the record-as-data rule are unchanged.
It is never the default, a product run cannot load it, and only `prompt-gate measure
--task-version screen-v2` (a dry run here: no network, no key) can.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from kits.agent.test_measure import MODEL, USAGE, ScriptedDriver, _answer, _no_secrets, _script, _workspace
from scholar_agent.drivers import DriverResult
from typer.testing import CliRunner

from scholar_agent import measure as ms
from scholar_agent import prompt_gate as pg
from scholar_agent.tasks import screening as task_mod
from scholar_harness.cli import app

QUOTE_RULE = (
    "For every `yes` or `no`, copy a short quote that supports it, character for character, from the record "
    "(its title, abstract or `Published:` line): no paraphrase, no ellipsis, no added words, at most about thirty "
    "words. If you cannot find such a quote, the answer is `not_reported`."
)


def test_the_default_task_is_unchanged_and_the_candidate_is_its_own_version():
    default = task_mod.load_task()
    assert default.task_version == "screen-v1" and task_mod.load_task(None).prompt_sha256 == default.prompt_sha256
    assert task_mod.load_task("screen-v1").prompt_sha256 == default.prompt_sha256
    v2 = task_mod.load_task("screen-v2")
    assert v2.task_version == "screen-v2" and v2.prompt_sha256 != default.prompt_sha256
    assert v2.defaults == default.defaults
    assert task_mod.candidate_versions() == {"screen-v2": {"prompt": "prompt-screen-v2.md", "measured": False}}
    with pytest.raises(ValueError, match="unknown screening task version"):
        task_mod.load_task("screen-v9")


def test_the_only_change_is_the_reasonable_grounds_guidance():
    v1, v2 = task_mod.load_task().template, task_mod.load_task("screen-v2").template
    # The quote rule, cannot_decide, reasoning and the record-as-data rule are word for word the same.
    assert QUOTE_RULE in v1 and QUOTE_RULE in v2
    tail = v1[v1.index("Set `cannot_decide`"):].rstrip()
    assert v2.rstrip().endswith(tail)
    assert v1[: v1.index("## How to answer")] == v2[: v2.index("## How to answer")]
    # What changed: the grounds, and the line that keeps not_reported for no grounds.
    assert "reasonable grounds" not in v1 and "reasonable grounds" in v2
    assert "give no grounds either way" in v2


def test_a_product_run_cannot_choose_a_task_version(tmp_path):
    """The run route has no task version field; a run always loads the default task."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "console"))
    from test_screening_api_v1 import BASE, DESKTOP, _workspace as screening_workspace

    from scholar_harness.console import create_app

    ws = screening_workspace(tmp_path)
    client = TestClient(create_app(ws, token=DESKTOP), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})
    refused = client.post(f"{BASE}/proposals/runs", json={"estimate_only": True, "task_version": "screen-v2"})
    assert refused.status_code == 422
    assert client.get(f"{BASE}/proposals/setup").json()["task"]["task_version"] == "screen-v1"


def test_a_dry_run_of_the_candidate_plans_with_its_prompt_and_passes_the_blind_check(tmp_path):
    ws = _workspace(tmp_path)
    plan_v1 = ms.measure(ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=4096, driver=None)
    plan_v2 = ms.measure(ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=4096, driver=None,
                         task_version="screen-v2")
    assert plan_v2["network_calls"] == 0 and plan_v2["blind_check"] == "passed"
    assert plan_v2["records"] == plan_v1["records"]
    assert plan_v2["prompt"]["system_tokens"] > plan_v1["prompt"]["system_tokens"]  # the added guidance


def test_a_scripted_measurement_of_the_candidate_reports_its_version(tmp_path):
    ws = _workspace(tmp_path)
    report = ms.measure(ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=1024,
                        driver=ScriptedDriver(), out_dir=tmp_path / "out", task_version="screen-v2")
    assert report["task_version"] == "screen-v2"
    assert report["prompt_sha256"] == task_mod.load_task("screen-v2").prompt_sha256
    assert report["paths"]["json"].endswith("_screen-v2.json")


def test_the_cli_dry_run_takes_the_task_version_and_reads_no_key(tmp_path, monkeypatch):
    _no_secrets(monkeypatch)
    ws = _workspace(tmp_path)
    result = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", str(ws), "--scope", "all",
                                      "--model", MODEL, "--task-version", "screen-v2", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "task screen-v2" in result.output and "Network calls made: 0" in result.output
    unknown = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", str(ws), "--scope", "all",
                                       "--task-version", "screen-v9", "--dry-run"])
    assert unknown.exit_code == 1 and "unknown screening task version" in unknown.output


def test_the_gate_spec_of_the_default_is_unchanged():
    spec = pg.run_spec({"screening_criteria": {"inclusion": [{"id": "INC-01", "description": "x"}]}},
                       model="m", effort="low", max_tokens=10)
    assert spec.task_version == ""


def test_the_measurement_can_derive_under_another_not_reported_policy(tmp_path):
    """The frozen set's protocol says nothing (`unclear`); `--not-reported decisive_first` re-derives offline."""
    ws = _workspace(tmp_path)
    # One record answers EXC-01 yes beside an unreported INC-01: Unclear as-is, Exclude under decisive_first.
    script = {**_script(), "SCI-000009": lambda s: DriverResult(
        s, "ok", output=_answer("UAV weeds 9", inc="not_reported", exc="yes"), usage=USAGE, model=MODEL)}
    as_is = ms.measure(ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=1024,
                       driver=ScriptedDriver(script), out_dir=tmp_path / "a")
    decisive = ms.measure(ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=1024,
                          driver=ScriptedDriver(script), out_dir=tmp_path / "b", not_reported="decisive_first")
    assert (as_is["not_reported_policy"], decisive["not_reported_policy"]) == ("unclear", "decisive_first")
    assert "`decisive_first` not-reported rule" in (tmp_path / "b").joinpath(
        next(p.name for p in (tmp_path / "b").glob("*.md"))).read_text(encoding="utf-8")
    # A decisive answer beside a gap is Unclear as-is and decided under decisive_first: never more Unclear.
    unclear = lambda r: sum(row["MAYBE"] for row in r["confusion"]["table"].values())  # noqa: E731
    assert unclear(decisive) <= unclear(as_is)
    # Review: the rule changes an outcome here, it is not only a label.
    assert as_is["confusion"]["table"]["EXCLUDE"]["MAYBE"] == decisive["confusion"]["table"]["EXCLUDE"]["MAYBE"] + 1
    assert decisive["confusion"]["table"]["EXCLUDE"]["EXCLUDE"] == as_is["confusion"]["table"]["EXCLUDE"]["EXCLUDE"] + 1


def test_the_measurement_reads_the_workspaces_amended_rule(tmp_path, monkeypatch):
    """Review F5: without --not-reported the rule is the workspace's rule in force (amendments included)."""
    from dataclasses import replace

    from scholar_harness.screening import method as m

    real = m.effective_method
    asked = []

    def amended(ws, **kw):
        asked.append(ws)
        method = real(ws, **kw)
        return replace(method, config=method.config.model_copy(update={"not_reported": "decisive_first"}))

    monkeypatch.setattr(m, "effective_method", amended)
    ws = _workspace(tmp_path)
    report = ms.measure(ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=1024,
                        driver=ScriptedDriver(), out_dir=tmp_path / "c")
    assert asked == [ws] and report["not_reported_policy"] == "decisive_first"


def test_the_cli_refuses_an_unknown_not_reported_policy(tmp_path, monkeypatch):
    _no_secrets(monkeypatch)
    ws = _workspace(tmp_path)
    result = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", str(ws), "--scope", "all",
                                      "--not-reported", "include", "--dry-run"])
    assert result.exit_code == 1 and "--not-reported must be one of" in result.output
