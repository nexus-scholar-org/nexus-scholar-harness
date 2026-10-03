import { expect, type Page } from "@playwright/test";

/**
 * The horizontal-overflow recipe, in a module with **no** test registrations.
 *
 * It is here rather than inline in `overflow.spec.ts` because two configurations
 * must run literally the same measurement: the browser suite
 * (`playwright.config.ts`, `tests-browser/overflow.spec.ts`) and the 30 %
 * expansion gate (`playwright.long-strings.config.ts`,
 * `tests-long-strings/long-strings.spec.ts`). A copy of this measurement in the
 * long-strings spec would be a second implementation, and the day it drifted —
 * say by loosening a tolerance — the gate would still be green while measuring
 * something weaker than the suite it claims to mirror. So the long-strings spec
 * imports these two functions and the runner owns no assertions of its own.
 *
 * Two deliberate properties:
 *
 * 1. **It is not per-element.** The check is over `documentElement`, `body` and
 *    `main`, not over every descendant. A single element that is allowed to shrink
 *    — a `min-w-0` flex child, a long identifier inside a `<bdi>` — reports
 *    `scrollWidth > clientWidth` while causing no page-level scroll, so per-element
 *    checking yields failures that must each be argued away, and each argument is
 *    an opportunity to relax a real constraint. What this gate needs to know is
 *    whether *the reader* can scroll sideways.
 * 2. **The `documentElement` comparison is strict and `<body>`/`<main>` carry a
 *    1px tolerance.** Sub-pixel rounding of fractional layout widths is not a
 *    scrollbar; asserting a strict `<=` against it would be a flaky assertion
 *    dressed up as a strict one.
 */

export interface OverflowReading {
  innerWidth: number;
  documentElement: { scrollWidth: number; clientWidth: number };
  body: { scrollWidth: number; clientWidth: number };
  main: { scrollWidth: number; clientWidth: number };
}

/** Read the three widths that decide whether the viewport scrolls sideways. */
export async function measureOverflow(page: Page): Promise<OverflowReading> {
  return page.evaluate(() => {
    const read = (element: Element | null) =>
      element === null
        ? { scrollWidth: 0, clientWidth: 0 }
        : { scrollWidth: element.scrollWidth, clientWidth: element.clientWidth };
    return {
      innerWidth: window.innerWidth,
      documentElement: read(document.documentElement),
      body: read(document.body),
      main: read(document.querySelector("main")),
    };
  });
}

/** The shared assertions, with a context string so a failure names its locale. */
export function expectNoSidewaysScroll(measured: OverflowReading, context: string): void {
  expect(
    measured.documentElement.scrollWidth,
    `${context}: the viewport itself must not scroll sideways`,
  ).toBeLessThanOrEqual(measured.documentElement.clientWidth);
  expect(
    measured.body.scrollWidth,
    `${context}: body must not scroll sideways`,
  ).toBeLessThanOrEqual(measured.body.clientWidth + 1);
  expect(
    measured.main.scrollWidth,
    `${context}: main must not scroll sideways`,
  ).toBeLessThanOrEqual(measured.main.clientWidth + 1);
}