"""WP01-E2 extracted-text boundary conformance (harness limbs).

Packet E2 (``docs/architecture/wp01_packet_e2_extracted_text_handoff.md`` §10.1.7
/ §14.1) draws a hard line: the *behavioral* proofs of extraction live in the
canonical ``scholar-pdf-kit`` and ``scholar-agent-kit`` suites, and the harness
enforces only its own **cross-repository** obligations. A green run of this file
is therefore **not** evidence that extraction works -- the kit suites are. What
this file proves is that the harness side of the boundary is real:

``E2-NEG-037`` cross-repository drift
    The canonical pdf-kit/agent-kit commits, the vendored ``tools/<kit>/``
    snapshot record, the full-SHA ``plugins.json`` pin, and the generated
    metapackage pin must name the same commit, and the imported ``scholar_pdf`` /
    ``scholar_agent`` packages must resolve inside those vendored trees rather
    than from some other install.

``E2-NEG-021`` frozen-registry rejection
    ``pdf_extraction_manifest`` is owned by the PDF kit. Handing it to the
    **frozen** Contract v1 acceptance/chain registries must be rejected as
    ``UNSUPPORTED_ARTIFACT_TYPE`` with no fabricated registry entry, and the
    registries must still hold exactly the six frozen Contract v1 types -- so
    the harness cannot absorb the kit type to make the test pass. A registered
    type is used as the positive control (E1-NEG-044's shape).

``E2-POS-001`` / ``E2-POS-002`` registered publication
    A real ``scholar_pdf`` candidate -- built by the kit's own
    ``build_document_manifest_candidate`` over the frozen golden two-study chain
    -- is parsed through the frozen ``DocumentManifestArtifact`` and accepted by
    ``scholar_harness.extraction_adapter``, the single harness surface allowed to
    expose an accepted extraction reference. The accepted reference is checked
    for agreement with the candidate (``E2-NEG-036`` fingerprint agreement) and
    an exact replay must be idempotent with no duplicate registry entry, file, or
    audit event.

``E2-NEG-022`` / ``E2-NEG-035`` parent discipline
    A ``document_manifest`` may declare only the accepted ``screening_decisions``
    parent, that parent must be registered, and its registered ``sha256`` must
    equal the declared hash. An empty ``inputs`` list, a foreign/unregistered
    ``artifact_id``, and a divergent parent hash are each rejected with no
    publication and no silently substituted parent. A changed payload under an
    already registered ``ART-`` id is ``IDEMPOTENCY_CONFLICT`` (``E2-NEG-045``),
    never an overwrite.

``E2-NEG-019`` / ``E2-NEG-020`` declared MCP boundary
    The vendored agent kit declares ``pdf_extraction`` with
    ``mcp_supported=false``, owning surfaces ``("API", "CLI")``, and returns the
    standard operation envelope (``operation="extract_pdf"``,
    ``status="FAILED"``, empty artifacts/warnings, exactly one non-retryable
    ``UNSUPPORTED_CAPABILITY`` error naming the ``scholar-pdf extract-run`` CLI
    and the ``scholar_pdf.extraction.PDFExtractionService`` API) with zero I/O
    proven structurally. The E1 ``pdf_acquisition`` declaration is asserted
    un-broadened by E2.

Everything here is offline and deterministic: no network, no provider, no PDF
engine, no daemon, no sleep, no clock dependence in any assertion, and every
filesystem effect confined to pytest's ``tmp_path``. No PDF is actually
extracted here on purpose -- that is the canonical kit's job; the records built
here are deterministic fixtures with the kit's own committed field set.
"""

from __future__ import annotations

import ast
import copy
import json
import tomllib
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest
import scholar_pdf
import typer.main
from pydantic import ValidationError
from scholar_agent import capabilities as caps
from scholar_pdf import cli as pdf_cli
from scholar_pdf import contract_candidate, extraction_models
from scholar_pdf.acquisition_models import (
    AcceptedParentBinding,
    AccessAssertion,
    AccessStatus,
    AcquisitionAttempt,
    AcquisitionSourceKind,
    AcquisitionStatus,
    MethodProvenance,
    ProducerProvenance,
)
from scholar_pdf.extraction_models import (
    AttemptResult,
    DocumentContentStatus,
    ExtractedDocumentRecord,
    ExtractionAttempt,
    ExtractionEngine,
    ExtractionMethod,
    ExtractionOutputFormat,
    ExtractionStatus,
)

from scholar_harness.contracts import (
    acceptance,
    canonical_fingerprint,
    chain,
    validate_artifact_chain,
)
from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
from scholar_harness.contracts.models import DocumentManifestArtifact
from scholar_harness.extraction_adapter import (
    accept_extraction_candidate,
    parse_extraction_candidate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

FIXTURE_DIR = REPO_ROOT / "tests" / "conformance" / "fixtures" / "e1_vendored"
MANIFEST = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"
PINS_JSON = REPO_ROOT / "packaging" / "nexus-scholar" / "nexus_scholar_pins.json"
PDF_KIT_PYPROJECT = REPO_ROOT / "tools" / "scholar-pdf-kit" / "pyproject.toml"

# The frozen Contract v1 golden chain. Read-only: it is the generated
# ``tests/fixtures/contracts/v1/two_study_artifact_chain.json`` (the same fixture
# ``tests/test_contract_artifact_chain.py`` loads), never regenerated here.
GOLDEN_CHAIN = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "contracts"
    / "v1"
    / "two_study_artifact_chain.json"
)

#: The golden chain prefix a ``document_manifest`` may descend from, in
#: acceptance order. ``document_manifest`` requires a ``screening_decisions``
#: parent (frozen ``acceptance.py:40-45``), which itself requires
#: ``screening_batch``, which requires ``corpus_snapshot``.
GOLDEN_PREFIX = ("corpus_snapshot", "screening_batch", "screening_decisions")

