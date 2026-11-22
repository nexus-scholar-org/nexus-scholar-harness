import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PREPARE_COPY, ScreeningPrepare } from "@/components/screening-prepare";
import { SUPPORTED_LOCALES } from "@/i18n";

/** Prepare (spec 02) in jsdom; the snapshot refusal is the engine's recorded fixture. */

const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;
const fixture = (name: string) => JSON.parse(readFileSync(`${FIXTURES}${name}.json`, "utf-8")).response;

function engine(job?: { state: string; error?: string | null }, settings: Record<string, unknown> = {}, batched = false) {
  let polls = 0;
  const log: { method: string; path: string; body: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? JSON.parse(String(init.body)) : null;
      log.push({ method, path, body });
      const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "content-type": "application/json" } });
      if (path === "/settings" && method === "GET") return json({ ...fixture("settings_default").body, ...settings });
      if (path === "/settings" && method === "PUT") return json({ ...fixture("settings_default").body, ...settings, ...body });
      if (path === "/method/amendments" && method === "POST") {
        // H-screening-drafts: the engine records the amendment and answers with the settings in force.
        const field = body.field as "blinding" | "not_reported";
        const amendment = { amendment_id: "AMD-1", field, from: field === "blinding" ? "reveal_after_decision" : "unclear", to: body.value, amended_by: "researcher:local", amended_at: "2026-11-20T10:00:00Z", protocol_fingerprint: "sha256:x", note: null };
        const next = { ...fixture("settings_default").body, ...settings, ...(field === "blinding" ? { blinding: body.value } : { not_reported_policy: body.value, not_reported_source: "amendment" }), method_amendments: [amendment] };
        return json({ amendment, settings: next });
      }
      if (path === "/ui/batches") {
        const entry = { batch_index: 1, batch_file: "batch_001.json", items: 20, decisions_file: null, decisions_count: null, collected: false, coverage: "INCOMPLETE", unresolved_rows: [] };
        return json({ shape: "ui07.screening-batches-v1", run_id: null, count: batched ? 1 : 0, batches: batched ? [entry] : [], missing: [] });
      }
      if (path === "/summary") {
        return json({ total: 20, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 20, conflicts: 0, lanes: { agent: 0, you: 0, second_screener: "PARKED" }, protocol_changed: false, criteria_version: 1, recheck: 0, pilot: null });
      }
      if (path === "/criteria") {
        return json({ criteria_version: 1, criteria: [], retired: [], amendments: [], can_amend: true, batches_prepared: true, batch_approved: false, handoff_batches: [] });
      }
      if (path === "/prepare") {
        if (job) return json({ job_id: "job_1" });
        const refused = fixture("prepare_snapshot_not_accepted");
        return json(refused.body, refused.status);
      }
      if (path === "/api/console/api/v1/jobs/job_1" && job) {
        polls += 1;
        const state = polls < 2 ? "running" : job.state;
        return json({ job: { job_id: "job_1", action_id: "screen_prepare", state, exit_code: state === "success" ? 0 : 1, error: job.error ?? null } });
      }
      return json({ detail: { code: "NOT_FOUND" } }, 404);
    }),
  );
  return log;
}

afterEach(() => vi.unstubAllGlobals());

