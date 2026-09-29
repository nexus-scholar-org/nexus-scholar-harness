import {
  DESKTOP_VIEWPORT,
  describeStop,
  expect,
  measureTabRing,
  MOBILE_VIEWPORT,
  report,
  test,
} from "./helpers";

/**
 * The rendered tab ring, measured at two real viewport widths.
 *
 * `tests/keyboard-traversal.test.tsx` (jsdom) asserts the *union* of tab stops
 * across widths, because jsdom applies no stylesheet and therefore cannot know
 * that `display: none` removes an element from the focus order. These two tests
 * close that gap empirically with real `keyboard.press("Tab")` against a real
 * layout engine.
 *
 * The expected sequences below are the ones `GATES.md` §1 gate 12 and
 * `tests/keyboard-traversal.test.tsx` already document. If the application
 * changes such that the measurement differs, the DOCUMENTATION is what gets
 * corrected, not these assertions.
 */
test.describe("rendered tab order", () => {
  test("375px: the desktop <nav> is display:none, so the ring is [skip, trigger]", async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);

    const ring = await measureTabRing(page);
    const order = ring.map(describeStop);
    report(`375px tab ring = ${JSON.stringify(order)}`);

    expect(order).toEqual(["a:Skip to main content", "button:Open main navigation"]);

    // The stop that jsdom also reports is genuinely absent here, and the reason
    // is the rendered one — not an absent element.
    expect(ring.some((stop) => stop.inPrimaryNav)).toBe(false);
    const primaryNav = page.locator('nav[aria-label="Primary"]');
    await expect(primaryNav).toBeHidden();
  });

  test("1440px: the mobile disclosure is display:none, so the ring is [skip, Overview]", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);

    const ring = await measureTabRing(page);
    const order = ring.map(describeStop);
    report(`1440px tab ring = ${JSON.stringify(order)}`);

    expect(order).toEqual(["a:Skip to main content", "a:Overview"]);

    expect(ring.some((stop) => stop.inMobileDisclosure)).toBe(false);
    const trigger = page.getByRole("button", { name: "Open main navigation" });
    await expect(trigger).toBeHidden();
  });
});
