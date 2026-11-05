"""The driver contract (M1b-2): one suite, three providers.

Every driver must turn its provider's response bodies into the same result
statuses, return exactly one result per request matched by `custom_id`, and
never put a key in a URL. The bodies below follow each provider's documented
response shape; they are not captured from a live API (the live prompt-gate
run replaces them with captured bodies).
"""

from __future__ import annotations

import json

import httpx
import pytest

from scholar_agent.drivers import RunSpec, ScreeningRequest, make_driver
from scholar_agent.drivers import anthropic_driver as ad
from scholar_agent.drivers import gemini as gd
from scholar_agent.drivers import openai_compatible as od

ANSWER = {"criteria": [{"id": "INC-01", "answer": "yes", "quote": "UAV"}], "cannot_decide": False, "reasoning": "r"}
SPEC = RunSpec(system="criteria…", schema={"type": "object", "additionalProperties": False}, model="m", effort="low", max_tokens=512)


def anthropic_body(case: str) -> dict:
    base = {"id": "msg_1", "model": "claude-opus-5-5", "usage": {"input_tokens": 100, "output_tokens": 80, "cache_read_input_tokens": 500, "cache_creation_input_tokens": 0}}
    text = {"type": "text", "text": json.dumps(ANSWER)}
    return {
        "ok": {**base, "stop_reason": "end_turn", "content": [text]},
        "refusal": {**base, "stop_reason": "refusal", "stop_details": {"category": "bio"}, "content": []},
        "truncated": {**base, "stop_reason": "max_tokens", "content": [{"type": "text", "text": "{\"crit"}]},
        "invalid": {**base, "stop_reason": "end_turn", "content": [{"type": "text", "text": "not json"}]},
    }[case]


def openai_body(case: str) -> dict:
    def choice(content, finish="stop", refusal=None):
        return {"id": "chatcmpl-1", "model": "gpt-x", "usage": {"prompt_tokens": 600, "completion_tokens": 80, "prompt_tokens_details": {"cached_tokens": 512}},
                "choices": [{"finish_reason": finish, "message": {"role": "assistant", "content": content, "refusal": refusal}}]}
    return {
        "ok": choice(json.dumps(ANSWER)),
        "refusal": choice(None, refusal="I can't help with that."),
        "truncated": choice("{\"crit", finish="length"),
        "invalid": choice("not json"),
    }[case]


def gemini_body(case: str) -> dict:
    def cand(text, finish="STOP"):
        return {"responseId": "r1", "modelVersion": "gemini-x", "usageMetadata": {"promptTokenCount": 600, "candidatesTokenCount": 80, "cachedContentTokenCount": 0},
                "candidates": [{"finishReason": finish, "content": {"parts": [{"text": text}]}}]}
    return {
        "ok": cand(json.dumps(ANSWER)),
        "refusal": cand("", finish="SAFETY"),
        "truncated": cand("{\"crit", finish="MAX_TOKENS"),
        "invalid": cand("not json"),
    }[case]


PARSERS = {
    "anthropic": (anthropic_body, lambda body: ad.parse_message("STU-1", body)),
    "openai_compatible": (openai_body, lambda body: od.parse_completion("STU-1", body)),
    "gemini": (gemini_body, lambda body: gd.parse_generation("STU-1", body)),
}


@pytest.mark.parametrize("provider", sorted(PARSERS))
@pytest.mark.parametrize("case", ["ok", "refusal", "truncated", "invalid"])
def test_every_provider_maps_the_same_cases_to_the_same_status(provider, case):
    body, parse = PARSERS[provider]
    result = parse(body(case))
    assert result.custom_id == "STU-1" and result.status == case
    if case == "ok":
        assert result.output == ANSWER
        assert result.usage.input_tokens == 600 and result.usage.output_tokens == 80
    else:
        assert result.output is None  # no output is ever kept from a non-ok answer
    if case == "refusal":
        assert result.detail


def test_anthropic_reads_the_stop_reason_before_content():
    body = anthropic_body("ok") | {"stop_reason": "refusal", "stop_details": {"category": "cyber"}}
    result = ad.parse_message("STU-1", body)
    assert (result.status, result.detail, result.output) == ("refusal", "cyber", None)
    # Anthropic's input_tokens excludes cached tokens; the driver reports the total.
    assert (result.usage.input_tokens, result.usage.cache_read_tokens) == (600, 500)


def test_anthropic_batch_entries_errored_canceled_expired_are_errors():
    for kind in ("errored", "canceled", "expired"):
        entry = {"custom_id": "STU-9", "result": {"type": kind, "error": {"type": "overloaded_error"}}}
        result = ad.parse_batch_result(entry, batch_id="msgbatch_1")
        assert (result.custom_id, result.status, result.batch_id) == ("STU-9", "error", "msgbatch_1")


