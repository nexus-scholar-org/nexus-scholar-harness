import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryHarvest } from "@/components/discovery-harvest";
import { DiscoveryPlan } from "@/components/discovery-plan";
import type { Estimate } from "@/lib/discovery-api";

import { FINGERPRINT, refuse } from "./fixtures/discovery-engine";
import { sent, setUp } from "./discovery-helpers";

/**
 * M10b Part D: the size estimate card on Plan and Harvest (spec docs/ux/phase1-discovery/final/01-plan.md
 * "Size estimate (M10b)"; 03-harvest.md "Size estimate (M10b)"). The engine is the stateful fake; the
 * estimate answer is stubbed with figures a naive sum in the browser would contradict.
 */

afterEach(() => {
  vi.unstubAllGlobals();
});

const ESTIMATE = "/api/v1/discovery/estimate";

type Row = Estimate["providers"][number];
const row = (name: string, extra: Partial<Row> = {}): Row => ({
  name, status: "counted", reported_total: 100, fetch_estimate: 100, fetch_is_upper_bound: false, cap_binds: false, not_fetched: 0,
  error: null, error_code: null, notes: [], ...extra,
});

/** An answer whose totals do not add up on purpose: every figure on screen must be the answer's own. */
function answer(overrides: Partial<Estimate> = {}): Estimate {
  return {
    shape: "discovery.estimate-v1",
    protocol_fingerprint: FINGERPRINT,
    counted_at: "2026-11-18T10:15:00+00:00",
    served_from_cache: false,
    recall_check: null,
    cap: { value: 500, source: "protocol", ceiling: 10000 },
    providers: [
      row("openalex", { reported_total: 4321, fetch_estimate: 500, cap_binds: true, not_fetched: 3821 }),
      row("crossref", { reported_total: 222, fetch_estimate: 222 }),
      row("arxiv", { reported_total: 77, fetch_estimate: 77, fetch_is_upper_bound: true }),
      row("pubmed", { status: "not_selected", reported_total: null, fetch_estimate: null, cap_binds: null, not_fetched: null }),
    ],
    estimate: { counted_all: true, records: { low: 7001, high: 7002 }, works: { low: 7003, high: 7004 }, assumption: "x" },
    effort: { pace_seconds: 30, hours: { low: 41.5, high: 42.5 } },
    warn: { level: "none", threshold_works: 1000, limit: { value: 1000, source: "general" } },
    recommendation: { kind: null, cap: null, expected_works: null, cuts: null },
    ...overrides,
  };
}

async function planCard(options: Parameters<typeof setUp>[0] = {}) {
  const ctx = setUp(options);
  render(<DiscoveryPlan locale="en" />);
  await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
  const card = (await waitFor(() => {
    const found = document.querySelector("[data-estimate]");
    expect(found).not.toBeNull();
    return found;
  })) as HTMLElement;
  return { ...ctx, card };
}

async function count(card: HTMLElement) {
  const user = userEvent.setup();
  await user.click(within(card).getByRole("button", { name: /Count what the databases hold|Count again/ }));
  await waitFor(() => expect(card.querySelector("[data-estimate-count]")?.getAttribute("aria-busy")).toBeNull());
  return user;
}

const estimateCalls = (engine: Parameters<typeof sent>[0]) => engine.calls.filter((c) => c.method === "POST" && c.path === ESTIMATE);

