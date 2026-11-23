"""H-workspace-format-version: the format version, the copy before a newer build writes, the refusals.

Record: ``docs/roadmap/milestones/H-workspace-format-version.md`` §6 (definition of done).
Every test fails on ``cc0e8fa1``: there was no ``workspace/format.py``, no copy and no refusal.
"""

from __future__ import annotations

import hashlib
import json
import threading
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.workspace import catalog
from scholar_harness.workspace import format as wf
from scholar_harness.workspace.audit import append_event, append_legacy_event

BUILD = wf.build_version()
REPLACED = "audit/replaced/20260101T000000Z"
LEFT_OUT = (".env", ".agents/skills/s/SKILL.md", ".cache/c.bin", "exports/e.txt", "rag/r.bin", "chroma_db/c.bin",
            f"{REPLACED}/.cache/x.bin")


@pytest.fixture(autouse=True)
def _fresh_memory():
    wf.forget()
    yield
    wf.forget()


def _hashes(ws: Path) -> dict[str, str]:
    return {
        p.relative_to(ws).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ws.rglob("*")) if p.is_file()
    }


def _journal(ws: Path) -> list[dict]:
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def _zips(ws: Path) -> list[Path]:
    folder = wf.copies_dir(ws)
    return sorted(folder.glob("*.zip")) if folder.is_dir() else []


@pytest.fixture
def old(tmp_path) -> Path:
    """A workspace as every build before this one left it: no format file, PDFs, the usual folders."""
    root = tmp_path / "root"
    catalog.create(root, "Old Review")
    ws = root / "old-review"
    (ws / wf.FORMAT_FILE).unlink()
    files = {
        "pdfs/S1.pdf": b"%PDF-1.7\n" + bytes(range(256)) * 40,
        f"{REPLACED}/pdfs/old.pdf": b"%PDF-1.4\nold",
        f"{REPLACED}/protocol.json": b"{}",
        "extracted/S1.md": b"---\ntitle: one\n---\ntext",
        ".harness-console/pipelines/p.json": b'{"id": "p"}',
        "charting/form.json": b'{"schema": "nexus.charting-form.v1"}',
    }
    files.update({rel: b"left out" for rel in LEFT_OUT})
    for rel, data in files.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_bytes(data)
    return ws


def _newer(ws: Path, number: int = wf.CURRENT_FORMAT + 1) -> None:
    (ws / wf.FORMAT_FILE).write_text(
        json.dumps({"schema": wf.FORMAT_SCHEMA, "format": number, "written_by": "9.9.9", "updated_at": "x"}), encoding="utf-8"
    )


def _assert_only_stamp_changed(before: dict[str, str], ws: Path) -> None:
    after = _hashes(ws)
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    assert changed <= {wf.FORMAT_FILE, "audit/journal.jsonl", "project.json"}, changed


# --- 1, 2: the first open for writing, and the second ---------------------------- #


