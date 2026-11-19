import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { discoveryEngine, type DiscoveryFakeOptions } from "../tests/fixtures/discovery-engine";
import { completeDraft, inceptionEngine, proofId, SESSION, type FakeOptions } from "../tests/fixtures/inception-engine";
import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * 03-guidance "Acceptance tests", Playwright (M10d): hints by mouse, touch and
 * keyboard; placement in Arabic; a warning never inside a hint; moved text in
 * the DOM while closed; Recommended never preselected; axe with a hint open and
 * the folds closed. The console proxy is answered by the inception fake, as in
 * `inception.spec.ts`. Runs in the light and the dark project.
 */

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;
const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

async function engine(page: Page, options: FakeOptions & { draft?: Record<string, unknown> } = {}) {
  const fake = inceptionEngine(options);
  if (options.draft) fake.seed(options.draft);
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console", "") + url.search;
    const raw = route.request().postData();
    const answer = fake.handle(route.request().method(), path, raw ? (JSON.parse(raw) as Record<string, unknown>) : null);
    if (answer.sse) await route.fulfill({ status: answer.status, contentType: "text/event-stream", body: String(answer.body) });
    else await route.fulfill({ status: answer.status, json: answer.body });
  });
  return fake;
}

const decided = () => completeDraft({ criteria_decisions: { [proofId()]: true } });

test.use({ viewport: DESKTOP_VIEWPORT });

test("hint opens on click, closes on Escape and returns focus to its button; its text is in the DOM while closed", async ({ page }) => {
  await engine(page, { draft: decided() });
  await page.goto(`/en/inception/scope/?draft=${SESSION}`);
  const button = page.getByRole("button", { name: "About Research topic, in one or two sentences" });
  const body = page.locator('[data-hint-body="scope.topicHelp"]');
  await expect(body).toBeAttached();
  await expect(body).toBeHidden();
  await expect(page.getByRole("textbox", { name: "Research topic, in one or two sentences" })).toHaveAccessibleDescription(/One subject\./);
  await button.click();
  await expect(body).toBeVisible();
  await expect(button).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Escape");
  await expect(body).toBeHidden();
  await expect(button).toBeFocused();
  // A click outside closes it; opening another closes the first.
  await button.click();
  await page.getByRole("button", { name: "About Languages" }).click();
  await expect(body).toBeHidden();
  await expect(page.locator('[data-hint-body="scope.languagesHelp"]')).toBeVisible();
  await page.getByRole("heading", { name: "What is the review about?" }).click();
  await expect(page.locator('[data-hint-body="scope.languagesHelp"]')).toBeHidden();
  // The target is 44 px.
  const box = await button.boundingBox();
  expect(box?.width).toBeGreaterThanOrEqual(44);
  expect(box?.height).toBeGreaterThanOrEqual(44);
});

test.describe("touch", () => {
  test.use({ hasTouch: true });
  test("hint opens and closes on a touch tap", async ({ page }) => {
    await engine(page, { draft: decided() });
    await page.goto(`/en/inception/scope/?draft=${SESSION}`);
    const button = page.getByRole("button", { name: "About Languages" });
    await button.tap();
    await expect(page.locator('[data-hint-body="scope.languagesHelp"]')).toBeVisible();
    await button.tap();
    await expect(page.locator('[data-hint-body="scope.languagesHelp"]')).toBeHidden();
  });
});

test("hint placement mirrors in Arabic: the panel opens on the physical left of its button, inside the viewport", async ({ page }) => {
  await engine(page, { draft: decided() });
  await page.goto(`/ar/inception/scope/?draft=${SESSION}`);
  const button = page.locator('[data-hint-button="scope.topicHelp"]');
  await button.click();
  const body = page.locator('[data-hint-body="scope.topicHelp"]');
  await expect(body).toBeVisible();
  await expect(body).toHaveAttribute("data-placement", "inline-end");
  const b = (await button.boundingBox())!;
  const p = (await body.boundingBox())!;
  expect(p.x + p.width).toBeLessThanOrEqual(b.x + 1);
  expect(p.x).toBeGreaterThanOrEqual(0);
  // In English the same hint opens on the physical right.
  await page.goto(`/en/inception/scope/?draft=${SESSION}`);
  await page.locator('[data-hint-button="scope.topicHelp"]').click();
  const b2 = (await page.locator('[data-hint-button="scope.topicHelp"]').boundingBox())!;
  const p2 = (await page.locator('[data-hint-body="scope.topicHelp"]').boundingBox())!;
  expect(p2.x).toBeGreaterThanOrEqual(b2.x + b2.width - 1);
});

