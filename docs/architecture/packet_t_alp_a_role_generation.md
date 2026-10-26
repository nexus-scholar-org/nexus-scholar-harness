# Task packet — T-ALP-A: role records and generated permissions

**Status:** implemented, final cleanup pass applied 2026-10-25
**Owner surface:** harness
**Governing spec:** `specs/agent-layer-portability/01_role_model.md` (orchestrator-owned; not editable by the implementing agent)
**Delivery lane:** `STANDARD`

This file exists because the reviewer of the first Phase A submission correctly observed that
the acceptance criteria — including a named exception to criterion 8 — were recorded only in an
agent conversation and could not be reconstructed from the repository. A criterion that cannot
be read by a later reviewer is not a criterion.

---

## 1. Objective

Make `roles/<id>.json` the single source of truth for agent capability, and generate from it:

1. the YAML frontmatter of `.opencode/agent/<id>.md`;
2. one machine-readable permission map at `.opencode/agent/_generated/permissions.json`;
3. a conformance test that makes description/capability disagreement detectable.

The instruction body of each agent is **preserved verbatim**. It is not regenerated. See
`01_role_model.md` §"Generated frontmatter, preserved body".

## 2. Scope

**Allowed paths**

- `roles/**`
- `scripts/generate_agent_roles.py`
- `tests/conformance/test_agent_role_permissions.py`
- `tests/conformance/fixtures/expected_permissions.json`
- `.opencode/agent/**` (frontmatter regenerated; bodies preserved)
- `opencode.json` (agent sections only)
- `docs/architecture/contract_v1_baseline.json` (regenerated)
- `docs/architecture/git_workflow.md` (moved from `.opencode/agent/`)
- `docs/architecture/decision_phase_a_role_generation_2026-10-25.md`
- `docs/architecture/context_efficiency_policy.md`
- `docs/architecture/packet_t_alp_a_role_generation.md` (this file)

**Forbidden paths**

- `tools/**` — no kit source, no pin bump, no vendored re-sync
- `src/**`
- `workspaces/**`
- `specs/**` — normative input, orchestrator-owned
- `tests/fixtures/**` except the conformance fixture named above
- `.agents/plugins/nexus-scholar/plugins.json`

## 3. Acceptance criteria

1. `uv run python scripts/generate_agent_roles.py --check` exits 0.
2. Every role declares at least one output with a `write_glob`.
3. A description asserting unqualified "read-only" implies no `edit`/`write` capability.
4. A `.opencode/agent/` file without `kind: role` is rejected by the loader with a named error.
5. `opencode.json` carries no hand-authored per-agent permission keys.
6. `uv run python scripts/generate_contract_baseline.py --check` exits 0, and the baseline diff
   is confined to `.opencode/agent/*` entries.
7. `tests/conformance/test_agent_role_permissions.py` passes.
8. **Bodies preserved.** The instruction body of each agent is byte-identical to the version at
   the baseline commit — *subject to the named exception in §4*.
9. `screening-critic` and `tester` no longer grant `edit`; `reviewer` retains `edit: deny` and
   `bash: ask`.
10. No file outside the allowed paths is modified.

## 4. Named exceptions

**E1 — criterion 8, scoped to capability sentences.** `roles/screening-critic.prompt.md` may
have exactly two capability sentences amended, because criterion 9 removes the write capability
those sentences asserted. Behavioural instructions must not change. The change must be shown as
a diff, and a conformance guard must check body write-claims against `written_by`.

**E2 — explicit denials are authorised.** `task: deny` (seven roles) and `skill: deny`
(`reviewer`) are consequences of deriving permissions from an exhaustive `tools` list. No
capability is gained; two inherited defaults are removed. Authorised as decision D9.

**E3 — shorthand.** `permission: allow` is permitted only for `coder`, `orchestrator`,
`inception-agent`, and means every tool is allowed, including unlisted ones. Authorised in
`01_role_model.md` R5. Switching any other role to shorthand requires an owner decision.

## 5. Negative cases

