import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TriagePage } from "@/components/triage-page";
import { SUPPORTED_LOCALES } from "@/i18n";
import type { DecisionEvent, StoredEvent } from "@/lib/screening-v1";
import { TRIAGE_COPY, tc } from "@/lib/triage-copy";
import { contradicts, decisiveFor, mayReadProposal, reasonOptions, triageKey, undoTarget } from "@/lib/triage-logic";

/**
 * Desktop triage (spec 03) and record detail (spec 05), in jsdom against a
 * small in-memory engine. The fake mirrors the M1a rules that matter to the
 * screen: blinding refuses an undecided draft read (403 `PROPOSAL_HIDDEN`), a
 * read is recorded as a reveal, and a superseding event after a reveal is
 * stamped `changed_after_reveal` by the engine, never by the client.
 */

const BINDING = { protocol_fingerprint: "sha256:" + "4".repeat(64), batch_id: "batch-1", batch_sha256: "sha256:" + "b".repeat(64) };
const CRITERIA = [
  { id: "INC-01", text: "UAV imagery", kind: "inclusion" as const },
  { id: "EXC-01", text: "Not a crop field", kind: "exclusion" as const },
];
const PROPOSAL = {
  proposal_id: "PRP-1",
  task_version: "screen-v1",
  model: "claude-opus-5-5",
  prompt_sha256: "sha256:" + "a".repeat(64),
  criteria: [
    { id: "INC-01", answer: "yes", evidence: { start: 0, end: 5, text: "drone" } },
    { id: "EXC-01", answer: "yes", evidence: { start: 0, end: 5, text: "drone" } },
  ],
  derived_outcome: "EXCLUDE",
  reason_code: "EXC-01",
  validators: [{ name: "schema", ok: true, detail: "" }],
  cannot_decide: false,
};

interface Engine {
  log: { method: string; path: string; body?: unknown }[];
  events: StoredEvent[];
  reveals: Set<string>;
  blinding: "reveal_after_decision" | "show";
  proposals: Set<string>;
  conflicts?: unknown[];
  criteria?: typeof CRITERIA;
  proposalDelay?: Promise<void>;
  proposal?: typeof PROPOSAL;
  advance?: "show_draft_then_next" | "next_at_once";
  /** The protocol's not-reported policy (M7-method). */
  policy?: "unclear" | "exclude";
}

let engine: Engine;

function studies() {
  return [
    { study_id: "STU-a", title: "Drone weed mapping", abstract: "drone imagery of maize weeds" },
    { study_id: "STU-b", title: "Title only record", abstract: null },
    { study_id: "STU-c", title: "Third record", abstract: "satellite crops" },
  ];
}

