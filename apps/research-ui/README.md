# Nexus Scholar Research UI

The researcher's app for Phases 0 to 2: inception, discovery and screening.
Every screen reads a live workspace (for inception, a draft) through the
engine; none reads workspace files directly.

Routes (`/<locale>/…`, locales `en`, `fr`, `ar`):

| Route | Screen |
| :-- | :-- |
| `/workspaces` | the workspaces screen (spec 00); `/<locale>` forwards here |
| `/inception` | inception drafts and resume (Phase 0 spec 08) |
| `/inception/scope`, `/explore`, `/direction`, `/shape`, `/criteria`, `/review`, `/done` | the inception steps (Phase 0 specs 01 to 07; `?draft=`). Explore (02) and Direction (03) read the recon routes of the draft (M4d) |
| `/discovery` | the discovery entry page |
| `/discovery/plan`, `/recall`, `/harvest`, `/dedup`, `/report`, `/handoff` | the discovery steps (Phase 1 specs 01 to 03, 05, 06, 08); Import (04) is `/screening/import?return=discovery` |
| `/screening/home`, `/import`, `/prepare`, `/triage`, `/proposals`, `/agreement`, `/publish`, `/export` | the screening steps (Phase 2 specs 01 to 03, 06, 07, 09 to 11); `/screening` forwards to the home |

The header (`components/site-header.tsx`) holds the wordmark, the three
destinations (Workspaces, Discovery, Screening), the language menu and the theme; below `lg` they move into one
menu dialog. The demonstration screens (overview, the single-record screening
page, corpus, lineage, audit) and their mock data were removed on 2026-11-05;
see `docs/decisions.md`.

## Local commands

```powershell
cd apps/research-ui
npm install
npm run typecheck
npm run test
npm run build
npm run dev
npm run test:browser   # Playwright, tests-browser/
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

In development the screens read the local Harness Console through the proxy:

```powershell
# both terminals share one per-launch token (any long random string)
$env:NEXUS_CONSOLE_TOKEN = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
# terminal 1 — the backend
uv run scholar-harness serve --workspace workspaces/uav-crop-weed-v03 --port 8765
# terminal 2 — the product surface (set the same NEXUS_CONSOLE_TOKEN first)
cd apps/research-ui && npm run dev
# then open http://localhost:3000/en/workspaces
```

The console requires `Authorization: Bearer <token>` on every route except
`/healthz`, answers only on a loopback `Host`, and refuses non-loopback
`Origin`s (INC-01). If `NEXUS_CONSOLE_TOKEN` is not set, `serve` generates a
token and prints it once; start the UI with that value. The proxy adds the
header server-side, so the browser never holds the token. It also refuses a
request addressed to a non-loopback host and a POST whose `Origin` is not the
app's own.

Reads, event streams and the allowlisted screening POSTs go to this
application's own origin at `/api/console/...`; the route handler
`app/api/console/[...path]/route.ts` forwards them server-side. SSE responses
(`/api/v1/events/tick`, `/api/v1/jobs/{id}/stream`, the recon job events
under `/api/v1/inception/drafts/{id}/recon/jobs/{job}/events` and the discovery
job events under `/api/v1/discovery/jobs/{id}/events`) are streamed through,
not buffered (`STREAM_PATHS` in the route handler). Set
`NEXUS_CONSOLE_URL` to move that upstream (it must be a plain loopback
`http(s)` origin; default `http://127.0.0.1:8765`). The browser never sees the
console's port, and the console's GET-only CORS policy stays as reviewed.

`?console=http://127.0.0.1:8765` is a test-only override for pointing a live
screen at a console directly; it is not part of normal use.

## Visual direction

Since 2026-11-03 the brand book (`docs/ux/brand/BRAND_BOOK.md`, tokens in
`docs/ux/brand/tokens.json`, generated into `app/theme.css` by `npm run tokens`)
is the design system (plan §3, `docs/decisions.md`); the parts of
VISUAL_DIRECTION that do not conflict with it are kept as amendments.
[`VISUAL_DIRECTION.md`](docs/VISUAL_DIRECTION.md) was the design system of record for
this application — product character, six named principles, the semantic palette
roles, the two typeface roles, spacing and radius rules, provenance treatment,
and use/avoid patterns. Read it before changing anything visual; UI-02 through
UI-06 extend it to further routes and must not invent a second language.

Its values live in `app/globals.css`'s `@theme`. Components consume the **roles**
(`bg-paper`, `text-ink-muted`, `border-rule`, `text-evidence`, …). A raw hex or
a raw `slate-*`/`blue-*` utility in a component is a defect, and needs a written
reason to become one.

Two constraints that are easy to undo by accident:

- **No font request leaves the machine.** The brand faces (Literata, Public
  Sans, IBM Plex Mono) are bundled from `@fontsource` packages in
  `app/[locale]/layout.tsx`. Do not add a font CDN or a `fonts.googleapis.com` link.
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
