import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * The Charting view, the form panel and the one-study view (M12a Part B, specs
 * 01 and 02, DoD 14) in a real browser on the production build. As in the other
 * specs of this suite the console is answered at the network boundary by a small
 * stateful fake in the engine's shapes (`tests/console/test_charting_form_api.py`):
 * the table with its form and cells, the one-study read, cell events with undo,
 * the form's PUT (a reason once a value exists, recorded as an amendment) and
 * "End pilot". It runs in light (`chromium`) and dark (`chromium-dark`).
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

type Cell = { state: string | null; value: unknown; note: string | null; where_from: string | null; pilot: boolean; chart_again: boolean; history: unknown[]; event_id: string | null; form_version: number | null };
type Column = { column_id: string; name: string; definition: string; type: string; options: string[]; required: boolean; from_protocol: string | null; derived_from: string[] };
type Row = Record<string, unknown> & { study_id: string; kept: boolean; fulltext: Record<string, unknown> & { status: string }; ft_decision: { outcome: string } | null; heads: Record<string, string | null>; cells: Record<string, Cell>; charted: boolean; pilot: boolean; no_full_text: boolean };

const TITLES = ["Weed mapping from UAV imagery", "Deep learning for crop rows", "Multispectral drone survey", "Sugar beet weed detection", "Herbicide spot spraying", "Thermal imaging of maize", "Cross-camera transfer"];

function columns(): Column[] {
  const c = (column_id: string, name: string, type: string, options: string[] = [], definition = ""): Column => ({ column_id, name, definition, type, options, required: false, from_protocol: column_id, derived_from: [] });
  return [
    c("sensor_problems", "Sensor problems addressed", "several", ["Misregistration", "Missing band", "Change of camera"], "Misregistration, missing band, change of camera"),
    c("cameras", "Cameras and evaluation design", "text", [], "Cameras, splits, cross-camera tests"),
    c("n_images", "Images", "number", [], "Number of images"),
    c("split", "Data split", "one", ["Random tiles", "By field", "By date"], "How the data are split"),
    c("cross_camera", "Test camera absent from training", "yes_no", ["Yes", "No"]),
  ];
}

const empty = (): Cell => ({ state: null, value: null, note: null, where_from: null, pilot: false, chart_again: false, history: [], event_id: null, form_version: null });

function row(i: number, cols: Column[]): Row {
  return {
    study_id: `STU-${String(i).padStart(3, "0")}`,
    title: TITLES[(i - 1) % TITLES.length] + (i > TITLES.length ? ` ${i}` : ""),
    authors: ["Sa, I.", "Popović, M."],
    year: 2017 + (i % 7),
    venue: "Remote Sensing",
    doi: `10.3390/rs${1000 + i}`,
    url: null,
    abstract: `Study ${i}. We mapped weeds in sugar beet fields from UAV images taken with a RedEdge-M multispectral camera; 1,260 images were split by field.`,
    arxiv_id: null,
    round: 1,
    arm: "databases",
    round_label: "Databases",
    generation_id: "gen-1",
    ta_decision: i % 3 === 0 ? "MAYBE" : "INCLUDE",
    ta_reason: "",
    kept: true,
    new_since: null,
    fulltext: { status: "to_get", requested_on: null, reason: null, reason_text: null, attachment: null, link: null },
    ft_decision: null,
    heads: { fulltext_status: null, fulltext_decision: null, attachment: null, link: null },
    cells: Object.fromEntries(cols.map((c) => [c.column_id, empty()])),
    charted: false,
    pilot: false,
    no_full_text: true,
  };
}

