"use client";

import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
} from "@headlessui/react";
import { Bars3Icon, CheckIcon, ChevronDownIcon, LanguageIcon, XMarkIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useState } from "react";

import { LOCALE_METADATA, SUPPORTED_LOCALES, navKey, swapLocale, translate, type Locale } from "@/i18n";

import { ThemeToggle } from "./theme-toggle";

/**
 * The application header (M5-slim, 2026-11-05): one 64px bar with the
 * wordmark, the two places a researcher works (their workspaces, and the
 * screening of the open one), and on the inline end the language menu and the
 * theme toolbar. Below `lg` the navigation and both selectors move into one
 * menu dialog behind a single button.
 *
 * The brand book has no logo yet: the name, set in Literata, is the mark.
 */

export const MOBILE_NAV_PANEL_ID = "mobile-primary-nav";

/** The primary destinations. Every entry is a route that exists. */
export const NAV_ITEMS = [
  { id: "workspaces", href: "/workspaces" },
  { id: "screening", href: "/screening/home" },
] as const;

export type NavId = (typeof NAV_ITEMS)[number]["id"];

/**
 * Which destination the pathname belongs to: `/screening/<step>` is all one
 * destination, so every screening step marks "Screening" current.
 */
export function currentNavId(pathname: string, locale: Locale): NavId | undefined {
  const path = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
  if (path === `/${locale}/workspaces`) return "workspaces";
  if (path === `/${locale}/screening` || path.startsWith(`/${locale}/screening/`)) return "screening";
  return undefined;
}

/**
 * The `?console=` origin a development build reads the engine from. The
 * packaged app serves pages and engine from one origin and has none, so the
 * links carry nothing there. Read after mount: prerendered pages have no query at
 * build time.
 */
function useConsoleQuery(): string {
  const [query, setQuery] = useState("");
  useEffect(() => {
    const origin = new URLSearchParams(window.location.search).get("console");
    setQuery(origin ? `?console=${encodeURIComponent(origin)}` : "");
  }, []);
  return query;
}

const NAV_LINK =
  "relative inline-flex h-16 items-center px-3 text-sm font-medium text-ink-muted hover:text-ink aria-[current=page]:text-ink after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:rounded-full after:bg-transparent aria-[current=page]:after:bg-brand";

const MOBILE_NAV_LINK =
  "flex min-h-11 items-center rounded-md px-3 text-base font-medium text-ink hover:bg-paper aria-[current=page]:bg-brand-soft aria-[current=page]:text-brand";

export function SiteHeader({ locale, pathname }: Readonly<{ locale: Locale; pathname: string }>) {
  const query = useConsoleQuery();
  const current = currentNavId(pathname, locale);
  const t = (key: Parameters<typeof translate>[1]) => translate(locale, key);
  const themeLabels = { system: t("theme.system"), light: t("theme.light"), dark: t("theme.dark") };

  return (
    <header className="sticky top-0 z-30 border-b border-rule bg-leaf">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 shrink-0 items-center gap-3">
          <Link
            href={`/${locale}/workspaces${query}`}
            className="rounded-sm font-display text-lg font-semibold leading-none tracking-tight text-ink"
            data-brand-home
          >
            {t("brand.productName")}
          </Link>
          <span className="hidden border-s border-rule ps-3 text-sm leading-5 text-ink-muted xl:inline">
            {t("shell.descriptor")}
          </span>
        </div>

        <nav aria-label={t("nav.landmark.primary")} data-nav-region="primary" className="hidden lg:block">
          <ul className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.id}>
                <Link
                  href={`/${locale}${item.href}${query}`}
                  aria-current={item.id === current ? "page" : undefined}
                  className={NAV_LINK}
                >
                  {translate(locale, navKey(item.id))}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="ms-auto flex items-center gap-3">
          <div className="hidden items-center gap-3 lg:flex">
            <LocaleMenu locale={locale} pathname={pathname} query={query} />
            <ThemeToggle selectorLabel={t("theme.selectorLabel")} labels={themeLabels} />
          </div>
          <MobileMenu locale={locale} pathname={pathname} query={query} current={current} themeLabels={themeLabels} />
        </div>
      </div>
    </header>
  );
}

