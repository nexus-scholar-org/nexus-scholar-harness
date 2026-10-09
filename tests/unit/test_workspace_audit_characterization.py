"""HCM-01 characterization: workspace identity, manifest merge, and audit behavior.

Test-only; no production behavior is changed here. All fixtures live under
``tmp_path`` (never ``workspaces/``). Observations pin what the code does
today; ``OBSERVED-NOT-APPROVED`` marks behavior recorded without endorsing it
as a future policy. No test claims cross-process locking, fsync durability,
whole-bundle atomicity, or crash recovery: the serial appends below prove
only serial append-only discipline.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
from pathlib import Path

import pytest

from scholar_harness.console.api import audit as console_audit
from scholar_harness.inception.genesis import (
    recorded_or_minted_workspace_id,
    scaffold_raw_project,
    validate_registered_workspace_id,
)
from scholar_harness.orchestrator import (
    RegisteredWorkspaceIdentityMissingError,
    ResearchOrchestrator,
)

EVT_RE = re.compile(r"^EVT-\d{14}-[0-9a-f]{6}$")
WSP_VALID = "WSP-" + "a" * 32


def _manifest(ws: Path) -> dict:
    return json.loads((ws / "project.json").read_text(encoding="utf-8"))


def _journal_lines(ws: Path) -> list[str]:
    journal = ws / "audit" / "journal.jsonl"
    if not journal.exists():
        return []
    return [
        line
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ---------------------------------------------------------------------------
# HC1-1: mint-once, then re-read through the resolver
# ---------------------------------------------------------------------------


def test_hc1_1_mint_then_reread_via_resolver_returns_same_value(tmp_path):
    """HC1-1 gap: scaffold mints once; the resolver re-reads the same value.

    Existing tests pin mint shape, stability across raw manifest re-reads,
    and orchestrator agreement; this pins the resolver path itself.
    """
    ws = scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )
    recorded = _manifest(ws)["registered_workspace_id"]
    assert recorded != "evidence-synthesis"
    assert recorded_or_minted_workspace_id(ws) == recorded
    assert ResearchOrchestrator(ws).recorded_workspace_id() == recorded
    assert validate_registered_workspace_id(recorded) == recorded


# ---------------------------------------------------------------------------
# HC1-2: consumer refusal (orchestrator.recorded_workspace_id + Stage 6 gate)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "must_name"),
    [
        (
            json.dumps({"registered_workspace_id": "WSP-legacy-workspace-1"}),
            "WSP-legacy-workspace-1",
        ),
        (json.dumps({"registered_workspace_id": "WSP-" + "a" * 31}), "WSP-" + "a" * 31),
        (json.dumps({"registered_workspace_id": 42}), "registered_workspace_id"),
        ("{not json", "project.json"),
        (
            json.dumps({"project_id": "my-slug", "registered_workspace_id": "my-slug"}),
            "my-slug",
        ),
    ],
    ids=[
        "hc1_2-legacy-non-hex",
        "hc1_2-short",
        "hc1_2-non-string",
        "hc1_2-corrupt",
        "hc1_2-slug-as-id",
    ],
)
def test_hc1_2_consumer_refuses_invalid_recorded_forms(tmp_path, raw, must_name):
    """HC1-2: the consumer refuses invalid recorded identity with a typed error.

    The slug is never returned as an identity in any case.
    """
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text(raw, encoding="utf-8")
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as excinfo:
        ResearchOrchestrator(ws).recorded_workspace_id()
    message = str(excinfo.value)
    assert must_name in message
    assert "registered_workspace_id" in message


def test_hc1_2_refusal_leaves_bytes_and_store_untouched(tmp_path, monkeypatch):
    """HC1-2: refusal happens before any backend/store and changes no bytes."""
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "evidence-synthesis"}), encoding="utf-8"
    )
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    pj_before = (ws / "project.json").read_bytes()
    journal_before = (ws / "audit" / "journal.jsonl").read_bytes()
    chroma_dir = ws / "rag" / "chroma_db"

    def _boom(**kwargs):
        raise AssertionError(
            "backend must not be constructed before identity validation"
        )

    import scholar_harness.orchestrator as orch_module

    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom)
    monkeypatch.setattr(orch_module, "get_embedder", _boom)

    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        ResearchOrchestrator(ws)._run_indexing_stage(chroma_dir)

    assert (ws / "project.json").read_bytes() == pj_before
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert not chroma_dir.exists()


def test_hc1_2_nonobject_consumer_manifest_crashes_untyped_observed(tmp_path):
    """HC1-2 OBSERVED-NOT-APPROVED: non-object manifest crashes without a typed refusal.

    ``recorded_workspace_id`` calls ``manifest.get`` outside its ``try`` block,
    so a JSON array manifest raises ``AttributeError`` instead of
    ``RegisteredWorkspaceIdentityMissingError``. Recorded as an unexpected
    defect; HCM-02 must decide the typed policy. Not a claim of correct behavior.
    """
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(AttributeError):
        ResearchOrchestrator(ws).recorded_workspace_id()


# ---------------------------------------------------------------------------
# HC1-3: manifest merge, dry-run, malformed-manifest observation
# ---------------------------------------------------------------------------


def test_hc1_3_sync_preserves_unrelated_fields_and_merges_stats(tmp_path):
    """HC1-3: sync merges counted stats, keeps unrelated fields and custom stats."""
    ws = tmp_path / "ws"
    ws.mkdir()
    before_updated = "2026-01-01T00:00:00+00:00"
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "my-slug",
                "registered_workspace_id": WSP_VALID,
                "title": "My Title",
                "paradigm": "Positivist",
                "research_questions": ["RQ1?"],
                "keywords": ["k"],
                "custom_field": "keep-me",
                "status": "active",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": before_updated,
                "stats": {"discovered_papers": 99, "my_custom_stat": 7},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    lit = ws / "literature"
    lit.mkdir()
    (lit / "raw_search.json").write_text(
        json.dumps([{"x": 1}, {"x": 2}]), encoding="utf-8"
    )

    result = ResearchOrchestrator(ws).sync_state()

    assert result["dry_run"] is False
    after = _manifest(ws)
    assert after["registered_workspace_id"] == WSP_VALID
    assert after["custom_field"] == "keep-me"
    assert after["title"] == "My Title"
    assert after["paradigm"] == "Positivist"
    assert after["research_questions"] == ["RQ1?"]
    assert after["stats"]["discovered_papers"] == 2
    assert after["stats"]["my_custom_stat"] == 7
    assert after["updated_at"] != before_updated


def test_hc1_3_dry_run_writes_nothing(tmp_path):
    """HC1-3: dry-run returns dry_run True and changes no bytes, logs no event."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "s",
                "registered_workspace_id": WSP_VALID,
                "title": "T",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "stats": {"discovered_papers": 5},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (ws / "INDEX.md").write_text("# old index", encoding="utf-8")
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text('{"action":"OLD"}\n', encoding="utf-8")
    pj_before = (ws / "project.json").read_bytes()
    idx_before = (ws / "INDEX.md").read_bytes()
    journal_before = (ws / "audit" / "journal.jsonl").read_bytes()
    lit = ws / "literature"
    lit.mkdir()
    (lit / "raw_search.json").write_text(json.dumps([{"x": 1}]), encoding="utf-8")

    result = ResearchOrchestrator(ws).sync_state(dry_run=True)

    assert result["dry_run"] is True
    assert result["index_regenerated"] is False
    assert (ws / "project.json").read_bytes() == pj_before
    assert (ws / "INDEX.md").read_bytes() == idx_before
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert b"STATE_SYNC" not in journal_before
    assert b"STATE_SYNC" not in (ws / "audit" / "journal.jsonl").read_bytes()


