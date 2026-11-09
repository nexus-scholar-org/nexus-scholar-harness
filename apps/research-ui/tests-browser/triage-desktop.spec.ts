import { createRequire } from "node:module";

import type { Page, Route } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * Triage by keyboard (spec 03, M6-beta amendments) in a real browser. The
 * console proxy is answered by a small stateful fake with the engine's shapes;
 * the engine side is covered by the Python suite. The budget the spec sets:
 * ten records decided by keyboard in at most ten keypresses each.
 */

const N = 10;
const CRITERIA = [
  { id: "INC-01", text: "Uses UAV-acquired imagery", kind: "inclusion" },
  { id: "EXC-01", text: "Not a crop field", kind: "exclusion" },
];
const BINDING = { protocol_fingerprint: "sha256:p", batch_id: "batch-1", batch_sha256: "sha256:b" };

async function engine(page: Page, options: { abstract?: string; criteria?: typeof CRITERIA } = {}) {
  const decided = new Map<string, Record<string, unknown>>();
  const criteria = options.criteria ?? CRITERIA;
  const studies = Array.from({ length: N }, (_, i) => ({ study_id: `STU-${i + 1}`, title: `Record number ${i + 1}`, abstract: options.abstract ?? `Abstract ${i + 1} about drones.` }));
  const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, json: body });
  await page.route("**/api/console/api/v1/screening/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console/api/v1/screening", "");
    const method = route.request().method();
    if (path === "/settings") return json(route, { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: "show_draft_then_next" });
    if (path === "/summary") return json(route, { total: N, decided: decided.size, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: N - decided.size, conflicts: 0, lanes: { agent: 0, you: decided.size, second_screener: "PARKED" } });
    if (path === "/queue") {
      const view = url.searchParams.get("view");
      const items = studies
        .map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", batch_index: 1, has_proposal: false, decided: decided.has(s.study_id), flags: [] }))
        .filter((i) => (view === "decided" ? i.decided : !i.decided));
      return json(route, { items, next_cursor: null });
    }
    if (path === "/decisions/conflicts") return json(route, { items: [] });
    const record = path.match(/^\/records\/([^/]+)$/);
    if (record) {
      const s = studies.find((x) => x.study_id === record[1])!;
      const mine = decided.get(s.study_id) ?? null;
      return json(route, { ...s, year: 2024, venue: null, doi: null, batch_index: 1, highlights: [], criteria, binding: BINDING, my_decision: mine, history: mine ? [mine] : [] });
    }
    if (path === "/decisions/events" && method === "POST") {
      const events = (route.request().postDataJSON() as { events: Record<string, unknown>[] }).events;
      for (const e of events) decided.set(String(e.study_id), { ...e, received_at: "2026-11-07T10:00:00Z", token_scope: "desktop", changed_after_reveal: false });
      return json(route, { results: events.map((e) => ({ event_id: e.event_id, result: "accepted" })) });
    }
    return json(route, { detail: { code: "NOT_FOUND", message: path } }, 404);
  });
  return decided;
}

test.use({ viewport: DESKTOP_VIEWPORT });

test("ten records decided by keyboard, at most ten keypresses each", async ({ page }) => {
  const decided = await engine(page);
  await page.goto("/en/screening/triage");
  await expect(page.locator("[data-position]")).toHaveText("Record 1 of 10 · batch 1");
  let keypresses = 0;
  for (let i = 1; i <= N; i += 1) {
    // The position line appears once the record itself is loaded, not only its queue row.
    await expect(page.locator("[data-position]")).toHaveText(`Record ${i} of 10 · batch 1`);
    const before = decided.size;
    if (i % 2 === 1) {
      // Include: INC-01 yes (1), then I.
      for (const key of ["1", "i"]) {
        await page.keyboard.press(key);
        keypresses += 1;
      }
    } else {
      // Exclude with the reason from the checklist: INC-01 no (2), then E, then Enter.
      for (const key of ["2", "e", "Enter"]) {
        await page.keyboard.press(key);
        keypresses += 1;
      }
    }
    await expect.poll(() => decided.size).toBe(before + 1);
    if (i < N) {
      // Focus lands on the next record's title (spec 03 amendment 3).
      await expect(page.locator("article p[tabindex='-1']")).toBeFocused();
    }
  }
  expect(keypresses / N).toBeLessThanOrEqual(10);
  await expect(page.getByRole("heading", { name: "All 10 records are decided" })).toBeVisible();
  const excluded = [...decided.values()].filter((e) => e.outcome === "EXCLUDE");
  expect(excluded).toHaveLength(5);
  expect(excluded.every((e) => e.reason_code === "FAILS-INC-01")).toBe(true);
});

