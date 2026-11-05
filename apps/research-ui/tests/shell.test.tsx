import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { AxeResults, Result } from "axe-core";
import { describe, expect, it, vi } from "vitest";

import { generateMetadata } from "@/app/[locale]/layout";
import { AppShell, MAIN_CONTENT_ID } from "@/components/app-shell";
import { NAV_ITEMS, currentNavId } from "@/components/site-header";
import { LOCALE_METADATA, SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CATALOGS } from "@/messages";

/**
 * The application shell (2026-11-05 header and footer): skip link, banner,
 * one main, contentinfo; the two destinations; the language menu and the
 * theme toolbar; the mobile menu dialog. Rendered with a stand-in route so the
 * file tests the chrome, not a screen.
 */

let currentPath = "/en/workspaces";

vi.mock("next/navigation", () => ({
  usePathname: () => currentPath,
}));

function renderShell(locale: Locale, path = `/${locale}/workspaces`) {
  cleanup();
  currentPath = path;
  return render(
    <AppShell locale={locale}>
      <h1>Route</h1>
    </AppShell>,
  );
}

function t(locale: Locale, key: keyof (typeof CATALOGS)["en"]): string {
  return CATALOGS[locale][key];
}

function blockingViolations(results: AxeResults): Result[] {
  return results.violations.filter((violation) => violation.impact === "critical" || violation.impact === "serious");
}

function describeViolation(violation: Result): string {
  return `[${violation.impact ?? "unknown"}] ${violation.id}: ${violation.nodes.map((node) => JSON.stringify(node.target)).join(" | ")}`;
}

/** axe over the whole document, with the `lang` and `title` the layout sets. */
async function runAxeOnDocument(locale: Locale): Promise<AxeResults> {
  const metadata = await generateMetadata({ params: Promise.resolve({ locale }) });
  document.documentElement.setAttribute("lang", LOCALE_METADATA[locale].lang);
  document.title = String(metadata.title);
  try {
    return await axe.run(document.documentElement);
  } finally {
    document.documentElement.removeAttribute("lang");
    document.title = "";
  }
}

describe("landmarks", () => {
  it("puts the skip link first and points it at the one main landmark", async () => {
    const user = userEvent.setup();
    renderShell("en");
    await user.tab();
    const skip = screen.getByRole("link", { name: t("en", "a11y.skipToMain") });
    expect(skip).toHaveFocus();
    expect(skip).toHaveAttribute("href", `#${MAIN_CONTENT_ID}`);
    const mains = screen.getAllByRole("main");
    expect(mains).toHaveLength(1);
    expect(mains[0]).toHaveAttribute("id", MAIN_CONTENT_ID);
    expect(mains[0]).toHaveAttribute("tabindex", "-1");
  });

  it("keeps the banner and the footer siblings of main, never inside it", () => {
    renderShell("en");
    const main = screen.getByRole("main");
    const banner = screen.getByRole("banner");
    const footer = screen.getByRole("contentinfo");
    expect(main.contains(banner)).toBe(false);
    expect(main.contains(footer)).toBe(false);
    expect(banner.parentElement).toBe(main.parentElement);
    expect(footer.parentElement).toBe(main.parentElement);
  });

  it("names every navigation landmark distinctly, in every locale, with the menu open", async () => {
    for (const locale of SUPPORTED_LOCALES) {
      const user = userEvent.setup();
      renderShell(locale);
      await user.click(screen.getByRole("button", { name: t(locale, "a11y.openMainNavigation") }));
      const names = screen.getAllByRole("navigation", { hidden: true }).map((nav) => nav.getAttribute("aria-label"));
      expect(new Set(names).size, locale).toBe(names.length);
      expect(names, locale).toContain(t(locale, "nav.landmark.primary"));
      expect(names, locale).toContain(t(locale, "nav.landmark.primaryMobile"));
    }
  });
});

