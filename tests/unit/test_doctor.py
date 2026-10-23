"""P7.5 tests: ``nexus-scholar doctor`` — distribution-health checks.

Hermetic: ``tmp_path`` workspaces, an injectable ``{kit: importable}`` map for
the kits check, and monkeypatched resolver/check seams -- no network, no heavy
dependencies.

Seam-context note: the dev environment installs the harness as
``nexus-scholar-harness``; the ``scholar-agent`` entrypoint ships from the
``scholar-agent-kit`` console script. The ``nexus-scholar`` metapackage
entrypoint is wheel-provided and therefore asserted only where it is
guaranteed to exist (the ``uvx --from`` smoke).
"""

from __future__ import annotations

import json
import re
import shutil

from typer.testing import CliRunner

from scholar_harness import doctor as doctor_mod
from scholar_harness.cli import app
from scholar_harness.doctor import (
    CheckResult,
    Status,
    check_keys,
    check_kits,
    check_layout,
    check_seam,
    check_skills,
    load_kit_manifest,
)

runner = CliRunner()

# Rich renders typer help through a Console; when the environment forces color
# (FORCE_COLOR, CI, a tty) ANSI style codes are interleaved inside the rendered
# flag text, so raw ``in result.stdout`` checks only hold in plain-render
# environments. Stripping the escapes asserts the real invariant -- the flag is
# registered and documented in ``--help`` -- under every rendering mode.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _help_text(result) -> str:
    """The ``--help`` output with ANSI styling removed (render-mode independent)."""
    return _ANSI_RE.sub("", result.stdout)


def _pass_seam() -> list[CheckResult]:
    return [
        CheckResult("seam", "python-version", Status.PASS, "Python 3"),
        CheckResult("seam", "cli-import", Status.PASS, "app importable"),
        CheckResult("seam", "entrypoint-nexus-scholar", Status.PASS, "present"),
        CheckResult("seam", "entrypoint-scholar-agent", Status.PASS, "present"),
    ]


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_doctor_command_registered():
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    help_text = _help_text(result)
    assert "--workspace" in help_text
    assert "--env-file" in help_text
    assert "--json" in help_text
    assert "--exit-code" in help_text
    assert (
        "Validate kits/versions, API keys, skills, and workspace layout"
        in help_text
    )


# ---------------------------------------------------------------------------
# kits
# ---------------------------------------------------------------------------


def test_kits_all_importable_dev_env():
    manifest = load_kit_manifest()
    assert len(manifest) == 8  # all 8 scholar-*-kit packages declared
    results = check_kits()
    assert [r.name for r in results] == list(manifest)
    assert all(r.status == Status.PASS for r in results)
    # every declared kit carries its pinned default_rev in the detail
    assert all("pinned" in r.detail for r in results)


