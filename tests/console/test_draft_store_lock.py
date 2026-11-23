"""One draft record, two processes (M10c, decision item 10).

The MCP server (the researcher's assistant) and the console are two
processes writing the same ``draft.json``. Each write is read-then-write of
the whole record, so without a lock both processes hold, a side write that
read the record before the console's save landed writes the old draft back.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from scholar_harness.inception.drafts import DraftStore

_SIDE_WRITER = textwrap.dedent(
    """
    import sys, time
    from pathlib import Path
    from scholar_harness.inception.drafts import DraftStore

    root, sid, marker = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])

    def change(record):
        marker.write_text("inside", encoding="utf-8")  # the record is read; hold it
        time.sleep(1.5)
        record["assistant_findings"] = [{"subject": "find_1"}]

    DraftStore(root).transact(sid, change, answer=False)
    """
)


@pytest.mark.slow  # H-faster-python-tests: starts a process (recorded 2026-11-23).
def test_a_side_write_in_another_process_does_not_undo_a_save(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    record = store.create({"topic": "first words"})
    sid = record["session_id"]
    marker = tmp_path / "inside.txt"
    script = tmp_path / "side_writer.py"
    script.write_text(_SIDE_WRITER, encoding="utf-8")

    child = subprocess.Popen([sys.executable, str(script), str(tmp_path), sid, str(marker)])
    try:
        deadline = time.monotonic() + 30
        while not marker.exists():
            assert child.poll() is None, "the side writer ended before it read the record"
            assert time.monotonic() < deadline, "the side writer never read the record"
            time.sleep(0.02)
        # The other process holds the record it read; this save must wait for it, not race it.
        store.save(sid, {"topic": "the researcher's newer words"})
    finally:
        assert child.wait(timeout=60) == 0

    final = store.load(sid)
    # M11b part D: a new draft also carries the two method fields, which the save keeps.
    assert {k: v for k, v in final["draft"].items() if not k.startswith("method_")} == {"topic": "the researcher's newer words"}
    assert final["assistant_findings"] == [{"subject": "find_1"}]


def test_the_lock_is_reentrant_in_one_process(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    sid = store.create({"topic": "t"})["session_id"]

    def change(record):
        # A write made while this thread already holds the draft's lock must not deadlock.
        store.update_side(sid, "origin", lambda _cur: {"kind": "x"})
        record["proposals"] = []

    store.transact(sid, change, answer=False)
    assert store.load(sid)["proposals"] == []


def test_the_lock_file_lives_outside_the_draft_folder(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    sid = store.create({"topic": "t"})["session_id"]
    store.save(sid, {"topic": "u"})
    store.discard(sid)  # a lock file inside the folder would keep it open on Windows
    assert not (tmp_path / ".drafts" / sid).exists()
    assert [d["session_id"] for d in store.listing()] == []
