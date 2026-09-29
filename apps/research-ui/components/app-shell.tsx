import type { ReactNode } from "react";

import { MobileNav } from "./mobile-nav";
import { PrimaryNav } from "./primary-nav";

/**
 * The id the skip link targets.
 *
 * This constant is the contract between the layout and every route. The shell
 * renders `<main id={MAIN_CONTENT_ID} tabIndex={-1}>` around the route's
 * content. The `tabIndex={-1}` makes that landmark a programmatic skip-link
 * target without adding a stop to the tab order, so a focusable selector of the
 * form `[tabindex]:not([tabindex="-1"])` still matches exactly the real tab
 * stops.
 */
export const MAIN_CONTENT_ID = "main-content";

/**
 * The application shell (packet UI-01).
 *
 * Owns, in document order: the skip link, the banner landmark with the project
 * identity and the demonstration-data marker, the primary navigation and the
 * narrow-screen disclosure, the route's own content, and a minimal footer.
 *
 * The banner is a *sibling* of `main`, never an ancestor or descendant of it.
 * Nested banner/main is a real landmark defect: assistive technology then
 * reports the site identity as part of the page's main content.
 *
 * The shell owns **exactly one** `main` landmark, and it is the skip link's
 * target. Because a layout renders `{children}`, that landmark wraps the route's
 * content, so a route must **not** render a `main` of its own: a nested second
 * one is both a `critical` `landmark-one-main` violation and a dead skip link,
 * because the shell's skip link would land on the outer, near-empty landmark.
 *
 * The obligation is therefore one-directional, and the shell discharges it for
 * every route rather than leaving it to each route author. See
 * `tests/shell.test.tsx` and the landmark-contract note in `GATES.md` §4.3.
 */
export function AppShell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <>
      <a className="skip-link" href={`#${MAIN_CONTENT_ID}`}>
        Skip to main content
      </a>

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-4 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
            <div>
              <p className="text-sm font-semibold text-blue-700">Nexus Scholar</p>
              <p className="text-xs text-slate-500">Research integrity you can inspect</p>
            </div>
            {/*
              The demonstration-data marker is a safety label, not chrome: it is
              rendered in the always-present banner, at every viewport width, and
              never inside the mobile disclosure.
            */}
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-amber-600/20">
              Demonstration data
            </span>
            <PrimaryNav />
          </div>
          <MobileNav />
        </div>
      </header>

      {/*
        The route's content, inside the shell's `main`. The route renders no
        landmark of its own; see the note on `AppShell` above.
      */}
      <main id={MAIN_CONTENT_ID} tabIndex={-1}>
        {children}
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
          <p className="text-xs leading-5 text-slate-500">
            Read-only demonstrator. The Python harness remains authoritative for contracts, identity,
            acceptance, toolkit execution and audit events.
          </p>
        </div>
      </footer>
    </>
  );
}
