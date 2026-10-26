# Decision — Phase A agent-role generation (2026-10-25)

**Task:** T-ALP-A · **Repair cycles:** T-ALP-A-r1 … r4 (2026-10-25) · **Owner surface:** harness · **Governing spec:** `specs/agent-layer-portability/01_role_model.md`

## 0. Spec attribution

The amendments to `01_role_model.md` that this repair implements — `written_by`
in R3, the rewritten R5 (derived `edit`/`skill`), the new R7 (a critic denies what
it judges), and the matching §6 table and §7 assertions — were authored by the
**orchestrator** before this repair was dispatched. They were present in the
working tree, uncommitted, and are therefore **not** part of this coder's change.
The orchestrator owns that edit and will land it as its own separate commit. This
packet implements against the amended spec and does not modify it.

A **second** orchestrator amendment (also 2026-10-25, before T-ALP-A-r2) made
`deny_glob` explicitly a write denylist (R4 and the field table), narrowed §4
from `audit/**` to `audit/journal.jsonl` so `inception-agent`'s
`audit/recon_context.json` output is legal, fixed the §2 example, and added the
R5 shorthand exception for `coder`, `orchestrator`, and `inception-agent`. R2 was
amended with the same intent: `{repo}` is a permitted glob parameter and
`.git/**` is the single permitted repo-relative constant. This repair conforms to
those rules; it does not edit `specs/**`.

## 1. The frozen baseline was regenerated

`docs/architecture/contract_v1_baseline.json` was regenerated because Phase A
regenerates the frontmatter of the OpenCode agent definitions, and nine of those
files are baseline-locked. Regenerating was authorised by the task packet, not
inferred: the packet lists the baseline file as an allowed path and requires it
to be regenerated.

Only the agent entries changed. Verified by diffing the `locked_files` map of
`HEAD` against the regenerated file:

```
changed count: 9
  .opencode/agent/adjudicator.md
  .opencode/agent/coder.md
  .opencode/agent/extraction-critic.md
  .opencode/agent/extractor-a.md
  .opencode/agent/extractor-b.md
  .opencode/agent/orchestrator.md
  .opencode/agent/reviewer.md
  .opencode/agent/screener.md
  .opencode/agent/screening-critic.md
added: []
removed: []
unchanged count: 40
NON-AGENT CHANGED: []
```

`tester.md` and `inception-agent.md` are not baseline-locked, so their
regeneration does not appear in the baseline. `docs/architecture/contract_v1_baseline.md`
is itself baseline-locked and was deliberately **not** edited.

Within the repair cycle, only `extraction-critic.md` (repaired description)
changed again among the locked files; `coder.md` returned to its all-allow
frontmatter once the coder's required skill was declared (D13). The permission
maps of `reviewer`, `screening-critic`, and `tester` were already correct; their
outputs gained `written_by: adapter`, which is recorded in
`_generated/permissions.json` and not in the `.md` frontmatter. `tester.md` is
not baseline-locked.

## 2. Why an agent-frontmatter regeneration is a baseline event

The agent frontmatter is now generated from `roles/<id>.json`. That is the point
of the change: the capability record and the permission map can no longer
disagree. The baseline records the bytes of the agent definitions because they
enforce scientific-workflow independence, so a generated change is still a
baseline change — the anchor is the review of *why* the bytes changed, not the
claim that they did not.

The instruction bodies were **not** regenerated. Each body is the byte-for-byte
extraction of the corresponding `.md`, now stored in `roles/<id>.prompt.md`, and
the generator re-emits it unchanged. Line endings were normalised to LF in both
the source and the output, as §6 requires; the comparison is therefore exact.

Ten of the eleven bodies remain byte-identical to `HEAD` after this repair. The
exception is `screening-critic`: T-ALP-A-r2 granted a named, sentence-scoped
exception (criterion 8) to repair two capability claims that contradicted its
`written_by: adapter` record — line 2 now says the critique is its only *output*
and the harness persists it, and line 16 says it must *emit* only that critique
and the harness writes the file. No behavioural instruction, ordering, or blank
line changed (see D16).

Generation writes each file through a sibling temp file and `os.replace`, so the
write is atomic **per file**; the tree as a whole is not a transaction. A failed
run can leave some agents regenerated and others not, which `--check` then
reports.

## 3. Behavioural delta

The original packet's clause that Phase A permits **exactly two** behavioural
changes (`screening-critic` and `tester` lose `edit`) is **wrong and superseded**
by D9. The amended R5/R7 rules make several previously implicit defaults
explicit, and this repair also repairs the two HIGH findings the reviewer
confirmed. The invariant that still holds is: **no role gains a capability.**

