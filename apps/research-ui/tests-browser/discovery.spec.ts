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

// M10a (decided 2026-11-14, item 2a): the database choice per harvest, from Plan to the run.
const tickedRows = (page: Page) => page.locator('[data-harvest-picker] [data-picker-row][data-selected="true"]');

test("a choice made on Plan reaches Harvest in the address; the run asks the chosen databases in the chosen order", async ({ page }) => {
  const fake = await engine(page);
  await page.goto("/en/discovery/plan/");
  await expect(page.getByRole("heading", { name: "This is what each database will receive" })).toBeVisible();
  for (const name of ["Semantic Scholar", "arXiv", "PubMed"]) await page.getByRole("checkbox", { name: `Search ${name}` }).uncheck();
  await page.getByRole("button", { name: "Move Crossref up" }).click();
  await expect(page.locator("[data-picker-differs]")).toContainText("left out Semantic Scholar, arXiv, PubMed; moved Crossref, OpenAlex");
  const next = page.getByRole("link", { name: "Continue to Harvest with this choice" });
  await expect(next).toHaveAttribute("href", "/en/discovery/harvest/?databases=crossref,openalex");
  await expect(page.getByRole("link", { name: "Continue to Recall" })).toHaveAttribute("href", "/en/discovery/recall/");
  await next.click();

  await expect(page.getByRole("heading", { name: "Search the databases your protocol selects" })).toBeVisible();
  // The router may re-encode the comma (`%2C`); the parameter the page reads is the same.
  expect(new URL(page.url()).searchParams.get("databases")).toBe("crossref,openalex");
  await expect(tickedRows(page)).toHaveCount(2);
  expect(await tickedRows(page).evaluateAll((rows) => rows.map((r) => (r as HTMLElement).dataset.pickerRow))).toEqual(["crossref", "openalex"]);
  await page.getByRole("checkbox", { name: "Search OpenAlex" }).uncheck();
  await page.getByRole("checkbox", { name: "Search arXiv" }).check();
  await page.getByRole("button", { name: "Start the harvest" }).click();
  await expect(page.getByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." })).toBeVisible();

  const post = fake.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/runs");
  expect(post?.body).toEqual({ providers: ["crossref", "arxiv"] });
  expect(await page.locator("[data-asked]").evaluateAll((items) => items.map((i) => (i as HTMLElement).dataset.asked))).toEqual(["crossref", "arxiv"]);
  expect(await page.locator("[data-leg]").evaluateAll((rows) => rows.map((r) => (r as HTMLElement).dataset.leg))).toEqual(["crossref", "arxiv"]);
  await expect(page.locator('[data-not-asked="openalex"]')).toHaveText("OpenAlex · Not selected for this harvest.");
  await expect(page.locator('[data-leg="crossref"] [data-leg-query]')).toHaveText("weed detection weed segmentation edge device embedded");
  await page.goto("/en/discovery/report/");
  await expect(page.locator("[data-not-searched]")).toContainText("OpenAlex · Not selected for this harvest.");
});

test("ar/discovery/harvest: the picker is right to left, moves by keyboard, keeps focus and never mirrors its icons", async ({ page }) => {
  const fake = await engine(page);
  await page.goto("/ar/discovery/harvest/?databases=crossref,openalex");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(tickedRows(page)).toHaveCount(2);
  const down = page.getByRole("button", { name: "انقل Crossref إلى الأسفل" });
  await down.focus();
  await page.keyboard.press("Space");
  expect(await tickedRows(page).evaluateAll((rows) => rows.map((r) => (r as HTMLElement).dataset.pickerRow))).toEqual(["openalex", "crossref"]);
  // Crossref reached the end: its Move down is disabled, so focus moved to its Move up.
  await expect(page.getByRole("button", { name: "انقل Crossref إلى الأعلى" })).toBeFocused();
  await expect(page.locator("[data-picker-status]")).toHaveText("نُقلت Crossref إلى الموضع 2 من 2");
  const transforms = await page.locator("[data-harvest-picker] svg").evaluateAll((icons) => icons.map((i) => getComputedStyle(i).transform));
  expect(transforms.every((value) => value === "none")).toBe(true);
  await page.locator("[data-start]").click();
  await expect.poll(() => fake.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/runs")?.body).toEqual({ providers: ["openalex", "crossref"] });
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

// --------------------------------------------------------------------------- M3i-harvest-robustness

test("M3i: the hand-off of an unfinished harvest says so and leads to Finish preparing; no search runs again; the accept follows", async ({ page }) => {
  // The strict run's state: a published search (records saved), no job in memory, the later steps never ended.
  const fake = await engine(page, { runs: 1, preparation: "interrupted", legacyRun: true });
  await page.goto("/en/discovery/handoff/");
  await expect(page.getByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." })).toBeVisible();
  await expect(page.getByText("There is nothing to hand off yet.")).toHaveCount(0);
  await expect(page.locator("[data-pending-body]")).toHaveText(
    "The search of run_001 finished, but its corpus was not prepared. The console may have been closed while it ran.",
  );
  await expect(page.getByRole("button", { name: "Accept this corpus" })).toHaveCount(0);

  await page.getByRole("link", { name: "Finish preparing this corpus on Harvest" }).click();
  await expect(page).toHaveURL(/\/en\/discovery\/harvest\/?\?run=run_001/);
  await expect(page.getByRole("heading", { level: 1, name: "The search finished, but the corpus was not prepared." })).toBeVisible();
  const card = page.locator('[data-preparation="interrupted"]');
  await expect(card.locator("[data-no-marker]")).toBeVisible();
  await expect(page.locator('[data-leg="openalex"]')).toBeVisible();

  await card.getByRole("button", { name: "Finish preparing this corpus" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "The harvest is finished. The corpus is not frozen yet." })).toBeVisible();
  await expect(page.locator("[data-preparation]")).toHaveCount(0);
  const posts = fake.calls.filter((c) => c.method === "POST").map((c) => c.path);
  expect(posts).toEqual(["/api/v1/discovery/runs/run_001/prepare"]);

  await page.getByRole("link", { name: "Go to the hand-off" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Accept this corpus for screening?" })).toBeVisible();
  await page.getByRole("button", { name: "Accept this corpus" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "This corpus is accepted." })).toBeVisible();
  expect(fake.accepted).toBe(true);
});

test("M3i: a harvest that fails after its search says where, and says it again after a reload", async ({ page }) => {
  await engine(page, { preparation: "failed" });
  await page.goto("/en/discovery/harvest/");
  await page.getByRole("button", { name: "Start the harvest" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "The search finished, but preparing the corpus failed." })).toBeVisible();
  await expect(page.locator('[data-refusal="DISCOVERY_FAILED"]')).toHaveCount(0);
  const card = page.locator('[data-preparation="failed"]');
  await expect(card).toHaveAttribute("data-preparation-stage", "verification");
  await expect(card.locator("[data-stage-ended]")).toHaveText(["Duplicates", "Abstracts"]);

  // A reload has no job to read: the state comes from the engine's own record of the run.
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: "The search finished, but preparing the corpus failed." })).toBeVisible();
  await expect(page.locator('[data-preparation="failed"]').getByRole("button", { name: "Finish preparing this corpus" })).toBeEnabled();
  await page.locator('[data-preparation="failed"]').getByText("Details").click();
  await expect(page.locator("[data-preparation-message]")).toHaveText("RuntimeError: verifier down");
});

test("M3i: Stop stays after the search and ends the harvest as stopped before the next step", async ({ page }) => {
  const fake = await engine(page, { holdAfterSearch: true });
  await page.goto("/en/discovery/harvest/");
  await page.getByRole("button", { name: "Start the harvest" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "The corpus is being prepared" })).toBeVisible();
  await expect(page.locator("[data-stop-late]")).toContainText("A stop now takes effect when the current step ends");
  await page.getByRole("button", { name: "Stop after the current step" }).click();
  expect(fake.calls.some((c) => c.method === "POST" && c.path.endsWith("/cancel"))).toBe(true);
  // The held stream of the fake has no live end: Retry reads the job as the engine left it.
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "You stopped the harvest before the corpus was prepared." })).toBeVisible();
  await expect(page.locator('[data-preparation="stopped"]').getByText(/You stopped before the step “Checks”/)).toBeVisible();

  await page.goto("/en/discovery/handoff/");
  await expect(page.locator("[data-pending-body]")).toHaveText("You stopped the harvest of run_001 before the step “Checks”.");
});

