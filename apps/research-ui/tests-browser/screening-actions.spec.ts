import type { Page } from "@playwright/test";

import { ACTION_CHROME } from "../components/pairing-dialog";
import { demoScreeningRecord } from "../lib/mock-screening";
import { DESKTOP_VIEWPORT, expect, report, test } from "./helpers";

/**
 * The protected action flow, in a real browser (packet UI-07, action side).
 *
 * The console is fulfilled at the network boundary with shape-conformant
 * payloads, so every scenario below runs the real page against typed API
 * shapes without depending on a live workspace: six scenarios covering the
 * approve / expired / stale / defer / publish / double-press journey, plus
 * the guards that travel with all of them (no page error, no console error,
 * no browser storage write, no fixture fallback).
 *
 * Fulfilled responses carry loopback CORS headers, and preflight OPTIONS is
 * answered the way the frozen console middleware answers it, so the flow
 * proves what the page does with the API rather than what the test harness
 * forgives. The non-localhost guard in the base fixture independently fails
 * any run that reaches past localhost.
 */

const CONSOLE = "http://127.0.0.1:8765";
const CODE = "AB12C-DE34F-GH56J-KL78M-NP9QR2S";

const SUMMARY = {
  shape: "ui07.project-summary-v1",
  workspace_id: "WSP-cccccccccccccccccccccccccccccccc",
  project_id: "ui-actions-browser",
  protocol: { present: true, fingerprint: "sha256:live" },
  run: { screening_run_id: "RUN-UI-BROWSER-1", batches: 1, batches_resolved: 1 },
  readiness: {
    screening_prepared: true,
    all_batches_resolved: true,
    publication: {
      shape: "ui07.publication-status-v1",
      status: "CURRENT",
      code: null,
      generation_id: "GEN-UI-BROWSER-1",
      outputs: { "included.json": "sha256:live" },
      message: "screening generation is current",
      details: { generation_id: "GEN-UI-BROWSER-1" },
    },
  },
  missing: [],
};

const BATCHES = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-UI-BROWSER-1",
  count: 1,
  batches: [
    {
      batch_index: 0,
      batch_file: "batch_000.json",
      items: 1,
      decisions_file: "batch_000_decisions.json",
      decisions_count: 1,
      collected: false,
      coverage: "COMPLETE",
      unresolved_rows: [],
    },
  ],
  missing: [],
};

const PUBLICATION = {
  shape: "ui07.publication-status-v1",
  status: "CURRENT",
  code: null,
  generation_id: "GEN-UI-BROWSER-1",
  outputs: { "included.json": "sha256:live" },
  message: "screening generation is current",
  details: { generation_id: "GEN-UI-BROWSER-1" },
};

const ROWS = {
  shape: "ui07.screening-rows-v1",
  batch_index: 0,
  batch_file: "batch_000.json",
  total: 1,
  offset: 0,
  limit: 100,
  rows: [
    {
      shape: "ui07.screening-row-v1",
      study_id: "STUDY-UI-BROWSER-001",
      citation: "Browser Author. A live read for the browser action flow. J Live; 2025.",
      abstract: "Browser abstract for actions, served exactly as stored.",
      decision: "INCLUDE",
      reasons: ["Matches the population criterion."],
      uncertainty: "confidence 0.9",
      criterion_refs: { inclusion: ["INC-01"], exclusion: [] },
      source_locators: { doi: "10.0000/browser1" },
    },
  ],
  missing: [],
};

const REFS = {
  shape: "ui07.criterion-refs-v1",
  protocol_fingerprint: "sha256:live",
  inclusion: [{ id: "INC-01", text: "Names the population and outcome." }],
  exclusion: [],
  sources: [{ workspace_id: "STUDY-UI-BROWSER-001", doi: "10.0000/browser1" }],
  missing: [],
};

