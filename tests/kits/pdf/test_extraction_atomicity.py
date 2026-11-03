"""WP01-E2 extraction atomicity and crash-recovery tests (offline, hermetic)."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from .test_extraction_contract import acquired_fixture, usable_engine

from scholar_pdf.acquisition import InMemoryAuditSink
from scholar_pdf.acquisition_models import OperationStatus
from scholar_pdf.extraction import (
    ExtractionCommitError,
    ExtractionFault,
)
from scholar_pdf.extraction_engines import EngineRegistry
from scholar_pdf.extraction_models import ExtractionEngine, ExtractionManifest
from scholar_pdf.frontmatter import parse_bound_frontmatter

_TESTS_DIR = str(Path(__file__).resolve().parent)

#: Terminal styling.  ``typer``/``rich`` colorize a help panel when stdout is a
#: terminal, and the styling is applied per span rather than per word, so a
#: hyphenated option name such as ``--audit-logger`` is not guaranteed to be
#: contiguous in the raw bytes: on the Linux runners it arrives split mid-name
#: across two ``1;36`` spans (bold cyan, which is typer's ``STYLE_OPTION``).
#: Windows piped output is plain, so this is only visible on Linux.  The
#: assertions below are about *content*, not about the absence of styling, so
#: they strip the escape sequences instead of forcing ``NO_COLOR`` (which would
#: change what the CLI is actually exercised as).  Stripping only SGR sequences
#: cannot alter the text, so this stays a content assertion.
_ANSI_SGR = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Return ``text`` without ANSI SGR escape sequences."""

    return _ANSI_SGR.sub("", text)


def _registry() -> EngineRegistry:
    return EngineRegistry({ExtractionEngine.PYMUPDF: usable_engine()})


# A child process that dies at the sidecar publication point.  It re-derives the
# workspace bindings from disk, so it exercises the restart path too.  Paths are
# passed as argv so no quoting survives into the child's source.
_CRASH_CHILD = """
import asyncio, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).parents[1]))
from kits.pdf.test_extraction_contract import acquired_fixture, usable_engine
from scholar_pdf.acquisition import InMemoryAuditSink
from scholar_pdf.extraction import ExtractionFault
from scholar_pdf.extraction_engines import EngineRegistry
from scholar_pdf.extraction_models import ExtractionEngine


def _die(point, identity):
    # Process death runs no cleanup handler.
    if point is ExtractionFault.SIDECAR_REPLACE:
        os._exit(9)


workspace = acquired_fixture(Path(sys.argv[2]))
service = workspace.service(
    EngineRegistry({ExtractionEngine.PYMUPDF: usable_engine()}),
    fault_injector=_die,
    audit_sink=InMemoryAuditSink(),
)
asyncio.run(service.extract([workspace.request()]))
print("child completed without crashing", file=sys.stderr)
"""


def test_e2_pos_002_exact_rerun_is_idempotent_and_never_re_extracts(
    tmp_path: Path,
) -> None:
    """E2-POS-002: the sidecar is the commit marker and a rerun reuses it.

    Also the E2-NEG-045 limb for the rerun itself: the identical rerun is the
    section 7.4 REUSED path, so the atomicity property -- one sidecar, no second
    run directory, no partially visible state -- holds for the replay as well as
    for the first run.
    """

    fixture = acquired_fixture(tmp_path)
    engine = usable_engine()
    service = fixture.service(EngineRegistry({ExtractionEngine.PYMUPDF: engine}))
    request = fixture.request()

    first = asyncio.run(service.extract([request]))
    second = asyncio.run(service.extract([request]))

    assert first.status is OperationStatus.SUCCESS
    assert second.status is OperationStatus.SUCCESS
    # Same sidecar, same checksum, no second run directory.
    assert first.data.manifest_reference == second.data.manifest_reference
    sidecars = list((fixture.root / "literature" / "extraction").rglob("EXT-*.json"))
    assert len(sidecars) == 1
    # The engine is only invoked on the first (real) run.
    assert len(engine.calls) == 1


