"""M9a-measure: the screening agent against the researcher's own decisions.

One command measures what the autonomy ladder needs before its thresholds are
fixed (`docs/architecture/agent_autonomy_ladder.md` §4, §10): the agent's
include recall against decisions the researcher made, its precision on
includes, how often it leaves a record Unclear, how many answers were
truncated, refused or malformed, the tokens and the cost per record, and the
workspace batches where it falls under the ladder's draft thresholds.

It reuses the prompt gate and does not replace it: the frozen set, the record
text (checked against its hashes), the system prompt, the drivers, the
engine's own validators and rule table, the Wilson bound and the price table
all come from `scholar_agent.prompt_gate`. What it adds is the report
(`analyse`), the batch-wise run that mirrors a product run (`execute`), and a
plan that makes no network call (`plan`).

Rules that hold here, as in the product:

- **Blind.** The agent sees the system prompt (protocol criteria only) and one
  record's text per call: never a label, a decision, an outcome statistic or
  the database a record came from (ladder §4, "What the agent is never shown";
  lesson 54). `assert_blind` checks this before anything is sent.
- **A failed call is Unclear, never Exclude** (agent-system §1.3). Records a
  run never reached (a stopped run) are not scored at all, so a stop cannot
  inflate recall.
- **The workspace is only read.** Reports go to a separate output folder.
- **The researcher's Unclear counts as an include** for the comparison, as
  `calibration_result` already does, because an Unclear goes to full text.
"""

from __future__ import annotations

import glob
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_agent import prompt_gate as pg
from scholar_agent.drivers import Driver, DriverResult, RunSpec, ScreeningRequest

OUT_DIR = Path(".cache") / "m9a-measure"
SCOPES = ("frozen", "all")
#: Output tokens per record used for the "heavier thinking" sensitivity in `plan`.
HEAVY_OUTPUT_TOKENS = 1500
#: A cheap model costs a fraction of a cent per record; `cost_usd` rounds to 4 places, which would lose most of it.
COST_DIGITS = 8


@dataclass(frozen=True)
class Gate:
    """A DRAFT ladder gate (ladder §4). M9a decides the final numbers from data."""

    name: str
    min_includes: int
    recall_ci_low: float


L1 = Gate("L1", 35, 0.90)
L2 = Gate("L2", 75, 0.95)
GATES = (L1, L2)


# --- the researcher's decisions --------------------------------------------------


def human_label(decision: str) -> str | None:
    """INCLUDE or EXCLUDE; the researcher's Unclear counts as an include (ladder §4)."""
    value = str(decision).strip().upper()
    if value in ("INCLUDE", "MAYBE", "UNCLEAR"):
        return "INCLUDE"
    if value == "EXCLUDE":
        return "EXCLUDE"
    return None


def batch_index(workspace: Path) -> dict[str, str]:
    """Study id to the workspace screening batch (`batch_NNN`) that holds it."""
    out: dict[str, str] = {}
    for name in sorted(glob.glob(str(workspace / "literature" / "screening" / "batch_[0-9][0-9][0-9].json"))):
        batch = Path(name).stem
        for paper in json.loads(Path(name).read_text(encoding="utf-8"))["papers"]:
            out[str(paper["workspace_id"])] = batch
    return out


