import { createRequire } from "node:module";

import type { Page, Route } from "@playwright/test";

import { expect, test } from "./helpers";

/**
 * M8b-triage-highlights in a real browser (spec 03, M8b points 1, 2, 8, 11):
 * the record pane with both kinds of mark on, at the two desktop sizes, in
 * light and dark (the two projects), in English and Arabic. The engine's
 * matching is tested in Python; this fake sends spans in the engine's shapes.
 */

const CRITERIA = [
  { id: "INC-01", text: "Uses UAV-acquired imagery for crop or weed mapping", kind: "inclusion" },
  { id: "INC-02", text: "Primary empirical study", kind: "inclusion" },
  { id: "EXC-01", text: "Satellite-only imagery", kind: "exclusion" },
];
const BINDING = { protocol_fingerprint: "sha256:p", batch_id: "batch-1", batch_sha256: "sha256:b" };
const TITLE = "Weed mapping in maize from unmanned aerial vehicle imagery";
const SENTENCE =
  "In this study, weeds in a maize field were mapped from images taken by an unmanned aerial vehicle (UAV), using multi-spectral bands and a segmentation network; crop rows and weed patches were compared with ground measurements and reached high overall accuracy.";
const ABSTRACT = Array.from({ length: 8 }, () => SENTENCE).join(" ");
const CONCEPTS = [
  { concept: "UAV", terms: ["UAV", "unmanned aerial vehicle", "drone"] },
  { concept: "weed", terms: ["weed"] },
  { concept: "multispectral", terms: ["multi-spectral", "multispectral"] },
  { concept: "maize", terms: ["maize"] },
  { concept: "rice", terms: ["rice"] },
];

/** Test data only: where each term's words sit, longest first, so the fake answers in the engine's shape. */
function marks(text: string, field: "title" | "abstract") {
  const found: { field: string; start: number; end: number; concept: number }[] = [];
  const terms = CONCEPTS.flatMap((c, concept) => c.terms.map((term) => ({ term, concept }))).sort((a, b) => b.term.length - a.term.length);
  for (const { term, concept } of terms) {
    const re = new RegExp(`(?<![\\p{L}\\p{N}])${term.replace(/[-]/g, "[- ]")}(?:s|es)?(?![\\p{L}\\p{N}])`, "giu");
    for (const m of text.matchAll(re)) {
      const start = m.index!;
      const end = start + m[0].length;
      if (found.every((f) => f.field !== field || end <= f.start || start >= f.end)) found.push({ field, start, end, concept });
    }
  }
  return found.sort((a, b) => a.start - b.start);
}

const QUOTE = "images taken by an unmanned aerial vehicle (UAV)";
const SEARCH_TERMS = (() => {
  const all = [...marks(TITLE, "title"), ...marks(ABSTRACT, "abstract")];
  return {
    concepts: CONCEPTS.map((c, i) => ({ ...c, concept: c.concept, mentions: all.filter((m) => m.concept === i).length })),
    marks: all,
  };
})();
const QUOTES = [
  { criterion_id: "INC-01", answer: "yes", found: true, field: "abstract", start: ABSTRACT.indexOf(QUOTE), end: ABSTRACT.indexOf(QUOTE) + QUOTE.length },
  { criterion_id: "INC-02", answer: "yes", found: true, field: "title", start: 0, end: 12 },
  { criterion_id: "EXC-01", answer: "no", found: false, field: null, start: null, end: null },
];

