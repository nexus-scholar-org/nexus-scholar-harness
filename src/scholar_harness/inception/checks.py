"""Fixed checks (M10b, ``docs/ux/shared/final/02-checks.md``). No language model.

Each check is arithmetic, a set test or a string test on data the engine
already holds. The engine returns every check with its level, its numbers,
its text keys and one recommended action; the browser renders and computes
nothing. A ``blocker`` exists only where the engine already refuses (its
``refusal`` names the code); a ``warning`` or ``note`` never blocks.

This module holds the shared machinery (the check object, the evidence digest,
dismissals and the list response) and the inception catalogue; the discovery
catalogue is ``scholar_harness.console.discovery_checks``.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.recon.gates import POOL_THIN_FLOOR

from . import steps

#: The workspace's dismissal record (from genesis on).
DISMISSALS_FILE = "audit/check_dismissals.jsonl"
INCEPTION_STEPS = ("scope", "explore", "direction", "shape", "criteria", "review")
DISCOVERY_STEPS = ("plan", "recall", "harvest", "dedup", "report", "handoff")
LEVELS = ("blocker", "warning", "note")

# --- thresholds (engine constants; ⚑ = first values, calibrated before freezing) ---
#: ⚑ The largest share of the pool from one database before ``EXPLORE_SAMPLE_ONE_SOURCE``.
ONE_SOURCE_SHARE = 0.7
ONE_SOURCE_MIN_DOCS = 10
#: ⚑ Fewer recall seeds than this is a note.
SEEDS_FEW = 3
#: The acronym rule of ``CONCEPT_TERM_MISSING``: 2 to 6 capital letters.
ACRONYM = re.compile(r"\b([A-Z]{2,6})s?\b")
TERM_MAX_INSTANCES = 5
#: ⚑ Two or more accepted exclusions with one distinct code.
REASONS_UNIFORM_MIN = 2
#: An own direction occurring in fewer records is not grounded (``grounding.py``).
OWN_DIRECTION_MIN_ANCHORS = 2


def _now() -> str:
    return datetime.now(UTC).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(check_id: str, subject: str, evidence: list[dict[str, Any]]) -> str:
    raw = canonical([check_id, subject, evidence])
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


#: The en sentence of each check (``message``, for logs and the methods record;
#: the browser shows ``checks.<ID>.sentence`` from its own catalogue).
SENTENCES: dict[str, str] = {
    "SCOPE_TOPIC_MISSING": "Your question is empty.",
    "SCOPE_START_YEAR_DEFAULTED": "No start year is set. The first search used {year}.",
    "EXPLORE_DATABASE_EMPTY": "{database} answered with no papers, while others found some.",
    "EXPLORE_DATABASE_FAILED": "{database} did not answer ({code}). The sample is partial.",
    "EXPLORE_SAMPLE_ONE_SOURCE": "{share} of the {n} sample papers came from {database}.",
    "EXPLORE_POOL_THIN": "The sample has only {n} papers. {floor} or more gives steadier suggestions.",
    "EXPLORE_SAMPLE_MOSTLY_LEFT_OUT": "You have left out {k} of {total} sample papers.",
    "EXPLORE_SCOPE_CHANGED": "The sample was searched for an earlier question, years or languages.",
    "DIRECTION_BINDING_STALE": "The direction you chose no longer matches the sample.",
    "DIRECTION_NOT_CHOSEN": "No direction is chosen. The protocol will say it was not grounded.",
    "DIRECTION_OWN_UNGROUNDED": "Your own direction appears in {n} sample papers.",
    "DIRECTION_SEEDS_FEW": "Only {n} recall seeds are kept.",
    "SHAPE_REQUIRED_MISSING": "Still needed: {fields}.",
    "SHAPE_LEXICON_WARNING": "Your question uses words the {lens} lens avoids: {words}.",
    "SHAPE_PLANNED_SIZE_EMPTY": "You have not said how many records you plan to screen.",
    "CONCEPTS_NONE": "You have no concept yet.",
    "CONCEPT_TERM_MISSING": "Your title and questions use {term}, but no concept or synonym does.",
    "CONCEPT_NOT_ANCHORED": "None of the {concept} terms appears in the {n} sample papers.",
    "CONCEPTS_ONE_ONLY": "The search uses one concept only.",
    "CRITERIA_UNDECIDED": "{n} criteria still need your Accept or Drop.",
    "CRITERIA_SIDE_MISSING": "The protocol needs an accepted {side} criterion.",
    "CRITERIA_REASONS_UNIFORM": "All {n} exclusion criteria carry the same reason, {code}.",
    "REVIEW_PROJECT_MISSING": "Still needed: {fields}.",
    "REVIEW_TITLE_NOT_A_FOLDER": "This title cannot name a folder.",
    "REVIEW_COMPILER_REFUSED": "The compiler refused these answers.",
    "REVIEW_TARGET_NOT_WORKSPACE": "A folder with this name exists and is not a workspace.",
    "REVIEW_TARGET_HAS_WORKSPACE": "A workspace with this name exists.",
    "REVIEW_TARGET_HAS_SCREENING": "That workspace has {n} screening decisions.",
    "REVIEW_PROPOSALS_OPEN": "{n} suggestions are still open.",
    "REVIEW_IMPORT_STEP_NOT_OPENED": "Not opened since the import: {steps}.",
    # discovery
    "PLAN_MAILTO_NOT_SET": "The console has no contact address, so no search can start.",
    "PLAN_OPENALEX_KEY_NOT_SET": "OpenAlex is selected and the console has no OpenAlex key.",
    "PLAN_QUERY_TERM_MISSING": "The protocol's title and questions use {term}, but the search query does not.",
    "PLAN_NO_CAP": "No cap is set. Each database is searched up to {ceiling} records.",
    "RECALL_NOT_RUN": "No recall check yet.",
    "RECALL_SEED_MISSED": "No database found {seed}.",
    "RECALL_CHECK_STALE": "This check was made for an earlier protocol.",
    "HARVEST_ABOVE_TARGET": "The harvest fetched {n} records; you planned {min} to {max}.",
    "HARVEST_ABOVE_TARGET.general": "The harvest fetched {n} records, over the general limit of {limit}.",
    "HARVEST_DATABASE_EMPTY": "{database} fetched no records, while others did.",
    "HARVEST_LEG_FAILED": "{database} failed ({code}). The run is partial.",
    "HARVEST_LOWER_BOUND": "{database} stopped at its cap, so its count is a lower bound.",
    "DEDUP_NOT_RUN": "No deduplication has run.",
    "DEDUP_RATE_LOW": "Only {share} of {n} records were merged across {k} databases.",
    "REPORT_METHODS_NOT_REVIEWED": "The methods text is not reviewed.",
    "HANDOFF_PREPARATION_UNFINISHED": "{run} fetched {n} records, but its preparation {state} at {stage}.",
    "HANDOFF_SEARCH_CHANGED": "{run} searched a query or years the protocol no longer has.",
    "HANDOFF_PROTOCOL_CHANGED": "The protocol changed after this search, outside the search itself.",
    "HANDOFF_ABSTRACTS_MISSING": "Only {share} of the works have an abstract.",
    "HANDOFF_ONE_DATABASE_DOMINATES": "{database} found {share} of the works.",
}

#: Catalogue order and each check's owning step (02-checks "The catalogue").
CATALOGUE: dict[str, str] = {
    "SCOPE_TOPIC_MISSING": "scope",
    "SCOPE_START_YEAR_DEFAULTED": "scope",
    "EXPLORE_DATABASE_EMPTY": "explore",
    "EXPLORE_DATABASE_FAILED": "explore",
    "EXPLORE_SAMPLE_ONE_SOURCE": "explore",
    "EXPLORE_POOL_THIN": "explore",
    "EXPLORE_SAMPLE_MOSTLY_LEFT_OUT": "explore",
    "EXPLORE_SCOPE_CHANGED": "explore",
    "DIRECTION_BINDING_STALE": "direction",
    "DIRECTION_NOT_CHOSEN": "direction",
    "DIRECTION_OWN_UNGROUNDED": "direction",
    "DIRECTION_SEEDS_FEW": "direction",
    "SHAPE_REQUIRED_MISSING": "shape",
    "SHAPE_LEXICON_WARNING": "shape",
    "SHAPE_PLANNED_SIZE_EMPTY": "shape",
    "CONCEPTS_NONE": "criteria",
    "CONCEPT_TERM_MISSING": "criteria",
    "CONCEPT_NOT_ANCHORED": "criteria",
    "CONCEPTS_ONE_ONLY": "criteria",
    "CRITERIA_UNDECIDED": "criteria",
    "CRITERIA_SIDE_MISSING": "criteria",
    "CRITERIA_REASONS_UNIFORM": "criteria",
    "REVIEW_PROJECT_MISSING": "review",
    "REVIEW_TITLE_NOT_A_FOLDER": "review",
    "REVIEW_COMPILER_REFUSED": "review",
    "REVIEW_TARGET_NOT_WORKSPACE": "review",
    "REVIEW_TARGET_HAS_WORKSPACE": "review",
    "REVIEW_TARGET_HAS_SCREENING": "review",
    "REVIEW_PROPOSALS_OPEN": "review",
    "REVIEW_IMPORT_STEP_NOT_OPENED": "review",
    # discovery
    "PLAN_MAILTO_NOT_SET": "plan",
    "PLAN_OPENALEX_KEY_NOT_SET": "plan",
    "PLAN_QUERY_TERM_MISSING": "plan",
    "PLAN_NO_CAP": "plan",
    "RECALL_NOT_RUN": "recall",
    "RECALL_SEED_MISSED": "recall",
    "RECALL_CHECK_STALE": "recall",
    "HARVEST_ABOVE_TARGET": "harvest",
    "HARVEST_DATABASE_EMPTY": "harvest",
    "HARVEST_LEG_FAILED": "harvest",
    "HARVEST_LOWER_BOUND": "harvest",
    "DEDUP_NOT_RUN": "dedup",
    "DEDUP_RATE_LOW": "dedup",
    "REPORT_METHODS_NOT_REVIEWED": "report",
    "HANDOFF_PREPARATION_UNFINISHED": "handoff",
    "HANDOFF_SEARCH_CHANGED": "handoff",
    "HANDOFF_PROTOCOL_CHANGED": "handoff",
    "HANDOFF_ABSTRACTS_MISSING": "handoff",
    "HANDOFF_ONE_DATABASE_DOMINATES": "handoff",
}
#: ``PLAN_ESTIMATE_ABOVE_TARGET`` lives on the estimate card only (Part D) and is not served here.
ORDER = {cid: i for i, cid in enumerate(CATALOGUE)}
#: An assistant's finding (M10c): a row of the same object with ``source: "agent"``; its step is its own.
AGENT_CHECK_ID = "ASSISTANT_FINDING"
#: Answered by a confirmation in the gate (06), so never dismissed here.
NOT_DISMISSIBLE = frozenset({"REVIEW_TARGET_HAS_WORKSPACE", "REVIEW_TARGET_HAS_SCREENING"})


class CheckRefused(Exception):
    """A check route refused; console-style ``{code, message, details}``."""

    def __init__(self, code: str, message: str, status: int = 409, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


def check(
    check_id: str,
    level: str,
    *,
    subject: str = "",
    params: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    threshold: dict[str, Any] | None = None,
    action: dict[str, Any],
    refusal: str | None = None,
    sentence: str | None = None,
) -> dict[str, Any]:
    """One check object (02-checks "The check object"); ``sentence`` picks a variant of the en text."""
    params = dict(params or {})
    evidence = list(evidence or [])
    template = SENTENCES[sentence or check_id]
    try:
        message = template.format(**params)
    except (KeyError, IndexError):
        message = template
    key = (sentence or check_id).replace(".", "_")
    return {
        "check_id": check_id,
        "subject": subject,
        "step": CATALOGUE[check_id],
        "level": level,
        "source": "check",
        "message_key": f"checks.{key}.sentence",
        "params": params,
        "message": message,
        "why_key": f"checks.{key}.why",
        "why_params": params,
        "evidence": evidence,
        "threshold": threshold,
        "action": {**action, "label_key": f"checks.{check_id}.action"},
        "refusal": refusal if level == "blocker" else None,
        "dismissible": level != "blocker" and check_id not in NOT_DISMISSIBLE,
        "status": "open",
        "dismissal": None,
        "previously_dismissed": None,
        "evidence_digest": digest(check_id, subject, evidence),
    }


def _field(step: str, field: str) -> dict[str, Any]:
    return {"kind": "field", "step": step, "field": field}


def _step(step: str) -> dict[str, Any]:
    return {"kind": "step", "step": step}


# ---------------------------------------------------------------------------
# Dismissal (02-checks "Dismissal")
# ---------------------------------------------------------------------------


def _last(dismissals: list[dict[str, Any]], check_id: str, subject: str) -> dict[str, Any] | None:
    found = None
    for entry in dismissals or []:
        if entry.get("check_id") == check_id and (entry.get("subject") or "") == subject:
            found = entry
    return found


def with_dismissals(items: list[dict[str, Any]], dismissals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each check's ``status``: dismissed when its last entry dismissed this very digest."""
    for item in items:
        last = _last(dismissals, item["check_id"], item["subject"])
        if not last or last.get("action") != "dismissed" or not item["dismissible"]:
            continue
        stamp = {"reason": last.get("reason") or "", "at": last.get("at")}
        if last.get("evidence_digest") == item["evidence_digest"]:
            item["status"], item["dismissal"] = "dismissed", stamp
        else:
            item["previously_dismissed"] = stamp
    return items


