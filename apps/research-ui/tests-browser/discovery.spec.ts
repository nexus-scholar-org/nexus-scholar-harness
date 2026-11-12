import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { discoveryEngine, refuse, type DiscoveryFakeOptions } from "../tests/fixtures/discovery-engine";
import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * The discovery screens (specs `docs/ux/phase1-discovery/final/01–08`, M3c-screens)
 * in a real browser. The console proxy is answered by the stateful fake in
 * `tests/fixtures/discovery-engine.ts`, with the engine's shapes and refusal
 * codes; job events are served as a real `text/event-stream` body. The engine
 * itself is covered by the Python suite. Runs in the light and the dark project.
 */

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

test.use({ viewport: DESKTOP_VIEWPORT });

test("a researcher goes from the plan to the hand-off accept and lands on screening Home", async ({ page }) => {
  const fake = await engine(page);
  await page.goto("/en/discovery/");
  await expect(page.getByRole("heading", { name: "Where the search stands" })).toBeVisible();
  await page.locator("nav[data-discovery-steps]").getByRole("link", { name: "1 Plan" }).click();

  await expect(page.getByRole("heading", { name: "This is what each database will receive" })).toBeVisible();
  await expect(page.locator('[data-provider="openalex"] [data-executed]')).toContainText("title_and_abstract.search");
  await expect(page.getByRole("button", { name: /Approve/ })).toHaveCount(0);
  await page.getByRole("link", { name: "Continue to Recall" }).click();

  await expect(page.getByRole("heading", { name: "No recall check yet" })).toBeVisible();
  await page.getByLabel("Identifier of seed 1").fill("10.1016/j.compag.2021.106067");
  await page.getByRole("button", { name: "Add a seed" }).click();
  await page.getByLabel("Kind of seed 2").selectOption("arxiv");
  await page.getByLabel("Identifier of seed 2").fill("2106.01234");
  await page.getByRole("button", { name: "Check these seeds" }).click();
  await expect(page.getByRole("heading", { name: "The query finds 1 of the 2 papers you gave it" })).toBeVisible();
  await expect(page.locator("[data-missed]")).toHaveCount(1);
  await page.getByRole("link", { name: "Continue to Harvest" }).click();

  await expect(page.getByRole("heading", { name: "Search the databases your protocol selects" })).toBeVisible();
  await page.getByRole("button", { name: "Start the harvest" }).click();
  await expect(page.getByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." })).toBeVisible();
  await expect(page.locator('[data-leg="crossref"] [data-count]')).toHaveText("at least 500");
  await expect(page.getByText(/ready for screening/i)).toHaveCount(0);
  expect(fake.calls.some((c) => c.path.endsWith("/events"))).toBe(true);
  await page.getByRole("link", { name: "Go to Duplicates" }).click();

  await expect(page.getByRole("heading", { name: "1453 records became 1060 works." })).toBeVisible();
  await expect(page.getByRole("button", { name: /Merge|Keep both/ })).toHaveCount(0);
  await page.getByRole("link", { name: "Continue to the report" }).click();

  await expect(page.getByRole("heading", { name: "What each database was asked and what came back." })).toBeVisible();
  await expect(page.locator('[data-ident="crossref"] [data-fetched]')).toHaveText("At least 500");
  await page.getByRole("button", { name: "I reviewed this text" }).click();
  await expect(page.locator("[data-methods]")).toHaveAttribute("data-reviewed", "true");
  await page.getByRole("link", { name: "Continue to hand-off" }).click();

  await expect(page.getByRole("heading", { name: "Accept this corpus for screening?" })).toBeVisible();
  await expect(page.locator("[data-lower-bound-note]")).toContainText("Crossref");
  await page.getByRole("button", { name: "Accept this corpus" }).click();
  await expect(page.getByRole("heading", { name: "This corpus is accepted." })).toBeVisible();
  await page.getByRole("link", { name: "Go to screening" }).click();
  await page.waitForURL(/\/en\/screening\/home\/?$/);
  expect(fake.accepted).toBe(true);
});

test("MAILTO_NOT_SET prints the line to set; Check again re-reads, then the harvest starts", async ({ page }) => {
  const fake = await engine(page, { mailto: false });
  await page.goto("/en/discovery/harvest/");
  await expect(page.locator("[data-mailto-line]").first()).toHaveText("SCHOLAR_MAILTO=<your email>");
  await page.getByRole("button", { name: "Start the harvest" }).click();
  const card = page.locator('[data-state="MAILTO_NOT_SET"]');
  await expect(card).toBeVisible();
  await expect(card).toContainText("SCHOLAR_MAILTO=<your email>");
  fake.setMailto(true);
  await card.getByRole("button", { name: "Check again" }).click();
  await expect(card).toHaveCount(0);
  await expect(page.locator("[data-mailto-line]")).toHaveCount(0);
  await page.getByRole("button", { name: "Start the harvest" }).click();
  await expect(page.getByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." })).toBeVisible();
});

test("a frozen corpus is never searched again: CORPUS_ALREADY_ACCEPTED", async ({ page }) => {
  await engine(page, { runs: 1, accepted: true });
  await page.goto("/en/discovery/harvest/");
  await expect(page.locator("[data-accepted]")).toBeVisible();
  await expect(page.getByRole("button", { name: /Start the harvest|Harvest again/ })).toHaveCount(0);
  await page.goto("/en/discovery/handoff/");
  await expect(page.getByRole("heading", { name: "This corpus is accepted." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Accept this corpus" })).toHaveCount(0);
});

test("DISCOVERY_JOB_ACTIVE is a sentence with its code under Details", async ({ page }) => {
  await engine(page, {
    refuseOnce: { "POST /api/v1/discovery/runs": refuse(409, "DISCOVERY_JOB_ACTIVE", "A discovery job is already running for this workspace.", { job: { job_id: "djob_x", kind: "recall", state: "running" } }) },
  });
  await page.goto("/en/discovery/harvest/");
  await page.getByRole("button", { name: "Start the harvest" }).click();
  const card = page.locator('[data-state="DISCOVERY_JOB_ACTIVE"]');
  await expect(card.getByRole("heading", { name: "A search is already running" })).toBeVisible();
  await card.getByText("Details").click();
  await expect(card.getByText("DISCOVERY_JOB_ACTIVE", { exact: true })).toBeVisible();
});

test("a failed database shows its typed code and a capped one is a lower bound", async ({ page }) => {
  await engine(page, { runs: 1, failedLeg: { provider: "pubmed", code: "PROVIDER_RATE_LIMITED", error: "HTTPStatusError: 429 Too Many Requests" } });
  await page.goto("/en/discovery/harvest/");
  const pubmed = page.locator('[data-leg="pubmed"]');
  await expect(pubmed).toHaveAttribute("data-leg-status", "failed");
  await expect(pubmed.locator("[data-leg-error]")).toHaveAttribute("data-leg-error", "PROVIDER_RATE_LIMITED");
  await expect(pubmed).toContainText("The database limited the request rate.");
  await expect(page.locator('[data-leg="crossref"] [data-count]')).toHaveText("at least 500");
  await page.goto("/en/discovery/report/");
  await expect(page.locator('[data-ident="pubmed"] [data-error-code]')).toHaveText("PROVIDER_RATE_LIMITED");
  await expect(page.locator('[data-ident="crossref"]')).toHaveAttribute("data-completeness", "lower_bound");
});

test("a published screening is chased, one database fails and one is capped, the accept starts round 2 and lands on Home", async ({ page }) => {
  const fake = await engine(page, { runs: 1, accepted: true, published: true, chaseCapped: true, chaseFailedLeg: { provider: "semanticscholar", direction: "backward", code: "PROVIDER_RATE_LIMITED", error: "HTTP 429" } });
  await page.goto("/en/discovery/chase/");
  await expect(page.getByRole("heading", { name: "Chase the citations of your included studies" })).toBeVisible();
  await expect(page.locator("nav[data-discovery-steps]").getByRole("link", { name: "8 Chase" })).toHaveAttribute("aria-current", "step");
  await page.getByRole("button", { name: "Chase citations" }).click();
  await expect(page.getByRole("heading", { name: "The chase is finished. These works are new." })).toBeVisible();
  await expect(page.locator('[data-summary="openalex|forward"] [data-fetched]')).toContainText("at least 500");
  await expect(page.locator('[data-summary="semanticscholar|backward"]')).toContainText("1");
  await expect(page.locator("[data-count=new]")).toBeVisible();
  await page.getByRole("button", { name: /Send these \d+ works to screening/ }).click();
  await expect(page.getByRole("heading", { name: "These works are with screening as round 2." })).toBeVisible();
  expect(fake.round).toBe(2);
  await page.getByRole("link", { name: "Go to screening" }).click();
  await page.waitForURL(/\/en\/screening\/home\/?$/);
});

test("before publication the chase screen asks for the publish screen and shows no form", async ({ page }) => {
  await engine(page, { runs: 1, accepted: true });
  await page.goto("/en/discovery/chase/");
  await expect(page.getByRole("heading", { name: "Publish the screening first." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Chase citations" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Go to the Publish screen" })).toHaveAttribute("href", /\/en\/screening\/publish/);
  await expect(page.locator("nav[data-discovery-steps]").getByRole("link", { name: "7 Hand-off" })).toBeVisible();
});

test("the hand-off refuses a run from an earlier protocol: PROTOCOL_CHANGED_SINCE_RUN", async ({ page }) => {
  const fake = await engine(page, { runs: 1, protocolChangedSinceRun: true });
  await page.goto("/en/discovery/handoff/");
  await page.getByRole("button", { name: "Accept this corpus" }).click();
  const card = page.locator('[data-state="PROTOCOL_CHANGED_SINCE_RUN"]');
  await expect(card.getByRole("heading", { name: "The protocol changed after this search" })).toBeVisible();
  await expect(card.getByRole("link", { name: "Search again" })).toHaveAttribute("href", "/en/discovery/harvest/");
  expect(fake.accepted).toBe(false);
});

const SCREENS = ["", "plan/", "recall/", "harvest/", "dedup/", "report/", "handoff/", "chase/"] as const;
const SEEDED: DiscoveryFakeOptions = { runs: 1 };

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
    test(`${locale}/discovery/${screen}: axe finds no violation, contrast included`, async ({ page }) => {
      await engine(page, SEEDED);
      await page.goto(`/${locale}/discovery/${screen}`);
      await expect(page.locator("h1")).toBeVisible();
      await page.waitForLoadState("networkidle");
      const result = await axe(page);
      expect(result.violations).toEqual([]);
      expect(result.passes).toContain("color-contrast");
    });
  }
  test(`${locale}/screening/import?return=discovery: axe finds no violation`, async ({ page }) => {
    await engine(page, SEEDED);
    await page.goto(`/${locale}/screening/import?return=discovery`);
    await expect(page.locator("h1")).toBeVisible();
    await page.waitForLoadState("networkidle");
    expect((await axe(page)).violations).toEqual([]);
  });
}

for (const locale of ["en", "ar"] as const) {
  for (const [name, viewport] of [
    ["375px", MOBILE_VIEWPORT],
    ["1440px", DESKTOP_VIEWPORT],
  ] as const) {
    for (const screen of SCREENS) {
      test(`${locale}/discovery/${screen} ${name}: nothing scrolls sideways`, async ({ page }) => {
        await engine(page, SEEDED);
        await page.setViewportSize(viewport);
        await page.goto(`/${locale}/discovery/${screen}`);
        await expect(page.locator("h1")).toBeVisible();
        await page.waitForLoadState("networkidle");
        expectNoSidewaysScroll(await measureOverflow(page), `${locale}/discovery/${screen} ${name}`);
      });
    }
  }
}

for (const screen of SCREENS) {
  test(`en/discovery/${screen}: no hydration mismatch with ?run= in the address`, async ({ page }) => {
    // The pages are prerendered without a query string; the screens read `?run=` and
    // `?console=` only after mount, so the first render matches the server's.
    const problems: string[] = [];
    page.on("console", (message) => {
      if (/hydrat|did not match|Text content does not match/i.test(message.text())) problems.push(`console.${message.type()}: ${message.text()}`);
    });
    page.on("pageerror", (error) => {
      if (/hydrat|did not match/i.test(error.message)) problems.push(`pageerror: ${error.message}`);
    });
    await engine(page, { runs: 2 });
    // Only `?run=`: a `?console=` override would send the calls past the proxy the fake answers.
    await page.goto(`/en/discovery/${screen}?run=run_001`);
    await expect(page.locator("h1")).toBeVisible();
    await page.waitForLoadState("networkidle");
    expect(problems, `en/discovery/${screen} reported a hydration mismatch`).toEqual([]);
  });
}

test("en/screening/import: no hydration mismatch with ?return=discovery in the address", async ({ page }) => {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (/hydrat|did not match/i.test(message.text())) problems.push(message.text());
  });
  await engine(page, SEEDED);
  await page.goto("/en/screening/import?return=discovery");
  await expect(page.locator("[data-back-to-discovery]")).toBeVisible();
  await expect(page.locator('[data-staging-refused="VERIFIED_EXISTS"]')).toBeVisible();
  await page.waitForLoadState("networkidle");
  expect(problems).toEqual([]);
});
