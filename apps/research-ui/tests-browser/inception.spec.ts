import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { completeDraft, inceptionEngine, proofId, SESSION, type FakeOptions } from "../tests/fixtures/inception-engine";
import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * The inception screens (specs 01–08, M4b) in a real browser. The console proxy
 * is answered by the stateful fake in `tests/fixtures/inception-engine.ts`, with
 * the engine's shapes and refusal codes; the engine itself is covered by the
 * Python suite. Runs in the light and the dark project (playwright.config.ts).
 */

async function engine(page: Page, options: FakeOptions & { draft?: Record<string, unknown> } = {}) {
  const fake = inceptionEngine(options);
  if (options.draft) fake.seed(options.draft);
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console", "");
    const raw = route.request().postData();
    const answer = fake.handle(route.request().method(), path, raw ? (JSON.parse(raw) as Record<string, unknown>) : null);
    await route.fulfill({ status: answer.status, json: answer.body });
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
  await expect(page.getByText("2 Explore · coming with recon")).toBeVisible();
  await page.getByLabel("Research topic, in one or two sentences").fill("on-device weed detection");
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
  await page.waitForURL(//en/screening/home/?$/);
  expect(fake.calls.find((c) => c.path === "/api/v1/workspaces/open")?.body).toEqual({ slug: "weed-review" });
});

test("replacing a workspace with screening needs the typed name, and a wrong one is a sentence", async ({ page }) => {
  await engine(page, { draft: decided(), existing: "bound" });
  await page.goto(`/en/inception/review/?draft=${SESSION}`);
  await expect(page.getByText("4 screening decisions exist in this folder")).toBeVisible();
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

const SCREENS = ["", "scope/", "shape/", "criteria/", "review/", "done/"] as const;

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
        await page.setViewportSize(viewport);
        await page.goto(`/${locale}/inception/${screen}${screen ? `?draft=${SESSION}` : ""}`);
        await expect(page.locator("h1")).toBeVisible();
        await page.waitForLoadState("networkidle");
        expectNoSidewaysScroll(await measureOverflow(page), `${locale}/inception/${screen} ${name}`);
      });
    }
  }
}
