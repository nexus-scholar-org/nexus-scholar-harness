import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryReport } from "@/components/discovery-report";

import { sent, setUp } from "./discovery-helpers";

/** 06 Search report (spec docs/ux/phase1-discovery/final/06-report.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

const TITLE = "What each database was asked and what came back.";
const PUT = "PUT /api/v1/discovery/report/methods";

describe("discovery.report", () => {
  it("reads a capped database as at least N, a failed one with its code, and adds up no total", async () => {
    setUp({ runs: 1, failedLeg: { provider: "pubmed", code: "PROVIDER_RATE_LIMITED", error: "HTTPStatusError: 429" } });
    render(<DiscoveryReport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const crossref = document.querySelector('[data-ident="crossref"]') as HTMLElement;
    expect(crossref).toHaveAttribute("data-completeness", "lower_bound");
    expect(crossref.querySelector("[data-fetched]")).toHaveTextContent(/^At least 500$/);
    expect(within(crossref).getByText("Lower bound")).toBeInTheDocument();
    const pubmed = document.querySelector('[data-ident="pubmed"]') as HTMLElement;
    expect(within(pubmed).getByText("Failed")).toBeInTheDocument();
    expect(pubmed.querySelector("[data-error-code]")).toHaveTextContent("PROVIDER_RATE_LIMITED");
    // Fetched 412 + 388 + 500 + 57 + 0, reported 412 + 388 + 1840 + 57: neither sum is on the page.
    expect(screen.queryByText("1357")).toBeNull();
    expect(screen.queryByText("2697")).toBeNull();
    expect(screen.queryByText(/^Total/i)).toBeNull();
  });

  it("prints the not-searched reasons and the PRISMA line when screening has not started", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryReport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const notSearched = document.querySelector("[data-not-searched]") as HTMLElement;
    expect(notSearched).toHaveTextContent("bioRxiv · off by default");
    expect(screen.getByText("Screening has not started, so there is no PRISMA box yet.")).toBeInTheDocument();
    expect(document.querySelector("[data-cap-override]")).toBeNull();
  });

  it("says the duplicate counts are not an older run's, never 0, and keeps the older run read only", async () => {
    setUp({ runs: 2, search: "?run=run_001" });
    render(<DiscoveryReport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const dedup = document.querySelector("[data-dedup]") as HTMLElement;
    expect(within(dedup).getByText("Duplicate counts are not this run's: a later run's records became the corpus.")).toBeInTheDocument();
    expect(within(dedup).queryByText("0")).toBeNull();
    expect(screen.getByText("An earlier run: read only.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "I reviewed this text" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Save as draft" })).toBeNull();
    expect(screen.getByLabelText("Methods text for run_001")).toHaveAttribute("readonly");
  });

  it("shows the methods text as a draft, records the review once and shows Reviewed from the answer", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1 });
    render(<DiscoveryReport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const methods = document.querySelector("[data-methods]") as HTMLElement;
    expect(within(methods).getByText("Methods text · draft · not reviewed")).toBeInTheDocument();
    expect(within(methods).queryByText(/Reviewed by you/)).toBeNull();
    expect(methods).toHaveAttribute("data-reviewed", "false");
    const text = (screen.getByLabelText("Methods text for run_001") as HTMLTextAreaElement).value;

    await user.click(screen.getByRole("button", { name: "I reviewed this text" }));
    await within(methods).findByText(/^Reviewed by you · /);
    const puts = engine.calls.filter((c) => `${c.method} ${c.path}` === PUT);
    expect(puts).toHaveLength(1);
    expect(puts[0].body).toEqual({ text, reviewed: true, run: "run_001" });
    expect(methods).toHaveAttribute("data-reviewed", "true");
  });

  it("does not show Reviewed when the engine's answer is not reviewed", async () => {
    const user = userEvent.setup();
    setUp({
      runs: 1,
      refuseOnce: { [PUT]: { status: 200, body: { text: "kept", built_from: "run_001", reviewed: false, reviewed_at: null } } },
    });
    render(<DiscoveryReport locale="en" />);
    await user.click(await screen.findByRole("button", { name: "I reviewed this text" }));
    await screen.findByText("Recorded");
    expect(screen.getByText("Methods text · draft · not reviewed")).toBeInTheDocument();
    expect(screen.queryByText(/Reviewed by you/)).toBeNull();
  });

  it("marks an edit after review as not saved and warns before saving it as a draft", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1 });
    render(<DiscoveryReport locale="en" />);
    await user.click(await screen.findByRole("button", { name: "I reviewed this text" }));
    await screen.findByText(/^Reviewed by you · /);
    await user.type(screen.getByLabelText("Methods text for run_001"), " More.");
    expect(screen.getByText("Edited, not saved")).toBeInTheDocument();
    expect(screen.queryByText(/^Reviewed by you · /)).toBeNull();

    await user.click(screen.getByRole("button", { name: "Save as draft" }));
    expect(screen.getByText("This text will no longer be marked as reviewed.")).toBeInTheDocument();
    expect(sent(engine).filter((c) => c === PUT)).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Save as draft anyway" }));
    await waitFor(() => expect(sent(engine).filter((c) => c === PUT)).toHaveLength(2));
    const last = engine.calls.filter((c) => `${c.method} ${c.path}` === PUT).at(-1);
    expect(last?.body).toMatchObject({ reviewed: false, run: "run_001" });
    expect(String(last?.body?.text)).toMatch(/ More\.$/);
    await screen.findByText("Methods text · draft · not reviewed");
  });

  it("shows RUN_NOT_FOUND when there is no run", async () => {
    setUp();
    render(<DiscoveryReport locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "RUN_NOT_FOUND");
    expect(within(card).getByText("RUN_NOT_FOUND")).toBeInTheDocument();
  });

  it("links the markdown report through the console proxy", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryReport locale="en" />);
    const link = await screen.findByRole("link", { name: "Open the report as markdown" });
    expect(link).toHaveAttribute("href", "/api/console/api/v1/discovery/runs/run_001/report");
  });
});
