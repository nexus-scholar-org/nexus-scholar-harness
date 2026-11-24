"""Build the Windows bundle and, optionally, its installer (M13 Part W).

    python packaging/windows/build.py --wheel dist/nexus_scholar-<v>-py3-none-any.whl \
        [--work C:\\nsb] [--out dist/windows] [--installer] [--iscc "C:\\...\\ISCC.exe"]

1. A throw-away environment (`uv venv`, Python 3.12) gets the wheel with its
   `ai` and `pdf` extras and PyInstaller; the project's own environment is
   never used (the researcher's answer to Q12 and to Part W's question 2).
2. PyInstaller builds the one-folder bundle from `nexus-scholar.spec`.
3. With `--installer`, Inno Setup compiles `nexus-scholar.iss` into
   `NexusScholar-<version>-setup.exe`. The researcher chose to build the
   installer on GitHub's Windows runner only; locally the bundle is enough.

The work folder should have a short path: Windows refuses paths over 260
characters, and a bundle is deep (the trial build's first failure).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = "3.12"
#: The PyInstaller the bundle is built with; raised on purpose, never floating.
PYINSTALLER = "pyinstaller==6.22.3"
_VERSION = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?(?:(a|b|rc)(\d+))?(?:\.dev(\d+))?$")
_STAGE = {"a": 1000, "b": 2000, "rc": 3000}


def version_key(version: str) -> int:
    """A number that orders versions as PEP 440 does, for the installer's downgrade check.

    ``1.1.0b7`` < ``1.1.0rc1`` < ``1.1.0`` < ``1.1.1.dev1`` < ``1.1.1``. Inno Setup
    compares the installed key with its own, so it needs one integer.
    """
    match = _VERSION.match(version.strip())
    if not match:
        raise ValueError(f"not a version this build knows how to order: {version!r}")
    major, minor, patch, stage, number, dev = match.groups()
    if stage:
        step = _STAGE[stage] + int(number)
    elif dev is not None:
        step = int(dev)  # a development build comes before every pre-release of its version
    else:
        step = 9999
    if stage and dev is not None:
        raise ValueError(f"a development build of a pre-release is not supported: {version!r}")
    return (int(major) * 1000 + int(minor)) * 10**8 + int(patch or 0) * 10**4 + step


def wheel_version(wheel: Path) -> str:
    """The version in a wheel's file name (`nexus_scholar-<version>-py3-none-any.whl`)."""
    parts = wheel.name.split("-")
    if len(parts) < 2 or not wheel.name.endswith(".whl"):
        raise ValueError(f"not a wheel file name: {wheel.name}")
    return parts[1]


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, **kwargs)


def build_bundle(wheel: Path, work: Path, out: Path) -> Path:
    venv = work / "venv"
    if venv.exists():
        shutil.rmtree(venv)
    run(["uv", "venv", "--python", PYTHON, str(venv)])
    python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    run(["uv", "pip", "install", "--python", str(python), f"{wheel.resolve()}[ai,pdf]", PYINSTALLER])
    dist = out / "bundle"
    run([str(python), "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(dist),
         "--workpath", str(work / "pyi"), str(HERE / "nexus-scholar.spec")])
    folder = dist / "Nexus Scholar"
    for program in ("Nexus Scholar.exe", "nexus-scholar-mcp.exe"):
        if sys.platform == "win32" and not (folder / program).is_file():
            raise SystemExit(f"the bundle has no {program}")
    return folder


def build_installer(folder: Path, version: str, out: Path, iscc: str) -> Path:
    # Absolute: Inno Setup reads a relative Source or output folder from the script's own folder.
    folder, out = folder.resolve(), out.resolve()
    run([iscc, f"/DAppVersion={version}", f"/DVersionKey={version_key(version)}", f"/DSourceDir={folder}",
         f"/O{out}", str(HERE / "nexus-scholar.iss")])
    setup = out / f"NexusScholar-{version}-setup.exe"
    if not setup.is_file():
        raise SystemExit(f"Inno Setup made no {setup.name}")
    return setup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=Path("build/windows-work"))
    parser.add_argument("--out", type=Path, default=Path("dist/windows"))
    parser.add_argument("--installer", action="store_true")
    parser.add_argument("--iscc", default="iscc")
    args = parser.parse_args(argv)
    version = wheel_version(args.wheel)
    version_key(version)  # refuse a version the installer could not order, before building
    args.out.mkdir(parents=True, exist_ok=True)
    folder = build_bundle(args.wheel, args.work, args.out)
    print(f"bundle: {folder}")
    if args.installer:
        print(f"installer: {build_installer(folder, version, args.out, args.iscc)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