async function engine(page: Page) {
  const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, json: body });
  await page.route("**/api/console/api/v1/screening/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console/api/v1/screening", "");
    if (path === "/settings") return json(route, { blinding: "show", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: "show_draft_then_next" });
    if (path === "/summary") return json(route, { total: 2, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 1, needs_you: 2, conflicts: 0, lanes: { agent: 1, you: 0, second_screener: "PARKED" } });
    if (path === "/queue") {
      const items = ["STU-1", "STU-2"].map((id, i) => ({ study_id: id, title: i ? "Second record" : TITLE, batch_id: "batch-1", batch_index: 1, has_proposal: true, decided: false, flags: [] }));
      return json(route, { items: url.searchParams.get("view") === "decided" ? [] : items, next_cursor: null });
    }
    if (path === "/decisions/conflicts") return json(route, { items: [] });
    if (/^\/records\/[^/]+\/proposal$/.test(path)) {
      return json(route, {
        proposal: {
          proposal_id: "PRP-1",
          task_version: "screen-v1",
          model: "claude-haiku-5-5",
          prompt_sha256: "sha256:" + "a".repeat(64),
          criteria: [
            { id: "INC-01", answer: "yes", evidence: { start: 0, end: QUOTE.length, text: QUOTE } },
            { id: "INC-02", answer: "yes", evidence: { start: 0, end: 12, text: TITLE.slice(0, 12) } },
            { id: "EXC-01", answer: "no", evidence: { start: 3, end: 9, text: "satellite" } },
          ],
          derived_outcome: "MAYBE",
          reason_code: null,
          validators: [{ name: "quote_in_source", ok: false, detail: "EXC-01: quote not at its offsets" }],
          cannot_decide: false,
          quotes: QUOTES,
        },
      });
    }
    const record = path.match(/^\/records\/([^/]+)$/);
    if (record) {
      return json(route, { study_id: record[1], title: TITLE, abstract: ABSTRACT, year: 2024, venue: "Remote Sensing", doi: null, batch_index: 1, highlights: [], criteria: CRITERIA, binding: BINDING, my_decision: null, history: [], not_reported_policy: "unclear", search_terms: SEARCH_TERMS });
    }
    return json(route, { detail: { code: "NOT_FOUND", message: path } }, 404);
  });
}

async function open(page: Page, locale: "en" | "ar" = "en") {
  await engine(page);
  await page.goto(`/${locale}/screening/triage`);
  await expect(page.locator("[data-record-pane] [data-quote]").first()).toBeVisible();
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 1280, height: 720 },
]) {
  test(`marks on at ${viewport.width}x${viewport.height}: the page never scrolls, the record pane does`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await open(page);
    expect(await page.evaluate(() => document.documentElement.scrollHeight <= window.innerHeight)).toBe(true);
    const pane = page.locator("[data-record-pane]");
    expect(await pane.evaluate((el) => el.scrollHeight > el.clientHeight)).toBe(true);
    const bar = await page.locator("[data-decision-bar]").boundingBox();
    expect(bar && bar.y + bar.height <= viewport.height).toBe(true);
  });
}

test("turning the marks off and on never moves the text", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page);
  const boxes = () =>
    page.evaluate(() => {
      const box = (sel: string) => {
        const r = document.querySelector(sel)!.getBoundingClientRect();
        return [r.x, r.y, r.width, r.height].map((v) => Math.round(v * 10) / 10);
      };
      return { title: box("[data-record-title]"), abstract: box("[data-record-abstract]") };
    });
  const before = await boxes();
  await page.locator('[data-marks-switch="terms"]').click();
  await page.locator('[data-marks-switch="quotes"]').click();
  await expect(page.locator("[data-record-pane] [data-term]")).toHaveCount(0);
  await expect(page.locator("[data-record-pane] [data-quote]")).toHaveCount(0);
  expect(await boxes()).toEqual(before);
  await page.locator('[data-marks-switch="terms"]').click();
  await page.locator('[data-marks-switch="quotes"]').click();
  expect(await boxes()).toEqual(before);
  // Remembered on this computer: a reload keeps the choice.
  await page.locator('[data-marks-switch="terms"]').click();
  await page.reload();
  await expect(page.locator('[data-marks-switch="terms"]')).toHaveAttribute("aria-pressed", "false");
});

test("a search-term mark inside a quote stays visible (overlap)", async ({ page }) => {
  await open(page);
  const inner = page.locator('[data-record-abstract] [data-quote] [data-term="0"]').first();
  await expect(inner).toHaveText("unmanned aerial vehicle");
  const style = await inner.evaluate((el) => getComputedStyle(el).textDecorationLine);
  expect(style).toContain("underline");
});

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
  test(`${locale}: axe finds no violation with both kinds of mark on; screenshot of the record pane`, async ({ page }, info) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await open(page, locale);
    await expect(page.locator("html")).toHaveAttribute("dir", locale === "ar" ? "rtl" : "ltr");
    // A quote under the active frame, as when the researcher hovers its answer.
    await page.locator("#answer-INC-01").hover();
    await expect(page.locator('[data-quote~="INC-01"]')).toHaveAttribute("data-active", "");
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
    const dir = process.env.M8B_SHOTS;
    const name = `triage-highlights-${locale}-${info.project.name.includes("dark") ? "dark" : "light"}.png`;
    await page.screenshot({ path: dir ? `${dir}/${name}` : info.outputPath(name), fullPage: false });
  });
}
