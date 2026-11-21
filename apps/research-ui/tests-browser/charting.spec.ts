import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * The charting screen, Full text view (M12a Part A, spec 01), in a real browser.
 * Like the other specs of this suite, the same-origin console proxy is answered
 * at the network boundary: a small stateful fake that answers in the engine's
 * shapes (`tests/console/test_charting_api.py`) for a published screening with
 * five kept studies. It applies status and decision events as the engine does,
 * so the keyboard, the counts and the undo are exercised end to end in the build.
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

type Row = Record<string, unknown> & {
  study_id: string;
  kept: boolean;
  fulltext: Record<string, unknown> & { status: string };
  ft_decision: { outcome: string; reason_code?: string | null; reason_text?: string | null } | null;
  heads: Record<string, string | null>;
};

function row(i: number): Row {
  return {
    study_id: `STU-00${i}`,
    title: ["Weed mapping from UAV imagery", "Deep learning for crop rows", "Multispectral drone survey", "Sugar beet weed detection", "Herbicide spot spraying"][i - 1],
    authors: ["Sa, I."],
    year: 2018 + i,
    venue: "Remote Sensing",
    doi: `10.3390/rs${1000 + i}`,
    url: null,
    abstract: null,
    arxiv_id: null,
    round: 1,
    arm: "databases",
    round_label: "Databases",
    generation_id: "gen-1",
    ta_decision: i === 3 ? "MAYBE" : "INCLUDE",
    ta_reason: "",
    kept: true,
    new_since: null,
    fulltext: { status: "to_get", requested_on: null, reason: null, reason_text: null, attachment: null, link: null },
    ft_decision: null,
    heads: { fulltext_status: null, fulltext_decision: null, attachment: null, link: null },
  };
}

function counts(rows: Row[]) {
  const live = rows.filter((r) => r.kept);
  const by = (test: (r: Row) => boolean) => live.filter(test).length;
  return {
    kept: live.length,
    to_get: by((r) => r.fulltext.status === "to_get"),
    requested: by((r) => r.fulltext.status === "requested"),
    retrieved: by((r) => r.fulltext.status === "retrieved"),
    not_retrieved: by((r) => r.fulltext.status === "not_retrieved"),
    included: by((r) => r.ft_decision?.outcome === "INCLUDE"),
    excluded: by((r) => r.ft_decision?.outcome === "EXCLUDE"),
    to_decide: by((r) => !r.ft_decision),
  };
}

async function engine(page: Page) {
  const rows = [1, 2, 3, 4, 5].map(row);
  const posted: unknown[][] = [];
  const table = () => ({
    shape: "charting.table-v1",
    screener_id: "researcher:local",
    publication: { status: "CURRENT", code: null, generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z", round: 1 },
    rounds: [{ round: 1, arm: "databases", generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z" }],
    chasing_pending: false,
    stale: false,
    changes: null,
    read_only: false,
    read_only_code: null,
    reason_options: [
      { code: "EXC-01", label: "Not a crop field", kind: "exclusion", category: null },
      { code: "FAILS-INC-01", label: "UAV imagery", kind: "fails_inclusion", category: null },
      { code: "OTHER", label: "Other", kind: "other", category: null },
    ],
    not_retrieved_reasons: ["no_access", "not_found", "no_reply", "other"],
    counts: counts(rows),
    rows,
  });
  await page.route("**/api/console/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/console/api/v1", "");
    if (path === "/review/next-step") return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: "" } } });
    if (path === "/charting" && request.method() === "GET") return route.fulfill({ json: table() });
    if (path === "/charting/events" && request.method() === "POST") {
      const events = (request.postDataJSON() as { events: { event_id: string; study_id: string; kind: string; value: Record<string, string> | null }[] }).events;
      posted.push(events);
      const results = events.map((event) => {
        const target = rows.find((r) => r.study_id === event.study_id)!;
        if (event.kind === "fulltext_status") {
          const v = event.value ?? { status: "to_get" };
          target.fulltext = { ...target.fulltext, status: v.status, reason: v.reason ?? null, reason_text: v.reason_text ?? null, requested_on: v.requested_on ?? null };
          target.heads = { ...target.heads, fulltext_status: event.event_id };
        } else if (event.kind === "fulltext_decision") {
          target.ft_decision = event.value ? { outcome: event.value.outcome, reason_code: event.value.reason_code ?? null, reason_text: event.value.reason_text ?? null } : null;
          target.heads = { ...target.heads, fulltext_decision: event.event_id };
        }
        return { event_id: event.event_id, result: "accepted" };
      });
      const touched = new Set(events.map((e) => e.study_id));
      return route.fulfill({ json: { results, counts: counts(rows), rows: rows.filter((r) => touched.has(r.study_id)) } });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  return posted;
}

