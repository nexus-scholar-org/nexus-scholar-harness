import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryHarvest, LegRow } from "@/components/discovery-harvest";
import type { SearchLeg } from "@/lib/discovery-api";
import { discoveryT } from "@/lib/discovery-copy";

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

  it("prints the SCHOLAR_OPENALEX_KEY line for OPENALEX_KEY_NOT_SET; Check again re-reads and starts nothing (F12)", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ openalexKey: false });
    render(<DiscoveryHarvest locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Start the harvest" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "OPENALEX_KEY_NOT_SET");
    expect(within(card).getByText("SCHOLAR_OPENALEX_KEY=<your key>")).toBeInTheDocument();
    engine.setOpenalexKey(true);
    await user.click(within(card).getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(1);
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

  it("says 0 results, never Done, for a database that found nothing (M10a, OBS-1b)", () => {
    for (const locale of ["en", "ar"] as const) {
      const t = discoveryT(locale);
      const leg = { provider: "openalex", fetched: 0, reported_total: 0, cap: 25, cap_hit: false, status: "ok", error_code: null };
      const { container, unmount } = render(
        <table>
          <tbody>
            <LegRow locale={locale} leg={leg} />
          </tbody>
        </table>,
      );
      const row = container.querySelector('[data-leg="openalex"]') as HTMLElement;
      expect(row.textContent).not.toContain(t("harvest.leg.status.ok"));
      expect(row.querySelector('[data-role="unclear"]')?.textContent).toBe(t("harvest.leg.status.none"));
      expect(row.querySelector('[data-role="include"]')).toBeNull();
      expect(row.querySelector("[data-count]")?.textContent).toBe(t("harvest.count.of", { fetched: 0, reported: 0 }));
      unmount();
    }
  });
});

// --------------------------------------------------------------------------- M10a: the database choice per harvest

const READY = "Search the databases your protocol selects";
const FINISHED = "The harvest is finished. The corpus is not frozen yet.";
const ticked = () => [...document.querySelectorAll<HTMLElement>('[data-picker-row][data-selected="true"]')].map((r) => r.dataset.pickerRow);
const rowIds = () => [...document.querySelectorAll<HTMLElement>("[data-picker-row]")].map((r) => r.dataset.pickerRow);
const runPost = (engine: { calls: { method: string; path: string; body: Record<string, unknown> | null }[] }) =>
  engine.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/discovery/runs");

function legRow(leg: Partial<SearchLeg> & { provider: string }, full?: Partial<SearchLeg>) {
  const view = { fetched: 0, reported_total: null, cap: 500, cap_hit: false, status: "ok", error_code: null, ...leg };
  const { container, unmount } = render(
    <table>
      <tbody>
        <LegRow locale="en" leg={view} full={full ? ({ ...view, executed_query: null, ...full } as SearchLeg) : undefined} />
      </tbody>
    </table>,
  );
  return { row: container.querySelector(`[data-leg="${leg.provider}"]`) as HTMLElement, unmount };
}