@pytest.mark.slow
def test_e2_neg_029_crash_before_sidecar_leaves_no_authoritative_output(
    tmp_path: Path,
) -> None:
    """E2-NEG-029: a crash between promotion and sidecar write claims nothing.

    The promoted file is real content, but with no sidecar it is not
    authoritative.  Process death cannot run a cleanup handler, which is exactly
    the condition the commit-intent marker and the publication lock must
    survive -- so the crash runs in a real child process.
    """

    fixture = acquired_fixture(tmp_path)
    completed = subprocess.run(
        [sys.executable, "-c", _CRASH_CHILD, _TESTS_DIR, str(fixture.root)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,  # the child is *expected* to die
    )
    assert completed.returncode == 9, completed.stderr
    # The crash prevented the sidecar: nothing authoritative was published.
    assert not list((fixture.root / "literature" / "extraction").rglob("EXT-*.json"))


def test_e2_neg_029b_fault_injection_leaves_no_partial_sidecar(
    tmp_path: Path,
) -> None:
    """E2-NEG-029 plus the kit limb of E2-NEG-023: an abort publishes nothing.

    The injected fault raises, exactly as a real abort would; what matters is
    that the workspace is left with no half-published claim.  Limb A injects at
    ``ENGINE``, before any result exists.  Limb B injects at ``VALIDATION`` --
    after the engine returned usable text but before the commit -- which is the
    E2-NEG-023 window "between extraction success and candidate construction":
    the candidate is never built, so nothing is published and no candidate id
    exists anywhere for a caller to mistake for a decision.
    """

    fixture = acquired_fixture(tmp_path)

    for point in (ExtractionFault.ENGINE, ExtractionFault.VALIDATION):

        def die(
            injected: ExtractionFault, identity: str, _point: ExtractionFault = point
        ) -> None:
            if injected is _point:
                raise RuntimeError("injected extraction crash")

        service = fixture.service(
            _registry(), fault_injector=die, audit_sink=InMemoryAuditSink()
        )
        with pytest.raises(RuntimeError):
            asyncio.run(service.extract([fixture.request()]))

        assert not list(
            (fixture.root / "literature" / "extraction").rglob("EXT-*.json")
        )
        assert not list((fixture.root / "extracted").glob("*.tmp"))
        assert not list((fixture.root / "extracted").glob("*.md"))


def test_e2_neg_009_sidecar_verification_detects_field_mutation(
    tmp_path: Path,
) -> None:
    """E2-NEG-009: any sidecar field mutation fails verification."""

    fixture = acquired_fixture(tmp_path)
    service = fixture.service(_registry())
    outcome = asyncio.run(service.extract([fixture.request()]))
    reference = outcome.data.manifest_reference
    assert reference is not None
    sidecar = fixture.root / reference.workspace_relative_path
    manifest = ExtractionManifest.model_validate_json(
        sidecar.read_text(encoding="utf-8")
    )
    # A clean manifest verifies.
    service.verify_manifest(manifest, verify_bytes=True)

    # Mutating the committed_at provenance field must be detected.
    raw = json.loads(sidecar.read_text(encoding="utf-8"))
    raw["committed_at"] = "2026-01-02T00:00:00Z"
    sidecar.write_text(json.dumps(raw), encoding="utf-8")
    mutated = ExtractionManifest.model_validate_json(
        sidecar.read_text(encoding="utf-8")
    )
    with pytest.raises(ExtractionCommitError):
        service.verify_manifest(mutated, verify_bytes=True)


def test_e2_neg_034_audit_event_is_appended_once_per_commit(tmp_path: Path) -> None:
    """E2-NEG-034: the audit ledger is never double-logged by a replay."""
    fixture = acquired_fixture(tmp_path)
    audit = InMemoryAuditSink()
    service = fixture.service(_registry(), audit_sink=audit)
    request = fixture.request()
    asyncio.run(service.extract([request]))
    asyncio.run(service.extract([request]))  # replay must not double-log
    assert len(audit.events) == 1
    assert audit.events[0]["action"] == "PDF_TEXT_EXTRACTION"


def test_e2_neg_017_body_and_frontmatter_survive_a_restart(tmp_path: Path) -> None:
    """E2-NEG-017: a fresh service after restart re-verifies the committed file."""

    fixture = acquired_fixture(tmp_path)
    service = fixture.service(_registry())
    outcome = asyncio.run(service.extract([fixture.request()]))
    reference = outcome.data.manifest_reference
    assert reference is not None
    document_id = fixture.acquisition.records[0].document_id
    extracted = fixture.root / "extracted" / f"{document_id}.md"

    # A brand-new service instance (as after restart) re-verifies cleanly.
    fresh = fixture.service(_registry())
    manifest = ExtractionManifest.model_validate_json(
        (fixture.root / reference.workspace_relative_path).read_text(encoding="utf-8")
    )
    fresh.verify_manifest(manifest, verify_bytes=True)

    values, _body = parse_bound_frontmatter(extracted.read_bytes())
    assert values["document_id"] == document_id