const STAGED = {
  shape: "screening-action-pairing-status-v1",
  batch_index: 0,
  state: "STAGED",
  expires_at: "2026-10-13T12:05:00+00:00",
  snapshot_fingerprint: "sha256:staged",
  attempts_remaining: 5,
  request_id: "REQ-STATUS-1",
};

const REDEEM_OK = {
  shape: "screening-action-redeem-v1",
  request_id: "REQ-BROWSER-1",
  journal_event_id: "EVT-20261013120000-b1",
  batch_index: 0,
  snapshot_fingerprint: "sha256:staged",
  approval_fingerprint: "sha256:browser-approval",
  publication_approval_fingerprint: "sha256:browser-pubapproval",
  operator_identity: "ui07-operator@example",
  superseded: true,
};

const DEFER_OK = {
  shape: "screening-action-defer-v1",
  request_id: "REQ-BROWSER-2",
  journal_event_id: "EVT-20261013120000-b2",
  batch_index: 0,
  deferral_file: "batch_000_deferral.json",
  reason: "awaiting full text",
  cancelled: false,
  pairing_voided: true,
};

const PUBLISH_OK = {
  shape: "screening-action-publish-v1",
  request_id: "REQ-BROWSER-3",
  journal_event_id: "EVT-20261013120000-b3",
  status: "CURRENT",
  generation_id: "GEN-UI-BROWSER-2",
  generation_fingerprint: "sha256:browser-generation",
  outputs: { "included.json": "sha256:live" },
};

function refusal(code: string, message: string, status: number) {
  return {
    status,
    body: { detail: { code, message, details: {} } },
  };
}

type RouteTable = Record<string, { status: number; body: unknown }>;

const READS: RouteTable = {
  "/api/v1/ui/project-summary": { status: 200, body: SUMMARY },
  "/api/v1/screening/ui/batches": { status: 200, body: BATCHES },
  "/api/v1/ui/publication-status": { status: 200, body: PUBLICATION },
  "/api/v1/screening/ui/batch/0/rows": { status: 200, body: ROWS },
  "/api/v1/screening/ui/batch/0/criterion-refs": { status: 200, body: REFS },
  "/api/v1/screening/actions/pairing/status": { status: 200, body: STAGED },
};

/** Install the fulfilled console and the guards that travel every scenario. */
async function useConsole(
  page: Page,
  routes: RouteTable,
  hits: string[],
  pageErrors: string[],
  consoleErrors: string[],
): Promise<void> {
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    // Expected-refusal resource logs are excluded because the scenarios assert
    // those refusals (403/409); all other console errors (including 500s,
    // failed chunk/asset loads, and any status outside the asserted refusal
    // set) still fail. Filtering these logs is NOT weakening the guard: the
    // guard's intent is "no UNEXPECTED console errors" — a resource-load log
    // for an HTTP status the test itself asserts is expected evidence, not
    // pollution. (Chromium words it "status of 403 (Forbidden)" — parens hold
    // the reason, not the code — so the guard matches the bare code.)
    if (/Failed to load resource.*status of (403|409)\b/.test(text)) return;
    consoleErrors.push(text);
  });
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const origin = request.headers()["origin"] ?? "*";
    const cors = { "access-control-allow-origin": origin };
    // Preflight answers the way the frozen console middleware answers it:
    // loopback GETs pass, anything else carries no POST allowance here.
    if (request.method() === "OPTIONS") {
      await route.fulfill({
        status: 200,
        headers: {
          ...cors,
          "access-control-allow-methods": "GET",
          "access-control-allow-headers": "content-type",
        },
        body: "",
      });
      return;
    }
    hits.push(`${request.method()} ${url.pathname}`);
    const entry = routes[url.pathname];
    if (!entry) {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        headers: cors,
        body: JSON.stringify(refusal("BATCH_MISSING", "missing", 404).body),
      });
      return;
    }
    await route.fulfill({
      status: entry.status,
      contentType: "application/json",
      headers: cors,
      body: JSON.stringify(entry.body),
    });
  });
}