def load_records(
    workspace: Path, scope: str, *, frozen: dict[str, Any] | None = None
) -> tuple[list[pg.EvalRecord], dict[str, Any]]:
    """The records to measure, with their text checked against stored hashes.

    `frozen`: the prompt gate's frozen sample (every confirmed include and 1,000
    seeded excludes). `all`: every record the researcher decided in the workspace.
    Returns the records and a description of the scope for the report.
    """
    from scholar_harness.screening.proposals import input_sha256

    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}")
    confirmation = "absent"
    if (workspace / "literature" / "screening" / "HUMAN_CONFIRMATION.json").is_file():
        pg.verify_confirmation(workspace)
        confirmation = "verified"
    if scope == "frozen":
        if frozen is None:
            frozen = json.loads(pg.SET_FILE.read_text(encoding="utf-8"))
        if frozen.get("source") != workspace.name:
            raise ValueError(f"the frozen set was drawn from {frozen.get('source')!r}, not {workspace.name!r}; use scope `all`")
        records = pg.load_set(workspace, frozen)
        return records, {"scope": "frozen", "set_sha256": frozen["set_sha256"], "human_confirmation": confirmation, "undecided_in_workspace": 0}
    papers, labels = pg._papers(workspace), pg._labels(workspace)
    records, skipped = [], 0
    for study_id in sorted(labels):
        label = human_label(labels[study_id])
        if label is None or study_id not in papers:
            skipped += 1
            continue
        title, abstract, published = pg._record(papers[study_id])
        records.append(pg.EvalRecord(study_id, label, title, abstract, published))
    digest = hashlib.sha256(
        json.dumps([[r.study_id, r.label, input_sha256(r.title, r.abstract, r.published)] for r in records]).encode("utf-8")
    ).hexdigest()
    return records, {"scope": "all", "set_sha256": "sha256:" + digest, "human_confirmation": confirmation, "undecided_in_workspace": skipped}


# --- what the agent may see ------------------------------------------------------

#: Words that are outcome statistics or priors when they reach the agent (ladder §4).
_WORDS = (
    r"\b(include rate|inclusion rate|exclusion rate|agreement|precision|recall|most of (these|the records)|almost all)\b"
)
_STATISTIC_WORDS = re.compile(_WORDS, re.IGNORECASE)
#: In the task's own text a percentage is also refused ("about 95 to 100% exclusion", lesson 54).
_STATISTIC = re.compile(_WORDS + r"|\d\s*%|per ?cent", re.IGNORECASE)


def assert_blind(spec: RunSpec, requests: list[ScreeningRequest], records: list[pg.EvalRecord], protocol: dict[str, Any]) -> None:
    """Refuse to send anything that carries a label, an outcome or a statistic.

    The check is on the exact bytes that would leave the machine: the system
    prompt and each request message. A record's own words are not scanned for
    statistics (an abstract may say "95%"); they are the data being screened.
    """
    # The criteria are the researcher's protocol text (the product sends them too) and may state a
    # sampling plan; the task's own words around them may carry no figure at all.
    task = pg.task_mod.load_task(spec.task_version or None)
    expected_spec = pg.run_spec(
        protocol, model=spec.model, effort=spec.effort, max_tokens=spec.max_tokens, task_version=spec.task_version or None
    )
    if spec.system != expected_spec.system:
        raise ValueError("the system prompt is not the task's prompt with the protocol's criteria")
    prefix, _, suffix = task.template.partition("{criteria}")
    block = " ".join(c.text for c in pg.task_mod.criteria_from_protocol(protocol))
    for text, pattern in ((prefix + suffix, _STATISTIC), (block, _STATISTIC_WORDS)):
        hit = pattern.search(text)
        if hit:
            raise ValueError(f"the system prompt carries an outcome statistic ({hit.group(0)!r}); the agent must never see one")
    by_id = {r.study_id: r for r in records}
    for request in requests:
        record = by_id[request.custom_id]
        expected = pg.task_mod.record_message(record.title, record.abstract, record.published)
        if request.user_message != expected:
            raise ValueError(f"{request.custom_id}: the request is not exactly the record's text")
        if request.custom_id in request.user_message:
            raise ValueError(f"{request.custom_id}: the study id is inside the message")


# --- dry run ---------------------------------------------------------------------


