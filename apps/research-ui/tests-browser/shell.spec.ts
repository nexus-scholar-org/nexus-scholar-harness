import { join } from "node:path";

import {
  DESKTOP_VIEWPORT,
  MOBILE_NAV_PANEL_ID,
  MOBILE_NAV_TRIGGER,
  MOBILE_VIEWPORT,
  PRIMARY_NAV,
  SCREENSHOT_DIR,
  activeStop,
  describeStop,
  expect,
  focusStyleOf,
  report,
  test,
} from "./helpers";
import { LOCALE_METADATA } from "@/i18n";
import { CATALOGS } from "@/messages";

/**
 * The header and footer as rendered (2026-11-05): which controls each width
 * shows, the keyboard ring, visible focus, the language menu keeping the
 * path, right-to-left placement, and the theme. The committed screenshots in
 * `screenshots/` are written by the last block.
 */

const LANGUAGE_BUTTON = '[data-nav-region="locale"] button';
const THEME_GROUP = '[data-nav-region="theme"]';

test.describe("header at each width", () => {
  test("1440px shows the navigation, the language menu and the theme; hides the menu button", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en/screening/home");
    await expect(page.locator(PRIMARY_NAV)).toBeVisible();
    await expect(page.locator(LANGUAGE_BUTTON)).toBeVisible();
    await expect(page.locator(`header ${THEME_GROUP}`)).toBeVisible();
    await expect(page.locator(MOBILE_NAV_TRIGGER)).toBeHidden();
    await expect(page.locator(PRIMARY_NAV).getByRole("link", { name: CATALOGS.en["nav.screening"] })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  test("375px keeps the wordmark and one menu button; the menu dialog holds the rest", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en/workspaces");
    await expect(page.locator(PRIMARY_NAV)).toBeHidden();
    await expect(page.locator(LANGUAGE_BUTTON)).toBeHidden();
    const trigger = page.locator(MOBILE_NAV_TRIGGER);
    await expect(trigger).toBeVisible();
    const box = await trigger.boundingBox();
    expect(box?.height ?? 0, "the menu button is a 44px target").toBeGreaterThanOrEqual(44);

    await trigger.click();
    const panel = page.locator(`#${MOBILE_NAV_PANEL_ID}`);
    await expect(panel).toBeVisible();
    await expect(panel.getByRole("link", { name: CATALOGS.en["nav.workspaces"] })).toHaveAttribute("aria-current", "page");
    await expect(panel.getByRole("link", { name: "Français" })).toBeVisible();
    await expect(panel.getByRole("group", { name: CATALOGS.en["theme.selectorLabel"] })).toBeVisible();

    // Focus stays inside the open dialog; Escape closes it and returns focus.
    for (let press = 0; press < 12; press += 1) {
      await page.keyboard.press("Tab");
      const stop = await activeStop(page);
      expect(stop?.inMobileDialog, `Tab ${press + 1} left the dialog: ${describeStop(stop)}`).toBe(true);
    }
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
    await expect(trigger).toBeFocused();
  });
});

test.describe("keyboard", () => {
  test("1440px ring: skip link, wordmark, two destinations, language, three themes", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/fr/workspaces");
    await page.waitForLoadState("networkidle");
    const ring: string[] = [];
    for (let press = 0; press < 8; press += 1) {
      await page.keyboard.press("Tab");
      ring.push(describeStop(await activeStop(page)));
    }
    report(`1440/fr ring: ${JSON.stringify(ring)}`);
    const fr = CATALOGS.fr;
    expect(ring).toEqual([
      `a:${fr["a11y.skipToMain"]}`,
      `a:${fr["brand.productName"]}`,
      `a:${fr["nav.workspaces"]}`,
      `a:${fr["nav.screening"]}`,
      `button:${fr["locale.selectorLabel"]}: ${LOCALE_METADATA.fr.endonym}`,
      `button:${fr["theme.system"]}`,
      `button:${fr["theme.light"]}`,
      `button:${fr["theme.dark"]}`,
    ]);
  });

  test("every header control shows the 2px focus ring", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en/workspaces");
    await page.keyboard.press("Tab"); // a keyboard modality, so :focus-visible applies
    for (const selector of ["[data-brand-home]", `${PRIMARY_NAV} a`, LANGUAGE_BUTTON, `header ${THEME_GROUP} button`]) {
      const style = await focusStyleOf(page, selector);
      report(`${selector} focus: ${JSON.stringify(style)}`);
      expect(style.outlineStyle, selector).toBe("solid");
      expect(style.outlineWidth, selector).toBe("2px");
    }
  });
});

test.describe("language menu", () => {
  test("switches language on the same screen", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/fr/screening/triage");
    await page.locator(LANGUAGE_BUTTON).click();
    await page.getByRole("menuitem", { name: LOCALE_METADATA.ar.endonym }).click();
    await page.waitForURL(/\/ar\/screening\/triage\/?$/);
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator(PRIMARY_NAV)).toContainText(CATALOGS.ar["nav.screening"]);
  });
});

test.describe("right to left", () => {
  test("the wordmark sits on the right and the controls on the left; no icon is mirrored", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/ar/workspaces");
    const brand = await page.locator("[data-brand-home]").boundingBox();
    const language = await page.locator(LANGUAGE_BUTTON).boundingBox();
    expect(brand && language && brand.x > language.x, "wordmark right of the language menu in ar").toBe(true);
    const mirrored = await page.evaluate(() =>
      Array.from(document.querySelectorAll("header svg")).filter((svg) => {
        const transform = getComputedStyle(svg).transform;
        return transform !== "none" && transform.startsWith("matrix(-1");
      }).length,
    );
    expect(mirrored).toBe(0);
  });
});

test.describe("theme", () => {
  test("dark sets data-theme and survives a reload; system clears it", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en/workspaces");
    const group = page.locator(`header ${THEME_GROUP}`);
    await group.getByRole("button", { name: CATALOGS.en["theme.dark"] }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(group.getByRole("button", { name: CATALOGS.en["theme.dark"] })).toHaveAttribute("aria-pressed", "true");
    await group.getByRole("button", { name: CATALOGS.en["theme.system"] }).click();
    await expect(page.locator("html")).not.toHaveAttribute("data-theme", /.+/);
  });
});

test.describe("committed screenshots", () => {
  // Written once, in light; the dark project would overwrite them.
  test.skip(({ colorScheme }) => colorScheme === "dark", "screenshots are taken in light only");

  const SHOTS = [
    { file: "1440-workspaces.png", path: "/en/workspaces", viewport: DESKTOP_VIEWPORT },
    { file: "1440-screening-home.png", path: "/en/screening/home", viewport: DESKTOP_VIEWPORT },
    { file: "1440-screening-home-ar.png", path: "/ar/screening/home", viewport: DESKTOP_VIEWPORT },
    { file: "375-workspaces.png", path: "/en/workspaces", viewport: MOBILE_VIEWPORT },
  ] as const;

  for (const shot of SHOTS) {
    test(shot.file, async ({ page }) => {
      await page.setViewportSize(shot.viewport);
      await page.goto(shot.path);
      await page.waitForLoadState("networkidle");
      await page.screenshot({ path: join(SCREENSHOT_DIR, shot.file) });
    });
  }

  test("375-mobile-menu-open.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en/screening/home");
    await page.locator(MOBILE_NAV_TRIGGER).click();
    await expect(page.locator(`#${MOBILE_NAV_PANEL_ID}`)).toBeVisible();
    await page.screenshot({ path: join(SCREENSHOT_DIR, "375-mobile-menu-open.png") });
  });
});
