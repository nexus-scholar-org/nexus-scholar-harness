"""The search's HTTP cache lives under SCHOLAR_CACHE_DIR, never in the starting folder (M13 Part A).

Found in the Browser pane on the installed app (2026-11-24): its engine runs in
the user's settings folder, which has no `.cache`. hishel's default storage is
`.cache/hishel` in the current folder, made without `exist_ok`, so the
discovery plan's first request answered 500 (`FileNotFoundError`, then
`FileExistsError` when several clients were built at once).
"""

from __future__ import annotations

import threading

from scholar_search import http_client
from scholar_search.http_client import AcademicHttpClient


def test_clients_built_at_once_in_a_fresh_folder_use_the_configured_cache(tmp_path, monkeypatch):
    start = tmp_path / "settings-folder"
    start.mkdir()
    monkeypatch.chdir(start)
    monkeypatch.setattr(http_client.settings, "cache_dir", tmp_path / "user-cache" / "search")
    monkeypatch.setattr(http_client.settings, "http_cache", True)

    errors: list[BaseException] = []
    gate = threading.Barrier(8)

    def build() -> None:
        try:
            gate.wait()
            AcademicHttpClient(name="test", rate_limit=10.0)
        except BaseException as exc:  # noqa: BLE001 - collected for the assertion
            errors.append(exc)

    threads = [threading.Thread(target=build) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert errors == []
    assert not (start / ".cache").exists(), "the cache was made in the folder the process started in"
    assert (tmp_path / "user-cache" / "search" / "scholar_cache").is_dir()
