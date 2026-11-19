import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { discoveryEngine, type DiscoveryFakeOptions } from "../tests/fixtures/discovery-engine";
import { DESKTOP_VIEWPORT, MOBILE_VIEWPORT, expect, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * The next-step bar (`docs/ux/shared/final/04-next-step.md`, M10b Part C) in a real browser.
 * The console proxy is answered by the stateful discovery fake, which computes
 * `GET /api/v1/review/next-step` from its own state in the simplest way; the
 * engine's rules are pinned by `tests/console/test_next_step_api.py`.
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

async function engine(page: Page, options: DiscoveryFakeOptions = {}) {
  const fake = discoveryEngine(options);
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console", "") + url.search;
    const raw = route.request().postData();
    const answer = fake.handle(route.request().method(), path, raw ? (JSON.parse(raw) as Record<string, unknown>) : null);
    if (answer.sse) await route.fulfill({ status: answer.status, contentType: "text/event-stream", body: String(answer.body) });
    else if (typeof answer.body === "string") await route.fulfill({ status: answer.status, contentType: "text/markdown", body: answer.body });
    else await route.fulfill({ status: answer.status, json: answer.body });
  });
  return fake;
}

const bar = (page: Page) => page.getByRole("region", { name: "What comes next" });
const nextReads = (fake: ReturnType<typeof discoveryEngine>) => fake.calls.filter((c) => c.path === "/api/v1/review/next-step").length;

test.use({ viewport: DESKTOP_VIEWPORT });

test("harvest finished, verification running: the bar sits above the Hand-off's Not ready state, then names the Hand-off's own button", async ({ page }) => {
  const fake = await engine(page, { holdAfterSearch: true, preparingStage: "verification" });
  // A harvest whose search ended and was published; its job is now checking the works (no end yet).
  const started = fake.handle("POST", "/api/v1/discovery/runs", {});
  const job = (started.body as { job: { job_id: string } }).job.job_id;
  await page.goto("/en/discovery/handoff/");

  const region = bar(page);
  await expect(region).toContainText("Checking 1,060 works against the databases. The hand-off opens when this ends.");
  await expect(region.locator('[data-next-word="running"]')).toHaveText("Running");
  const heading = page.getByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." });
  await expect(heading).toBeVisible();
  const barBox = await region.boundingBox();
  const headingBox = await heading.boundingBox();
  expect(barBox!.y + barBox!.height).toBeLessThanOrEqual(headingBox!.y);
  await expect(region.getByRole("link", { name: "Follow the search" })).toHaveAttribute("href", `/en/discovery/harvest/?job=${job}`);
  await expect(region).not.toContainText("Accept");

  // The job ends and the run is prepared: the 5 s poll reads the corpus as ready.
  fake.finishHeldJob();
  await expect(region).toContainText("Your corpus is ready: 1,060 works from 1,453 records. Accept it to start screening.", { timeout: 15_000 });
  await expect(region).toContainText("Next: Review and accept the corpus. The button is on this page.");
  await expect(region.getByRole("link")).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole("button", { name: "Accept this corpus" })).toBeVisible();
  await expect(bar(page).getByRole("link")).toHaveCount(0);
});

test("interrupted: the bar offers Finish preparing this corpus, which leads to Harvest; a run that cannot be finished offers Search again only", async ({ page }) => {
  await engine(page, { runs: 1, preparation: "interrupted" });
  await page.goto("/en/discovery/handoff/");
  const region = bar(page);
  await expect(region).toContainText("The search finished, but the corpus was not prepared. The console may have been closed while it ran.");
  await expect(region.getByRole("link", { name: "Search again" })).toHaveAttribute("href", "/en/discovery/harvest/");
  await region.getByRole("link", { name: "Finish preparing this corpus" }).click();
  await expect(page).toHaveURL(/\/en\/discovery\/harvest\/?\?run=run_001/);
  await expect(page.locator('[data-preparation="interrupted"]').getByRole("button", { name: "Finish preparing this corpus" })).toBeVisible();

  const other = await page.context().newPage();
  await engine(other, { runs: 1, preparation: "interrupted", recordsMissing: true });
  await other.goto("/en/discovery/handoff/");
  const second = bar(other);
  await expect(second.getByRole("link", { name: "Search again" })).toBeVisible();
  await expect(second.getByRole("link", { name: "Finish preparing this corpus" })).toHaveCount(0);
  await expect(second.locator("[data-next-detail-cannot-finish]")).toHaveCount(1);
  await other.close();
});

