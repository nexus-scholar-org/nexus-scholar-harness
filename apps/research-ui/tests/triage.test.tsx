import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TriagePage } from "@/components/triage-page";
import { SUPPORTED_LOCALES } from "@/i18n";
import type { DecisionEvent, StoredEvent } from "@/lib/screening-v1";
import { TRIAGE_COPY, tc } from "@/lib/triage-copy";
import { mayReadProposal, reasonOptions, triageKey, undoTarget } from "@/lib/triage-logic";

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
  if (path === "/settings") return Promise.resolve(json({ blinding: engine.blinding, mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" }));
  if (path === "/queue") {
    const view = parsed.searchParams.get("view");
    const items = studies()
      .map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", has_proposal: engine.proposals.has(s.study_id), decided: head(s.study_id) !== null, flags: s.abstract ? [] : ["title_only"] }))
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
      json({ ...s, year: 2024, venue: null, doi: null, highlights: [], criteria: engine.criteria ?? CRITERIA, binding: BINDING, my_decision: head(s.study_id), history: engine.events.filter((e) => e.study_id === s.study_id) }),
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
  vi.stubGlobal("fetch", vi.fn(fakeFetch));
});

afterEach(() => vi.unstubAllGlobals());

const proposalReads = () => engine.log.filter((l) => l.path.endsWith("/proposal"));
const postedEvents = () => engine.log.filter((l) => l.path === "/decisions/events").flatMap((l) => (l.body as { events: DecisionEvent[] }).events);

async function ready() {
  render(<TriagePage locale="en" />);
  await screen.findByText("Drone weed mapping", { selector: "p bdi" });
}

function answerAll() {
  for (const group of document.querySelectorAll('[role="group"][aria-label]')) {
    const yes = within(group as HTMLElement).queryByRole("button", { name: "Yes" });
    if (yes) fireEvent.click(yes);
  }
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
    expect(postedEvents()[0]).toMatchObject({ method: "HUMAN", outcome: "INCLUDE", criteria: [{ id: "INC-01", answer: "yes" }, { id: "EXC-01", answer: "yes" }] });
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
    fireEvent.click(screen.getByRole("button", { name: /^Exclude/ }));
    fireEvent.click(screen.getByRole("button", { name: "1. EXC-01" }));
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
  it("picks reason chip 4 by keyboard and confirms with Enter", async () => {
    engine.criteria = [
      { id: "INC-01", text: "UAV imagery", kind: "inclusion" },
      { id: "EXC-01", text: "a", kind: "exclusion" },
      { id: "EXC-02", text: "b", kind: "exclusion" },
      { id: "EXC-03", text: "c", kind: "exclusion" },
    ];
    await ready();
    answerAll();
    await act(async () => {
      fireEvent.keyDown(window, { key: "e" });
    });
    await act(async () => {
      fireEvent.keyDown(window, { key: "4" });
    });
    expect(screen.getByRole("button", { name: "4. FAILS-INC-01" })).toHaveAttribute("aria-pressed", "true");
    await act(async () => {
      fireEvent.keyDown(window, { key: "Enter" });
    });
    await waitFor(() => expect(postedEvents()).toHaveLength(1));
    expect(postedEvents()[0]).toMatchObject({ outcome: "EXCLUDE", reason_code: "FAILS-INC-01" });
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
