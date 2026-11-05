import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

import type { Page } from "@playwright/test";

import { expect, test } from "../tests-browser/helpers";

/**
 * Live gate (M1b-1): the 30 golden records screened end to end in the real UI
 * against a real console (`playwright.live.config.ts`).
 *
 * The decisions follow a fixed SYNTHETIC pattern (include, exclude, unclear in
 * turn) to exercise the pipeline; they are not screening judgements. The real
 * golden run with the researcher's own decisions is the M5-slim gate.
 *
 * What this proves, in the browser, against the engine:
 * - no draft is ever requested for a record before its decision (blinding);
 * - a draft revealed after a decision, then a change, is stamped by the engine
 *   as changed after the reveal;
 * - a conflict from another device locks the record until one event is kept,
 *   and re-sending an event is a duplicate (replay is idempotent);
 * - each batch is approved with the code the console prints in its terminal,
 *   the screening publishes, and `scripts/check_golden_workspace.py` passes.
 */

const TERMINAL_LOG = process.env.LIVE_TERMINAL_LOG ?? "";
const SANDBOX = process.env.LIVE_SANDBOX ?? "";
const API = "/api/console/api/v1/screening";

function watchBlinding(page: Page) {
  const decided = new Set<string>();
  const violations: string[] = [];
  page.on("response", async (response) => {
    const request = response.request();
    if (request.method() === "POST" && request.url().endsWith("/decisions/events") && response.ok()) {
      const body = JSON.parse(request.postData() ?? "{}") as { events?: { study_id: string }[] };
      for (const e of body.events ?? []) decided.add(e.study_id);
    }
  });
  page.on("request", (request) => {
    const match = request.url().match(/\/records\/([^/?]+)\/proposal/);
    if (match && !decided.has(decodeURIComponent(match[1]))) violations.push(match[1]);
  });
  return violations;
}

async function answerChecklist(page: Page) {
  // One answer group per criterion (`role=group` with the criterion id as its label).
  const groups = page.locator('[role="group"][aria-label]').filter({ has: page.getByRole("button", { name: "Not reported" }) });
  const labels = await groups.evaluateAll((nodes) => nodes.map((n) => n.getAttribute("aria-label") ?? ""));
  for (const label of labels) {
    await page.keyboard.press(label.startsWith("INC") ? "1" : "2");
    await expect(page.getByRole("group", { name: label }).getByRole("button", { pressed: true })).toHaveCount(1);
  }
}

async function decide(page: Page, outcome: "I" | "E" | "U") {
  await expect(page.getByRole("button", { name: /^Include/ })).toBeVisible();
  await answerChecklist(page);
  if (outcome === "E") {
    await page.keyboard.press("e");
    await page.keyboard.press("1");
    await page.keyboard.press("Enter");
  } else {
    await page.keyboard.press(outcome.toLowerCase());
  }
  // Decided: the card now offers Next record instead of the outcome buttons.
  await expect(page.getByRole("button", { name: /^Next record/ })).toBeVisible();
}

test("the golden workspace screened, revealed, changed, reconciled and published in the browser", async ({ page }) => {
  const violations = watchBlinding(page);
  await page.goto("/en/screening/home");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("0 of 30 records are decided; 30 still need you.");
  await page.getByRole("link", { name: /Open triage/ }).click();
  await expect(page.getByTestId("proposal-aside")).toContainText("Hidden until you decide.");

  // Decide all 30 in queue order; the first three records carry sandbox drafts.
  const pattern = ["I", "E", "U"] as const;
  for (let i = 0; i < 30; i += 1) {
    await decide(page, pattern[i % 3]);
    if (i === 0) {
      await expect(page.getByTestId("proposal-aside")).toContainText("Not a decision");
      await expect(page.getByRole("heading", { name: "You and the agent's draft agree." })).toBeVisible();
    }
    if (i === 1) {
      // Revealed after an Exclude; changing it now is a change after the reveal.
      await expect(page.getByRole("heading", { name: "Your decision differs from the agent's draft." })).toBeVisible();
      await page.getByRole("button", { name: "Change my decision" }).click();
      await page.keyboard.press("u");
      await expect(page.getByText("Changed after seeing the agent's draft").first()).toBeVisible();
    }
    if (i < 29) await page.keyboard.press("n");
  }
  expect(violations).toEqual([]);

  // A second device decides record 6 differently: a real conflict.
  const queue = await (await page.request.get(`${API}/queue?view=decided&limit=50`)).json();
  const target = queue.items[5];
  const record = await (await page.request.get(`${API}/records/${target.study_id}`)).json();
  const rival = {
    event_id: "01a1aa5c-0fbb-7000-8000-00000000c0f1",
    study_id: target.study_id,
    screener_id: "researcher:local",
    method: "HUMAN",
    outcome: record.my_decision.outcome === "INCLUDE" ? "MAYBE" : "INCLUDE",
    reason_code: null,
    note: "Second device, live gate",
    criteria: [],
    decided_at: "2026-11-05T12:00:00.000Z",
    device: "desktop",
    supersedes: null,
    proposal_shown: null,
    binding: record.binding,
  };
  const post = (events: unknown[]) =>
    page.request.post(`${API}/decisions/events`, { data: { events }, headers: { origin: new URL(page.url()).origin } });
  expect((await (await post([rival])).json()).results[0].result).toBe("conflict");
  expect((await (await post([rival])).json()).results[0].result).toBe("duplicate");

  // A conflicted record has no winning decision, so it is back in "Needs you" and is the only one there.
  const queueNav = page.getByRole("navigation", { name: "Queue" });
  await queueNav.getByRole("button", { name: "Needs you", exact: true }).click();
  await expect(queueNav.getByRole("listitem")).toHaveCount(1);
  await expect(queueNav.getByRole("listitem")).toContainText(target.title.slice(0, 20));
  await queueNav.getByRole("listitem").getByRole("button").click();
  await expect(page.getByRole("heading", { name: "Decided differently on two devices" })).toBeVisible();
  await page.getByRole("button", { name: /^Keep / }).first().click();
  await expect(page.getByRole("heading", { name: "Decided differently on two devices" })).toHaveCount(0);

  // Publish: approve each batch with the code from the console's terminal.
  await page.goto("/en/screening/publish");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Approve each batch, then publish the screening.");
  const batches = await page.locator("[data-batch]").evaluateAll((nodes) => nodes.map((n) => n.getAttribute("data-batch")));
  for (const batch of batches) {
    const item = page.locator(`[data-batch="${batch}"]`);
    await item.getByRole("button", { name: "Show a code in the terminal" }).click();
    await expect(item.getByText(/Code printed in the terminal/)).toBeVisible();
    const codes = [...readFileSync(TERMINAL_LOG, "utf-8").matchAll(new RegExp(`approval code for batch ${batch}: (\\S+)`, "g"))];
    const code = codes.at(-1)?.[1];
    expect(code, `terminal code for batch ${batch}`).toBeTruthy();
    await item.getByLabel(/Approval code for/).fill(code!);
    await item.getByRole("button", { name: /^Approve / }).click();
    await expect(item.getByText("Approval on file", { exact: true })).toBeVisible();
  }
  await page.getByRole("button", { name: "Publish the screening" }).click();
  await expect(page.getByText(/^Published generation /)).toBeVisible();

  const checker = execFileSync("uv", ["run", "python", "../../scripts/check_golden_workspace.py", SANDBOX], { encoding: "utf-8" });
  expect(checker).not.toContain("FAIL");
});
