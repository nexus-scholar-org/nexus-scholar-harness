"""HCM-02: neutral workspace/audit service migration tests.

Internal modularity refactor only; zero approved-behavior change. All fixtures
under ``tmp_path`` (never ``workspaces/``). Covers HCM2-01..HCM2-10 and the
required negative cases. Preserves HCM-01 observed defects (a)-(c) and defers
(d); implementing a behavior change without approval would fail this packet.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from scholar_harness import inception
from scholar_harness.console.api import audit as console_audit
from scholar_harness.workspace import audit as neutral_audit
from scholar_harness.workspace import identity as neutral_identity
from scholar_harness.workspace import loader as neutral_loader
from scholar_harness.workspace.errors import (
    NotWorkspaceError,
    RegisteredWorkspaceIdentityMissingError,
)

EVT_RE = re.compile(r"^EVT-\d{14}-[0-9a-f]{6}$")
WSP_VALID = "WSP-" + "a" * 32
WSP_OTHER = "WSP-" + "b" * 32

REPO_ROOT = Path(__file__).resolve().parents[2]


def _manifest(ws: Path) -> dict:
    return json.loads((ws / "project.json").read_text(encoding="utf-8"))


def _journal_lines(ws: Path) -> list[str]:
    journal = ws / "audit" / "journal.jsonl"
    if not journal.exists():
        return []
    return [l for l in journal.read_text(encoding="utf-8").splitlines() if l.strip()]


def _make_ws(tmp_path: Path, manifest: dict | None = None) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    if manifest is None:
        manifest = {
            "project_id": "s",
            "title": "T",
            "registered_workspace_id": WSP_VALID,
            "updated_at": "2026-01-01T00:00:00+00:00",
            "stats": {},
        }
    (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# HCM2-01: neutral direction, no console transport in core paths (guard)
# ---------------------------------------------------------------------------


FORBIDDEN = "console.api.audit"
CORE_PATHS = [
    "src/scholar_harness/contracts/acceptance.py",
    "src/scholar_harness/index_acceptance.py",
    "src/scholar_harness/extraction_producer.py",
    "src/scholar_harness/orchestrator.py",
    "src/scholar_harness/handoff.py",
    "src/scholar_harness/audit_log.py",
    "src/scholar_harness/inception/genesis.py",
    "src/scholar_harness/workspace/audit.py",
    "src/scholar_harness/workspace/identity.py",
    "src/scholar_harness/workspace/loader.py",
    "src/scholar_harness/workspace/manifest.py",
    "src/scholar_harness/workspace/__init__.py",
]
# Console-internal adapter seams that legitimately keep ``from .audit import``.
ALLOWED_ADAPTERS = {
    "src/scholar_harness/console/api/screening.py",
    "src/scholar_harness/console/api/pipelines.py",
    "src/scholar_harness/console/api/audit.py",
}


def _has_forbidden(path: Path) -> bool:
    """True when *path* imports console transport (import lines only, not prose)."""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "console.api.audit" in line and ("import" in line):
            return True
    return False


def test_hcm2_01_no_console_transport_in_migrated_core_paths():
    """HCM2-01: migrated core paths use the neutral service, not console transport."""
    for rel in CORE_PATHS:
        p = REPO_ROOT / rel
        assert p.is_file(), rel
        assert not _has_forbidden(p), f"{rel} still imports console transport"


def test_hcm2_01_console_adapter_retained_with_reason():
    """HCM2-01: screening/pipelines keep ``via console adapter`` with documented reason.

    Console-internal ``from .audit import log_event`` is retained because those
    modules are themselves transport (FastAPI operator surface); they consume
    the neutral service transitively through ``console.api.audit`` (thin
    adapter), so no direct core->transport edge is introduced.
    """
    for rel in sorted(ALLOWED_ADAPTERS):
        assert (REPO_ROOT / rel).is_file()
    # The adapter itself delegates to neutral (no hand-rolled journal).
    adapter_src = (REPO_ROOT / "src/scholar_harness/console/api/audit.py").read_text(
        encoding="utf-8"
    )
    assert "workspace.audit" in adapter_src
    assert "workspace.loader" in adapter_src


def test_hcm2_01_guard_fails_when_forbidden_restored(tmp_path):
    """Negative: the guard detects a deliberately restored console dependency."""
    fake = tmp_path / "acceptance.py"
    fake.write_text(
        "from scholar_harness.console.api.audit import log_event\n", encoding="utf-8"
    )
    assert _has_forbidden(fake) is True
    clean = tmp_path / "clean.py"
    clean.write_text(
        "from scholar_harness.workspace.audit import log_event\n", encoding="utf-8"
    )
    assert _has_forbidden(clean) is False


def test_hcm2_01_acceptance_exposes_neutral_sink_for_injection():
    """HCM2-01: acceptance/index/extraction expose neutral ``log_event`` for fault injection."""
    import scholar_harness.contracts.acceptance as acceptance
    import scholar_harness.extraction_producer as producer
    import scholar_harness.index_acceptance as index_acc

    assert acceptance.log_event is neutral_audit.log_event
    assert producer.log_event is neutral_audit.log_event
    assert index_acc.log_event is neutral_audit.log_event


# ---------------------------------------------------------------------------
# HCM2-02: recorded identity survives, no rerun re-mint
# ---------------------------------------------------------------------------


def test_hcm2_02_require_recorded_identity_roundtrip(tmp_path):
    ws = _make_ws(tmp_path)
    assert neutral_identity.require_recorded_identity(ws) == WSP_VALID
    # No rerun re-mint: second read returns same value, file untouched.
    before = (ws / "project.json").read_bytes()
    assert neutral_identity.require_recorded_identity(ws) == WSP_VALID
    assert (ws / "project.json").read_bytes() == before


def test_hcm2_02_orchestrator_delegates_to_neutral(tmp_path):
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = _make_ws(tmp_path)
    assert ResearchOrchestrator(ws).recorded_workspace_id() == WSP_VALID
    assert ResearchOrchestrator(
        ws
    ).recorded_workspace_id() == neutral_identity.require_recorded_identity(ws)


def test_hcm2_02_recorded_or_minted_mints_once_then_reuses(tmp_path):
    ws = tmp_path / "fresh"
    ws.mkdir()
    first = neutral_identity.recorded_or_minted_workspace_id(ws)
    assert EVT_RE.match("EVT-20260101000000-abcdef")  # sanity: regex itself valid
    assert re.fullmatch(r"^WSP-[0-9a-f]{32}$", first)
    # Simulate init writing the minted value, then re-read reuses it.
    (ws / "project.json").write_text(
        json.dumps({"project_id": "s", "registered_workspace_id": first}),
        encoding="utf-8",
    )
    assert neutral_identity.recorded_or_minted_workspace_id(ws) == first
    assert neutral_identity.require_recorded_identity(ws) == first


def test_hcm2_02_sync_preserves_identity_and_fields(tmp_path):
    """HCM2-02: sync merges stats without re-minting or dropping fields."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "my-slug",
                "registered_workspace_id": WSP_VALID,
                "title": "My Title",
                "custom_field": "keep-me",
                "status": "active",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "stats": {"discovered_papers": 99, "my_custom_stat": 7},
            }
        ),
        encoding="utf-8",
    )
    (ws / "literature").mkdir()
    (ws / "literature" / "raw_search.json").write_text(
        json.dumps([{"x": 1}]), encoding="utf-8"
    )
    ResearchOrchestrator(ws).sync_state()
    after = _manifest(ws)
    assert after["registered_workspace_id"] == WSP_VALID
    assert after["custom_field"] == "keep-me"
    assert after["stats"]["my_custom_stat"] == 7