1. Hand-editing a generated `.md` fails `--check`.
2. Adding `edit` to `screening-critic` fails conformance.
3. A role with no `write_glob` fails validation.
4. `blinded_from` naming an unknown role fails.
5. `write_glob` intersecting `deny_glob` fails.
6. A `.opencode/agent/` file without `kind: role` is rejected.
7. Brace alternations that hide `..` traversal are rejected.
8. A body claiming a write with only adapter-written outputs fails.
9. A role whose required input is sourced from one of its own `blinded_from`
   roles fails (R6).
10. A bare repo-relative glob (`.agents/skills/**`) fails; `{repo}/...` is the
    parameterised form (R2).
11. A synthetic `synthesis-critic` with an undefended read family fails R7
    without any change to the generator.
12. A role whose `deny_glob` omits `audit/journal.jsonl` or `.git/**` fails,
    including when it reads the tree repo-wide (R4/§4).

## 6. Validation commands

```
uv run python scripts/generate_agent_roles.py --check
uv run pytest tests/conformance/test_agent_role_permissions.py -q
uv run pytest tests/conformance/test_contract_baseline.py -q
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/check_context_policy.py --check
uv run ruff check scripts/
```

## 7. Toolkit sync and workspace audit

- No `tools/<kit>/` change is in scope, so no canonical-repo change, pin bump, or vendored
  re-sync arises. A packet that needs one must return `BLOCKED_CANONICAL_REPO`.
- No workspace is named or mutated, so no `audit/journal.jsonl` event is owed.

## 8. Review history

| Cycle | Verdict | Principal finding | Resolution |
|---|---|---|---|
| 1 | `BLOCKED` | Governing spec modified inside the task diff, unattributed, leaving its generation model self-contradictory | Amendment attributed to the orchestrator; spec repaired for internal contradictions; it lands as its own commit |
| 2 | `CHANGES_REQUESTED` | `extraction-critic` retained `edit` without fencing its inputs; `reviewer`/`tester` declared outputs they could not write; permission map unpinned by any independent expectation | `deny_glob` fencing + R7; `written_by: adapter`; independent expected-map fixture |
| 3 | `CHANGES_REQUESTED` | `deny_glob` was a write denylist in `01` but a read filter in `04`/`05`; four records carried `deny_glob: []` against a rule saying it is never empty | `04`/`05` aligned to write-only semantics in the orchestrator's amendment; record-level fix carried into the final pass |
| final (authorised) | Findings addressed | Four records still had `deny_glob: []` with a `read_glob == ["**"]` exemption the spec never granted; `reviewer` required an input from a role it is blinded from; R7's critic set was hardcoded; R2 was unenforced; D16/D17 overstated the tests | C1–C5: universal journal/`.git` denial, `written-input` for the review change set plus a blinded-input validator, derived critic set, `{repo}` parameter with bare-prefix rejection, and corrected decision text |
| 4 | `CHANGES_REQUESTED` | The body write-claim guard decoded only three first-person phrases, so a third-person claim naming a file passed for an adapter-persisted role (independent tester, probe 6) | Guard widened to declarative claims; D16 rewritten to a heuristic with a named limitation list |
| 5 | `CHANGES_REQUESTED` | Negation guard was clause-blind; `.`/empty segments defeated R4's journal invariant; `{repo}/./src/**` and nested braces escaped R2 | Clause-reset guard; segment normalisation; segment-based `{repo}` check; recursive brace expansion with malformed-group rejection |
| 6 | `GATE: RED` (tester) → `CHANGES_REQUESTED` (review) | On win32, case, trailing dots/spaces, `:` alternate data streams and `~` 8.3 short names alias the same file, so R4 certified a journal write | Comparison folds case; trailing-dot/space, `:` and `~` and control characters rejected outright; alias matrix pinned by tests |

**Authorisation record.** Cycles 1–3 are the three permitted coder–reviewer cycles. Cycles 4–6
were each opened by an independent gate that produced a *reproducible failure* (a shipped
contradiction, a validator hole proved by an actual write, a platform alias proved by inode
identity), not by stylistic disagreement. Each was explicitly authorised by the decision owner
before dispatch. They are recorded here rather than absorbed silently: three cycles of authorised
remediation after the cap, each with its finding and its closure evidence.
