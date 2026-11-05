"""The screening prompt gate (agent-system §5; decisions 2026-11-05).

A task version (prompt, schema, provider, model, effort) passes when the 95%
Wilson lower bound of its include-recall on the frozen v03 set is at least
`BAR` (0.90). Include-recall counts an agent Unclear as not excluded, because
Unclear goes on to full text. The report also gives how much work the agent
would save (the share of confirmed excludes it excludes) and its Unclear
rate; those are reported, not gated.

- **The set** is every human-confirmed include of `uav-crop-weed-v03` and
  1,000 of its confirmed excludes, drawn with a fixed seed. It is stored as
  study ids, labels and input hashes only; the text is read from the
  workspace at run time and checked against those hashes. The workspace is
  only read, and its decision files must still match the researcher's signed
  confirmation (`HUMAN_CONFIRMATION.json`), compared with LF line endings.
- **The outcome** of every record comes from the engine's own validators and
  rule table (`scholar_harness.screening.proposals`), exactly as for a run;
  a refusal, truncation, invalid answer or error is Unclear.
- **Cost** is estimated before a run from the dated price table and measured
  after it from the providers' usage.
"""

from __future__ import annotations

import glob
import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scholar_agent.drivers import DriverResult, RunSpec, ScreeningRequest
from scholar_agent.tasks import screening as task_mod

BAR = 0.90
SEED = 20261105
EXCLUDES = 1000
SET_FILE = task_mod.HERE / "eval" / "v03_set.json"
RESULTS_DIR = task_mod.HERE / "eval" / "results"


def _has_abstract(abstract: str | None) -> bool:
    text = (abstract or "").strip()
    return bool(text) and text != "No abstract available."


# --- the frozen set ------------------------------------------------------------


def verify_confirmation(workspace: Path) -> dict[str, Any]:
    """The decision files must be the ones the researcher signed (LF-normalised)."""
    path = workspace / "literature" / "screening" / "HUMAN_CONFIRMATION.json"
    confirmation = json.loads(path.read_text(encoding="utf-8"))
    changed = []
    for artifact in confirmation["artifacts"]:
        data = (workspace / artifact["path"]).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            changed.append(artifact["path"])
    if changed:
        raise ValueError(f"{len(changed)} decision file(s) differ from the signed confirmation, e.g. {changed[0]}")
    return confirmation


def _papers(workspace: Path) -> dict[str, dict[str, Any]]:
    papers: dict[str, dict[str, Any]] = {}
    for name in sorted(glob.glob(str(workspace / "literature" / "screening" / "batch_[0-9][0-9][0-9].json"))):
        for paper in json.loads(Path(name).read_text(encoding="utf-8"))["papers"]:
            papers[str(paper["workspace_id"])] = paper
    return papers