def dismissal_entry(
    items: list[dict[str, Any]], dismissals: list[dict[str, Any]], check_id: str, action: str, *,
    subject: str = "", evidence_digest: str | None = None, reason: str | None = None,
) -> dict[str, Any]:
    """The entry a dismiss or restore appends, or the refusal (02-checks "New refusal codes")."""
    instance = next((c for c in items if c["check_id"] == check_id and c["subject"] == subject), None)
    if (check_id not in CATALOGUE and check_id != AGENT_CHECK_ID) or instance is None:
        raise CheckRefused(
            "CHECK_NOT_FOUND", f"no check {check_id} for {subject!r} now", 404,
            {"check_id": check_id, "subject": subject},
        )
    if action == "restored":
        last = _last(dismissals, check_id, subject)
        if not last or last.get("action") != "dismissed":
            raise CheckRefused("CHECK_NOT_DISMISSED", "this check is not dismissed", 409, {"status": instance["status"]})
        return {
            "check_id": check_id, "subject": subject, "evidence_digest": last.get("evidence_digest"),
            "action": "restored", "reason": "", "at": _now(),
        }
    if not instance["dismissible"]:
        raise CheckRefused(
            "CHECK_NOT_DISMISSIBLE", "this check cannot be dismissed", 409,
            {"level": instance["level"], "refusal": instance["refusal"]},
        )
    text = (reason or "").strip()
    if len(text) > steps.MAX_TEXT_CHARS or (instance["level"] == "warning" and not text):
        raise CheckRefused(
            "CHECK_REASON_REQUIRED", "write a short reason for dismissing a warning", 422,
            {"limit": steps.MAX_TEXT_CHARS, "level": instance["level"]},
        )
    if evidence_digest != instance["evidence_digest"]:
        raise CheckRefused("CHECK_CHANGED", "the data changed since the check was read", 409, {"current": instance})
    return {
        "check_id": check_id, "subject": subject, "evidence_digest": instance["evidence_digest"],
        "action": "dismissed", "reason": text, "at": _now(),
    }


