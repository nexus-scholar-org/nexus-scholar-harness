"""Cross-kit canonical & identifier parity pin -- T-SC1.

Packet: ``docs/architecture/packet_t_sc1_canonical_profile_parity_2026-10-21.md``.

The canonicalization and identifier primitives are deliberately *restated* in
four places so the kits stay standalone-buildable (they never import the
harness).  Restatement without a cross-repo pin is an unpinned obligation: a
kit can change its semantics and every identity it mints moves silently.  This
file is that pin.  It proves the three ``contract_v1_canonical``
implementations (harness, RAG kit, PDF kit) are **byte-identical** over a frozen
golden payload set -- including which inputs they *reject* -- and that the two
non-contract profiles (``documents_list_ascii``,
``protocol_declaration_order``) are **provably distinct**, never silently
coerced into the contract profile (G3 / D-3: assert distinctness, never
normalize).

What a green run proves and what it does not
--------------------------------------------
Green here proves the *boundary* is real: the restatements still agree with the
frozen Contract v1 reference and with each other over the golden set, and the
distinct profiles stay distinct.  It does **not** prove the kits work -- their
own suites do.  If any kit has drifted, the relevant parity test fails with the
exact payload id; per G5 the implementer stops and reports ``BLOCKED_KIT_DRIFT``
rather than fixing kit code or regenerating a golden to hide the failure.

The mutation tests at the bottom (NC-1..NC-9) build a deliberately *different*
implementation of one dimension each and assert it diverges from the frozen
golden on the same input, which is what makes the goldens load-bearing instead
of decorative.  NC-4 (hand-edited golden) and NC-5 (non-deterministic
generator) are proven by temporary, reverted mutations recorded in the task
report, not by a permanent test.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest
from scholar_pdf import canonical as pdf_canonical
from scholar_protocol.canonical import (
    canonical_fingerprint as protocol_fingerprint,
)
from scholar_protocol.canonical import (
    canonical_json as protocol_canonical_json,
)
from scholar_protocol.models import ResearchProtocol
from scholar_rag import canonical as rag_canonical
from scholar_search.canonical import (
    canonical_fingerprint as search_fingerprint,
)
from scholar_search.canonical import (
    canonical_json as search_canonical_json,
)

from scholar_harness.contracts import canonical as harness_canonical
from scholar_harness.contracts import identifiers as harness_identifiers

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "canonical_profiles"
GENERATOR_SCRIPT = REPO_ROOT / "scripts" / "generate_canonical_profile_goldens.py"

#: The three declared profiles (G3).  Anything else is a legacy/custom profile
#: and must be detected and reported, never normalized into one of these.
CONTRACT_PROFILE = "contract_v1_canonical"
DOCUMENTS_PROFILE = "documents_list_ascii"
PROTOCOL_PROFILE = "protocol_declaration_order"
DECLARED_PROFILES = {CONTRACT_PROFILE, DOCUMENTS_PROFILE, PROTOCOL_PROFILE}

#: Each implementation maps to exactly ONE profile.  This is the AC-9 registry:
#: no serializer is routed through another profile's code path.
PROFILE_REGISTRY: dict[str, str] = {
    "scholar_harness.contracts.canonical": CONTRACT_PROFILE,
    "scholar_rag.canonical": CONTRACT_PROFILE,
    "scholar_pdf.canonical": CONTRACT_PROFILE,
    "scholar_search.canonical": DOCUMENTS_PROFILE,
    "scholar_protocol.canonical": PROTOCOL_PROFILE,
}

FINGERPRINT_SPELLING = re.compile(r"^sha256:[0-9a-f]{64}$")


# --------------------------------------------------------------------------- #
# Loaders: the generator module (payload builders) and the frozen goldens
# --------------------------------------------------------------------------- #
def _load_generator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "canonical_profile_goldens_generator", GENERATOR_SCRIPT
    )
    assert spec is not None and spec.loader is not None, (
        f"cannot load the golden generator at {GENERATOR_SCRIPT}"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _load_golden(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


#: The four frozen goldens, loaded once at module import.  Plain constants (not
#: fixtures) because the parametrize decorators need them at collection time.
CONTRACT_GOLDEN: dict[str, Any] = _load_golden("contract_v1_canonical.json")
DOCUMENTS_GOLDEN: dict[str, Any] = _load_golden("documents_list_ascii.json")
PROTOCOL_GOLDEN: dict[str, Any] = _load_golden("protocol_declaration_order.json")
REGISTRY_GOLDEN: dict[str, Any] = _load_golden("identifier_registry.json")


# --------------------------------------------------------------------------- #
# AC-1 / AC-2 / AC-3 -- the goldens are in sync, deterministic, and clean
# --------------------------------------------------------------------------- #
def test_goldens_are_in_sync_with_the_generator() -> None:
    """AC-1: on-disk goldens equal what the generator currently produces.

    This is the ``--check`` logic in-process; the CLI ``--check`` is also run in
    the validation lane.  A hand-edited golden (NC-4) fails here and in the CLI
    with the file and field named.
    """

    rebuilt = GEN.build_goldens()
    for name, obj in rebuilt.items():
        path = FIXTURE_DIR / name
        assert path.is_file(), f"missing golden {name}; run the generator"
        assert path.read_text(encoding="utf-8") == GEN._render(obj), (
            f"{name} is out of sync with the generator -- regenerate deliberately, "
            "never hand-edit"
        )


def test_generator_is_deterministic_on_a_double_build() -> None:
    """AC-2 / G7: two builds render byte-identical text."""

    first = {name: GEN._render(obj) for name, obj in GEN.build_goldens().items()}
    second = {name: GEN._render(obj) for name, obj in GEN.build_goldens().items()}
    assert first == second


def test_goldens_carry_no_generation_or_environment_data() -> None:
    """AC-3: no absolute path, hostname, env value, or generation timestamp.

    The only timestamp-like string permitted is the protocol payload's pinned
    ``created_at`` constant (a required model field fixed for determinism), which
    must equal the generator's own constant -- it is data, not wall-clock.
    """

    banned_tokens = (
        "C:\\",
        "/Users/",
        "/home/",
        "C:/",
        "USERNAME",
        "USERPROFILE",
        "COMPUTERNAME",
        "APPDATA",
        "HOSTNAME",
        "worktree",
        "mouadh",
    )
    iso_timestamp = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        for token in banned_tokens:
            assert token not in text, f"{path.name} leaked environment value {token!r}"
        for match in iso_timestamp.findall(text):
            assert match == GEN.PROTOCOL_PAYLOAD["created_at"][:16], (
                f"{path.name} contains an unexpected timestamp {match!r}"
            )
    # And the pinned protocol timestamp is exactly the generator constant.
    assert GEN.PROTOCOL_PAYLOAD["created_at"] == "2026-09-20T12:00:00+00:00"


# --------------------------------------------------------------------------- #
# AC-4 -- contract-v1 parity: harness == rag == pdf == golden, byte-identical
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "case",
    CONTRACT_GOLDEN["cases"],
    ids=[c["payload_id"] for c in CONTRACT_GOLDEN["cases"]],
)
def test_contract_v1_parity_is_byte_identical_across_three_implementations(
    case: dict[str, Any],
) -> None:
    """AC-4: the normative profile agrees byte-for-byte across the three kits.

    This is the drift detector (G5).  Expected bytes come from the HARNESS
    reference only; if any kit has drifted, its bytes differ from the frozen
    golden here and the implementer reports BLOCKED_KIT_DRIFT.
    """

    payload = case["payload"]
    set_like = tuple(case.get("set_like_arrays", []))
    expected_bytes = case["expected_canonical_bytes"].encode("utf-8")
    expected_fp = case["expected_fingerprint"]

    harness_bytes = harness_canonical.canonical_json_bytes(
        payload, set_like_arrays=set_like
    )
    rag_bytes = rag_canonical.canonical_json_bytes(payload, set_like_arrays=set_like)
    pdf_bytes = pdf_canonical.canonical_json_bytes(payload, set_like_arrays=set_like)

    assert harness_bytes == expected_bytes, f"harness drifted on {case['payload_id']}"
    assert rag_bytes == expected_bytes, (
        f"RAG kit drifted from the contract-v1 golden on {case['payload_id']}: "
        f"kit={rag_bytes!r} golden={expected_bytes!r}"
    )
    assert pdf_bytes == expected_bytes, (
        f"PDF kit drifted from the contract-v1 golden on {case['payload_id']}: "
        f"kit={pdf_bytes!r} golden={expected_bytes!r}"
    )
    for name, module in (
        ("harness", harness_canonical),
        ("rag", rag_canonical),
        ("pdf", pdf_canonical),
    ):
        fp = module.canonical_fingerprint(payload, set_like_arrays=set_like)
        assert fp == expected_fp, f"{name} fingerprint drifted on {case['payload_id']}"
        assert FINGERPRINT_SPELLING.fullmatch(fp)


def test_key_order_permutation_yields_identical_contract_bytes() -> None:
    """G7: a pair differing only by key order serializes identically.

    The insertion-order difference lives in the generator's PYTHON payload
    literals; the golden round-trips through ``sort_keys=True`` so the stored
    payloads are already normalized.  Both facts are asserted: the python
    payloads differ by insertion order, and their canonical bytes agree and
    match the frozen golden.
    """

    python_payloads = {pid: payload for pid, payload, _ in GEN.CONTRACT_CASES}
    alpha = python_payloads["keyorder_alpha"]
    beta = python_payloads["keyorder_beta"]
    assert list(alpha) != list(beta), "the pair must differ by insertion order"
    assert list(alpha["z"]) != list(beta["z"])
    a_bytes = harness_canonical.canonical_json_bytes(alpha)
    b_bytes = harness_canonical.canonical_json_bytes(beta)
    assert a_bytes == b_bytes
    golden = next(
        c for c in CONTRACT_GOLDEN["cases"] if c["payload_id"] == "keyorder_alpha"
    )
    assert a_bytes == golden["expected_canonical_bytes"].encode("utf-8")
    assert harness_canonical.canonical_fingerprint(alpha) == (
        harness_canonical.canonical_fingerprint(beta)
    )


def test_array_order_permutation_yields_different_contract_bytes() -> None:
    """G7 / NC-8: an order-significant array is NOT silently normalized."""

    forward = next(
        c for c in CONTRACT_GOLDEN["cases"] if c["payload_id"] == "arrayorder_forward"
    )
    reverse = next(
        c for c in CONTRACT_GOLDEN["cases"] if c["payload_id"] == "arrayorder_reverse"
    )
    f_bytes = harness_canonical.canonical_json_bytes(forward["payload"])
    r_bytes = harness_canonical.canonical_json_bytes(reverse["payload"])
    assert f_bytes != r_bytes, "array order must stay semantic (not set-like here)"
    assert f_bytes == forward["expected_canonical_bytes"].encode("utf-8")
    assert r_bytes == reverse["expected_canonical_bytes"].encode("utf-8")


def test_repeated_serialization_is_deterministic() -> None:
    """AC-14 determinism: repeated calls over payloads return identical bytes."""

    for case in CONTRACT_GOLDEN["cases"]:
        payload = case["payload"]
        set_like = tuple(case.get("set_like_arrays", []))
        first = harness_canonical.canonical_json_bytes(
            payload, set_like_arrays=set_like
        )
        second = harness_canonical.canonical_json_bytes(
            payload, set_like_arrays=set_like
        )
        assert first == second


# --------------------------------------------------------------------------- #
# AC-6 / G6 -- rejection parity: all three reject the same inputs, same types
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "rejection",
    CONTRACT_GOLDEN["rejections"],
    ids=[r["payload_id"] for r in CONTRACT_GOLDEN["rejections"]],
)
def test_rejection_parity_all_three_reject_the_same_inputs(
    rejection: dict[str, Any],
) -> None:
    """AC-6 / G6: which inputs are rejected, with which exception type.

    A kit that ACCEPTS a payload the harness rejects (coercion, NC-3) is a
    parity failure, not a pass.
    """

    payload = GEN.build_rejection_payload(rejection["builder"])
    expected_type = rejection["expected_exception_type"]
    for name, module in (
        ("harness", harness_canonical),
        ("rag", rag_canonical),
        ("pdf", pdf_canonical),
    ):
        with pytest.raises(Exception) as caught:
            module.canonical_json_bytes(payload)
        assert type(caught.value).__name__ == expected_type, (
            f"{name} raised {type(caught.value).__name__} instead of "
            f"{expected_type} on {rejection['payload_id']} -- rejection drift (G6)"
        )
        # And it is a real rejection, never a coerced success.
        assert not isinstance(caught.value, (str, bytes))


# --------------------------------------------------------------------------- #
# AC-7 -- documents_list_ascii matches its own golden and is DISTINCT
# --------------------------------------------------------------------------- #
def test_documents_list_ascii_matches_its_own_golden() -> None:
    case = DOCUMENTS_GOLDEN["cases"][0]
    payload = case["payload"]
    assert payload == GEN.DOCUMENTS_PAYLOAD
    assert search_canonical_json(payload) == case["expected_canonical_bytes"].encode(
        "utf-8"
    )
    assert search_fingerprint(payload) == case["expected_fingerprint"]


def test_documents_list_ascii_is_distinct_from_contract_v1_on_unicode() -> None:
    """AC-7 / G3 / D-3: the search profile is NOT the contract profile.

    On the same unicode payload the two serializers must disagree (search
    escapes non-ASCII, contract emits raw UTF-8): different bytes and a
    different fingerprint.  This proves the two are not interchangeable and no
    code path routes one through the other's serializer.
    """

    case = DOCUMENTS_GOLDEN["cases"][0]
    payload = case["payload"]
    documents_bytes = search_canonical_json(payload)
    contract_bytes = harness_canonical.canonical_json_bytes(payload)
    assert documents_bytes != contract_bytes, (
        "documents_list_ascii and contract_v1_canonical unexpectedly agree on the "
        "unicode payload -- a profile was coerced"
    )
    assert b"\\u" in documents_bytes and b"\\u" not in contract_bytes
    assert search_fingerprint(payload) != harness_canonical.canonical_fingerprint(
        payload
    )
    # Names the profile each implementation belongs to.
    assert PROFILE_REGISTRY["scholar_search.canonical"] == DOCUMENTS_PROFILE
    assert PROFILE_REGISTRY["scholar_harness.contracts.canonical"] == CONTRACT_PROFILE


# --------------------------------------------------------------------------- #
# AC-8 -- protocol_declaration_order matches its own golden and is DISTINCT
# --------------------------------------------------------------------------- #
def test_protocol_declaration_order_matches_its_own_golden() -> None:
    case = PROTOCOL_GOLDEN["cases"][0]
    assert case["payload"] == GEN.PROTOCOL_PAYLOAD
    model = ResearchProtocol.model_validate(case["payload"])
    assert protocol_canonical_json(model) == case["expected_canonical_bytes"].encode(
        "utf-8"
    )
    assert protocol_fingerprint(model) == case["expected_fingerprint"]


def test_protocol_declaration_order_is_distinct_from_a_key_sorted_serialization() -> (
    None
):
    """AC-8: declaration order is preserved, not sorted (G3 / D-3)."""

    case = PROTOCOL_GOLDEN["cases"][0]
    model = ResearchProtocol.model_validate(case["payload"])
    protocol_bytes = protocol_canonical_json(model)
    key_sorted = json.dumps(
        model.model_dump(mode="json", by_alias=True),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert protocol_bytes != key_sorted, (
        "protocol_declaration_order collapsed into a key-sorted serialization -- "
        "declaration order must be preserved"
    )
    assert protocol_bytes == case["expected_canonical_bytes"].encode("utf-8")
    assert PROFILE_REGISTRY["scholar_protocol.canonical"] == PROTOCOL_PROFILE


# --------------------------------------------------------------------------- #
# AC-9 -- the profile registry: one profile per implementation, no coercion
# --------------------------------------------------------------------------- #
def test_profile_registry_maps_each_implementation_to_exactly_one_profile() -> None:
    """AC-9: no implementation is routed through another profile's serializer."""

    assert set(PROFILE_REGISTRY.values()) == DECLARED_PROFILES
    # Every declared profile is represented.
    assert set(PROFILE_REGISTRY) == {
        "scholar_harness.contracts.canonical",
        "scholar_rag.canonical",
        "scholar_pdf.canonical",
        "scholar_search.canonical",
        "scholar_protocol.canonical",
    }
    # The one DEFINED agreement across distinct-looking names: rag and pdf are
    # contract_v1_canonical, so they agree WITH the harness by design.  The
    # profiles that must NOT agree are the non-contract ones, proved next.
    assert (
        PROFILE_REGISTRY["scholar_rag.canonical"]
        == PROFILE_REGISTRY["scholar_harness.contracts.canonical"]
        == CONTRACT_PROFILE
    )


