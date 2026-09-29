import { createRequire } from "node:module";

import {
  DESKTOP_VIEWPORT,
  expect,
  MOBILE_NAV_PANEL_ID,
  MOBILE_NAV_TRIGGER_LABEL,
  MOBILE_VIEWPORT,
  report,
  test,
} from "./helpers";

/**
 * axe-core on the *rendered* page, in Chromium.
 *
 * `GATES.md` §2 records that the jsdom run reports `color-contrast` as
 * `incomplete`, never as passed, because jsdom computes no real contrast
 * ratio. This is the run that can actually answer it — so it separates three
 * outcomes and never collapses them into one:
 *
 *   violation  -> a real failure. Fails the test. Never suppressed.
 *   incomplete  -> axe could not decide (unknown background, image text, …).
 *                  Reported as `incomplete`, which is NOT a pass.
 *   pass        -> only when the rule id appears in `passes`.
 *
 * `incomplete` is reported, not suppressed — but it is also not allowed to
 * *satisfy the non-vacuity guard* below, which requires `color-contrast` in
 * `passes` specifically. That tightening was made deliberately on review. The
 * guard previously accepted the rule appearing in `passes` **or** in
 * `incomplete`, which contradicts the three outcomes above: it let
 * `incomplete` stand in for a pass. A regression that moved the rule silently
 * from `passes` to `incomplete` — a background gradient, an overlap or any
 * other node whose background becomes undecidable — would then have left the
 * run green while the empty `violations` array above went vacuous, which is
 * precisely the failure the guard exists to prevent. A genuine contrast failure
 * is already caught by the `violations` `toEqual([])` assertion, so requiring a
 * *decided* pass costs no real coverage. It is satisfiable today: this page
 * reports `color-contrast` in `passes` with `incomplete: []` at both viewports,
 * so a node that legitimately becomes undecidable now fails the guard loudly
 * instead of passing quietly. No rule was disabled, no node excluded, and the
 * guard was tightened rather than removed.
 *
 * A negative control injects a deliberately broken `<img>` and asserts axe
 * reports it as a `critical` `image-alt` violation, so a run in which the
 * injected core silently failed to evaluate anything cannot look identical to
 * a clean one.
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

/**
 * axe's own id for the contrast rule, quoted from `node_modules/axe-core`.
 *
 * It is the American spelling, `color-contrast`. The literals in this file
 * previously read `colour-contrast`, which axe never emits, so the non-vacuity
 * guard below compared against a string that could not be present: it was dead
 * code that could only ever fail, and it stayed hidden because the
 * `expect(outcome.violations).toEqual([])` assertion failed first on any run
 * where contrast genuinely failed. The guard is a real requirement — an empty
 * `violations` array is only evidence if the rule was actually evaluated — so
 * it is repaired here against the real id rather than removed. Nothing is
 * allow-listed, excluded or downgraded; the id is the only thing that changed.
 */
const AXE_CONTRAST_RULE_ID = "color-contrast";

interface AxeNode {
  target: string;
  contrastRatio: string | null;
  message: string;
}

interface AxeOutcome {
  violations: Array<{
    id: string;
    impact: string | null;
    nodes: AxeNode[];
    help: string;
  }>;
  incomplete: Array<{
    id: string;
    impact: string | null;
    nodes: number;
    help: string;
    reason: string;
  }>;
  passes: string[];
}

async function runAxe(page: import("@playwright/test").Page): Promise<AxeOutcome> {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const axe = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<unknown> } }).axe;
    const raw = (await axe.run(document)) as {
      violations: Array<{
        id: string;
        impact: string | null;
        nodes: Array<{
          target: string[];
          any: Array<{ message: string; data: Record<string, string> | null }>;
        }>;
        help: string;
      }>;
      incomplete: Array<{
        id: string;
        impact: string | null;
        nodes: Array<{ any: Array<{ message: string }> }>;
        help: string;
      }>;
      passes: Array<{ id: string }>;
    };
    return {
      violations: raw.violations.map((item) => ({
        id: item.id,
        impact: item.impact,
        help: item.help,
        // Per-node detail is kept so a red run states *which* elements failed
        // and at what ratio, instead of only a rule id.
        nodes: item.nodes.map((node) => ({
          target: node.target.join(" "),
          contrastRatio: node.any[0]?.data?.contrastRatio ?? null,
          message: node.any[0]?.message ?? "",
        })),
      })),
      incomplete: raw.incomplete.map((item) => ({
        id: item.id,
        impact: item.impact,
        nodes: item.nodes.length,
        help: item.help,
        reason: item.nodes[0]?.any?.[0]?.message ?? "",
      })),
      passes: raw.passes.map((item) => item.id),
    };
  });
}

