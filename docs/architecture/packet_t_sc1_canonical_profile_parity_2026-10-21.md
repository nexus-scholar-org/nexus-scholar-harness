# Packet T-SC1 — Cross-kit canonical & identifier parity pin

**Status:** dispatched and implemented (PR #144). The orchestrator recorded the dispatch-time baseline in §4.5; all 19 AC clauses and G1-G9 carry executable evidence, and the P2 combining-coverage defect was repaired before landing.
**Date:** 2026-10-21. **Delivery lane:** `RELEASE` (identity + cross-kit → always RELEASE per
`docs/architecture/DEVELOPER_COMPASS.md` §7).
**Predecessor:** none required (harness-only, measure-only). **Sibling in flight:** `T-K0`
(landed as PR #139) — this packet does **not** touch the search-kit tree.

> **Scope note.** This is **Phase 1** of the "shared core" program, not the merge. It does not
> create a `scholar_core` package and does not move any implementation. It *pins* the frozen
> primitives so that any future divergence fails a test instead of silently changing a
> fingerprint. Phase 2 (`scholar_core` extraction) is gated on measured drift — see §15.

---

## 1. TASK_ID

`T-SC1` (packet/document name) — **manifest task id: `T-230`**.

`docs/architecture/test_gate_manifest.json` and `scripts/select_test_gate.py:75,167` order
tasks with `int(value.split("-")[1])`, so a non-numeric suffix (`SC1`) raises
`ValueError: invalid literal for int() with base 10: 'SC1'`. The manifest therefore carries
`T-230`; `T-SC1` remains the packet name. Teaching the selector to tolerate non-numeric ids
is a separate follow-up (§17) and is **out of scope** here.

---

## 2. OBJECTIVE

Make the **canonicalization and identifier primitives** shared across the harness and the kits
**provably identical (or provably deliberately different)**, and freeze that fact as an
executable gate.

Concretely, four things must be true at the end:

1. The **contract-v1 canonical profile** — the algorithm implemented four times — is proven
   **byte-identical** across `scholar_harness.contracts.canonical`,
   `scholar_rag.canonical`, and `scholar_pdf.canonical` over a frozen golden payload set,
   including **rejection behaviour** (not only success bytes).
2. The two **non-contract profiles** (`scholar_search` documents-list, `scholar_protocol`
   declaration-order) are **explicitly declared as distinct**, with their own goldens, and a
   test asserts they are **not interchangeable** with the contract-v1 profile (no silent
   coercion).
3. The **identifier registry and identity-minting formulas** are proven equivalent:
   `scholar_harness.contracts.identifiers` ↔ `scholar_rag.canonical` (restated copy), and
   `scholar_harness.contracts.canonical.deterministic_id` ↔
   `scholar_pdf.canonical.deterministic_document_id` / `corpus_snapshot_fingerprint`.
4. A **drift detector** exists: if any kit changes its canonical semantics, the harness
   conformance suite fails until the golden is deliberately updated and reviewed.

**What this packet is NOT:** not a merge, not a new package, not a kit source change, not a
contract version change, not a pin bump.

---

## 3. OWNER_SURFACE

**Harness repository only** (`nexus-scholar-org/nexus-scholar-harness`).

No canonical toolkit repository is in scope. This is deliberate: the packet is
**measure-only**, so it can run without a kit PR, without a `plugins.json` bump, and without a
vendored re-sync — which is what makes it dependency-safe while other kit work is in flight.

---

## 4. DEPENDENCIES_AND_EVIDENCE

### 4.1 The duplication this pins (verified by reading the sources, 2026-10-21)

| Implementation | Path | Profile | Notes |
|---|---|---|---|
| Harness | `src/scholar_harness/contracts/canonical.py` | `contract_v1_canonical` | normative reference: `canonical_json_bytes`, `canonical_fingerprint`, `corpus_snapshot_fingerprint`, `deterministic_id`, `normalize_doi` |
| RAG kit | `tools/scholar-rag-kit/src/scholar_rag/canonical.py` | `contract_v1_canonical` | restates the harness algorithm **and** the identifier registry (`IdentifierKind`, `ID_PREFIXES`, `primary_prefix`, `validate_identifier`, `deterministic_id`) |
| PDF kit | `tools/scholar-pdf-kit/src/scholar_pdf/canonical.py` | `contract_v1_canonical` | restates the harness algorithm; adds kit-specific identity helpers (`deterministic_document_id`, `deterministic_acquisition_manifest_id`, `extraction_identity_payload`, …) |
| Search kit | `tools/scholar-search-kit/src/scholar_search/canonical.py` | `documents_list_ascii` | **different**: `ensure_ascii=True`, `default=str`, list-of-documents only |
| Protocol kit | `tools/scholar-protocol-kit/src/scholar_protocol/canonical.py` | `protocol_declaration_order` | **different**: `sort_keys=False`, Pydantic declaration order, `ensure_ascii=True` |

### 4.2 The pin that does not exist yet (the actual debt)

`tools/scholar-rag-kit/src/scholar_rag/canonical.py:1-25` (its own module docstring) states:

> *"The harness-side conformance test that will pin this module against the shared golden
> payloads is **pending** - it is scheduled at WP01-E3-T-120/T-140 and **does not exist yet**,
> so nothing in the harness repo checks this file as of this commit. … its literals were
> derived by executing `scholar_harness.contracts.canonical` and
> `scholar_harness.contracts.identifiers` at harness commit `d15a0108` and are replayed
> offline, so the check is available with no harness dependency. When the harness conformance
> test arrives it must reproduce these same bytes."*

The same restatement pattern appears in `tools/scholar-pdf-kit/src/scholar_pdf/canonical.py:1-9`.

**Therefore: today, four independent implementations of a frozen identity algorithm exist,
and only the RAG kit's own offline golden battery checks any of them.** The duplication is
intentional (the kits must stay standalone-buildable and must not import the harness), but
the *absence of a cross-repo conformance pin* is an unpinned obligation, not a style choice.

### 4.3 Repository state at drafting time

| Fact | Value | Verified by |
|---|---|---|
| Harness HEAD at drafting | `5dde06c` (PR #140 truth-counts merged; PR #139 K0 search-kit pin landing merged) | `git log --oneline -5` |
| Search-kit pin | `d20292a410a4aaa278fa9ffef8021b949a3218c3` | `plugins.json` |
| All four baseline checks | **exit 0** | `generate_contract_baseline.py --check`, `generate_contract_schemas.py --check`, `generate_two_study_contract_fixture.py --check`, `generate_nexus_scholar_pins.py --check` |
| RAG kit canonical suite | **114 passed** | `uv run --directory tools/scholar-rag-kit --extra dev pytest tests/test_canonical.py -q` |
| Kit pytest invocation | `uv run --directory tools/<kit> --extra dev pytest -q` (plain `uv run --directory` does **not** provide pytest) | kit CI workflow + local run |
| Harness pytest imports kits | `pyproject.toml` `pythonpath` includes `tools/*/src` | `pyproject.toml`; precedent in `tests/conformance/test_e3_index_lineage_boundary.py` (imports `scholar_rag.canonical`, `scholar_protocol.canonical`) |
| PDF kit canonical coverage | **no** `tests/test_canonical.py` in `tools/scholar-pdf-kit/tests/` | directory listing |

### 4.4 Concurrency caveat (binding)

**The working tree moved during drafting** (`c10d281` → `5dde06c` → `c2b1ed2`; PRs #139, #140,
#141 landed). Another actor is committing in this repository concurrently.

**Binding requirement:** the implementer must re-run `git status -sb` and `git log -3` at
dispatch start, re-record the dirty baseline, and **re-verify §4.3** (baseline checks exit 0)
before writing any file. If the baseline checks are red, stop and report
`BLOCKED_BASELINE_DRIFT`.

### 4.5 Dispatch-time baseline actually observed (2026-10-22)

Recorded by the first dispatch attempt, which stopped before writing anything:

| Fact | Value |
|---|---|
| HEAD | `c2b1ed2` (Merge PR #141) |
| Dirty entries | **25**: 1 modified (`.opencode/agent/reviewer.md`), 22 staged `A` under `workspaces/uav-pilot-demo/`, 2 untracked (this packet, `workspaces/uav-crop-weed-v03/`) |
| `git status --short tools/` | empty |
| `generate_contract_baseline.py --check` | **exit 1 — `Contract baseline drifted`** |
| other three baseline checks | exit 0 |
| RAG kit canonical suite | 114 passed |

**Root cause of the red baseline (verified independently):** `docs/architecture/contract_v1_baseline.json`
records the **HEAD** blob for `.opencode/agent/reviewer.md` (`80077d4b…`). The working-tree copy
is a **pre-existing, uncommitted edit by another actor** whose diff collapses

```yaml
permission:
  read: allow
  glob: allow
  grep: allow
  list: allow
  edit: deny
  bash: ask
```

to `permission: allow`. So this is *not* contract drift; it is uncommitted concurrent work.
It is still a hard stop: regenerating the baseline would (a) absorb another actor's change and
(b) bless a removal of the reviewer's `edit: deny` guard, which is the doer/critic
independence gate.

**Precondition to resume:** the owner must resolve that edit (revert it, or commit it together
with a regenerated baseline as an explicit, reviewed decision) so that
`generate_contract_baseline.py --check` exits 0. **This packet must not do either.**

### 4.6 Packet corrections made after the first dispatch attempt

1. **Manifest id is `T-230`, not `T-SC1`** — `scripts/select_test_gate.py:75,167` sorts with
   `int(value.split("-")[1])` (`int("SC1")` → `ValueError`). See §1.
2. **`tests/unit/test_select_test_gate.py` is now in ALLOWED_PATHS** — its
   `test_manifest_is_valid_and_covers_every_e3_task` asserts the manifest task set *exactly*,
   so any new entry fails it. Extending that set is part of this packet; weakening the
   assertion is not.
3. **Packet §7's dirty list is stale** — `docs/README.md`, `docs/architecture/README.md`,
   `AGENTS.md`, `apps/research-ui/AGENTS.md`, `.github/workflows/ci.yml` and the
   screening-decision-contract files landed in PRs #139-#141. Use the §4.5 snapshot instead.
4. **Profile-distinctness is not total.** A pure-ASCII `list[dict]` serializes identically
   under `documents_list_ascii` and `contract_v1_canonical` (both compact + sorted keys). AC-9's
   "except where defined to agree" is load-bearing: the implementation must enumerate the
   exact expected agreement set and assert observed agreement **equals** it. Divergence points
   to pin: `ensure_ascii=True` (search/protocol), `default=str` (search), `sort_keys=False` +
   declaration order + `5.0` retained (protocol), `5.0→5` and `-0.0→0` (contract).

---

## 5. GOVERNING_REQUIREMENTS

**G1 — Measure only.** Harness-only. No file under `tools/**` may be created, edited, or
deleted by this packet. Kits are **imported and executed**, never modified.

**G2 — No contract change.** `CONTRACT_VERSION` stays `1.0.0`. No schema, golden fixture,
or baseline regeneration is permitted. `docs/architecture/contract_v1_baseline.json` and the
frozen contract models are read-only.

**G3 — Profiles are declared, never coerced.** Three profiles are named explicitly in the
goldens file (`contract_v1_canonical`, `documents_list_ascii`,
`protocol_declaration_order`). The parity test must assert that the two non-contract profiles
are **distinct** from the contract-v1 profile on a payload where they provably differ, and
must assert that **no code path routes one profile's bytes through another profile's
serializer**. A legacy/custom profile is detected and reported, never silently normalized.

**G4 — Goldens are frozen literals.** The golden file is a committed, reviewable artifact of
expected bytes/fingerprints. It is produced by a deterministic generator and verified by
`--check`; **hand-editing it is a failing condition**, not a shortcut. Regeneration is an
explicit, reviewed act (same discipline as `generate_contract_baseline.py`).

**G5 — Fail closed on drift.** If any kit implementation fails parity, the implementer
**stops and reports `BLOCKED_KIT_DRIFT`** with the exact payload, both byte strings, and both
fingerprints. The implementer **must not** fix kit code inside this packet (that would
require a kit PR under the three-invariant rule) and **must not** regenerate the golden to
make the failure disappear.

**G6 — Rejection parity, not only success parity.** Parity covers the *failure* behaviour
too: which inputs are rejected, with which exception type, and that rejections are not
coerced into success. A kit that accepts a payload the harness rejects is a parity failure.

**G7 — Determinism and order rules.** The golden payload set must include a pair of payloads
that differ only by key order (identical bytes expected) and a pair that differ only by array
order (different bytes expected for order-significant arrays). The generator is run twice and
must produce identical output.

**G8 — Lineage and provenance unchanged.** No artifact semantics, schema, fingerprint
spelling (`sha256:<hex>`), identifier prefix, or provenance field changes. This packet
**characterizes**; it does not alter any produced artifact.

**G9 — RELEASE-lane gates.** Identity + cross-kit work is `RELEASE` (`DEVELOPER_COMPASS.md` §7):
full owning-repo suite, all four baseline checks, and the kit suites whose modules are
imported.

---

## 6. ALLOWED_PATHS

```
scripts/generate_canonical_profile_goldens.py                  (new)
tests/fixtures/canonical_profiles/contract_v1_canonical.json    (new, frozen golden)
tests/fixtures/canonical_profiles/documents_list_ascii.json      (new, frozen golden)
tests/fixtures/canonical_profiles/protocol_declaration_order.json (new, frozen golden)
tests/fixtures/canonical_profiles/identifier_registry.json       (new, frozen golden)
tests/conformance/test_canonical_profile_parity.py              (new)
tests/unit/test_select_test_gate.py                              (extend the task-id set only)
docs/architecture/canonical_profile_parity.md                   (new, short record)
docs/architecture/test_gate_manifest.json                        (add T-230 mapping only)
docs/architecture/packet_t_sc1_canonical_profile_parity_2026-10-21.md  (this file)
```

---

## 7. FORBIDDEN_PATHS

```
src/scholar_harness/contracts/**            frozen Contract v1 — read only
src/scholar_harness/**                       (outside the new test/script/fixture files)
tools/**                                     no kit source change (G1)
.agents/plugins/nexus-scholar/plugins.json   no pin change
packaging/nexus-scholar/**                   no metapackage change
workspaces/**                                read-only; write nothing
apps/**                                      no UI change
.github/workflows/**                         no CI change
.opencode/agent/**                           no agent-permission change
scripts/select_test_gate.py                  no selector change (numeric id avoids it)
scripts/push_tools.py                        not used, not modified
docs/architecture/contract_v1_baseline.json  frozen
docs/architecture/contract_v1_baseline.md    frozen
docs/architecture/DEVELOPER_COMPASS.md       frozen
```

**Pre-existing dirty / untracked files that must not be modified, absorbed, or deleted**
(re-record at dispatch start — see §4.4):

```
.github/workflows/ci.yml
AGENTS.md
apps/research-ui/AGENTS.md
docs/README.md
docs/architecture/README.md
docs/architecture/context_efficiency_policy.md          (untracked)
docs/architecture/open_work_triage_2026-10-20.md        (untracked)
docs/architecture/packet_d0_d2_decision_contract_reader_2026-10-20.md  (untracked)
docs/architecture/packets_from_uav_demo_2026-10-19.md   (untracked)
docs/lessons/                                          (untracked)
scripts/check_context_policy.py                         (untracked)
src/scholar_harness/screening/decision_contract.py      (untracked)
tests/fixtures/screening_decision_contract/             (untracked)
tests/test_screening_decision_contract.py               (untracked)
tests/unit/test_context_policy.py                       (untracked)
workspaces/uav-pilot-demo/**                            (staged)
workspaces/uav-crop-weed-v03/**                         (untracked)
```

`docs/README.md` and `docs/architecture/README.md` are **already modified by another actor** —
this packet does **not** add index entries to them (a separate follow-up may, after the
in-flight edits land).

---

## 8. INPUTS

| Path | Use |
|---|---|
| `src/scholar_harness/contracts/canonical.py` | Normative reference implementation (profile `contract_v1_canonical`). |
| `src/scholar_harness/contracts/identifiers.py` | Normative identifier registry (`IdentifierKind`, `ID_PREFIXES`, `primary_prefix`, `validate_identifier`, `identifier_registry`). |
| `tools/scholar-rag-kit/src/scholar_rag/canonical.py` | Restated contract-v1 profile **+** restated identifier registry. |
| `tools/scholar-pdf-kit/src/scholar_pdf/canonical.py` | Restated contract-v1 profile **+** kit identity helpers. |
| `tools/scholar-search-kit/src/scholar_search/canonical.py` | Profile `documents_list_ascii` (documents list). |
| `tools/scholar-protocol-kit/src/scholar_protocol/canonical.py` | Profile `protocol_declaration_order` (Pydantic model). |
| `tools/scholar-rag-kit/tests/test_canonical.py` | Existing kit golden battery (114 tests) — the payload style to imitate; must not regress. |
| `tools/scholar-search-kit/tests/test_canonical.py` | Existing kit golden battery — same. |
| `tools/scholar-protocol-kit/tests/test_canonical.py` | Existing kit golden battery — same. |
| `tests/conformance/test_e3_index_lineage_boundary.py` | Precedent: a harness conformance test importing kit modules (`scholar_rag.canonical`, `scholar_protocol.canonical`). |
| `scripts/generate_contract_baseline.py`, `scripts/generate_nexus_scholar_pins.py` | Pattern to imitate for a deterministic generator with `--check`. |
| `docs/architecture/test_gate_manifest.json` | Machine-readable gate mapping; add `T-SC1`. |
| `docs/architecture/DEVELOPER_COMPASS.md` §3, §7, §8 | Identity invariants, lane selection, toolkit-sync rule. |
| `docs/architecture/packet_k0_search_kit_landing_2026-10-20.md` | Precedent packet shape (this packet deliberately mirrors its section structure). |

---

## 9. OUTPUTS

1. **`scripts/generate_canonical_profile_goldens.py`** — deterministic generator with
   `--check` mode. Emits the four golden JSON files from the reference implementation of each
   profile over a frozen payload list. Running it twice must produce byte-identical files.
2. **Four frozen golden files** under `tests/fixtures/canonical_profiles/` containing, per
   profile: the payload id, the payload, the **expected canonical bytes** (as a JSON string,
   exact), the **expected fingerprint** (`sha256:<hex>`), and for rejection cases the
   **expected exception type**. No timestamps, no absolute paths, no environment data.
3. **`tests/conformance/test_canonical_profile_parity.py`** — the executable gate:
   - profile `contract_v1_canonical`: harness ≡ rag-kit ≡ pdf-kit, byte-identical bytes and
     identical fingerprints, for **every** payload in the golden set;
   - rejection parity: for each rejection case, all three raise the **same exception type**
     (message text is compared case-insensitively by class, not literally);
   - profile `documents_list_ascii`: search-kit ≡ its golden; and **asserted distinct** from
     the contract-v1 profile on the unicode payload (proving the two serializers are not
     interchangeable);
   - profile `protocol_declaration_order`: protocol-kit ≡ its golden; and **asserted distinct**
     from a key-sorted serialization of the same model (proving declaration order is
     preserved);
   - identifier parity: harness registry ≡ rag-kit registry (same kind set, same prefix
     tuples, same mint prefix, same accept/reject behaviour for the same strings);
   - identity-minting parity: harness `deterministic_id(DOCUMENT, ws, input, "v1")` ≡
     pdf-kit `deterministic_document_id(study_id=…, source_hash=…, workspace_id=…)` for the
     same inputs; harness `corpus_snapshot_fingerprint` ≡ pdf-kit
     `corpus_snapshot_fingerprint`; harness `deterministic_id` ≡ rag-kit `deterministic_id`
     **including the non-default `algorithm_version="rag-chunk-identity-v1"`** that the RAG
     kit actually mints chunk IDs with;
   - determinism: repeated calls return identical bytes; key-order-permuted payloads agree;
     array-order-permuted payloads differ where order is semantic.
4. **`docs/architecture/canonical_profile_parity.md`** — one page recording: the three
   profiles, why the kits restate instead of importing, what is now pinned, what is **not**
   pinned (kit-specific extensions such as `deterministic_acquisition_manifest_id`), and the
   Phase-2 decision gate.
5. **`docs/architecture/test_gate_manifest.json`** — a **`T-230`** entry mapping
   `repo: "harness"`, the four new paths, and `inner` / `checkpoint` / `pr` / `closure`
   command lists (numeric suffix required; see §1).
6. **`tests/unit/test_select_test_gate.py`** — extend the exhaustive task-id guard
   (`test_manifest_is_valid_and_covers_every_e3_task`, lines 15-20) to include `T-230`.
   This is required, not optional: the guard asserts the manifest's task set **exactly**, so
   any new entry fails it today. Extend the set only; do not weaken or remove the assertion,
   and do not touch the selector itself.
6. **Validation evidence** for every command in §11, quoted verbatim.

---

## 10. ACCEPTANCE_CRITERIA

| ID | Criterion |
|---|---|
| AC-1 | `uv run python scripts/generate_canonical_profile_goldens.py --check` exits 0 and prints `[OK]`; the goldens are **in sync** with the reference implementations. |
| AC-2 | Running the generator twice produces **byte-identical** golden files (verified by hashing before/after a second run). |
| AC-3 | The golden files contain **no** timestamp, absolute path, hostname, or environment-derived value (a grep assertion covers it). |
| AC-4 | For every payload in the `contract_v1_canonical` golden set, `scholar_harness.contracts.canonical`, `scholar_rag.canonical`, and `scholar_pdf.canonical` return **byte-identical** canonical bytes and **identical** fingerprints. |
| AC-5 | The payload set covers, at minimum: non-ASCII text (combining + CJK + emoji), an integral float (`5.0`), `-0.0`, a nested empty dict and empty list, a deeply nested structure, a large integer, a numeric-looking string, key-order permutations of one payload, and array-order permutations of another. |
| AC-6 | Rejection parity: for each rejection case (`NaN`, `Infinity`, non-string object key, unsupported type), harness, rag-kit, and pdf-kit raise the **same exception type**; a kit that accepts a rejected payload fails the test. |
| AC-7 | The `documents_list_ascii` profile is asserted **distinct** from `contract_v1_canonical` on the unicode payload (different bytes, different fingerprint), and the test names which profile each implementation belongs to. |
| AC-8 | The `protocol_declaration_order` profile is asserted **distinct** from a key-sorted serialization of the same model, and the protocol-kit golden matches its own profile. |
| AC-9 | No implementation is routed through another profile's serializer: the parity test contains an explicit assertion that the profile registry maps each implementation to exactly one profile, and that no profile's expected bytes equal another profile's expected bytes for the shared payloads (except where the profiles are *defined* to agree, which must be enumerated and justified in the record). |
| AC-10 | Identifier parity: harness `IdentifierKind`/`ID_PREFIXES` and rag-kit's restated registry have the same kind set, the same prefix tuples in the same order, and the same `primary_prefix`; `validate_identifier` accepts and rejects the same strings in both. |
| AC-11 | Identity parity: harness `deterministic_id` ≡ rag-kit `deterministic_id` for the same `(kind, workspace_namespace, canonical_input, algorithm_version)` — **including** `algorithm_version="rag-chunk-identity-v1"` — and harness `deterministic_id(DOCUMENT, …)` ≡ pdf-kit `deterministic_document_id(…)` for the same inputs. |
| AC-12 | Corpus fingerprint parity: harness `corpus_snapshot_fingerprint` ≡ pdf-kit `corpus_snapshot_fingerprint` for the shared corpus payload, including the `record_to_study` mapping. |
| AC-13 | Existing kit golden batteries do not regress: `uv run --directory tools/scholar-rag-kit --extra dev pytest tests/test_canonical.py -q` → 114 passed (or more); search-kit and protocol-kit canonical suites green. |
| AC-14 | `uv run pytest tests/conformance/test_canonical_profile_parity.py -q` is green, and the harness suite `uv run pytest -q` shows **no decrease** in the passed-test count versus the recorded baseline. |
| AC-15 | All four baseline checks remain green (exit 0 each): `generate_contract_baseline.py --check`, `generate_contract_schemas.py --check`, `generate_two_study_contract_fixture.py --check`, `generate_nexus_scholar_pins.py --check`. **No generated file was modified.** |
| AC-16 | `uv run ruff check scripts/` passes, and `uv run ruff check tests/conformance/test_canonical_profile_parity.py scripts/generate_canonical_profile_goldens.py` reports no new findings. |
| AC-17 | `git status --short` shows **no** modification under `tools/**`, `src/scholar_harness/contracts/**`, `.agents/plugins/nexus-scholar/plugins.json`, or `packaging/nexus-scholar/**`. |
| AC-18 | `docs/architecture/canonical_profile_parity.md` states the three profiles, the pinned surface, the explicitly **unpinned** kit-specific extensions, and the Phase-2 decision gate — with no claim stronger than the tests demonstrate. |
| AC-19 | The implementer reports the §9 outputs, the exact command output, and the dirty-tree baseline observed at dispatch start; no pre-existing dirty file was modified or absorbed. |
| AC-20 | The manifest entry is `T-230` and resolves: `uv run python scripts/select_test_gate.py --check` → `OK`, `uv run python scripts/select_test_gate.py --task T-230 --stage inner` prints the expected commands, and `uv run python scripts/select_test_gate.py --path tests/conformance/test_canonical_profile_parity.py --stage pr` resolves without a `ValueError`. `scripts/select_test_gate.py` is **unmodified**. |
| AC-21 | `uv run pytest tests/unit/test_select_test_gate.py -q` passes, and `git diff tests/unit/test_select_test_gate.py` shows only the added `T-230` member — no assertion weakened, no existing entry removed. |

---

## 11. NEGATIVE_CASES

The parity gate must be shown to **fail** under each of these; each needs an executable
control (a mutation-style test or a documented temporary mutation that is reverted).

| ID | Negative case | Expected failure |
|---|---|---|
| NC-1 | A kit flips `ensure_ascii` (e.g. rag-kit to `True`). | The contract-v1 parity test fails on the unicode payload, with both byte strings printed. |
| NC-2 | A kit adds an identifier kind or changes a prefix (e.g. `STU-` → `STU2-`). | The registry parity test fails, naming the differing kind. |
| NC-3 | A kit starts coercing a rejected input (e.g. `default=str` in the contract-v1 profile). | The rejection-parity test fails with the accepted-vs-rejected mismatch. |
| NC-4 | A golden file is hand-edited (one expected byte changed). | `generate_canonical_profile_goldens.py --check` fails and names the file and field. |
| NC-5 | The generator is run twice with a non-deterministic payload ordering. | The two runs differ → AC-2 fails; the generator must sort deterministically. |
| NC-6 | A kit implementation is mistakenly routed through another profile's serializer (e.g. search-kit output compared to the contract-v1 golden). | The profile-distinctness assertion fails; the test must not silently accept a coerced profile. |
| NC-7 | The harness `deterministic_id` is restricted to `algorithm_version == "v1"` (the version-pinning regression the RAG kit docstring warns about). | The identity-parity test fails on the `rag-chunk-identity-v1` case. |
| NC-8 | A payload's array order is changed for an order-significant array. | The order-sensitivity assertion fails (bytes differ) — order must not be silently normalized. |
| NC-9 | An implementation is changed so that a rejected payload raises a *different* exception type (e.g. `ValueError` instead of `TypeError`). | The rejection-type parity test fails. |
| NC-10 | A kit file is edited during this packet. | `git status --short tools/` shows it; AC-17 fails and the implementer must revert and report. |

---

## 12. VALIDATION_COMMANDS

```powershell
# --- inner (during implementation) ---
uv run pytest tests/conformance/test_canonical_profile_parity.py -q
uv run python scripts/generate_canonical_profile_goldens.py --check
uv run --directory tools/scholar-rag-kit --extra dev pytest tests/test_canonical.py -q

# --- checkpoint (boundary) ---
uv run pytest tests/conformance -q
uv run python scripts/generate_canonical_profile_goldens.py          # regenerate deliberately, then --check
uv run python scripts/generate_canonical_profile_goldens.py --check

# --- pr (owning-repo suite, once) ---
uv run pytest -q
uv run ruff check scripts/
uv run ruff check tests/conformance/test_canonical_profile_parity.py scripts/generate_canonical_profile_goldens.py

# --- closure (RELEASE lane: baseline + imported kit suites) ---
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
uv run --directory tools/scholar-rag-kit --extra dev pytest -q
uv run --directory tools/scholar-search-kit --extra dev pytest -q
uv run --directory tools/scholar-protocol-kit --extra dev pytest -q
uv run --directory tools/scholar-pdf-kit --extra dev pytest -q

# --- scope proof ---
git status --short tools/ src/scholar_harness/contracts/ .agents/plugins/nexus-scholar/plugins.json packaging/nexus-scholar/
```

**Note on kit pytest:** `uv run --directory tools/<kit> pytest` **fails** (`pytest` not spawned);
the `dev` extra is required: `uv run --directory tools/<kit> --extra dev pytest -q`.

---

## 13. TOOLKIT_SYNC_AND_PIN_PLAN

**No toolkit sync is required, and none may be performed by this packet.**

| Invariant | Status |
|---|---|
| Canonical kit repo change | **None** — no file under `tools/**` is written. |
| `plugins.json` `default_rev` bump | **None** — no kit source changed, so no pin may move. |
| Vendored `tools/<kit>/` re-sync | **None.** |
| `nexus_scholar_pins.json` regeneration | **None** — `generate_nexus_scholar_pins.py --check` must stay green untouched. |
| Fork + PR | **None.** |

If parity fails and the drift is genuinely in a kit, the correct action is:

1. **Stop.** Report `BLOCKED_KIT_DRIFT` with the payload, both byte strings, both fingerprints,
   and the exact source lines that diverge.
2. Open a **separate kit-side packet** with its own three-invariant plan (fork branch → PR →
   canonical merge → `plugins.json` bump → vendored re-sync → pins regeneration), per
   `AGENTS.md` and `DEVELOPER_COMPASS.md` §8.
3. Do **not** regenerate the golden to silence the failure, and do **not** edit the vendored
   copy.

---

## 14. WORKSPACE_AUDIT_EVENT

**None.** This packet mutates no workspace under `workspaces/`, produces no artifact, and
changes no scientific state. The repository-level record is the PR, the golden diff, and the
validation output. (Precedent: `packet_k0_search_kit_landing_2026-10-20.md` §
`WORKSPACE_AUDIT_EVENT`.) The workspace audit ledger is not a sink for repository changes.

---

## 15. PHASE-2 DECISION GATE — when to consider a real `scholar_core` package

Phase 2 is **not** authorized by this packet. It becomes worth doing only if the Phase-1 gate
shows **actual measured drift**, or if a second consumer of the primitives appears.

Options to weigh at that point:

| Option | Effect | Cost |
|---|---|---|
| **A. Keep the restatement, keep the pin** (status quo + Phase 1) | Kits stay standalone-buildable; no cross-repo dependency; no new package. Drift is caught, not prevented. | Lowest. Duplication stays (4 copies). |
| **B. New `scholar_core` package in its own repo** | One implementation, consumed by harness + kits. | A 9th repo, a 9th pin, install-order dependency for kits, and it breaks the "kits do not import the harness" property — a new **Contract v1-adjacent** decision needing its own ADR. |
| **C. `scholar_core` inside the harness repo** | One implementation, no new repo. | Kits would import the harness → violates the standalone-build property that the RAG/PDF kits explicitly chose; worse than B. |

**Recommendation:** stay on **Option A** until drift is measured. If Phase 1 reports drift in
the contract-v1 profile, that is a **contract-level incident** (identities would have moved),
not a refactor trigger, and it must be handled as such.

---

## 16. DECISIONS REQUIRED FROM THE RESEARCHER (before dispatch)

| # | Decision | Recommendation |
|---|---|---|
| D-1 | **Scope:** pin-only (this packet) vs. pin + create `scholar_core` now? | **Pin-only.** Creating the package before drift is measured adds a 9th distribution, a new pin, and a contract-adjacent decision with no proven payoff. |
| D-2 | **Golden home:** `tests/fixtures/canonical_profiles/` (harness) vs. one shared location consumed by kits? | **Harness.** The kits already carry their own offline goldens (`tests/test_canonical.py`); duplicating the shared set into every kit repo is exactly the drift the pin is meant to catch. |
| D-3 | **Distinct-profile handling:** assert the two non-contract profiles are *different* (and forbid coercion), or normalize them to the contract-v1 profile? | **Assert distinctness.** Normalizing would change existing search-kit and protocol-kit fingerprints and force a contract change. |

---

## 17. FOLLOW-UPS (not in this packet)

- **Selector tolerance for non-numeric task ids** — `scripts/select_test_gate.py:75,167`
  order tasks with `int(value.split("-")[1])`, so any `T-<non-numeric>` id raises
  `ValueError`. `T-230` sidesteps it here; the real fix is a tolerant sort key
  (`(0, int(n))` for numeric ids, `(1, id)` otherwise) plus a unit test. Small, harness-only,
  and worth doing before the next non-numeric packet id is proposed.
- **Agent-permission drift (owner action)** — the uncommitted `.opencode/agent/reviewer.md`
  edit that replaces `edit: deny` / `bash: ask` with `permission: allow` must be resolved by
  its owner (§4.5). It is **not** absorbed, regenerated past, or "fixed" by this packet, and
  no critic may be dispatched while the reviewer definition grants edit permission.
- **T-SC2** — *conditional*: a `scholar_core` extraction ADR, opened **only** if Phase 1
  reports measured drift or a second consumer appears (§15).
- **Kit-side golden adoption** — after this packet lands, ask the RAG and PDF kit repos to
  point their own golden batteries at the shared payload set (each a normal kit PR + pin
  bump). Optional; the harness-side pin already protects the boundary.
- **`tests/conformance` index** — add a pointer to the new conformance test in
  `docs/architecture/README.md` **after** the in-flight edits to that file land (currently
  modified by another actor; excluded here).