def plan(
    records: list[pg.EvalRecord],
    spec: RunSpec,
    *,
    provider: str,
    chunk: int,
    scope: dict[str, Any],
    batch_of: dict[str, str],
    max_tokens: int,
    protocol: dict[str, Any],
) -> dict[str, Any]:
    """Counts, prompt sizes and an estimated cost from the prompt sizes. No network, no key."""
    requests = pg.requests_for(records)
    assert_blind(spec, requests, records, protocol)
    use_batches = provider == "anthropic" and len(records) > pg.DIRECT_LIMIT
    expected = pg.estimate(records, spec, provider=provider, batch=use_batches)
    priced = expected["priced"]
    price = pg.price_for(provider, spec.model)
    n = len(records)
    tokens = expected["tokens"]
    system_tokens = math.ceil(len(spec.system) / expected["assumptions"]["chars_per_token"])
    record_tokens = sum(math.ceil(len(r.user_message) / expected["assumptions"]["chars_per_token"]) for r in requests)
    no_cache = {"input_tokens": system_tokens * n + record_tokens, "cache_read_tokens": 0, "cache_write_tokens": 0}
    heavy = pg.estimate(records, spec, provider=provider, batch=use_batches, output_tokens_per_record=HEAVY_OUTPUT_TOKENS)

    def cost(output_per_record: int) -> float | None:
        if price is None:
            return None
        return pg.cost_usd({**no_cache, "output_tokens": output_per_record * n}, price, batch=use_batches)

    labels = Counter(r.label for r in records)
    return {
        "scope": scope,
        "provider": provider,
        "model": spec.model,
        "effort": spec.effort,
        "records": n,
        "labels": dict(labels),
        "workspace_batches": len({batch_of.get(r.study_id, "?") for r in records}),
        "requests": {
            "mode": "Message Batches" if use_batches else "direct calls",
            "calls": math.ceil(n / chunk) if use_batches else n,
            "records_per_call": chunk if use_batches else 1,
        },
        "prompt": {
            "system_tokens": system_tokens,
            "record_tokens_mean": round(record_tokens / n, 1) if n else 0.0,
            "record_tokens_max": max((math.ceil(len(r.user_message) / expected["assumptions"]["chars_per_token"]) for r in requests), default=0),
        },
        "tokens_expected": tokens,
        "cost_usd": {
            "expected": expected["cost_usd"],
            "expected_note": f"{expected['assumptions']['output_tokens_per_record']} output tokens per record (thinking included), system prompt cached after the first record",
            "no_cache_expected_output": cost(expected["assumptions"]["output_tokens_per_record"]),
            f"no_cache_{HEAVY_OUTPUT_TOKENS}_output_tokens": cost(HEAVY_OUTPUT_TOKENS),
            "hard_ceiling": cost(max_tokens),
            "hard_ceiling_note": f"every record returns max_tokens ({max_tokens}) and nothing is cached; a call cannot cost more",
            "heavy_with_cache": heavy["cost_usd"],
        },
        "priced": priced,
        "prices_as_of": expected["prices_as_of"],
        "blind_check": "passed",
        "network_calls": 0,
    }


# --- the run ---------------------------------------------------------------------


def driver_options(provider: str) -> dict[str, Any]:
    """The driver options a product run uses (`agent_runs.start_run`), so a measurement runs the same way."""
    from scholar_harness.screening.agent_runs import CHUNK

    return {"direct_limit": pg.DIRECT_LIMIT, "max_per_batch": CHUNK} if provider == "anthropic" else {}


def execute(
    driver: Driver,
    records: list[pg.EvalRecord],
    spec: RunSpec,
    *,
    provider: str,
    protocol: dict[str, Any],
    cost_ceiling_usd: float | None = None,
) -> tuple[list[DriverResult], str | None]:
    """Send the records and return the results; stops, like a product run, once the cost passes the ceiling.

    Returns the results and a stop code (`COST_CEILING_REACHED`) or None.
    """
    requests = pg.requests_for(records)
    assert_blind(spec, requests, records, protocol)
    price = pg.price_for(provider, spec.model)
    if cost_ceiling_usd is not None and price is None:
        raise ValueError(f"{provider}/{spec.model} has no price in the price table, so a ceiling cannot be enforced")
    use_batches = provider == "anthropic" and len(records) > pg.DIRECT_LIMIT
    state = {"cost": 0.0, "stopped": None}

    def on_result(result: DriverResult) -> None:
        if price is not None:
            state["cost"] += pg.cost_usd(result.usage.as_dict(), price, batch=use_batches, ndigits=COST_DIGITS)
        if cost_ceiling_usd is not None and state["cost"] >= cost_ceiling_usd:
            state["stopped"] = "COST_CEILING_REACHED"

    results = driver.run(requests, spec, on_result=on_result, cancelled=lambda: state["stopped"] is not None)
    return results, state["stopped"]


# --- the report ------------------------------------------------------------------