function head(study: string): StoredEvent | null {
  const mine = engine.events.filter((e) => e.study_id === study);
  const superseded = new Set(mine.map((e) => e.supersedes).filter(Boolean));
  return mine.filter((e) => !superseded.has(e.event_id)).at(-1) ?? null;
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function fakeFetch(url: string, init?: RequestInit): Promise<Response> {
  const parsed = new URL(url, "http://localhost");
  const path = parsed.pathname.replace(/^\/api\/console\/api\/v1\/screening/, "");
  const method = (init?.method ?? "GET").toUpperCase();
  const body = init?.body ? JSON.parse(String(init.body)) : undefined;
  engine.log.push({ method, path, body });
  if (path === "/settings") return Promise.resolve(json({ blinding: engine.blinding, mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: engine.advance ?? "show_draft_then_next" }));
  if (path === "/summary") {
    const decided = studies().filter((x) => head(x.study_id) !== null).length;
    return Promise.resolve(json({ total: 3, decided, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 1, needs_you: 3 - decided, conflicts: 0, lanes: { agent: 1, you: decided, second_screener: "PARKED" } }));
  }
  if (path === "/queue") {
    const view = parsed.searchParams.get("view");
    const items = studies()
      .map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", batch_index: 1, has_proposal: engine.proposals.has(s.study_id), decided: head(s.study_id) !== null, flags: s.abstract ? [] : ["title_only"] }))
      .filter((i) => (view === "decided" ? i.decided : !i.decided));
    return Promise.resolve(json({ items, next_cursor: null }));
  }
  const proposal = path.match(/^\/records\/([^/]+)\/proposal$/);
  if (proposal) {
    const study = proposal[1];
    if (engine.blinding === "reveal_after_decision" && head(study) === null) {
      return Promise.resolve(json({ detail: { code: "PROPOSAL_HIDDEN", message: "hidden" } }, 403));
    }
    if (!engine.proposals.has(study)) return Promise.resolve(json({ proposal: null }));
    engine.reveals.add(study);
    return (engine.proposalDelay ?? Promise.resolve()).then(() => json({ proposal: engine.proposal ?? PROPOSAL }));
  }
  const record = path.match(/^\/records\/([^/]+)$/);
  if (record) {
    const s = studies().find((x) => x.study_id === record[1])!;
    return Promise.resolve(
      json({ ...s, year: 2024, venue: null, doi: null, batch_index: 1, highlights: [], criteria: engine.criteria ?? CRITERIA, binding: BINDING, my_decision: head(s.study_id), history: engine.events.filter((e) => e.study_id === s.study_id), not_reported_policy: engine.policy ?? "unclear" }),
    );
  }
  if (path === "/decisions/events" && method === "POST") {
    const results = (body.events as DecisionEvent[]).map((e) => {
      engine.events.push({ ...e, received_at: "2026-11-05T10:00:00Z", token_scope: "desktop", changed_after_reveal: Boolean(e.supersedes) && engine.reveals.has(e.study_id) });
      return { event_id: e.event_id, result: "accepted" };
    });
    return Promise.resolve(json({ results }));
  }
  if (path === "/decisions/conflicts") return Promise.resolve(json({ items: engine.conflicts ?? [] }));
  return Promise.resolve(json({ detail: { code: "NOT_FOUND", message: path } }, 404));
}

beforeEach(() => {
  engine = { log: [], events: [], reveals: new Set(), blinding: "reveal_after_decision", proposals: new Set(["STU-a"]) };
  window.sessionStorage.clear(); // the queue's open/closed choice lasts the session
  vi.stubGlobal("fetch", vi.fn(fakeFetch));
});

afterEach(() => vi.unstubAllGlobals());

const proposalReads = () => engine.log.filter((l) => l.path.endsWith("/proposal"));
const postedEvents = () => engine.log.filter((l) => l.path === "/decisions/events").flatMap((l) => (l.body as { events: DecisionEvent[] }).events);

async function ready() {
  render(<TriagePage locale="en" />);
  await screen.findByText("Drone weed mapping", { selector: "p bdi" });
}

/** The checklist is collapsed by default (M8-triage); a test that answers opens it first, as a person would. */
function openChecklist() {
  const toggle = screen.queryByRole("button", { name: /^Your checklist/ });
  if (toggle && toggle.getAttribute("aria-expanded") === "false") fireEvent.click(toggle);
}

function answerAll() {
  // Inclusions yes, exclusions no (M6-beta, answer until decisive).
  openChecklist();
  for (const group of document.querySelectorAll('[role="group"][aria-label]')) {
    const id = (group as HTMLElement).getAttribute("aria-label") ?? "";
    const pick = within(group as HTMLElement).queryByRole("button", { name: id.startsWith("EXC") ? "No" : "Yes" });
    if (pick) fireEvent.click(pick);
  }
}

function answer(id: string, value: "Yes" | "No" | "Not reported") {
  openChecklist();
  const group = document.querySelector(`[role="group"][aria-label="${id}"]`) as HTMLElement;
  fireEvent.click(within(group).getByRole("button", { name: value }));
}

describe("triage.blinding-no-proposal-field", () => {
  it("never requests the draft of an undecided record, and the queue shows no agent call", async () => {
    await ready();
    expect(proposalReads()).toEqual([]);
    expect(screen.getByTestId("proposal-aside")).toHaveTextContent("Hidden until you decide.");
    expect(screen.getByRole("navigation", { name: "Queue" })).not.toHaveTextContent(/exclude/i);
  });

  it("prefetches records but never drafts (M1b-0 review P3-2)", async () => {
    await ready();
    await waitFor(() => expect(engine.log.filter((l) => l.path === "/records/STU-b").length).toBeGreaterThan(0));
    expect(proposalReads()).toEqual([]);
  });
});

describe("record-detail.hidden-until-decision and derived-outcome-from-server", () => {
  it("reads the draft only after the decision, and shows the server's outcome as not a decision", async () => {
    await ready();
    answerAll();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Your decision differs from the agent's draft.");
    expect(proposalReads()).toHaveLength(1);
    const aside = screen.getByTestId("proposal-aside");
    expect(aside).toHaveTextContent("Exclude · EXC-01");
    expect(aside).toHaveTextContent("Not a decision");
    expect(postedEvents()[0]).toMatchObject({ method: "HUMAN", outcome: "INCLUDE", criteria: [{ id: "INC-01", answer: "yes" }, { id: "EXC-01", answer: "no" }] });
  });
});

describe("record-detail.draft-never-include-tint", () => {
  it("renders the draft on the plain surface, with no include role inside the aside", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(screen.getByTestId("proposal-aside")).toHaveTextContent("Not a decision"));
    const aside = screen.getByTestId("proposal-aside");
    expect(aside.className).not.toMatch(/include/);
    expect(aside.querySelector('[data-role="include"]')).toBeNull();
  });
});

