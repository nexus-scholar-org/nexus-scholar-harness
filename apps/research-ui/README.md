# Nexus Scholar Research UI

Researcher-facing Next.js application for demonstrating and eventually driving the Nexus Scholar harness.

The scaffold is intentionally read-only and uses `lib/mock-project.ts`. It does not read workspace files directly and contains no Contract v1 implementation. The future API boundary belongs in `src/scholar_harness/api/`; the browser consumes presentation models derived by that boundary.

## Local commands

```powershell
cd apps/research-ui
npm install
npm run typecheck
npm run test
npm run build
npm run dev
```

`npm run typecheck` and `npm run build` must pass before a change is considered
reviewable. `npm run test` runs the component/unit suite in-process with Vitest
on jsdom; it needs no server and no browser. `npm run dev` starts the Next.js
development server for manual inspection and is not used by the test run.

What the test suite does and does not prove is recorded in `GATES.md`. Real
browser verification (screenshots, 375px/1440px rendering, axe on rendered CSS)
runs separately via `npm run test:browser`; `GATES.md` §3 is the authoritative
record of what it measured and what is still open.

Do not commit `node_modules/` or `.next/`; both are ignored.

## Guardrails

- Never mint contract, study, document, chunk, or artifact identities in TypeScript.
- Never write `workspaces/**` files from Next.js server actions or browser code.
- Never append directly to `audit/journal.jsonl`.
- Never import source from `tools/**` into the frontend.
- Keep mock/demo data visibly labelled.
- Treat rejection and uncertainty as first-class visible states.

See `docs/architecture/research_ui/README.md` and this directory's `AGENTS.md` before implementation.
