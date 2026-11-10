import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryHarvest } from "@/components/discovery-harvest";

import { refuse } from "./fixtures/discovery-engine";
import { sent, setUp } from "./discovery-helpers";

/** 03 Harvest (spec docs/ux/phase1-discovery/final/03-harvest.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("discovery.harvest", () => {
  it("starts with the cap override and the note, streams each database, and ends not frozen", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ failedLeg: { provider: "pubmed", code: "PROVIDER_RATE_LIMITED", error: "HTTPStatusError: 429 Too Many Requests" } });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: "Search the databases your protocol selects" });
    expect(screen.queryByRole("button", { name: /Stop arXiv|slice/i })).toBeNull();

    await user.type(screen.getByLabelText("Cap for this harvest only"), "500");
    await user.type(screen.getByLabelText("Note for this run (optional)"), "first pass");
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));

    await screen.findByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." });
    const post = engine.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/runs");
    expect(post?.body).toEqual({ cap_override: 500, note: "first pass" });
    expect(screen.queryByText(/ready for screening/i)).toBeNull();

    await screen.findByText("Cap for this run: 500 (run override)");
    const crossref = document.querySelector('[data-leg="crossref"]') as HTMLElement;
    expect(within(crossref).getByText("at least 500")).toBeInTheDocument();
    const pubmed = document.querySelector('[data-leg="pubmed"]') as HTMLElement;
    expect(within(pubmed).getByText("The database limited the request rate.")).toBeInTheDocument();
    expect(within(pubmed).getByText("PROVIDER_RATE_LIMITED")).toBeInTheDocument();
    expect(document.querySelectorAll('[data-cap-source="run_override"]').length).toBeGreaterThan(0);
    expect(screen.getByText("Cap for this run: 500 (run override)")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Duplicates" })).toHaveAttribute("href", "/en/discovery/dedup/");
    expect(sent(engine)).toContain("GET /api/v1/discovery/jobs/djob_0000000000000000/events");
  });

  it("prints the SCHOLAR_MAILTO line; Check again re-reads and starts nothing", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ mailto: false });
    render(<DiscoveryHarvest locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Start the harvest" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "MAILTO_NOT_SET");
    expect(within(card).getByText("SCHOLAR_MAILTO=<your email>")).toBeInTheDocument();
    engine.setMailto(true);
    await user.click(within(card).getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." });
  });

  it("refuses a frozen corpus and removes Start", async () => {
    setUp({ runs: 1, accepted: true });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByText("The corpus is frozen. No harvest is started from here; the runs stay as a record.");
    expect(screen.queryByRole("button", { name: /Start the harvest|Harvest again/ })).toBeNull();
  });

  it("says DISCOVERY_JOB_ACTIVE as a sentence and follows the running job", async () => {
    const user = userEvent.setup();
    setUp({ refuseOnce: { "POST /api/v1/discovery/runs": refuse(409, "DISCOVERY_JOB_ACTIVE", "busy", { job: { job_id: "djob_x", kind: "run", state: "running" } }) } });
    render(<DiscoveryHarvest locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Start the harvest" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "DISCOVERY_JOB_ACTIVE");
    expect(within(card).getByText("DISCOVERY_JOB_ACTIVE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Follow the running job" })).toBeInTheDocument();
  });

  it("reattaches to a running harvest on load and stops the whole harvest", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ activeJob: true });
    render(<DiscoveryHarvest locale="en" />);
    // The open stream ends without a done event: one reconnect, then the last state with Retry.
    await screen.findByText(/Connection lost/);
    expect(document.querySelector('[data-leg="openalex"]')).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "Stop the harvest and keep what was fetched" }));
    expect(sent(engine)).toContain("POST /api/v1/discovery/jobs/djob_0000000000000000/cancel");
  });

  it("marks an older run read only and stale", async () => {
    setUp({ runs: 2, search: "?run=run_001" });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: "Run run_001" });
    expect(screen.getAllByText("Stale").length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Harvest again" })).toBeNull();
  });
});
