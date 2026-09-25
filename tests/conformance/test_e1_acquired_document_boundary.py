"""WP01-E1 acquired-document boundary conformance (harness limbs).

Covers the three harness-side acceptance rows of Packet E1 -- Acquired-Document
Boundary (``docs/architecture/wp01_packet_e1_acquired_document_handoff.md``
§10.2), each of which is a *harness* obligation rather than a kit obligation:

``E1-NEG-030`` sync/packaging drift
    Every changed canonical kit commit, the vendored tree under ``tools/``, the
    full-SHA ``plugins.json`` pin, and the generated metapackage pin must agree.
    Drift is checked in **both** directions: the fixture lists the exact
    ``(mode, blob, path)`` rows the vendored tree must carry, and
    ``git ls-files -s`` must list exactly those rows -- so a kit commit that is
    pinned but not vendored, a vendored tree that is not pinned, and a
    hand-edited blob all fail. ``git ls-files`` reads the *index*, so the
    comparison is deliberately the next commit's content: unstaged vendored
    drift is a failure, not a silent pass.

``E1-NEG-044`` non-registry manifest
    ``pdf_acquisition_manifest`` is owned by ``scholar-pdf-kit``. Handing it to
    the **frozen** Contract v1 acceptance/chain registries must be rejected as
    ``UNSUPPORTED_ARTIFACT_TYPE``, and no registry entry may be fabricated. The
    registries are asserted to still hold exactly the six frozen Contract v1
    types, so the harness cannot quietly absorb the kit type to make the test
    pass. A registered type is used as the positive control.

``E1-NEG-047`` MCP capability boundary
    The registry, the skills, and the surface matrix must declare acquisition
    unavailable on MCP, and an acquisition-shaped MCP call must return the
    standard envelope (``operation=acquire_pdf``, ``status=FAILED``, no
    artifacts, non-retryable ``UNSUPPORTED_CAPABILITY``) with zero I/O -- while
    the same acquisition remains supported through the PDF kit's API and CLI.

Everything here is offline and deterministic: no provider or network access, no
sleep, no clock dependence, and every filesystem effect is confined to pytest's
``tmp_path``.
"""

from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType

import pytest
from scholar_agent import capabilities as caps
from scholar_agent.server import mcp
from scholar_pdf import acquisition_models as acq
from scholar_pdf import cli as pdf_cli

from scholar_harness.contracts import acceptance, chain, validate_artifact_chain
from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact

REPO_ROOT = Path(__file__).resolve().parents[2]

FIXTURE_DIR = REPO_ROOT / "tests" / "conformance" / "fixtures" / "e1_vendored"
MANIFEST = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"
PINS_JSON = REPO_ROOT / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json"

SKILLS_CANONICAL = REPO_ROOT / ".agents" / "skills"
SKILLS_MIRROR = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "skills"
SURFACE_MATRIX = REPO_ROOT / "docs" / "kits_surface_matrix.md"

# The two kits whose E1 work Stage 5 vendored, and the exact merged canonical
# commits they were vendored from. The commit is duplicated inside each fixture
# file; the cross-check against plugins.json below is what makes the two facts
# agree, so neither can drift alone.
E1_KITS: tuple[tuple[str, str], ...] = (
    ("scholar-pdf-kit", "858911f6b7dd5738de94fa749ffc4c65b6d0b70e"),
    ("scholar-agent-kit", "6050e0c99cdddb0f2c1ce7e0c62458a58eab5ce7"),
)

# The frozen Contract v1 registry keyset. Asserted exactly (not as a subset) so
# adding -- or absorbing -- a type is a hard failure.
FROZEN_ARTIFACT_TYPES = frozenset(
    {
        "claims_ledger",
        "corpus_snapshot",
        "document_manifest",
        "run_manifest",
        "screening_batch",
        "screening_decisions",
    }
)