function summarise(outcome: AxeOutcome): string {
  const contrast = outcome.passes.includes(AXE_CONTRAST_RULE_ID)
    ? "pass"
    : outcome.incomplete.some((item) => item.id === AXE_CONTRAST_RULE_ID)
      ? "incomplete"
      : "violation";
  const detail = outcome.violations
    .flatMap((item) => item.nodes.map((node) => `${item.id}@${node.contrastRatio ?? "?"} ${node.target}`))
    .join(" | ");
  return [
    `${AXE_CONTRAST_RULE_ID}=${contrast}`,
    `violations=${outcome.violations.map((item) => `${item.id}(${item.impact}, ${item.nodes.length} nodes)`).join(", ") || "none"}`,
    `incomplete=${outcome.incomplete.map((item) => `${item.id}(${item.nodes})`).join(", ") || "none"}`,
    detail,
  ].join(" ; ");
}

test.describe("axe-core on rendered CSS", () => {
  for (const [name, viewport] of [
    ["375px", MOBILE_VIEWPORT],
    ["1440px", DESKTOP_VIEWPORT],
  ] as const) {
    test(`${name}: zero real violations on the rendered page`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/");
      // Settle fonts/layout so contrast is measured against final computed
      // styles rather than an in-flight paint.
      await page.waitForLoadState("networkidle");

    const outcome = await runAxe(page);
    report(`${name} axe: ${summarise(outcome)}`);

    // Any impact, not just critical/serious: this is the same bar gate 18
    // sets for the document-scope jsdom run. A `color-contrast` failure here is
    // a real WCAG failure on rendered CSS and is left red, not allow-listed.
    expect(
      outcome.violations,
      `${name}: axe reported real violations on the rendered page`,
    ).toEqual([]);


      // Non-vacuity: `color-contrast` must be *decided*, not merely attempted.
      // Requiring it in `passes` specifically is deliberate — see the note in
      // this file's docstring. `incomplete` is not accepted here: per the three
      // outcomes above it is not a pass, and accepting it would let a silent
      // `passes` -> `incomplete` regression leave this run green while the empty
      // `violations` array above went vacuous. A real contrast failure is
      // already caught by that `toEqual([])`, so this assertion adds
      // non-vacuity only, and it fails loudly if any node becomes genuinely
      // undecidable rather than quietly tolerating it.
      expect(
        outcome.passes,
        `${name}: ${AXE_CONTRAST_RULE_ID} is not in axe's passing rule set, so the empty violations array is meaningless (an undecidable contrast is reported under "incomplete", not here)`,
      ).toContain(AXE_CONTRAST_RULE_ID);
    });
  }

  test("375px: zero real violations with the mobile dialog open", async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL }).click();

    // The panel must be open *and* visible first. Headless UI unmounts it when
    // closed (measured at `responsive-nav.spec.ts:122`), and the desktop `<nav>`
    // is `hidden lg:block`, so an axe run against a closed dialog would measure a
    // page containing no navigation at all — and still look green.
    const panel = page.locator(`#${MOBILE_NAV_PANEL_ID}`);
    await expect(panel).toBeVisible();

    const outcome = await runAxe(page);
    report(`375px dialog-open axe: ${summarise(outcome)}`);

    expect(
      outcome.violations,
      "375px with the mobile dialog open: axe reported real violations on the rendered page",
    ).toEqual([]);
    expect(
      outcome.passes,
      `375px with the mobile dialog open: ${AXE_CONTRAST_RULE_ID} is not in axe's passing rule set, so the empty violations array is meaningless (an undecidable contrast is reported under "incomplete", not here)`,
    ).toContain(AXE_CONTRAST_RULE_ID);
  });

  test("negative control: axe really runs on the live page", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/");

    // A deliberately broken element, injected into the rendered document only
    // for this test. No application file is touched.
    await page.evaluate(() => {
      const broken = document.createElement("img");
      broken.setAttribute("src", "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7");
      broken.id = "axe-negative-control";
      document.body.append(broken);
    });

    const outcome = await runAxe(page);
    const control = outcome.violations.find((item) => item.id === "image-alt");
    report(`negative control: ${JSON.stringify(control ?? null)}`);

    expect(
      control,
      "the injected <img> without alt must be reported as image-alt, or this run proves nothing",
    ).toBeDefined();
    expect(control?.impact).toBe("critical");
    expect(control?.nodes.length).toBe(1);
  });
});