describe("discovery.harvest Crossref and a joined query (H-run-small-fixes, finding 9)", () => {
  it("starts without Crossref when the protocol took the default list, says why, and sends the list", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "crossref", "arxiv"] });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    expect(ticked()).toEqual(["openalex", "semanticscholar", "arxiv"]);
    expect(document.querySelector('[data-default-without="crossref"]')).toHaveTextContent(
      "Crossref is left out by default: this query joins 2 concepts and Crossref would not apply the AND.",
    );
    expect(document.querySelector("[data-ignores-and]")).toBeNull();
    // Review P1: the estimate counts the same databases the harvest will search.
    const card = document.querySelector("[data-estimate]") as HTMLElement;
    await user.click(within(card).getByRole("button", { name: /count/i }));
    await waitFor(() => expect(engine.calls.some((c) => c.method === "POST" && c.path === "/api/v1/discovery/estimate")).toBe(true));
    expect(engine.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/estimate")?.body).toMatchObject({
      providers: ["openalex", "semanticscholar", "arxiv"],
    });
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: FINISHED });
    expect(runPost(engine)[0].body).toEqual({ providers: ["openalex", "semanticscholar", "arxiv"] });
  });

  it("after Reset to the protocol, the estimate counts Crossref (review N1)", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "crossref", "arxiv"] });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    await user.click(screen.getByRole("button", { name: "Reset to the protocol" }));
    expect(ticked()).toContain("crossref");
    const card = document.querySelector("[data-estimate]") as HTMLElement;
    await user.click(within(card).getByRole("button", { name: /count/i }));
    await waitFor(() => expect(engine.calls.some((c) => c.method === "POST" && c.path === "/api/v1/discovery/estimate")).toBe(true));
    const body = engine.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/discovery/estimate").at(-1)?.body as { providers?: string[] };
    expect(body.providers).toContain("crossref");
  });

  it("warns as soon as Crossref is ticked for a joined query", async () => {
    const user = userEvent.setup();
    setUp({ protocolProviders: ["openalex", "semanticscholar", "crossref", "arxiv"] });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    await user.click(screen.getByRole("checkbox", { name: "Search Crossref" }));
    expect(document.querySelector('[data-ignores-and="crossref"]')).toHaveTextContent(
      "Crossref does not apply the AND between the 2 concepts of this query",
    );
  });

  it("keeps Crossref for a protocol that names its own list, with the warning", async () => {
    setUp();
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    expect(ticked()).toContain("crossref");
    expect(document.querySelector('[data-ignores-and="crossref"]')).not.toBeNull();
  });

  it("neither warns nor leaves Crossref out for a one-concept query", async () => {
    setUp({ protocolProviders: ["openalex", "semanticscholar", "crossref", "arxiv"], concepts: 1 });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    expect(ticked()).toContain("crossref");
    expect(document.querySelector("[data-ignores-and], [data-default-without]")).toBeNull();
  });
});

