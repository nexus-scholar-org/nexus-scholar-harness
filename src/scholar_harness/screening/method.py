"""The method parameters in force for a workspace (M7-method M3).

Decision 2026-11-08 ("Method parameters move into the protocol"): the dedup
tiers, the rule-table version, the not-reported policy and blinding may be
set in ``protocol.json`` under ``method``. This module is the one reader:
every consumer asks ``effective_method`` and never re-reads the protocol.

Only the ``method`` key is validated here, so an unrelated protocol problem
does not stop dedup or screening from learning their parameters. A protocol
without the block yields the defaults (today's values) with source
``"defaults"``; an invalid block is refused, never replaced by defaults.

**Method amendments** (H-screening-drafts, decision 2026-11-20, PROPOSED).
``blinding`` and ``not_reported`` can be changed after the workspace was
created, without touching ``protocol.json``: the signed protocol, its
fingerprint, the accepted corpus, the batches and every decision event keep
their binding. Each change is one line of ``audit/method_amendments.jsonl``
(who, when, from, to, and the protocol fingerprint it was made under) and one
``PROTOCOL_METHOD_AMENDED`` journal row. An amendment applies only while the
protocol it was made under is the current one, so a re-inception (a new
protocol) starts from the new protocol's own values. The methods paragraph
reports every amendment made before publication.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError
from scholar_protocol.models import MethodConfig
from scholar_search.dedup import Deduplicator

PROTOCOL_METHOD_INVALID = "PROTOCOL_METHOD_INVALID"

#: The reporting guideline a playbook implies when the protocol does not set one
#: (decision 2026-11-08, "Reporting follows a guideline chosen in the protocol").
PLAYBOOK_REPORTING: dict[str, str] = {
    "PRISMA_SLR": "prisma-2020",
    "RAPID_EVIDENCE": "prisma-2020",
    "STUDENT_DISSERTATION": "prisma-2020",
    "SCOPING_REVIEW": "prisma-scr",
    "DESIGN_SCIENCE": "none",
}
DEFAULT_REPORTING = "prisma-2020"


class MethodInvalid(ValueError):
    """The protocol's ``method`` block is outside the checked limits."""

    code = PROTOCOL_METHOD_INVALID


@dataclass(frozen=True)
class EffectiveMethod:
    config: MethodConfig
    source: Literal["protocol", "defaults"]
    #: The guideline in force and where it came from (M7b-guideline). No defaults:
    #: every construction states both (M7b review 4).
    reporting: str
    reporting_source: Literal["protocol", "playbook", "defaults"]
    #: The amendments applied on top of ``source``, oldest first (H-screening-drafts).
    amendments: tuple[dict[str, Any], ...] = ()

    def source_of(self, field: str) -> str:
        """``"amendment"`` when an amendment set ``field``, else ``source``."""
        return "amendment" if any(a.get("field") == field for a in self.amendments) else self.source

    def deduplicator(self) -> Deduplicator:
        dedup = self.config.dedup
        return Deduplicator(
            title_similarity=dedup.title_similarity,
            first_author=dedup.first_author,
            year_tolerance=dedup.year_tolerance,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            # retrieval_cap is a discovery value (M3a); the screening view
            # and its figures do not carry it.
            **self.config.model_dump(mode="json", exclude={"reporting", "retrieval_cap"}),
            "reporting": self.reporting,
            "reporting_source": self.reporting_source,
        }


def effective_method(workspace: Path | str, *, until: datetime | None = None) -> EffectiveMethod:
    """The method values in force and where they come from.

    With ``until``, only the amendments made at or before it apply (the methods
    paragraph states the values at publication).
    """
    from . import read_store

    path = Path(workspace) / "protocol.json"
    try:
        raw = json.loads(read_store.read_text(path))
    except (OSError, ValueError):
        raw = None
    protocol = raw if isinstance(raw, dict) else None
    method = method_from_protocol(protocol)
    if not (Path(workspace) / AMENDMENTS_FILE).is_file():
        return method  # no amendment: the protocol is not fingerprinted for nothing
    return apply_amendments(method, workspace, protocol_fingerprint(protocol), until=until)


def method_from_protocol(protocol: dict[str, Any] | None) -> EffectiveMethod:
    """The same reading, for a caller that already holds the protocol dict."""
    block = protocol.get("method") if isinstance(protocol, dict) else None
    playbook = str(protocol.get("playbook_type") or "") if isinstance(protocol, dict) else ""
    derived = PLAYBOOK_REPORTING.get(playbook, DEFAULT_REPORTING)
    # Without a protocol there is no playbook to derive from (M7b review 3).
    derived_source = "playbook" if isinstance(protocol, dict) else "defaults"
    if block is None:
        return EffectiveMethod(MethodConfig(), "defaults", derived, derived_source)
    try:
        config = MethodConfig.model_validate(block)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc']) or 'method'}: {err['msg']}" for err in exc.errors()
        )
        raise MethodInvalid(f"the protocol's method block is outside the checked limits ({problems})") from exc
    if config.reporting is not None:
        return EffectiveMethod(config, "protocol", config.reporting, "protocol")
    return EffectiveMethod(config, "protocol", derived, derived_source)


