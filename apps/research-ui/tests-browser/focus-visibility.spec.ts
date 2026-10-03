import {
  DESKTOP_VIEWPORT,
  expect,
  focusStyleOf,
  type FocusStyle,
  MOBILE_VIEWPORT,
  readColourToken,
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
const PRIMARY_NAV_LINK = 'nav[data-nav-region="primary"] a[href]';
const LOCALE_NAV_LINK = 'nav[data-nav-region="locale"] a[href]';
const MOBILE_TRIGGER = "[aria-controls='mobile-primary-nav']";

/**
 * The custom property that defines the application ring, in `app/globals.css`.
 *
 * Packet UI-01c (finding F3) changed this token. It used to read
 * `--color-accent: #1d4ed8`, and this file asserted the *literal*
 * `rgb(29, 78, 216)` in two places, so the palette could not move without the
 * literal going stale — the literal was a second, undeclared copy of the
 * stylesheet, and it was the copy that decided the test.
 *
 * The expected colour is now read off the live document with
 * `readColourToken`, which normalises the declared hex into the `rgb()` form
 * Chromium reports for a computed colour. That keeps the assertion about what
 * it was always about — *the application's own declared ring, not the browser's
 * fallback* — and stops it from being a stale mirror of a value it is supposed
 * to police.
 *
 * Three things stop this from being a weakening, and all three are asserted
 * below: the ring's width, style and offset are pinned to values no user-agent
 * default produces; the resolved token is asserted to be different from the
 * user-agent default colour; and the nav ring is cross-checked against the skip
 * link's own ring in the same run, so `a:focus-visible` and `.skip-link:focus`
 * cannot drift onto different tokens without the suite going red.
 */
const FOCUS_COLOUR_TOKEN = "--color-focus";

/** What Chromium reports when the application rule is absent. */
const USER_AGENT_OUTLINE_COLOUR = "rgb(16, 16, 16)";

const APP_FOCUS_OUTLINE_WIDTH_PX = 2;
const APP_FOCUS_OUTLINE_OFFSET_PX = 2;

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
 * resolved `--color-focus` token. Width alone is not enough (1px is a width),
 * style alone is not enough (`auto` is a style), and colour alone is not enough
 * (`rgb(16,16,16)` is a colour). All three together cannot be produced by the
 * browser default.
 */
function expectAppFocusRing(name: string, style: FocusStyle, expectedColour: string): void {
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
    `${name} outline-color: expected the app focus token ${FOCUS_COLOUR_TOKEN} (${expectedColour}), got ${style.outlineColor}`,
  ).toBe(expectedColour);
  expect(
    Number.parseFloat(style.outlineOffset),
    `${name} outline-offset: expected ${APP_FOCUS_OUTLINE_OFFSET_PX}px, got ${style.outlineOffset}`,
  ).toBe(APP_FOCUS_OUTLINE_OFFSET_PX);
  report(
    `${name} application ring: ${style.outlineWidth} ${style.outlineStyle} ${style.outlineColor} offset=${style.outlineOffset} (expected "${APP_FOCUS_OUTLINE_WIDTH_PX}px solid ${expectedColour}")`,
  );
}