async function engine(page: Page, size = 7) {
  const form = { schema: "nexus.charting-form.v1", version: 1, columns: columns(), pilot: { on: true, ended_at: null as string | null, ended_by: null as string | null }, amendments: [] as Record<string, unknown>[], has_values: false };
  const rows = Array.from({ length: size }, (_, i) => row(i + 1, form.columns));
  const posted: Record<string, unknown>[][] = [];
  const derive = (r: Row) => {
    r.charted = r.kept && r.ft_decision?.outcome !== "EXCLUDE" && form.columns.every((c) => r.cells[c.column_id]?.state != null && !r.cells[c.column_id]?.chart_again);
    r.pilot = Object.values(r.cells).some((c) => c.pilot);
    r.no_full_text = r.fulltext.status !== "retrieved";
  };
  const counts = () => {
    const live = rows.filter((r) => r.kept);
    const by = (test: (r: Row) => boolean) => live.filter(test).length;
    return {
      kept: live.length, to_get: by((r) => r.fulltext.status === "to_get"), requested: by((r) => r.fulltext.status === "requested"),
      retrieved: by((r) => r.fulltext.status === "retrieved"), not_retrieved: by((r) => r.fulltext.status === "not_retrieved"),
      included: by((r) => r.ft_decision?.outcome === "INCLUDE"), excluded: by((r) => r.ft_decision?.outcome === "EXCLUDE"), to_decide: by((r) => !r.ft_decision),
      charted: by((r) => r.charted), not_charted: by((r) => !r.charted && r.ft_decision?.outcome !== "EXCLUDE"), pilot: by((r) => r.pilot),
    };
  };
  const table = () => ({
    shape: "charting.table-v1", screener_id: "researcher:local",
    publication: { status: "CURRENT", code: null, generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z", round: 1 },
    rounds: [{ round: 1, arm: "databases", generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z" }],
    chasing_pending: false, stale: false, changes: null, read_only: false, read_only_code: null,
    reason_options: [
      { code: "EXC-01", label: "Not a crop field", kind: "exclusion", category: null },
      { code: "OTHER", label: "Other", kind: "other", category: null },
    ],
    not_retrieved_reasons: ["no_access", "not_found", "no_reply", "other"],
    counts: counts(), form, rows,
  });
  await page.route("**/api/console/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace("/api/console/api/v1", "");
    const method = request.method();
    if (path === "/charting" && method === "GET") return route.fulfill({ json: table() });
    const record = /^\/charting\/records\/([^/]+)$/.exec(path);
    if (record && method === "GET") {
      const found = rows.find((r) => r.study_id === record[1]);
      if (!found) return route.fulfill({ status: 409, json: { detail: { code: "RECORD_NOT_KEPT", message: "" } } });
      const t = table();
      return route.fulfill({ json: { shape: "charting.record-v1", row: found, form, read_only: false, reason_options: t.reason_options, not_retrieved_reasons: t.not_retrieved_reasons, publication: t.publication, counts: t.counts } });
    }
    if (path === "/charting/events" && method === "POST") {
      const events = (request.postDataJSON() as { events: { event_id: string; study_id: string; kind: string; value: Record<string, unknown> | null; note?: string; where_from?: string }[] }).events;
      posted.push(events);
      const results = events.map((event) => {
        const target = rows.find((r) => r.study_id === event.study_id)!;
        if (event.kind === "cell") {
          const v = event.value as { column_id: string; state: string | null; value: unknown };
          const before = target.cells[v.column_id];
          target.cells[v.column_id] = {
            state: v.state, value: v.state === "value" ? v.value : null, note: v.state ? event.note ?? null : null, where_from: v.state ? event.where_from ?? null : null,
            pilot: v.state !== null && form.pilot.on, chart_again: false,
            history: before.state !== null ? [...before.history, { ...before, at: null }] : before.history, event_id: event.event_id, form_version: form.version,
          };
          if (v.state !== null) form.has_values = true;
        } else if (event.kind === "fulltext_status") {
          target.fulltext = { ...target.fulltext, status: String((event.value ?? { status: "to_get" }).status) };
          target.heads = { ...target.heads, fulltext_status: event.event_id };
        } else if (event.kind === "fulltext_decision") {
          target.ft_decision = event.value ? { outcome: String(event.value.outcome) } : null;
          target.heads = { ...target.heads, fulltext_decision: event.event_id };
        }
        derive(target);
        return { event_id: event.event_id, result: "accepted" };
      });
      const touched = new Set(events.map((e) => e.study_id));
      return route.fulfill({ json: { results, counts: counts(), rows: rows.filter((r) => touched.has(r.study_id)) } });
    }
    if (path === "/charting/form" && method === "PUT") {
      const body = request.postDataJSON() as { base_version: number; columns: Column[]; reason?: string };
      if (body.base_version !== form.version) return route.fulfill({ status: 409, json: { detail: { code: "CHARTING_FORM_STALE", message: "" } } });
      if (form.has_values && !body.reason) return route.fulfill({ status: 422, json: { detail: { code: "CHARTING_AMENDMENT_REASON_REQUIRED", message: "" } } });
      const old = new Map(form.columns.map((c) => [c.column_id, c]));
      const version = form.version + 1;
      if (form.has_values) {
        for (const c of body.columns) {
          const was = old.get(c.column_id);
          if (was && was.name !== c.name) form.amendments.push({ amendment_id: `amd_${version}`, change: "renamed", column_id: c.column_id, from: was.name, to: c.name, reason: body.reason, pilot: form.pilot.on, amended_by: "researcher:local", amended_at: "2026-11-21T14:32:00Z", form_version_to: version });
        }
      }
      form.columns = body.columns.map((c) => ({ ...c, options: c.type === "yes_no" ? ["Yes", "No"] : c.options }));
      form.version = version;
      return route.fulfill({ json: form });
    }
    if (path === "/charting/form/pilot/end" && method === "POST") {
      form.pilot = { on: false, ended_at: "2026-11-21T15:00:00Z", ended_by: "researcher:local" };
      return route.fulfill({ json: form });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  return { posted, rows, form };
}

async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
    const raw = await run.run(document);
    return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
  });
}

const position = (page: Page) => page.locator("[data-position]");

test("chart five studies from the abstract by keyboard, then undo the last change", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const { posted, rows } = await engine(page);
  await page.goto("/en/charting?view=charting");
  await expect(page.locator("[data-counts]")).toContainText("0 charted");
  // Enter on the study cell opens the one-study view.
  await page.locator('[data-cell="STU-001:0"]').click({ position: { x: 4, y: 4 } });
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/en\/charting\/study\?view=charting&id=STU-001/);
  for (let k = 1; k <= 5; k += 1) {
    await expect(position(page)).toHaveText(`Study ${k} of 7`);
    await expect(page.locator("[data-from-abstract]")).toContainText("Charting from the abstract.");
    // The focus is on the first field: tick the first option, Enter saves it and moves to the next field.
    await expect(page.locator('[data-field="sensor_problems"] input').first()).toBeFocused();
    await page.keyboard.press("Space");
    await page.keyboard.press("Enter");
    await expect(page.locator('[data-field="cameras"] [data-value-input]')).toBeFocused();
    await page.keyboard.type(`RedEdge-M, study ${k}`);
    await page.keyboard.press("Enter");
    await expect(page.locator('[data-field="n_images"] [data-value-input]')).toBeFocused();
    await page.keyboard.type(String(1000 + k));
    await page.keyboard.press("Enter");
    // Data split: not reported in this abstract.
    await expect(page.locator('[data-field="split"] input').first()).toBeFocused();
    await page.keyboard.press("Alt+N");
    await expect(page.locator('[data-field="split"] [data-special="not_reported"]')).toHaveAttribute("aria-pressed", "true");
    await page.locator('[data-field="cross_camera"] input').first().focus();
    await page.keyboard.press("Alt+A");
    await expect(page.locator('[data-field="cross_camera"] [data-special="not_applicable"]')).toHaveAttribute("aria-pressed", "true");
    // Ctrl+Down saves and opens the next study.
    await page.keyboard.press("Control+ArrowDown");
    if (k < 5) await expect(page.locator("[data-announce]")).toHaveText(`Study ${k + 1} of 7. Saved.`);
  }
  await expect(position(page)).toHaveText("Study 6 of 7");
  expect(rows.slice(0, 5).every((r) => r.charted)).toBe(true);
  expect(posted.flat().filter((e) => e.kind === "cell")).toHaveLength(25);
  // Undo the last change (study 5, the Yes/No field) from outside a field.
  // The move to study 6 puts the focus on its first field once the study has loaded; wait for that,
  // or it lands after the focus below and the key is typed inside a field, where it does nothing.
  await expect(page.locator('[data-field="sensor_problems"] input').first()).toBeFocused();
  await page.locator("[data-region=study]").focus();
  await page.keyboard.press("z");
  await expect(page.locator("[data-announce]")).toHaveText("Undone");
  expect(rows[4].cells.cross_camera.state).toBeNull();
  // Esc goes back to the table on this study's row.
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/en\/charting\?view=charting&row=STU-006/);
  await expect(page.locator("[data-counts]")).toContainText("4 charted");
  await expect(page.locator('[data-cell="STU-006:0"]')).toBeFocused();
});