def _gate(name_gate: Gate, includes: int, kept: int, *, strict_kept: int | None = None, measured: bool = True) -> dict[str, Any]:
    """A draft gate. `passes` is the product's rule (a failed call is Unclear, so kept) and needs a run that
    measured something; `passes_if_failed_calls_were_misses` is the same gate with every failed call a miss."""
    strict = kept if strict_kept is None else strict_kept
    lower, strict_lower = pg.wilson_lower(kept, includes), pg.wilson_lower(strict, includes)
    enough = includes >= name_gate.min_includes
    return {
        "gate": name_gate.name,
        "draft_min_includes": name_gate.min_includes,
        "draft_recall_ci_low": name_gate.recall_ci_low,
        "includes_compared": includes,
        "enough_includes": enough,
        "include_recall_ci_low": round(lower, 4),
        "include_recall_ci_low_if_failed_calls_were_misses": round(strict_lower, 4),
        "passes": measured and enough and lower >= name_gate.recall_ci_low,
        "passes_if_failed_calls_were_misses": measured and enough and strict_lower >= name_gate.recall_ci_low,
    }


def analyse(
    *,
    scope: dict[str, Any],
    records: list[pg.EvalRecord],
    results: list[DriverResult],
    protocol: dict[str, Any],
    provider: str,
    spec: RunSpec,
    batch_of: dict[str, str],
    stopped: str | None = None,
    plan_: dict[str, Any] | None = None,
    not_reported: str | None = None,
) -> dict[str, Any]:
    """The M9a report. Records without a result are `not_reached` and are not scored."""
    got = {r.custom_id for r in results}
    reached = [r for r in records if r.study_id in got]
    not_reached = sorted(r.study_id for r in records if r.study_id not in got)
    use_batches = provider == "anthropic" and len(records) > pg.DIRECT_LIMIT
    base = pg.report(
        frozen={"set_sha256": scope["set_sha256"], "counts": dict(Counter(r.label for r in records))},
        records=reached,
        results=results,
        protocol=protocol,
        provider=provider,
        spec=spec,
        batch=use_batches,
        not_reported=not_reported,
    )
    rows = base["records"]
    label_of = {r["study_id"]: r["label"] for r in rows}
    price = pg.price_for(provider, spec.model)

    def row_cost(row: dict[str, Any]) -> float | None:
        if price is None or not row.get("usage"):
            return None
        return pg.cost_usd(row["usage"], price, batch=use_batches, ndigits=COST_DIGITS)

    for row in rows:
        row["cost_usd"] = row_cost(row)
        row["batch"] = batch_of.get(row["study_id"], "?")

    # Confusion: the researcher's label (rows) against the engine's outcome (columns).
    confusion: dict[str, dict[str, int]] = {lab: {"INCLUDE": 0, "MAYBE": 0, "EXCLUDE": 0} for lab in ("INCLUDE", "EXCLUDE")}
    driver_failed = {"INCLUDE": 0, "EXCLUDE": 0}
    for row in rows:
        confusion[row["label"]][row["outcome"]] += 1
        if row["driver_status"] != "ok":
            driver_failed[row["label"]] += 1
    agent_include = confusion["INCLUDE"]["INCLUDE"] + confusion["EXCLUDE"]["INCLUDE"]
    agent_include_or_unclear = agent_include + confusion["INCLUDE"]["MAYBE"] + confusion["EXCLUDE"]["MAYBE"]
    human_includes = sum(confusion["INCLUDE"].values())
    kept = human_includes - confusion["INCLUDE"]["EXCLUDE"]
    failed_includes = sum(1 for r in rows if r["label"] == "INCLUDE" and r["driver_status"] != "ok")
    strict_kept = kept - failed_includes

    def ratio(a: int, b: int) -> float | None:
        return round(a / b, 4) if b else None

    # What the agent left undecided, and what went wrong with an answer.
    results_by_id = {r.custom_id: r for r in results}
    undecided = [r for r in rows if r["outcome"] == "MAYBE" and r["driver_status"] == "ok"]
    for row in undecided:
        output = results_by_id[row["study_id"]].output
        row["cannot_decide"] = isinstance(output, dict) and output.get("cannot_decide") is True
    reasons = Counter(
        "cannot_decide" if r["cannot_decide"] else "failed_check" if r["failed_checks"] else "criterion_not_reported" for r in undecided
    )
    by_status = defaultdict(list)
    for row in rows:
        if row["driver_status"] != "ok":
            by_status[row["driver_status"]].append(row["study_id"])
    check_failures = Counter(name for row in rows for name in row["failed_checks"] if row["driver_status"] == "ok")

    # Tokens and cost.
    usages = [r["usage"] for r in rows if r.get("usage")]
    per_record_tokens = [u["input_tokens"] + u["output_tokens"] for u in usages]
    totals = base["usage"]
    n = len(rows)

    # Batches against the draft thresholds (descriptive: the gate itself is review-wide).
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["batch"]].append(row)
    batches = []
    for name in sorted(grouped):
        group = grouped[name]
        incl = [r for r in group if r["label"] == "INCLUDE"]
        missed = [r["study_id"] for r in incl if r["outcome"] == "EXCLUDE"]
        recall = ratio(len(incl) - len(missed), len(incl))
        batches.append({
            "batch": name,
            "records": len(group),
            "human_includes": len(incl),
            "missed_includes": missed,
            "include_recall": recall,
            "unclear": sum(1 for r in group if r["outcome"] == "MAYBE"),
            "below_l1": recall is not None and recall < L1.recall_ci_low,
            "below_l2": recall is not None and recall < L2.recall_ci_low,
        })

    warnings = []
    if not_reached and stopped is None:
        warnings.append(f"{len(not_reached)} record(s) got no result although the run was not stopped; they are not scored. The driver dropped them.")
    if not base["measured"]:
        warnings.append("no call succeeded: nothing was measured, and no gate passes")
    if scope.get("limit"):
        warnings.append(f"SMOKE RUN: only the first {scope['limit']} records by study id; not a measurement of the set")
    report = {
        "milestone": "M9a-measure",
        "task_version": base["task_version"],
        "prompt_sha256": base["prompt_sha256"],
        "not_reported_policy": base["not_reported_policy"],
        "provider": provider,
        "model": spec.model,
        "effort": spec.effort,
        "scope": scope,
        "records": len(records),
        "scored": n,
        "not_reached": {"count": len(not_reached), "study_ids": not_reached},
        "stopped": stopped,
        "warnings": warnings,
        "measured": base["measured"],
        "include_recall": {
            "point": ratio(kept, human_includes),
            "ci_low": base["score"]["include_recall_ci_low"],
            "missed_includes": base["score"]["missed_includes"],
            "if_failed_calls_counted_as_missed": ratio(strict_kept, human_includes),
            "ci_low_if_failed_calls_counted_as_missed": round(pg.wilson_lower(strict_kept, human_includes), 4),
        },
        "precision_on_includes": {
            "agent_include": ratio(confusion["INCLUDE"]["INCLUDE"], agent_include),
            "agent_include_or_unclear": ratio(confusion["INCLUDE"]["INCLUDE"] + confusion["INCLUDE"]["MAYBE"], agent_include_or_unclear),
        },
        "exclusion_rate_on_human_excludes": ratio(confusion["EXCLUDE"]["EXCLUDE"], sum(confusion["EXCLUDE"].values())),
        "unclear_rate": ratio(sum(1 for r in rows if r["outcome"] == "MAYBE"), n),
        "confusion": {"rows": "researcher", "columns": "agent outcome", "table": confusion, "driver_failed": driver_failed},
        "gates": [_gate(g, human_includes, kept, strict_kept=strict_kept, measured=base["measured"]) for g in GATES],
        "agent_left_undecided": {
            "count": len(undecided),
            "by_reason": dict(reasons),
            "study_ids": [r["study_id"] for r in undecided],
        },
        "answers_not_usable": {
            "driver_statuses": base["driver_statuses"],
            "truncated": by_status.get("truncated", []),
            "invalid": by_status.get("invalid", []),
            "refusal": by_status.get("refusal", []),
            "error": by_status.get("error", []),
            "failed_checks_on_ok_answers": dict(check_failures),
        },
        "usage": {
            "totals": totals,
            "tokens_per_record_mean": round(sum(per_record_tokens) / len(per_record_tokens), 1) if per_record_tokens else None,
            "tokens_per_record_max": max(per_record_tokens, default=None),
        },
        "cost_usd": {
            "total": base["cost_usd"],
            "per_record": round(base["cost_usd"] / n, 6) if base["cost_usd"] is not None and n else None,
            "per_1000_records": base["cost_per_1000_records_usd"],
            "batch_discount_applied": use_batches,
            "prices_as_of": base["prices_as_of"],
        },
        "batches": batches,
        "batches_below_draft_thresholds": {
            "below_l1": [b["batch"] for b in batches if b["below_l1"]],
            "below_l2": [b["batch"] for b in batches if b["below_l2"]],
            "note": "descriptive: a batch holds few includes; the gates above are the review-wide figures",
        },
        "records_detail": rows,
    }
    if plan_ is not None:
        report["plan"] = plan_
    return report


