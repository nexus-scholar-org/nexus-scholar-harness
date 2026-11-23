import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ScreeningPilot } from "@/components/screening-pilot";
import type { PilotResult } from "@/lib/screening-v1";

/** The pilot result and its dialogs (spec 13, states C and D; M11b part C) against a fake engine. */

const ROWS = [
  { id: "INC-01", side: "inclusion", text: "UAV imagery of crops", retired: false, exclusions: { count: 0, of: 25 }, checklist_not_reported: null, draft_not_reported: null, read_differently: null },
  { id: "EXC-01", side: "exclusion", text: "Not a crop field", retired: false, exclusions: { count: 20, of: 25 }, checklist_not_reported: null, draft_not_reported: null, read_differently: null },
  { id: "EXC-02", side: "exclusion", text: "Not an image study", retired: false, exclusions: { count: 0, of: 25 }, checklist_not_reported: null, draft_not_reported: null, read_differently: null },
];

function baseResult(over: Partial<PilotResult> = {}): PilotResult {
  return {
    pilot_id: "pilot_001", n: 50, decided: 50, open: false, closed_at: "2026-11-21T10:00:00Z", closed_reason: "complete",
    seed: 1234, drawn_at: "2026-11-21T09:00:00Z", snapshot_id: "SNAP-1", protocol_fingerprint: "sha256:" + "4".repeat(64),
    criteria_version_drawn: 1, criteria_versions_decided: [1], criteria_version: 1, counted: false,
    by_outcome: { INCLUDE: 14, MAYBE: 11, EXCLUDE: 25 },
    criteria: ROWS as PilotResult["criteria"],
    drafts: { records: 0, of: 50 }, checklist: { records: 0, of: 50 },
    observations: [
      { kind: "does_most_work", criteria: ["EXC-01"], counts: { count: 20, of: 25 } },
      { kind: "never_used", form: "weaker", criteria: ["EXC-02"], counts: { exclusions: 0, of: 25 } },
    ],
    not_computed: [
      { kind: "hard_to_judge", needs: ["agent_check", "checklist"] },
      { kind: "fire_together", needs: ["agent_check", "checklist"] },
      { kind: "mirrored_pair", needs: ["agent_check"] },
      { kind: "read_differently", needs: ["agent_check"] },
    ],
    records: Array.from({ length: 30 }, (_, i) => ({
      study_id: `STU-${i}`, title: `Record ${i}`, outcome: i % 2 ? "EXCLUDE" : "INCLUDE", reason_code: i % 2 ? "EXC-01" : null, criteria_version: 1,
    })) as PilotResult["records"],
    previous: null,
    ...over,
  };
}

interface Fake {
  log: { method: string; path: string; body: Record<string, unknown> | null }[];
  result: PilotResult;
  approved: boolean;
  key: boolean;
  consent: boolean;
  lastModel: string | null;
  shownAgain: number;
  refuseAmend?: string;
  handoff?: boolean;
}
let fake: Fake;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

