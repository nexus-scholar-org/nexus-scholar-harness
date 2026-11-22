import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TriagePage } from "@/components/triage-page";
import type { CriteriaAmendment, DecisionEvent, StoredEvent } from "@/lib/screening-v1";

/**
 * Triage in the pilot view and for records shown again after a criteria revision (spec 13,
 * M11b part C), against a small fake engine. Pilot decisions go to the pilot route, never to
 * the main intake; a record shown again is decided again by superseding the decision shown.
 */

const BINDING = { protocol_fingerprint: "sha256:" + "4".repeat(64), batch_id: "batch-1", batch_sha256: "sha256:" + "b".repeat(64), criteria_version: 2 };
const CRITERIA = [
  { id: "INC-01", text: "UAV imagery", kind: "inclusion" as const },
  { id: "EXC-01", text: "Not a crop field", kind: "exclusion" as const },
];
const STUDIES = [
  { study_id: "STU-a", title: "Drone weed mapping", abstract: "drone imagery" },
  { study_id: "STU-b", title: "Second record", abstract: "satellite crops" },
];
const EARLIER: StoredEvent = {
  event_id: "EV-old",
  study_id: "STU-a",
  screener_id: "researcher:local",
  method: "HUMAN",
  outcome: "EXCLUDE",
  reason_code: "EXC-01",
  criteria: [{ id: "EXC-01", answer: "yes" }],
  note: null,
  supersedes: null,
  binding: { ...BINDING, criteria_version: 1 },
  proposal_shown: null,
  decided_at: "2026-11-20T10:00:00Z",
  received_at: "2026-11-20T10:00:00Z",
  token_scope: "desktop",
  changed_after_reveal: false,
  criteria_version: 1,
} as unknown as StoredEvent;
const AMENDMENT: CriteriaAmendment = {
  amendment_id: "AMD-1",
  op: "reword",
  side: "exclusion",
  from: [{ id: "EXC-01", text: "Not a crop field", reason_category: null }],
  to: [{ id: "EXC-01", text: "Not an arable crop field", reason_category: null }],
  reason: "Orchards were read two ways",
  criteria_version_before: 1,
  criteria_version_after: 2,
  pilot_id: "pilot_001",
  decided_at_time: 1,
  shown_again: { INCLUDE: 0, MAYBE: 0, EXCLUDE: 1, total: 1 },
  amended_by: "researcher:local",
  amended_at: "2026-11-21T10:00:00Z",
};

interface Fake {
  log: { method: string; path: string; search: string; body?: Record<string, unknown> }[];
  pilot: Record<string, { pilot_decision_id: string; outcome: string; reason_code: string | null; criteria: unknown[]; criteria_version: number }>;
  pilotOpen: boolean;
  main: StoredEvent[];
  recheck: boolean;
  refuseMain?: string;
}
let fake: Fake;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function mainHead(study: string): StoredEvent | null {
  const mine = fake.main.filter((e) => e.study_id === study);
  const gone = new Set(mine.map((e) => e.supersedes).filter(Boolean));
  return mine.filter((e) => !gone.has(e.event_id)).at(-1) ?? null;
}

function shownAgain(study: string) {
  return fake.recheck && study === "STU-a" && mainHead(study) === null;
}