| Role | Before (HEAD) | After | Delta |
|---|---|---|---|
| `orchestrator` | `permission: allow` | `permission: allow` | none; record now declares `requires_skill: [pull-request-gate]` (its body requires loading it) so `skill` stays allow |
| `coder` | `permission: allow` | `permission: allow` | none; record now declares `requires_skill: [workspace-manager]` (its body requires the workspace-manager audit tooling) so `skill` stays allow |
| `inception-agent` | `permission: allow` | all allow | none |
| `reviewer` | `edit: deny`, `bash: ask`, read tools allow, no `skill`/`task` | same toggles, plus explicit `skill: deny`, `task: deny`; output `written_by: adapter` | no capability gained; two inherited defaults removed (D9) |
| `tester` | `permission: allow` | bash allow, **`edit: deny`**, read tools allow, **`skill: deny`**, **`task: deny`**; output `written_by: adapter` | **loses `edit`** (mandated); removes `skill` and `task` (R5/F-P3-1) |
| `screening-critic` | `edit: allow` | **`edit: deny`**, `task: deny`, `skill: allow`; output `written_by: adapter`; `deny_glob` extended | **loses `edit`** (mandated); R7 denials; adapter persistence |
| `screener` | `edit: allow`, `bash: ask`, `skill: allow` | identical, plus `task: deny` | no capability gained; removes one inherited default (D9) |
| `extractor-a`, `extractor-b` | `edit: allow`, `bash: ask`, `skill: allow` | identical, plus `task: deny` | as above |
| `extraction-critic` | `edit: allow`, `bash: ask`, `skill: allow`, description claimed read-only | same permission map plus `task: deny`; **repaired purpose**; `deny_glob` extended; version `2.0.1` | R7/P1-1 repair: it still writes its critique, now denies every family it judges |
| `adjudicator` | `edit: allow`, `bash: ask`, `skill: allow` | identical, plus `task: deny` | as above |

No role gains a capability. `reviewer` keeps `bash: ask` and `edit: deny` as the
packet's behaviour boundary requires; the spec §0 recommendation of `bash: allow`
is a separate autonomy decision and was not taken here.

## 4. Where the specification was ambiguous, and what was decided

**D1 — Fragment location.** `01_role_model.md` §1 names `.opencode/agent/<id>.json`
plus `roles/_generated/capabilities.json`; the task packet names a single
`.opencode/agent/_generated/permissions.json`. The packet is the narrower
instruction and its path is inside an allowed path, so the consolidated file was
implemented. It carries both the tri-state `permission` map and the capability
fields (`read_glob`, `write_glob`, `deny_glob`, `independence`, `network`,
`requires_skill`, `refusal_codes`, `audit`), so nothing in the adapter contract
is lost.

**D2 — `bash` is tri-state.** §6 maps "`tools` contains `bash`" to `bash: allow`,
but the packet requires `reviewer` to keep `bash: ask`, and seven roles today
have approval-gated shell. Resolved with an optional `bash_approval` field
(`allow` default, `ask` permitted) that can only tighten a `bash` capability the
record already grants; it can never grant `bash` on its own. Conformance rejects
`bash_approval` when `bash` is absent from `tools`. Honouring §6 literally would
have widened shell autonomy for seven roles in a change that is explicitly
structural.

**D3 — `mode` is a required record field.** `mode: primary|subagent` has to come
from somewhere. Leaving it in the generator would reintroduce a hand-authored
value outside the source of truth, so it is part of `Role@1` and is emitted into
the frontmatter.

**D4 — `extraction-critic` could write what it judged (fixed in this repair).**
Phase A removed the false "read-only" label but preserved `edit`, leaving the
prose/capability contradiction in place (the old R1 residual risk). T-ALP-A-r1
repairs it under amended R7: `deny_glob` now contains every read family outside
its `write_glob` — `extracted/**`, `literature/**`, `pdfs/**`, `protocol.json` —
and the `purpose` states what the role writes and that edits to the artifacts it
judges are denied by contract. The packet listed three families; R7's
"every read family" also required `pdfs/**`, which was added. The role keeps
`edit` because it writes its own critique; it no longer describes itself as
read-only, which §6 reserves for a role with no write capability at all.
`version` moves `2.0.0 → 2.0.1` (purpose wording = patch, §8).

**D5 — `opencode.json` entries, and what `permissionRef` is.** Four agents are
registered by hand; the other seven are discovered from `.opencode/agent/*.md`.
The four entries were kept (and only those), reduced to `file` plus
`permissionRef`, because adding explicit entries for the two primary agents could
change primary-agent registration and default selection — a behaviour change this
phase must not make. `description` and `role` were removed: both duplicated the
generated record.

**Correction (T-ALP-A-r1):** `permissionRef` is a **harness-internal pointer
convention**, not opencode configuration. opencode does **not** define that key
and does **not** read this `agents` block; opencode discovers agents from
`.opencode/agent/*.md` frontmatter. The `agents` block is retained only as an
app-side pointer map, and must not be mistaken for working opencode permission
config.

