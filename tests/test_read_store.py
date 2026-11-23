"""The store in front of the display routes (H-screening-read-performance, question 2 and 3).

A result is kept only inside a display call, keyed by every file's name, size
and modification time; outside one, everything reads the disk.
"""

from __future__ import annotations

import os
import threading

import pytest

from scholar_harness.screening import read_store


@pytest.fixture(autouse=True)
def _empty_store():
    read_store.clear()
    yield
    read_store.clear()


@pytest.fixture
def ws(tmp_path):
    root = tmp_path / "ws"
    (root / "literature" / "screening").mkdir(parents=True)
    (root / "literature" / "screening" / "batch_001_decisions.json").write_text("{}", encoding="utf-8")
    (root / "protocol.json").write_text('{"a": 1}', encoding="utf-8")
    return root


class Counter:
    def __init__(self, value="x"):
        self.calls = 0
        self.value = value

    def __call__(self):
        self.calls += 1
        return {"value": self.value, "calls": self.calls}


def test_outside_a_display_call_nothing_is_kept(ws):
    compute = Counter()
    assert read_store.remember(ws, "r", compute)["calls"] == 1
    assert read_store.remember(ws, "r", compute)["calls"] == 2
    assert not read_store.active()


def test_inside_display_calls_a_result_is_kept_while_no_file_changes(ws):
    compute = Counter()
    with read_store.display_reads():
        first = read_store.remember(ws, "r", compute)
    with read_store.display_reads():
        second = read_store.remember(ws, "r", compute)
    assert compute.calls == 1 and first == second
    second["value"] = "changed by the caller"
    with read_store.display_reads():
        assert read_store.remember(ws, "r", compute)["value"] == "x"  # each caller gets its own copy


@pytest.mark.parametrize("change", ["rewrite", "append", "touch", "add", "remove"])
def test_any_file_change_recomputes(ws, change):
    compute = Counter()
    path = ws / "literature" / "screening" / "batch_001_decisions.json"
    with read_store.display_reads():
        read_store.remember(ws, "r", compute)
    if change == "rewrite":
        path.write_text('{"b":2}', encoding="utf-8")
    elif change == "append":
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
    elif change == "touch":
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    elif change == "add":
        (ws / "literature" / "screening" / "batch_002_decisions.json").write_text("{}", encoding="utf-8")
    else:
        path.unlink()
    with read_store.display_reads():
        read_store.remember(ws, "r", compute)
    assert compute.calls == 2


def test_a_change_in_a_folder_no_kept_result_reads_keeps_the_result(ws):
    compute = Counter()
    with read_store.display_reads():
        read_store.remember(ws, "r", compute)
    for folder in sorted(read_store.NOT_READ):
        (ws / folder).mkdir(exist_ok=True)
        (ws / folder / "file.txt").write_text("text", encoding="utf-8")
    with read_store.display_reads():
        read_store.remember(ws, "r", compute)
    assert compute.calls == 1


def test_a_file_written_while_the_result_was_computed_is_never_kept(ws):
    path = ws / "protocol.json"

    def compute():
        path.write_text('{"a": 2, "written": "during"}', encoding="utf-8")
        return "computed while the file changed"

    with read_store.display_reads():
        read_store.remember(ws, "r", compute)
    later = Counter()
    with read_store.display_reads():
        read_store.remember(ws, "r", later)
    assert later.calls == 1


def test_an_exception_is_not_kept(ws):
    calls = []

    def fails():
        calls.append(1)
        raise ValueError("unreadable")

    for _ in range(2):
        with read_store.display_reads(), pytest.raises(ValueError):
            read_store.remember(ws, "r", fails)
    assert len(calls) == 2


def test_two_workspaces_keep_their_own_results(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    with read_store.display_reads():
        assert read_store.remember(a, "r", lambda: "a") == "a"
        assert read_store.remember(b, "r", lambda: "b") == "b"
        assert read_store.remember(a, "r", lambda: "not a") == "a"


_OPENED: list[str] = []
_WATCH: list[str] = []


def _hook(event, args):
    if event == "open" and _WATCH and args and isinstance(args[0], str) and os.path.abspath(args[0]) == _WATCH[0]:
        _OPENED.append(args[0])


import sys

sys.addaudithook(_hook)


def test_a_file_is_opened_once_per_display_call_and_again_when_it_changes(ws):
    path = ws / "protocol.json"
    _OPENED.clear()
    _WATCH[:] = [os.path.abspath(path)]
    try:
        with read_store.display_reads():
            assert read_store.read_text(path) == '{"a": 1}'
            assert read_store.read_bytes(path) == b'{"a": 1}'
            assert len(_OPENED) == 1
            path.write_text('{"a": 22}', encoding="utf-8")  # another size: read again
            before = len(_OPENED)
            assert read_store.read_text(path) == '{"a": 22}'
            assert len(_OPENED) == before + 1
        before = len(_OPENED)
        read_store.read_bytes(path)
        read_store.read_bytes(path)
        assert len(_OPENED) == before + 2  # outside a display call: every read opens the file
    finally:
        _WATCH.clear()


def test_read_text_reads_line_endings_as_path_read_text_does(ws):
    path = ws / "events.jsonl"
    path.write_bytes(b'{"a": 1}\r\n{"b": 2}\r{"c": 3}\n')
    with read_store.display_reads():
        inside = read_store.read_text(path)
    assert inside == read_store.read_text(path) == path.read_text(encoding="utf-8")


def test_the_display_scope_does_not_leak_into_another_thread(ws):
    seen = []
    with read_store.display_reads():
        thread = threading.Thread(target=lambda: seen.append(read_store.active()))
        thread.start()
        thread.join()
        assert read_store.active()
    assert seen == [False]
    assert not read_store.active()


def test_a_display_route_keeps_its_function_signature():
    import inspect

    def route(request, study_id: str, limit: int = 3):
        return read_store.active()

    wrapped = read_store.display_route(route)
    assert inspect.signature(wrapped) == inspect.signature(route)
    assert wrapped(None, "S") is True
    assert not read_store.active()