def test_no_distinct_profile_shares_bytes_with_the_contract_profile() -> None:
    """AC-9: for the shared unicode payload, distinct profiles disagree.

    The only profiles defined to agree are the three contract_v1_canonical
    implementations (enumerated in the registry test above).  The non-contract
    profiles must never reproduce the contract profile's bytes.
    """

    payload = DOCUMENTS_GOLDEN["cases"][0]["payload"]
    contract_bytes = harness_canonical.canonical_json_bytes(payload)
    documents_bytes = search_canonical_json(payload)
    assert contract_bytes != documents_bytes


# --------------------------------------------------------------------------- #
# AC-10 -- identifier registry parity: harness == rag
# --------------------------------------------------------------------------- #
def _registry_view(id_prefixes: Any) -> dict[str, Any]:
    """Project a kit's ``ID_PREFIXES`` mapping into the golden registry shape.

    This is the single projection both the real NC-2 gate and the NC-2
    mutation proof run through, so the proof and the gate cannot diverge.
    Keys may be enum members (the real rag-kit registry) or plain strings
    (the in-test mutant); the projection is identical either way.
    """

    return {
        getattr(kind, "value", kind): {
            "prefixes": list(prefixes),
            "mint_prefix": prefixes[0],
            "legacy_prefixes": list(prefixes[1:]),
        }
        for kind, prefixes in id_prefixes.items()
    }


