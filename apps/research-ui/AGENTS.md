# Research UI agent boundary

This file governs work under `apps/research-ui/`.

## Purpose

Build a researcher-facing view/controller over Nexus Scholar. The Python harness remains authoritative for contracts, identity, acceptance, toolkit execution, workspace mutation, and audit events.

## Allowed without an API packet

- Page shells, navigation, responsive layout, accessibility, and visual states.
- Presentation-only TypeScript interfaces under `lib/`.
- Clearly labelled fixture data under `lib/mock-*.ts`.
- Component tests and visual/browser tests contained in this application.
- Tailwind Plus component adaptation through the local `tailwind-plus` MCP.

## Forbidden

- Editing `src/scholar_harness/`, `contracts/`, `tools/`, `.agents/plugins/`, or `workspaces/`.
- Inventing or computing Nexus Scholar identifiers, fingerprints, checksums, acceptance results, or refusal codes.
- Calling kit CLIs directly from Node or browser code.
- Writing workspace JSON, Markdown, BibTeX, PDFs, vector stores, or `audit/journal.jsonl`.
- Presenting mock data without the visible `Demonstration data` label.
- Copying the local Tailwind Plus catalog or complete templates into this repository.

## Implementation rules

1. Read the assigned work packet (`docs/architecture/research_ui/AGENT_WORK_PACKETS.md`), this directory's `README.md`, the governance set under `apps/research-ui/docs/` (`GATES.md`, `VISUAL_DIRECTION.md`, `I18N.md`), and the active task context capsule rules from `docs/architecture/agent_context_protocol.md`.
2. Work on exactly one screen or cross-cutting UI primitive.
3. Search Tailwind Plus by capability; adapt only the component needed.
4. Use semantic HTML, keyboard navigation, visible focus, and text labels in addition to color.
5. Keep server data behind `lib/api-client.ts` once that boundary exists.
6. Use mock data only until an API contract is approved.
7. Run targeted type, component, and browser checks for the changed surface.
8. Report files changed, screenshots checked, tests run, and any missing API capability.

## Context boundary

UI work is its own context domain. For a UI task, keep the repeated reading set
to the active capsule, this file, the assigned UI packet, and the API contract
being displayed. Do not load E3 handoffs, kit internals, or Contract v1 history
unless an approved UI/API boundary packet explicitly makes them relevant.

## Definition of done

- Responsive at narrow and desktop widths.
- Keyboard reachable with meaningful headings and labels.
- Loading, empty, error/refused, and populated states exist where applicable.
- No domain decision is made in frontend code.
- No protected path outside `apps/research-ui/` changed.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
