# Agent Context Protocol

**Status:** Active. Applies to every development, review, testing, and UI task.

## Purpose

Scientific and contract work needs authoritative sources, but repeatedly loading
the complete history of a packet wastes context and can cause compaction before
an agent reaches the changed code. This protocol keeps the sources authoritative
while making the repeated working set small and explicit.

## Two context layers

| Layer | Read when | Contents |
|---|---|---|
| Stable context | Once when a task starts, or again only after an escalation trigger | The governing contract/architecture decision, the assigned handoff, the relevant kit or UI guidance, and the test-gate policy. |
| Working context | Every implementation, review, or repair round | The task context capsule, current commit, changed paths/diff, assigned acceptance IDs, open findings, known baseline failures, and selected commands. |

Historical reports are evidence, not mandatory prompt material. Cite their
commit SHA and relevant file/line range from the capsule instead of pasting
their complete text into later rounds.

## Required task context capsule

The orchestrator creates and maintains one short capsule for every active task.
It may live in the task packet, a PR body, or an active-task file, but it must
contain only the fields below and must be updated after every published repair.

```yaml
task: E3-T-110
delivery_lane: STANDARD
owner_repo: nexus-scholar-org/scholar-rag-kit
base_sha: <immutable merge base>
head_sha: <current candidate>
allowed_paths: []
immutable_boundaries: []
acceptance_ids: []
open_findings: []
known_baseline_failures: []
evidence:
  - command: <exact command>
    commit: <tested sha>
    result: <pass/fail and count>
next_gate: inner|checkpoint|pr|closure
stable_sources:
  - <path@sha plus needed line range>
```

The capsule is a routing index, not a second specification. It must link to
the governing source instead of copying or paraphrasing contract rules.

## Role protocol

### First task round

The coder, reviewer, and tester each read the stable sources named in the
capsule once. The orchestrator records the resolved SHAs, relevant line ranges,
and known baseline failures in the capsule. Each role then works from the
capsule plus its assigned paths.

### Implementation and review rounds

- A coder reads the capsule, its assigned acceptance IDs, and changed files.
- A reviewer reads the capsule, the declared immutable boundaries, the diff,
  and the cited source slices necessary to test a claim. Independence means
  independently checking evidence, not rereading unrelated history.
- A tester reads the capsule and the selected gate commands. It does not run a
  broader suite unless the delivery lane or an invalidation trigger requires it.
- A repair packet contains only the finding IDs, required outcome, changed-path
  allowance, and the evidence invalidated by the repair.

## Escalation triggers

An agent must reread the affected stable source and update the capsule when a
repair changes any immutable boundary, public API/CLI/MCP behavior, artifact
identity or publication semantics, dependency/pin state, merge base, or gate
selection. Otherwise, no role should reload the complete handoff or prior
transcript.

## UI isolation

UI work is a separate context domain. A UI agent reads
`apps/research-ui/AGENTS.md`, the assigned UI packet, the active UI capsule,
and only the API contract it displays. It must not load E3 handoffs, toolkit
internals, or Contract v1 history unless a separately approved UI/API boundary
packet explicitly requires it. Backend agents likewise do not load UI design
history for kit work.

## Packet-size rule

Task prompts must name a bounded reading set: normally the capsule, no more
than four stable sources, and exact line ranges where practical. If the task
cannot be stated within that envelope, split it before dispatch. New unrelated
P3 observations are recorded as follow-up tasks under the delivery-lane policy,
not appended to the current context.
