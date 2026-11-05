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
- **One run per workspace** (`RUN_ALREADY_ACTIVE`), held by a lock file. The
  driver is built before the lock is taken, so a driver that cannot be built
  is refused (`DRIVER_UNAVAILABLE`) and never holds it. The lock names its
  engine process, and it is stale only when that process is gone (or, in this
  engine, when the run has no worker): the next run, or a cancel of that run,
  then finishes it and frees the lock. A second engine on the same workspace
  is refused rather than taking a run that is still going in the first.
- **The cost ceiling is a hard stop:** when the measured cost passes it the
  run stops with `COST_CEILING_REACHED`; finished proposals are kept. Batches
  are sent in chunks of `CHUNK` records, so a Batch run checks the ceiling
  between chunks. A provider or model without a price cannot be measured, so
  a ceiling on it is refused (`CEILING_NOT_PRICED`) and its `cost_so_far` is
  null, never 0.
- **A live run is held in memory** under one lock per run: the status and
  cancel routes read and change that record, and every write of the run file
  happens under the same lock. There is no read-modify-write of the file
  (which lost cancels, and which Windows refuses while another handle has the
  file open).
- **Journal:** `AGENT_RUN_STARTED` and `AGENT_RUN_COMPLETED` with counts of
  proposals, refusals, truncations, invalid answers, errors and failed checks,
  never with outcomes (the journal is readable before a decision). A journal
  row that cannot be written is recorded as `journal_error` on the run.

Calibration runs are the same over records the researcher has decided; their
result is include-recall with its Wilson bound and the missed includes, and it
is advisory (it never blocks a run).
"""

from __future__ import annotations

import copy
import json
import os
import threading
import time
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
DRIVER_UNAVAILABLE = "DRIVER_UNAVAILABLE"
CEILING_NOT_PRICED = "CEILING_NOT_PRICED"
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


class _Live:
    """A run with a worker in this engine: its record, the lock every change takes, its cancel."""

    def __init__(self, ws: Path, run: dict[str, Any]):
        self.ws, self.run = ws, run
        self.lock = threading.Lock()
        self.cancel = threading.Event()


_LIVE: dict[tuple[str, str], _Live] = {}
_LIVE_GUARD = threading.Lock()


def _key(ws: Path, run_id: str) -> tuple[str, str]:
    return (str(ws.resolve()), run_id)


def _live(ws: Path, run_id: str) -> _Live | None:
    with _LIVE_GUARD:
        return _LIVE.get(_key(ws, run_id))


def _run_path(ws: Path, run_id: str) -> Path:
    return ws / RUNS_DIR / f"{run_id}.json"


def _retry(fn: Callable[[], Any]) -> Any:
    # Windows refuses to open or replace a file that another handle has open;
    # a short retry covers a reader meeting a write in progress.
    for attempt in range(20):
        try:
            return fn()
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.05)
    return None


def _read_file(path: Path) -> dict[str, Any]:
    return _retry(lambda: json.loads(path.read_text(encoding="utf-8")))


def read_run(ws: Path, run_id: str) -> dict[str, Any]:
    live = _live(ws, run_id) if run_id.startswith("RUN-") else None
    if live is not None:
        with live.lock:
            return copy.deepcopy(live.run)
    path = _run_path(ws, run_id)
    if not (run_id.startswith("RUN-") and path.is_file()):
        raise RunRefused(UNKNOWN_RUN, f"no run {run_id}", status=404)
    return _read_file(path)


def list_runs(ws: Path) -> list[dict[str, Any]]:
    folder = ws / RUNS_DIR
    return [read_run(ws, f.stem) for f in sorted(folder.glob("RUN-*.json"))] if folder.is_dir() else []


def _write_run(ws: Path, run: dict[str, Any]) -> None:
    path = _run_path(ws, run["run_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.stem}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _retry(lambda: tmp.replace(path))


#: This engine process. The lock names it, so another engine on the same
#: workspace never takes a run that is still going here for a stale one.
_ENGINE_ID = uuid.uuid4().hex
#: Taking the lock and registering the run as live is one step, so a fresh
#: lock is never seen without its live run.
_START_GUARD = threading.RLock()
#: A lock file still empty or partial after this long was never finished.
_UNWRITTEN_LOCK_SECONDS = 30.0


def _pid_alive(pid: int) -> bool:
    """Whether a process exists. One this engine may not inspect counts as alive."""
    if not 0 < pid < 2**31:
        return False
    if os.name == "nt":
        import ctypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            # Access denied: it exists under another account, or is protected.
            return ctypes.get_last_error() == 5
        try:
            code = ctypes.c_ulong()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_lock(lock: Path) -> dict[str, Any] | None:
    """The lock's owner, `{}` while it is empty or unreadable, None when there is no lock."""
    try:
        text = _retry(lambda: lock.read_text(encoding="utf-8")).strip()
    except FileNotFoundError:
        return None
    try:
        info = json.loads(text) if text else {}
    except ValueError:
        info = {}
    return info if isinstance(info, dict) else {}


