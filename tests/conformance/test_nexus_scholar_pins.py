"""The nexus-scholar metapackage pins must mirror plugins.json, the single source of truth.

The generated snapshot at ``packaging/nexus-scholar/nexus_scholar_pins.json`` is
CI-enforced in sync with ``.agents/plugins/nexus-scholar/plugins.json`` by
``scripts/generate_nexus_scholar_pins.py --check``.  A byte-different snapshot
here fails the suite, so the two can never drift.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

MANIFEST = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"
PINS_JSON = REPO_ROOT / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json"
CODEGEN = REPO_ROOT / "scripts" / "generate_nexus_scholar_pins.py"

EXPECTED_KITS = 8

# Same full-SHA pattern enforced for plugins.json in test_count_freshness.py.
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Wheel force-include source layout for kit packages: ../../tools/<kit>/src/<pkg>.
KIT_SOURCE_RE = re.compile(r"^\.\./\.\./tools/(scholar-[a-z-]+-kit)/src/([a-z_]+)$")

METAPACKAGE_DIR = REPO_ROOT / "packaging" / "nexus-scholar"


def package_for_kit(kit_name: str) -> str:
    """Map a pinned kit name to its wheel import package.

    ``scholar-protocol-kit`` -> ``scholar_protocol``, mirroring the top-level
    package dir each kit ships under ``tools/<kit>/src/`` and that the wheel's
    ``force-include`` maps to.
    """
    return kit_name.removesuffix("-kit").replace("-", "_")


def _load_codegen():
    spec = importlib.util.spec_from_file_location(
        "_nexus_scholar_pins_codegen", CODEGEN
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pins_reflect_plugins_manifest_exactly():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pins = json.loads(PINS_JSON.read_text(encoding="utf-8"))
    assert len(manifest["plugins"]) == EXPECTED_KITS
    assert len(pins["kits"]) == EXPECTED_KITS
    by_name = {pin["name"]: pin for pin in pins["kits"]}
    assert set(by_name) == {plugin["name"] for plugin in manifest["plugins"]}
    for plugin in manifest["plugins"]:
        pin = by_name[plugin["name"]]
        assert pin["repo"] == plugin["repo"]
        assert pin["default_rev"] == plugin["default_rev"]
        assert pin["console_script"] == plugin["console_script"]


def test_pins_default_revs_are_pinned_commits():
    pins = json.loads(PINS_JSON.read_text(encoding="utf-8"))
    unpinned = [
        pin["name"] for pin in pins["kits"] if not FULL_SHA_RE.match(pin["default_rev"])
    ]
    assert not unpinned, f"pins default_rev must be full commit SHAs: {unpinned}"


def test_regenerating_pins_is_byte_identical():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    codegen = _load_codegen()
    assert codegen.render_pins(manifest) == PINS_JSON.read_bytes()


def test_check_subcommand_exits_zero_when_in_sync():
    result = subprocess.run(
        [sys.executable, str(CODEGEN), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _make_pins_repo_mirror(root: Path) -> Path:
    """Mirror the codegen script and its inputs into an isolated repo-shaped tree.

    ``generate_nexus_scholar_pins.py`` resolves its repo root from its own
    ``__file__``, so a copy under ``root`` runs against the copied snapshot —
    the real ``packaging/nexus-scholar/nexus_scholar_pins.json`` is never
    touched, so no restore step is ever needed.
    """
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "generate_nexus_scholar_pins.py").write_bytes(
        CODEGEN.read_bytes()
    )
    plugins_dir = root / ".agents" / "plugins" / "nexus-scholar"
    plugins_dir.mkdir(parents=True)
    (plugins_dir / "plugins.json").write_bytes(MANIFEST.read_bytes())
    (root / "packaging" / "nexus-scholar").mkdir(parents=True)
    return root


def _run_check(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/generate_nexus_scholar_pins.py", "--check"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_subcommand_rejects_corrupted_pins_snapshot(tmp_path):
    """--check must exit non-zero on a tampered snapshot without touching the real one."""
    codegen = _load_codegen()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    correct_bytes = codegen.render_pins(manifest)

    # Sanity: the mirrored tree with the authoritative snapshot reports in sync,
    # proving the corruption below (not the mirror arrangement) triggers the fail.
    sane_repo = _make_pins_repo_mirror(tmp_path / "sane")
    (sane_repo / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json").write_bytes(
        correct_bytes
    )
    sane = _run_check(sane_repo)
    assert sane.returncode == 0, sane.stdout + sane.stderr

    # Negative path: truncate one pinned 40-hex SHA, then re-check the mirror.
    corrupt_repo = _make_pins_repo_mirror(tmp_path / "corrupt")
    corrupt = json.loads(correct_bytes.decode("utf-8"))
    corrupt["kits"][0]["default_rev"] = corrupt["kits"][0]["default_rev"][:-1]
    (corrupt_repo / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json").write_bytes(
        json.dumps(corrupt, indent=2).encode("utf-8")
    )
    rejected = _run_check(corrupt_repo)
    combined = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0, combined
    assert "out of sync" in combined, combined

    # The real checkout snapshot is byte-identical: no mutate, no restore.
    assert PINS_JSON.read_bytes() == correct_bytes


def test_pins_and_wheel_force_include_name_the_same_kits():
    """Pins ↔ force-include: every pinned kit is source-bundled by the wheel, and vice versa.

    ``nexus_scholar_pins.json`` records the kits from plugins.json while the
    metapackage wheel ships kit sources via ``[tool.hatch.build.targets.wheel.force-include]``
    (``../../tools/<kit>/src/<scholar_pkg>``).  Removing a kit from either side
    must fail here.
    """
    pins = json.loads(PINS_JSON.read_text(encoding="utf-8"))
    with (METAPACKAGE_DIR / "pyproject.toml").open("rb") as fh:
        pyproject = tomllib.load(fh)
    force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]

    pinned = {pin["name"]: package_for_kit(pin["name"]) for pin in pins["kits"]}

    bundled: dict[str, str] = {}
    for source, destination in force_include.items():
        match = KIT_SOURCE_RE.match(source)
        if match is None:
            continue  # harness bundle / pins json, not a kit package
        kit_name, package = match.groups()
        expected_package = package_for_kit(kit_name)
        assert package == expected_package, (
            f"{source!r} bundles {package!r}; the {kit_name!r} convention is "
            f"{expected_package!r}"
        )
        assert destination == package, (
            f"force-include {source!r} maps to {destination!r}, expected {package!r}"
        )
        bundled[kit_name] = package

    assert set(bundled) == set(pinned), (
        "pins snapshot and wheel force-include disagree: "
        f"pinned-but-not-bundled={sorted(set(pinned) - set(bundled))} "
        f"bundled-but-not-pinned={sorted(set(bundled) - set(pinned))}"
    )
    for kit_name, package in pinned.items():
        source_dir = REPO_ROOT / "tools" / kit_name / "src" / package
        assert source_dir.is_dir(), (
            f"{source_dir} is missing; the pinned/force-included kit source is gone"
        )