"""Which API key the app uses, and saying so (H-key-precedence-2026-11-20).

On 2026-11-19 a paid M9a run was refused three times (401) because the OS
keychain held an old key and `resolve_key` read it before a valid
`ANTHROPIC_API_KEY`; `keys status` said only "keychain". Every test here runs
on a fake keychain and a patched environment: no real key, no real keychain,
no network, no provider SDK.
"""

from __future__ import annotations

import re
import sys

import pytest
from typer.testing import CliRunner

from scholar_agent import drivers, keys
from scholar_agent import prompt_gate as pg
from scholar_agent.drivers import DriverResult, Usage
from scholar_agent.drivers import (
    ensure_sdk as real_ensure_sdk,  # the conftest stubs the module attribute
)
from scholar_harness.cli import app

from .test_measure import HUMAN, MODEL, ScriptedDriver, _workspace
from .test_prompt_gate import _workspace as _gate_workspace

ENV_KEY = "ENV-KEY-aaaa1111bbbb2222"
KEYCHAIN_KEY = "KEYCHAIN-KEY-cccc3333dddd4444"
ANSI = re.compile(chr(27) + r"\[[0-9;]*m")
UNAUTHORIZED = "AuthenticationError: Error code: 401 - {'type': 'error', 'error': {'message': 'invalid x-api-key'}}"


def _flat(output: str) -> str:
    """The console wraps long lines and colours them (even off a terminal); compare the words, not the line breaks."""
    return " ".join(ANSI.sub("", output).split())


def _no_secret_printed(output: str) -> None:
    for secret in (ENV_KEY, KEYCHAIN_KEY):
        # Not the key, and not a recognisable part of it (its first 8 characters).
        assert secret not in output and secret[:8] not in output


# --- precedence ------------------------------------------------------------------------------------


