import type { Page, Route } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * Agent proposals run (spec 06) and agreement (spec 07) in a real browser.
 * The same-origin proxy is answered at the network boundary with the engine's
 * response shapes; a run is a small state machine here (running until
 * cancelled, or stopped part-way), so the page's polling, cancel and resume are
 * the real build reacting to the engine. No provider is ever reached.
 */

const ESTIMATE = {
  records: 3,
  tokens: { input_tokens: 2400, cache_read_tokens: 1200, cache_write_tokens: 600, output_tokens: 1800 },
  assumptions: { chars_per_token: 4, output_tokens_per_record: 600 },
  cost_usd: 0.05,
  batch: false,
  prices_as_of: "2026-11-05",
  priced: true,
};
const SETUP = {
  task: { task_version: "screen-v1", prompt_sha256: "sha256:abc", model: "claude-opus-5-5", effort: "low" },
  providers: [
    { provider: "anthropic", key: "keychain", consent: null },
    { provider: "openai_compatible", key: "none", consent: null },
    { provider: "gemini", key: "none", consent: null },
  ],
  data_flow: "titles, abstracts and publication years of every record in the run, and the screening criteria",
  active_run: null,
  latest_run: null,
};

function view(id: string, overrides: Record<string, unknown>) {
  return {
    run_id: id, kind: "proposals", state: "running", code: null, provider: "anthropic", model: "claude-opus-5-5", effort: "low",
    records: 3, done: 0, failed: 0, refused: 0, truncated: 0, invalid: 0, check_failures: 0, cost_so_far: 0, cost_ceiling_usd: null,
    started_at: "2026-11-05T10:00:00Z", finished_at: null, ...overrides,
  };
}

type Sent = { path: string; body: Record<string, unknown> | null };

