# Canonical profile parity pin (T-SC1)

**Packet:** `docs/architecture/packet_t_sc1_canonical_profile_parity_2026-10-21.md`
**Gate:** `tests/conformance/test_canonical_profile_parity.py`
**Goldens:** `tests/fixtures/canonical_profiles/`
**Generator:** `scripts/generate_canonical_profile_goldens.py` (`--check`)

## Why this exists

The canonicalization and identifier primitives are **restated** in several places so the
kits stay standalone-buildable: a kit must not import the harness, not even at import time.
Restatement without a cross-repo pin is an unpinned obligation — the RAG kit's own module
docstring says the harness conformance test that pins it "does not exist yet". This packet
**is** that pin. It is Phase 1 of the "shared core" program: it *pins* the frozen primitives
so a future divergence fails a test instead of silently moving an identity. It does **not**
create a `scholar_core` package and does **not** move any implementation.

## The three profiles

| Profile | Owner (reference) | Restated by | Serialization |
|---|---|---|---|
| `contract_v1_canonical` | `scholar_harness.contracts.canonical` | `scholar_rag.canonical`, `scholar_pdf.canonical` | `ensure_ascii=False`, `sort_keys=True`, compact separators, integral floats → ints, `-0.0` → `0`, NaN/inf/non-string-keys/unsupported-types **rejected** |
| `documents_list_ascii` | `scholar_search.canonical` | — | a **list of documents**; `ensure_ascii=True` (escapes non-ASCII), `default=str` (coerces), `sort_keys=True` |
| `protocol_declaration_order` | `scholar_protocol.canonical` | — | a Pydantic `ResearchProtocol`; `sort_keys=False` (**declaration order** preserved), `ensure_ascii=True`, nested `metadata`/`date_range`/`target_candidate_pool_size` sorted, trust threshold forced to float |

The two non-contract profiles are **provably distinct** from the contract profile and are
never coerced into it (decision D-3: *assert distinctness, never normalize*). Normalizing
them would move existing search-kit and protocol-kit fingerprints — a contract change, which
`CONTRACT_VERSION == 1.0.0` forbids. The gate proves:

- `documents_list_ascii` ≠ `contract_v1_canonical` on the unicode payload (different bytes:
  escaped vs raw UTF-8; different fingerprint);
- `protocol_declaration_order` ≠ a key-sorted serialization of the same model (declaration
  order is preserved).

## What is pinned

- **Contract-v1 bytes + fingerprints** across harness ≡ rag-kit ≡ pdf-kit over a frozen
  payload set (two distinct non-ASCII strings — one carrying the **precomposed** acute
  U+00E9, one carrying the **genuine combining sequence** `e` + U+0301 that NFC would
  recompose — each with CJK and an emoji, so Unicode normalization drift in a kit is
  caught instead of passing as a no-op; integral float, `-0.0`, empty dict & list, deep
  nesting, large integer, numeric-looking string, a key-order-permuted pair → identical
  bytes, an array-order-permuted pair → different bytes).
- **Rejection parity** (`NaN`, `Infinity`, non-string key, unsupported type): all three
  implementations raise the **same exception type**, and a kit that *accepts* a rejected
  payload is a failure (G6).
- **Identifier registry**: harness `IdentifierKind`/`ID_PREFIXES` ≡ rag-kit's restated
  registry (same kind set, same prefix tuples in the same order, same mint prefix), and
  `validate_identifier` accepts/rejects the same strings.
- **Identity-minting formulas**: harness `deterministic_id` ≡ rag-kit `deterministic_id`
  for the same `(kind, namespace, input, version)` — **including** the non-default
  `algorithm_version="rag-chunk-identity-v1"` the RAG kit really mints chunk ids with; and
  harness `deterministic_id(DOCUMENT, …)` ≡ pdf-kit `deterministic_document_id(…)`.
- **Corpus fingerprint**: harness `corpus_snapshot_fingerprint` ≡ pdf-kit
  `corpus_snapshot_fingerprint`, order-insensitive over studies/source-record ids/alias ids/
  external-id values and over the `record_to_study` mapping.

## What is NOT pinned (kit-specific extensions)

The PDF kit's kit-owned identity helpers are **out of scope** here — they have no harness
equivalent and are not part of the cross-kit contract surface:

- `deterministic_acquisition_manifest_id` (`ACQ-*`)
- `deterministic_extraction_manifest_id` (`EXT-*`) and `extraction_identity_payload`
- `document_identity_payload` / `source_sha256` (the `DOC-` *formula* is pinned above via
  `deterministic_document_id`; the payload-builder helper itself is not)

These may evolve in the PDF kit's own repo without moving a Contract v1 identity. The pin
covers only the primitives that must agree across the harness and every kit.

## How drift is reported

Expected bytes come from each profile's **own reference implementation** (the contract
profile's from the harness), never from a different profile's serializer, so a kit cannot be
baked into a golden to force a green. If any kit has drifted, the parity test fails with the
exact payload id; per **G5** the correct action is to stop and report `BLOCKED_KIT_DRIFT`
with the payload, both byte strings, and both fingerprints — **not** to fix kit code inside
this packet and **not** to regenerate a golden to make the failure disappear (that would be
a contract change). Goldens are generated by the deterministic generator and verified by
`--check`; a hand-edited golden is a failing condition.

## Gate manifest mapping

The manifest task id is **`T-230`**, not `T-SC1`. `docs/architecture/test_gate_manifest.json`
and `scripts/select_test_gate.py` order tasks with `int(value.split("-")[1])`, so a
non-numeric suffix (`SC1`) raises `ValueError`; `T-SC1` remains the packet name only. The
`T-230` entry maps `repo: "harness"` and selects on the four new paths:

- `scripts/generate_canonical_profile_goldens.py`
- `tests/conformance/test_canonical_profile_parity.py`
- `tests/fixtures/canonical_profiles/**`
- `docs/architecture/canonical_profile_parity.md`

Teaching the selector to tolerate non-numeric ids is a separate follow-up (packet §17) and is
**out of scope** here.

## Phase-2 decision gate

Phase 2 (`scholar_core` extraction) is **not** authorized by this packet. It becomes worth
considering only if this Phase-1 gate shows **actual measured drift**, or if a second
consumer of the primitives appears. As of this packet the three contract-v1 implementations
are byte-identical over the golden set (no drift measured), so the recommendation is to keep
the restatement + pin (option A in the packet §15) until drift is measured. If drift later
appears, that is a **contract-level incident** (identities would have moved), not a refactor
trigger, and it must be handled as such via a separate kit-side packet with its own
three-invariant plan.