describe("discovery.estimate on Plan", () => {
  it("counts nothing on load: the empty sentence, and no estimate request", async () => {
    const { engine, card } = await planCard();
    expect(within(card).getByText(/Nothing has been counted yet\./)).toBeInTheDocument();
    expect(within(card).getByText("Estimate · not a count of what will be fetched")).toBeInTheDocument();
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/runs"));
    expect(estimateCalls(engine)).toHaveLength(0);
    // No pace field before a count (the plan has no number field).
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
  });

  it("sends exactly one POST with an empty body for the protocol's databases", async () => {
    const { engine, card } = await planCard();
    await count(card);
    expect(estimateCalls(engine)).toHaveLength(1);
    expect(estimateCalls(engine)[0].body).toEqual({});
  });

  it("prints the answer's figures, none computed in the browser", async () => {
    const { card } = await planCard({ estimate: answer() });
    await count(card);
    expect(within(card).getByText("Records: about 7002")).toBeInTheDocument();
    expect(within(card).getByText("Works after duplicates: 7003 to 7004")).toBeInTheDocument();
    expect(within(card).getByText(/At least as many works as your largest database returns/)).toBeInTheDocument();
    expect(within(card).getByText("Screening: 41.5 to 42.5 hours")).toBeInTheDocument();
    expect(within(card).getByText("At 30 seconds per record, for one reviewer. Two reviewers double it.")).toBeInTheDocument();
    expect(within(card).getByText("Cap in force: 500 per database, set in the protocol.")).toBeInTheDocument();
    // A naive sum of the rows (500 + 222 + 77 = 799) appears nowhere.
    expect(card.textContent).not.toContain("799");
    // A database the run does not ask has no row.
    expect(card.querySelector('[data-estimate-row="pubmed"]')).toBeNull();
  });

  it("says when the cap cuts a database, and when it fetches all of it; arXiv is an upper limit", async () => {
    const { card } = await planCard({ estimate: answer() });
    await count(card);
    const oa = card.querySelector('[data-estimate-row="openalex"]') as HTMLElement;
    expect(within(oa).getByText("Cut by the cap")).toBeInTheDocument();
    expect(within(oa).getByText(/OpenAlex: 4321 found, cap 500\. The first 500 will be fetched; 3821 will not\./)).toBeInTheDocument();
    const cr = card.querySelector('[data-estimate-row="crossref"]') as HTMLElement;
    expect(within(cr).getByText("All of them")).toBeInTheDocument();
    expect(within(cr).getByText("Crossref: 222 found, cap 500. All of them will be fetched.")).toBeInTheDocument();
    const ax = card.querySelector('[data-estimate-row="arxiv"]') as HTMLElement;
    expect(within(ax).getByText("will fetch up to 77")).toBeInTheDocument();
    expect(within(ax).getByText(/so this is an upper limit/)).toBeInTheDocument();
  });

  it("prints 'at least' and the unbounded warning when a database could not be counted, never '0 found'", async () => {
    const estimate = answer({
      providers: [
        row("openalex", { reported_total: 300, fetch_estimate: 300 }),
        row("semanticscholar", { status: "failed", reported_total: null, fetch_estimate: null, cap_binds: null, not_fetched: null, error: "[semanticscholar] slow down (HTTP 429)", error_code: "PROVIDER_RATE_LIMITED" }),
      ],
      estimate: { counted_all: false, records: { low: 300, high: null }, works: { low: 300, high: null }, assumption: "x" },
      effort: { pace_seconds: 30, hours: { low: 2.5, high: null } },
      warn: { level: "note", threshold_works: 1000, limit: { value: 1000, source: "general" } },
      recommendation: { kind: "narrow", cap: null, expected_works: null, cuts: null },
    });
    const { card } = await planCard({ estimate });
    await count(card);
    expect(within(card).getByText("Records: at least 300")).toBeInTheDocument();
    expect(within(card).getByText("Works after duplicates: at least 300")).toBeInTheDocument();
    expect(within(card).getByText("Screening: at least 2.5 hours")).toBeInTheDocument();
    expect(within(card).getByText("The size cannot be bounded: Semantic Scholar could not be counted.")).toBeInTheDocument();
    const s2 = card.querySelector('[data-estimate-row="semanticscholar"]') as HTMLElement;
    expect(within(s2).getByText("Not counted: The database limited the request rate.")).toBeInTheDocument();
    expect(within(s2).getByText(/slow down \(HTTP 429\)/)).toBeInTheDocument();
    expect(s2.textContent).not.toMatch(/\b0 found/);
  });

  it.each([
    ["warning", "This harvest is likely to be large: at least 7003 works, over 1000."],
    ["note", "This harvest could be large: up to 7004 works, over 1000."],
  ])("shows the %s banner", async (level, text) => {
    const { card } = await planCard({ estimate: answer({ warn: { level, threshold_works: 1000, limit: { value: 1000, source: "general" } } }) });
    await count(card);
    const banner = card.querySelector(`[data-estimate-warn="${level}"]`) as HTMLElement;
    expect(within(banner).getByText(text)).toBeInTheDocument();
    expect(within(banner).getByText(/You have not stated a planned number, so this uses a general limit of 1000\./)).toBeInTheDocument();
    expect(within(banner).getByRole("link", { name: "State how many records you plan to screen" })).toBeInTheDocument();
  });

  it("names the planned limit and offers no 'state a number' link when one is stated", async () => {
    const { card } = await planCard({ estimate: answer({ warn: { level: "warning", threshold_works: 300, limit: { value: 300, source: "planned" } } }) });
    await count(card);
    expect(within(card).getByText(/You planned to screen up to 300 records\./, { selector: "[data-estimate-warn] p" })).toBeInTheDocument();
    expect(card.querySelector("[data-estimate-set-plan]")).toBeNull();
  });

  it("shows no banner and no recommendation when the level is none", async () => {
    const { card } = await planCard({ estimate: answer() });
    await count(card);
    expect(card.querySelector("[data-estimate-warn]")).toBeNull();
    expect(card.querySelector("[data-estimate-rec]")).toBeNull();
  });

  it("offers a cap as a link to Harvest that sends nothing, never a narrow link beside it", async () => {
    const estimate = answer({
      warn: { level: "note", threshold_works: 1000, limit: { value: 1000, source: "general" } },
      recommendation: { kind: "cap", cap: 300, expected_works: { low: 300, high: 999 }, cuts: 2 },
    });
    const { engine, card } = await planCard({ estimate });
    await count(card);
    const rec = card.querySelector('[data-estimate-rec="cap"]') as HTMLElement;
    expect(within(rec).getByText(/A cap of 300 per database would keep this harvest to at most 999 records\. It cuts 2 databases short/)).toBeInTheDocument();
    const link = within(rec).getByRole("link", { name: "Use 300 for this harvest" });
    expect(link.getAttribute("href")).toBe("/en/discovery/harvest/?cap=300");
    expect(card.querySelector("[data-estimate-narrow]")).toBeNull();
    const calls = engine.calls.length;
    await userEvent.setup().click(within(rec).getByText("Why this"));
    expect(engine.calls.length).toBe(calls);
    expect(sent(engine).filter((c) => c.startsWith("POST /api/v1/discovery/runs"))).toHaveLength(0);
  });

  it("advises narrowing with the inception link and no cap button", async () => {
    const estimate = answer({
      warn: { level: "warning", threshold_works: 1000, limit: { value: 1000, source: "general" } },
      recommendation: { kind: "narrow", cap: null, expected_works: null, cuts: null },
    });
    const { card } = await planCard({ estimate });
    await count(card);
    const rec = card.querySelector('[data-estimate-rec="narrow"]') as HTMLElement;
    expect(within(rec).getByText(/Narrowing the question will help more than a cap/)).toBeInTheDocument();
    expect(within(rec).getByRole("link", { name: "Change the protocol through inception" }).getAttribute("href")).toBe("/en/inception/");
    expect(card.querySelector("[data-estimate-use-cap]")).toBeNull();
  });

  it("re-sends the estimate with the edited pace and prints the engine's new hours", async () => {
    const { engine, card } = await planCard({
      estimate: (body) => answer({ effort: { pace_seconds: (body?.pace_seconds as number) ?? 30, hours: body?.pace_seconds ? { low: 99.5, high: 100.5 } : { low: 41.5, high: 42.5 } } }),
    });
    const user = await count(card);
    const pace = within(card).getByLabelText("Seconds per record");
    expect(pace).toHaveValue("30");
    await user.clear(pace);
    await user.type(pace, "60{Enter}");
    await waitFor(() => expect(within(card).getByText("Screening: 99.5 to 100.5 hours")).toBeInTheDocument());
    expect(estimateCalls(engine).map((c) => c.body)).toEqual([{}, { pace_seconds: 60 }]);
    expect(within(card).getByText("At 60 seconds per record, for one reviewer. Two reviewers double it.")).toBeInTheDocument();
  });

  it("marks the pace field invalid on PACE_INVALID", async () => {
    const { card } = await planCard();
    const user = await count(card);
    const pace = within(card).getByLabelText("Seconds per record");
    await user.clear(pace);
    await user.type(pace, "4{Enter}");
    await waitFor(() => expect(pace).toHaveAttribute("aria-invalid", "true"));
    expect(card.querySelector('[data-refusal="PACE_INVALID"]')).not.toBeNull();
    expect(within(card).getAllByText("Use a whole number of seconds between 5 and 600").length).toBeGreaterThan(0);
  });

  it("shows no figure when the estimate was counted for another protocol", async () => {
    const { card } = await planCard({ estimate: answer({ protocol_fingerprint: "sha256:" + "00".repeat(32) }) });
    await count(card);
    expect(within(card).getByText("The protocol changed since this was counted.")).toBeInTheDocument();
    expect(card.querySelector("[data-estimate-figures]")).toBeNull();
  });

  it.each(["MAILTO_NOT_SET", "OPENALEX_KEY_NOT_SET"])("maps %s to its card with the code, and leaves the page usable", async (code) => {
    const { card } = await planCard({ refuseOnce: { [`POST ${ESTIMATE}`]: refuse(409, code, "not set") } });
    await count(card);
    const refusal = card.querySelector(`[data-refusal="${code}"]`) as HTMLElement;
    expect(refusal).not.toBeNull();
    expect(within(refusal).getByText(code)).toBeInTheDocument();
    // The rest of the page still works: the strings are there and the count can be tried again.
    expect(document.querySelectorAll("[data-provider]").length).toBeGreaterThan(0);
    expect(within(card).getByRole("button", { name: "Count what the databases hold" })).toBeEnabled();
  });

  it("keeps the last estimate 'As of' its time when the engine is unreachable", async () => {
    const { card } = await planCard({ estimate: answer() });
    await count(card);
    const working = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes("/discovery/estimate")) throw new TypeError("Failed to fetch");
      return working(input, init);
    }));
    await count(card);
    expect(card.querySelector('[data-refusal="CONSOLE_UNREACHABLE"]')).not.toBeNull();
    expect(within(card).getByText("As of 2026-11-18 10:15")).toBeInTheDocument();
    expect(within(card).getByText("Records: about 7002")).toBeInTheDocument();
  });

  it("sends the chosen databases when the run would send them, and clears the estimate when the choice changes", async () => {
    const { engine, card } = await planCard({ estimate: answer() });
    const user = await count(card);
    expect(card.querySelector("[data-estimate-figures]")).not.toBeNull();
    await user.click(screen.getByRole("checkbox", { name: "Search PubMed" }));
    await waitFor(() => expect(document.querySelector("[data-estimate-figures]")).toBeNull());
    const fresh = document.querySelector("[data-estimate]") as HTMLElement;
    await count(fresh);
    expect(estimateCalls(engine).map((c) => c.body)).toEqual([{}, { providers: ["openalex", "semanticscholar", "crossref", "arxiv"] }]);
  });

  it("uses a recall check's totals and refreshes past them on Count again", async () => {
    const { engine, card } = await planCard({ estimate: answer({ recall_check: { check: "check_001", checked_at: "2026-11-17T10:00:00+00:00" } }) });
    await count(card);
    expect(within(card).getByText("From your recall check of 2026-11-17 10:00. Count again to refresh.")).toBeInTheDocument();
    await count(card);
    expect(estimateCalls(engine).map((c) => c.body)).toEqual([{}, { refresh: true }]);
  });

  it("is not drawn once a run exists or the corpus is accepted", async () => {
    setUp({ runs: 1 });
    const first = render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    await waitFor(() => expect(document.querySelector("[data-imports-after-run]")).not.toBeNull());
    expect(document.querySelector("[data-estimate]")).toBeNull();
    first.unmount();
    vi.unstubAllGlobals();
    const { engine } = setUp({ accepted: true });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/screening/corpus"));
    await waitFor(() => expect(document.querySelector("[data-estimate]")).toBeNull());
  });
});

