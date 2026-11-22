import { createRequire } from "node:module";

import type { Page } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * The look-up of open-access copies (M12a Part F, spec 03) in a real browser on
 * the production build. As in the other charting specs, the console is answered
 * at the network boundary by a small stateful fake in the engine's shapes
 * (`src/scholar_harness/charting/fetch.py`, `tests/console/test_charting_fetch_api.py`):
 * the table with its waiting files, the plan, a run that moves on each read, the
 * cancel, the manifest of one record, the waiting PDF (the context's route, so a
 * new tab is answered too), and the confirm and discard events with their undo.
 * No service is asked and no console runs. It runs in light (`chromium`) and
 * dark (`chromium-dark`).
 */

const AXE_PATH = createRequire(import.meta.url).resolve("axe-core");

type Pending = Record<string, unknown> & { manifest_row: string; sha256: string; duplicate_of: string[] };
type Row = Record<string, unknown> & {
  study_id: string;
  title: string;
  kept: boolean;
  fulltext: Record<string, unknown> & { status: string; pending_fetch: Pending | null; attachment: unknown };
  ft_decision: { outcome: string; reason_code?: string | null } | null;
  heads: Record<string, string | null>;
};
type Event = { event_id: string; study_id: string; kind: string; value: Record<string, string> | null; supersedes?: string };

const TITLES = ["Weed mapping from UAV imagery", "Deep learning for crop rows", "Multispectral drone survey", "Sugar beet weed detection", "Herbicide spot spraying"];

function pending(i: number, over: Record<string, unknown> = {}): Pending {
  return {
    manifest_row: `FMR-${String(i).padStart(24, "0")}`,
    run_id: "FR-000000000000000000000001",
    source: "Unpaywall",
    source_name: "Europe PMC",
    host: "europepmc.org",
    host_type: "repository",
    address: `https://europepmc.org/articles/PMC${i}/pdf/paper.pdf`,
    version: "publishedVersion",
    version_label: "publishedVersion",
    licence: "cc-by",
    size: 1_258_291,
    sha256: String(i).repeat(64),
    identity: i === 2 ? "not found: check it" : "doi found",
    at: "2026-11-22T14:30:00Z",
    duplicate_of: [],
    ...over,
  };
}

function row(i: number, waiting: boolean): Row {
  return {
    study_id: `STU-00${i}`,
    title: TITLES[i - 1],
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
    ta_decision: "INCLUDE",
    ta_reason: "",
    kept: true,
    new_since: null,
    fulltext: {
      status: "to_get",
      requested_on: null,
      reason: null,
      reason_text: null,
      attachment: null,
      link: null,
      pending_fetch: waiting ? pending(i) : null,
      last_lookup: waiting
        ? { run_id: "FR-000000000000000000000001", manifest_row: `FMR-${String(i).padStart(24, "0")}`, at: "2026-11-22T14:30:00Z", outcome: "ACQUIRED", try_later: false }
        : i === 5
          ? { run_id: "FR-000000000000000000000001", manifest_row: "FMR-000000000000000000000099", at: "2026-11-22T14:31:00Z", outcome: "PDF_NOT_FETCHED", message: "not a PDF", try_later: false }
          : null,
      discarded_fetch: null,
    },
    ft_decision: null,
    heads: { fulltext_status: null, fulltext_decision: null, attachment: null, link: null, fetched_confirm: null, fetched_discard: null },
  };
}

function runView(over: Record<string, unknown>) {
  return {
    state: "running", run_id: "FR-000000000000000000000002", total: 2, reached: 0, found: 0, downloaded: 0, failed_checks: 0, errors: {},
    no_open_copy: 0, no_direct_pdf: 0, try_later: 0, skipped_no_id: 0, not_reached: 0, providers: ["unpaywall"], email: "you@example.org",
    openalex_key_set: false, now: { phase: "starting", host: null }, recent_requests: [], started_at: "2026-11-22T14:00:00Z", finished_at: null, error: null,
    ...over,
  };
}

