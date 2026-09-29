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
export const MOBILE_NAV_TRIGGER_LABEL = "Open main navigation";
export const MOBILE_NAV_CLOSE_LABEL = "Close main navigation";
export const SKIP_LINK_LABEL = "Skip to main content";

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
      inPrimaryNav: el.closest('nav[aria-label="Primary"]') !== null,
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
 */
export async function measureTabRing(page: Page, presses = 8): Promise<FocusStop[]> {
  await page.goto("/");
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
