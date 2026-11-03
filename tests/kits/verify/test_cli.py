"""CLI smoke tests using typer's CliRunner (no network)."""

from __future__ import annotations

import json

from typer.testing import CliRunner as TyperCliRunner

from scholar_verify.cli import app

runner = TyperCliRunner()


def _make_workspace(tmp_path):
    ws = tmp_path / "ws"
    (ws / "literature" / "extraction" / "merged").mkdir(parents=True)
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "extracted").mkdir()
    (ws / "phase4" / "_agent_results").mkdir(parents=True)
    (ws / "protocol.json").write_text("{}", encoding="utf-8")
    (ws / "INDEX.md").write_text("# WS", encoding="utf-8")
    return ws


def test_open_science_cli(tmp_path):
    ws = _make_workspace(tmp_path)
    (ws / "extracted" / "W1.md").write_text(
        "Data available at https://zenodo.org/record/1; source code on GitHub.",
        encoding="utf-8",
    )
    records = [
        {
            "workspace_id": "W1",
            "study": {"title": "T1", "year": 2023, "extracted_md": "W1.md"},
        }
    ]
    (ws / "literature" / "extraction" / "merged" / "records.json").write_text(
        json.dumps(records), encoding="utf-8"
    )
    res = runner.invoke(app, ["open-science", "--workspace", str(ws)])
    assert res.exit_code == 0, res.output
    out = json.loads((ws / "phase4" / "open_science_regex_baseline.json").read_text(encoding="utf-8"))
    assert out["summary"]["das"]["public+link"] == 1
    assert (ws / "phase4" / "open_science_regex_baseline.md").exists()


def test_risk_of_bias_cli(tmp_path):
    ws = _make_workspace(tmp_path)
    record = {
        "workspace_id": "W1",
        "segmentation": {
            "dataset": {"uav_collected": True, "name": "FieldD", "images": 500,
                    "note": "public benchmark with annotated ground truth"},
            "metrics": {"mIoU": {"reported": True, "confidence": 0.9, "agreement": "both_equal"}},
        },
        "edge": {"reported": True, "device": "Jetson", "runtime_reported": True, "efficiency_reported": True,
                 "fps": {"reported": True}, "latency_ms": {"reported": True}},
    }
    (ws / "literature" / "extraction" / "merged" / "records.json").write_text(
        json.dumps([record]), encoding="utf-8"
    )
    (ws / "phase4" / "_manifest.json").write_text(
        json.dumps([{"workspace_id": "W1", "title": "T1", "year": 2023}]), encoding="utf-8"
    )
    res = runner.invoke(app, ["risk-of-bias", "--workspace", str(ws)])
    assert res.exit_code == 0, res.output
    out = json.loads((ws / "phase4" / "risk_of_bias.json").read_text(encoding="utf-8"))
    assert out["summary"]["overall_risk"] == {"L": 1}


def test_coi_cli(tmp_path):
    ws = _make_workspace(tmp_path)
    (ws / "phase4" / "_manifest.json").write_text(
        json.dumps([{"workspace_id": "W1", "title": "T1", "year": 2023}]), encoding="utf-8"
    )
    chunks = [
        {
            "workspace_id": "W1",
            "coi_label": "no-statement",
            "funding_statement": "NSF grant",
            "industry_entities": [],
        }
    ]
    for i in range(1, 9):
        (ws / "phase4" / "_agent_results" / f"coi_chunk_{i}.json").write_text(
            json.dumps(chunks if i == 1 else []), encoding="utf-8"
        )
    res = runner.invoke(app, ["coi", "--workspace", str(ws)])
    assert res.exit_code == 0, res.output
    out = json.loads((ws / "phase4" / "coi_audit.json").read_text(encoding="utf-8"))
    assert out["summary"]["labels"]["academic-or-public"] == 1


def test_retraction_cli_dry_run(tmp_path, monkeypatch):
    ws = _make_workspace(tmp_path)
    (ws / "literature" / "extraction" / "merged" / "records.json").write_text(
        json.dumps([{"workspace_id": "W1", "study": {"title": "T", "year": 2023}}]), encoding="utf-8"
    )
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "W1", "external_ids": {"doi": "10.1/x"}}]), encoding="utf-8"
    )
    calls = []

    class FakeChecker:
        def __init__(self, sleep_s=0.2, http=None):
            calls.append(sleep_s)

        def check(self, records, included):
            return {
                "run_metadata": {"run_date_utc": "2024-06-01T00:00:00S"},
                "summary": {
                    "studies_checked": 1,
                    "flagged_any": 0,
                    "retracted_openalex": 0,
                    "crossref_update_events": {},
                    "openalex_provenance_status": {"available": 1},
                    "unresolved_lookups": [],
                },
                "results": [
                    {
                        "workspace_id": "W1",
                        "title": "T",
                        "year": 2023,
                        "doi": "10.1/x",
                        "flagged": False,
                        "openalex": {"is_retracted": False, "last_status_in_oa": "available"},
                        "crossref": {"update_to": []},
                    }
                ],
            }

    monkeypatch.setattr("scholar_verify.cli.retraction.RetractionChecker", FakeChecker)
    res = runner.invoke(app, ["retraction", "--workspace", str(ws), "--yes", "--dry-run"])
    assert res.exit_code == 0, res.output
    assert "studies_checked" in res.output
    # dry-run: no files written
    assert not (ws / "phase4" / "retraction_status_check.json").exists()


def test_core_streams_run_without_network_are_importable():
    from scholar_verify import http_client
    assert http_client.VerifyHttpClient is not None


def test_cli_help_lists_commands():
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    for cmd in ("retraction", "open-science", "coi", "risk-of-bias", "all"):
        assert cmd in res.output