const countsLine = (page: Page) => page.locator("[data-counts]");
const rowOf = (page: Page, id: string) => page.locator(`[data-study-row="${id}"]`);

test("the Full text view: status by keyboard on one row and on all, a decision with a reason, and undo", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const posted = await engine(page);
  await page.goto("/en/charting");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Charting");
  await expect(countsLine(page)).toHaveText("5 kept · 0 retrieved · 0 not retrieved · 5 to get · 0 included at full text · 0 excluded");

  await rowOf(page, "STU-001").click({ position: { x: 4, y: 4 } });
  await page.keyboard.press("r");
  await expect(rowOf(page, "STU-001").locator("[data-badge^=status]")).toHaveText("Retrieved");
  await expect(countsLine(page)).toContainText("1 retrieved");

  // All shown, Requested, Enter: one request with one event per record.
  await page.keyboard.press("a");
  await page.keyboard.press("q");
  await expect(page.locator("[data-confirm-line]")).toContainText("Mark 5 records as Requested? Enter to confirm · Esc to cancel");
  await page.keyboard.press("Enter");
  await expect(countsLine(page)).toContainText("0 retrieved");
  expect(posted.at(-1)).toHaveLength(5);
  await page.keyboard.press("Escape"); // clears the selection

  // Exclude the focused study with the first reason.
  await page.keyboard.press("e");
  await page.keyboard.press("1");
  await page.keyboard.press("Enter");
  await expect(rowOf(page, "STU-001").locator("[data-badge^=decision]")).toHaveText("Exclude");
  await expect(countsLine(page)).toContainText("1 excluded");

  // Undo takes the exclusion back; the row is undecided again.
  await page.keyboard.press("z");
  await expect(page.locator("[data-announce]")).toHaveText("Undone");
  await expect(countsLine(page)).toContainText("0 excluded");
  await expect(rowOf(page, "STU-001").locator("[data-badge^=decision]")).toHaveText("To decide");

  // Include the next study.
  await page.keyboard.press("j");
  await page.keyboard.press("i");
  await expect(rowOf(page, "STU-002").locator("[data-badge^=decision]")).toHaveText("Include");
  await expect(countsLine(page)).toContainText("1 included at full text");
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale}: axe finds no violation on the Full text view, contrast included`, async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await engine(page);
    await page.goto(`/${locale}/charting`);
    await expect(countsLine(page)).toBeVisible();
    // A row focused and a reason line open: the states a keyboard user sees.
    await rowOf(page, "STU-001").click({ position: { x: 4, y: 4 } });
    await page.keyboard.press("n");
    await expect(page.locator("[data-chip]").first()).toBeVisible();
    await page.addScriptTag({ path: AXE_PATH });
    const result = await page.evaluate(async () => {
      const axe = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
      const raw = await axe.run(document);
      return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
    });
    expect(result.violations).toEqual([]);
    expect(result.passes).toContain("color-contrast");
    if (locale === "ar") {
      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      expect(await rowOf(page, "STU-001").locator("[data-doi]").evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
    }
  });
}

test("at 390 px a read-only list: the desktop pointer, the cards, no action", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const posted = await engine(page);
  await page.goto("/en/charting");
  const phone = page.locator("[data-phone]");
  await expect(phone).toBeVisible();
  await expect(phone).toContainText("Charting is on your desktop.");
  await expect(phone.locator("[data-phone-card]")).toHaveCount(5);
  await expect(page.locator("[data-desktop]")).toBeHidden();
  await expect(phone.getByRole("button")).toHaveCount(0);
  await expect(phone.getByRole("combobox", { name: "Show" })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  await page.keyboard.press("r");
  expect(posted).toHaveLength(0);
});