# --- method amendments (H-screening-drafts) -------------------------------------

AMENDMENTS_FILE = Path("audit") / "method_amendments.jsonl"
AMENDED_ACTION = "PROTOCOL_METHOD_AMENDED"
METHOD_AMENDMENT_INVALID = "METHOD_AMENDMENT_INVALID"
#: What an amendment may change, and to what. Dedup and the rule-table version
#: shape the corpus and the table itself; they change only by re-inception.
AMENDABLE: dict[str, tuple[str, ...]] = {
    "blinding": ("reveal_after_decision", "show"),
    "not_reported": ("unclear", "exclude", "decisive_first"),
}


class AmendmentInvalid(ValueError):
    """An amendment outside ``AMENDABLE``, one that changes nothing, or blinding the protocol does not set."""

    code = METHOD_AMENDMENT_INVALID


def protocol_fingerprint(protocol: dict[str, Any] | None) -> str | None:
    """The protocol's canonical fingerprint, or ``None`` when it does not validate."""
    if not isinstance(protocol, dict):
        return None
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol

    try:
        return canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    except (ValidationError, ValueError, TypeError):
        return None


def _time(value: Any) -> datetime | None:
    """An aware instant (UTC when the text names no zone), or ``None``."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def read_amendments(
    workspace: Path | str, fingerprint: str | None, *, until: datetime | None = None
) -> list[dict[str, Any]]:
    """The amendments made under ``fingerprint``, oldest first; an unreadable line is skipped."""
    path = Path(workspace) / AMENDMENTS_FILE
    if fingerprint is None or not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("protocol_fingerprint") != fingerprint:
            continue
        if row.get("field") not in AMENDABLE or row.get("to") not in AMENDABLE[row["field"]]:
            continue
        when = _time(row.get("amended_at"))
        if until is not None and (when is None or when > until):
            continue
        rows.append(row)
    return sorted(rows, key=lambda r: str(r.get("amended_at") or ""))


def apply_amendments(
    method: EffectiveMethod, workspace: Path | str, fingerprint: str | None, *, until: datetime | None = None
) -> EffectiveMethod:
    """``method`` with the amendments recorded under ``fingerprint`` applied in order."""
    rows = read_amendments(workspace, fingerprint, until=until)
    if not rows:
        return method
    config = method.config.model_copy(update={row["field"]: row["to"] for row in rows})
    return replace(method, config=config, amendments=tuple(rows))


def amend_method(
    workspace: Path | str, *, field: str, value: str, amended_by: str, amended_at: str, note: str | None = None
) -> dict[str, Any]:
    """Record one method amendment: a line in ``AMENDMENTS_FILE``, then one journal row.

    Refuses (``AmendmentInvalid``) a field or value outside ``AMENDABLE``, a value
    already in force, and a blinding change on a protocol without a method block
    (blinding is then a workspace setting, changed on Prepare as before). A
    journal row that cannot be written takes the line back out.
    """
    from scholar_harness.workspace.audit import append_event

    ws = Path(workspace)
    if field not in AMENDABLE:
        raise AmendmentInvalid(f"{field!r} cannot be amended; only {', '.join(AMENDABLE)} can")
    if value not in AMENDABLE[field]:
        raise AmendmentInvalid(f"{field} must be one of {', '.join(AMENDABLE[field])}")
    try:
        raw = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AmendmentInvalid("the workspace has no readable protocol.json") from exc
    fingerprint = protocol_fingerprint(raw)
    if fingerprint is None:
        raise AmendmentInvalid("the protocol does not validate, so an amendment could not be bound to it")
    method = apply_amendments(method_from_protocol(raw), ws, fingerprint)
    if field == "blinding" and method.source != "protocol":
        raise AmendmentInvalid("the protocol does not set blinding; it is a workspace setting, changed on Prepare")
    before = getattr(method.config, field)
    if before == value:
        raise AmendmentInvalid(f"{field} is already {value}")
    row = {
        "amendment_id": "AMD-" + uuid.uuid4().hex[:24],
        "field": field,
        "from": before,
        "to": value,
        "protocol_fingerprint": fingerprint,
        "amended_by": amended_by,
        "amended_at": amended_at,
        "note": note,
    }
    path = ws / AMENDMENTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    size = path.stat().st_size if path.exists() else 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    try:
        append_event(
            ws,
            AMENDED_ACTION,
            f"Amended the protocol's method: {field} {before} -> {value} (the signed protocol is unchanged)",
            agent="scholar-harness/console",
            outputs=[AMENDMENTS_FILE.as_posix()],
            parameters={
                "amendment_id": row["amendment_id"],
                "field": field,
                "before": {field: before},
                "after": {field: value},
                "amended_by": amended_by,
                "protocol_fingerprint": fingerprint,
                "note": note,
            },
        )
    except OSError:
        with path.open("r+b") as handle:
            handle.truncate(size)
        raise
    return row
