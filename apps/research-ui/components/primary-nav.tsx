import { navKey, translate, type Locale } from "@/i18n";

import Link from "next/link";

/**
 * One entry in the primary navigation.
 *
 * `href` is present ONLY when the route actually exists. An entry without one
 * names a surface that `docs/architecture/research_ui/AGENT_WORK_PACKETS.md`
 * describes but that has no route yet, and it is rendered as annotated text
 * rather than as a link.
 */
export interface PrimaryNavItem {
  /** Stable identifier; also used as the React key and for `aria-current`. */
  id: string;
  label: string;
  href?: string;
}

/**
 * The surfaces that actually exist as packets, and nothing beyond them.
 *
 * `overview` has always carried a route (`/`, and since packet UI-01d the
 * locale-prefixed `/en`, `/fr`, `/ar`), and packet **UI-04 added the second
 * one**: `screening` now resolves to `/${locale}/screening`, so it carries an
 * `href` too and is rendered as a real link. `evidence` and `audit` are packets
 * UI-05 and UI-06; they still carry no `href` on purpose so the navigation
 * cannot present a dead route as a working link.
 *
 * The `href` field is the "which route exists" declaration, and it is what
 * `tests/shell.test.tsx` uses to pick the no-route entries (its *absence* on
 * `evidence` and `audit`). It stays a root-relative suffix rather than a fully
 * rendered URL: the rendered href is computed at render time from the locale,
 * below, and asserted for all three locales so a sentinel or a bare root link
 * can never reach the document. Every field here remains a declared surface —
 * a route that does not exist may not gain an `href` without its packet.
 *
 * Two fields are frozen in *meaning* by packets UI-01c/UI-01d even as UI-04
 * grew the table:
 *
 * - `label` is the English source string, and it is not what gets rendered. The
 *   rendered label is `translate(locale, navKey(item.id))`, whose English value
 *   is byte-identical to `label` — asserted by `tests/i18n-catalog.test.ts`, so
 *   the pin cannot rot into a difference.
 * - `href` never holds a locale. `renderedHref` below prefixes whatever suffix
 *   is declared here, and `tests/shell.test.tsx` asserts the rendered value in
 *   every locale.
 */
export const PRIMARY_NAV_ITEMS: readonly PrimaryNavItem[] = [
  { id: "overview", label: "Overview", href: "/" },
  { id: "screening", label: "Screening", href: "/screening" },
  { id: "evidence", label: "Evidence" },
  { id: "audit", label: "Audit" },
];

/**
 * The annotation shown next to a surface that has no route. It is real, visible
 * text — not `sr-only` — so the honesty of the navigation is available to
 * sighted users as well as to assistive technology.
 */
export const UNAVAILABLE_NAV_TEXT = "Not yet available";

const LIST_CLASS = {
  inline: "flex flex-wrap items-center gap-x-1 gap-y-1",
  stacked: "flex flex-col items-stretch gap-y-1",
} as const;

/*
 * Navigation treatment (packet UI-01c).
 *
 * No corner rounding (the whole `rounded-*` family), no tinted pill behind the
 * current route: the active surface is marked the way a contents page marks an
 * entry — a real underline in
 * `--color-evidence`, drawn on a transparent decoration so it appears on hover
 * and on `aria-current` and is absent otherwise. That keeps the "which surface
 * am I on" signal a rule rather than a filled chip, which is what makes the
 * header read as a masthead rather than as a toolbar.
 *
 * `UNAVAILABLE_TAG_CLASS` was the 4.34:1 near miss that UI-00b repaired; it is
 * now a hairline-boxed marginal stamp in `--color-ink-faint` (measured 5.72:1
 * on `--color-leaf`) rather than a filled pill, so it is both lighter in weight
 * and no longer competing with the one real link beside it.
 */
const AVAILABLE_ITEM_CLASS =
  "block px-2 py-1.5 text-sm font-medium text-ink-muted underline decoration-2 underline-offset-4 decoration-transparent hover:text-ink hover:decoration-rule-strong aria-[current]:text-evidence aria-[current]:decoration-evidence";

const UNAVAILABLE_ITEM_CLASS =
  "flex flex-wrap items-center gap-2 px-2 py-1.5 text-sm text-ink-muted";

const UNAVAILABLE_TAG_CLASS =
  "border border-rule-strong px-1.5 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] text-ink-faint rtl:tracking-normal rtl:text-[0.75rem]";

/**
 * The navigation entries themselves, without the surrounding `<nav>` landmark,
 * so the desktop and mobile presentations cannot drift apart.
 *
 * `locale` is required (D-I18N-05): it decides both the rendered labels and the
 * rendered href, and a component that could default it would let a route ship an
 * English link inside an Arabic document.
 */
export function PrimaryNavList({
  variant,
  currentItemId,
  locale,
}: {
  variant: "inline" | "stacked";
  currentItemId: string | undefined;
  locale: Locale;
}) {
  return (
    <ul className={LIST_CLASS[variant]}>
      {PRIMARY_NAV_ITEMS.map((item) => (
        <li key={item.id}>
          {item.href ? (
            <Link
              href={renderedHref(locale, item)}
              aria-current={item.id === currentItemId ? "page" : undefined}
              className={AVAILABLE_ITEM_CLASS}
            >
              {translate(locale, navKey(item.id))}
            </Link>
          ) : (
            <span className={UNAVAILABLE_ITEM_CLASS}>
              {translate(locale, navKey(item.id))}
              <span className={UNAVAILABLE_TAG_CLASS}>
                {translate(locale, "nav.unavailable")}
              </span>
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * The href a nav entry renders with.
 *
 * Derived from the locale and the declared suffix, never read verbatim from
 * `item.href`: the declaration carries the root sentinel `"/"` for the overview
 * and the path suffix `"/screening"` for the screening workspace, and a rendered
 * link to `/` from `/ar` would drop the reader's language without saying so.
 * The decision is in one place, so a third route landing later is a single site
 * to change, and `tests/shell.test.tsx` asserts the rendered value for all three
 * locales.
 */
export function renderedHref(locale: Locale, item: PrimaryNavItem): string {
  return item.href === "/" ? `/${locale}` : `/${locale}${item.href ?? ""}`;
}

/**
 * Which nav surface the current pathname is on, for `aria-current`.
 *
 * Packet UI-04 introduced a second route, which means "which link is current"
 * can no longer be a default: the shell derives it from the URL instead of
 * assuming the overview. The comparison is against `renderedHref`'s own output —
 * the same function that produced the link — so a pathname that matches how a
 * link was built is the only way to earn `aria-current`, and an unknown path
 * yields `undefined` (no current surface) rather than a guessed one.
 *
 * A trailing slash is stripped first, because the router may report `/en/` for
 * the same document the link calls `/en`.
 */
export function currentItemIdFromPathname(pathname: string, locale: Locale): string | undefined {
  const path =
    pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
  return PRIMARY_NAV_ITEMS.find(
    (item) => item.href !== undefined && renderedHref(locale, item) === path,
  )?.id;
}

/** Desktop/narrow-screen primary navigation landmark. */
export function PrimaryNav({
  locale,
  currentItemId,
}: {
  locale: Locale;
  currentItemId: string | undefined;
}) {
  return (
    <nav
      aria-label={translate(locale, "nav.landmark.primary")}
      data-nav-region="primary"
      className="hidden lg:block"
    >
      <PrimaryNavList variant="inline" currentItemId={currentItemId} locale={locale} />
    </nav>
  );
}