def test_hc1_3_corrupt_manifest_rebuilds_fresh_observed(tmp_path):
    """HC1-3 OBSERVED-NOT-APPROVED: corrupt JSON is replaced with a fresh default.

    ``sync_state`` swallows the decode error (``except Exception: manifest = {}``)
    and writes a fresh manifest with ``project_id == ws.name``. The corrupt
    recorded identity is silently discarded. This is today's behavior, not an
    approved repair policy; HCM-02 must decide the malformed-manifest policy.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text("{not json", encoding="utf-8")
    (ws / "literature").mkdir()
    (ws / "literature" / "raw_search.json").write_text("[]", encoding="utf-8")

    ResearchOrchestrator(ws).sync_state()

    after = _manifest(ws)
    assert after["project_id"] == ws.name
    assert "registered_workspace_id" not in after


def test_hc1_3_nonobject_manifest_raises_typeerror_observed(tmp_path):
    """HC1-3 OBSERVED-NOT-APPROVED: a JSON-array manifest crashes sync.

    ``manifest['updated_at'] = ...`` assumes a dict, so a valid-JSON non-object
    raises ``TypeError``. Recorded as an unexpected defect; no approved policy
    is claimed.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(TypeError):
        ResearchOrchestrator(ws).sync_state()


# ---------------------------------------------------------------------------
# HC1-4: serial journal append discipline (console audit surface)
# ---------------------------------------------------------------------------


