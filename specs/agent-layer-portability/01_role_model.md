# 01 — Role Model

A role is a **capability contract**, not a persona. It states what an agent may read, what it may write, what schema it must produce, and under what conditions it must refuse.

The YAML frontmatter that currently lives in `.opencode/agent/*.md` becomes **generated output**. The instruction body beneath it is preserved verbatim as authored prose. `roles/<id>.json` becomes the source of truth for permissions; `roles/<id>.prompt.md` becomes the source of truth for behaviour.

---

## 1. Why generating the prose matters

Today, `screening-critic.md` says "your only write is the assigned critique artifact" and grants `edit: allow`. Both statements were written by hand, in two different places, and nobody owns the agreement between them.

Generating the frontmatter from the record that produces the permission map removes disagreement between **description and capability**. It does not remove disagreement between the preserved instruction body and the capability record: the body is authored prose, and no generator can reconcile prose with policy by construction. That residual is bounded by a conformance guard — a body that claims a write must own a `written_by: role` output — and by review. It is not eliminated, and this specification should not claim otherwise.

The two outputs:

| Output | Consumed by | Purpose |
|---|---|---|
| `.opencode/agent/<id>.md` | opencode (dev loop) | frontmatter (generated) + body (verbatim from `roles/<id>.prompt.md`) |
| `.opencode/agent/_generated/permissions.json` | `opencode.json` pointer; `CapabilityAdapter` (app) | one machine-readable map for all roles: derived permission per tool, globs, isolation, network |

## 2. Schema

```json
{
  "id": "screening-critic",
  "title": "Screening Critic",
  "version": "2.0.0",
  "kind": "role",
  "mode": "subagent",
  "purpose": "Adversarially judge one screening batch against frozen criteria without repairing it.",

  "inputs": [
    { "schema": "ScreeningBatch@1",     "required": true,  "from": "written-input" },
    { "schema": "ScreeningDecisions@1", "required": true,  "from": "screener" },
    { "schema": "Protocol@1",           "required": true,  "from": "workspace" }
  ],

  "outputs": [
    {
      "schema": "ScreeningCritique@1",
      "write_glob": "workspaces/{ws}/critique/screening/{batch}.{role}.json",
      "written_by": "adapter",
      "required": true
    }
  ],

  "read_glob": [
    "workspaces/{ws}/literature/{batch,screening}/**",
    "workspaces/{ws}/protocol.json",
    "workspaces/{ws}/SCREENING_CRITERIA.md"
  ],
  "deny_glob": [
    "workspaces/{ws}/literature/**",
    "workspaces/{ws}/protocol.json",
    "workspaces/{ws}/SCREENING_CRITERIA.md",
    "workspaces/{ws}/audit/**",
    "workspaces/{ws}/critique/screening/*.prior.json",
    ".git/**"
  ],

  "tools": ["read", "grep", "glob", "list", "skill"],
  "network": "deny",
  "requires_skill": ["critic-contract"],

  "independence": {
    "blinded_from": ["adjudicator"],
    "isolation": "directory"
  },

  "refusal_codes": [
    "BLOCKED_INPUT",
    "CRITERIA_HASH_MISMATCH",
    "BATCH_INCOMPLETE",
    "INVALID_OUTPUT"
  ],

  "stop_conditions": [
    "decision coverage < 100% of batch records",
    "criteria_sha256 does not match the protocol fingerprint",
    "batch_id in decisions differs from batch_id in batch file"
  ],

  "audit": {
    "emit": ["CRITIQUE_SUBMITTED", "CRITIQUE_REFUSED"],
    "actor": "{role}@{version}"
  }
}
```

### Generated frontmatter, preserved body

The generator owns **only the YAML frontmatter** — `description` and the derived permission map. The instruction body is authored prose and must never be regenerated.

Rationale: 521 lines of operational instructions currently live in `.opencode/agent/*.md` (start-of-task checks, stop conditions, refusal discipline, dispatch rules). None of that is expressible in a capability record, and regenerating it would silently destroy it.

```
roles/<id>.json           # capability contract — source of truth for permissions
roles/<id>.prompt.md      # instruction body — source of truth for behaviour
.opencode/agent/<id>.md   # GENERATED: frontmatter + body concatenated verbatim
```

`--check` fails if either the frontmatter drifts from `roles/<id>.json` **or** the concatenated body differs from `roles/<id>.prompt.md`. The body file is the extraction of the current `.md` with its frontmatter removed, byte-for-byte.



