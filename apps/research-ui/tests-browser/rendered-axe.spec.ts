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
 *
 * Packet UI-01c (acceptance A6) added the third outcome as an ASSERTION.
 * `incomplete` was described correctly in this header and then never checked:
 * `summarise` printed it, and that was all. A run whose `color-contrast` had
 * quietly moved from `passes` to `incomplete` — an undecidable background, an
 * overlap, a translucent backdrop showing through — would have stayed green on
 * every assertion in this file. Each of the three runs now asserts the whole
 * `incomplete` ledger with `toEqual`, so an unexpected rule, or a change in the
 * node count of the one expected rule, is a red run rather than an extra line in
 * a log. Nothing is suppressed, allow-listed or excluded; the expected value is
 * the value the run has always reported.
 *
 * The same packet also repaired `summarise`'s precedence, which printed
 * `color-contrast=pass` for a rule that both passed and violated — see the note
 * on that function.
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
  /*
   * Three-way precedence, and the order matters (packet UI-01c, finding F5).
   *
   * This used to ask `passes` first, so a rule that passed for some nodes and
   * violated for others printed `color-contrast=pass`: the run's own log
   * contradicted the red assertion two lines below it. Reporting only — the
   * adjacent `violations=` field and the `toEqual([])` assertion always carried
   * the real verdict — but a log line that says "pass" for a failing page is the
   * kind of thing that later gets quoted in a report. A violation now wins.
   */
  const contrast = outcome.violations.some((item) => item.id === AXE_CONTRAST_RULE_ID)
    ? "violation"
    : outcome.incomplete.some((item) => item.id === AXE_CONTRAST_RULE_ID)
      ? "incomplete"
      : outcome.passes.includes(AXE_CONTRAST_RULE_ID)
        ? "pass"
        : "not-evaluated";
  const detail = outcome.violations
    .flatMap((item) => item.nodes.map((node) => `${item.id}@${node.contrastRatio ?? "?"} ${node.target}`))
    .join(" | ");
  return [
    `${AXE_CONTRAST_RULE_ID}=${contrast}`,
    `violations=${outcome.violations.map((item) => `${item.id}(${item.impact}, ${item.nodes.length} nodes)`).join(", ") || "none"}`,
    `incomplete=${incompleteSummary(outcome).join(", ") || "none"}`,
    detail,
  ].join(" ; ");
}

/**
 * The `incomplete` ("needs review") results as `<id>(<node count>)` strings.
 *
 * Packet UI-01c, acceptance A6: `incomplete` was previously **printed** by
 * {@link summarise} and never asserted, which is exactly the condition that
 * lets a contrast gate become vacuously green — an `incomplete` result is not a
 * pass, and `color-contrast` reaching it silently is the one regression the
 * non-vacuity guard above exists to catch. This function is what makes the
 * ledger assertable, and it is compared with `toEqual` so an unexpected rule
 * fails by name.
 */
function incompleteSummary(outcome: AxeOutcome): string[] {
  return outcome.incomplete.map((item) => `${item.id}(${item.nodes})`);
}

/**
 * The `incomplete` ledger the closed-dialog runs must present (A6).
 *
 * Empty, at both viewports. The only `incomplete` this application has ever
 * produced is `aria-hidden-focus` from Headless UI's own focus guards, and only
 * with the mobile dialog open — see {@link EXPECTED_DIALOG_OPEN_INCOMPLETE}.
 */
const EXPECTED_CLOSED_INCOMPLETE: readonly string[] = [];

/**
 * The `incomplete` ledger the 375px dialog-open run must present (A6).
 *
 * `aria-hidden-focus` on exactly 2 nodes: the two 1x0px
 * `button[data-headlessui-focus-guard]` sentinels Headless UI injects at the
 * boundary of the background it marks `aria-hidden`. They are library-generated,
 * they are expected, and they are reported rather than suppressed — but they are
 * now *pinned*, so a change that adds a third focusable-inside-aria-hidden node,
 * or a new undecidable contrast node, turns this suite red instead of adding one
 * more line to a log nobody diffs.
 */
const EXPECTED_DIALOG_OPEN_INCOMPLETE: readonly string[] = ["aria-hidden-focus(2)"];

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

      /*
       * A6: the `incomplete` ledger is asserted, not merely printed.
       *
       * This is the assertion that stands between the contrast gate and vacuity.
       * `color-contrast` is separately required to be a decided *pass*, but that
       * check is about one rule id; this one is about the whole incomplete set.
       * An undecidable contrast node — a gradient, an overlap, a translucent
       * backdrop showing through — would land here rather than in `violations`,
       * and without this assertion it would only ever be read in a log.
       *
       * With the dialog closed, nothing is undecidable on this page, so the
       * expectation is empty at BOTH viewports.
       */
      expect(
        incompleteSummary(outcome),
        `${name}: axe reported an "incomplete" (needs review) result. Nothing may be undecidable with the dialog closed; an incomplete is not a pass.`,
      ).toEqual([...EXPECTED_CLOSED_INCOMPLETE]);

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
    /*
     * A6, the third state. This is the one run with a non-empty ledger, and it
     * is pinned exactly: `aria-hidden-focus` on 2 nodes, which are Headless UI's
     * own 1x0px focus guards inside the `aria-hidden` background (see
     * `GATES.md` §3.6.3 for the node selectors). Naming the count means a new
     * focusable-inside-aria-hidden node is a red run rather than a longer log
     * line, and means a contrast node that goes undecidable here cannot hide
     * inside the one `incomplete` that is legitimately expected.
     */
    expect(
      incompleteSummary(outcome),
      '375px with the mobile dialog open: the only expected "incomplete" is Headless UI\'s two focus guards, aria-hidden-focus(2)',
    ).toEqual([...EXPECTED_DIALOG_OPEN_INCOMPLETE]);
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
