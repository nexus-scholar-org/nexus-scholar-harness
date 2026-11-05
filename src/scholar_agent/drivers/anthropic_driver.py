"""Anthropic driver: Message Batches, the cached protocol prefix, structured output.

- **Bulk:** requests go through Message Batches (half price), matched by
  `custom_id`. A run of `direct_limit` records or fewer (a dry run) uses
  direct calls instead, so the researcher sees results at once.
- **Caching:** the system prompt (task template and criteria) is identical
  for every record and is marked `cache_control: ephemeral`; the record goes
  last, in the user message.
- **Structured output:** `output_config.format` carries the task schema;
  `output_config.effort` is the depth control (thinking cannot be disabled on
  Opus 5.5).
- **Stops:** `stop_reason` is read before content. `refusal` keeps its
  `stop_details.category`; `max_tokens` is `truncated`.

The SDK (`anthropic`, extra `ai`) is imported only when no client is passed.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from .base import DriverResult, RunSpec, ScreeningRequest, Usage, missing, parse_json_text

PROVIDER = "anthropic"


def request_params(request: ScreeningRequest, spec: RunSpec) -> dict[str, Any]:
    return {
        "model": spec.model,
        "max_tokens": spec.max_tokens,
        "system": [{"type": "text", "text": spec.system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": request.user_message}],
        "output_config": {"effort": spec.effort, "format": {"type": "json_schema", "schema": spec.schema}},
    }


def _usage(body: dict[str, Any]) -> Usage:
    u = body.get("usage") or {}
    return Usage(
        input_tokens=int(u.get("input_tokens") or 0),
        output_tokens=int(u.get("output_tokens") or 0),
        cache_read_tokens=int(u.get("cache_read_input_tokens") or 0),
        cache_write_tokens=int(u.get("cache_creation_input_tokens") or 0),
    )


def parse_message(custom_id: str, body: dict[str, Any], *, batch_id: str | None = None) -> DriverResult:
    """One Messages API response body → a result. `stop_reason` first, then content."""
    model = str(body.get("model") or "")
    common = {"usage": _usage(body), "model": model, "request_id": body.get("id"), "batch_id": batch_id}
    stop = body.get("stop_reason")
    if stop == "refusal":
        details = body.get("stop_details") or {}
        return DriverResult(custom_id, "refusal", detail=str(details.get("category") or "refusal"), **common)
    if stop == "max_tokens":
        return DriverResult(custom_id, "truncated", detail="max_tokens", **common)
    text = next((b.get("text") for b in body.get("content") or [] if isinstance(b, dict) and b.get("type") == "text"), None)
    status, output, detail = parse_json_text(text)
    return DriverResult(custom_id, status, output=output, detail=detail, **common)


def parse_batch_result(entry: dict[str, Any], *, batch_id: str) -> DriverResult:
    """One line of a batch's results: succeeded, errored, canceled or expired."""
    custom_id = str(entry.get("custom_id") or "")
    result = entry.get("result") or {}
    kind = result.get("type")
    if kind == "succeeded":
        return parse_message(custom_id, result.get("message") or {}, batch_id=batch_id)
    error = result.get("error") or {}
    detail = f"{kind}: {error.get('type') or ''}".strip(": ") if kind == "errored" else str(kind or "unknown")
    return DriverResult(custom_id, "error", detail=detail, batch_id=batch_id)


def _dump(obj: Any) -> dict[str, Any]:
    return obj if isinstance(obj, dict) else obj.model_dump()


class AnthropicDriver:
    provider = PROVIDER

    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: Any = None,
        direct_limit: int = 20,
        poll_seconds: float = 30.0,
        max_per_batch: int = 10000,
    ):
        if client is None:
            import anthropic  # extra `ai`

            client = anthropic.Anthropic(api_key=api_key)
        self.client = client
        self.direct_limit = direct_limit
        self.poll_seconds = poll_seconds
        self.max_per_batch = max_per_batch

    def run(
        self,
        requests: list[ScreeningRequest],
        spec: RunSpec,
        *,
        on_result: Callable[[DriverResult], None] | None = None,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> list[DriverResult]:
        results: list[DriverResult] = []

        def emit(result: DriverResult) -> None:
            results.append(result)
            if on_result is not None:
                on_result(result)

        if len(requests) <= self.direct_limit:
            for request in requests:
                if cancelled():
                    break
                try:
                    body = _dump(self.client.messages.create(**request_params(request, spec)))
                    emit(parse_message(request.custom_id, body))
                except Exception as exc:  # noqa: BLE001 - every failure is a result, never a drop
                    emit(DriverResult(request.custom_id, "error", detail=f"{type(exc).__name__}: {exc}", model=spec.model))
            return results

        for start in range(0, len(requests), self.max_per_batch):
            chunk = requests[start : start + self.max_per_batch]
            if cancelled():
                break
            batch = _dump(
                self.client.messages.batches.create(
                    requests=[{"custom_id": r.custom_id, "params": request_params(r, spec)} for r in chunk]
                )
            )
            batch_id = str(batch["id"])
            cancel_sent = False
            # A cancelled batch passes through "canceling"; its results (the
            # requests that did finish) are readable once it has ended.
            while _dump(self.client.messages.batches.retrieve(batch_id)).get("processing_status") != "ended":
                if cancelled() and not cancel_sent:
                    self.client.messages.batches.cancel(batch_id)
                    cancel_sent = True
                time.sleep(self.poll_seconds)
            for entry in self.client.messages.batches.results(batch_id):
                emit(parse_batch_result(_dump(entry), batch_id=batch_id))
            for result in missing(chunk, results, spec.model, "no result returned by the batch"):
                emit(result)
        return results