def _lock_holder(lock: Path) -> str | None:
    info = _read_lock(lock)
    return (info or {}).get("run_id") or None


def active_run(ws: Path) -> str | None:
    return _lock_holder(ws / LOCK_FILE)


def _lock_is_stale(ws: Path, lock: Path, info: dict[str, Any]) -> bool:
    """True only when the owner of the lock is provably gone."""
    if not info.get("run_id") or not isinstance(info.get("pid"), int):
        try:
            return time.time() - lock.stat().st_mtime > _UNWRITTEN_LOCK_SECONDS
        except FileNotFoundError:
            return True
    if info["pid"] == os.getpid():
        return info.get("engine") != _ENGINE_ID or _live(ws, info["run_id"]) is None
    return not _pid_alive(info["pid"])


def _unlink_lock(lock: Path) -> None:
    try:
        _retry(lock.unlink)
    except FileNotFoundError:
        pass


def _recover(ws: Path, run_id: str, state: str) -> dict[str, Any] | None:
    """Finish a run whose engine is gone, and free its lock. Call it under `_START_GUARD`."""
    path = _run_path(ws, run_id)
    run = _read_file(path) if run_id.startswith("RUN-") and path.is_file() else None
    if run is not None and run["state"] in ("running", "queued"):
        run.update(state=state, finished_at=_now(), error="the engine stopped while this run was active")
        _write_run(ws, run)
        journal_error = _journal_completed(ws, run)
        if journal_error is not None:
            run["journal_error"] = journal_error
            _write_run(ws, run)
    lock = ws / LOCK_FILE
    if _lock_holder(lock) == run_id:
        _unlink_lock(lock)
    return run


def _acquire(ws: Path, run_id: str) -> None:
    """Take the workspace lock for `run_id`; call it under `_START_GUARD`."""
    lock = ws / LOCK_FILE
    lock.parent.mkdir(parents=True, exist_ok=True)
    owner = json.dumps({"run_id": run_id, "pid": os.getpid(), "engine": _ENGINE_ID})
    for _ in range(2):
        try:
            with lock.open("x", encoding="utf-8") as handle:
                handle.write(owner)
            return
        except FileExistsError as exc:
            info = _read_lock(lock)
            if info is None:
                continue  # released meanwhile
            if not _lock_is_stale(ws, lock, info):
                raise RunRefused(RUN_ALREADY_ACTIVE, f"run {info.get('run_id') or '(starting)'} is still active; one run per workspace") from exc
            if info.get("run_id"):
                _recover(ws, info["run_id"], "failed")
            else:
                _unlink_lock(lock)
    raise RunRefused(RUN_ALREADY_ACTIVE, f"run {active_run(ws)} is still active; one run per workspace")


def _release(ws: Path, run_id: str) -> None:
    lock = ws / LOCK_FILE
    if _lock_holder(lock) == run_id:
        _unlink_lock(lock)


def request_cancel(ws: Path, run_id: str) -> dict[str, Any]:
    live = _live(ws, run_id) if run_id.startswith("RUN-") else None
    if live is not None:
        with live.lock:
            if live.run["state"] in ("running", "queued"):
                live.run["cancel_requested"] = True
                live.cancel.set()
                _write_run(ws, live.run)
            return copy.deepcopy(live.run)
    run = read_run(ws, run_id)
    if run["state"] not in ("running", "queued"):
        return run
    with _START_GUARD:
        lock = ws / LOCK_FILE
        info = _read_lock(lock)
        if info and info.get("run_id") == run_id and not _lock_is_stale(ws, lock, info):
            raise RunRefused(RUN_ALREADY_ACTIVE, f"run {run_id} is running in another engine process; cancel it there")
        # Its engine is gone: finish it now, so the lock does not outlive it.
        return _recover(ws, run_id, "cancelled") or run


