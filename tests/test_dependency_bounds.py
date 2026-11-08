"""The published package resolves to dependencies the app can import.

2026-11-08, after the 1.1.0b3 release: `uv tool install --prerelease allow
nexus-scholar` lets every dependency be a pre-release, so it picked
`httpx 1.0.dev6`, which no longer depends on `httpcore`. `hishel==0.0.32`
(our HTTP cache) imports `httpcore`, so the installed app could not start.
The lock file pinned `httpx 0.28.1`, so the test suite never saw it.

The package now declares what it imports: `httpx` stays below 1.0 (the
API `hishel 0.0.32` is written against) and `httpcore` is a direct dependency.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]


def _requirements() -> dict[str, Requirement]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    return {Requirement(r).name.lower(): Requirement(r) for r in project["dependencies"]}


def test_httpx_stays_below_1_0_even_for_pre_releases() -> None:
    httpx = _requirements()["httpx"]
    assert not httpx.specifier.contains(Version("1.0.dev6"), prereleases=True)
    assert not httpx.specifier.contains(Version("1.0.0"), prereleases=True)
    assert httpx.specifier.contains(Version("0.28.1"))


def test_httpcore_is_declared_because_hishel_imports_it() -> None:
    httpcore = _requirements().get("httpcore")
    assert httpcore is not None, "hishel imports httpcore; declare it, do not rely on httpx bringing it"
    assert httpcore.specifier.contains(Version("1.0.9"))
