import type { Page, Route } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, test } from "./helpers";

/**
 * The M1b-1 screens' refusal states (spec 08) in a real browser, in both the
 * light and dark projects. The same-origin console proxy is answered at the
 * network boundary with the engine's response shapes, so each screen is the
 * real build reacting to a typed refusal. The live gate
 * (`playwright.live.config.ts`) covers the same screens against a real engine.
 */

const BATCHES_STALE = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-1",
  count: 1,
  batches: [{ batch_index: 1, batch_file: "batch_001.json", items: 3, decisions_file: null, decisions_count: null, collected: false, coverage: "INCOMPLETE", unresolved_rows: [], binding: { state: "STALE_BINDING", reason: "protocol changed" } }],
  missing: [],
};
const SUMMARY = { total: 3, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 3, conflicts: 0, lanes: { agent: 0, you: 0, second_screener: "PARKED" } };
const SETTINGS = { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" };
const PREVIEW_STALE = {
  identified: 3, duplicates_removed: 0, screened: 3, excluded: { total: 0, by_reason: {} }, unclear_to_full_text: 0, included: 3, not_yet_decided: 0,
  checks: [
    { name: "human_provenance", ok: true, detail: "" },
    { name: "no_open_conflicts", ok: true, detail: "0 open" },
    { name: "bound_to_current_protocol", ok: true, detail: "" },
    { name: "every_record_decided", ok: true, detail: "0 not yet decided" },
    { name: "projections_current", ok: false, detail: "PROJECTION_STALE: batch(es) 001 differ from the decision events" },
  ],
};

async function answer(page: Page, routes: Record<string, unknown | ((route: Route) => Promise<void>)>) {
  await page.route("**/api/console/api/v1/screening/**", async (route) => {
    const path = new URL(route.request().url()).pathname.replace("/api/console/api/v1/screening", "");
    const handler = routes[path];
    if (typeof handler === "function") return (handler as (r: Route) => Promise<void>)(route);
    if (handler === undefined) return route.fulfill({ status: 404, json: { detail: { code: "NOT_FOUND", message: path } } });
    return route.fulfill({ status: 200, json: handler });
  });
}

test.use({ viewport: DESKTOP_VIEWPORT });

test("home shows the protocol-changed card and sends the next step to prepare", async ({ page }) => {
  await answer(page, { "/summary": SUMMARY, "/ui/batches": BATCHES_STALE, "/decisions/conflicts": { items: [] }, "/settings": SETTINGS });
  await page.goto("/en/screening/home");
  const card = page.locator('[data-state="STALE_BINDING"]');
  await expect(card).toContainText("Protocol changed");
  await expect(card).toContainText("STALE_BINDING");
  await expect(page.getByRole("link", { name: "See the change" })).toHaveAttribute("href", "/en/screening/prepare");
});

test("triage shows the engine-unreachable card with a retry", async ({ page }) => {
  await answer(page, { "/settings": async (route: Route) => route.abort("connectionrefused") });
  await page.goto("/en/screening/triage");
  await expect(page.locator("section[role=alert]")).toContainText("could not be reached");
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});

test("publish shows the PROJECTION_STALE card and keeps Publish disabled", async ({ page }) => {
  await answer(page, {
    "/prisma/preview": PREVIEW_STALE,
    "/ui/batches": { ...BATCHES_STALE, batches: [{ ...BATCHES_STALE.batches[0], binding: undefined, coverage: "COMPLETE" }] },
    "/ui/batch/1/review": { shape: "ui07.review-state-v1", batch_index: 1, recommendation: { present: false }, resolution: { resolved: 3, total: 3, unresolved_rows: [] }, override: { superseded: false }, review: { present: true, approval_fingerprint: "sha256:x" }, deferral: { present: false }, missing: [] },
  });
  await page.goto("/en/screening/publish");
  await expect(page.locator('[data-state="PROJECTION_STALE"]')).toContainText("A decisions file is out of date");
  await expect(page.getByRole("button", { name: "Publish the screening" })).toBeDisabled();
});

test("prepare shows the snapshot refusal with the terminal command, in Arabic too", async ({ page }) => {
  await answer(page, {
    "/settings": SETTINGS,
    "/ui/batches": { shape: "ui07.screening-batches-v1", run_id: null, count: 0, batches: [], missing: [] },
    "/prepare": async (route: Route) => route.fulfill({ status: 409, json: { detail: { code: "SNAPSHOT_NOT_ACCEPTED", message: "no accepted corpus snapshot" } } }),
  });
  await page.goto("/ar/screening/prepare");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await page.getByRole("button", { name: "تحضير الدفعات" }).click();
  await page.getByRole("button", { name: "حضّر الآن" }).click();
  const card = page.locator('[data-state="SNAPSHOT_NOT_ACCEPTED"]');
  await expect(card).toContainText("nexus-scholar accept-corpus");
  await expect(card.locator("code")).toHaveAttribute("dir", "ltr");
});
