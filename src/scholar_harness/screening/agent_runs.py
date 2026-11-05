"""Agent proposal runs (agent-system §2-§4; contract §4 `/proposals/*`; spec 06).

A run sends the screening task for a set of records to one provider and
stores one proposal per record through `proposals.submit_proposal`. It never
writes a decision. Every record in scope gets a proposal: a refusal,
truncation, invalid answer or error is stored as an Unclear draft with the
driver's status, never dropped and never excluded.

- **Consent** is per provider, recorded in the workspace and journaled
  (`SCREENING_AGENT_CONSENT`); a run without it is refused `CONSENT_REQUIRED`.
- **Keys** come from the OS keychain or the environment (`scholar_agent.keys`);
  a provider without a key is refused `PROVIDER_KEY_MISSING`.
- **One run per workspace** (`RUN_ALREADY_ACTIVE`), held by a lock file.
- **The cost ceiling is a hard stop:** when the measured cost passes it the
  run stops with `COST_CEILING_REACHED`; finished proposals are kept. Batches
  are sent in chunks so the ceiling is checked between them.
- **Journal:** `AGENT_RUN_STARTED` and `AGENT_RUN_COMPLETED` with counts of
  proposals, refusals, truncations, invalid answers, errors and failed checks,
  never with outcomes (the journal is readable before a decision).

Calibration runs are the same over records the researcher has decided; their
result is include-recall with its Wilson bound and the missed includes, and it
is advisory (it never blocks a run).
"""

from __future__ import annotations

import json
import threading
import uuid
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.screening import events as ev
from scholar_harness.screening import proposals as pr
from scholar_harness.workspace.audit import append_event

RUNS_DIR = Path("literature") / "screening" / "proposals" / "runs"
CONSENT_FILE = Path("literature") / "screening" / "agent_consent.json"
LOCK_FILE = RUNS_DIR / "active.lock"
CONSENT_REQUIRED = "CONSENT_REQUIRED"
RUN_ALREADY_ACTIVE = "RUN_ALREADY_ACTIVE"
COST_CEILING_REACHED = "COST_CEILING_REACHED"
PROVIDER_KEY_MISSING = "PROVIDER_KEY_MISSING"
UNKNOWN_RUN = "UNKNOWN_RUN"
#: What leaves the machine, stated in the consent and on the run screen.
DATA_FLOW = "titles, abstracts and publication years of every record in the run, and the screening criteria"
CHUNK = 200


