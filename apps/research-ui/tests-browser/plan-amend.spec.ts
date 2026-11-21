import { createRequire } from "node:module";
import { join } from "node:path";

import type { Page } from "@playwright/test";

import { discoveryEngine, type DiscoveryFakeOptions } from "../tests/fixtures/discovery-engine";
import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * "Change the search" on Plan (M11a part D; spec
 * `docs/ux/phase1-discovery/final/10-plan-amend-search.md`, Playwright) against the
 * stateful discovery fake. Runs in the light and the dark project.
 * `M11A_SHOTS=<folder>` also writes the screenshots looked at for the build record.
 */

async function engine(page: Page, options: DiscoveryFakeOptions = {}) {
  const fake = discoveryEngine(options);
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console", "") + url.search;
    const raw = route.request().postData();
    const answer = fake.handle(route.request().method(), path, raw ? (JSON.parse(raw) as Record<string, unknown>) : null);
    if (typeof answer.body === "string") await route.fulfill({ status: answer.status, contentType: "text/markdown", body: answer.body });
    else await route.fulfill({ status: answer.status, json: answer.body });
  });
  return fake;
}

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");
async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
    const raw = await run.run(document);
    return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
  });
}

const OPTIONS: DiscoveryFakeOptions = { protocolProviders: ["openalex", "semanticscholar", "arxiv"], staged: true };

/** Open the section, count, merge the two concepts, and open the confirmation with a reason. */
async function confirm(page: Page) {
  await page.locator("[data-plan-search-open]").click();
  await page.locator("[data-workbench] [data-count]").click();
  await expect(page.locator("[data-row='openalex'] [data-cell='query']")).toBeVisible();
  await page.locator("[data-select='0']").check();
  await page.locator("[data-select='1']").check();
  await page.locator("[data-merge]").click();
  await page.locator("[data-merge-do]").click();
  await page.locator("[data-record-open]").click();
  await expect(page.locator("[data-consequences]")).toBeVisible();
  await page.locator("#plan-search-reason").fill("Edge devices and weed detection are one idea in this review.");
}

test.use({ viewport: DESKTOP_VIEWPORT });

test("change the search on Plan: count, merge, read what it changes, record with a reason, and see Plan read again", async ({ page }) => {
  const fake = await engine(page, OPTIONS);
  await page.goto("/en/discovery/plan/");
  await confirm(page);
  await expect(page.locator("[data-conseq='export']")).toContainText("Scopus, 120 records");
  await page.locator("[data-record]").click();
  await expect(page.locator("[data-amended]")).toContainText("Amendment recorded.");
  expect(fake.amendments).toHaveLength(1);
  await expect(page.locator("[data-plan-strings]")).toContainText("sha256:01");
});

test("keyboard: Enter in the reason never records, Escape returns to Record, Ctrl+Enter reopens, the button records and focus goes to the h1", async ({ page }) => {
  const fake = await engine(page, OPTIONS);
  const amendPosts: boolean[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/workbench/amend")) amendPosts.push(!!(JSON.parse(request.postData() ?? "{}") as { dry_run?: boolean }).dry_run);
  });
  await page.goto("/en/discovery/plan/");
  await confirm(page);
  const reason = page.locator("#plan-search-reason");
  await expect(reason).toBeFocused();
  // A real browser submits a form on Enter: here the field is not in one, so nothing is recorded.
  await reason.press("Enter");
  await page.waitForTimeout(300);
  expect(amendPosts.filter((dry) => !dry)).toHaveLength(0);
  await reason.press("Escape");
  await expect(page.locator("[data-amend-confirm]")).toHaveCount(0);
  await expect(page.locator("[data-record-open]")).toBeFocused();
  await page.getByLabel("Concept 1").press("Control+Enter");
  await expect(page.locator("[data-amend-confirm]")).toBeVisible();
  await expect(reason).toBeFocused();
  await reason.fill("Edge devices and weed detection are one idea in this review.");
  await page.keyboard.press("Tab"); // the consequences are text: Cancel, then Record
  await expect(page.locator("[data-record-cancel]")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.locator("[data-record]")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("[data-amended]")).toContainText("Amendment recorded.");
  await expect(page.locator("h1")).toBeFocused();
  expect(fake.amendments).toHaveLength(1);
});

test("the #change-search anchor opens the section; closing clears it, so the next link to it opens the section again", async ({ page }) => {
  await engine(page, OPTIONS);
  await page.goto("/en/discovery/plan/#change-search");
  await expect(page.locator("[data-workbench]")).toBeVisible();
  await page.locator("[data-plan-search-close]").click();
  await expect(page.locator("[data-workbench]")).toHaveCount(0);
  await expect(page.locator("[data-plan-search-open]")).toBeFocused();
  expect(new URL(page.url()).hash).toBe("");
  await page.evaluate(() => {
    window.location.hash = "change-search";
  });
  await expect(page.locator("[data-workbench]")).toBeVisible();
});

test("after the corpus is accepted, the section counts but records nothing", async ({ page }) => {
  await engine(page, { ...OPTIONS, accepted: true });
  await page.goto("/en/discovery/plan/");
  await page.locator("[data-plan-search-open]").click();
  await expect(page.locator("[data-plan-search-accepted]")).toBeVisible();
  await expect(page.locator("[data-record-open]")).toHaveCount(0);
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: the open confirmation passes axe with contrast and never scrolls sideways`, async ({ page }, info) => {
    await engine(page, OPTIONS);
    await page.goto(`/${locale}/discovery/plan/`);
    await confirm(page);
    await expect(page.locator("html")).toHaveAttribute("dir", locale === "ar" ? "rtl" : "ltr");
    await page.waitForLoadState("networkidle");
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
    const shots = process.env.M11A_SHOTS;
    if (shots) {
      // The section is taller than the window: an element shot is stitched while scrolling, and the
      // sticky site header would land across it. For the picture only (after the checks above).
      await page.addStyleTag({ content: "body > * header.sticky { position: static !important; }" });
      await page.locator("[data-plan-search]").screenshot({ path: join(shots, `plan-amend-${locale}-${info.project.name}.png`) });
    }
    for (const width of [1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      expectNoSidewaysScroll(await measureOverflow(page), `${locale} ${width}px`);
    }
    await page.setViewportSize(MOBILE_VIEWPORT);
    expectNoSidewaysScroll(await measureOverflow(page), `${locale} 375px`);
  });
}
