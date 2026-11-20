"""M3f-combined-corpus at the engine and CLI level: one snapshot from a harvest plus staged exports.

The harvest is written by hand here (a published run with a finished stage
marker), so these tests need no search engine; ``tests/console/test_combined_corpus_api.py``
runs the real engine with doubles.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_harness.cli import app

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "c" * 32
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
runner = CliRunner()

SCOPUS = (
    "TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV multispectral weed mapping in maize\nPY  - 2024\nDO  - 10.1000/uav-1\n"
    "AB  - Scopus one.\nER  - \n"
    "TY  - JOUR\nAU  - Chen, L.\nTI  - Drone crop scouting with deep learning\nPY  - 2022\nDO  - 10.1000/m3f-2\nER  - \n"
)
WOS = "TY  - JOUR\nAU  - Okafor, N.\nTI  - Site-specific herbicide prescription maps\nPY  - 2023\nDO  - 10.1000/m3f-4\nER  - \n"

HARVEST = [
    {"workspace_id": "SCI-100000000000001", "title": "UAV multispectral weed mapping in maize", "year": 2024,
     "provider": "openalex", "provider_id": "W1", "external_ids": {"doi": "10.1000/uav-1"}, "abstract": None,
     "sources": [{"provider": "openalex", "id": "W1"}]},
    {"workspace_id": "SCI-100000000000003", "title": "Deep learning weed detection from drone imagery", "year": 2023,
     "provider": "arxiv", "provider_id": "2301.00001", "external_ids": {"arxiv_id": "2301.00001"},
     "abstract": "Abstract three.", "sources": [{"provider": "arxiv", "id": "2301.00001"}]},
]


def _workspace(tmp_path: Path, name: str = "ws") -> Path:
    ws = tmp_path / name
    (ws / "literature").mkdir(parents=True)
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(json.dumps({"project_id": "m3f", "registered_workspace_id": WS_ID}), encoding="utf-8")
    (ws / "protocol.json").write_text(PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")
    return ws


def _ready_harvest(ws: Path, run: str = "run_001", *, ended: str = "DONE") -> Path:
    """A published search run whose preparation ended, as the pipeline leaves it (M3i marker)."""
    run_dir = ws / "literature" / "search_runs" / run
    run_dir.mkdir(parents=True)
    legs = [
        {"provider": "openalex", "fetched": 2, "reported_total": 2, "status": "ok", "cap_hit": False,
         "executed_query": "q", "started_at": "2026-11-20T09:00:00Z"},
        {"provider": "arxiv", "fetched": 1, "reported_total": 1, "status": "ok", "cap_hit": False,
         "executed_query": "q", "started_at": "2026-11-20T09:00:00Z"},
    ]
    (run_dir / "legs.json").write_text(json.dumps({
        "run": run, "status": "SUCCESS", "corpus_published": True, "legs": legs,
        **_search_of(ws),
    }), encoding="utf-8")
    (run_dir / "pipeline.json").write_text(json.dumps({
        "schema": "nexus.harvest-pipeline.v1", "run": run, "stages": {},
        "ended": {"status": ended, "at": "2026-11-20T09:05:00Z", "stage": "verification", "message": None},
        "verified_run": run if ended in {"DONE", "INCOMPLETE"} else None, "resumed": [],
    }), encoding="utf-8")
    (ws / "literature" / "verified.json").write_text(json.dumps(HARVEST), encoding="utf-8")
    return run_dir


def _search_of(ws: Path) -> dict:
    """What a run records of the protocol's search, so the accept's drift check passes."""
    from scholar_harness.pipeline.discovery import protocol_search_record

    fingerprint, search = protocol_search_record(ws / "protocol.json")
    return {"protocol_fingerprint": fingerprint, "protocol_search": search, "query_text": search["query_text"],
            "year_min": search["year_min"], "year_max": search["year_max"]}


def _stage(ws: Path, label: str, text: str, name: str) -> dict:
    from scholar_harness.corpus_accept import stage_ris_source

    return stage_ris_source(ws, label, text.encode(), file_name=name)


def _snapshot(ws: Path) -> dict:
    registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))["artifacts"]
    (entry,) = [e for e in registry.values() if e["artifact_type"] == "corpus_snapshot"]
    return json.loads((ws / entry["path"]).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- unchanged paths (characterization)

#: Taken at origin/main 2436fe66, before M3f: an import-only and a bare-verified.json accept.
IMPORT_ONLY_ARTIFACT = "ART-corpus-8ddb6e7a0c8626c2c115833838d43759"
VERIFIED_ONLY_ARTIFACT = "ART-corpus-37531fd36ece4001740d4d8495d38af5"


def test_an_import_only_accept_gives_the_snapshot_it_gave_before(tmp_path):
    from scholar_harness.corpus_accept import accept_corpus

    ws = _workspace(tmp_path)
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")
    _stage(ws, "Web of Science", WOS, "wos.ris")
    result = accept_corpus(ws, now=NOW)
    assert result.artifact_id == IMPORT_ONLY_ARTIFACT
    assert json.loads((ws / "literature" / "raw" / "provenance_manifest.json").read_text(encoding="utf-8"))["schema"] == (
        "nexus.corpus-import.v1")


def test_a_verified_only_accept_gives_the_snapshot_it_gave_before(tmp_path):
    from scholar_harness.corpus_accept import accept_corpus

    ws = _workspace(tmp_path)
    (ws / "literature" / "verified.json").write_text(json.dumps(HARVEST), encoding="utf-8")
    assert accept_corpus(ws, now=NOW).artifact_id == VERIFIED_ONLY_ARTIFACT


# --------------------------------------------------------------------------- the combined accept


def test_accept_corpus_combines_a_ready_harvest_with_staged_exports(tmp_path):
    from scholar_harness.corpus_accept import accept_corpus

    ws = _workspace(tmp_path)
    _ready_harvest(ws)
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")  # refused before M3f: VERIFIED_EXISTS
    result = accept_corpus(ws, now=NOW)
    # 2 harvested works + 2 Scopus records; Scopus #1 has the DOI of the openalex work.
    assert (result.record_count, result.study_count) == (4, 3)
    rows = json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))
    assert rows[:2] == HARVEST and [r["source_database"] for r in rows[2:]] == ["Scopus", "Scopus"]
    copy = ws / "literature" / "search_runs" / "run_001" / "verified.json"
    assert json.loads(copy.read_text(encoding="utf-8")) == HARVEST


def test_the_combined_snapshot_is_the_same_whatever_was_done_first(tmp_path):
    """The rows are ordered by part (harvest, then exports in staging order), never by the researcher's order."""
    from scholar_harness.corpus_accept import accept_corpus

    first = _workspace(tmp_path, "first")
    _ready_harvest(first)
    _stage(first, "Scopus", SCOPUS, "scopus.ris")

    second = _workspace(tmp_path, "second")
    _stage(second, "Scopus", SCOPUS, "scopus.ris")
    _ready_harvest(second)

    assert accept_corpus(first, now=NOW).artifact_id == accept_corpus(second, now=NOW).artifact_id