beforeEach(() => {
  fake = { log: [], result: baseResult(), approved: false, key: true, consent: true, lastModel: null, shownAgain: 0 };
  window.history.replaceState(null, "", "/en/screening/pilot?id=pilot_001");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      fake.log.push({ method, path, body });
      if (path === "/summary") {
        return json({ total: 1062, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 1062, conflicts: 0,
          lanes: { agent: 0, you: 0, second_screener: "PARKED" }, protocol_changed: false, criteria_version: 1, recheck: 0,
          pilot: { pilot_id: "pilot_001", n: 50, decided: fake.result.decided, open: fake.result.open, closed_at: null, closed_reason: null, pilots: 1, recheck: 0 } });
      }
      if (path === "/criteria") {
        return json({
          criteria_version: 1,
          criteria: ROWS.map((r) => ({ id: r.id, side: r.side, text: r.text, reason_category: null, since_version: 1 })),
          retired: [], amendments: [], can_amend: !fake.approved && !fake.handoff, batches_prepared: true, batch_approved: fake.approved, handoff_batches: fake.handoff ? [1] : [],
        });
      }
      if (path === "/proposals/setup") {
        return json({
          task: { task_version: "v1", prompt_sha256: "x", model: "claude-opus-5-5", effort: "low" },
          providers: [{ provider: "anthropic", key: fake.key ? "keychain" : "none", consent: fake.consent ? { accepted_at: "x", model: "m", prompt_sha256: "x" } : null }],
          data_flow: "titles and abstracts", active_run: null, latest_run: null,
          last_model: fake.lastModel ? { provider: "anthropic", model: fake.lastModel } : null,
        });
      }
      if (path === "/proposals/runs" && method === "POST") {
        return json({ run_id: null, estimate: { records: 50, tokens: { input_tokens: 1, cache_read_tokens: 0, cache_write_tokens: 0, output_tokens: 1 }, assumptions: { chars_per_token: 4, output_tokens_per_record: 1 }, cost_usd: 0.01, batch: false, prices_as_of: "2026-11-01", priced: true } });
      }
      if (path === "/proposals/calibrations" && method === "POST") return json({ run_id: "RUN-1" });
      if (path === "/proposals/runs/RUN-1") {
        return json({ run_id: "RUN-1", kind: "calibration", state: "completed", code: null, provider: "anthropic", model: "claude-haiku-5-5", effort: "low", records: 50, done: 50, failed: 0, refused: 0, truncated: 0, invalid: 0, check_failures: 0, cost_so_far: 0.01, cost_ceiling_usd: null, started_at: null, finished_at: null,
          calibration: { include_recall: 0.9, ci_low: 0.8, missed_includes: [], missed_includes_count: 2, compared: 25, advisory: true } });
      }
      if (path === "/pilot/pilot_001/result") return json(fake.result);
      if (path === "/pilot/pilot_404/result") return json({ detail: { code: "PILOT_NOT_FOUND", message: "no such pilot" } }, 404);
      if (path === "/pilot/pilot_001/close" && method === "POST") {
        fake.result = { ...fake.result, open: false, closed_reason: "ended" };
        return json({ pilot_id: "pilot_001", n: 50, decided: fake.result.decided, open: false, closed_at: "x", closed_reason: "ended" });
      }
      if (path === "/criteria/amendments" && method === "POST") {
        if (fake.refuseAmend) return json({ detail: { code: fake.refuseAmend, message: "the reason is required" } }, 422);
        const total = fake.shownAgain;
        return json({ recorded: Boolean(body?.confirm), op: body?.op, side: body?.side, new_ids: body?.op === "split" ? ["EXC-03", "EXC-04"] : [], retired_ids: body?.op === "split" ? ["EXC-01"] : [],
          criteria_version_before: 1, criteria_version_after: 2, decided: 0, shown_again: { INCLUDE: total ? 6 : 0, MAYBE: total ? 5 : 0, EXCLUDE: total ? 3 : 0, total }, waiting_after: 0 });
      }
      const record = path.match(/^\/records\/([^/]+)$/);
      if (record) return json({ study_id: record[1], title: "Record", abstract: "An abstract.", year: 2024, venue: null, doi: null, criteria: [], binding: {}, my_decision: null, history: [], highlights: [] });
      return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState(null, "", "/");
});

const posts = (path: string) => fake.log.filter((l) => l.method === "POST" && l.path === path);

async function ready() {
  render(<ScreeningPilot locale="en" />);
  // The loading frame has its own heading (H-screening-read-performance); the page's comes after it.
  await waitFor(() => expect(document.querySelector("[data-loading-frame]")).toBeNull());
  return screen.findByRole("heading", { level: 1 });
}

