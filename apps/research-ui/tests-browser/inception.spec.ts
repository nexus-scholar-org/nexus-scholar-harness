import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { completeDraft, inceptionEngine, proofId, SESSION, type FakeOptions } from "../tests/fixtures/inception-engine";
import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * The inception screens (specs 01–08, M4b; Explore and Direction, M4d) in a real
 * browser. The console proxy is answered by the stateful fake in
 * `tests/fixtures/inception-engine.ts` (recon routes in `recon-engine.ts`, job
 * events as a real `text/event-stream` body), with the engine's shapes and
 * refusal codes; the engine itself is covered by the Python suite. Nothing
 * leaves the machine. Runs in the light and the dark project (playwright.config.ts).
 */

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

test("a researcher creates a workspace from the browser and lands on screening Home", async ({ page }) => {
  const fake = await engine(page);
  await page.goto("/en/inception/");
  await page.getByRole("button", { name: "Start a new review" }).click();

  await expect(page.getByRole("heading", { name: "What is the review about?" })).toBeVisible();
  await expect(page.getByRole("link", { name: "2 Explore" })).toBeVisible();
  await page.getByLabel("Research topic, in one or two sentences").fill("on-device weed detection");
  await page.getByRole("button", { name: "Continue to Explore" }).click();

  // Explore (M4d): the first search, its databases, the pool.
  await page.getByRole("button", { name: "Search the literature" }).click();
  await expect(page.getByRole("heading", { name: "Pool · 14 papers" })).toBeVisible();
  await expect(page.locator("[data-databases] [data-leg]")).toHaveCount(4);
  const doi = page.locator("[data-papers] a[data-doi]").first();
  await expect(doi).toHaveAttribute("target", "_blank");
  await expect(doi).toHaveAttribute("rel", "noopener noreferrer");
  await page.getByRole("button", { name: "See 3 directions" }).click();

  // Direction (M4d): nothing chosen for you; choose, bind, go on.
  await expect(page.getByRole("heading", { name: "Which direction should this review pursue?" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Pursue a direction" })).toBeDisabled();
  await page.getByRole("radio", { name: "weed detection" }).check();
  await page.getByRole("button", { name: "Pursue weed detection" }).click();
  await expect(page.getByRole("heading", { name: "Your direction: weed detection" })).toBeFocused();
  await page.getByRole("button", { name: "Continue to Shape" }).click();

  await page.getByRole("radio", { name: /Design Science/ }).check();
  await page.getByRole("radio", { name: /DESIGN_SCIENCE/ }).check();
  await page.getByLabel("Unit of analysis").fill("embedded cameras");
  await page.getByLabel("Proof a reviewer would accept").fill("mIoU and FPS on a public benchmark");
  await page.getByLabel("Out of scope").fill("closed-source models");
  await page.getByRole("button", { name: "Use this draft as RQ1" }).click();
  await page.getByRole("button", { name: "Continue to concepts and criteria" }).click();

  await page.getByRole("button", { name: "Add weed" }).click();
  const proof = page.locator("[data-criterion]", { hasText: "Reports the gold-standard proof" });
  await expect(proof).toHaveAttribute("data-status", "undecided");
  await proof.getByRole("button", { name: "Accept" }).click();
  await expect(proof).toHaveAttribute("data-status", "accepted");
  await page.getByRole("button", { name: "Continue to review" }).click();

  await page.getByLabel("Title of the review").fill("Weed review");
  await page.getByLabel("Lead researcher").fill("Dr. R");
  await page.getByRole("button", { name: "Check the protocol" }).click();
  await expect(page.locator("[data-fingerprint]")).toContainText("sha256:");
  await page.getByRole("button", { name: "Create the workspace" }).click();

  await expect(page.getByRole("heading", { name: "The workspace is created" })).toBeVisible();
  await page.getByRole("button", { name: "Open the workspace" }).click();
  await page.waitForURL(/\/en\/screening\/home\/?$/);
  expect(fake.calls.find((c) => c.path === "/api/v1/workspaces/open")?.body).toEqual({ slug: "weed-review" });
});

test("replacing a workspace with screening needs the typed name, and a wrong one is a sentence", async ({ page }) => {
  await engine(page, { draft: decided(), existing: "bound" });
  await page.goto(`/en/inception/review/?draft=${SESSION}`);
  await expect(page.getByText("4 decision events and 0 batch decision files exist in this folder")).toBeVisible();
  await page.getByRole("button", { name: "Create the workspace" }).click();
  await page.getByRole("button", { name: "Replace and back up" }).click();
  await expect(page.getByRole("heading", { name: "Screening was done under the current protocol" })).toBeFocused();
  const field = page.getByLabel(/To replace it anyway/);
  await field.fill("wrong");
  await field.press("Enter");
  await expect(page.getByRole("heading", { name: "The name does not match" })).toBeVisible();
  await field.fill("on-device-weed-detection");
  await page.getByRole("button", { name: "Replace, and discard the screening link" }).click();
  await expect(page.getByRole("heading", { name: "The protocol is replaced" })).toBeVisible();
  await expect(page.locator("[data-backup]")).toContainText("audit");
});

const SCREENS = ["", "scope/", "explore/", "direction/", "shape/", "criteria/", "review/", "done/"] as const;

/** Explore and Direction are drawn with a pool, and Direction with a bound choice, so the checks see their full screen. */
function withPool(fake: Awaited<ReturnType<typeof engine>>, screen: string) {
  if (screen !== "explore/" && screen !== "direction/") return;
  fake.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
  if (screen === "direction/") {
    const record = fake.drafts.get(SESSION)!;
    fake.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/bind`, { direction: "weed detection", accept_thin_pool: false, base_updated_at: record.updated_at });
  }
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

for (const locale of ["en", "ar"] as const) {
  for (const screen of SCREENS) {
    test(`${locale}/inception/${screen}: axe finds no violation, contrast included`, async ({ page }) => {
      const emitted = screen === "done/";
      const fake = await engine(page, { draft: emitted ? undefined : decided() });
      if (emitted) fake.seed(decided(), { slug: "on-device-weed-detection", path: "C:\\w\\on-device-weed-detection", protocol_fingerprint: "sha256:" + "ab".repeat(32), replaced: false });
      withPool(fake, screen);
      await page.goto(`/${locale}/inception/${screen}${screen ? `?draft=${SESSION}` : ""}`);
      await expect(page.locator("h1")).toBeVisible();
      await page.waitForLoadState("networkidle");
      const result = await axe(page);
      expect(result.violations).toEqual([]);
      expect(result.passes).toContain("color-contrast");
    });
  }
}

for (const locale of ["en", "ar"] as const) {
  for (const [name, viewport] of [
    ["375px", MOBILE_VIEWPORT],
    ["1440px", DESKTOP_VIEWPORT],
  ] as const) {
    for (const screen of SCREENS) {
      test(`${locale}/inception/${screen} ${name}: nothing scrolls sideways`, async ({ page }) => {
        const emitted = screen === "done/";
        const fake = await engine(page, { draft: emitted ? undefined : decided() });
        if (emitted) fake.seed(decided(), { slug: "on-device-weed-detection", path: "C:\\Users\\r\\Documents\\Nexus Scholar\\workspaces\\on-device-weed-detection", protocol_fingerprint: "sha256:" + "ab".repeat(32), replaced: false });
        withPool(fake, screen);
        await page.setViewportSize(viewport);
        await page.goto(`/${locale}/inception/${screen}${screen ? `?draft=${SESSION}` : ""}`);
        await expect(page.locator("h1")).toBeVisible();
        await page.waitForLoadState("networkidle");
        expectNoSidewaysScroll(await measureOverflow(page), `${locale}/inception/${screen} ${name}`);
      });
    }
  }
}

for (const screen of SCREENS) {
  test(`en/inception/${screen}: no hydration mismatch with ?draft= in the address`, async ({ page }) => {
    // The pages are prerendered without a query string; the step bar hrefs used
    // to read `?draft=` during the first render, so React saw hrefs the server
    // never sent and logged a mismatch on every screen (M4b follow-up).
    const problems: string[] = [];
    page.on("console", (message) => {
      if (/hydrat|did not match|Text content does not match/i.test(message.text())) problems.push(`console.${message.type()}: ${message.text()}`);
    });
    page.on("pageerror", (error) => {
      if (/hydrat|did not match/i.test(error.message)) problems.push(`pageerror: ${error.message}`);
    });
    const emitted = screen === "done/";
    const fake = await engine(page, { draft: emitted ? undefined : decided() });
    if (emitted) fake.seed(decided(), { slug: "on-device-weed-detection", path: "C:\w\on-device-weed-detection", protocol_fingerprint: "sha256:" + "ab".repeat(32), replaced: false });
    withPool(fake, screen);
    // Only `?draft=`: a `?console=` override would send the calls past the proxy the fake answers.
    await page.goto(`/en/inception/${screen}${screen ? `?draft=${SESSION}` : ""}`);
    await expect(page.locator("h1")).toBeVisible();
    await page.waitForLoadState("networkidle");
    expect(problems, `en/inception/${screen} reported a hydration mismatch`).toEqual([]);
  });
}

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;

test("a failed search names each database, and the next search brings the pool (M4d)", async ({ page }) => {
  await engine(page, { draft: decided(), recon: { outcomes: ["failed", "ok"] } });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await page.getByRole("button", { name: "Search the literature" }).click();
  await expect(page.getByRole("heading", { name: "Every database failed to answer" })).toBeVisible();
  await expect(page.locator("[data-job-error='PROVIDERS_FAILED'] [data-leg-status='failed']")).toHaveCount(4);
  await page.getByRole("button", { name: "Search the literature" }).click();
  await expect(page.getByRole("heading", { name: "Pool · 14 papers" })).toBeVisible();
});

test("a page opened during a running search re-attaches to it (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided(), recon: { holdStream: true } });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await expect(page.getByRole("heading", { name: "Pool · 14 papers" })).toBeVisible();
  expect(fake.calls.some((c) => /\/recon\/jobs\/rjob_\d+\/events$/.test(c.path))).toBe(true);
});

test("seeds ticked on Direction survive a reload, a refresh warns and makes the choice stale, binding again clears it (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided() });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/direction/?draft=${SESSION}`);
  await page.getByRole("radio", { name: "weed segmentation" }).check();
  await page.getByRole("button", { name: "Pursue weed segmentation" }).click();
  await expect(page.getByRole("heading", { name: "Papers to check discovery against" })).toBeVisible();
  const boxes = page.locator("[data-seeds] input[type=checkbox]");
  await boxes.nth(0).check();
  await boxes.nth(1).check();
  await page.getByRole("button", { name: "Save seeds" }).click();
  await expect(page.getByText("Seeds saved")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Your direction: weed segmentation" })).toBeVisible();
  await expect(page.getByText("2 of 25 ticked")).toBeVisible();

  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await page.getByRole("button", { name: "Refresh pool" }).click();
  const dialog = page.getByRole("alertdialog");
  await expect(dialog.getByRole("button", { name: "Keep the current pool" })).toBeFocused();
  await dialog.getByRole("button", { name: "Search again" }).click();
  await expect(page.getByText("The direction you chose was based on an earlier pool, or on a scope you have since changed.")).toBeVisible();
  await page.getByRole("link", { name: "Choose a direction" }).click();
  await expect(page.getByRole("heading", { name: /The direction you chose was based on an earlier pool/ })).toBeVisible();
  await expect(page.getByText("chosen on the earlier pool")).toBeVisible();
  await page.getByRole("radio", { name: "weed detection" }).check();
  await page.getByRole("button", { name: "Pursue weed detection" }).click();
  await expect(page.getByRole("heading", { name: "Your direction: weed detection" })).toBeVisible();
  await expect(page.locator("[data-stale]")).toHaveCount(0);
});

test("changing the years after binding is shown as a stale choice naming the years (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided() });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  const record = fake.drafts.get(SESSION)!;
  fake.handle("POST", `${RECON}/bind`, { direction: "weed detection", accept_thin_pool: false, base_updated_at: record.updated_at });
  await page.goto(`/en/inception/scope/?draft=${SESSION}`);
  await page.getByLabel("To year").fill("2025");
  await page.getByRole("button", { name: "Continue to Explore" }).click();
  await expect(page.locator("[data-scope-changed]")).toContainText("years");
  await page.goto(`/en/inception/direction/?draft=${SESSION}`);
  await expect(page.getByText("Changed: years")).toBeVisible();
});

test("your own phrase under two papers is checked and recorded as not grounded; a thin pool needs the box (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided(), recon: { outcomes: ["thin"] } });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/direction/?draft=${SESSION}`);
  await page.getByRole("button", { name: "Write my own direction" }).click();
  await page.getByLabel("Your direction").fill("quantum sensing");
  await page.getByRole("button", { name: "Check my phrase" }).click();
  await expect(page.getByText(/This phrase occurs in 0 of 7 titles or abstracts. A grounded direction needs two./)).toBeVisible();
  const pursue = page.getByRole("button", { name: "Pursue quantum sensing" });
  await expect(pursue).toBeDisabled();
  await page.getByRole("checkbox", { name: "I accept a pool this small" }).check();
  await pursue.click();
  await expect(page.getByText("Your direction is recorded as not grounded: it occurs in 0 of 7 titles or abstracts, and a direction needs two.")).toBeVisible();
});

test("a narrower search recomputes the directions and the first search can be brought back (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided() });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/direction/?draft=${SESSION}`);
  await page.getByRole("radio", { name: "weed segmentation" }).check();
  await page.getByRole("button", { name: "Search again, narrower · 1 left" }).click();
  await expect(page.getByText("These directions come from the narrower search on “weed segmentation”.")).toBeVisible();
  await expect(page.getByRole("radio", { name: "embedded weed detection" })).toBeVisible();
  await page.getByRole("button", { name: "Go back to the first search" }).click();
  await expect(page.getByRole("radio", { name: "weed segmentation" })).toBeVisible();
  await expect(page.locator("[data-from-narrower]")).toHaveCount(0);
});

test("going on without a direction lands on Shape, and Review says Not grounded (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided() });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/direction/?draft=${SESSION}`);
  await page.getByRole("button", { name: "Continue without a direction" }).click();
  await page.waitForURL(/\/en\/inception\/shape\/?\?draft=/);
  await page.goto(`/en/inception/review/?draft=${SESSION}`);
  await expect(page.getByText("No direction chosen · Not grounded")).toBeVisible();
});

test("Direction can be completed with the keyboard alone (M4d)", async ({ page }) => {
  const fake = await engine(page, { draft: decided() });
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/direction/?draft=${SESSION}`);
  await page.getByRole("radio", { name: "weed detection" }).focus();
  await page.keyboard.press("Space");
  await expect(page.getByRole("radio", { name: "weed detection" })).toBeChecked();
  await page.getByRole("button", { name: "Pursue weed detection" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Your direction: weed detection" })).toBeFocused();
});