describe("prepare.snapshot-missing", () => {
  it("confirms before preparing, then shows the refusal with the Import link and the terminal step", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    expect(log.some((l) => l.path === "/prepare")).toBe(false);
    expect(screen.getByText("Prepare batches of 20 records?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    await screen.findByText("SNAPSHOT_NOT_ACCEPTED");
    expect(screen.getByRole("link", { name: "Import the corpus" })).toHaveAttribute("href", "/en/screening/import");
    expect(screen.getByText("nexus-scholar accept-corpus --ris Scopus=<file>.ris")).toBeInTheDocument();
    expect(log.find((l) => l.path === "/prepare")?.body).toEqual({ batch_size: 20 });
  });
});

describe("prepare.job-followed", () => {
  it("says when the prepare job failed instead of waiting forever (golden run)", async () => {
    engine({ state: "failed", error: "No module named scholar_harness" });
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    const alert = await screen.findByRole("alert", {}, { timeout: 4000 });
    expect(alert).toHaveTextContent("Preparing failed (job job_1). Nothing was prepared. The engine said: No module named scholar_harness");
  });

  it("gives the exit code when the job failed without an error message", async () => {
    // A non-zero exit sets no `error` in the runner; only a timeout or exception does.
    engine({ state: "failed", error: null });
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    expect(await screen.findByRole("alert", {}, { timeout: 4000 })).toHaveTextContent("The engine said: exit code 1");
  });

  it("says the batches are prepared and re-reads them when the job succeeds", async () => {
    const log = engine({ state: "success" });
    render(<ScreeningPrepare locale="en" />);
    await screen.findByText("No batches yet.");
    fireEvent.click(screen.getByRole("button", { name: "Prepare batches" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare now" }));
    expect(await screen.findByText("Batches prepared (job job_1).", {}, { timeout: 4000 })).toBeInTheDocument();
    expect(log.filter((l) => l.path === "/ui/batches").length).toBeGreaterThanOrEqual(2);
  });
});

describe("prepare.rule-table-readonly", () => {
  it("describes the engine's rules in order and offers no control to change them", async () => {
    engine();
    render(<ScreeningPrepare locale="en" />);
    const rules = await screen.findByRole("heading", { name: "How an agent draft's outcome is derived" });
    const section = rules.closest("section")!;
    expect(section.querySelectorAll("input, select, button, textarea")).toHaveLength(0);
    const items = [...section.querySelectorAll("li")].map((li) => li.textContent);
    expect(items[0]).toMatch(/^First, Unclear/);
  });
});

describe("prepare.ai-agreed-needs-confirm", () => {
  it("keeps Save disabled until the opt-in is confirmed with a sample size, and sends the confirmation", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    fireEvent.click(await screen.findByLabelText(/AI-agreed exclusion/));
    const save = screen.getByRole("button", { name: "Save settings" });
    expect(save).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Sample-audit size/), { target: { value: "60" } });
    expect(save).toBeDisabled();
    fireEvent.click(screen.getByLabelText(/I understand this skips records/));
    expect(save).toBeEnabled();
    fireEvent.click(save);
    await screen.findByText("Settings saved");
    expect(log.find((l) => l.method === "PUT")?.body).toEqual({
      blinding: "reveal_after_decision",
      mode: "ai_agreed_exclusion",
      sample_audit_size: 60,
      confirm_ai_agreed_exclusion: true,
    });
  });
});

describe("prepare copy", () => {
  it("has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PREPARE_COPY[locale]).sort()).toEqual(Object.keys(PREPARE_COPY.en).sort());
      for (const [key, value] of Object.entries(PREPARE_COPY[locale])) {
        expect(holes(value), `${locale}/${key}`).toEqual(holes(PREPARE_COPY.en[key as keyof typeof PREPARE_COPY.en]));
      }
    }
  });
});

describe("prepare.advance-on-decide (M6-beta)", () => {
  it("offers the two values, default first, and sends the setting only when it changes", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    const draftThenNext = await screen.findByLabelText("Show the draft, then N (default)");
    expect(draftThenNext).toBeChecked();
    fireEvent.click(screen.getByLabelText(/Move on at once/));
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
    await screen.findByText("Settings saved");
    expect(log.find((l) => l.method === "PUT")?.body).toMatchObject({ advance_on_decide: "next_at_once" });
  });
});

describe("prepare.advance-setting (review fixes)", () => {
  it("is disabled, with a note, while drafts are shown beside the record", async () => {
    engine();
    render(<ScreeningPrepare locale="en" />);
    fireEvent.click(await screen.findByLabelText("Show beside the record"));
    expect(screen.getByLabelText(/Move on at once/)).toBeDisabled();
    expect(screen.getByText("Drafts are already beside the record, so the next record always opens at once.")).toBeInTheDocument();
  });

  it("sends no advance_on_decide when saving without changing it", async () => {
    const log = engine();
    render(<ScreeningPrepare locale="en" />);
    fireEvent.click(await screen.findByLabelText("Show beside the record"));
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
    await screen.findByText("Settings saved");
    expect(log.find((l) => l.method === "PUT")?.body).not.toHaveProperty("advance_on_decide");
  });
});