describe("discovery.estimate on Harvest", () => {
  async function harvest(options: Parameters<typeof setUp>[0] = {}) {
    const ctx = setUp(options);
    render(<DiscoveryHarvest locale="en" />);
    const card = (await waitFor(() => {
      const found = document.querySelector("[data-estimate]");
      expect(found).not.toBeNull();
      return found;
    })) as HTMLElement;
    return { ...ctx, card };
  }

  it("fills the cap field from ?cap= after hydration and submits nothing", async () => {
    const { engine } = await harvest({ search: "?cap=300" });
    const field = screen.getByLabelText("Cap for this harvest only");
    await waitFor(() => expect(field).toHaveValue("300"));
    expect(screen.getByText(/Filled in from the estimate\. You can change it\./)).toBeInTheDocument();
    expect(sent(engine).some((c) => c.startsWith("POST /api/v1/discovery/runs"))).toBe(false);
    expect(estimateCalls(engine)).toHaveLength(0);
  });

  it("'Use {cap}' fills the field, and Start is still a separate click", async () => {
    const estimate = answer({
      warn: { level: "note", threshold_works: 1000, limit: { value: 1000, source: "general" } },
      recommendation: { kind: "cap", cap: 282, expected_works: { low: 282, high: 999 }, cuts: 1 },
    });
    const { engine, card } = await harvest({ estimate });
    const user = await count(card);
    await user.click(within(card).getByRole("button", { name: "Use 282 for this harvest" }));
    expect(screen.getByLabelText("Cap for this harvest only")).toHaveValue("282");
    expect(sent(engine).some((c) => c.startsWith("POST /api/v1/discovery/runs"))).toBe(false);
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await waitFor(() => expect(sent(engine)).toContain("POST /api/v1/discovery/runs"));
    expect(engine.calls.find((c) => c.method === "POST" && c.path === "/api/v1/discovery/runs")?.body).toEqual({ cap_override: 282 });
  });

  it("sends the cap field's number as a what-if", async () => {
    const { engine, card } = await harvest({ search: "?cap=250" });
    await waitFor(() => expect(screen.getByLabelText("Cap for this harvest only")).toHaveValue("250"));
    await count(card);
    expect(estimateCalls(engine)[0].body).toEqual({ cap: 250 });
  });

  it("is removed once the corpus is accepted", async () => {
    setUp({ accepted: true });
    render(<DiscoveryHarvest locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-accepted]")).not.toBeNull());
    expect(document.querySelector("[data-estimate]")).toBeNull();
  });
});
