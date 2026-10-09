import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { test as base, type Page } from "@playwright/test";

/**
 * Shared helpers for the browser suite.
 *
 * Deliberately dependency-free: no fixture library, no global setup, no
 * synthetic data. Every value a test asserts was read out of the running
 * application, and the measured values are echoed to stdout so the run's own
 * output is the report's source.
 */

/** Absolute path of the application root (`apps/research-ui/`). */
export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));

/** Where the committed screenshots are written. Deliberately NOT gitignored. */
export const SCREENSHOT_DIR = join(APP_ROOT, "screenshots");

/** The two real viewports every responsive gate is measured at. */
export const MOBILE_VIEWPORT = { width: 375, height: 812 } as const;
export const DESKTOP_VIEWPORT = { width: 1440, height: 900 } as const;

/** `components/mobile-nav.tsx` exports these; mirrored here, never invented. */
export const MOBILE_NAV_PANEL_ID = "mobile-primary-nav";
export const MOBILE_NAV_CLOSE_LABEL = "Close main navigation";
export const SKIP_LINK_LABEL = "Skip to main content";

/**
 * Locale-stable selectors (packet UI-01d, D-I18N-10).
 *
 * These replace `nav[aria-label="Primary"]` and
 * `getByRole("button", { name: "Open main navigation" })` throughout the suite,
 * and the reason is not tidiness: both of those spell an *English string* that
 * this packet translates. A selector built from an English accessible name keeps
 * matching nothing in `fr` and `ar` — or, worse, keeps matching the wrong element
 * if a translation collides — so a test that passed in `en` would quietly stop
 * asserting anything in the other two locales. The hooks are part of the markup
 * contract (`D-I18N-10`), so the suite reads them the same way the packet does.
 *
 * `MOBILE_NAV_TRIGGER_LABEL` is deliberately **gone** rather than kept as an
 * unused export: leaving it invites the next test to reach for it, and the whole
 * point is that the English label is no longer a reliable handle.
 */
export const PRIMARY_NAV = 'nav[data-nav-region="primary"]';
export const LOCALE_NAV = 'nav[data-nav-region="locale"]';
export const MOBILE_NAV = 'nav[data-nav-region="mobile"]';
export const MOBILE_NAV_TRIGGER = '[data-nav-region="mobile-trigger"]';

/**
 * Base test with one inherited guard: the running application must not make a
 * single request to anything other than localhost. This covers the packet's
 * "no external requests / no analytics" rule for every test, not just the one
 * that thinks to check it, because it lives in the `page` fixture itself.
 */
export const test = base.extend({
  page: async ({ page }, use) => {
    const external: string[] = [];
    page.on("request", (request) => {
      const url = new URL(request.url());
      if (url.protocol !== "http:" && url.protocol !== "https:") return;
      if (url.hostname === "localhost" || url.hostname === "127.0.0.1") return;
      external.push(request.url());
    });
    await use(page);
    if (external.length > 0) {
      throw new Error(
        `the running app requested a non-localhost origin: ${external.join(", ")}`,
      );
    }
  },
});

export { expect } from "@playwright/test";

/** A stable, readable description of whatever currently holds focus. */
export interface FocusStop {
  tag: string;
  text: string;
  inPrimaryNav: boolean;
  inMobileDisclosure: boolean;
  inMobileDialog: boolean;
  inDialogRole: boolean;
  focusId: string;
}

export async function activeStop(page: Page): Promise<FocusStop | null> {
  return page.evaluate((panelId) => {
    const el = document.activeElement as HTMLElement | null;
    if (el === null || el === document.body || el === document.documentElement) {
      return null;
    }
    const text = (el.getAttribute("aria-label") ?? el.textContent ?? "").replace(/\s+/g, " ").trim();
    return {
      tag: el.tagName.toLowerCase(),
      text,
      focusId: el.id,
      inPrimaryNav: el.closest('nav[data-nav-region="primary"]') !== null,
      inMobileDisclosure: el.closest("[aria-controls]") !== null,
      inMobileDialog: el.closest(`#${panelId}`) !== null,
      // The accessibility boundary is the dialog subtree, which Headless UI
      // roots at its own `role="dialog"` element — an *ancestor* of
      // `DialogPanel`, not the panel itself. See `GATES.md` §3.1.
      inDialogRole: el.closest('[role="dialog"]') !== null,
    };
  }, MOBILE_NAV_PANEL_ID);
}

/** `<document>` is the honest name for "focus left the page", not a failure. */
export function describeStop(stop: FocusStop | null): string {
  return stop === null ? "<document>" : `${stop.tag}:${stop.text}`;
}