def _labels(workspace: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for name in sorted(glob.glob(str(workspace / "literature" / "screening" / "batch_[0-9][0-9][0-9]_decisions.json"))):
        payload = json.loads(Path(name).read_text(encoding="utf-8"))
        for row in payload["decisions"] if isinstance(payload, dict) else payload:
            labels[str(row["workspace_id"])] = str(row["decision"])
    return labels


def _record(paper: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    abstract = paper.get("abstract") if _has_abstract(paper.get("abstract")) else None
    return paper.get("title"), abstract, (str(paper["year"]) if paper.get("year") else None)


def build_set(workspace: Path, *, excludes: int = EXCLUDES, seed: int = SEED) -> dict[str, Any]:
    """Every confirmed include and `excludes` confirmed excludes, seeded; ids and hashes only."""
    from scholar_harness.screening.proposals import input_sha256

    confirmation = verify_confirmation(workspace)
    labels, papers = _labels(workspace), _papers(workspace)
    includes = sorted(s for s, label in labels.items() if label == "INCLUDE")
    pool = sorted(s for s, label in labels.items() if label == "EXCLUDE")
    chosen = sorted(random.Random(seed).sample(pool, min(excludes, len(pool))))
    records = [
        {"study_id": s, "label": labels[s], "input_sha256": input_sha256(*_record(papers[s]))}
        for s in sorted(includes + chosen)
    ]
    body = {
        "source": workspace.name,
        "confirmation": {"reviewer": confirmation.get("reviewer", {}).get("name"), "summary": confirmation.get("summary")},
        "seed": seed,
        "counts": dict(Counter(r["label"] for r in records)),
        "records": records,
    }
    body["set_sha256"] = "sha256:" + hashlib.sha256(json.dumps(records, sort_keys=True).encode("utf-8")).hexdigest()
    return body


@dataclass(frozen=True)
class EvalRecord:
    study_id: str
    label: str
    title: str | None
    abstract: str | None
    published: str | None


def load_set(workspace: Path, frozen: dict[str, Any]) -> list[EvalRecord]:
    """The frozen set's records with their text, each checked against its stored hash."""
    from scholar_harness.screening.proposals import input_sha256

    papers = _papers(workspace)
    out = []
    for item in frozen["records"]:
        title, abstract, published = _record(papers[item["study_id"]])
        if input_sha256(title, abstract, published) != item["input_sha256"]:
            raise ValueError(f"{item['study_id']}: the record text changed since the set was frozen")
        out.append(EvalRecord(item["study_id"], item["label"], title, abstract, published))
    return out


# --- run, score, cost ---------------------------------------------------------


def run_spec(protocol: dict[str, Any], *, model: str, effort: str, max_tokens: int) -> RunSpec:
    task = task_mod.load_task()
    criteria = task_mod.criteria_from_protocol(protocol)
    return RunSpec(
        system=task_mod.system_prompt(task, criteria),
        schema=task_mod.output_schema([c.id for c in criteria]),
        model=model,
        effort=effort,
        max_tokens=max_tokens,
    )


def requests_for(records: list[EvalRecord]) -> list[ScreeningRequest]:
    return [ScreeningRequest(r.study_id, task_mod.record_message(r.title, r.abstract, r.published)) for r in records]


def derive(record: EvalRecord, result: DriverResult | None, protocol: dict[str, Any]) -> tuple[str, str | None, list[dict[str, Any]]]:
    """The engine's outcome for one record; any non-ok or missing result is Unclear."""
    from scholar_harness.screening import proposals as pr

    criteria = pr.Criteria.from_protocol(protocol)
    if result is None or result.status != "ok":
        return "MAYBE", None, [{"name": "driver", "ok": False, "detail": result.status if result else "no result"}]
    output = task_mod.to_proposal_output(result.output, record.title, record.abstract, record.published)
    checks = pr.validate_output(output, criteria, pr.record_text(record.title, record.abstract, record.published))
    outcome, reason = pr.derive_outcome(output, criteria, checks)
    return outcome, reason, checks


def wilson_lower(successes: int, total: int, z: float = 1.959964) -> float:
    if total == 0:
        return 0.0
    p = successes / total
    centre = p + z * z / (2 * total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return (centre - margin) / (1 + z * z / total)


def score(outcomes: dict[str, str], labels: dict[str, str]) -> dict[str, Any]:
    includes = [s for s, label in labels.items() if label == "INCLUDE"]
    excludes = [s for s, label in labels.items() if label == "EXCLUDE"]
    kept = [s for s in includes if outcomes.get(s, "MAYBE") != "EXCLUDE"]
    excluded_right = [s for s in excludes if outcomes.get(s) == "EXCLUDE"]
    unclear = [s for s in labels if outcomes.get(s, "MAYBE") == "MAYBE"]
    recall = len(kept) / len(includes) if includes else 0.0
    lower = wilson_lower(len(kept), len(includes))
    return {
        "include_recall": round(recall, 4),
        "include_recall_ci_low": round(lower, 4),
        "bar": BAR,
        "passes": lower >= BAR,
        "missed_includes": sorted(set(includes) - set(kept)),
        # Reported, not gated (decision 2026-11-05):
        "exclusion_rate_on_confirmed_excludes": round(len(excluded_right) / len(excludes), 4) if excludes else 0.0,
        "unclear_rate": round(len(unclear) / len(labels), 4) if labels else 0.0,
        "outcomes": dict(Counter(outcomes.get(s, "MAYBE") for s in labels)),
    }


def price_for(provider: str, model: str) -> dict[str, float] | None:
    return (task_mod.load_prices().get(provider) or {}).get(model)


def cost_usd(usage: dict[str, int], price: dict[str, float], *, batch: bool) -> float:
    factor = task_mod.load_prices()["batch_discount"] if batch else 1.0
    uncached = max(0, usage["input_tokens"] - usage["cache_read_tokens"] - usage["cache_write_tokens"])
    total = (
        uncached * price["input"]
        + usage["cache_read_tokens"] * price["cache_read"]
        + usage["cache_write_tokens"] * price["cache_write"]
        + usage["output_tokens"] * price["output"]
    ) / 1_000_000
    return round(total * factor, 4)


def estimate(records: list[EvalRecord], spec: RunSpec, *, provider: str, output_tokens_per_record: int = 600, chars_per_token: float = 3.5) -> dict[str, Any]:
    """A pre-run estimate: input from text length, output assumed (thinking included).

    It is an estimate, never a measurement: the tokenizer differs by model, and
    thinking at low effort varies. The measured cost replaces it after the run.
    """
    system_tokens = math.ceil(len(spec.system) / chars_per_token)
    record_tokens = sum(math.ceil(len(r.user_message) / chars_per_token) for r in requests_for(records))
    n = len(records)
    usage = {
        "input_tokens": record_tokens + system_tokens * n,
        "cache_read_tokens": system_tokens * max(0, n - 1),
        "cache_write_tokens": system_tokens,
        "output_tokens": output_tokens_per_record * n,
    }
    price = price_for(provider, spec.model)
    prices = task_mod.load_prices()
    return {
        "records": n,
        "tokens": usage,
        "assumptions": {"chars_per_token": chars_per_token, "output_tokens_per_record": output_tokens_per_record},
        "cost_usd": cost_usd(usage, price, batch=True) if price else None,
        "prices_as_of": prices["as_of"],
        "priced": price is not None,
    }


def report(
    *,
    frozen: dict[str, Any],
    records: list[EvalRecord],
    results: list[DriverResult],
    protocol: dict[str, Any],
    provider: str,
    spec: RunSpec,
    batch: bool,
) -> dict[str, Any]:
    by_id = {r.custom_id: r for r in results}
    outcomes, per_record = {}, []
    usage = Counter()
    for record in records:
        result = by_id.get(record.study_id)
        outcome, reason, checks = derive(record, result, protocol)
        outcomes[record.study_id] = outcome
        if result is not None:
            usage.update(result.usage.as_dict())
        per_record.append({
            "study_id": record.study_id,
            "label": record.label,
            "outcome": outcome,
            "reason_code": reason,
            "driver_status": result.status if result else "missing",
            "failed_checks": [c["name"] for c in checks if not c["ok"]],
        })
    totals = {k: int(usage.get(k, 0)) for k in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")}
    price = price_for(provider, spec.model)
    measured = cost_usd(totals, price, batch=batch) if price else None
    task = task_mod.load_task()
    return {
        "task_version": task.task_version,
        "prompt_sha256": task.prompt_sha256,
        "provider": provider,
        "model": spec.model,
        "effort": spec.effort,
        "set_sha256": frozen["set_sha256"],
        "counts": frozen["counts"],
        "driver_statuses": dict(Counter(r["driver_status"] for r in per_record)),
        "score": score(outcomes, {r.study_id: r.label for r in records}),
        "usage": totals,
        "cost_usd": measured,
        "cost_per_1000_records_usd": round(measured * 1000 / len(records), 2) if measured is not None and records else None,
        "prices_as_of": task_mod.load_prices()["as_of"],
        "records": per_record,
    }
