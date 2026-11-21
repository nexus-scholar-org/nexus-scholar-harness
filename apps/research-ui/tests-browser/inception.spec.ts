import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { completeDraft, inceptionEngine, outOfScopeId, proofId, SESSION, type FakeOptions } from "../tests/fixtures/inception-engine";
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

const decided = () => completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } });
/** M10b Part B: a question that names UAV, so the screens draw the checks panel and a proposal card (axe, overflow, hydration). */
const assisted = () => completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true }, rqs: ["Can on-device weed detection run in real time on a UAV?"] });

test.use({ viewport: DESKTOP_VIEWPORT });

test("a researcher creates a workspace from the browser and lands on screening Home", async ({ page }) => {
  const fake = await engine(page);
  await page.goto("/en/inception/");
  await page.getByRole("button", { name: "Start a new review" }).click();

  await expect(page.getByRole("heading", { name: "What is the review about?" })).toBeVisible();
  await expect(page.getByRole("link", { name: "2 Explore" })).toBeVisible();
  await page.getByLabel("Research topic, in one or two sentences", { exact: true }).fill("on-device weed detection");
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
  await page.getByLabel("Unit of analysis", { exact: true }).fill("embedded cameras");
  await page.getByLabel("Proof a reviewer would accept", { exact: true }).fill("mIoU and FPS on a public benchmark");
  await page.getByLabel("Out of scope", { exact: true }).fill("closed-source models");
  await page.getByRole("button", { name: "Use this draft as RQ1" }).click();
  await page.getByRole("button", { name: "Continue to concepts and criteria" }).click();

  await page.getByRole("button", { name: "Add weed" }).click();
  const proof = page.locator("[data-criterion]", { hasText: "Reports the gold-standard proof" });
  await expect(proof).toHaveAttribute("data-status", "undecided");
  await proof.getByRole("button", { name: "Accept" }).click();
  await expect(proof).toHaveAttribute("data-status", "accepted");
  // H-run-small-fixes (finding 2): the out-of-scope item waits for Accept too.
  const outOfScope = page.locator("[data-criterion]", { hasText: "closed-source models" });
  await expect(outOfScope).toHaveAttribute("data-status", "undecided");
  await outOfScope.getByRole("button", { name: "Accept" }).click();
  await expect(outOfScope).toHaveAttribute("data-status", "accepted");
  await page.getByRole("button", { name: "Continue to review" }).click();

  await page.getByLabel("Title of the review", { exact: true }).fill("Weed review");
  await page.getByLabel("Lead researcher").fill("Dr. R");
  await page.getByRole("button", { name: "Check the protocol" }).click();
  await expect(page.locator("[data-fingerprint]")).toContainText("sha256:");
  await page.getByRole("button", { name: "Create the workspace" }).click();

  await expect(page.getByRole("heading", { name: "The workspace is created" })).toBeVisible();
  await page.getByRole("button", { name: "Open the workspace" }).click();
  await page.waitForURL(/\/en\/screening\/home\/?$/);
  expect(fake.calls.find((c) => c.path === "/api/v1/workspaces/open")?.body).toEqual({ slug: "weed-review" });
});

const EARLIER = {
  playbook_type: "SCOPING_REVIEW",
  metadata: { title: "UAV crop-weed mapping", lead_researcher: "M" },
  epistemology: { primary_paradigm: "Pragmatist / Mixed Methods" },
  research_questions: [{ id: "RQ1", text: "How reliable is UAV weed mapping across fields?" }],
  search_strategy: {},
  screening_criteria: {
    inclusion: [{ id: "INC-01", criterion: "Field trials with UAV imagery" }],
    exclusion: [{ id: "EXC-01", criterion: "Satellite only", reason_category: "WRONG_PLATFORM" }],
  },
};

