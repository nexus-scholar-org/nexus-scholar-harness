import { join } from "node:path";

import {
  activeStop,
  DESKTOP_VIEWPORT,
  describeStop,
  expect,
  MOBILE_NAV_PANEL_ID,
  MOBILE_VIEWPORT,
  report,
  SCREENSHOT_DIR,
  test,
} from "./helpers";

/**
 * Responsive navigation, in a real layout engine.
 *
 * `GATES.md` §3 listed "Tailwind's `lg:` breakpoint behaviour" as unverified
 * because jsdom applies no stylesheet: in the in-process tests BOTH the
 * desktop `<nav>` and the mobile disclosure are present and visible at once.
 * These tests measure the rendered truth at 375px and 1440px, then exercise
 * the disclosure's delegated focus trap.
 */

test.describe("responsive navigation", () => {
  test("375px shows the disclosure and hides the desktop <nav>", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");

    await expect(page.locator('nav[aria-label="Primary"]')).toBeHidden();
    await expect(page.getByRole("button", { name: "Open main navigation" })).toBeVisible();

    report("375px: nav[aria-label=Primary] hidden = true, trigger visible = true");
  });

  test("1440px shows the desktop <nav> and hides the disclosure", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/");

    await expect(page.locator('nav[aria-label="Primary"]')).toBeVisible();
    await expect(page.getByRole("button", { name: "Open main navigation" })).toBeHidden();

    report("1440px: nav[aria-label=Primary] visible = true, trigger visible = false");
  });

  test("375px: the open dialog traps focus, Escape closes it and restores focus", async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");

    const trigger = page.getByRole("button", { name: "Open main navigation" });

    // Open from the keyboard, not the mouse: the packet asks for keyboard
    // reachability, and a click would bypass the tab-order work above.
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    expect(describeStop(await activeStop(page))).toBe("button:Open main navigation");

    await page.keyboard.press("Enter");

    const panel = page.locator(`#${MOBILE_NAV_PANEL_ID}`);
    await expect(panel).toBeVisible();

    const onOpen = await activeStop(page);
    report(
      `dialog opened: focus target = ${onOpen?.tag}#${onOpen?.focusId || "-"}; inside role=dialog=${onOpen?.inDialogRole}; inside #${MOBILE_NAV_PANEL_ID}=${onOpen?.inMobileDialog}`,
    );
    expect(onOpen, "focus must be inside the dialog immediately after opening").not.toBeNull();
    // Headless UI roots the dialog at its own `role="dialog"` element
    // (`tabindex="-1"`), which is an *ancestor* of `DialogPanel`, and focuses
    // that on open. So the honest containment test is the dialog subtree, not
    // the panel subtree. Measured, not assumed: see `GATES.md` §3.1.
    expect(onOpen?.inDialogRole, "focus must land inside the open dialog").toBe(true);

    // Walk the ring far enough to prove it never escapes to the background.
    const insideRing: string[] = [];
    const escapes: string[] = [];
    for (let index = 0; index < 6; index += 1) {
      await page.keyboard.press("Tab");
      const stop = await activeStop(page);
      const label = describeStop(stop);
      if (stop === null || !stop.inDialogRole) {
        escapes.push(label);
      } else {
        insideRing.push(label);
      }
    }
    report(`dialog tab ring (all presses stayed inside): ${JSON.stringify(insideRing)}`);
    expect(
      escapes,
      `focus escaped the open dialog to: ${escapes.join(", ")}`,
    ).toEqual([]);

    // Record which mechanism Headless UI used, without asserting on it: the
    // trap is delegated and its internals are not the application's contract.
    // `inert` in a real browser vs `aria-hidden` in jsdom is an environment
    // difference, not a defect.
    const inertMechanism = await page.evaluate((panelId) => {
      const panel = document.getElementById(panelId);
      return {
        panelRole: panel?.getAttribute("role") ?? null,
        dialogRootId: document.querySelector('[role="dialog"]')?.id ?? null,
        dialogRootTabIndex: document.querySelector('[role="dialog"]')?.getAttribute("tabindex") ?? null,
        dialogRootContainsPanel:
          document.querySelector('[role="dialog"]')?.querySelector(`#${panelId}`) !== null,
        inertNodes: document.querySelectorAll("[inert]").length,
        ariaHiddenNodes: document.querySelectorAll('[aria-hidden="true"]').length,
      };
    }, MOBILE_NAV_PANEL_ID);
    report(`dialog mechanism: ${JSON.stringify(inertMechanism)}`);

    await page.screenshot({
      path: join(SCREENSHOT_DIR, "375-mobile-nav-open.png"),
      animations: "disabled",
      caret: "hide",
      scale: "css",
    });

    await page.keyboard.press("Escape");

    await expect(panel).toHaveCount(0);
    const restored = await activeStop(page);
    report(`after Escape: panel removed, focus returned to ${describeStop(restored)}`);
    expect(
      describeStop(restored),
      "Escape must close the dialog and return focus to the trigger",
    ).toBe("button:Open main navigation");
  });
});
