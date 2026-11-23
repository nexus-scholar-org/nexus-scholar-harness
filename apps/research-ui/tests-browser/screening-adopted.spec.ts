import { createRequire } from "node:module";

import type { Page, Route } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * H-adopted-decisions-disclosure (DoD 6) in a real browser: the declaration screen offers the
 * engine's candidates, sends nothing until the reviewer confirms that they did not read the
 * records one by one, and then Agreement and Publish state it. The console proxy is answered by
 * a small stateful fake with the engine's shapes; the engine is covered by the Python suite
 * (`tests/console/test_adoption_declarations_api.py`). No provider is reached.
 */

type Sent = { method: string; path: string; body: Record<string, unknown> | null };

const OUTCOMES0 = { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 };
const CANDIDATES = [
  { event_id: "11111111-1111-4111-8111-111111111111", study_id: "STU-1", outcome: "EXCLUDE", note: "Adopted in bulk from the agent's draft; not reviewed individually" },
  { event_id: "22222222-2222-4222-8222-222222222222", study_id: "STU-2", outcome: "EXCLUDE", note: "Adopted in bulk from the agent's draft; not reviewed individually" },
  { event_id: "33333333-3333-4333-8333-333333333333", study_id: "STU-3", outcome: "INCLUDE", note: "Adopted in bulk from the agent's draft; not reviewed individually" },
];