**D6 — `{arm}` is a path parameter.** The original R2 closed set was
`{ws, batch, task_id, role, stu}`, but the specification's own screening write
glob is `workspaces/{ws}/literature/screening/{batch}_decisions_{arm}.json`. The
parameter set was extended with `arm`, and amended R2 now names it, so the
specification's own catalogue is valid rather than contradicting its own rule.
The generator's `PATH_PARAMETERS` carries the same set.

**D7 — Audit and `.git` read access.** §4 makes the journal and `.git/**`
unwritable by every role, and R4 makes reads solely a `read_glob` question.
`orchestrator` and `reviewer` are required by their bodies to reconcile against
`audit/journal.jsonl`, and the dev-loop roles must run `git status`/`git diff`,
so those roles read the repository tree (`read_glob: ["**"]`), which covers both
paths. `tester` has the same repo-wide read for a different reason: it must run
validation commands and inspect the artifacts they produce, and it never
mentions the journal or the audit tree in its body. The invariant that matters
is enforced universally instead: **no `write_glob` may intersect
`workspaces/{ws}/audit/journal.jsonl` or `.git/**`**.
`inception-agent` legitimately writes `workspaces/{ws}/audit/recon_context.json`,
so it denies the journal path specifically rather than the whole audit tree
(amended §4 makes that output legal).

**D8 — Initial version.** No role previously carried a version, so every record
started at `2.0.0`, matching the spec's own `screening-critic` example. Future
changes follow §8 (purpose = patch, new stop condition/refusal = minor,
inputs/outputs/write_glob/independence/network = major). `extraction-critic` is
`2.0.1` after the D4 purpose repair; every other role is `2.0.0`.

**D9 — Absent capabilities are emitted as explicit `deny` (authorised).** §6
requires "any other tool absent → deny" and "always `task: deny` unless
explicitly listed", so the generated block enumerates every key instead of
relying on inherited opencode defaults. This is the one place where
"behaviour-preserving" is read as *no capability gained* rather than *identical
effective defaults*.

The original packet's "only two changes" clause is **superseded**. The explicit
denials are a consequence of the derivation, not an unapproved widening:

- `task: deny` for the **seven** roles that do not list `task`
  (`adjudicator`, `extraction-critic`, `extractor-a`, `extractor-b`, `reviewer`,
  `screener`, `screening-critic`).
- `skill: deny` for `reviewer` (no `requires_skill`) — and, after aligning the
  records with amended R5, for `tester` as well (D13). Its `skill` tool was
  removed because it declares no required skill.

**No capability was gained.** In the original Phase-A delta this removed two
inherited defaults — `task` for seven roles and `skill` for `reviewer`. Aligning
the records with amended R5 extends the same kind of removal to `tester`
(`skill`), and F-P3-1 removes `tester`'s `task`. `coder` and `orchestrator` keep
`skill` because their bodies require a skill and their records now declare it
(D13). None of those roles uses a capability in a way its body contradicts.

**D10 — `coder`'s delegated write scope.** §5 records coder's write scope as
`runs/{task_id}/coder_report.json` **and** `packet.allowed_paths`.
`packet.allowed_paths` is not expressible as a static glob. The record therefore
declares the `coder_report` artifact; the delegated edit scope remains packet
discipline enforced at dispatch, exactly as before this change. opencode's
tri-state `edit: allow` cannot express a glob either (spec §6 known limitation).

What the R2 validator rejects, precisely, is `**` as a whole `write_glob`, and
`{repo}/**` as a write target because it names the entire repository. Scoped
breadth is legal: `runs/{task_id}/**` and a family glob such as
`workspaces/{ws}/critique/**` are accepted, because the adapter still resolves
the root parameter (a `workspaces/{ws}/**` write remains rejected by R4, since it
would cover the audit journal). The earlier wording ("a `**` glob is rejected")
was imprecise — it is the unbounded root that is rejected, not every trailing
`**`.

**D11 — Adapter-persisted outputs (`written_by: adapter`).** Under amended R3 an
output may be persisted by the adapter when the role returns the result instead
of writing a file. `reviewer` (`ReviewVerdict`), `tester` (`TestReport`), and
`screening-critic` (`ScreeningCritique`) have no `edit`/`write` capability but
declare an output path, so each is marked `written_by: adapter`. The generator
now rejects the inverse: an output that is `written_by: role` (or omits
`written_by`, which defaults to `role`) while `tools` grants no write capability.
This is what keeps "declares an output" from silently implying a write the role
cannot perform. `screening-critic` was not named in the packet's F-P2-2 text,
but the new rule applies to every role and it has the same shape as `reviewer`
and `tester`; it was marked adapter rather than granted a write tool.