def _registry_view_differences(
    view: dict[str, Any], registry: dict[str, Any]
) -> list[str]:
    """The kinds where ``view`` and the golden ``registry`` differ.

    Names every differing, missing, or extra kind so an actual NC-2 drift
    failure is diagnosable without reading the mutation proof.
    """

    return [
        kind
        for kind in sorted(set(view) | set(registry))
        if view.get(kind) != registry.get(kind)
    ]


def test_identifier_registry_mirrors_between_harness_and_rag() -> None:
    registry = REGISTRY_GOLDEN["registry"]
    # The golden came from the harness; the harness still agrees with it.
    assert harness_identifiers.identifier_registry() == registry
    # The RAG restatement has the same kind set, same prefix tuples in the same
    # order, and the same mint prefix (== prefixes[0]).  The comparison and the
    # naming below go through the same helpers the NC-2 mutation proof uses.
    rag_registry = _registry_view(rag_canonical.ID_PREFIXES)
    differing = _registry_view_differences(rag_registry, registry)
    assert not differing, (
        f"RAG kit identifier registry drifted (NC-2); differing kind(s): {differing}"
    )
    assert [k.value for k in rag_canonical.IdentifierKind] == [
        k.value for k in harness_identifiers.IdentifierKind
    ]
    for kind in harness_identifiers.IdentifierKind:
        assert rag_canonical.primary_prefix(
            kind.value
        ) == harness_identifiers.primary_prefix(kind)


