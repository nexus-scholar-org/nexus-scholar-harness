import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PREPARE_COPY, ScreeningPrepare } from "@/components/screening-prepare";
import { SUPPORTED_LOCALES } from "@/i18n";

/** Prepare (spec 02) in jsdom; the snapshot refusal is the engine's recorded fixture. */

const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;
const fixture = (name: string) => JSON.parse(readFileSync(`${FIXTURES}${name}.json`, "utf-8")).response;

function engine(job?: { state: string; error?: string | null }) {
  let polls = 0;
  const log: { method: string; path: string; body: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? JSON.parse(String(init.body)) : null;
      log.push({ method, path, body });
      const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "content-type": "application/json" } });
      if (path === "/settings" && method === "GET") return json(fixture("settings_default").body);
      if (path === "/settings" && method === "PUT") return json({ ...fixture("settings_default").body, ...body });
      if (path === "/ui/batches") return json({ shape: "ui07.screening-batches-v1", run_id: null, count: 0, batches: [], missing: [] });
      if (path === "/prepare") {
        if (job) return json({ job_id: "job_1" });
        const refused = fixture("prepare_snapshot_not_accepted");
        return json(refused.body, refused.status);
      }
      if (path === "/api/console/api/v1/jobs/job_1" && job) {
        polls += 1;
        const state = polls < 2 ? "running" : job.state;
        return json({ job: { job_id: "job_1", action_id: "screen_prepare", state, exit_code: state === "success" ? 0 : 1, error: job.error ?? null } });
      }
      return json({ detail: { code: "NOT_FOUND" } }, 404);
    }),
  );
  return log;
}

afterEach(() => vi.unstubAllGlobals());

describe("prepare.snapshot-missing", () => {
  it("confirms before preparing, then shows the refusal with the Import link and the terminal step", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    expect(log.some((l) => l.path === "/prepare")).toBe(false);
    expect(screen.getByText("Prepare batches of 20 records?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    await screen.findByText("SNAPSHOT_NOT_ACCEPTED");
    expect(screen.getByRole("link", { name: "Import the corpus" })).toHaveAttribute("href", "/en/screening/import");
    expect(screen.getByText("nexus-scholar accept-corpus --ris Scopus=<file>.ris")).toBeInTheDocument();
    expect(log.find((l) => l.path === "/prepare")?.body).toEqual({ batch_size: 20 });
  });
});

describe("prepare.job-followed", () => {
  it("says when the prepare job failed instead of waiting forever (golden run)", async () => {
    engine({ state: "failed", error: "No module named scholar_harness" });
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    const alert = await screen.findByRole("alert", {}, { timeout: 4000 });
    expect(alert).toHaveTextContent("Preparing failed (job job_1). Nothing was prepared. The engine said: No module named scholar_harness");
  });

  it("gives the exit code when the job failed without an error message", async () => {
    // A non-zero exit sets no `error` in the runner; only a timeout or exception does.
    engine({ state: "failed", error: null });
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    expect(await screen.findByRole("alert", {}, { timeout: 4000 })).toHaveTextContent("The engine said: exit code 1");
  });

  it("says the batches are prepared and re-reads them when the job succeeds", async () => {
    const log = engine({ state: "success" });
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    expect(await screen.findByText("Batches prepared (job job_1).", {}, { timeout: 4000 })).toBeInTheDocument();
    expect(log.filter((l) => l.path === "/ui/batches").length).toBeGreaterThanOrEqual(2);
  });
});

describe("prepare.rule-table-readonly", () => {
  it("describes the engine's rules in order and offers no control to change them", async () => {
    engine();
    render(<ScreeningPrepare locale="en" />);
    const rules = await screen.findByRole("heading", { name: "How an agent draft's outcome is derived" });
    const section = rules.closest("section")!;
    expect(section.querySelectorAll("input, select, button, textarea")).toHaveLength(0);
    const items = [...section.querySelectorAll("li")].map((li) => li.textContent);
    expect(items[0]).toMatch(/^First, Unclear/);
  });
});

describe("prepare.ai-agreed-needs-confirm", () => {
  it("keeps Save disabled until the opt-in is confirmed with a sample size, and sends the confirmation", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    fireEvent.click(await screen.findByLabelText(/AI-agreed exclusion/));
    const save = screen.getByRole("button", { name: "Save settings" });
    expect(save).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Sample-audit size/), { target: { value: "60" } });
    expect(save).toBeDisabled();
    fireEvent.click(screen.getByLabelText(/I understand this skips records/));
    expect(save).toBeEnabled();
    fireEvent.click(save);
    await screen.findByText("Settings saved");
    expect(log.find((l) => l.method === "PUT")?.body).toEqual({
      blinding: "reveal_after_decision",
      mode: "ai_agreed_exclusion",
      sample_audit_size: 60,
      confirm_ai_agreed_exclusion: true,
    });
  });
});

describe("prepare copy", () => {
  it("has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PREPARE_COPY[locale]).sort()).toEqual(Object.keys(PREPARE_COPY.en).sort());
      for (const [key, value] of Object.entries(PREPARE_COPY[locale])) {
        expect(holes(value), `${locale}/${key}`).toEqual(holes(PREPARE_COPY.en[key as keyof typeof PREPARE_COPY.en]));
      }
    }
  });
});

describe("prepare.advance-on-decide (M6-beta)", () => {
  it("offers the two values, default first, and sends the setting only when it changes", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    const draftThenNext = await screen.findByLabelText("Show the draft, then N (default)");
    expect(draftThenNext).toBeChecked();
    fireEvent.click(screen.getByLabelText(/Move on at once/));
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
    await screen.findByText("Settings saved");
    expect(log.find((l) => l.method === "PUT")?.body).toMatchObject({ advance_on_decide: "next_at_once" });
  });
});