| Field | Meaning | Rule |
|---|---|---|
| `kind` | `role` or `doc` | Only `role` is loadable as an agent. `doc` exists so misplaced prose (e.g. a git-policy file in the agent directory) fails the loader instead of silently becoming an agent. |
| `inputs[].from` | Provenance expectation: `workspace`, `written-input`, another role id | Used for `independence` checks and lineage assertions |
| `outputs[].write_glob` | The **only** locations this role may write | Required for every output. A role with no output has no write permission at all. |
| `outputs[].written_by` | `role` (default) or `adapter` | `role`: the agent writes the file. `adapter`: the agent returns the result and the harness persists it. Only `role` outputs justify `edit`. |
| `read_glob` | Allowlist for reads | Reads outside this set are denied, not warned |
| `deny_glob` | **Write** denials, evaluated after `write_glob` | A path in both `write_glob` and `deny_glob` is not writable. Does **not** restrict reads; reads are governed solely by `read_glob`. Always contains `audit/journal.jsonl` and `.git/**`. |
| `tools` | Capability set | The permission map is derived from this list; it is never authored separately |
| `network` | `deny` \| `allow` \| `allowlist` | Default `deny`. Scientific judgment roles have no network need. |
| `requires_skill` | Skill ids the prompt must include | Also becomes `skill: allow` scope |
| `independence.blinded_from` | Roles whose outputs must not be visible | Enforced by the adapter, never by prompt instruction |
| `independence.isolation` | `none` \| `directory` \| `redacted-input` | `redacted-input` additionally strips identifying fields before the run |
| `refusal_codes` | Closed set the role may return | Any other code is `INVALID_OUTPUT` |
| `stop_conditions` | Predicates that force a refusal | Evaluated before work begins |
| `audit.emit` | Event actions this role may raise | Journal writes are adapter-mediated (§5) |

## 3. Rules

**R1 — A role contains no command.** No `uv run`, no CLI string, no shell snippet. Procedure belongs to skills. A role that names a command cannot be executed by a second runtime.

**R2 — A role contains no absolute or repo-relative path.** Every path is a glob parameterised by `{repo}`, `{ws}`, `{batch}`, `{task_id}`, `{role}`, `{arm}`, or `{stu}`. The adapter resolves parameters; the role never learns where it is running.

Four consequences are enforceable and must be enforced by the generator:

1. **Parameter position is fixed.** The segment after `workspaces/` must be `{ws}`, and the segment after `runs/` must be `{task_id}`. A literal slug or task id — `workspaces/uav-crop-weed-v03/…`, `runs/task-42/…` — is a repo-relative path wearing a parameter's clothes, and is rejected.
2. **`{repo}` is read-only.** Every legitimate output lives under `workspaces/` or `runs/`, so a `{repo}` entry in `write_glob` is never correct and is rejected — anywhere in the glob, not only as its root. `{repo}/**` is additionally too broad to be a write target.
3. **`{repo}` does not escape the source-tree exclusion.** A glob rooted at `{repo}` is checked against the same excluded source trees as a bare one; `{repo}/src/**` is rejected exactly as `src/**` is.
4. **Segments are normalised and canonical before any rule runs.** `.` and empty segments are rejected alongside `..`, so no rule can be evaded by spelling a path differently: `workspaces/{ws}/audit/./journal.jsonl` and `{repo}/./src/**` are the same paths as the ones the rules forbid, and are rejected as such. A brace group that survives expansion with a `{` or `}` still inside it is a malformed glob, not a parameter, and is rejected.

   Because the validator runs on case-insensitive hosts, comparison folds case and rejects the spellings that alias there: a segment ending in `.` or whitespace, any segment containing `:` (an NTFS alternate data stream writes into the file it names), `~` (the 8.3 short-name marker addresses the long name), and any control character including NUL. These are rejected outright rather than compared, so the guarantee does not depend on a resolver's canonicalisation. Declared spelling in the generated output is never rewritten.

`**` is permitted as a whole-tree **read** for a role that must see the repository; it is never a valid write target.

`.git/**` is the single permitted repo-relative constant — it names the version-control directory itself, which cannot be parameterised into a workspace path without changing its meaning.

**R3 — Every declared output has a `write_glob`.** "Your only write is X" becomes a filesystem fact. There is no output that is "just reported" — a report is an artifact with a path.

An output may carry `"written_by": "adapter"` when the role returns its result to the caller instead of writing a file; the adapter persists it. This is the only exception, and it must be explicit. A role that neither writes its output nor delegates it is mis-specified.

**R4 — `deny_glob` always wins over `write_glob`.** Write permission is `write_glob` intersected with the complement of `deny_glob`; denial is final. `deny_glob` never restricts reads — `read_glob` alone decides what a role may read. This is what makes the journal safe: read is scoped by `read_glob`, write is impossible. The two axes are separate by design; conflating them would make it impossible for a critic to read the artifact it must judge.