def test_a_combined_accept_is_idempotent(tmp_path):
    from scholar_harness.corpus_accept import accept_corpus

    ws = _workspace(tmp_path)
    _ready_harvest(ws)
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")
    first = accept_corpus(ws, now=NOW)
    again = accept_corpus(ws, now=NOW)
    assert again.already_accepted and again.artifact_id == first.artifact_id


def test_a_refused_gate_puts_the_harvests_file_back(tmp_path, monkeypatch):
    """Failure publishes nothing and leaves the harvest part as it was (Compass §7)."""
    from scholar_harness import corpus_accept
    from scholar_harness.contracts.acceptance import AcceptanceResult

    ws = _workspace(tmp_path)
    _ready_harvest(ws)
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")
    before = (ws / "literature" / "verified.json").read_bytes()
    monkeypatch.setattr(corpus_accept, "accept_artifact",
                        lambda *a, **k: AcceptanceResult(accepted=False, payload_hash="sha256:" + "0" * 64))
    with pytest.raises(corpus_accept.AcceptCorpusRefused):
        corpus_accept.accept_corpus(ws, now=NOW)
    assert (ws / "literature" / "verified.json").read_bytes() == before
    assert not (ws / "literature" / "raw" / "provenance_manifest.json").exists()


def test_prisma_identification_counts_fetched_plus_imported(tmp_path):
    from scholar_harness.corpus_accept import accept_corpus, prisma_identification

    ws = _workspace(tmp_path)
    _ready_harvest(ws)
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")
    _stage(ws, "Web of Science", WOS, "wos.ris")
    accepted = accept_corpus(ws, now=NOW)
    # 3 fetched by the harvest (legs) + 3 imported; 4 works.
    assert accepted.study_count == 4
    assert prisma_identification(ws, accepted.study_count) == (6, 2)


def test_an_unfinished_harvest_is_left_out_when_exports_are_staged(tmp_path):
    """M3i item 10 kept: the exports are accepted alone; the CLI says the harvest was left out."""
    ws = _workspace(tmp_path)
    _ready_harvest(ws, ended="FAILED")
    (ws / "literature" / "verified.json").unlink()
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")
    result = runner.invoke(app, ["accept-corpus", "--workspace", str(ws)])
    assert result.exit_code == 0, result.stdout
    assert "run_001" in result.stdout and "left out" in result.stdout
    assert len(_snapshot(ws)["data"]["record_to_study"]) == 2


def test_accept_corpus_ris_after_a_harvest_combines(tmp_path):
    ws = _workspace(tmp_path)
    _ready_harvest(ws)
    export = tmp_path / "scopus.ris"
    export.write_text(SCOPUS, encoding="utf-8")
    result = runner.invoke(app, ["accept-corpus", "--workspace", str(ws), "--ris", f"Scopus={export}"])
    assert result.exit_code == 0, result.stdout
    assert len(_snapshot(ws)["data"]["record_to_study"]) == 4


def test_the_workspace_copy_is_not_needed_to_reproduce(tmp_path):
    """Determinism: the same parts in two folders give the same artifact id."""
    from scholar_harness.corpus_accept import accept_corpus

    ws = _workspace(tmp_path)
    _ready_harvest(ws)
    _stage(ws, "Scopus", SCOPUS, "scopus.ris")
    twin = tmp_path / "twin"
    shutil.copytree(ws, twin)
    assert accept_corpus(ws, now=NOW).artifact_id == accept_corpus(twin, now=NOW).artifact_id
