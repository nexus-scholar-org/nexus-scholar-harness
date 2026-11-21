import { createRequire } from "node:module";
import { join } from "node:path";

import type { Page } from "@playwright/test";

import { completeDraft, inceptionEngine, outOfScopeId, proofId, SESSION, type FakeOptions } from "../tests/fixtures/inception-engine";
import { DESKTOP_VIEWPORT, expect, MOBILE_VIEWPORT, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * The query workbench on Inception's step 5 (M11a part C; spec
 * `docs/ux/phase0-inception/final/10-query-workbench.md`, "Acceptance tests",
 * Playwright) against the stateful fake (`tests/fixtures/workbench-engine.ts`
 * inside the inception fake). Runs in the light and the dark project.
 * `M11A_SHOTS=<folder>` also writes the screenshots looked at for the build
 * record (en and ar, light and dark); nothing is written into the repository.
 */

const FOUR = [
  { concept: "UAV", synonyms: ["unmanned aerial vehicle", "drone"] },
  { concept: "multispectral", synonyms: ["multi-spectral"] },
  { concept: "weed", synonyms: [] },
  { concept: "segmentation", synonyms: ["semantic segmentation"] },
];
const SCOPUS = [
  "TY  - JOUR\nTI  - Weed segmentation from UAV multispectral imagery\nDO  - 10.9/a\nER  - ",
  "TY  - JOUR\nTI  - Hyperspectral weed segmentation from a UAV\nAB  - hyperspectral imagery\nDO  - 10.9/b\nER  - ",
  "TY  - JOUR\nTI  - Hyperspectral weed segmentation in fields\nAB  - hyperspectral imagery\nDO  - 10.9/c\nER  - ",
].join("\n") + "\n";

async function engine(page: Page, options: FakeOptions & { draft?: Record<string, unknown> } = {}) {
  const fake = inceptionEngine(options);
  if (options.draft) fake.seed(options.draft);
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console", "") + url.search;
    const raw = route.request().postData();
    const answer = fake.handle(route.request().method(), path, raw ? (JSON.parse(raw) as Record<string, unknown>) : null);
    await route.fulfill({ status: answer.status, json: answer.body });
  });
  return fake;
}

const draft = () =>
  completeDraft({
    concepts: FOUR,
    golden_seeds: ["10.1/a", "10.1/b", "10.1/c"],
    criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true },
  });
const STRICT = "Weed segmentation from UAV multispectral imagery";
const OPTIONS: FakeOptions = { workbench: { seedTitles: { "10.1/a": STRICT, "10.1/b": STRICT, "10.1/c": STRICT } } };

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");
async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
    const raw = await run.run(document);
    return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
  });
}

/** Count, open every section, stage the Scopus export and compare: the fullest state of the region. */
async function fill(page: Page, locale: "en" | "ar") {
  const region = page.locator("[data-workbench]");
  await region.locator("[data-count]").click();
  await expect(page.locator("[data-row='openalex'] [data-cell='query']")).toBeVisible();
  for (const s of ["seeds", "comparison"]) await page.locator(`[data-section='${s}'] summary`).click();
  await page.locator("#wb-cmp-file").setInputFiles({ name: "scopus.ris", mimeType: "application/x-research-info-systems", buffer: Buffer.from(SCOPUS) });
  await page.locator("#wb-cmp-db").fill("Scopus");
  await page.locator("[data-cmp-stage]").click();
  await page.locator("[data-compare='cmp_001']").click();
  await expect(page.locator("[data-report='cmp_001'] [data-report-line]")).toBeVisible();
  void locale;
}

test.use({ viewport: DESKTOP_VIEWPORT });