test("in-cell editing in the Charting view, then a form amendment with its reason", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const { form } = await engine(page);
  await page.goto("/en/charting?view=charting");
  await page.locator('[data-cell="STU-001:2"]').click();
  await page.keyboard.press("Enter");
  await page.keyboard.type("Sequoia");
  await page.keyboard.press("Enter");
  await expect(page.locator('[data-cell="STU-001:2"]')).toHaveText("Sequoia");
  await expect(page.locator('[data-cell="STU-002:2"]')).toBeFocused();
  await page.keyboard.press("Alt+N");
  await expect(page.locator('[data-cell="STU-002:2"]')).toContainText("Not reported");
  // The form panel: a rename after a value waits for one sentence.
  await page.keyboard.press("f");
  const panel = page.getByRole("complementary", { name: "Charting form" });
  await expect(panel).toBeVisible();
  const name = panel.locator('[data-form-column="cameras"] [data-form-name]');
  await name.fill("Cameras");
  await name.blur();
  await expect(panel.locator("[data-amendment-prompt]")).toContainText("Why does the form change? One sentence.");
  await panel.getByRole("textbox", { name: "Why does the form change? One sentence." }).fill("A shorter name reads better in the table.");
  await panel.getByRole("button", { name: "Record the amendment" }).click();
  await expect(panel.locator("[data-amendment-line]")).toHaveText("Amended on 2026-11-21 by researcher:local: renamed, from “Cameras and evaluation design” to “Cameras”.");
  expect(form.version).toBe(2);
  await expect(page.locator("[role=grid] thead")).toContainText("Cameras");
  // Esc closes the panel and gives the focus back to the Form button.
  await panel.locator("[data-form-name]").first().focus();
  await page.keyboard.press("Escape");
  await expect(panel).toHaveCount(0);
  await expect(page.locator("[data-form-button]")).toBeFocused();
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: axe finds no violation on the Charting view with the form panel, and on the one-study view`, async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await engine(page);
    await page.goto(`/${locale}/charting?view=charting`);
    await page.locator('[data-cell="STU-001:1"]').click();
    await page.keyboard.press("Alt+N");
    await page.keyboard.press("f");
    await expect(page.locator("[data-form-panel]")).toBeVisible();
    let result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
    await page.goto(`/${locale}/charting/study?view=charting&id=STU-001`);
    await expect(page.locator("[data-field]").first()).toBeVisible();
    result = await axe(page);
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
    if (locale === "ar") {
      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      expect(await page.locator("[data-doi] span[dir=ltr]").evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
    }
  });
}

for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 720 }]) {
  test(`the one-study view does not scroll the page at ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await engine(page);
    await page.goto("/en/charting/study?view=charting&id=STU-001");
    await expect(page.locator("[data-field]").first()).toBeVisible();
    const sizes = await page.evaluate(() => ({ scroll: document.documentElement.scrollHeight, client: document.documentElement.clientHeight, wide: document.documentElement.scrollWidth - document.documentElement.clientWidth }));
    expect(sizes.scroll).toBeLessThanOrEqual(sizes.client);
    expect(sizes.wide).toBeLessThanOrEqual(0);
    // The two columns scroll inside themselves.
    for (const name of ["study", "form"]) {
      const overflow = await page.locator(`[data-region=${name}]`).evaluate((el) => getComputedStyle(el).overflowY);
      expect(overflow).toBe("auto");
    }
    await expect(page.locator("[data-study-status] [data-next-study]")).toBeInViewport();
  });
}