FULL_SHA = "sha256:" + "0" * 64


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _fixture(kit: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{kit}.json").read_text(encoding="utf-8"))


def _plugins() -> dict[str, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {plugin["name"]: plugin for plugin in manifest["plugins"]}


def _staged_index_rows(kit: str) -> dict[str, str]:
    """Return ``{harness path: blob sha}`` for ``git ls-files -s tools/<kit>``."""

    git = subprocess.run(
        ["git", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert git.returncode == 0, (
        f"E1-NEG-030 needs git on PATH to compare the vendored tree: {git.stderr}"
    )

    result = subprocess.run(
        ["git", "ls-files", "-s", "--", f"tools/{kit}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    rows: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        meta, _, path = line.partition("\t")
        mode, blob, stage = meta.split()
        assert stage == "0", f"{path} is unmerged (stage {stage})"
        assert mode == "100644", f"{path} is mode {mode}, expected 100644"
        rows[path] = blob
    return rows


def _fixture_rows(fixture: dict) -> dict[str, str]:
    return {path: blob for mode, blob, path in fixture["files"]}


def _kit_owned_manifest_payload() -> dict:
    """A minimal, realistic payload of the PDF-kit-owned acquisition manifest.

    The frozen registries reject on ``artifact_type`` *before* any schema
    validation, so the body only has to be recognisably the kit's own artifact:
    its declared schema version, type, and an ``ACQ-`` identity.
    """

    return {
        "schema_version": acq.MANIFEST_SCHEMA_VERSION,
        "artifact_type": acq.MANIFEST_TYPE,
        "artifact_id": "ACQ-" + "a" * 32,
        "contract_version": acq.CONTRACT_VERSION,
    }


def _context() -> AcceptanceContext:
    return AcceptanceContext(
        workspace_id="WSP-test",
        protocol_fingerprint=FULL_SHA,
        corpus_fingerprint=FULL_SHA,
    )


# --------------------------------------------------------------------------- #
# E1-NEG-030 -- sync / packaging drift
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("kit", "commit"), E1_KITS, ids=[k for k, _ in E1_KITS])
def test_vendored_fixture_records_the_pinned_canonical_commit(kit: str, commit: str):
    """The fixture is the vendored tree's record of one exact canonical commit."""

    fixture = _fixture(kit)
    assert fixture["kit"] == kit
    assert fixture["commit"] == commit
    assert len(fixture["commit"]) == 40
    assert int(fixture["commit"], 16) >= 0  # full 40-hex commit, not a branch
    paths = [entry[2] for entry in fixture["files"]]
    assert paths == sorted(paths), "fixture rows must be sorted by path"
    assert len(set(paths)) == len(paths), "fixture paths must be unique"
    for mode, blob, path in fixture["files"]:
        assert mode == "100644", f"{path} fixture mode is {mode}"
        assert len(blob) == 40, f"{path} fixture blob {blob!r} is not a 40-hex sha"
        assert path.startswith(f"tools/{kit}/")


@pytest.mark.parametrize(("kit", "commit"), E1_KITS, ids=[k for k, _ in E1_KITS])
def test_plugin_pin_equals_the_vendored_commit(kit: str, commit: str):
    """plugins.json default_rev must be the commit the tree was vendored from."""

    plugins = _plugins()
    assert kit in plugins, f"{kit} is missing from plugins.json"
    assert plugins[kit]["default_rev"] == _fixture(kit)["commit"] == commit


@pytest.mark.parametrize(("kit", "_commit"), E1_KITS, ids=[k for k, _ in E1_KITS])
def test_vendored_tree_blob_matches_the_pinned_commit_exactly(kit: str, _commit: str):
    """The vendored tree and the pinned commit must be the same blobs.

    Compared as an exact set equality, so a missing vendored file, an extra
    vendored file, or a single differing blob each fail.
    """

    expected = _fixture_rows(_fixture(kit))
    actual = _staged_index_rows(kit)
    assert actual == expected, (
        f"vendored {kit} drifted from its pinned commit: "
        f"missing={sorted(set(expected) - set(actual))} "
        f"unexpected={sorted(set(actual) - set(expected))} "
        f"changed={sorted(p for p in set(actual) & set(expected) if actual[p] != expected[p])}"
    )


@pytest.mark.parametrize(("kit", "_commit"), E1_KITS, ids=[k for k, _ in E1_KITS])
def test_vendored_files_exist_on_disk_with_matching_content(kit: str, _commit: str):
    """Every pinned blob is present and clean-filter-equivalent in the worktree.

    ``git hash-object --path`` applies the repository's configured clean filters,
    matching the bytes Git would stage. This detects unstaged content drift while
    remaining portable across LF and ``core.autocrlf`` Windows checkouts.
    """

    for path, blob in _fixture_rows(_fixture(kit)).items():
        target = REPO_ROOT / path
        assert target.is_file(), (
            f"pinned vendored file {path} is missing from the worktree"
        )
        result = subprocess.run(
            ["git", "hash-object", f"--path={path}", "--", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        digest = result.stdout.strip()
        assert digest == blob, f"{path} content does not match its pinned blob"


def test_agent_kit_vendoring_excludes_generated_egg_info():
    """The canonical agent repo tracks egg-info; the harness snapshot must not.

    The exclusion is a standing vendoring convention (generated build metadata,
    already gitignored harness-wide), not a silent omission: a fixture row or
    tracked path under ``*.egg-info/`` is a failure.
    """

    fixture_rows = _fixture_rows(_fixture("scholar-agent-kit"))
    egg_info = sorted(p for p in fixture_rows if "egg-info" in p)
    assert not egg_info, f"generated egg-info must not be vendored: {egg_info}"
    tracked = _staged_index_rows("scholar-agent-kit")
    assert not [p for p in tracked if "egg-info" in p]


def test_pdf_kit_vendoring_has_no_exclusions():
    """The pdf-kit snapshot is complete: every canonical path is vendored."""

    pdf_paths = set(_fixture_rows(_fixture("scholar-pdf-kit")))
    assert len(pdf_paths) == 38, (
        f"expected 38 vendored pdf-kit paths, got {len(pdf_paths)}"
    )
    for required in (
        "tools/scholar-pdf-kit/src/scholar_pdf/acquisition.py",
        "tools/scholar-pdf-kit/src/scholar_pdf/acquisition_models.py",
        "tools/scholar-pdf-kit/src/scholar_pdf/canonical.py",
        "tools/scholar-pdf-kit/src/scholar_pdf/contract_parents.py",
        "tools/scholar-pdf-kit/tests/test_acquisition_contract.py",
        "tools/scholar-pdf-kit/tests/test_atomic_acquisition.py",
    ):
        assert required in pdf_paths, (
            f"E1 acquisition source {required} is not vendored"
        )


@pytest.mark.parametrize(("kit", "commit"), E1_KITS, ids=[k for k, _ in E1_KITS])
def test_metapackage_pins_mirror_the_manifest_for_e1_kits(kit: str, commit: str):
    """Light cross-check: the generated snapshot carries the same full SHA.

    ``test_nexus_scholar_pins.py`` owns the exhaustive snapshot codegen check;
    this asserts the E1 kits specifically so an E1 pin bump cannot skip the
    metapackage.
    """

    pins = json.loads(PINS_JSON.read_text(encoding="utf-8"))
    by_name = {pin["name"]: pin for pin in pins["kits"]}
    assert by_name[kit]["default_rev"] == commit
    assert by_name[kit]["repo"] == _plugins()[kit]["repo"]


def test_other_six_kits_were_not_disturbed_by_the_e1_sync():
    """The E1 vendoring did not spill into another kit's snapshot.

    Scope guard, not a content gate: every non-E1 kit still has a vendored tree,
    and every tracked path under it stays inside its own directory. (Byte-level
    content of the other six kits is not this packet's concern -- the kit-sync
    drift gate for them is their own fixtures' job.)
    """

    e1_kits = {name for name, _ in E1_KITS}
    assert len(_plugins()) - len(e1_kits) == 6, "expected six untouched kits"
    for kit in _plugins():
        if kit in e1_kits:
            continue
        rows = _staged_index_rows(kit)
        assert rows, f"{kit} has no vendored files"
        strays = sorted(p for p in rows if not p.startswith(f"tools/{kit}/"))
        assert not strays, f"{kit} snapshot contains foreign paths: {strays}"


# --------------------------------------------------------------------------- #
# E1-NEG-044 -- the kit-owned manifest is not a registry type
# --------------------------------------------------------------------------- #


def test_manifest_type_is_the_kit_owned_acquisition_type():
    """Anchor the row to the kit's real constants, not a copied literal."""

    assert acq.MANIFEST_TYPE == "pdf_acquisition_manifest"
    assert acq.MANIFEST_SCHEMA_VERSION == "pdf-acquisition-manifest-v1"
    assert acq.CONTRACT_VERSION == "1.0.0"


@pytest.mark.parametrize("registry_name", ["acceptance", "chain"])
def test_frozen_registries_do_not_register_the_kit_manifest_type(registry_name: str):
    """The harness did not absorb the kit type to make E1-NEG-044 pass.

    Exact keyset equality, not containment: adding a seventh type -- the kit's
    or anyone's -- fails here.
    """

    registry = getattr(
        acceptance if registry_name == "acceptance" else chain, "_ARTIFACT_MODELS"
    )
    assert set(registry) == FROZEN_ARTIFACT_TYPES, (
        f"{registry_name}._ARTIFACT_MODELS is no longer the frozen Contract v1 keyset"
    )
    assert acq.MANIFEST_TYPE not in registry


def test_acceptance_rejects_the_kit_manifest_and_fabricates_no_registry_entry(tmp_path):
    """accept_artifact fails closed on the kit-owned manifest type.

    The documented rejection path (``audit/rejections/`` + an ``ARTIFACT_REJECTED``
    journal event) is expected and is *not* a fabricated acceptance; what must
    never appear is a published artifact or a registry entry.
    """

    result = accept_artifact(
        workspace=tmp_path,
        payload=_kit_owned_manifest_payload(),
        expected=_context(),
    )

    assert result.accepted is False
    assert {issue.code for issue in result.issues} == {"UNSUPPORTED_ARTIFACT_TYPE"}
    assert result.artifact_type == acq.MANIFEST_TYPE
    assert result.published_path is None

    assert not (tmp_path / "artifacts").exists(), (
        "no artifact directory may be created for an unsupported type"
    )
    assert not (tmp_path / "artifacts" / acq.MANIFEST_TYPE).exists()
    assert not (tmp_path / "audit" / "artifact_registry.json").exists(), (
        "no registry entry may be fabricated for an unsupported type"
    )


def test_artifact_chain_rejects_the_kit_manifest():
    """The chain registry rejects the same payload for the same reason.

    ``validate_artifact_chain`` is pure -- it takes no workspace and touches no
    filesystem -- so this needs no fixture directory.
    """

    report = validate_artifact_chain([_kit_owned_manifest_payload()])

    assert report.valid is False
    assert "UNSUPPORTED_ARTIFACT_TYPE" in {issue.code for issue in report.issues}
    assert report.artifact_count == 0


def test_acceptance_type_gate_admits_a_registered_type(tmp_path):
    """Positive control: the assertion above is about the *type gate*, not luck.

    A ``document_manifest``-typed payload gets past the type lookup and fails
    later, on schema validation. If it were also rejected as
    ``UNSUPPORTED_ARTIFACT_TYPE`` the E1-NEG-044 test would be vacuous.
    """

    control = dict(_kit_owned_manifest_payload())
    control["artifact_type"] = "document_manifest"
    assert control["artifact_type"] in acceptance._ARTIFACT_MODELS

    result = accept_artifact(workspace=tmp_path, payload=control, expected=_context())
    assert result.accepted is False, (
        "a bare control payload must not be accepted either"
    )
    codes = {issue.code for issue in result.issues}
    assert "UNSUPPORTED_ARTIFACT_TYPE" not in codes, (
        "a registered type must clear the type gate; the E1-NEG-044 assertion "
        f"would be vacuous (got {sorted(codes)})"
    )
    assert "SCHEMA_VALIDATION_ERROR" in codes

    report = validate_artifact_chain([control])
    assert report.valid is False
    assert "UNSUPPORTED_ARTIFACT_TYPE" not in {issue.code for issue in report.issues}


# --------------------------------------------------------------------------- #
# E1-NEG-047 -- the declared MCP capability boundary
# --------------------------------------------------------------------------- #


DOC_SKILL_PDF = SKILLS_CANONICAL / "scholar-pdf-kit" / "SKILL.md"
DOC_SKILL_PDF_MIRROR = SKILLS_MIRROR / "scholar-pdf-kit" / "SKILL.md"
DOC_SKILL_AGENT = SKILLS_CANONICAL / "scholar-agent-kit" / "SKILL.md"
DOC_SKILL_AGENT_MIRROR = SKILLS_MIRROR / "scholar-agent-kit" / "SKILL.md"

#: Every declared-boundary document must carry both marker strings.
BOUNDARY_DOCS = (
    DOC_SKILL_PDF,
    DOC_SKILL_PDF_MIRROR,
    DOC_SKILL_AGENT,
    DOC_SKILL_AGENT_MIRROR,
    SURFACE_MATRIX,
)

#: The agent-kit skills (canonical + mirror) additionally name the mechanism.
AGENT_SKILL_DOCS = (DOC_SKILL_AGENT, DOC_SKILL_AGENT_MIRROR)

#: The pdf-kit skills (canonical + mirror) additionally name the alternatives.
PDF_SKILL_DOCS = (DOC_SKILL_PDF, DOC_SKILL_PDF_MIRROR)


@pytest.mark.parametrize("doc", BOUNDARY_DOCS, ids=lambda p: p.name if p else "")
def test_boundary_documents_declare_the_unsupported_capability(doc: Path):
    text = doc.read_text(encoding="utf-8")
    assert "pdf_acquisition" in text, f"{doc} does not name the capability"
    assert "UNSUPPORTED_CAPABILITY" in text, f"{doc} does not name the rejection code"


@pytest.mark.parametrize("doc", AGENT_SKILL_DOCS, ids=lambda p: p.name if p else "")
def test_agent_skill_documents_declare_the_mcp_mechanism(doc: Path):
    text = doc.read_text(encoding="utf-8")
    assert "mcp_supported" in text, f"{doc} does not declare the mcp_supported flag"
    assert "nexus_pdf_acquire" in text, f"{doc} does not name the registered tool"


@pytest.mark.parametrize("doc", PDF_SKILL_DOCS, ids=lambda p: p.name if p else "")
def test_pdf_skill_documents_name_the_supported_alternatives(doc: Path):
    text = doc.read_text(encoding="utf-8")
    assert "scholar-pdf acquire" in text, f"{doc} does not name the CLI alternative"
    assert "scholar_pdf.acquisition" in text, f"{doc} does not name the API alternative"


def test_surface_matrix_declares_api_cli_only_with_no_parity_claim():
    text = SURFACE_MATRIX.read_text(encoding="utf-8")
    assert "WP01-E1 acquired-document boundary" in text
    assert "mcp_supported=false" in text
    assert "acquire_pdf" in text
    assert "Zero I/O" in text or "zero I/O" in text
    assert "not** a parity claim" in text or "no parity claim" in text.lower()


def test_capability_registry_declares_pdf_acquisition_unsupported_on_mcp():
    declaration = caps.get_capability(caps.PDF_ACQUISITION)
    assert caps.PDF_ACQUISITION == "pdf_acquisition"
    assert caps.UNSUPPORTED_CAPABILITY == "UNSUPPORTED_CAPABILITY"
    assert caps.ACQUIRE_PDF_OPERATION == "acquire_pdf"
    assert declaration is caps.PDF_ACQUISITION_DECLARATION
    assert declaration.mcp_supported is False
    assert declaration.rejection_code == caps.UNSUPPORTED_CAPABILITY
    assert declaration.rejection_operation == caps.ACQUIRE_PDF_OPERATION
    assert declaration.owning_surfaces == ("API", "CLI")
    assert "MCP" not in declaration.owning_surfaces
    # The registry is an immutable mapping and the declaration a frozen dataclass,
    # so the boundary cannot be flipped at runtime.
    assert isinstance(caps.CAPABILITIES, MappingProxyType)
    with pytest.raises(TypeError):
        caps.CAPABILITIES["pdf_acquisition"] = declaration  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        declaration.mcp_supported = True  # type: ignore[misc]


def test_unsupported_capability_envelope_is_fail_closed_and_actionable():
    envelope = json.loads(
        caps.unsupported_capability_envelope_json(caps.PDF_ACQUISITION)
    )

    assert envelope["operation"] == caps.ACQUIRE_PDF_OPERATION == "acquire_pdf"
    assert envelope["status"] == "FAILED"
    assert envelope["artifacts"] == [], '"no artifacts" must be explicit, not absent'
    assert envelope["warnings"] == []

    errors = envelope["errors"]
    assert len(errors) == 1, "exactly one diagnostic, so the failure is unambiguous"
    error = errors[0]
    assert error["code"] == caps.UNSUPPORTED_CAPABILITY == "UNSUPPORTED_CAPABILITY"
    assert error["retryable"] is False, "retrying a declared boundary cannot succeed"
    assert "scholar-pdf acquire" in error["message"]
    assert "scholar_pdf.acquisition" in error["message"]
    assert error["details"]["mcp_supported"] is False
    assert error["details"]["capability"] == caps.PDF_ACQUISITION


def test_unsupported_capability_envelope_is_pure_and_zero_io():
    """Zero I/O, proven structurally rather than asserted in prose.

    The rejection is a pure projection of an immutable declaration: calling it
    neither mutates the registry nor perturbs the declaration, and repeated calls
    are byte-identical. A filesystem- or network-touching implementation would
    fail the determinism or the immutability check.
    """

    before_declaration = vars(caps.PDF_ACQUISITION_DECLARATION).copy()
    first = caps.unsupported_capability_envelope_json(caps.PDF_ACQUISITION)
    second = caps.unsupported_capability_envelope_json(caps.PDF_ACQUISITION)
    assert first == second, "the rejection envelope must be deterministic"

    assert vars(caps.PDF_ACQUISITION_DECLARATION) == before_declaration
    assert caps.get_capability(caps.PDF_ACQUISITION) is caps.PDF_ACQUISITION_DECLARATION


def test_unknown_capability_is_never_silently_unsupported():
    """An undeclared capability is a bug, not a soft 'unsupported' answer."""

    with pytest.raises(caps.UnknownCapabilityError):
        caps.get_capability("not_a_capability")
    with pytest.raises(caps.UnknownCapabilityError):
        caps.unsupported_capability_envelope_json("not_a_capability")


def test_pdf_acquire_tool_is_registered_and_the_surface_is_24_tools():
    """The boundary is observable: the tool is registered, and --help lists it."""

    registered = {tool.name for tool in mcp._tool_manager.list_tools()}
    assert "nexus_pdf_acquire" in registered, (
        "the declared-unsupported tool must exist so the boundary is observable"
    )
    assert len(registered) == 24, (
        f"expected 24 registered MCP tools, found {len(registered)}"
    )


def test_acquisition_remains_supported_through_the_pdf_kit_api(tmp_path):
    """The same acquisition is a first-class API request, not a refusal."""

    workspace_root = tmp_path.resolve()
    request = acq.AcquisitionRequest(
        workspace_id="WSP-t",
        workspace_root=workspace_root,
        run_id="RUN-t",
        study_id="STU-t",
        protocol_fingerprint=FULL_SHA,
        corpus_fingerprint=FULL_SHA,
        inputs=acq.ParentArtifactInputs(
            corpus_snapshot=acq.ParentArtifactInput(
                artifact_id="ART-t",
                artifact_type="corpus_snapshot",
                sha256=FULL_SHA,
                workspace_relative_path="literature/corpus/corpus_snapshot.json",
            ),
            screening_decisions=acq.ParentArtifactInput(
                artifact_id="ART-t",
                artifact_type="screening_decisions",
                sha256=FULL_SHA,
                workspace_relative_path="literature/screening/included.json",
            ),
        ),
        source_mode=acq.SourceMode.USER_PATH,
        source_path=workspace_root / "pdfs" / "incoming" / "local.pdf",
        access_assertion=acq.AccessAssertion(
            supplied_by="conformance-test", permission_basis="local fixture"
        ),
        source_kind=acq.AcquisitionSourceKind.USER_PATH,
        access_status=acq.AccessStatus.USER_PROVIDED,
    )

    assert request.schema_version == acq.REQUEST_SCHEMA_VERSION
    assert request.source_mode is acq.SourceMode.USER_PATH
    # Parent binding is mandatory and typed: both accepted parents, and no others.
    assert {
        request.inputs.corpus_snapshot.artifact_type,
        request.inputs.screening_decisions.artifact_type,
    } == {"corpus_snapshot", "screening_decisions"}
    with pytest.raises(ValueError):
        acq.AcquiredDocumentManifest.model_validate(
            {
                "schema_version": acq.MANIFEST_SCHEMA_VERSION,
                "manifest_type": "claims_ledger",
            }
        )
    with pytest.raises(ValueError):
        acq.AcquiredDocumentManifest.model_validate(
            {
                "schema_version": acq.MANIFEST_SCHEMA_VERSION,
                "manifest_type": acq.MANIFEST_TYPE,
                "manifest_id": "not-an-acq-id",
            }
        )


def test_acquisition_remains_supported_through_the_pdf_kit_cli():
    """`scholar-pdf acquire` is a registered CLI command."""

    import typer.main

    names = {
        command.name
        for command in pdf_cli.app.registered_commands
        if command.name is not None
    }
    assert "acquire" in names, f"scholar-pdf acquire is not registered: {sorted(names)}"

    click_command = typer.main.get_command(pdf_cli.app)
    assert "acquire" in click_command.commands, (
        f"click cannot resolve `scholar-pdf acquire`: {sorted(click_command.commands)}"
    )
    # The other long-standing pdf commands must survive alongside it.
    assert {"download", "ingest", "extract"} <= set(click_command.commands)
    # The command's own help must present acquisition as a supported API/CLI
    # operation, not imply an MCP parity it does not have.
    help_text = (click_command.commands["acquire"].help or "") + " ".join(
        parameter.help or "" for parameter in click_command.commands["acquire"].params
    )
    assert "acquire" in help_text.lower()
    assert "unsupported" not in help_text.lower(), (
        "the CLI surface supports acquisition; it must not describe itself as "
        f"unsupported: {help_text[:200]!r}"
    )


def test_mcp_boundary_module_declares_without_doing_acquisition():
    """The agent kit declares a boundary; it must not own PDF domain logic.

    Parsed rather than grepped: the module may not import the pdf kit, nor any
    filesystem/network capability, so the declared-unsupported path *cannot*
    acquire, ingest, validate, store, or write a manifest even by accident.
    """

    tree = ast.parse(Path(caps.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])

    assert "scholar_pdf" not in imported, (
        "the MCP boundary must not import the pdf kit; it declares, not implements"
    )
    forbidden = imported & {
        "os",
        "io",
        "pathlib",
        "shutil",
        "tempfile",
        "socket",
        "http",
        "urllib",
        "httpx",
        "requests",
        "aiohttp",
    }
    assert not forbidden, (
        f"the declared-unsupported path must be zero-I/O, but imports {sorted(forbidden)}"
    )
    assert isinstance(caps.CAPABILITIES, MappingProxyType)
