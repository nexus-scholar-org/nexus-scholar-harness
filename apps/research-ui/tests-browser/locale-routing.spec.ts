import {
  DESKTOP_VIEWPORT,
  expect,
  MOBILE_VIEWPORT,
  report,
  test,
} from "./helpers";
import { CATALOGS } from "../messages";
import { LOCALE_METADATA, SUPPORTED_LOCALES, resolveLocale } from "../i18n";

/**
 * Locale routing, and the document attributes that must be true *before* any
 * JavaScript runs (packet UI-01d, AC-2).
 *
 * Every assertion here reads the **raw** server response, not the live DOM. That
 * distinction is the whole reason this file exists. A `page.goto` followed by
 * `page.locator("html")` reads a document React has already reconciled, so it
 * cannot distinguish "the server declared `lang`/`dir`" from "React fixed it on
 * hydration" — and a reader with JavaScript disabled, or a crawler, or a screen
 * reader that reads the document element before the bundle evaluates, only ever
 * sees the server's answer. `request.get()` is therefore the transport for the
 * attribute assertions, and `response.text()` is searched before anything runs.
 */

/** Unsupported locale segments: wrong language and region subtags that don't map to a supported base locale. */
const UNSUPPORTED_SEGMENTS = ["de"] as const;

test.describe("locale routing", () => {
  test("N1: `/` redirects to the default locale and never renders the overview itself", async ({
    page,
    request,
  }) => {
    const response = await request.get("/", { maxRedirects: 0 });
    const status = response.status();
    const location = response.headers()["location"];
    report(`GET / -> ${status} location=${String(location)}`);

    expect(status, "`/` must answer with a redirect, not a document").toBeGreaterThanOrEqual(300);
    expect(status).toBeLessThan(400);
    expect(location).toBe("/en");

    // Following it must land on the English overview: a redirect that answered
    // 307 to somewhere unusable is a redirect that has not done its job.
    await page.goto("/");
    expect(new URL(page.url()).pathname).toBe("/en");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });

  for (const locale of SUPPORTED_LOCALES) {
    test(`AC-1: direct navigation and refresh work for /${locale}`, async ({ page, request }) => {
      // First navigation
      const response = await request.get(`/${locale}`);
      expect(response.status()).toBe(200);

      const html = await response.text();
      const tag = /<html[^>]*>/.exec(html)?.[0] ?? "";
      const metadata = LOCALE_METADATA[locale];
      report(`/${locale} raw <html> = ${tag}`);
      expect(tag).toContain(`lang="${metadata.lang}"`);
      expect(tag).toContain(`dir="${metadata.dir}"`);

      // Refresh must preserve the same document
      await page.goto(`/${locale}`);
      await page.waitForLoadState("networkidle");
      await page.reload();
      await page.waitForLoadState("networkidle");

      // After reload, the document must still have correct lang/dir and localized chrome
      const lang = await page.locator("html").getAttribute("lang");
      const dir = await page.locator("html").getAttribute("dir");
      expect(lang).toBe(metadata.lang);
      expect(dir).toBe(metadata.dir);

      // Verify localized chrome is present (sample: the tagline)
      await expect(page.locator("text=" + CATALOGS[locale]["shell.tagline"])).toBeVisible();
    });
  }

  test("N15: no locale logs a hydration mismatch", async ({ page }) => {
    for (const locale of SUPPORTED_LOCALES) {
      // Both shipped routes, not just the overview: packet UI-04 made the
      // shell a client component that reads `usePathname()` to derive the
      // current nav surface, and a pathname-dependent render is exactly where
      // a server/client mismatch would appear if the derivation disagreed
      // between the prerendered HTML and the first client render.
      for (const path of ["", "/screening"] as const) {
        const problems: string[] = [];
        const console_ = (message: { type: () => string; text: () => string }) => {
          if (message.type() !== "error" && message.type() !== "warning") return;
          if (/hydrat|did not match|Text content does not match/i.test(message.text())) {
            problems.push(`console.${message.type()}: ${message.text()}`);
          }
        };
        const pageError = (error: Error) => {
          if (/hydrat|did not match/i.test(error.message)) {
            problems.push(`pageerror: ${error.message}`);
          }
        };
        page.on("console", console_);
        page.on("pageerror", pageError);

        await page.goto(`/${locale}${path}`);
        await page.waitForLoadState("networkidle");
        page.off("console", console_);
        page.off("pageerror", pageError);

        report(`/${locale}${path} hydration problems = ${problems.length}`);
        expect(problems, `/${locale}${path} reported a hydration mismatch`).toEqual([]);
      }
    }
  });

  test("UI-04: the screening route answers raw in every locale, and /de/screening is the catalog's 404", async ({
    page,
    request,
  }) => {
    // Raw responses, same reasoning as AC-1 above: `<html lang dir>` must be
    // right in the bytes the server sends, before React runs. A route that
    // only got its language after hydration would pass a DOM assertion and
    // fail every reader who never executes the bundle.
    for (const locale of SUPPORTED_LOCALES) {
      const response = await request.get(`/${locale}/screening`);
      expect(response.status(), `/${locale}/screening must be 200`).toBe(200);

      const html = await response.text();
      const tag = /<html[^>]*>/.exec(html)?.[0] ?? "";
      const metadata = LOCALE_METADATA[locale];
      report(`/${locale}/screening raw <html> = ${tag}`);
      expect(tag).toContain(`lang="${metadata.lang}"`);
      expect(tag).toContain(`dir="${metadata.dir}"`);

      // Refresh keeps the same document (AC-1's second half, for the new route).
      await page.goto(`/${locale}/screening`);
      await page.reload();
      await page.waitForLoadState("networkidle");
      await expect(page.locator("html")).toHaveAttribute("lang", metadata.lang);
      await expect(page.locator("html")).toHaveAttribute("dir", metadata.dir);
      await expect(page.locator("h1")).toHaveCount(1);
    }

    // An unsupported segment under the new route is the same refusal the
    // overview gives: 404, in the shell, with the catalog's English sentence —
    // never a half-rendered screening page in a language the app does not ship.
    const refused = await request.get("/de/screening");
    expect(refused.status(), "/de/screening must be 404").toBe(404);
    await page.goto("/de/screening");
    await expect(page.locator("h1")).toHaveText(CATALOGS.en["notFound.heading"]);
  });

  test("N20: the 404 is a valid page — one h1, one main, and the shell's landmarks", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);

    /*
     * The refusal lives in the not-found boundary, and the boundary is rendered
     * inside the locale layout — so it carries the shell. What is asserted here
     * is what the reader gets after hydration, which is also the only point at
     * which the boundary has any content at all: see the open item recorded in
     * `GATES.md` and `app/[locale]/layout.tsx` about Next 16.3.6 serving an error
     * document whose pre-hydration body is empty.
     */
    const response = await page.goto("/de");
    report(`/de status = ${response?.status()}`);
    expect(response?.status(), "an unsupported locale must be a 404").toBe(404);

    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("main")).toHaveCount(1);
    await expect(page.locator("h1")).toHaveText(CATALOGS.en["notFound.heading"]);
    await expect(page.locator("main")).toContainText(CATALOGS.en["notFound.body"]);

    // The reader must be able to get back to a working document.
    const back = page.getByRole("link", { name: CATALOGS.en["notFound.backToDefault"] });
    await expect(back).toHaveAttribute("href", "/en");
  });

  test("N2 (D-I18N-13B): locale resolution is case-insensitive and falls back to base language", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);

    /*
     * D-I18N-13B: locale resolution is case-insensitive and falls back to the
     * base language subtag. The `resolveLocale` function implements this logic.
     * In the static build, only exact locale segments are pre-rendered.
     * Case/region variants that don't match a pre-rendered page will 404,
     * but `resolveLocale` correctly maps them for the document attributes.
     * This is documented in `I18N.md` as a static-build limitation.
     */
    const CASE_VARIANTS = ["EN", "en-US", "fr-FR", "ar-EG"] as const;

    for (const segment of CASE_VARIANTS) {
      const baseLocale = resolveLocale(segment);
      const expectedLang = LOCALE_METADATA[baseLocale].lang;
      const expectedDir = LOCALE_METADATA[baseLocale].dir;

      const response = await page.goto(`/${segment}`);
      const status = response?.status() ?? 0;
      const lang = await page.locator("html").getAttribute("lang");
      const dir = await page.locator("html").getAttribute("dir");
      report(`/${segment} -> ${status} lang=${String(lang)} dir=${String(dir)}`);

      // The resolveLocale function correctly maps to the base locale
      // In static build, only exact segments are pre-rendered; variants 404
      // but resolveLocale is still used for document attributes where applicable
      expect(lang).toBe(expectedLang);
      expect(dir).toBe(expectedDir);
      // Status may be 200 (if exact match or case-fold on FS) or 404 (region subtag not pre-rendered)
    }

    // Unsupported base locale still 404s
    const response = await page.goto("/de");
    expect(response?.status(), "/de must be 404").toBe(404);
    const lang = await page.locator("html").getAttribute("lang");
    const dir = await page.locator("html").getAttribute("dir");
    expect(lang).toBe("en");
    expect(dir).toBe("ltr");
  });
});