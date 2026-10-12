# Research UI track

Index and context boundary for the UI track. The application lives in
`apps/research-ui/`; this directory holds its governing spec.

## What governs the UI track

| Purpose | File |
|---|---|
| Work packets (spec of record: UI-01 … UI-07) | [`AGENT_WORK_PACKETS.md`](./AGENT_WORK_PACKETS.md) |
| Agent boundary and implementation rules for the app | [`apps/research-ui/AGENTS.md`](../../../apps/research-ui/AGENTS.md) |
| Verification-gates ledger (executable / open / `NOT_VERIFIED`) | [`apps/research-ui/docs/GATES.md`](../../../apps/research-ui/docs/GATES.md) |
| Visual design system of record | [`apps/research-ui/docs/VISUAL_DIRECTION.md`](../../../apps/research-ui/docs/VISUAL_DIRECTION.md) |
| Internationalization policy | [`apps/research-ui/docs/I18N.md`](../../../apps/research-ui/docs/I18N.md) |

## Read set for a UI task

The assigned packet section in `AGENT_WORK_PACKETS.md`, plus
`apps/research-ui/AGENTS.md`, `apps/research-ui/README.md`, and the governance
set under `apps/research-ui/docs/` (`GATES.md`, `VISUAL_DIRECTION.md`,
`I18N.md`). Keep the read set to the active capsule and these files; do not load
E3 handoffs, kit internals, or Contract v1 history unless a packet explicitly
makes them relevant.

## Historical note — the predecessor README (do not cite it)

Packets UI-01C and UI-01D cite a `docs/architecture/research_ui/README.md`
(§"Internationalization policy", lines 64–75; also line 91) as a mandatory
read. That file was **untracked** and is **not recoverable from git history**
(`git log --all -- docs/architecture/research_ui/README.md` is empty), so those
line-number citations cannot be followed to matching content.

- The internationalization policy now lives in
  `apps/research-ui/docs/I18N.md`.
- The mandatory-read role is now served by `AGENT_WORK_PACKETS.md` plus the
  governance set above; `apps/research-ui/AGENTS.md` rule 1 was retargeted
  accordingly in the UI-04a maintenance pass.
- Do not create new citations to this file's line numbers; cite the file above.