describe("record-detail.draft-answers", () => {
  it("lists every criterion with the agent's answer, open ones first, each quote under its answer", async () => {
    engine.blinding = "show";
    engine.proposal = {
      ...PROPOSAL,
      criteria: [
        { id: "INC-01", answer: "no", evidence: { start: 0, end: 5, text: "drone" } },
        { id: "INC-02", answer: "not_reported" } as (typeof PROPOSAL)["criteria"][number],
        { id: "INC-03", answer: "yes", evidence: { start: 0, end: 5, text: "Published: 2023" } },
        { id: "EXC-01", answer: "no", evidence: { start: 0, end: 5, text: "mounted on a UAV" } },
        { id: "EXC-02", answer: "not_reported" } as (typeof PROPOSAL)["criteria"][number],
      ],
      derived_outcome: "MAYBE",
      reason_code: null as unknown as string,
    };
    await ready();
    await waitFor(() => expect(screen.getByTestId("proposal-aside")).toHaveTextContent("Not a decision"));
    const list = within(screen.getByTestId("proposal-aside")).getByRole("region", { name: "The agent's answer to each criterion" });
    const items = within(list).getAllByRole("listitem");
    // All five, not the first three quotes; the two open answers lead.
    expect(items.map((li) => li.getAttribute("data-criterion"))).toEqual(["INC-02", "EXC-02", "INC-01", "INC-03", "EXC-01"]);
    expect(items[0]).toHaveTextContent("Not reported");
    expect(items[0]).toHaveTextContent("The record does not say either way.");
    // A quote is read with its answer: a refuting quote says No.
    expect(items[2]).toHaveTextContent("INC-01");
    expect(within(items[2]).getByText("No", { exact: true })).toBeInTheDocument();
    expect(within(items[2]).getByRole("blockquote")).toHaveTextContent("drone");
    expect(within(items[3]).getByText("Yes", { exact: true })).toBeInTheDocument();
  });

  it("names the list and the answers in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of ["agentAnswers", "recordSilent", "noQuote"] as const) {
        expect(tc(locale, key), `${locale} ${key}`).not.toBe("");
      }
    }
  });
});

describe("record-detail.missing-field", () => {
  it("shows a title-only record as such and an absent field as Not stored", async () => {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: /Title only record/ }));
    await screen.findByText("No abstract available");
    expect(screen.getAllByText("Not stored").length).toBeGreaterThan(0);
  });
});

describe("triage.skip-writes-no-event", () => {
  it("moves on without posting anything", async () => {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: /^Skip/ }));
    await screen.findByText("Title only record", { selector: "p bdi" });
    expect(postedEvents()).toEqual([]);
  });
});