/**
 * Press `Tab` up to `presses` times from a freshly loaded document and record
 * the real ring, stopping when focus leaves the page.
 *
 * The page is reloaded first on purpose: Chromium keeps a "sequential focus
 * navigation starting point" that `blur()` does not reliably reset, so a warm
 * page would measure where the last test left off rather than the top of the
 * document.
 *
 * `locale` is stated explicitly (packet UI-01d, M4) rather than left to the `/`
 * redirect: the ring's *contents* are translated — the skip link, the nav item
 * and the three language names all change — so a ring measured through a redirect
 * is a ring measured in one locale by accident. `/` still redirects to `/en`, so
 * the default keeps old call sites green while every locale-aware test says which
 * document it meant.
 *
 * The `documentElement.lang` check immediately after the navigation is a
 * non-vacuity guard, not an assertion the caller opted into. The default
 * `locale = "en"` is a convenience, and a convenience alone leaves the original
 * defect reachable by omission: a caller who asks for the `ar` ring against a
 * page that silently served `en` would assert an Arabic ring and measure an
 * English one. So the helper **throws** unless the served document really declares
 * the locale it was asked for — the failure is loud, at the point of the mistake,
 * instead of a green assertion somewhere downstream.
 *
 * `subpath` (packet UI-04) selects a route *within* the locale — `"/screening"`
 * for the screening workspace — instead of the locale root. It is a suffix of
 * the same `/${locale}` document, never a bare path: the ring's labels are
 * locale-dependent, so a route measured without its locale would be measuring
 * the wrong language, which is the very defect the `lang` guard exists to catch.
 */
export async function measureTabRing(
  page: Page,
  presses = 8,
  locale = "en",
  subpath = "",
): Promise<FocusStop[]> {
  await page.goto(`/${locale}${subpath}`);
  const declared = await page.evaluate(() => document.documentElement.lang);
  if (declared !== locale) {
    throw new Error(
      `measureTabRing asked for the /${locale} ring but the served document declares ` +
        `lang="${declared}"; measuring the wrong language is worse than failing`,
    );
  }
  const ring: FocusStop[] = [];
  for (let index = 0; index < presses; index += 1) {
    await page.keyboard.press("Tab");
    const stop = await activeStop(page);
    if (stop === null) break;
    ring.push(stop);
  }
  return ring;
}

/** The computed focus-indicator values, read from the live element. */
export interface FocusStyle {
  label: string;
  focusVisible: boolean;
  outlineStyle: string;
  outlineWidth: string;
  outlineColor: string;
  outlineOffset: string;
  clipPath: string;
  position: string;
  width: number;
  height: number;
  withinViewport: boolean;
}

export async function focusStyleOf(page: Page, selector: string): Promise<FocusStyle> {
  return page.evaluate((target) => {
    const el = document.querySelector<HTMLElement>(target);
    if (el === null) throw new Error(`no element matches ${target}`);
    el.focus();
    const style = getComputedStyle(el);
    const box = el.getBoundingClientRect();
    return {
      label: (el.getAttribute("aria-label") ?? el.textContent ?? "")
        .replace(/\s+/g, " ")
        .trim(),
      focusVisible: el.matches(":focus-visible"),
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
      outlineColor: style.outlineColor,
      outlineOffset: style.outlineOffset,
      clipPath: style.clipPath,
      position: style.position,
      width: Math.round(box.width * 100) / 100,
      height: Math.round(box.height * 100) / 100,
      withinViewport: box.top >= 0 && box.left >= 0 && box.right <= innerWidth && box.bottom <= innerHeight,
    };
  }, selector);
}

/** Human-readable one-liner for the run log and the report. */
export function report(line: string): void {
  console.log(`[measured] ${line}`);
}

/**
 * Normalise a CSS colour literal to the `rgb(r, g, b)` spelling Chromium uses
 * for a computed colour.
 *
 * This exists (packet UI-01c, decision D4) because the two spellings of the
 * same colour are not interchangeable. A custom property declared in
 * `app/globals.css` keeps the literal that was written, so `--color-focus:
 * #1c1a17` reads back as `#1c1a17`, while `getComputedStyle(el).outlineColor`
 * for an element using that token reads back as `rgb(28, 26, 23)`. Comparing the
 * two directly fails on format even though both are the same colour and the
 * rendered result is correct.
 *
 * It accepts 3- and 6-digit hex and passes `rgb()`/`rgba()` through unchanged,
 * and **throws** on anything else rather than returning a best-effort string: a
 * silent fallback here would turn a colour-token regression into a confusing
 * string mismatch instead of a legible error at the point of failure.
 */
export function toRgbString(value: string): string {
  const literal = value.trim();
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(literal);
  if (hex !== null) {
    const digits =
      hex[1].length === 3
        ? hex[1]
            .split("")
            .map((digit) => digit + digit)
            .join("")
        : hex[1];
    const channels = [0, 2, 4].map((offset) =>
      Number.parseInt(digits.slice(offset, offset + 2), 16),
    );
    return `rgb(${channels.join(", ")})`;
  }
  if (/^rgba?\(/i.test(literal)) {
    return literal;
  }
  throw new Error(
    `cannot normalise CSS colour literal to an rgb() form: ${JSON.stringify(value)}`,
  );
}

/**
 * Read a `--color-*` / `--font-*` custom property off the live document and, for
 * a colour, normalise it with {@link toRgbString}.
 *
 * The token is read from `:root` on the running page, so the assertion follows
 * the shipped stylesheet instead of a literal copied beside it — a literal is
 * exactly what goes stale when the palette is redesigned (packet UI-01c,
 * finding F3). The companion assertion that keeps this honest is in
 * `tests-browser/focus-visibility.spec.ts`: the width, style and offset are
 * pinned independently of the colour, and the ring is cross-checked against the
 * skip link's own ring, so deleting the CSS rule still fails the suite rather
 * than silently passing a different colour.
 */
export async function readColourToken(page: Page, token: string): Promise<string> {
  const declared = await page.evaluate((name) => {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }, token);
  if (declared === "") {
    throw new Error(`custom property ${token} is not declared on :root in the served CSS`);
  }
  return toRgbString(declared);
}