def test_an_environment_variable_wins_over_the_keychain(keychain, monkeypatch):
    keys.store_key("anthropic", KEYCHAIN_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", ENV_KEY)
    assert keys.resolve_key("anthropic") == ENV_KEY
    status = keys.key_status("anthropic")
    assert status.source == "environment" and status.also_in_keychain is True


@pytest.mark.parametrize("provider", list(keys.ENV_VARS))
def test_every_provider_follows_the_same_order(keychain, monkeypatch, provider):
    keys.store_key(provider, KEYCHAIN_KEY)
    assert keys.resolve_key(provider) == KEYCHAIN_KEY and keys.key_status(provider).source == "keychain"
    monkeypatch.setenv(keys.ENV_VARS[provider], ENV_KEY)
    assert keys.resolve_key(provider) == ENV_KEY


def test_the_keychain_stays_the_default_when_no_variable_is_set(keychain, monkeypatch):
    keys.store_key("anthropic", KEYCHAIN_KEY)
    assert keys.resolve_key("anthropic") == KEYCHAIN_KEY
    status = keys.key_status("anthropic")
    assert status.source == "keychain" and status.also_in_keychain is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")  # a blank variable is not a key
    assert keys.resolve_key("anthropic") == KEYCHAIN_KEY and keys.key_status("anthropic").source == "keychain"


def test_the_environment_alone_and_no_key_at_all(keychain, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", ENV_KEY)
    status = keys.key_status("gemini")
    assert status.source == "environment" and status.also_in_keychain is False
    assert keys.key_status("openai_compatible").source == "none"


# --- visibility: `keys status` ------------------------------------------------------------------------


def test_status_says_which_source_is_used_and_that_the_other_also_exists(keychain, monkeypatch):
    keys.store_key("anthropic", KEYCHAIN_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", ENV_KEY)
    keys.store_key("gemini", KEYCHAIN_KEY)
    monkeypatch.setenv("OPENAI_API_KEY", ENV_KEY)
    result = CliRunner().invoke(app, ["keys", "status"])
    assert result.exit_code == 0, result.output
    text = _flat(result.output)
    assert "anthropic: environment (ANTHROPIC_API_KEY; a keychain key also exists and is not used)" in text
    assert "ANTHROPIC_API_KEY" in text and "keys clear anthropic" in text  # how to use the keychain key instead
    assert "gemini: keychain" in text
    assert "openai_compatible: environment (OPENAI_API_KEY)" in text and "OPENAI_API_KEY; a keychain" not in text
    _no_secret_printed(result.output)


def test_status_says_so_when_there_is_no_keychain_support(monkeypatch):
    monkeypatch.setitem(sys.modules, "keyring", None)  # `import keyring` -> ImportError
    result = CliRunner().invoke(app, ["keys", "status"])
    assert result.exit_code == 0
    assert "keychain" in _flat(result.output) and "ai" in _flat(result.output)


# --- visibility: a refused key in the paid commands -----------------------------------------------------


def _measure(tmp_path, *extra):
    return CliRunner().invoke(
        app,
        ["prompt-gate", "measure", "--workspace", str(_workspace(tmp_path)), "--scope", "all", "--model", MODEL, "--yes", "--out", str(tmp_path / "r"), *extra],
    )


def _refusing_driver(monkeypatch):
    dead = {sid: (lambda s: DriverResult(s, "error", detail=UNAUTHORIZED, usage=Usage(), model=MODEL)) for sid in HUMAN}
    monkeypatch.setattr(drivers, "make_driver", lambda *a, **k: ScriptedDriver(dead))


def test_measure_names_the_environment_as_the_source_of_a_refused_key(tmp_path, keychain, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", ENV_KEY)
    keys.store_key("anthropic", KEYCHAIN_KEY)
    _refusing_driver(monkeypatch)
    result = _measure(tmp_path)
    text = _flat(result.output)
    assert result.exit_code == 1 and "Not measured" in text
    assert "anthropic refused the key from the environment variable ANTHROPIC_API_KEY" in text
    assert "keychain key also exists and is not used" in text
    _no_secret_printed(result.output)


def test_measure_names_the_keychain_as_the_source_of_a_refused_key(tmp_path, keychain, monkeypatch):
    keys.store_key("anthropic", KEYCHAIN_KEY)
    _refusing_driver(monkeypatch)
    result = _measure(tmp_path)
    text = _flat(result.output)
    assert result.exit_code == 1
    assert "anthropic refused the key stored in the OS keychain" in text
    assert "nexus-scholar keys set anthropic" in text and "nexus-scholar keys clear anthropic" in text
    _no_secret_printed(result.output)


def test_a_batch_that_the_provider_refuses_is_a_sentence_not_a_traceback(tmp_path, keychain, monkeypatch):
    # In batch mode the SDK raises from `batches.create`; nothing is a per-record result.
    class Unauthorized(Exception):
        status_code = 401

    class Raising:
        def run(self, *_a, **_k):
            raise Unauthorized("Error code: 401 - invalid x-api-key")

    monkeypatch.setenv("ANTHROPIC_API_KEY", ENV_KEY)
    monkeypatch.setattr(drivers, "make_driver", lambda *a, **k: Raising())
    result = _measure(tmp_path)
    text = _flat(result.output)
    assert result.exit_code == 1 and isinstance(result.exception, SystemExit)
    assert "anthropic refused the key from the environment variable ANTHROPIC_API_KEY" in text
    _no_secret_printed(result.output)


def test_a_failure_that_is_not_a_refusal_is_not_blamed_on_the_key(tmp_path, keychain, monkeypatch):
    class Broken:
        def run(self, *_a, **_k):
            raise RuntimeError("the network is down")

    monkeypatch.setenv("ANTHROPIC_API_KEY", ENV_KEY)
    monkeypatch.setattr(drivers, "make_driver", lambda *a, **k: Broken())
    result = _measure(tmp_path)
    assert isinstance(result.exception, RuntimeError) and "refused the key" not in _flat(result.output)


def test_gate_run_names_the_source_of_a_refused_key(tmp_path, keychain, monkeypatch):
    import json

    ws = _gate_workspace(tmp_path)
    frozen = pg.build_set(ws, excludes=2)
    set_file = tmp_path / "set.json"
    set_file.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(pg, "SET_FILE", set_file)
    monkeypatch.setattr(pg, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setenv("ANTHROPIC_API_KEY", ENV_KEY)

    class Failing:
        def run(self, requests, spec):
            return [DriverResult(r.custom_id, "error", detail=UNAUTHORIZED) for r in requests]

    monkeypatch.setattr(drivers, "make_driver", lambda *a, **k: Failing())
    result = CliRunner().invoke(app, ["prompt-gate", "run", "--workspace", str(ws), "--yes"])
    text = _flat(result.output)
    assert result.exit_code == 1 and "Not measured" in text
    assert "anthropic refused the key from the environment variable ANTHROPIC_API_KEY" in text
    _no_secret_printed(result.output)


def test_is_refusal_recognises_a_401_and_nothing_wider():
    class Unauthorized(Exception):
        status_code = 401

    assert keys.is_refusal(Unauthorized("x")) and keys.is_refusal(UNAUTHORIZED) and keys.is_refusal("HTTP 401")
    assert keys.is_refusal(type("AuthenticationError", (Exception,), {})("bad key"))
    assert not keys.is_refusal(RuntimeError("GET https://x/401/y failed")) and not keys.is_refusal(Exception("status 401 in text"))
    assert not keys.is_refusal("HTTP 429") and not keys.is_refusal("overloaded_error: try again")
    assert not keys.is_refusal(RuntimeError("1401 records")) and not keys.is_refusal("")


# --- the missing `ai` extra --------------------------------------------------------------------------


@pytest.fixture
def no_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", None)  # `import anthropic` -> ImportError
    monkeypatch.setattr(drivers, "ensure_sdk", real_ensure_sdk)
    built = []
    monkeypatch.setattr(drivers, "make_driver", lambda *a, **k: built.append(a))
    return built


def test_ensure_sdk_says_what_to_install(no_sdk):
    with pytest.raises(ImportError) as info:
        real_ensure_sdk("anthropic")
    message = str(info.value)
    assert "uv sync --extra ai" in message and "[ai]" in message and "\n" not in message
    real_ensure_sdk("gemini")  # these two use httpx, not an SDK
    real_ensure_sdk("openai_compatible")


def test_make_driver_gives_the_same_sentence_instead_of_a_module_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", None)
    monkeypatch.setattr(drivers, "ensure_sdk", real_ensure_sdk)
    with pytest.raises(ImportError, match=r"uv sync --extra ai"):
        drivers.make_driver("anthropic", api_key="k")


def test_measure_without_the_sdk_says_so_before_any_spend_is_announced(tmp_path, keychain, no_sdk):
    ws = str(_workspace(tmp_path))
    for extra in ([], ["--yes"]):
        result = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", ws, "--scope", "all", "--model", MODEL, *extra])
        text = _flat(result.output)
        assert result.exit_code == 1 and "uv sync --extra ai" in text, text
        assert "Traceback" not in result.output and not isinstance(result.exception, ImportError)
        # Nothing about money before the sentence: no estimate, no "add --yes to spend".
        assert "estimated cost" not in text and "to spend your key" not in text
        assert 'nexus-scholar[ai]' in text, text  # Rich must not read "[ai]" as markup and drop it
    assert no_sdk == []


def test_measure_dry_run_needs_no_sdk(tmp_path, keychain, no_sdk):
    result = CliRunner().invoke(app, ["prompt-gate", "measure", "--workspace", str(_workspace(tmp_path)), "--scope", "all", "--dry-run"])
    assert result.exit_code == 0 and "Network calls made: 0" in result.output


def test_gate_run_without_the_sdk_says_so_before_the_estimate(tmp_path, keychain, no_sdk, monkeypatch):
    import json

    ws = _gate_workspace(tmp_path)
    set_file = tmp_path / "set.json"
    set_file.write_text(json.dumps(pg.build_set(ws, excludes=2)), encoding="utf-8")
    monkeypatch.setattr(pg, "SET_FILE", set_file)
    result = CliRunner().invoke(app, ["prompt-gate", "run", "--workspace", str(ws)])
    text = _flat(result.output)
    assert result.exit_code == 1 and "uv sync --extra ai" in text and "Estimate" not in text and "Traceback" not in result.output
    assert "nexus-scholar[ai]" in text