test("a path through the review: each answer of the engine, refreshed after the page's own writes", async ({ page }) => {
  const fake = await engine(page, { protocol: "missing" });
  await page.goto("/en/discovery/plan/");
  await expect(bar(page)).toContainText("This review has no protocol yet.");
  await expect(bar(page).getByRole("link", { name: "Go to inception" })).toHaveAttribute("href", "/en/inception/");

  fake.setProtocol("ok");
  await page.reload();
  await expect(bar(page)).toContainText("Your protocol is ready. Run the search.");
  await bar(page).getByRole("link", { name: "Go to Harvest" }).click();
  await expect(page).toHaveURL(/\/en\/discovery\/harvest\/?$/);
  await expect(bar(page)).toContainText("Next: Go to Harvest. The button is on this page.");

  // The run ends on the page's job stream; the bar re-reads on its events, with no reload.
  await page.getByRole("button", { name: "Start the harvest" }).click();
  await expect(page.getByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." })).toBeVisible();
  await expect(bar(page)).toContainText("Your corpus is ready: 1,060 works from 1,453 records.");
  await bar(page).getByRole("link", { name: "Review and accept the corpus" }).click();

  await expect(page.getByRole("heading", { level: 1, name: "Accept this corpus for screening?" })).toBeVisible();
  await expect(bar(page)).toContainText("Next: Review and accept the corpus. The button is on this page.");
  await page.getByRole("button", { name: "Accept this corpus" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "This corpus is accepted." })).toBeVisible();
  await expect(bar(page)).toContainText("The corpus is accepted. Prepare the screening batches.");
  await expect(bar(page).getByRole("link", { name: "Go to screening" })).toHaveAttribute("href", "/en/screening/home");

  fake.setPublished(true);
  await page.goto("/en/discovery/chase/");
  await expect(bar(page)).toContainText("Screening is published. You can chase the citations of your included studies.");
  await expect(bar(page)).toContainText("Next: Go to Chase. The button is on this page.");
  expect(nextReads(fake)).toBeGreaterThanOrEqual(6);
});

test("the bar is not on /workspaces or on triage, and reads nothing there", async ({ page }) => {
  const fake = await engine(page, { runs: 1 });
  await page.goto("/en/workspaces");
  await page.waitForLoadState("networkidle");
  await expect(page.locator("main")).toBeVisible();
  await expect(page.locator("[data-next-step]")).toHaveCount(0);
  await page.goto("/en/screening/triage");
  await page.waitForLoadState("networkidle");
  await expect(page.locator("[data-next-step]")).toHaveCount(0);
  expect(nextReads(fake)).toBe(0);
});

test("Arabic: the bar mirrors, ids and counts stay left to right, the arrow mirrors", async ({ page }) => {
  await engine(page, { runs: 1, preparation: "failed" });
  await page.goto("/ar/discovery/handoff/");
  const region = page.getByRole("region", { name: "ما التالي" });
  await expect(region.getByRole("link", { name: "أكمل تحضير هذه المجموعة" })).toBeVisible();
  expect(await region.evaluate((el) => getComputedStyle(el).direction)).toBe("rtl");
  await region.locator("[data-next-details] summary").click();
  expect(await region.locator("[data-next-detail-run] bdi").evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
  // Tailwind 4 mirrors with the `scale` property; an older build would use `transform`.
  const mirror = await region.locator("[data-next-action] svg").evaluate((el) => ({ scale: getComputedStyle(el).scale, transform: getComputedStyle(el).transform }));
  expect(mirror.scale.startsWith("-1") || mirror.transform.startsWith("matrix(-1"), JSON.stringify(mirror)).toBe(true);
});

async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
    const raw = await run.run(document);
    return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
  });
}

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: axe finds no violation with the bar in a waiting state and its Details open, contrast included`, async ({ page }) => {
    await engine(page, { runs: 1, preparation: "failed" });
    await page.goto(`/${locale}/discovery/handoff/`);
    await expect(page.locator('[data-next-step="ready"]')).toBeVisible();
    await page.locator("[data-next-details] summary").click();
    await page.waitForLoadState("networkidle");
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
  });
}

for (const viewport of [MOBILE_VIEWPORT, DESKTOP_VIEWPORT]) {
  test(`no horizontal overflow at ${viewport.width} px with the bar's longest state`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await engine(page, { runs: 1, preparation: "failed" });
    await page.goto("/fr/discovery/handoff/");
    await expect(page.locator('[data-next-step="ready"]')).toBeVisible();
    await page.locator("[data-next-details] summary").click();
    expectNoSidewaysScroll(await measureOverflow(page), `fr ${viewport.width}`);
  });
}