def _journal_completed(ws: Path, run: dict[str, Any]) -> str | None:
    try:
        append_event(
            ws,
            "AGENT_RUN_COMPLETED",
            f"Agent run {run['run_id']} {run['state']}: {run['done']} of {run['records']} record(s) proposed",
            agent="scholar-harness/agent-runs",
            outputs=[str(RUNS_DIR / f"{run['run_id']}.json").replace("\\", "/")],
            parameters={"run_id": run["run_id"], "state": run["state"], "code": run.get("code")},
            metrics={k: run[k] for k in ("records", "done", "failed", "refused", "truncated", "invalid", "check_failures", "cost_so_far")},
            refresh_index=False,
        )
    except OSError as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


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
    priced = pg.price_for(provider, model) is not None
    if cost_ceiling_usd is not None and not priced:
        raise RunRefused(
            CEILING_NOT_PRICED,
            f"{provider}/{model} has no price in the price table, so its cost cannot be measured; run it without a ceiling",
            status=422,
        )
    if cost_ceiling_usd is not None and estimate["cost_usd"] is not None and estimate["cost_usd"] > cost_ceiling_usd:
        raise RunRefused(COST_CEILING_REACHED, f"the estimate (${estimate['cost_usd']:.2f}) is above the ceiling (${cost_ceiling_usd:.2f})")

    def build(p: str, k: str | None) -> Any:
        if driver_factory is not None:
            return driver_factory(p, k)
        options = {"direct_limit": pg.DIRECT_LIMIT, "max_per_batch": CHUNK} if p == "anthropic" else {}
        return make_driver(p, api_key=k, base_url=base_url, **options)

    # Built before the lock: a driver that cannot be built never holds it.
    try:
        driver = build(provider, key)
    except ImportError as exc:
        raise RunRefused(DRIVER_UNAVAILABLE, f"the {provider} driver is not installed (install the `ai` extra): {exc}") from exc
    except ValueError as exc:
        raise RunRefused(DRIVER_UNAVAILABLE, str(exc), status=422) from exc

    run_id = "RUN-" + uuid.uuid4().hex[:24]
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
        "cost_so_far": 0.0 if priced else None,
        "cost_ceiling_usd": cost_ceiling_usd,
        "estimate": estimate,
        "code": None,
        "started_at": _now(),
        "finished_at": None,
        "cancel_requested": False,
    }
    live = _Live(ws, run)
    with _START_GUARD:
        _acquire(ws, run_id)
        with _LIVE_GUARD:
            _LIVE[_key(ws, run_id)] = live
    try:
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
    except BaseException as exc:
        _finish(live, f"{type(exc).__name__}: {exc}")
        raise

    def work() -> None:
        error = None
        try:
            _execute(live, driver, requests, spec, papers, protocol, batch)
        except BaseException as exc:  # noqa: BLE001 - a crashed run is recorded, never left running
            error = f"{type(exc).__name__}: {exc}"
        finally:
            _finish(live, error)

    (executor or (lambda fn: threading.Thread(target=fn, name=f"agent-run-{run_id}", daemon=True).start()))(work)
    return read_run(ws, run_id)


def _execute(live: _Live, driver, requests, spec, papers, protocol, batch) -> None:
    from scholar_agent import prompt_gate as pg

    ws, run_id = live.ws, live.run["run_id"]
    context = ev.load_context(ws)
    price = pg.price_for(live.run["provider"], spec.model)
    stats = Counter()
    state = {"cost": 0.0}

    def stopped() -> bool:
        return live.cancel.is_set() or live.run.get("code") == COST_CEILING_REACHED

    def on_result(result) -> None:
        title, abstract, published = _text(papers.get(result.custom_id, {}))
        batch_binding = context.batches[context.study_batch[result.custom_id]]
        output = None
        if result.status == "ok":
            from scholar_agent.tasks import screening as task_mod

            output = task_mod.to_proposal_output(result.output, title, abstract, published)
        cost = pg.cost_usd(result.usage.as_dict(), price, batch=batch) if price else None
        with live.lock:
            run = live.run
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
            if cost is not None:
                state["cost"] += cost
            run.update(
                done=run["done"] + 1,
                failed=stats["error"],
                refused=stats["refusal"],
                truncated=stats["truncated"],
                invalid=stats["invalid"],
                check_failures=stats["check_failures"],
                cost_so_far=round(state["cost"], 4) if price else None,
            )
            ceiling = run.get("cost_ceiling_usd")
            if ceiling is not None and price and state["cost"] >= ceiling:
                run["code"] = COST_CEILING_REACHED
            _write_run(ws, run)

    driver.run(requests, spec, on_result=on_result, cancelled=stopped)


def _finish(live: _Live, error: str | None) -> None:
    """Record the run's end, free the lock and journal it, whatever happened."""
    ws, run_id = live.ws, live.run["run_id"]
    try:
        with live.lock:
            run = live.run
            if error is not None:
                run["state"], run["error"] = "failed", error
            elif run.get("code") == COST_CEILING_REACHED:
                run["state"] = "stopped"
            elif run.get("cancel_requested"):
                run["state"] = "cancelled"
            else:
                run["state"] = "completed"
            run["finished_at"] = _now()
            if run["kind"] == "calibration":
                try:
                    run["calibration"] = calibration_result(ws, run["study_ids"])
                except Exception as exc:  # noqa: BLE001 - the run's end is still recorded
                    run["calibration_error"] = f"{type(exc).__name__}: {exc}"
            _write_run(ws, run)
    finally:
        try:
            _release(ws, run_id)
        finally:
            with _LIVE_GUARD:
                _LIVE.pop(_key(ws, run_id), None)
    journal_error = _journal_completed(ws, run)
    if journal_error is not None:
        run["journal_error"] = journal_error
        _write_run(ws, run)


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