describe("triage.undo-superseding and triage.changed-after-reveal", () => {
  it("a change after the reveal supersedes the decision and shows the engine's stamp; undo restores the previous one", async () => {
    await ready();
    answerAll();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Your decision differs from the agent's draft.");
    const first = postedEvents()[0];

    fireEvent.click(screen.getByRole("button", { name: "Change my decision" }));
    answer("EXC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Exclude/ }));
    // EXC-01 is pre-selected from the checklist, shown in words with its code (M6-beta).
    expect(screen.getByRole("button", { name: /^1\. Not a crop field/ })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Exclude with this reason" }));
    await screen.findByText("Changed after seeing the agent's draft");
    const change = postedEvents()[1];
    expect(change).toMatchObject({ outcome: "EXCLUDE", reason_code: "EXC-01", supersedes: first.event_id });
    expect(change).not.toHaveProperty("changed_after_reveal");

    fireEvent.click(screen.getByRole("button", { name: /^Undo/ }));
    await waitFor(() => expect(postedEvents()).toHaveLength(3));
    expect(postedEvents()[2]).toMatchObject({ outcome: "INCLUDE", supersedes: change.event_id, reason_code: null });
  });

  it("a first decision cannot be undone", () => {
    const first = { event_id: "e1", supersedes: null } as StoredEvent;
    expect(undoTarget(first, [first])).toBeNull();
    const second = { event_id: "e2", supersedes: "e1" } as StoredEvent;
    expect(undoTarget(second, [first, second])).toBe(first);
  });
});

describe("triage conflict from another device", () => {
  it("locks the record with the conflict card on open, and reads no draft", async () => {
    const rival = (outcome: string, id: string) => ({ event_id: id, study_id: "STU-a", outcome, reason_code: outcome === "EXCLUDE" ? "EXC-01" : null, supersedes: null });
    engine.conflicts = [{ study_id: "STU-a", screener_id: "researcher:local", events: [rival("INCLUDE", "e1"), rival("EXCLUDE", "e2")] }];
    await ready();
    await screen.findByText("Decided differently on two devices");
    expect(screen.getByRole("button", { name: "Keep Include" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Keep Exclude · EXC-01" })).toBeInTheDocument();
    expect(proposalReads()).toEqual([]);
  });
});

describe("review 1: a late draft never lands on another record", () => {
  it("keeps the aside hidden on an undecided record when the previous record's draft arrives late", async () => {
    let release: () => void = () => undefined;
    engine.proposalDelay = new Promise<void>((resolve) => (release = resolve));
    await ready();
    answerAll();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(proposalReads()).toHaveLength(1)); // A's draft is in flight
    await act(async () => {
      fireEvent.keyDown(window, { key: "j" });
    });
    await screen.findByText("Title only record", { selector: "p bdi" });
    await act(async () => release());
    await new Promise((r) => setTimeout(r, 20));
    const aside = screen.getByTestId("proposal-aside");
    expect(aside).toHaveTextContent("Hidden until you decide.");
    expect(aside).not.toHaveTextContent("Not a decision");
  });
});

describe("review 2: show mode names the draft that was on screen", () => {
  it("sends proposal_shown with revealed_after_decision false, and true for a change after a reveal", async () => {
    engine.blinding = "show";
    await ready();
    await waitFor(() => expect(screen.getByTestId("proposal-aside")).toHaveTextContent("Not a decision"));
    answerAll();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0].proposal_shown).toEqual({ proposal_id: "PRP-1", revealed_after_decision: false });
    await screen.findByText("Title only record", { selector: "p bdi" }); // moved on at once
    await act(async () => {
      fireEvent.keyDown(window, { key: "k" });
    });
    await screen.findByRole("button", { name: "Change my decision" });
    fireEvent.click(screen.getByRole("button", { name: "Change my decision" }));
    fireEvent.click(screen.getByRole("button", { name: /^Unclear/ }));
    await waitFor(() => expect(postedEvents()).toHaveLength(2));
    expect(postedEvents()[1].proposal_shown).toEqual({ proposal_id: "PRP-1", revealed_after_decision: true });
  });

  it("sends proposal_shown null when no draft was on screen", async () => {
    await ready();
    answerAll();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0].proposal_shown).toBeNull();
  });
});

describe("review 3 and 7: reason keys and Enter", () => {
  it("picks reason chip 3 by keyboard over the pre-selected one, and confirms with Enter", async () => {
    engine.criteria = [
      { id: "INC-01", text: "UAV imagery", kind: "inclusion" },
      { id: "EXC-01", text: "a", kind: "exclusion" },
      { id: "EXC-02", text: "b", kind: "exclusion" },
      { id: "EXC-03", text: "c", kind: "exclusion" },
    ];
    await ready();
    answer("INC-01", "Yes");
    answer("EXC-02", "Yes");
    answer("EXC-03", "Yes");
    await act(async () => {
      fireEvent.keyDown(window, { key: "e" });
    });
    // The first failed criterion in protocol order is pre-selected (M6-beta).
    expect(screen.getByRole("button", { name: /^2\. b/ })).toHaveAttribute("aria-pressed", "true");
    await act(async () => {
      fireEvent.keyDown(window, { key: "3" });
    });
    expect(screen.getByRole("button", { name: /^3\. c/ })).toHaveAttribute("aria-pressed", "true");
    await act(async () => {
      fireEvent.keyDown(window, { key: "Enter" });
    });
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0]).toMatchObject({ outcome: "EXCLUDE", reason_code: "EXC-03" });
  });

  it("does not submit when Enter is pressed in the note", async () => {
    await ready();
    answerAll();
    await act(async () => {
      fireEvent.keyDown(window, { key: "e" });
    });
    await act(async () => {
      fireEvent.keyDown(window, { key: "1" });
    });
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    await new Promise((r) => setTimeout(r, 20));
    expect(postedEvents()).toEqual([]);
  });
});