test("at 390 px: the list opens a study, which stacks with Previous and Next at the bottom", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await engine(page);
  await page.goto("/en/charting?view=charting");
  const card = page.locator("[data-phone-link]").first();
  await expect(card).toBeVisible();
  await card.click();
  await expect(page).toHaveURL(/\/en\/charting\/study\?view=charting&id=STU-001/);
  await expect(page.locator("[data-field]").first()).toBeVisible();
  const study = await page.locator("[data-region=study]").boundingBox();
  const form = await page.locator("[data-region=form]").boundingBox();
  expect(form!.y).toBeGreaterThan(study!.y + study!.height - 1);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  const next = page.locator("[data-next-study]");
  expect((await next.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await next.click();
  await expect(position(page)).toHaveText("Study 2 of 7");
});

test("DoD 14 in the browser: 150 rows by 5 columns, first draw and a walk of 60 cells within budget", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page, 150);
  const started = Date.now();
  await page.goto("/en/charting?view=charting");
  await expect(page.locator('[data-cell="STU-150:5"]')).toHaveCount(1);
  const firstDraw = Date.now() - started;
  await page.locator('[data-cell="STU-001:1"]').click();
  const moves = 60;
  const walk = Date.now();
  for (let i = 0; i < moves; i += 1) await page.keyboard.press(i % 10 === 9 ? "ArrowRight" : "ArrowDown");
  await expect(page.locator('[data-cell="STU-055:5"]')).toBeFocused();
  const perMove = (Date.now() - walk) / moves;
  console.log(`[DoD 14 browser] first draw ${firstDraw} ms (budget 3000, page load included); ${perMove.toFixed(1)} ms per key over ${moves} keys (budget 50, Playwright's round trip included)`);
  expect(firstDraw).toBeLessThan(3000);
  expect(perMove).toBeLessThan(50);
});

