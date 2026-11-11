"""Screening rounds (M3g-citation-chasing, decision 2026-11-12 item 4).

A workspace screens one corpus snapshot at a time in ``literature/screening/``.
Citation chasing adds records *after* the first screening is published, and
the contract binds every batch and decision to the corpus fingerprint, so the
chased records are screened as a **second round** with their own snapshot
instead of joining the frozen one. When a round starts, the previous round's
``literature/screening/`` folder and its published outputs are moved, never
deleted, into ``literature/screening_rounds/round_NNN/``, and
``literature/screening_rounds/rounds.json`` says which round is current and
what the earlier rounds were (with their published PRISMA counts, so the
report can print the databases arm as it was published).

PRISMA 2020 draws two arms: identification via databases (round 1) and via
other methods (citation searching, round 2 and later). The round's own
``prisma_report.json`` keeps the kit's fields for the round being screened (the
decisions of this generation) and, from round 2 on, adds ``arm``, ``round``,
``identification`` (what the chase fetched and removed before screening),
``previous_rounds`` (each round's published counts, verbatim) and
``review_totals``. A workspace without a chase writes exactly what it wrote
before this module existed.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROUNDS_DIRNAME = "screening_rounds"
ROUNDS_SCHEMA = "nexus.screening-rounds.v1"
ROUND_SCHEMA = "nexus.screening-round.v1"
ARM_DATABASES = "databases"
ARM_CITATION_SEARCHING = "citation_searching"
#: The published outputs a round leaves in ``literature/``.
PUBLISHED_OUTPUTS = (
    "included.json", "excluded.json", "conflicts.json", "prisma_report.json", "prisma_screening_report.md",
)
#: What moves into the round folder when the next round starts (directories end in ``/``).
ARCHIVED_WITH_ROUND = ("screening/", *PUBLISHED_OUTPUTS, "verified.json")


class RoundArchiveIncomplete(Exception):
    """A move failed part way; ``moved`` and ``not_moved`` say where every path is."""

    code = "ARCHIVE_INCOMPLETE"

    def __init__(self, message: str, *, backup: str, moved: list[str], not_moved: list[str]) -> None:
        super().__init__(message)
        self.backup, self.moved, self.not_moved = backup, moved, not_moved


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def rounds_dir(workspace: Path | str) -> Path:
    return Path(workspace) / "literature" / ROUNDS_DIRNAME


def rounds_path(workspace: Path | str) -> Path:
    return rounds_dir(workspace) / "rounds.json"


def _default() -> dict[str, Any]:
    return {
        "schema": ROUNDS_SCHEMA,
        "current": {"round": 1, "arm": ARM_DATABASES, "chase": None, "corpus_artifact_id": None, "started_at": None},
        "rounds": [],
    }


def read_rounds(workspace: Path | str) -> dict[str, Any]:
    """The rounds index, or the implicit first round when none was written."""
    path = rounds_path(workspace)
    if not path.is_file():
        return _default()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _default()
    if not isinstance(data, dict) or data.get("schema") != ROUNDS_SCHEMA:
        return _default()
    data.setdefault("current", _default()["current"])
    data.setdefault("rounds", [])
    return data


def current_round(workspace: Path | str) -> dict[str, Any]:
    return dict(read_rounds(workspace)["current"])


def previous_rounds(workspace: Path | str) -> list[dict[str, Any]]:
    return [dict(r) for r in read_rounds(workspace)["rounds"] if isinstance(r, dict)]


def write_rounds(workspace: Path | str, data: dict[str, Any]) -> None:
    path = rounds_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def round_folder(workspace: Path | str, number: int) -> Path:
    return rounds_dir(workspace) / f"round_{number:03d}"


def archive_round(
    workspace: Path | str,
    *,
    number: int,
    arm: str,
    generation_id: str | None,
    corpus_artifact_id: str | None,
    chase: str | None = None,
) -> dict[str, Any]:
    """Move the current round's screening folder and published outputs into its round folder.

    Idempotent for a retry: a path already moved is skipped. The published
    ``prisma_report.json`` is read before the move and kept in the round
    record, so later reports print the arm as it was published. A failed move
    raises :class:`RoundArchiveIncomplete` naming what moved and what did not;
    nothing is moved back.
    """
    ws = Path(workspace)
    lit = ws / "literature"
    backup = round_folder(ws, number)
    backup.mkdir(parents=True, exist_ok=True)
    prisma: dict[str, Any] | None = None
    for candidate in (lit / "prisma_report.json", backup / "prisma_report.json"):
        if candidate.is_file():
            try:
                prisma = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                prisma = None
            break
    moved: list[str] = []
    planned = [rel for rel in ARCHIVED_WITH_ROUND if (lit / rel.rstrip("/")).exists()]
    # A retry after a partial move: what is already in the round folder counts as moved.
    moved_before = [
        rel for rel in ARCHIVED_WITH_ROUND
        if (backup / rel.rstrip("/")).exists() and not (lit / rel.rstrip("/")).exists()
    ]
    try:
        for rel in planned:
            source = lit / rel.rstrip("/")
            dest = backup / rel.rstrip("/")
            if dest.exists():
                # Never merge two copies: a path present on both sides is a refusal.
                raise OSError(f"{rel} exists both in literature/ and in the round folder")
            shutil.move(str(source), str(dest))
            moved.append(rel)
    except OSError as exc:
        rel_backup = backup.relative_to(ws).as_posix()
        not_moved = [rel for rel in planned if rel not in moved]
        raise RoundArchiveIncomplete(
            f"archiving round {number} into {rel_backup} stopped: {type(exc).__name__}: {str(exc)[:200]}. "
            f"Moved: {', '.join(moved) or 'nothing'}. Not moved: {', '.join(not_moved) or 'nothing'}.",
            backup=rel_backup, moved=moved, not_moved=not_moved,
        ) from exc
    record = {
        "schema": ROUND_SCHEMA,
        "round": number,
        "arm": arm,
        "generation_id": generation_id,
        "corpus_artifact_id": corpus_artifact_id,
        "chase": chase,
        "archived_at": _now(),
        "path": backup.relative_to(ws).as_posix(),
        "moved": moved_before + moved,
        "prisma": prisma,
    }
    (backup / "round.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return record


def start_round(
    workspace: Path | str,
    previous: dict[str, Any],
    *,
    number: int,
    arm: str,
    chase: str | None,
    corpus_artifact_id: str | None,
) -> dict[str, Any]:
    """Record ``previous`` as finished and make round ``number`` the current one."""
    data = read_rounds(workspace)
    rounds = [r for r in data["rounds"] if isinstance(r, dict) and r.get("round") != previous.get("round")]
    rounds.append({k: v for k, v in previous.items() if k != "schema"})
    rounds.sort(key=lambda r: int(r.get("round") or 0))
    data["rounds"] = rounds
    data["current"] = {
        "round": number, "arm": arm, "chase": chase, "corpus_artifact_id": corpus_artifact_id, "started_at": _now(),
    }
    write_rounds(workspace, data)
    return data


# --------------------------------------------------------------------------- PRISMA with rounds


def _chase_counts(workspace: Path, chase: str | None) -> dict[str, Any] | None:
    if not chase:
        return None
    path = Path(workspace) / "literature" / "citation_chase" / chase / "chase.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    counts = manifest.get("counts") if isinstance(manifest, dict) else None
    if not isinstance(counts, dict):
        return None
    return {
        "chase": chase,
        "seeds": len(manifest.get("seeds") or []),
        "chaseable_seeds": sum(1 for s in manifest.get("seeds") or [] if isinstance(s, dict) and s.get("chaseable")),
        "providers": list(manifest.get("providers") or []),
        "directions": list(manifest.get("directions") or []),
        "forward_cap": manifest.get("forward_cap"),
        "year_min": manifest.get("year_min"),
        "year_max": manifest.get("year_max"),
        "counts": {k: int(counts.get(k) or 0) for k in (
            "raw", "duplicates_within_chase", "already_in_corpus", "outside_year_window", "over_ceiling", "new",
        )},
    }


def chase_identification(workspace: Path | str) -> tuple[int, int] | None:
    """``(identified, duplicates_removed)`` of the current citation-searching round, else ``None``.

    Identified is every record the chase fetched; a duplicate is a record found
    twice in the chase or already in the corpus. Records outside the year
    window (and over the ceiling) are reported apart, as removed before
    screening, in :func:`prisma_outputs`.
    """
    current = current_round(workspace)
    if current.get("arm") != ARM_CITATION_SEARCHING:
        return None
    info = _chase_counts(Path(workspace), current.get("chase"))
    if info is None:
        return None
    c = info["counts"]
    return c["raw"], c["duplicates_within_chase"] + c["already_in_corpus"]


def _round_counts(prisma: dict[str, Any] | None) -> dict[str, int]:
    prisma = prisma if isinstance(prisma, dict) else {}
    return {
        key: int(prisma.get(key) or 0)
        for key in ("total_identified", "duplicates_removed", "records_screened", "records_excluded",
                    "records_included", "records_unclear", "conflicts_flagged")
    }


def prisma_outputs(workspace: Path | str, report: Any) -> dict[str, str]:
    """``prisma_report.json`` and ``prisma_screening_report.md`` for the current round.

    Collect and approval both call this so the two hash the same bytes. A first
    round writes exactly the kit's report; a citation-searching round adds the
    arm, what the chase removed before screening, every earlier round's
    published counts and the review totals, and appends the second arm to the
    markdown.
    """
    ws = Path(workspace)
    current = current_round(ws)
    base = asdict(report)
    markdown = report.to_markdown()
    if int(current.get("round") or 1) <= 1 or current.get("arm") != ARM_CITATION_SEARCHING:
        return {"prisma_screening_report.md": markdown, "prisma_report.json": json.dumps(base, indent=2)}

    info = _chase_counts(ws, current.get("chase")) or {"chase": current.get("chase"), "counts": {}}
    counts = info.get("counts") or {}
    earlier = []
    for record in previous_rounds(ws):
        earlier.append({
            "round": record.get("round"),
            "arm": record.get("arm"),
            "generation_id": record.get("generation_id"),
            "corpus_artifact_id": record.get("corpus_artifact_id"),
            "chase": record.get("chase"),
            "path": record.get("path"),
            "prisma": record.get("prisma"),
        })
    totals = _round_counts(base)
    for record in earlier:
        for key, value in _round_counts(record.get("prisma")).items():
            totals[key] += value
    data = {
        **base,
        "arm": ARM_CITATION_SEARCHING,
        "round": int(current.get("round") or 1),
        "identification": {
            "source": ARM_CITATION_SEARCHING,
            **{k: v for k, v in info.items() if k != "counts"},
            "fetched": counts.get("raw", base.get("total_identified")),
            "duplicates_within_chase": counts.get("duplicates_within_chase", 0),
            "already_in_corpus": counts.get("already_in_corpus", 0),
            "removed_before_screening": {
                "outside_year_window": counts.get("outside_year_window", 0),
                "over_ceiling": counts.get("over_ceiling", 0),
            },
        },
        "previous_rounds": earlier,
        "review_totals": {
            "records_screened": totals["records_screened"],
            "records_excluded": totals["records_excluded"],
            "records_included": totals["records_included"],
            "records_unclear": totals["records_unclear"],
        },
    }
    lines = [
        markdown.rstrip("\n"),
        "",
        "---",
        "",
        f"## 3. Identification of studies via other methods (round {data['round']}: citation searching)",
        "",
        "The counts above are this round's: the records found by citation searching "
        f"({info.get('chase') or 'chase'}, {' and '.join(info.get('directions') or ['forward', 'backward'])}, "
        f"{', '.join(info.get('providers') or [])}) from {info.get('chaseable_seeds', 0)} of "
        f"{info.get('seeds', 0)} included studies.",
        "",
        f"- **Records identified by citation searching**: `{counts.get('raw', base.get('total_identified'))}`",
        f"- **Duplicates within the chase**: `{counts.get('duplicates_within_chase', 0)}`",
        f"- **Already in the corpus (screened in an earlier round)**: `{counts.get('already_in_corpus', 0)}`",
        f"- **Removed before screening, outside the protocol's year window**: `{counts.get('outside_year_window', 0)}`",
        f"- **Removed before screening, over the run ceiling**: `{counts.get('over_ceiling', 0)}`",
        f"- **Records screened in this round**: `{base.get('records_screened', 0)}`",
        "",
        "## 4. Identification of studies via databases (earlier rounds, as published)",
        "",
        "| Round | Arm | Identified | Duplicates removed | Screened | Excluded | Unclear | Included |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in earlier:
        c = _round_counts(record.get("prisma"))
        lines.append(
            f"| {record.get('round')} | {record.get('arm')} | {c['total_identified']} | {c['duplicates_removed']} | "
            f"{c['records_screened']} | {c['records_excluded']} | {c['records_unclear']} | {c['records_included']} |"
        )
    lines.extend([
        "",
        "## 5. Review totals (every round)",
        "",
        f"- **Records screened**: `{totals['records_screened']}`",
        f"- **Records excluded**: `{totals['records_excluded']}`",
        f"- **Unclear → full text**: `{totals['records_unclear']}`",
        f"- **Included at title/abstract**: `{totals['records_included']}`",
        "",
    ])
    return {"prisma_screening_report.md": "\n".join(lines), "prisma_report.json": json.dumps(data, indent=2)}
