import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * Export and methods for the charting table (M12a Part C, spec 04) in a real
 * browser on the production build. As in the other charting specs, the console
 * is answered at the network boundary by a small fake in the engine's shapes
 * (`src/scholar_harness/console/api/charting.py`, `charting/report.py`): the
 * table with its counts and last export, the methods block with the PRISMA
 * full-text counts, and the three exports, each of which records the last export
 * the way `table.export` does. No console runs. It runs in light (`chromium`)
 * and dark (`chromium-dark`).
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

const PARAGRAPH =
  "Of 17 reports sought for retrieval, 3 were not retrieved (No access or paywalled: 1; Not found: 1; Authors did not reply: 1). 12 reports were assessed at full text by one reviewer; 4 were excluded (EXC-01 Not a crop field: 2; FAILS-INC-01 UAV imagery: 1; Other: 1) and 8 were included. The counts are of reports; reports of the same study were not linked.";

function group(over: Record<string, unknown> = {}) {
  return {
    sought: 0, not_retrieved: 0, not_retrieved_reasons: {}, assessed: 0, excluded: 0, exclusion_reasons: {}, included: 0,
    awaiting_retrieval: 0, to_confirm: 0, retrieved_not_assessed: 0, assessed_without_full_text: 0,
    ...over,
  };
}

const DATABASES = group({
  sought: 12, not_retrieved: 2, not_retrieved_reasons: { "No access or paywalled": 1, "Not found": 1 }, assessed: 9, excluded: 3,
  exclusion_reasons: { "EXC-01": 2, OTHER: 1 }, included: 6, awaiting_retrieval: 1, assessed_without_full_text: 1,
});
const CHASING = group({
  sought: 5, not_retrieved: 1, not_retrieved_reasons: { "Authors did not reply": 1 }, assessed: 3, excluded: 1,
  exclusion_reasons: { "FAILS-INC-01": 1 }, included: 2, awaiting_retrieval: 1, to_confirm: 1,
});
const TOTAL = group({
  sought: 17, not_retrieved: 3, not_retrieved_reasons: { "No access or paywalled": 1, "Not found": 1, "Authors did not reply": 1 }, assessed: 12, excluded: 4,
  exclusion_reasons: { "EXC-01": 2, OTHER: 1, "FAILS-INC-01": 1 }, included: 8, awaiting_retrieval: 2, to_confirm: 1, assessed_without_full_text: 1,
});

function methods(state: "default" | "nothing-assessed") {
  const empty = state === "nothing-assessed";
  const paragraph = empty ? "Of 4 reports sought for retrieval, none were not retrieved. No report has been assessed at full text yet." : PARAGRAPH;
  const databases = empty ? group({ sought: 4, awaiting_retrieval: 4 }) : DATABASES;
  return {
    shape: "charting.methods-v1",
    sentences: [paragraph],
    paragraph,
    figures: {
      prisma: { schema: "nexus.charting-prisma-fulltext.v1", unit: "reports", rounds: [], arms: { databases, citation_searching: empty ? group() : CHASING }, total: empty ? databases : TOTAL },
      open_access: { used: 1, discarded: 0, services: ["Unpaywall"] },
      reviewers: { fulltext_decisions: 1, charting: 1 },
      charted: 5, not_charted: 3, cells_open: 7, required_open: 2, pilot: 2, amendments: [],
    },
    caveats: empty ? [] : ["1 fetched copy waits for the reviewer's confirmation and is not counted as retrieved."],
    not_stated: empty ? [] : ["The sentences give totals over every round; the PRISMA counts are split by round."],
    sources: [{ name: "included.json", path: "literature/included.json", digest: `sha256:${"d".repeat(64)}` }],
  };
}

function row(i: number) {
  return {
    study_id: `STU-00${i}`, title: `Study ${i}`, authors: ["Sa, I."], year: 2020, venue: "Remote Sensing", doi: `10.3390/rs${1000 + i}`, url: null,
    abstract: null, arxiv_id: null, round: 1, arm: "databases", round_label: "Databases", generation_id: "gen-1", ta_decision: "INCLUDE", ta_reason: "",
    kept: true, new_since: null,
    fulltext: { status: "to_get", requested_on: null, reason: null, reason_text: null, attachment: null, link: null, pending_fetch: null, last_lookup: null, discarded_fetch: null },
    ft_decision: null, heads: { fulltext_status: null, fulltext_decision: null, attachment: null, link: null },
  };
}