async function engine(page: Page) {
  const sent: Sent[] = [];
  const declared = new Set<string>();
  let declaration: Record<string, unknown> | null = null;
  const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, json: body });
  const state = () => {
    const list = CANDIDATES.map((c) => ({ ...c, declared: declared.has(c.event_id) }));
    const by = (rows: typeof list) => ({
      INCLUDE: rows.filter((r) => r.outcome === "INCLUDE").length,
      EXCLUDE: rows.filter((r) => r.outcome === "EXCLUDE").length,
      MAYBE: 0,
    });
    const declaredRows = list.filter((c) => c.declared);
    const open = list.filter((c) => !c.declared);
    const sample = declaration?.sample as { size: number; seed: number; study_ids: string[] } | null | undefined;
    return {
      phrase: "stored from the agent's draft without being read one by one",
      declared: declaredRows.length,
      declared_by_outcome: by(declaredRows),
      candidates: list.length,
      undeclared_candidates: open.length,
      undeclared_by_outcome: by(open),
      declarations: declaration ? [declaration] : [],
      samples: sample ? [{ declaration_id: "ADD-1", size: sample.size, seed: sample.seed, study_ids: sample.study_ids, read: false, changed: null, recorded_at: null }] : [],
      sample_owed: declaredRows.some((r) => r.outcome === "EXCLUDE"),
      sample_owed_size: sample ? sample.size : null,
      no_sample_drawn: declaredRows.some((r) => r.outcome === "EXCLUDE") && !sample,
      integrity: { removed: [], unconfirmed: [] },
      candidate_list: list,
      declared_study_ids: declaredRows.map((r) => r.study_id),
    };
  };
  await page.route("**/api/console/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname.replace("/api/console/api/v1/screening", "");
    const method = req.method();
    const body = req.postData() ? (JSON.parse(req.postData()!) as Record<string, unknown>) : null;
    sent.push({ method, path, body });
    if (path === "/adoption-declarations" && method === "GET") return json(route, state());
    if (path === "/adoption-declarations" && method === "POST") {
      if (body?.confirm !== true) return json(route, { detail: { code: "ADOPTION_CONFIRM_REQUIRED", message: "confirm" } }, 422);
      const ids = (body.event_ids as string[]) ?? [];
      ids.forEach((id) => declared.add(id));
      const rows = CANDIDATES.filter((c) => ids.includes(c.event_id));
      const sample = body.sample as { size: number; seed: number } | undefined;
      declaration = {
        declaration_id: "ADD-1", declared_by: "researcher:local", declared_at: "2026-11-23T10:00:00Z", note: body.note ?? null,
        counts: { INCLUDE: rows.filter((r) => r.outcome === "INCLUDE").length, EXCLUDE: rows.filter((r) => r.outcome === "EXCLUDE").length, MAYBE: 0 },
        sample: sample ? { size: sample.size, seed: sample.seed, study_ids: ["STU-1"], how: "drawn" } : null,
      };
      return json(route, { declaration, state: state() });
    }
    if (path === "/settings") return json(route, { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" });
    if (path === "/summary") {
      return json(route, { total: 4, decided: 4, by_outcome: { INCLUDE: 2, EXCLUDE: 2, MAYBE: 0 }, agent_proposed: 4, needs_you: 0, conflicts: 0, lanes: { agent: 4, you: 4, second_screener: "PARKED" }, adoption: { declared: declared.size, undeclared_candidates: 3 - declared.size } });
    }
    if (path === "/agreement") {
      const s = state();
      return json(route, {
        decided_with_proposal: 4 - s.declared, decided_after_seeing_the_draft: 0, agreement_pct: 100,
        table_2x2: { both_include: 1, you_include_agent_exclude: 0, you_exclude_agent_include: 0, both_exclude: 4 - s.declared - 1 },
        splits_by_criterion: [], unclear_either_side: 0, kappa: null, kappa_note: "needs a second human screener",
        adoption: { ...s, candidate_list: undefined, declared_study_ids: undefined },
      });
    }
    if (path === "/corpus") return json(route, { state: "ACCEPTED" });
    return json(route, { detail: { code: "NOT_FOUND", message: path } }, 404);
  });
  return { sent, declared };
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

test("the candidates are offered, nothing is sent until confirmed, then Agreement states the declaration", async ({ page }) => {
  const { sent, declared } = await engine(page);
  await page.goto("/en/screening/adopted");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Decisions stored from the agent's draft");
  await expect(page.locator("[data-candidates]")).toContainText("3 decisions have a note that says they were adopted or stored in bulk");
  expect(sent.filter((s) => s.method === "POST")).toHaveLength(0);

  await page.locator("[data-sample-size]").fill("1");
  await page.getByRole("button", { name: "Declare 3 decisions" }).click();
  const dialog = page.getByRole("alertdialog");
  await expect(dialog).toContainText("Declare 3 decisions as stored from the agent's draft without being read one by one?");
  const tick = dialog.getByRole("checkbox", { name: "I did not read these records one by one." });
  await expect(tick).toBeFocused();
  await expect(dialog.getByRole("button", { name: "Record the declaration" })).toBeDisabled();
  expect(await axe(page)).toEqual([]);
  expect(sent.filter((s) => s.method === "POST")).toHaveLength(0);

  await tick.check();
  await dialog.getByRole("button", { name: "Record the declaration" }).click();
  await expect(page.locator("[data-recorded]")).toHaveText("Recorded.");
  const posts = sent.filter((s) => s.method === "POST");
  expect(posts).toHaveLength(1);
  expect(posts[0].path).toBe("/adoption-declarations");
  expect(posts[0].body).toMatchObject({ confirm: true, event_ids: CANDIDATES.map((c) => c.event_id), sample: { size: 1 } });
  expect(declared.size).toBe(3);
  await expect(page.locator('[data-declaration="ADD-1"]')).toContainText("3 decisions");
  await expect(page.locator('[data-sample="owed"]')).toContainText("Owed: read these records in Triage, then record the result.");

  await page.goto("/en/screening/agreement");
  await expect(page.locator("[data-adoption-not-counted]")).toHaveText(
    "3 decisions were stored from the agent's draft without being read one by one; they are not counted here.",
  );
  await expect(page.locator('[data-sample="declared"]')).toContainText("A sample of 1 adopted exclusions is owed.");
  await expect(page.locator("body")).not.toContainText("You saw every record");
});

for (const [locale, heading, dir] of [
  ["fr", "Décisions enregistrées depuis le brouillon de l'agent", "ltr"],
  ["ar", "القرارات المحفوظة من مسودة الوكيل", "rtl"],
] as const) {
  test(`the declaration screen reads in ${locale}`, async ({ page }) => {
    await engine(page);
    await page.goto(`/${locale}/screening/adopted`);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(heading);
    await expect(page.locator("html")).toHaveAttribute("dir", dir);
    expect(await axe(page)).toEqual([]);
  });
}