def test_hc1_4_serial_append_preserves_first_line(tmp_path):
    """HC1-4: two serial appends via console audit keep the first line byte-identical.

    Provenance (event_id/timestamp) is minted by the writer; the caller cannot
    set it. Action/status are uppercased and retained. Explicit non-claim: no
    concurrency, fsync, crash-durability, or whole-bundle atomicity is proven.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "s",
                "title": "T",
                "registered_workspace_id": WSP_VALID,
                "updated_at": "2026-01-01T00:00:00+00:00",
                "stats": {},
            }
        ),
        encoding="utf-8",
    )
    first = console_audit.log_event(
        ws,
        action="my_action",
        description="first",
        status="success",
        refresh_index=False,
    )
    first_bytes = (ws / "audit" / "journal.jsonl").read_bytes()
    second = console_audit.log_event(
        ws,
        action="second_action",
        description="second",
        status="failed",
        refresh_index=False,
    )

    lines = _journal_lines(ws)
    assert len(lines) == 2
    assert lines[0] == first_bytes.decode("utf-8").strip()
    first_record = json.loads(lines[0])
    second_record = json.loads(lines[1])
    assert first_record["action"] == "MY_ACTION"
    assert first_record["status"] == "SUCCESS"
    assert second_record["action"] == "SECOND_ACTION"
    assert second_record["status"] == "FAILED"
    assert EVT_RE.match(first_record["event_id"])
    assert EVT_RE.match(second_record["event_id"])
    assert first_record["event_id"] != second_record["event_id"]
    _dt.datetime.fromisoformat(first_record["timestamp"])
    _dt.datetime.fromisoformat(second_record["timestamp"])
    assert first["event_id"] == first_record["event_id"]
    assert second["event_id"] == second_record["event_id"]


# ---------------------------------------------------------------------------
# HC1-5: projections (stats gating, identity preservation, best-effort refresh)
# ---------------------------------------------------------------------------


def test_hc1_5_projection_ignores_unknown_stats_and_preserves_identity(tmp_path):
    """HC1-5: only pre-existing stats keys are projected; identity is preserved."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "s",
                "title": "T",
                "registered_workspace_id": WSP_VALID,
                "updated_at": "2026-01-01T00:00:00+00:00",
                "stats": {"discovered_papers": 5, "verified_papers": 3},
            }
        ),
        encoding="utf-8",
    )
    event = console_audit.log_event(
        ws,
        action="probe",
        description="d",
        metrics={"discovered_papers": 9, "verified_papers": 4, "unknown_stat": 123},
        refresh_index=False,
    )
    assert event["metrics"]["unknown_stat"] == 123
    after = _manifest(ws)
    assert after["registered_workspace_id"] == WSP_VALID
    assert after["stats"]["discovered_papers"] == 9
    assert after["stats"]["verified_papers"] == 4
    assert "unknown_stat" not in after["stats"]
    assert after["updated_at"] != "2026-01-01T00:00:00+00:00"


