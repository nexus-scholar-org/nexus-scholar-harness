"""Generate the nexus-scholar metapackage pins snapshot.

Reads the single source of truth for kit versions
(``.agents/plugins/nexus-scholar/plugins.json``) and emits a byte-deterministic
machine-readable snapshot at ``packaging/nexus-scholar/nexus_scholar_pins.json``
containing, per kit: name, repo, default_rev, console_script.  Never edit the
snapshot by hand; ``--check`` fails CI when the two drift.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_JSON = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"
PINS_JSON = (
    REPO_ROOT / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json"
)

FIELDS = ("name", "repo", "default_rev", "console_script")


def load_manifest() -> dict:
    with PLUGINS_JSON.open(encoding="utf-8") as fh:
        return json.load(fh)


def build_pins(manifest: dict) -> dict:
    """Stable pins payload: kits sorted by name, fixed per-kit key order."""
    kits = [
        {field: plugin[field] for field in FIELDS}
        for plugin in manifest["plugins"]
    ]
    kits.sort(key=lambda kit: kit["name"])
    return {"kits": kits}


def render_pins(manifest: dict) -> bytes:
    payload = build_pins(manifest)
    return json.dumps(payload, indent=2).encode("utf-8") + b"\n"


def write_pins(rendered: bytes) -> None:
    PINS_JSON.parent.mkdir(parents=True, exist_ok=True)
    PINS_JSON.write_bytes(rendered)


def check_pins(rendered: bytes) -> bool:
    if not PINS_JSON.exists():
        return False
    return PINS_JSON.read_bytes() == rendered


def print_diff(existing: bytes, generated: bytes) -> None:
    for line in difflib.unified_diff(
        existing.decode("utf-8").splitlines(keepends=True),
        generated.decode("utf-8").splitlines(keepends=True),
        fromfile=str(PINS_JSON),
        tofile="<generated from plugins.json>",
    ):
        print(line, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate_nexus_scholar_pins",
        description="Write or check the nexus-scholar metapackage pins snapshot.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the existing snapshot to the generated one and exit non-zero on drift.",
    )
    args = parser.parse_args(argv)

    rendered = render_pins(load_manifest())

    if args.check:
        if check_pins(rendered):
            print(f"[OK] {PINS_JSON.relative_to(REPO_ROOT)} is in sync with plugins.json")
            return 0
        existing = PINS_JSON.read_bytes() if PINS_JSON.exists() else b""
        print(
            f"[FAIL] {PINS_JSON.relative_to(REPO_ROOT)} is out of sync with plugins.json:"
        )
        print_diff(existing, rendered)
        return 1

    write_pins(rendered)
    print(
        f"[OK] Wrote {PINS_JSON.relative_to(REPO_ROOT)} "
        f"({len(build_pins(load_manifest())['kits'])} kits)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())