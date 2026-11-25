import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryPlan, differsText } from "@/components/discovery-plan";
import type { Plan } from "@/lib/discovery-api";
import { DISCOVERY_COPY } from "@/lib/discovery-copy";

import { discoveryEngine } from "./fixtures/discovery-engine";
import { sent, setUp } from "./discovery-helpers";

/** 01 Plan (spec docs/ux/phase1-discovery/final/01-plan.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

/** The plan the fake answers, read from a separate fake so the screen's call log stays clean. */
function enginePlan(): Plan {
  return discoveryEngine().handle("GET", "/api/v1/discovery/plan", null).body as Plan;
}

describe("discovery.plan Crossref and a joined query (H-run-small-fixes, finding 9)", () => {
  it("previews the default choice without Crossref and warns when it is ticked again", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "crossref", "arxiv"] });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/plan?providers=openalex,semanticscholar,arxiv"));
    expect(screen.getByRole("checkbox", { name: "Search Crossref" })).not.toBeChecked();
    expect(document.querySelector('[data-default-without="crossref"]')).not.toBeNull();
    await user.click(screen.getByRole("checkbox", { name: "Search Crossref" }));
    await waitFor(() => expect(document.querySelector('[data-ignores-and="crossref"]')).not.toBeNull());
  });

  it("after Reset to the protocol, the estimate counts Crossref (review N1)", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "crossref", "arxiv"] });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    await user.click(await screen.findByRole("button", { name: "Reset to the protocol" }));
    await waitFor(() => expect(screen.getByRole("checkbox", { name: "Search Crossref" })).toBeChecked());
    const card = document.querySelector("[data-estimate]") as HTMLElement;
    await user.click(within(card).getByRole("button", { name: /count/i }));
    await waitFor(() => expect(engine.calls.some((c) => c.method === "POST" && c.path === "/api/v1/discovery/estimate")).toBe(true));
    const body = engine.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/discovery/estimate").at(-1)?.body as { providers?: string[] };
    expect(body.providers).toContain("crossref");
  });
});

