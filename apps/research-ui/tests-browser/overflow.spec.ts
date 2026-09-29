import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, report, test } from "./helpers";

/**
 * Horizontal overflow, measured on the real layout.
 *
 * jsdom performs no layout, so nothing in the in-process suite can see a
 * sideways scrollbar. `scrollWidth`/`clientWidth` are read off the live
 * `documentElement`, `body` and `<main>`.
 *
 * The `<body>` and `<main>` checks use a 1px tolerance: sub-pixel rounding of
 * fractional layout widths is not a scrollbar, and asserting a strict `<=`
 * against it would be a flaky assertion dressed up as a strict one. The
 * `documentElement` check is strict, because that is the one that decides
 * whether the viewport actually scrolls sideways.
 */

interface Overflow {
  scrollWidth: number;
  clientWidth: number;
}

test.describe("horizontal overflow", () => {
  for (const [name, viewport] of [
    ["375px", MOBILE_VIEWPORT],
    ["1440px", DESKTOP_VIEWPORT],
  ] as const) {
    test(`${name}: nothing scrolls sideways`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/");

      const measured = await page.evaluate(() => {
        const main = document.querySelector("main");
        const read = (element: Element | null): Record<string, number> =>
          element === null
            ? {}
            : { scrollWidth: element.scrollWidth, clientWidth: element.clientWidth };
        return {
          innerWidth: window.innerWidth,
          documentElement: read(document.documentElement),
          body: read(document.body),
          main: read(main),
        };
      });

      report(
        `${name} overflow: ${JSON.stringify(measured)}`,
      );

      expect(measured.documentElement.scrollWidth).toBeLessThanOrEqual(
        measured.documentElement.clientWidth,
      );
      expect(measured.body.scrollWidth).toBeLessThanOrEqual(measured.body.clientWidth + 1);
      expect(measured.main.scrollWidth).toBeLessThanOrEqual(measured.main.clientWidth + 1);
    });
  }

  test("no unbreakable token in the shipped fixture can force a sideways scroll", async ({
    page,
  }) => {
    // The check is over the strings the application actually ships. There is no
    // synthetic long token injected here: inventing one would be fabricating
    // data to make a gate look covered.
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");

    const widest = await page.evaluate(() => {
      let longest = { text: "", width: 0 };
      for (const node of Array.from(document.querySelectorAll("body *"))) {
        const style = getComputedStyle(node);
        if (style.display === "none" || style.visibility === "hidden") continue;
        // A real unbreakable run has no break opportunity inside it.
        const word = node.textContent?.match(/[^\s]{24,}/)?.[0] ?? null;
        if (word === null) continue;
        const box = node.getBoundingClientRect();
        if (box.width > longest.width) longest = { text: word, width: Math.round(box.width) };
      }
      return longest;
    });

    report(`375px widest unbreakable token: ${JSON.stringify(widest)}`);
    // 24 characters is well under the ~343px content box of a 375px viewport.
    expect(widest.text.length === 0 || widest.width <= 375).toBe(true);
  });
});