test("develop the search: count four concepts, read the largest effect, merge two, count again side by side, use it, and find it saved after a reload", async ({ page }) => {
  const fake = await engine(page, { draft: draft(), ...OPTIONS });
  await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
  await expect(page.locator("[data-cost]")).toHaveText(/^Count: \d+ requests \(OpenAlex \d+, Semantic Scholar \d+, Crossref|^Count: \d+ requests/);
  await page.locator("[data-count]").click();
  await expect(page.locator("[data-row='openalex'] [data-largest]")).toHaveCount(1);
  await expect(page.locator("[data-row='crossref']")).toContainText("Crossref cannot combine concepts with AND.");
  await page.getByRole("checkbox", { name: "Select UAV to merge" }).check();
  await page.getByRole("checkbox", { name: "Select multispectral to merge" }).check();
  await page.getByRole("button", { name: "Merge into one" }).click();
  await page.getByRole("button", { name: "Merge", exact: true }).click();
  await expect(page.locator("[data-versions] [data-version='now']")).toContainText("not counted");
  await page.locator("[data-count]").click();
  await expect(page.locator("[data-version='last']")).toContainText("OpenAlex");
  await expect(page.locator("[data-version='now']")).toContainText("3 concepts");
  await page.getByRole("button", { name: "Use this version" }).click();
  await expect(page.getByText("This version is now the draft's search.")).toBeVisible();
  const saved = (fake.drafts.get(SESSION)!.draft as { concepts: { concept: string; synonyms: string[] }[] }).concepts;
  expect(saved.map((c) => c.concept)).toEqual(["UAV", "weed", "segmentation"]);
  expect(saved[0].synonyms).toEqual(["unmanned aerial vehicle", "drone", "multispectral", "multi-spectral"]);
  await page.reload();
  await expect(page.locator("#wb-concept-0")).toHaveValue("UAV");
  await expect(page.locator("[data-concept-row]")).toHaveCount(3);
});

test("compare with a staged export and apply one term to a concept", async ({ page }) => {
  await engine(page, { draft: draft(), ...OPTIONS });
  await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
  await fill(page, "en");
  await expect(page.locator("[data-report-line]")).toHaveText("2 of 3 Scopus records are missing from what your query finds.");
  const row = page.locator("[data-suggestion-row='hyperspectral']");
  await row.getByLabel("Add as synonym of").selectOption("1");
  await row.getByRole("button", { name: "Apply" }).click();
  await expect(page.locator("[data-chips='1'] [data-chip='hyperspectral']")).toBeVisible();
});

test("keyboard only: count with Ctrl+Enter, reach a suggestion, apply it with A", async ({ page }) => {
  const fake = await engine(page, { draft: completeDraft({ concepts: [{ concept: "weed detection", synonyms: [] }] }) });
  fake.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
  await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
  await page.locator("#wb-concept-0").focus();
  await page.keyboard.press("Control+Enter");
  await expect(page.locator("[data-row='openalex'] [data-cell='query']")).toContainText("counted");
  const row = page.locator("[data-suggestion-row='embedded hardware']");
  await row.focus();
  await page.keyboard.press("a");
  await expect(page.locator("[data-chip='embedded hardware']")).toBeVisible();
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: the filled workbench passes axe with contrast, reads ${locale === "ar" ? "right to left" : "left to right"}, and never scrolls sideways`, async ({ page }, info) => {
    await engine(page, { draft: draft(), ...OPTIONS });
    await page.goto(`/${locale}/inception/criteria/?draft=${SESSION}`);
    await expect(page.locator("[data-workbench]")).toBeVisible();
    await fill(page, locale);
    await expect(page.locator("html")).toHaveAttribute("dir", locale === "ar" ? "rtl" : "ltr");
    await expect(page.locator("[data-row='openalex'] [data-string]")).toHaveAttribute("dir", "ltr");
    await page.waitForLoadState("networkidle");
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
    const shots = process.env.M11A_SHOTS;
    if (shots) {
      await page.locator("[data-workbench]").screenshot({ path: join(shots, `workbench-${locale}-${info.project.name}.png`) });
    }
    for (const width of [1024, 1280, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      expectNoSidewaysScroll(await measureOverflow(page), `${locale} ${width}px`);
    }
    await page.setViewportSize(MOBILE_VIEWPORT);
    expectNoSidewaysScroll(await measureOverflow(page), `${locale} 375px`);
  });
}