// M7-method (spec 02 amendment 2026-11-08): blinding set by the protocol, and
// the rule table follows the protocol's not-reported policy.
describe("prepare.blinding-from-protocol", () => {
  // H-screening-drafts (acceptance run 2026-11-20): "Show beside the record" did
  // nothing on a workspace whose protocol sets blinding. Now it is a recorded
  // amendment, confirmed first; it never goes through PUT /settings.
  it("changes blinding set by the protocol only through a confirmed, recorded amendment", async () => {
    const log = engine(undefined, { blinding: "reveal_after_decision", blinding_source: "protocol" });
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("The agent's draft")).closest("fieldset")!;
    expect(screen.getByText("Set by your protocol. A change is recorded as an amendment.")).toBeInTheDocument();
    const radios = [...group.querySelectorAll('input[type="radio"]')] as HTMLInputElement[];
    expect(radios.map((r) => r.checked)).toEqual([true, false]);
    fireEvent.click(radios[1]);
    const confirm = await screen.findByRole("alertdialog", { name: /Amend the protocol's method/ });
    expect(confirm).toHaveTextContent("The agent's draft: from “Reveal after my decision (recommended)” to “Show beside the record”.");
    expect(confirm).toHaveTextContent("The signed protocol, the corpus and your decisions are not changed.");
    expect(log.some((l) => l.path === "/method/amendments")).toBe(false); // nothing before the confirmation
    fireEvent.click(screen.getByRole("button", { name: "Record the amendment" }));
    await screen.findByText(/Amended on 2026-11-20 by researcher:local: The agent's draft/);
    expect(log.find((l) => l.path === "/method/amendments")?.body).toEqual({ field: "blinding", value: "show", confirm: true });
    expect(radios[1].checked).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: /^Save/ }));
    await screen.findByText(/saved/i);
    expect(log.find((l) => l.method === "PUT" && l.path === "/settings")?.body).not.toHaveProperty("blinding");
  });

  it("cancelling the amendment keeps the protocol's value and sends nothing", async () => {
    const log = engine(undefined, { blinding: "reveal_after_decision", blinding_source: "protocol" });
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("The agent's draft")).closest("fieldset")!;
    const radios = [...group.querySelectorAll('input[type="radio"]')] as HTMLInputElement[];
    fireEvent.click(radios[1]);
    fireEvent.click(await screen.findByRole("button", { name: "Keep the protocol's value" }));
    expect(radios.map((r) => r.checked)).toEqual([true, false]);
    expect(log.some((l) => l.path === "/method/amendments")).toBe(false);
  });

  it("stays a plain setting when the protocol does not set blinding", async () => {
    engine(undefined, { blinding_source: "settings" });
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("The agent's draft")).closest("fieldset")!;
    expect(screen.queryByText(/Set by your protocol/)).toBeNull();
    fireEvent.click(group.querySelectorAll('input[type="radio"]')[1]);
    expect(screen.queryByRole("alertdialog")).toBeNull();
  });
});

describe("prepare.not-reported-amendment (H-screening-drafts)", () => {
  it("offers the three not-reported rules and changes the rule through a confirmed amendment", async () => {
    const log = engine(undefined, { not_reported_policy: "unclear", not_reported_source: "protocol" });
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("A criterion the title and abstract do not report")).closest("fieldset")!;
    const labels = [...group.querySelectorAll("label")].map((l) => l.textContent);
    expect(labels).toEqual([
      "It sends the record to Unclear (full text), even beside a decisive answer",
      "A decisive answer first: an exclusion met or an inclusion not met excludes; otherwise Unclear",
      "An unreported inclusion criterion excludes the record",
    ]);
    fireEvent.click(group.querySelectorAll('input[type="radio"]')[1]);
    const confirm = await screen.findByRole("alertdialog", { name: /Amend the protocol's method/ });
    expect(confirm).toHaveTextContent("Existing agent drafts keep their answers and are shown and counted under the new rule");
    fireEvent.click(screen.getByRole("button", { name: "Record the amendment" }));
    await screen.findByText(/Amended on 2026-11-20 by researcher:local: A criterion the title and abstract do not report/);
    expect(log.find((l) => l.path === "/method/amendments")?.body).toEqual({ field: "not_reported", value: "decisive_first", confirm: true });
    // The rule table follows the amended policy.
    const rules = screen.getByRole("heading", { name: "How an agent draft's outcome is derived" }).closest("section")!;
    expect(rules.querySelectorAll("li")[0]).toHaveTextContent("First, Unclear → full text: a check on the draft failed or the agent could not decide.");
  });

  it("says why it refused when the engine refuses the amendment", async () => {
    engine(undefined, { not_reported_policy: "unclear" });
    const real = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if (String(url).includes("/method/amendments")) {
        return new Response(JSON.stringify({ detail: { code: "METHOD_AMENDMENT_INVALID", message: "not_reported is already decisive_first" } }), { status: 422 });
      }
      return real(url, init);
    }));
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("A criterion the title and abstract do not report")).closest("fieldset")!;
    fireEvent.click(group.querySelectorAll('input[type="radio"]')[1]);
    fireEvent.click(await screen.findByRole("button", { name: "Record the amendment" }));
    expect(await screen.findByText("not_reported is already decisive_first")).toBeInTheDocument();
  });
});

