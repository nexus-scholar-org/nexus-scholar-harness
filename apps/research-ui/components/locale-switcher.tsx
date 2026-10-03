"use client";

import { LOCALE_METADATA, SUPPORTED_LOCALES, swapLocale } from "@/i18n/locales";
import type { Locale } from "@/i18n/locales";
import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * The locale selector: one link per shipped locale.
 *
 * Links, not a custom listbox (D-I18N-10). A `<select>` or an ARIA listbox would
 * mean a widget role, a roving-tabindex implementation, a popup that has to
 * close on Escape and on outside click, and — worst — a control whose current
 * value is hidden until it is opened. Three plain links are keyboard reachable
 * with no JS state at all, they survive copy-link, middle-click and
 * "open in new tab", and the current one is marked with `aria-current`, which is
 * announced without being opened. There is nothing here that a browser does not
 * already do correctly.
 *
 * The equivalent route is preserved. `swapLocale` replaces the leading segment
 * of the current pathname and keeps everything after it, so switching from
 * `/fr/evidence?x=1` lands on `/ar/evidence?x=1` rather than at the overview, and
 * a route added in a later packet does not need this component to learn about
 * it.
 *
 * Two deliberate constraints:
 *
 * - **It imports no catalog.** `translate` runs in the server shell and the one
 *   string this component needs arrives as the `selectorLabel` prop, so the
 *   catalogs never enter the client bundle and a translated shell cannot be
 *   rendered by a component that has to be interactive.
 * - **It carries no breakpoint.** It is present at 375px and at 1440px
 *   (D-I18N-11). Hiding it on narrow screens would leave a mobile reader with no
 *   locale affordance at all, since the URL segment is the only source of locale
 *   truth.
 *
 * The link text is each language's **endonym**, not a translated label
 * (D-I18N-06): "العربية" is the name of that language in that language, and it is
 * the only spelling that is correct in all three documents at once. A language's
 * own name is not something the product says, which is why it lives in the
 * locale metadata table rather than in the catalogs. The links are rendered in
 * `SUPPORTED_LOCALES` order, and that order is the tab order.
 *
 * `usePathname()` returns a path without the query string, so a `?tab=` in the
 * address is not carried across; the path, including any trailing segment, is.
 * It is typed as a string but can read `null` before the router context is
 * attached (it does in an out-of-router render, which is exactly what a unit
 * test does), so the fallback is the root rather than a crash — a switcher that
 * throws while the app is hydrating would take the whole page with it.
 */
export function LocaleSwitcher({
  locale,
  selectorLabel,
}: Readonly<{ locale: Locale; selectorLabel: string }>) {
  const pathname = usePathname();

  return (
    <nav
      aria-label={selectorLabel}
      data-nav-region="locale"
      className="mt-4 flex flex-wrap items-center gap-x-1 gap-y-1"
    >
      <ul className="flex flex-wrap items-center gap-x-1 gap-y-1">
        {SUPPORTED_LOCALES.map((code) => (
          <li key={code}>
            <Link
              href={swapLocale(pathname ?? "/", code)}
              lang={code}
              hrefLang={code}
              aria-current={code === locale ? "true" : undefined}
              className="block px-2 py-1.5 text-sm font-medium text-ink-muted underline decoration-2 underline-offset-4 decoration-transparent hover:text-ink hover:decoration-rule-strong aria-[current]:text-evidence aria-[current]:decoration-evidence"
            >
              {LOCALE_METADATA[code].endonym}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}