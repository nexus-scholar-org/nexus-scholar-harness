# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe of the Windows bundle (M13 Part W; specification §2.2, Q1, Q10).

One folder, two programs: `Nexus Scholar.exe` (windowed: the installed app,
its approval-code window and its folder dialog) and `nexus-scholar-mcp.exe`
(console: the MCP server). Built from the `nexus-scholar` wheel with the `ai`
and `pdf` extras, in a throw-away environment (`packaging/windows/build.py`).

What the trial build of 2026-11-23 taught (specification §8): the app's screens
and skills are data (`scholar_harness_data`) and must be collected with the
package's version information; the parked graph code that pulled in `jedi`
and IPython is gone (H-remove-graph), and they stay excluded so a stray import
cannot bring back thousands of files and the Windows path-length limit.
"""

import os
import sysconfig

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules, copy_metadata

HERE = os.path.dirname(os.path.abspath(SPEC))  # noqa: F821 - PyInstaller defines SPEC
ICON = os.path.join(HERE, "..", "icons", "nexus-scholar.ico")
PACKAGES = ("scholar_harness", "scholar_search", "scholar_pdf", "scholar_protocol", "scholar_agent")
EXCLUDES = ["IPython", "jedi", "parso", "matplotlib", "pytest", "_pytest"]

datas, binaries, hidden = [], [], []
d, b, h = collect_all("scholar_harness_data")  # the app's screens, skills and docs
datas += d
binaries += b
hidden += h
for package in PACKAGES:
    datas += collect_data_files(package)
    hidden += collect_submodules(package)  # routes and drivers imported by name
datas += copy_metadata("nexus-scholar")
# The agent-plugin manifest sits beside the packages in the wheel (genesis.py reads it there).
manifest = os.path.join(sysconfig.get_paths()["purelib"], "nexus_scholar_plugins.json")
if os.path.isfile(manifest):
    datas.append((manifest, "."))


def analysis(entry):
    return Analysis(  # noqa: F821 - PyInstaller names
        [os.path.join(HERE, entry)],
        datas=datas,
        binaries=binaries,
        hiddenimports=hidden,
        excludes=EXCLUDES,
        noarchive=False,
    )


app = analysis("entry_app.py")
mcp = analysis("entry_mcp.py")
app_exe = EXE(  # noqa: F821
    PYZ(app.pure),  # noqa: F821
    app.scripts,
    [],
    exclude_binaries=True,
    name="Nexus Scholar",
    console=False,
    icon=ICON,
)
mcp_exe = EXE(  # noqa: F821
    PYZ(mcp.pure),  # noqa: F821
    mcp.scripts,
    [],
    exclude_binaries=True,
    name="nexus-scholar-mcp",
    console=True,
    icon=ICON,
)
COLLECT(  # noqa: F821
    app_exe,
    app.binaries,
    app.datas,
    mcp_exe,
    mcp.binaries,
    mcp.datas,
    name="Nexus Scholar",
)
