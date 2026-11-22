import { createRequire } from "node:module";
import { join } from "node:path";

import type { Page, Route } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * The criteria pilot (spec 13, M11b part C) in a real browser: Triage in the pilot view, the
 * result with its revise and end dialogs, and a record shown again after a revision. The console
 * proxy is answered by a small stateful fake with the engine's shapes; the engine is covered by
 * the Python suite. No provider is reached.
 */

const CRITERIA = [
  { id: "INC-01", text: "Uses UAV-acquired imagery", kind: "inclusion", side: "inclusion" },
  { id: "EXC-01", text: "Not a crop field", kind: "exclusion", side: "exclusion" },
];
const BINDING = { protocol_fingerprint: "sha256:p", batch_id: "batch-1", batch_sha256: "sha256:b", criteria_version: 1 };
const N = 3;

type Sent = { method: string; path: string; body: Record<string, unknown> | null };

async function engine(page: Page, options: { open?: boolean; recheck?: boolean } = {}) {
  const sent: Sent[] = [];
  const studies = Array.from({ length: N }, (_, i) => ({ study_id: `STU-${i + 1}`, title: `Pilot record ${i + 1}`, abstract: `Abstract ${i + 1} about drones over maize.` }));
  const pilot = new Map<string, Record<string, unknown>>();
  const main = new Map<string, Record<string, unknown>>();
  let open = options.open ?? true;
  let closedReason: string | null = open ? null : "complete";
  let version = 1;
  const amendments: Record<string, unknown>[] = [];
  const earlier = {
    event_id: "EV-old", study_id: "STU-1", screener_id: "researcher:local", method: "HUMAN", outcome: "EXCLUDE", reason_code: "EXC-01",
    criteria: [{ id: "EXC-01", answer: "yes" }], note: null, supersedes: null, binding: BINDING, proposal_shown: null,
    decided_at: "2026-11-20T10:00:00Z", received_at: "2026-11-20T10:00:00Z", token_scope: "desktop", changed_after_reveal: false, criteria_version: 1,
  };
  const shownAgain = (id: string) => Boolean(options.recheck) && id === "STU-1" && !main.has(id);
  const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, json: body });
  const result = () => {
    const decisions = [...pilot.values()];
    const count = (o: string) => decisions.filter((d) => d.outcome === o).length;
    const excludes = count("EXCLUDE");
    return {
      pilot_id: "pilot_001", n: N, decided: decisions.length, open, closed_at: open ? null : "2026-11-21T10:00:00Z", closed_reason: closedReason,
      seed: 4242, drawn_at: "2026-11-21T09:00:00Z", snapshot_id: "SNAP-1", protocol_fingerprint: "sha256:p",
      criteria_version_drawn: 1, criteria_versions_decided: [1], criteria_version: version, counted: false,
      by_outcome: { INCLUDE: count("INCLUDE"), MAYBE: count("MAYBE"), EXCLUDE: excludes },
      criteria: CRITERIA.map((c) => ({ id: c.id, side: c.side, text: c.text, retired: false, exclusions: { count: 0, of: excludes }, checklist_not_reported: null, draft_not_reported: null, read_differently: null })),
      drafts: { records: 0, of: decisions.length }, checklist: { records: 0, of: decisions.length },
      observations: [],
      not_computed: [
        { kind: "hard_to_judge", needs: ["agent_check", "checklist"] },
        { kind: "fire_together", needs: ["agent_check", "checklist"] },
        { kind: "mirrored_pair", needs: ["agent_check"] },
        { kind: "read_differently", needs: ["agent_check"] },
      ],
      records: studies.filter((s) => pilot.has(s.study_id)).map((s) => ({ study_id: s.study_id, title: s.title, outcome: pilot.get(s.study_id)!.outcome, reason_code: pilot.get(s.study_id)!.reason_code ?? null, criteria_version: 1 })),
      previous: null,
    };
  };
  await page.route("**/api/console/api/v1/screening/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname.replace("/api/console/api/v1/screening", "");
    const method = req.method();
    const body = req.postData() ? (JSON.parse(req.postData()!) as Record<string, unknown>) : null;
    sent.push({ method, path, body });
    if (path === "/settings") return json(route, { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: "next_at_once" });
    if (path === "/summary") {
      return json(route, {
        total: N, decided: main.size, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: N - main.size, conflicts: 0,
        lanes: { agent: 0, you: main.size, second_screener: "PARKED" }, protocol_changed: false, criteria_version: version,
        recheck: studies.filter((s) => shownAgain(s.study_id)).length,
        pilot: { pilot_id: "pilot_001", n: N, decided: pilot.size, open, closed_at: null, closed_reason: closedReason, pilots: 1, recheck: 0 },
      });
    }
    if (path === "/criteria") {
      return json(route, {
        criteria_version: version, criteria: CRITERIA.map((c) => ({ id: c.id, side: c.side, text: c.text, reason_category: null, since_version: 1 })),
        retired: [], amendments, can_amend: true, batches_prepared: true, batch_approved: false, handoff_batches: [],
      });
    }
    if (path === "/proposals/setup") {
      return json(route, { task: { task_version: "v1", prompt_sha256: "x", model: "claude-opus-5-5", effort: "low" }, providers: [{ provider: "anthropic", key: "none", consent: null }], data_flow: "titles and abstracts", active_run: null, latest_run: null, last_model: null });
    }
    if (path === "/proposals/runs" && method === "POST") return json(route, { detail: { code: "PROVIDER_KEY_MISSING", message: "no key" } }, 409);
    if (path === "/queue") {
      const view = url.searchParams.get("view");
      if (view === "pilot") {
        const items = studies.map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", batch_index: 1, has_proposal: false, decided: pilot.has(s.study_id), flags: [], shown_again: false, pilot_decision: pilot.get(s.study_id) ?? null }));
        return json(route, { items, next_cursor: null, pilot: { pilot_id: "pilot_001", open }, checklist_default: "collapsed" });
      }
      const items = studies
        .map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", batch_index: 1, has_proposal: false, decided: main.has(s.study_id), flags: [], shown_again: shownAgain(s.study_id) }))
        .filter((i) => (view === "decided" ? i.decided : !i.decided));
      return json(route, { items, next_cursor: null });
    }
    if (path === "/decisions/conflicts") return json(route, { items: [] });
    const record = path.match(/^\/records\/([^/]+)$/);
    if (record) {
      const s = studies.find((x) => x.study_id === record[1])!;
      const mine = main.get(s.study_id) ?? null;
      return json(route, {
        ...s, year: 2024, venue: null, doi: null, batch_index: 1, highlights: [], criteria: CRITERIA, binding: { ...BINDING, criteria_version: version },
        my_decision: mine, history: mine ? [mine] : [], criteria_version: version,
        shown_again: shownAgain(s.study_id) ? { decision: earlier, criteria_version: 1 } : null,
      });
    }
    if (path === "/pilot/pilot_001/decisions" && method === "POST") {
      const decisions = (body!.decisions as Record<string, unknown>[]) ?? [];
      for (const d of decisions) pilot.set(String(d.study_id), { pilot_decision_id: `PLD-${d.event_id}`, outcome: d.outcome, reason_code: d.reason_code ?? null, criteria: d.criteria ?? null, criteria_version: 1 });
      if (pilot.size === N) {
        open = false;
        closedReason = "complete";
      }
      return json(route, { results: decisions.map((d) => ({ event_id: d.event_id, result: "accepted", pilot_decision_id: `PLD-${d.event_id}` })), pilot: { pilot_id: "pilot_001", n: N, decided: pilot.size, open, closed_at: null, closed_reason: closedReason } });
    }
    if (path === "/pilot/pilot_001/close" && method === "POST") {
      open = false;
      closedReason = "ended";
      return json(route, { pilot_id: "pilot_001", n: N, decided: pilot.size, open: false, closed_at: "x", closed_reason: "ended" });
    }
    if (path === "/pilot/pilot_001/result") return json(route, result());
    if (path === "/criteria/amendments" && method === "POST") {
      const answer = { recorded: Boolean(body?.confirm), op: body?.op, side: body?.side, new_ids: [], retired_ids: [], criteria_version_before: version, criteria_version_after: version + 1, decided: 0, shown_again: { INCLUDE: 0, MAYBE: 0, EXCLUDE: 0, total: 0 }, waiting_after: 0 };
      if (body?.confirm) {
        version += 1;
        amendments.push({ amendment_id: "CRA-1", op: body.op, side: body.side, from: [CRITERIA[1]], to: [{ ...CRITERIA[1], text: body.text }], reason: body.reason, criteria_version_before: 1, criteria_version_after: version, pilot_id: "pilot_001", decided_at_time: 0, shown_again: answer.shown_again, amended_by: "researcher:local", amended_at: "2026-11-21T11:00:00Z" });
      }
      return json(route, answer);
    }
    if (path === "/decisions/events" && method === "POST") {
      const events = (body!.events as Record<string, unknown>[]) ?? [];
      for (const e of events) main.set(String(e.study_id), { ...e, received_at: "2026-11-21T12:00:00Z", token_scope: "desktop", changed_after_reveal: false, criteria_version: version });
      return json(route, { results: events.map((e) => ({ event_id: e.event_id, result: "accepted" })) });
    }
    return json(route, { detail: { code: "NOT_FOUND", message: path } }, 404);
  });
  return { sent, pilot, main };
}

