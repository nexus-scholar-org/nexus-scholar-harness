"""OpenAI-compatible driver: any Chat Completions endpoint, by base URL and key.

Covers OpenAI, OpenRouter, Azure OpenAI's compatible endpoint, and local
servers (Ollama, vLLM, LM Studio). It speaks plain HTTP (`httpx`, a base
dependency), so no SDK is needed and a local server works without a key.

- **Structured output where offered:** `response_format: json_schema` (strict)
  first. A server that rejects it (HTTP 400/422 naming the response format)
  is retried once in JSON mode; the engine's schema check still validates
  the answer, and a failed check makes the record Unclear.
- **Stops:** `finish_reason: length` is `truncated`; `content_filter`, or a
  `message.refusal` string, is `refusal`.
- **Throughput:** most compatible servers have no batch API, so requests run
  in parallel up to `concurrency`.
- **The key** goes in the `Authorization` header, never in a URL.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from .base import DriverResult, RunSpec, ScreeningRequest, Usage, parse_json_text

PROVIDER = "openai_compatible"


def request_body(request: ScreeningRequest, spec: RunSpec, *, json_schema: bool = True) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": spec.model,
        "max_tokens": spec.max_tokens,
        "messages": [
            {"role": "system", "content": spec.system},
            {"role": "user", "content": request.user_message},
        ],
    }
    if json_schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "screening_proposal", "strict": True, "schema": spec.schema},
        }
    else:
        body["response_format"] = {"type": "json_object"}
    return body


def parse_completion(custom_id: str, body: dict[str, Any]) -> DriverResult:
    u = body.get("usage") or {}
    details = u.get("prompt_tokens_details") or {}
    usage = Usage(
        input_tokens=int(u.get("prompt_tokens") or 0),
        output_tokens=int(u.get("completion_tokens") or 0),
        cache_read_tokens=int(details.get("cached_tokens") or 0),
    )
    common = {"usage": usage, "model": str(body.get("model") or ""), "request_id": body.get("id")}
    choices = body.get("choices") or []
    if not choices:
        return DriverResult(custom_id, "error", detail="no choices in the response", **common)
    choice = choices[0] or {}
    message = choice.get("message") or {}
    finish = choice.get("finish_reason")
    if message.get("refusal") or finish == "content_filter":
        return DriverResult(custom_id, "refusal", detail=str(message.get("refusal") or "content_filter"), **common)
    if finish == "length":
        return DriverResult(custom_id, "truncated", detail="length", **common)
    status, output, detail = parse_json_text(message.get("content"))
    return DriverResult(custom_id, status, output=output, detail=detail, **common)


def _rejects_schema(response: httpx.Response) -> bool:
    return response.status_code in (400, 422) and "response_format" in response.text


class OpenAICompatibleDriver:
    provider = PROVIDER

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        *,
        concurrency: int = 4,
        client: httpx.Client | None = None,
        timeout: float = 120.0,
    ):
        self.url = base_url.rstrip("/") + "/chat/completions"
        headers = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        self.client = client or httpx.Client(headers=headers, timeout=timeout)
        self.concurrency = max(1, concurrency)
        self.json_schema = True  # cleared once if the server rejects structured output

    def _one(self, request: ScreeningRequest, spec: RunSpec) -> DriverResult:
        try:
            response = self.client.post(self.url, json=request_body(request, spec, json_schema=self.json_schema))
            if self.json_schema and _rejects_schema(response):
                self.json_schema = False
                response = self.client.post(self.url, json=request_body(request, spec, json_schema=False))
            if response.status_code >= 400:
                return DriverResult(request.custom_id, "error", detail=f"HTTP {response.status_code}", model=spec.model)
            return parse_completion(request.custom_id, response.json())
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
