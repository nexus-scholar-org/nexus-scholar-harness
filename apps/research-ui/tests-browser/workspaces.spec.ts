import type { Page, Route } from "@playwright/test";

import { DESKTOP_VIEWPORT, MOBILE_VIEWPORT, expect, test } from "./helpers";

/**
 * The workspace screen (spec 00) in a real browser, light and dark. The console
 * is answered at the network boundary with the workspaces routes' shapes; Open
 * is a small state machine (the "engine" answers for the old folder, then for
 * the new one), so the page's restart wait is the real build reacting to it.
 */

const ROOT = "/home/r/Documents/Nexus Scholar/workspaces";
const row = (slug: string, extra: Record<string, unknown> = {}) => ({
  slug, title: slug.replace(/-/g, " "), path: `${ROOT}/${slug}`, valid: true, has_corpus: true, screening_started: false,
  last_event: { at: "2026-11-05T10:00:00+00:00", action: "GENESIS" }, is_current: false, ...extra,
});

async function engine(page: Page, plan: { busy?: boolean } = {}) {
  let opened = false;
  const items = [row("uav-review", { is_current: true, screening_started: true }), row("crop-review")];
  await page.route("**/api/console/api/v1/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace("/api/console", "");
    if (path === "/api/v1/workspaces" && request.method() === "GET") {
      return route.fulfill({ json: { root: ROOT, root_source: "default", writable: true, current: { slug: "uav-review", path: `${ROOT}/uav-review` }, busy: { run_active: false, pairing_open: false }, skipped_count: 0, items } });
    }
    if (path === "/api/v1/workspaces" && request.method() === "POST") {
      items.push(row("weed-mapping", { has_corpus: false }));
      return route.fulfill({ status: 201, json: { slug: "weed-mapping", path: `${ROOT}/weed-mapping`, protocol_fingerprint: "sha256:x" } });
    }
    if (path === "/api/v1/workspaces/open") {
      if (plan.busy) return route.fulfill({ status: 409, json: { detail: { code: "WORKSPACE_BUSY", message: "busy", details: { run_active: true, pairing_open: false } } } });
      opened = true;
      return route.fulfill({ status: 202, json: { slug: "crop-review", path: `${ROOT}/crop-review`, restarting: true } });
    }
    if (path === "/api/v1/workspace/meta") return route.fulfill({ json: { workspace: `${ROOT}/${opened ? "crop-review" : "uav-review"}` } });
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
}

test.describe("desktop", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("create shows the folder, then the accept-corpus step; no demonstration marker", async ({ page }) => {
    await engine(page);
    await page.goto("/en/workspaces");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Which review are you working on?");
    await expect(page.getByText("Demonstration data")).toHaveCount(0);
    await page.keyboard.press("n");
    const field = page.getByLabel("Title of the review");
    await expect(field).toBeFocused();
    await field.fill("Weed Mapping");
    await expect(page.locator("[data-folder]")).toContainText(`${ROOT}/weed-mapping`);
    await field.press("Enter");
    await expect(page.getByRole("heading", { name: "Workspace created" })).toBeFocused();
    await expect(page.locator("[data-next-step]")).toContainText(`nexus-scholar accept-corpus --workspace "${ROOT}/weed-mapping"`);
    await expect(page.locator('[data-row="weed-mapping"]')).toContainText("No corpus yet");
  });

  test("open waits for the restarted engine, then loads screening", async ({ page }) => {
    await engine(page);
    await page.goto("/en/workspaces");
    await page.locator('[data-row="crop-review"]').getByRole("button", { name: "Open" }).click();
    await expect(page.locator("[data-opening]")).toContainText("Opening crop review");
    // The export build keeps the trailing slash; the dev and standalone builds drop it.
    await page.waitForURL(/\/en\/screening\/?$/);
  });

  test("open refused while a run is active points to screening home", async ({ page }) => {
    await engine(page, { busy: true });
    await page.goto("/en/workspaces");
    await page.locator('[data-row="crop-review"]').getByRole("button", { name: "Open" }).click();
    await expect(page.locator('[data-state="WORKSPACE_BUSY"]')).toBeVisible();
    await expect(page.locator("[data-busy]")).toContainText("An agent run is active");
  });

  test("in Arabic the page is right-to-left and paths stay left-to-right", async ({ page }) => {
    await engine(page);
    await page.goto("/ar/workspaces");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("على أي مراجعة تعمل؟");
    await expect(page.locator('[data-row="uav-review"] bdi').first()).toHaveAttribute("dir", "ltr");
  });
});

test.describe("phone", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("a phone sees only the desktop pointer", async ({ page }) => {
    await engine(page);
    await page.goto("/en/workspaces");
    await expect(page.locator("[data-phone]")).toBeVisible();
    await expect(page.locator("[data-phone]")).toContainText("Choose the workspace on your desktop");
    await expect(page.getByRole("button", { name: "New workspace" })).toBeHidden();
  });
});