/**
 * `M12A_SHOTS=<folder>` writes the four screenshots shown to the researcher (en, light,
 * 1440x900): the Full text view, the Charting view with a cell being edited, the form
 * panel and the one-study view. Nothing is written into the repository; without the
 * switch the test is skipped.
 */
test("screenshots for the researcher (M12A_SHOTS)", async ({ page }, info) => {
  const shots = process.env.M12A_SHOTS;
  test.skip(!shots || info.project.name !== "chromium", "M12A_SHOTS names a folder; light theme only");
  const { join } = await import("node:path");
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page);
  // 1. The Full text view with rows in different states.
  await page.goto("/en/charting");
  const notNowFirst = page.getByRole("button", { name: "Not now" });
  if (await notNowFirst.count()) await notNowFirst.click();
  await page.locator("[role=grid] tbody tr").first().click();
  // One key at a time, each after the last save has answered.
  for (const key of ["r", "i", "j", "q", "j", "n", "1", "Enter", "j", "r", "e", "1", "Enter", "j", "j"]) {
    await page.keyboard.press(key);
    await page.waitForTimeout(350);
  }
  await page.screenshot({ path: join(shots!, "1-full-text.png") });
  // 2. The Charting view, two values saved and a third being typed.
  await page.goto("/en/charting?view=charting");
  const notNow = page.getByRole("button", { name: "Not now" });
  if (await notNow.count()) await notNow.click();
  await page.locator('[data-cell="STU-001:2"]').click();
  await page.keyboard.press("Enter");
  await page.keyboard.type("RedEdge-M and Sequoia; one model per camera");
  await page.keyboard.press("Enter");
  await page.keyboard.press("Alt+N");
  await page.locator('[data-cell="STU-003:2"]').click();
  await page.keyboard.press("Enter");
  await page.keyboard.type("Sequoia only");
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(shots!, "2-charting-editing.png") });
  await page.keyboard.press("Escape");
  // 3. The form panel open.
  await page.keyboard.press("f");
  await expect(page.getByRole("complementary", { name: "Charting form" })).toBeVisible();
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(shots!, "3-form-panel.png") });
  // 4. The one-study view.
  await page.goto("/en/charting/study?id=STU-001");
  await expect(page.locator("[data-position]")).toBeVisible();
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(shots!, "4-one-study.png") });
});
