import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { join } from "node:path";

import { DESKTOP_VIEWPORT, MOBILE_VIEWPORT, SCREENSHOT_DIR, expect, test } from "./helpers";

/**
 * Import the corpus (spec 11) in a real browser. The console proxy is answered
 * at the network boundary by a small stateful fake with the engine's shapes:
 * it keeps the staged files and returns the counts a real engine would have
 * computed for them (the fake's numbers are fixed per file, not computed by the
 * screen). The engine side is covered by tests/console/test_corpus_import_api.py.
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");
const LIMITS = { max_source_bytes: 50 * 1024 * 1024, label_max_length: 40 };
const RIS = "TY  - JOUR\nTI  - A\nER  - \nTY  - JOUR\nTI  - B\nER  - \n";

type Source = { id: string; label: string; file_name: string; records: number; searched_on: string | null; query: string | null };

async function engine(page: Page, start: { sources?: Source[]; accepted?: boolean } = {}) {
  const sources: Source[] = [...(start.sources ?? [])];
  let accepted = start.accepted ?? false;
  const posts: { path: string; body: unknown }[] = [];
  const corpus = () => {
    const databases = new Map<string, { label: string; records: number; files: number; searched_on: string[]; search_details_missing: boolean }>();
    for (const s of sources) {
      const row = databases.get(s.label) ?? { label: s.label, records: 0, files: 0, searched_on: [], search_details_missing: false };
      row.records += s.records;
      row.files += 1;
      if (s.searched_on && !row.searched_on.includes(s.searched_on)) row.searched_on.push(s.searched_on);
      if (!s.searched_on || !s.query) row.search_details_missing = true;
      databases.set(s.label, row);
    }
    const identified = sources.reduce((n, s) => n + s.records, 0);
    const duplicates = sources.length > 1 ? 1 : 0;
    return {
      shape: "screening.corpus-v1",
      state: accepted ? "ACCEPTED" : sources.length ? "STAGED" : "EMPTY",
      sources,
      databases: [...databases.values()],
      preview: { identified, duplicates, unique_studies: identified - duplicates },
      accepted: accepted ? { artifact_id: "ART-corpus-0123456789abcdef", accepted_at: "2026-11-06T21:00:00Z", records: identified, studies: identified - duplicates, duplicates } : null,
      from_discovery: false,
      limits: LIMITS,
    };
  };
  await page.route("**/api/console/api/v1/screening/**", async (route) => {
    const path = new URL(route.request().url()).pathname.replace("/api/console/api/v1/screening", "");
    const method = route.request().method();
    if (path === "/corpus" && method === "GET") return route.fulfill({ json: corpus() });
    if (path === "/corpus/sources" && method === "POST") {
      const body = route.request().postDataJSON() as { label: string; file_name: string; searched_on: string | null; query: string | null };
      posts.push({ path, body });
      const label = sources.find((s) => s.label.toLowerCase() === body.label.toLowerCase())?.label ?? body.label;
      sources.push({ id: `${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${sources.length}`, label, file_name: body.file_name, records: 2, searched_on: body.searched_on, query: body.query });
      return route.fulfill({ status: 201, json: corpus() });
    }
    if (path === "/corpus/accept" && method === "POST") {
      posts.push({ path, body: null });
      accepted = true;
      return route.fulfill({ json: corpus() });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  return posts;
}

async function addFile(page: Page, name: string, label: string, details?: { date: string; query: string }) {
  await page.locator('input[type="file"]').setInputFiles({ name, mimeType: "application/x-research-info-systems", buffer: Buffer.from(RIS) });
  await page.locator("[data-import-form] input[list]").fill(label);
  if (details) {
    // The disclosure stays as the researcher left it between files.
    if (!(await page.locator("[data-search-details]").evaluate((el) => (el as HTMLDetailsElement).open))) {
      await page.locator("[data-search-details] summary").click();
    }
    await page.locator('[data-search-details] input[type="date"]').fill(details.date);
    await page.locator("[data-search-details] textarea:not([data-limits])").fill(details.query);
  }
  await page.locator("[data-import-form] button[type=submit]").click();
  // After an add the form clears its file input; the next file waits for that.
  await expect(page.locator('input[type="file"]')).toHaveValue("");
}

test.use({ viewport: DESKTOP_VIEWPORT });

test("two parts of one database and a second database are counted, then frozen", async ({ page }) => {
  const posts = await engine(page);
  await page.goto("/en/screening/import");
  await expect(page.getByRole("link", { name: "Import", exact: true })).toHaveAttribute("aria-current", "page");
  await addFile(page, "scopus-1.ris", "Scopus", { date: "2026-11-06", query: "uav AND weed" });
  await expect(page.locator('[data-database="Scopus"]')).toContainText("scopus-1.ris");
  await addFile(page, "scopus-2.ris", "scopus", { date: "2026-11-06", query: "uav AND weed" });
  await addFile(page, "savedrecs.ris", "Web of Science");

  await expect(page.locator("[data-database]")).toHaveCount(2);
  await expect(page.locator('[data-database="Scopus"]')).toContainText("scopus-2.ris");
  const counts = page.locator("[data-import-counts]");
  await expect(counts).toContainText("Preview · not frozen");
  await expect(counts.locator("[data-prisma-sentence]")).toHaveText(
    "Records identified from: Scopus (n = 4); Web of Science (n = 2); duplicate records removed (n = 1). Studies to screen: 5.",
  );
  await expect(counts.locator("[data-not-stated]")).toContainText("Web of Science");
  expect(posts[0].body).toMatchObject({ label: "Scopus", file_name: "scopus-1.ris", searched_on: "2026-11-06", query: "uav AND weed" });
  expect(posts[2].body).toMatchObject({ label: "Web of Science", searched_on: null, query: null });

  await page.getByRole("button", { name: "Accept and freeze the corpus" }).click();
  await expect(page.getByRole("button", { name: "Go back" })).toBeFocused();
  await page.getByRole("button", { name: "Freeze the corpus" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "What was imported" })).toBeVisible();
  await expect(page.locator("[data-import-form]")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Continue to Prepare" })).toHaveAttribute("href", "/en/screening/prepare");
});

test("Arabic mirrors the page and keeps file names and the search string left-to-right", async ({ page }) => {
  await engine(page, { sources: [{ id: "scopus-0", label: "Scopus", file_name: "scopus-1.ris", records: 2, searched_on: "2026-11-06", query: "uav AND weed" }] });
  await page.goto("/ar/screening/import");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByRole("heading", { level: 1, name: "استورد نتائج بحثك" })).toBeVisible();
  const file = page.locator('[data-database="Scopus"] bdi[dir="ltr"]').first();
  expect(await file.evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
  await page.locator("[data-search-details] summary").click();
  expect(await page.locator("[data-search-details] textarea:not([data-limits])").evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
});

test("a phone sees only the desktop pointer", async ({ page }) => {
  await page.setViewportSize(MOBILE_VIEWPORT);
  await engine(page);
  await page.goto("/en/screening/import");
  await expect(page.locator("[data-phone-pointer]")).toBeVisible();
  await expect(page.locator("[data-import-form]")).toBeHidden();
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: axe finds no violation on the staged screen, contrast included`, async ({ page }) => {
    await engine(page, {
      sources: [
        { id: "scopus-0", label: "Scopus", file_name: "scopus-1.ris", records: 2, searched_on: "2026-11-06", query: "uav" },
        { id: "wos-1", label: "Web of Science", file_name: "savedrecs.ris", records: 2, searched_on: null, query: null },
      ],
    });
    await page.goto(`/${locale}/screening/import`);
    await expect(page.locator("[data-import-counts]")).toBeVisible();
    await page.addScriptTag({ path: AXE_PATH });
    const result = await page.evaluate(async () => {
      const axe = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
      const raw = await axe.run(document);
      return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
    });
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
  });
}

test.describe("committed screenshots", () => {
  test.skip(({ colorScheme }) => colorScheme === "dark", "screenshots are taken in light only");
  const STAGED: Source[] = [
    { id: "scopus-0", label: "Scopus", file_name: "scopus-uav-weed-part1.ris", records: 1204, searched_on: "2026-11-06", query: 'TITLE-ABS-KEY(("UAV" OR drone*) AND weed* AND (detect* OR segment* OR map*))' },
    { id: "scopus-1", label: "Scopus", file_name: "scopus-uav-weed-part2.ris", records: 311, searched_on: "2026-11-06", query: 'TITLE-ABS-KEY(("UAV" OR drone*) AND weed* AND (detect* OR segment* OR map*))' },
    { id: "web-of-science-2", label: "Web of Science", file_name: "savedrecs.ris", records: 987, searched_on: null, query: null },
  ];
  const shot = (name: string) => join(SCREENSHOT_DIR, name);

  test("1440-screening-import-empty.png", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await engine(page);
    await page.goto("/en/screening/import");
    await expect(page.locator("[data-import-form]")).toBeVisible();
    await page.locator("[data-search-details] summary").click();
    await page.screenshot({ path: shot("1440-screening-import-empty.png"), fullPage: true });
  });

  for (const locale of ["en", "ar"] as const) {
    test(`1440-screening-import-staged${locale === "en" ? "" : "-ar"}.png`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1100 });
      await engine(page, { sources: STAGED });
      await page.goto(`/${locale}/screening/import`);
      await expect(page.locator("[data-import-counts]")).toBeVisible();
      await page.screenshot({ path: shot(`1440-screening-import-staged${locale === "en" ? "" : "-ar"}.png`), fullPage: true });
    });
  }

  test("1440-screening-import-confirm.png", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1100 });
    await engine(page, { sources: STAGED });
    await page.goto("/en/screening/import");
    await page.getByRole("button", { name: "Accept and freeze the corpus" }).click();
    await expect(page.getByRole("alertdialog")).toBeVisible();
    await page.screenshot({ path: shot("1440-screening-import-confirm.png"), fullPage: true });
  });

  test("1440-screening-import-accepted.png", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1100 });
    await engine(page, { sources: STAGED, accepted: true });
    await page.goto("/en/screening/import");
    await expect(page.locator("[data-import-frozen]")).toBeVisible();
    await page.screenshot({ path: shot("1440-screening-import-accepted.png"), fullPage: true });
  });

  test("375-screening-import.png", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await engine(page, { sources: STAGED });
    await page.goto("/en/screening/import");
    await expect(page.locator("[data-phone-pointer]")).toBeVisible();
    await page.screenshot({ path: shot("375-screening-import.png"), fullPage: true });
  });
});
