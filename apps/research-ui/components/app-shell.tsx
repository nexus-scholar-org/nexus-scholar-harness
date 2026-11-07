"use client";

import type { ReactNode } from "react";

import { usePathname } from "next/navigation";

import { translate, type Locale } from "@/i18n";

import { SiteHeader } from "./site-header";

/**
 * The id the skip link targets.
 *
 * The shell renders `<main id={MAIN_CONTENT_ID} tabIndex={-1}>` around the
 * route's content. `tabIndex={-1}` makes the landmark a skip-link target
 * without adding a stop to the tab order.
 */
export const MAIN_CONTENT_ID = "main-content";

/**
 * The application shell: the skip link, the header (banner), the route's
 * content in the one `main` landmark, and the footer (contentinfo).
 *
 * The banner and the footer are siblings of `main`, never inside it, and a
 * route must not render a `main` of its own: a second one is a
 * `landmark-one-main` violation and a dead skip link.
 *
 * Every route the shell wraps reads live workspace data (the workspaces screen
 * and the screening steps); the demonstration screens and their
 * "Demonstration data" marker were removed on 2026-11-05.
 *
 * `locale` is a required prop (D-I18N-05), so a test can render any locale
 * without a provider; `<html lang dir>` is owned by `LocaleDocument`.
 */
export function AppShell({
  locale,
  children,
}: Readonly<{ locale: Locale; children: ReactNode }>) {
  const pathname = usePathname() ?? `/${locale}`;

  return (
    <div className="flex min-h-screen flex-col">
      <a className="skip-link" href={`#${MAIN_CONTENT_ID}`}>
        {translate(locale, "a11y.skipToMain")}
      </a>

      <SiteHeader locale={locale} pathname={pathname} />

      <main id={MAIN_CONTENT_ID} tabIndex={-1} className="flex-1 focus:outline-none">
        {children}
      </main>

      <footer className="border-t border-rule bg-leaf">
        <div className="mx-auto flex max-w-7xl flex-col gap-1.5 px-4 py-5 text-xs leading-5 text-ink-muted sm:px-6 md:flex-row md:items-center md:justify-between md:gap-6 lg:px-8">
          <p className="flex flex-col gap-1.5 md:flex-row md:items-center md:gap-3">
            <span className="font-display text-sm font-semibold text-ink">{translate(locale, "brand.productName")}</span>
            <span aria-hidden="true" className="hidden h-3 w-px bg-rule md:inline-block" />
            <span>{translate(locale, "footer.local")}</span>
            {process.env.NEXT_PUBLIC_NEXUS_VERSION ? (
              <span className="font-mono" dir="ltr" data-version>
                {process.env.NEXT_PUBLIC_NEXUS_VERSION}
              </span>
            ) : null}
          </p>
          <p>{translate(locale, "footer.journal")}</p>
        </div>
      </footer>
    </div>
  );
}
