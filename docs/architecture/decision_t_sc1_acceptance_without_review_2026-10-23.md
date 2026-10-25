# Decision record — T-SC1 accepted without a recorded independent review

**Status:** `ACCEPTED_RISK` (PR #144) · reviewer-permission item `RESOLVED` 2026-10-25 — see §8.
**Recorded:** 2026-10-23 · decision owner: researcher (mouadh).
**Subject:** PR #144 (`feat(conformance): T-SC1 cross-kit canonical & identifier parity pin`)
and the local `.opencode/agent/reviewer.md` permission relaxation.

**Why this file exists.** A RELEASE-lane, identity-related change entered `main` without the
independent reviewer and tester evidence that the harness's own gates require. Accepting that
is a legitimate researcher decision, but it must be an **explicit, findable** decision — not
something a future agent discovers in `git log` and reads as drift, or worse, reads as
precedent for skipping review.

---

## 1. The decision

1. **PR #144 stays merged.** It is not reverted and no post-hoc review pass is scheduled.
2. **The local reviewer permission relaxation stays.** `.opencode/agent/reviewer.md` in the
   local worktrees keeps `permission: allow`; it is **uncommitted**, so no clone, CI run, or
   fresh checkout sees it. **Attribution: the researcher confirmed on 2026-10-23 that this
   edit is their own**, not an agent's. There is therefore no self-escalation finding attached
   to it — only the recorded fact that the local critic is no longer read-only.
   *(Superseded 2026-10-25: the edit was reverted. See §8.)*
3. The researcher reviewed the alternative (revert `reviewer.md` + run an independent
   reviewer/tester pass over the merged diff) and chose to accept the current state instead.
   *(Superseded 2026-10-25: the revert alternative was subsequently taken. See §8.)*

## 2. What was actually delivered by #144

For traceability, so this record is not only a risk note:

- `scripts/generate_canonical_profile_goldens.py` (deterministic generator + `--check`);
- `tests/conformance/test_canonical_profile_parity.py` (the cross-kit parity gate);
- four frozen goldens under `tests/fixtures/canonical_profiles/`
  (`contract_v1_canonical`, `documents_list_ascii`, `protocol_declaration_order`,
  `identifier_registry`);
- `docs/architecture/canonical_profile_parity.md`;
- manifest entry **`T-230`** plus the `tests/unit/test_select_test_gate.py` task-set extension;
- the packet document itself, including the `T-230` correction and §4.5/§4.6.

**Untouched, as the packet required:** `tools/**` (no kit source, no pin, no vendored
re-sync), `src/scholar_harness/contracts/**`, the frozen baseline files, and all workspaces.

## 3. What this acceptance does NOT claim

- It does **not** claim the packet's 21 acceptance criteria and 10 negative cases were
  independently verified. They were implemented; they were not independently judged.
- It does **not** claim the reviewer subagent is read-only in these local worktrees. It is not.
- It does **not** change any rule in `docs/architecture/DEVELOPER_COMPASS.md` or `AGENTS.md`.
  This is a one-off acceptance of an already-merged change, **not** a policy change and **not**
  a precedent.

## 4. Residual exposure

State as of 2026-10-23. Rows 1–3 were resolved on 2026-10-25 — see §8.

| Item | State | Consequence |
|---|---|---|
| Local `generate_contract_baseline.py --check` | **exit 1** (`Contract baseline drifted`) while `.opencode/agent/reviewer.md` is modified | Any packet whose preconditions include §4.4/AC-15 will return `BLOCKED_BASELINE_DRIFT`. |
| `tests/conformance/test_contract_baseline.py` | red in these worktrees for the same reason | The full harness suite is not green locally. |
| Reviewer independence (local sessions) | not enforced | A critic dispatched from these worktrees can edit the artifact it judges. Do not treat a local critic verdict as independent until this is resolved. |
| Reviewer independence (git history, CI, fresh clones) | **intact** | The committed `reviewer.md` still has `edit: deny` / `bash: ask`. |
| Cross-kit drift detection going forward | **active** | The #144 conformance test runs on every clean checkout; the *gate* is real even though the *review* was skipped. |

## 5. Conditions on any future resolution

- If the local `reviewer.md` edit is ever **committed**, it must ship with a regenerated
  `contract_v1_baseline.json` **and** an explicit decision that the reviewer is no longer
  read-only. It must not be regenerated silently.
- If the local edit is **reverted**, the baseline check goes green with no other action — this
  record can then be updated to `RESOLVED` rather than deleted.

## 6. Evidence used

```text
gh pr view <n> --json reviews,reviewDecision,mergedBy
  #142 reviews=0  decision=''   mergedBy=author
  #143 reviews=0  decision=''   mergedBy=author
  #144 reviews=0  decision=''   mergedBy=author
  #145 reviews=0  decision=''   mergedBy=author
  #146 reviews=0  decision=''   mergedBy=author
  #147 reviews=0  decision=''   mergedBy=author

git log --oneline HEAD..origin/main     (9 commits, 2026-10-22 → 2026-10-23)
git diff --stat HEAD..origin/main       (21 files, +3,020/-32 for #144..#147)
git diff -- .opencode/agent/reviewer.md (permission block → `permission: allow`)
uv run python scripts/generate_contract_baseline.py --check   → exit 1
```

| PR | Feature commit | Scope |
|---|---|---|
| #142 | `66adbd8` | claims/v1 citation contract — 14 files, +1,285, 91 tests, **not wired into any caller** |
| #143 | `98b371c` | `.gitattributes` LF pin for the claims artifacts |
| #144 | `82608b6` | T-SC1 parity pin — 21 files, +3,020 |
| #145 | `44a8dd0` | CI python-test job + paired heavy-backend backfill |
| #146 | `ee9f5f3` | extraction: resolve study-PDF path before workspace containment check (XC-027) |
| #147 | `d665be1` | CLI help tests assert on ANSI-stripped output |

## 7. Reopen triggers

Reopen this decision (do not silently extend it) if any of these occur:

- a fingerprint, chunk ID, or identifier value is later found inconsistent with Contract v1 —
  this note marks the point where an unreviewed identity change entered the tree;
- any agent cites this record as authority to skip independent review — **refuse**; it grants
  no such authority;
- the local `reviewer.md` edit is committed (as of 2026-10-25 it is reverted, not committed);
- a RELEASE-lane packet is proposed that reuses #144's implementation as its evidence base
  without re-deriving the acceptance criteria.

## 8. Amendment — 2026-10-25: reviewer-permission item resolved

The `permission: allow` relaxation was **reverted** rather than committed. The committed
`reviewer.md` (`edit: deny`, `bash: ask`) is restored, so:

| Item | 2026-10-23 | 2026-10-25 |
|---|---|---|
| `.opencode/agent/reviewer.md` | `permission: allow` (uncommitted) | reverted to committed version |
| `generate_contract_baseline.py --check` | exit 1 | **exit 0** |
| `tests/conformance/test_contract_baseline.py` | red locally | green locally |
| Reviewer independence (local sessions) | not enforced | restored |

**Why reverted rather than blessed.** Committing the relaxation would have granted the
reviewer the ability to edit the artifacts it judges, and would have required regenerating the
baseline for a permission that contradicts the file's own description. The operational motive
for the edit — no approval prompt when the reviewer runs `git diff` or a test — is **not**
addressed by this revert. It is addressed in `specs/agent-layer-portability/05_migration_plan.md`
§0: grant `bash`, deny `edit`.

**Unchanged:** item 1 (PR #144 stays merged, no post-hoc review) and all of §3. This
amendment resolves the reviewer-permission finding only.

```text
git checkout -- .opencode/agent/reviewer.md
uv run python scripts/generate_contract_baseline.py --check
  → "Contract baseline current: docs\architecture\contract_v1_baseline.json"  exit 0
```