def respond(
    items: list[dict[str, Any]],
    *,
    steps_order: tuple[str, ...],
    step: str | None,
    scope: dict[str, Any],
    waiting: list[dict[str, Any]] | None = None,
    partial: list[dict[str, Any]] | None = None,
    ready: bool | None = None,
) -> dict[str, Any]:
    """The list response: the checks sorted by level then catalogue order, the counts and ``by_step``."""
    rank = {lvl: i for i, lvl in enumerate(LEVELS)}
    items = sorted(items, key=lambda c: (rank[c["level"]], ORDER.get(c["check_id"], 999), c["subject"]))
    waiting = list(waiting or [])
    out: dict[str, Any] = {
        "shape": "checks-v1",
        "scope": scope,
        "computed_at": _now(),
        "sources": ["check", *(["agent"] if any(c.get("source") == "agent" for c in items) else [])],
    }
    by_step = {s: {"blocker": 0, "warning": 0, "note": 0} for s in steps_order}
    for item in items:
        if item["status"] == "open" and item["step"] in by_step:
            by_step[item["step"]][item["level"]] += 1
    if step is not None:
        items = [c for c in items if c["step"] == step]
        waiting = [w for w in waiting if w["step"] == step]
    counts = {lvl: sum(1 for c in items if c["level"] == lvl and c["status"] == "open") for lvl in LEVELS}
    counts["dismissed"] = sum(1 for c in items if c["status"] == "dismissed")
    out.update(checks=items, waiting=waiting, counts=counts, partial=list(partial or []))
    if step is None:
        out["by_step"] = by_step
    if ready is not None:
        out["ready"] = ready
    return out


