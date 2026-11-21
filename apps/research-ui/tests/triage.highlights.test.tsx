import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TriagePage } from "@/components/triage-page";
import { QUOTES_KEY, TERMS_KEY } from "@/components/triage-marks";
import type { Locale } from "@/i18n";
import type { DecisionEvent, QuotePlace, SearchTerms, StoredEvent } from "@/lib/screening-v1";

/**
 * M8b-triage-highlights (spec 03, M8b): search-term marks and the agent's
 * quotes in the record pane, against a small in-memory engine that follows the
 * blinding rule (an undecided draft read is refused, 403 `PROPOSAL_HIDDEN`).
 */

const BINDING = { protocol_fingerprint: "sha256:" + "4".repeat(64), batch_id: "batch-1", batch_sha256: "sha256:" + "b".repeat(64) };
const CRITERIA = [
  { id: "INC-01", text: "UAV imagery", kind: "inclusion" as const },
  { id: "EXC-01", text: "Not a crop field", kind: "exclusion" as const },
];
const TITLE = "Drone weed mapping";
const ABSTRACT = "drone imagery of maize weeds";
const TERMS: SearchTerms = {
  concepts: [
    { concept: "UAV", terms: ["UAV", "drone"], mentions: 2 },
    { concept: "weed", terms: ["weed"], mentions: 2 },
    { concept: "rice", terms: ["rice"], mentions: 0 },
  ],
  marks: [
    { field: "title", start: 0, end: 5, concept: 0 },
    { field: "title", start: 6, end: 10, concept: 1 },
    { field: "abstract", start: 0, end: 5, concept: 0 },
    { field: "abstract", start: 23, end: 28, concept: 1 },
  ],
};
const QUOTES: QuotePlace[] = [
  // "imagery of maize weeds": the weed term sits inside the quote (overlap)
  { criterion_id: "INC-01", answer: "yes", found: true, field: "abstract", start: 6, end: 28 },
  { criterion_id: "EXC-01", answer: "no", found: false, field: null, start: null, end: null },
];

interface Engine {
  log: { method: string; path: string }[];
  events: StoredEvent[];
  blinding: "reveal_after_decision" | "show";
  terms?: SearchTerms;
  quotes?: QuotePlace[] | undefined;
}

let engine: Engine;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

const decided = (study: string) => engine.events.some((e) => e.study_id === study);

function fakeFetch(url: string, init?: RequestInit): Promise<Response> {
  const parsed = new URL(url, "http://localhost");
  const path = parsed.pathname.replace(/^\/api\/console\/api\/v1\/screening/, "");
  const method = (init?.method ?? "GET").toUpperCase();
  engine.log.push({ method, path });
  if (path === "/settings") return Promise.resolve(json({ blinding: engine.blinding, mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: "show_draft_then_next" }));
  if (path === "/summary") return Promise.resolve(json({ total: 1, decided: decided("STU-a") ? 1 : 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 1, needs_you: decided("STU-a") ? 0 : 1, conflicts: 0, lanes: { agent: 1, you: 0, second_screener: "PARKED" } }));
  if (path === "/queue") {
    const view = parsed.searchParams.get("view");
    const item = { study_id: "STU-a", title: TITLE, batch_id: "batch-1", batch_index: 1, has_proposal: true, decided: decided("STU-a"), flags: [] };
    return Promise.resolve(json({ items: (view === "decided") === item.decided ? [item] : [], next_cursor: null }));
  }
  if (path === "/records/STU-a/proposal") {
    if (engine.blinding === "reveal_after_decision" && !decided("STU-a")) return Promise.resolve(json({ detail: { code: "PROPOSAL_HIDDEN", message: "hidden" } }, 403));
    const proposal = {
      proposal_id: "PRP-1",
      task_version: "screen-v1",
      model: "claude-opus-5-5",
      prompt_sha256: "sha256:" + "a".repeat(64),
      criteria: [
        { id: "INC-01", answer: "yes", evidence: { start: 25, end: 47, text: "imagery of maize weeds" } },
        { id: "EXC-01", answer: "no", evidence: { start: 3, end: 9, text: "fields" } },
      ],
      derived_outcome: "INCLUDE",
      reason_code: null,
      validators: [{ name: "quote_in_source", ok: false, detail: "EXC-01: quote not at its offsets" }],
      cannot_decide: false,
      ...(engine.quotes ? { quotes: engine.quotes } : {}),
    };
    return Promise.resolve(json({ proposal }));
  }
  if (path === "/records/STU-a") {
    return Promise.resolve(
      json({ study_id: "STU-a", title: TITLE, abstract: ABSTRACT, year: 2024, venue: null, doi: null, batch_index: 1, highlights: [], criteria: CRITERIA, binding: BINDING, my_decision: engine.events.at(-1) ?? null, history: engine.events, not_reported_policy: "unclear", ...(engine.terms ? { search_terms: engine.terms } : {}) }),
    );
  }
  if (path === "/decisions/events" && method === "POST") {
    const body = JSON.parse(String(init!.body)) as { events: DecisionEvent[] };
    const results = body.events.map((e) => {
      engine.events.push({ ...e, received_at: "2026-11-21T10:00:00Z", token_scope: "desktop", changed_after_reveal: false });
      return { event_id: e.event_id, result: "accepted" };
    });
    return Promise.resolve(json({ results }));
  }
  if (path === "/decisions/conflicts") return Promise.resolve(json({ items: [] }));
  return Promise.resolve(json({ detail: { code: "NOT_FOUND", message: path } }, 404));
}