describe("pilot.result-counts", () => {
  it("shows the engine's counts with their denominators, one line saying they are not counted", async () => {
    expect(await ready()).toHaveTextContent("The pilot is decided: 50 of 50 records.");
    expect(screen.getByText("These pilot decisions are not counted. The records come back in the main screening.")).toBeTruthy();
    const include = document.querySelector('[data-count="INCLUDE"]') as HTMLElement;
    expect(include).toHaveTextContent("Include");
    expect(include).toHaveTextContent("14");
    expect(include).toHaveTextContent("of 50");
    expect(document.querySelector('[data-criterion="EXC-01"] [data-cell="exclusions"]')).toHaveTextContent("20 of 25 exclusions");
    expect(screen.getByText("Counts from 50 records. A criterion that decided nothing here may still matter in the full corpus.")).toBeTruthy();
  });

  it("renders no checklist or agent column without answers or an agent check", async () => {
    await ready();
    const headers = screen.getAllByRole("columnheader").map((h) => h.textContent);
    expect(headers.some((h) => h?.includes("Reason for exclusions"))).toBe(true);
    expect(headers.some((h) => h?.includes("Your checklist"))).toBe(false);
    expect(document.querySelector("[data-draft-column]")).toBeNull();
  });

  it("with an agent check and no answers, the agent columns are draft-styled and say what they compare with", async () => {
    fake.result = baseResult({
      drafts: { records: 50, of: 50 },
      criteria: ROWS.map((r) => ({ ...r, draft_not_reported: { count: 9, of: 40 }, read_differently: { count: 6, of: 38, source: "implied" } })) as PilotResult["criteria"],
      not_computed: [],
    });
    await ready();
    const draft = document.querySelectorAll("[data-draft-column]");
    expect(draft).toHaveLength(2);
    expect(draft[0]).toHaveTextContent("Agent draft · not a decision");
    expect(draft[1]).toHaveTextContent("against your decisions, not answers per criterion");
    expect(document.querySelector('[data-criterion="EXC-01"] [data-cell="read-differently"]')).toHaveTextContent("6 of 38");
  });

  it("an open pilot reads its denominators as decided so far, and leads to Continue the pilot", async () => {
    fake.result = baseResult({ open: true, decided: 12, closed_at: null, closed_reason: null });
    expect(await ready()).toHaveTextContent("Pilot in progress: 12 of 50 decided.");
    expect(document.querySelector('[data-count="INCLUDE"]')).toHaveTextContent("decided so far");
    const go = screen.getByRole("link", { name: "Continue the pilot" });
    expect(go.getAttribute("data-variant")).toBe("primary");
    expect(go.getAttribute("href")).toContain("view=pilot");
  });
});

describe("pilot.result-not-computed and observations", () => {
  it("names the four readings that need answers, with the estimate, and the mirror Details", async () => {
    await ready();
    const line = document.querySelector("[data-not-computed]") as HTMLElement;
    expect(await within(line).findByText(/about \$0\.01/)).toBeTruthy();
    expect(line).toHaveTextContent("Four readings need answers per criterion: hard to judge, fire together, mirrored pair, read differently.");
    expect(line).toHaveTextContent("A mirror of meaning");
    expect(within(line).getByRole("button", { name: "Let the agent check these 50 records" })).toBeTruthy();
  });

  it("each observation names its criterion and counts, with one Revise per id and no proposed wording", async () => {
    await ready();
    const cards = document.querySelectorAll("[data-observation]");
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveTextContent("EXC-01 decided 20 of the 25 exclusions.");
    expect(cards[1]).toHaveTextContent("EXC-02 was the reason for none of the 25 exclusions in this pilot of 50.");
    for (const card of cards) {
      expect(card).toHaveTextContent("A reading of your answers · not an instruction");
      expect(within(card as HTMLElement).getAllByRole("button")).toHaveLength(1);
    }
  });

  it("with no observation, says nothing stood out", async () => {
    fake.result = baseResult({ observations: [] });
    await ready();
    expect(screen.getByText("Nothing stood out in these 50 records.")).toBeTruthy();
  });
});