def _safely(
    items: list[dict[str, Any]], partial: list[dict[str, Any]], check_id: str, fn: Callable[[], list[dict[str, Any]]],
) -> None:
    """Run one check; an unexpected error never hides the others (it is named in ``partial``)."""
    try:
        items.extend(fn())
    except Exception as exc:  # noqa: BLE001 - one broken check must not hide the others
        partial.append({"kind": "check_failed", "check_id": check_id, "error": type(exc).__name__})


# ---------------------------------------------------------------------------
# The inception catalogue
# ---------------------------------------------------------------------------


def _empty(value: Any) -> bool:
    return not (value.strip() if isinstance(value, str) else value)


def _missing(draft: steps.Draft, *fields: str) -> list[str]:
    return [f for f in steps._required(draft, *fields) if _empty(getattr(draft, f))]


def salient_terms(*texts: str) -> list[str]:
    """The terms a term check looks for: all-capitals acronyms of 2 to 6 letters, in order of first use.

    Calibrated on 2026-11-18 over the golden UAV protocols (decision item 27,
    proposed): the spec's second rule, a title word that also occurs in a research
    question, flagged only "reliability" and "generalization" there, the review's
    outcomes rather than its search words, so it was dropped. The acronym rule
    finds the 2026-11-13 case (UAV).
    """
    out: list[str] = []
    for text in texts:
        for match in ACRONYM.finditer(text or ""):
            if match.group(1) not in out:
                out.append(match.group(1))
    return out


def missing_terms(texts: list[str], known: list[str]) -> list[str]:
    """The salient terms of ``texts`` that occur in none of ``known`` (whole words, case-insensitive)."""
    from scholar_harness.recon.session import term_occurs

    found = [t for t in salient_terms(*texts) if not any(term_occurs(t, k) for k in known if k.strip())]
    return found[:TERM_MAX_INSTANCES]


def _term_missing(draft: steps.Draft) -> list[dict[str, Any]]:
    """``CONCEPT_TERM_MISSING``: an acronym of the title, topic and questions in no concept or synonym."""
    known = [t for c in draft.concepts for t in (c.concept, *c.synonyms)]
    return [{"term": t, "concept": _initials_match(t, draft)} for t in missing_terms([draft.title, draft.topic, *draft.rqs], known)]


def _initials_match(term: str, draft: steps.Draft) -> str | None:
    """The concept whose words' initials spell the acronym (UAV and "unmanned aerial vehicle")."""
    if not term.isupper():
        return None
    for concept in draft.concepts:
        words = re.findall(r"[A-Za-z0-9]+", concept.concept)
        if len(words) >= 2 and "".join(w[0] for w in words).upper() == term:
            return concept.concept
    return None


