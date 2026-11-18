"""The discovery checks (M10b, ``docs/ux/shared/final/02-checks.md`` "Discovery").

Pure reads of what the discovery routes already serve (``plan``, ``runs``,
``recall``, ``dedup``, ``report``, ``handoff``): each check is computed from
the same answer the screen reads, so the panel and the screen cannot disagree.
No check records a proposal in M10b. ``PLAN_ESTIMATE_ABOVE_TARGET`` lives on
the estimate card only (Part D) and is not served here.

Dismissals of a workspace's checks are appended to ``audit/check_dismissals.jsonl``
(one line each, never rewritten), with ``CHECK_DISMISSED`` / ``CHECK_RESTORED``
journal rows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request

from scholar_harness.inception import checks as C
from scholar_harness.workspace.audit import append_event

# --- thresholds (⚑ first values, calibrated before freezing) ------------------
#: The general size limit when the researcher stated no planned number (R3).
SIZE_WARN_WORKS = 1_000
#: ⚑ ``DEDUP_RATE_LOW``: removed share below this, with at least 3 databases and 200 records.
DEDUP_RATE_FLOOR = 0.05
DEDUP_MIN_DATABASES = 3
DEDUP_MIN_RECORDS = 200
#: ⚑ ``HANDOFF_ABSTRACTS_MISSING``: share of works with an abstract below this.
ABSTRACT_SHARE_FLOOR = 0.8
#: ⚑ ``HANDOFF_ONE_DATABASE_DOMINATES``: the largest share above this.
DOMINATES_SHARE = 0.8
UNFINISHED = ("failed", "stopped", "interrupted")


def _field_free(step: str) -> dict[str, Any]:
    return {"kind": "step", "step": step}


def _read(fn, *args, **kwargs) -> Any:
    """A discovery route's answer, or ``None`` when it refuses (no run, no recall, no dedup)."""
    try:
        return fn(*args, **kwargs)
    except HTTPException:
        return None


def planned(ws: Path) -> dict[str, Any] | None:
    """The researcher's stated plan: ``{min, max}`` from ``intent.json`` when ``pool_max`` is set.

    A preset in ``protocol.json`` is never read as the researcher's plan (02-checks, question 1).
    """
    try:
        intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(intent, dict) or intent.get("pool_max") is None:
        return None
    return {"min": int(intent.get("pool_min") or 0), "max": int(intent["pool_max"])}


def _plan_term_missing(ws: Path) -> list[dict[str, Any]]:
    """``PLAN_QUERY_TERM_MISSING``: as ``CONCEPT_TERM_MISSING``, on the signed protocol."""
    try:
        protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    title = str((protocol.get("metadata") or {}).get("title") or "")
    rqs = [str(rq.get("text") or "") for rq in protocol.get("research_questions") or [] if isinstance(rq, dict)]
    concepts = (protocol.get("search_strategy") or {}).get("core_concepts") or []
    known = [t for c in concepts if isinstance(c, dict) for t in (c.get("concept") or "", *(c.get("synonyms") or []))]
    return [
        C.check("PLAN_QUERY_TERM_MISSING", "warning", subject=t, params={"term": t},
                evidence=[{"kind": "words", "name": "term", "value": t}], action=_field_free("inception"))
        for t in C.missing_terms([title, *rqs], known)
    ]


