from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.panel import Panel

from ..recon.engine import ReconEngine
from ..recon.session import ReconRefused, ReconSessions, term_evidence
from .display import console
from .drafts import new_session_id
from .intent import ConceptDraft, draft_default_concepts
from ..recon.directions import (  # noqa: F401 - re-exported under the old names
    _LEADING_FUNCTIONAL_TOKENS,
    _VENUE_NOISE_TOKENS,
    _family_tokens,
    _grounded_default_concepts,
    _grounded_directions_for_terms,
    _is_junk_term_label,
    _same_direction_family,
    _select_diverse_directions,
)

# We need to import distill_pool and TOPIC_COHERENCE_TOP3_SHARE
from ..recon.distiller import distill_pool
from ..recon.gates import TOPIC_COHERENCE_TOP3_SHARE

if TYPE_CHECKING:
    from .wizard import Responder

# ---------------------------------------------------------------------------
# Grounded recon loop (--grounded): Step 2 probe -> Step 3 distill -> Step 4
# direction proposal + validation, inserted between Stage 1 and Stage 2.
# ---------------------------------------------------------------------------

# Shown verbatim in the direction list, so it reads as an action, not a token.
_DELTA_PROBE_CHOICE = "Search again, narrower"

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
    engine = recon_engine if recon_engine is not None else ReconEngine()
    # M4c: the wizard records its probes in the recon session store the MCP
    # tools and the console use, under one rec_<hex> id.
    sessions = ReconSessions(engine=engine)
    session_id = new_session_id()  # M4a: one id format with the drafts and MCP recon
    cache_keys: list[str] = []
    pool_sizes: list[int] = []
    pool_created_at: list[str] = []
    pool_fingerprints: list[str] = []
    anchor_dois: list[str] = []
    evidence: dict[str, dict] = {}

    def probe_and_read(query: str, purpose: str = "topic") -> dict:
        try:
            record = asyncio.run(
                sessions.probe(query, session_id=session_id, topic=topic, purpose=purpose)
            )
        except ReconRefused as exc:
            raise typer.Exit(f"{exc.code}: {exc.message}") from exc
        pool = json.loads(Path(record["pool_path"]).read_text(encoding="utf-8"))
        _note_pool(record)
        cache_keys.append(record["cache_key"])
        pool_sizes.append(record["n_docs"])
        pool_created_at.append(str(record["created_at"] or ""))
        pool_fingerprints.append(record["fingerprint"])
        return {"pool": pool, "terms": distill_pool(pool, query_text=query)}

    data = probe_and_read(topic)
    directions = _grounded_directions_for_terms(data["terms"])
    if not directions:
        raise typer.Exit(
            "No literature evidence was found under this topic (no direction with "
            ">= 2 citation anchors could be formed from the probe pool). Refine "
            "the topic or run inception without --grounded."
        )

    # INC-21: the topic is anchored only on records that contain it.
    evidence[topic] = term_evidence(data["pool"], topic)
    topic_dois = evidence[topic]["anchor_dois"]

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
            choices.append((_DELTA_PROBE_CHOICE, "one refined delta probe, 1 left"))
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
            delta = probe_and_read(target, purpose="narrower")
            delta_directions = _grounded_directions_for_terms(delta["terms"])
            if delta_directions:
                directions = delta_directions
                data = delta
                console.print(
                    f"[bold]Narrower search for '{target}' found "
                    f"{len(delta_directions)} direction(s).[/bold]"
                )
            else:
                console.print(
                    f"[yellow]⚠ Narrower search for '{target}' found no direction "
                    "with >= 2 citation anchors; showing the original directions.[/yellow]"
                )
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
        anchored_terms: dict[str, list[str]] = {}
        if topic_dois:
            anchored_terms[topic] = list(topic_dois)
        anchored_terms[validated_concept] = list(selected["anchor_dois"])
        for t in data["terms"].get("micro_taxonomy", []):
            if len(t["anchor_dois"]) >= 1:
                anchored_terms.setdefault(t["term"], []).extend(t["anchor_dois"])
        evidence[validated_concept] = term_evidence(data["pool"], validated_concept)
        return {
            "session_id": session_id,
            "cache_keys": cache_keys,
            "pool_sizes": pool_sizes,
            # INC-09: when each pool was made, and which pool the direction came from.
            "pool_created_at": pool_created_at,
            "pool_fingerprints": pool_fingerprints,
            "anchor_dois": anchor_dois,
            "direction": selected["label"],
            "concept": validated_concept,
            "default_concepts": _grounded_default_concepts(
                data["terms"], validated_concept
            ),
            "anchored_terms": anchored_terms,
            # INC-21: records returned (hits) apart from records containing the term.
            "term_evidence": evidence,
        }


_GROUNDED_PROBE_BUDGET = 3


def _note_pool(record: dict) -> None:
    """Say when a probe answered only in part or not at all (INC-09)."""
    failed = [leg["provider"] for leg in record.get("legs") or [] if leg.get("status") == "failed"]
    if failed:
        console.print(
            f"[yellow]\u26a0 {', '.join(failed)} did not answer; this pool is partial and was not cached.[/yellow]"
        )
    elif record.get("status") == "empty":
        console.print("[yellow]\u26a0 The search found no papers; nothing was cached.[/yellow]")
    elif record.get("served_from_cache"):
        console.print(f"[dim]Pool from the cache, made {record.get('created_at')}.[/dim]")


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
    cache_keys: list[str] = recon_context.setdefault("cache_keys", [])
    pool_sizes: list[int] = recon_context.setdefault("pool_sizes", [])
    pool_created_at: list[str] = recon_context.setdefault("pool_created_at", [])
    evidence: dict[str, dict] = recon_context.setdefault("term_evidence", {})
    sessions = ReconSessions(engine=recon_engine)
    session_id = recon_context.get("session_id") or new_session_id()
    probes_used = 0

    def probe(term: str) -> list[str]:
        """INC-21: a term's anchors are the probed records that contain it."""
        nonlocal probes_used
        probes_used += 1
        try:
            record = asyncio.run(sessions.probe(term, session_id=session_id, purpose="concept"))
        except ReconRefused as exc:
            raise typer.Exit(f"{exc.code}: {exc.message}") from exc
        pool = json.loads(Path(record["pool_path"]).read_text(encoding="utf-8"))
        _note_pool(record)
        cache_keys.append(record["cache_key"])
        pool_sizes.append(record["n_docs"])
        pool_created_at.append(str(record["created_at"] or ""))
        evidence[term] = term_evidence(pool, term)
        return evidence[term]["anchor_dois"]

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




