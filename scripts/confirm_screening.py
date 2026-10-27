"""Screening confirmation producer (agent-layer Phase C, spec ``06`` §4).

Signs ``literature/screening/HUMAN_CONFIRMATION.json`` under a workspace:

* discovers **every** decision artifact under ``literature/screening/`` and
  refuses ``BLOCKED_INPUT`` naming uncovered files — the reviewer does not
  partially bless a set;
* hashes each artifact at review start, stages the bytes, and re-verifies the
  on-disk hash at write time — an artifact mutated between the reviewer's look
  and the write refuses ``PARENT_HASH_MISMATCH``, never a silent re-bind;
* never signs for anyone: reviewer identity is supplied explicitly (queue or
  interactive prompts) and confirmed interactively.

Refusal convention (mirrors ``scholar_harness.contracts.envelope``): a JSON
refusal object on stderr, exit code 1; ``REFUSED`` is the export-gate-only
code and this producer refuses with registry codes only.

Why no real ``--retrospective`` path exists for the pilot corpus: the pilot
stays labelled agent-mutual (owner decision, spec `06` header). ``--retrospective``
only relabels a fresh signature as retrospective, and the tool states plainly
that the export gate will never accept it.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import sys
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scholar_harness.contracts.confirmation.api import (
    ConfirmationRefusalError,
    discover_decision_artifacts,
    enforce_coverage,
    validate,
)
from scholar_harness.contracts.envelope.registry import RefusalCode

CONFIRMATION_RELPATH = "literature/screening/HUMAN_CONFIRMATION.json"
_ARTIFACT_SCHEMA = "HumanConfirmation@1"

_MUTATION_PROBE: Any = None  # test seam: invoked after staging, before write


def _refuse(refusal_code: RefusalCode | str, detail: str) -> int:
    print(
        json.dumps(
            {
                "result": "rejected",
                "status": str(refusal_code),
                "refusal_code": str(refusal_code),
                "detail": detail,
            }
        ),
        file=sys.stderr,
    )
    return 1


def _doc_loader():
    log_event_path = (
        ROOT / ".agents" / "skills" / "workspace-manager" / "scripts" / "log_event.py"
    )
    spec = importlib.util.spec_from_file_location("workspace_log_event", log_event_path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:  # pragma: no cover — defensive
        raise ImportError(log_event_path)
    spec.loader.exec_module(module)
    return module.log_project_event


def _sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_decision_file(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("decisions"), list):
        return payload["decisions"]
    if isinstance(payload, list):
        return payload
    raise ValueError("expected a JSON list or wrapper object")


def _read_artifact(ws: Path, relative: str) -> list[dict[str, Any]]:
    candidate = PurePosixPath(relative)
    path = ws / Path(*candidate.parts)
    return _load_decision_file(path)


def _study_ids(ws: Path, artifacts: list[str]) -> list[str]:
    """Workspace study ids in artifact order, each exactly once (no duplicates)."""

    ids: list[str] = []
    for relative in artifacts:
        for entry in _read_artifact(ws, relative):
            study_id = str(entry.get("study_id") or entry.get("workspace_id") or "")
            if not study_id:
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"decision artifact {relative!r} has a record without a "
                    "study/workspace id; a confirmation cannot bind unnamed studies",
                )
            if study_id not in ids:
                ids.append(study_id)
    if not ids:
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT,
            "the decision artifacts record no study ids; nothing to confirm",
        )
    return ids


def _prompt_nonblank(label: str) -> str:
    for _ in range(3):
        try:
            answer = input(f"{label}: ").strip()
        except EOFError as exc:
            raise ConfirmationRefusalError(
                RefusalCode.BLOCKED_INPUT,
                f"no {label} supplied (interactive input ended)",
            ) from exc
        if answer:
            return answer
        print(f"  a non-empty {label} is required — the signature names a person")
    raise ConfirmationRefusalError(
        RefusalCode.INVALID_OUTPUT, f"{label} left empty three times; refusing to sign"
    )


def _prompt_verdict(study_id: str) -> dict[str, Any] | None:
    """Prompt one study; ``None`` confirms (no amendments carried)."""

    while True:
        try:
            answer = (
                input(
                    f"  [STU] {study_id} — confirm / change / defer (C/d/e, default C): "
                )
                .strip()
                .lower()
            )
        except EOFError as exc:
            raise ConfirmationRefusalError(
                RefusalCode.BLOCKED_INPUT, "interactive input ended mid-review"
            ) from exc
        if answer in ("", "c", "confirm"):
            return None
        if answer in ("d", "change"):
            amended = _prompt_nonblank("amended verdict")
            rationale = _prompt_nonblank("rationale (required for a change)")
            return {"verdict": "changed", "amended": amended, "rationale": rationale}
        if answer in ("e", "defer"):
            reason = _prompt_nonblank("defer reason")
            return {"verdict": "deferred", "defer_reason": reason}
        print("  answer C (confirm), d (change), or e (defer)")


def _label_for(relative: str) -> str:
    name = relative.rsplit("/", 1)[-1]
    if "screener2" in name:
        return "second-screen batch decisions"
    if name.startswith("_adjudication"):
        return "adjudication group decisions"
    return "batch decisions"


def _build_record(
    ws: Path,
    reviewer: dict[str, str],
    overrides: dict[str, dict[str, Any]],
    *,
    retrospective: bool,
    study_ids: list[str],
    artifacts: list[str],
    hashes: dict[str, str],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    confirmed = changed = deferred = 0
    for study_id in study_ids:
        override = overrides.get(study_id)
        if override is None:
            rows.append({"study_id": study_id, "verdict": "confirmed"})
            confirmed += 1
            continue
        verdict = override.get("verdict")
        if verdict not in ("changed", "deferred"):
            rows.append({"study_id": study_id, "verdict": "confirmed"})
            confirmed += 1
            continue
        row = {"study_id": study_id, "verdict": verdict}
        if verdict == "changed":
            row["amended"] = override.get("amended")
            row["rationale"] = override.get("rationale")
            changed += 1
        else:
            row["defer_reason"] = override.get("defer_reason")
            deferred += 1
        rows.append(row)
    return {
        "schema": _ARTIFACT_SCHEMA,
        "retrospective": bool(retrospective),
        "reviewer": {
            "name": reviewer["name"],
            "affiliation": reviewer["affiliation"],
            "signing_capacity": "lead_reviewer",
        },
        "artifacts": [
            {
                "path": relative,
                "sha256": hashes[relative],
                "label": _label_for(relative),
            }
            for relative in artifacts
        ],
        "decisions": rows,
        "summary": {
            "considered": len(study_ids),
            "confirmed": confirmed,
            "changed": changed,
            "deferred": deferred,
        },
        "provenance": {
            "tool": "confirm_screening.py",
            "created_at": datetime.datetime.now(datetime.UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        },
    }


def _run(
    ws: Path,
    reviewer: dict[str, str],
    overrides: dict[str, dict[str, Any]],
    artifact_list: list[str] | None,
    *,
    retrospective: bool,
    interactive: bool,
) -> int:
    screening = ws / "literature" / "screening"
    if not screening.is_dir():
        return _refuse(
            RefusalCode.BLOCKED_INPUT,
            f"{ws.name} has no literature/screening directory; there are no "
            "decision artifacts to confirm",
        )

    artifacts = discover_decision_artifacts(ws)
    if not artifacts:
        return _refuse(
            RefusalCode.BLOCKED_INPUT,
            f"no decision artifacts found under literature/screening/ in "
            f"{ws.name}; nothing to confirm",
        )

    # §3.1: the sign covers every artifact present; an explicit list that
    # disagrees is refused naming the uncovered paths.
    if artifact_list is not None:
        try:
            enforce_coverage(artifact_list, ws)
        except ConfirmationRefusalError as error:
            return _refuse(error.refusal_code, error.detail)

    # Review start: hash + stage the bytes the reviewer is about to judge.
    staged: dict[str, str] = {
        relative: _sha_file(ws / Path(*PurePosixPath(relative).parts))
        for relative in artifacts
    }

    if _MUTATION_PROBE is not None:
        _MUTATION_PROBE(ws)

    try:
        study_ids = _study_ids(ws, artifacts)
        # §5 honesty pricing, both signing modes: an override naming a study
        # absent from the decision artifacts must refuse — silently dropping
        # it would record that study as confirmed behind the reviewer's back.
        unknown = sorted(set(overrides) - set(study_ids))
        if unknown:
            return _refuse(
                RefusalCode.INVALID_OUTPUT,
                "overrides (interactive or queue) name study ids absent from "
                f"the decision artifacts: {unknown}",
            )
        record = _build_record(
            ws,
            reviewer,
            overrides,
            retrospective=retrospective,
            study_ids=study_ids,
            artifacts=artifacts,
            hashes=staged,
        )
        validate(record)
    except ConfirmationRefusalError as error:
        return _refuse(error.refusal_code, error.detail)

    if interactive:
        print()
        summary = record["summary"]
        print(f"  {len(artifacts)} artifact(s): {', '.join(artifacts)}")
        print(
            f"  {summary['considered']} study/studies — "
            f"{summary['confirmed']} confirmed, {summary['changed']} changed, "
            f"{summary['deferred']} deferred"
        )
        for row in record["decisions"]:
            if row["verdict"] != "confirmed":
                reason = row.get("rationale") or row.get("defer_reason") or ""
                print(f"    * {row['study_id']}: {row['verdict']!s} — {reason}")
        try:
            answer = (
                input(
                    f"  Sign as {reviewer['name']} ({reviewer['affiliation']}, "
                    "lead_reviewer) over exactly these bytes? [yes/no]: "
                )
                .strip()
                .lower()
            )
        except EOFError as exc:
            raise ConfirmationRefusalError(
                RefusalCode.BLOCKED_INPUT, "no sign-off entered"
            ) from exc
        if answer != "yes":
            return _refuse(
                RefusalCode.INVALID_OUTPUT,
                "the reviewer declined to sign; nothing written",
            )

    # Write time: re-verify every hash against the *current* disk bytes. A
    # mutation after review start refuses PARENT_HASH_MISMATCH — the staged
    # copy is never quietly re-sessioned onto new bytes.
    for relative in artifacts:
        if _sha_file(ws / Path(*PurePosixPath(relative).parts)) != staged[relative]:
            return _refuse(
                RefusalCode.PARENT_HASH_MISMATCH,
                f"decision artifact {relative!r} changed after the reviewer saw "
                "it; the confirmation cannot silently bind the new bytes — "
                "restart the signing run against the current artifacts",
            )

    if retrospective:
        print(
            "RETROSPECTIVE: this record is labelled retrospective=true; the "
            "export gate will never accept it as confirmation of an export."
        )

    out_path = ws / Path(*PurePosixPath(CONFIRMATION_RELPATH).parts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    # Audit journal event (workspace-manager conventions; real actor + IO).
    _doc_loader()(
        ws,
        "HUMAN_CONFIRMATION",
        "confirm_screening.py",
        (
            f"Screening confirmation signed by {reviewer['name']} "
            f"({reviewer['affiliation']}, lead_reviewer); summary considered="
            f"{record['summary']['considered']}, confirmed="
            f"{record['summary']['confirmed']}, changed={record['summary']['changed']}, "
            f"deferred={record['summary']['deferred']}; retrospective="
            f"{str(bool(retrospective)).lower()}"
        ),
        inputs=artifacts,
        outputs=[CONFIRMATION_RELPATH],
        parameters={
            "tool": "confirm_screening.py",
            "reviewer": reviewer["name"],
            "affiliation": reviewer["affiliation"],
            "signing_capacity": "lead_reviewer",
            "retrospective": bool(retrospective),
            "summary": record["summary"],
        },
        metrics={
            "artifacts_bound": len(artifacts),
            "studies_confirmed": record["summary"]["considered"],
        },
    )

    print(
        json.dumps(
            {
                "result": "accepted",
                "path": CONFIRMATION_RELPATH,
                "reviewer": reviewer["name"],
                "artifacts": len(artifacts),
                "summary": record["summary"],
            }
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/confirm_screening.py",
        description=(
            "Sign literature/screening/HUMAN_CONFIRMATION.json binding a named "
            f"{_ARTIFACT_SCHEMA} reviewer to every screening decision artifact."
        ),
    )
    parser.add_argument("workspace", help="research workspace directory")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--interactive",
        action="store_true",
        help="prompt for the reviewer identity and per-study verdicts",
    )
    mode.add_argument(
        "--from-queue",
        metavar="json",
        help="read the sign-off queue (reviewer, optional overrides/artifacts)",
    )
    parser.add_argument(
        "--retrospective",
        action="store_true",
        help="label the record retrospective=true (never accepted by the export gate)",
    )
    args = parser.parse_args(argv)

    ws = Path(args.workspace).resolve()
    if not ws.is_dir():
        return _refuse(
            RefusalCode.BLOCKED_INPUT, f"workspace directory not found: {ws}"
        )

    overrides: dict[str, dict[str, Any]] = {}
    reviewer = None
    artifact_list = None
    if args.interactive:
        reviewer = {
            "name": _prompt_nonblank("Reviewer name"),
            "affiliation": _prompt_nonblank("Reviewer affiliation"),
        }
        overrides = {}
        print("Mark exceptions first (empty input confirms by default).")
        for study_id in _study_ids(ws, discover_decision_artifacts(ws)):
            row = _prompt_verdict(study_id)
            if row is not None:
                overrides[study_id] = row
    else:
        try:
            queue = json.loads(Path(args.from_queue).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            return _refuse(RefusalCode.BLOCKED_INPUT, f"queue unreadable: {exc}")
        except json.JSONDecodeError as exc:
            return _refuse(
                RefusalCode.INVALID_OUTPUT, f"queue is not valid JSON: {exc}"
            )
        if not isinstance(queue, dict):
            return _refuse(RefusalCode.INVALID_OUTPUT, "queue must be a JSON object")
        reviewer = {
            "name": str(queue.get("reviewer", {}).get("name") or ""),
            "affiliation": str(queue.get("reviewer", {}).get("affiliation") or ""),
        }
        if not reviewer["name"].strip() or not reviewer["affiliation"].strip():
            return _refuse(
                RefusalCode.INVALID_OUTPUT,
                "queue must name the reviewer (non-empty 'reviewer.name' and "
                "from 'reviewer.affiliation')",
            )
        queue_overrides = queue.get("overrides")
        if queue_overrides is not None and not isinstance(queue_overrides, dict):
            return _refuse(
                RefusalCode.INVALID_OUTPUT, "queue.overrides must be an object"
            )
        overrides = {
            study_id: dict(row) for study_id, row in (queue_overrides or {}).items()
        }
        artifacts = queue.get("artifacts")
        if artifacts is not None and not isinstance(artifacts, list):
            return _refuse(RefusalCode.INVALID_OUTPUT, "queue.artifacts must be a list")
        artifact_list = artifacts

    return _run(
        ws,
        reviewer,
        overrides,
        artifact_list,
        retrospective=args.retrospective,
        interactive=bool(args.interactive),
    )


if __name__ == "__main__":
    raise SystemExit(main())