describe("discovery.plan", () => {
  it("renders one block per provider in the engine's order with the executed strings verbatim, and no approve control", async () => {
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const plan = enginePlan();
    const blocks = [...document.querySelectorAll<HTMLElement>("[data-provider]")];
    expect(blocks.map((b) => b.dataset.provider)).toEqual(plan.providers.map((p) => p.name));
    for (const p of plan.providers) {
      const block = document.querySelector(`[data-provider="${p.name}"]`) as HTMLElement;
      if (p.executed_query) expect(within(block).getByText(p.executed_query)).toBeInTheDocument();
      else expect(block.querySelector("[data-executed]")).toBeNull();
    }
    expect(within(document.querySelector('[data-provider="biorxiv"]') as HTMLElement).getByText("Off by default")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve|gate|confirm|accept|start/i })).toBeNull();
  });

  it("shows the protocol cap and has no override field", async () => {
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const cap = document.querySelector('[data-cap="protocol"]') as HTMLElement;
    expect(within(cap).getByText("500")).toBeInTheDocument();
    expect(within(cap).getByText(/Set in the protocol\./)).toBeInTheDocument();
    // M10d (03-guidance D-P10): the sentence is the cap's hint, closed.
    expect(within(cap).getByText(/Set in the protocol\./).closest("[data-hint-body]")).toHaveAttribute("hidden");
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
    expect(screen.queryAllByRole("spinbutton")).toHaveLength(0);
    expect(screen.queryByLabelText(/cap/i, { selector: "input" })).toBeNull();
  });

  it("prints the SCHOLAR_MAILTO line and Check again re-reads the plan only", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ mailto: false });
    render(<DiscoveryPlan locale="en" />);
    const card = (await screen.findByText("SCHOLAR_MAILTO=<your email>")).closest("[data-mailto]") as HTMLElement;
    expect(within(card).getByText("Save your contact e-mail on the Settings screen; it applies at once. Or put this line in the console's environment, or in a .env file, then start the console again.")).toBeInTheDocument();
    // Let the first load's side reads settle before counting.
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/runs"));
    const before = engine.calls.length;
    engine.setMailto(true);
    await user.click(within(card).getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(document.querySelector("[data-mailto]")).toBeNull());
    expect(screen.getAllByText("Set")).toHaveLength(2); // the contact email and the OpenAlex key
    expect(sent(engine).slice(before)).toEqual(["GET /api/v1/discovery/plan"]);
  });

  it("prints the SCHOLAR_OPENALEX_KEY line when OpenAlex is selected without its key, and Check again re-reads the plan only (F12)", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ openalexKey: false });
    render(<DiscoveryPlan locale="en" />);
    const card = (await screen.findByText("SCHOLAR_OPENALEX_KEY=<your key>")).closest("[data-openalex-key]") as HTMLElement;
    expect(within(card).getByText(/OpenAlex requires a free API key since February 2026\./)).toBeInTheDocument();
    expect(document.querySelector('[data-openalex-key-set="false"]')).not.toBeNull();
    expect(screen.getByText("Required by Crossref and PubMed. OpenAlex needs its API key instead.")).toBeInTheDocument();
    expect(document.querySelector("[data-mailto]")).toBeNull();
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/runs"));
    const before = engine.calls.length;
    engine.setOpenalexKey(true);
    await user.click(within(card).getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(document.querySelector("[data-openalex-key]")).toBeNull());
    expect(document.querySelector('[data-openalex-key-set="true"]')).not.toBeNull();
    expect(sent(engine).slice(before)).toEqual(["GET /api/v1/discovery/plan"]);
  });

  it("prints the OpenAlex key line in French and Arabic with the variable name untranslated", async () => {
    for (const locale of ["fr", "ar"] as const) {
      setUp({ openalexKey: false });
      const { unmount } = render(<DiscoveryPlan locale={locale} />);
      const line = await screen.findByText("SCHOLAR_OPENALEX_KEY=<your key>");
      expect(line).toHaveAttribute("dir", "ltr");
      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("says a Semantic Scholar key is set but not verified, and that none is optional", async () => {
    setUp({ s2Key: true });
    const { unmount } = render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const row = document.querySelector('[data-s2-key-set="true"]') as HTMLElement;
    expect(within(row).getByText("Set, not yet verified")).toBeInTheDocument();
    expect(within(row).getByText(/never retried without the key/)).toBeInTheDocument();
    unmount();
    vi.unstubAllGlobals();
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const none = document.querySelector('[data-s2-key-set="false"]') as HTMLElement;
    expect(within(none).getByText("Not set")).toBeInTheDocument();
    expect(within(none).getByText(/^Optional\./)).toBeInTheDocument();
  });

  it("shows no key card when the plan does not select OpenAlex", async () => {
    const plan = enginePlan();
    const without: Plan = {
      ...plan,
      openalex_key_set: false,
      providers: plan.providers.map((p) => (p.name === "openalex" ? { ...p, selected: false, status: "not_selected", executed_query: null, request: null } : p)),
    };
    setUp({ refuseOnce: { "GET /api/v1/discovery/plan": { status: 200, body: without } } });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    expect(document.querySelector('[data-openalex-key-set="false"]')).not.toBeNull();
    expect(document.querySelector("[data-openalex-key]")).toBeNull();
  });

  it("shows No preview for a selected database without a string, and an unknown status verbatim", async () => {
    const plan = enginePlan();
    const odd: Plan = {
      ...plan,
      providers: [
        { ...plan.providers[0], status: "selected", executed_query: null, request: null },
        { ...plan.providers[1], status: "translated_later" },
        ...plan.providers.slice(2),
      ],
    };
    setUp({ refuseOnce: { "GET /api/v1/discovery/plan": { status: 200, body: odd } } });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const first = document.querySelector(`[data-provider="${plan.providers[0].name}"]`) as HTMLElement;
    expect(within(first).getByText("No preview for this database.")).toBeInTheDocument();
    expect(first.querySelector("[data-executed]")).toBeNull();
    const second = document.querySelector(`[data-provider="${plan.providers[1].name}"]`) as HTMLElement;
    expect(within(second).getByText("translated_later")).toBeInTheDocument();
  });

  it.each([
    ["PROTOCOL_MISSING", "missing", "Write the protocol in inception"],
    ["PROTOCOL_INVALID", "invalid", "Open inception"],
  ] as const)("maps %s to its card with the code under Details and a link to inception", async (code, protocol, link) => {
    setUp({ protocol });
    render(<DiscoveryPlan locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", code);
    const details = card.querySelector("details") as HTMLDetailsElement;
    expect(within(details).getByText(code)).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: link })).toHaveAttribute("href", "/en/inception/");
    expect(document.querySelector("[data-provider]")).toBeNull();
  });

  it("copies all executed strings verbatim", async () => {
    const user = userEvent.setup();
    const { writeText } = setUp();
    render(<DiscoveryPlan locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Copy all executed strings" }));
    const plan = enginePlan();
    const text = (writeText.mock.calls as unknown as string[][])[0]?.[0] ?? "";
    for (const p of plan.providers) {
      if (p.executed_query) expect(text).toContain(p.executed_query);
    }
    expect(text.split("\n")).toHaveLength(plan.providers.filter((p) => p.executed_query).length);
    await screen.findByText("Copied");
  });
});

