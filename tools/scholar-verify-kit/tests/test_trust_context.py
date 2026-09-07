"""Hermetic tests for trust-weighted consensus (no DB, no network)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from scholar_verify import trust_context as tc
from scholar_verify.cli import app

runner = CliRunner()


def _consensus() -> dict:
    return {
        "rq_id": "RQ1",
        "input_claims": 3,
        "total_groups": 2,
        "threshold": 0.4,
        "high_consensus": [
            {
                "cluster_id": "C1",
                "theme": "RAG improves retrieval accuracy",
                "supporting_studies": ["S1", "S2"],
                "claims": [],
            }
        ],
        "active_debates": [],
        "unresolved": [],
        "provisional": [
            {
                "cluster_id": "C2",
                "theme": "Edge latency is acceptable",
                "supporting_studies": ["S3"],
                "claims": [],
            }
        ],
        "rendered_markdown": "",
    }


def _phase4() -> dict:
    return {
        "risk_of_bias": [
            {
                "workspace_id": "S1",
                "overall_risk": "L",
                "domains": {"d1": {"rating": "L"}, "d2": {"rating": "L"}},
            },
            {"workspace_id": "S2", "overall_risk": "L", "domains": {}},
        ],
        "coi": [
            {
                "workspace_id": "S1",
                "coi_label": "declared-no-conflict",
                "industry_entities": [],
            },
            {
                "workspace_id": "S2",
                "coi_label": "declared-no-conflict",
                "industry_entities": [],
            },
        ],
        "retraction": [
            {"workspace_id": "S1", "flagged": False, "flag_reasons": []},
            {"workspace_id": "S2", "flagged": False, "flag_reasons": []},
        ],
        "open_science": [
            {"workspace_id": "S1", "das": "public+link", "cas": "not-stated", "repo_links": ["https://gh/a"]},
            {"workspace_id": "S2", "das": "not-stated", "cas": "not-stated", "repo_links": []},
        ],
    }


class TestIndex:
    def test_build_index_flattens_streams(self):
        index = tc.build_trust_index(_phase4())
        assert index["S1"]["overall_risk"] == "L"
        assert index["S1"]["das"] == "public+link"
        assert index["S1"]["coi_label"] == "declared-no-conflict"
        assert index["S2"]["flagged"] is False
        assert index["S2"]["industry_entities"] == []

    def test_missing_studies_absent(self):
        index = tc.build_trust_index(_phase4())
        assert "S9" not in index

    def test_rows_accepts_file_dict_and_bare_list(self):
        assert tc._rows({"results": _phase4()["coi"]}) == _phase4()["coi"]
        assert tc._rows(_phase4()["coi"]) == _phase4()["coi"]
        assert tc._rows(None) == []


class TestLevels:
    def test_blocked_on_flagged_study(self):
        studies = [{"workspace_id": "S1", "flagged": True, "flag_reasons": ["crossref:retraction"]}]
        assert tc.trust_level(studies, 1.0) == "BLOCKED"

    def test_unverified_when_empty(self):
        assert tc.trust_level([], 0.0) == "UNVERIFIED"
        assert tc.trust_level([{"workspace_id": "S1"}], 0.0) == "UNVERIFIED"

    def test_weak_on_low_coverage(self):
        studies = [{"workspace_id": "S1", "overall_risk": "L", "coi_label": "declared-no-conflict", "industry_entities": []}]
        assert tc.trust_level(studies, 0.3) == "WEAK"

    def test_weak_on_high_risk_study(self):
        studies = [{"workspace_id": "S1", "overall_risk": "H", "industry_entities": []}]
        assert tc.trust_level(studies, 1.0) == "WEAK"

    def test_weak_on_industry_money(self):
        studies = [{"workspace_id": "S1", "overall_risk": "L", "industry_entities": [{"kind": "funding"}]}]
        assert tc.trust_level(studies, 1.0) == "WEAK"

    def test_strong_requires_public_link_and_definitive_risk(self):
        studies = [{"workspace_id": "S1", "overall_risk": "L", "industry_entities": [], "das": "public+link", "cas": "not-stated"}]
        assert tc.trust_level(studies, 1.0) == "STRONG"

    def test_adequate_otherwise(self):
        studies = [{"workspace_id": "S1", "overall_risk": "?", "industry_entities": []}]
        assert tc.trust_level(studies, 1.0) == "ADEQUATE"


class TestAnnotate:
    def test_cluster_annotations(self):
        out = tc.annotate(_consensus(), _phase4())
        assert out["total_groups"] == 2
        c1 = out["buckets"]["high_consensus"][0]
        t = c1["trust"]
        assert t["trust_level"] == "STRONG"
        assert t["studies_audited"] == 2
        assert t["studies_total"] == 2
        assert t["aggregates"]["overall_risk"] == {"H": 0, "L": 2, "?": 0}
        assert t["aggregates"]["open_science_public_link"] == 1

        c2 = out["buckets"]["provisional"][0]
        assert c2["trust"]["trust_level"] == "UNVERIFIED"
        assert "unverified" in c2["trust"]["flags"]

    def test_level_counts(self):
        out = tc.annotate(_consensus(), _phase4())
        assert out["trust_level_counts"]["STRONG"] == 1
        assert out["trust_level_counts"]["UNVERIFIED"] == 1

    def test_industry_money_demotes_to_weak(self):
        phase4 = _phase4()
        phase4["coi"][1]["coi_label"] = "industry-money"
        phase4["coi"][1]["industry_entities"] = [{"entity": "ACME", "kind": "funding"}]
        out = tc.annotate(_consensus(), phase4)
        assert out["trust_level_counts"]["WEAK"] == 1
        assert "industry-money" in out["buckets"]["high_consensus"][0]["trust"]["flags"]

    def test_render_report_contains_study_table(self):
        out = tc.annotate(_consensus(), _phase4())
        md = tc.render_report(out)
        assert "Trust-Weighted Consensus Report" in md
        assert "| S1 | L |" in md
        assert "STRONG" in md


class TestCli:
    def _make_ws(self, tmp_path):
        ws = tmp_path / "ws"
        (ws / "phase4").mkdir(parents=True)
        (ws / "synthesis").mkdir()
        (ws / "protocol.json").write_text("{}", encoding="utf-8")

        def dump(name, data):
            (ws / "phase4" / name).write_text(json.dumps(data), encoding="utf-8")

        dump("risk_of_bias.json", _phase4()["risk_of_bias"])
        dump("coi_audit.json", _phase4()["coi"])
        dump("retraction_status_check.json", _phase4()["retraction"])
        dump("open_science_regex_baseline.json", _phase4()["open_science"])
        (ws / "synthesis" / "consensus.json").write_text(json.dumps(_consensus()), encoding="utf-8")
        return ws

    def test_cli_trust_context(self, tmp_path):
        ws = self._make_ws(tmp_path)
        res = runner.invoke(app, ["trust-context", "--workspace", str(ws)])
        assert res.exit_code == 0, res.output
        out = json.loads((ws / "phase4" / "trust_consensus.json").read_text(encoding="utf-8"))
        assert out["trust_level_counts"]["STRONG"] == 1
        assert "Trust-Weighted Consensus Report" in (ws / "phase4" / "trust_consensus.md").read_text(encoding="utf-8")