# The two kits whose E2 work Stage 2 vendored, and the exact merged canonical
# commits this packet's harness limb is pinned to. These are the standing record
# for E2-NEG-037: plugins.json, the vendored fixture, and the generated
# metapackage pin must all name the same commit (E1's E1-NEG-030 blob-level
# index/worktree comparison owns the deeper tree check).
E2_KITS: tuple[tuple[str, str], ...] = (
    ("scholar-pdf-kit", "6ec6e3bb45612b40498772124de2ebc16717eb56"),
    ("scholar-agent-kit", "deebfad995ba88bbd748be9beddd1aa2b8a51264"),
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

#: The vendored canonical pdf-kit commit recorded as the candidate producer.
#: Not an invented revision: the same E2 pdf-kit pin asserted in E2-NEG-037.
PDF_KIT_COMMIT = "6ec6e3bb45612b40498772124de2ebc16717eb56"

#: The extraction run id used for the candidate envelope. Deterministic: the
#: candidate's ``artifact_id`` is a pure function of the payload, so nothing here
#: may read a clock (packet E2 §2.3 invariant 11).
EXTRACTION_RUN_ID = "RUN-extraction-two-study"

# --------------------------------------------------------------------------- #
# Deterministic fixture constants for the one committed extraction record.
#
# These are test *constants*, not measured facts: no PDF is extracted in this
# harness packet, because engine execution, content-status truthfulness, and
# sidecar commit are the canonical kit's behavioral proofs (§14.1). What the
# harness must prove is narrower and is proven below: that a record built with
# the kit's own committed field set yields a candidate the frozen model accepts
# and that the frozen acceptance gate publishes it once, bound to the accepted
# screening parent. Every hash below is a fixed literal so the candidate identity
# and payload hash are reproducible run to run.
# --------------------------------------------------------------------------- #

#: Opaque ``DOC-`` identity (the kit's ``_DOCUMENT_ID_RE`` shape: 32 lowercase
#: hex). E1 mints identity; E2 reuses it, so the harness never re-derives one.
DOCUMENT_ID = "DOC-" + "ab" * 16
#: Opaque ``ACQ-`` E1 manifest identity the record's lineage is bound to.
ACQUISITION_MANIFEST_ID = "ACQ-" + "cd" * 16
#: The study the document belongs to; a real study id from the golden corpus, so
#: the record is bound to the accepted corpus/screening lineage.
STUDY_ID = "STU-alpha"
#: Stable engine coordinates for the deterministic local engine. Explicit
#: constants (not ``importlib.metadata`` lookups) because the candidate must be
#: byte-reproducible; ``PYMUPDF`` -> ``DETERMINISTIC_RULE`` is the kit's own
#: ``ENGINE_METHODS`` mapping.
ENGINE = ExtractionEngine.PYMUPDF.value
ENGINE_VERSION = "1.2.3"
PAGE_COUNT = 3
CHARACTER_COUNT = 480
#: The recorded extracted body length and digests. No file is written; these are
#: the kit's recorded provenance fields, fixed for determinism.
EXTRACTED_SHA256 = "sha256:" + "3" * 64
EXTRACTED_FILE_SHA256 = "sha256:" + "4" * 64
SOURCE_SHA256 = "sha256:" + "2" * 64
SOURCE_BYTE_LENGTH = 4096
ACQUISITION_MANIFEST_SHA256 = "sha256:" + "1" * 64
SOURCE_RELATIVE_PATH = f"pdfs/acquired/{DOCUMENT_ID}.pdf"
EXTRACTED_RELATIVE_PATH = f"extracted/{DOCUMENT_ID}.md"
ACQUISITION_MANIFEST_PATH = (
    f"literature/acquisition/RUN-acquisition/{ACQUISITION_MANIFEST_ID}.json"
)
#: A 64-hex digest that no registered parent carries, for the "unregistered or
#: foreign parent" limbs.
FOREIGN_SHA256 = "sha256:" + "9" * 64
#: A well-formed ``ART-`` id that is not in the workspace registry.
FOREIGN_ARTIFACT_ID = "ART-foreign-unregistered-parent"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _fixture(kit: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{kit}.json").read_text(encoding="utf-8"))


def _plugins() -> dict[str, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {plugin["name"]: plugin for plugin in manifest["plugins"]}


def _pins() -> dict[str, dict]:
    pins = json.loads(PINS_JSON.read_text(encoding="utf-8"))
    return {pin["name"]: pin for pin in pins["kits"]}


def _vendored_pdf_kit_version() -> str:
    """The real version of the vendored canonical pdf kit.

    Read from ``tools/scholar-pdf-kit/pyproject.toml`` ``[project] version`` --
    the vendored snapshot's own declared version, not a hard-coded literal, so a
    version bump in the kit cannot leave the harness asserting a stale one.
    """

    declared = tomllib.loads(PDF_KIT_PYPROJECT.read_text(encoding="utf-8"))
    return str(declared["project"]["version"])


def _golden_artifacts() -> list[dict]:
    """A fresh, mutable copy of the frozen golden chain payloads."""

    payload = json.loads(GOLDEN_CHAIN.read_text(encoding="utf-8"))
    return copy.deepcopy(payload["artifacts"])


def _by_type(artifacts: list[dict], artifact_type: str) -> dict:
    return next(item for item in artifacts if item["artifact_type"] == artifact_type)


def _context_from(payload: dict) -> AcceptanceContext:
    """The trusted acceptance context, derived from an accepted artifact.

    Never invented: the workspace id and both fingerprints come from the payload
    that was accepted, which is exactly what ``accept_artifact``'s ``expected``
    argument is supposed to be (packet C reference, "Inputs and outputs").
    """

    return AcceptanceContext(
        workspace_id=payload["workspace_id"],
        protocol_fingerprint=payload["protocol_fingerprint"],
        corpus_fingerprint=payload["corpus_fingerprint"],
    )


def _codes(result) -> set[str]:
    return {issue.code for issue in result.issues}


def _registry(workspace: Path) -> dict:
    return json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )


def _journal_events(workspace: Path, action: str) -> list[dict]:
    """Every journal event with ``action``, read back from the append-only file."""

    journal = workspace / "audit" / "journal.jsonl"
    if not journal.is_file():
        return []
    events = [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [event for event in events if event.get("action") == action]


def _candidate_id(workspace: Path) -> str | None:
    """The registered ``document_manifest`` id in ``workspace``, if any."""

    registry_path = workspace / "audit" / "artifact_registry.json"
    if not registry_path.is_file():
        return None
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for artifact_id, entry in registry["artifacts"].items():
        if entry["artifact_type"] == extraction_models.CONTRACT_ARTIFACT_TYPE:
            return artifact_id
    return None


def scholar_agent_paths() -> list[str]:
    """The on-disk locations of the imported ``scholar_agent`` namespace package.

    ``scholar_agent`` is a namespace package -- it shares ``src/`` with the
    agent kit's other modules and therefore has no ``__file__`` -- so its search
    path is the only authority on where the vendored copy resolved.
    """

    import scholar_agent

    return list(scholar_agent.__path__)


def _extracted_record() -> ExtractedDocumentRecord:
    """One committed extraction record, field-for-field the kit's own shape.

    Mirrored from the canonical construction in
    ``tools/scholar-pdf-kit/src/scholar_pdf/extraction.py:2272-2306``
    (``PDFExtractionService._extracted_record``, the only place the vendored kit
    builds an :class:`ExtractedDocumentRecord`). The kit's own E2 suite does not
    construct a record directly -- it drives a real extraction and reads the
    committed record back out of the sidecar, then projects it into the candidate
    (``tools/scholar-pdf-kit/tests/test_extraction_contract.py:1573-1596`` for the
    sidecar records, ``:1611-1625`` for
    ``ArtifactRecordProjection.from_outcome`` + ``build_document_manifest_candidate``).

    Every value here is a fixed constant, so the candidate payload -- and
    therefore its derived ``artifact_id`` -- is byte-reproducible. No engine ran
    and no file was written: engine execution and sidecar commit are the kit's
    behavioral proof (§14.1), and this harness packet asserts only that a record
    of the committed field set yields a candidate the frozen gate accepts.
    """

    return ExtractedDocumentRecord(
        # E1 identity, reused byte-for-byte (packet E2 §2.3 invariants 1 and 3).
        document_id=DOCUMENT_ID,
        document_identity_algorithm_version="v1",
        study_id=STUDY_ID,
        acquisition_manifest_id=ACQUISITION_MANIFEST_ID,
        acquisition_manifest_sha256=ACQUISITION_MANIFEST_SHA256,
        acquisition_manifest_path=ACQUISITION_MANIFEST_PATH,
        source_sha256=SOURCE_SHA256,
        byte_length=SOURCE_BYTE_LENGTH,
        media_type=extraction_models.PDF_MEDIA_TYPE,
        source_workspace_relative_path=SOURCE_RELATIVE_PATH,
        # Truthful outcome: the deterministic local engine produced usable text.
        extraction_status=ExtractionStatus.EXTRACTED,
        content_status=DocumentContentStatus.VALID,
        extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
        requested_engine=ENGINE,
        requested_engine_version=ENGINE_VERSION,
        effective_engine=ENGINE,
        effective_engine_version=ENGINE_VERSION,
        fallback_chain=[],
        degradation_reasons=[],
        attempts=[
            ExtractionAttempt(
                ordinal=1,
                engine=ENGINE,
                engine_version=ENGINE_VERSION,
                output_format=ExtractionOutputFormat.MARKDOWN,
                result=AttemptResult.TEXT_EXTRACTED,
                effective=True,
                page_count=PAGE_COUNT,
                character_count=CHARACTER_COUNT,
                text_layer_present=True,
            )
        ],
        page_count=PAGE_COUNT,
        character_count=CHARACTER_COUNT,
        extracted_sha256=EXTRACTED_SHA256,
        extracted_file_sha256=EXTRACTED_FILE_SHA256,
        extracted_path=EXTRACTED_RELATIVE_PATH,
        extraction_output_format=ExtractionOutputFormat.MARKDOWN,
        # E1 access facts, preserved and never re-derived.
        access_status=AccessStatus.USER_PROVIDED,
        acquisition_method=MethodProvenance.HUMAN,
        acquisition_attempts=[
            AcquisitionAttempt(
                ordinal=1,
                source_kind=AcquisitionSourceKind.USER_PATH,
                requested_source=SOURCE_RELATIVE_PATH,
                result=AcquisitionStatus.ACQUIRED,
                resolved_source=SOURCE_RELATIVE_PATH,
            )
        ],
        access_assertion=AccessAssertion(
            supplied_by="conformance-test",
            permission_basis="local fixture supplied to the harness conformance test",
        ),
        selected_source=SOURCE_RELATIVE_PATH,
        selected_source_url=None,
        normalized_doi=None,
    )


def _producer() -> ProducerProvenance:
    """Real provenance: the vendored kit's declared version and E2 pinned commit."""

    return ProducerProvenance(
        package="scholar-pdf-kit",
        version=_vendored_pdf_kit_version(),
        commit=PDF_KIT_COMMIT,
    )


def _kit_owned_extraction_manifest_payload() -> dict:
    """A minimal, realistic payload of the PDF-kit-owned extraction sidecar.

    The frozen registries reject on ``artifact_type`` *before* any schema
    validation, so the body only has to be recognisably the kit's own artifact:
    its declared schema version, type, and an ``EXT-`` identity.
    """

    return {
        "schema_version": extraction_models.EXTRACTION_MANIFEST_SCHEMA_VERSION,
        "artifact_type": extraction_models.EXTRACTION_MANIFEST_TYPE,
        "artifact_id": "EXT-" + "e" * 32,
        "contract_version": extraction_models.CONTRACT_VERSION,
    }


@dataclass(frozen=True)
class AcceptedChain:
    """A ``tmp_path`` workspace holding the accepted golden prefix + candidate."""

    workspace: Path
    context: AcceptanceContext
    decisions_payload: dict
    decisions_result: Any
    parent: AcceptedParentBinding
    candidate: Any


@pytest.fixture
def accepted_chain(tmp_path: Path) -> AcceptedChain:
    """Accept ``corpus_snapshot -> screening_batch -> screening_decisions``.

    The three artifacts are the frozen golden chain's own payloads, accepted in
    lineage order through the frozen gate with an ``AcceptanceContext`` derived
    from the artifacts' own ``workspace_id``/fingerprints. The PDF-kit candidate
    is then built by the kit's own ``build_document_manifest_candidate`` over the
    *accepted* ``screening_decisions`` parent binding -- the kit never sees the
    harness registry, it only sees the accepted parent reference.
    """

    artifacts = _golden_artifacts()
    corpus = _by_type(artifacts, "corpus_snapshot")
    context = _context_from(corpus)

    results: dict[str, Any] = {}
    for artifact_type in GOLDEN_PREFIX:
        result = accept_artifact(
            tmp_path, _by_type(artifacts, artifact_type), expected=context
        )
        assert result.accepted is True, (artifact_type, _codes(result))
        results[artifact_type] = result

    decisions_payload = _by_type(artifacts, "screening_decisions")
    decisions_result = results["screening_decisions"]
    # The accepted parent binding carries the exact accepted reference: identity
    # and hash from the registry/canonical fingerprint, location from the
    # acceptance result, and the raw accepted payload for lineage re-checks.
    parent = AcceptedParentBinding(
        artifact_id=decisions_result.artifact_id,
        artifact_type=decisions_result.artifact_type,
        sha256=decisions_result.payload_hash,
        workspace_relative_path=decisions_result.published_path,
        workspace_id=decisions_payload["workspace_id"],
        run_id=decisions_payload["run_id"],
        protocol_fingerprint=decisions_payload["protocol_fingerprint"],
        corpus_fingerprint=decisions_payload["corpus_fingerprint"],
        payload=decisions_payload,
    )
    # The binding is self-consistent by construction (its validators recompute the
    # canonical fingerprint and cross-check the envelope), which is what makes the
    # candidate's single declared input trustworthy.
    assert parent.sha256 == canonical_fingerprint(decisions_payload)

    candidate = contract_candidate.build_document_manifest_candidate(
        workspace_id=decisions_payload["workspace_id"],
        run_id=EXTRACTION_RUN_ID,
        protocol_fingerprint=decisions_payload["protocol_fingerprint"],
        corpus_fingerprint=decisions_payload["corpus_fingerprint"],
        screening_parent=parent,
        producer=_producer(),
        records=[_extracted_record()],
        non_committed=[],
    )
    return AcceptedChain(
        workspace=tmp_path,
        context=context,
        decisions_payload=decisions_payload,
        decisions_result=decisions_result,
        parent=parent,
        candidate=candidate,
    )


def _mutated_candidate_payload(accepted: AcceptedChain) -> dict:
    """A deep copy of the kit-built candidate payload, safe to mutate."""

    return copy.deepcopy(accepted.candidate.payload)


# --------------------------------------------------------------------------- #
# Anchors -- the row is tied to the kits' real constants, not copied literals
# --------------------------------------------------------------------------- #


def test_e2_anchors_are_the_kits_own_constants() -> None:
    """The E2 rows name the kit's own identifiers, not strings copied here."""

    assert extraction_models.EXTRACTION_MANIFEST_TYPE == "pdf_extraction_manifest"
    assert extraction_models.EXTRACTION_MANIFEST_SCHEMA_VERSION == (
        "pdf-extraction-manifest-v1"
    )
    assert extraction_models.CONTRACT_ARTIFACT_TYPE == "document_manifest"
    assert extraction_models.CONTRACT_VERSION == "1.0.0"
    # The only Contract artifact type an extraction candidate may declare.
    assert extraction_models.SCREENING_DECISIONS_ARTIFACT_TYPE == "screening_decisions"
    assert extraction_models.CONTRACT_ACCEPTANCE_NOT_PERFORMED == "not_performed_by_kit"
    assert extraction_models.PDF_MEDIA_TYPE == "application/pdf"

    assert caps.PDF_EXTRACTION == "pdf_extraction"
    assert caps.EXTRACT_PDF_OPERATION == "extract_pdf"
    assert caps.UNSUPPORTED_CAPABILITY == "UNSUPPORTED_CAPABILITY"
    # The kit's Contract type is a *frozen* type, not a new one: E2 emits the
    # existing ``document_manifest`` and adds no registry entry (E2-NEG-021).
    assert extraction_models.CONTRACT_ARTIFACT_TYPE in FROZEN_ARTIFACT_TYPES
    assert extraction_models.SCREENING_DECISIONS_ARTIFACT_TYPE in FROZEN_ARTIFACT_TYPES


def test_e2_anchors_producer_provenance_is_the_real_vendored_kit() -> None:
    """The candidate producer is the vendored kit, not an invented identity."""

    producer = _producer()
    assert producer.package == "scholar-pdf-kit"
    assert producer.version == _vendored_pdf_kit_version()
    assert producer.commit == PDF_KIT_COMMIT
    assert len(producer.commit) == 40, "a full canonical commit, not a branch"
    assert PDF_KIT_COMMIT == dict(E2_KITS)["scholar-pdf-kit"], (
        "the producer commit and the E2-NEG-037 pin must be the same fact"
    )


# --------------------------------------------------------------------------- #
# E2-NEG-021 -- the kit-owned extraction sidecar is not a Contract registry type
# --------------------------------------------------------------------------- #


def test_e2_neg_021_extraction_manifest_type_is_the_kit_owned_type() -> None:
    """Anchor the row to the kit's real sidecar constants."""

    assert extraction_models.EXTRACTION_MANIFEST_TYPE == "pdf_extraction_manifest"
    assert extraction_models.EXTRACTION_MANIFEST_SCHEMA_VERSION == (
        "pdf-extraction-manifest-v1"
    )
    assert extraction_models.CONTRACT_VERSION == "1.0.0"
    assert extraction_models.SIDECAR_STORAGE_PREFIX == "literature/extraction"


#: The two frozen artifact-type registries, keyed by the name used in test ids.
#: Accessing the private ``_ARTIFACT_MODELS`` is deliberate: a harness that
#: quietly registered a seventh type would defeat the exact-keyset assertion.
_FROZEN_REGISTRIES = {
    "acceptance": acceptance._ARTIFACT_MODELS,
    "chain": chain._ARTIFACT_MODELS,
}


@pytest.mark.parametrize("registry_name", ["acceptance", "chain"])
def test_e2_neg_021_frozen_registries_do_not_register_the_extraction_manifest(
    registry_name: str,
) -> None:
    """The harness did not absorb the kit sidecar type to make E2-NEG-021 pass.

    Exact keyset equality, not containment: adding a seventh type -- the kit's
    or anyone's -- fails here, and so does dropping a frozen one.
    """

    registry = _FROZEN_REGISTRIES[registry_name]
    assert set(registry) == FROZEN_ARTIFACT_TYPES, (
        f"{registry_name}._ARTIFACT_MODELS is no longer the frozen Contract v1 keyset"
    )
    assert extraction_models.EXTRACTION_MANIFEST_TYPE not in registry
    assert extraction_models.CONTRACT_ACCEPTANCE_NOT_PERFORMED not in registry


def test_e2_neg_021_acceptance_rejects_the_sidecar_and_fabricates_no_registry_entry(
    tmp_path: Path,
) -> None:
    """``accept_artifact`` fails closed on the kit-owned sidecar type.

    The documented rejection path (``audit/rejections/`` + an ``ARTIFACT_REJECTED``
    journal event) is expected and is *not* a fabricated acceptance; what must
    never appear is a published artifact or a registry entry.
    """

    result = accept_artifact(
        workspace=tmp_path,
        payload=_kit_owned_extraction_manifest_payload(),
        expected=_context_from(_by_type(_golden_artifacts(), "corpus_snapshot")),
    )

    assert result.accepted is False
    assert _codes(result) == {"UNSUPPORTED_ARTIFACT_TYPE"}
    assert result.artifact_type == extraction_models.EXTRACTION_MANIFEST_TYPE
    assert result.published_path is None

    assert not (tmp_path / "artifacts").exists(), (
        "no artifact directory may be created for an unsupported type"
    )
    assert not (
        tmp_path / "artifacts" / extraction_models.EXTRACTION_MANIFEST_TYPE
    ).exists()
    assert not (tmp_path / "audit" / "artifact_registry.json").exists(), (
        "no registry entry may be fabricated for an unsupported type"
    )
    assert _journal_events(tmp_path, "ARTIFACT_ACCEPTED") == []


def test_e2_neg_021_artifact_chain_rejects_the_sidecar() -> None:
    """The chain registry rejects the same payload for the same reason.

    ``validate_artifact_chain`` is pure -- it takes no workspace and touches no
    filesystem -- so this needs no fixture directory.
    """

    report = validate_artifact_chain([_kit_owned_extraction_manifest_payload()])

    assert report.valid is False
    assert "UNSUPPORTED_ARTIFACT_TYPE" in {issue.code for issue in report.issues}
    assert report.artifact_count == 0


def test_e2_neg_021_acceptance_type_gate_admits_a_registered_type(
    tmp_path: Path,
) -> None:
    """Positive control: the assertion above is about the *type gate*, not luck.

    A ``document_manifest``-typed payload gets past the type lookup and fails
    later, on schema validation. If it were also rejected as
    ``UNSUPPORTED_ARTIFACT_TYPE`` the E2-NEG-021 test would be vacuous.
    """

    control = dict(_kit_owned_extraction_manifest_payload())
    control["artifact_type"] = extraction_models.CONTRACT_ARTIFACT_TYPE
    assert control["artifact_type"] in acceptance._ARTIFACT_MODELS

    result = accept_artifact(
        workspace=tmp_path,
        payload=control,
        expected=_context_from(_by_type(_golden_artifacts(), "corpus_snapshot")),
    )
    assert result.accepted is False, (
        "a bare control payload must not be accepted either"
    )
    codes = _codes(result)
    assert "UNSUPPORTED_ARTIFACT_TYPE" not in codes, (
        "a registered type must clear the type gate; the E2-NEG-021 assertion "
        f"would be vacuous (got {sorted(codes)})"
    )
    assert "SCHEMA_VALIDATION_ERROR" in codes

    report = validate_artifact_chain([control])
    assert report.valid is False
    assert "UNSUPPORTED_ARTIFACT_TYPE" not in {issue.code for issue in report.issues}


# --------------------------------------------------------------------------- #
# E2-POS-001 / E2-NEG-036 -- adapter acceptance and fingerprint agreement
# --------------------------------------------------------------------------- #


def test_e2_pos_001_kit_candidate_declares_only_the_accepted_screening_parent(
    accepted_chain: AcceptedChain,
) -> None:
    """The kit's candidate is a non-authoritative, single-parent payload.

    Mirrors the frozen golden shape (packet E2 §1.1 consequence 1): the
    acquisition manifest is *not* an ``inputs`` entry, and the candidate still
    says plainly that the kit did not accept it.
    """

    candidate = accepted_chain.candidate
    assert candidate.artifact_type == extraction_models.CONTRACT_ARTIFACT_TYPE
    assert (
        candidate.contract_acceptance
        == extraction_models.CONTRACT_ACCEPTANCE_NOT_PERFORMED
    )
    assert candidate.artifact_id == candidate.payload["artifact_id"]
    assert candidate.artifact_id.startswith("ART-")
    assert candidate.payload["producer"]["package"] == "scholar-pdf-kit"
    assert candidate.payload["inputs"] == [
        {
            "artifact_id": accepted_chain.parent.artifact_id,
            "sha256": accepted_chain.parent.sha256,
        }
    ]
    assert accepted_chain.parent.artifact_type == (
        extraction_models.SCREENING_DECISIONS_ARTIFACT_TYPE
    )
    # Truthful per-document state projected from the committed record.
    documents = candidate.payload["data"]["documents"]
    assert len(documents) == 1
    assert documents[0] == {
        "document_id": DOCUMENT_ID,
        "study_id": STUDY_ID,
        "source_hash": SOURCE_SHA256,
        "content_status": DocumentContentStatus.VALID.value,
        "extracted_path": EXTRACTED_RELATIVE_PATH,
        "extraction_method": ExtractionMethod.DETERMINISTIC_RULE.value,
    }


def test_e2_pos_001_adapter_accepts_the_candidate_and_publishes_it(
    accepted_chain: AcceptedChain,
) -> None:
    """E2-POS-001: the adapter alone turns the candidate into an accepted artifact.

    ``scholar_harness.extraction_adapter`` is the single harness surface allowed
    to expose an accepted extraction reference; this asserts that its result is
    the only place one appears, and that the accepted reference points at the
    canonical publication path plus a real audit event.
    """

    workspace = accepted_chain.workspace
    candidate = accepted_chain.candidate

    result = accept_extraction_candidate(
        workspace, candidate.payload, expected=accepted_chain.context
    )

    assert result.accepted is True, _codes(result)
    assert result.issues == []
    assert result.idempotent is False, "a first acceptance is not a replay"
    assert result.artifact_id == candidate.artifact_id
    assert result.artifact_type == extraction_models.CONTRACT_ARTIFACT_TYPE
    assert result.published_path == (
        f"artifacts/document_manifest/{candidate.artifact_id}.json"
    )
    assert result.event_id, "acceptance must append a canonical audit event"

    published = workspace / result.published_path
    assert published.is_file()
    events = [
        event
        for event in _journal_events(workspace, "ARTIFACT_ACCEPTED")
        if accepted_chain.parent.artifact_id in event.get("inputs", [])
    ]
    assert len(events) == 1
    assert events[0]["event_id"] == result.event_id
    assert events[0]["agent_or_tool"] == "scholar-harness-extraction-adapter"
    assert result.published_path in events[0]["outputs"]


def test_e2_neg_036_accepted_fingerprint_matches_the_candidate_exactly(
    accepted_chain: AcceptedChain,
) -> None:
    """E2-NEG-036: registry hash, candidate hash, and payload agree, exactly.

    The accepted artifact's canonical fingerprint must equal the kit's own
    ``payload_sha256`` and a freshly recomputed canonical fingerprint, and the
    workspace/protocol/corpus generation must equal the accepted parent's, or
    acceptance could have bound the manifest to a different generation.
    """

    workspace = accepted_chain.workspace
    candidate = accepted_chain.candidate
    result = accept_extraction_candidate(
        workspace, candidate.payload, expected=accepted_chain.context
    )
    assert result.accepted is True, _codes(result)

    entry = _registry(workspace)["artifacts"][candidate.artifact_id]
    assert entry["sha256"] == candidate.payload_sha256
    assert entry["sha256"] == canonical_fingerprint(candidate.payload)
    assert entry["sha256"] == result.payload_hash
    assert entry["artifact_type"] == extraction_models.CONTRACT_ARTIFACT_TYPE
    assert entry["path"] == result.published_path
    assert entry["run_id"] == EXTRACTION_RUN_ID

    # Parent lineage: the screening parent is the only declared input, and its
    # declared hash is the *registered* parent's hash -- the adapter never
    # substituted a different accepted artifact for the declared reference.
    assert candidate.payload["inputs"] == [
        {
            "artifact_id": accepted_chain.parent.artifact_id,
            "sha256": accepted_chain.parent.sha256,
        }
    ]
    registered_parent = _registry(workspace)["artifacts"][
        accepted_chain.parent.artifact_id
    ]
    assert registered_parent["sha256"] == accepted_chain.parent.sha256
    assert registered_parent["artifact_type"] == (
        extraction_models.SCREENING_DECISIONS_ARTIFACT_TYPE
    )

    # Generation agreement across manifest, parent, and trusted context.
    for field in ("workspace_id", "protocol_fingerprint", "corpus_fingerprint"):
        assert candidate.payload[field] == accepted_chain.parent.payload[field]
        assert candidate.payload[field] == getattr(accepted_chain.context, field)
    assert accepted_chain.context == _context_from(accepted_chain.decisions_payload)


def test_e2_pos_001_published_artifact_revalidates_through_the_frozen_model(
    accepted_chain: AcceptedChain,
) -> None:
    """What the gate wrote on disk is the frozen ``DocumentManifestArtifact``.

    The adapter passes the payload through ``accept_artifact``; the stored bytes
    must still satisfy the unmodified frozen model, with the same document
    record the kit projected.
    """

    workspace = accepted_chain.workspace
    result = accept_extraction_candidate(
        workspace, accepted_chain.candidate.payload, expected=accepted_chain.context
    )
    assert result.accepted is True, _codes(result)

    stored = json.loads((workspace / result.published_path).read_text(encoding="utf-8"))
    assert canonical_fingerprint(stored) == result.payload_hash

    artifact = DocumentManifestArtifact.model_validate(stored)
    assert artifact.artifact_type == extraction_models.CONTRACT_ARTIFACT_TYPE
    assert artifact.artifact_id == accepted_chain.candidate.artifact_id
    assert artifact.workspace_id == accepted_chain.context.workspace_id
    assert [document.document_id for document in artifact.data.documents] == [
        DOCUMENT_ID
    ]
    assert artifact.data.documents[0].extracted_path == EXTRACTED_RELATIVE_PATH
    assert [parent.artifact_id for parent in artifact.inputs] == [
        accepted_chain.parent.artifact_id
    ]


def test_e2_adapter_frozen_model_gate_rejects_a_non_conforming_candidate(
    accepted_chain: AcceptedChain,
) -> None:
    """The adapter parses through the frozen model *before* the acceptance gate.

    A payload the frozen model would reject must raise rather than come back as
    an ``AcceptanceResult``: a caller must never be handed an "accepted
    extraction" -- or a soft rejection code -- for a payload that is not a
    ``document_manifest`` at all.
    """

    workspace = accepted_chain.workspace
    sidecar = _kit_owned_extraction_manifest_payload()
    with pytest.raises(ValidationError):
        parse_extraction_candidate(sidecar)
    with pytest.raises(ValidationError):
        accept_extraction_candidate(workspace, sidecar, expected=accepted_chain.context)

    # A VALID record with no extracted_path is a frozen-model violation
    # (models.py:503-510) and must not survive the parse gate either.
    pathless = _mutated_candidate_payload(accepted_chain)
    del pathless["data"]["documents"][0]["extracted_path"]
    with pytest.raises(ValidationError):
        accept_extraction_candidate(
            workspace, pathless, expected=accepted_chain.context
        )

    # DocumentManifestData.documents has min_length=1: an empty set is a
    # frozen-model violation, never a lenient "nothing worked" encoding.
    empty = _mutated_candidate_payload(accepted_chain)
    empty["data"]["documents"] = []
    with pytest.raises(ValidationError):
        accept_extraction_candidate(workspace, empty, expected=accepted_chain.context)

    # Nothing was published and no registry entry was fabricated by any of them.
    assert _candidate_id(workspace) is None
    assert not (
        workspace / "artifacts" / extraction_models.CONTRACT_ARTIFACT_TYPE
    ).exists()


# --------------------------------------------------------------------------- #
# E2-POS-002 -- exact replay
# --------------------------------------------------------------------------- #


def test_e2_pos_002_exact_replay_is_idempotent_and_changes_nothing(
    accepted_chain: AcceptedChain,
) -> None:
    """E2-POS-002: the same payload again is a replay, not a second artifact.

    No duplicate registry entry, no rewritten file, and no second audit event --
    the same three no-duplication obligations the kit's own sidecar replay has.
    """

    workspace = accepted_chain.workspace
    candidate = accepted_chain.candidate
    first = accept_extraction_candidate(
        workspace, candidate.payload, expected=accepted_chain.context
    )
    assert first.accepted is True, _codes(first)
    published = workspace / first.published_path
    before_bytes = published.read_bytes()
    before_registry = _registry(workspace)
    before_events = len(_journal_events(workspace, "ARTIFACT_ACCEPTED"))

    replay = accept_extraction_candidate(
        workspace, candidate.payload, expected=accepted_chain.context
    )

    assert replay.accepted is True
    assert replay.idempotent is True
    assert replay.issues == []
    assert replay.artifact_id == first.artifact_id
    assert replay.published_path == first.published_path
    assert replay.payload_hash == first.payload_hash
    # An idempotent replay appends no event, so it carries no event id.
    assert replay.event_id is None

    assert _registry(workspace) == before_registry
    registry = _registry(workspace)
    assert [
        artifact_id
        for artifact_id, entry in registry["artifacts"].items()
        if entry["artifact_type"] == extraction_models.CONTRACT_ARTIFACT_TYPE
    ] == [candidate.artifact_id], "exactly one entry for the manifest"
    assert published.read_bytes() == before_bytes
    assert len(_journal_events(workspace, "ARTIFACT_ACCEPTED")) == before_events


# --------------------------------------------------------------------------- #
# E2-NEG-045 -- artifact idempotency is a conflict, never an overwrite
# --------------------------------------------------------------------------- #


def test_e2_neg_045_changed_payload_under_a_registered_id_never_overwrites(
    accepted_chain: AcceptedChain,
) -> None:
    """E2-NEG-045: a mutated payload under a registered ``ART-`` id conflicts.

    The artifact id is the kit's own deterministic identity, so a changed payload
    presented under the *same* id is precisely the case the frozen gate must
    refuse. Nothing on disk or in the registry may move.
    """

    workspace = accepted_chain.workspace
    candidate = accepted_chain.candidate
    first = accept_extraction_candidate(
        workspace, candidate.payload, expected=accepted_chain.context
    )
    assert first.accepted is True, _codes(first)
    published = workspace / first.published_path
    before_bytes = published.read_bytes()
    before_entry = _registry(workspace)["artifacts"][candidate.artifact_id]

    mutated = _mutated_candidate_payload(accepted_chain)
    assert mutated["artifact_id"] == candidate.artifact_id, (
        "the id is deliberately kept"
    )
    mutated["data"]["documents"][0]["study_id"] = "STU-beta"
    assert canonical_fingerprint(mutated) != candidate.payload_sha256

    conflict = accept_extraction_candidate(
        workspace, mutated, expected=accepted_chain.context
    )

    assert conflict.accepted is False
    assert _codes(conflict) == {"IDEMPOTENCY_CONFLICT"}
    assert conflict.artifact_id == candidate.artifact_id
    assert conflict.published_path is None
    # No overwrite: the accepted bytes and the registry entry are untouched.
    assert published.read_bytes() == before_bytes
    assert _registry(workspace)["artifacts"][candidate.artifact_id] == before_entry
    assert _registry(workspace)["artifacts"][candidate.artifact_id]["sha256"] == (
        candidate.payload_sha256
    )


# --------------------------------------------------------------------------- #
# E2-NEG-022 -- parent discipline
# --------------------------------------------------------------------------- #


def test_e2_neg_022_empty_inputs_is_rejected_and_publishes_nothing(
    accepted_chain: AcceptedChain,
) -> None:
    """A ``document_manifest`` with no declared parent cannot be published.

    ``inputs`` defaults to ``[]`` in the frozen envelope, so "no parent" is
    schema-legal and must be caught by the gate: ``document_manifest`` requires a
    ``screening_decisions`` parent (frozen ``acceptance.py:40-45``).
    """

    workspace = accepted_chain.workspace
    orphan = _mutated_candidate_payload(accepted_chain)
    orphan["inputs"] = []
    # The payload still satisfies the frozen model -- the gate is what refuses it.
    DocumentManifestArtifact.model_validate(orphan)

    result = accept_extraction_candidate(
        workspace, orphan, expected=accepted_chain.context
    )

    assert result.accepted is False
    assert _codes(result) == {"REQUIRED_PARENT_TYPE_MISSING"}
    assert result.published_path is None
    assert _candidate_id(workspace) is None
    assert not (
        workspace / "artifacts" / extraction_models.CONTRACT_ARTIFACT_TYPE
    ).exists()


def test_e2_neg_022_unregistered_parent_reference_is_rejected(
    accepted_chain: AcceptedChain,
) -> None:
    """A foreign/unregistered ``artifact_id`` in ``inputs`` is refused, not adopted.

    The accepted screening parent is present in the registry under its own id; a
    candidate pointing somewhere else names no accepted parent at all.
    """

    workspace = accepted_chain.workspace
    foreign = _mutated_candidate_payload(accepted_chain)
    foreign["inputs"] = [
        {
            "artifact_id": FOREIGN_ARTIFACT_ID,
            "sha256": accepted_chain.parent.sha256,
        }
    ]

    result = accept_extraction_candidate(
        workspace, foreign, expected=accepted_chain.context
    )

    assert result.accepted is False
    assert result.published_path is None
    assert "MISSING_PARENT_ARTIFACT" in _codes(result)
    # The required parent type is missing too: the only declared input is not
    # registered, so no accepted screening_decisions parent backs this manifest.
    assert "REQUIRED_PARENT_TYPE_MISSING" in _codes(result)
    assert _candidate_id(workspace) is None
    assert FOREIGN_ARTIFACT_ID not in _registry(workspace)["artifacts"]


# --------------------------------------------------------------------------- #
# E2-NEG-035 -- parent registration and hash discipline
# --------------------------------------------------------------------------- #


def test_e2_neg_035_declared_parent_hash_must_match_the_registered_entry(
    accepted_chain: AcceptedChain,
) -> None:
    """A parent id that is registered but with a different hash is rejected.

    This is the "silently replace the parent" failure mode: the gate must not
    accept the manifest against a *different* accepted artifact just because the
    id happens to resolve.
    """

    workspace = accepted_chain.workspace
    divergent = _mutated_candidate_payload(accepted_chain)
    divergent["inputs"] = [
        {
            "artifact_id": accepted_chain.parent.artifact_id,
            "sha256": FOREIGN_SHA256,
        }
    ]

    result = accept_extraction_candidate(
        workspace, divergent, expected=accepted_chain.context
    )

    assert result.accepted is False
    assert "PARENT_HASH_MISMATCH" in _codes(result)
    # The mismatched parent is not admitted to the registered-parent band, so the
    # required screening_decisions parent type is missing as well.
    assert "REQUIRED_PARENT_TYPE_MISSING" in _codes(result)
    assert "MISSING_PARENT_ARTIFACT" not in _codes(result)
    assert result.published_path is None

    # The registry is unchanged: no manifest entry, and the parent entry still
    # carries its own accepted hash.
    registry = _registry(workspace)
    assert _candidate_id(workspace) is None
    assert registry["artifacts"][accepted_chain.parent.artifact_id]["sha256"] == (
        accepted_chain.parent.sha256
    )
    assert len(registry["artifacts"]) == len(GOLDEN_PREFIX)


def test_e2_neg_035_parent_is_never_silently_replaced_with_a_registered_one(
    accepted_chain: AcceptedChain,
) -> None:
    """E2-NEG-035 second limb: the gate never swaps in a registered substitute.

    The workspace registry *does* hold the correct screening parent, and the
    candidate points at a different, unregistered id. Acceptance still fails:
    the adapter may not repair a lineage reference.
    """

    workspace = accepted_chain.workspace
    registered = _registry(workspace)["artifacts"]
    assert accepted_chain.parent.artifact_id in registered

    foreign = _mutated_candidate_payload(accepted_chain)
    foreign["inputs"] = [
        {"artifact_id": FOREIGN_ARTIFACT_ID, "sha256": accepted_chain.parent.sha256}
    ]

    result = accept_extraction_candidate(
        workspace, foreign, expected=accepted_chain.context
    )

    assert result.accepted is False
    assert "MISSING_PARENT_ARTIFACT" in _codes(result)
    assert _candidate_id(workspace) is None
    # The registry is byte-for-byte the accepted prefix: no fabricated entry, no
    # rewritten parent hash.
    assert set(registered) == set(_registry(workspace)["artifacts"])
    assert (
        _registry(workspace)["artifacts"][accepted_chain.parent.artifact_id]
        == registered[accepted_chain.parent.artifact_id]
    )


# --------------------------------------------------------------------------- #
# E2-NEG-037 -- cross-repository drift
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("kit", "commit"), E2_KITS, ids=[k for k, _ in E2_KITS])
def test_e2_neg_037_pins_and_vendored_records_agree_on_the_e2_commit(
    kit: str, commit: str
) -> None:
    """Canonical commit, vendored snapshot record, and both pins must be one fact.

    ``plugins.json`` ``default_rev``, the E1 vendored fixture's ``commit``, the
    generated metapackage pin, and this packet's standing record must all name
    the same full 40-hex commit. A kit commit that is pinned but not vendored, a
    vendored tree that is not pinned, or a pin that drifted from both fails here.
    (The blob-level index/worktree comparison is E1's E1-NEG-030 gate.)
    """

    assert len(commit) == 40
    assert int(commit, 16) >= 0, "a full commit sha, never a floating branch"

    plugins = _plugins()
    assert kit in plugins, f"{kit} is missing from plugins.json"
    assert plugins[kit]["default_rev"] == commit

    fixture = _fixture(kit)
    assert fixture["kit"] == kit
    assert fixture["commit"] == commit

    pin = _pins()[kit]
    assert pin["default_rev"] == commit
    assert pin["repo"] == plugins[kit]["repo"]


def test_e2_neg_037_imported_kits_resolve_under_the_vendored_snapshots() -> None:
    """The imported E2 surfaces come from ``tools/<kit>/src``, not another install.

    ``scholar_pdf`` is a regular package, so its ``__file__`` is authoritative;
    ``scholar_agent`` is a namespace package (it shares the ``src`` directory
    with its other modules), so ``__path__[0]`` is used instead.
    """

    pdf_file = Path(scholar_pdf.__file__).resolve()
    expected_pdf = (REPO_ROOT / "tools" / "scholar-pdf-kit" / "src").resolve()
    assert expected_pdf in pdf_file.parents, (
        f"scholar_pdf resolved to {pdf_file}, not the vendored pdf-kit snapshot"
    )

    agent_paths = [Path(entry).resolve() for entry in scholar_agent_paths()]
    expected_agent = (REPO_ROOT / "tools" / "scholar-agent-kit" / "src").resolve()
    assert any(expected_agent in entry.parents for entry in agent_paths), (
        f"scholar_agent resolved to {agent_paths}, not the vendored agent-kit snapshot"
    )
    # The agent kit that owns the E2 capability declaration is the one imported.
    # Compared as resolved Paths, never as string suffixes: Windows separators
    # would make a slash-joined suffix assertion silently pass for the wrong
    # reason (or fail on the right answer).
    assert Path(caps.__file__).resolve() == expected_agent / "scholar_agent" / (
        "capabilities.py"
    )


# --------------------------------------------------------------------------- #
# E2-NEG-019 / E2-NEG-020 -- the declared MCP extraction boundary
# --------------------------------------------------------------------------- #


def test_e2_neg_019_capability_registry_declares_pdf_extraction_unsupported_on_mcp() -> (
    None
):
    """The extraction boundary is declared, immutable, and owned by the PDF kit."""
    declaration = caps.get_capability(caps.PDF_EXTRACTION)
    assert declaration is caps.PDF_EXTRACTION_DECLARATION
    assert declaration.name == caps.PDF_EXTRACTION == "pdf_extraction"
    assert declaration.mcp_supported is False
    assert declaration.rejection_code == caps.UNSUPPORTED_CAPABILITY
    assert declaration.rejection_operation == caps.EXTRACT_PDF_OPERATION
    assert declaration.owning_surfaces == ("API", "CLI")
    assert "MCP" not in declaration.owning_surfaces
    assert declaration.owner == "nexus-scholar-org/scholar-pdf-kit"
    # The alternatives name the authoritative surfaces, not the legacy
    # raw-path conveniences.
    joined = " ".join(declaration.alternatives)
    assert "scholar-pdf extract-run" in joined
    assert "PDFExtractionService" in joined
    # The registry is an immutable mapping and the declaration a frozen dataclass,
    # so the boundary cannot be flipped at runtime.
    assert isinstance(caps.CAPABILITIES, MappingProxyType)
    with pytest.raises(TypeError):
        caps.CAPABILITIES["pdf_extraction"] = declaration  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        declaration.mcp_supported = True  # type: ignore[misc]


def test_e2_neg_019_extraction_rejection_envelope_is_fail_closed_and_actionable() -> (
    None
):
    """An extraction-shaped MCP request returns one non-retryable refusal.

    ``operation="extract_pdf"``, ``status="FAILED"``, no artifacts, no warnings,
    exactly one error, and a message that names both supported alternatives so a
    caller is redirected rather than merely refused.
    """

    envelope = json.loads(
        caps.unsupported_capability_envelope_json(caps.PDF_EXTRACTION)
    )

    assert envelope["operation"] == caps.EXTRACT_PDF_OPERATION == "extract_pdf"
    assert envelope["status"] == "FAILED"
    assert envelope["artifacts"] == [], '"no artifacts" must be explicit, not absent'
    assert envelope["warnings"] == []

    errors = envelope["errors"]
    assert len(errors) == 1, "exactly one diagnostic, so the failure is unambiguous"
    error = errors[0]
    assert error["code"] == caps.UNSUPPORTED_CAPABILITY == "UNSUPPORTED_CAPABILITY"
    assert error["retryable"] is False, "retrying a declared boundary cannot succeed"
    assert "scholar-pdf extract-run" in error["message"]
    assert "scholar_pdf.extraction.PDFExtractionService" in error["message"]
    assert error["details"]["mcp_supported"] is False
    assert error["details"]["capability"] == caps.PDF_EXTRACTION
    assert error["details"]["owning_surfaces"] == ["API", "CLI"]
    assert error["details"]["owner"] == "nexus-scholar-org/scholar-pdf-kit"


def test_e2_neg_019_rejection_envelope_is_pure_and_zero_io() -> None:
    """Zero I/O, proven structurally rather than asserted in prose.

    The rejection is a pure projection of an immutable declaration: calling it
    neither mutates the registry nor perturbs the declaration, and repeated calls
    are byte-identical. A filesystem- or network-touching implementation would
    fail the determinism or the immutability check.
    """

    before_declaration = vars(caps.PDF_EXTRACTION_DECLARATION).copy()
    first = caps.unsupported_capability_envelope_json(caps.PDF_EXTRACTION)
    second = caps.unsupported_capability_envelope_json(caps.PDF_EXTRACTION)
    assert first == second, "the rejection envelope must be deterministic"
    assert first.encode("utf-8") == second.encode("utf-8"), (
        "two calls must be byte-identical, not merely equal after parsing"
    )

    assert vars(caps.PDF_EXTRACTION_DECLARATION) == before_declaration
    assert caps.get_capability(caps.PDF_EXTRACTION) is caps.PDF_EXTRACTION_DECLARATION


def test_e2_neg_020_e2_does_not_broaden_the_e1_acquisition_declaration() -> None:
    """E2-NEG-020: exactly two declared capabilities, E1's boundary unchanged."""

    assert set(caps.CAPABILITIES) == {caps.PDF_ACQUISITION, caps.PDF_EXTRACTION}
    assert caps.PDF_ACQUISITION_DECLARATION.mcp_supported is False
    assert (
        caps.PDF_ACQUISITION_DECLARATION.rejection_operation
        == caps.ACQUIRE_PDF_OPERATION
    )
    assert (
        caps.PDF_ACQUISITION_DECLARATION.rejection_code == caps.UNSUPPORTED_CAPABILITY
    )
    # E1's envelope is untouched by E2: still acquire_pdf, still one
    # non-retryable UNSUPPORTED_CAPABILITY error, still naming E1's alternatives.
    acquisition = json.loads(
        caps.unsupported_capability_envelope_json(caps.PDF_ACQUISITION)
    )
    assert acquisition["operation"] == "acquire_pdf"
    assert acquisition["status"] == "FAILED"
    assert len(acquisition["errors"]) == 1
    assert acquisition["errors"][0]["code"] == caps.UNSUPPORTED_CAPABILITY
    assert acquisition["errors"][0]["retryable"] is False
    assert "scholar-pdf acquire" in acquisition["errors"][0]["message"]


def test_e2_neg_020_unknown_capability_is_never_silently_unsupported() -> None:
    """An undeclared capability is a bug, not a soft 'unsupported' answer."""

    with pytest.raises(caps.UnknownCapabilityError):
        caps.get_capability("not_a_capability")
    with pytest.raises(caps.UnknownCapabilityError):
        caps.unsupported_capability_envelope_json("not_a_capability")


def test_e2_neg_019_mcp_boundary_module_declares_without_doing_extraction() -> None:
    """The agent kit declares a boundary; it must not own PDF extraction logic.

    Parsed rather than grepped: the module may not import the pdf kit, nor any
    filesystem/network capability, so the declared-unsupported path *cannot*
    extract, write a sidecar, or emit a Contract artifact even by accident.
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


# --------------------------------------------------------------------------- #
# CLI-surface parity -- the authoritative alternative really exists
# --------------------------------------------------------------------------- #


def test_e2_cli_extract_run_is_registered_and_the_legacy_extract_survives() -> None:
    """`scholar-pdf extract-run` is a registered command; `extract` remains.

    The rejection envelope redirects callers to the ``extract-run`` CLI, so that
    command must resolve. The legacy raw-path ``extract`` stays beside it as the
    non-authoritative convenience packet E2 §9.4 keeps.
    """

    names = {
        command.name
        for command in pdf_cli.app.registered_commands
        if command.name is not None
    }
    assert "extract-run" in names, (
        f"scholar-pdf extract-run is not registered: {sorted(names)}"
    )
    assert "extract" in names, "the legacy non-authoritative extract must survive"

    click_command = typer.main.get_command(pdf_cli.app)
    assert "extract-run" in click_command.commands, (
        f"click cannot resolve `scholar-pdf extract-run`: {sorted(click_command.commands)}"
    )
    # The other long-standing pdf commands must survive alongside both.
    assert {"acquire", "download", "ingest", "extract", "extract-run"} <= set(
        click_command.commands
    )


def test_e2_cli_extract_run_help_claims_no_mcp_parity() -> None:
    """The CLI surface must not advertise MCP parity it does not have.

    E2 is a declared unsupported difference on MCP (§9.5). The authoritative CLI
    presents itself as the supported API/CLI path, and the legacy command is
    labelled non-authoritative rather than silently authoritative.
    """

    click_command = typer.main.get_command(pdf_cli.app)
    authoritative = click_command.commands["extract-run"]
    help_text = " ".join(
        filter(None, [authoritative.help, *(p.help for p in authoritative.params)])
    )
    assert "extraction" in help_text.lower()
    assert "authoritative" in help_text.lower(), (
        f"extract-run must present itself as the authoritative surface: {help_text!r}"
    )
    assert "mcp" not in help_text.lower(), (
        f"the CLI must not claim MCP parity: {help_text!r}"
    )

    legacy = click_command.commands["extract"]
    legacy_help = " ".join(
        filter(None, [legacy.help, *(p.help for p in legacy.params)])
    )
    assert "non-authoritative" in legacy_help.lower(), (
        f"the legacy extract command must be labelled non-authoritative: {legacy_help!r}"
    )