**D12 — R7 critic denial coverage.** `screening-critic` and `extraction-critic`
now deny every read family outside their own `write_glob`
(`literature/**`, `protocol.json`, `SCREENING_CRITERIA.md` / `extracted/**`,
`pdfs/**`). `reviewer` reads `**`, and denying `**` would intersect its own
output (R4), so it takes R7's **single exemption** (spec §3, keyed on
`written_by`, never on a role name): every output stays `written_by: adapter`, so
the role has no role-written output, and its `deny_glob` covers the artifact
families it must not touch. A repo-wide critic that gains a role-written output
loses the exemption and fails the gate. Two limits are declared, not hidden:
opencode cannot enforce the `deny_glob` entries, and `bash: ask` remains an
approval-gated write path outside a two-entry `deny_glob`. Phase E closes both;
until then this is a capability fact plus a declaration, not a filesystem view.

R7 is implemented against R4's definition: `deny_glob` is the **write**
denylist. A family may appear in both `read_glob` (read allowed) and `deny_glob`
(write denied) — that is precisely the critic pattern, "read the artifact, never
write it". `read_glob` scopes reads; `deny_glob` denies writes, and
`write_glob` intersecting `deny_glob` is the contradiction R4 rejects. The
Phase-E adapter must implement that read/write split. This is a declaration, not
enforcement: Phase A makes the claim honest, Phase E makes it true (§5 R3).

**D13 — `skill` is derived from `requires_skill` (amended R5).** `skill` is
allowed iff `requires_skill` is non-empty, and `"skill" in tools` must agree with
that. `tester` declared the `skill` tool but no required skill, so the tool was
removed. `orchestrator`'s instruction body requires the `pull-request-gate` skill
before git publication, and `coder`'s body requires the `workspace-manager`
audit tooling for significant workspace mutations, so instead of removing their
`skill` capability those records now declare
`requires_skill: ["pull-request-gate"]` and `["workspace-manager"]`
respectively; neither permission set changes. A record that disagrees in either
direction is rejected with a named error.

**D14 — Input and audit validation (registry deferred).** Every `input` must
declare a `schema` and a `from` of `workspace`, `written-input`, or a known role
id. `audit.emit` actions must be non-empty strings. The **closed action registry**
is not invented here; it arrives with the Phase-B envelope work and is recorded
as deferred.

