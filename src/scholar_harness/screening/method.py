"""The method parameters in force for a workspace (M7-method M3).

Decision 2026-11-08 ("Method parameters move into the protocol"): the dedup
tiers, the rule-table version, the not-reported policy and blinding may be
set in ``protocol.json`` under ``method``. This module is the one reader:
every consumer asks ``effective_method`` and never re-reads the protocol.

Only the ``method`` key is validated here, so an unrelated protocol problem
does not stop dedup or screening from learning their parameters. A protocol
without the block yields the defaults (today's values) with source
``"defaults"``; an invalid block is refused, never replaced by defaults.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
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


def effective_method(workspace: Path | str) -> EffectiveMethod:
    """The method values in force and where they come from."""
    path = Path(workspace) / "protocol.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = None
    return method_from_protocol(raw if isinstance(raw, dict) else None)


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
