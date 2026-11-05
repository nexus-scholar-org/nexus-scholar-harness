"""One interface for every screening provider (decision 2026-11-05).

A driver sends one structured request per record and returns one
`DriverResult` per record, in any order, matched by `custom_id` (the study
id), never by position. It never decides anything and never fills a gap:

- `ok` carries the parsed JSON object the model returned;
- `refusal` (with the provider's category), `truncated`, `invalid` (not JSON)
  and `error` carry no output.

The run turns every non-`ok` result into an Unclear proposal; a record is
never dropped and never excluded because a call failed (agent-system §1.3).

Each driver parses its provider's raw response bodies (`parse_*` functions),
so the same contract tests run every driver on recorded bodies without a
network or an SDK.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Status = Literal["ok", "refusal", "truncated", "invalid", "error"]
PROVIDERS = ("anthropic", "openai_compatible", "gemini")


@dataclass(frozen=True)
class ScreeningRequest:
    custom_id: str
    user_message: str


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
        }


@dataclass(frozen=True)
class DriverResult:
    custom_id: str
    status: Status
    output: Any = None
    detail: str = ""
    usage: Usage = field(default_factory=Usage)
    model: str = ""
    request_id: str | None = None
    batch_id: str | None = None


@dataclass(frozen=True)
class RunSpec:
    """What every request of a run shares: the cached prefix, schema and model."""

    system: str
    schema: dict[str, Any]
    model: str
    effort: str
    max_tokens: int


class Driver(Protocol):
    provider: str

    def run(
        self,
        requests: list[ScreeningRequest],
        spec: RunSpec,
        *,
        on_result: Callable[[DriverResult], None] | None = None,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> list[DriverResult]: ...


def parse_json_text(text: str | None) -> tuple[Status, Any, str]:
    """`ok` with the object, or `invalid` with why; never a guess."""
    if not text or not text.strip():
        return "invalid", None, "empty response text"
    try:
        value = json.loads(text)
    except ValueError as exc:
        return "invalid", None, f"not JSON: {exc}"
    if not isinstance(value, dict):
        return "invalid", None, "the JSON is not an object"
    return "ok", value, ""


def missing(requests: list[ScreeningRequest], results: list[DriverResult], model: str, detail: str) -> list[DriverResult]:
    """An `error` result for every request the provider returned nothing for."""
    seen = {r.custom_id for r in results}
    return [DriverResult(r.custom_id, "error", detail=detail, model=model) for r in requests if r.custom_id not in seen]