**D15 — The permission map is pinned by an independent fixture.**
`tests/conformance/fixtures/expected_permissions.json` is hand-authored from
§6's derivation table **plus D2's `bash_approval` field** (which is why seven
roles carry `bash: ask` rather than §6's bare `allow`), and never copied from
generator output. The conformance suite compares `_generated/permissions.json`
to it exactly. The previous test compared the generator's output to the
generator's own derivation function, so a wrong rule would certify itself.
Mutating `derive_permissions` to emit `task: allow` for every role fails the
suite; that was reproduced by mutation during review, and the negative case is
pinned by the fixture comparison rather than by the generator's own function.

**D16 — Body write claims are guarded (T-ALP-A-r2; widened in r3 and r4 after
review).** The `screening-critic` body said "your only write is…" while the
record is `written_by: adapter` and `edit: deny`. A named packet exception
allowed exactly those two capability sentences to be corrected; every
behavioural instruction is unchanged. The conformance suite asserts, for every
role, that a detected write claim implies at least one `written_by: role`
output, and that an all-adapter role makes no detected claim. The guard detects
three shapes:

1. **First-person imperatives** — `your only write`, `Write only`, `you may
   write`.
2. **Third-person declarative claims** — a write verb (`write(s)`, `wrote`,
   `persist(s)`, `save(s)`, `create(s)`, `produce(s)`) whose subject is the role
   itself (`you`, `your`, `the critic`, `the reviewer`, `the role`, `this agent`,
   `the agent`, or the role id with hyphens replaced by spaces) and which names a
   concrete file path (`.json`, `.jsonl`, `.md`, `.yaml`/`.yml`, `.csv`, `.txt`,
   `.html`) within a bounded window of the verb. The subject is the nearest role
   mention in the verb's own clause — the clause, not a character window, is the
   attribution bound — and a clause opened by `it`/`they` inherits the role
   subject of the previous clause, which is how "The critic never repairs the
   batch; it writes …" is caught.
3. **Passive restatements** — `is`/`are`/`was`/`were`/`be` + `written`,
   `persisted`, `saved`, `created`, or `produced` + `by` + a role subject, with a
   concrete path token nearby. "`critique/x.json` is written by the critic" is a
   finding; "`critique/x.json` is written by the harness" is not, because the
   harness is not the role.

A negation guard (`not`, `never`, `cannot`, `no longer`, `do not`, `does not`)
and the path-token requirement keep ordinary prose out: "partial writes", "You
DO NOT: Write code", "the harness writes the file", and "do not rewrite
decisions" are not findings. Through r2 the guard scanned 60 characters *before*
the subject, so a negation in an earlier clause masked a later genuine claim:
"Do not edit the decisions; the critic writes …" and "The critic never repairs
the batch; it writes …" both returned no finding. Since r3 the guard is scoped
to the subject→verb span of the verb's own clause, so a negation suppresses only
when it governs that verb; "The critic never writes `critique/x.json`" remains
clean. **Since r4 the guard also resets at the last clause boundary inside that
span** — `,`, `;`, `and`, `but`, `yet`, `so` — because the r3 span was still
sentence-wide when the two clauses were joined by a conjunction or a comma. The
measured escapes that shape let through, all now findings:

- "The critic never repairs the batch but writes `critique/x.json`."
- "The critic does not edit decisions and writes `critique/x.json`."
- "The critic, which never edits decisions, writes `critique/x.json`."

"The critic never writes `critique/x.json`" has no boundary between subject and
verb and stays clean; so does "The critic, when it judges a batch, never writes
`critique/x.json`", where the negation follows the last boundary.

The detector is still a heuristic, not a proof. Measured escapes that remain
**undetected** and are therefore review-only:

- a claim with **no path token** ("the critic writes the report");
- a subject that is **not** the role ("the pipeline archives the critique");
- **gerund** forms ("writing the critique into the workspace");
- a **hyphenated role id** — the subject list carries `screening critic`, not
  `screening-critic`;
- write verbs **outside the closed list** (`archives`, `generates`,
  `appends`);
- passive forms **outside the enumerated participles** ("the critique ends up
  in…"), and passive clauses whose agent is an unnamed actor;
- a claim **split across clauses** where the later clause's subject is not the
  pronoun `it`/`they`, so no role subject is inherited from the clause before it.

**Measured false positives.** The guard fails closed, and a tester verified that
it reports these legitimate sentences. They are accepted costs, not bugs to be
argued away:

- "The critic checks that the harness writes `critique/x.json`." — the subject is
  the harness, but the nearest role mention in the clause is "the critic".
- "The critic reviews the batch; it is the harness that writes
  `critique/x.json`." — the cleft `it` inherits "the critic", so the clause's
  role subject is the critic even though the writer is the harness.
- "The critic never repairs the batch; it writes nothing into
  `critique/x.json`." — `nothing` is not in the negation set, so the clause reads
  as a positive claim about the path token.

The trade-off is deliberate: a false positive fails CI on a legitimate prompt
edit, and the author's remedy is to reword the sentence (name the writing actor
explicitly, or drop the path token). A false negative certifies a capability
claim the record contradicts, which is the defect this guard exists to catch. The
guard is therefore tuned to fail closed, and this decision does not claim
precision it does not have: the false-positive list above is the measured
over-report rate, not a bound on all possible over-reports.

Review remains the control for the undetected shapes. Negative fixtures prove the
guard fails an adapter-persisted role that makes any of the three detected
shapes, and accepts a role-written output that says it writes.

**D17 — The spec's own example is executable (T-ALP-A-r2; description corrected
in the final pass).** The §2 JSON block is extracted from the specification and
validated with the same `validate_role` the real records use: the test builds a
`roles/<id>.json` path under `tmp_path` and passes the parsed record to the
validator — nothing is written into the real `roles/` tree. The test validates
the example literally, with no field patched in: `mode: subagent` is present in
the §2 example and the test asserts it explicitly. Because `mode` is part of the
schema (D3) and of the example, a missing or changed `mode` fails there. A drift
in any spec-defined field — as happened with R3/R7 before the orchestrator's
amendment — also fails the test.

**D18 — `blinded_from` hides narrative, not written input (final pass, C2).**
`reviewer` is `blinded_from: ["coder"]` and requires the `ChangeSet@1` artifact.
That is not a contradiction: `blinded_from` means the reviewer does not see the
coder's narrative/self-assessment, while the diff and change set are handed over
by the orchestrator as **written input**. The record therefore sources
`ChangeSet@1` from `written-input`, and a general validator now rejects any role
that declares a **required** input whose `from` is one of its own
`blinded_from` roles. A synthetic negative test pins that rule. R6 is an adapter
control; the record must not require an input the adapter would hide.

## 5. Final cleanup pass (authorised after cycle 3)

The decision owner authorised one pass beyond the three-cycle cap to close the
reviewer-confirmed contradictions that remained after cycle 3. The durable task
packet, including the named exceptions (E1–E3) and the review history, is now
`docs/architecture/packet_t_alp_a_role_generation.md`.

