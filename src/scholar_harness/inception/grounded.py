from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import UTC, datetime

import typer
from rich.panel import Panel

from ..recon.engine import ReconEngine
from .display import console
from .intent import ConceptDraft, draft_default_concepts

# We need to import distill_pool and TOPIC_COHERENCE_TOP3_SHARE
from ..recon.distiller import distill_pool
from ..recon.gates import TOPIC_COHERENCE_TOP3_SHARE

# ---------------------------------------------------------------------------
# Grounded recon loop (--grounded): Step 2 probe -> Step 3 distill -> Step 4
# direction proposal + validation, inserted between Stage 1 and Stage 2.
# ---------------------------------------------------------------------------

_DELTA_PROBE_CHOICE = "__delta_probe__"

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


def _present_grounded_directions(terms: dict, directions: list[dict]) -> None:
    schools = terms.get("schools", [])
    if schools:
        console.print(
            "[bold]Observed sub-schools in the pool:[/bold] "
            + ", ".join(f"{s['label']} ({s['n']})" for s in schools)
        )
    for i, d in enumerate(directions, start=1):
        body = f"[bold]{d['label']}[/bold]\n{d['detail']}\n\n[bold]Citation anchors:[/bold]"
        for doi in d["anchor_dois"]:
            body += f"\n  \u2022 {doi}"
        console.print(Panel.fit(body, title=f"Grounded Direction {i}", border_style="green"))


def _present_pool_assessment(pool_size: int, terms: dict) -> None:
    """Advisory pool-qa panel shown before directions (P5 + P2; additive).

    Computed from the two recon admission gates
    (``scholar_harness.recon.gates``) and printed only when there is
    something non-obvious to say.  It never aborts: the human remains the
    final gate in the interactive wizard, and in headless mode these notes
    are informational.
    """
    from ..recon.gates import (
        TOPIC_COHERENCE_TOP3_SHARE,
        compute_pool_sufficiency,
        compute_topic_purity,
    )

    suff = compute_pool_sufficiency(pool_size)
    purity = compute_topic_purity(terms.get("topics") or [])
    notes: list[str] = []
    if not suff["sufficient"]:
        notes.append(
            f"thin pool ({suff['n_docs']} docs < {suff['threshold']}): proposed "
            "directions may be fragmentary -- raise the probe limit or run a "
            "delta probe before validating."
        )
    if purity["label"] == "indeterminate":
        notes.append(
            "no OpenAlex topics: topical coherence is indeterminate (treat "
            "purity as unknown, not absent)."
        )
    elif purity["label"] == "fragmented":
        notes.append(
            f"topically fragmented (top-3 topic share {purity['purity']:.2f} < "
            f"{purity['threshold']:.2f}): the pool spans several subfields."
        )
    qei = terms.get("qei")
    if (
        qei is not None
        and purity["label"] == "coherent"
        and qei > TOPIC_COHERENCE_TOP3_SHARE
    ):
        notes.append(
            "QEI high on a topically coherent pool: high echo here reflects a "
            "well-scoped seed, not poor inquiry -- do not reject on QEI alone."
        )
    if notes:
        console.print("[bold]Pool assessment:[/bold] " + " ".join(notes))