async function engine(page: Page, plan: { first: "running" | "stopped" }) {
  const sent: Sent[] = [];
  const runs: Record<string, Record<string, unknown>> = {};
  let n = 0;
  await page.route("**/api/console/api/v1/screening/**", async (route: Route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname.replace("/api/console/api/v1/screening", "");
    const body = req.postData() ? (JSON.parse(req.postData()!) as Record<string, unknown>) : null;
    sent.push({ path, body });
    if (path === "/proposals/setup") return route.fulfill({ json: SETUP });
    if (path === "/queue") return route.fulfill({ json: { items: [], next_cursor: null } });
    if (path === "/proposals/runs" && body?.estimate_only) return route.fulfill({ json: { run_id: null, estimate: body.dry_run ? { ...ESTIMATE, records: 3 } : ESTIMATE } });
    if (path === "/proposals/runs") {
      n += 1;
      const id = `RUN-${n}`;
      runs[id] = n === 1 && plan.first === "stopped"
        ? view(id, { state: "stopped", code: "COST_CEILING_REACHED", done: 1, cost_so_far: 0.02, cost_ceiling_usd: 0.02 })
        : n === 1 ? view(id, { done: 1 }) : view(id, { state: "completed", done: 2, records: 2 });
      return route.fulfill({ json: { run_id: id, estimate: ESTIMATE } });
    }
    const status = path.match(/^\/proposals\/runs\/(RUN-\d+)$/);
    if (status) return route.fulfill({ json: runs[status[1]] });
    const cancel = path.match(/^\/proposals\/runs\/(RUN-\d+)\/cancel$/);
    if (cancel) {
      runs[cancel[1]] = { ...runs[cancel[1]], state: "cancelled", finished_at: "2026-11-05T10:02:00Z" };
      return route.fulfill({ json: { run_id: cancel[1], state: "cancelled" } });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  return sent;
}

const runPosts = (sent: Sent[]) => sent.filter((s) => s.path === "/proposals/runs" && !s.body?.estimate_only);

test.use({ viewport: DESKTOP_VIEWPORT });

test("a dry run needs consent, states the data flow, then polls and cancels", async ({ page }) => {
  const sent = await engine(page, { first: "running" });
  await page.goto("/en/screening/proposals");
  const dry = page.getByRole("button", { name: "Dry run on 20 records" });
  await expect(page.getByText(/prices as of 2026-11-05/)).toBeVisible();
  // A live-only step: no demonstration marker, and the footer says live data.
  await expect(page.getByText("Demonstration data")).toHaveCount(0);
  await expect(page.getByRole("contentinfo")).toContainText("Live workspace data.");
  await expect(dry).toBeDisabled();
  await page.getByRole("checkbox", { name: /I consent/ }).check();
  await dry.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("What leaves this machine");
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await dry.click();
  await page.getByRole("button", { name: "Start the run" }).click();
  await expect(page.getByText("1 of 3 proposed").first()).toBeVisible();
  expect(runPosts(sent)[0].body).toMatchObject({ dry_run: true, consent: { provider: "anthropic" } });
  await page.getByRole("button", { name: "Cancel the run" }).click();
  await expect(page.locator("[data-run]")).toContainText("Cancelled");
  await expect(page.locator("[data-partial]")).toContainText("2 records have no draft");
});

test("a run stopped at the ceiling is partial and resumes over the records without a draft", async ({ page }) => {
  const sent = await engine(page, { first: "stopped" });
  await page.goto("/en/screening/proposals");
  await page.getByLabel("Cost ceiling (USD)").fill("0.02");
  await page.getByRole("checkbox", { name: /I consent/ }).check();
  await page.getByRole("button", { name: "Start agent proposals · 3 records" }).click();
  await page.getByRole("button", { name: "Start the run" }).click();
  await expect(page.locator('[data-state="COST_CEILING_REACHED"]')).toBeVisible();
  await expect(page.locator("[data-partial]")).toContainText("stopped at 1 of 3");
  await page.getByRole("checkbox", { name: /I consent/ }).check();
  await page.getByRole("button", { name: "Resume over the records without a draft" }).click();
  await page.getByRole("button", { name: "Start the run" }).click();
  await expect(page.locator("[data-run]")).toContainText("Completed");
  const posts = runPosts(sent);
  expect(posts).toHaveLength(2);
  expect(posts[0].body!.cost_ceiling_usd).toBe(0.02);
  expect(posts[1].body!.scope).toEqual({ view: "no_proposal" });
  // No draft is ever read from this screen.
  expect(sent.some((s) => /\/records\/.+\/proposal$/.test(s.path))).toBe(false);
});

test("agreement prints the engine's numbers with a greyed kappa, in Arabic too", async ({ page }) => {
  await page.route("**/api/console/api/v1/screening/**", async (route: Route) => {
    const path = new URL(route.request().url()).pathname.replace("/api/console/api/v1/screening", "");
    const bodies: Record<string, unknown> = {
      "/agreement": { decided_with_proposal: 4, decided_after_seeing_the_draft: 0, agreement_pct: 75, table_2x2: { both_include: 1, you_include_agent_exclude: 1, you_exclude_agent_include: 0, both_exclude: 2 }, splits_by_criterion: [{ criterion_id: "INC-03", n: 1 }], unclear_either_side: 0, kappa: null, kappa_note: "needs a second human screener" },
      "/summary": { total: 4, decided: 4, by_outcome: { INCLUDE: 2, EXCLUDE: 2, MAYBE: 0 }, agent_proposed: 4, needs_you: 0, conflicts: 0, lanes: { agent: 4, you: 4, second_screener: "PARKED" } },
      "/settings": { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" },
    };
    return path in bodies ? route.fulfill({ json: bodies[path] }) : route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  await page.goto("/en/screening/agreement");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("agreed on 75% of records; it would have dropped 1 of your includes");
  await expect(page.locator("[data-kappa]")).toHaveAttribute("aria-disabled", "true");
  await expect(page.locator('[data-split="INC-03"]')).toContainText("1");
  await page.goto("/ar/screening/agreement");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("[data-kappa]")).toContainText("يحتاج إلى مراجع بشري ثانٍ");
});
