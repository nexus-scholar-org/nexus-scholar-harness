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
 * The application shell (packet UI-01; visual direction packet UI-01c).
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
 *
 * Visually, the banner and footer are `--color-leaf`: a slightly brighter sheet
 * than the `--color-paper` ground of the route, divided by hairlines rather than
 * by floating cards. That is the whole chrome treatment — two rules, one type
 * swap, no shadow and no radius anywhere in it.
 */
export function AppShell({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <>
      <a className="skip-link" href={`#${MAIN_CONTENT_ID}`}>
        Skip to main content
      </a>

      <header className="border-b border-rule-strong bg-leaf">
        <div className="mx-auto max-w-7xl px-6 py-5 lg:px-8">
          <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
            <div className="min-w-0">
              <p className="font-display text-lg leading-tight text-ink">Nexus Scholar</p>
              {/*
                The product's one-line position. It was the F2 thin-margin site
                at 4.76:1; `--color-ink-muted` on `--color-leaf` measures
                9.19:1. See `GATES.md` §3.7.
              */}
              <p className="mt-1 text-xs leading-5 text-ink-muted">Research integrity you can inspect</p>
            </div>
            {/*
              The demonstration-data marker is a safety label, not chrome: it is
              rendered in the always-present banner, at every viewport width, and
              never inside the mobile disclosure.

              It is a provenance stamp, which is one of the two things A4 reserves
              the stamp shape for, so the square hairline box is deliberate
              rather than a missing `rounded-full`. `tests/home-page.test.tsx`
              pins it inside this `<header>`, so it cannot be moved out of the
              banner and demoted to page content.
            */}
            <span className="self-center border border-warning/50 px-2.5 py-1 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.14em] text-warning">
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

      <footer className="border-t border-rule bg-leaf">
        <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
          {/*
            The read-only authority statement. The other F2 thin-margin site, and
            repaired on the same token: 4.76:1 before, 9.19:1 now.
          */}
          <p className="max-w-3xl text-xs leading-5 text-ink-muted">
            Read-only demonstrator. The Python harness remains authoritative for contracts, identity,
            acceptance, toolkit execution and audit events.
          </p>
        </div>
      </footer>
    </>
  );
}
