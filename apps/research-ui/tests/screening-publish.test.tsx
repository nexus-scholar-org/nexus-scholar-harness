import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningPublish } from "@/components/screening-publish";

/**
 * Publish (spec 09) in jsdom. The PRISMA preview is the engine's recorded
 * fixture; approval state comes from `/ui/batches/review` (each batch's `/ui/batch/{n}/review`). The approval code
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

function engine(options: { preview?: unknown; approved?: boolean; redeem?: Response; redeemAll?: Response; publication?: string; approver?: string | null; reporting?: string; shownOn?: "terminal" | "desktop"; beginAll?: unknown } = {}) {
  let approved = options.approved ?? false;
  let approver = options.approver === undefined ? "Researcher" : options.approver;
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
      if (path === "/settings" && options.reporting === "error") return new Response(JSON.stringify({ detail: { code: "PROTOCOL_METHOD_INVALID" } }), { status: 409 });
      if (path === "/settings" && options.reporting) return ok({ reporting: options.reporting, reporting_source: "protocol" });
      if (path === "/settings") return ok({ blinding: "reveal_after_decision" }); // an engine without the field
      if (path === "/ui/batches") return ok(BATCHES);
      if (path === "/approver") {
        if (method === "PUT") approver = (body as { name: string }).name;
        return ok({ name: approver, set_at: approver ? "2026-11-06T13:00:00Z" : null, basis: "typed-name" });
      }
      if (path === "/ui/batch/1/review") return ok(review(approved));
      // H-screening-read-performance: every batch's review in one request, as the engine answers it.
      if (path === "/ui/batches/review") return ok({ shape: "ui07.batch-reviews-v1", count: 1, reviews: [review(approved)] });
      if (path === "/actions/pairing/begin-all" && options.beginAll) return ok(options.beginAll);
      if (path === "/actions/pairing/begin-all")
        return ok({ batches: [{ batch_index: 1, snapshot_fingerprint: "sha256:s" }], skipped: [{ batch_index: 2, reason: "DEFERRED" }], code_expires_at: "2026-11-05T10:05:00Z", attempt_cap: 5, code_shown_on: options.shownOn ?? "desktop" });
      if (path === "/actions/pairing/redeem-all") {
        if (options.redeemAll) return options.redeemAll;
        approved = true;
        return ok({ shape: "screening-action-redeem-all-v1", request_id: "r", approved: [{ batch_index: 1, approval_fingerprint: "sha256:a", journal_event_id: "e" }], refused: [], publication_approval_fingerprint: "sha256:p" });
      }
      if (path === "/actions/pairing/redeem") {
        if (options.redeem) return options.redeem;
        approved = true;
        return ok({ shape: "screening-action-redeem-v1", batch_index: 1 });
      }
      if (path === "/api/console/api/v1/ui/publication-status") {
        if (!options.publication) return new Response(JSON.stringify({ detail: { code: "NOT_FOUND" } }), { status: 404 });
        return ok({ shape: "ui07.publication-status-v1", status: options.publication, code: options.publication === "STALE" ? "GENERATION_STALE" : null, generation_id: "GEN-1", outputs: {}, message: "", details: options.publication === "STALE" ? { changed: 2 } : {} });
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

describe("publish.approver", () => {
  it("asks for the approver's name before any batch can be approved, then saves it", async () => {
    // Golden run 2026-11-06: nothing set the name, so the first approval refused OPERATOR_CONTEXT_MISSING.
    const log = engine({ approver: null });
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("No name yet. Approving a batch needs your name first.");
    expect(screen.getByRole("button", { name: "Show a code for batch 1" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save name" })).toBeDisabled();
    expect(screen.getByText(/not a verified sign-in/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Test Researcher" } });
    fireEvent.click(screen.getByRole("button", { name: "Save name" }));
    await screen.findByText("Approvals are recorded as Test Researcher.");
    expect(log.find((l) => l.method === "PUT" && l.path === "/approver")?.body).toEqual({ name: "Test Researcher" });
    expect(screen.getByRole("status")).toHaveTextContent("Name saved.");
    expect(screen.getByRole("button", { name: "Show a code for batch 1" })).toBeEnabled();
  });
});

describe("publish approval and publish", () => {
  it("shows the engine's refusal for a wrong code", async () => {
    engine({ redeem: new Response(JSON.stringify({ detail: { code: "PAIRING_CODE_INVALID", message: "no" } }), { status: 403, headers: { "content-type": "application/json" } }) });
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("Approve each batch, then publish the screening.");
    fireEvent.change(screen.getByLabelText("Approval code for batch 1"), { target: { value: "WRONG" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve batch 1" }));
    await screen.findByText("PAIRING_CODE_INVALID");
    expect(screen.getByText("Wrong approval code", { selector: "h2" })).toBeInTheDocument();
  });
});

describe("publish.approve-all (finding 38)", () => {
  it("stages every decided batch's code in one action and redeems one pasted block", async () => {
    const log = engine();
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("Batches fully decided and not approved yet: 1 of 1.");
    fireEvent.click(screen.getByRole("button", { name: "Show the codes for every decided batch" }));
    await screen.findByText(/The codes \(batches: 1\) are in a Nexus Scholar window on this computer's desktop/);
    expect(screen.getByText("Left out: 0 already approved, 1 deferred, 0 not fully decided.")).toBeInTheDocument();
    expect(log.find((l) => l.path === "/actions/pairing/begin-all")?.body).toEqual({});

    const field = screen.getByLabelText(/Paste the codes/);
    const pasted = "batch 1: ABCDEFGHJKMNPQRSTUVWXYZ234";
    fireEvent.change(field, { target: { value: pasted } });
    fireEvent.click(screen.getByRole("button", { name: "Approve the batches" }));
    await screen.findByText("Batches approved: 1.");
    expect(log.filter((l) => l.path === "/actions/pairing/redeem-all").map((l) => l.body)).toEqual([{ codes: pasted, request_id: null }]);
    // The pasted codes are kept nowhere once sent (UI-07 §3.6).
    expect(field).toHaveValue("");
    await screen.findByText("Approval on file");
  });

  it("says when the codes are on the terminal only, and names each batch the engine refused", async () => {
    engine({
      shownOn: "terminal",
      redeemAll: new Response(
        JSON.stringify({ shape: "screening-action-redeem-all-v1", request_id: "r", approved: [], refused: [{ batch_index: 1, code: "STALE_VIEW", message: "changed" }], publication_approval_fingerprint: null }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    });
    render(<ScreeningPublish locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Show the codes for every decided batch" }));
    await screen.findByText(/The codes \(batches: 1\) are printed in the engine's terminal/);
    fireEvent.change(screen.getByLabelText(/Paste the codes/), { target: { value: "batch 1: X" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve the batches" }));
    await screen.findByText("Not approved: batch 1 (STALE_VIEW). Show the codes again for it.");
  });

  it("shows the engine's refusal when the paste holds no valid code", async () => {
    engine({ redeemAll: new Response(JSON.stringify({ detail: { code: "PAIRING_CODE_INVALID", message: "no" } }), { status: 403, headers: { "content-type": "application/json" } }) });
    render(<ScreeningPublish locale="en" />);
    fireEvent.change(await screen.findByLabelText(/Paste the codes/), { target: { value: "hello" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve the batches" }));
    await screen.findByText("PAIRING_CODE_INVALID");
  });

  it("names a batch the engine refused a code, and clears the pasted codes when they expire", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const soon = new Date(Date.now() + 60_000).toISOString();
      engine({
        beginAll: { batches: [{ batch_index: 1, snapshot_fingerprint: "s" }], skipped: [{ batch_index: 2, reason: "WORKER_BATCH_MISSING" }], code_expires_at: soon, attempt_cap: 5, code_shown_on: "terminal" },
      });
      render(<ScreeningPublish locale="en" />);
      fireEvent.click(await screen.findByRole("button", { name: "Show the codes for every decided batch" }));
      await screen.findByText("No code for batch 2 (WORKER_BATCH_MISSING).");
      const field = screen.getByLabelText(/Paste the codes/);
      fireEvent.change(field, { target: { value: "batch 1: CODE" } });
      await vi.advanceTimersByTimeAsync(61_000);
      await waitFor(() => expect(field).toHaveValue(""));
      expect(document.querySelector("[data-bulk-begun]")).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps the one-batch controls folded under their own heading", async () => {
    engine();
    render(<ScreeningPublish locale="en" />);
    const summary = await screen.findByText("Approve one batch at a time");
    const details = summary.closest("details");
    expect(details).not.toBeNull();
    expect(details).not.toHaveAttribute("open");
    expect(within(details as HTMLElement).getByLabelText("Approval code for batch 1")).toBeInTheDocument();
  });
});

describe("export.link on publish", () => {
  it("links to Export and methods only while the publication is CURRENT (spec 10, decision 3)", async () => {
    engine({ approved: true, publication: "CURRENT" });
    const { unmount } = render(<ScreeningPublish locale="en" />);
    expect(await screen.findByRole("link", { name: "Export and methods" })).toHaveAttribute("href", "/en/screening/export");
    unmount();
    vi.unstubAllGlobals();
    engine({ approved: true, publication: "STALE" });
    render(<ScreeningPublish locale="en" />);
    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByRole("link", { name: "Export and methods" })).toBeNull();
  });
});

describe("publish.details (M6-beta, spec 09 amendment)", () => {
  it("shows each check as one line; a passing check's detail and the batch file name sit behind Details", async () => {
    engine();
    render(<ScreeningPublish locale="en" />);
    await screen.findByRole("heading", { name: "Checks" });
    for (const li of document.querySelectorAll("[data-check]")) {
      expect(li.querySelector("[dir=ltr]")).toBeNull(); // no inline detail on a passing line
    }
    const checks = document.querySelector("[data-checks-details]") as HTMLDetailsElement;
    expect(checks.open).toBe(false);
    expect(screen.getByText("batch_001.json").closest("details")).not.toBeNull();
    expect(screen.getByText(/^batch 1$/i)).toBeInTheDocument();
    // The PRISMA preview keeps its reasons table.
    expect(screen.getByRole("columnheader", { name: "Reason" })).toBeInTheDocument();
  });

  it("says how many studies changed after publishing, with the code behind Details", async () => {
    engine({ publication: "STALE" });
    render(<ScreeningPublish locale="en" />);
    const notice = await waitFor(() => {
      const el = document.querySelector("[data-publication-stale]");
      if (!el) throw new Error("not yet");
      return el;
    });
    expect(notice).toHaveTextContent("Decisions changed after this was published (2 studies). Approve and publish again.");
    expect(within(notice as HTMLElement).getByText("GENERATION_STALE").closest("details")).not.toBeNull();
  });
});


// M7b-guideline (spec 09 amendment 2026-11-08): the preview names the guideline.
describe("publish.reporting", () => {
  it.each([
    ["prisma-2020", "PRISMA 2020 screening preview"],
    ["prisma-scr", "PRISMA-ScR screening preview"],
    ["none", "Screening preview"],
  ])("heading follows %s", async (reporting, heading) => {
    engine({ reporting });
    render(<ScreeningPublish locale="en" />);
    expect(await screen.findByText(heading)).toBeInTheDocument();
  });

  it("names the screening counts report under none, and reads an absent guideline as PRISMA 2020", async () => {
    engine({ reporting: "none" });
    const { unmount } = render(<ScreeningPublish locale="en" />);
    expect(await screen.findByText(/the screening counts report for the approved generation/)).toBeInTheDocument();
    unmount();
    engine();
    render(<ScreeningPublish locale="en" />);
    expect(await screen.findByText("PRISMA 2020 screening preview")).toBeInTheDocument();
  });

  it("names no guideline when the settings call fails (review 2)", async () => {
    engine({ reporting: "error" });
    render(<ScreeningPublish locale="en" />);
    expect(await screen.findByText("Screening preview")).toBeInTheDocument();
    expect(screen.queryByText("PRISMA 2020 screening preview")).toBeNull();
  });
});

// One decision each, from a seeded engine state (H-test-diet).
describe("publish.one-decision", () => {
  it("sends a typed approval code once, trimmed, and clears the field", async () => {
    const log = engine();
    render(<ScreeningPublish locale="en" />);
    await screen.findByText("Approve each batch, then publish the screening.");
    const field = screen.getByLabelText("Approval code for batch 1");
    fireEvent.change(field, { target: { value: " AB12C-DE34F " } });
    fireEvent.click(screen.getByRole("button", { name: "Approve batch 1" }));
    await screen.findByText("Approval on file");
    expect(log.filter((l) => l.path === "/actions/pairing/redeem").map((l) => l.body)).toEqual([expect.objectContaining({ batch: 1, code: "AB12C-DE34F" })]);
    expect(field).toHaveValue("");
    // The UI cannot tell whether an approval on file is still current, so re-approval stays available (review 4).
    expect(screen.getByRole("button", { name: "Approve batch 1" })).toBeInTheDocument();
  });

  it("Publish the screening, with every batch approved, sends one publish request and says Published", async () => {
    const log = engine({ approved: true });
    render(<ScreeningPublish locale="en" />);
    const publish = await screen.findByRole("button", { name: "Publish the screening" });
    await waitFor(() => expect(publish).toBeEnabled());
    fireEvent.click(publish);
    // "Published", with the generation id behind Details (M6-beta, rule page 12).
    const banner = await waitFor(() => {
      const el = document.querySelector("[data-published]");
      if (!el) throw new Error("not yet");
      return el;
    });
    expect(log.filter((l) => l.method === "POST" && l.path.endsWith("/actions/publish"))).toHaveLength(1);
    expect(banner).toHaveTextContent("Published");
    expect(within(banner as HTMLElement).getByText("GEN-1").closest("details")).not.toBeNull();
  });
});
