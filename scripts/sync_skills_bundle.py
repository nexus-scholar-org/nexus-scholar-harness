"""Mirror canonical `.agents/skills/<name>` trees into the nexus-scholar plugin bundle.

Canonical-source rule (`specs/inception-ecosystem/03_skill_tree_and_plugin_distribution.md`):
`.agents/skills/` is always edited first; this script makes the bundle byte-identical
for every canonical skill **except** the intentional exclusions below (mirror scope
table, spec §3.2: `scholar-*-kit` = yes, `pull-request-gate` = no) and reports
pre-existing drift.

Usage:
    uv run python scripts/sync_skills_bundle.py [--check] [SKILL ...]
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / ".agents" / "skills"
BUNDLE = ROOT / ".agents" / "plugins" / "nexus-scholar" / "skills"

# Intentional exclusions (spec §3.2 mirror-scope table): repo-policy enforcement only.
EXCLUDED = ("pull-request-gate",)


def _rel_files(root: Path) -> list[Path]:
    rels: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            rels.append(p.relative_to(root))
    return sorted(rels)


def _same_tree(a: Path, b: Path) -> bool:
    rel_a, rel_b = _rel_files(a), _rel_files(b)
    if rel_a != rel_b:
        return False
    return all(filecmp.cmp(a / rel, b / rel, shallow=False) for rel in rel_a)


def sync_skill(name: str, check: bool) -> bool:
    src = CANONICAL / name
    dst = BUNDLE / name
    if not src.is_dir():
        print(f"SKIP  {name}: canonical missing")
        return True
    drifted = not (dst.is_dir() and _same_tree(src, dst))
    if check:
        print(f"{'OK  ' if not drifted else 'DIFF'}  {name}")
        return not drifted
    if drifted:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"SYNC  {name}")
    else:
        print(f"SYNC  {name} (already identical)")
    return True


def main() -> int:
    for root in (CANONICAL, BUNDLE):
        for child in root.rglob("__pycache__"):
            shutil.rmtree(child, ignore_errors=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="report drift without copying"
    )
    parser.add_argument(
        "skills", nargs="*",
        default=sorted(name for name in os.listdir(CANONICAL) if name not in EXCLUDED),
        help="skill names to sync",
    )
    args = parser.parse_args()
    ok = all(sync_skill(name, args.check) for name in args.skills)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())