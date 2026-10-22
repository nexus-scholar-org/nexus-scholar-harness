"""Generate or verify the claims/v1 citation contract's frozen artifacts.

Comparable in spirit to ``scripts/generate_contract_schemas.py --check`` for
Contract v1: the JSON Schema and the golden fixtures under
``tests/fixtures/claim_citation/`` are all *derived* from the live
``ClaimCitation`` model, so any unexplained change to the contract's
validators, canonicalization, or field set changes the derived bytes and
fails ``--check`` until the change is explicitly regenerated and reviewed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scholar_harness.claims import (
    ClaimCitation,
    citation_canonical_bytes,
    render_schema_files,
)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "src" / "scholar_harness" / "claims" / "schemas"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "claim_citation"

# Golden fixture sources.  Each citation is rendered twice: once as readable
# source JSON and once as the exact canonical bytes produced by the contract.
FIXTURE_SOURCES: dict[str, dict[str, object]] = {
    "valid_citation": {
        "artifact_id": "ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",
        "path": "synthesis/meta_analysis.json",
        "locator": "/results/pooled_effect/risk_ratio",
        "value": 1.42,
    },
    # Differs from the valid citation ONLY in the claimed value: the
    # canonical bytes MUST differ.
    "value_shifted_citation": {
        "artifact_id": "ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",
        "path": "synthesis/meta_analysis.json",
        "locator": "/results/pooled_effect/risk_ratio",
        "value": 1.43,
    },
    # Differs from the valid citation ONLY in the locator token: the
    # canonical bytes MUST differ.
    "locator_shifted_citation": {
        "artifact_id": "ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",
        "path": "synthesis/meta_analysis.json",
        "locator": "/results/pooled_effect/odds_ratio",
        "value": 1.42,
    },
}


def _rejected_inputs() -> tuple[tuple[str, dict[str, object]], ...]:
    """Representative inputs the contract MUST keep rejecting.

    Behavior-level probes: a weakened validator would not necessarily change
    any derived byte, so ``--check`` re-runs these through the model and
    fails if any of them becomes acceptable.
    """

    valid = FIXTURE_SOURCES["valid_citation"]
    return (
        ("path escapes root", {**valid, "path": "../secrets.json"}),
        ("path is absolute", {**valid, "path": "/etc/passwd"}),
        ("path uses backslash", {**valid, "path": "a\\b"}),
        ("path is empty", {**valid, "path": ""}),
        ("path has drive prefix", {**valid, "path": "C:/Windows/x"}),
        ("path non-canonical spelling", {**valid, "path": "a/./b"}),
        ("locator missing slash", {**valid, "locator": "results/pooled"}),
        ("locator invalid escape", {**valid, "locator": "/a/~2b"}),
        ("locator unescaped tilde", {**valid, "locator": "/a/~b"}),
        ("locator dangling escape", {**valid, "locator": "/a/~"}),
        ("locator fragment form", {**valid, "locator": "#/a/b"}),
        ("locator is empty", {**valid, "locator": ""}),
        ("artifact_id empty", {**valid, "artifact_id": ""}),
        ("artifact_id whitespace only", {**valid, "artifact_id": "   "}),
        ("artifact_id ambiguous", {**valid, "artifact_id": "ART-abc def"}),
        ("artifact_id wrong prefix", {**valid, "artifact_id": "art-abc1"}),
        ("value is non-finite", {**valid, "value": float("nan")}),
        ("value unverifiable kind", {**valid, "value": {1, 2}}),
        ("value carries non-string key", {**valid, "value": {1: "x"}}),
        ("citation has a fifth field", {**valid, "confidence": 0.9}),
    )


def build_expected() -> dict[Path, bytes]:
    """Return every generated file mapped to its exact expected bytes."""

    expected: dict[Path, bytes] = {}
    for filename, content in render_schema_files().items():
        expected[SCHEMA_DIR / filename] = content.encode("utf-8")
    for stem, payload in FIXTURE_SOURCES.items():
        source = (
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        )
        expected[FIXTURE_DIR / f"{stem}.json"] = source.encode("utf-8")
        citation = ClaimCitation.model_validate(payload)
        expected[FIXTURE_DIR / f"{stem}.canonical.json"] = citation_canonical_bytes(
            citation
        )
    return expected


def _probe_rejections() -> list[str]:
    messages: list[str] = []
    for label, payload in _rejected_inputs():
        try:
            ClaimCitation.model_validate(payload)
        except ValueError:
            continue
        messages.append(f"contract accepts an input it must reject: {label}")
    return messages


def generate(*, check: bool = False) -> list[str]:
    """Write generated artifacts, or return drift messages in check mode."""

    messages: list[str] = []
    messages.extend(_probe_rejections())
    try:
        expected = build_expected()
    except ValueError as error:
        messages.append(f"contract no longer accepts its own golden fixtures: {error}")
        return messages

    known = {".gitkeep"}
    for directory in (SCHEMA_DIR, FIXTURE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        known_files = {
            path.name for path in expected if path.parent == directory
        } | known
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.name not in known_files:
                messages.append(f"unexpected generated file: {path.relative_to(ROOT)}")

    for path, content in sorted(expected.items(), key=lambda item: str(item[0])):
        if check:
            actual = path.read_bytes() if path.is_file() else None
            if actual != content:
                messages.append(f"stale or missing: {path.relative_to(ROOT)}")
        else:
            path.write_bytes(content)

    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail when generated files drift"
    )
    args = parser.parse_args()
    messages = generate(check=args.check)
    if messages:
        print("\n".join(messages))
        return 1
    if not args.check:
        print(
            "Generated claim citation contract artifacts under "
            f"{SCHEMA_DIR} and {FIXTURE_DIR}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