def inception_checks(
    record: dict[str, Any],
    *,
    pool: dict[str, Any] | None = None,
    scope_changes: list[str] | None = None,
    binding: dict[str, Any] | None = None,
    workspaces_root: Path | None = None,
    make_proposal: Callable[..., dict[str, Any]] | None = None,
    sample: dict[str, Any] | None = None,
    raw_pool: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Every inception check of a saved draft record.

    Returns ``(checks, waiting, partial, proposals)``; ``proposals`` are the
    open proposals the checks recommend (recorded by the caller, idempotently).
    ``pool`` is the draft's latest recon pool as the later steps read it (the
    effective pool, M10b Part C), ``scope_changes`` what differs from it,
    ``binding`` the result of ``check_binding`` for a bound draft and
    ``sample`` the sample object of ``recon/sample.py`` (``view``) and
    ``raw_pool`` the pool as stored, whose fingerprint the evidence names
    (review of Part C, finding 3).
    """
    raw = record.get("draft") or {}
    draft = steps.parse_draft(raw)
    items: list[dict[str, Any]] = []
    waiting: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    grounding = record.get("grounding")

    def run(check_id: str, fn: Callable[[], list[dict[str, Any]]]) -> None:
        _safely(items, partial, check_id, fn)

    # Scope
    run("SCOPE_TOPIC_MISSING", lambda: [
        check("SCOPE_TOPIC_MISSING", "blocker", action=_field("scope", "topic"), refusal="DRAFT_INCOMPLETE")
    ] if _empty(draft.topic) else [])
    run("SCOPE_START_YEAR_DEFAULTED", lambda: [
        check("SCOPE_START_YEAR_DEFAULTED", "note", params={"year": 2000},
              evidence=[{"kind": "count", "name": "year", "value": 2000, "unit": "year"}],
              action=_field("scope", "start_year"))
    # H-run-small-fixes (finding 4): the note speaks of "the first search", so only after one.
    ] if draft.start_year is None and pool is not None else [])

    # Explore
    if pool is None:
        for cid in ("EXPLORE_DATABASE_EMPTY", "EXPLORE_DATABASE_FAILED", "EXPLORE_SAMPLE_ONE_SOURCE", "EXPLORE_POOL_THIN",
                    "EXPLORE_SAMPLE_MOSTLY_LEFT_OUT"):
            waiting.append({"check_id": cid, "step": "explore", "needs": "pool"})
    else:
        legs = [leg for leg in pool.get("legs") or [] if isinstance(leg, dict)]
        docs = [d for d in pool.get("docs") or [] if isinstance(d, dict)]
        run("EXPLORE_DATABASE_EMPTY", lambda: _explore_empty(legs, _pool_ev(raw_pool if raw_pool is not None else pool)))
        run("EXPLORE_DATABASE_FAILED", lambda: _explore_failed(legs, _pool_ev(raw_pool if raw_pool is not None else pool)))
        run("EXPLORE_SAMPLE_ONE_SOURCE", lambda: _one_source(docs, legs, _pool_ev(raw_pool if raw_pool is not None else pool)))
        run("EXPLORE_POOL_THIN", lambda: [
            check("EXPLORE_POOL_THIN", "warning", params={"n": len(docs), "floor": POOL_THIN_FLOOR},
                  evidence=[{"kind": "count", "name": "papers", "value": len(docs), "unit": "papers"}, _pool_ev(raw_pool if raw_pool is not None else pool)],
                  threshold={"name": "POOL_THIN_FLOOR", "value": POOL_THIN_FLOOR, "default": POOL_THIN_FLOOR, "unit": "papers"},
                  action=_step("scope"))
        ] if len(docs) < POOL_THIN_FLOOR else [])
        if any(leg.get("status") == "failed" for leg in legs):
            partial.append({
                "kind": "pool_partial",
                "databases": [str(leg.get("provider")) for leg in legs if leg.get("status") == "failed"],
            })
        run("EXPLORE_SAMPLE_MOSTLY_LEFT_OUT", lambda: _mostly_left_out(sample, pool, raw_pool))
    from .grounding import scope_of

    run("EXPLORE_SCOPE_CHANGED", lambda: [
        check("EXPLORE_SCOPE_CHANGED", "warning",
              evidence=[{"kind": "name", "name": "changed", "value": list(scope_changes)},
                        {"kind": "name", "name": "draft_scope", "value": scope_of(draft)}, _pool_ev(raw_pool if raw_pool is not None else pool)],
              action=_step("explore"))
    ] if scope_changes else [])

    # Direction
    run("DIRECTION_BINDING_STALE", lambda: [
        check("DIRECTION_BINDING_STALE", "blocker",
              evidence=[{"kind": "name", "name": "reason", "value": (binding or {}).get("code")}],
              action=_step("direction"), refusal="STALE_BINDING")
    ] if grounding and (binding or {}).get("stale") else [])
    run("DIRECTION_NOT_CHOSEN", lambda: [
        check("DIRECTION_NOT_CHOSEN", "note", action=_step("direction"))
    ] if not grounding or grounding.get("choice") == "none" else [])
    run("DIRECTION_OWN_UNGROUNDED", lambda: _own_ungrounded(grounding))
    run("DIRECTION_SEEDS_FEW", lambda: [
        check("DIRECTION_SEEDS_FEW", "note", params={"n": len(draft.golden_seeds)},
              evidence=[{"kind": "count", "name": "seeds", "value": len(draft.golden_seeds), "unit": "DOIs"}],
              threshold={"name": "SEEDS_FEW", "value": SEEDS_FEW, "default": SEEDS_FEW, "unit": "DOIs"},
              action=_field("direction", "golden_seeds"))
    ] if len(draft.golden_seeds) < SEEDS_FEW else [])

    # Shape
    shape_missing = _missing(draft, "paradigm", "playbook", "unit_of_analysis", "proof", "rqs")
    run("SHAPE_REQUIRED_MISSING", lambda: [
        check("SHAPE_REQUIRED_MISSING", "blocker", params={"fields": ", ".join(shape_missing)},
              evidence=[{"kind": "name", "name": "missing", "value": shape_missing}],
              action=_field("shape", shape_missing[0]), refusal="DRAFT_INCOMPLETE")
    ] if shape_missing else [])
    run("SHAPE_LEXICON_WARNING", lambda: _lexicon(draft))
    run("SHAPE_PLANNED_SIZE_EMPTY", lambda: [
        check("SHAPE_PLANNED_SIZE_EMPTY", "note",
              threshold={"name": "SIZE_WARN_WORKS", "value": 1000, "default": 1000, "unit": "works"},
              action=_field("shape", "pool_max"))
    ] if draft.pool_max is None else [])

    # Concepts and criteria
    run("CONCEPTS_NONE", lambda: [
        check("CONCEPTS_NONE", "blocker", action=_field("criteria", "concepts"), refusal="DRAFT_INCOMPLETE")
    ] if not draft.concepts else [])

    def term_rows() -> list[dict[str, Any]]:
        rows = []
        for found in _term_missing(draft):
            term, concept = found["term"], found["concept"]
            if concept:
                field, op, value = f"concepts[{concept}].synonyms", "add", term
            else:
                field, op, value = "concepts", "add", {"concept": term, "synonyms": []}
            action: dict[str, Any] = _field("criteria", "concepts")
            if make_proposal is not None:
                proposal = make_proposal(
                    source="check:CONCEPT_TERM_MISSING", field=field, op=op, value=value,
                    why=f"Your title and questions use {term}, but no concept or synonym does.",
                    evidence=[{"kind": "check", "check_id": "CONCEPT_TERM_MISSING"}],
                )
                proposals.append(proposal)
                action = {"kind": "proposal", "proposal_id": proposal["proposal_id"]}
            rows.append(check(
                "CONCEPT_TERM_MISSING", "warning", subject=term, params={"term": term},
                evidence=[{"kind": "words", "name": "term", "value": term}], action=action,
            ))
        return rows

    run("CONCEPT_TERM_MISSING", term_rows)
    if pool is None:
        waiting.append({"check_id": "CONCEPT_NOT_ANCHORED", "step": "criteria", "needs": "pool"})
    else:
        run("CONCEPT_NOT_ANCHORED", lambda: _not_anchored(draft, pool, raw_pool))
    run("CONCEPTS_ONE_ONLY", lambda: [
        check("CONCEPTS_ONE_ONLY", "note", action=_field("criteria", "concepts"))
    ] if len(draft.concepts) == 1 else [])
    run("CRITERIA_*", lambda: _criteria_checks(draft))

    # Review
    project_missing = _missing(draft, "title", "lead_researcher")
    run("REVIEW_PROJECT_MISSING", lambda: [
        check("REVIEW_PROJECT_MISSING", "blocker", params={"fields": ", ".join(project_missing)},
              evidence=[{"kind": "name", "name": "missing", "value": project_missing}],
              action=_field("review", project_missing[0]), refusal="DRAFT_INCOMPLETE")
    ] if project_missing else [])
    from .intent import slugify

    slug = slugify(draft.title) if draft.title.strip() else ""
    run("REVIEW_TITLE_NOT_A_FOLDER", lambda: [
        check("REVIEW_TITLE_NOT_A_FOLDER", "blocker", action=_field("review", "title"), refusal="WORKSPACE_TITLE_INVALID")
    ] if draft.title.strip() and not slug else [])
    run("REVIEW_COMPILER_REFUSED", lambda: _compiler(raw))
    if slug and workspaces_root is not None:
        run("REVIEW_TARGET_*", lambda: _target(Path(workspaces_root) / slug))
    run("REVIEW_PROPOSALS_OPEN", lambda: _proposals_open(record))
    run("REVIEW_IMPORT_STEP_NOT_OPENED", lambda: _import_not_opened(record))
    return items, waiting, partial, proposals


def _pool_ev(pool: dict[str, Any] | None) -> dict[str, Any]:
    """The pool a check was computed on: a new search makes a new digest, so its dismissals reopen."""
    from scholar_harness.recon.session import pool_fingerprint

    return {"kind": "name", "name": "pool", "value": pool_fingerprint(pool) if pool else None}


def _mostly_left_out(
    sample: dict[str, Any] | None, pool: dict[str, Any], ev_pool: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """``EXPLORE_SAMPLE_MOSTLY_LEFT_OUT`` (M10b Part C): from the engine's ``sample.recommend``."""
    from scholar_harness.recon.sample import MOSTLY_OFF_TOPIC, SAMPLE_OFFTOPIC_SHARE

    recommend = (sample or {}).get("recommend") or {}
    if MOSTLY_OFF_TOPIC not in (recommend.get("reasons") or []):
        return []
    k = int(sample.get("excluded_in_pool") or 0)
    total = k + int(sample.get("n_docs") or 0)
    return [check(
        "EXPLORE_SAMPLE_MOSTLY_LEFT_OUT", "warning", params={"k": k, "total": total},
        evidence=[{"kind": "count", "name": "left_out", "value": k, "unit": "papers"},
                  {"kind": "count", "name": "papers", "value": total, "unit": "papers"},
                  {"kind": "name", "name": "left_out_keys", "value": sample.get("exclusions_digest")}, _pool_ev(ev_pool if ev_pool is not None else pool)],
        threshold={"name": "SAMPLE_OFFTOPIC_SHARE", "value": SAMPLE_OFFTOPIC_SHARE, "default": SAMPLE_OFFTOPIC_SHARE,
                   "unit": "share"},
        action=_step("scope"),
    )]


