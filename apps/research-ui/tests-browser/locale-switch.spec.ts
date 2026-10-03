import { expect, report, test } from "./helpers";
import { CATALOGS } from "../messages";
import { LOCALE_METADATA, swapLocale } from "../i18n";
import { demoProject } from "../lib/mock-project";

/**
 * The locale selector (packet UI-01d, AC-5, N13, N14).
 *
 * Two properties are load-bearing and easy to lose:
 *
 * 1. **The locale is never browser state.** It is the URL and nothing else, so a
 *    fresh context at `/en` is English no matter what the previous one did. The
 *    check below is deliberately a *new browser context* rather than a navigation:
 *    a same-context navigation would pass even if the selector had stashed the
 *    choice in a cookie, and the cookie/localStorage assertion is the part that
 *    would catch it.
 * 2. **Switching preserves the equivalent route.** Each link is computed from the
 *    current path, so `/fr` + `ar` is `/ar` and a future `/fr/evidence` + `ar` is
 *    `/ar/evidence`. Asserting the rendered `href` rather than the behaviour of a
 *    click is what makes that checkable before the second route exists.
 */

const SELECTOR_LINKS = 'nav[data-nav-region="locale"] a[href]';

test.describe("locale selector", () => {
  test("AC-5: announces its purpose, marks the current locale, and links every other one", async ({
    page,
  }) => {
    await page.goto("/fr");

    const selector = page.locator('nav[data-nav-region="locale"]');
    await expect(selector).toHaveAttribute("aria-label", CATALOGS.fr["locale.selectorLabel"]);

    const links = page.locator(SELECTOR_LINKS);
    await expect(links).toHaveCount(3);

    for (const locale of ["en", "fr", "ar"] as const) {
      const link = page.locator(`${SELECTOR_LINKS}[href="/${locale}"]`);
      await expect(link).toHaveCount(1);
      // A language's own name, never its English label: a reader who cannot read
      // the current interface language must still find their own in the list.
      await expect(link).toHaveText(LOCALE_METADATA[locale].endonym);
      // Each option declares the language it switches *to*, so a screen reader
      // announces the target rather than the label it is leaving.
      await expect(link).toHaveAttribute("lang", LOCALE_METADATA[locale].lang);
    }

    await expect(page.locator(`${SELECTOR_LINKS}[href="/fr"]`)).toHaveAttribute(
      "aria-current",
      "true",
    );
    await expect(page.locator(`${SELECTOR_LINKS}[href="/en"]`)).not.toHaveAttribute(
      "aria-current",
      "true",
    );
  });

test("N14: activating `ar` from `/fr` lands on `/ar` in Arabic, with no 404", async ({
    page,
  }) => {
    await page.goto("/fr");

    await page.locator(`${SELECTOR_LINKS}[href="/ar"]`).click();
    await page.waitForURL("**/ar");

    expect(new URL(page.url()).pathname).toBe("/ar");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    report(`switched fr -> ar: ${page.url()}`);
  });

  test("N14: every link is the same path in another locale", async ({ page }) => {
    // `/fr` is the only shipped document, so the remainder is empty here; the
    // computation is exercised directly for the deeper case so the rule is
    // pinned rather than merely true by accident.
    await page.goto("/fr");
    const hrefs = await page.locator(SELECTOR_LINKS).evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute("href")),
    );
    expect(hrefs).toEqual(["/en", "/fr", "/ar"]);

    expect(swapLocale("/fr", "ar")).toBe("/ar");
    expect(swapLocale("/fr/evidence", "ar")).toBe("/ar/evidence");
    expect(swapLocale("/fr/evidence/", "en")).toBe("/en/evidence/");
    expect(swapLocale("/fr/evidence?tab=chain", "ar")).toBe("/ar/evidence?tab=chain");
    expect(swapLocale("/", "ar")).toBe("/ar");
  });

  test("N13: the locale is the URL, not a cookie or a storage key", async ({
    browser,
    page,
  }) => {
    await page.goto("/fr");
    await page.locator(`${SELECTOR_LINKS}[href="/ar"]`).click();
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");

    const stored = await page.evaluate(() => ({
      cookies: document.cookie,
      localKeys: Object.keys(localStorage),
      sessionKeys: Object.keys(sessionStorage),
    }));
    report(`browser state after switching locale = ${JSON.stringify(stored)}`);
    expect(stored.cookies, "the selector must not write a cookie").toBe("");
    expect(stored.localKeys, "the locale must not live in localStorage").toEqual([]);
    expect(stored.sessionKeys, "the locale must not live in sessionStorage").toEqual([]);

    // A brand-new context shares no cookies, no storage and no history with the
    // one that switched. If the locale were browser state in any form, this
    // would not be Arabic.
    const fresh = await browser.newContext();
    const freshPage = await fresh.newPage();
    await freshPage.goto("/en");
    await expect(freshPage.locator("html")).toHaveAttribute("lang", "en");
    await expect(freshPage.locator("html")).toHaveAttribute("dir", "ltr");
    // The `<h1>` is the fixture's own title inside `<bdi>`, not a catalogued string:
    // `overview.eyebrow` is the small caps line above it. Asserting the wrong one
    // produced a failure that looked like a translation regression and was not.
    await expect(freshPage.locator("h1")).toHaveText(demoProject.title);
    await fresh.close();
  });
});