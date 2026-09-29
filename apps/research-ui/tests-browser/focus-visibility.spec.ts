import {
  DESKTOP_VIEWPORT,
  expect,
  focusStyleOf,
  type FocusStyle,
  MOBILE_VIEWPORT,
  report,
  test,
} from "./helpers";

/**
 * Rendered focus visibility.
 *
 * `app/globals.css` hides `.skip-link` with the clip technique and reveals it
 * on `:focus`. Whether that reveal is actually visible is a rendering question,
 * so it is answered here against computed style read off the live element, not
 * inferred from the source. The same file also owns the shared application
 * focus ring: a non-zero `outline-width` is not evidence of one, because the
 * user-agent default has one, so `expectAppFocusRing` pins the width, style,
 * colour and offset. The visual confirmation is captured separately by
 * `screenshots.spec.ts`, which owns the whole committed set.
 */


const SKIP_LINK = "a.skip-link";
const PRIMARY_NAV_LINK = 'nav[aria-label="Primary"] a[href]';
const MOBILE_TRIGGER = "[aria-controls='mobile-primary-nav']";

/**
 * The one application focus ring, as it must read on the rendered page.
 *
 * `app/globals.css` declares it once, for `a:focus-visible, button:focus-visible`,
 * using `var(--color-accent)`. UI-00b measured that the primary-nav link and
 * the mobile trigger were falling through to the user-agent default
 * (`outline: 1px auto rgb(16, 16, 16)`), which is platform-dependent and
 * low-contrast — and an assertion of "outline-width > 0" is satisfied by that
 * default, so it could not have caught the gap. These constants are the
 * application's own values, quoted from `app/globals.css` (`--color-accent:
 * #1d4ed8`) and the 2px/2px geometry shared with `.skip-link:focus`; a
 * regression to `1px auto` fails all three.
 */
const APP_FOCUS_OUTLINE = "2px solid rgb(29, 78, 216)";
const APP_FOCUS_OUTLINE_WIDTH_PX = 2;
const APP_FOCUS_OUTLINE_OFFSET_PX = 2;
const APP_ACCENT_RGB = "rgb(29, 78, 216)";

/** A computed colour is "real" when it is an `rgb()`/`rgba()` with alpha > 0. */
function parseColour(value: string): { r: number; g: number; b: number; a: number } | null {
  const match = /^rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)(?:[\s,/]+([\d.]+))?\s*\)$/.exec(value);
  if (match === null) return null;
  return {
    r: Number(match[1]),
    g: Number(match[2]),
    b: Number(match[3]),
    a: match[4] === undefined ? 1 : Number(match[4]),
  };
}

/**
 * Assert the element shows the *application* ring, not merely some ring.
 *
 * The user-agent default reports `1px auto rgb(16, 16, 16)`, so the width, the
 * style and the colour are each checked: width 2px, style solid, and the
 * accent token. Width alone is not enough (1px is a width), style alone is not
 * enough (`auto` is a style), and colour alone is not enough (`rgb(16,16,16)`
 * is a colour). All three together cannot be produced by the browser default.
 */
function expectAppFocusRing(name: string, style: FocusStyle): void {
  expect(style.focusVisible, `${name} must match :focus-visible`).toBe(true);
  expect(
    Number.parseFloat(style.outlineWidth),
    `${name} outline-width: expected ${APP_FOCUS_OUTLINE_WIDTH_PX}px, got ${style.outlineWidth}`,
  ).toBe(APP_FOCUS_OUTLINE_WIDTH_PX);
  expect(
    style.outlineStyle,
    `${name} outline-style: expected solid, got ${style.outlineStyle}`,
  ).toBe("solid");
  expect(
    style.outlineColor,
    `${name} outline-color: expected the app accent from app/globals.css`,
  ).toBe(APP_ACCENT_RGB);
  expect(
    Number.parseFloat(style.outlineOffset),
    `${name} outline-offset: expected ${APP_FOCUS_OUTLINE_OFFSET_PX}px, got ${style.outlineOffset}`,
  ).toBe(APP_FOCUS_OUTLINE_OFFSET_PX);
  report(
    `${name} application ring: ${style.outlineWidth} ${style.outlineStyle} ${style.outlineColor} offset=${style.outlineOffset} (expected "${APP_FOCUS_OUTLINE}")`,
  );
}