// --------------------------------------------------------------------------- M10a: the database choice per harvest

const TITLE = "This is what each database will receive";
const PLAN_READS = (engine: ReturnType<typeof discoveryEngine>) => sent(engine).filter((c) => c.startsWith("GET /api/v1/discovery/plan"));
const rowIds = () => [...document.querySelectorAll<HTMLElement>("[data-picker-row]")].map((r) => r.dataset.pickerRow);
const ticked = () => [...document.querySelectorAll<HTMLElement>('[data-picker-row][data-selected="true"]')].map((r) => r.dataset.pickerRow);
const blocks = () => [...document.querySelectorAll<HTMLElement>("[data-provider]")].map((b) => b.dataset.provider);

describe("discovery.plan database picker (M10a)", () => {
  it("lists the six databases, the protocol's ticked first in its order, bioRxiv unticked and off by default; the first read sends no providers", async () => {
    const { engine } = setUp({ protocolProviders: ["crossref", "openalex"] });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const picker = document.querySelector("[data-picker]") as HTMLElement;
    expect(within(picker).getByText("Databases to search")).toBeInTheDocument();
    expect(rowIds()).toEqual(["crossref", "openalex", "semanticscholar", "arxiv", "pubmed", "biorxiv"]);
    expect(ticked()).toEqual(["crossref", "openalex"]);
    const biorxiv = document.querySelector('[data-picker-row="biorxiv"]') as HTMLElement;
    expect(biorxiv).toHaveAttribute("data-selected", "false");
    expect(within(biorxiv).getByText("Off by default")).toBeInTheDocument();
    expect(screen.getByText("The order only sets the order the databases are searched and listed; it never changes the corpus.")).toBeInTheDocument();
    expect(PLAN_READS(engine)).toEqual(["GET /api/v1/discovery/plan"]);
    expect(document.querySelector("[data-picker-differs]")).toBeNull();
  });

  it("unticking one re-reads the plan with the chosen order, lists the chosen databases first and names what was left out", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    await user.click(screen.getByRole("checkbox", { name: "Search Semantic Scholar" }));
    await waitFor(() => expect(PLAN_READS(engine)).toContain("GET /api/v1/discovery/plan?providers=openalex,crossref,arxiv,pubmed"));
    await waitFor(() => expect(blocks()).toEqual(["openalex", "crossref", "arxiv", "pubmed", "semanticscholar", "biorxiv"]));
    expect(document.querySelector('[data-provider="semanticscholar"]')).toHaveAttribute("data-status", "not_selected");
    const differs = document.querySelector("[data-picker-differs]") as HTMLElement;
    expect(differs).toHaveTextContent("This harvest differs from the protocol: left out Semantic Scholar");
    expect(differs).toHaveAttribute("data-role", "unclear");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("moving one keeps focus on the same button, announces the position, re-reads in that order and names the order", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    expect(screen.getByRole("button", { name: "Move OpenAlex up" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move PubMed down" })).toBeDisabled();
    const up = screen.getByRole("button", { name: "Move Crossref up" });
    up.focus();
    await user.keyboard("{Enter}");
    await waitFor(() => expect(PLAN_READS(engine)).toContain("GET /api/v1/discovery/plan?providers=openalex,crossref,semanticscholar,arxiv,pubmed"));
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move Crossref up" }));
    expect(document.querySelector("[data-picker-status]")).toHaveTextContent("Crossref moved to position 2 of 5");
    await waitFor(() => expect(document.querySelector("[data-picker-differs]")).toHaveTextContent("This harvest differs from the protocol: order"));
  });

  it("Reset to the protocol restores the protocol's list and reads the plan without providers", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    await user.click(screen.getByRole("checkbox", { name: "Search arXiv" }));
    await waitFor(() => expect(document.querySelector("[data-picker-differs]")).not.toBeNull());
    await user.click(screen.getByRole("button", { name: "Reset to the protocol" }));
    await waitFor(() => expect(document.querySelector("[data-picker-differs]")).toBeNull());
    expect(ticked()).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]);
    expect(PLAN_READS(engine).at(-1)).toBe("GET /api/v1/discovery/plan");
    // The reset button is gone with the difference: focus goes to the page's h1, not to the body.
    expect(screen.queryByRole("button", { name: "Reset to the protocol" })).toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: TITLE })).toHaveFocus();
  });

  it("unticking the last database says Pick at least one database and makes no request", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ protocolProviders: ["crossref"] });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/runs"));
    const before = engine.calls.length;
    await user.click(screen.getByRole("checkbox", { name: "Search Crossref" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Pick at least one database.");
    expect(engine.calls.length).toBe(before);
    expect(screen.queryByRole("link", { name: "Continue to Harvest with this choice" })).toBeNull();
  });

  it("carries ?databases= to Harvest only when the choice differs, never to Recall, and neither exit is the brand button", async () => {
    const user = userEvent.setup();
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const harvest = () => screen.getByRole("link", { name: "Continue to Harvest with this choice" });
    const recall = () => screen.getByRole("link", { name: "Continue to Recall" });
    expect(harvest()).toHaveAttribute("href", "/en/discovery/harvest/");
    expect(recall()).toHaveAttribute("href", "/en/discovery/recall/");
    await user.click(screen.getByRole("button", { name: "Move Crossref up" }));
    await waitFor(() => expect(harvest()).toHaveAttribute("href", "/en/discovery/harvest/?databases=openalex,crossref,semanticscholar,arxiv,pubmed"));
    expect(recall()).toHaveAttribute("href", "/en/discovery/recall/");
    // M10d (03-guidance rule 2, per-screen check): "Continue to Recall" is the Plan's one main action; the Harvest exit is not.
    expect(harvest().className).not.toMatch(/\bbg-brand\b/);
    expect(recall()).toHaveAttribute("data-variant", "primary");
  });

  it("maps PROVIDER_UNKNOWN from the address to its card with the id under Details, and Reset to the protocol reads the protocol's plan", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ search: "?databases=openalex,scopus" });
    render(<DiscoveryPlan locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "PROVIDER_UNKNOWN");
    const details = card.querySelector("details") as HTMLDetailsElement;
    expect(within(details).getByText("PROVIDER_UNKNOWN")).toBeInTheDocument();
    expect(within(details).getByText("scopus")).toBeInTheDocument();
    expect(PLAN_READS(engine)).toEqual(["GET /api/v1/discovery/plan?providers=openalex,scopus"]);
    // The button is the card's action: its words appear once, not again as a muted line.
    expect(screen.getAllByText("Reset to the protocol")).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Reset to the protocol" }));
    const title = await screen.findByRole("heading", { level: 1, name: TITLE });
    expect(PLAN_READS(engine).at(-1)).toBe("GET /api/v1/discovery/plan");
    expect(ticked()).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]);
    // The card and its button are gone: focus lands on the h1 of the plan that replaced them.
    await waitFor(() => expect(title).toHaveFocus());
  });

  it("renders the picker right to left in Arabic with its own copy and logical classes only", async () => {
    setUp();
    const { container } = render(
      <div dir="rtl">
        <DiscoveryPlan locale="ar" />
      </div>,
    );
    const ar = DISCOVERY_COPY.ar;
    await screen.findByText(ar["plan.picker.legend"]);
    expect(screen.getByRole("checkbox", { name: ar["plan.picker.check.crossref"] })).toBeChecked();
    expect(screen.getByRole("button", { name: ar["plan.picker.up.crossref"] })).toBeEnabled();
    const picker = container.querySelector("[data-picker]") as HTMLElement;
    for (const [label, pattern] of PHYSICAL) expect(picker.innerHTML.match(pattern)?.[0], label).toBeUndefined();
    expect(picker.closest("[dir]")?.getAttribute("dir")).toBe("rtl");
  });

  it("names the moved databases when some are added or left out and the shared ones are reordered, and says order only when nothing else differs", () => {
    const protocol = ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"];
    expect(differsText("en", ["crossref", "openalex"], protocol)).toBe(
      "This harvest differs from the protocol: left out Semantic Scholar, arXiv, PubMed; moved Crossref, OpenAlex",
    );
    expect(differsText("en", ["openalex", "crossref", "semanticscholar", "biorxiv"], protocol)).toBe(
      "This harvest differs from the protocol: added bioRxiv; left out arXiv, PubMed; moved Crossref, Semantic Scholar",
    );
    expect(differsText("en", ["semanticscholar", "openalex", "crossref", "arxiv", "pubmed"], protocol)).toBe("This harvest differs from the protocol: order");
    expect(differsText("en", [...protocol, "biorxiv"], protocol)).toBe("This harvest differs from the protocol: added bioRxiv");
    expect(differsText("en", protocol, protocol)).toBeNull();
    for (const locale of ["fr", "ar"] as const) {
      const moved = DISCOVERY_COPY[locale]["plan.picker.differs.moved"];
      expect(moved).toContain("{names}");
      expect(differsText(locale, ["crossref", "openalex"], protocol)).toContain(moved.replace("{names}", locale === "ar" ? "Crossref، OpenAlex" : "Crossref, OpenAlex"));
    }
  });

  it("keeps the previous strings dimmed under a Loading status line while a changed choice is read, and invents none", async () => {
    const user = userEvent.setup();
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const arxiv = enginePlan().providers.find((p) => p.name === "arxiv")?.executed_query as string;
    // The status line is in the page before any change (a live region must exist before it speaks),
    // outside the busy section (a busy region's changes may not be announced).
    const status = document.querySelector("[data-plan-status]") as HTMLElement;
    expect(status).toHaveAttribute("role", "status");
    expect(status).toHaveTextContent("");
    expect(status.closest("[data-plan-strings]")).toBeNull();
    const held = holdPlanReads();
    await user.click(screen.getByRole("checkbox", { name: "Search arXiv" }));
    await waitFor(() => expect(held).toHaveLength(1));
    const strings = document.querySelector("[data-plan-strings]") as HTMLElement;
    expect(strings).toHaveAttribute("aria-busy", "true");
    expect(document.querySelector("[data-plan-status]")).toBe(status);
    expect(status).toHaveTextContent("Loading the plan for this choice");
    expect(status.closest("[aria-busy]")).toBeNull();
    expect(strings.querySelector("[data-plan-blocks]")).toHaveAttribute("data-dimmed", "true");
    // The last answer stays readable as it was: arXiv still shows the string it was last sent.
    expect(blocks()).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"]);
    expect(within(document.querySelector('[data-provider="arxiv"]') as HTMLElement).getByText(arxiv)).toBeInTheDocument();
    held[0].release();
    await waitFor(() => expect(document.querySelector("[data-plan-strings]")).not.toHaveAttribute("aria-busy"));
    expect(document.querySelector("[data-plan-loading]")).toBeNull();
    expect(document.querySelector("[data-plan-status]")).toBe(status);
    expect(status).toHaveTextContent("");
    expect(document.querySelector("[data-plan-blocks]")).not.toHaveAttribute("data-dimmed");
    expect(document.querySelector('[data-provider="arxiv"]')).toHaveAttribute("data-status", "not_selected");
  });

  it("shows the later choice when two re-reads answer out of order", async () => {
    const user = userEvent.setup();
    const { engine } = setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const held = holdPlanReads();
    await user.click(screen.getByRole("checkbox", { name: "Search arXiv" }));
    await user.click(screen.getByRole("button", { name: "Move Crossref up" }));
    await waitFor(() => expect(held.map((h) => h.url)).toEqual(["/discovery/plan?providers=openalex,semanticscholar,crossref,pubmed", "/discovery/plan?providers=openalex,crossref,semanticscholar,pubmed"]));
    held[1].release();
    await waitFor(() => expect(blocks()).toEqual(["openalex", "crossref", "semanticscholar", "pubmed", "arxiv", "biorxiv"]));
    // The earlier read answers last: its answer is dropped.
    held[0].release();
    await waitFor(() => expect(PLAN_READS(engine)).toHaveLength(3));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(blocks()).toEqual(["openalex", "crossref", "semanticscholar", "pubmed", "arxiv", "biorxiv"]);
    expect(ticked()).toEqual(["openalex", "crossref", "semanticscholar", "pubmed"]);
    expect(document.querySelector("[data-picker-differs]")).toHaveTextContent("This harvest differs from the protocol: left out arXiv; moved Crossref, Semantic Scholar");
    expect(document.querySelector("[data-plan-loading]")).toBeNull();
  });

  it("Check again finds the protocol's list changed: the picker resets to it and says the protocol changed", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ mailto: false });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    await user.click(screen.getByRole("checkbox", { name: "Search arXiv" }));
    await waitFor(() => expect(document.querySelector('[data-provider="arxiv"]')).toHaveAttribute("data-status", "not_selected"));
    expect(document.querySelector("[data-plan-changed]")).toBeNull();
    engine.setProtocolProviders(["crossref", "pubmed"]);
    await user.click(within(document.querySelector("[data-mailto]") as HTMLElement).getByRole("button", { name: "Check again" }));
    expect(await screen.findByText("The protocol changed since this page was read.")).toHaveAttribute("data-plan-changed");
    await waitFor(() => expect(ticked()).toEqual(["crossref", "pubmed"]));
    // Check again re-read the current choice, then the protocol's own plan.
    expect(PLAN_READS(engine).slice(-2)).toEqual(["GET /api/v1/discovery/plan?providers=openalex,semanticscholar,crossref,pubmed", "GET /api/v1/discovery/plan"]);
    await waitFor(() => expect(document.querySelector('[data-provider="crossref"]')).toHaveAttribute("data-status", "translated"));
    expect(document.querySelector('[data-provider="openalex"]')).toHaveAttribute("data-status", "not_selected");
    expect(document.querySelector("[data-picker-differs]")).toBeNull();
    expect(screen.getByRole("link", { name: "Continue to Harvest with this choice" })).toHaveAttribute("href", "/en/discovery/harvest/");
  });

  it("PROVIDER_UNKNOWN says the database is unknown and nothing was started, and shows an empty name as quotes under Details", async () => {
    setUp({ search: "?databases=openalex,,crossref" });
    render(<DiscoveryPlan locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "PROVIDER_UNKNOWN");
    expect(within(card).getByText("That database is not one the engine knows. Nothing was started.")).toBeInTheDocument();
    expect(card.textContent).not.toMatch(/list is under Details/);
    const details = card.querySelector("details") as HTMLDetailsElement;
    expect([...details.querySelectorAll("[data-unknown-provider]")].map((el) => el.textContent)).toEqual(['""']);
    expect(screen.getByRole("button", { name: "Reset to the protocol" })).toBeInTheDocument();
  });
});