describe("pilot.records-list", () => {
  it("filters by criterion and outcome, pages by 25, and opens a record read-only with its pilot decision", async () => {
    await ready();
    const list = screen.getByRole("region", { name: "Records" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(25);
    fireEvent.change(within(list).getByLabelText("Outcome"), { target: { value: "EXCLUDE" } });
    expect(within(list).getAllByRole("listitem")).toHaveLength(15);
    expect(within(list).queryByLabelText(/agent/i)).toBeNull();
    fireEvent.click(within(list).getByRole("button", { name: "Record 1" }));
    const view = await screen.findByRole("dialog", { name: "Record 1" });
    expect(within(view).getByText("Your pilot decision, under criteria version 1. Not counted.")).toBeTruthy();
    expect(await within(view).findByText("An abstract.")).toBeTruthy();
    expect(within(view).queryByRole("button", { name: /^Include|^Exclude/ })).toBeNull();
  });
});

describe("pilot.end", () => {
  it("asks first, writes nothing on Not now, and after ending reads Pilot ended without Continue", async () => {
    fake.result = baseResult({ open: true, decided: 38, closed_at: null, closed_reason: null });
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "End the pilot" }));
    const dialog = screen.getByRole("alertdialog", { name: "End the pilot?" });
    expect(dialog).toHaveTextContent("You decided 38 of 50.");
    fireEvent.click(within(dialog).getByRole("button", { name: "Not now" }));
    expect(posts("/pilot/pilot_001/close")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "End the pilot" }));
    fireEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: "End the pilot" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Pilot ended: 38 of 50 decided." })).toBeTruthy();
    expect(posts("/pilot/pilot_001/close")).toHaveLength(1);
    expect(screen.queryByRole("link", { name: "Continue the pilot" })).toBeNull();
    expect(screen.getByRole("link", { name: "Screen the rest" }).getAttribute("data-variant")).toBe("primary");
  });
});