test.describe("rendered focus visibility", () => {
  test("the skip link is visibly focused at 375px and the clip reveal really happens", async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");

    // Before focus: the clip technique is in force, so the element occupies a
    // 1px box. This is the state `app/globals.css:53-63` describes.
    const clipped = await page.evaluate((selector) => {
      const el = document.querySelector<HTMLElement>(selector);
      if (el === null) throw new Error("skip link missing");
      const box = el.getBoundingClientRect();
      return { clipPath: getComputedStyle(el).clipPath, width: box.width, height: box.height };
    }, SKIP_LINK);
    report(`skip link UNfocused: clip-path=${clipped.clipPath} box=${clipped.width}x${clipped.height}`);
    expect(clipped.clipPath).not.toBe("none");

    await page.keyboard.press("Tab");
    const focused = await page.evaluate((selector) => {
      const el = document.querySelector<HTMLElement>(selector);
      return el === document.activeElement;
    }, SKIP_LINK);
    expect(focused, "one Tab press must land on the skip link").toBe(true);

    const style = await focusStyleOf(page, SKIP_LINK);
    report(
      `skip link FOCUSED @375: :focus-visible=${style.focusVisible} outline=${style.outlineWidth} ${style.outlineStyle} ${style.outlineColor} offset=${style.outlineOffset} position=${style.position} clip-path=${style.clipPath} box=${style.width}x${style.height} withinViewport=${style.withinViewport}`,
    );

    expect(style.focusVisible).toBe(true);
    expect(Number.parseFloat(style.outlineWidth)).toBeGreaterThan(0);
    expect(style.outlineStyle).not.toBe("none");
    const colour = parseColour(style.outlineColor);
    expect(colour, `outline-color did not resolve to a colour: ${style.outlineColor}`).not.toBeNull();
    expect(colour?.a ?? 0).toBeGreaterThan(0);
    // The reveal: no longer clipped, real size, actually on screen.
    expect(style.clipPath).toBe("none");
    expect(style.width).toBeGreaterThan(20);
    expect(style.height).toBeGreaterThan(10);
    expect(style.withinViewport).toBe(true);
  });

  test("the skip link is visibly focused at 1440px", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/");
    await page.keyboard.press("Tab");

    const style = await focusStyleOf(page, SKIP_LINK);
    report(
      `skip link FOCUSED @1440: :focus-visible=${style.focusVisible} outline=${style.outlineWidth} ${style.outlineStyle} ${style.outlineColor} offset=${style.outlineOffset} withinViewport=${style.withinViewport}`,
    );

    expect(style.focusVisible).toBe(true);
    expect(Number.parseFloat(style.outlineWidth)).toBeGreaterThan(0);
    const colour = parseColour(style.outlineColor);
    expect(colour, `outline-color did not resolve to a colour: ${style.outlineColor}`).not.toBeNull();
    expect(colour?.a ?? 0).toBeGreaterThan(0);
    expect(style.clipPath).toBe("none");
  });

  test("keyboard focus on the primary nav link and the mobile trigger is visible", async ({
    page,
  }) => {
    // 1440px: the primary nav link.
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const navLink = await focusStyleOf(page, PRIMARY_NAV_LINK);
    report(
      `primary nav link FOCUSED @1440: :focus-visible=${navLink.focusVisible} outline=${navLink.outlineWidth} ${navLink.outlineStyle} ${navLink.outlineColor} offset=${navLink.outlineOffset}`,
    );

    // 375px: the disclosure trigger.
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const trigger = await focusStyleOf(page, MOBILE_TRIGGER);
    report(
      `mobile trigger FOCUSED @375: :focus-visible=${trigger.focusVisible} outline=${trigger.outlineWidth} ${trigger.outlineStyle} ${trigger.outlineColor} offset=${trigger.outlineOffset}`,
    );

    expectAppFocusRing("primary nav link @1440", navLink);
    expectAppFocusRing("mobile trigger @375", trigger);

    // Cross-check: the shared rule must agree with the skip link's own
    // explicit `:focus` treatment, or "one application ring" is only a claim.
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/");
    await page.keyboard.press("Tab");
    const skipLink = await focusStyleOf(page, SKIP_LINK);
    report(
      `skip link ring for cross-check: ${skipLink.outlineWidth} ${skipLink.outlineStyle} ${skipLink.outlineColor} offset=${skipLink.outlineOffset}`,
    );
    expect(
      `${navLink.outlineWidth} ${navLink.outlineStyle} ${navLink.outlineColor}`,
      "the nav link ring must match the skip link ring",
    ).toBe(`${skipLink.outlineWidth} ${skipLink.outlineStyle} ${skipLink.outlineColor}`);
  });
});