async function engine(page: Page, options: { waiting?: number[]; runs?: Record<string, unknown>[] } = {}) {
  const waiting = new Set(options.waiting ?? [1, 2, 3]);
  const rows = [1, 2, 3, 4, 5].map((i) => row(i, waiting.has(i)));
  const posted: Event[][] = [];
  const starts: unknown[] = [];
  const opened: string[] = [];
  let runs: Record<string, unknown>[] = options.runs ?? [{ state: "idle", run_id: null }];
  const saved = new Map<string, { pending: Pending; status: string }>();
  const counts = () => {
    const live = rows.filter((r) => r.kept);
    const by = (test: (r: Row) => boolean) => live.filter(test).length;
    const w = (r: Row) => Boolean(r.fulltext.pending_fetch);
    return {
      kept: live.length, to_get: by((r) => r.fulltext.status === "to_get" && !w(r)), requested: by((r) => r.fulltext.status === "requested" && !w(r)),
      retrieved: by((r) => r.fulltext.status === "retrieved"), not_retrieved: by((r) => r.fulltext.status === "not_retrieved" && !w(r)), to_confirm: by(w),
      included: by((r) => r.ft_decision?.outcome === "INCLUDE"), excluded: by((r) => r.ft_decision?.outcome === "EXCLUDE"), to_decide: by((r) => !r.ft_decision),
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
    counts: counts(), rows,
  });
  // The waiting file, served to whichever tab asks (a new tab does not see the page's routes).
  await page.context().route("**/api/console/api/v1/charting/records/*/fetched", async (route) => {
    const study = decodeURIComponent(/\/records\/([^/]+)\/fetched$/.exec(new URL(route.request().url()).pathname)![1]);
    opened.push(study);
    return route.fulfill({ status: 200, body: Buffer.from("%PDF-1.7\n%%EOF\n"), headers: { "content-type": "application/pdf", "content-disposition": "inline", "x-content-type-options": "nosniff" } });
  });
  await page.route("**/api/console/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/console/api/v1", "");
    const method = request.method();
    if (path === "/review/next-step") return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: "" } } });
    if (path === "/charting" && method === "GET") return route.fulfill({ json: table() });
    if (path === "/charting/fetch/plan" && method === "GET") {
      const ids = url.searchParams.get("ids")?.split(",") ?? null;
      const scope = rows.filter((r) => (ids ? ids.includes(r.study_id) : r.fulltext.status === "to_get"));
      const asked = scope.filter((r) => !r.fulltext.pending_fetch && !r.fulltext.attachment);
      return route.fulfill({
        json: {
          shape: "charting.fetch-plan-v1", scope: ids ? "ids" : "to_get", total: scope.length, asked: asked.length, with_doi: asked.length, with_arxiv_only: 0, neither: 0,
          arxiv_id_incomplete: 0, already_have_file: 0, waiting: scope.length - asked.length, discarded: 0, email: "you@example.org", openalex_key_set: false,
          services: { unpaywall: "asked", openalex: "not_asked", arxiv: "not_needed" }, notes: [],
        },
      });
    }
    if (path === "/charting/fetch" && method === "POST") {
      starts.push(request.postDataJSON());
      runs = [
        runView({ reached: 0 }),
        runView({ reached: 1, found: 1, downloaded: 1, now: { phase: "downloading", host: "europepmc.org" }, recent_requests: [{ host: "europepmc.org", answer: "stored" }] }),
      ];
      return route.fulfill({ status: 202, json: runs[0] });
    }
    if (path === "/charting/fetch" && method === "GET") {
      const answer = runs.length > 1 ? runs.shift()! : runs[0];
      return route.fulfill({ json: answer });
    }
    if (path === "/charting/fetch/cancel" && method === "POST") {
      runs = [
        { ...runs[0], state: "cancelling" },
        runView({ state: "cancelled", reached: 1, found: 1, downloaded: 1, not_reached: 1, finished_at: "2026-11-22T14:05:00Z" }),
      ];
      return route.fulfill({ json: runs[0] });
    }
    if (/^\/charting\/records\/STU-005\/fetch$/.test(path)) {
      return route.fulfill({
        json: {
          shape: "charting.fetch-tried-v1", study_id: "STU-005",
          rows: [{
            row_id: "FMR-000000000000000000000099", run_id: "FR-000000000000000000000001", study_id: "STU-005", outcome: "PDF_NOT_FETCHED",
            address: "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5/pdf/a.pdf", version: "acceptedVersion", version_label: "acceptedVersion", license: null, provider: "unpaywall",
            checks: {}, time: "2026-11-22T14:31:00Z",
            lookups: [{ service: "unpaywall", state: "ANSWERED", http_status: 200, error: null }, { service: "openalex", state: "NOT_ASKED", http_status: null, error: null }],
            requests: [{ url: "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5/pdf/a.pdf", host: "www.ncbi.nlm.nih.gov", http_status: 403, error: "HTTP 403", redirects: [] }],
          }],
        },
      });
    }
    if (path === "/charting/events" && method === "POST") {
      const events = (request.postDataJSON() as { events: Event[] }).events;
      posted.push(events);
      const results: Record<string, unknown>[] = [];
      for (const event of events) {
        const target = rows.find((r) => r.study_id === event.study_id)!;
        const ft = target.fulltext;
        if (event.kind === "fetched_confirm" && event.value) {
          saved.set(event.event_id, { pending: ft.pending_fetch!, status: ft.status });
          target.fulltext = { ...ft, status: "retrieved", attachment: { name: `${target.study_id}.pdf`, size: 1_258_291, sha256: ft.pending_fetch!.sha256, path: "", origin: "fetched" }, pending_fetch: null };
          target.heads = { ...target.heads, fetched_confirm: event.event_id };
        } else if (event.kind === "fetched_confirm") {
          const was = saved.get(event.supersedes!)!;
          target.fulltext = { ...ft, status: was.status, attachment: null, pending_fetch: was.pending };
        } else if (event.kind === "fetched_discard" && event.value) {
          saved.set(event.event_id, { pending: ft.pending_fetch!, status: ft.status });
          target.fulltext = { ...ft, pending_fetch: null, discarded_fetch: { reason: event.value.reason, reason_text: event.value.reason_text ?? null, at: "", manifest_row: event.value.manifest_row } };
          target.heads = { ...target.heads, fetched_discard: event.event_id };
        } else if (event.kind === "fulltext_decision") {
          target.ft_decision = event.value ? { outcome: event.value.outcome, reason_code: event.value.reason_code ?? null } : null;
          target.heads = { ...target.heads, fulltext_decision: event.event_id };
        }
        results.push({ event_id: event.event_id, result: "accepted" });
      }
      const touched = new Set(events.map((e) => e.study_id));
      return route.fulfill({ json: { results, counts: counts(), rows: rows.filter((r) => touched.has(r.study_id)) } });
    }
    return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
  });
  return { posted, starts, opened };
}