def _explore_empty(legs: list[dict[str, Any]], pool_ev: dict[str, Any]) -> list[dict[str, Any]]:
    if not any((leg.get("fetched") or 0) > 0 for leg in legs):
        return []
    return [
        check("EXPLORE_DATABASE_EMPTY", "warning", subject=str(leg.get("provider")),
              params={"database": str(leg.get("provider"))},
              evidence=[{"kind": "count", "name": str(leg.get("provider")), "value": 0, "unit": "records"}, pool_ev],
              threshold={"name": "fetched", "value": 0, "default": 0, "unit": "records"},
              action=_field("scope", "topic"))
        for leg in legs if leg.get("status") != "failed" and (leg.get("fetched") or 0) == 0
    ]


def _explore_failed(legs: list[dict[str, Any]], pool_ev: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        check("EXPLORE_DATABASE_FAILED", "warning", subject=str(leg.get("provider")),
              params={"database": str(leg.get("provider")), "code": str(leg.get("error_code") or "")},
              evidence=[{"kind": "name", "name": "error_code", "value": leg.get("error_code")},
                        {"kind": "name", "name": "key_set", "value": leg.get("key_set")}, pool_ev],
              action=_step("explore"))
        for leg in legs if leg.get("status") == "failed"
    ]


def _one_source(docs: list[dict[str, Any]], legs: list[dict[str, Any]], pool_ev: dict[str, Any]) -> list[dict[str, Any]]:
    if len(legs) < 2 or len(docs) < ONE_SOURCE_MIN_DOCS:
        return []
    tally: dict[str, int] = {}
    for doc in docs:
        tally[str(doc.get("provider"))] = tally.get(str(doc.get("provider")), 0) + 1
    database, top = max(tally.items(), key=lambda kv: (kv[1], kv[0]))
    share = top / len(docs)
    if share <= ONE_SOURCE_SHARE:
        return []
    return [check(
        "EXPLORE_SAMPLE_ONE_SOURCE", "warning",
        params={"share": f"{round(share * 100)}%", "n": len(docs), "database": database},
        evidence=[{"kind": "share", "name": database, "value": round(share, 4)},
                  {"kind": "count", "name": "papers", "value": len(docs), "unit": "papers"}, pool_ev],
        threshold={"name": "ONE_SOURCE_SHARE", "value": ONE_SOURCE_SHARE, "default": ONE_SOURCE_SHARE, "unit": "share"},
        action=_step("explore"),
    )]


