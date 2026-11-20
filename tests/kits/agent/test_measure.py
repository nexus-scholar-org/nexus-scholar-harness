"""M9a-measure: the whole path on a scripted driver, so no model is ever called.

The fake driver answers per study id, in chunks, and can return a truncated, a
refused, an invalid and a malformed answer. The scorer, the report, the dry run
and the ceiling are proven on it; the real run is the same code with a real
driver and waits for the researcher's approval of spend.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_agent import measure as ms
from scholar_agent import prompt_gate as pg
from scholar_agent.drivers import DriverResult, RunSpec, ScreeningRequest, Usage
from scholar_harness.cli import app

PROTOCOL = {
    "screening_criteria": {
        "inclusion": [{"id": "INC-01", "criterion": "UAV imagery"}],
        "exclusion": [{"id": "EXC-01", "criterion": "not agricultural"}],
    }
}
USAGE = Usage(input_tokens=1000, output_tokens=100)
MODEL = "claude-haiku-5-5"
#: 0.1/M input + 0.5/M output (the price table), direct calls (12 records <= the direct limit).
COST_PER_RECORD = (1000 * 0.10 + 100 * 0.50) / 1_000_000
HUMAN = {  # study id -> the researcher's decision
    **{f"SCI-{i:06d}": "INCLUDE" for i in range(0, 4)},
    "SCI-000004": "MAYBE",  # the researcher's own Unclear counts as an include
    **{f"SCI-{i:06d}": "EXCLUDE" for i in range(5, 12)},
}


def _workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "v03"
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True)
    artifacts = []
    for batch, ids in (("batch_001", range(0, 6)), ("batch_002", range(6, 12))):
        papers = [
            {"workspace_id": f"SCI-{i:06d}", "title": f"UAV weeds {i}", "abstract": f"Drone maize study {i}.", "year": "2024"} for i in ids
        ]
        (screening / f"{batch}.json").write_text(json.dumps({"papers": papers}), encoding="utf-8")
        body = json.dumps({"decisions": [{"workspace_id": p["workspace_id"], "decision": HUMAN[p["workspace_id"]]} for p in papers]})
        (screening / f"{batch}_decisions.json").write_text(body, encoding="utf-8")
        artifacts.append({"path": f"literature/screening/{batch}_decisions.json", "sha256": hashlib.sha256(body.encode()).hexdigest()})
    (screening / "HUMAN_CONFIRMATION.json").write_text(json.dumps({"artifacts": artifacts, "reviewer": {"name": "R"}}), encoding="utf-8")
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL), encoding="utf-8")
    return ws


def _answer(record_title: str, inc: str, exc: str = "no", *, quote: str | None = None, cannot: bool = False) -> dict:
    q = record_title if quote is None else quote
    return {
        "criteria": [
            {"id": "INC-01", "answer": inc, "quote": q if inc != "not_reported" else ""},
            {"id": "EXC-01", "answer": exc, "quote": "Published: 2024" if exc != "not_reported" else ""},
        ],
        "cannot_decide": cannot,
        "reasoning": "scripted",
    }


def _script() -> dict[str, Callable[[str], DriverResult]]:
    """One scripted behaviour per study; see the assertions below for what each becomes."""

    def ok(sid: str, **kw) -> DriverResult:
        return DriverResult(sid, "ok", output=_answer(f"UAV weeds {int(sid[4:])}", **kw), usage=USAGE, model=MODEL)

    def fail(status: str, detail: str = "") -> Callable[[str], DriverResult]:
        return lambda sid: DriverResult(sid, status, detail=detail, usage=USAGE, model=MODEL)

    return {
        "SCI-000000": lambda s: ok(s, inc="yes"),  # include kept as Include
        "SCI-000001": fail("refusal", "bio"),  # include, refused -> Unclear
        "SCI-000002": fail("truncated", "max_tokens"),  # include, cut off -> Unclear
        "SCI-000003": lambda s: ok(s, inc="no"),  # include MISSED (Exclude)
        "SCI-000004": lambda s: ok(s, inc="yes"),  # the researcher's Unclear, kept as Include
        "SCI-000005": fail("invalid", "not JSON"),  # exclude, malformed text -> Unclear
        "SCI-000006": lambda s: DriverResult(s, "ok", output={"criteria": "no"}, usage=USAGE, model=MODEL),  # parsed but malformed
        "SCI-000007": lambda s: ok(s, inc="yes", cannot=True),  # the agent says it cannot decide
        "SCI-000008": lambda s: ok(s, inc="no", quote="words that are not in the record"),  # quote not in the source
        "SCI-000009": lambda s: ok(s, inc="no"),  # exclude caught
        "SCI-000010": lambda s: ok(s, inc="yes"),  # exclude wrongly Included (a precision miss)
        "SCI-000011": lambda s: ok(s, inc="no"),  # exclude caught
    }


class ScriptedDriver:
    """Answers each request from the script, `chunk` at a time, and records what it was sent."""

    provider = "anthropic"

    def __init__(self, script=None, *, chunk: int = 100):
        self.script = script or _script()
        self.chunk = chunk
        self.calls = 0
        self.sent: list[ScreeningRequest] = []
        self.specs: list[RunSpec] = []

    def run(self, requests, spec, *, on_result=None, cancelled=lambda: False):
        self.specs.append(spec)
        results = []
        for start in range(0, len(requests), self.chunk):
            if cancelled():
                break  # like the real drivers: a stopped run sends no further chunk
            self.calls += 1
            for request in requests[start : start + self.chunk]:
                self.sent.append(request)
                result = self.script[request.custom_id](request.custom_id)
                results.append(result)
                if on_result:
                    on_result(result)
        return results


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode() + path.read_bytes())
    return digest.hexdigest()


def _measure(tmp_path: Path, driver, **kw):
    ws = _workspace(tmp_path)
    return ws, ms.measure(
        ws, scope="all", provider="anthropic", model=MODEL, effort="low", max_tokens=1024,
        driver=driver, out_dir=tmp_path / "out", **kw,
    )


# --- the scorer and the report ---------------------------------------------------


def test_report_on_a_scripted_driver_proves_the_scorer_and_every_section(tmp_path):
    driver = ScriptedDriver()
    ws, report = _measure(tmp_path, driver)
    assert report["scored"] == 12 and report["not_reached"]["count"] == 0 and report["measured"] is True

    # Researcher's includes: 0-3 and the Unclear 4. Kept = 0, 1, 2 (Unclear), 4; missed = 3.
    recall = report["include_recall"]
    assert recall["point"] == 0.8 and recall["missed_includes"] == ["SCI-000003"]
    # If the failed calls (refused 1, truncated 2) counted as misses, 2 of 5 are kept.
    assert recall["if_failed_calls_counted_as_missed"] == 0.4
    assert recall["ci_low"] == round(pg.wilson_lower(4, 5), 4)

    # Agent Includes: 0, 4 (true) and 10 (false); Unclear on includes 1, 2.
    assert report["precision_on_includes"]["agent_include"] == round(2 / 3, 4)
    assert report["confusion"]["table"] == {
        "INCLUDE": {"INCLUDE": 2, "MAYBE": 2, "EXCLUDE": 1},
        "EXCLUDE": {"INCLUDE": 1, "MAYBE": 4, "EXCLUDE": 2},
    }
    assert report["confusion"]["driver_failed"] == {"INCLUDE": 2, "EXCLUDE": 1}
    assert report["exclusion_rate_on_human_excludes"] == round(2 / 7, 4)

    # Undecided, truncated, refused, malformed.
    answers = report["answers_not_usable"]
    assert answers["truncated"] == ["SCI-000002"] and answers["refusal"] == ["SCI-000001"] and answers["invalid"] == ["SCI-000005"]
    assert answers["driver_statuses"] == {"ok": 9, "refusal": 1, "truncated": 1, "invalid": 1}
    assert report["agent_left_undecided"]["study_ids"] == ["SCI-000006", "SCI-000007", "SCI-000008"]
    assert report["agent_left_undecided"]["by_reason"] == {"failed_check": 2, "cannot_decide": 1}
    assert "quote_in_source" in answers["failed_checks_on_ok_answers"]

    # Tokens and cost, per record and in total (haiku, direct calls).
    assert report["usage"]["totals"] == {"input_tokens": 12000, "output_tokens": 1200, "cache_read_tokens": 0, "cache_write_tokens": 0}
    assert report["usage"]["tokens_per_record_mean"] == 1100.0
    assert report["cost_usd"]["total"] == pytest.approx(12 * COST_PER_RECORD, abs=1e-4)
    assert report["cost_usd"]["per_1000_records"] == pytest.approx(1000 * COST_PER_RECORD, abs=0.01)
    assert all(r["cost_usd"] == pytest.approx(COST_PER_RECORD, abs=1e-6) for r in report["records_detail"])

    # The workspace is only read; the report went to the output folder.
    assert not list(ws.rglob("measure_*")) and Path(report["paths"]["json"]).is_file()
    assert "Confusion" in Path(report["paths"]["markdown"]).read_text(encoding="utf-8")


def test_a_researcher_unclear_is_an_include_and_other_labels_are_not_measured(tmp_path):
    assert ms.human_label("MAYBE") == "INCLUDE" and ms.human_label("unclear") == "INCLUDE"
    assert ms.human_label("EXCLUDE") == "EXCLUDE" and ms.human_label("PENDING") is None
    ws = _workspace(tmp_path)
    records, scope = ms.load_records(ws, "all")
    assert {r.study_id: r.label for r in records}["SCI-000004"] == "INCLUDE"
    assert scope["human_confirmation"] == "verified"


def test_batches_below_the_draft_thresholds_are_named(tmp_path):
    _, report = _measure(tmp_path, ScriptedDriver())
    by_batch = {b["batch"]: b for b in report["batches"]}
    # batch_001 holds includes 0-4 with one miss: 4 of 5. batch_002 holds none.
    assert by_batch["batch_001"]["include_recall"] == 0.8 and by_batch["batch_001"]["missed_includes"] == ["SCI-000003"]
    assert by_batch["batch_001"]["below_l1"] and by_batch["batch_001"]["below_l2"]
    assert by_batch["batch_002"]["include_recall"] is None and not by_batch["batch_002"]["below_l1"]
    assert report["batches_below_draft_thresholds"]["below_l1"] == ["batch_001"]


def test_draft_gates_count_includes_and_use_the_wilson_bound():
    assert ms._gate(ms.L1, 35, 35)["passes"] is True  # 35 of 35: bound 0.90 (ladder §4)
    assert ms._gate(ms.L1, 35, 34)["passes"] is False
    assert ms._gate(ms.L1, 10, 10)["passes"] is False and ms._gate(ms.L1, 10, 10)["enough_includes"] is False
    assert ms._gate(ms.L2, 75, 75)["passes"] is True and ms._gate(ms.L2, 75, 74)["passes"] is False


def test_a_stopped_run_does_not_score_the_records_it_never_reached(tmp_path):
    # Ceiling = 4 records' cost; the driver sends 4 at a time, so the run stops after the first chunk.
    driver = ScriptedDriver(chunk=4)
    _, report = _measure(tmp_path, driver, cost_ceiling_usd=4 * COST_PER_RECORD)
    assert report["stopped"] == "COST_CEILING_REACHED" and driver.calls == 1
    assert report["scored"] == 4 and report["not_reached"]["count"] == 8
    assert report["not_reached"]["study_ids"][0] == "SCI-000004"
    # Reached 0-3: includes 0 kept, 1 and 2 Unclear (kept), 3 missed. The 8 unreached are not Unclear-kept.
    assert report["include_recall"]["point"] == 0.75 and report["confusion"]["table"]["EXCLUDE"] == {"INCLUDE": 0, "MAYBE": 0, "EXCLUDE": 0}


def test_a_ceiling_needs_a_price(tmp_path):
    ws = _workspace(tmp_path)
    with pytest.raises(ValueError, match="no price"):
        ms.measure(ws, scope="all", provider="gemini", model="gemini-x", effort="low", max_tokens=1024,
                   driver=ScriptedDriver(), cost_ceiling_usd=1.0, out_dir=tmp_path / "out")


# --- what the agent sees ----------------------------------------------------------


def test_the_agent_is_sent_only_record_text_and_the_protocols_criteria(tmp_path):
    driver = ScriptedDriver()
    ws, _ = _measure(tmp_path, driver)
    assert len(driver.sent) == 12
    spec = driver.specs[0]
    for request in driver.sent:
        assert request.user_message.startswith("<record>") and "Drone maize study" in request.user_message
        for word in ("INCLUDE", "EXCLUDE", "MAYBE", "SCI-"):
            assert word not in request.user_message
    assert ms._STATISTIC.search(spec.system) is None
    ms.assert_blind(spec, driver.sent, ms.load_records(ws, "all")[0], PROTOCOL)


def test_a_prior_in_the_prompt_is_refused_before_anything_is_sent(tmp_path, monkeypatch):
    # Lesson 54: one sentence ("about 95 to 100% exclusion") flipped Unclear to Exclude.
    import dataclasses

    ws = _workspace(tmp_path)
    records, _ = ms.load_records(ws, "all")
    spec = pg.run_spec(PROTOCOL, model=MODEL, effort="low", max_tokens=1024)
    driver = ScriptedDriver()

    # 1. A sentence added to the system prompt after the fact is not the task's prompt.
    tainted = RunSpec(spec.system + "\nAbout 95 to 100% exclusion.", spec.schema, spec.model, spec.effort, spec.max_tokens)
    with pytest.raises(ValueError, match="not the task's prompt"):
        ms.execute(driver, records, tainted, provider="anthropic", protocol=PROTOCOL)

    # 2. A prior written into the task's own template is refused by name.
    real = pg.task_mod.load_task()
    prior = dataclasses.replace(real, template=real.template + "\nMost of these records are excluded (about 95 to 100% exclusion).")
    monkeypatch.setattr(pg.task_mod, "load_task", lambda version=None: prior)
    with pytest.raises(ValueError, match="outcome statistic"):
        ms.execute(driver, records, pg.run_spec(PROTOCOL, model=MODEL, effort="low", max_tokens=1024), provider="anthropic", protocol=PROTOCOL)
    monkeypatch.undo()
    assert driver.calls == 0  # nothing was sent

    # 3. A request that carries anything but the record's text (a label) is refused.
    leaky = [ScreeningRequest(r.study_id, pg.task_mod.record_message(r.title, r.abstract, r.published) + f"\nlabel: {r.label}") for r in records]
    with pytest.raises(ValueError, match="not exactly the record's text"):
        ms.assert_blind(spec, leaky, records, PROTOCOL)


def test_a_protocol_that_states_a_sampling_plan_is_not_an_outcome_statistic(tmp_path):
    # The real v03 criteria mention "~10% random sample" (a review method, not an outcome); the product sends it.
    protocol = json.loads(json.dumps(PROTOCOL))
    protocol["screening_criteria"]["inclusion"][0]["criterion"] = "UAV imagery (screened with a ~10% random sample check)"
    spec = pg.run_spec(protocol, model=MODEL, effort="low", max_tokens=1024)
    ms.assert_blind(spec, [], [], protocol)
    protocol["screening_criteria"]["inclusion"][0]["criterion"] = "UAV imagery; recall of includes was 98%"
    with pytest.raises(ValueError, match="outcome statistic"):
        ms.assert_blind(pg.run_spec(protocol, model=MODEL, effort="low", max_tokens=1024), [], [], protocol)


# --- the dry run and the command ----------------------------------------------------


def test_the_dry_run_counts_records_batches_tokens_and_cost_with_no_driver(tmp_path):
    ws = _workspace(tmp_path)
    before = _tree_hash(ws)
    plan = ms.measure(ws, scope="all", provider="anthropic", model="claude-opus-5-5", effort="low", max_tokens=4096, driver=None)
    assert plan["records"] == 12 and plan["labels"] == {"INCLUDE": 5, "EXCLUDE": 7} and plan["workspace_batches"] == 2
    assert plan["network_calls"] == 0 and plan["blind_check"] == "passed" and plan["priced"] is True
    assert plan["requests"] == {"mode": "direct calls", "calls": 12, "records_per_call": 1}  # 12 <= the direct limit
    c = plan["cost_usd"]
    assert 0 < c["expected"] < c["no_cache_expected_output"] < c["hard_ceiling"]
    assert plan["prompt"]["system_tokens"] > 100 and plan["tokens_expected"]["output_tokens"] == 600 * 12
    assert _tree_hash(ws) == before  # read only


def test_a_large_scope_is_sent_as_message_batches_of_the_products_chunk(tmp_path):
    ws = _workspace(tmp_path)
    records, scope = ms.load_records(ws, "all")
    many = (records * 5)[:30]  # > the direct limit of 20
    spec = pg.run_spec(PROTOCOL, model=MODEL, effort="low", max_tokens=1024)
    plan = ms.plan(many, spec, provider="anthropic", chunk=200, scope=scope, batch_of={}, max_tokens=1024, protocol=PROTOCOL)
    assert plan["requests"] == {"mode": "Message Batches", "calls": 1, "records_per_call": 200}
    assert ms.driver_options("anthropic") == {"direct_limit": pg.DIRECT_LIMIT, "max_per_batch": 200}  # as `agent_runs.start_run`
    assert ms.driver_options("gemini") == {}


def test_the_frozen_scope_refuses_another_workspace(tmp_path):
    ws = _workspace(tmp_path)
    frozen = pg.build_set(ws, excludes=3)
    records, scope = ms.load_records(ws, "frozen", frozen=frozen)
    # 4 includes + 3 excludes: the gate's frozen set holds only INCLUDE and EXCLUDE labels (a researcher Unclear is not in it)
    assert len(records) == 7 and scope["set_sha256"] == frozen["set_sha256"]
    other = tmp_path / "elsewhere" / "other"
    other.mkdir(parents=True)
    with pytest.raises(ValueError, match="use scope `all`"):
        ms.load_records(other, "frozen", frozen=frozen)


def _no_secrets(monkeypatch):
    """Any key read or driver build is a failure: a dry run must touch neither."""
    import scholar_agent.drivers as drivers
    import scholar_agent.keys as keys

    def boom(*_a, **_k):
        raise AssertionError("a dry run must not read a key or build a driver")

    monkeypatch.setattr(keys, "resolve_key", boom)
    monkeypatch.setattr(drivers, "make_driver", boom)


def test_cli_dry_run_prints_the_plan_and_never_reads_a_key(tmp_path, monkeypatch):
    _no_secrets(monkeypatch)
    ws = _workspace(tmp_path)
    result = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", str(ws), "--scope", "all", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "12 records" in result.output and "Network calls made: 0" in result.output and "estimated cost: expected $" in result.output


def test_cli_without_yes_is_not_run_and_never_reads_a_key(tmp_path, monkeypatch):
    _no_secrets(monkeypatch)
    ws = _workspace(tmp_path)
    result = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", str(ws), "--scope", "all"])
    assert result.exit_code == 1 and "Not run" in result.output


def test_cli_with_yes_runs_the_scripted_driver_and_writes_the_report(tmp_path, monkeypatch):
    import scholar_agent.drivers as drivers
    import scholar_agent.keys as keys

    monkeypatch.setattr(keys, "resolve_key", lambda provider: "fake-key-for-the-test")
    built = {}

    def fake_make_driver(provider, *, api_key, base_url=None, **options):
        built.update(provider=provider, options=options)
        return ScriptedDriver()

    monkeypatch.setattr(drivers, "make_driver", fake_make_driver)
    ws = _workspace(tmp_path)
    out = tmp_path / "report"
    result = CliRunner().invoke(
        app, ["prompt-gate", "measure", "--workspace", str(ws), "--scope", "all", "--model", MODEL, "--yes", "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert "include recall 0.8" in result.output and "report" in result.output
    assert built == {"provider": "anthropic", "options": {"direct_limit": pg.DIRECT_LIMIT, "max_per_batch": 200}}
    assert len(list(out.glob("measure_*.json"))) == 1 and len(list(out.glob("measure_*.md"))) == 1


def test_cli_where_no_call_succeeded_is_not_measured(tmp_path, monkeypatch):
    import scholar_agent.drivers as drivers
    import scholar_agent.keys as keys

    monkeypatch.setattr(keys, "resolve_key", lambda provider: "fake-key-for-the-test")
    dead = {sid: (lambda s: DriverResult(s, "error", detail="401 invalid x-api-key", usage=Usage(), model=MODEL)) for sid in HUMAN}
    monkeypatch.setattr(drivers, "make_driver", lambda *a, **k: ScriptedDriver(dead))
    result = CliRunner().invoke(
        app, ["prompt-gate", "measure", "--workspace", str(_workspace(tmp_path)), "--scope", "all", "--model", MODEL, "--yes", "--out", str(tmp_path / "r")]
    )
    assert result.exit_code == 1 and "Not measured" in result.output and "401" in result.output


# --- review round 1 ----------------------------------------------------------------


def _many_includes(n: int = 80):
    records = [pg.EvalRecord(f"SCI-{i:06d}", "INCLUDE", f"UAV weeds {i}", f"Drone maize study {i}.", "2024") for i in range(n)]
    spec = pg.run_spec(PROTOCOL, model=MODEL, effort="low", max_tokens=1024)
    return records, spec


def test_a_run_where_every_call_failed_passes_no_gate():
    # A failed call is Unclear, so it is "kept": without this guard 80 of 80 includes kept gave recall 1.0 and a pass.
    records, spec = _many_includes()
    dead = [DriverResult(r.study_id, "error", detail="401", usage=Usage(), model=MODEL) for r in records]
    report = ms.analyse(scope={"scope": "all", "set_sha256": "x", "human_confirmation": "absent"}, records=records, results=dead,
                        protocol=PROTOCOL, provider="anthropic", spec=spec, batch_of={})
    assert report["measured"] is False and report["include_recall"]["point"] == 1.0
    assert all(g["passes"] is False and g["passes_if_failed_calls_were_misses"] is False for g in report["gates"])
    assert any("nothing was measured" in w for w in report["warnings"])


def test_a_gate_names_which_figure_passes_when_some_calls_failed():
    # 80 includes, 60 answered Include, 20 calls failed: lenient 80/80, strict 60/80.
    assert ms._gate(ms.L2, 80, 80, strict_kept=60)["passes"] is True
    assert ms._gate(ms.L2, 80, 80, strict_kept=60)["passes_if_failed_calls_were_misses"] is False
    assert ms._gate(ms.L2, 80, 80, measured=False)["passes"] is False


def test_results_a_driver_dropped_without_a_stop_are_flagged(tmp_path):
    class Dropping(ScriptedDriver):
        def run(self, requests, spec, **kw):
            return super().run(requests, spec, **kw)[:8]

    _, report = _measure(tmp_path, Dropping())
    assert report["not_reached"]["count"] == 4 and report["stopped"] is None
    assert any("driver dropped them" in w for w in report["warnings"])


def test_a_smoke_run_says_so_in_the_report(tmp_path):
    _, report = _measure(tmp_path, ScriptedDriver(), limit=6)
    assert report["scope"]["limit"] == 6 and any("SMOKE RUN" in w for w in report["warnings"])
    assert "WARNING: SMOKE RUN" in Path(report["paths"]["markdown"]).read_text(encoding="utf-8")


def test_cli_refuses_a_ceiling_below_the_estimate_and_an_unpriced_model_before_reading_a_key(tmp_path, monkeypatch):
    import scholar_agent.drivers as drivers
    import scholar_agent.keys as keys

    def boom(*_a, **_k):
        raise AssertionError("refused before a key is read or a driver built")

    monkeypatch.setattr(keys, "resolve_key", boom)
    monkeypatch.setattr(drivers, "make_driver", boom)
    ws = str(_workspace(tmp_path))
    low = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", ws, "--scope", "all", "--model", "claude-opus-5-5", "--yes", "--cost-ceiling", "0.000001"])
    assert low.exit_code == 1 and "below the expected cost" in low.output
    unpriced = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", ws, "--scope", "all", "--provider", "gemini", "--model", "gemini-x", "--yes"])
    assert unpriced.exit_code == 1 and "no price" in unpriced.output