const rowOf = (page: Page, id: string) => page.locator(`[data-desktop] [data-study-row="${id}"]`);

async function axe(page: Page) {
  await page.addScriptTag({ path: AXE_PATH });
  return page.evaluate(async () => {
    const run = (globalThis as unknown as { axe: { run: (ctx: Document) => Promise<{ violations: { id: string; nodes: { target: unknown }[] }[]; passes: { id: string }[] }> } }).axe;
    const raw = await run.run(document);
    return { violations: raw.violations.map((v) => `${v.id} ${JSON.stringify(v.nodes.map((n) => n.target))}`), passes: raw.passes.map((p) => p.id) };
  });
}

test("L shows the plan, Enter starts the run; its progress moves; Cancel stops after the record in hand", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const fake = await engine(page, { waiting: [] });
  await page.goto("/en/charting");
  await expect(page.locator("[data-counts]")).toBeVisible();
  await rowOf(page, "STU-001").click({ position: { x: 4, y: 4 } });
  await page.keyboard.press("l");
  const plan = page.locator("[data-desktop] [data-fetch-plan]");
  await expect(plan).toHaveAttribute("data-fetch-plan", "ready");
  await expect(plan).toContainText("Look up open-access copies of 5 records?");
  await expect(plan).toContainText("Asks Unpaywall with your contact e-mail you@example.org, for the 5 records with a DOI.");
  await expect(plan).toContainText("OpenAlex is not asked: SCHOLAR_OPENALEX_KEY is not set.");
  await expect(plan).toBeFocused();
  await page.keyboard.press("Enter");
  expect(fake.starts).toEqual([{ scope: "to_get", confirm: true }]);
  const card = page.locator("[data-desktop] [data-fetch-run]");
  await expect(card).toBeVisible();
  await expect(page.locator("[data-desktop] [data-fetch-announce]")).toHaveText("Look-up started: 2 records");
  await expect(card.getByRole("progressbar")).toHaveAttribute("aria-valuetext", "1 of 2 records", { timeout: 8000 });
  await expect(card).toContainText("Downloading from europepmc.org");
  await card.getByRole("button", { name: "Cancel the look-up" }).click();
  await expect(card).toContainText("Stopping after the record in hand…");
  await expect(page.locator("[data-desktop] [data-fetch-summary]")).toContainText("Look-up cancelled", { timeout: 8000 });
  await expect(page.locator("[data-desktop] [data-fetch-summary] [data-summary-line=notReached]")).toHaveText("1 not reached");
});

