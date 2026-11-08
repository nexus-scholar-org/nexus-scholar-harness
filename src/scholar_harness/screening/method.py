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


class MethodInvalid(ValueError):
    """The protocol's ``method`` block is outside the checked limits."""

    code = PROTOCOL_METHOD_INVALID


@dataclass(frozen=True)
class EffectiveMethod:
    config: MethodConfig
    source: Literal["protocol", "defaults"]

    def deduplicator(self) -> Deduplicator:
        dedup = self.config.dedup
        return Deduplicator(
            title_similarity=dedup.title_similarity,
            first_author=dedup.first_author,
            year_tolerance=dedup.year_tolerance,
        )

    def as_dict(self) -> dict[str, Any]:
        return {"source": self.source, **self.config.model_dump(mode="json")}


def effective_method(workspace: Path | str) -> EffectiveMethod:
    """The method values in force and where they come from."""
    path = Path(workspace) / "protocol.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = None
    block = raw.get("method") if isinstance(raw, dict) else None
    if block is None:
        return EffectiveMethod(MethodConfig(), "defaults")
    try:
        return EffectiveMethod(MethodConfig.model_validate(block), "protocol")
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc']) or 'method'}: {err['msg']}" for err in exc.errors()
        )
        raise MethodInvalid(f"the protocol's method block is outside the checked limits ({problems})") from exc