beforeEach(() => {
  engine = { log: [], events: [], blinding: "reveal_after_decision", terms: TERMS, quotes: QUOTES };
  window.sessionStorage.clear();
  window.localStorage.clear();
  vi.stubGlobal("fetch", vi.fn(fakeFetch));
  Element.prototype.scrollIntoView = vi.fn();
});

afterEach(() => vi.unstubAllGlobals());

async function ready(locale: Locale = "en") {
  render(<TriagePage locale={locale} />);
  await waitFor(() => expect(document.querySelector("[data-record-abstract]")).not.toBeNull());
}

const pane = () => document.querySelector("[data-record-pane]") as HTMLElement;
const legend = () => document.querySelector("[data-marks-legend]") as HTMLElement;
const switchOf = (name: string) => document.querySelector(`[data-marks-switch="${name}"]`) as HTMLButtonElement | null;
const termMarks = () => [...pane().querySelectorAll("[data-term]")].map((m) => [m.textContent, m.getAttribute("data-term")]);
const quoteMarks = () => [...pane().querySelectorAll("[data-quote]")];

describe("triage.highlights legend", () => {
  it("names every concept in protocol order, with mentions in words and the absent one said absent", async () => {
    await ready();
    const items = within(legend()).getAllByRole("listitem");
    expect(items.map((i) => i.textContent)).toEqual(["AaUAV: 2 mentions", "Aaweed: 2 mentions", "Aarice: not in this record"].map((s) => s.replace(/(UAV|weed|rice)/, "⁨$1⁩")));
    expect(legend()).toHaveTextContent("Mentions 2 of 3 concepts");
    expect(within(legend()).getByRole("list")).toHaveAccessibleName("Search terms in this record");
  });

  it("says 1 mention in the singular and uses the Arabic forms", async () => {
    engine.terms = { ...TERMS, concepts: [{ concept: "UAV", terms: ["UAV"], mentions: 1 }] };
    await ready();
    expect(legend()).toHaveTextContent("1 mention");
    expect(legend()).not.toHaveTextContent("1 mentions");
  });

  it("caps the marks at four: the fifth concept on share one item, Other concepts", async () => {
    const concepts = ["a1", "b2", "c3", "d4", "e5", "f6"].map((concept, i) => ({ concept, terms: [concept], mentions: i === 5 ? 3 : 0 }));
    engine.terms = { concepts, marks: [{ field: "title", start: 0, end: 5, concept: 5 }] };
    await ready();
    const items = within(legend()).getAllByRole("listitem");
    expect(items).toHaveLength(5);
    expect(items[4]).toHaveTextContent("Other concepts: 3 mentions (e5, f6)");
    expect(termMarks()).toEqual([["Drone", "4"]]);
  });

  it("with no concepts, says so and offers no search-terms switch", async () => {
    engine.terms = { concepts: [], marks: [] };
    await ready();
    expect(pane()).toHaveTextContent("The protocol has no search concepts.");
    expect(switchOf("terms")).toBeNull();
    expect(legend()).toBeNull();
  });

  it("with an older engine (no search_terms), shows no marks bar", async () => {
    engine.terms = undefined;
    await ready();
    expect(document.querySelector("[data-marks-bar]")).toBeNull();
    expect(pane()).toHaveTextContent(ABSTRACT);
  });
});

