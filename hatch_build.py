"""Bundle the Research UI's static export into the wheel (M5-slim).

`npm --prefix apps/research-ui run build:export` writes the export to
`apps/research-ui/.next-export/`; when it is there, the wheel carries it as
`scholar_harness_data/ui`, which `nexus-scholar ui` serves.

A wheel built without the export has no screens, and `nexus-scholar ui` on it
says "no app bundle". So a missing export is a build error by default, naming the
two commands to run. `NEXUS_WHEEL_ALLOW_NO_UI=1` builds the UI-less wheel on
purpose (a machine without Node, or an extension that only needs the MCP server)
and says so on stderr. `NEXUS_WHEEL_REQUIRE_UI=1` (set in CI and release) keeps
the error even when the opt-out is also set, so a published wheel has its UI.
Editable installs (`uv sync`) never need the export.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

UI_EXPORT = Path("apps") / "research-ui" / ".next-export"
UI_TARGET = "scholar_harness_data/ui"
BUILD_UI = "cd apps/research-ui && npm ci && npm run build:export && cd ../.."


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        if self.target_name != "wheel" or version == "editable":
            return
        export = Path(self.root) / UI_EXPORT
        if (export / "en" / "index.html").is_file():
            build_data["force_include"][str(export)] = UI_TARGET
            return
        allowed = os.environ.get("NEXUS_WHEEL_ALLOW_NO_UI") == "1" and os.environ.get("NEXUS_WHEEL_REQUIRE_UI") != "1"
        if allowed:
            print(
                f"WARNING: {UI_EXPORT.as_posix()} has no static export, so this wheel has no UI "
                "(NEXUS_WHEEL_ALLOW_NO_UI=1). `nexus-scholar ui` on it will say it has no app bundle. "
                f"To include the UI: {BUILD_UI}",
                file=sys.stderr,
            )
            return
        raise RuntimeError(
            f"{UI_EXPORT.as_posix()} has no static export, so the wheel would have no UI. "
            f"Build the UI first, from the repository root:\n    {BUILD_UI}\n"
            "then run `uv build --wheel` again. To build a wheel without the UI on purpose, "
            "set NEXUS_WHEEL_ALLOW_NO_UI=1."
        )