@pytest.mark.parametrize(
    "case",
    REGISTRY_GOLDEN["validate_identifier_cases"],
    ids=[c["payload_id"] for c in REGISTRY_GOLDEN["validate_identifier_cases"]],
)
def test_validate_identifier_accepts_and_rejects_the_same_strings(
    case: dict[str, Any],
) -> None:
    harness_kind = harness_identifiers.IdentifierKind(case["kind"])
    rag_kind = rag_canonical.IdentifierKind(case["kind"])
    if case["accepted"]:
        assert (
            harness_identifiers.validate_identifier(harness_kind, case["value"])
            == case["value"]
        )
        assert (
            rag_canonical.validate_identifier(rag_kind, case["value"]) == case["value"]
        )
    else:
        expected = case["expected_exception_type"]
        with pytest.raises(Exception) as harnessCaught:
            harness_identifiers.validate_identifier(harness_kind, case["value"])
        with pytest.raises(Exception) as ragCaught:
            rag_canonical.validate_identifier(rag_kind, case["value"])
        assert type(harnessCaught.value).__name__ == expected
        assert type(ragCaught.value).__name__ == expected


# --------------------------------------------------------------------------- #
# AC-11 -- identity-minting parity (rag incl. rag-chunk; pdf document id)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "case",
    REGISTRY_GOLDEN["deterministic_id_cases"],
    ids=[c["payload_id"] for c in REGISTRY_GOLDEN["deterministic_id_cases"]],
)
def test_deterministic_id_parity_harness_equals_rag(
    case: dict[str, Any],
) -> None:
    """AC-11: the same (kind, namespace, input, version) mints the same id.

    Includes the non-default ``rag-chunk-identity-v1`` version the RAG kit
    really mints chunk ids with (NC-7).
    """

    harness_kind = harness_identifiers.IdentifierKind(case["kind"])
    rag_kind = rag_canonical.IdentifierKind(case["kind"])
    expected = case["expected_id"]
    harness_id = harness_canonical.deterministic_id(
        harness_kind,
        case["workspace_namespace"],
        case["input"],
        algorithm_version=case["algorithm_version"],
    )
    rag_id = rag_canonical.deterministic_id(
        rag_kind,
        case["workspace_namespace"],
        case["input"],
        algorithm_version=case["algorithm_version"],
    )
    assert harness_id == expected, f"harness mint drifted on {case['payload_id']}"
    assert rag_id == expected, (
        f"RAG kit mint drifted on {case['payload_id']}: kit={rag_id!r} golden={expected!r}"
    )