/** The physical-direction class patterns of tests/i18n-direction-source.test.ts (N10), width suffixes optional. */
const PHYSICAL: Array<[string, RegExp]> = [
  ["border-left", /border-l(?:-[0-9]+)?(?![\w-])/],
  ["border-right", /border-r(?:-[0-9]+)?(?![\w-])/],
  ["rounded-left", /rounded-l(?:-[0-9]+)?(?![\w-])/],
  ["rounded-right", /rounded-r(?:-[0-9]+)?(?![\w-])/],
  ["text-align", /text-left|text-right(?![\w-])/],
  ["margin-left", /ml-\d/],
  ["margin-right", /mr-\d/],
  ["padding-left", /pl-\d/],
  ["padding-right", /pr-\d/],
  ["inset-left", /left-\d/],
  ["inset-right", /right-\d/],
  ["reversed flow", /space-x-reverse|divide-x-reverse/],
  ["transform origin", /origin-left|origin-right/],
  ["float", /float-left|float-right/],
];

/** Holds each `GET /discovery/plan?providers=` read until the test releases it (the fake answers then). */
function holdPlanReads(): { url: string; release: () => void }[] {
  const inner = globalThis.fetch;
  const held: { url: string; release: () => void }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const at = url.indexOf("/discovery/plan?providers=");
      if (at < 0) return inner(input, init);
      return new Promise<Response>((resolve) => held.push({ url: url.slice(at), release: () => resolve(inner(input, init)) }));
    }),
  );
  return held;
}
