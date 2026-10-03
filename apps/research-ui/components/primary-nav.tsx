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
 * `overview` is the only route in the application today (`/`, and since packet
 * UI-01d the locale-prefixed `/en`, `/fr`, `/ar`). `screening`, `evidence` and
 * `audit` are packets UI-04, UI-05 and UI-06; they carry no `href` on purpose so
 * the navigation cannot present a dead route as a working link.
 *
 * Every field here is **frozen** by packet UI-01c, and packet UI-01d keeps it
 * frozen. Two consequences are worth stating because they look like violations:
 *
 * - `label` is the English source string, and it is not what gets rendered. The
 *   rendered label is `translate(locale, navKey(item.id))`, whose English value
 *   is byte-identical to `label` — asserted by `tests/i18n-catalog.test.ts`, so
 *   the pin cannot rot into a difference.
 * - `href` stays the sentinel `"/"` rather than becoming `"/en"`. It is the
 *   "which route exists" declaration, and `tests/shell.test.tsx` uses its
 *   *absence* on the other three entries to pick the no-route ones. The rendered
 *   href is computed at render time from the locale, below, and asserted for all
 *   three locales so the sentinel can never surface as a bare root link.
 */
export const PRIMARY_NAV_ITEMS: readonly PrimaryNavItem[] = [
  { id: "overview", label: "Overview", href: "/" },
  { id: "screening", label: "Screening" },
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
  currentItemId: string;
  locale: Locale;
}) {
  return (
    <ul className={LIST_CLASS[variant]}>
      {PRIMARY_NAV_ITEMS.map((item) => (
        <li key={item.id}>
          {item.href ? (
            <Link
              href={renderedHref(locale)}
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
 * Computed from the locale, never read from `item.href`: the frozen constant
 * carries the sentinel root, and a rendered link to `/` from `/ar` would drop the
 * reader's language without saying so. Only the overview exists, so the target is
 * the locale root — but the decision is derived here, in one place, so the day a
 * second route lands there is a single site to change.
 */
function renderedHref(locale: Locale): string {
  return `/${locale}`;
}

/** Desktop/narrow-screen primary navigation landmark. */
export function PrimaryNav({
  locale,
  currentItemId = "overview",
}: {
  locale: Locale;
  currentItemId?: string;
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