def render_markdown(report: dict[str, Any]) -> str:
    """The report a person reads; the JSON holds every record."""

    def pct(value: float | None) -> str:
        return "n/a" if value is None else f"{value:.1%}"

    rc, pr, cm = report["include_recall"], report["precision_on_includes"], report["confusion"]["table"]
    lines = [
        f"# M9a-measure report: {report['provider']}/{report['model']} ({report['effort']} effort)",
        "",
        f"Task `{report['task_version']}`, prompt `{report['prompt_sha256']}`, outcomes derived under the "
        f"`{report.get('not_reported_policy', 'unclear')}` not-reported rule. Scope `{report['scope']['scope']}`, "
        f"set `{report['scope']['set_sha256']}`, researcher's decisions {report['scope']['human_confirmation']}.",
        *[f"**WARNING: {w}**" for w in report["warnings"]],
        f"{report['scored']} of {report['records']} records scored; {report['not_reached']['count']} not reached"
        + (f" (run stopped: {report['stopped']})." if report["stopped"] else "."),
        "",
        "## Recall and precision on includes",
        f"- Include recall (an Unclear is kept): {pct(rc['point'])}, 95% Wilson lower bound {pct(rc['ci_low'])}; "
        f"missed includes: {len(rc['missed_includes'])}.",
        f"- Same, if failed calls count as misses: {pct(rc['if_failed_calls_counted_as_missed'])} "
        f"(lower bound {pct(rc['ci_low_if_failed_calls_counted_as_missed'])}).",
        f"- Precision on includes: {pct(pr['agent_include'])} of the agent's Includes are the researcher's includes; "
        f"{pct(pr['agent_include_or_unclear'])} counting its Unclear as an include.",
        f"- Excludes caught: {pct(report['exclusion_rate_on_human_excludes'])} of the researcher's excludes. Unclear rate: {pct(report['unclear_rate'])}.",
        "",
        "## Confusion (rows: researcher, columns: agent)",
        "| researcher \\ agent | Include | Unclear | Exclude | of which the call failed |",
        "| :-- | --: | --: | --: | --: |",
    ]
    for label in ("INCLUDE", "EXCLUDE"):
        row = cm[label]
        lines.append(f"| {label} | {row['INCLUDE']} | {row['MAYBE']} | {row['EXCLUDE']} | {report['confusion']['driver_failed'][label]} |")
    lines += ["", "## Draft ladder gates (review-wide)", "| gate | includes compared | needed | recall lower bound | if failed calls were misses | needed | passes | passes if failed calls were misses |", "| :-- | --: | --: | --: | --: | --: | :-- | :-- |"]
    for g in report["gates"]:
        lines.append(
            f"| {g['gate']} | {g['includes_compared']} | {g['draft_min_includes']} | {pct(g['include_recall_ci_low'])} | "
            f"{pct(g['include_recall_ci_low_if_failed_calls_were_misses'])} | "
            f"{pct(g['draft_recall_ci_low'])} | {'yes' if g['passes'] else 'no'} | {'yes' if g['passes_if_failed_calls_were_misses'] else 'no'} |"
        )
    au = report["answers_not_usable"]
    lines += [
        "",
        "## Undecided, truncated and malformed",
        f"- Left undecided by the agent (call ok, outcome Unclear): {report['agent_left_undecided']['count']}, "
        f"by reason {report['agent_left_undecided']['by_reason']}.",
        f"- Driver statuses: {au['driver_statuses']}; truncated {len(au['truncated'])}, invalid {len(au['invalid'])}, "
        f"refused {len(au['refusal'])}, error {len(au['error'])}.",
        f"- Failed checks on answers that parsed: {au['failed_checks_on_ok_answers'] or 'none'}.",
        "",
        "## Tokens and cost",
        f"- Totals: {report['usage']['totals']}; mean {report['usage']['tokens_per_record_mean']} and max "
        f"{report['usage']['tokens_per_record_max']} tokens per record.",
        f"- Cost: total ${report['cost_usd']['total']}, per record ${report['cost_usd']['per_record']}, per 1,000 records "
        f"${report['cost_usd']['per_1000_records']} (prices as of {report['cost_usd']['prices_as_of']}"
        f"{', Batches half price' if report['cost_usd']['batch_discount_applied'] else ''}).",
        "",
        "## Batches under the draft thresholds",
        f"- Under L1's recall ({L1.recall_ci_low}): {', '.join(report['batches_below_draft_thresholds']['below_l1']) or 'none'}.",
        f"- Under L2's recall ({L2.recall_ci_low}): {', '.join(report['batches_below_draft_thresholds']['below_l2']) or 'none'}.",
        f"- {report['batches_below_draft_thresholds']['note']}.",
        "",
    ]
    return "\n".join(lines)