# ---------------------------------------------------------------------------
# HCM2-03: missing/invalid/unregistered creates nothing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        json.dumps({"project_id": "s"}),
        json.dumps({"registered_workspace_id": ""}),
        json.dumps({"registered_workspace_id": None}),
        json.dumps({"registered_workspace_id": "WSP-legacy"}),
        json.dumps({"registered_workspace_id": "my-slug"}),
        "{not json",
    ],
)
def test_hcm2_03_invalid_identity_creates_nothing(tmp_path, raw):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(raw, encoding="utf-8")
    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        neutral_identity.require_recorded_identity(ws)
    assert not (ws / "audit" / "journal.jsonl").exists()
    assert not (ws / "audit" / "artifact_registry.json").exists()
    assert not (ws / "artifacts").exists()


def test_hcm2_03_absent_manifest_creates_nothing_on_require(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        neutral_identity.require_recorded_identity(ws)
    assert not (ws / "audit").exists()


def test_hcm2_03_nonobject_consumer_preserved_untyped(tmp_path):
    """Policy (a) PRESERVED: non-object consumer manifest stays untyped AttributeError."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(AttributeError):
        neutral_identity.require_recorded_identity(ws)
    with pytest.raises(AttributeError):
        ResearchOrchestrator(ws).recorded_workspace_id()


def test_hcm2_03_sync_nonobject_preserved_typeerror(tmp_path):
    """Policy (b) PRESERVED: sync on non-object manifest stays untyped TypeError."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(TypeError):
        ResearchOrchestrator(ws).sync_state()


def test_hcm2_03_corrupt_manifest_sync_rebuild_observed(tmp_path):
    """Policy (c) PRESERVED (OBSERVED-NOT-APPROVED): corrupt rebuilds fresh + SUCCESS."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text("{not json", encoding="utf-8")
    (ws / "literature").mkdir()
    (ws / "literature" / "raw_search.json").write_text("[]", encoding="utf-8")
    ResearchOrchestrator(ws).sync_state()
    after = _manifest(ws)
    assert after["project_id"] == ws.name
    assert "registered_workspace_id" not in after
    actions = [json.loads(l).get("action") for l in _journal_lines(ws)]
    assert "STATE_SYNC" in actions


# ---------------------------------------------------------------------------
# HCM2-04: injected audit failure -> typed refusal, nothing successful
# ---------------------------------------------------------------------------


def test_hcm2_04_accept_failure_reports_atomic_and_publishes_nothing(
    tmp_path, monkeypatch
):
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    import scholar_harness.contracts.acceptance as acceptance

    fixture = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "contracts"
        / "v1"
        / "two_study_artifact_chain.json"
    )
    artifact = json.loads(fixture.read_text(encoding="utf-8"))["artifacts"][0]
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "WS-GOLDEN", "stats": {}}), encoding="utf-8"
    )
    context = AcceptanceContext(
        workspace_id=artifact["workspace_id"],
        protocol_fingerprint=artifact["protocol_fingerprint"],
        corpus_fingerprint=artifact["corpus_fingerprint"],
    )

    def _fail(*a, **k):
        raise OSError("audit unavailable")

    monkeypatch.setattr(acceptance, "log_event", _fail)
    result = accept_artifact(ws, artifact, expected=context)
    assert result.accepted is False
    assert result.published_path is None
    assert result.event_id is None
    assert [i.code for i in result.issues] == ["ATOMIC_COMMIT_FAILED"]
    assert not (ws / "artifacts").exists()
    assert not (ws / "audit" / "artifact_registry.json").exists()
    if (ws / "audit" / "journal.jsonl").exists():
        assert "ARTIFACT_ACCEPTED" not in [
            json.loads(l).get("action") for l in _journal_lines(ws)
        ]


def test_hcm2_04_legacy_append_failure_propagates_no_success(tmp_path, monkeypatch):
    """HCM2-04: legacy append OSError propagates; no SUCCESS row is left behind."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = _make_ws(tmp_path)
    orch = ResearchOrchestrator(ws)

    def _boom(*a, **k):
        raise OSError("journal unwritable")

    monkeypatch.setattr("scholar_harness.workspace.audit.append_legacy_event", _boom)
    with pytest.raises(OSError):
        orch._log_audit_event(
            action="RAG_INDEX_BUILT",
            agent="scholar-harness",
            description="boom",
            inputs=[],
            outputs=[],
            metrics={},
            status="SUCCESS",
        )
    assert _journal_lines(ws) == []


def test_hcm2_04_canonical_append_failure_propagates(tmp_path, monkeypatch):
    ws = _make_ws(tmp_path)
    import scholar_harness.workspace.audit as svc

    def _boom_open(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", _boom_open)
    with pytest.raises(OSError):
        svc.append_event(ws, "PROBE", "d")
    # Best-effort projection must not have created a success illusion elsewhere.
    assert not (ws / "artifacts").exists()


# ---------------------------------------------------------------------------
# HCM2-05: one whole valid event, prior rows byte-preserved
# ---------------------------------------------------------------------------


def test_hcm2_05_canonical_serial_preserves_first_line(tmp_path):
    ws = _make_ws(tmp_path)
    first = neutral_audit.append_event(
        ws, "my_action", "first", status="success", refresh_index=False
    )
    first_bytes = (ws / "audit" / "journal.jsonl").read_bytes()
    second = neutral_audit.append_event(
        ws, "second_action", "second", status="failed", refresh_index=False
    )
    lines = _journal_lines(ws)
    assert len(lines) == 2
    assert lines[0] == first_bytes.decode("utf-8").strip()
    assert json.loads(lines[0])["action"] == "MY_ACTION"
    assert json.loads(lines[1])["status"] == "FAILED"
    assert EVT_RE.match(json.loads(lines[0])["event_id"])
    assert first["event_id"] == json.loads(lines[0])["event_id"]
    assert second["event_id"] == json.loads(lines[1])["event_id"]


def test_hcm2_05_legacy_serial_preserves_first_line_and_scheme(tmp_path):
    """HCM2-05 + parity: orchestrator legacy keeps odd scheme, first line stable."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = _make_ws(tmp_path)
    pj_before = (ws / "project.json").read_bytes()
    orch = ResearchOrchestrator(ws)
    orch._log_audit_event(
        action="my_action",
        agent="scholar-harness",
        description="first",
        inputs=[],
        outputs=[],
        metrics={},
        status="success",
    )
    first_bytes = (ws / "audit" / "journal.jsonl").read_bytes()
    orch._log_audit_event(
        action="second_action",
        agent="scholar-harness",
        description="second",
        inputs=[],
        outputs=[],
        metrics={},
        status="failed",
    )
    lines = _journal_lines(ws)
    assert len(lines) == 2
    assert lines[0] == first_bytes.decode("utf-8").strip()
    first_rec, second_rec = json.loads(lines[0]), json.loads(lines[1])
    # Preserved divergence: legacy does NOT uppercase (canonical would).
    assert first_rec["action"] == "my_action"
    assert first_rec["status"] == "success"
    assert second_rec["action"] == "second_action"
    # Odd scheme still EVT-shaped; provenance minted by writer.
    assert EVT_RE.match(first_rec["event_id"])
    assert first_rec["event_id"] != second_rec["event_id"]
    # Legacy appends no manifest update and no INDEX side effects.
    assert (ws / "project.json").read_bytes() == pj_before
    assert set(first_rec) == {
        "timestamp",
        "event_id",
        "action",
        "agent_or_tool",
        "description",
        "parameters",
        "inputs",
        "outputs",
        "metrics",
        "status",
    }


def test_hcm2_05_handoff_preserves_success_for_phase_advance(tmp_path):
    """Handoff parity: PHASE_ADVANCE stays hardcoded SUCCESS via neutral legacy."""
    from scholar_harness import handoff

    ws = _make_ws(tmp_path)
    pj_before = (ws / "project.json").read_bytes()
    handoff._log_audit_event(
        ws,
        action="PHASE_ADVANCE",
        agent="supervisor",
        description="Phase advanced from INCEPTION to SCREENING",
        inputs=[],
        outputs=["handoff_state.json"],
        metrics={"from_phase": "INCEPTION", "to_phase": "SCREENING"},
    )
    rec = json.loads(_journal_lines(ws)[-1])
    assert rec["action"] == "PHASE_ADVANCE"
    assert rec["status"] == "SUCCESS"
    assert EVT_RE.match(rec["event_id"])
    assert (ws / "project.json").read_bytes() == pj_before


# ---------------------------------------------------------------------------
# HCM2-06: sync-index refreshes INDEX with zero new audit rows
# ---------------------------------------------------------------------------


def test_hcm2_06_refresh_atomic_appends_no_rows_and_restores_on_empty(tmp_path):
    ws = _make_ws(tmp_path)
    (ws / "INDEX.md").write_text("# old index", encoding="utf-8")
    (ws / "audit").mkdir(exist_ok=True)
    (ws / "audit" / "journal.jsonl").write_text('{"action":"OLD"}\n', encoding="utf-8")
    before = (ws / "audit" / "journal.jsonl").read_bytes()

    def _empty(_w):
        (_w / "INDEX.md").write_text("   \n", encoding="utf-8")

    assert neutral_audit.refresh_index_atomic(ws, refresher=_empty) is False
    assert (ws / "INDEX.md").read_text(encoding="utf-8") == "# old index"
    assert (ws / "audit" / "journal.jsonl").read_bytes() == before


def test_hcm2_06_refresh_atomic_success_appends_no_rows(tmp_path):
    ws = _make_ws(tmp_path)
    (ws / "INDEX.md").write_text("# old", encoding="utf-8")
    (ws / "audit").mkdir(exist_ok=True)
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")

    def _good(_w):
        (_w / "INDEX.md").write_text("# Project Index: T\n", encoding="utf-8")

    assert neutral_audit.refresh_index_atomic(ws, refresher=_good) is True
    assert "Project Index" in (ws / "INDEX.md").read_text(encoding="utf-8")
    assert _journal_lines(ws) == []


def test_hcm2_06_orchestrator_refresh_appends_no_rows(tmp_path):
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = _make_ws(tmp_path)
    (ws / "INDEX.md").write_text("# old", encoding="utf-8")
    (ws / "audit").mkdir(exist_ok=True)
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    orch = ResearchOrchestrator(ws)
    orch._refresh_index_md_atomic()
    assert _journal_lines(ws) == []


def test_hcm2_06_cli_sync_index_refreshes_without_appending(tmp_path):
    from typer.testing import CliRunner

    from scholar_harness.cli import app
    from scholar_harness.inception import init_command

    runner = CliRunner()
    ws = tmp_path / "ws"
    init_command("Sync Probe", ws, scaffold_only=True)
    before = len(_journal_lines(ws))
    (ws / "INDEX.md").write_text("JUNK THAT MUST BE REGENERATED\n", encoding="utf-8")
    result = runner.invoke(app, ["log", "sync-index", str(ws)])
    assert result.exit_code == 0, result.output
    assert "JUNK" not in (ws / "INDEX.md").read_text(encoding="utf-8")
    assert len(_journal_lines(ws)) == before


# ---------------------------------------------------------------------------
# HCM2-07: NEXUS_SKILLS_SRC / wheel / repo precedence, CWD-independent
# ---------------------------------------------------------------------------


def test_hcm2_07_env_override_preferred_cwd_independent(tmp_path, monkeypatch):
    from scholar_harness.audit_log import _resolve_log_module

    source = (
        REPO_ROOT
        / ".agents"
        / "skills"
        / "workspace-manager"
        / "scripts"
        / "log_event.py"
    )
    assert source.is_file()
    fake = tmp_path / "bundle"
    (fake / "workspace-manager" / "scripts").mkdir(parents=True)
    shutil.copy2(source, fake / "workspace-manager" / "scripts" / "log_event.py")
    monkeypatch.setenv("NEXUS_SKILLS_SRC", str(fake))
    monkeypatch.setattr(inception, "_log_module_ref", None)
    monkeypatch.setattr(inception, "_log_module_tried", False)
    bare = tmp_path / "bare"
    bare.mkdir()
    monkeypatch.chdir(bare)
    module = _resolve_log_module()
    assert module is not None
    assert str(Path(module.__file__).resolve()).startswith(str(fake.resolve()))
    assert neutral_loader.resolve_skills_root() == fake.resolve()
    assert (
        neutral_loader.resolve_workspace_manager_scripts()
        == (fake / "workspace-manager" / "scripts").resolve()
    )


def test_hcm2_07_wheel_bundle_reached_from_bare_cwd(tmp_path, monkeypatch):
    ws = _make_ws(tmp_path)
    source = (
        REPO_ROOT
        / ".agents"
        / "skills"
        / "workspace-manager"
        / "scripts"
        / "log_event.py"
    )
    fake = tmp_path / "wheel-bundle"
    (fake / "workspace-manager" / "scripts").mkdir(parents=True)
    shutil.copy2(source, fake / "workspace-manager" / "scripts" / "log_event.py")
    monkeypatch.delenv("NEXUS_SKILLS_SRC", raising=False)
    monkeypatch.setattr(inception, "_bundled_skills_root", lambda: fake)
    monkeypatch.setattr(inception, "_log_module_ref", None)
    monkeypatch.setattr(inception, "_log_module_tried", False)
    bare = tmp_path / "bare2"
    bare.mkdir()
    monkeypatch.chdir(bare)
    from scholar_harness.audit_log import _resolve_log_module

    module = _resolve_log_module()
    assert module is not None
    assert str(Path(module.__file__).resolve()).startswith(str(fake.resolve()))


def test_hcm2_07_strict_resolver_refuses_plain_dir(tmp_path):
    from scholar_harness.audit_log import _NotWorkspaceError, _resolve_workspace

    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(_NotWorkspaceError):
        _resolve_workspace(plain)
    assert not (plain / "audit" / "journal.jsonl").exists()
    with pytest.raises(NotWorkspaceError):
        neutral_audit.resolve_workspace(plain)


# ---------------------------------------------------------------------------
# HCM2-08: every caller migrated / retained / blocked (no hidden legacy)
# ---------------------------------------------------------------------------


def test_hcm2_08_no_hidden_legacy_log_loader():
    """No hand-rolled importlib log_event load remains outside the neutral loader."""
    offenders = []
    for rel in [
        "src/scholar_harness/orchestrator.py",
        "src/scholar_harness/handoff.py",
        "src/scholar_harness/audit_log.py",
        "src/scholar_harness/inception/genesis.py",
        "src/scholar_harness/contracts/acceptance.py",
        "src/scholar_harness/index_acceptance.py",
        "src/scholar_harness/extraction_producer.py",
    ]:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if "spec_from_file_location" in text and "log_event" in text:
            offenders.append(rel)
    assert offenders == []


def test_hcm2_08_extraction_identity_retained_with_reason():
    """extraction_producer identity stays local: PublicationRefused policy is scientific-adjacent.

    Only its audit sink migrates to neutral; its ``_recorded_workspace_id``
    (WORKSPACE_MANIFEST_* / WORKSPACE_IDENTITY_* codes) is retained to avoid
    entangling publication policy with this internal refactor.
    """
    import scholar_harness.extraction_producer as producer

    assert producer.log_event is neutral_audit.log_event
    src = Path(producer.__file__).read_text(encoding="utf-8")
    assert "PublicationRefused" in src
    assert "WORKSPACE_IDENTITY_NOT_RECORDED" in src


# ---------------------------------------------------------------------------
# HCM2-09: no migration / minting / contract / scientific-policy change
# ---------------------------------------------------------------------------


def test_hcm2_09_consumers_never_mint(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        neutral_identity.require_recorded_identity(ws)
    # No manifest was created as a side effect of refusal.
    assert not (ws / "project.json").exists()


def test_hcm2_09_init_mints_only_when_no_recorded_identity(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    minted = neutral_identity.recorded_or_minted_workspace_id(empty)
    assert re.fullmatch(r"^WSP-[0-9a-f]{32}$", minted)
    ws = _make_ws(tmp_path)
    # Valid recorded identity is reused, never replaced.
    assert neutral_identity.recorded_or_minted_workspace_id(ws) == WSP_VALID


def test_hcm2_09_slug_is_never_an_identity(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "my-slug"}), encoding="utf-8"
    )
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as exc:
        neutral_identity.require_recorded_identity(ws)
    assert "my-slug" in str(exc.value)
    assert "registered_workspace_id" in str(exc.value)


# ---------------------------------------------------------------------------
# HCM2-10 + end-to-end: valid recorded workspace through the service
# ---------------------------------------------------------------------------


def test_hcm2_10_valid_workspace_end_to_end_through_service(tmp_path):
    """Valid recorded workspace works end-to-end through the neutral service."""
    from scholar_harness.orchestrator import ResearchOrchestrator

    ws = _make_ws(tmp_path)
    ws_id = neutral_identity.require_recorded_identity(ws)
    assert ws_id == WSP_VALID
    assert ResearchOrchestrator(ws).recorded_workspace_id() == ws_id
    event = neutral_audit.append_event(
        ws, "probe", "end-to-end", agent="test", metrics={}, refresh_index=False
    )
    assert EVT_RE.match(event["event_id"])
    assert event["action"] == "PROBE"
    assert neutral_audit.refresh_index_atomic(ws, refresher=_w_index) is True


def _w_index(w: Path):
    (w / "INDEX.md").write_text("# Project Index: T\n", encoding="utf-8")
