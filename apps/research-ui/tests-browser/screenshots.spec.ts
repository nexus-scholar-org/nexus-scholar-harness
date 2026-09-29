import { readFile, stat } from "node:fs/promises";
import { join } from "node:path";

import {
  DESKTOP_VIEWPORT,
  expect,
  MOBILE_NAV_PANEL_ID,
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
 * All five files are produced here rather than borrowed from another spec, so
 * the set does not depend on test-file execution order.
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
    await page.goto("/");
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

  test("1440-overview.png", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/");
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

  test("375-skiplink-focused.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");
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
    await page.goto("/");
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
    await page.goto("/");
    await page.getByRole("button", { name: "Open main navigation" }).click();
    await expect(page.locator(`#${MOBILE_NAV_PANEL_ID}`)).toBeVisible();
    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-mobile-nav-open.png"),
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });
    await assertRealCapture("375-mobile-nav-open.png");
  });
});