| Finding | Fix |
|---|---|
| **C1** Four records (`coder`, `orchestrator`, `reviewer`, `tester`) still had `deny_glob: []`, and the generator exempted them through `read_glob == ["**"]` | The four records now deny the audit journal and `.git/**`. The `**` carve-out is removed: every role must deny both. The separate R7 `family == "**"` exemption remains, because it is gated on the absence of a `written_by: role` output. A conformance assertion checks the rule for all eleven roles. |
| **C2** `reviewer` was `blinded_from: ["coder"]` while requiring `ChangeSet@1` from `coder` | The input is now `from: "written-input"` (D18). A general validator rejects a required input sourced from a role in the record's own `blinded_from`, with a negative test. |
| **C3** R7's critic set was hardcoded, so a future `synthesis-critic` would escape | The set is derived from the records (`critic` in the id or purpose, plus `reviewer`). A synthetic `synthesis-critic` test proves R7 applies without a code change. |
| **C4** R2 was unenforced and `inception-agent` used bare repo-relative globs | `{repo}` is a permitted glob parameter. `inception-agent` reads `{repo}/.agents/skills/**`, `{repo}/.cache/inception_recon/**`, and `{repo}/.mcp.json`; `.git/**` stays as the permitted repo-relative constant. A bare `.agents/skills/**` glob is rejected. T-ALP-A-r3 closes the rest of R2: the segment after `workspaces/` must be `{ws}` and after `runs/` must be `{task_id}`, `{repo}` may not appear in a `write_glob` at any position (r5 widened this from the root alone, so `workspaces/{ws}/{repo}/x.json` and `workspaces/{ws}/x/{repo}.json` are rejected like `{repo}/x.json`), `{repo}/**` is not a valid write target, and a `{repo}`-rooted glob is checked against the source-tree exclusion. T-ALP-A-r4 closes the spelling evasions: `.`/empty segments are rejected and normalised, the source-tree check compares the first segment (so `{repo}/src` and `{repo}/./src/**` fail while `{repo}/srcs/…` passes), and a nested brace group is expanded or rejected as malformed. |
| **C5** D16/D17 overstated what the tests prove | Both decisions now describe the tests that exist. |
| **C6** An independent tester's probe 6 showed the literal-only write-claim guard missed a third-person declarative claim that names a file path | The guard was widened, not weakened: D16 now detects first-person imperatives, role-subject declarative claims with a nearby path token, and (r3) passive restatements, with negation and non-role-subject cases pinned as tests. |

**T-ALP-A-r3 (review repair).** An independent review of the repaired tree
returned `CHANGES_REQUESTED`. All of it is closed here; no record, prompt, spec,
or generated file changed.

| Finding | Fix |
|---|---|
| **HIGH** the negation guard was clause-blind (`subject_start - 60`), so "Do not edit the decisions; the critic writes …" and "The critic never repairs the batch; it writes …" both returned no finding | The guard is now `body[subject_start:verb.start()]` within the verb's own clause; a clause-opening `it`/`they` inherits the previous clause's role subject, and the guard starts at that pronoun's clause. Two regression tests pin both shapes; "The critic never writes …" stays clean. |
| **V1** literal slugs passed R2 (`workspaces/uav-crop-weed-v03/…`, `runs/task-42/…`) | Parameter position is enforced with named errors; both negative cases are tested. |
| **V2** `{repo}` bypassed the write and source-tree guards | `{repo}` is read-only for writes, `{repo}/**` is rejected as a write target, and `{repo}/src/**` is rejected for reads and writes. Only `inception-agent.read_glob` uses `{repo}`, so no record needed a change; a test asserts that. |
| **V3** D10 claimed a `**` glob is rejected while `runs/{task_id}/**` is accepted | D10 now states what is rejected (bare `**`, `{repo}/**`) and what is legal (scoped breadth under a resolved root). |
| **C5** the decision record overstated what the tests prove | D16's limitation list now names the measured escapes; D17 describes how the example is actually validated; D15 no longer cites a report that is not in the tree. |
| **C5/D2** passive restatements were undetected | A passive detector (`is written by <role>` + nearby path) was added, with "written by the critic" and "written by the harness" pinned as opposite cases. |
| **C5/D7** RR6 described R7's `**` route as "`edit: deny`" only | RR6 and D12 now record the `written_by`-keyed exemption and the `bash: ask` write path outside a two-entry `deny_glob`. |

The cleanup changes no permission toggle and no instruction body. The only
generated-file content changes are the capability map's `deny_glob` / `read_glob`
entries; no agent frontmatter changed, so the contract baseline's nine agent
entries are unchanged from the previous pass.

**T-ALP-A-r4 (tester RED + reviewer CHANGES_REQUESTED).** One adversarial case
was still accepted and two validator holes plus a guard gap remained. All seven
findings are closed without touching a record, a prompt, a generated file, or the
specification; the negatives are pinned in the conformance suite.