def test_pdf_document_identity_matches_harness_deterministic_id() -> None:
    """AC-11: harness ``deterministic_id(DOCUMENT,...)`` == pdf
    ``deterministic_document_id(...)`` for the same inputs."""

    case = next(
        c
        for c in REGISTRY_GOLDEN["deterministic_id_cases"]
        if c["payload_id"] == "document_pdf"
    )
    pdf_id = pdf_canonical.deterministic_document_id(
        study_id=case["input"]["study_id"],
        source_hash=case["input"]["source_sha256"],
        workspace_id=case["workspace_namespace"],
    )
    assert pdf_id == case["expected_id"]


def test_rag_chunk_identity_uses_the_non_default_algorithm_version() -> None:
    """NC-7 guard: the rag-chunk case really pins the non-default version."""

    case = next(
        c
        for c in REGISTRY_GOLDEN["deterministic_id_cases"]
        if c["payload_id"] == "chunk_rag"
    )
    assert case["algorithm_version"] == "rag-chunk-identity-v1"
    # A v1-only restriction would mint a DIFFERENT id, so the parity test above
    # (which pins the rag-chunk-identity-v1 golden) would fail.
    v1_id = rag_canonical.deterministic_id(
        rag_canonical.IdentifierKind(case["kind"]),
        case["workspace_namespace"],
        case["input"],
        algorithm_version="v1",
    )
    assert v1_id != case["expected_id"]