**R5 — Permissions are derived, never authored.** `edit` is granted iff `edit` appears in `tools` **and** the role has at least one output with `written_by: role`. `bash` is granted iff `bash` is in `tools`. `skill` is granted iff `requires_skill` is non-empty, and `skill` appears in `tools` exactly when `requires_skill` is non-empty. Every tool listed is granted; every tool absent is denied.

**Shorthand exception.** When the derived map is all-`allow`, the frontmatter may render `permission: allow`. That shorthand means *every* tool is allowed, including tools absent from `tools`, and is therefore reserved for the three fully-autonomous dev-loop roles (`coder`, `orchestrator`, `inception-agent`). Every other role enumerates its keys explicitly. A role must never be switched to shorthand without an owner decision, because shorthand silently removes the "absent ⇒ denied" guarantee.

**R6 — Independence is enforced by the adapter.** `blinded_from` produces a filesystem view that does not contain the other arm's outputs. A prompt saying "do not look" is not a control. (See `04_capability_adapter_and_app_surface.md` §3.)

**R7 — A critic cannot write what it judges.** For a role whose `id` or `purpose` marks it a critic, or that is the `reviewer`, every path family in `read_glob` that is not inside one of the role's own `write_glob` locations must also appear in `deny_glob`. The declaration is not enforcement (§6); it is the contract the adapter enforces in Phase E, and the test that keeps the claim honest today.

**Single exemption.** A critic that reads the whole tree (`**`) cannot enumerate what it judges, so it satisfies R7 by the opposite route: it writes nothing of its own (`written_by: adapter` for every output) and its `deny_glob` carries the universal journal and `.git` denials — which is all that can be required of a role whose premise is that it cannot enumerate its inputs. The exemption is keyed on `written_by`, never on a role name, so a future critic that gains write capability loses the exemption automatically. Note that `bash: ask` remains an approval-gated write path outside a two-entry `deny_glob`; Phase E closes it, and until then it is a declared residual risk rather than a satisfied rule.

## 4. The audit journal is adapter-mediated

No role receives `edit` or `write` on `workspaces/{ws}/audit/journal.jsonl` or `.git/**`. Other files under `audit/` — for example a recon context written by the inception agent — are ordinary workspace artifacts and must be declared in `write_glob` like any other output. The journal itself is never writable by a role.

Roles declare `audit.emit` events; the adapter writes them and stamps:

- the real `agent_or_tool` (`role@version`),
- the actor identity passed in the run context (never a value the role can set),
- input and output content hashes,
- the envelope status.

This closes the failure mode where a generic actor name or an empty provenance block makes an event unattributable. An agent that can write its own audit trail is not an audited agent.

## 5. Catalogue of roles

Eleven files currently load as agents. `git_workflow.md` used to be a policy document sitting in the agent directory; it has been moved to `docs/architecture/git_workflow.md`. The loader still rejects any such file if it returns, because it has no `kind: role`.

| Role | Inputs | Output schema | Write glob | Independence |
|---|---|---|---|---|
| `orchestrator` | plan, workspace state, prior verdicts | `TaskPacket@1`, `Verdict@1` | `runs/{task_id}/{packet,verdict}.json` | none |
| `coder` | `TaskPacket@1` | `ChangeSet@1` + acceptance map | `runs/{task_id}/coder_report.json` **and** `packet.allowed_paths` | blinded from `reviewer`, `tester` |
| `reviewer` | `TaskPacket@1`, `ChangeSet@1`, diff | `ReviewVerdict@1` | `runs/{task_id}/review.json` | blinded from `coder` rationale (sees diff, not self-assessment) |
| `tester` | `TaskPacket@1`, validation commands | `TestReport@1` | `runs/{task_id}/test_report.json` | blinded from `coder` claims; runs commands only |
| `screener` | `ScreeningBatch@1`, `Protocol@1` | `ScreeningDecisions@1` | `workspaces/{ws}/literature/screening/{batch}_decisions_{arm}.json` | `redacted-input` when arm = B |
| `screening-critic` | `ScreeningDecisions@1`, batch, criteria | `ScreeningCritique@1` | `workspaces/{ws}/critique/screening/{batch}.{role}.json` | blinded from `adjudicator` |
| `adjudicator` | two `ScreeningDecisions@1`, declared conflicts | `Adjudication@1` | `workspaces/{ws}/adjudication/{batch}.json` | sees both arms (required) |
| `extractor-a` | included batch, `extracted/**` sources | `ExtractionRecord@1` | `workspaces/{ws}/extracted/A/{stu}.json` | `directory` |
| `extractor-b` | included batch, `extracted/**` sources | `ExtractionRecord@1` | `workspaces/{ws}/extracted/B/{stu}.json` | `redacted-input`, blinded from `extractor-a` |
| `extraction-critic` | both `ExtractionRecord@1`, source text | `ExtractionCritique@1` | `workspaces/{ws}/critique/extraction/{stu}.json` | blinded from `adjudicator` |
| `inception-agent` | `intent.json` or chat, bounded probes | `Protocol@1` + workspace scaffold | `workspaces/{ws}/{protocol,intent,project}.json` | none |
| `human-confirm` | candidate artifact + evidence bundle | `HumanConfirmation@1` | `workspaces/{ws}/confirmations/{scope}.json` | none — this role *is* the independence of last resort |