describe("criteria.revise-dialog", () => {
  it("needs an operation and a reason; the dry call writes nothing; the confirmation names what changes", async () => {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Revise EXC-01" }));
    const dialog = screen.getByRole("dialog", { name: "Revise a criterion" });
    const radios = within(dialog).getAllByRole("radio");
    expect(radios).toHaveLength(6);
    expect(radios.every((r) => !(r as HTMLInputElement).checked)).toBe(true);
    const check = within(dialog).getByRole("button", { name: "Check what this changes" });
    expect(check).toBeDisabled();
    fireEvent.click(within(dialog).getByRole("radio", { name: "Reword · same test, clearer words" }));
    expect((within(dialog).getByLabelText("New wording") as HTMLTextAreaElement).value).toBe("Not a crop field");
    fireEvent.change(within(dialog).getByLabelText("New wording"), { target: { value: "Not an arable crop field" } });
    expect(check).toBeDisabled();
    fireEvent.change(within(dialog).getByLabelText("Why are you making this change? One sentence."), { target: { value: "Orchards were read two ways" } });
    expect(within(dialog).getByText("27 of 500 characters")).toBeTruthy();
    fireEvent.click(check);
    const confirm = await screen.findByRole("alertdialog", { name: "Record this revision?" });
    expect(posts("/criteria/amendments").map((p) => p.body?.confirm)).toEqual([false]);
    expect(posts("/criteria/amendments")[0].body).toMatchObject({ op: "reword", side: "exclusion", ids: ["EXC-01"], text: "Not an arable crop field", reason: "Orchards were read two ways" });
    expect(confirm).toHaveTextContent("EXC-01 keeps its number. Its wording becomes version 2.");
    expect(confirm).toHaveTextContent("No record will be shown again.");
    expect(confirm).toHaveTextContent("Your pilot decisions are not counted and are not shown again.");
    fireEvent.click(within(confirm).getByRole("button", { name: "Record the revision" }));
    await vi.waitFor(() => expect(posts("/criteria/amendments").map((p) => p.body?.confirm)).toEqual([false, true]));
  });

  it("lists the records shown again by outcome when the dry answer has counted decisions", async () => {
    fake.shownAgain = 14;
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Revise a criterion" }));
    const dialog = screen.getByRole("dialog", { name: "Revise a criterion" });
    fireEvent.click(within(dialog).getByRole("radio", { name: "Split · one criterion into two" }));
    fireEvent.change(within(dialog).getByLabelText("Criterion"), { target: { value: "EXC-01" } });
    fireEvent.change(within(dialog).getByLabelText("New wording 1"), { target: { value: "Not a field" } });
    fireEvent.change(within(dialog).getByLabelText("New wording 2"), { target: { value: "Not a crop" } });
    fireEvent.change(within(dialog).getByLabelText("Why are you making this change? One sentence."), { target: { value: "Two tests in one" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Check what this changes" }));
    const confirm = await screen.findByRole("alertdialog");
    expect(confirm).toHaveTextContent("EXC-01 will be retired. New criteria: EXC-03, EXC-04.");
    expect(confirm).toHaveTextContent("This will show again 14 records you decided: 6 Include, 5 Unclear, 3 Exclude citing EXC-01.");
  });

  it("a refusal keeps the typed text and shows the engine's sentence and code", async () => {
    fake.refuseAmend = "CRITERIA_AMENDMENT_INVALID";
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Revise EXC-02" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("radio", { name: "Remove" }));
    fireEvent.change(within(dialog).getByLabelText("Why are you making this change? One sentence."), { target: { value: "Never used" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Check what this changes" }));
    expect(await within(dialog).findByText(/CRITERIA_AMENDMENT_INVALID/)).toBeTruthy();
    expect((within(dialog).getByLabelText("Why are you making this change? One sentence.") as HTMLTextAreaElement).value).toBe("Never used");
  });
});

describe("pilot.calibration-dialog", () => {
  it("names the model, count and estimate, and always sends the model and the pilot", async () => {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Check the agent on these 50 records" }));
    const dialog = screen.getByRole("dialog", { name: "Check the agent on these 50 records" });
    expect((within(dialog).getByLabelText("Model") as HTMLSelectElement).value).toBe("claude-haiku-5-5");
    expect(dialog).toHaveTextContent("50 records you decided");
    expect(await within(dialog).findByText(/About \$0\.01 for 50 records on claude-haiku-5-5/)).toBeTruthy();
    expect(posts("/proposals/calibrations")).toHaveLength(0);
    const runButton = within(dialog).getByRole("button", { name: /^Run the check/ });
    runButton.focus();
    fireEvent.click(runButton);
    await vi.waitFor(() => expect(posts("/proposals/calibrations")).toHaveLength(1));
    expect(posts("/proposals/calibrations")[0].body).toMatchObject({ pilot_id: "pilot_001", provider: "anthropic", model: "claude-haiku-5-5" });
    expect(await within(dialog).findByText("Missed includes: 2 of 25")).toBeTruthy();
    // Review C round 2: focus stays inside once the run view replaces the form (it moves there in an effect).
    await vi.waitFor(() => expect(dialog.contains(document.activeElement)).toBe(true));
  });

  it("uses the last model of the workspace when there is one", async () => {
    fake.lastModel = "claude-sonnet-5-5";
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Check the agent on these 50 records" }));
    expect((within(screen.getByRole("dialog")).getByLabelText("Model") as HTMLSelectElement).value).toBe("claude-sonnet-5-5");
  });

  it("without consent on file, nothing can be sent", async () => {
    fake.consent = false;
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Check the agent on these 50 records" }));
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(/CONSENT_REQUIRED/)).toBeTruthy();
    expect(within(dialog).getByRole("button", { name: /^Run the check/ })).toBeDisabled();
  });

  it("is not offered without a provider key", async () => {
    fake.key = false;
    await ready();
    expect(screen.queryByRole("button", { name: "Check the agent on these 50 records" })).toBeNull();
  });
});

describe("pilot states", () => {
  it("after an approval the criteria are fixed: no revise, no end, no more pilots", async () => {
    fake.approved = true;
    await ready();
    expect(document.querySelector("[data-fixed]")).toHaveTextContent("A batch is already approved, so the criteria are fixed.");
    expect(screen.queryByRole("button", { name: "Revise a criterion" })).toBeNull();
    expect(screen.queryByRole("button", { name: /^Revise EXC/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Pilot 50 more records/ })).toBeNull();
  });

  it("an unknown pilot shows the engine's not-found card", async () => {
    window.history.replaceState(null, "", "/en/screening/pilot?id=pilot_404");
    render(<ScreeningPilot locale="en" />);
    expect(await screen.findByRole("heading", { level: 1, name: "That pilot does not exist in this workspace" })).toBeTruthy();
  });

  it("a second pilot shows the first pilot's figures beside it, captioned by criteria version", async () => {
    fake.result = baseResult({
      pilot_id: "pilot_002",
      criteria_versions_decided: [2],
      previous: { pilot_id: "pilot_001", n: 50, decided: 50, by_outcome: { INCLUDE: 10, MAYBE: 15, EXCLUDE: 25 }, criteria: ROWS as PilotResult["criteria"], criteria_versions_decided: [1] },
    });
    window.history.replaceState(null, "", "/en/screening/pilot?id=pilot_001");
    await ready();
    expect(screen.getByText("Criteria version 1 and criteria version 2")).toBeTruthy();
    const headers = screen.getAllByRole("columnheader").map((h) => h.textContent ?? "");
    expect(headers.filter((h) => h.startsWith("Reason for exclusions"))).toEqual(["Reason for exclusions · Pilot 1", "Reason for exclusions · Pilot 2"]);
    expect(document.querySelector('[data-count="MAYBE"] [data-previous]')).toHaveTextContent("Pilot 1: 15 of 50");
  });
});

describe("review C round 1", () => {
  const amend = () => fake.log.filter((l) => l.method === "POST" && l.path === "/criteria/amendments").map((l) => l.body!);
  async function revise(op: string, fill: (dialog: HTMLElement) => void) {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "Revise a criterion" }));
    const dialog = screen.getByRole("dialog", { name: "Revise a criterion" });
    fireEvent.click(within(dialog).getByRole("radio", { name: op }));
    fill(dialog);
    fireEvent.change(within(dialog).getByLabelText("Why are you making this change? One sentence."), { target: { value: "A reason" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Check what this changes" }));
    await screen.findByRole("alertdialog", { name: "Record this revision?" });
    return amend()[0];
  }

  it("finding 8: each operation sends its own body; only a reason-category change sends reason_category", async () => {
    const reword = await revise("Reword · same test, clearer words", (d) => {
      fireEvent.change(within(d).getByLabelText("Criterion"), { target: { value: "EXC-01" } });
      fireEvent.change(within(d).getByLabelText("New wording"), { target: { value: "Not an arable field" } });
    });
    expect(reword).toEqual({ op: "reword", side: "exclusion", ids: ["EXC-01"], text: "Not an arable field", reason: "A reason", confirm: false });
  });

  it("finding 8: split sends two texts and no reason_category", async () => {
    const body = await revise("Split · one criterion into two", (d) => {
      fireEvent.change(within(d).getByLabelText("Criterion"), { target: { value: "EXC-01" } });
      fireEvent.change(within(d).getByLabelText("New wording 1"), { target: { value: "Not a field" } });
      fireEvent.change(within(d).getByLabelText("New wording 2"), { target: { value: "Not a crop" } });
    });
    expect(body).toEqual({ op: "split", side: "exclusion", ids: ["EXC-01"], text: ["Not a field", "Not a crop"], reason: "A reason", confirm: false });
  });

  it("finding 8: merge sends both ids of one side and one text", async () => {
    const body = await revise("Merge · two criteria into one", (d) => {
      fireEvent.change(within(d).getByLabelText("Criterion 1"), { target: { value: "EXC-01" } });
      fireEvent.change(within(d).getByLabelText("Criterion 2"), { target: { value: "EXC-02" } });
      fireEvent.change(within(d).getByLabelText("New wording"), { target: { value: "Not a crop image study" } });
    });
    expect(body).toEqual({ op: "merge", side: "exclusion", ids: ["EXC-01", "EXC-02"], text: "Not a crop image study", reason: "A reason", confirm: false });
  });

  it("finding 8: remove sends the id only; add sends the side and the text, no id", async () => {
    const removed = await revise("Remove", (d) => fireEvent.change(within(d).getByLabelText("Criterion"), { target: { value: "EXC-02" } }));
    expect(removed).toEqual({ op: "remove", side: "exclusion", ids: ["EXC-02"], reason: "A reason", confirm: false });
  });

  it("finding 8: add sends the side and the text, no id", async () => {
    const added = await revise("Add", (d) => {
      fireEvent.click(within(d).getByRole("radio", { name: "Inclusion" }));
      fireEvent.change(within(d).getByLabelText("New wording"), { target: { value: "Peer reviewed" } });
    });
    expect(added).toEqual({ op: "add", side: "inclusion", ids: [], text: "Peer reviewed", reason: "A reason", confirm: false });
  });

  it("finding 8: a reason-category change sends the category and no text", async () => {
    const body = await revise("Change the reason category · wording stays", (d) => {
      fireEvent.change(within(d).getByLabelText("Criterion"), { target: { value: "EXC-01" } });
      fireEvent.change(within(d).getByLabelText("Rejection reason text"), { target: { value: "Not a field" } });
    });
    expect(body).toEqual({ op: "reason_category", side: "exclusion", ids: ["EXC-01"], reason_category: "Not a field", reason: "A reason", confirm: false });
  });

  it("finding 3: an addition that shows records again cites no criterion", async () => {
    fake.shownAgain = 14;
    await revise("Add", (d) => {
      fireEvent.click(within(d).getByRole("radio", { name: "Exclusion" }));
      fireEvent.change(within(d).getByLabelText("New wording"), { target: { value: "Not peer reviewed" } });
    });
    const confirm = screen.getByRole("alertdialog");
    expect(confirm).toHaveTextContent("This will show again 14 records you decided: 6 Include, 5 Unclear.");
    expect(confirm.textContent).not.toMatch(/citing/);
  });

  it("finding 4: batches decided through the hand-off say so, not that a batch was approved", async () => {
    fake.handoff = true;
    await ready();
    const note = document.querySelector("[data-fixed]") as HTMLElement;
    expect(note.getAttribute("data-fixed")).toBe("handoff");
    expect(note).toHaveTextContent("decisions made through the file hand-off");
    expect(note.textContent).not.toMatch(/already approved/);
    expect(screen.queryByRole("button", { name: "Revise a criterion" })).toBeNull();
  });

  it("finding 2: a dialog takes focus when it opens, keeps Tab inside, and gives focus back on close", async () => {
    await ready();
    const opener = screen.getByRole("button", { name: "Check the agent on these 50 records" });
    opener.focus();
    fireEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: "Check the agent on these 50 records" });
    await vi.waitFor(() => expect(dialog.contains(document.activeElement)).toBe(true));
    const buttons = within(dialog).getAllByRole("button");
    const last = buttons[buttons.length - 1];
    last.focus();
    fireEvent.keyDown(last, { key: "Tab" });
    expect(dialog.contains(document.activeElement)).toBe(true);
    expect(document.activeElement).not.toBe(last);
    fireEvent.keyDown(dialog, { key: "Escape" });
    await vi.waitFor(() => expect(document.activeElement).toBe(opener));
  });

  it("finding 2: the revise dialog keeps focus inside when it moves to its confirmation and back", async () => {
    await revise("Remove", (d) => fireEvent.change(within(d).getByLabelText("Criterion"), { target: { value: "EXC-02" } }));
    const confirm = screen.getByRole("alertdialog");
    await vi.waitFor(() => expect(confirm.contains(document.activeElement)).toBe(true));
    fireEvent.click(within(confirm).getByRole("button", { name: "Back" }));
    const form = screen.getByRole("dialog", { name: "Revise a criterion" });
    await vi.waitFor(() => expect(form.contains(document.activeElement)).toBe(true));
  });
});
