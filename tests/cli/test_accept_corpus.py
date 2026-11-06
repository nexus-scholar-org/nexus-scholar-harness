"""M0: ``nexus-scholar accept-corpus`` is the entry path into screening.

Before it, nothing outside tests built a corpus snapshot, so ``prepare``
exited on a fresh workspace ("No artifact registry found", CORE-07). The
command builds the Contract-v1 snapshot from ``literature/verified.json`` or a
RIS export, passes it through the acceptance gate, and leaves the workspace
ready for ``prepare``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.screening.batcher import cmd_prepare

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "b" * 32

runner = CliRunner()
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


def _workspace(tmp_path: Path, *, registered: bool = True) -> Path:
    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    manifest = {"project_id": "accept-corpus-test"}
    if registered:
        manifest["registered_workspace_id"] = WS_ID
    (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    (ws / "protocol.json").write_text(PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")
    return ws


def _verified(ws: Path) -> list[dict]:
    records = [
        {
            "workspace_id": "SCI-000001",
            "title": "UAV multispectral weed mapping in maize",
            "year": 2024,
            "provider": "openalex",
            "provider_id": "W1",
            "external_ids": {"doi": "10.1000/uav-1"},
            "abstract": "Abstract one.",
        },
        {
            "workspace_id": "SCI-000002",
            "title": "UAV multispectral weed mapping in maize",
            "year": 2024,
            "provider": "crossref",
            "provider_id": "10.1000/uav-1",
            "external_ids": {"doi": "10.1000/uav-1"},
            "abstract": "Abstract one, from Crossref.",
        },
        {
            "workspace_id": "SCI-000003",
            "title": "Deep learning weed detection from drone imagery",
            "year": 2023,
            "provider": "openalex",
            "provider_id": "W3",
            "external_ids": {"doi": "10.1000/uav-3"},
            "abstract": "Abstract three.",
        },
    ]
    (ws / "literature" / "verified.json").write_text(json.dumps(records), encoding="utf-8")
    return records


def _registry(ws: Path) -> dict:
    return json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))


def _corpus_entries(ws: Path) -> list[dict]:
    return [e for e in _registry(ws)["artifacts"].values() if e["artifact_type"] == "corpus_snapshot"]


def test_prepare_succeeds_on_a_fresh_workspace_after_accept_corpus(tmp_path):
    ws = _workspace(tmp_path)
    _verified(ws)

    with pytest.raises(SystemExit):
        cmd_prepare(ws)  # the gap this command closes

    result = runner.invoke(app, ["accept-corpus", "--workspace", str(ws)])
    assert result.exit_code == 0, result.stdout
    assert len(_corpus_entries(ws)) == 1
    assert "2 studies from 3 records" in _plain(result.stdout)

    cmd_prepare(ws, batch_size=20)
    batch = json.loads((ws / "literature" / "screening" / "batch_001.json").read_text(encoding="utf-8"))
    papers = batch["papers"]
    assert len(papers) == 2
    assert all(p["workspace_id"].startswith("STU-") for p in papers)
    abstracts = sorted(p["abstract"] for p in papers)
    assert "Abstract three." in abstracts  # verified.json abstracts reach the batch


def test_accept_corpus_is_idempotent(tmp_path):
    ws = _workspace(tmp_path)
    _verified(ws)
    first = runner.invoke(app, ["accept-corpus", "--workspace", str(ws)])
    second = runner.invoke(app, ["accept-corpus", "--workspace", str(ws)])
    assert first.exit_code == 0, first.stdout
    assert second.exit_code == 0, second.stdout
    assert len(_corpus_entries(ws)) == 1


def test_accept_corpus_from_ris_writes_verified_with_stable_ids(tmp_path):
    ws = _workspace(tmp_path)
    ris = tmp_path / "scopus.ris"
    ris.write_text(
        "TY  - JOUR\nTI  - UAV weed mapping\nPY  - 2024\nDO  - 10.1000/ris-1\nAB  - RIS abstract one.\nER  - \n"
        "TY  - JOUR\nTI  - Drone crop scouting\nPY  - 2022\nDO  - 10.1000/ris-2\nAB  - RIS abstract two.\nER  - \n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["accept-corpus", "--workspace", str(ws), "--ris", str(ris)])
    assert result.exit_code == 0, result.stdout

    verified = json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))
    ids = [r["workspace_id"] for r in verified]
    assert len(ids) == 2 and all(i.startswith("SCI-") for i in ids)

    again = tmp_path / "ws2"
    again.mkdir()
    ws2 = _workspace(again)
    runner.invoke(app, ["accept-corpus", "--workspace", str(ws2), "--ris", str(ris)])
    ids2 = [r["workspace_id"] for r in json.loads((ws2 / "literature" / "verified.json").read_text(encoding="utf-8"))]
    assert ids2 == ids  # derived from the record, not arrival order

    events = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(e["action"] == "CORPUS_IMPORTED" for e in events)

    cmd_prepare(ws, batch_size=20)
    batch = json.loads((ws / "literature" / "screening" / "batch_001.json").read_text(encoding="utf-8"))
    assert sorted(p["abstract"] for p in batch["papers"]) == ["RIS abstract one.", "RIS abstract two."]


def test_accept_corpus_from_ris_refuses_to_overwrite_verified(tmp_path):
    ws = _workspace(tmp_path)
    _verified(ws)
    ris = tmp_path / "x.ris"
    ris.write_text("TY  - JOUR\nTI  - X\nER  - \n", encoding="utf-8")
    result = runner.invoke(app, ["accept-corpus", "--workspace", str(ws), "--ris", str(ris)])
    assert result.exit_code == 1
    assert "verified.json already exists" in _plain(result.stdout)


@pytest.mark.parametrize(
    ("setup", "message"),
    [
        ("unregistered", "registered_workspace_id"),
        ("no-protocol", "protocol.json"),
        ("no-records", "verified.json"),
        ("empty-records", "no records"),
    ],
)
def test_accept_corpus_refusals(tmp_path, setup, message):
    ws = _workspace(tmp_path, registered=setup != "unregistered")
    if setup == "no-protocol":
        (ws / "protocol.json").unlink()
    if setup == "empty-records":
        (ws / "literature" / "verified.json").write_text("[]", encoding="utf-8")
    if setup in ("unregistered", "no-protocol"):
        _verified(ws)
    result = runner.invoke(app, ["accept-corpus", "--workspace", str(ws)])
    assert result.exit_code == 1, result.stdout
    assert message in _plain(result.stdout)
    assert not (ws / "audit" / "artifact_registry.json").exists()


# --- M5b: several database exports, deduplicated across files -----------------

SCOPUS = (
    "TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV weed mapping in maize\nPY  - 2024\nDO  - 10.1000/m5b-1\nAB  - One.\nER  - \n"
    "TY  - JOUR\nAU  - Chen, L.\nTI  - Drone crop scouting with deep learning\nPY  - 2022\nDO  - 10.1000/m5b-2\nAB  - Two.\nER  - \n"
    "TY  - JOUR\nAU  - Diaz, A.\nTI  - Hyperspectral weed discrimination\nPY  - 2021\nAB  - Three.\nER  - \n"
)
# One DOI repeat of Scopus #1, one title-only near-twin of Scopus #3, one new record.
WOS = (
    "TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV Weed Mapping in Maize\nPY  - 2024\nDO  - https://doi.org/10.1000/M5B-1\nER  - \n"
    "TY  - JOUR\nAU  - Diaz, A.\nTI  - Hyperspectral weed discrimination.\nPY  - 2021\nER  - \n"
    "TY  - JOUR\nAU  - Okafor, N.\nTI  - Site-specific herbicide prescription maps\nPY  - 2023\nDO  - 10.1000/m5b-4\nER  - \n"
)


def _ris_files(tmp_path: Path) -> tuple[Path, Path]:
    scopus, wos = tmp_path / "scopus-export.ris", tmp_path / "savedrecs.ris"
    scopus.write_text(SCOPUS, encoding="utf-8")
    wos.write_text(WOS, encoding="utf-8")
    return scopus, wos


def test_several_ris_exports_are_deduplicated_and_counted_per_database(tmp_path):
    ws = _workspace(tmp_path)
    scopus, wos = _ris_files(tmp_path)
    result = runner.invoke(
        app,
        ["accept-corpus", "--workspace", str(ws), "--ris", f"Scopus={scopus}", "--ris", f"Web of Science={wos}"],
    )
    assert result.exit_code == 0, _plain(result.stdout)
    assert "4 studies from 6 records" in _plain(result.stdout)

    verified = json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))
    assert [r["source_database"] for r in verified] == ["Scopus"] * 3 + ["Web of Science"] * 3
    assert len({r["workspace_id"] for r in verified}) == 6  # a repeat is still its own record

    manifest = json.loads((ws / "literature" / "raw" / "provenance_manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_raw_harvested"] == 6
    assert [(s["label"], s["records"]) for s in manifest["sources"]] == [("Scopus", 3), ("Web of Science", 3)]
    assert (ws / "literature" / "raw" / "ris" / "scopus.ris").read_text(encoding="utf-8") == SCOPUS

    snapshot = _corpus_entries(ws)
    assert len(snapshot) == 1
    cmd_prepare(ws, batch_size=20)
    batch = json.loads((ws / "literature" / "screening" / "batch_001.json").read_text(encoding="utf-8"))
    assert len(batch["papers"]) == 4

    events = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    imported = [e for e in events if e["action"] == "CORPUS_IMPORTED"]
    assert imported and imported[-1]["metrics"]["by_source"] == {"Scopus": 3, "Web of Science": 3}
    assert sum(e["action"] == "CORPUS_SOURCE_STAGED" for e in events) == 2


def test_preview_matches_what_acceptance_builds(tmp_path):
    from scholar_harness.corpus_accept import accept_corpus, preview_staged, stage_ris_source

    ws = _workspace(tmp_path)
    scopus, wos = _ris_files(tmp_path)
    stage_ris_source(ws, "Scopus", scopus.read_bytes(), file_name=scopus.name, searched_on="2026-11-06", query="uav AND weed")
    stage_ris_source(ws, "Web of Science", wos.read_bytes(), file_name=wos.name)
    preview = preview_staged(ws)
    assert (preview["identified"], preview["duplicates"], preview["unique_studies"]) == (6, 2, 4)
    assert preview["sources"][0] == {
        "label": "Scopus", "file_name": "scopus-export.ris", "records": 3,
        "searched_on": "2026-11-06", "query": "uav AND weed",
    }
    assert not (ws / "literature" / "verified.json").exists()  # a preview writes nothing
    result = accept_corpus(ws)
    assert (result.record_count, result.study_count) == (6, 4)
    again = accept_corpus(ws)
    assert again.already_accepted and again.artifact_id == result.artifact_id


@pytest.mark.parametrize(
    ("label", "content", "kwargs", "code"),
    [
        ("Scopus", SCOPUS.encode(), {}, "SOURCE_LABEL_TAKEN"),
        ("scopus", WOS.encode(), {}, "SOURCE_LABEL_TAKEN"),
        ("Copy", SCOPUS.encode(), {}, "SOURCE_DUPLICATE_FILE"),
        ("Notes", b"just some text\n", {}, "SOURCE_NOT_RIS"),
        ("", WOS.encode(), {}, "SOURCE_LABEL_INVALID"),
        ("<script>", WOS.encode(), {}, "SOURCE_LABEL_INVALID"),
        ("IEEE", WOS.encode(), {"searched_on": "06/11/2026"}, "SOURCE_DATE_INVALID"),
    ],
)
def test_staging_refusals(tmp_path, label, content, kwargs, code):
    from scholar_harness.corpus_accept import AcceptCorpusRefused, stage_ris_source, staged_sources

    ws = _workspace(tmp_path)
    stage_ris_source(ws, "Scopus", SCOPUS.encode(), file_name="scopus.ris")
    with pytest.raises(AcceptCorpusRefused) as caught:
        stage_ris_source(ws, label, content, file_name="x.ris", **kwargs)
    assert caught.value.code == code
    assert [s["label"] for s in staged_sources(ws)] == ["Scopus"]
    assert sorted(p.name for p in (ws / "literature" / "raw" / "ris").iterdir()) == ["scopus.ris", "sources.json"]


def test_a_large_file_is_refused(tmp_path, monkeypatch):
    from scholar_harness import corpus_accept

    ws = _workspace(tmp_path)
    monkeypatch.setattr(corpus_accept, "MAX_SOURCE_BYTES", 10)
    with pytest.raises(corpus_accept.AcceptCorpusRefused) as caught:
        corpus_accept.stage_ris_source(ws, "Scopus", SCOPUS.encode(), file_name="scopus.ris")
    assert caught.value.code == "SOURCE_TOO_LARGE"


def test_sources_are_frozen_once_the_corpus_is_accepted(tmp_path):
    from scholar_harness.corpus_accept import (
        AcceptCorpusRefused,
        accept_corpus,
        remove_staged_source,
        stage_ris_source,
        staged_sources,
    )

    ws = _workspace(tmp_path)
    stage_ris_source(ws, "Scopus", SCOPUS.encode(), file_name="scopus.ris")
    stage_ris_source(ws, "WoS", WOS.encode(), file_name="wos.ris")
    remove_staged_source(ws, "wos")
    assert [s["label"] for s in staged_sources(ws)] == ["Scopus"]
    assert not (ws / "literature" / "raw" / "ris" / "wos.ris").exists()
    accept_corpus(ws)
    for attempt in (
        lambda: stage_ris_source(ws, "WoS", WOS.encode(), file_name="wos.ris"),
        lambda: remove_staged_source(ws, "Scopus"),
    ):
        with pytest.raises(AcceptCorpusRefused) as caught:
            attempt()
        assert caught.value.code == "CORPUS_ALREADY_ACCEPTED"


def test_staging_refuses_when_discovery_already_wrote_the_corpus(tmp_path):
    from scholar_harness.corpus_accept import AcceptCorpusRefused, stage_ris_source

    ws = _workspace(tmp_path)
    _verified(ws)
    with pytest.raises(AcceptCorpusRefused) as caught:
        stage_ris_source(ws, "Scopus", SCOPUS.encode(), file_name="scopus.ris")
    assert caught.value.code == "VERIFIED_EXISTS"


@pytest.mark.parametrize(
    ("value", "label", "path"),
    [
        ("Scopus=exports/scopus.ris", "Scopus", "exports/scopus.ris"),
        (r"Web of Science=C:\x\wos.ris", "Web of Science", r"C:\x\wos.ris"),
        (r"C:\x\wos.ris", None, r"C:\x\wos.ris"),
        ("exports/a=b.ris", None, "exports/a=b.ris"),
        ("scopus.ris", None, "scopus.ris"),
    ],
)
def test_ris_option_parsing(value, label, path):
    from scholar_harness.corpus_accept import parse_ris_option

    assert parse_ris_option(value) == (label, Path(path))
