"""Gemini driver: the same screening task over the Generative Language REST API.

It replaces nothing silently: unlike the legacy `scholar_search.screening`
path, a record the model does not answer is an `error` (so Unclear), never a
heuristic verdict.

- **Structured output:** `responseMimeType: application/json` with
  `responseSchema`, Gemini's OpenAPI-subset schema (`additionalProperties`
  is not part of it and is removed; the engine's checks still apply).
- **Stops:** a blocked prompt (`promptFeedback.blockReason`) or a
  `SAFETY`/`RECITATION`/`BLOCKLIST`/`PROHIBITED_CONTENT`/`SPII` finish is a
  `refusal`; `MAX_TOKENS` is `truncated`.
- **The key** goes in the `x-goog-api-key` header, never in the URL.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from .base import DriverResult, RunSpec, ScreeningRequest, Usage, parse_json_text

PROVIDER = "gemini"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
REFUSAL_FINISHES = frozenset({"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY"})


def gemini_schema(schema: Any) -> Any:
    """The task schema without the keywords Gemini's schema subset rejects."""
    if isinstance(schema, dict):
        return {k: gemini_schema(v) for k, v in schema.items() if k != "additionalProperties"}
    if isinstance(schema, list):
        return [gemini_schema(v) for v in schema]
    return schema


def request_body(request: ScreeningRequest, spec: RunSpec) -> dict[str, Any]:
    return {
        "systemInstruction": {"parts": [{"text": spec.system}]},
        "contents": [{"role": "user", "parts": [{"text": request.user_message}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": gemini_schema(spec.schema),
            "maxOutputTokens": spec.max_tokens,
        },
    }


def parse_generation(custom_id: str, body: dict[str, Any], *, model: str = "") -> DriverResult:
    u = body.get("usageMetadata") or {}
    usage = Usage(
        input_tokens=int(u.get("promptTokenCount") or 0),
        output_tokens=int(u.get("candidatesTokenCount") or 0) + int(u.get("thoughtsTokenCount") or 0),
        cache_read_tokens=int(u.get("cachedContentTokenCount") or 0),
    )
    common = {"usage": usage, "model": str(body.get("modelVersion") or model), "request_id": body.get("responseId")}
    blocked = (body.get("promptFeedback") or {}).get("blockReason")
    if blocked:
        return DriverResult(custom_id, "refusal", detail=str(blocked), **common)
    candidates = body.get("candidates") or []
    if not candidates:
        return DriverResult(custom_id, "error", detail="no candidates in the response", **common)
    candidate = candidates[0] or {}
    finish = candidate.get("finishReason")
    if finish in REFUSAL_FINISHES:
        return DriverResult(custom_id, "refusal", detail=str(finish), **common)
    if finish == "MAX_TOKENS":
        return DriverResult(custom_id, "truncated", detail="MAX_TOKENS", **common)
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought"))
    status, output, detail = parse_json_text(text)
    return DriverResult(custom_id, status, output=output, detail=detail, **common)


class GeminiDriver:
    provider = PROVIDER

    def __init__(self, api_key: str, *, concurrency: int = 4, client: httpx.Client | None = None, timeout: float = 120.0):
        self.client = client or httpx.Client(
            headers={"content-type": "application/json", "x-goog-api-key": api_key}, timeout=timeout
        )
        self.concurrency = max(1, concurrency)

    def _one(self, request: ScreeningRequest, spec: RunSpec) -> DriverResult:
        url = f"{BASE_URL}/models/{spec.model}:generateContent"
        try:
            response = self.client.post(url, json=request_body(request, spec))
            if response.status_code >= 400:
                return DriverResult(request.custom_id, "error", detail=f"HTTP {response.status_code}", model=spec.model)
            return parse_generation(request.custom_id, response.json(), model=spec.model)
        except (httpx.HTTPError, ValueError) as exc:
            return DriverResult(request.custom_id, "error", detail=f"{type(exc).__name__}: {exc}", model=spec.model)

    def run(
        self,
        requests: list[ScreeningRequest],
        spec: RunSpec,
        *,
        on_result: Callable[[DriverResult], None] | None = None,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> list[DriverResult]:
        results: list[DriverResult] = []

        def task(request: ScreeningRequest) -> DriverResult | None:
            return None if cancelled() else self._one(request, spec)

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            for result in pool.map(task, requests):
                if result is None:
                    continue
                results.append(result)
                if on_result is not None:
                    on_result(result)
        return results