def test_gemini_blocked_prompt_is_a_refusal_and_its_schema_drops_additional_properties():
    assert gd.parse_generation("STU-1", {"promptFeedback": {"blockReason": "SAFETY"}}).status == "refusal"
    assert "additionalProperties" not in json.dumps(gd.gemini_schema({"type": "object", "additionalProperties": False, "properties": {"a": {"type": "object", "additionalProperties": False}}}))


# --- run level: one result per request, matched by custom_id -------------------

REQUESTS = [ScreeningRequest(f"STU-{i}", f"<record>{i}</record>") for i in range(3)]


class FakeBatches:
    def __init__(self, bodies):
        self.bodies, self.created, self.cancelled, self.polls = bodies, [], [], 0

    def create(self, requests):
        self.created.append(requests)
        return {"id": f"msgbatch_{len(self.created)}"}

    def retrieve(self, batch_id):
        self.polls += 1
        return {"processing_status": "ended" if self.polls > 1 else "in_progress"}

    def cancel(self, batch_id):
        self.cancelled.append(batch_id)

    def results(self, batch_id):
        # Out of order, and one request missing: the driver matches by custom_id.
        reqs = self.created[-1]
        return [{"custom_id": r["custom_id"], "result": {"type": "succeeded", "message": self.bodies}} for r in reversed(reqs[1:])]


class FakeAnthropic:
    def __init__(self, body):
        self.messages = type("M", (), {})()
        self.messages.batches = FakeBatches(body)
        self.calls = []
        self.messages.create = lambda **params: self.calls.append(params) or body


def test_anthropic_batch_run_matches_by_custom_id_and_reports_the_missing_one():
    client = FakeAnthropic(anthropic_body("ok"))
    results = ad.AnthropicDriver(client=client, direct_limit=0, poll_seconds=0).run(REQUESTS, SPEC)
    by_id = {r.custom_id: r for r in results}
    assert sorted(by_id) == ["STU-0", "STU-1", "STU-2"]
    assert by_id["STU-0"].status == "error" and "no result" in by_id["STU-0"].detail
    assert by_id["STU-2"].status == "ok" and by_id["STU-2"].batch_id == "msgbatch_1"
    params = client.messages.batches.created[0][0]["params"]
    assert params["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert params["output_config"] == {"effort": "low", "format": {"type": "json_schema", "schema": SPEC.schema}}
    assert params["messages"][0]["content"].startswith("<record>")


def test_anthropic_cancel_waits_for_the_batch_to_end_and_keeps_finished_results():
    client = FakeAnthropic(anthropic_body("ok"))
    results = ad.AnthropicDriver(client=client, direct_limit=0, poll_seconds=0).run(REQUESTS, SPEC, cancelled=lambda: client.messages.batches.polls >= 1)
    assert client.messages.batches.cancelled == ["msgbatch_1"]
    assert len(results) == 3


def test_anthropic_direct_calls_turn_exceptions_into_error_results():
    client = FakeAnthropic(anthropic_body("ok"))

    def boom(**params):
        raise RuntimeError("overloaded")

    client.messages.create = boom
    results = ad.AnthropicDriver(client=client, direct_limit=20).run(REQUESTS, SPEC)
    assert [r.status for r in results] == ["error"] * 3


def _http(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_openai_compatible_falls_back_to_json_mode_once_and_keeps_the_key_out_of_the_url():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append((str(request.url), body["response_format"]["type"]))
        if body["response_format"]["type"] == "json_schema":
            return httpx.Response(400, text="response_format json_schema is not supported")
        return httpx.Response(200, json=openai_body("ok"))

    driver = od.OpenAICompatibleDriver("http://127.0.0.1:11434/v1", "sk-test", client=_http(handler), concurrency=1)
    results = driver.run(REQUESTS, SPEC)
    assert [r.status for r in results] == ["ok"] * 3
    assert seen[0][1] == "json_schema" and all(kind == "json_object" for _, kind in seen[1:])
    assert all("sk-test" not in url for url, _ in seen)


def test_gemini_sends_the_key_in_a_header_and_http_errors_are_results():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(503, text="unavailable")

    driver = gd.GeminiDriver("AIza-test", client=_http(handler), concurrency=2)
    results = driver.run(REQUESTS, SPEC)
    assert sorted(r.custom_id for r in results) == ["STU-0", "STU-1", "STU-2"]
    assert {r.status for r in results} == {"error"}
    assert all("AIza-test" not in str(r.url) for r in seen)


def test_make_driver_needs_what_each_provider_needs():
    with pytest.raises(ValueError, match="base URL"):
        make_driver("openai_compatible", api_key=None)
    with pytest.raises(ValueError, match="API key"):
        make_driver("gemini", api_key=None)
    with pytest.raises(ValueError, match="unknown provider"):
        make_driver("local", api_key="x")
