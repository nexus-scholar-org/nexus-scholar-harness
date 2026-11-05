import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { join } from "node:path";

import { DESKTOP_VIEWPORT, MOBILE_VIEWPORT, SCREENSHOT_DIR, expect, test } from "./helpers";

/**
 * Export and methods (spec 10) in a real browser. The same-origin console
 * proxy is answered at the network boundary with the engine's shapes, so the
 * screen is the real build: the file arrives as a browser download under the
 * engine's name, and the English paragraph stays left-to-right on an Arabic
 * page. The live gate covers the same routes against a real engine.
 */

const PARAGRAPH =
  "30 records were identified; 0 duplicates were removed; 30 records were screened; 20 were excluded (EX-01: 20); 4 were unclear and went to full-text assessment; 6 were included. One reviewer screened every record.";

const METHODS = {
  generation_id: "GEN-0123456789abcdef0123",
  generation_fingerprint: "sha256:feedface",
  published_at: "2026-11-05T10:00:00Z",
  language: "en",
  paragraph: PARAGRAPH,
  figures: { identified: 30, duplicates_removed: 0, screened: 30, excluded: 20, unclear: 4, included: 6, exclusion_reasons: { "EX-01": 20 } },
  sources: [{ name: "prisma_report.json", path: "literature/prisma_report.json", digest: "sha256:abc" }],
  caveats: [],
  not_stated: [],
};

const PREVIEW = {
  identified: 30, duplicates_removed: 0, screened: 30, excluded: { total: 20, by_reason: { "EX-01": 20 } }, unclear_to_full_text: 4, included: 6, not_yet_decided: 0, checks: [],
};

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

const RIS = "TY  - JOUR\r\nTI  - A study\r\nER  - \r\n";

async function engine(page: Page, publication = "CURRENT") {
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console/api/v1", "");
    if (path === "/ui/publication-status") {
      return route.fulfill({ json: { shape: "ui07.publication-status-v1", status: publication, code: publication === "CURRENT" ? null : "GENERATION_STALE", generation_id: "GEN-1", outputs: {}, message: "", details: {} } });
    }
    if (path === "/screening/methods") return route.fulfill({ json: METHODS });
    if (path === "/screening/prisma/preview") return route.fulfill({ json: PREVIEW });
    if (path === "/screening/export") {
      const format = url.searchParams.get("format") ?? "ris";
      return route.fulfill({
        status: 200,
        body: format === "ris" ? RIS : "﻿study_id,decision\r\n",
        headers: { "content-type": "text/plain", "content-disposition": `attachment; filename="golden-screening-GEN-1-${url.searchParams.get("set")}.${format}"` },
      });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
}

test("downloads the RIS under the engine's name and shows the draft paragraph", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page);
  await page.goto("/en/screening/export");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Take your screening with you.");
  await expect(page.locator("[data-paragraph]")).toHaveText(PARAGRAPH);

  const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Download" }).click()]);
  expect(download.suggestedFilename()).toBe("golden-screening-GEN-1-included,unclear.ris");

  await page.getByRole("radio", { name: /CSV/ }).check();
  const [csv] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Download" }).click()]);
  expect(csv.suggestedFilename()).toBe("golden-screening-GEN-1-included,unclear,excluded.csv");
});

test("keeps the English paragraph left-to-right on the Arabic page", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page);
  await page.goto("/ar/screening/export");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  const paragraph = page.locator("[data-paragraph]");
  await expect(paragraph).toHaveText(PARAGRAPH);
  expect(await paragraph.evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
});

test("a stale publication refuses export with its code", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page, "STALE");
  await page.goto("/en/screening/export");
  await expect(page.locator('[data-state="GENERATION_STALE"]')).toContainText("Publish again before you export.");
  await expect(page.getByRole("button", { name: "Download" })).toHaveCount(0);
});

test("a phone sees only the desktop pointer", async ({ page }) => {
  await page.setViewportSize(MOBILE_VIEWPORT);
  await engine(page);
  await page.goto("/en/screening/export");
  await expect(page.locator("[data-phone]")).toBeVisible();
  await expect(page.locator("[data-phone]")).toContainText("Export and methods are on your desktop.");
  await expect(page.locator("[data-paragraph]")).toBeHidden();
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: axe finds no violation on the ready screen, contrast included`, async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await engine(page);
    await page.goto(`/${locale}/screening/export`);
    await expect(page.locator("[data-paragraph]")).toBeVisible();
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
  for (const locale of ["en", "ar"] as const) {
    test(`1440-screening-export${locale === "en" ? "" : "-ar"}.png`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1100 });
      await engine(page);
      await page.goto(`/${locale}/screening/export`);
      await expect(page.locator("[data-paragraph]")).toBeVisible();
      await page.screenshot({ path: join(SCREENSHOT_DIR, `1440-screening-export${locale === "en" ? "" : "-ar"}.png`), fullPage: true });
    });
  }
});