/** The language menu: the current language's endonym, then the three links. */
function LocaleMenu({ locale, pathname, query }: Readonly<{ locale: Locale; pathname: string; query: string }>) {
  const label = translate(locale, "locale.selectorLabel");
  return (
    <Menu as="div" className="relative" data-nav-region="locale">
      <MenuButton
        aria-label={`${label}: ${LOCALE_METADATA[locale].endonym}`}
        className="inline-flex h-9 items-center gap-1.5 rounded-md border border-rule bg-leaf px-2.5 text-sm font-medium text-ink hover:bg-paper data-open:bg-paper"
      >
        <LanguageIcon aria-hidden="true" className="size-4 text-ink-muted" />
        <span lang={locale}>{LOCALE_METADATA[locale].endonym}</span>
        <ChevronDownIcon aria-hidden="true" className="size-3.5 text-ink-muted" />
      </MenuButton>
      <MenuItems
        anchor={{ to: "bottom end", gap: 6 }}
        className="z-40 w-44 rounded-md border border-rule bg-leaf p-1 shadow-[var(--shadow-overlay)] focus:outline-none"
      >
        {SUPPORTED_LOCALES.map((code) => (
          <MenuItem key={code}>
            <Link
              href={`${swapLocale(pathname, code)}${query}`}
              lang={code}
              hrefLang={code}
              aria-current={code === locale ? "true" : undefined}
              className="flex min-h-9 items-center justify-between gap-3 rounded-sm px-2.5 text-sm text-ink data-focus:bg-paper aria-[current=true]:font-medium aria-[current=true]:text-brand"
            >
              {LOCALE_METADATA[code].endonym}
              {code === locale ? <CheckIcon aria-hidden="true" className="size-4" /> : null}
            </Link>
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>
  );
}

/**
 * Below `lg`: one button opening a panel with the navigation, the languages
 * and the theme. Headless UI's `Dialog` supplies the modal semantics, `Escape`
 * and focus restoration. The panel sits on the inline end, so in `ar` it opens
 * from the left.
 */
function MobileMenu({
  locale,
  pathname,
  query,
  current,
  themeLabels,
}: Readonly<{
  locale: Locale;
  pathname: string;
  query: string;
  current: NavId | undefined;
  themeLabels: Readonly<Record<"system" | "light" | "dark", string>>;
}>) {
  const [open, setOpen] = useState(false);
  const t = (key: Parameters<typeof translate>[1]) => translate(locale, key);

  return (
    <div className="lg:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={MOBILE_NAV_PANEL_ID}
        onClick={() => setOpen(true)}
        data-nav-region="mobile-trigger"
        className="inline-flex size-11 items-center justify-center rounded-md text-ink hover:bg-paper"
      >
        <Bars3Icon aria-hidden="true" className="size-6" />
        <span className="sr-only">{t("a11y.openMainNavigation")}</span>
      </button>

      <Dialog open={open} onClose={setOpen} className="relative z-50">
        <DialogBackdrop className="fixed inset-0 bg-ink/40" />
        <DialogPanel
          id={MOBILE_NAV_PANEL_ID}
          className="fixed inset-y-0 end-0 flex w-full max-w-sm flex-col overflow-y-auto border-s border-rule bg-leaf"
        >
          <div className="flex h-16 items-center justify-between border-b border-rule px-4 sm:px-6">
            <DialogTitle className="font-display text-lg font-semibold text-ink">
              {t("nav.mobileDialogTitle")}
            </DialogTitle>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="inline-flex size-11 items-center justify-center rounded-md text-ink hover:bg-paper"
            >
              <XMarkIcon aria-hidden="true" className="size-6" />
              <span className="sr-only">{t("a11y.closeMainNavigation")}</span>
            </button>
          </div>

          <div className="flex flex-1 flex-col gap-8 px-4 py-6 sm:px-6">
            <nav aria-label={t("nav.landmark.primaryMobile")} data-nav-region="mobile">
              <ul className="flex flex-col gap-1">
                {NAV_ITEMS.map((item) => (
                  <li key={item.id}>
                    <Link
                      href={`/${locale}${item.href}${query}`}
                      aria-current={item.id === current ? "page" : undefined}
                      onClick={() => setOpen(false)}
                      className={MOBILE_NAV_LINK}
                    >
                      {translate(locale, navKey(item.id))}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            <nav aria-label={t("locale.selectorLabel")} data-nav-region="locale-mobile">
              <p className="mb-2 px-3 text-xs font-medium uppercase tracking-[0.05em] text-ink-muted rtl:tracking-normal">
                {t("locale.selectorLabel")}
              </p>
              <ul className="flex flex-col gap-1">
                {SUPPORTED_LOCALES.map((code) => (
                  <li key={code}>
                    <Link
                      href={`${swapLocale(pathname, code)}${query}`}
                      lang={code}
                      hrefLang={code}
                      aria-current={code === locale ? "true" : undefined}
                      className="flex min-h-11 items-center justify-between rounded-md px-3 text-base text-ink hover:bg-paper aria-[current=true]:font-medium aria-[current=true]:text-brand"
                    >
                      {LOCALE_METADATA[code].endonym}
                      {code === locale ? <CheckIcon aria-hidden="true" className="size-5" /> : null}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            <div>
              <p className="mb-2 px-3 text-xs font-medium uppercase tracking-[0.05em] text-ink-muted rtl:tracking-normal">
                {t("theme.selectorLabel")}
              </p>
              <ThemeToggle selectorLabel={t("theme.selectorLabel")} labels={themeLabels} variant="full" />
            </div>
          </div>
        </DialogPanel>
      </Dialog>
    </div>
  );
}
