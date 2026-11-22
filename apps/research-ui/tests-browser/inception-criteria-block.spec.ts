import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { completeDraft, inceptionEngine, outOfScopeId, proofId, SESSION, type FakeOptions } from "../tests/fixtures/inception-engine";
import { DESKTOP_VIEWPORT, expect, test } from "./helpers";
import { expectNoSidewaysScroll, measureOverflow } from "./overflow-recipe";

/**
 * Step 5's criteria section (spec 11, M11b part D) in a real browser, against the stateful fake of
 * `tests/fixtures/inception-engine.ts` with the engine's `method` answer: the rule has no default
 * and holds Continue until chosen; the choice reaches Review in words; out-of-scope items become
 * exclusion rows; keyboard only; axe in light and dark (both projects), English and Arabic.
 */

async function engine(page: Page, options: FakeOptions & { draft?: Record<string, unknown> } = {}) {
  const fake = inceptionEngine(options);
  if (options.draft) fake.seed(options.draft);
  await page.route("**/api/console/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/console", "") + url.search;
    const raw = route.request().postData();
    const answer = fake.handle(route.request().method(), path, raw ? (JSON.parse(raw) as Record<string, unknown>) : null);
    if (answer.sse) await route.fulfill({ status: answer.status, contentType: "text/event-stream", body: String(answer.body) });
    else await route.fulfill({ status: answer.status, json: answer.body });
  });
  return fake;
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

const decided = (extra: Record<string, unknown> = {}) =>
  completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true }, ...extra });

test.use({ viewport: DESKTOP_VIEWPORT });

test("the rule holds Continue until chosen, and the choice reaches Review in words", async ({ page }) => {
  const fake = await engine(page, { draft: decided({ method_blinding: "reveal_after_decision", method_not_reported: null }), method: true });
  await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
  const go = page.getByRole("button", { name: "Continue to review" });
  await expect(go).toBeDisabled();
  await expect(page.locator("[data-rule-blocked]")).toContainText("Choose what the agent should do when a criterion is not reported");
  expect(await axe(page)).toEqual([]);
  const rule = page.getByRole("group", { name: /the agent's draft should/ });
  await rule.getByRole("radio", { name: /Exclude only on a clear failure/ }).check();
  await expect(go).toBeEnabled();
  await go.click();
  await page.waitForURL(/\/en\/inception\/review\/?\?draft=/);
  const group = page.getByRole("region", { name: "How you will screen" });
  await expect(group).toContainText("The agent's draft is shown after you decide each record.");
  await expect(group).toContainText("A criterion the abstract does not report leaves the record Unclear unless another criterion clearly fails.");
  expect(fake.calls.filter((c) => c.method === "PUT").at(-1)?.body).toMatchObject({ draft: { method_not_reported: "decisive_first", method_blinding: "reveal_after_decision" } });
  expect(await axe(page)).toEqual([]);
});

test("out-of-scope items are added on step 5 and wait as exclusion rows; the rule is chosen by keyboard", async ({ page }) => {
  await engine(page, { draft: decided({ method_not_reported: null }), method: true });
  await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
  const field = page.getByLabel("Is anything out of scope?");
  await field.fill("closed-source models; satellite only");
  await page.getByRole("button", { name: "Add an out-of-scope topic" }).click();
  const row = page.locator("li[data-criterion]", { hasText: "satellite only" });
  await expect(row).toHaveAttribute("data-status", "undecided");
  await expect(row).toContainText("Your out-of-scope answer");
  // Keyboard: Tab into the rule's group, then an arrow chooses (the radio pattern).
  const first = page.getByRole("group", { name: /the agent's draft should/ }).getByRole("radio").first();
  await first.focus();
  await page.keyboard.press("Space");
  await expect(first).toBeChecked();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("group", { name: /the agent's draft should/ }).getByRole("radio").nth(1)).toBeChecked();
});

for (const width of [375, 1024, 1280, 1440]) {
  test(`step 5's criteria section does not scroll sideways at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await engine(page, { draft: decided({ method_not_reported: null }), method: true });
    await page.goto(`/en/inception/criteria/?draft=${SESSION}`);
    await expect(page.locator("[data-method]")).toBeVisible();
    expectNoSidewaysScroll(await measureOverflow(page), `criteria ${width}px`);
  });
}

test("ar: the criteria section reads right to left and axe finds nothing", async ({ page }) => {
  await engine(page, { draft: decided({ method_not_reported: null }), method: true });
  await page.goto(`/ar/inception/criteria/?draft=${SESSION}`);
  await expect(page.locator("[data-method]")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.dir)).toBe("rtl");
  expect(await axe(page)).toEqual([]);
});