describe("prepare.not-reported-default (M11b placeholder follow-up, decision item 8)", () => {
  const DEFAULT_LINE = "The rule shown is the harness default: the protocol does not set it and nobody has chosen it.";

  it("says the rule shown is the default, not a choice, when the engine's source is defaults", async () => {
    engine(undefined, { not_reported_policy: "unclear", not_reported_source: "defaults" });
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("A criterion the title and abstract do not report")).closest("fieldset")!;
    const line = screen.getByText(DEFAULT_LINE);
    expect(group).toContainElement(line);
    // Read with the group, as the note is; no new control.
    expect(group.getAttribute("aria-describedby")?.split(" ")).toContain(line.id);
    expect(group.querySelectorAll("input, button, select")).toHaveLength(3);
  });

  it("says nothing when the protocol sets the rule or an amendment changed it", async () => {
    for (const source of ["protocol", "amendment"]) {
      engine(undefined, { not_reported_policy: "unclear", not_reported_source: source });
      const { unmount } = render(<ScreeningPrepare locale="en" />);
      await screen.findByText("A criterion the title and abstract do not report");
      expect(screen.queryByText(DEFAULT_LINE)).toBeNull();
      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("drops the line once the researcher records an amendment", async () => {
    engine(undefined, { not_reported_policy: "unclear", not_reported_source: "defaults" });
    render(<ScreeningPrepare locale="en" />);
    const group = (await screen.findByText("A criterion the title and abstract do not report")).closest("fieldset")!;
    expect(screen.getByText(DEFAULT_LINE)).toBeInTheDocument();
    fireEvent.click(group.querySelectorAll('input[type="radio"]')[2]);
    await screen.findByRole("alertdialog", { name: /Amend the protocol's method/ });
    fireEvent.click(screen.getByRole("button", { name: "Record the amendment" }));
    await screen.findByText(/Amended on 2026-11-20/);
    expect(screen.queryByText(DEFAULT_LINE)).toBeNull();
  });

  it("is written in French and Arabic", async () => {
    for (const locale of ["fr", "ar"] as const) {
      engine(undefined, { not_reported_source: "defaults" });
      const { unmount } = render(<ScreeningPrepare locale={locale} />);
      expect(await screen.findByText(PREPARE_COPY[locale].notReportedDefault)).toBeInTheDocument();
      expect(PREPARE_COPY[locale].notReportedDefault).not.toBe(PREPARE_COPY.en.notReportedDefault);
      unmount();
      vi.unstubAllGlobals();
    }
  });
});

describe("prepare.rule-table-policy", () => {
  it("describes the decisive-first table (H-screening-drafts)", async () => {
    engine(undefined, { not_reported_policy: "decisive_first" });
    render(<ScreeningPrepare locale="en" />);
    const rules = await screen.findByRole("heading", { name: "How an agent draft's outcome is derived" });
    const items = [...rules.closest("section")!.querySelectorAll("li")].map((li) => li.textContent);
    expect(items).toEqual([
      "First, Unclear → full text: a check on the draft failed or the agent could not decide.",
      "Then exclude: any exclusion criterion answered yes, or any inclusion criterion answered no, even when other criteria are not reported.",
      "Then Unclear → full text: any criterion not reported. Otherwise include: every inclusion yes and every exclusion no.",
    ]);
  });

  it("describes the exclude policy's table when the protocol sets it", async () => {
    engine(undefined, { not_reported_policy: "exclude" });
    render(<ScreeningPrepare locale="en" />);
    const rules = await screen.findByRole("heading", { name: "How an agent draft's outcome is derived" });
    const items = [...rules.closest("section")!.querySelectorAll("li")].map((li) => li.textContent);
    expect(items).toEqual([
      "First, Unclear → full text: a check on the draft failed or the agent could not decide.",
      "Otherwise exclude: any exclusion criterion answered yes, any inclusion criterion answered no, or any inclusion criterion not reported.",
      "Otherwise include: every inclusion yes and no exclusion yes.",
    ]);
  });
});

describe("prepare with batches (M11b part C, review round 1 finding 7)", () => {
  it("has one brand action: the pilot card's draw; Prepare again is secondary", async () => {
    engine(undefined, {}, true);
    render(<ScreeningPrepare locale="en" />);
    await screen.findByRole("button", { name: "Draw a pilot of 50" });
    const brand = [...document.querySelectorAll('[data-variant="primary"]')].map((e) => e.textContent?.trim());
    expect(brand).toEqual(["Draw a pilot of 50"]);
  });
});