test("filter to confirm; open, confirm and discard by keyboard within four keypresses per row", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const fake = await engine(page, { waiting: [1, 3, 4] });
  await page.goto("/en/charting");
  await expect(page.locator("[data-counts]")).toContainText("3 to confirm");
  await page.locator("[data-desktop]").getByRole("combobox", { name: "Show" }).selectOption("toConfirm");
  await expect(page.locator("[data-desktop] [data-study-row]")).toHaveCount(3);
  await expect(page.locator("[data-desktop] [data-shown]")).toHaveText("3 of 5 shown");
  await rowOf(page, "STU-001").click({ position: { x: 4, y: 4 } });

  // Row 1: open the file (O), then confirm it (C): two keypresses.
  const popup = page.waitForEvent("popup");
  await page.keyboard.press("o");
  await (await popup).close();
  expect(fake.opened).toContain("STU-001");
  await page.keyboard.press("c");
  await expect(page.locator("[data-desktop] [data-study-row]")).toHaveCount(2);
  await expect(rowOf(page, "STU-003")).toBeFocused();
  await expect(page.locator("[data-announce]")).toHaveText("Confirmed. 2 files to confirm.");

  // Row 3: discard it as the wrong paper (D, 1, Enter): three keypresses.
  await page.keyboard.press("d");
  await page.keyboard.press("1");
  await page.keyboard.press("Enter");
  await expect(page.locator("[data-desktop] [data-study-row]")).toHaveCount(1);
  await expect(rowOf(page, "STU-004")).toBeFocused();

  // Row 4: confirm it (C): one keypress; the list is empty and the option stays.
  await page.keyboard.press("c");
  await expect(page.locator("[data-desktop] [data-empty-filter]")).toHaveText("No fetched file is waiting for you.");
  expect(fake.posted.map((events) => events.map((e) => [e.study_id, e.kind, e.value?.reason ?? null]))).toEqual([
    [["STU-001", "fetched_confirm", null]],
    [["STU-003", "fetched_discard", "wrong_paper"]],
    [["STU-004", "fetched_confirm", null]],
  ]);
  await expect(page.locator("[data-counts]")).toContainText("2 retrieved");
  await expect(page.locator("[data-counts]")).not.toContainText("to confirm");
});

test("a failed row keeps its status, says what came of it and shows what was tried", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page, { waiting: [] });
  await page.goto("/en/charting");
  const failed = rowOf(page, "STU-005");
  await expect(failed.locator("[data-badge^=status]")).toHaveText("To get");
  await expect(failed.locator("[data-last-lookup]")).toContainText("the file failed the checks: not a PDF (an HTML page, for example)");
  await failed.getByRole("button", { name: "What was tried" }).click();
  const panel = failed.locator("[data-tried]");
  await expect(panel).toContainText("Unpaywall: open copy listed");
  await expect(panel).toContainText("OpenAlex: not asked (SCHOLAR_OPENALEX_KEY is not set)");
  await expect(panel).toContainText("www.ncbi.nlm.nih.gov · Accepted manuscript · Licence not given · HTTP 403: the host refused");
  await expect(panel).toContainText("PubMed Central did not give its PDF to this app.");
  await expect(panel).toContainText("This is not a paywall determination.");
  await expect(failed.getByRole("button", { name: "What was tried" })).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Escape");
  await expect(panel).toHaveCount(0);
});