def test_load_kit_manifest_wheel_fallback(tmp_path, monkeypatch):
    """The wheel-deployed scenario: no repo plugins.json, bundled pins snapshot."""
    pins = tmp_path / "nexus_scholar_pins.json"
    pins.write_text(
        json.dumps(
            {
                "kits": [
                    {"name": "scholar-rag-kit", "default_rev": "abc123"},
                    {"name": "other"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor_mod, "_repo_plugins_json", lambda: tmp_path / "ghost")
    monkeypatch.setattr(doctor_mod, "_wheel_pins_path", lambda: pins)
    manifest = load_kit_manifest()
    assert manifest == {"scholar-rag-kit": "abc123", "other": ""}
    # no repo, no wheel -> empty manifest (doctor stays usable)
    monkeypatch.setattr(doctor_mod, "_wheel_pins_path", lambda: None)
    assert load_kit_manifest() == {}


def test_kits_fail_reachable_via_importable_map():
    names = [r.name for r in check_kits()]
    importable_map = dict.fromkeys(names, True)
    importable_map["scholar-rag-kit"] = False
    results = check_kits(importable_map=importable_map)
    assert [r.name for r in results] == names
    assert any(r.status == Status.FAIL for r in results)
    rag = next(r for r in results if r.name == "scholar-rag-kit")
    assert "import FAILED" in rag.detail


def test_cli_doctor_fail_reachable_via_monkeypatch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor_mod,
        "check_kits",
        lambda importable_map=None: [
            CheckResult("kits", "scholar-rag-kit", Status.FAIL, "import FAILED")
        ],
    )
    result = runner.invoke(app, ["doctor", "--workspace", str(tmp_path)])
    assert result.exit_code == 0  # advisory default
    assert "FAIL" in result.stdout


# ---------------------------------------------------------------------------
# keys (presence checks, values never echoed)
# ---------------------------------------------------------------------------


def test_keys_mailto_pass_model_keys_warn_not_fail(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SCHOLAR_MAILTO=me@example.com\n", encoding="utf-8")
    results = check_keys(env)
    by_name = {r.name: r.status for r in results}
    assert by_name["SCHOLAR_MAILTO"] == Status.PASS
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        assert by_name[key] == Status.WARN
    assert not any(r.status == Status.FAIL for r in results)
    assert not any("me@example.com" in r.detail for r in results)


def test_keys_no_env_file_skips():
    results = check_keys(None)
    assert len(results) == 1
    assert results[0].status == Status.SKIP


def test_keys_missing_mailto_warns(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=sk-value\n", encoding="utf-8")
    results = check_keys(env)
    by_name = {r.name: r.status for r in results}
    assert by_name["SCHOLAR_MAILTO"] == Status.WARN
    assert by_name["OPENAI_API_KEY"] == Status.PASS


# ---------------------------------------------------------------------------
# skills
# ---------------------------------------------------------------------------


def test_skills_pass_when_resolver_has_skills(tmp_path):
    root = tmp_path / "skills-root"
    (root / "scholar-search-kit").mkdir(parents=True)
    (root / "scholar-search-kit" / "SKILL.md").write_text(
        "# scholar-search\n", encoding="utf-8"
    )
    results = check_skills(skills_root=root)
    assert len(results) == 1
    assert results[0].status == Status.PASS


def test_skills_fail_when_resolver_none(monkeypatch):
    monkeypatch.setattr("scholar_harness.inception.resolve_skills_root", lambda: None)
    results = check_skills()
    assert len(results) == 1
    assert results[0].status == Status.FAIL
    assert "NEXUS_SKILLS_SRC" in results[0].detail  # guidance line present


# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------


def _scaffold(tmp_path):
    from scholar_harness.inception import init_command

    ws = tmp_path / "proj"
    init_command("Doctor Test Project", ws, scaffold_only=True)
    return ws


def test_layout_pass_on_scaffolded_workspace(tmp_path):
    ws = _scaffold(tmp_path)
    results = check_layout(ws)
    assert results
    assert any(r.name == "canonical-files" and r.status == Status.PASS for r in results)
    assert not any(r.status == Status.FAIL for r in results)


def test_layout_fail_when_protocol_removed(tmp_path):
    ws = _scaffold(tmp_path)
    (ws / "protocol.json").unlink()
    results = check_layout(ws)
    assert any(r.status == Status.FAIL for r in results)
    canonical = next(r for r in results if r.name == "canonical-files")
    assert "protocol.json" in canonical.detail


def test_layout_skip_on_empty_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    results = check_layout(empty)
    assert results
    assert all(r.status == Status.SKIP for r in results)


def test_layout_bom_tolerant_when_stats_stale(tmp_path):
    """Windows tools write UTF-8 BOM; doctor must still read/parse project.json."""
    ws = _scaffold(tmp_path)
    (ws / "literature" / "raw_search.json").write_text("[{}]", encoding="utf-8")
    manifest = ws / "project.json"
    content = manifest.read_text(encoding="utf-8")
    manifest.write_text("\ufeff" + content, encoding="utf-8")
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    # Stale (raw_search.json has 1 doc, declared 0) -- and a stale summary is
    # a correctness defect (FAIL), not a soft hint (T-TRUTH-COUNTS-01).
    assert stats.status == Status.FAIL
    assert "declared=0" in stats.detail and "actual=1" in stats.detail


def test_layout_stale_stats_is_fail_not_warn(tmp_path):
    """AC-3: a declared-vs-actual mismatch is FAIL-severity, never WARN."""
    ws = _scaffold(tmp_path)
    (ws / "literature" / "raw_search.json").write_text(
        json.dumps([{"t": 1}, {"t": 2}]), encoding="utf-8"
    )
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status is Status.FAIL
    assert not any(
        r.name == "project.json-stats" and r.status is Status.WARN for r in results
    )


def test_layout_reports_physical_corpus_counts(tmp_path):
    """AC-2: the doctor summary states the physically counted corpus."""
    ws = _scaffold(tmp_path)
    corpus = ws / "calibration"
    corpus.mkdir()
    (corpus / "raw_union.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(7)]}), encoding="utf-8"
    )
    results = check_layout(ws)
    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is Status.PASS
    assert "7" in corpus_check.detail
    assert "calibration/raw_union.json" in corpus_check.detail


def test_layout_reports_no_corpus_explicitly(tmp_path):
    """N-2/D-2: an empty workspace says "no corpus" -- and reconciles.

    ``NO_CORPUS`` means "this workspace holds no corpus artifact at all": a
    verifiable state that reconciles against the declared ``0`` (PASS). It is
    not the old conflated "nothing was counted" state.
    """
    ws = _scaffold(tmp_path)
    results = check_layout(ws)
    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is Status.PASS
    assert "no corpus artifact" in corpus_check.detail.lower()


# ---------------------------------------------------------------------------
# T-TRUTH-COUNTS-01 repair: a reconciliation that never happened is not PASS
# ---------------------------------------------------------------------------


def test_layout_project_stats_pass_for_a_corpus_free_workspace(tmp_path):
    """B2/D-2: a corpus-free workspace RECONCILES against its declared 0.

    The old state ("NOT RECONCILED -- NOTHING WAS COUNTED") conflated "this
    workspace holds no corpus" with "the reconciliation never happened"; the
    two are separate, verifiable states now.
    """
    ws = _scaffold(tmp_path)
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status is Status.PASS
    assert "no corpus artifact in this workspace" in stats.detail
    assert "reconcile against the physical state" in stats.detail


def test_layout_project_stats_not_pass_for_unclassified_corpus(tmp_path):
    """B2: a corpus artifact with an unrecognised name is not a PASS."""
    ws = _scaffold(tmp_path)
    (ws / "literature" / "mystery_dump.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(4)]}), encoding="utf-8"
    )
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status is not Status.PASS
    assert stats.status is Status.FAIL
    assert "NOT RECONCILED" in stats.detail
    assert "mystery_dump.json" in stats.detail


def test_layout_unreadable_corpus_artifact_is_a_named_non_pass_state(tmp_path):
    """B2: an unreadable corpus artifact is named, never a silent 0."""
    ws = _scaffold(tmp_path)
    (ws / "literature" / "raw_search.json").write_text(
        '[{"t": 1}, {"t"', encoding="utf-8"
    )
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status is Status.FAIL
    assert "UNREADABLE" in stats.detail
    assert "raw_search.json" in stats.detail

    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is Status.FAIL
    assert "raw_search.json" in corpus_check.detail


def test_layout_json_output_distinguishes_not_reconciled_from_pass(tmp_path, monkeypatch):
    """B2/B-F5: the --json output distinguishes "not reconciled" from a PASS.

    The seam is stubbed with ``_pass_seam()`` so the verdict is decided by
    the reconciliation alone -- an unrelated seam WARN must never be the
    reason the assertion holds (that was the old, accidental pass).
    """
    from scholar_harness.doctor import run_doctor

    monkeypatch.setattr(doctor_mod, "check_seam", lambda: _pass_seam())
    ws = _scaffold(tmp_path)
    # A corpus artifact the manifest does not declare -> the reconciliation
    # was performed and found the summary stale.
    (ws / "literature" / "raw_search.json").write_text(
        json.dumps([{"t": 1}]), encoding="utf-8"
    )

    report = run_doctor(ws)
    stats = next(c for c in report["checks"] if c["name"] == "project.json-stats")
    assert stats["status"] == "FAIL"
    assert "declared=0" in stats["detail"] and "actual=1" in stats["detail"]

    reconciliation = report["reconciliation"]
    assert reconciliation["performed"] is True
    assert reconciliation["reconciled"] is False
    assert reconciliation["status"] == "STALE"
    assert report["overall"] == "FAIL"


def test_layout_json_output_reports_a_verified_reconciliation(tmp_path, monkeypatch):
    """B-F9: a genuinely reconciled workspace reports PASS (the positive path)."""
    from scholar_harness.doctor import run_doctor

    monkeypatch.setattr(doctor_mod, "check_seam", lambda: _pass_seam())
    ws = _scaffold(tmp_path)
    (ws / "literature" / "raw_search.json").write_text(
        json.dumps([{"t": i} for i in range(5)]), encoding="utf-8"
    )
    manifest = ws / "project.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["stats"]["discovered_papers"] = 5
    manifest.write_text(json.dumps(data), encoding="utf-8")

    report = run_doctor(ws)
    stats = next(c for c in report["checks"] if c["name"] == "project.json-stats")
    assert stats["status"] == "PASS"
    assert report["reconciliation"]["performed"] is True
    assert report["reconciliation"]["reconciled"] is True
    assert report["reconciliation"]["status"] == "OK"
    assert report["overall"] == "PASS"


def test_overall_is_never_pass_when_the_reconciliation_was_not_performed(
    tmp_path, monkeypatch
):
    """D-3: the aggregate cannot report PASS while a reconciliation is missing.

    Only the reconciliation row may block a PASS aggregate -- an ordinary
    optional SKIP sub-check stays harmless.
    """
    from scholar_harness.doctor import run_doctor

    monkeypatch.setattr(doctor_mod, "check_seam", lambda: _pass_seam())
    monkeypatch.setattr(
        doctor_mod,
        "check_layout",
        lambda ws, state=None: [
            CheckResult(
                "layout", "canonical-files", Status.PASS, "All canonical contract files present"
            ),
            CheckResult(
                "layout", "project.json-stats", Status.SKIP, "NOT RECONCILED - nothing was counted"
            ),
        ],
    )
    report = run_doctor(tmp_path)
    assert report["overall"] != "PASS"
    assert report["reconciliation"]["performed"] is False


def test_declared_pdf_counter_is_compared_without_a_pdf_directory(tmp_path):
    """B-F6: a declared PDF counter is compared even without ``pdfs/``."""
    ws = _scaffold(tmp_path)
    manifest = ws / "project.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["stats"]["downloaded_pdfs"] = 5
    manifest.write_text(json.dumps(data), encoding="utf-8")
    # No PDF was ever downloaded: the directory is absent entirely.
    shutil.rmtree(ws / "pdfs", ignore_errors=True)
    assert not (ws / "pdfs").exists()

    stats = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats.status is Status.FAIL
    assert "downloaded_pdfs declared=5 actual=0" in stats.detail


def test_missing_manifest_still_reports_a_non_pass_reconciliation_row(tmp_path):
    """B-F7: the row exists even when ``project.json`` is missing."""
    ws = _scaffold(tmp_path)
    (ws / "project.json").unlink()
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status is not Status.PASS
    assert "no reconciliation was performed" in stats.detail


# ---------------------------------------------------------------------------
# --json: valid, machine-readable, secret-free
# ---------------------------------------------------------------------------


def test_json_output_valid_and_masked(tmp_path):
    secret = "sk-super-secret-doctor-test"
    mailto = "doctor-secret@example.com"
    env = tmp_path / ".env"
    env.write_text(
        f"SCHOLAR_MAILTO={mailto}\nOPENAI_API_KEY={secret}\n", encoding="utf-8"
    )

    result = runner.invoke(
        app, ["doctor", "--workspace", str(tmp_path), "--env-file", str(env), "--json"]
    )
    assert result.exit_code == 0, result.stdout

    payload = json.loads(result.stdout)
    assert "checks" in payload and "overall" in payload
    assert all(
        {"group", "name", "status", "detail"} <= set(c) for c in payload["checks"]
    )

    # mask proof: no env values anywhere, present keys masked as ***
    text = result.stdout
    assert secret not in text
    assert mailto not in text
    keys = [c for c in payload["checks"] if c["group"] == "keys"]
    mailto_check = next(c for c in keys if c["name"] == "SCHOLAR_MAILTO")
    assert mailto_check["status"] == "PASS"
    assert mailto_check["detail"] == "***"


def test_doctor_default_env_file_from_workspace(tmp_path):
    ws = _scaffold(tmp_path)
    (ws / ".env").write_text("SCHOLAR_MAILTO=a@b.c\n", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--workspace", str(ws), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    keys = [c for c in payload["checks"] if c["group"] == "keys"]
    assert any(c["name"] == "SCHOLAR_MAILTO" and c["status"] == "PASS" for c in keys)
    assert "a@b.c" not in result.stdout


# ---------------------------------------------------------------------------
# seam
# ---------------------------------------------------------------------------


def test_seam_entrypoints_and_python_version():
    results = check_seam()
    by_name = {r.name: r.status for r in results}
    assert by_name["cli-import"] == Status.PASS
    assert by_name["python-version"] == Status.PASS
    # scholar-agent is present in the dev environment's console_scripts
    assert by_name["entrypoint-scholar-agent"] == Status.PASS
    # The nexus-scholar metapackage entrypoint is wheel-provided: PASS inside
    # the installed wheel, WARN in a repo/dev checkout — never FAIL (clamp:
    # a healthy dev workspace must not report overall FAIL on its seam).
    assert by_name["entrypoint-nexus-scholar"] in (Status.PASS, Status.WARN)
    version = next(r for r in results if r.name == "python-version")
    assert version.detail.startswith("Python ")


# ---------------------------------------------------------------------------
# --exit-code: opt-in; only FAIL trips it
# ---------------------------------------------------------------------------


def test_exit_code_flag_exits_1_on_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor_mod,
        "check_kits",
        lambda importable_map=None: [
            CheckResult("kits", "scholar-rag-kit", Status.FAIL, "import FAILED")
        ],
    )
    result = runner.invoke(app, ["doctor", "--workspace", str(tmp_path), "--exit-code"])
    assert result.exit_code == 1


def test_advisory_default_exits_0_despite_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor_mod,
        "check_kits",
        lambda importable_map=None: [
            CheckResult("kits", "scholar-rag-kit", Status.FAIL, "import FAILED")
        ],
    )
    result = runner.invoke(app, ["doctor", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "FAIL" in result.stdout


def test_exit_code_not_tripped_by_warn(tmp_path, monkeypatch):
    """Wheel-style scenario: missing model keys WARN but never trip --exit-code."""
    monkeypatch.setattr(
        doctor_mod,
        "check_keys",
        lambda env_file=None: [
            CheckResult("keys", "OPENAI_API_KEY", Status.WARN, "Missing (optional)")
        ],
    )
    monkeypatch.setattr(doctor_mod, "check_seam", lambda: _pass_seam())
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(app, ["doctor", "--workspace", str(ws), "--exit-code"])
    assert result.exit_code == 0
    assert "WARN" in result.stdout
