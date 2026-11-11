import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryRecall } from "@/components/discovery-recall";
import type { RecallCheck } from "@/lib/discovery-api";

import { QUERY_TEXT, refuse } from "./fixtures/discovery-engine";
import { setUp } from "./discovery-helpers";

/** 02 Recall check (spec docs/ux/phase1-discovery/final/02-recall.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

const EARLIER: RecallCheck = {
  shape: "discovery.recall-v1",
  protocol_fingerprint: "sha256:" + "ab".repeat(32),
  checked_at: "2026-11-01T08:00:00+00:00",
  query_text: QUERY_TEXT,
  seeds: [
    { id: "10.1000/one", kind: "doi", source: "you", title: "Seed one", title_check: "ok", per_provider: { openalex: "found", crossref: "found", arxiv: "n/a" } },
    { id: "2101.00001", kind: "arxiv", source: "you", title: "Seed two", title_check: "ok", per_provider: { openalex: "not_found", crossref: "not_found", arxiv: "not_found" } },
  ],
  found: 1,
  total: 2,
  missed_everywhere: ["2101.00001"],
  legs: [],
} as unknown as RecallCheck;

describe("discovery.recall", () => {
  it("opens on the empty state without a code, with Check disabled until a seed is typed", async () => {
    setUp();
    render(<DiscoveryRecall locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "No recall check yet" });
    expect(screen.queryByText("RECALL_NOT_RUN")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("button", { name: "Check these seeds" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /synonym|run anyway/i })).toBeNull();
    expect(screen.queryByRole("textbox", { name: /synonym/i })).toBeNull();
  });

  it("sends exactly the typed seeds with source you and no providers, then shows the engine's table", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryRecall locale="en" />);
    await user.type(await screen.findByLabelText("Identifier of seed 1"), "10.1000/one");
    await user.click(screen.getByRole("button", { name: "Add a seed" }));
    await user.selectOptions(screen.getByLabelText("Kind of seed 2"), "arxiv");
    await user.type(screen.getByLabelText("Identifier of seed 2"), "2101.00001");
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));

    await screen.findByRole("heading", { level: 1, name: "The query finds 1 of the 2 papers you gave it" });
    const posts = engine.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/discovery/recall");
    expect(posts).toHaveLength(1);
    expect(posts[0].body).toEqual({
      seeds: [
        { id: "10.1000/one", kind: "doi", source: "you" },
        { id: "2101.00001", kind: "arxiv", source: "you" },
      ],
    });
    const table = document.querySelector("[data-recall-table] table") as HTMLElement;
    // Seed and Source, then one column per database the engine answered for.
    expect(within(table).getAllByRole("columnheader")).toHaveLength(2 + 5);
    const missed = document.querySelector('[data-seed="2101.00001"]') as HTMLElement;
    expect(within(missed).getByText("Not found by any database")).toBeInTheDocument();
    const found = document.querySelector('[data-seed="10.1000/one"]') as HTMLElement;
    expect(within(found).queryByText("Not found by any database")).toBeNull();
    expect(found.querySelector('[data-cell="n/a"]')).not.toBeNull();
  });

  it("cannot add a 26th seed", async () => {
    const user = userEvent.setup();
    setUp();
    render(<DiscoveryRecall locale="en" />);
    const add = await screen.findByRole("button", { name: "Add a seed" });
    for (let i = 1; i < 25; i++) await user.click(add);
    expect(document.querySelectorAll("[data-seed-row]")).toHaveLength(25);
    expect(add).toBeDisabled();
  });

  it("renders a stored check from an earlier protocol with the banner and one column per database", async () => {
    setUp({ refuseOnce: { "GET /api/v1/discovery/recall": { status: 200, body: EARLIER } } });
    render(<DiscoveryRecall locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The query finds 1 of the 2 papers you gave it" });
    expect(screen.getByText("This check was made for an earlier protocol; the query below is not the current one.")).toBeInTheDocument();
    const table = document.querySelector("[data-recall-table] table") as HTMLElement;
    expect(within(table).getAllByRole("columnheader").map((h) => h.textContent)).toEqual(["Seed", "Source", "OpenAlex", "Crossref", "arXiv"]);
    expect(within(document.querySelector('[data-seed="2101.00001"]') as HTMLElement).getByText("Not found by any database")).toBeInTheDocument();
  });

  it("maps SEEDS_INVALID to its card with the engine's message and the code under Details", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryRecall locale="en" />);
    await user.type(await screen.findByLabelText("Identifier of seed 1"), "not-a-doi");
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "SEEDS_INVALID");
    expect(within(card.querySelector("details") as HTMLElement).getByText("SEEDS_INVALID")).toBeInTheDocument();
    expect(document.querySelector("[data-seeds-invalid]")?.textContent).toBe("seed not-a-doi is not a well-formed identifier");
    expect(screen.getByLabelText("Identifier of seed 1")).toHaveAttribute("aria-invalid", "true");
    expect(engine.calls.some((c) => c.path.startsWith("/api/v1/discovery/jobs/"))).toBe(false);
  });

  it("prints the SCHOLAR_MAILTO line for MAILTO_NOT_SET and checks again", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ mailto: false });
    render(<DiscoveryRecall locale="en" />);
    await user.type(await screen.findByLabelText("Identifier of seed 1"), "10.1000/one");
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "MAILTO_NOT_SET");
    expect(within(card).getByText("SCHOLAR_MAILTO=<your email>")).toBeInTheDocument();
    expect(within(card.querySelector("details") as HTMLElement).getByText("MAILTO_NOT_SET")).toBeInTheDocument();
    engine.setMailto(true);
    await user.click(within(card).getByRole("button", { name: "Check again" }));
    // Check again re-reads; it starts nothing (review 4).
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));
    await screen.findByRole("heading", { level: 1, name: "The query finds 1 of the 1 papers you gave it" });
  });

  it("says DISCOVERY_JOB_ACTIVE as a sentence and points to the running harvest", async () => {
    const user = userEvent.setup();
    setUp({ refuseOnce: { "POST /api/v1/discovery/recall": refuse(409, "DISCOVERY_JOB_ACTIVE", "busy", { job: { job_id: "djob_x", kind: "run", state: "running" } }) } });
    render(<DiscoveryRecall locale="en" />);
    await user.type(await screen.findByLabelText("Identifier of seed 1"), "10.1000/one");
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "DISCOVERY_JOB_ACTIVE");
    expect(within(card).getByText("DISCOVERY_JOB_ACTIVE")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Open Harvest" })[0]).toHaveAttribute("href", "/en/discovery/harvest/");
  });

  it("removes the form once the corpus is accepted", async () => {
    setUp({ runs: 1, accepted: true });
    render(<DiscoveryRecall locale="en" />);
    await screen.findByText("The corpus is frozen. This check is kept as a record.");
    await waitFor(() => expect(document.querySelector("[data-recall-form]")).toBeNull());
    expect(screen.queryByRole("button", { name: /Check these seeds|Check again/ })).toBeNull();
  });

  it("prints no seed count for a check reattached after a reload (review 3)", async () => {
    setUp({
      refuseOnce: {
        "GET /api/v1/discovery/runs": { status: 200, body: { shape: "discovery.runs-v1", runs: [], active_job: { job_id: "djob_r", kind: "recall", state: "running", started_at: "2026-11-10T09:00:00+00:00", finished_at: null, result: null, error: null } } },
      },
    });
    render(<DiscoveryRecall locale="en" />);
    await screen.findByText("Checking the seeds");
    expect(screen.queryByText(/Checking \d+ seeds/)).toBeNull();
  });

  it("pre-fills the protocol's anchor seeds as removable Anchor rows and sends them only on the button (M4d)", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ goldenSeeds: ["10.1000/a", "10.1000/b"] });
    render(<DiscoveryRecall locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "No recall check yet" });
    expect(screen.getByText("These are the anchor papers you kept in inception. Remove any you do not want, or add your own.")).toBeInTheDocument();
    expect(screen.getByLabelText("Identifier of seed 1")).toHaveValue("10.1000/a");
    expect(screen.getByLabelText("Identifier of seed 2")).toHaveValue("10.1000/b");
    expect(document.querySelectorAll("[data-anchor-row]")).toHaveLength(2);
    expect(engine.calls.some((c) => c.method === "POST" && c.path === "/api/v1/discovery/recall")).toBe(false);
    await user.click(screen.getByRole("button", { name: "Add a seed" }));
    await user.type(screen.getByLabelText("Identifier of seed 3"), "10.1000/mine");
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));
    await screen.findByRole("heading", { level: 1, name: /The query finds/ });
    const post = engine.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/recall")!;
    expect(post.body).toEqual({
      seeds: [
        { id: "10.1000/a", kind: "doi", source: "anchor" },
        { id: "10.1000/b", kind: "doi", source: "anchor" },
        { id: "10.1000/mine", kind: "doi", source: "you" },
      ],
    });
  });

  it("sends only the anchor seed that was not removed (M4d)", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ goldenSeeds: ["10.1000/a", "10.1000/b"] });
    render(<DiscoveryRecall locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Remove seed 1" }));
    await user.click(screen.getByRole("button", { name: "Check these seeds" }));
    await screen.findByRole("heading", { level: 1, name: /The query finds/ });
    expect(engine.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/recall")!.body).toEqual({ seeds: [{ id: "10.1000/b", kind: "doi", source: "anchor" }] });
  });

  it("opens with one empty row when the protocol has no anchor seeds, and with the stored check's seeds when one exists (M4d)", async () => {
    setUp({ goldenSeeds: [] });
    render(<DiscoveryRecall locale="en" />);
    expect(await screen.findByLabelText("Identifier of seed 1")).toHaveValue("");
    expect(document.querySelectorAll("[data-seed-row]")).toHaveLength(1);
    expect(document.querySelector("[data-anchor-row]")).toBeNull();
  });

  it("fills the form from a stored check, not from the anchor seeds (M4d)", async () => {
    const { engine } = setUp({ goldenSeeds: ["10.1000/anchor-only"] });
    engine.handle("POST", "/api/v1/discovery/recall", { seeds: [{ id: "10.1000/one", kind: "doi", source: "you" }] });
    render(<DiscoveryRecall locale="en" />);
    await screen.findByRole("heading", { level: 1, name: /The query finds/ });
    const values = [...document.querySelectorAll("[data-seed-row] input")].map((i) => (i as HTMLInputElement).value);
    expect(values.length).toBeGreaterThan(0);
    expect(values).not.toContain("10.1000/anchor-only");
  });
});
