import {
  DESKTOP_VIEWPORT,
  MOBILE_NAV_TRIGGER,
  MOBILE_VIEWPORT,
  PRIMARY_NAV,
  describeStop,
  expect,
  measureTabRing,
  report,
  test,
} from "./helpers";
import { CATALOGS } from "../messages";
import { LOCALE_METADATA } from "../i18n";

/**
 * The rendered tab ring, measured at two real viewport widths, in two directions.
 *
 * `tests/keyboard-traversal.test.tsx` (jsdom) asserts the *union* of tab stops
 * across widths, because jsdom applies no stylesheet and therefore cannot know
 * that `display: none` removes an element from the focus order. These tests close
 * that gap empirically with real `keyboard.press("Tab")` against a real layout
 * engine.
 *
 * The expectations are built from the catalogs rather than written out, and that
 * is the point of this revision (packet UI-01d, M4/M13). Every stop's *label* is
 * translated, so a literal copied into this file is a claim that the translation
 * will never change — and in `ar` the ring's labels are Arabic while its order is
 * identical, which is exactly the property worth asserting. Deriving them from the
 * catalog means a renamed key fails the ring, and a changed translation fails it
 * too, instead of leaving a stale expectation passing against a document nobody
 * reads.
 *
 * If a measurement differs, the DOCUMENTATION is what gets corrected, not these
 * assertions.
 *
 * **Both rings grew by three stops in this revision, and that is the packet's
 * requirement rather than a drift.** `D-I18N-11` is explicit that the locale
 * selector carries *no breakpoint* — it is visible at 375px as well as 1440px,
 * because hiding it below `lg` would leave a mobile user with no locale affordance
 * at all when the URL is the only source of locale truth — and it pins the
 * resulting `order` at both viewports. The two test titles that previously read
 * "the ring is [skip, trigger]" and "the ring is [skip, Overview]" are therefore
 * updated to state the full sequence; §13.1 lists rows 35, 40, 44, 53 and 56 of
 * this file as updated for exactly that reason, and a title that understated the
 * measured ring would be its own kind of false claim.
 */

/** The three language names, in tab order — endonyms, so they never translate. */
const LOCALE_ENDONYMS = [
  LOCALE_METADATA.en.endonym,
  LOCALE_METADATA.fr.endonym,
  LOCALE_METADATA.ar.endonym,
];