def test_unstamped_workspace_is_copied_then_stamped_on_first_open_and_nothing_else_changes(old):
    before = _hashes(old)
    project_before = json.loads((old / "project.json").read_text(encoding="utf-8"))
    rows_before = (old / "audit" / "journal.jsonl").read_bytes()

    app = create_app(old)

    gate = app.state.format_gate
    assert gate.state == "ready" and gate.result.copy is not None
    assert len(_zips(old)) == 1
    stamp = json.loads((old / wf.FORMAT_FILE).read_text(encoding="utf-8"))
    assert stamp == {**stamp, "schema": wf.FORMAT_SCHEMA, "format": wf.CURRENT_FORMAT, "written_by": BUILD}
    journal = (old / "audit" / "journal.jsonl").read_bytes()
    assert journal.startswith(rows_before)
    new_rows = _journal(old)[len(rows_before.splitlines()):]
    assert [r["action"] for r in new_rows] == [wf.ACTION_STAMPED]
    assert new_rows[0]["parameters"]["copy"].endswith(_zips(old)[0].name)
    project_after = json.loads((old / "project.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in project_after.items() if k != "updated_at"} == {
        k: v for k, v in project_before.items() if k != "updated_at"
    }
    _assert_only_stamp_changed(before, old)
    assert TestClient(app).get("/api/v1/workspace/meta").status_code == 200


def test_a_second_open_makes_no_second_copy_and_writes_nothing(old):
    create_app(old)
    after_first = _hashes(old)
    wf.forget()  # a new process
    app = create_app(old)
    assert app.state.format_gate.result.copy is None
    root = old.parent
    catalog.check_open(root, old.name, None)
    assert len(_zips(old)) == 1
    assert _hashes(old) == after_first


# --- 3: a failed copy -------------------------------------------------------------- #


def test_a_copy_that_fails_midway_leaves_the_workspace_untouched_and_refused(old, monkeypatch):
    before = _hashes(old)
    real_write = zipfile.ZipFile.write
    calls = {"n": 0}

    def failing(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("disk full")
        return real_write(self, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "write", failing)
    app = create_app(old)

    gate = app.state.format_gate
    assert gate.state == "refused" and gate.refusal.code == wf.WORKSPACE_COPY_FAILED
    assert "disk full" in gate.refusal.message and "Nothing in the review was changed" in gate.refusal.message
    assert _hashes(old) == before
    assert not list(wf.copies_dir(old).glob("*.partial")) and not _zips(old)
    client = TestClient(app)
    for method, path in (("GET", "/api/v1/workspace/meta"), ("POST", "/api/v1/screening/decisions/events")):
        answer = client.request(method, path, json={})
        assert answer.status_code == 409 and answer.json()["detail"]["code"] == wf.WORKSPACE_COPY_FAILED
    listing = client.get("/api/v1/workspaces").json()
    assert listing["preparation"]["state"] == "refused"


def test_a_copies_folder_that_cannot_be_made_refuses_the_open(old):
    before = _hashes(old)
    (old.parent / wf.COPIES_DIR).write_text("a file where the folder should be", encoding="utf-8")
    app = create_app(old)
    assert app.state.format_gate.refusal.code == wf.WORKSPACE_COPY_FAILED
    assert _hashes(old) == before


# --- 4: a newer-format workspace ---------------------------------------------------- #


def test_a_newer_workspace_is_refused_everywhere_and_never_written(old, monkeypatch):
    _newer(old)
    before = _hashes(old)
    app = create_app(old)
    assert app.state.format_gate.refusal.code == wf.WORKSPACE_FORMAT_NEWER
    client = TestClient(app)
    answer = client.get("/api/v1/workspace/meta")
    assert answer.status_code == 409
    assert answer.json()["detail"]["code"] == wf.WORKSPACE_FORMAT_NEWER
    assert "Made with a newer version of Nexus Scholar" in answer.json()["detail"]["message"]
    assert "9.9.9" in answer.json()["detail"]["message"]
    with pytest.raises(wf.WorkspaceFormatRefused):
        append_event(old, "ANY", "x")
    with pytest.raises(wf.WorkspaceFormatRefused):
        append_legacy_event(old, "ANY", "agent", "x", [], [], {})
    with pytest.raises(wf.WorkspaceFormatRefused):
        wf.prepare_for_writing(old, agent="test")
    row = next(i for i in client.get("/api/v1/workspaces").json()["items"] if i["slug"] == old.name)
    assert row["format"]["newer"] is True and row["format"]["written_by"] == "9.9.9"
    assert _hashes(old) == before and not _zips(old)


def test_open_on_the_workspaces_screen_refuses_a_newer_workspace_and_keeps_the_current_one(old, tmp_path):
    root = old.parent
    catalog.create(root, "Current Review")
    current = root / "current-review"
    _newer(old)
    opened = []
    app = create_app(current, workspaces_root=root, on_open=opened.append)
    answer = TestClient(app).post("/api/v1/workspaces/open", json={"slug": old.name})
    assert answer.status_code == 409 and answer.json()["detail"]["code"] == wf.WORKSPACE_FORMAT_NEWER
    assert opened == []


def test_an_unreadable_format_file_is_refused_and_nothing_is_written(old):
    (old / wf.FORMAT_FILE).write_text("{not json", encoding="utf-8")
    before = _hashes(old)
    app = create_app(old)
    assert app.state.format_gate.refusal.code == wf.WORKSPACE_FORMAT_UNREADABLE
    assert _hashes(old) == before and not _zips(old)


# --- 5: what the copy holds, and the restore -------------------------------------- #


def test_the_copy_holds_the_whole_review_with_pdfs_and_restores_by_itself(old, tmp_path):
    before = _hashes(old)
    status_before = catalog.describe(old, None)["status"]
    create_app(old)
    (archive_path,) = _zips(old)
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        kinds = {info.filename: info.compress_type for info in archive.infolist()}
        restored = tmp_path / "restored" / old.name
        archive.extractall(restored)
    def left_out(rel: str) -> bool:
        top = rel.split("/")[0]
        under_replaced = rel.startswith(f"{REPLACED}/") and rel.split("/")[3] in wf.EXCLUDED_DIRS
        return rel == ".env" or top in wf.EXCLUDED_DIRS or under_replaced

    for rel in LEFT_OUT:
        assert left_out(rel) and rel not in names
    assert not any(left_out(name) for name in names)
    assert {"pdfs/S1.pdf", f"{REPLACED}/pdfs/old.pdf", "extracted/S1.md", ".harness-console/pipelines/p.json",
            "charting/form.json", "protocol.json", "project.json", "audit/journal.jsonl", ".mcp.json"} <= names
    assert kinds["pdfs/S1.pdf"] == zipfile.ZIP_STORED and kinds["protocol.json"] == zipfile.ZIP_DEFLATED
    assert _hashes(restored) == {k: v for k, v in before.items() if not left_out(k)}
    assert catalog.validity(restored) == (True, None)
    assert wf.read_format(restored).format == 0  # the copy is the review as it was before the stamp
    assert catalog.describe(restored, None)["status"] == status_before


# --- 5b: the copy is visible while it runs ------------------------------------------ #


class _Hold:
    """Blocks the copy after its first file until released."""

    def __init__(self, monkeypatch):
        self.started, self.release = threading.Event(), threading.Event()
        real = zipfile.ZipFile.write

        def held(zself, *args, **kwargs):
            self.started.set()
            assert self.release.wait(10)
            return real(zself, *args, **kwargs)

        monkeypatch.setattr(zipfile.ZipFile, "write", held)


def test_a_large_copy_runs_in_the_background_and_every_workspace_route_says_so(old, monkeypatch):
    monkeypatch.setattr(wf, "FOREGROUND_BYTES", 0)
    hold = _Hold(monkeypatch)
    app = create_app(old)
    assert hold.started.wait(10)
    client = TestClient(app)
    answer = client.get("/api/v1/workspace/meta")
    assert answer.status_code == 503
    detail = answer.json()["detail"]
    assert detail["code"] == wf.WORKSPACE_PREPARING and "Old Review" in detail["message"]
    assert detail["details"]["title"] == "Old Review" and detail["details"]["total_bytes"] > 0
    preparation = client.get("/api/v1/workspaces/preparation").json()["preparation"]
    assert preparation["state"] == "preparing" and preparation["reason"] == "format"
    assert client.get("/api/v1/workspaces").status_code == 200
    hold.release.set()
    assert app.state.format_gate.wait(10)
    assert client.get("/api/v1/workspace/meta").status_code == 200
    assert client.get("/api/v1/workspaces/preparation").json()["preparation"]["result"]["copied"] is True


def test_stopping_the_server_during_the_copy_cancels_it_and_stamps_nothing(old, monkeypatch):
    monkeypatch.setattr(wf, "FOREGROUND_BYTES", 0)
    hold = _Hold(monkeypatch)
    before = _hashes(old)
    app = create_app(old)
    assert hold.started.wait(10)
    gate = app.state.format_gate
    gate._cancel.set()
    hold.release.set()
    gate.stop()
    assert gate.state == "cancelled"
    assert not _zips(old) and not list(wf.copies_dir(old).glob("*.partial"))
    assert _hashes(old) == before


def test_the_ui_start_path_opens_the_most_recent_review_and_shows_the_copy(old, tmp_path, monkeypatch):
    """`nexus-scholar ui` with no --workspace opens the most recent review with no click (cli.py)."""
    from scholar_harness.console import launcher

    monkeypatch.setattr(wf, "FOREGROUND_BYTES", 0)
    hold = _Hold(monkeypatch)
    ui = tmp_path / "ui"
    for page in ("", "workspaces", "screening/home"):
        (ui / "en" / page).mkdir(parents=True, exist_ok=True)
        (ui / "en" / page / "index.html").write_text("<html></html>", encoding="utf-8")
    seen = {}

    class Server:
        def __init__(self, app, host, port):
            self.app, self.started, self.should_exit = app, True, False

        def run(self):
            client = TestClient(self.app, base_url="http://127.0.0.1:8770",
                                headers={"Authorization": f"Bearer {app_launcher.token}"})
            assert hold.started.wait(10)
            seen["during"] = client.get("/api/v1/workspace/meta").json()["detail"]
            hold.release.set()
            assert self.app.state.format_gate.wait(10)
            seen["after"] = client.get("/api/v1/workspace/meta").status_code

    root = old.parent
    app_launcher = launcher.Launcher(root=root, workspace=catalog.most_recent(root), ui_dir=ui, open_browser=False,
                                     server_factory=Server, say=lambda _: None)
    app_launcher.run()
    assert seen["during"]["code"] == wf.WORKSPACE_PREPARING and seen["during"]["details"]["title"] == "Old Review"
    assert seen["after"] == 200
    assert wf.read_format(old).format == wf.CURRENT_FORMAT and len(_zips(old)) == 1


# --- 6: reads never write --------------------------------------------------------- #


def test_the_list_and_status_never_copy_or_stamp(old):
    from typer.testing import CliRunner

    from scholar_harness.cli import app as cli

    before = _hashes(old)
    root = old.parent
    listing = catalog.listing(root, "flag", None)
    row = next(i for i in listing["items"] if i["slug"] == old.name)
    assert row["format"] == {"recorded": False, "format": None, "written_by": None, "newer": False, "unreadable": False}
    assert row["last_copy"] is None
    catalog.most_recent(root)
    assert CliRunner().invoke(cli, ["status", "--workspace", str(old)]).exit_code == 0
    assert _hashes(old) == before and not wf.copies_dir(old).exists()


# --- 7: birth ----------------------------------------------------------------------- #


def test_a_new_workspace_is_stamped_at_birth_and_its_first_open_copies_nothing(tmp_path):
    from scholar_harness.inception.emit import NEW_WORKSPACE_FILES

    root = tmp_path / "root"
    catalog.create(root, "New Review")
    ws = root / "new-review"
    state = wf.read_format(ws)
    assert (state.format, state.written_by, state.recorded) == (wf.CURRENT_FORMAT, BUILD, True)
    assert wf.FORMAT_FILE in NEW_WORKSPACE_FILES
    create_app(ws)
    assert not wf.copies_dir(ws).exists()


def test_the_workspace_manager_script_stamps_the_monorepo_layout(tmp_path):
    from scholar_harness.inception.genesis import scaffold_project

    ws = scaffold_project(tmp_path, "Script Review", "script-review", "Positivist", ["RQ1"])
    assert wf.read_format(ws).format == wf.CURRENT_FORMAT


# --- 8: the registry ----------------------------------------------------------------- #


def test_every_format_has_one_idempotent_step_to_the_next(old):
    assert sorted(wf.STEPS) == list(range(wf.CURRENT_FORMAT))
    for number, step in wf.STEPS.items():
        assert step.from_format == number and step.to_format == number + 1
        before = _hashes(old)
        first = step.apply(old)
        once = _hashes(old)
        second = step.apply(old)
        assert _hashes(old) == once and second in ([], first)
        if number == 0:
            assert first == [] and once == before  # stamp-today rewrites no file


# --- 9: a crash mid-way ------------------------------------------------------------- #


def test_a_crash_between_the_copy_and_the_stamp_is_finished_by_the_next_open(old, monkeypatch):
    before = _hashes(old)
    real = wf.write_format

    def crash(*args, **kwargs):
        raise OSError("power cut")

    monkeypatch.setattr(wf, "write_format", crash)
    with pytest.raises(wf.WorkspaceFormatRefused) as refused:
        wf.prepare_for_writing(old, agent="test")
    assert "could not be recorded" in refused.value.message
    assert wf.read_format(old).format == 0
    monkeypatch.setattr(wf, "write_format", real)
    result = wf.prepare_for_writing(old, agent="test")
    assert result.copy is not None and wf.read_format(old).format == wf.CURRENT_FORMAT
    _assert_only_stamp_changed(before, old)


# --- 10: a newer build, same format ------------------------------------------------- #


def test_a_newer_build_copies_once_and_records_itself(old):
    wf.write_format(old, wf.CURRENT_FORMAT, "1.0.0")
    result = wf.prepare_for_writing(old, agent="test", build="1.2.0")
    assert result.copy is not None and result.reason == "build"
    assert wf.read_format(old).written_by == "1.2.0"
    assert _journal(old)[-1]["action"] == wf.ACTION_NEWER_BUILD
    assert "1.0.0-to-1.2.0" in result.copy.name
    wf.forget()
    assert wf.prepare_for_writing(old, agent="test", build="1.2.0").copy is None
    wf.forget()
    assert wf.prepare_for_writing(old, agent="test", build="1.1.0").copy is None  # an older build: same format, no copy
    assert wf.read_format(old).written_by == "1.2.0"  # never written back down


# --- 11: pruning -------------------------------------------------------------------- #


def test_the_five_newest_copies_are_kept_and_nothing_else_is_deleted(old):
    folder = wf.copies_dir(old)
    folder.mkdir(parents=True)
    (folder / "my-notes.zip").write_bytes(b"mine")
    (folder / "other-review-20260101T000000Z-format0-to1-earlier-to-1.0.0.zip").write_bytes(b"other")
    wf.write_format(old, wf.CURRENT_FORMAT, "1.0.0")
    for minor in range(1, 7):
        wf.forget()
        assert wf.prepare_for_writing(old, agent="test", build=f"1.{minor}.0").copy is not None
    ours = [p for p in _zips(old) if p.name.startswith(old.name)]
    assert len(ours) == 5
    assert not any("1.0.0-to-1.1.0" in p.name for p in ours)  # the oldest went
    assert (folder / "my-notes.zip").is_file()
    assert (folder / "other-review-20260101T000000Z-format0-to1-earlier-to-1.0.0.zip").is_file()
    assert wf.last_copy(old)["name"].endswith("1.5.0-to-1.6.0.zip")


# --- the command line, agent_screen and the MCP server ------------------------------- #


WRITING_COMMANDS = (
    ["sync", "--workspace", "{ws}"],
    ["run", "--workspace", "{ws}"],
    ["export", "latex", "--workspace", "{ws}"],
    ["accept-corpus", "--workspace", "{ws}"],
    ["supervise", "--workspace", "{ws}"],
    ["setup-mcp", "--workspace", "{ws}"],
    ["chase", "run", "{ws}"],
    ["chase", "accept", "{ws}"],
    ["log", "event", "{ws}", "--action", "X"],
    ["log", "sync-index", "{ws}"],
    ["extract", "publish", "{ws}"],
)


@pytest.mark.parametrize("command", WRITING_COMMANDS, ids=lambda c: " ".join(c[:2]))
def test_every_writing_command_refuses_a_newer_workspace_before_writing(old, command):
    from typer.testing import CliRunner

    from scholar_harness.cli import app as cli

    _newer(old)
    before = _hashes(old)
    result = CliRunner().invoke(cli, [part.format(ws=old) for part in command])
    assert result.exit_code == 1, result.output
    assert "newer version of Nexus Scholar" in result.output
    assert _hashes(old) == before


def test_a_writing_command_copies_and_stamps_an_older_workspace_first(old):
    from typer.testing import CliRunner

    from scholar_harness.cli import app as cli

    result = CliRunner().invoke(cli, ["log", "event", str(old), "--action", "NOTE", "--description", "x"])
    assert result.exit_code == 0, result.output
    assert "Saving a copy of old-review" in result.stderr and "Saved a copy of this review" in result.stderr
    assert "copy" not in result.stdout  # standard output stays the command's own (it may be JSON)
    assert [r["action"] for r in _journal(old)][-2:] == [wf.ACTION_STAMPED, "NOTE"]


def test_agent_screen_refuses_a_newer_workspace(old, monkeypatch):
    from scholar_harness import agent_screen

    _newer(old)
    before = _hashes(old)
    monkeypatch.setattr("sys.argv", ["agent_screen.py", "prepare", str(old)])
    with pytest.raises(SystemExit) as stop:
        agent_screen.main()
    assert stop.value.code == 1
    assert _hashes(old) == before


def test_the_mcp_server_refuses_to_write_into_a_newer_workspace(old, monkeypatch):
    from scholar_agent import server

    _newer(old)
    before = _hashes(old)
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(old))
    answer = json.loads(server.nexus_dedup(str(old / "missing.json"), str(old / "out.json")))
    assert answer["status"] == "ERROR" and answer["code"] == wf.WORKSPACE_FORMAT_NEWER
    with pytest.raises(wf.WorkspaceFormatRefused):
        server._open_for_writing(old)
    assert _hashes(old) == before


# --- versions ------------------------------------------------------------------------ #


def test_versions_sort_as_releases_do():
    order = ["1.0.0", "1.1.0.dev1", "1.1.0a1", "1.1.0b7", "1.1.0b8", "1.1.0rc1", "1.1.0", "1.1.0.post1", "1.1.1"]
    keys = [wf.version_key(v) for v in order]
    assert keys == sorted(keys)
    assert wf.version_key("not a version") is None and wf.version_key(None) is None