`human-confirm` is specified in `04_capability_adapter_and_app_surface.md`. It is a role in the same registry because its artifact is what closes the loop between "agents suggested" and "a person accepted."

## 6. Code generation

```
uv run python scripts/generate_agent_roles.py            # write
uv run python scripts/generate_agent_roles.py --check    # CI gate
```

Generation is deterministic: no timestamps, stable key order, LF endings, UTF-8 without BOM. `--check` fails on any drift between `roles/*.json` and the generated files.

Generated permission map:

| Role field | opencode key |
|---|---|
| `tools` contains `read`/`grep`/`glob`/`list` | corresponding keys `allow` |
| `tools` contains `edit` or `write`, **and** an output is `written_by: role` | `edit: allow` |
| `tools` contains `bash` | `bash: allow` (or `ask` for `human-confirm`) |
| any other tool absent | `deny` |
| `requires_skill` non-empty (and `skill` in `tools`) | `skill: allow` |
| always | `task: deny` unless explicitly listed |

**Known limitation, and the reason the adapter exists:** opencode permissions are tri-state (`allow`/`ask`/`deny`) and cannot express a glob. `write_glob` is therefore *not* enforceable by opencode itself — it is enforced by the adapter or by a validated wrapper. Phase A removes the false claim; Phase E makes the claim true.

Until Phase E, a generated description may assert read-only **only** when the role has no write capability at all. A role that writes its own critique may not call itself read-only: it states what it writes, and that edits elsewhere are denied by contract rather than by opencode. Descriptions must not borrow "read-only" to mean "I am careful"; that word is reserved for a capability fact.

## 7. Conformance test

`tests/conformance/test_agent_role_permissions.py` — the test that makes the repaired contradictions detectable. It does not prove their absence: the body write-claim guard is a bounded detector, and the residue it cannot see is listed in `docs/architecture/decision_phase_a_role_generation_2026-10-25.md` D16.

| Assertion | Catches |
|---|---|
| Every `roles/*.json` parses and validates against `Role@1` | Hand-edited drift |
| No two roles share an `id` | Accidental override |
| Every output declares a `write_glob` | Untracked writes |
| `write_glob` and `deny_glob` never intersect | Self-contradicting policy |
| Generated `.md` matches `roles/*.json` under `--check` | Manual edits to generated files |
| A file in `.opencode/agent/` with no `kind: role` is rejected by the loader | `git_workflow.md` regression |
| Description asserts unqualified "read-only" ⇒ the role has no `edit`/`write` capability | The exact `reviewer.md` / `screening-critic.md` failure |
| Critic roles: each `read_glob` family outside `write_glob` appears in `deny_glob` | A critic editing the artifact it judges |
| Each role's derived permission map equals an independently authored expected map | A wrong derivation rule that the generator would otherwise certify |
| `blinded_from` references an existing role | Dead independence declarations |
| `refusal_codes` ⊆ global registry | Freelance status strings |
| Every role in the catalogue has a fixture envelope *(deferred to Phase B — no envelope fixtures exist yet)* | Roles that were never executed |

### Negative cases (must fail)

1. Role with `purpose` containing a shell command → `R1` violation.
2. Role whose `write_glob` is `workspaces/{ws}/**` → too broad; policy lint rejects.
3. `screening-critic` with `tools: [..., "edit"]` → conformance failure.
4. `extractor-b` without `blinded_from: ["extractor-a"]` → independence failure.
5. Generated `.md` edited by hand → `--check` drift.
6. `human-confirm` with `network: allow` → policy failure.

## 8. Versioning

Roles carry semver in the envelope. The version is part of the run's reproducibility record.

| Change | Bump |
|---|---|
| Wording of `purpose` | patch |
| New `stop_condition` or refusal code | minor |
| Changed `inputs`/`outputs` schema or `write_glob` | major |
| Changed `independence` or `network` | major |

Because the envelope records `role@version`, a corpus produced under `screener@2.1.0` and one under `screener@3.0.0` are distinguishable after the fact. Today they are indistinguishable, which is a reproducibility gap independent of this spec.