def _own_ungrounded(grounding: dict[str, Any] | None) -> list[dict[str, Any]]:
    direction = (grounding or {}).get("direction") or {}
    if not grounding or grounding.get("choice") != "researcher" or direction.get("grounded"):
        return []
    n = int(direction.get("observed_in") or 0)
    return [check(
        "DIRECTION_OWN_UNGROUNDED", "warning", params={"n": n},
        evidence=[{"kind": "count", "name": "observed_in", "value": n, "unit": "papers"},
                  {"kind": "words", "name": "direction", "value": direction.get("label")},
                  {"kind": "name", "name": "pool", "value": ((grounding or {}).get("pool") or {}).get("fingerprint")}],
        threshold={"name": "OWN_DIRECTION_MIN_ANCHORS", "value": OWN_DIRECTION_MIN_ANCHORS,
                   "default": OWN_DIRECTION_MIN_ANCHORS, "unit": "papers"},
        action=_step("direction"),
    )]


def _lexicon(draft: steps.Draft) -> list[dict[str, Any]]:
    from .intent import PARADIGM_PROFILE, enforce_lexicon

    if not draft.paradigm or draft.paradigm not in PARADIGM_PROFILE or _empty(draft.topic):
        return []
    words = enforce_lexicon(draft.paradigm, draft.topic)
    if not words:
        return []
    # ``enforce_lexicon`` answers "Flagged Positivist term: 'x'"; the sentence quotes the terms.
    flat = [m.group(1) for w in words for m in [re.search(r"'([^']+)'", str(w))] if m] or [str(w) for w in words]
    return [check(
        "SHAPE_LEXICON_WARNING", "warning", params={"lens": draft.paradigm, "words": ", ".join(flat)},
        evidence=[{"kind": "words", "name": "words", "value": flat}], action=_field("shape", "paradigm"),
    )]