const WARNINGS = '[role="alert"], [data-state], [data-role="blocked"], [data-role="unclear"], [data-check], [data-gate], [data-tile="size"]';

async function openEveryHint(page: Page) {
  const buttons = page.locator("[data-hint-button]");
  const n = await buttons.count();
  for (let i = 0; i < n; i++) {
    const b = buttons.nth(i);
    if (await b.isVisible()) {
      await b.click();
      await expect(b).toHaveAttribute("aria-expanded", "true");
      // Every warning on the page stays visible and outside the open hint.
      const inside = await page.locator(WARNINGS).evaluateAll((els) => els.filter((el) => el.closest("[data-hint-body]")).length);
      expect(inside).toBe(0);
    }
  }
  await page.keyboard.press("Escape");
}

test("a warning is never inside a hint: Explore with a thin pool, Review with an existing workspace", async ({ page }) => {
  const fake = await engine(page, { draft: decided(), recon: { outcomes: ["thin"] }, existing: "workspace" });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  const tile = page.locator('[data-tile="size"]');
  await expect(tile.getByText("Only 7 papers came back")).toBeVisible();
  await openEveryHint(page);
  await expect(tile.getByText("Only 7 papers came back")).toBeVisible();
  await expect(tile.getByText("Recommended · pool size check")).toBeVisible();
  // The folds are closed and name their counts; the key lines stay outside them.
  await expect(page.locator("details[data-papers]")).not.toHaveAttribute("open", "");
  await expect(page.locator("details[data-papers] summary")).toContainText("Papers · 7");
  await expect(page.locator("[data-databases-keys]")).toBeVisible();

  await page.goto(`/en/inception/review/?draft=${SESSION}`);
  await expect(page.getByRole("button", { name: "Create the workspace" })).toBeVisible();
  await openEveryHint(page);
  await expect(page.locator("section.border-brand")).toContainText("Writes the protocol");
});

test("Recommended is never preselected: Shape's leaning lens and Explore's semantic search on a thin pool", async ({ page }) => {
  const fake = await engine(page, { draft: { topic: "weed detection" }, recon: { outcomes: ["thin"] } });
  await page.goto(`/en/inception/shape/?draft=${SESSION}`);
  const lens = page.locator("label", { has: page.getByText("Recommended · word scan of your topic") });
  await expect(lens).toBeVisible();
  for (const radio of await page.getByRole("radio").all()) await expect(radio).not.toBeChecked();
  await expect(page.getByRole("button", { name: "Continue to concepts and criteria" })).toBeDisabled();
  await expect(lens.locator("[data-hint-button]")).toHaveCount(0);

  fake.seed(decided());
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await expect(page.getByText("Recommended · pool size check")).toBeVisible();
  await expect(page.getByRole("radio", { name: "Semantic" })).not.toBeChecked();
  await expect(page.getByRole("button", { name: "Search again with semantic search" })).not.toBeFocused();
});

test("hints work without a mouse: the Scope form is completed and every hint opened and closed by keyboard", async ({ page }) => {
  await engine(page, { draft: decided() });
  await page.goto(`/en/inception/scope/?draft=${SESSION}`);
  const topic = page.getByRole("textbox", { name: "Research topic, in one or two sentences" });
  await topic.focus();
  // The hint button comes right after its label in the tab order, before the field: reach it backwards.
  await page.keyboard.press("Shift+Tab");
  await expect(page.locator('[data-hint-button="scope.topicHelp"]')).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator('[data-hint-body="scope.topicHelp"]')).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator('[data-hint-body="scope.topicHelp"]')).toBeHidden();
  await page.keyboard.press("Tab");
  await expect(topic).toBeFocused();
  await page.keyboard.press("Control+A");
  await page.keyboard.type("on-device weed detection");
  for (const key of ["scope.toYearHelp", "scope.languagesHelp"]) {
    const b = page.locator(`[data-hint-button="${key}"]`);
    await b.focus();
    await page.keyboard.press(" ");
    await expect(page.locator(`[data-hint-body="${key}"]`)).toBeVisible();
    // Tab away closes it.
    await page.keyboard.press("Tab");
    await expect(page.locator(`[data-hint-body="${key}"]`)).toBeHidden();
  }
  await page.getByRole("button", { name: "Continue to Explore" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "What do the first papers say about your question?" })).toBeVisible();
});

