"""Bundle the Research UI's static export into the wheel (M5-slim).

`npm --prefix apps/research-ui run build:static` writes the export to
`apps/research-ui/.next-static/`; when it is there, the wheel carries it as
`scholar_harness_data/ui`, which `nexus-scholar ui` serves. A wheel built
without it (no Node on the machine) still works and has no UI.
`NEXUS_WHEEL_REQUIRE_UI=1` (set in CI and release) turns a missing export into a
build error, so a published wheel always has its UI.
"""

from __future__ import annotations

import os
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

UI_EXPORT = Path("apps") / "research-ui" / ".next-static"
UI_TARGET = "scholar_harness_data/ui"


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        if self.target_name != "wheel" or version == "editable":
            return
        export = Path(self.root) / UI_EXPORT
        if (export / "en" / "index.html").is_file():
            build_data["force_include"][str(export)] = UI_TARGET
        elif os.environ.get("NEXUS_WHEEL_REQUIRE_UI") == "1":
            raise RuntimeError(
                f"{UI_EXPORT} has no static export; run `npm --prefix apps/research-ui run build:static` first"
            )
