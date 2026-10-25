# 01 — Role Model

A role is a **capability contract**, not a persona. It states what an agent may read, what it may write, what schema it must produce, and under what conditions it must refuse.

The prose that currently lives in `.opencode/agent/*.md` becomes **generated output**. The source of truth becomes `roles/<id>.json`.

---

## 1. Why generating the prose matters

Today, `screening-critic.md` says "your only write is the assigned critique artifact" and grants `edit: allow`. Both statements were written by hand, in two different places, and nobody owns the agreement between them.

If the description is generated from the same record that produces the permission map, the contradiction cannot exist. That is the entire argument for this layer: **one record, three outputs, no possible disagreement.**

The three outputs:

| Output | Consumed by | Purpose |
|---|---|---|
| `.opencode/agent/<id>.md` | opencode (dev loop) | frontmatter + generated prompt body |
| `.opencode/agent/<id>.json` (permission fragment) | opencode config / `opencode.json` | machine permission map |
| `roles/_generated/capabilities.json` | `CapabilityAdapter` (app) | read/write globs, isolation, network policy |

## 2. Schema

```json
{
  "id": "screening-critic",
  "title": "Screening Critic",
  "version": "2.0.0",
  "kind": "role",
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
      "required": true
    }
  ],

  "read_glob": [
    "workspaces/{ws}/literature/{batch,screening}/**",
    "workspaces/{ws}/protocol.json",
    "workspaces/{ws}/SCREENING_CRITERIA.md"
  ],
  "deny_glob": [
    "workspaces/{ws}/audit/**",
    "workspaces/{ws}/critique/screening/*.prior.json",
    ".git/**"
  ],

  "tools": ["read", "grep", "glob", "list"],
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

### Field semantics

| Field | Meaning | Rule |
|---|---|---|
| `kind` | `role` or `doc` | Only `role` is loadable as an agent. `doc` exists so misplaced prose (e.g. a git-policy file in the agent directory) fails the loader instead of silently becoming an agent. |
| `inputs[].from` | Provenance expectation: `workspace`, `written-input`, another role id | Used for `independence` checks and lineage assertions |
| `outputs[].write_glob` | The **only** locations this role may write | Required for every output. A role with no output has no write permission at all. |
| `read_glob` | Allowlist for reads | Reads outside this set are denied, not warned |
| `deny_glob` | Explicit denials, evaluated **after** allowlists | Always contains `audit/**` unless `audit.emit` is used |
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

**R2 — A role contains no absolute or repo-relative path.** Every path is a glob parameterised by `{ws}`, `{batch}`, `{task_id}`, `{role}`, or `{stu}`. The adapter resolves parameters; the role never learns where it is running.

**R3 — Every declared output has a `write_glob`.** "Your only write is X" becomes a filesystem fact. There is no output that is "just reported" — a report is an artifact with a path.

**R4 — `deny_glob` always wins.** Allowlist and denylist are both evaluated; denial is final. This is what makes `audit/**` safe: read of the journal is scoped, write is impossible.

**R5 — Permissions are derived, never authored.** `edit` is granted iff the role has an output with `write_glob`. `bash` is granted iff `bash` is in `tools`. `skill` is granted only for `requires_skill`.

**R6 — Independence is enforced by the adapter.** `blinded_from` produces a filesystem view that does not contain the other arm's outputs. A prompt saying "do not look" is not a control. (See `04_capability_adapter_and_app_surface.md` §3.)

## 4. The audit journal is adapter-mediated

No role receives `edit` or `write` on `workspaces/{ws}/audit/**`. Roles declare `audit.emit` events; the adapter writes them and stamps:

- the real `agent_or_tool` (`role@version`),
- the actor identity passed in the run context (never a value the role can set),
- input and output content hashes,
- the envelope status.

This closes the failure mode where a generic actor name or an empty provenance block makes an event unattributable. An agent that can write its own audit trail is not an audited agent.

## 5. Catalogue of roles

Eleven files currently load as agents. `git_workflow.md` is a policy document that happens to sit in the agent directory; under this schema it has no `kind: role` and fails to load, which is the desired outcome.

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
| `tools` contains `edit` or `write` | `edit: allow` |
| `tools` contains `bash` | `bash: allow` (or `ask` for `human-confirm`) |
| any other tool absent | `deny` |
| `requires_skill` non-empty | `skill: allow` |
| always | `task: deny` unless explicitly listed |

**Known limitation, and the reason the adapter exists:** opencode permissions are tri-state (`allow`/`ask`/`deny`) and cannot express a glob. `write_glob` is therefore *not* enforceable by opencode itself — it is enforced by the adapter or by a validated wrapper. Phase A removes the false claim; Phase E makes the claim true. Until Phase E, the generated description must not say "read-only" — it says "edit limited to <glob> by policy; see adapter" only once enforcement exists.

## 7. Conformance test

`tests/conformance/test_agent_role_permissions.py` — the test that makes today's contradiction impossible.

| Assertion | Catches |
|---|---|
| Every `roles/*.json` parses and validates against `Role@1` | Hand-edited drift |
| No two roles share an `id` | Accidental override |
| Every output declares a `write_glob` | Untracked writes |
| `write_glob` and `deny_glob` never intersect | Self-contradicting policy |
| Generated `.md` matches `roles/*.json` under `--check` | Manual edits to generated files |
| A file in `.opencode/agent/` with no `kind: role` is rejected by the loader | `git_workflow.md` regression |
| Description contains "read-only" ⇒ `tools` excludes `edit` and `write` | The exact `reviewer.md` / `screening-critic.md` failure |
| `blinded_from` references an existing role | Dead independence declarations |
| `refusal_codes` ⊆ global registry | Freelance status strings |
| Every role in the catalogue has a fixture envelope | Roles that were never executed |

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
