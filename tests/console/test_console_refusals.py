"""The console refusal set and the screening API contract §7 stay in step."""

from __future__ import annotations

import re
from pathlib import Path

from scholar_harness.console import refusals

CONTRACT = Path(__file__).resolve().parents[2] / "docs" / "architecture" / "screening-api-contract.md"


def _proposed_codes() -> set[str]:
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split("**Proposed here**", 1)[1].split("## 8.", 1)[0]
    return set(re.findall(r"^\| `([A-Z_]+)` \|", section, flags=re.M))


def test_every_contract_code_is_in_the_console_set():
    proposed = _proposed_codes()
    assert len(proposed) >= 9  # anti-vacuity: the table parsed
    engine_codes = proposed - {"ENGINE_UNREACHABLE"}  # client-side only
    assert engine_codes == set(refusals.CONTRACT_ADDED)


def test_codes_are_their_own_names():
    for code in refusals.CONSOLE_REFUSALS:
        assert re.fullmatch(r"[A-Z][A-Z_]+", code)
    assert refusals.CONTRACT_ADDED <= refusals.CONSOLE_REFUSALS


def test_the_import_rejection_codes_are_the_importers_own():
    """E3 (M3d-engine): the row codes the console registers are the ones the importers write."""
    from scholar_search import importers

    assert refusals.IMPORT_REJECTION_CODES == {
        importers.IMPORT_NO_TITLE, importers.IMPORT_BAD_TAG, importers.IMPORT_BAD_YEAR,
    }


def _bare_client(tmp_path):
    """A console with no workspace open: the inception routes still take bodies."""
    from fastapi.testclient import TestClient

    from scholar_harness.console import create_app

    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token="t", workspaces_root=root)
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": "Bearer t"})


def test_a_body_pydantic_refuses_answers_the_refusal_envelope(tmp_path):
    """F5 (three-phase review): a wrong-typed body answers `BODY_INVALID`, never FastAPI's bare error list."""
    client = _bare_client(tmp_path)
    response = client.post("/api/v1/inception/drafts", json={"draft": 5})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, dict), detail  # the envelope, not a list
    assert detail["code"] == "BODY_INVALID" and "BODY_INVALID" in refusals.CONSOLE_REFUSALS
    assert detail["message"] and "\n" not in detail["message"]
    errors = detail["details"]["errors"]
    assert errors[0]["loc"] == ["body", "draft"] and errors[0]["msg"]
    assert "input" not in errors[0]  # the client's value is not echoed back


def test_an_unknown_body_field_is_body_invalid(tmp_path):
    client = _bare_client(tmp_path)
    response = client.post("/api/v1/inception/drafts", json={"draft": {}, "surprise": 1})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "BODY_INVALID"
    assert [e["loc"] for e in detail["details"]["errors"]] == [["body", "surprise"]]
    assert "surprise" in detail["message"]