describe("triage.keymap", () => {
  it("answers with 1/2/3, includes with I, and ignores keys typed in the note", async () => {
    await ready();
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "i" });
    expect(postedEvents()).toEqual([]);
    // One key per render, as a person types.
    await act(async () => {
      fireEvent.keyDown(window, { key: "1" });
    });
    await act(async () => {
      fireEvent.keyDown(window, { key: "2" });
    });
    expect(within(screen.getByRole("group", { name: "INC-01" })).getByRole("button", { name: "Yes" })).toHaveAttribute("aria-pressed", "true");
    expect(within(screen.getByRole("group", { name: "EXC-01" })).getByRole("button", { name: "No" })).toHaveAttribute("aria-pressed", "true");
    await act(async () => {
      fireEvent.keyDown(window, { key: "i" });
    });
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0].outcome).toBe("INCLUDE");
  });

  it("maps keys only outside text fields and without modifiers", () => {
    const input = document.createElement("input");
    expect(triageKey({ key: "i", ctrlKey: false, metaKey: false, altKey: false }, input)).toBeNull();
    expect(triageKey({ key: "i", ctrlKey: true, metaKey: false, altKey: false }, document.body)).toBeNull();
    expect(triageKey({ key: "E", ctrlKey: false, metaKey: false, altKey: false }, document.body)).toBe("exclude");
  });
});

describe("triage logic", () => {
  it("reads a draft only when it would be shown", () => {
    expect(mayReadProposal({ hasProposal: true, decided: false, blinding: "reveal_after_decision" })).toBe(false);
    expect(mayReadProposal({ hasProposal: true, decided: true, blinding: "reveal_after_decision" })).toBe(true);
    expect(mayReadProposal({ hasProposal: true, decided: false, blinding: "show" })).toBe(true);
    expect(mayReadProposal({ hasProposal: false, decided: true, blinding: "show" })).toBe(false);
  });

  it("offers exclusion codes, then FAILS-<inclusion id>", () => {
    expect(reasonOptions(CRITERIA)).toEqual(["EXC-01", "FAILS-INC-01"]);
  });
});

describe("triage copy", () => {
  it("has the same keys and holes in every locale, none empty", () => {
    const keys = Object.keys(TRIAGE_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(TRIAGE_COPY[locale]).sort()).toEqual(keys);
      for (const key of keys as (keyof typeof TRIAGE_COPY.en)[]) {
        const value = TRIAGE_COPY[locale][key];
        expect(value.trim(), `${locale}/${key}`).not.toBe("");
        const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
        expect(holes(value), `${locale}/${key}`).toEqual(holes(TRIAGE_COPY.en[key]));
      }
    }
    expect(() => tc("en", "refused")).toThrow(/needs \{code\}/);
  });
});


// --- M6-beta, spec 03 amendments ---------------------------------------------

async function press(key: string) {
  await act(async () => {
    fireEvent.keyDown(window, { key });
  });
}