test("a researcher starts from an earlier review, writes the question, adds a reason and an own column (M10b)", async ({ page }) => {
  const fake = await engine(page, { workspaces: [{ slug: "uav-crop-weed-v03", title: "UAV review v0.3", protocol: EARLIER }] });
  await page.goto("/en/inception/");
  await page.getByRole("link", { name: "Start from an existing review" }).click();
  await page.getByRole("radio", { name: /UAV review v0.3/ }).check();
  await expect(page.getByRole("heading", { name: "Comes across as you wrote it" })).toBeVisible();
  await page.getByRole("button", { name: "Create the draft from this review" }).click();

  await expect(page.locator("[data-imported-banner]")).toContainText("Started from uav-crop-weed-v03");
  await expect(page.locator("[data-imported-mark='shape']")).toBeVisible();
  await expect(page.locator("[data-imported-mark='scope']")).toHaveCount(0);
  await page.getByRole("button", { name: "Use research question 1" }).click();
  await page.getByRole("button", { name: "Save draft and exit" }).click();
  await page.waitForURL(/\/en\/inception\/?(\?|$)/);
  const id = [...fake.drafts.keys()].find((key) => key !== SESSION)!;
  expect((fake.drafts.get(id)!.draft as { topic: string }).topic).toBe("How reliable is UAV weed mapping across fields?");

  await page.goto(`/en/inception/criteria/?draft=${id}`);
  const exclusion = page.locator("[data-criterion]", { hasText: "Satellite only" });
  await expect(exclusion.getByText("Reason WRONG_PLATFORM")).toBeVisible();
  const own = page.locator("[data-own-columns]");
  await own.getByLabel("Column name").fill("Sensor");
  await own.getByLabel("What should be extracted?").fill("Camera on the UAV");
  await own.getByRole("button", { name: "Add column" }).click();
  await expect(own.locator("[data-own-column='Sensor']")).toBeVisible();
  await page.getByRole("button", { name: "Continue to review" }).click();
  await page.waitForURL(/\/en\/inception\/review\/?\?draft=/);
  const draft = fake.drafts.get(id)!.draft as { custom_matrix_columns: unknown[]; extra_exclusions: unknown[] };
  expect(draft.custom_matrix_columns).toEqual([{ name: "Sensor", description: "Camera on the UAV", data_type: "free_text", required: false }]);
  expect(draft.extra_exclusions).toEqual([{ criterion: "Satellite only", reason_category: "WRONG_PLATFORM" }]);
});