# --------------------------------------------------------------------------- #
# AC-12 -- corpus fingerprint parity: harness == pdf
# --------------------------------------------------------------------------- #
def test_corpus_snapshot_fingerprint_parity_harness_equals_pdf() -> None:
    snapshot = REGISTRY_GOLDEN["corpus_snapshot"]
    assert snapshot["payload"] == GEN.CORPUS_SNAPSHOT_PAYLOAD
    expected = snapshot["expected_fingerprint"]
    harness_fp = harness_canonical.corpus_snapshot_fingerprint(snapshot["payload"])
    pdf_fp = pdf_canonical.corpus_snapshot_fingerprint(snapshot["payload"])
    assert harness_fp == expected
    assert pdf_fp == expected, (
        f"PDF kit corpus fingerprint drifted: kit={pdf_fp!r} golden={expected!r}"
    )
    # The normalization is real: order-insensitive to study/record array order.
    reordered = json.loads(json.dumps(snapshot["payload"]))
    reordered["studies"].reverse()
    assert harness_canonical.corpus_snapshot_fingerprint(reordered) == expected


# --------------------------------------------------------------------------- #
# NC mutation proofs -- these build a deliberately-wrong implementation and
# assert the corresponding check BITES (diverges from the golden).  They prove
# the parity gate is load-bearing, not decorative.
# --------------------------------------------------------------------------- #
def _contract_mutant_bytes(value: Any, **dump_overrides: Any) -> bytes:
    normalized = harness_canonical._normalize_json(
        value, path=(), set_like_arrays=frozenset()
    )
    kwargs = {
        "ensure_ascii": False,
        "sort_keys": True,
        "separators": (",", ":"),
        "allow_nan": False,
    }
    kwargs.update(dump_overrides)
    return json.dumps(normalized, **kwargs).encode("utf-8")


