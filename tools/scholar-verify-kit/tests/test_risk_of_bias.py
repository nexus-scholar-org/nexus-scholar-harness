"""Tests for the deterministic QUADAS-2/PROBAST risk-of-bias scorer."""

from __future__ import annotations

from scholar_verify import risk_of_bias as rob


def _record(wid, *, uav=True, named="FieldD", images=500, note="", has_metric=True,
            conf=0.9, agmt="both_equal", amb=False, annotated=False,
            edge_device="Jetson", runtime=True, eff=True, fps=True, lat=True):
    ds = {"uav_collected": uav}
    if named:
        ds["name"] = named
    if images is not None:
        ds["images"] = images
    if note:
        ds["note"] = note
    if annotated:
        ds["note"] = (ds.get("note", "") + " dataset with public annotations").strip()
    rec = {"workspace_id": wid, "segmentation": {"dataset": ds, "metrics": {}}}
    if has_metric:
        rec["segmentation"]["metrics"]["mIoU"] = {
            "reported": True, "confidence": conf, "agreement": agmt, "ambiguity": amb,
        }
    if edge_device or runtime or eff or fps or lat:
        edge = {
            "reported": True,
            "device": edge_device,
            "runtime_reported": runtime,
            "efficiency_reported": eff,
            "fps": {"reported": fps},
            "latency_ms": {"reported": lat},
        }
        if not edge_device:
            edge["device"] = ""
        rec["edge"] = edge
    return rec


MANIFEST = [
    {"workspace_id": "W1", "title": "T1", "year": 2023},
    {"workspace_id": "W2", "title": "T2", "year": 2022},
]


def test_rate_d1_high_without_uav():
    rating, _ = rob.rate_d1(_record("W1", uav=False))
    assert rating == "H"


def test_rate_d1_low_with_named_split():
    rating, _ = rob.rate_d1(_record("W1", named="AgBench", note="with train/test split"))
    assert rating == "L"


def test_rate_d2_high_without_metric():
    rating, _ = rob.rate_d2(_record("W1", has_metric=False))
    assert rating == "H"


def test_rate_d2_high_confidence_both_equal():
    rating, _ = rob.rate_d2(_record("W1", conf=0.95, agmt="both_equal"))
    assert rating == "L"
    rating2, _ = rob.rate_d2(_record("W1", conf=0.7, agmt="both_equal"))
    assert rating2 == "?"


def test_rate_d3_benchmark():
    rating, _ = rob.rate_d3(_record("W1", annotated=True))
    assert rating == "L"


def test_rate_d4_na_when_no_edge():
    rec = _record("W1", edge_device="", runtime=False, eff=False, fps=False, lat=False)
    rating, _ = rob.rate_d4(rec)
    assert rating == "n/a"


def test_rate_d4_full_report():
    rating, _ = rob.rate_d4(_record("W1", edge_device="Jetson", runtime=True, eff=True, fps=True, lat=True))
    assert rating == "L"


def test_run_overall_worst_domain():
    records = [
        _record("W1", named="", uav=False, has_metric=False),   # D1 H, D2 H -> overall H
        _record("W2", annotated=True),                          # all L -> overall L (+ D4 L)
    ]
    out = rob.run(records, MANIFEST)
    summary = out["summary"]
    assert summary["overall_risk"]["H"] == 1
    assert summary["overall_risk"]["L"] == 1
    assert summary["studies_high_risk"] == ["W1"]
    assert summary["studies_edge_rq2"] == 2
    assert out["results"][1]["domains"]["d4"]["rating"] == "L"


def test_run_raises_on_missing_records():
    try:
        rob.run([_record("W1")], MANIFEST)
    except SystemExit as exc:
        assert "W2" in str(exc)


def test_render_report_contains_tables():
    out = rob.run([_record("W1"), _record("W2", annotated=True)], MANIFEST)
    md = rob.render_report(out)
    assert "# Risk-of-Bias Assessment" in md
    assert "## Per-study ratings" in md
    assert "| W1 |" in md