def write_report(report: dict[str, Any], out_dir: Path, stem: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / f"{stem}.json", out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def measure(
    workspace: Path,
    *,
    scope: str,
    provider: str,
    model: str,
    effort: str,
    max_tokens: int,
    driver: Driver | None,
    cost_ceiling_usd: float | None = None,
    limit: int = 0,
    frozen: dict[str, Any] | None = None,
    out_dir: Path = OUT_DIR,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    task_version: str | None = None,
    not_reported: str | None = None,
) -> dict[str, Any]:
    """Plan (`driver` None: dry run, no network) or run and write the report.

    ``not_reported`` derives the outcomes under that policy instead of the
    protocol's own (H-screening-drafts: to see ``decisive_first`` on the frozen set).

    ``task_version`` measures a candidate task version (H-screening-drafts, ``screen-v2``);
    ``None`` is the default task, the one product runs use.

    Returns the plan for a dry run, else the report with its `paths`.
    """
    from scholar_harness.screening.agent_runs import CHUNK

    records, scope_info = load_records(workspace, scope, frozen=frozen)
    if limit:
        inc = [r for r in records if r.label == "INCLUDE"][: (limit + 1) // 2]
        exc = [r for r in records if r.label == "EXCLUDE"][: limit // 2]
        records = inc + exc
        scope_info = {**scope_info, "limit": limit}
    protocol = json.loads((workspace / "protocol.json").read_text(encoding="utf-8"))
    if not_reported is None:
        # H-screening-drafts (review F5): the rule in force, with the workspace's method amendments.
        from scholar_harness.screening.method import effective_method

        not_reported = effective_method(workspace).config.not_reported
    spec = pg.run_spec(protocol, model=model, effort=effort, max_tokens=max_tokens, task_version=task_version)
    batch_of = batch_index(workspace)
    the_plan = plan(records, spec, provider=provider, chunk=CHUNK, scope=scope_info, batch_of=batch_of, max_tokens=max_tokens, protocol=protocol)
    if driver is None:
        return the_plan
    results, stopped = execute(driver, records, spec, provider=provider, protocol=protocol, cost_ceiling_usd=cost_ceiling_usd)
    report = analyse(
        scope=scope_info, records=records, results=results, protocol=protocol, provider=provider,
        spec=spec, batch_of=batch_of, stopped=stopped, plan_=the_plan, not_reported=not_reported,
    )
    report["finished_at"] = now().isoformat()
    stamp = now().strftime("%Y%m%dT%H%M%SZ")
    version = f"_{spec.task_version}" if spec.task_version else ""
    json_path, md_path = write_report(report, out_dir, f"measure_{stamp}_{provider}_{model}_{effort}{version}")
    report["paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return report
