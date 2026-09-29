import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { expect, APP_ROOT, report, test } from "./helpers";

/**
 * Supply-chain and privacy hygiene for the browser suite.
 *
 * The `page` fixture in `helpers.ts` already fails any test in which the
 * running app requests a non-localhost origin, which is the substantive check.
 * These two close the ways that guard can be bypassed: a URL baked into the
 * served markup that is never fetched, and an analytics global that is loaded
 * from the same origin.
 */

const PLAYWRIGHT_CONFIG = join(APP_ROOT, "playwright.config.ts");

test.describe("browser-suite hygiene", () => {
  test("the served HTML references no absolute non-localhost URL", async ({ request }) => {
    const response = await request.get("/");
    expect(response.status()).toBe(200);
    const html = await response.text();

    const absolute = Array.from(
      html.matchAll(/(?:src|href|action|data-src)\s*=\s*["'](https?:\/\/[^"']+)["']/gi),
    ).map((match) => match[1]);
    report(`absolute URLs in served HTML: ${JSON.stringify(absolute)}`);
    expect(
      absolute.filter((url) => new URL(url).hostname !== "localhost"),
      "the served document must not point at anything but localhost",
    ).toEqual([]);

    // No analytics or tag-manager payload is inlined into the document. The
    // needles are deliberately specific: an earlier pass used the bare string
    // "G-", which matched `ring-1` in a Tailwind class and failed the run for
    // no reason. A detector that cries wolf is a disabled detector.
    const payloads = [
      "googletagmanager.com",
      "google-analytics.com",
      "gtag/js",
      "plausible.io",
      "segment.io",
      "hotjar.com",
      /gtag\(/i,
      /\bG-[A-Z0-9]{6,}\b/,
    ];
    const found = payloads.filter((needle) =>
      typeof needle === "string"
        ? html.toLowerCase().includes(needle.toLowerCase())
        : needle.test(html),
    );
    report(`analytics payloads in served HTML: ${JSON.stringify(found.map(String))}`);
    expect(found.map(String)).toEqual([]);
  });

  test("the running page exposes no analytics globals", async ({ page }) => {
    await page.goto("/");
    const globals = await page.evaluate(() =>
      ["gtag", "ga", "analytics", "_paq", "plausible", "segment", "intercom", "hotjar"]
        .filter((name) => (window as unknown as Record<string, unknown>)[name] !== undefined)
        .map((name) => name),
    );
    report(`analytics globals on window: ${JSON.stringify(globals)}`);
    expect(globals).toEqual([]);
  });

  test("the Playwright config carries no credential-shaped literal", async () => {
    const source = await readFile(PLAYWRIGHT_CONFIG, "utf8");
    // A crude but honest sweep: nothing that looks like a bearer token, an
    // API key assignment, or a hard-coded auth header.
    const suspicious = source.match(
      /(bearer\s+[a-z0-9._-]{16,}|sk-[a-z0-9]{16,}|(?:api[_-]?key|token|password|secret|authorization)\s*[:=]\s*["'][^"']{6,}["'])/gi,
    );
    report(`credential-shaped literals in playwright.config.ts: ${JSON.stringify(suspicious ?? [])}`);
    expect(suspicious ?? []).toEqual([]);
  });
});