/**
 * `M11B_SHOTS=<folder>` also writes the screenshots looked at for the build record (English, light
 * theme, 1440 by 900); nothing is written into the repository.
 */
async function shot(page: Page, name: string, project: string) {
  const folder = process.env.M11B_SHOTS;
  if (!folder || project !== "chromium") return;
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({ path: join(folder, `${name}.png`) });
}

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[] }> } }).axe;
    const raw = await run.run(document);
    return raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`);
  });
}

test.use({ viewport: DESKTOP_VIEWPORT });

test("the pilot decided by keyboard goes to the pilot route only, then hands off to its result", async ({ page }, info) => {
  const { sent, pilot, main } = await engine(page);
  await page.goto("/en/screening/triage?view=pilot");
  await expect(page.getByRole("region", { name: "Pilot" })).toContainText("Pilot · 0 of 3 decided");
  await expect(page.locator("[data-position]")).toHaveText("Pilot record 1 of 3");
  await shot(page, "2-triage-pilot-view", info.project.name);
  for (let i = 1; i <= N; i += 1) {
    await expect(page.locator("[data-position]")).toHaveText(`Pilot record ${i} of 3`);
    await page.keyboard.press("i");
    await expect.poll(() => pilot.size).toBe(i);
  }
  expect(main.size).toBe(0);
  expect(sent.filter((s) => s.path === "/decisions/events")).toHaveLength(0);
  await expect(page.getByRole("heading", { name: "The pilot is decided: 3 of 3" })).toBeVisible();
  await page.getByRole("link", { name: "See the pilot result" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("The pilot is decided: 3 of 3 records.");
  await expect(page.locator("[data-not-computed]")).toContainText("Four readings need answers per criterion");
});

for (const width of [1440, 1280]) {
  test(`at ${width} px: the result, a revision recorded through its dry call, and axe clean`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const { sent } = await engine(page, { open: false });
    await page.goto("/en/screening/pilot?id=pilot_001");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(await axe(page)).toEqual([]);
    if (width === 1440) await shot(page, "4-pilot-result", info.project.name);
    await page.getByRole("button", { name: "Revise a criterion" }).click();
    const dialog = page.getByRole("dialog", { name: "Revise a criterion" });
    await dialog.getByRole("radio", { name: "Reword · same test, clearer words" }).check();
    await dialog.locator("select").first().selectOption("EXC-01");
    await dialog.locator("textarea").first().fill("Not an arable crop field");
    await dialog.getByLabel("Why are you making this change? One sentence.").fill("Orchards were read two ways");
    expect(await axe(page)).toEqual([]);
    if (width === 1440) await shot(page, "5-revise-dialog", info.project.name);
    await dialog.getByRole("button", { name: "Check what this changes" }).click();
    const confirm = page.getByRole("alertdialog", { name: "Record this revision?" });
    await expect(confirm).toContainText("No record will be shown again.");
    expect(sent.filter((s) => s.path === "/criteria/amendments").map((s) => s.body?.confirm)).toEqual([false]);
    await confirm.getByRole("button", { name: "Record the revision" }).click();
    await expect(page.locator("[data-revision-notice]")).toContainText("Criteria version 2 recorded");
    await expect(page.locator("[data-revision-notice]")).toBeFocused();
    expect(sent.filter((s) => s.path === "/criteria/amendments").map((s) => s.body?.confirm)).toEqual([false, true]);
  });
}

test("ending an open pilot asks first, then the result reads ended and the records wait in the main queue", async ({ page }) => {
  const { sent } = await engine(page);
  await page.goto("/en/screening/pilot?id=pilot_001");
  await page.getByRole("button", { name: "End the pilot" }).click();
  const dialog = page.getByRole("alertdialog", { name: "End the pilot?" });
  await expect(dialog.getByRole("button", { name: "Not now" })).toBeFocused();
  expect(await axe(page)).toEqual([]);
  await dialog.getByRole("button", { name: "End the pilot" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Pilot ended: 0 of 3 decided.");
  expect(sent.filter((s) => s.path === "/pilot/pilot_001/close")).toHaveLength(1);
  await page.getByRole("link", { name: "Screen the rest" }).click();
  await expect(page.locator("[data-position]")).toHaveText(/^Record 1 of 3/);
  await expect(page.locator("[data-pilot-banner]")).toHaveCount(0);
  await expect(page.locator("[data-earlier-decision]")).toHaveCount(0);
});

test("a record shown again shows the earlier decision beside it and is decided again", async ({ page }, info) => {
  const { sent } = await engine(page, { open: false, recheck: true });
  await page.goto("/en/screening/triage");
  await expect(page.locator("[data-recheck-banner]")).toContainText("1 records are shown again because criteria changed");
  const earlier = page.locator("[data-earlier-decision]");
  await expect(earlier).toContainText("Your decision under the earlier wording (version 1)");
  expect(await axe(page)).toEqual([]);
  await shot(page, "3-record-shown-again", info.project.name);
  await page.keyboard.press("i");
  await expect.poll(() => sent.filter((s) => s.path === "/decisions/events").length).toBe(1);
  const event = (sent.find((s) => s.path === "/decisions/events")!.body!.events as Record<string, unknown>[])[0];
  expect(event).toMatchObject({ study_id: "STU-1", outcome: "INCLUDE", supersedes: "EV-old" });
});

test("screenshots only: Prepare with the pilot card", async ({ page }, info) => {
  test.skip(!process.env.M11B_SHOTS || info.project.name !== "chromium", "screenshots only (M11B_SHOTS)");
  await engine(page, { open: false });
  // Prepare reads its own two answers; the pilot card reads the pilot fake's summary and criteria.
  await page.route("**/api/console/api/v1/screening/settings", (route) =>
    route.fulfill({ json: { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: "show_draft_then_next", not_reported_policy: "unclear", not_reported_source: "protocol", method_amendments: [] } }),
  );
  await page.route("**/api/console/api/v1/screening/ui/batches", (route) =>
    route.fulfill({ json: { shape: "ui07.screening-batches-v1", run_id: null, count: 1, batches: [{ batch_index: 1, batch_file: "batch_001.json", items: 3, decisions_file: null, decisions_count: null, collected: false, coverage: "INCOMPLETE", unresolved_rows: [] }], missing: [] } }),
  );
  await page.route("**/api/console/api/v1/screening/summary", (route) =>
    route.fulfill({ json: { total: 1062, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 1062, conflicts: 0, lanes: { agent: 0, you: 0, second_screener: "PARKED" }, protocol_changed: false, criteria_version: 1, recheck: 0, pilot: null } }),
  );
  await page.goto("/en/screening/prepare");
  await expect(page.getByRole("button", { name: "Draw a pilot of 50" })).toBeVisible();
  await page.locator("[data-pilot-card]").scrollIntoViewIfNeeded();
  await shot(page, "1-prepare-pilot-card", info.project.name);
});
