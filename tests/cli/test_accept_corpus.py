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