test("replacing a workspace with screening needs the typed name, and a wrong one is a sentence", async ({ page }) => {
  // M10b: the old Checks card line is the engine's REVIEW_TARGET_HAS_SCREENING row of "Ready to create?".
  const screening = { check_id: "REVIEW_TARGET_HAS_SCREENING", step: "review", level: "warning" as const, dismissible: false, params: { n: 4 }, action: { kind: "field", step: "review", field: "title" } };
  await engine(page, { draft: decided(), existing: "bound", checks: () => [screening] });
  await page.goto(`/en/inception/review/?draft=${SESSION}`);
  await expect(page.locator("[data-check='REVIEW_TARGET_HAS_SCREENING'] [data-sentence]")).toHaveText("That workspace has 4 screening decisions.");
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

test("a check proposes UAV on Concepts and criteria; Apply writes it; a dismissed warning survives a reload; Review reads Not ready, then Ready (M10b)", async ({ page }) => {
    const fake = await engine(page, {
      // The out-of-scope item accepted (H-run-small-fixes, finding 2), so the wizard's proof criterion is the one blocker.
      draft: completeDraft({ title: "UAV weed detection", rqs: ["Can RGB cameras on a UAV find weeds in real time?"], criteria_decisions: { [outOfScopeId()]: true } }),
      checks: true,
    });
    await page.goto(`/en/inception/criteria/?draft=${SESSION}`);

    // The check made a proposal; nothing is applied until the click.
    const proposals = page.locator("[data-proposals='criteria']");
    const uav = proposals.locator("li[data-proposal]", { hasText: "Add UAV to Concepts" });
    await expect(uav).toHaveAttribute("data-status", "open");
    await expect(page.locator("#concept-1")).toHaveCount(0);
    await uav.getByRole("button", { name: "Apply" }).click();
    await expect(page.locator("#concept-1")).toHaveValue("UAV");
    expect((fake.drafts.get(SESSION)!.draft as { concepts: { concept: string }[] }).concepts.map((c) => c.concept)).toEqual(["weed detection", "UAV"]);
    await page.reload();
    await expect(page.locator("#concept-1")).toHaveValue("UAV");
    await proposals.locator("[data-decided] summary").click();
    await expect(proposals.locator("[data-decided]").getByText("Applied by you")).toBeVisible();

    // A warning dismissed with a reason is kept across a reload, under Dismissed, and can be restored.
    const panel = page.locator("[data-checks-panel='criteria']");
    const rgb = panel.locator("[data-open-rows] li[data-check='CONCEPT_TERM_MISSING'][data-subject='RGB']");
    await rgb.getByRole("button", { name: "Dismiss" }).click();
    await panel.getByLabel("Why are you dismissing this? It is kept in the record.").fill("RGB is the camera type, not a search word.");
    await panel.getByRole("button", { name: "Dismiss with this reason" }).click();
    await expect(panel.locator("[data-dismissed] summary")).toHaveText("Dismissed (1)");
    await page.reload();
    const dismissed = page.locator("[data-checks-panel='criteria'] [data-dismissed]");
    await dismissed.locator("summary").click();
    await expect(dismissed.locator("[data-dismissal]")).toContainText("RGB is the camera type, not a search word.");
    await dismissed.getByRole("button", { name: "Restore" }).click();
    await expect(page.locator("[data-checks-panel='criteria'] [data-open-rows] li[data-check='CONCEPT_TERM_MISSING'][data-subject='RGB']")).toBeVisible();

    // Review: the undecided wizard criterion is a blocker; once accepted, Ready.
    await page.goto(`/en/inception/review/?draft=${SESSION}`);
    const ready = page.locator("[data-checks-panel='review-ready']");
    await expect(ready.locator("[data-ready-sentence]")).toHaveText("Not ready: 1 must be fixed first.");
    await expect(ready.locator("li[data-check='CRITERIA_UNDECIDED'] [data-step-chip]")).toHaveText("Step 5");
    await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
    const proof = page.locator("[data-criterion]", { hasText: "Reports the gold-standard proof" });
    await proof.getByRole("button", { name: "Accept" }).click();
    await page.getByRole("button", { name: "Continue to review" }).click();
    await page.waitForURL(/\/en\/inception\/review\/?\?draft=/);
    await expect(page.locator("[data-checks-panel='review-ready'] [data-ready-sentence]")).toHaveText(/^Ready to create\./);
    // The Accept on a wizard criterion was recorded with the save.
    const put = fake.calls.filter((c) => c.method === "PUT").at(-1)!;
    expect(put.body?.accepted_from).toEqual([{ mechanism: "wizard_criterion", field: "criteria_decisions", value: proofId() }]);
});

const SCREENS = ["", "scope/", "explore/", "direction/", "shape/", "criteria/", "review/", "done/", "import/"] as const;

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
      const fake = await engine(page, { draft: emitted ? undefined : assisted(), checks: true });
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
        const fake = await engine(page, { draft: emitted ? undefined : assisted(), checks: true });
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
    const fake = await engine(page, { draft: emitted ? undefined : assisted(), checks: true });
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

test("the researcher unticks a database, moves another, edits the query, and each database shows the query it received (M10a)", async ({ page }) => {
  const fake = await engine(page, { draft: decided() });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  const field = page.getByRole("textbox", { name: "Query sent to the databases" });
  await expect(field).toHaveValue("on-device weed detection");
  await page.getByRole("checkbox", { name: "Ask Semantic Scholar" }).uncheck();
  const down = page.getByRole("button", { name: "Move OpenAlex down" });
  await down.focus();
  await page.keyboard.press("Enter");
  await expect(down).toBeFocused();
  await expect(page.locator("[data-picker-status]")).toHaveText("OpenAlex moved to position 2 of 3");
  await field.fill("weed camera");
  await page.getByRole("button", { name: "Search the literature" }).click();
  await expect(page.getByRole("heading", { name: "Pool · 14 papers" })).toBeVisible();

  const probes = fake.calls.filter((c) => c.method === "POST" && c.path === `${RECON}/probe`);
  expect(probes.map((c) => c.body)).toEqual([{ refresh: false, semantic: false, databases: ["crossref", "openalex", "arxiv"], query: "weed camera" }]);
  // The topic sentence is not changed by the query.
  expect((fake.drafts.get(SESSION)!.draft as { topic: string }).topic).toBe("on-device weed detection");
  const legs = page.locator("[data-databases] [data-leg]");
  await expect(legs).toHaveCount(3);
  await expect(page.locator("[data-databases] [data-leg='crossref'] [data-executed-query]")).toHaveText("weed camera");
  await expect(page.locator("[data-databases] [data-leg='openalex'] [data-executed-query]")).toHaveText("weed camera");
  await expect(page.locator("[data-databases] [data-leg='arxiv'] [data-executed-query]")).toHaveText("all:weed AND all:camera");
  // A reload shows the last choice.
  await page.reload();
  await expect(page.getByRole("textbox", { name: "Query sent to the databases" })).toHaveValue("weed camera");
  await expect(page.locator("[data-picker-row][data-selected='true']")).toHaveCount(3);
  await expect(page.locator("[data-picker-row]").first()).toHaveAttribute("data-picker-row", "crossref");
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}/inception/explore/ before the first search: the picker passes axe, and reads ${locale === "ar" ? "right to left" : "left to right"} (M10a)`, async ({ page }) => {
    await engine(page, { draft: decided() });
    await page.goto(`/${locale}/inception/explore/?draft=${SESSION}`);
    const row = page.locator("[data-picker-row='crossref']");
    await expect(row).toBeVisible();
    await page.waitForLoadState("networkidle");
    // Checkbox at the inline start, move buttons at the inline end.
    const box = (await row.locator("input[type=checkbox]").boundingBox())!;
    const up = (await row.locator("[data-move='up']").boundingBox())!;
    if (locale === "ar") expect(up.x).toBeLessThan(box.x);
    else expect(up.x).toBeGreaterThan(box.x);
    // Up and down are vertical: never mirrored.
    const transforms = await page.locator("[data-picker] svg").evaluateAll((svgs) => svgs.map((s) => getComputedStyle(s).transform));
    expect(transforms.every((t) => t === "none")).toBe(true);
    await expect(page.locator("#explore-query")).toHaveAttribute("dir", "ltr");
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
  });
}

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
  await page.getByRole("button", { name: "Refresh pool", exact: true }).click();
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
  await page.getByLabel("To year", { exact: true }).fill("2025");
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
  await page.getByLabel("Your direction", { exact: true }).fill("quantum sensing");
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
  await page.getByRole("button", { name: "Search again, narrower · 1 left", exact: true }).click();
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

// --- M10b Part C: sample curation on Explore (02-explore "Sample curation") ----------------

/** The checks the fake answers: the thin-sample row from the engine's own `sample.recommend` (the screen compares nothing). */
async function curating(page: Page) {
  let fake: Awaited<ReturnType<typeof engine>> | null = null;
  const thin = (record: Record<string, unknown>) => {
    const sample = fake?.recon.sample(record) as { n_docs: number; recommend: { reasons: string[]; threshold: { floor: number } } } | null;
    return sample?.recommend.reasons.includes("BELOW_FLOOR")
      ? [{ check_id: "EXPLORE_POOL_THIN", step: "explore", level: "warning" as const, params: { n: sample.n_docs, floor: sample.recommend.threshold.floor }, action: { kind: "step", step: "scope" } }]
      : [];
  };
  fake = await engine(page, { draft: decided(), checks: thin });
  return fake;
}

const notRelevant = (page: Page, title: string) => page.getByRole("button", { name: `Not relevant: ${title}` });
const SEG = (i: number) => `Lightweight cnn weed segmentation ${i}`;
/** M10d (03-guidance rule 4): the papers are folded behind "Papers · {n}"; one added step opens them. */
async function openPapers(page: Page) {
  const papers = page.locator("details[data-papers]");
  await papers.waitFor({ state: "attached" });
  if (!(await papers.evaluate((d) => (d as HTMLDetailsElement).open))) await papers.locator(":scope > summary").click();
}

test("a researcher leaves papers out, sees the directions and counts change, undoes one, and a bound direction goes out of date (M10b)", async ({ page }) => {
  const fake = await curating(page);
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await page.getByRole("button", { name: "Search the literature" }).click();
  await expect(page.getByRole("heading", { name: "Pool · 14 papers" })).toBeVisible();
  await openPapers(page);
  await expect(page.getByText("14 papers · none left out")).toBeVisible();
  await page.getByRole("button", { name: /^\+ 9 more/ }).click();

  // Three papers: two replaced from the reserve, the third makes the sample smaller.
  for (const i of [0, 1, 2]) {
    await notRelevant(page, SEG(i)).click();
    await expect(notRelevant(page, SEG(i))).toHaveCount(0);
  }
  await expect(page.getByText("13 papers · 3 left out")).toBeVisible();
  await expect(page.locator("[data-added-for]")).toHaveCount(2);
  await expect(page.getByRole("button", { name: "See 3 directions" })).toBeVisible();

  // Two more: the segmentation direction loses its anchors and the sample falls under the floor.
  for (const i of [3, 4]) {
    await notRelevant(page, SEG(i)).click();
    await expect(notRelevant(page, SEG(i))).toHaveCount(0);
  }
  await expect(page.getByRole("button", { name: "See 2 directions" })).toBeEnabled();
  await expect(page.getByText("11 papers · 5 left out")).toBeVisible();
  await expect(page.locator("[data-sample-moved]")).toHaveText(`Left out: ${SEG(4)}. Directions: 3 to 2. Papers: 11.`);
  const thinRow = page.locator("[data-checks-panel='explore'] [data-check='EXPLORE_POOL_THIN']");
  await expect(thinRow).toContainText("The sample has only 11 papers. 12 or more gives steadier suggestions.");
  await expect(thinRow.getByRole("link", { name: "Change scope" })).toBeVisible();

  // A reload keeps them left out.
  await page.reload();
  await openPapers(page);
  await expect(page.getByText("11 papers · 5 left out")).toBeVisible();

  // Put one back from the Left out list.
  await page.getByRole("button", { name: "Left out · 5" }).click();
  await page.getByRole("button", { name: `Put back: ${SEG(4)}` }).click();
  await expect(page.getByText("12 papers · 4 left out")).toBeVisible();
  await expect(page.getByRole("button", { name: "Left out · 4" })).toBeFocused();
  await expect(page.locator("[data-check='EXPLORE_POOL_THIN']")).toHaveCount(0);

  // Bind a direction, then leave another paper out: the warning, then the stale note.
  await page.getByRole("button", { name: "See 3 directions" }).click();
  await page.getByRole("radio", { name: "weed detection" }).check();
  await page.getByRole("button", { name: "Pursue weed detection" }).click();
  await expect(page.getByRole("heading", { name: "Your direction: weed detection" })).toBeFocused();
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await openPapers(page);
  await notRelevant(page, "Real-time weed detection on embedded hardware 0").click();
  const dialog = page.getByRole("alertdialog", { name: "Leaving this paper out will make your chosen direction out of date" });
  await expect(dialog.getByRole("button", { name: "Keep the paper" })).toBeFocused();
  await dialog.getByRole("button", { name: "Leave it out" }).click();
  await expect(page.getByText("The direction you chose was based on an earlier sample.")).toBeVisible();
  expect(fake.calls.filter((c) => c.method === "POST" && c.path === `${RECON}/sample`)).toHaveLength(7);

  // Bind again: the sample is now under the floor, so the box is needed.
  await page.getByRole("link", { name: "Choose a direction" }).click();
  await page.getByRole("radio", { name: "weed detection" }).check();
  await page.getByRole("checkbox", { name: "I accept a pool this small" }).check();
  await page.getByRole("button", { name: "Pursue weed detection" }).click();
  await expect(page.getByRole("heading", { name: "Your direction: weed detection" })).toBeVisible();
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await expect(page.getByRole("heading", { name: "Pool · 11 papers" })).toBeVisible();
  await expect(page.locator("[data-stale-binding]")).toHaveCount(0);
});

test("a mark and its undo can be done with the keyboard alone (M10b)", async ({ page }) => {
  const fake = await curating(page);
  fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await openPapers(page);
  const first = notRelevant(page, "Real-time weed detection on embedded hardware 0");
  await first.focus();
  await page.keyboard.press("Enter");
  await expect(notRelevant(page, "Real-time weed detection on embedded hardware 1")).toBeFocused();
  await expect(page.locator("[data-sample-toast='mark']")).toContainText("Left out: Real-time weed detection on embedded hardware 0");
  const undo = page.locator("[data-sample-toast] [data-undo]");
  for (let i = 0; i < 40 && !(await undo.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
  await expect(undo).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("14 papers · none left out")).toBeVisible();
  expect(fake.calls.filter((c) => c.method === "POST" && c.path === `${RECON}/sample`).map((c) => c.body)).toEqual([
    { add: ["10.1/w000"], base_updated_at: expect.any(String) },
    { remove: ["10.1/w000"], base_updated_at: expect.any(String) },
  ]);
});

for (const scheme of ["light", "dark"] as const) {
  test(`ar/inception/explore/ with papers left out (${scheme}): the row button sits at the inline end, axe passes, nothing scrolls sideways (M10b)`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    const fake = await curating(page);
    fake.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = fake.drafts.get(SESSION)!;
    fake.handle("POST", `${RECON}/sample`, { add: ["10.1/s000"], base_updated_at: record.updated_at });
    await page.goto(`/ar/inception/explore/?draft=${SESSION}`);
    await openPapers(page);
    const row = page.locator("[data-paper-key='10.1/w000']");
    await expect(row.locator("[data-mark]")).toBeVisible();
    const button = (await row.locator("[data-mark]").boundingBox())!;
    const title = (await row.locator("td").first().boundingBox())!;
    expect(button.x).toBeLessThan(title.x);
    await page.locator("[data-left-out-toggle]").click();
    await page.waitForLoadState("networkidle");
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    for (const viewport of [MOBILE_VIEWPORT, DESKTOP_VIEWPORT]) {
      await page.setViewportSize(viewport);
      expectNoSidewaysScroll(await measureOverflow(page), `ar/inception/explore/ ${viewport.width}px with papers left out`);
    }
  });
}

test("an empty search shows one Databases asked list and the shorten advice only when the engine says so (M10b)", async ({ page }) => {
  await engine(page, { draft: decided(), recon: { outcomes: ["empty"] } });
  await page.goto(`/en/inception/explore/?draft=${SESSION}`);
  await page.getByRole("button", { name: "Search the literature" }).click();
  await expect(page.getByRole("heading", { name: "The search found no papers" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Databases asked" })).toHaveCount(1);
  await expect(page.getByText("Every word of the query must appear, so a long query can find nothing. Shorten the query above.")).toBeVisible();
});
