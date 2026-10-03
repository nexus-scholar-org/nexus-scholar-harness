import { readFile, stat } from "node:fs/promises";
import { join } from "node:path";

import {
  DESKTOP_VIEWPORT,
  expect,
  MOBILE_NAV_PANEL_ID,
  MOBILE_NAV_TRIGGER,
  MOBILE_VIEWPORT,
  report,
  SCREENSHOT_DIR,
  test,
} from "./helpers";

/**
 * The committed screenshot set — the whole of it, owned by this one file.
 *
 * These are real captures of the production build, written by Chromium at a
 * fixed viewport and `deviceScaleFactor: 1` with animations and the caret
 * disabled. Nothing edits, annotates, resizes or synthesises an image. The
 * assertions are on the rendered DOM *and* on the bytes on disk, so a 0-byte
 * file or a renamed text file fails instead of passing quietly.
 *
 * All ten files are produced here rather than borrowed from another spec, so the
 * set does not depend on test-file execution order. The one overlap is
 * `375-mobile-nav-open.png`, which `responsive-nav.spec.ts` also writes from
 * inside its focus-trap test; this file remains the owner and the byte checks
 * live here. That overlap is pre-existing and is recorded rather than changed,
 * because the trap test's capture is evidence about focus containment and
 * removing it would remove that evidence.
 *
 * The `fr`/`ar` captures (packet UI-01d, §15.1) exist because a mirrored layout
 * cannot be reviewed from an English screenshot: a reversed reading order, a
 * mirrored skip-link offset or an Arabic line breaking in the wrong place are all
 * invisible in `375-overview.png`. Each one is a real capture of the same
 * document in another locale, at the widths the layout actually has to work at.
 */

const MIN_PNG_BYTES = 5_000;
const PNG_MAGIC = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];

async function assertRealCapture(name: string): Promise<number> {
  const file = join(SCREENSHOT_DIR, name);
  const { size } = await stat(file);
  const bytes = await readFile(file);
  report(`${name}: ${size} bytes, magic=${bytes.subarray(0, 8).toString("hex")}`);
  expect(size, `${name} is missing or implausibly small`).toBeGreaterThanOrEqual(MIN_PNG_BYTES);
  expect([...bytes.subarray(0, 8)], `${name} is not a PNG`).toEqual(PNG_MAGIC);
  return size;
}

test.describe("committed screenshots", () => {
  test("375-overview.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en");
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-overview.png"),
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-overview.png");
  });

  test("375-overview-fr.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/fr");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("html")).toHaveAttribute("lang", "fr");
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-overview-fr.png"),
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-overview-fr.png");
  });

  test("375-overview-ar.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/ar");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-overview-ar.png"),
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-overview-ar.png");
  });

  test("1440-overview.png", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "1440-overview.png"),
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("1440-overview.png");
  });

  test("1440-overview-ar.png", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/ar");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "1440-overview-ar.png"),
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("1440-overview-ar.png");
  });

  /*
   * The signature motif, at a size a human can actually judge.
   *
   * Packet UI-01c makes the visible path from a research claim back through
   * evidence and provenance the application's defining composition, and a
   * reviewer asked "is this deliberate rather than incidental?" cannot answer
   * that about four marginal numerals in a 1440px full-page capture. So the
   * evidence section is captured on its own: element-scoped, no new attribute on
   * the markup (it is selected by the `aria-labelledby` the section already
   * carries), so the image shows the hairline spine, the marginal ordinals and
   * the marginal node kinds at their rendered size rather than scaled down.
   */
  test("1440-evidence-trail.png", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");
    await page.waitForLoadState("networkidle");

    const trail = page.locator('section[aria-labelledby="evidence-title"]');
    await expect(trail).toBeVisible();
    await trail.screenshot({
      path: join(SCREENSHOT_DIR, "1440-evidence-trail.png"),
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("1440-evidence-trail.png");
  });

  test("375-skiplink-focused.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en");
    await page.keyboard.press("Tab");
    // The clip reveal is the thing being evidenced, so the capture must show
    // the focused state. A viewport shot, not fullPage: the skip link is
    // `position: fixed` and a stitched full-page shot would not reliably
    // contain it.
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-skiplink-focused.png"),
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-skiplink-focused.png");
  });

  test("1440-skiplink-focused.png", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");
    await page.keyboard.press("Tab");
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "1440-skiplink-focused.png"),
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("1440-skiplink-focused.png");
  });

  test("375-mobile-nav-open.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/en");
    await page.locator(MOBILE_NAV_TRIGGER).click();
    await expect(page.locator(`#${MOBILE_NAV_PANEL_ID}`)).toBeVisible();
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-mobile-nav-open.png"),
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-mobile-nav-open.png");
  });

  test("375-mobile-ar.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/ar");
    await page.locator(MOBILE_NAV_TRIGGER).click();
    await expect(page.locator(`#${MOBILE_NAV_PANEL_ID}`)).toBeVisible();
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-mobile-ar.png"),
      fullPage: true,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-mobile-ar.png");
  });
});