async function engine(page: Page, state: "default" | "nothing-assessed" | "not-published" = "default") {
  const exports: string[] = [];
  let lastExport: Record<string, unknown> | null = null;
  const table = () => ({
    shape: "charting.table-v1", screener_id: "researcher:local",
    publication: { status: "CURRENT", code: null, generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z", round: 1 },
    rounds: [{ round: 1, arm: "databases", generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z" }],
    chasing_pending: false, stale: false, changes: null, read_only: false, read_only_code: null,
    reason_options: [
      { code: "EXC-01", label: "Not a crop field", kind: "exclusion", category: null },
      { code: "FAILS-INC-01", label: "UAV imagery", kind: "fails_inclusion", category: null },
      { code: "OTHER", label: "Other", kind: "other", category: null },
    ],
    not_retrieved_reasons: ["no_access", "not_found", "no_reply", "other"],
    counts: { kept: 4, to_get: 4, requested: 0, retrieved: 0, not_retrieved: 0, included: 0, excluded: 0, to_decide: 4, charted: 0, not_charted: 4, pilot: 0, to_confirm: 0, cells_open: 9, required_open: 4 },
    last_export: lastExport,
    rows: [1, 2, 3, 4].map(row),
  });
  await page.route("**/api/console/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/console/api/v1", "");
    if (path === "/review/next-step") return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: "" } } });
    if (state === "not-published" && path.startsWith("/charting")) {
      return route.fulfill({ status: 409, json: { detail: { code: "SCREENING_NOT_PUBLISHED", message: "publish first" } } });
    }
    if (path === "/charting" && request.method() === "GET") return route.fulfill({ json: table() });
    if (path === "/charting/methods") return route.fulfill({ json: methods(state === "nothing-assessed" ? "nothing-assessed" : "default") });
    if (path === "/charting/export") {
      const format = url.searchParams.get("format") ?? "csv";
      const view = url.searchParams.get("view") ?? "fulltext";
      exports.push(`${format}:${format === "xlsx" ? "" : view}`);
      const name = format === "xlsx" ? "charting-20261122T101500Z.xlsx" : `charting-${view}-20261122T101500Z.csv`;
      lastExport = { at: "2026-11-22T10:15:00Z", format, view: format === "xlsx" ? null : view, file_name: name, sha256: "c".repeat(64), rows: 4, not_charted: 4, cells_open: 9, required_open: 4 };
      const body = format === "xlsx" ? Buffer.from([0x50, 0x4b, 0x03, 0x04]) : Buffer.from("﻿study_id,title\r\nSTU-001,Study 1\r\n", "utf-8");
      return route.fulfill({
        status: 200,
        body,
        headers: {
          "content-type": format === "xlsx" ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" : "text/csv; charset=utf-8",
          "content-disposition": `attachment; filename="${name}"`,
        },
      });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  return { exports };
}

async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
    const raw = await run.run(document);
    return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
  });
}

const desktop = (page: Page) => page.locator("[data-desktop]");

test("renders the counts and the paragraph, downloads the CSVs and the spreadsheet, shows the last export, copies the paragraph", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const fake = await engine(page);
  await page.goto("/en/charting/report");
  await expect(desktop(page).getByRole("heading", { level: 1 })).toHaveText("Export and methods");
  await expect(page.locator("[data-paragraph]")).toHaveText(PARAGRAPH);
  await expect(page.locator('[data-count-row="sought"] td')).toHaveText(["12", "5", "17"]);
  await expect(page.locator('[data-count-row="included"] td')).toHaveText(["6", "2", "8"]);
  await expect(desktop(page).locator("[data-last-export]")).toHaveCount(0);
  await expect(desktop(page).locator("[data-required-open]")).toHaveText("4 required cells are empty.");

  const [csv] = await Promise.all([page.waitForEvent("download"), page.locator('[data-file="fulltext"]').click()]);
  expect(csv.suggestedFilename()).toBe("charting-fulltext-20261122T101500Z.csv");
  const text = readFileSync((await csv.path())!, "utf-8");
  expect(text.replace(/^﻿/, "").split("\r\n")[0].split(",")).toEqual(["study_id", "title"]);
  await expect(desktop(page).locator("[data-last-export]")).toContainText("(CSV): 4 rows.");

  await expect(page.locator('[data-file="charting"]')).toBeEnabled();
  const [charting] = await Promise.all([page.waitForEvent("download"), page.locator('[data-file="charting"]').click()]);
  expect(charting.suggestedFilename()).toBe("charting-charting-20261122T101500Z.csv");

  await expect(page.locator('[data-file="xlsx"]')).toBeEnabled();
  const [xlsx] = await Promise.all([page.waitForEvent("download"), page.locator('[data-file="xlsx"]').click()]);
  expect(xlsx.suggestedFilename()).toBe("charting-20261122T101500Z.xlsx");
  expect(readFileSync((await xlsx.path())!).subarray(0, 2).toString("latin1")).toBe("PK");
  await expect(desktop(page).locator("[data-last-export]")).toContainText("(spreadsheet): 4 rows.");
  expect(fake.exports).toEqual(["csv:fulltext", "csv:charting", "xlsx:"]);

  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByRole("button", { name: "Copy paragraph" }).click();
  await expect(desktop(page).locator("[data-announce]")).toHaveText("Copied");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(PARAGRAPH);
});

test("Arabic at 1280 px: the page mirrors, the paragraph stays left to right", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await engine(page);
  await page.goto("/ar/charting/report");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  const paragraph = page.locator("[data-paragraph]");
  await expect(paragraph).toHaveText(PARAGRAPH);
  expect(await paragraph.evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
  await expect(desktop(page).getByRole("heading", { level: 1 })).toHaveText("التصدير والمنهجية");
  await expect(page.locator('[data-count-row="sought"] td')).toHaveText(["12", "5", "17"]);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

for (const state of ["default", "nothing-assessed", "not-published"] as const) {
  test(`axe finds no violation, contrast included: ${state}`, async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await engine(page, state);
    await page.goto("/en/charting/report");
    if (state === "not-published") await expect(desktop(page).locator('[data-state="not-published"]')).toBeVisible();
    else await expect(page.locator("[data-paragraph]")).toBeVisible();
    if (state === "nothing-assessed") await expect(desktop(page).locator("[data-no-decisions]")).toBeVisible();
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
  });
}

test("at 390 px a phone sees only the desktop line and the link to charting, and no file is asked", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const fake = await engine(page);
  await page.goto("/en/charting/report");
  const phone = page.locator("[data-phone]");
  await expect(phone).toBeVisible();
  await expect(phone.getByRole("heading", { level: 1 })).toHaveText("Export and methods are on your desktop.");
  const link = phone.getByRole("link", { name: "Go to charting" });
  await expect(link).toHaveAttribute("href", "/en/charting");
  expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await expect(page.locator("[data-paragraph]")).toHaveCount(0);
  await expect(page.locator("[data-file]")).toHaveCount(0);
  expect(fake.exports).toEqual([]);
});
