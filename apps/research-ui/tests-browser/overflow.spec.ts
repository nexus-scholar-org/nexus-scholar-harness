import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, report, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * Horizontal overflow, measured on the real layout.
 *
 * jsdom performs no layout, so nothing in the in-process suite can see a
 * sideways scrollbar. `scrollWidth`/`clientWidth` are read off the live
 * `documentElement`, `body` and `<main>`.
 *
 * The measurement and its assertions live in `overflow-recipe.ts`, not here,
 * because the 30 % expansion gate has to run literally this recipe rather than a
 * paraphrase of it; see that module for why the check is not per-element, and why
 * the `<body>`/`<main>` comparisons carry a 1px tolerance while
 * `documentElement`'s is strict.
 *
 * `fr` and `ar` are measured with the same recipe (packet UI-01d, N16): French
 * runs longer than English in this corpus and Arabic has far fewer spaces to
 * break in, so a layout that fits the English strings is not thereby a layout
 * that fits the other two.
 */

const VIEWPORTS = [
  ["375px", MOBILE_VIEWPORT],
  ["1440px", DESKTOP_VIEWPORT],
] as const;

test.describe("horizontal overflow", () => {
  for (const [name, viewport] of VIEWPORTS) {
    test(`${name}: nothing scrolls sideways`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/en");

      const measured = await measureOverflow(page);
      report(`${name} overflow: ${JSON.stringify(measured)}`);
      expectNoSidewaysScroll(measured, `${name}/en`);
    });
  }

  for (const locale of ["fr", "ar"] as const) {
    for (const [name, viewport] of VIEWPORTS) {
      test(`${name}/${locale}: nothing scrolls sideways`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await page.goto(`/${locale}`);

        const measured = await measureOverflow(page);
        report(`${name}/${locale} overflow: ${JSON.stringify(measured)}`);
        expectNoSidewaysScroll(measured, `${name}/${locale}`);
      });
    }
  }

  test("no unbreakable token in the shipped fixture can force a sideways scroll", async ({
    page,
  }) => {
    // The check is over the strings the application actually ships. There is no
    // synthetic long token injected here: inventing one would be fabricating
    // data to make a gate look covered.
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en");

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