test("M3i: the accept on the Import step names an unfinished harvest (the engine's refusal)", async ({ page }) => {
  const fake = await engine(page, { runs: 1, preparation: "failed", refuseOnce: {} });
  const answer = fake.handle("POST", "/api/v1/screening/corpus/accept", null);
  expect(answer.status).toBe(409);
  expect((answer.body as { detail: { code: string; details: { run: string; state: string; stage: string } } }).detail).toMatchObject({
    code: "PREPARATION_UNFINISHED", details: { run: "run_001", state: "failed", stage: "verification" },
  });
  expect(fake.accepted).toBe(false);
  await page.goto("/en/discovery/handoff/");
  await expect(page.getByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." })).toBeVisible();
});

const UNFINISHED: DiscoveryFakeOptions = { runs: 1, preparation: "failed" };
const UNFINISHED_SCREENS = ["harvest/", "handoff/"] as const;

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

for (const locale of ["en", "ar"] as const) {
  for (const screen of UNFINISHED_SCREENS) {
    test(`M3i ${locale}/discovery/${screen} with an unfinished preparation: axe finds no violation, contrast included`, async ({ page }) => {
      await engine(page, UNFINISHED);
      await page.goto(`/${locale}/discovery/${screen}`);
      await expect(page.locator("h1")).toBeVisible();
      await expect(page.locator(screen === "harvest/" ? "[data-preparation]" : "[data-pending]")).toBeVisible();
      await page.waitForLoadState("networkidle");
      const result = await axe(page);
      expect(result.violations).toEqual([]);
      expect(result.passes).toContain("color-contrast");
    });
    for (const [name, viewport] of [
      ["375px", MOBILE_VIEWPORT],
      ["1440px", DESKTOP_VIEWPORT],
    ] as const) {
      test(`M3i ${locale}/discovery/${screen} ${name} with an unfinished preparation: nothing scrolls sideways`, async ({ page }) => {
        await engine(page, UNFINISHED);
        await page.setViewportSize(viewport);
        await page.goto(`/${locale}/discovery/${screen}`);
        await expect(page.locator(screen === "harvest/" ? "[data-preparation]" : "[data-pending]")).toBeVisible();
        await page.waitForLoadState("networkidle");
        expectNoSidewaysScroll(await measureOverflow(page), `${locale}/discovery/${screen} ${name} (unfinished)`);
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