describe("primary navigation", () => {
  it("links the two destinations in every locale, and nothing else", () => {
    for (const locale of SUPPORTED_LOCALES) {
      renderShell(locale);
      const nav = screen.getByRole("navigation", { name: t(locale, "nav.landmark.primary") });
      const links = within(nav).getAllByRole("link");
      expect(links.map((link) => link.textContent), locale).toEqual([t(locale, "nav.workspaces"), t(locale, "nav.screening")]);
      expect(links.map((link) => link.getAttribute("href")), locale).toEqual([
        `/${locale}/workspaces`,
        `/${locale}/screening/home`,
      ]);
    }
  });

  it("marks the destination of the current path, and only that one", () => {
    renderShell("fr", "/fr/screening/triage/");
    const nav = screen.getByRole("navigation", { name: t("fr", "nav.landmark.primary") });
    const current = within(nav).getAllByRole("link").filter((link) => link.getAttribute("aria-current") === "page");
    expect(current.map((link) => link.textContent)).toEqual([t("fr", "nav.screening")]);
  });

  it("derives the current destination from the path, and none for an unknown one", () => {
    expect(currentNavId("/en/workspaces/", "en")).toBe("workspaces");
    for (const step of ["home", "prepare", "proposals", "triage", "agreement", "publish"]) {
      expect(currentNavId(`/ar/screening/${step}`, "ar")).toBe("screening");
    }
    expect(currentNavId("/en/screening", "en")).toBe("screening");
    expect(currentNavId("/en/screeningx", "en")).toBeUndefined();
    expect(currentNavId("/en/corpus", "en")).toBeUndefined();
    expect(currentNavId("/fr/workspaces", "en")).toBeUndefined();
    expect(NAV_ITEMS.map((item) => item.id)).toEqual(["workspaces", "screening"]);
  });

  it("sends the wordmark to the workspaces screen", () => {
    renderShell("ar", "/ar/screening/home");
    const banner = screen.getByRole("banner");
    const home = within(banner).getByRole("link", { name: new RegExp(t("ar", "brand.productName")) });
    expect(home).toHaveAttribute("href", "/ar/workspaces");
  });

  it("carries a development build's console origin on every link", async () => {
    window.history.replaceState(null, "", "/en/workspaces?console=http%3A%2F%2F127.0.0.1%3A8000");
    try {
      renderShell("en");
      const nav = screen.getByRole("navigation", { name: t("en", "nav.landmark.primary") });
      expect(await within(nav).findByRole("link", { name: t("en", "nav.screening") })).toHaveAttribute(
        "href",
        "/en/screening/home?console=http%3A%2F%2F127.0.0.1%3A8000",
      );
    } finally {
      window.history.replaceState(null, "", "/");
    }
  });
});

describe("language menu", () => {
  it("names the current language, and lists all three with their own lang", async () => {
    const user = userEvent.setup();
    renderShell("en", "/en/screening/triage");
    const button = screen.getByRole("button", { name: `${t("en", "locale.selectorLabel")}: English` });
    await user.click(button);
    const items = screen.getAllByRole("menuitem");
    expect(items.map((item) => item.textContent)).toEqual(SUPPORTED_LOCALES.map((code) => LOCALE_METADATA[code].endonym));
    expect(items.map((item) => item.getAttribute("href"))).toEqual(["/en/screening/triage", "/fr/screening/triage", "/ar/screening/triage"]);
    expect(items.map((item) => item.getAttribute("lang"))).toEqual(["en", "fr", "ar"]);
    expect(items.map((item) => item.getAttribute("aria-current"))).toEqual(["true", null, null]);
  });
});

describe("mobile menu", () => {
  it("opens from the keyboard, closes with Escape and returns focus", async () => {
    const user = userEvent.setup();
    renderShell("en");
    const trigger = screen.getByRole("button", { name: t("en", "a11y.openMainNavigation") });
    trigger.focus();
    await user.keyboard("{Enter}");
    const dialog = screen.getByRole("dialog", { name: t("en", "nav.mobileDialogTitle") });
    expect(within(dialog).getAllByRole("link").map((link) => link.textContent)).toEqual([
      t("en", "nav.workspaces"),
      t("en", "nav.screening"),
      ...SUPPORTED_LOCALES.map((code) => LOCALE_METADATA[code].endonym),
    ]);
    expect(within(dialog).getByRole("group", { name: t("en", "theme.selectorLabel") })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(trigger).toHaveFocus();
  });

  it("closes from its own close control", async () => {
    const user = userEvent.setup();
    renderShell("ar");
    await user.click(screen.getByRole("button", { name: t("ar", "a11y.openMainNavigation") }));
    await user.click(screen.getByRole("button", { name: t("ar", "a11y.closeMainNavigation") }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("footer", () => {
  it("states where the app runs and where decisions are recorded, in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      renderShell(locale);
      const footer = screen.getByRole("contentinfo");
      expect(footer, locale).toHaveTextContent(t(locale, "footer.local"));
      expect(footer, locale).toHaveTextContent(t(locale, "footer.journal"));
    }
  });

  it("shows no demonstration marker anywhere: every route reads live data", () => {
    renderShell("en");
    expect(document.body.textContent).not.toMatch(/demonstration/i);
  });
});

describe("accessibility (jsdom + axe-core)", () => {
  it("reports no violations with the document-level rules evaluated", async () => {
    renderShell("en");
    const results = await runAxeOnDocument("en");
    const evaluated = new Set(
      [...results.passes, ...results.violations, ...results.incomplete, ...results.inapplicable].map((result) => result.id),
    );
    for (const rule of ["bypass", "landmark-one-main", "page-has-heading-one", "region", "landmark-unique"]) {
      expect(evaluated.has(rule), rule).toBe(true);
    }
    expect(results.violations.map(describeViolation)).toEqual([]);
  });

  it("reports no critical or serious violations with the mobile menu open", async () => {
    const user = userEvent.setup();
    renderShell("ar");
    await user.click(screen.getByRole("button", { name: t("ar", "a11y.openMainNavigation") }));
    const results = await runAxeOnDocument("ar");
    expect(blockingViolations(results).map(describeViolation)).toEqual([]);
  });

  it("reports no critical or serious violations with the language menu open", async () => {
    const user = userEvent.setup();
    renderShell("fr");
    await user.click(screen.getByRole("button", { name: `${t("fr", "locale.selectorLabel")}: Français` }));
    const results = await runAxeOnDocument("fr");
    expect(blockingViolations(results).map(describeViolation)).toEqual([]);
  });
});
