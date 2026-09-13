"""Grounded-direction parity helper for the inception-agent skill.

Reuses the REAL wizard implementations (``scholar_harness.inception``
``_grounded_directions_for_terms`` / ``_grounded_default_concepts``) so the
chat-driven flow proposes exactly the directions the ``--grounded`` wizard
would -- same >= 2-anchor filter, same ordering (multi-word -> freq ->
lexicographic), same <= 3 cap, and the same P1 behaviour: junk fragments
(numeric/verb/venue-scrape) are filtered and at most one direction per
lexical family is proposed (plural-normalized). No sorting logic is
re-derived here.

Also emits the ``recon_context`` document the wizard writes into the GENESIS
event (anchored_terms derivation mirrors ``_run_grounded_recon``); the calling
agent adds the session lineage (session_id / cache_keys / pool_sizes) from the
MCP replies.

Usage::

  uv run python .agents/skills/inception-agent/scripts/grounded_directions.py \\
      --terms <distilled terms json> --topic "<session topic>" \\
      [--pool <pool json>] [--direction "<validated direction label>"] \\
      [--max-default-concepts N]

Exit codes: 0 ok, 2 bad invocation or unvalidatable selection.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scholar_harness.inception import (
    _grounded_default_concepts,
    _grounded_directions_for_terms,
)


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _distinct_dois(docs: list[dict]) -> list[str]:
    """Distinct, sorted DOIs carried by a probe pool (empty == unanchored)."""
    seen: list[str] = []
    for doc in docs:
        doi = doc.get("doi")
        if doi and doi not in seen:
            seen.append(doi)
    return sorted(seen)


def _qei_note(qei: object) -> str | None:
    if qei is None:
        return None
    try:
        value = float(qei)
    except (TypeError, ValueError):
        return None
    if value <= 0.3:
        return "PASS: pool vocabulary is not dominated by prompt echo (QEI <= 0.3)."
    if value >= 1.0:
        return "PROMPT-ECHO: pure echo (QEI == 1.0) -- require a narrower topic."
    return "PROMPT-ECHO: top taxonomy largely echoes the prompt (QEI > 0.3) -- consider narrowing."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Propose the wizard's grounded directions from a distilled terms artifact."
    )
    parser.add_argument(
        "--terms", required=True, help="Distilled terms JSON (recon_distill terms_path)."
    )
    parser.add_argument("--topic", required=True, help="Session topic (the probe query).")
    parser.add_argument(
        "--pool", default=None, help="Probe pool JSON (for topic-level anchor DOIs)."
    )
    parser.add_argument(
        "--direction",
        default=None,
        help="Validated direction label; emits the recon_context for that direction.",
    )
    parser.add_argument(
        "--max-default-concepts",
        type=int,
        default=None,
        help="Cap default_concepts in recon_context (chat seeding convenience). "
        "None (default) keeps full wizard parity; a rich pool's wizard default "
        "can be hundreds of anchored terms.",
    )
    args = parser.parse_args(argv)

    try:
        terms = _load(args.terms)
    except OSError as exc:
        print(json.dumps({"error": f"cannot read --terms: {exc}"}, indent=2))
        return 2

    directions = _grounded_directions_for_terms(terms)
    out: dict = {"directions": directions, "qei": terms.get("qei")}
    out["qei_note"] = _qei_note(terms.get("qei"))

    if args.direction:
        selected = next((d for d in directions if d["label"] == args.direction), None)
        if selected is None:
            allowed = ", ".join(f'"{d["label"]}"' for d in directions) if directions else "(none)"
            print(json.dumps({"error": f"direction not found; available: {allowed}"}, indent=2))
            return 2
        anchor_dois = list(selected["anchor_dois"])
        validated_concept = selected["concept"]
        topic_dois = _distinct_dois(_load(args.pool).get("docs", [])) if args.pool else []
        anchored_terms: dict[str, list[str]] = {
            args.topic: topic_dois,
            validated_concept: list(anchor_dois),
        }
        for term in terms.get("micro_taxonomy", []):
            if len(term["anchor_dois"]) >= 1:
                anchored_terms.setdefault(term["term"], []).extend(term["anchor_dois"])
        default_concepts = _grounded_default_concepts(terms, validated_concept)
        if args.max_default_concepts is not None:
            default_concepts = default_concepts[: max(0, args.max_default_concepts)]
        out["recon_context"] = {
            "anchor_dois": anchor_dois,
            "direction": selected["label"],
            "concept": validated_concept,
            "default_concepts": default_concepts,
            "anchored_terms": anchored_terms,
        }

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())