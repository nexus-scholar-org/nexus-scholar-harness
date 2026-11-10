# Research UI track

Index and context boundary for the UI track. The application lives in
`apps/research-ui/`; this directory holds its governing spec.

## What governs the UI track

| Purpose | File |
|---|---|
| Per-screen specs (build source since the production plan) | `docs/ux/phase0-inception/final/`, `docs/ux/phase1-discovery/final/`, `docs/ux/phase2-screening/final/` |
| Discovery routes, codes and decisions (Phase 1 screens, built in M3b-api, M3d-engine, M3c-screens) | [`DISCOVERY_API_PACKET.md`](./DISCOVERY_API_PACKET.md) |
| Other API contracts the screens read | [`screening-api-contract.md`](../screening-api-contract.md), [`inception-api.md`](../inception-api.md), [`workspaces-api.md`](../workspaces-api.md), [`console/SPECS.md`](../console/SPECS.md) |
| Work packets UI-01 to UI-10 (mostly history; see its status note) | [`AGENT_WORK_PACKETS.md`](./AGENT_WORK_PACKETS.md) |
| Agent boundary and implementation rules for the app | [`apps/research-ui/AGENTS.md`](../../../apps/research-ui/AGENTS.md) |
| Verification-gates ledger (executable / open / `NOT_VERIFIED`) | [`apps/research-ui/docs/GATES.md`](../../../apps/research-ui/docs/GATES.md) |
| Design system: the brand book replaced `VISUAL_DIRECTION.md` on 2026-11-03 (`docs/decisions.md`); its non-conflicting parts stay as amendments | [`docs/ux/brand/BRAND_BOOK.md`](../../ux/brand/BRAND_BOOK.md), [`tokens.json`](../../ux/brand/tokens.json); history: [`VISUAL_DIRECTION.md`](../../../apps/research-ui/docs/VISUAL_DIRECTION.md) |
| Internationalization policy | [`apps/research-ui/docs/I18N.md`](../../../apps/research-ui/docs/I18N.md) |

## Read set for a UI task

The screen's final spec (or, for older work, the assigned packet section in `AGENT_WORK_PACKETS.md`), plus
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
