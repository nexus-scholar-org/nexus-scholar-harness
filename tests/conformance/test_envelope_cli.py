"""CLI gate for ``python -m scholar_harness.contracts.envelope`` (decision D10).

Every violation exits 1 with a machine-readable JSON refusal on *stderr*; a
successful validate/diff exits 0 with JSON on stdout. These paths cover the
reviewer-repaired F1/F2/F4 surfaces: no traceback may escape.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scholar_harness.contracts.envelope import diff, envelope_id
from scholar_harness.contracts.envelope.cli import main

ROOT = Path(__file__).resolve().parents[2]
ROLES = ROOT / "roles"
FIXTURES = ROOT / "tests" / "conformance" / "fixtures" / "envelope"


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _write(tmp_path: Path, name: str, raw: dict[str, Any]) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_cli_validate_accepted_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "validate", str(FIXTURES / "ok.json"))
    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["result"] == "accepted"
    assert payload["status"] == "OK"
    assert payload["envelope_id"] == envelope_id(
        json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
    )


def test_cli_validate_role_incompat_is_json_refusal_on_stderr(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Reviewer F1: role-major incompatibility used to raise AttributeError."""

    raw = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
    raw["role_version"] = "9.0.0"
    raw["envelope_id"] = envelope_id(raw)
    path = _write(tmp_path, "incompat.json", raw)
    code, out, err = _run(capsys, "validate", str(path), "--roles-dir", str(ROLES))
    assert code == 1
    assert out == ""
    refusal = json.loads(err)
    assert refusal["result"] == "rejected"
    assert refusal["status"] == "INVALID_OUTPUT"
    assert refusal["refusal_code"] == "INVALID_OUTPUT"
    assert "9.0.0" in refusal["detail"]


@pytest.mark.parametrize(
    ("content", "detail_fragment"),
    [
        ("{ not json", "not valid JSON"),
        (b"\xef\xbb\xbf{ not json", "not valid JSON"),
    ],
)
def test_cli_validate_malformed_json_is_refusal(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    content: object,
    detail_fragment: str,
) -> None:
    """Reviewer F2: malformed/BOM-prefixed files refuse, never traceback."""

    path = tmp_path / "malformed.json"
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    code, out, err = _run(capsys, "validate", str(path))
    assert code == 1
    assert out == ""
    refusal = json.loads(err)
    assert refusal["result"] == "rejected"
    assert refusal["refusal_code"] == "INVALID_OUTPUT"
    assert detail_fragment in refusal["detail"]


def test_cli_validate_unreadable_path_is_refusal(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    code, out, err = _run(capsys, "validate", str(tmp_path / "does_not_exist.json"))
    assert code == 1
    assert out == ""
    refusal = json.loads(err)
    assert refusal["result"] == "rejected"
    assert refusal["refusal_code"] == "INVALID_OUTPUT"
    assert "unreadable" in refusal["detail"]


@pytest.fixture()
def binding_root(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """A tmp tree holding the two parents the ok fixture declares."""

    root = tmp_path / "ws"
    root.mkdir()
    raw = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
    (root / "protocol.json").write_bytes(b'{"title": "protocol"}\n')
    (root / "SCREENING_CRITERIA.md").write_bytes(b"# criteria\n")
    parents = [
        {
            "artifact": "protocol.json",
            "sha256": hashlib.sha256(b'{"title": "protocol"}\n').hexdigest(),
        },
        {
            "artifact": "SCREENING_CRITERIA.md",
            "sha256": hashlib.sha256(b"# criteria\n").hexdigest(),
        },
    ]
    raw["parents"] = parents
    raw["inputs"] = []
    raw["envelope_id"] = envelope_id(raw)
    return root, raw


def test_cli_verify_parents_mutated_file_is_hash_mismatch(
    capsys: pytest.CaptureFixture[str], binding_root: tuple[Path, dict[str, Any]]
) -> None:
    root, raw = binding_root
    path = _write(root.parent, "envelope.json", raw)
    (root / "SCREENING_CRITERIA.md").write_bytes(b"# criteria mutated\n")
    code, out, err = _run(
        capsys,
        "validate",
        str(path),
        "--verify-parents",
        "--root",
        str(root),
        "--roles-dir",
        str(ROLES),
    )
    assert code == 1
    assert out == ""
    refusal = json.loads(err)
    assert refusal["result"] == "rejected"
    assert refusal["refusal_code"] == "PARENT_HASH_MISMATCH"
    assert refusal["status"] == "PARENT_HASH_MISMATCH"
    assert "SCREENING_CRITERIA.md" in refusal["detail"]


def test_cli_diff_two_fixtures_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(
        capsys, "diff", str(FIXTURES / "ok.json"), str(FIXTURES / "partial.json")
    )
    assert code == 0
    assert err == ""
    report = json.loads(out)
    assert "differing_fields" in report
    assert report["differing_fields"]  # ok vs partial genuinely differ


def test_cli_diff_identical_envelopes_exits_zero(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    a = _write(
        tmp_path,
        "a.json",
        json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8")),
    )
    b = _write(
        tmp_path,
        "b.json",
        json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8")),
    )
    code, out, _err = _run(capsys, "diff", str(a), str(b))
    assert code == 0
    report = json.loads(out)
    assert report["differing_fields"] == []
    assert report["hash_changes"] == {}


def test_diff_surfaces_tampered_envelope_id_cause(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Reviewer F4: an id differing with no §4-field reason must name itself."""

    raw = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
    tampered = json.loads(json.dumps(raw))
    tampered["envelope_id"] = "ENV-0000000000000000"
    report = diff(raw, tampered).as_dict()
    assert report["differing_fields"] == ["envelope_id"]
    assert report["hash_changes"]["envelope_id"]["b"] == "ENV-0000000000000000"
    assert "same_output_different_identifiers" in report
    summary = report["same_output_different_identifiers"]
    assert summary is not None
    assert "does not match its own recomputation" in summary
    assert "envelope_id(b)" in summary
    # And via the CLI it still exits 0 with the same report.
    code, out, _err = _run(
        capsys,
        "diff",
        str(_write(tmp_path, "clean.json", raw)),
        str(_write(tmp_path, "tampered.json", tampered)),
    )
    assert code == 0
    assert json.loads(out)["same_output_different_identifiers"] == summary


def test_cli_validate_without_discoverable_roles_dir_refuses(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewer F1 (cycle 2): a CWD with no roles/ ancestor must fail loud,
    never silently skip the role-record cross-checks (D11).
    """

    raw = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
    raw["output"]["schema"] = "ScreeningDecisions@2"
    raw["envelope_id"] = envelope_id(raw)
    artifact = _write(tmp_path, "unregistered_schema.json", raw)
    monkeypatch.chdir(tmp_path)
    code, out, err = _run(capsys, "validate", str(artifact))
    assert code == 1
    assert out == ""
    refusal = json.loads(err)
    assert refusal["result"] == "rejected"
    assert refusal["refusal_code"] == "BLOCKED_INPUT"
    assert refusal["status"] == "BLOCKED_INPUT"
    assert "--roles-dir" in refusal["detail"]
    # And the same artifact with an explicit --roles-dir is still refused —
    # now by the D11 schema-name authority itself.
    code, out, err = _run(capsys, "validate", str(artifact), "--roles-dir", str(ROLES))
    assert code == 1
    assert out == ""
    refusal = json.loads(err)
    assert refusal["result"] == "rejected"
    assert refusal["refusal_code"] == "INVALID_OUTPUT"
    assert "ScreeningDecisions@2" in refusal["detail"]
