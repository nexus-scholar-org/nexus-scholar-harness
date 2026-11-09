"""Grounded directions from a distilled pool (M0.3, P1; moved here in M4c).

Pure functions shared by the CLI wizard (``inception/grounded.py``), the MCP
tools and the console recon routes, so all three propose the same directions
from the same pool. ``inception/grounded.py`` re-exports them under their old
names.
"""

from __future__ import annotations

import re

# P1 junk filter (16_inception_improvements.md F1/F3): numeric- and venue-
# scrape artifacts and verb-led sentence fragments must never surface as a
# validated direction or a default concept.  Curated from observed distiller
# fragments ("11 kcal mol", "reduces default probability") and venue noise
# ("62nd annual meeting", "computational linguistics volume").
_VENUE_NOISE_TOKENS = frozenset(
    {
        "proceedings",
        "conference",
        "symposium",
        "workshop",
        "meeting",
        "volume",
        "journal",
        "congress",
        "edition",
    }
)
_LEADING_FUNCTIONAL_TOKENS = frozenset(
    {
        "using", "based", "use", "uses", "used",
        "reduces", "reduce", "reduced",
        "improves", "improve", "improved",
        "increases", "increase", "increased",
        "achieves", "achieve", "achieving",
        "provides", "provide", "provided",
        "enables", "enable", "enabled",
        "shows", "show", "demonstrates", "demonstrate",
        "allows", "allow",
        "toward", "towards", "with", "for", "how", "what", "does",
        "under", "during", "between", "from", "on", "in",
        "the", "a", "an", "this", "that",
    }
)


def _is_junk_term_label(label: str | None) -> bool:
    """True for non-direction lexical artifacts (P1 junk filter).

    ``False`` always for terms with leading n-gram numeric prefixes, ordinal
    years/editions, verb-led fragments or venue-scrape tokens, so the
    filters are purely additive: a clean term is never rejected.
    """
    text = (label or "").strip()
    if not text:
        return True
    first = text.split()[0].casefold()
    if re.fullmatch(r"\d+(?:\.\d+)?", first):  # "11 kcal mol"
        return True
    if re.fullmatch(r"\d+(?:st|nd|rd|th)", first):  # "62nd annual meeting"
        return True
    if first in _LEADING_FUNCTIONAL_TOKENS:  # "reduces default probability"
        return True
    return any(tok in text.casefold() for tok in _VENUE_NOISE_TOKENS)


def _family_tokens(term: str) -> set[str]:
    """Plural-normalized token set for family matching (labels stay verbatim).

    ``language model`` vs ``language models`` are the same family, so the
    trailing plural ``-s``/``-es`` is dropped before comparison.  This is the
    only place the surface form is loosened: proposed labels keep their
    exact distiller spelling.
    """
    tokens: set[str] = set()
    for tok in term.casefold().split():
        if len(tok) > 3 and tok.endswith("es"):
            tok = tok[:-2]
        elif len(tok) > 3 and tok.endswith("s"):
            tok = tok[:-1]
        tokens.add(tok)
    return tokens


def _same_direction_family(a: dict, b: dict) -> bool:
    """True when two taxonomy terms are lexical variants of one direction.

    Collision iff they share >= 2 (plural-normalized) tokens -- covers
    ``large language model`` vs ``large language models`` and vs ``vision
    language models`` -- or one term's token set is a subset of the other's
    while sharing >= 1 token (modifier-dropped paraphrases).  A genuinely
    distinct sub-field term such as ``vision-language-action vla models``
    shares only a genus head (``model``) and stays separate, as does
    ``self-regulated learning srl`` (only ``learning`` in common with
    ``learning analytics dashboards``) -- that is the diversity P1 is meant
    to surface.
    """
    ta = _family_tokens(a["term"])
    tb = _family_tokens(b["term"])
    shared = ta & tb
    if len(shared) >= 2:
        return True
    return bool(shared) and (ta <= tb or tb <= ta)


def _select_diverse_directions(candidates: list[dict], limit: int = 3) -> list[dict]:
    """Greedy rank-order selection, at most one direction per term family.

    Deterministic: the relative rank of the input (multi-word desc, freq
    desc, lexicographic) is preserved; a candidate is only *dropped* when it
    duplicates a family already selected.  When no overlaps exist the output
    is exactly the old top-N, so legacy behavior is the default.
    """
    selected: list[dict] = []
    for candidate in candidates:
        if any(_same_direction_family(candidate, s) for s in selected):
            continue
        selected.append(candidate)
        if len(selected) == limit:
            break
    return selected


def _grounded_directions_for_terms(terms: dict) -> list[dict]:
    """Build up to 3 DOI-anchored directions from the distilled micro-taxonomy.

    Every direction carries >= 2 distinct anchor DOIs observed in the pool
    (hard filter: an unanchored term can never be proposed).  P1 applies the
    junk filter first, then diversity capping so lexical variants of one
    family never monopolize the top-3.
    """
    candidates = [
        t
        for t in terms.get("micro_taxonomy", [])
        if len(t["anchor_dois"]) >= 2 and not _is_junk_term_label(t["term"])
    ]
    candidates.sort(key=lambda t: (-len(t["term"].split()), -t["freq"], t["term"]))
    candidates = _select_diverse_directions(candidates)
    directions = [
        {
            "label": t["term"],
            "concept": t["term"],
            "anchor_dois": list(t["anchor_dois"]),
            "detail": f"pool term observed in {len(t['anchor_dois'])} papers",
        }
        for t in candidates[:3]
    ]
    if directions:
        return directions
    dois: list[str] = []
    labels: list[str] = []
    for entry in terms.get("micro_taxonomy", []):
        if _is_junk_term_label(entry["term"]):
            continue
        labels.append(entry["term"])
        for doi in entry["anchor_dois"]:
            if doi not in dois:
                dois.append(doi)
        if len(dois) >= 2:
            break
    if len(dois) >= 2:
        return [
            {
                "label": " ".join(labels)[:80] or "pool vocabulary",
                "concept": labels[0] if labels else "pool vocabulary",
                "anchor_dois": sorted(dois),
                "detail": f"pool vocabulary observed in {len(dois)} papers",
            }
        ]
    return []


def _grounded_default_concepts(terms: dict, validated_concept: str) -> list[str]:
    """Stage-4b "Core search concepts" default in grounded mode (M0.3 DoD 3).

    Built exclusively from pool-anchored taxonomy terms -- :func:`draft_default_concepts`
    is never called in the grounded branch.  The validated direction's concept
    always leads; every remaining taxonomy term carrying >= 2 anchor DOIs
    follows (P1 junk filter applied), multi-word terms first (then frequency,
    then lexicographic).
    """
    defaults: list[str] = []
    seen: set[str] = set()
    if validated_concept:
        defaults.append(validated_concept)
        seen.add(validated_concept)
    others = [
        t
        for t in terms.get("micro_taxonomy", [])
        if (
            t["term"] not in seen
            and len(t["anchor_dois"]) >= 2
            and not _is_junk_term_label(t["term"])  # P1: venue-scrape/noise
        )
    ]
    others.sort(key=lambda t: (-len(t["term"].split()), -t["freq"], t["term"]))
    defaults.extend(t["term"] for t in others)
    return defaults