describe("triage.highlights search terms", () => {
  it("marks each concept's words in the title and the abstract, text unchanged", async () => {
    await ready();
    expect(termMarks()).toEqual([["Drone", "0"], ["weed", "1"], ["drone", "0"], ["weeds", "1"]]);
    expect(document.querySelector("[data-record-abstract]")!.textContent).toBe(ABSTRACT);
    expect(document.querySelector("[data-record-title]")!.textContent).toBe(TITLE);
  });

  it("the switch turns them off, keeps the legend, and is remembered on this computer", async () => {
    await ready();
    const terms = switchOf("terms")!;
    expect(terms).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(terms);
    expect(terms).toHaveAttribute("aria-pressed", "false");
    expect(termMarks()).toEqual([]);
    expect(legend()).not.toBeNull();
    expect(window.localStorage.getItem(TERMS_KEY)).toBe("0");
  });

  it("starts off when this computer remembers it off", async () => {
    window.localStorage.setItem(TERMS_KEY, "0");
    await ready();
    expect(switchOf("terms")).toHaveAttribute("aria-pressed", "false");
    expect(termMarks()).toEqual([]);
  });
});

describe("triage.highlights agent's quotes and blinding", () => {
  it("shows no quote and no quotes switch before the decision under reveal_after_decision", async () => {
    await ready();
    expect(quoteMarks()).toHaveLength(0);
    expect(switchOf("quotes")).toBeNull();
    expect(engine.log.filter((l) => l.path.endsWith("/proposal"))).toEqual([]);
  });

  it("marks the quotes once the decision reveals the draft", async () => {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    expect(switchOf("quotes")).toHaveAttribute("aria-pressed", "true");
  });

  it("under show, marks the quotes with the draft, tied to criterion and answer, never in a decision colour", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    const [quote] = quoteMarks();
    expect(quote.textContent).toBe("imagery of maize weeds");
    expect(quote).toHaveAccessibleName("imagery of maize weeds (agent's quote for INC-01 (yes))");
    expect(quote.className).not.toMatch(/include|exclude|unclear|blocked/);
    // The weed term stays marked inside the quote (overlap layering).
    expect(quote.querySelector('[data-term="1"]')!.textContent).toBe("weeds");
  });

  it("a quote not at its place is not marked and the draft says so", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    const exc = document.getElementById("answer-EXC-01")!;
    expect(exc).toHaveTextContent("Not found at its place in the record, so it is not marked.");
    expect(within(exc).queryByRole("button", { name: "Show in the text" })).toBeNull();
    expect(quoteMarks().some((q) => q.getAttribute("data-quote")!.includes("EXC-01"))).toBe(false);
  });

  it("activating the quote moves focus to its answer in the draft", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    fireEvent.click(quoteMarks()[0]);
    expect(document.activeElement).toBe(document.getElementById("answer-INC-01"));
    expect(quoteMarks()[0]).toHaveAttribute("data-active");
  });

  it("hovering an answer frames its quote; Show in the text scrolls to it", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    const inc = document.getElementById("answer-INC-01")!;
    fireEvent.mouseEnter(inc);
    expect(quoteMarks()[0]).toHaveAttribute("data-active");
    expect(quoteMarks()[0].className).toMatch(/ring-2/);
    fireEvent.mouseLeave(inc);
    expect(quoteMarks()[0]).not.toHaveAttribute("data-active");
    fireEvent.click(within(inc).getByRole("button", { name: "Show in the text" }));
    await waitFor(() => expect(Element.prototype.scrollIntoView).toHaveBeenCalled());
  });

  it("the quotes switch hides them and is remembered; Show in the text still marks that one quote", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    fireEvent.click(switchOf("quotes")!);
    expect(quoteMarks()).toHaveLength(0);
    expect(window.localStorage.getItem(QUOTES_KEY)).toBe("0");
    fireEvent.click(within(document.getElementById("answer-INC-01")!).getByRole("button", { name: "Show in the text" }));
    expect(quoteMarks()).toHaveLength(1);
    expect(switchOf("quotes")).toHaveAttribute("aria-pressed", "false");
  });

  it("an older engine without quotes shows no quotes switch", async () => {
    engine.blinding = "show";
    engine.quotes = undefined;
    await ready();
    await waitFor(() => expect(screen.getByTestId("proposal-aside")).toHaveTextContent("Not a decision"));
    expect(switchOf("quotes")).toBeNull();
    expect(quoteMarks()).toHaveLength(0);
  });
});

describe("triage.highlights in Arabic", () => {
  it("speaks Arabic in the bar and the quote's name, and keeps the abstract's text", async () => {
    engine.blinding = "show";
    await ready("ar");
    await waitFor(() => expect(quoteMarks()).toHaveLength(1));
    expect(switchOf("terms")).toHaveTextContent("مصطلحات البحث");
    expect(switchOf("quotes")).toHaveTextContent("اقتباسات الوكيل");
    expect(legend()).toHaveTextContent("غير موجود في هذا السجل");
    expect(quoteMarks()[0]).toHaveAccessibleName(/اقتباس الوكيل لـ INC-01/);
    expect(document.querySelector("[data-record-abstract]")!.getAttribute("dir")).toBe("auto");
  });
});