describe("triage.decisive (M8-triage: the checklist is a tool for the reason, not a gate)", () => {
  it("enables all three decisions with no answers; Include is off only while an answer fails", async () => {
    await ready();
    const include = () => screen.getByRole("button", { name: /^Include/ });
    const exclude = () => screen.getByRole("button", { name: /^Exclude/ });
    const line = () => document.querySelector("[data-decisive]");
    expect(include()).toBeEnabled();
    expect(exclude()).toBeEnabled();
    expect(screen.getByRole("button", { name: /^Unclear/ })).toBeEnabled();
    expect(line()).toHaveTextContent("The checklist is optional: decide now, or answer to give a reason.");
    answer("INC-01", "No");
    expect(include()).toBeDisabled();
    expect(exclude()).toBeEnabled();
    expect(line()).toHaveTextContent("Exclude is ready: INC-01 answered no. Include is off while it fails.");
    answer("INC-01", "Not reported");
    // Under the default policy "not reported" does not fail: Include is back.
    expect(include()).toBeEnabled();
    expect(line()).toHaveTextContent("1 of 2 answered; unanswered criteria are not recorded.");
    answer("INC-01", "Yes");
    expect(include()).toBeEnabled();
    expect(line()).toHaveTextContent("Include is ready");
    answer("EXC-01", "Yes");
    expect(include()).toBeDisabled();
    expect(line()).toHaveTextContent("Exclude is ready: EXC-01 answered yes. Include is off while it fails.");
  });

  it("sends only the criteria answered; an unanswered one is absent, never not_reported", async () => {
    await ready();
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0].criteria).toEqual([{ id: "INC-01", answer: "yes" }]);
  });

  it("decides from the answers given, never from unanswered ones", () => {
    expect(decisiveFor(CRITERIA, {})).toMatchObject({ include: true, exclude: false, failed: null, includeReady: false, answered: 0, total: 2 });
    expect(decisiveFor(CRITERIA, { "INC-01": "yes" })).toMatchObject({ include: true, includeReady: true, answered: 1 });
    expect(decisiveFor(CRITERIA, { "INC-01": "no" })).toMatchObject({ include: false, exclude: true, failed: { id: "INC-01", answer: "no", kind: "inclusion" } });
  });
});

describe("triage.collapsed-checklist", () => {
  const toggle = () => screen.getByRole("button", { name: /^Your checklist/ });

  it("is closed by default, and I includes with no answers sent", async () => {
    engine.proposals = new Set();
    await ready();
    expect(toggle()).toHaveAttribute("aria-expanded", "false");
    expect(toggle()).toHaveTextContent("No answers");
    expect(document.querySelector('[role="group"][aria-label="INC-01"]')).toBeNull();
    await press("i");
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0]).toMatchObject({ outcome: "INCLUDE", criteria: [] });
  });

  it("opens on its toggle, and that choice lasts to the next record", async () => {
    engine.proposals = new Set();
    await ready();
    fireEvent.click(toggle());
    expect(toggle()).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("group", { name: "INC-01" })).toBeInTheDocument();
    await press("i");
    await screen.findByText("Title only record", { selector: "p bdi" });
    expect(toggle()).toHaveAttribute("aria-expanded", "true");
  });

  it("opens on a number key, which answers the focused criterion; the next record opens closed", async () => {
    engine.proposals = new Set();
    await ready();
    await press("2");
    expect(toggle()).toHaveAttribute("aria-expanded", "true");
    expect(toggle()).toHaveTextContent("1 of 2 answered");
    expect(within(screen.getByRole("group", { name: "INC-01" })).getByRole("button", { name: "No" })).toHaveAttribute("aria-pressed", "true");
    await press("e");
    await press("Enter");
    await screen.findByText("Title only record", { selector: "p bdi" });
    expect(toggle()).toHaveAttribute("aria-expanded", "false");
  });

  it("opens on E with the reason chips and none chosen; a chip number then Enter excludes", async () => {
    await ready();
    await press("e");
    expect(toggle()).toHaveAttribute("aria-expanded", "true");
    expect(document.querySelector("[data-reason]")).toBeNull();
    expect(screen.getByText("Choose a reason: press its number, then Enter")).toBeInTheDocument();
    await press("Enter");
    expect(postedEvents()).toEqual([]);
    await press("2");
    expect(document.querySelector("[data-reason]")).toHaveTextContent("FAILS-INC-01");
    await press("Enter");
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0]).toMatchObject({ outcome: "EXCLUDE", reason_code: "FAILS-INC-01", criteria: [] });
  });
});

describe("triage.reason-from-checklist", () => {
  it("pre-selects the failed criterion, shows it in words, and E then Enter excludes", async () => {
    await ready();
    answer("INC-01", "No");
    await press("e");
    const chosen = document.querySelector("[data-reason]")!;
    expect(chosen).toHaveTextContent("Fails INC-01 · UAV imagery");
    expect(chosen).toHaveTextContent("FAILS-INC-01");
    await press("Enter");
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0]).toMatchObject({ outcome: "EXCLUDE", reason_code: "FAILS-INC-01" });
  });

  it("disables a chip that contradicts an answer, and its number key does nothing", async () => {
    await ready();
    answer("INC-01", "Yes");
    await press("e");
    expect(screen.getByRole("button", { name: /^2\. UAV imagery/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /^1\. Not a crop field/ })).toBeEnabled();
    await press("2");
    expect(document.querySelector("[data-reason]")).toBeNull();
    expect(contradicts("FAILS-INC-01", { "INC-01": "yes" })).toBe(true);
    expect(contradicts("EXC-01", { "EXC-01": "no" })).toBe(true);
    expect(contradicts("FAILS-INC-01", { "INC-01": "not_reported" })).toBe(false);
    expect(contradicts("EXC-01", {})).toBe(false);
  });
});

