import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

function engine(options: { preview?: unknown; approved?: boolean; redeem?: Response; publication?: string; approver?: string | null; reporting?: string } = {}) {
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
      if (path === "/settings" && options.reporting) return ok({ reporting: options.reporting, reporting_source: "protocol" });
      if (path === "/ui/batches") return ok(BATCHES);
      if (path === "/approver") {
        if (method === "PUT") approver = (body as { name: string }).name;
        return ok({ name: approver, set_at: approver ? "2026-11-06T13:00:00Z" : null, basis: "typed-name" });
      }
      if (path === "/ui/batch/1/review") return ok(review(approved));
      if (path === "/actions/pairing/begin") return ok({ batch_index: 1, snapshot_fingerprint: "sha256:s", code_expires_at: "2026-11-05T10:05:00Z", attempt_cap: 5, code_shown_on: "terminal" });
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
    expect(screen.getByRole("button", { name: "Show a code in the terminal" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save name" })).toBeDisabled();
    expect(screen.getByText(/not a verified sign-in/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Mouadh Bekhouche" } });
    fireEvent.click(screen.getByRole("button", { name: "Save name" }));
    await screen.findByText("Approvals are recorded as Mouadh Bekhouche.");
    expect(log.find((l) => l.method === "PUT" && l.path === "/approver")?.body).toEqual({ name: "Mouadh Bekhouche" });
    expect(screen.getByRole("status")).toHaveTextContent("Name saved.");
    expect(screen.getByRole("button", { name: "Show a code in the terminal" })).toBeEnabled();
  });

  it("names the approver in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of ["approverTitle", "approverBody", "approverCurrent", "approverNone", "approverLabel", "approverSave", "approverSaved"] as const) {
        expect(PUBLISH_COPY[locale][key], `${locale} ${key}`).toBeTruthy();
      }
      expect(PUBLISH_COPY[locale].approverCurrent, locale).toContain("{name}");
    }
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

    const field = screen.getByLabelText("Approval code for batch 1");
    fireEvent.change(field, { target: { value: " AB12C-DE34F " } });
    fireEvent.click(screen.getByRole("button", { name: "Approve batch 1" }));
    await screen.findByText("Approval on file");
    // The UI cannot tell whether an approval on file is still current, so re-approval stays available (review 4).
    expect(screen.getByRole("button", { name: "Approve batch 1" })).toBeInTheDocument();
    expect(log.find((l) => l.path === "/actions/pairing/redeem")?.body).toMatchObject({ batch: 1, code: "AB12C-DE34F" });
    expect(field).toHaveValue("");

    const publish = screen.getByRole("button", { name: "Publish the screening" });
    await waitFor(() => expect(publish).toBeEnabled());
    fireEvent.click(publish);
    // "Published", with the generation id behind Details (M6-beta, rule page 12).
    const banner = await waitFor(() => {
      const el = document.querySelector("[data-published]");
      if (!el) throw new Error("not yet");
      return el;
    });
    expect(banner).toHaveTextContent("Published");
    expect(within(banner as HTMLElement).getByText("GEN-1").closest("details")).not.toBeNull();
  });

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

  it("has the three variants in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of ["prisma", "prismaScr", "prismaNone", "publishBodyNone"] as const) expect(PUBLISH_COPY[locale][key]).toBeTruthy();
    }
  });
});