test.describe("rendered tab order", () => {
  test("375px: the desktop <nav> is display:none, so the ring is [skip, trigger, three locales]", async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);

    const ring = await measureTabRing(page, 8, "en");
    const order = ring.map(describeStop);
    report(`375px/en tab ring = ${JSON.stringify(order)}`);

    // The skip link and the disclosure trigger are the whole ring *besides* the
    // selector: the desktop `<nav>` is `display: none` here, so its links are not
    // stops, and the selector's three links are, because it is in the header at
    // every width.
    expect(order).toEqual([
      `a:${CATALOGS.en["a11y.skipToMain"]}`,
      `button:${CATALOGS.en["a11y.openMainNavigation"]}`,
      ...LOCALE_ENDONYMS.map((endonym) => `a:${endonym}`),
    ]);

    // The stop that jsdom also reports is genuinely absent here, and the reason
    // is the rendered one — not an absent element.
    expect(ring.some((stop) => stop.inPrimaryNav)).toBe(false);
    await expect(page.locator(PRIMARY_NAV)).toBeHidden();
  });

  test("375px/ar: the same five stops, in Arabic chrome", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);

    const ring = await measureTabRing(page, 8, "ar");
    const order = ring.map(describeStop);
    report(`375px/ar tab ring = ${JSON.stringify(order)}`);

    // Same order as English, Arabic names on the first two, and the same three
    // endonyms at the end — because they are endonyms, and because mirroring
    // must not reorder a DOM ring.
    expect(order).toEqual([
      `a:${CATALOGS.ar["a11y.skipToMain"]}`,
      `button:${CATALOGS.ar["a11y.openMainNavigation"]}`,
      ...LOCALE_ENDONYMS.map((endonym) => `a:${endonym}`),
    ]);
    expect(ring.some((stop) => stop.inPrimaryNav)).toBe(false);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  });

  test("1440px: the mobile disclosure is display:none, so the ring is [skip, Overview, Screening, three locales]", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);

    const ring = await measureTabRing(page, 8, "en");
    const order = ring.map(describeStop);
    report(`1440px/en tab ring = ${JSON.stringify(order)}`);

    // Two of the four nav entries are links since packet UI-04 routed the
    // screening surface; `Evidence` and `Audit` are still deliberately
    // non-interactive "not yet available" spans, so the next stop after
    // `Screening` is the selector's first language link. The mobile disclosure
    // is `display: none` at this width and therefore absent from the ring
    // entirely.
    expect(order).toEqual([
      `a:${CATALOGS.en["a11y.skipToMain"]}`,
      `a:${CATALOGS.en["nav.overview"]}`,
      `a:${CATALOGS.en["nav.screening"]}`,
      ...LOCALE_ENDONYMS.map((endonym) => `a:${endonym}`),
    ]);
    expect(ring.some((stop) => stop.inMobileDisclosure)).toBe(false);
    await expect(page.locator(MOBILE_NAV_TRIGGER)).toBeHidden();
  });

  test("1440px/ar: Arabic chrome with Latin endonyms, and the same order", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);

    const ring = await measureTabRing(page, 8, "ar");
    const order = ring.map(describeStop);
    report(`1440px/ar tab ring = ${JSON.stringify(order)}`);

    expect(order).toEqual([
      `a:${CATALOGS.ar["a11y.skipToMain"]}`,
      `a:${CATALOGS.ar["nav.overview"]}`,
      `a:${CATALOGS.ar["nav.screening"]}`,
      ...LOCALE_ENDONYMS.map((endonym) => `a:${endonym}`),
    ]);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  });
});

test.describe("rendered tab order — the screening workspace", () => {
  // Two stops live in the form rather than the header: the radio group is ONE
  // stop (Chromium enters the group at the first radio when nothing is checked
  // and Tab leaves it again — arrows move within the group), and the disabled
  // submit is not a stop at all, because `disabled` removes an element from the
  // focus order. That is asserted rather than assumed: `presses` runs past the
  // expected list, so a submit button that became focusable would show up as an
  // extra stop and fail the equality instead of hiding past the press limit.
  const RADIO = "input:screening-decision-include";
  const REASON = "textarea:screening-reason";

  test("1440px/en: [skip, Overview, Screening, three locales, include radio, reason field]", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);

    const ring = await measureTabRing(page, 10, "en", "/screening");
    const order = ring.map((stop) => (stop.focusId === "" ? describeStop(stop) : `${stop.tag}:${stop.focusId}`));
    report(`1440px/en/screening tab ring = ${JSON.stringify(ring.map(describeStop))}`);

    expect(order).toEqual([
      `a:${CATALOGS.en["a11y.skipToMain"]}`,
      `a:${CATALOGS.en["nav.overview"]}`,
      `a:${CATALOGS.en["nav.screening"]}`,
      ...LOCALE_ENDONYMS.map((endonym) => `a:${endonym}`),
      RADIO,
      REASON,
    ]);
    await expect(page.locator(PRIMARY_NAV)).toBeVisible();
  });

  test("375px/ar: the narrow ring drops the primary nav, in RTL chrome", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);

    const ring = await measureTabRing(page, 10, "ar", "/screening");
    const order = ring.map((stop) => (stop.focusId === "" ? describeStop(stop) : `${stop.tag}:${stop.focusId}`));
    report(`375px/ar/screening tab ring = ${JSON.stringify(ring.map(describeStop))}`);

    expect(order).toEqual([
      `a:${CATALOGS.ar["a11y.skipToMain"]}`,
      `button:${CATALOGS.ar["a11y.openMainNavigation"]}`,
      ...LOCALE_ENDONYMS.map((endonym) => `a:${endonym}`),
      RADIO,
      REASON,
    ]);
    expect(ring.some((stop) => stop.inPrimaryNav)).toBe(false);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  });
});