describe("discovery.harvest database picker (M10a)", () => {
  it("offers the six databases, the protocol's ticked first in its order, and an untouched picker sends no providers", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["arxiv", "crossref"] });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    expect(rowIds()).toEqual(["arxiv", "crossref", "openalex", "semanticscholar", "pubmed", "biorxiv"]);
    expect(ticked()).toEqual(["arxiv", "crossref"]);
    expect(screen.queryByRole("button", { name: /slice/i })).toBeNull();
    expect(document.querySelector("[data-picker-differs]")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: FINISHED });
    expect(runPost(engine)).toHaveLength(1);
    expect(runPost(engine)[0].body).toEqual({});
  });

  it("pre-fills from ?databases= and sends providers in that order without a touch", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ search: "?databases=crossref,openalex" });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    expect(sent(engine)).toContain("GET /api/v1/discovery/plan?providers=crossref,openalex");
    expect(ticked()).toEqual(["crossref", "openalex"]);
    expect(document.querySelector("[data-picker-differs]")).toHaveTextContent(
      "This harvest differs from the protocol: left out Semantic Scholar, arXiv, PubMed; moved Crossref, OpenAlex",
    );
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: FINISHED });
    expect(runPost(engine)[0].body).toEqual({ providers: ["crossref", "openalex"] });
  });

  it("sends providers in the chosen order once the picker was touched; the same databases in another order name the order", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    expect(screen.getByRole("button", { name: "Move OpenAlex up" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move PubMed down" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move bioRxiv up" })).toBeDisabled();
    const down = screen.getByRole("button", { name: "Move OpenAlex down" });
    down.focus();
    await user.keyboard(" ");
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move OpenAlex down" }));
    expect(document.querySelector("[data-picker-status]")).toHaveTextContent("OpenAlex moved to position 2 of 5");
    expect(document.querySelector("[data-picker-differs]")).toHaveTextContent("This harvest differs from the protocol: order");
    expect(screen.queryByRole("alert")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: FINISHED });
    expect(runPost(engine)[0].body).toEqual({ providers: ["semanticscholar", "openalex", "crossref", "arxiv", "pubmed"] });
  });

  it("disables Start with Pick at least one database once the last one is unticked", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["crossref"] });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    await user.click(screen.getByRole("checkbox", { name: "Search Crossref" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Pick at least one database.");
    expect(screen.getByRole("button", { name: "Start the harvest" })).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: "Search bioRxiv" }));
    expect(screen.getByRole("button", { name: "Start the harvest" })).toBeEnabled();
    expect(document.querySelector("[data-picker-differs]")).toHaveTextContent("This harvest differs from the protocol: added bioRxiv; left out Crossref");
    expect(runPost(engine)).toHaveLength(0);
  });

  it("maps PROVIDER_UNKNOWN from a hand-edited address to its card with the id under Details; Reset to the protocol reloads the picker", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ search: "?databases=crossref,scopus" });
    render(<DiscoveryHarvest locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "PROVIDER_UNKNOWN");
    expect(within(card.querySelector("details") as HTMLElement).getByText("scopus")).toBeInTheDocument();
    expect(within(card.querySelector("details") as HTMLElement).getByText("PROVIDER_UNKNOWN")).toBeInTheDocument();
    // The button is the card's action: its words appear once, not again as a muted line.
    expect(screen.getAllByText("Reset to the protocol")).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Reset to the protocol" }));
    const title = await screen.findByRole("heading", { name: READY });
    // The card and its button are gone: focus lands on the h1 that replaced them.
    await waitFor(() => expect(title).toHaveFocus());
    expect(sent(engine).filter((c) => c.startsWith("GET /api/v1/discovery/plan")).at(-1)).toBe("GET /api/v1/discovery/plan");
    expect(ticked()).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]);
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: FINISHED });
    expect(runPost(engine)[0].body).toEqual({});
  });

  it("lists the databases asked in the run's order, and an unasked protocol database as not selected for this harvest", async () => {
    const user = userEvent.setup();
    setUp({ search: "?databases=crossref,openalex" });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: FINISHED });
    await waitFor(() => expect(document.querySelectorAll("[data-asked]")).toHaveLength(2));
    expect([...document.querySelectorAll<HTMLElement>("[data-asked]")].map((li) => li.dataset.asked)).toEqual(["crossref", "openalex"]);
    expect(screen.getByText("Databases asked, in order")).toBeInTheDocument();
    expect([...document.querySelectorAll<HTMLElement>("[data-leg]")].map((r) => r.dataset.leg)).toEqual(["crossref", "openalex"]);
    const left = document.querySelector('[data-not-asked="semanticscholar"]') as HTMLElement;
    expect(left).toHaveTextContent("Semantic Scholar · Not selected for this harvest.");
    expect(document.querySelector('[data-not-asked="biorxiv"]')).toHaveTextContent("bioRxiv · Off by default.");
    expect(document.querySelector("[data-picker-differs]")).toHaveTextContent("This harvest differs from the protocol:");
  });

  it("reads the asked list and the not-selected rows from requested_providers, not the legs: a stopped run's unreached database was asked", async () => {
    // arXiv is in neither the protocol nor the legs: only requested_providers says it was asked.
    const { engine } = setUp({ protocolProviders: ["crossref", "openalex"] });
    // Stopped after two of the three databases asked: the legs are a strict prefix of requested_providers.
    engine.addStoppedRun(["crossref", "openalex", "arxiv"], 2);
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: "You stopped the harvest. What was fetched is kept." });
    await waitFor(() => expect(document.querySelectorAll("[data-asked]")).toHaveLength(3));
    expect([...document.querySelectorAll<HTMLElement>("[data-asked]")].map((li) => li.dataset.asked)).toEqual(["crossref", "openalex", "arxiv"]);
    expect([...document.querySelectorAll<HTMLElement>("[data-leg]")].map((r) => r.dataset.leg)).toEqual(["crossref", "openalex"]);
    expect(document.querySelector('[data-not-asked="arxiv"]')).toBeNull();
    expect(document.querySelector('[data-not-asked="semanticscholar"]')).toHaveTextContent("Semantic Scholar · Not selected in the protocol.");
    expect(document.querySelector('[data-not-asked="pubmed"]')).toHaveTextContent("PubMed · Not selected in the protocol.");
    expect(document.querySelector('[data-not-asked="biorxiv"]')).toHaveTextContent("bioRxiv · Off by default.");
  });

  it("shows the databases asked, in order, while the harvest runs: the chosen list sent with Start", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ holdRun: true });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    await user.click(screen.getByRole("checkbox", { name: "Search arXiv" }));
    await user.click(screen.getByRole("checkbox", { name: "Search PubMed" }));
    await user.click(screen.getByRole("button", { name: "Move Crossref up" }));
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("button", { name: "Stop the harvest and keep what was fetched" });
    expect(runPost(engine)[0].body).toEqual({ providers: ["openalex", "crossref", "semanticscholar"] });
    const live = document.querySelector("[data-live]") as HTMLElement;
    expect(within(live).getByText("Databases asked, in order")).toBeInTheDocument();
    expect([...live.querySelectorAll<HTMLElement>("[data-asked]")].map((li) => li.dataset.asked)).toEqual(["openalex", "crossref", "semanticscholar"]);
    expect(document.querySelector("[data-picker]")).toBeNull();
  });

  it("shows the protocol's list as the databases asked while a harvest started without providers runs", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ holdRun: true, protocolProviders: ["arxiv", "crossref"] });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("button", { name: "Stop the harvest and keep what was fetched" });
    expect(runPost(engine)[0].body).toEqual({});
    const live = document.querySelector("[data-live]") as HTMLElement;
    expect([...live.querySelectorAll<HTMLElement>("[data-asked]")].map((li) => li.dataset.asked)).toEqual(["arxiv", "crossref"]);
  });

  it("Enter on a Move button keeps focus on that row's button", async () => {
    const user = userEvent.setup();
    setUp();
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    const up = screen.getByRole("button", { name: "Move Crossref up" });
    up.focus();
    await user.keyboard("{Enter}");
    expect(ticked()).toEqual(["openalex", "crossref", "semanticscholar", "arxiv", "pubmed"]);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move Crossref up" }));
    expect(document.querySelector("[data-picker-status]")).toHaveTextContent("Crossref moved to position 2 of 5");
  });

  it("Enter on Move down that takes a row to the end puts focus on that row's Move up", async () => {
    const user = userEvent.setup();
    setUp();
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: READY });
    screen.getByRole("button", { name: "Move arXiv down" }).focus();
    await user.keyboard("{Enter}");
    expect(ticked()).toEqual(["openalex", "semanticscholar", "crossref", "pubmed", "arxiv"]);
    expect(screen.getByRole("button", { name: "Move arXiv down" })).toBeDisabled();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move arXiv up" }));
    expect(document.querySelector("[data-picker-status]")).toHaveTextContent("arXiv moved to position 5 of 5");
  });

  it("prints each leg's executed query LTR under Query sent, and no line without one", () => {
    const { row, unmount } = legRow({ provider: "crossref", fetched: 12, reported_total: 12 }, { executed_query: "weed detection edge device" });
    expect(within(row).getByText("Query sent")).toBeInTheDocument();
    const query = row.querySelector("[data-leg-query]") as HTMLElement;
    expect(query).toHaveTextContent("weed detection edge device");
    expect(query).toHaveAttribute("dir", "ltr");
    unmount();
    const bare = legRow({ provider: "arxiv", fetched: 3, reported_total: 3 });
    expect(bare.row.querySelector("[data-leg-query]")).toBeNull();
    expect(within(bare.row).queryByText("Query sent")).toBeNull();
    bare.unmount();
  });

  it("says 0 results only for an ok leg with nothing fetched and a reported total of 0 or none", () => {
    const zero = legRow({ provider: "openalex", fetched: 0, reported_total: null });
    expect(within(zero.row).getByText("0 results")).toBeInTheDocument();
    zero.unmount();
    const reported = legRow({ provider: "crossref", fetched: 0, reported_total: 1840 });
    expect(within(reported.row).getByText("Done")).toBeInTheDocument();
    expect(within(reported.row).queryByText("0 results")).toBeNull();
    expect(reported.row.querySelector("[data-count]")).toHaveTextContent("0 of 1840");
    reported.unmount();
    const failed = legRow({ provider: "pubmed", fetched: 0, reported_total: null, status: "failed", error_code: "PROVIDER_TIMEOUT" });
    expect(within(failed.row).queryByText("0 results")).toBeNull();
    failed.unmount();
  });
});