test.describe("rendered focus visibility", () => {
  test("the skip link is visibly focused at 375px and the clip reveal really happens", async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en");

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

    // The skip link's ring is the application's, not the browser's. Asserted on
    // the token so the palette can move without a stale literal going green
    // (packet UI-01c, finding F3); see the note on `FOCUS_COLOUR_TOKEN`.
    expect(
      style.outlineColor,
      "the skip link must carry the application focus token, not the user-agent default",
    ).toBe(await readColourToken(page, FOCUS_COLOUR_TOKEN));
  });

  test("the skip link is visibly focused at 1440px", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");
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

    // Same application-token assertion as the 375px run, for the same reason:
    // a focus ring that is merely *some* ring is not the gate.
    expect(
      style.outlineColor,
      "the skip link must carry the application focus token, not the user-agent default",
    ).toBe(await readColourToken(page, FOCUS_COLOUR_TOKEN));
  });

  test("keyboard focus on the primary nav link and the mobile trigger is visible", async ({
    page,
  }) => {
    // 1440px: the primary nav link.
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const navLink = await focusStyleOf(page, PRIMARY_NAV_LINK);
    report(
      `primary nav link FOCUSED @1440: :focus-visible=${navLink.focusVisible} outline=${navLink.outlineWidth} ${navLink.outlineStyle} ${navLink.outlineColor} offset=${navLink.outlineOffset}`,
    );

    /*
     * The expected ring colour, read from the served stylesheet rather than
     * copied beside it. If the declaration is missing entirely this throws,
     * which is the correct outcome: the run measured a page whose stylesheet has
     * no focus token, and a colour assertion against a hard-coded value would
     * have silently passed or failed for unrelated reasons.
     */
    const focusToken = await readColourToken(page, FOCUS_COLOUR_TOKEN);
    report(`${FOCUS_COLOUR_TOKEN} resolves to ${focusToken}`);

    // The non-vacuity guard. Without this, a stylesheet that declared
    // `--color-focus` as the browser default would satisfy the colour assertion
    // while the application rule was absent; the width/style/offset assertions
    // would still fail in that case, so this is belt-and-braces rather than the
    // only thing standing between the suite and a vacuous pass.
    expect(
      focusToken,
      `${FOCUS_COLOUR_TOKEN} must not be the user-agent default outline colour`,
    ).not.toBe(USER_AGENT_OUTLINE_COLOUR);

    // 375px: the disclosure trigger.
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const trigger = await focusStyleOf(page, MOBILE_TRIGGER);
    report(
      `mobile trigger FOCUSED @375: :focus-visible=${trigger.focusVisible} outline=${trigger.outlineWidth} ${trigger.outlineStyle} ${trigger.outlineColor} offset=${trigger.outlineOffset}`,
    );

    expectAppFocusRing("primary nav link @1440", navLink, focusToken);
    expectAppFocusRing("mobile trigger @375", trigger, focusToken);

    // Cross-check: the shared rule must agree with the skip link's own
    // explicit `:focus` treatment, or "one application ring" is only a claim.
    //
    // This is also the check that catches the specific drift packet UI-01c
    // warns about (finding F3): moving `a:focus-visible` onto a new
    // `--color-focus` token while `.skip-link:focus` keeps the old one would
    // satisfy acceptance A9 perfectly and fail here, because the two render
    // different colours. Both rules now read `--color-focus`, so they agree.
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");
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

  /*
   * The same ring in Arabic (packet UI-01d, N18).
   *
   * Focus visibility is the one accessibility guarantee that a mirrored layout
   * can plausibly break on its own: a logical `inset-inline-start` offset, an
   * `rtl:` typography override or a reordered flex row can all push the indicator
   * out of the box it is supposed to be marking. Nothing about the *ring* is
   * translated, so the assertions here are the English ones applied to `ar` —
   * plus the locale links, which are new focusables this packet introduced and
   * would otherwise never be focus-tested in any locale at all.
   */
  test("the ring is visible on the nav link, the trigger and each locale link in ar", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/ar");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    const navLink = await focusStyleOf(page, PRIMARY_NAV_LINK);
    const firstLocaleLink = await focusStyleOf(page, LOCALE_NAV_LINK);
    const focusToken = await readColourToken(page, FOCUS_COLOUR_TOKEN);
    report(
      `ar nav link FOCUSED: :focus-visible=${navLink.focusVisible} outline=${navLink.outlineWidth} ${navLink.outlineStyle}; locale link ${JSON.stringify(firstLocaleLink.label)} :focus-visible=${firstLocaleLink.focusVisible}`,
    );

    expectAppFocusRing("primary nav link @1440/ar", navLink, focusToken);
    expectAppFocusRing("first locale link @1440/ar", firstLocaleLink, focusToken);

    // Each of the three selector links is reachable and ringed, not just the
    // first one — the ring is asserted after every press, so a locale whose link
    // dropped out of the order fails here rather than silently never being
    // visited.
    for (let index = 0; index < 2; index += 1) {
      await page.keyboard.press("Tab");
      const next = await focusStyleOf(page, LOCALE_NAV_LINK);
      expectAppFocusRing(`locale link ${index + 2} @1440/ar`, next, focusToken);
      report(`ar locale link ${index + 2} FOCUSED: ${JSON.stringify(next.label)}`);
    }

    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/ar");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const trigger = await focusStyleOf(page, MOBILE_TRIGGER);
    report(
      `ar mobile trigger FOCUSED @375: :focus-visible=${trigger.focusVisible} outline=${trigger.outlineWidth} ${trigger.outlineStyle} ${trigger.outlineColor}`,
    );
    expectAppFocusRing("mobile trigger @375/ar", trigger, focusToken);
  });
});
