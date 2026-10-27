# 05 — Migration Plan

Five phases. Each is a bounded task packet with its own acceptance gate; none is authorized by this document.

Ordering is by leverage per unit of effort. A, B, and C are mutually independent and can run in parallel across agents. D depends on B (envelopes give skills their return contracts). E depends on A, B, and D.

---

## 0. Precondition: the baseline decision

`uv run python scripts/generate_contract_baseline.py --check` exited 1 on 2026-10-23 because `.opencode/agent/reviewer.md` was modified in the working tree. **Resolved 2026-10-25:** that file was reverted and `--check` now exits 0.

Phase A regenerates that file. It cannot start from a red baseline, and the baseline must not be regenerated merely to bless the drift. The autonomy decision below still stands on its own merits — the revert removed the immediate drift, it did not settle reviewer autonomy.

> Is the current `reviewer.md` state intentional, and if so, which role declaration should replace it?

**Recommended resolution, and why the drift happened.** The `permission: allow` edit is almost certainly a response to `bash: ask`, which interrupts autonomous review every time the reviewer wants to run `git diff` or a test. The underlying need is *uninterrupted read-only commands*, not write access.

The role model expresses that precisely:

```json
"tools": ["read", "grep", "glob", "list", "bash"],
"outputs": [{ "schema": "ReviewVerdict@1", "write_glob": "runs/{task_id}/review.json", "written_by": "adapter" }]
```

`bash` present (no prompts for `git diff`), `edit` absent (no file modification), and the verdict is persisted by the harness rather than the role. That satisfies the operational motive and removes the contradiction, without granting the reviewer the ability to repair what it judges.

Any Phase-A packet issued before this decision returns `BLOCKED_BASELINE_DRIFT`.

## 1. Phase A — Role records and generated permissions

**Deliverable**

- `roles/<id>.json` for all eleven agents (schema in `01_role_model.md`)
- `scripts/generate_agent_roles.py` with `--check`
- Regenerated `.opencode/agent/*.md` and permission fragments
- `tests/conformance/test_agent_role_permissions.py`
- `git_workflow.md` moved out of `.opencode/agent/`
- `opencode.json` agent sections reduced to a pointer at the generated fragments

**Closes directly**

| Defect | How |
|---|---|
| `screening-critic` `edit: allow` vs "only write is the critique" | `edit` granted only when `edit` is in `tools` **and** an output is `written_by: role` |
| `reviewer.md` self-contradiction | Same |
| `tester.md` can edit what it verifies | `tools` excludes `edit` |
| `git_workflow.md` loaded as an agent | `kind: doc` rejected by loader |
| Duplicate permission declarations in `opencode.json` | Generated, single source |

**Acceptance criteria**

1. `uv run python scripts/generate_agent_roles.py --check` exits 0.
2. Every role has at least one output with a `write_glob`.
3. No generated description contains "read-only" unless `tools` excludes `edit` and `write`.
4. Loader rejects `git_workflow.md` with a named error.
5. `opencode.json` contains no hand-authored agent permission keys.
6. `uv run python scripts/generate_contract_baseline.py --check` exits 0.
7. `uv run pytest tests/conformance/test_agent_role_permissions.py -q` passes.

**Negative cases**

- Hand-edit a generated `.md`; `--check` must fail.
- Add `edit` to `screening-critic`; conformance must fail.
- Add a role without `write_glob`; conformance must fail.
- Point `blinded_from` at a nonexistent role; conformance must fail.

**Effort:** ~1 day. **Lane:** `STANDARD`.

## 2. Phase B — Envelope and refusal registry

**Deliverable**

- `Envelope@1` pydantic model + JSON schema (transport only; no Contract v1 payload changes)
- `scholar_harness.contracts.envelope` with `validate`, `diff`, `verify_parents`
- Refusal registry as a frozen enum + generated docs
- Fixtures: one `OK`, one `PARTIAL`, one `BLOCKED_INPUT`, one `REFUSED`, one `PROVIDER_TRANSIENT`, one `INVALID_OUTPUT`, one `PARENT_HASH_MISMATCH`
- Orchestrator emits envelopes for dispatched packets; roles return them

**Acceptance criteria**

1. Every invariant in `02_envelope_and_refusals.md` §3 is a test.
2. `envelope_id` is stable across runs with identical inputs and payload; changes when any part changes.
3. Timing fields do not affect either hash.
4. A `BLOCKED_INPUT` carrying a payload is rejected.
5. Unknown status string rejected.
6. Frozen `Contract v1` schemas and goldens are byte-identical before and after.

**Negative cases:** the full matrix in `02` §8, plus: re-running a role with a mutated parent must produce `PARENT_HASH_MISMATCH` at the consumer, not a silent success.

**Effort:** ~0.5 day. **Lane:** `STANDARD`.

## 3. Phase C — Human confirmation

**Deliverable**

- `HumanConfirmation@1` schema + fixtures
- `human-confirm` role record (`tools: [read]`, `network: deny`, `bash: deny`)
- `scripts/confirm_screening.py` — interactively or from a queue import, writes a confirmation artifact bound to the two decision hashes
- Backfill path for the existing calibration corpus, marked explicitly as *retrospective*

**Acceptance criteria**

1. A confirmation cannot bind to an artifact whose hash changed after the reviewer saw it.
2. `summary.considered == len(decisions)`.
3. Every `changed: true` row carries a `rationale`; the validator rejects it otherwise.
4. A workspace with no confirmation artifact cannot be exported as "confirmed".
5. Retrospective backfills are labelled `retrospective: true` and never presented as contemporaneous.