for (const locale of ["en", "ar"] as const) {
  test(`axe on Explore with the folds closed and a hint open (${locale})`, async ({ page }) => {
    const fake = await engine(page, { draft: decided() });
    fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    await page.goto(`/${locale}/inception/explore/?draft=${SESSION}`);
    await expect(page.locator("details[data-papers]")).toBeAttached();
    await page.locator('[data-hint-button="explore.pool.refreshNote"]').click();
    await expect(page.locator('[data-hint-body="explore.pool.refreshNote"]')).toBeVisible();
    await page.addScriptTag({ path: AXE_PATH });
    const violations = await page.evaluate(async () => {
      const axe = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: Array<{ id: string; nodes: unknown[] }> }> } }).axe;
      const result = await axe.run(document);
      return result.violations.map((v) => `${v.id} (${v.nodes.length})`);
    });
    expect(violations).toEqual([]);
  });
}

async function discovery(page: Page, options: DiscoveryFakeOptions = {}) {
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

test("a warning is never inside a hint: Harvest with a capped and a failed database", async ({ page }) => {
  await discovery(page, { runs: 1, failedLeg: { provider: "pubmed", code: "PROVIDER_RATE_LIMITED", error: "HTTPStatusError: 429 Too Many Requests" } });
  await page.goto("/en/discovery/harvest/");
  const pubmed = page.locator('[data-leg="pubmed"]');
  await expect(pubmed).toContainText("The database limited the request rate.");
  await openEveryHint(page);
  await expect(pubmed).toContainText("The database limited the request rate.");
  await expect(page.locator('[data-leg="crossref"] [data-count]')).toHaveText("at least 500");
  await expect(page.locator('[data-leg="crossref"]')).toBeVisible();
});

test("hints work without a mouse: the Shape form is completed and every field hint opened and closed by keyboard", async ({ page }) => {
  await engine(page, { draft: { topic: "weed detection" } });
  await page.goto(`/en/inception/shape/?draft=${SESSION}`);
  const lens = page.getByRole("radio", { name: /Design Science/ });
  await lens.focus();
  await page.keyboard.press("Space");
  await expect(lens).toBeChecked();
  const playbook = page.getByRole("radio", { name: /DESIGN_SCIENCE/ });
  await playbook.focus();
  await page.keyboard.press("Space");
  await expect(playbook).toBeChecked();
  for (const key of ["shape.leaningNote", "shape.planned.hint", "shape.unitHelp", "shape.proofHelp", "shape.outOfScopeHelp"]) {
    const b = page.locator(`[data-hint-button="${key}"]`);
    await b.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(`[data-hint-body="${key}"]`)).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.locator(`[data-hint-body="${key}"]`)).toBeHidden();
    await expect(b).toBeFocused();
  }
  await page.getByRole("textbox", { name: "Unit of analysis", exact: true }).focus();
  await page.keyboard.type("embedded cameras");
  await page.getByRole("textbox", { name: "Proof a reviewer would accept", exact: true }).focus();
  await page.keyboard.type("mIoU and FPS");
  await page.getByRole("button", { name: "Continue to concepts and criteria" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Which concepts and criteria will screen this review?" })).toBeVisible();
});

for (const locale of ["en", "ar"] as const) {
  for (const [step, key] of [
    ["shape", "shape.leaningNote"],
    ["review", "review.reviewTitleHelp"],
  ] as const) {
    test(`axe on ${step} with a hint open and the details closed (${locale})`, async ({ page }) => {
      await engine(page, { draft: decided() });
      await page.goto(`/${locale}/inception/${step}/?draft=${SESSION}`);
      await page.locator(`[data-hint-button="${key}"]`).click();
      await expect(page.locator(`[data-hint-body="${key}"]`)).toBeVisible();
      await page.addScriptTag({ path: AXE_PATH });
      const violations = await page.evaluate(async () => {
        const axe = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: Array<{ id: string; nodes: unknown[] }> }> } }).axe;
        const result = await axe.run(document);
        return result.violations.map((v) => `${v.id} (${v.nodes.length})`);
      });
      expect(violations).toEqual([]);
    });
  }
}