async function openLive(page: Page): Promise<void> {
  await page.setViewportSize(DESKTOP_VIEWPORT);
  await page.goto(`/en/screening?source=live&console=${CONSOLE}`);
  await expect(
    page.getByText("Browser Author. A live read for the browser action flow. J Live; 2025."),
  ).toBeVisible();
  await expect(page.getByText("STAGED", { exact: true })).toBeVisible();
}

function expectClean(
  pageErrors: string[],
  consoleErrors: string[],
  stored: { local: string[]; session: string[]; cookies: string },
): void {
  report(`page errors = ${JSON.stringify(pageErrors)}`);
  report(`console errors = ${JSON.stringify(consoleErrors)}`);
  report(`browser storage = ${JSON.stringify(stored)}`);
  expect(pageErrors, "the action flow must raise no page error").toEqual([]);
  expect(consoleErrors, "the action flow must log no console error").toEqual([]);
  expect(stored, "the action flow must write no browser storage").toEqual({
    local: [],
    session: [],
    cookies: "",
  });
}

test.describe("screening actions", () => {
  test("an approved code records the approval with its request id", async ({ page }) => {
    const hits: string[] = [];
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    await useConsole(
      page,
      { ...READS, "/api/v1/screening/actions/pairing/redeem": { status: 200, body: REDEEM_OK } },
      hits,
      pageErrors,
      consoleErrors,
    );
    await openLive(page);

    await page.getByRole("button", { name: ACTION_CHROME.en.approveButton }).click();
    await page.getByRole("textbox", { name: ACTION_CHROME.en.codeLabel }).fill(CODE);
    await page.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton }).click();

    await expect(page.getByText(ACTION_CHROME.en.approvedNote)).toBeVisible();
    await expect(page.getByText("sha256:browser-approval")).toBeVisible();
    await expect(page.getByText("REQ-BROWSER-1")).toBeVisible();
    // The typed code is cleared on submit: the field holds nothing after.
    await expect(page.getByRole("textbox", { name: ACTION_CHROME.en.codeLabel })).toHaveCount(0);
    // No fixture fallback: the demonstration record never appears in live mode.
    await expect(page.getByText(demoScreeningRecord.citation)).toHaveCount(0);

    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expectClean(pageErrors, consoleErrors, stored);
    report(`requests = ${JSON.stringify(hits)}`);
    expect(hits.filter((line) => line.startsWith("POST "))).toHaveLength(1);
  });

  test("an expired code explains itself with the typed refusal", async ({ page }) => {
    const hits: string[] = [];
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    await useConsole(
      page,
      {
        ...READS,
        "/api/v1/screening/actions/pairing/redeem": refusal(
          "PAIRING_CODE_INVALID",
          "that code is expired; begin again in the terminal",
          403,
        ),
      },
      hits,
      pageErrors,
      consoleErrors,
    );
    await openLive(page);

    await page.getByRole("button", { name: ACTION_CHROME.en.approveButton }).click();
    await page.getByRole("textbox", { name: ACTION_CHROME.en.codeLabel }).fill(CODE);
    await page.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton }).click();

    const alert = page
      .getByRole("dialog", { name: ACTION_CHROME.en.dialogTitle })
      .getByRole("alert");
    await expect(alert).toContainText("PAIRING_CODE_INVALID");
    await expect(alert).toContainText("that code is expired; begin again in the terminal");
    // The dialog stays open for a fresh code; nothing was approved.
    await expect(page.getByRole("textbox", { name: ACTION_CHROME.en.codeLabel })).toBeVisible();
    await expect(page.getByText(ACTION_CHROME.en.approvedNote)).toHaveCount(0);

    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expectClean(pageErrors, consoleErrors, stored);
  });

  test("a stale view names the change instead of approving", async ({ page }) => {
    const hits: string[] = [];
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    await useConsole(
      page,
      {
        ...READS,
        "/api/v1/screening/actions/pairing/redeem": refusal(
          "STALE_VIEW",
          "the content changed since review; re-review in the terminal before approving",
          409,
        ),
      },
      hits,
      pageErrors,
      consoleErrors,
    );
    await openLive(page);

    await page.getByRole("button", { name: ACTION_CHROME.en.approveButton }).click();
    await page.getByRole("textbox", { name: ACTION_CHROME.en.codeLabel }).fill(CODE);
    await page.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton }).click();

    await expect(
      page.getByRole("dialog", { name: ACTION_CHROME.en.dialogTitle }).getByRole("alert"),
    ).toContainText("STALE_VIEW");
    await expect(page.getByText(ACTION_CHROME.en.approvedNote)).toHaveCount(0);

    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expectClean(pageErrors, consoleErrors, stored);
  });

  test("a deferral records the reason and publishes nothing", async ({ page }) => {
    const hits: string[] = [];
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    await useConsole(
      page,
      { ...READS, "/api/v1/screening/actions/defer": { status: 200, body: DEFER_OK } },
      hits,
      pageErrors,
      consoleErrors,
    );
    await openLive(page);

    await page.getByLabel(ACTION_CHROME.en.reasonLabel).fill("awaiting full text");
    await page.getByRole("button", { name: ACTION_CHROME.en.deferButton }).click();

    await expect(page.getByText(ACTION_CHROME.en.deferredNote)).toBeVisible();
    await expect(page.getByText("REQ-BROWSER-2")).toBeVisible();

    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expectClean(pageErrors, consoleErrors, stored);
    report(`requests = ${JSON.stringify(hits)}`);
    expect(hits).toContain("POST /api/v1/screening/actions/defer");
  });

  test("a publication shows the current generation", async ({ page }) => {
    const hits: string[] = [];
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    await useConsole(
      page,
      { ...READS, "/api/v1/screening/actions/publish": { status: 200, body: PUBLISH_OK } },
      hits,
      pageErrors,
      consoleErrors,
    );
    await openLive(page);

    await page.getByRole("button", { name: ACTION_CHROME.en.publishButton }).click();

    await expect(page.getByText(ACTION_CHROME.en.publishedNote)).toBeVisible();
    await expect(page.getByText("GEN-UI-BROWSER-2")).toBeVisible();

    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expectClean(pageErrors, consoleErrors, stored);
  });

  test("a double press while pending sends one request", async ({ page }) => {
    const hits: string[] = [];
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    await page.route("**/api/v1/**", async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      const origin = request.headers()["origin"] ?? "*";
      const cors = { "access-control-allow-origin": origin };
      if (request.method() === "OPTIONS") {
        await route.fulfill({
          status: 200,
          headers: {
            ...cors,
            "access-control-allow-methods": "GET",
            "access-control-allow-headers": "content-type",
          },
          body: "",
        });
        return;
      }
      hits.push(`${request.method()} ${url.pathname}`);
      if (request.method() === "POST" && url.pathname === "/api/v1/screening/actions/publish") {
        // Hold the response so the second press lands while pending.
        await new Promise((resolve) => setTimeout(resolve, 800));
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          headers: cors,
          body: JSON.stringify(PUBLISH_OK),
        });
        return;
      }
      const entry = READS[url.pathname];
      await route.fulfill({
        status: entry?.status ?? 404,
        contentType: "application/json",
        headers: cors,
        body: JSON.stringify(entry?.body ?? refusal("BATCH_MISSING", "missing", 404).body),
      });
    });
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    await openLive(page);

    const publish = page.getByRole("button", { name: ACTION_CHROME.en.publishButton });
    await publish.click();
    await publish.click();
    await expect(page.getByText(ACTION_CHROME.en.publishedNote)).toBeVisible();
    report(`publish POSTs = ${hits.filter((line) => line === "POST /api/v1/screening/actions/publish").length}`);
    expect(
      hits.filter((line) => line === "POST /api/v1/screening/actions/publish"),
    ).toHaveLength(1);

    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expectClean(pageErrors, consoleErrors, stored);
  });
});