**Negative cases:** confirmation referencing a stale hash; `changed: true` with null rationale; `summary` counts disagreeing with the rows.

**Effort:** ~1 day. **Lane:** `STANDARD`.

## 4. Phase D — Skill portability

**Deliverable**

- `{CLI:*}`/`{KIT_ROOT:*}` preamble resolver
- Mechanical rewrite of all fourteen skills (content unchanged); `pull-request-gate` is rewritten only to be excluded from app packaging
- `Preflight` and `Refusals` sections added
- `SKILL.meta.json` generated at install from `plugins.json`
- Dangling doc pointers fixed (`docs/kits_surface_matrix.md` force-included or inlined)
- `tests/conformance/test_skill_portability.py`

**Acceptance criteria**

1. No skill contains `uv run`, an absolute path, a bare `tools/`, or a commit SHA.
2. Every skill resolves under both the dev preamble and a simulated app preamble.
3. Every referenced doc path exists in the wheel manifest.
4. The stale `scholar-agent-kit` pin in prose is gone; the manifest is the only source.
5. One end-to-end smoke run of a real workspace succeeds through the resolver.

**Negative cases:** reintroduce `uv run`; reintroduce a prose SHA; reference a non-shipped doc; omit `Preflight` from a skill with `requires`.

**Effort:** ~1 day. **Lane:** `STANDARD`.

## 5. Phase E — Capability adapter

**Deliverable**

- `CapabilityAdapter` protocol + `RunRequest`/`Envelope` wiring
- `OpencodeAdapter` (dev, best-effort enforcement, documented)
- `InProcessAdapter` (app, enforced: run view, path validation, egress policy, adapter-written audit)
- Isolation tests for `directory` and `redacted-input`
- Conformance test: a role attempting a write outside `write_glob` fails in app mode

**Acceptance criteria**

1. In app mode, a write outside `write_glob` fails with `SCOPE_VIOLATION` and leaves no file.
2. In app mode, arm B's run view does not contain arm A's outputs (asserted by listing the view).
3. In app mode, `network: deny` produces a refused connection, not a timeout-and-retry.
4. Journal entries carry adapter-stamped actor, role version, and input/output hashes.
5. Dev mode documents its residual risk in the adapter docstring and README; it does not claim app-grade enforcement.

**Negative cases:** role writes a denied path; role writes to `audit/**`; blinded role attempts to list the parent run directory; role claims `isolation: none` when `arm` is set.

**Effort:** ~2 days. **Lane:** `RELEASE`.

## 6. Traceability

| Discovered defect | Phase |
|---|---|
| Critics can edit their subject (`edit: allow`) | A |
| `reviewer.md` prose contradicts config | A |
| `tester` can modify what it verifies | A |
| `git_workflow.md` treated as an agent | A |
| Permission declarations duplicated in `opencode.json` | A |
| Handoffs untyped; failure as stack trace | B |
| No typed refusal for provider/input failure | B |
| "588 included" unprovable — no confirmation artifact | C |
| Skills unusable outside this repo (`uv run`, paths) | D |
| Stale pin in `scholar-agent-kit` skill (`79ffe42…`) | D |
| Dangling `kits_surface_matrix.md` pointer in wheel | D |
| Independence asserted in prompts, not enforced | E |
| Audit events can name a generic actor | E |
| Blind arm can technically read the other arm | E |

## 7. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Phase A regenerates the baseline to hide drift | Medium | Precondition §0: decision before packet |
| Over-enforcement slows the dev loop | Medium | Dev adapter is best-effort and says so; only app mode is enforced |
| Envelope duplicates or drifts from Contract v1 payloads | Medium | Envelope carries payloads opaquely; Contract v1 goldens must stay byte-identical (Phase B criterion 6) |
| Confirmation becomes rubber-stamping | High | Record `changed`/`deferred`; surface override rate; never reward 100% confirmation |
| Skill rewrite silently changes a command | Low | Mechanical diff review + one real workspace smoke run |
| Scope creep into an agent framework | Medium | Non-goal in `README.md` §5; no orchestration primitives in any phase |
| Two definitions of a role during migration | Medium | Generated files are the only committed form; `--check` in CI |

## 8. Open questions

1. **Reviewer autonomy.** Resolved 2026-10-25 for Phase A by reverting `reviewer.md` to `edit: deny` + `bash: ask`. Whether to upgrade `bash: ask` to `allow` (removing approval prompts on `git diff` and tests) remains an **open owner decision**; Phase A deliberately did not change it.
2. **`arm` placement.** Kept in the envelope, not the payload, so payload schemas stay frozen. Confirm this does not complicate existing `ScreeningDecisions@1` consumers.
3. **Confirmation scope in the product.** **Resolved 2026-10-26 by the owner:** the signing party is the **customer's named reviewer**, not the operator. Normative schema and gates in `06_human_confirmation.md`.
4. **Model selection.** Deliberately excluded. Roles must not encode a model, or portability breaks at the first provider change.
5. **Retrospective backfill.** **Resolved 2026-10-26 by the owner:** label only, no backfill. The existing calibration corpus stays agent-mutual without a confirmation artifact; retrospective export reliance is refused by the Phase C gate.

## 9. Definition of done

A person who has never opened this repository can:

1. receive a workspace and a protocol,
2. complete screening, extraction, and charting,
3. see every disagreement resolved or explicitly deferred,
4. export a bundle whose every artifact verifies against `MANIFEST.sha256`,
5. and ask "who decided this?" and get a named human, a timestamp, and the exact artifact hash they saw.

…without ever encountering the words `uv`, `git`, `pin`, `lane`, `extractor-b`, or `scholar-agent-kit`.