| Finding | Fix |
|---|---|
| **F1** `.` and empty segments defeated R4 and R2: `workspaces/{ws}/audit/./journal.jsonl` was accepted and did not intersect the journal glob | `validate_glob` rejects `.` and empty segments alongside `..`; `_path_segments` normalises both sides of every intersection/containment check, so `a/./b` and `a/b` are the same path. Two record-level negatives plus a helper assertion pin it. |
| **F2** the `{repo}` source-tree check was a byte-prefix test: `{repo}/./src/**` and `{repo}/src` were accepted as reads | The check compares the first segment after `{repo}` (normalised) against the source-tree names. `{repo}/src` and `{repo}/./src/**` are rejected; `{repo}/srcs/x.json` is accepted, so a sibling is not over-matched. |
| **F3** a nested brace group escaped every rule: `{{repo},foo}/x.json` and `workspaces/{ws}/{{repo}/}x.json` were accepted | `expand_braces` now finds the outermost balanced group and recurses into the alternatives it produces; a group surviving expansion with a brace inside it is rejected as a malformed brace group. A literal-segment alternation (`{a,b}` under `{ws}`) is still accepted and is pinned as such. |
| **F4** the negation guard was sentence-scoped: `The critic never repairs the batch but writes …`, `does not edit decisions and writes …`, and `, which never edits decisions, writes …` returned no finding | The guard resets at the last clause boundary between subject and verb (`,`, `;`, `and`, `but`, `yet`, `so`), and the subject search is bounded by the clause instead of a 40-character window (which truncated the third sentence before the subject). "The critic never writes …" and a comma-delimited negation *after* the boundary stay clean. |
| **F5** `test_repo_parameter_may_not_root_a_write_glob` matched `"read-only"`, which every `{repo}` message contains | The two write-root branches now assert their own text (`is the repository root`, `rooted at the read-only`), so deleting either branch fails its test. |
| **F6** D16 claimed precision the guard does not have | D16 now lists the three measured false-positive classes next to the known false negatives and states the trade-off: the guard fails closed, a legitimate prompt edit can fail CI, and the author's remedy is to reword. |
| **F7** `reviewer` is id-keyed rather than purpose-derived | The amended R7 defines the set as id-or-purpose `critic` plus `reviewer`, which is exactly what `_is_critic` implements; a new test derives the set independently from that sentence and asserts it equals the generator's set. Recorded as RR10. |

## 6. Residual risks (out of scope, explicitly not fixed)

- **RR1** Git mutation still runs through `bash` for `orchestrator`/`coder`; the
  adapter does not sandbox it in Phase A. Phase E must route git mutation through
  a privileged helper rather than a role write glob.
- **RR2** `network` is recorded and checked for legality, but the generated
  opencode permission map does not express it; `webfetch` is not part of the map.
- **RR3** opencode cannot enforce a `write_glob` **or** a `deny_glob`. Phase A
  makes the declaration honest; the glob only becomes enforceable with the
  Phase-E adapter. The adapter must apply `deny_glob` to writes and keep
  `read_glob` as the read allowlist (D12); a read-denial implementation would
  block critics from reading the artifacts they judge.
- **RR4** Instruction bodies retain status vocabularies that are not in the closed
  refusal registry (`BLOCKED_STALE_PARENT`, `NOT_MY_SCOPE`, `FAIL_ESCALATE`).
  Bodies are preserved verbatim by design; normalising them belongs to Phase B.
