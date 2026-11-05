import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PUBLISH_COPY, ScreeningPublish } from "@/components/screening-publish";
import { SUPPORTED_LOCALES } from "@/i18n";

/**
 * Publish (spec 09) in jsdom. The PRISMA preview is the engine's recorded
 * fixture; approval state comes from `/ui/batch/{n}/review`. The approval code
 * is typed by the researcher (the engine prints it in its terminal) and is
 * sent once to redeem, never kept.
 */

const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;
const PREVIEW = JSON.parse(readFileSync(`${FIXTURES}prisma_preview.json`, "utf-8")).response.body;

const BATCHES = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-1",
  count: 1,
  batches: [{ batch_index: 1, batch_file: "batch_001.json", items: 3, decisions_file: "batch_001_decisions.json", decisions_count: 3, collected: false, coverage: "COMPLETE", unresolved_rows: [] }],
  missing: [],
};

function review(approved: boolean) {
  return {
    shape: "ui07.review-state-v1",
    batch_index: 1,
    recommendation: { present: false },
    resolution: { resolved: 3, total: 3, unresolved_rows: [] },
    override: { superseded: false },
    review: approved ? { present: true, approval_fingerprint: "sha256:x" } : { present: false },
    deferral: { present: false },
    missing: [],
  };
}

function engine(options: { preview?: unknown; approved?: boolean; redeem?: Response } = {}) {
  let approved = options.approved ?? false;
  const log: { method: string; path: string; body: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? JSON.parse(String(init.body)) : null;
      log.push({ method, path, body });
      const ok = (b: unknown) => new Response(JSON.stringify(b), { status: 200, headers: { "content-type": "application/json" } });
      if (path === "/prisma/preview") return ok(options.preview ?? PREVIEW);
      if (path === "/ui/batches") return ok(BATCHES);
      if (path === "/ui/batch/1/review") return ok(review(approved));
      if (path === "/actions/pairing/begin") return ok({ batch_index: 1, snapshot_fingerprint: "sha256:s", code_expires_at: "2026-11-05T10:05:00Z", attempt_cap: 5, code_shown_on: "terminal" });
      if (path === "/actions/pairing/redeem") {
        if (options.redeem) return options.redeem;
        approved = true;
        return ok({ shape: "screening-action-redeem-v1", batch_index: 1 });
      }
      if (path === "/actions/publish") return ok({ shape: "screening-action-publish-v1", status: "CURRENT", generation_id: "GEN-1", generation_fingerprint: "sha256:g", outputs: {}, request_id: "r", journal_event_id: "e" });
      return new Response(JSON.stringify({ detail: { code: "NOT_FOUND" } }), { status: 404 });
    }),
  );
  return log;
}

afterEach(() => vi.unstubAllGlobals());

describe("publish.conflict-blocks", () => {
  it("keeps Publish disabled while a preview check fails, and names the failing check", async () => {
    const failing = { ...PREVIEW, checks: PREVIEW.checks.map((c: { name: string }) => (c.name === "no_open_conflicts" ? { ...c, ok: false, detail: "1 open" } : c)) };
    engine({ preview: failing, approved: true });
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("Publishing waits until every check passes.");
    expect(screen.getByRole("button", { name: "Publish the screening" })).toBeDisabled();
    expect(document.querySelector('[data-check="no_open_conflicts"]')).toHaveTextContent("Fails");
  });

  it("shows the PROJECTION_STALE card when a decisions file is out of date", async () => {
    engine({ preview: { ...PREVIEW, checks: PREVIEW.checks.map((c: { name: string }) => (c.name === "projections_current" ? { ...c, ok: false } : c)) } });
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("PROJECTION_STALE");
    expect(screen.getByText("A decisions file is out of date", { selector: "h2" })).toBeInTheDocument();
  });
});

describe("publish approval and publish", () => {
  it("asks the engine to print a code, sends the typed code once, clears it, then publishes", async () => {
    const log = engine();
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("Approve each batch, then publish the screening.");
    expect(screen.getByRole("button", { name: "Publish the screening" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Show a code in the terminal" }));
    await screen.findByText(/Code printed in the terminal/);
    const begin = log.find((l) => l.path === "/actions/pairing/begin");
    expect(begin?.body).toEqual({ batch: 1 });

    const field = screen.getByLabelText("Approval code for batch_001");
    fireEvent.change(field, { target: { value: " AB12C-DE34F " } });
    fireEvent.click(screen.getByRole("button", { name: "Approve batch_001" }));
    await screen.findByText("Approved");
    expect(log.find((l) => l.path === "/actions/pairing/redeem")?.body).toMatchObject({ batch: 1, code: "AB12C-DE34F" });
    expect(field).toHaveValue("");

    const publish = screen.getByRole("button", { name: "Publish the screening" });
    await waitFor(() => expect(publish).toBeEnabled());
    fireEvent.click(publish);
    await screen.findByText("Published generation GEN-1");
  });

  it("shows the engine's refusal for a wrong code", async () => {
    engine({ redeem: new Response(JSON.stringify({ detail: { code: "PAIRING_CODE_INVALID", message: "no" } }), { status: 403, headers: { "content-type": "application/json" } }) });
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("Approve each batch, then publish the screening.");
    fireEvent.change(screen.getByLabelText("Approval code for batch_001"), { target: { value: "WRONG" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve batch_001" }));
    await screen.findByText("PAIRING_CODE_INVALID");
    expect(screen.getByText("Wrong approval code", { selector: "h2" })).toBeInTheDocument();
  });
});

describe("publish copy", () => {
  it("has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PUBLISH_COPY[locale]).sort()).toEqual(Object.keys(PUBLISH_COPY.en).sort());
      for (const [key, value] of Object.entries(PUBLISH_COPY[locale])) {
        expect(value.trim()).not.toBe("");
        expect(holes(value), `${locale}/${key}`).toEqual(holes(PUBLISH_COPY.en[key as keyof typeof PUBLISH_COPY.en]));
      }
    }
  });
});
