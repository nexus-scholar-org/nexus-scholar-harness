"""Generate or verify the frozen cross-kit canonical-profile goldens (T-SC1).

This generator is the deterministic producer of the four golden files under
``tests/fixtures/canonical_profiles/``.  Each golden pins one *profile* of the
canonicalization/identifier primitives that are restated across the harness and
the kits:

* ``contract_v1_canonical``   -- the normative Contract v1 serializer owned by
  ``scholar_harness.contracts.canonical`` and restated byte-for-byte by
  ``scholar_rag.canonical`` and ``scholar_pdf.canonical``.
* ``documents_list_ascii``    -- the search-kit's distinct documents-list
  serializer (``ensure_ascii=True``), owned by ``scholar_search.canonical``.
* ``protocol_declaration_order`` -- the protocol-kit's distinct Pydantic
  declaration-order serializer, owned by ``scholar_protocol.canonical``.
* ``identifier_registry``     -- the Contract v1 identifier registry and
  identity-minting formulas owned by ``scholar_harness.contracts.identifiers``
  and restated by ``scholar_rag.canonical`` / ``scholar_pdf.canonical``.

The expected bytes/fingerprints for each profile are computed by that profile's
**owning reference implementation** (never by a different profile's serializer),
so a kit that silently changes its semantics cannot be baked into a golden to
make the parity gate green.  Running this script twice must produce
byte-identical files: payloads are fixed module-level literals, cases are held
in fixed-order lists, and the file itself is rendered with ``sort_keys=True``.
``--check`` verifies the committed goldens are in sync and names the first
differing file and field when they are not.

Goldens are generated, never hand-edited: a hand-edited golden is a failing
condition (the ``--check`` diff names it).  See
``docs/architecture/canonical_profile_parity.md``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scholar_protocol.canonical import (
    canonical_fingerprint as protocol_fingerprint,
)
from scholar_protocol.canonical import (
    canonical_json as protocol_canonical_json,
)
from scholar_protocol.models import ResearchProtocol
from scholar_search.canonical import (
    canonical_fingerprint as search_fingerprint,
)
from scholar_search.canonical import (
    canonical_json as search_canonical_json,
)

from scholar_harness.contracts import canonical as harness_canonical
from scholar_harness.contracts import identifiers as harness_identifiers

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "canonical_profiles"
GENERATOR_REL = "scripts/generate_canonical_profile_goldens.py"

# The three declared profiles.  A legacy/custom profile is detected and reported,
# never silently normalized into one of these (G3).
CONTRACT_PROFILE = "contract_v1_canonical"
DOCUMENTS_PROFILE = "documents_list_ascii"
PROTOCOL_PROFILE = "protocol_declaration_order"

FINGERPRINT_PREFIX = "sha256:"


# --------------------------------------------------------------------------- #
# contract_v1_canonical payloads (all JSON round-trippable; AC-5 coverage)
# --------------------------------------------------------------------------- #
# Two distinct non-ASCII strings, so Unicode normalization drift (NFC or NFD)
# cannot hide behind one no-op case:
# ``_UNICODE_TEXT`` carries the PRECOMPOSED acute (U+00E9), CJK (U+4E2D
# U+6587), and an emoji (U+1F9EA); normalizing it with NFC is a no-op.
# ``_UNICODE_COMBINING`` carries a GENUINE combining sequence -- an ASCII
# ``e`` followed by U+0301 COMBINING ACUTE ACCENT (never precomposed) -- plus
# the same CJK and emoji; NFC would recompose it to U+00E9 and move the bytes.
# Together they close the coverage hole: a kit that applies
# ``unicodedata.normalize`` is caught by one of the two on the byte-parity
# check (AC-5).  ``_UNICODE_TEXT`` is also the string carried (via
# ``DOCUMENTS_PAYLOAD``) that separates documents_list_ascii (escaped) from
# contract_v1_canonical (raw UTF-8), so AC-7 cannot pass without it.
_UNICODE_TEXT = "Caf\u00e9 \u4e2d\u6587 \U0001f9ea"
_UNICODE_COMBINING = "Cafe\u0301 \u4e2d\u6587 \U0001f9ea"

#: (payload_id, payload, set_like_arrays).  Fixed order; the golden's ``cases``
#: list follows this order exactly, which is what makes the generator
#: deterministic (AC-2 / G7).
CONTRACT_CASES: list[tuple[str, Any, tuple[str, ...]]] = [
    ("unicode_text", {"s": _UNICODE_TEXT}, ()),
    # AC-5 genuine combining sequence (e + U+0301, never precomposed): a kit
    # that applies Unicode NFC normalization recomposes it to U+00E9 and
    # moves the bytes, which the precomposed ``unicode_text`` case alone
    # could not detect (NFC on it is a no-op).
    ("unicode_combining", {"s": _UNICODE_COMBINING}, ()),
    ("integral_float", {"x": 5.0}, ()),
    ("negative_zero_float", {"x": -0.0}, ()),
    ("fractional_float", {"x": 2.5}, ()),
    ("empty_containers", {"e_dict": {}, "e_list": [], "n": None}, ()),
    (
        "deep_nesting",
        {"a": {"b": {"c": {"d": [1, 2, {"e": 3}]}}}},
        (),
    ),
    ("large_integer", {"n": 123456789012345678901234567890}, ()),
    ("numeric_looking_string", {"n": "42", "big": "1e10"}, ()),
    (
        "bool_vs_int",
        {"t": True, "i": 1, "f": False, "z": 0},
        (),
    ),
    # A key-order-permuted pair: identical keys/values, different insertion
    # order -> identical canonical bytes (G7 / AC-5).
    ("keyorder_alpha", {"b": 1, "a": 2, "z": {"y": 3, "x": 4}}, ()),
    ("keyorder_beta", {"z": {"x": 4, "y": 3}, "a": 2, "b": 1}, ()),
    # An array-order-permuted pair: order-significant array (not registered
    # set-like) -> different canonical bytes (G7 / NC-8).
    ("arrayorder_forward", {"study_ids": ["STU-a", "STU-b", "STU-c"]}, ()),
    ("arrayorder_reverse", {"study_ids": ["STU-c", "STU-b", "STU-a"]}, ()),
]

#: Rejection cases.  The payload builders are not JSON round-trippable, so the
#: golden stores only the payload id, the builder name, and the expected
#: exception type; the parity test reconstructs the payload through
#: :func:`build_rejection_payload`.  Expected types are the Contract v1
#: reference behaviour (G6).
REJECTION_CASES: list[tuple[str, str]] = [
    ("nan", "ValueError"),
    ("infinity", "ValueError"),
    ("negative_infinity", "ValueError"),
    ("non_string_key", "TypeError"),
    ("unsupported_bytes", "TypeError"),
    ("unsupported_object", "TypeError"),
]


def build_rejection_payload(payload_id: str) -> Any:
    """Reconstruct a rejection payload from its golden builder name."""

    builders: dict[str, Any] = {
        "nan": {"x": float("nan")},
        "infinity": {"x": float("inf")},
        "negative_infinity": {"x": float("-inf")},
        "non_string_key": {1: "a"},
        "unsupported_bytes": {"x": b"bytes"},
        "unsupported_object": {"x": object()},
    }
    try:
        return builders[payload_id]
    except KeyError:
        raise KeyError(f"unknown rejection payload builder: {payload_id}") from None


# --------------------------------------------------------------------------- #
# documents_list_ascii payload (search-kit owner)
# --------------------------------------------------------------------------- #
#: A list of raw document dicts with non-ASCII text.  Fed verbatim to the
#: search-kit serializer (its golden) *and* to the contract-v1 serializer (for
#: the AC-7 distinctness proof): the two profiles must disagree here.
DOCUMENTS_PAYLOAD: list[dict[str, Any]] = [
    {
        "title": f"RAG review {_UNICODE_TEXT}",
        "year": 2024,
        "provider": "openalex",
        "provider_id": "W-1",
        "external_ids": {"doi": "10.1234/test.1", "openalex_id": "W-1"},
        "abstract": f"An abstract {_UNICODE_TEXT}",
        "authors": [{"family_name": "Smith", "given_name": "John"}],
    }
]


# --------------------------------------------------------------------------- #
# protocol_declaration_order payload (protocol-kit owner)
# --------------------------------------------------------------------------- #
#: A fully explicit ``ResearchProtocol`` payload with a FIXED ``created_at`` so
#: serialization is deterministic (the model default reads the clock).
PROTOCOL_PAYLOAD: dict[str, Any] = {
    "$schema": "schemas/v1/protocol.schema.json",
    "protocol_id": "PRT-019a2b3c4d5e6f7a8b9c0d1e2f3a4b5c",
    "created_at": "2026-09-20T12:00:00+00:00",
    "project_slug": "canonical-profile-parity",
    "playbook_type": "SCOPING_REVIEW",
    "metadata": {
        "title": "Canonical Profile Parity Baseline",
        "lead_researcher": "Nexus Reviewer",
        "target_venue_type": "ACM Computing Surveys",
        "timeline_weeks": 8,
    },
    "epistemology": {
        "primary_paradigm": "Pragmatist / Mixed Methods",
        "secondary_paradigm": None,
        "unit_of_analysis": "Canonical protocol serialization",
        "trustworthiness_framework": "JBI Scoping Review Framework",
        "epistemological_rationale": "Validate protocol identity stability.",
        "incompatible_concepts": [],
    },
    "research_questions": [
        {
            "id": "RQ1",
            "text": "How do serializer profiles affect canonical identity?",
            "target_facet": "determinism",
            "synthesis_type": "Comparative Matrix",
            "required_evidence_type": "Empirical serialization output",
        }
    ],
    "search_strategy": {
        "core_concepts": [
            {
                "concept": "Protocol Identity",
                "synonyms": ["canonical serialization", "protocol fingerprint"],
                "boolean_operator": "OR",
            }
        ],
        "target_databases": ["openalex", "semanticscholar"],
        "date_range": {"start_year": 2020, "end_year": 2026},
        "languages": ["en"],
        "open_access_preferred": True,
        "target_candidate_pool_size": {"min": 100, "max": 500},
        "golden_seeds": [],
    },
    "screening_criteria": {
        "inclusion": [
            {
                "id": "INC-01",
                "criterion": "Protocols declaring explicit research questions",
                "maps_to_rqs": ["RQ1"],
                "reason_category": None,
            }
        ],
        "exclusion": [
            {
                "id": "EXC-01",
                "criterion": "Malformed protocol documents",
                "maps_to_rqs": [],
                "reason_category": "INVALID_FORMAT",
            }
        ],
        "two_tier_screening": True,
    },
    "matrix_dimensions": [],
    "verification": {
        "retraction_check_required": True,
        "coi_and_funding_audit_required": True,
        "reproducibility_das_cas_check": True,
        "minimum_trust_score_threshold": 5.0,
    },
}


# --------------------------------------------------------------------------- #
# identifier-registry / identity-minting payload (harness owner)
# --------------------------------------------------------------------------- #
WORKSPACE_NAMESPACE = "WSP-" + "ab" * 16
_SOURCE_HASH = "sha256:" + "ab" * 32
_STUDY_ID = "STU-" + "4" * 32

#: (payload_id, kind, canonical_input, algorithm_version).  Includes the
#: non-default ``rag-chunk-identity-v1`` version the RAG kit really mints chunk
#: IDs with (AC-11 / NC-7) and the document-identity input shape the PDF kit
#: mints ``DOC-`` ids from (AC-11).
DETERMINISTIC_ID_CASES: list[tuple[str, str, dict[str, Any], str]] = [
    (
        "document_pdf",
        "document",
        {
            "media_type": "application/pdf",
            "source_sha256": _SOURCE_HASH,
            "study_id": _STUDY_ID,
        },
        "v1",
    ),
    (
        "chunk_rag",
        "chunk",
        {"document_id": "DOC-" + "3" * 32, "study_id": _STUDY_ID},
        "rag-chunk-identity-v1",
    ),
    ("workspace_v1", "workspace", {"label": "x"}, "v1"),
    ("study_v1", "study", {"doi": "10.1/x"}, "v1"),
    ("corpus_v1", "corpus", {"query": "q", "limit": 10}, "v1"),
]

#: (payload_id, kind, value, accepted, expected_exception_type|None).
VALIDATE_IDENTIFIER_CASES: list[tuple[str, str, Any, bool, str | None]] = [
    ("study_stu", "study", "STU-000001", True, None),
    ("study_legacy_sci", "study", "SCI-000001", True, None),
    ("audit_aud", "audit_event", "AUD-000001", True, None),
    ("audit_legacy_evt", "audit_event", "EVT-000001", True, None),
    ("artifact_dotted", "artifact", "ART-abc.def-01", True, None),
    (
        "chunk_wrong_prefix",
        "chunk",
        "DOC-075c0f35ab39286246e4465643fe20d8",
        False,
        "ValueError",
    ),
    (
        "chunk_lowercase",
        "chunk",
        "chk-ab10cb5729e20ff5dc8d26a93455010c",
        False,
        "ValueError",
    ),
    ("chunk_empty_suffix", "chunk", "CHK-", False, "ValueError"),
    ("study_non_string", "study", 12345, False, "TypeError"),
]

#: A shared corpus snapshot with deliberately unsorted study/record/id arrays so
#: the ``corpus_snapshot_fingerprint`` normalization is exercised (AC-12).
CORPUS_SNAPSHOT_PAYLOAD: dict[str, Any] = {
    "studies": [
        {
            "study_id": "STU-b",
            "source_record_ids": ["REC-2", "REC-1"],
            "alias_ids": ["SCI-b"],
            "external_ids": {"openalex": ["W-2", "W-1"]},
        },
        {
            "study_id": "STU-a",
            "source_record_ids": ["REC-1"],
            "alias_ids": [],
            "external_ids": {},
        },
    ],
    "record_to_study": {"REC-1": "STU-a", "REC-2": "STU-b"},
}


# --------------------------------------------------------------------------- #
# Golden builders (one per profile, computed by that profile's owner)
# --------------------------------------------------------------------------- #
def _case_entry(
    payload_id: str, payload: Any, set_like: tuple[str, ...]
) -> dict[str, Any]:
    """A contract-v1 case pinned from the HARNESS reference implementation."""

    return {
        "payload_id": payload_id,
        "payload": payload,
        "set_like_arrays": list(set_like),
        "expected_canonical_bytes": harness_canonical.canonical_json_bytes(
            payload, set_like_arrays=set_like
        ).decode("utf-8"),
        "expected_fingerprint": harness_canonical.canonical_fingerprint(
            payload, set_like_arrays=set_like
        ),
    }


def build_contract_v1_golden() -> dict[str, Any]:
    cases = [
        _case_entry(pid, payload, set_like) for pid, payload, set_like in CONTRACT_CASES
    ]
    rejections = [
        {
            "payload_id": pid,
            "builder": pid,
            "expected_exception_type": expected_type,
        }
        for pid, expected_type in REJECTION_CASES
    ]
    return {
        "profile": CONTRACT_PROFILE,
        "generator": GENERATOR_REL,
        "reference": "scholar_harness.contracts.canonical",
        "cases": cases,
        "rejections": rejections,
    }


def build_documents_list_ascii_golden() -> dict[str, Any]:
    # Owned by the search-kit serializer (ensure_ascii=True).
    return {
        "profile": DOCUMENTS_PROFILE,
        "generator": GENERATOR_REL,
        "reference": "scholar_search.canonical",
        "cases": [
            {
                "payload_id": "documents_unicode",
                "payload": DOCUMENTS_PAYLOAD,
                "expected_canonical_bytes": search_canonical_json(
                    DOCUMENTS_PAYLOAD
                ).decode("utf-8"),
                "expected_fingerprint": search_fingerprint(DOCUMENTS_PAYLOAD),
            }
        ],
    }


def build_protocol_declaration_order_golden() -> dict[str, Any]:
    model = ResearchProtocol.model_validate(PROTOCOL_PAYLOAD)
    return {
        "profile": PROTOCOL_PROFILE,
        "generator": GENERATOR_REL,
        "reference": "scholar_protocol.canonical",
        "cases": [
            {
                "payload_id": "protocol_baseline",
                "payload": PROTOCOL_PAYLOAD,
                "expected_canonical_bytes": protocol_canonical_json(model).decode(
                    "utf-8"
                ),
                "expected_fingerprint": protocol_fingerprint(model),
            }
        ],
    }


def build_identifier_registry_golden() -> dict[str, Any]:
    registry = harness_identifiers.identifier_registry()
    id_cases = [
        {
            "payload_id": pid,
            "kind": kind,
            "workspace_namespace": WORKSPACE_NAMESPACE,
            "input": canonical_input,
            "algorithm_version": algorithm_version,
            "expected_id": harness_canonical.deterministic_id(
                harness_identifiers.IdentifierKind(kind),
                WORKSPACE_NAMESPACE,
                canonical_input,
                algorithm_version=algorithm_version,
            ),
        }
        for pid, kind, canonical_input, algorithm_version in DETERMINISTIC_ID_CASES
    ]
    validate_cases = [
        {
            "payload_id": pid,
            "kind": kind,
            "value": value,
            "accepted": accepted,
            "expected_exception_type": expected_type,
        }
        for pid, kind, value, accepted, expected_type in VALIDATE_IDENTIFIER_CASES
    ]
    return {
        "profile": "identifier_registry",
        "generator": GENERATOR_REL,
        "reference": "scholar_harness.contracts.identifiers",
        "registry": registry,
        "deterministic_id_cases": id_cases,
        "validate_identifier_cases": validate_cases,
        "corpus_snapshot": {
            "payload": CORPUS_SNAPSHOT_PAYLOAD,
            "expected_fingerprint": harness_canonical.corpus_snapshot_fingerprint(
                CORPUS_SNAPSHOT_PAYLOAD
            ),
        },
    }


#: filename -> (builder, on-disk text).  Fixed order for deterministic writes.
def build_goldens() -> dict[str, dict[str, Any]]:
    return {
        "contract_v1_canonical.json": build_contract_v1_golden(),
        "documents_list_ascii.json": build_documents_list_ascii_golden(),
        "protocol_declaration_order.json": build_protocol_declaration_order_golden(),
        "identifier_registry.json": build_identifier_registry_golden(),
    }


def _render(obj: dict[str, Any]) -> str:
    # sort_keys=True gives the golden file a canonical key order; ensure_ascii
    # stays False so non-ASCII payloads are stored exactly as they serialize.
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _first_difference(expected: Any, actual: Any, path: str = "") -> str | None:
    """Return a human-readable ``file:field`` path to the first difference."""

    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            sub = f"{path}.{key}" if path else key
            if key not in expected:
                return f"{sub}: unexpected field"
            if key not in actual:
                return f"{sub}: missing field"
            diff = _first_difference(expected[key], actual[key], sub)
            if diff:
                return diff
        return None
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return f"{path}: length {len(expected)} != {len(actual)}"
        for index, (exp_item, act_item) in enumerate(zip(expected, actual)):
            # Name list entries by payload_id when available for readability.
            label = (
                exp_item.get("payload_id", index)
                if isinstance(exp_item, dict)
                else index
            )
            diff = _first_difference(exp_item, act_item, f"{path}[{label}]")
            if diff:
                return diff
        return None
    if expected != actual:
        return f"{path}: {expected!r} != {actual!r}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    goldens = build_goldens()
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    if args.check:
        out_of_sync: list[str] = []
        for name, obj in goldens.items():
            path = FIXTURE_DIR / name
            expected_text = _render(obj)
            if not path.is_file():
                out_of_sync.append(f"{name}: missing (run the generator to create it)")
                continue
            actual_text = path.read_text(encoding="utf-8")
            if actual_text != expected_text:
                detail = _first_difference(
                    json.loads(expected_text), json.loads(actual_text), name
                )
                out_of_sync.append(detail or f"{name}: content differs")
        if out_of_sync:
            print("Canonical profile goldens out of sync:")
            for line in out_of_sync:
                print(f"  - {line}")
            return 1
        print(
            f"[OK] {len(goldens)} canonical profile goldens in sync under {FIXTURE_DIR.relative_to(ROOT).as_posix()}/"
        )
        return 0

    for name, obj in goldens.items():
        (FIXTURE_DIR / name).write_text(_render(obj), encoding="utf-8", newline="\n")
        print(f"Wrote {(FIXTURE_DIR / name).relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