test("I on a waiting row asks first, then Enter confirms the file and includes the study in one request", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  const fake = await engine(page, { waiting: [1, 3] });
  await page.goto("/en/charting");
  await rowOf(page, "STU-001").click({ position: { x: 4, y: 4 } });
  await page.keyboard.press("i");
  await expect(page.locator("[data-desktop] [data-confirm-line]")).toContainText("Confirm this PDF as the full text? Enter to confirm and decide · Esc to cancel");
  expect(fake.posted).toHaveLength(0);
  await page.keyboard.press("Enter");
  await expect(rowOf(page, "STU-001").locator("[data-badge^=decision]")).toHaveText("Include");
  await expect(rowOf(page, "STU-001").locator("[data-badge^=status]")).toHaveText("Retrieved");
  expect(fake.posted).toHaveLength(1);
  expect(fake.posted[0].map((e) => e.kind)).toEqual(["fetched_confirm", "fulltext_decision"]);
  // G on another waiting row is refused in words, and nothing is sent.
  await rowOf(page, "STU-003").click({ position: { x: 4, y: 4 } });
  await page.keyboard.press("g");
  await expect(page.locator("[data-desktop] [data-status-line]")).toHaveText("A fetched file is waiting on this row. Confirm it or discard it first.");
  expect(fake.posted).toHaveLength(1);
});

for (const locale of ["en", "ar"] as const) {
  test(`${locale} at 390 px: the waiting file is read-only, Open is a 44 px link, the desktop line, no button`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const fake = await engine(page, { waiting: [1, 2], runs: [runView({ reached: 1 })] });
    await page.goto(`/${locale}/charting`);
    const phone = page.locator("[data-phone]");
    await expect(phone.locator("[data-phone-pending]")).toHaveCount(2);
    const first = phone.locator("[data-phone-pending]").first();
    const open = first.locator("[data-open-fetched]");
    await expect(open).toBeVisible();
    expect((await open.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await expect(first.locator("[data-fetch-mobile]")).toBeVisible();
    await expect(phone.getByRole("button")).toHaveCount(0);
    await expect(phone.locator("[data-fetch-run]")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
    for (const key of ["l", "c", "d"]) await page.keyboard.press(key);
    expect(fake.posted).toHaveLength(0);
    expect(fake.starts).toHaveLength(0);
    if (locale === "en") {
      await expect(first.locator("[data-fetch-mobile]")).toHaveText("Confirm or discard this file on your desktop.");
    } else {
      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      await expect(first.locator("[data-fetch-mobile]")).toHaveText("أكّد هذا الملف أو استبعده على حاسوبك.");
      // The host stays left to right inside the right-to-left line.
      expect(await first.locator("[data-fetch-source] [dir=ltr]").evaluate((el) => getComputedStyle(el).direction)).toBe("ltr");
    }
  });
}

test("axe finds no violation with a run, waiting files, the tried panel and the plan open", async ({ page }) => {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await engine(page, { waiting: [1, 2], runs: [runView({ reached: 1, now: { phase: "downloading", host: "europepmc.org" } })] });
  await page.goto("/en/charting");
  await expect(page.locator("[data-desktop] [data-fetch-run]")).toBeVisible();
  await rowOf(page, "STU-005").getByRole("button", { name: "What was tried" }).click();
  await expect(rowOf(page, "STU-005").locator("[data-tried-not-paywall]")).toBeVisible();
  await page.locator("[data-desktop] [data-fetch-requests]").click();
  let result = await axe(page);
  expect(result.violations).toEqual([]);
  expect(result.passes).toContain("color-contrast");
  await rowOf(page, "STU-001").click({ position: { x: 4, y: 4 } });
  await page.keyboard.press("l");
  await expect(page.locator("[data-desktop] [data-fetch-plan]")).toHaveAttribute("data-fetch-plan", "ready");
  result = await axe(page);
  expect(result.violations).toEqual([]);
  await page.keyboard.press("Escape");
  await page.keyboard.press("d");
  await expect(page.locator("[data-desktop] [data-chip]").first()).toBeVisible();
  result = await axe(page);
  expect(result.violations).toEqual([]);
});