def test_nc1_ensure_ascii_flip_diverges_on_unicode() -> None:
    """NC-1: flipping ``ensure_ascii`` on the contract profile is caught."""

    unicode_case = next(
        c for c in CONTRACT_GOLDEN["cases"] if c["payload_id"] == "unicode_text"
    )
    golden = unicode_case["expected_canonical_bytes"].encode("utf-8")
    mutant = _contract_mutant_bytes(unicode_case["payload"], ensure_ascii=True)
    assert mutant != golden and b"\\u" in mutant
    assert harness_canonical.canonical_json_bytes(unicode_case["payload"]) == golden


def test_nc2_registry_prefix_change_diverges_naming_the_kind() -> None:
    """NC-2: a changed prefix fails registry parity, naming the differing kind.

    The mutant is an ``ID_PREFIXES``-shaped mapping (built from the REAL
    rag-kit registry, with only ``STUDY``'s prefix drifted) pushed through
    the SAME comparison path the real gate uses: ``_registry_view`` then
    ``_registry_view_differences`` against the frozen golden.  The proof and
    the gate therefore cannot diverge.
    """

    registry = REGISTRY_GOLDEN["registry"]
    mutated_id_prefixes = dict(rag_canonical.ID_PREFIXES)
    mutated_id_prefixes[rag_canonical.IdentifierKind.STUDY] = ("STU2-",)
    mutated_view = _registry_view(mutated_id_prefixes)
    assert mutated_view != registry, "the mutant must diverge from the golden"
    differing = _registry_view_differences(mutated_view, registry)
    assert differing == ["study"], differing


def test_nc3_coercing_serializer_accepts_a_rejected_payload() -> None:
    """NC-3 / G6: a ``default=str`` coercion ACCEPTS what the contract rejects.

    The contract profile must reject the unsupported type; a kit that switched
    to ``default=str`` would accept it and the rejection-parity check would
    fail.  This is exactly the boundary that keeps documents_list_ascii (which
    DOES coerce) out of the contract profile.
    """

    payload = GEN.build_rejection_payload("unsupported_bytes")
    with pytest.raises(TypeError):
        harness_canonical.canonical_json_bytes(payload)

    def coercing_serializer(value: Any) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

    # The coercion ACCEPTS the payload the contract rejects (no exception) --
    # proving the rejection-parity check bites: a kit that switched to
    # ``default=str`` would return bytes here instead of raising TypeError.
    coerced = coercing_serializer(payload)
    assert isinstance(coerced, bytes) and coerced


def test_nc6_routing_search_bytes_through_the_contract_golden_fails() -> None:
    """NC-6: a coerced profile routing is rejected by the distinctness check."""

    payload = DOCUMENTS_GOLDEN["cases"][0]["payload"]
    contract_case_bytes = harness_canonical.canonical_json_bytes(payload)
    documents_bytes = search_canonical_json(payload)
    # Comparing search-kit output to the contract-v1 golden must fail.
    assert documents_bytes != contract_case_bytes


def test_nc8_array_order_is_not_silently_normalized() -> None:
    """NC-8: changing an order-significant array moves the bytes."""

    forward = next(
        c for c in CONTRACT_GOLDEN["cases"] if c["payload_id"] == "arrayorder_forward"
    )
    reverse = next(
        c for c in CONTRACT_GOLDEN["cases"] if c["payload_id"] == "arrayorder_reverse"
    )
    assert harness_canonical.canonical_json_bytes(forward["payload"]) != (
        harness_canonical.canonical_json_bytes(reverse["payload"])
    )


def test_nc9_changed_exception_type_fails_rejection_parity() -> None:
    """NC-9: raising ValueError instead of TypeError fails the type parity."""

    rejection = next(
        r for r in CONTRACT_GOLDEN["rejections"] if r["payload_id"] == "non_string_key"
    )
    assert rejection["expected_exception_type"] == "TypeError"

    def mutant_non_string_key_raises_value_error(value: Any) -> bytes:
        # A plausible "tidying" edit: reject non-string keys with ValueError.
        if isinstance(value, dict) and any(not isinstance(k, str) for k in value):
            raise ValueError("keys must be strings")
        return json.dumps(value).encode("utf-8")

    payload = GEN.build_rejection_payload("non_string_key")
    with pytest.raises(ValueError) as mutant:
        mutant_non_string_key_raises_value_error(payload)
    # The mutant's type differs from the golden's TypeError -> parity fails.
    assert type(mutant.value).__name__ != rejection["expected_exception_type"]
    with pytest.raises(TypeError):
        harness_canonical.canonical_json_bytes(payload)