def _run_grounded_recon(
    responder: Responder,
    topic: str,
    recon_engine: ReconEngine | None = None,
    auto_select: bool = False,
    direction_id: int | None = None,
) -> dict | None:
    """Steps 2-4 of the grounding lifecycle for one session (--grounded).

    Probes the topic, distills the pool, presents <= 3 DOI-anchored directions,
    lets the researcher validate one (optionally after a single delta probe)
    and returns the session ``recon_context``.

    ``recon_context`` additionally carries ``default_concepts`` (the pool-anchored
    Stage-4b prompt default, M0.3 DoD 3) and ``anchored_terms`` (the session's
    anchored-term map: every term with literature evidence, term -> anchor DOIs).

    Hard contract: when the pool yields no >= 2-anchor direction, the wizard
    aborts with ``typer.Exit`` -- there is no warn-and-continue path, because
    emitting unanchored concepts would violate M0.3 DoD 3.

    Headless mode (M0.7 T7.8): ``auto_select=True`` picks the first (most
    anchored) direction; ``direction_id`` picks a specific 1-based direction.
    Either flag bypasses the interactive prompt, so a script/CI/agent run in a
    subshell never blocks on terminal input.  The interactive gate remains the
    default.
    """
    from ..recon.distiller import distill_pool

    engine = recon_engine if recon_engine is not None else ReconEngine()
    session_id = uuid.uuid4().hex[:12]
    cache_keys: list[str] = []
    pool_sizes: list[int] = []
    anchor_dois: list[str] = []

    def probe_and_read(query: str) -> dict:
        pool_path, _n = asyncio.run(engine.probe(query))
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        cache_keys.append(str(pool.get("cache_key") or ""))
        pool_sizes.append(len(pool.get("docs", [])))
        return {"pool": pool, "terms": distill_pool(pool, query_text=query)}

    data = probe_and_read(topic)
    directions = _grounded_directions_for_terms(data["terms"])
    if not directions:
        raise typer.Exit(
            "No literature evidence was found under this topic (no direction with "
            ">= 2 citation anchors could be formed from the probe pool). Refine "
            "the topic or run inception without --grounded."
        )

    topic_dois: list[str] = []
    for doc in data["pool"].get("docs", []):
        doi = doc.get("doi")
        if doi and doi not in topic_dois:
            topic_dois.append(doi)
    topic_dois.sort()

    delta_allowed = True
    while True:
        _present_pool_assessment(
            pool_sizes[-1] if pool_sizes else 0, data["terms"]
        )
        _present_grounded_directions(data["terms"], directions)
        choices = [
            (d["label"], f"{len(d['anchor_dois'])} anchor papers") for d in directions
        ]
        if delta_allowed:
            choices.append((_DELTA_PROBE_CHOICE, "Run one refined delta probe"))
        if auto_select or direction_id is not None:
            idx = (direction_id - 1) if direction_id is not None else 0
            if idx < 0 or idx >= len(directions):
                raise typer.Exit(
                    f"Direction {direction_id} out of range (1-{len(directions)}); "
                    "nothing was emitted."
                )
            pick = directions[idx]["label"]
        else:
            pick = responder.choice(
                "Select the grounded research direction to pursue",
                choices,
                default=directions[0]["label"],
            )
        if pick == _DELTA_PROBE_CHOICE:
            target = responder.choice(
                "Which direction should the delta probe refine?",
                [(d["label"], f"{len(d['anchor_dois'])} anchor papers") for d in directions],
                default=directions[0]["label"],
            )
            delta = probe_and_read(target)
            delta_directions = _grounded_directions_for_terms(delta["terms"])
            if delta_directions:
                directions = delta_directions
                data = delta
            delta_allowed = False
            continue
        selected = next((d for d in directions if d["label"] == pick), None)
        if selected is None:
            continue
        anchor_dois = list(selected["anchor_dois"])
        validated_concept = selected["concept"]
        # Session anchored-term map: topic + validated direction are already
        # anchored (never re-probed later); pool taxonomy terms with >= 1
        # anchor DOI are evidenced in the pool and count as anchored too.
        anchored_terms = {
            topic: topic_dois,
            validated_concept: list(selected["anchor_dois"]),
        }
        for t in data["terms"].get("micro_taxonomy", []):
            if len(t["anchor_dois"]) >= 1:
                anchored_terms.setdefault(t["term"], []).extend(t["anchor_dois"])
        return {
            "session_id": session_id,
            "cache_keys": cache_keys,
            "pool_sizes": pool_sizes,
            "anchor_dois": anchor_dois,
            "direction": selected["label"],
            "concept": validated_concept,
            "default_concepts": _grounded_default_concepts(
                data["terms"], validated_concept
            ),
            "anchored_terms": anchored_terms,
        }


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


_GROUNDED_PROBE_BUDGET = 3


def _pool_anchor_dois(pool: dict) -> list[str]:
    """Distinct DOIs carried by a probe pool (sorted; empty == unanchored)."""
    dois: list[str] = []
    for doc in pool.get("docs", []):
        doi = doc.get("doi")
        if doi and doi not in dois:
            dois.append(doi)
    return sorted(dois)


def _enforce_grounded_anchors(
    concepts: list[ConceptDraft],
    recon_context: dict,
    recon_engine: ReconEngine,
) -> dict:
    """Step-5 delta-probe enforcement (03_lifecycle.md Step 5; M0.3 DoD 3).

    Every concept/synonym that would enter ``core_concepts`` in grounded mode
    must already sit in the session's anchored-term map or earn its anchors
    through a bounded supplementary probe.  A synonym that still yields zero
    anchors is dropped with a yellow warning; a concept that still yields zero
    anchors (or cannot be probed within the budget) aborts the wizard with
    ``typer.Exit`` -- nothing unanchored is ever emitted.
    """
    anchored_terms = dict(recon_context.get("anchored_terms") or {})
    cache_keys: list[str] = recon_context.get("cache_keys", [])
    pool_sizes: list[int] = recon_context.get("pool_sizes", [])
    probes_used = 0

    def probe(term: str) -> list[str]:
        nonlocal probes_used
        probes_used += 1
        pool_path, _n = asyncio.run(recon_engine.probe(term))
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        cache_keys.append(str(pool.get("cache_key") or ""))
        pool_sizes.append(len(pool.get("docs", [])))
        return _pool_anchor_dois(pool)

    def budget_left() -> bool:
        return probes_used < _GROUNDED_PROBE_BUDGET

    def no_evidence_exit(term: str) -> typer.Exit:
        return typer.Exit(
            f"Concept '{term}' has no literature evidence; refine it or run "
            "inception without --grounded. Nothing was emitted."
        )

    for draft in concepts:
        if draft.concept not in anchored_terms:
            if not budget_left():
                raise no_evidence_exit(draft.concept)
            dois = probe(draft.concept)
            if not dois:
                raise no_evidence_exit(draft.concept)
            anchored_terms[draft.concept] = dois
        kept: list[str] = []
        for synonym in draft.synonyms:
            if synonym in anchored_terms:
                kept.append(synonym)
                continue
            if not budget_left():
                console.print(
                    f"[yellow]\u26a0 probe budget exceeded; '{synonym}' has no confirmed "
                    f"literature evidence, removed as a search synonym.[/yellow]"
                )
                continue
            dois = probe(synonym)
            if dois:
                anchored_terms[synonym] = dois
                kept.append(synonym)
            else:
                console.print(
                    f"[yellow]\u26a0 '{synonym}' has no literature evidence under probe; "
                    f"removed as a search synonym.[/yellow]"
                )
        draft.synonyms = kept

    # Belt-and-suspenders: never ship a concept that is still unanchored.
    for draft in concepts:
        if draft.concept not in anchored_terms:
            raise no_evidence_exit(draft.concept)
    recon_context["anchored_terms"] = anchored_terms
    return recon_context


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()




