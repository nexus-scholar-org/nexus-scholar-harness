"""The screening prompt gate (M1b-2): the frozen set, the score, the cost, the CLI guard."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_agent import prompt_gate as pg
from scholar_agent.drivers import DriverResult, Usage
from scholar_harness.cli import app

PROTOCOL = {
    "screening_criteria": {
        "inclusion": [{"id": "INC-01", "criterion": "UAV imagery"}],
        "exclusion": [{"id": "EXC-01", "criterion": "not agricultural"}],
    }
}


def _workspace(tmp_path: Path, n_inc: int = 3, n_exc: int = 5) -> Path:
    ws = tmp_path / "v03"
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True)
    papers, decisions = [], []
    for i in range(n_inc + n_exc):
        sid = f"SCI-{i:06d}"
        papers.append({"workspace_id": sid, "title": f"UAV weeds {i}", "abstract": f"Drone maize study {i}.", "year": "2024"})
        decisions.append({"workspace_id": sid, "decision": "INCLUDE" if i < n_inc else "EXCLUDE"})
    (screening / "batch_001.json").write_text(json.dumps({"papers": papers}), encoding="utf-8")
    body = json.dumps({"decisions": decisions})
    (screening / "batch_001_decisions.json").write_text(body, encoding="utf-8")
    artifact = {"path": "literature/screening/batch_001_decisions.json", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (screening / "HUMAN_CONFIRMATION.json").write_text(
        json.dumps({"artifacts": [artifact], "reviewer": {"name": "R"}, "summary": {"confirmed": n_inc + n_exc}}), encoding="utf-8"
    )
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL), encoding="utf-8")
    return ws


def test_wilson_lower_bound_matches_known_values():
    assert pg.wilson_lower(0, 0) == 0.0
    assert round(pg.wilson_lower(95, 100), 3) == 0.888
    assert round(pg.wilson_lower(644, 644), 3) == 0.994


def test_unclear_counts_as_kept_and_usefulness_is_reported_not_gated():
    labels = {"a": "INCLUDE", "b": "INCLUDE", "c": "EXCLUDE", "d": "EXCLUDE"}
    all_unclear = pg.score({s: "MAYBE" for s in labels}, labels)
    assert all_unclear["include_recall"] == 1.0 and all_unclear["exclusion_rate_on_confirmed_excludes"] == 0.0
    assert all_unclear["unclear_rate"] == 1.0  # passes recall, saves no work: visible in the report
    missed = pg.score({"a": "EXCLUDE", "b": "INCLUDE", "c": "EXCLUDE", "d": "MAYBE"}, labels)
    assert missed["include_recall"] == 0.5 and missed["missed_includes"] == ["a"] and missed["passes"] is False


def test_the_set_is_seeded_hashed_and_refuses_a_changed_confirmation(tmp_path):
    ws = _workspace(tmp_path)
    first, again = pg.build_set(ws, excludes=2), pg.build_set(ws, excludes=2)
    assert first == again and first["counts"] == {"INCLUDE": 3, "EXCLUDE": 2}
    assert "title" not in json.dumps(first["records"])  # ids, labels and hashes only
    records = pg.load_set(ws, first)
    assert all(r.published == "2024" for r in records)

    # CRLF on checkout is not a change (the confirmation hashes LF bytes).
    path = ws / "literature" / "screening" / "batch_001_decisions.json"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") or path.read_bytes())
    pg.verify_confirmation(ws)
    path.write_text(path.read_text(encoding="utf-8").replace("INCLUDE", "EXCLUDE", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="signed confirmation"):
        pg.build_set(ws)


def test_a_record_whose_text_changed_is_refused(tmp_path):
    ws = _workspace(tmp_path)
    frozen = pg.build_set(ws, excludes=2)
    batch = ws / "literature" / "screening" / "batch_001.json"
    batch.write_text(batch.read_text(encoding="utf-8").replace("Drone maize study 0.", "Changed."), encoding="utf-8")
    with pytest.raises(ValueError, match="changed since the set was frozen"):
        pg.load_set(ws, frozen)


def test_report_derives_outcomes_with_the_engine_and_non_ok_is_unclear(tmp_path):
    ws = _workspace(tmp_path)
    frozen = pg.build_set(ws, excludes=5)
    records = pg.load_set(ws, frozen)
    spec = pg.run_spec(PROTOCOL, model="claude-haiku-5-5", effort="low", max_tokens=1024)
    usage = Usage(input_tokens=1000, output_tokens=200, cache_read_tokens=800)

    def answer(record, inc, exc):
        text = pg.task_mod.record_text(record.title, record.abstract, record.published)
        return {"criteria": [
            {"id": "INC-01", "answer": inc, "quote": record.title if inc != "not_reported" else ""},
            {"id": "EXC-01", "answer": exc, "quote": "Published: 2024" if exc != "not_reported" else ""},
        ], "cannot_decide": False, "reasoning": text[:10]}

    results = []
    for r in records:
        if r.study_id == "SCI-000000":
            results.append(DriverResult(r.study_id, "refusal", detail="bio", usage=usage))
        elif r.label == "INCLUDE":
            results.append(DriverResult(r.study_id, "ok", output=answer(r, "yes", "no"), usage=usage))
        else:
            results.append(DriverResult(r.study_id, "ok", output=answer(r, "no", "no"), usage=usage))
    out = pg.report(frozen=frozen, records=records, results=results[:-1], protocol=PROTOCOL, provider="anthropic", spec=spec, batch=True)
    by_id = {r["study_id"]: r for r in out["records"]}
    assert by_id["SCI-000000"]["outcome"] == "MAYBE" and by_id["SCI-000000"]["driver_status"] == "refusal"
    assert by_id["SCI-000001"]["outcome"] == "INCLUDE"
    assert by_id["SCI-000003"]["outcome"] == "EXCLUDE" and by_id["SCI-000003"]["reason_code"] == "FAILS-INC-01"
    assert by_id[records[-1].study_id]["driver_status"] == "missing" and by_id[records[-1].study_id]["outcome"] == "MAYBE"
    assert out["score"]["include_recall"] == 1.0 and out["cost_usd"] is not None and out["prompt_sha256"].startswith("sha256:")


def test_cost_counts_cache_reads_once_and_halves_for_batches():
    price = {"input": 4.0, "output": 20.0, "cache_read": 0.2, "cache_write": 5.0}
    usage = {"input_tokens": 1_000_000, "output_tokens": 100_000, "cache_read_tokens": 500_000, "cache_write_tokens": 0}
    # 500k uncached at $4 + 500k cached at $0.2 + 100k out at $20 = 2 + 0.1 + 2 = 4.1; batch halves it.
    assert pg.cost_usd(usage, price, batch=False) == 4.1
    assert pg.cost_usd(usage, price, batch=True) == 2.05


def test_cli_run_spends_nothing_without_yes_and_without_a_key(tmp_path, monkeypatch):
    ws = _workspace(tmp_path)
    frozen = pg.build_set(ws, excludes=2)
    set_file = tmp_path / "set.json"
    set_file.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(pg, "SET_FILE", set_file)
    monkeypatch.setattr("scholar_agent.keys.resolve_key", lambda provider: None)
    called = []
    monkeypatch.setattr("scholar_agent.drivers.make_driver", lambda *a, **k: called.append(a) or None)
    runner = CliRunner()
    no_yes = runner.invoke(app, ["prompt-gate", "run", "--workspace", str(ws)])
    assert no_yes.exit_code == 1 and "Not run" in no_yes.output
    no_key = runner.invoke(app, ["prompt-gate", "run", "--workspace", str(ws), "--yes"])
    assert no_key.exit_code == 1 and "keys set anthropic" in no_key.output
    assert called == []
    estimate = runner.invoke(app, ["prompt-gate", "estimate", "--workspace", str(ws)])
    assert estimate.exit_code == 0 and "an estimate, not a measurement" in estimate.output


def test_cli_run_where_every_call_failed_is_not_measured_and_keeps_the_error(tmp_path, monkeypatch):
    # The first live smoke: a placeholder key made every call a 401, and the
    # gate printed FAIL with no reason, as if the prompt had been measured.
    ws = _workspace(tmp_path)
    frozen = pg.build_set(ws, excludes=2)
    set_file = tmp_path / "set.json"
    set_file.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(pg, "SET_FILE", set_file)
    monkeypatch.setattr(pg, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr("scholar_agent.keys.resolve_key", lambda provider: "k")
    detail = "AuthenticationError: Error code: 401 - Invalid bearer token"

    class Failing:
        def run(self, requests, spec):
            return [DriverResult(r.custom_id, "error", detail=detail) for r in requests]

    monkeypatch.setattr("scholar_agent.drivers.make_driver", lambda *a, **k: Failing())
    result = CliRunner().invoke(app, ["prompt-gate", "run", "--workspace", str(ws), "--yes"])
    assert result.exit_code == 1
    assert "Not measured" in result.output and "401" in result.output and "PASS" not in result.output and "FAIL" not in result.output
    out = json.loads(next((tmp_path / "results").glob("*.json")).read_text(encoding="utf-8"))
    assert out["measured"] is False
    assert {r["driver_detail"] for r in out["records"]} == {detail}


# --- the MCP route: export, agents answer, import ------------------------------


def _export(tmp_path, monkeypatch, limit=0):
    ws = _workspace(tmp_path, n_inc=4, n_exc=6)
    frozen = pg.build_set(ws, excludes=6)
    set_file = tmp_path / "set.json"
    set_file.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(pg, "SET_FILE", set_file)
    monkeypatch.setattr(pg, "RESULTS_DIR", tmp_path / "results")
    out = tmp_path / "export"
    args = ["prompt-gate", "export", "--out", str(out), "--workspace", str(ws)] + (["--limit", str(limit)] if limit else [])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    return ws, frozen, out


def test_the_export_carries_no_label_and_no_label_order(tmp_path, monkeypatch):
    ws, frozen, out = _export(tmp_path, monkeypatch, limit=6)
    text = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*") if p.is_file())
    for word in ("INCLUDE", "EXCLUDE", '"label"', "decision", "HUMAN_CONFIRMATION"):
        assert word not in text, word
    labels = {r["study_id"]: r["label"] for r in frozen["records"]}
    order = [item["study_id"] for name in json.loads((out / "manifest.json").read_text())["batches"]
             for item in json.loads((out / name).read_text(encoding="utf-8"))["records"]]
    assert len(order) == 6
    # The smoke selection is includes first; the export must not keep that order.
    assert [labels[s] for s in order] != sorted((labels[s] for s in order), key=lambda l: l != "INCLUDE")
    assert all("<record>" in item["message"] for name in json.loads((out / "manifest.json").read_text())["batches"]
               for item in json.loads((out / name).read_text(encoding="utf-8"))["records"])


def test_imported_answers_are_scored_like_a_run_and_a_bad_or_missing_answer_is_unclear(tmp_path, monkeypatch):
    ws, frozen, out = _export(tmp_path, monkeypatch)
    manifest = json.loads((out / "manifest.json").read_text())
    records = {r.study_id: r for r in pg.load_set(ws, frozen)}
    labels = {r["study_id"]: r["label"] for r in frozen["records"]}
    ids = manifest["study_ids"]
    for sid in ids[:-2]:
        inc = "yes" if labels[sid] == "INCLUDE" else "no"
        answer = {"criteria": [{"id": "INC-01", "answer": inc, "quote": records[sid].title},
                               {"id": "EXC-01", "answer": "no", "quote": "Published: 2024"}],
                  "cannot_decide": False, "reasoning": "r"}
        (out / "answers" / f"{sid}.json").write_text(json.dumps(answer), encoding="utf-8")
    (out / "answers" / f"{ids[-2]}.json").write_text("not json", encoding="utf-8")  # invalid; ids[-1] missing
    result = CliRunner().invoke(app, ["prompt-gate", "import", "--export", str(out), "--model", "claude-opus-5-5", "--workspace", str(ws)])
    assert result.exit_code == 0, result.output
    report = json.loads(next((tmp_path / "results").glob("*.json")).read_text(encoding="utf-8"))
    assert report["provider"] == "claude-code-mcp" and report["cost_usd"] is None and report["measured"] is True
    by_id = {r["study_id"]: r for r in report["records"]}
    assert by_id[ids[-2]]["driver_status"] == "invalid" and by_id[ids[-2]]["outcome"] == "MAYBE"
    assert by_id[ids[-1]]["driver_status"] == "missing" and by_id[ids[-1]]["outcome"] == "MAYBE"
    assert report["score"]["include_recall"] == 1.0


def test_an_export_from_another_prompt_is_refused(tmp_path, monkeypatch):
    ws, _frozen, out = _export(tmp_path, monkeypatch)
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["prompt_sha256"] = "sha256:other"
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = CliRunner().invoke(app, ["prompt-gate", "import", "--export", str(out), "--model", "m", "--workspace", str(ws)])
    assert result.exit_code == 1 and "another set or prompt" in result.output
