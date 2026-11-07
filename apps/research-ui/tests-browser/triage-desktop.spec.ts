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

async function engine(page: Page) {
  const decided = new Map<string, Record<string, unknown>>();
  const studies = Array.from({ length: N }, (_, i) => ({ study_id: `STU-${i + 1}`, title: `Record number ${i + 1}`, abstract: `Abstract ${i + 1} about drones.` }));
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
      return json(route, { ...s, year: 2024, venue: null, doi: null, batch_index: 1, highlights: [], criteria: CRITERIA, binding: BINDING, my_decision: mine, history: mine ? [mine] : [] });
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
    await page.getByRole("button", { name: "Show the whole queue" }).click();
    await expect(page.getByRole("button", { name: "Hide the queue" })).toHaveAttribute("aria-expanded", "true");
    await expect(page.locator("#triage-queue-list")).toContainText("Record number 10");
  });
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