describe("triage.advance-on-decide", () => {
  it("opens the next record at once when there is no draft to reveal", async () => {
    engine.proposals = new Set();
    await ready();
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Title only record", { selector: "p bdi" });
    expect(proposalReads()).toEqual([]);
  });

  it("with a draft and the default setting, shows the draft and waits for N", async () => {
    await ready();
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Your decision differs from the agent's draft.");
    expect(screen.getByText("Drone weed mapping", { selector: "p bdi" })).toBeInTheDocument();
  });

  it("with 'move on at once', opens the next record and never reads the draft", async () => {
    engine.advance = "next_at_once";
    await ready();
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Title only record", { selector: "p bdi" });
    expect(proposalReads()).toEqual([]);
    expect(engine.reveals.size).toBe(0);
  });
});

describe("triage.position and the collapsed queue", () => {
  it("says which record of how many, and shows only the current and next titles until opened", async () => {
    await ready();
    await waitFor(() => expect(document.querySelector("[data-position]")).toHaveTextContent("Record 1 of 3 · batch 1"));
    const queue = document.querySelector("[data-queue-collapsed]") as HTMLElement;
    expect(within(queue).getByText("Drone weed mapping")).toBeInTheDocument();
    expect(within(queue).getByText("Title only record")).toBeInTheDocument();
    expect(within(queue).queryByText("Third record")).toBeNull();
    const toggle = screen.getByRole("button", { name: "Show the whole queue" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await press("j");
    expect(screen.getByRole("button", { name: "Hide the queue" })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Third record")).toBeInTheDocument();
  });
});

describe("triage.undo-hidden", () => {
  it("shows no Undo on a first decision, and Undo once there is something to undo", async () => {
    engine.proposals = new Set();
    await ready();
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Title only record", { selector: "p bdi" });
    await press("k");
    await screen.findByRole("button", { name: "Change my decision" });
    expect(screen.queryByRole("button", { name: /^Undo/ })).toBeNull();
    expect(screen.queryByText("A first decision cannot be undone; change it instead.")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Change my decision" }));
    fireEvent.click(screen.getByRole("button", { name: /^Unclear/ }));
    await screen.findByRole("button", { name: /^Undo/ });
  });
});

describe("triage.all-decided", () => {
  it("hands off to Publish when nothing needs you, with no draft aside", async () => {
    for (const s of studies()) {
      engine.events.push({ event_id: `e-${s.study_id}`, study_id: s.study_id, outcome: "INCLUDE", supersedes: null } as unknown as StoredEvent);
    }
    render(<TriagePage locale="en" />);
    await screen.findByRole("heading", { name: "All 3 records are decided" });
    expect(screen.getByRole("link", { name: "Go to publish" })).toHaveAttribute("href", "/en/screening/publish");
    expect(screen.getByRole("link", { name: "Agreement" })).toHaveAttribute("href", "/en/screening/agreement");
    expect(screen.queryByTestId("proposal-aside")).toBeNull();
    expect(screen.getByText("Every record has your decision.")).toBeInTheDocument();
  });
});

describe("triage.details", () => {
  it("keeps the study id and the provenance line behind Details, and says Saved", async () => {
    engine.proposals = new Set();
    await ready();
    const details = document.querySelector("[data-record-details]") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details).toHaveTextContent("STU-a");
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await screen.findByText("Title only record", { selector: "p bdi" });
    await press("k");
    await screen.findByText("Saved");
    const provenance = document.querySelector("[data-decision-details]") as HTMLDetailsElement;
    expect(provenance.open).toBe(false);
    expect(provenance).toHaveTextContent("Recorded as you · HUMAN");
  });
});

describe("triage review fixes (M6-beta part 2)", () => {
  it("never claims all decided before the queue has answered", async () => {
    let release: () => void = () => undefined;
    const held = new Promise<void>((r) => {
      release = r;
    });
    const real = vi.mocked(fetch).getMockImplementation()!;
    vi.mocked(fetch).mockImplementation(async (url, init) => {
      if (String(url).includes("/queue")) await held;
      return real(url as string, init);
    });
    render(<TriagePage locale="en" />);
    await waitFor(() => expect(engine.log.some((l) => l.path === "/settings")).toBe(true));
    await new Promise((r) => setTimeout(r, 20));
    expect(document.querySelector("[data-all-decided]")).toBeNull();
    expect(screen.queryByText("Every record has your decision.")).toBeNull();
    release();
    await screen.findByText("Drone weed mapping", { selector: "p bdi" });
  });

  it("with drafts and the default setting, N after the last record reaches the hand-off", async () => {
    engine.proposals = new Set(["STU-a", "STU-b", "STU-c"]);
    await ready();
    for (const title of ["Drone weed mapping", "Title only record", "Third record"]) {
      await screen.findByText(title, { selector: "p bdi" });
      answer("INC-01", "Yes");
      fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
      await screen.findByText("Your decision differs from the agent's draft.");
      await press("n");
    }
    await screen.findByRole("heading", { name: "All 3 records are decided" });
  });

  it("moves focus to the next record's title after deciding", async () => {
    engine.proposals = new Set();
    await ready();
    answer("INC-01", "Yes");
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    const title = await screen.findByText("Title only record", { selector: "p bdi" });
    await waitFor(() => expect(title.closest("p")).toHaveFocus());
  });

  it("does not confirm an Exclude whose reason an answer now contradicts", async () => {
    await ready();
    answer("INC-01", "No");
    await press("e");
    answer("INC-01", "Yes");
    await press("Enter");
    expect(postedEvents()).toEqual([]);
    expect(screen.getByRole("button", { name: "Exclude with this reason" })).toBeDisabled();
  });
});


// M7-method (spec 03 amendment 2026-11-08): the offer follows the protocol's not-reported policy.
describe("triage.not-reported-policy", () => {
  const TWO = [
    { id: "INC-01", text: "UAV imagery", kind: "inclusion" as const },
    { id: "INC-02", text: "Weeds", kind: "inclusion" as const },
    { id: "EXC-01", text: "Not a crop field", kind: "exclusion" as const },
  ];

  it("unclear (default): a not-reported inclusion neither fails nor blocks Include, and is not yet ready", () => {
    const d = decisiveFor(TWO, { "INC-01": "not_reported", "INC-02": "yes" });
    expect(d.exclude).toBe(false);
    expect(d.failed).toBeNull();
    expect(d.include).toBe(true);
    expect(d.includeReady).toBe(false);
  });

  it("exclude: a not-reported inclusion readies Exclude; a definite failure outranks it", () => {
    const nr = decisiveFor(TWO, { "INC-01": "not_reported", "INC-02": "yes" }, "exclude");
    expect(nr.exclude).toBe(true);
    expect(nr.failed).toEqual({ id: "INC-01", answer: "not_reported", kind: "inclusion" });
    const definite = decisiveFor(TWO, { "INC-01": "not_reported", "INC-02": "no" }, "exclude");
    expect(definite.failed?.id).toBe("INC-02");
    const exclusion = decisiveFor(TWO, { "INC-01": "not_reported", "EXC-01": "yes" }, "exclude");
    expect(exclusion.failed?.id).toBe("EXC-01");
  });

  it("exclude: an exclusion that is not reported never fails; a not-reported inclusion turns Include off", () => {
    const d = decisiveFor(TWO, { "INC-01": "yes", "INC-02": "yes", "EXC-01": "not_reported" }, "exclude");
    expect(d.exclude).toBe(false);
    expect(d.include).toBe(true);
    expect(d.includeReady).toBe(true);
    expect(decisiveFor(TWO, { "INC-01": "not_reported" }, "exclude").include).toBe(false);
  });

  it("on screen: Not reported, then E and Enter, excludes with FAILS-INC-01 and says why", async () => {
    engine.policy = "exclude";
    await ready();
    answer("INC-01", "Not reported");
    expect(document.querySelector("[data-decisive]")).toHaveTextContent(
      "Exclude is ready: INC-01 not reported (your protocol excludes when not reported)",
    );
    expect(screen.getByRole("button", { name: /^Exclude/ })).toBeEnabled();
    fireEvent.keyDown(window, { key: "e" });
    fireEvent.keyDown(window, { key: "Enter" });
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0]).toMatchObject({ outcome: "EXCLUDE", reason_code: "FAILS-INC-01" });
    expect(postedEvents()[0].criteria).toEqual([{ id: "INC-01", answer: "not_reported" }]);
  });
});