function fakeFetch(url: string, init?: RequestInit): Promise<Response> {
  const parsed = new URL(url, "http://localhost");
  const path = parsed.pathname.replace(/^\/api\/console\/api\/v1\/screening/, "");
  const method = (init?.method ?? "GET").toUpperCase();
  const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : undefined;
  fake.log.push({ method, path, search: parsed.search, body });
  if (path === "/settings") {
    return Promise.resolve(json({ blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local", advance_on_decide: "next_at_once" }));
  }
  if (path === "/summary") {
    return Promise.resolve(json({
      total: 2, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 2, conflicts: 0,
      lanes: { agent: 0, you: 0, second_screener: "PARKED" }, criteria_version: fake.recheck ? 2 : 1,
      recheck: fake.recheck && shownAgain("STU-a") ? 1 : 0,
      pilot: { pilot_id: "pilot_001", n: 2, decided: Object.keys(fake.pilot).length, open: fake.pilotOpen, closed_at: null, closed_reason: null, pilots: 1, recheck: 0 },
    }));
  }
  if (path === "/criteria") {
    return Promise.resolve(json({ criteria_version: fake.recheck ? 2 : 1, criteria: [], retired: [], amendments: fake.recheck ? [AMENDMENT] : [], can_amend: true, batches_prepared: true, batch_approved: false, handoff_batches: [] }));
  }
  if (path === "/queue") {
    const view = parsed.searchParams.get("view");
    if (view === "pilot") {
      const items = STUDIES.map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", batch_index: 1, has_proposal: false, decided: s.study_id in fake.pilot, flags: [], shown_again: false, pilot_decision: fake.pilot[s.study_id] ?? null }));
      return Promise.resolve(json({ items, next_cursor: null, pilot: { pilot_id: "pilot_001", open: fake.pilotOpen }, checklist_default: "collapsed" }));
    }
    const items = STUDIES.map((s) => ({ study_id: s.study_id, title: s.title, batch_id: "batch-1", batch_index: 1, has_proposal: false, decided: mainHead(s.study_id) !== null, flags: [], shown_again: shownAgain(s.study_id) }))
      .filter((i) => (view === "decided" ? i.decided : !i.decided));
    return Promise.resolve(json({ items, next_cursor: null }));
  }
  const record = path.match(/^\/records\/([^/]+)$/);
  if (record) {
    const s = STUDIES.find((x) => x.study_id === record[1])!;
    return Promise.resolve(json({
      ...s, year: 2024, venue: null, doi: null, batch_index: 1, highlights: [], criteria: CRITERIA, binding: BINDING,
      my_decision: mainHead(s.study_id), history: fake.main.filter((e) => e.study_id === s.study_id), not_reported_policy: "unclear",
      criteria_version: fake.recheck ? 2 : 1, shown_again: shownAgain(s.study_id) ? { decision: EARLIER, criteria_version: 1 } : null,
    }));
  }
  const pilotPost = path.match(/^\/pilot\/([^/]+)\/decisions$/);
  if (pilotPost && method === "POST") {
    const results = (body!.decisions as (DecisionEvent & { supersedes: string | null })[]).map((d) => {
      const id = `PLD-${d.event_id}`;
      fake.pilot[d.study_id] = { pilot_decision_id: id, outcome: d.outcome, reason_code: d.reason_code ?? null, criteria: d.criteria, criteria_version: 1 };
      return { event_id: d.event_id, result: "accepted", pilot_decision_id: id };
    });
    return Promise.resolve(json({ results, pilot: { pilot_id: "pilot_001", n: 2, decided: Object.keys(fake.pilot).length, open: true, closed_at: null, closed_reason: null } }));
  }
  if (path === "/decisions/events" && method === "POST") {
    const results = (body!.events as DecisionEvent[]).map((e) => {
      if (fake.refuseMain) return { event_id: e.event_id, result: "refused", refusal: { code: fake.refuseMain, message: "refused" } };
      fake.main.push({ ...e, received_at: "2026-11-21T11:00:00Z", token_scope: "desktop", changed_after_reveal: false, criteria_version: 2 } as unknown as StoredEvent);
      return { event_id: e.event_id, result: "accepted" };
    });
    return Promise.resolve(json({ results }));
  }
  if (path === "/decisions/conflicts") return Promise.resolve(json({ items: [] }));
  return Promise.resolve(json({ detail: { code: "NOT_FOUND", message: path } }, 404));
}

beforeEach(() => {
  fake = { log: [], pilot: {}, pilotOpen: true, main: [], recheck: false };
  window.sessionStorage.clear();
  vi.stubGlobal("fetch", vi.fn(fakeFetch));
});

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState(null, "", "/");
});

const pilotPosts = () => fake.log.filter((l) => /^\/pilot\/[^/]+\/decisions$/.test(l.path));
const mainPosts = () => fake.log.filter((l) => l.path === "/decisions/events");

async function openPilot() {
  window.history.replaceState(null, "", "/en/screening/triage?view=pilot");
  render(<TriagePage locale="en" />);
  await screen.findByText("Drone weed mapping", { selector: "p bdi" });
}

describe("triage.pilot-mode (spec 13)", () => {
  it("opens the pilot view from ?view=pilot, with the banner, the sentence and the position", async () => {
    await openPilot();
    expect(fake.log.some((l) => l.path === "/queue" && l.search.includes("view=pilot"))).toBe(true);
    const banner = screen.getByRole("region", { name: "Pilot" });
    expect(banner).toHaveTextContent("Pilot · 0 of 2 decided");
    expect(banner).toHaveTextContent("are not counted");
    expect(screen.getByRole("link", { name: "See the result so far" }).getAttribute("href")).toContain("/en/screening/pilot?id=pilot_001");
    expect(screen.getByText("Pilot record 1 of 2")).toBeTruthy();
  });

  it("a decision goes to the pilot route, never to the main intake, and the next record opens", async () => {
    await openPilot();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(pilotPosts()).toHaveLength(1));
    const [sent] = pilotPosts()[0].body!.decisions as Record<string, unknown>[];
    expect(sent).toMatchObject({ study_id: "STU-a", outcome: "INCLUDE", supersedes: null });
    expect(sent).not.toHaveProperty("binding");
    expect(sent).not.toHaveProperty("proposal_shown");
    expect(mainPosts()).toHaveLength(0);
    await screen.findByText("Second record", { selector: "p bdi" });
    expect(screen.getByText("Pilot decision saved. Pilot record 1 of 2.")).toBeTruthy();
  });

  it("a change of mind supersedes your pilot decision, and the main decision is never shown", async () => {
    fake.pilot["STU-a"] = { pilot_decision_id: "PLD-1", outcome: "EXCLUDE", reason_code: "EXC-01", criteria: [], criteria_version: 1 };
    await openPilot();
    const head = await waitFor(() => {
      const el = document.querySelector("[data-pilot-head]");
      if (!el) throw new Error("no pilot head yet");
      return el as HTMLElement;
    });
    expect(head).toHaveTextContent("Your pilot decision:");
    expect(head).toHaveTextContent("Exclude · EXC-01");
    expect(screen.queryByRole("button", { name: /^Undo/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Change my decision" }));
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(pilotPosts()).toHaveLength(1));
    expect((pilotPosts()[0].body!.decisions as Record<string, unknown>[])[0]).toMatchObject({ outcome: "INCLUDE", supersedes: "PLD-1" });
    expect(mainPosts()).toHaveLength(0);
  });

  it("an ended pilot can be read but not changed", async () => {
    fake.pilotOpen = false;
    fake.pilot["STU-a"] = { pilot_decision_id: "PLD-1", outcome: "INCLUDE", reason_code: null, criteria: [], criteria_version: 1 };
    await openPilot();
    await waitFor(() => expect(document.querySelector("[data-pilot-head]")).not.toBeNull());
    expect(screen.queryByRole("button", { name: "Change my decision" })).toBeNull();
  });

  it("once every pilot record is decided, the hand-off leads to the result and the rest", async () => {
    fake.pilot["STU-a"] = { pilot_decision_id: "PLD-1", outcome: "INCLUDE", reason_code: null, criteria: [], criteria_version: 1 };
    fake.pilot["STU-b"] = { pilot_decision_id: "PLD-2", outcome: "EXCLUDE", reason_code: "EXC-01", criteria: [], criteria_version: 1 };
    window.history.replaceState(null, "", "/en/screening/triage?view=pilot");
    render(<TriagePage locale="en" />);
    expect(await screen.findByRole("heading", { name: "The pilot is decided: 2 of 2" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "See the pilot result" }).getAttribute("href")).toContain("/en/screening/pilot?id=pilot_001");
    expect(screen.getByRole("link", { name: "Screen the rest" })).toBeTruthy();
  });
});

describe("triage.shown-again (spec 13)", () => {
  it("names the revision in a banner, tags the record, and shows the earlier decision", async () => {
    fake.recheck = true;
    render(<TriagePage locale="en" />);
    await screen.findByText("Drone weed mapping", { selector: "p bdi" });
    const banner = document.querySelector("[data-recheck-banner]") as HTMLElement;
    expect(banner).toHaveTextContent("1 records are shown again because criteria changed (version 2).");
    expect(banner).toHaveTextContent("EXC-01: “Not a crop field” became “Not an arable crop field”.");
    expect(banner).toHaveTextContent("Reason: Orchards were read two ways");
    const earlier = document.querySelector("[data-earlier-decision]") as HTMLElement;
    expect(earlier).toHaveTextContent("Your decision under the earlier wording (version 1)");
    expect(earlier).toHaveTextContent("Exclude");
    expect(earlier).toHaveTextContent("EXC-01: yes");
    fireEvent.click(screen.getByRole("button", { name: /^Queue/ }));
    expect(screen.getByRole("navigation", { name: "Queue" })).toHaveTextContent("Shown again");
  });

  it("deciding again supersedes the decision shown again, then says what it replaced", async () => {
    fake.recheck = true;
    render(<TriagePage locale="en" />);
    await screen.findByText("Drone weed mapping", { selector: "p bdi" });
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    await waitFor(() => expect(mainPosts()).toHaveLength(1));
    const [sent] = (mainPosts()[0].body as { events: DecisionEvent[] }).events;
    expect(sent).toMatchObject({ study_id: "STU-a", outcome: "INCLUDE", supersedes: "EV-old" });
    expect(pilotPosts()).toHaveLength(0);
  });

  it("a PILOT_OPEN refusal names the engine's reason and links to the pilot", async () => {
    fake.refuseMain = "PILOT_OPEN";
    render(<TriagePage locale="en" />);
    await screen.findByText("Drone weed mapping", { selector: "p bdi" });
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("This record is in your open pilot");
    expect(screen.getByRole("link", { name: "Go to the pilot" }).getAttribute("href")).toContain("view=pilot");
  });

  it("a REASON_CODE_RETIRED refusal reads the record's criteria in force again", async () => {
    fake.refuseMain = "REASON_CODE_RETIRED";
    render(<TriagePage locale="en" />);
    await screen.findByText("Drone weed mapping", { selector: "p bdi" });
    const reads = () => fake.log.filter((l) => l.method === "GET" && l.path === "/records/STU-a").length;
    const before = reads();
    fireEvent.click(screen.getByRole("button", { name: /^Include/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("That reason was replaced");
    await waitFor(() => expect(reads()).toBeGreaterThan(before));
    expect(mainPosts()).toHaveLength(1);
  });

  it("offers the pilot view only while a pilot is open", async () => {
    render(<TriagePage locale="en" />);
    await screen.findByText("Drone weed mapping", { selector: "p bdi" });
    fireEvent.click(screen.getByRole("button", { name: /^Queue/ }));
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    const values = Array.from(select.options).map((o) => o.value);
    expect(values).toContain("pilot");
    expect(values).not.toContain("recheck");
  });
});