def test_hc1_5_refresher_failure_does_not_block_journal(tmp_path, monkeypatch):
    """HC1-5: a raising INDEX refresher does not fail the journal append."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "s",
                "title": "T",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "stats": {},
            }
        ),
        encoding="utf-8",
    )

    def _boom_loader():
        def _boom(_workspace: Path):
            raise RuntimeError("index boom")

        return _boom

    monkeypatch.setattr(console_audit, "_INDEX_MD_REFRESH", None)
    monkeypatch.setattr(console_audit, "_load_index_refresher", _boom_loader)

    event = console_audit.log_event(
        ws, action="probe", description="d", refresh_index=True
    )

    assert event["action"] == "PROBE"
    assert (ws / "audit" / "journal.jsonl").exists()
    assert json.loads(_journal_lines(ws)[-1])["event_id"] == event["event_id"]


# ---------------------------------------------------------------------------
# HC1-6: journal-failure atomic rollback (minimal accept_artifact case)
# ---------------------------------------------------------------------------


def test_hc1_6_accept_failure_reports_atomic_and_publishes_nothing(
    tmp_path, monkeypatch
):
    """HC1-6: journal failure yields structured ATOMIC_COMMIT_FAILED and no publication."""
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    import scholar_harness.contracts.acceptance as acceptance

    fixture = (
        Path(__file__).resolve().parents[1]
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

    def _fail_audit(*args, **kwargs):
        raise OSError("audit unavailable")

    monkeypatch.setattr(acceptance, "log_event", _fail_audit)

    result = accept_artifact(ws, artifact, expected=context)

    assert result.accepted is False
    assert result.published_path is None
    assert result.event_id is None
    assert [issue.code for issue in result.issues] == ["ATOMIC_COMMIT_FAILED"]
    assert not (ws / "artifacts").exists()
    assert not (ws / "audit" / "artifact_registry.json").exists()
    journal = ws / "audit" / "journal.jsonl"
    if journal.exists():
        actions = [json.loads(line).get("action") for line in _journal_lines(ws)]
        assert "ARTIFACT_ACCEPTED" not in actions


# ---------------------------------------------------------------------------
# HC1-7: portable loader via NEXUS_SKILLS_SRC
# ---------------------------------------------------------------------------


def test_hc1_7_portable_loader_prefers_env_override(tmp_path, monkeypatch):
    """HC1-7: audit_log resolves log_event.py through the NEXUS_SKILLS_SRC override."""
    from scholar_harness import inception
    from scholar_harness.audit_log import _resolve_log_module

    repo_root = Path(__file__).resolve().parents[2]
    source_script = (
        repo_root
        / ".agents"
        / "skills"
        / "workspace-manager"
        / "scripts"
        / "log_event.py"
    )
    assert source_script.is_file()
    fake_bundle = tmp_path / "wheel-bundle-skills"
    (fake_bundle / "workspace-manager" / "scripts").mkdir(parents=True)
    shutil.copy2(
        source_script, fake_bundle / "workspace-manager" / "scripts" / "log_event.py"
    )

    monkeypatch.setenv("NEXUS_SKILLS_SRC", str(fake_bundle))
    monkeypatch.setattr(inception, "_log_module_ref", None)
    monkeypatch.setattr(inception, "_log_module_tried", False)

    module = _resolve_log_module()

    assert module is not None
    assert hasattr(module, "log_project_event")
    assert str(Path(module.__file__).resolve()).startswith(str(fake_bundle.resolve()))