def compute(request: Request, run: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Every discovery check of the open workspace: ``(checks, waiting, partial, scope)``."""
    from .api import discovery as D

    ws = D._ws(request)
    proto = D._protocol(ws)  # PROTOCOL_MISSING / PROTOCOL_INVALID refuse the whole list, as the screens do
    items: list[dict[str, Any]] = []
    waiting: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []

    def run_check(check_id: str, fn) -> None:
        C._safely(items, partial, check_id, fn)

    # Plan
    plan = D.plan(request)
    run_check("PLAN_MAILTO_NOT_SET", lambda: [
        C.check("PLAN_MAILTO_NOT_SET", "blocker", action=_field_free("plan"), refusal="MAILTO_NOT_SET")
    ] if not plan["mailto_set"] else [])
    run_check("PLAN_OPENALEX_KEY_NOT_SET", lambda: [
        C.check("PLAN_OPENALEX_KEY_NOT_SET", "blocker", action=_field_free("plan"), refusal="OPENALEX_KEY_NOT_SET")
    ] if "openalex" in proto.providers and not plan["openalex_key_set"] else [])
    run_check("PLAN_QUERY_TERM_MISSING", lambda: _plan_term_missing(ws))
    run_check("PLAN_NO_CAP", lambda: [
        C.check("PLAN_NO_CAP", "warning", params={"ceiling": plan["cap"]["ceiling"]},
                evidence=[{"kind": "count", "name": "ceiling", "value": plan["cap"]["ceiling"], "unit": "records"}],
                action=_field_free("plan"))
    ] if plan["cap"]["source"] == "engine_ceiling" else [])

    # Recall
    recall = _read(D.last_recall, request)
    if recall is None:
        run_check("RECALL_NOT_RUN", lambda: [C.check("RECALL_NOT_RUN", "note", action=_field_free("recall"))])
    else:
        run_check("RECALL_SEED_MISSED", lambda: [
            C.check("RECALL_SEED_MISSED", "warning", subject=str(seed), params={"seed": str(seed)},
                    evidence=[{"kind": "doi", "value": str(seed)}], action=_field_free("inception"))
            for seed in recall.get("missed_everywhere") or []
        ])
        run_check("RECALL_CHECK_STALE", lambda: [
            C.check("RECALL_CHECK_STALE", "warning",
                    evidence=[{"kind": "name", "name": "protocol_fingerprint", "value": recall.get("protocol_fingerprint")}],
                    action=_field_free("recall"))
        ] if recall.get("protocol_fingerprint") and recall.get("protocol_fingerprint") != plan["protocol_fingerprint"] else [])

    # Harvest
    summaries = D._run_summaries(ws, D._jobs(request).active(ws))
    chosen = next((s for s in summaries if s["run"] == run), None) if run else (summaries[0] if summaries else None)
    if run and chosen is None:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND", "message": f"No search run {run} in this workspace."})
    if chosen is None:
        for cid in ("HARVEST_ABOVE_TARGET", "HARVEST_DATABASE_EMPTY", "HARVEST_LEG_FAILED", "HARVEST_LOWER_BOUND"):
            waiting.append({"check_id": cid, "step": "harvest", "needs": "run"})
    else:
        legs = D._manifest(D._run_dir(ws, chosen["run"]))["legs"]
        run_check("HARVEST_ABOVE_TARGET", lambda: _above_target(ws, chosen))
        run_check("HARVEST_DATABASE_EMPTY", lambda: [
            C.check("HARVEST_DATABASE_EMPTY", "warning", subject=str(leg.get("provider")),
                    params={"database": str(leg.get("provider"))},
                    evidence=[{"kind": "count", "name": str(leg.get("provider")), "value": 0, "unit": "records"},
                              {"kind": "run", "value": chosen["run"]}],
                    action=_field_free("plan"))
            for leg in legs if leg.get("status") != "failed" and int(leg.get("fetched") or 0) == 0
        ] if any(int(leg.get("fetched") or 0) > 0 for leg in legs) else [])
        run_check("HARVEST_LEG_FAILED", lambda: [
            C.check("HARVEST_LEG_FAILED", "warning", subject=str(leg.get("provider")),
                    params={"database": str(leg.get("provider")), "code": str(leg.get("error_code") or "")},
                    evidence=[{"kind": "name", "name": "error_code", "value": leg.get("error_code")},
                              {"kind": "run", "value": chosen["run"]}],
                    action=_field_free("harvest"))
            for leg in legs if leg.get("status") == "failed"
        ])
        run_check("HARVEST_LOWER_BOUND", lambda: [
            C.check("HARVEST_LOWER_BOUND", "note", subject=str(leg.get("provider")),
                    params={"database": str(leg.get("provider"))},
                    evidence=[{"kind": "count", "name": str(leg.get("provider")), "value": int(leg.get("fetched") or 0),
                               "unit": "records"}, {"kind": "run", "value": chosen["run"]}],
                    action=_field_free("plan"))
            for leg in legs if leg.get("cap_hit")
        ])

    # Duplicates
    dedup = D._dedup_summary(ws)
    if dedup is None:
        run_check("DEDUP_NOT_RUN", lambda: [C.check("DEDUP_NOT_RUN", "note", action=_field_free("harvest"))] if summaries else [])
    else:
        run_check("DEDUP_RATE_LOW", lambda: _dedup_low(ws, dedup))

    # Report
    if summaries:
        report = _read(D.report, request, run=chosen["run"] if chosen else None)
        if report is not None:
            run_check("REPORT_METHODS_NOT_REVIEWED", lambda: [
                C.check("REPORT_METHODS_NOT_REVIEWED", "note",
                        evidence=[{"kind": "run", "value": report["run"]}], action=_field_free("report"))
            ] if not report["methods_text"]["reviewed"] else [])

    # Hand-off
    handoff = D.handoff(request)
    run_check("HANDOFF_*", lambda: _handoff(handoff, chosen))
    scope = {"kind": "workspace", "protocol_fingerprint": plan["protocol_fingerprint"], "run": chosen["run"] if chosen else None}
    return items, waiting, partial, scope


def _above_target(ws: Path, summary: dict[str, Any]) -> list[dict[str, Any]]:
    stated = planned(ws)
    limit = stated["max"] if stated else SIZE_WARN_WORKS
    fetched = int(summary["fetched_total"])
    if fetched <= limit:
        return []
    params = {"n": fetched, **({"min": stated["min"], "max": stated["max"]} if stated else {"limit": limit})}
    return [C.check(
        "HARVEST_ABOVE_TARGET", "warning", params=params,
        sentence=None if stated else "HARVEST_ABOVE_TARGET.general",
        evidence=[{"kind": "count", "name": "fetched", "value": fetched, "unit": "records"}, {"kind": "run", "value": summary["run"]}],
        threshold={"name": "planned_max" if stated else "SIZE_WARN_WORKS", "value": limit, "default": SIZE_WARN_WORKS,
                   "unit": "records"},
        action=_field_free("plan"),
    )]


def _dedup_low(ws: Path, dedup: dict[str, Any]) -> list[dict[str, Any]]:
    from .api import discovery as D

    run = dedup.get("run")
    legs: list[dict[str, Any]] = []
    if run:
        try:
            legs = D._manifest(D._run_dir(ws, str(run)))["legs"]
        except D.Refused:
            legs = []
    contributing = [leg for leg in legs if int(leg.get("fetched") or 0) > 0]
    rate, n = float(dedup["removed_rate"]), int(dedup["input_records"])
    if len(contributing) < DEDUP_MIN_DATABASES or n < DEDUP_MIN_RECORDS or rate >= DEDUP_RATE_FLOOR:
        return []
    return [C.check(
        "DEDUP_RATE_LOW", "warning", params={"share": f"{rate * 100:.1f}%", "n": n, "k": len(contributing)},
        evidence=[{"kind": "share", "name": "removed_rate", "value": rate},
                  {"kind": "count", "name": "input_records", "value": n, "unit": "records"},
                  {"kind": "count", "name": "databases", "value": len(contributing), "unit": "databases"}],
        threshold={"name": "DEDUP_RATE_FLOOR", "value": DEDUP_RATE_FLOOR, "default": DEDUP_RATE_FLOOR, "unit": "share"},
        action=_field_free("dedup"),
    )]


def _handoff(handoff: dict[str, Any], chosen: dict[str, Any] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    corpus = handoff.get("corpus") or {}
    staged = bool(corpus.get("sources"))
    accepted = corpus.get("state") == "ACCEPTED"
    run = handoff.get("run")
    preparation = handoff.get("preparation") or {}
    if run and not accepted and preparation.get("state") in UNFINISHED:
        fetched = 0
        for summary in [chosen] if chosen and chosen["run"] == run else []:
            fetched = int(summary["fetched_total"])
        level = "note" if staged else "blocker"
        out.append(C.check(
            "HANDOFF_PREPARATION_UNFINISHED", level,
            params={"run": run, "n": fetched, "state": preparation["state"], "stage": preparation.get("stage") or ""},
            evidence=[{"kind": "run", "value": run}, {"kind": "name", "name": "state", "value": preparation["state"]},
                      {"kind": "name", "name": "stage", "value": preparation.get("stage")}],
            action={"kind": "step", "step": "harvest", "finish": bool(preparation.get("can_finish"))},
            refusal="PREPARATION_UNFINISHED",
        ))
    if run and not accepted and handoff.get("search_changed"):
        out.append(C.check(
            "HANDOFF_SEARCH_CHANGED", "note" if staged else "blocker", params={"run": run},
            evidence=[{"kind": "run", "value": run}], action={"kind": "step", "step": "harvest"},
            refusal="PROTOCOL_CHANGED_SINCE_RUN",
        ))
    elif run and not accepted and handoff.get("protocol_changed"):
        out.append(C.check("HANDOFF_PROTOCOL_CHANGED", "note", evidence=[{"kind": "run", "value": run}],
                           action={"kind": "step", "step": "handoff"}))
    abstracts = handoff.get("abstracts") or {}
    total = int(abstracts.get("with_abstract") or 0) + int(abstracts.get("title_only") or 0)
    share = float(abstracts.get("share_with_abstract") or 0.0)
    if total and share < ABSTRACT_SHARE_FLOOR:
        out.append(C.check(
            "HANDOFF_ABSTRACTS_MISSING", "warning", params={"share": f"{round(share * 100)}%"},
            evidence=[{"kind": "share", "name": "share_with_abstract", "value": share},
                      {"kind": "count", "name": "works", "value": total, "unit": "works"}],
            threshold={"name": "ABSTRACT_SHARE_FLOOR", "value": ABSTRACT_SHARE_FLOOR, "default": ABSTRACT_SHARE_FLOOR,
                       "unit": "share"},
            action={"kind": "step", "step": "report"},
        ))
    mix = handoff.get("provider_mix") or []
    if len(mix) >= 2 and float(mix[0].get("share") or 0) > DOMINATES_SHARE:
        top = mix[0]
        out.append(C.check(
            "HANDOFF_ONE_DATABASE_DOMINATES", "note", subject=str(top["provider"]),
            params={"database": str(top["provider"]), "share": f"{round(float(top['share']) * 100)}%"},
            evidence=[{"kind": "share", "name": str(top["provider"]), "value": float(top["share"])}],
            threshold={"name": "DOMINATES_SHARE", "value": DOMINATES_SHARE, "default": DOMINATES_SHARE, "unit": "share"},
            action={"kind": "step", "step": "report"},
        ))
    return out


# --- dismissals: audit/check_dismissals.jsonl ----------------------------------


def dismissals(ws: Path) -> list[dict[str, Any]]:
    path = ws / C.DISMISSALS_FILE
    out = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and "carried_from" not in entry:
            out.append(entry)
    return out


def append_dismissal(ws: Path, entry: dict[str, Any], *, run: str | None, agent: str) -> None:
    """One line in the record, then the journal row that indexes it."""
    path = ws / C.DISMISSALS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {**entry, **({"run": run} if run else {})}
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    action = "CHECK_DISMISSED" if entry["action"] == "dismissed" else "CHECK_RESTORED"
    append_event(
        ws, action, f"{entry['check_id']} {entry['action']}" + (f": {entry['reason']}" if entry.get("reason") else ""),
        agent=agent, outputs=[C.DISMISSALS_FILE],
        parameters={"check_id": entry["check_id"], "subject": entry["subject"], "reason": entry.get("reason") or "",
                    "evidence_digest": entry["evidence_digest"], "method": "HUMAN"},
    )
