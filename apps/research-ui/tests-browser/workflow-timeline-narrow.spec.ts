import { demoProject } from "../lib/mock-project";
import { CATALOGS } from "../messages";
import { MOBILE_VIEWPORT, expect, report, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * The narrow-width half of packet UI-03's gate: "state matrix test and
 * narrow-width visual check".
 *
 * The matrix half is `tests/workflow-timeline-state-matrix.test.tsx` (jsdom,
 * four states × three locales). What jsdom cannot answer is whether the icon
 * and the stamp it accompanies actually *fit*: jsdom performs no layout, so a
 * stamp cell pushed past the right edge of a 375px screen passes every
 * in-process assertion. This is the measurement.
 *
 * Two properties, both asserted rather than assumed:
 *
 * 1. **Every demo stage row carries exactly one icon and this locale's stamp
 *    word.** The row count is compared against `demoProject.stages`, not
 *    against a literal, so a fixture that gains or loses a stage moves the
 *    expectation instead of leaving it stale — and a page that rendered no
 *    timeline at all fails rather than passing an empty loop.
 * 2. **After the row is scrolled into view, its icon, its stamp cell and the
 *    stamp itself are each fully inside the viewport**, in both axes. Horizontal
 *    is the packet's "no horizontal clipping/overflow for the stamp cell";
 *    vertical is checked only *after* `scrollIntoViewIfNeeded`, because before
 *    that call a below-the-fold row is legitimately outside the viewport and an
 *    assertion on it would be an assertion about scrolling, not about layout.
 *
 * `measureOverflow` runs first so the page-level recipe
 * (`tests-browser/overflow-recipe.ts`, shared verbatim with the 30 % expansion
 * gate) still owns the sideways-scroll verdict, and this file adds only the
 * per-row boxes it exists for.
 *
 * `en` and `ar` are the two locales the packet names: Arabic is the
 * right-to-left case where a physical offset would push the stamp cell the
 * "wrong" way, and its stamp word is a different length again.
 */

/** The canonical state tokens, mirrored from `lib/contracts.ts`'s union. */
const STATE_TOKENS = ["complete", "active", "waiting", "refused"] as const;

/** This locale's four stamp words, read from the catalogs — never spelled out. */
function stampWords(locale: "en" | "ar"): string[] {
  return STATE_TOKENS.map((token) => CATALOGS[locale][`state.${token}` as "state.complete"]);
}

/** One row of the workflow record: the `<li>` that carries the state icon. */
const STAGE_ROW = "li:has(svg[data-stage-state-icon])";

test.describe("workflow timeline at 375px (packet UI-03)", () => {
  for (const locale of ["en", "ar"] as const) {
    test(`${locale}/375px: every stage row shows its icon and stamp fully inside the viewport`, async ({
      page,
    }) => {
      await page.setViewportSize(MOBILE_VIEWPORT);
      await page.goto(`/${locale}`);
      await page.waitForLoadState("networkidle");

      // The shared page-level recipe first: the verdict on sideways scrolling
      // belongs to one measurement, not to a paraphrase of it.
      const measured = await measureOverflow(page);
      report(`${locale}/375px overflow: ${JSON.stringify(measured)}`);
      expectNoSidewaysScroll(measured, `${locale}/375px`);

      const rows = page.locator(STAGE_ROW);
      const rowCount = await rows.count();
      report(`${locale}/375px stage rows carrying a state icon: ${rowCount}`);
      expect(
        rowCount,
        "one row per demo stage, each carrying a state icon — a page that rendered no timeline would otherwise pass an empty loop",
      ).toBe(demoProject.stages.length);
      expect(rowCount).toBeGreaterThan(0);

      const words = stampWords(locale);

      for (let index = 0; index < rowCount; index += 1) {
        const row = rows.nth(index);
        const icon = row.locator("svg[data-stage-state-icon]");
        expect(await icon.count(), `row ${index} must carry exactly one state icon`).toBe(1);

        const token = await icon.getAttribute("data-stage-state-icon");
        expect(
          STATE_TOKENS as readonly string[],
          `row ${index} must carry a canonical state token`,
        ).toContain(token);

        // The stamp cell is the icon's parent; the stamp is its next sibling —
        // the markup `components/workflow-timeline.tsx` renders.
        const stampCell = icon.locator("xpath=..");
        const stamp = icon.locator("xpath=following-sibling::span[1]");

        // `innerText` reports *rendered* text, and the stamp is uppercase by
        // design (P3), so the comparison is case-insensitive: the claim is that
        // the word is this locale's state word, not that CSS left its case
        // alone. `ar` has no case, which is why only the Latin runs need this.
        const stampText = (await stamp.innerText()).trim().toLowerCase();
        expect(
          words.map((word) => word.toLowerCase()),
          `row ${index} must show one of this locale's four state words, not a bare colour`,
        ).toContain(stampText);

        await row.scrollIntoViewIfNeeded();
        const boxes = [
          ["icon", icon],
          ["stamp cell", stampCell],
          ["stamp", stamp],
        ] as const;

        for (const [name, locator] of boxes) {
          const box = await locator.boundingBox();
          expect(box, `row ${index} ${name} must have a rendered box`).not.toBeNull();
          const boxRect = box!;
          report(
            `${locale}/375px row ${index} ${name}: x ${boxRect.x.toFixed(1)}..${(boxRect.x + boxRect.width).toFixed(1)}, y ${boxRect.y.toFixed(1)}..${(boxRect.y + boxRect.height).toFixed(1)}`,
          );

          expect(boxRect.width, `row ${index} ${name} must not be zero-width`).toBeGreaterThan(0);
          expect(
            boxRect.x,
            `row ${index} ${name} must not start left of the viewport`,
          ).toBeGreaterThanOrEqual(0);
          expect(
            boxRect.x + boxRect.width,
            `row ${index} ${name} must not be clipped at the right edge of the 375px viewport`,
          ).toBeLessThanOrEqual(MOBILE_VIEWPORT.width);
          expect(
            boxRect.y,
            `row ${index} ${name} must not start above the viewport once scrolled to`,
          ).toBeGreaterThanOrEqual(0);
          expect(
            boxRect.y + boxRect.height,
            `row ${index} ${name} must not be clipped at the bottom of the viewport once scrolled to`,
          ).toBeLessThanOrEqual(MOBILE_VIEWPORT.height);
        }
      }
    });
  }
});
