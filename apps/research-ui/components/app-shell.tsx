"use client";

import type { ReactNode } from "react";

import { usePathname } from "next/navigation";

import { translate, type Locale } from "@/i18n";

import { LocaleSwitcher } from "./locale-switcher";
import { MobileNav } from "./mobile-nav";
import { PrimaryNav, currentItemIdFromPathname } from "./primary-nav";

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
 * identity and the demonstration-data marker, the primary navigation, the
 * narrow-screen disclosure, the locale selector, the route's own content, and a
 * minimal footer.
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
 *
 * **Localization (packet UI-01d).** Every string in this file is now a catalog
 * lookup, and `locale` is a required prop rather than something read from a
 * context (D-I18N-05): the shell is rendered by the locale layout, the prop makes
 * the language an explicit input, and a component test can render any locale
 * without a provider. The `<html lang dir>` pair is owned one level up by
 * `LocaleDocument` and is not repeated here; nothing in this file declares a
 * direction.
 *
 * **Client boundary (packet UI-04).** This file became a client component for
 * exactly one reason: packet UI-04 added a second route, so "which nav surface
 * is current" can no longer be a constant. The shell reads the pathname with
 * `usePathname()` once, derives `currentItemId` from it with
 * `currentItemIdFromPathname` (exported from `primary-nav.tsx`, which stays a
 * plain module so server components can still import `PRIMARY_NAV_ITEMS` as a
 * value), and hands that id to both nav presentations. Three consequences are
 * worth stating rather than discovering:
 *
 * - the derivation uses the router's own pathname, which the server render and
 *   the first client render see identically (it is seeded from the RSC payload),
 *   so there is nothing to mismatch at hydration;
 * - `tests/shell.test.tsx` and the other in-process suites already mock
 *   `next/navigation`, so they keep rendering the real shell unchanged;
 * - `MAIN_CONTENT_ID` still lives here and is still imported only by that test
 *   file, never by a server component — a server import of this module would
 *   receive a client reference proxy for it rather than the string.
 *
 * The `LocaleSwitcher` is the **last** item in the header, after `MobileNav`
 * (D-I18N-11). That position is load-bearing and not aesthetic: it keeps the
 * measured focus-indicator counts in `tests-browser/responsive-nav.spec.ts` and
 * `tests-browser/focus-visibility.spec.ts` correct without editing their press
 * counts, and it confines the indicator's growth to the wide viewport's union. It
 * also carries no breakpoint of its own — a reader at 375px gets the same
 * affordance as a reader at 1440px, because with the URL as the only source of
 * locale truth a hidden selector would leave a narrow screen no way to change
 * language at all.
 */
export function AppShell({
  locale,
  children,
}: Readonly<{ locale: Locale; children: ReactNode }>) {
  const pathname = usePathname();
  const currentItemId = currentItemIdFromPathname(pathname, locale);

  return (
    <>
      <a className="skip-link" href={`#${MAIN_CONTENT_ID}`}>
        {translate(locale, "a11y.skipToMain")}
      </a>

      <header className="border-b border-rule-strong bg-leaf">
        <div className="mx-auto max-w-7xl px-6 py-5 lg:px-8">
          <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
            <div className="min-w-0">
              <p className="font-display text-lg leading-tight text-ink">
                {translate(locale, "brand.productName")}
              </p>
              {/*
                The product's one-line position. It was the F2 thin-margin site
                at 4.76:1; `--color-ink-muted` on `--color-leaf` measures
                9.19:1. See `GATES.md` §3.7.
              */}
              <p className="mt-1 text-xs leading-5 text-ink-muted">
                {translate(locale, "shell.tagline")}
              </p>
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
            <span className="self-center border border-warning/50 px-2.5 py-1 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.14em] text-warning rtl:tracking-normal rtl:text-[0.75rem]">
              {translate(locale, "safety.demoDataLabel")}
            </span>
            <PrimaryNav locale={locale} currentItemId={currentItemId} />
          </div>
          <MobileNav locale={locale} currentItemId={currentItemId} />
          {/*
            Last, and at every width. The label arrives as a prop so this
            switcher's own module stays catalog-free: the three link texts are
            locale metadata, not messages, and come from inside the switcher.
            (The shell as a whole is a client component since packet UI-04 — see
            the note above — so the prop is a module boundary, not a bundle
            claim.)
          */}
          <LocaleSwitcher
            locale={locale}
            selectorLabel={translate(locale, "locale.selectorLabel")}
          />
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
            {translate(locale, "shell.authorityStatement")}
          </p>
        </div>
      </footer>
    </>
  );
}