- **RR5** The `screening-critic` prose mismatch ("your only write is the assigned
  critique") was repaired under D16's sentence-scoped exception. The same phrasing
  still appears in `extraction-critic`, where it is *true*: that role has a
  `written_by: role` output and keeps `edit`. Any future adapter-persisted role
  that repeats the claim fails the D16 conformance guard instead of drifting.
- **RR6** `reviewer` reads the whole tree, so R7 cannot be expressed as a deny
  glob without denying its own output. It takes R7's single `**` exemption
  (spec §3, "Single exemption"), which is keyed on `written_by`: every output is
  `written_by: adapter`, so the role writes nothing of its own, and its
  `deny_glob` covers the artifact families it must not touch. A future critic
  with `**` that gains a role-written output loses the exemption and fails the
  gate. Until Phase E this is a capability fact (`edit: deny`) plus a two-entry
  `deny_glob`, not a filesystem view — and `bash: ask` remains an
  approval-gated write path outside that `deny_glob`. Phase E must close both;
  until then they are declared residual risks rather than satisfied rules.
- **RR7** `read_glob: []` is accepted by the schema, and no rule checks that the
  files a role declares in `inputs` are actually reachable under its `read_glob`.
  A record could therefore declare an input it cannot read. Phase B, where
  envelopes carry the resolved inputs, is the right place to add that check.
- **RR8** `read_glob: ["**"]` is available to any role, not only the dev-loop
  roles that need it today. A future record could use it to see a peer's output
  and silently weaken `blinded_from`: R6 is adapter-enforced, but the record's own
  read allowlist would contradict the blind. The generator has no role-level
  allowlist for `**`; this is a review question, not a schema rule.
- **RR10** `reviewer` is still **id-keyed**, not purpose-derived: R7's set is a
  role whose `id` or `purpose` contains `critic`, **plus `reviewer`** by name,
  because the reviewer's purpose describes adversarial review without using the
  word. The amended specification states exactly that definition, and
  `_is_critic` implements it literally, so the residual is not a mismatch between
  record and code — it is that a role which is a critic in substance but says
  neither "critic" nor is `reviewer` escapes R7. The purpose wording is the hook,
  and review is the control. A conformance test derives the set independently
  from R7's sentence (rather than calling `_is_critic`) and asserts it equals
  `{extraction-critic, reviewer, screening-critic}`, so a change to the predicate
  fails the gate.
- **RR11 — Path comparison folds case, and non-canonical segments are rejected
  (T-ALP-A-r5).** The validator runs on win32 and default macOS volumes, where
  `AUDIT` names `audit` and the path API strips a trailing dot or space from a
  segment. Before this repair `workspaces/{ws}/audit./journal.jsonl`,
  `workspaces/{ws}/AUDIT/journal.jsonl`, and
  `workspaces/{ws}/audit/journal.jsonl.` all opened the real journal while
  `globs_intersect` reported no intersection, so R4 certified a write the
  specification forbids (§4). `globs_intersect`, `glob_within`, and the `{repo}`
  source-tree comparison now fold case, and `validate_glob` rejects any segment
  ending in `.` or whitespace alongside `.`/`..`/empty segments. Only comparison
  folds: the declared spelling is never rewritten, and `INDEX.md`,
  `SCREENING_CRITERIA.md`, `extracted/A/{stu}.json`, and all 88 shipped globs
  still validate. A resolver that normalises differently (for example a Linux
  container) cannot reintroduce the alias for the journal or the source trees:
  the trailing-dot/space spellings are rejected before any comparison, and the
  case-folded spellings alias only on a host that folds case — the same
  condition under which the comparison folds. This is not a general
  case-canonicalisation of the tree: other case-insensitive aliases under
  `workspaces/{ws}/` (for example `Synthesis/` for `synthesis/`) are accepted
  and remain a Phase-E resolver concern, as does any resolver whose normalisation
  differs from the host's.

  **r5 extension — the remaining win32 alias spellings are rejected outright.**
  Review measured `workspaces/{ws}/audit/journal.jsonl::$DATA` as **accepted**
  and writing the real journal: `open(..., "a")` appends to `journal.jsonl` and
  creates no new file, while the last segment compares as
  `journal.jsonl::$DATA`, so `globs_intersect` saw no intersection. Enumerating
  the class on this host found a second, unreported alias: the volume generates
  NTFS **8.3 short names**, so `workspaces/{ws}/audit/JOURNA~1.JSO` resolves to
  the same inode as `journal.jsonl` and an append through it changes the journal
  — also accepted before this pass. `validate_glob` now rejects three segment
  spellings, each with a named error, before any comparison runs:

  - **`:`** — an NTFS alternate data stream. `journal.jsonl::$DATA` is the file's
    *default* stream (the journal's own bytes, measured) and
    `journal.jsonl:stream` creates a stream inside the journal file. Measured:
    `journal.jsonl:` alone raises `EINVAL` on this host and does not alias, but
    it is rejected too, so no resolver-specific colon handling is relied on.
  - **`~`** — the NTFS 8.3 short-name marker. Rejected in any segment (not only
    `~<digit>`), because no legitimate role glob needs it and the marker is what
    turns a long filename into a short-name alias.
  - **Control characters, including NUL** — Python's path helpers truncate at
    NUL and the NTFS API rejects or silently rewrites other control bytes, so a
    segment carrying one cannot be compared reliably with the paths it must not
    intersect. Checked on the raw pattern, so a brace alternative cannot hide one.

  The conformance suite pins each rule at `validate_role` (the record boundary),
  pins the brace-hidden shapes `{audit.,x}/journal.jsonl`, `{audit ,x}/journal.jsonl`
  and `{journal.jsonl:a,x}` (review found the first untested), and includes a
  win32-guarded test that asserts the two measured aliases really do reach the
  journal, self-skipping where the volume has no stream or 8.3 support. A
  mutation that disables any of the three rules fails 19 tests.

  The positive side is still incomplete and is **carried to Phase B**: there is
  no validation-time character whitelist, only a *test-time* drift guard that
  asserts every character in the 88 shipped globs is drawn from the documented
  set (letters, digits, `_ - . * ? [ ] { } / ~`). A future record that introduces
  a new segment character fails that test rather than silently widening the
  alphabet the alias rules must reason about, but the validator itself still
  accepts any character not explicitly denied. Closing that — an allowlist in
  `validate_glob` — is a Phase-B contract decision because it changes what a
  legal glob is, not just which spellings alias.


## 7. Reproduction

```
uv run python scripts/generate_agent_roles.py --check
uv run pytest tests/conformance/test_agent_role_permissions.py -q
uv run pytest tests/conformance/test_contract_baseline.py -q
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/check_context_policy.py --check
uv run ruff check scripts/
```