for (const width of [1440, 1024]) {
  test(`the queue is collapsed to the current and next titles at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await engine(page);
    await page.goto("/en/screening/triage");
    const queue = page.locator("[data-queue-collapsed]");
    await expect(queue).toContainText("Record number 1");
    await expect(queue).toContainText("Record number 2");
    await expect(queue).not.toContainText("Record number 3");
    await page.getByRole("button", { name: /^Queue/ }).click();
    await expect(page.getByRole("button", { name: /^Queue/ })).toHaveAttribute("aria-expanded", "true");
    await expect(page.locator("#triage-queue-list")).toContainText("Record number 10");
  });
}

// The real protocol's shape: seven criteria with long texts, and an IEEE-length abstract (M8-triage).
const LONG_CRITERIA = [
  { id: "INC-01", text: "Uses UAV-acquired imagery for crop/weed detection, segmentation, classification, or spatial weed mapping in an agricultural context (arable row crops, broadacre cereals, vegetables, or managed perennial orchards, vineyards, and pastures); UAV results must be separable in mixed-platform studies.", kind: "inclusion" },
  { id: "INC-02", text: "Primary empirical method study or dataset/benchmark paper with original quantitative results on UAV imagery.", kind: "inclusion" },
  { id: "INC-03", text: "Published from 2020 through the recorded freeze date of the search.", kind: "inclusion" },
  { id: "EXC-01", text: "Satellite-only, ground-robot-only, or handheld-camera-only imagery with no UAV component.", kind: "exclusion" },
  { id: "EXC-02", text: "UAV navigation/SLAM, yield estimation only, or spraying hardware without a weed or crop mapping task.", kind: "exclusion" },
  { id: "EXC-03", text: "Confirmed review, survey, editorial, or position paper.", kind: "exclusion" },
  { id: "EXC-04", text: "Outside the frozen publication date range.", kind: "exclusion" },
];
const LONG_ABSTRACT = Array.from({ length: 12 }, () =>
  "In this study, the components of olive trees were determined from images taken by an unmanned aerial vehicle over a commercial grove, using local extrema and multiresolution segmentation; crown borders, crown areas and tree heights were compared with terrestrial measurements and reached high overall accuracy.",
).join(" ");

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 1280, height: 720 },
]) {
  test(`one screen at ${viewport.width}x${viewport.height}: the page never scrolls, the record pane does`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await engine(page, { abstract: LONG_ABSTRACT, criteria: LONG_CRITERIA });
    await page.goto("/en/screening/triage");
    await expect(page.locator("[data-position]")).toHaveText("Record 1 of 10 · batch 1");
    const fits = () => page.evaluate(() => document.documentElement.scrollHeight <= window.innerHeight);
    expect(await fits(), "closed checklist").toBe(true);
    // The abstract scrolls inside its own pane.
    const pane = page.locator("[data-record-pane]");
    expect(await pane.evaluate((el) => el.scrollHeight > el.clientHeight)).toBe(true);
    // The decision bar is on screen, whole.
    const bar = await page.locator("[data-decision-bar]").boundingBox();
    expect(bar && bar.y + bar.height <= viewport.height).toBe(true);
    // Opened by a number key, and with the reason panel too, the page still does not scroll.
    await page.keyboard.press("2");
    await expect(page.getByRole("group", { name: "INC-01" })).toBeVisible();
    expect(await fits(), "open checklist").toBe(true);
    await page.keyboard.press("e");
    await expect(page.locator("[data-reason]")).toBeVisible();
    expect(await fits(), "reason panel open").toBe(true);
  });
}

// The focus screen (decision 2026-11-09): from 1024 px the site header, step bar and footer give way to the triage bar.
for (const { width, focus } of [
  { width: 1440, focus: true },
  { width: 800, focus: false },
]) {
  test(`at ${width} px the site header is ${focus ? "hidden behind the triage bar" : "shown"}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await engine(page);
    await page.goto("/en/screening/triage");
    await expect(page.locator("[data-position]")).toHaveText("Record 1 of 10 · batch 1");
    await expect(page.getByRole("banner")).toHaveCount(focus ? 0 : 1);
    await expect(page.getByRole("heading", { level: 1 })).toHaveAccessibleName(focus ? "Triage" : "Is this record in scope?");
    if (focus) {
      const leave = page.getByRole("link", { name: "Leave triage" });
      for (let i = 0; i < 12 && !(await leave.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
      await expect(leave).toBeFocused();
    }
  });
}

test("Include by I alone, and Exclude by E, a chip number and Enter, with no answers sent", async ({ page }) => {
  const decided = await engine(page);
  await page.goto("/en/screening/triage");
  await expect(page.locator("[data-position]")).toHaveText("Record 1 of 10 · batch 1");
  await page.keyboard.press("i");
  await expect.poll(() => decided.size).toBe(1);
  await expect(page.locator("[data-position]")).toHaveText("Record 2 of 10 · batch 1");
  for (const key of ["e", "2", "Enter"]) await page.keyboard.press(key);
  await expect.poll(() => decided.size).toBe(2);
  const events = [...decided.values()];
  expect(events.map((e) => [e.outcome, e.reason_code ?? null, e.criteria])).toEqual([
    ["INCLUDE", null, []],
    ["EXCLUDE", "FAILS-INC-01", []],
  ]);
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
  test(`${locale}: axe finds no violation on triage, with a reason panel open, contrast included`, async ({ page }) => {
    await engine(page);
    await page.goto(`/${locale}/screening/triage`);
    await expect(page.locator("[data-position]")).toBeVisible();
    await page.keyboard.press("2");
    await page.keyboard.press("e");
    await expect(page.locator("[data-reason]")).toBeVisible();
    const result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
  });
}