def _not_anchored(draft: steps.Draft, pool: dict[str, Any], ev_pool: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    from scholar_harness.recon.vocabulary import concept_report

    n_docs = len(pool.get("docs") or [])
    if n_docs < POOL_THIN_FLOOR or not draft.concepts:
        return []
    rows = [{"concept": c.concept, "synonyms": list(c.synonyms)} for c in draft.concepts]
    return [
        check("CONCEPT_NOT_ANCHORED", "warning", subject=row["concept"],
              params={"concept": row["concept"], "n": n_docs},
              evidence=[{"kind": "count", "name": "anchored_in", "value": 0, "unit": "papers"},
                        {"kind": "count", "name": "papers", "value": n_docs, "unit": "papers"},
                        {"kind": "words", "name": "terms", "value": [t["term"] for t in row["terms"]]}, _pool_ev(ev_pool if ev_pool is not None else pool)],
              action=_field("criteria", "concepts"))
        for row in concept_report(pool, rows, "draft") if row["anchored_in"] == 0
    ]


def _criteria_checks(draft: steps.Draft) -> list[dict[str, Any]]:
    if _missing(draft, "paradigm", "proof") or draft.paradigm is None:
        return []
    try:
        result = steps._criteria(draft)
    except steps.StepRefused:
        return []
    out = []
    if result["undecided"]:
        n = len(result["undecided"])
        out.append(check(
            "CRITERIA_UNDECIDED", "blocker", params={"n": n},
            evidence=[{"kind": "count", "name": "undecided", "value": n, "unit": "criteria"}],
            action={**_field("criteria", "criteria_decisions"), "criterion_id": result["undecided"][0]},
            refusal="CRITERIA_UNDECIDED",
        ))
    for side in result["missing_sides"]:
        out.append(check(
            "CRITERIA_SIDE_MISSING", "blocker", subject=side, params={"side": side},
            action=_field("criteria", "extra_inclusions" if side == "inclusion" else "extra_exclusions"),
            refusal="CRITERIA_MISSING",
        ))
    codes = [c.get("reason_category") for c in result["criteria"] if c["kind"] == "exclusion" and c["status"] == "accepted"]
    if len(codes) >= REASONS_UNIFORM_MIN and len(set(codes)) == 1:
        out.append(check(
            "CRITERIA_REASONS_UNIFORM", "warning", params={"n": len(codes), "code": codes[0]},
            evidence=[{"kind": "count", "name": "exclusions", "value": len(codes), "unit": "criteria"},
                      {"kind": "name", "name": "code", "value": codes[0]}],
            threshold={"name": "REASONS_UNIFORM_MIN", "value": REASONS_UNIFORM_MIN, "default": REASONS_UNIFORM_MIN,
                       "unit": "criteria"},
            action=_field("criteria", "extra_exclusions"),
        ))
    return out


def _compiler(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """``REVIEW_COMPILER_REFUSED`` only: every other refusal of the preview has its own row."""
    try:
        steps.preview(raw)
    except steps.StepRefused as exc:
        if exc.code != "INTENT_INVALID":
            return []
        errors = exc.details.get("errors") or []
        first = errors[0].get("loc", [None])[0] if errors and errors[0].get("loc") else None
        action = _field("shape", str(first)) if first else _step("shape")
        return [check(
            "REVIEW_COMPILER_REFUSED", "blocker",
            evidence=[{"kind": "name", "name": "errors", "value": [e.get("msg") for e in errors][:5]}],
            action=action, refusal="INTENT_INVALID",
        )]
    return []


def _target(target: Path) -> list[dict[str, Any]]:
    from .emit import existing_markers, screening_state

    if not target.exists():
        return []
    if not existing_markers(target):
        return [check("REVIEW_TARGET_NOT_WORKSPACE", "blocker", action=_field("review", "title"), refusal="WORKSPACE_EXISTS")]
    out = [check("REVIEW_TARGET_HAS_WORKSPACE", "warning", action=_field("review", "title"))]
    state = screening_state(target)
    decisions = int(state.get("decision_events") or 0) + int(state.get("decision_files") or 0)
    if state.get("bound"):
        out.append(check(
            "REVIEW_TARGET_HAS_SCREENING", "warning", params={"n": decisions},
            evidence=[{"kind": "count", "name": "decisions", "value": decisions, "unit": "decisions"}],
            action=_field("review", "title"),
        ))
    return out


def _proposals_open(record: dict[str, Any]) -> list[dict[str, Any]]:
    from . import proposals

    listed = [p for p in proposals.listing(record)["proposals"] if p["status"] == "open"]
    if not listed:
        return []
    return [check(
        "REVIEW_PROPOSALS_OPEN", "note", params={"n": len(listed)},
        evidence=[{"kind": "count", "name": "open", "value": len(listed), "unit": "suggestions"}],
        action=_step(listed[0]["step"]),
    )]


def _import_not_opened(record: dict[str, Any]) -> list[dict[str, Any]]:
    from .importer import IMPORTED_STEPS

    origin = record.get("origin")
    if not isinstance(origin, dict):
        return []
    checked = origin.get("checked") or {}
    left = [s for s in IMPORTED_STEPS if not checked.get(s)]
    return [
        check("REVIEW_IMPORT_STEP_NOT_OPENED", "note", subject=s, params={"steps": s},
              evidence=[{"kind": "name", "name": "step", "value": s}], action=_step(s))
        for s in left
    ]


# ---------------------------------------------------------------------------
# Genesis: audit/check_dismissals.jsonl
# ---------------------------------------------------------------------------


def genesis_lines(record: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The draft's dismissals and restores, carried into the workspace's record."""
    if not record:
        return []
    return [{**entry, "carried_from": "draft"} for entry in record.get("check_dismissals") or []]


def dismissal_counts(lines: list[dict[str, Any]]) -> dict[str, int]:
    out = {"dismissed": 0, "restored": 0}
    for line in lines:
        if line.get("action") in out:
            out[line["action"]] += 1
    return out