class RunRefused(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


# --- consent -------------------------------------------------------------------


def read_consent(ws: Path) -> dict[str, Any]:
    path = ws / CONSENT_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def record_consent(ws: Path, provider: str, *, model: str, prompt_sha256: str, accepted_at: str) -> dict[str, Any]:
    consent = read_consent(ws)
    consent[provider] = {"accepted_at": accepted_at, "model": model, "prompt_sha256": prompt_sha256, "data_flow": DATA_FLOW}
    path = ws / CONSENT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(consent, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(
        ws,
        "SCREENING_AGENT_CONSENT",
        f"Consent to send records to {provider} ({model})",
        agent="scholar-harness/agent-runs",
        outputs=[str(CONSENT_FILE).replace("\\", "/")],
        parameters={"provider": provider, "model": model, "prompt_sha256": prompt_sha256, "data_flow": DATA_FLOW},
        refresh_index=False,
    )
    return consent[provider]


# --- run records ---------------------------------------------------------------


def _run_path(ws: Path, run_id: str) -> Path:
    return ws / RUNS_DIR / f"{run_id}.json"


def read_run(ws: Path, run_id: str) -> dict[str, Any]:
    path = _run_path(ws, run_id)
    if not (run_id.startswith("RUN-") and path.is_file()):
        raise RunRefused(UNKNOWN_RUN, f"no run {run_id}", status=404)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_run(ws: Path, run: dict[str, Any]) -> None:
    path = _run_path(ws, run["run_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def active_run(ws: Path) -> str | None:
    lock = ws / LOCK_FILE
    return lock.read_text(encoding="utf-8").strip() or None if lock.is_file() else None


def _acquire(ws: Path, run_id: str) -> None:
    lock = ws / LOCK_FILE
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x", encoding="utf-8") as handle:
            handle.write(run_id)
    except FileExistsError as exc:
        raise RunRefused(RUN_ALREADY_ACTIVE, f"run {active_run(ws)} is still active; one run per workspace") from exc


def _release(ws: Path, run_id: str) -> None:
    lock = ws / LOCK_FILE
    if lock.is_file() and lock.read_text(encoding="utf-8").strip() == run_id:
        lock.unlink()


def request_cancel(ws: Path, run_id: str) -> dict[str, Any]:
    run = read_run(ws, run_id)
    if run["state"] in ("running", "queued"):
        run["cancel_requested"] = True
        _write_run(ws, run)
    return run


# --- the records of a run -------------------------------------------------------


def _papers(ws: Path, context: ev.ScreeningContext) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for index in context.batches:
        path = ws / "literature" / "screening" / f"batch_{index:03d}.json"
        if path.is_file():
            for paper in json.loads(path.read_text(encoding="utf-8")).get("papers", []):
                out[str(paper["workspace_id"])] = paper
    return out


def _text(paper: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    abstract = str(paper.get("abstract") or "").strip()
    abstract_or_none = abstract if abstract and abstract != "No abstract available." else None
    return paper.get("title"), abstract_or_none, (str(paper["year"]) if paper.get("year") else None)


# --- the run itself -------------------------------------------------------------


def start_run(
    ws: Path,
    *,
    provider: str,
    model: str,
    effort: str,
    study_ids: list[str],
    cost_ceiling_usd: float | None,
    kind: str = "proposals",
    driver_factory: Callable[[str, str | None], Any] | None = None,
    executor: Callable[[Callable[[], None]], None] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Refuse or start a run; returns the run record (state `running`)."""
    from scholar_agent import prompt_gate as pg
    from scholar_agent.drivers import ScreeningRequest, make_driver
    from scholar_agent.keys import resolve_key
    from scholar_agent.tasks import screening as task_mod

    if provider not in read_consent(ws):
        raise RunRefused(CONSENT_REQUIRED, f"no recorded consent to send records to {provider}")
    key = resolve_key(provider) if driver_factory is None else "injected"
    if key is None and provider != "openai_compatible":
        raise RunRefused(PROVIDER_KEY_MISSING, f"no {provider} key; run `nexus-scholar keys set {provider}` on this computer")
    context = ev.load_context(ws)
    unknown = [s for s in study_ids if s not in context.study_batch]
    if unknown:
        raise RunRefused("UNKNOWN_STUDY", f"{unknown[0]} is not in the bound corpus", status=422)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    task = task_mod.load_task()
    spec = pg.run_spec(protocol, model=model, effort=effort, max_tokens=int(task.defaults["max_tokens"]))
    papers = _papers(ws, context)
    requests = [ScreeningRequest(s, task_mod.record_message(*_text(papers.get(s, {})))) for s in study_ids]
    # Reuse the gate's estimate over the run's own records.
    records = [pg.EvalRecord(s, "", *_text(papers.get(s, {}))) for s in study_ids]
    batch = provider == "anthropic" and len(study_ids) > pg.DIRECT_LIMIT
    estimate = pg.estimate(records, spec, provider=provider, batch=batch)
    if cost_ceiling_usd is not None and estimate["cost_usd"] is not None and estimate["cost_usd"] > cost_ceiling_usd:
        raise RunRefused(COST_CEILING_REACHED, f"the estimate (${estimate['cost_usd']:.2f}) is above the ceiling (${cost_ceiling_usd:.2f})")

    run_id = "RUN-" + uuid.uuid4().hex[:24]
    _acquire(ws, run_id)
    run = {
        "run_id": run_id,
        "kind": kind,
        "state": "running",
        "provider": provider,
        "model": model,
        "effort": effort,
        "task_version": task.task_version,
        "prompt_sha256": task.prompt_sha256,
        "protocol_fingerprint": context.protocol_fingerprint,
        "records": len(study_ids),
        "study_ids": study_ids,
        "done": 0,
        "failed": 0,
        "refused": 0,
        "truncated": 0,
        "invalid": 0,
        "check_failures": 0,
        "cost_so_far": 0.0,
        "cost_ceiling_usd": cost_ceiling_usd,
        "estimate": estimate,
        "code": None,
        "started_at": _now(),
        "finished_at": None,
        "cancel_requested": False,
    }
    _write_run(ws, run)
    append_event(
        ws,
        "AGENT_RUN_STARTED",
        f"Started a {kind} run of {len(study_ids)} record(s) on {provider} ({model})",
        agent="scholar-harness/agent-runs",
        outputs=[str(RUNS_DIR / f"{run_id}.json").replace("\\", "/")],
        parameters={"run_id": run_id, "kind": kind, "provider": provider, "model": model, "effort": effort, "prompt_sha256": task.prompt_sha256},
        metrics={"records": len(study_ids)},
        refresh_index=False,
    )

    def factory(p: str, k: str | None) -> Any:
        if driver_factory is not None:
            return driver_factory(p, k)
        options = {"direct_limit": pg.DIRECT_LIMIT, "max_per_batch": CHUNK} if p == "anthropic" else {}
        return make_driver(p, api_key=k, base_url=base_url, **options)

    def work() -> None:
        _execute(ws, run_id, factory(provider, key), requests, spec, papers, protocol, batch)

    (executor or (lambda fn: threading.Thread(target=fn, name=f"agent-run-{run_id}", daemon=True).start()))(work)
    return run


def _execute(ws, run_id, driver, requests, spec, papers, protocol, batch) -> None:
    from scholar_agent import prompt_gate as pg

    context = ev.load_context(ws)
    price = pg.price_for(read_run(ws, run_id)["provider"], spec.model)
    stats = Counter()
    state = {"cost": 0.0}

    def stopped() -> bool:
        run = read_run(ws, run_id)
        return bool(run.get("cancel_requested")) or run.get("code") == COST_CEILING_REACHED

    def on_result(result) -> None:
        run = read_run(ws, run_id)
        title, abstract, published = _text(papers.get(result.custom_id, {}))
        batch_binding = context.batches[context.study_batch[result.custom_id]]
        output = None
        if result.status == "ok":
            from scholar_agent.tasks import screening as task_mod

            output = task_mod.to_proposal_output(result.output, title, abstract, published)
        cost = pg.cost_usd(result.usage.as_dict(), price, batch=batch) if price else 0.0
        record = pr.submit_proposal(
            ws,
            study_id=result.custom_id,
            title=title,
            abstract=abstract,
            published=published,
            output=output,
            protocol=protocol,
            protocol_fingerprint=context.protocol_fingerprint,
            provenance={
                "task_id": "screening",
                "task_version": run["task_version"],
                "prompt_sha256": run["prompt_sha256"],
                "driver": run["provider"],
                "model": result.model or spec.model,
                "effort": spec.effort,
                "batch_binding": {"batch_id": batch_binding.batch_id, "batch_sha256": batch_binding.batch_sha256},
                "usage": result.usage.as_dict(),
                "cost_estimate": cost,
                "request_id": result.request_id,
                "batch_id": result.batch_id,
                "driver_status": result.status,
                "driver_detail": result.detail,
                "run_id": run_id,
            },
            created_at=_now(),
        )
        stats[result.status] += 1
        if result.status == "ok" and not all(c["ok"] for c in record["validators"]):
            stats["check_failures"] += 1
        state["cost"] += cost
        run.update(
            done=run["done"] + 1,
            failed=stats["error"],
            refused=stats["refusal"],
            truncated=stats["truncated"],
            invalid=stats["invalid"],
            check_failures=stats["check_failures"],
            cost_so_far=round(state["cost"], 4),
        )
        ceiling = run.get("cost_ceiling_usd")
        if ceiling is not None and state["cost"] >= ceiling:
            run["code"] = COST_CEILING_REACHED
        _write_run(ws, run)

    final = "completed"
    try:
        driver.run(requests, spec, on_result=on_result, cancelled=stopped)
    except Exception as exc:  # noqa: BLE001 - a crashed run is recorded, never silent
        final = "failed"
        run = read_run(ws, run_id)
        run["error"] = f"{type(exc).__name__}: {exc}"
        _write_run(ws, run)
    run = read_run(ws, run_id)
    if final != "failed":
        if run.get("code") == COST_CEILING_REACHED:
            final = "stopped"
        elif run.get("cancel_requested"):
            final = "cancelled"
    run["state"] = final
    run["finished_at"] = _now()
    if run["kind"] == "calibration":
        run["calibration"] = calibration_result(ws, run["study_ids"])
    _write_run(ws, run)
    _release(ws, run_id)
    try:
        append_event(
            ws,
            "AGENT_RUN_COMPLETED",
            f"Agent run {run_id} {final}: {run['done']} of {run['records']} record(s) proposed",
            agent="scholar-harness/agent-runs",
            outputs=[str(RUNS_DIR / f"{run_id}.json").replace("\\", "/")],
            parameters={"run_id": run_id, "state": final, "code": run.get("code")},
            metrics={k: run[k] for k in ("records", "done", "failed", "refused", "truncated", "invalid", "check_failures", "cost_so_far")},
            refresh_index=False,
        )
    except OSError:
        # The run record already holds the outcome; a journal that cannot be
        # written must not leave the lock held or the run looking active.
        pass


def calibration_result(ws: Path, study_ids: list[str]) -> dict[str, Any]:
    """Include-recall of the latest proposals against the researcher's decisions (advisory)."""
    from scholar_agent import prompt_gate as pg

    context = ev.load_context(ws)
    events = ev.current_events(ev.read_events(ws), context)
    labels, outcomes = {}, {}
    for study in study_ids:
        screener = next((e["screener_id"] for e in events if e["study_id"] == study), None)
        winner = ev.winning_event(events, study, screener) if screener else None
        proposal = pr.latest_proposal(ws, study)
        if winner is None or proposal is None:
            continue
        labels[study] = "INCLUDE" if winner["outcome"] in ("INCLUDE", "MAYBE") else "EXCLUDE"
        outcomes[study] = proposal["derived_outcome"]
    scored = pg.score(outcomes, labels)
    return {
        "include_recall": scored["include_recall"],
        "ci_low": scored["include_recall_ci_low"],
        "missed_includes": scored["missed_includes"],
        "compared": len(labels),
        "advisory": True,
    }
