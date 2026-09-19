"""Generate or verify the bundled Nexus Scholar contract-v1 schema catalog."""

from __future__ import annotations

import argparse
from pathlib import Path

from scholar_harness.contracts.schema_catalog import render_schema_files

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "src" / "scholar_harness" / "contracts" / "schemas" / "v1"


def generate(*, check: bool = False) -> list[str]:
    """Write generated schemas, or return drift messages in check mode."""

    expected = render_schema_files()
    messages: list[str] = []
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, content in sorted(expected.items()):
        path = OUTPUT_DIR / filename
        if check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != content:
                messages.append(f"stale or missing: {path.relative_to(REPO_ROOT)}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")

    known = set(expected) | {".gitkeep"}
    extras = sorted(
        path for path in OUTPUT_DIR.iterdir() if path.is_file() and path.name not in known
    )
    for path in extras:
        messages.append(f"unexpected generated file: {path.relative_to(REPO_ROOT)}")

    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated files drift")
    args = parser.parse_args()
    messages = generate(check=args.check)
    if messages:
        print("\n".join(messages))
        return 1
    if not args.check:
        print(f"Generated contract schemas in {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
