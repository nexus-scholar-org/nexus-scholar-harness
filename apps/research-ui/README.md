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

What the test suite does and does not prove is recorded in `docs/GATES.md`. Real
browser verification (screenshots, 375px/1440px rendering, axe on rendered CSS)
runs separately via `npm run test:browser`; `docs/GATES.md` §3 is the authoritative
record of what it measured and what is still open.

Do not commit `node_modules/` or `.next/`; both are ignored.

## Live data and the console proxy

Every screen defaults to labelled demonstration data and performs no request.
Append `?source=live` to read the local Harness Console instead:

```powershell
# terminal 1 — the backend
uv run scholar-harness serve --workspace workspaces/uav-crop-weed-v03 --port 8765
# terminal 2 — the product surface
cd apps/research-ui && npm run dev
# then open http://localhost:3000/en/screening?source=live
```

Reads and the allowlisted screening POSTs go to this application's own origin
at `/api/console/...`; the route handler
`app/api/console/[...path]/route.ts` forwards them server-side. Set
`NEXUS_CONSOLE_URL` to move that upstream (it must be a plain loopback
`http(s)` origin; default `http://127.0.0.1:8765`). The browser never sees the
console's port, and the console's GET-only CORS policy stays as reviewed.

`?console=http://127.0.0.1:8765` is a test-only override for pointing a live
screen at a console directly; it is not part of normal use.

Each live screening row can record a draft decision. That posts one record to
the console's sanctioned draft writer (merged by workspace id, so siblings are
untouched) and the page re-reads the batch. A saved draft is **not** an
approval: coverage, pairing, approval and publication still run separately, and
saving never publishes.

The corpus screen reads paged rows from `GET /api/v1/ui/corpus/{kind}`
(`limit`/`offset`, plus a server-side `q` filter). The excluded set is 13.5k
rows on the pilot workspace, so it is never downloaded whole: the screen asks
for one 25-row page at a time, and "show more" requests the next offset. The
excluded page is only requested when the reader clicks "load excluded".

## Visual direction

[`VISUAL_DIRECTION.md`](docs/VISUAL_DIRECTION.md) is the design system of record for
this application — product character, six named principles, the semantic palette
roles, the two typeface roles, spacing and radius rules, provenance treatment,
and use/avoid patterns. Read it before changing anything visual; UI-02 through
UI-06 extend it to further routes and must not invent a second language.

Its values live in `app/globals.css`'s `@theme`. Components consume the **roles**
(`bg-paper`, `text-ink-muted`, `border-rule`, `text-evidence`, …). A raw hex or
a raw `slate-*`/`blue-*` utility in a component is a defect, and needs a written
reason to become one.

Two constraints that are easy to undo by accident:

- **No web font.** Both typeface roles are local stacks. Do not add `@font-face`,
  a font CDN, or a `fonts.googleapis.com` link.
- **`--color-focus` is the one focus ring.** `a:focus-visible` in
  `app/globals.css` and `.skip-link:focus` must both read it;
  `tests-browser/focus-visibility.spec.ts` cross-checks them, so moving one and
  not the other fails the suite even though every control still looks focused.

## Guardrails

- Never mint contract, study, document, chunk, or artifact identities in TypeScript.
- Never write `workspaces/**` files from Next.js server actions or browser code.
- Never append directly to `audit/journal.jsonl`.
- Never import source from `tools/**` into the frontend.
- Keep mock/demo data visibly labelled.
- Treat rejection and uncertainty as first-class visible states.

See `docs/architecture/research_ui/AGENT_WORK_PACKETS.md`, the governance set under
this directory's `docs/` (`GATES.md`, `VISUAL_DIRECTION.md`, `I18N.md`), and this
directory's `AGENTS.md` before implementation.
