import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryRecall } from "@/components/discovery-recall";
import { InceptionCriteria } from "@/components/inception-criteria";
import { InceptionReview } from "@/components/inception-review";
import { InceptionScope } from "@/components/inception-scope";
import { CHECK_IDS, CHECKS_COPY } from "@/lib/checks-copy";
import { checkRow, type CheckIn } from "./fixtures/checks-engine";
import { completeDraft, proofId, SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";
import { setUp as setUpDiscovery } from "./discovery-helpers";

/**
 * `docs/ux/shared/final/02-checks.md` "Acceptance tests / Vitest" (M10b B3): the
 * checks panel on a step, the Review readiness list and the discovery panel. The
 * fake serves the rows; the panel renders them and computes none.
 */

afterEach(() => vi.unstubAllGlobals());

const CHECKS = `/api/v1/inception/drafts/${SESSION}/checks`;
const decided = (extra: Record<string, unknown> = {}) => completeDraft({ criteria_decisions: { [proofId()]: true }, ...extra });

const blocker: CheckIn = { check_id: "SCOPE_TOPIC_MISSING", step: "scope", level: "blocker", action: { kind: "field", step: "scope", field: "topic" } };
const warning: CheckIn = { check_id: "EXPLORE_SCOPE_CHANGED", step: "scope", level: "warning", action: { kind: "step", step: "explore" } };
const note: CheckIn = { check_id: "SCOPE_START_YEAR_DEFAULTED", step: "scope", level: "note", params: { year: 2000 }, action: { kind: "field", step: "scope", field: "start_year" } };

const panel = () => document.querySelector("[data-checks-panel='scope']") as HTMLElement;
const row = (id: string, root: ParentNode = document) => root.querySelector(`li[data-check='${id}']`) as HTMLElement;
const dismissPosts = (engine: ReturnType<typeof setUp>["engine"]) => engine.calls.filter((c) => c.method === "POST" && /\/checks\/[A-Z_]+\/(dismiss|restore)$/.test(c.path));

describe("checks panel (02-checks)", () => {
  it("the panel renders the engine's rows and computes none", async () => {
    const one = checkRow(warning);
    setUp({
      draft: decided(),
      checks: () => [warning],
      checksAnswer: (step) => ({
        shape: "checks-v1", scope: { kind: "draft", id: SESSION, updated_at: "x" }, computed_at: "2026-11-18T10:00:00+00:00", sources: ["check"],
        checks: step === "scope" || !step ? [one] : [], waiting: [], counts: { blocker: 3, warning: 5, note: 0, dismissed: 0 }, partial: [],
        ...(step ? {} : { by_step: { scope: { blocker: 3, warning: 5, note: 0 }, explore: { blocker: 0, warning: 0, note: 0 }, direction: { blocker: 0, warning: 0, note: 0 }, shape: { blocker: 0, warning: 0, note: 0 }, criteria: { blocker: 0, warning: 0, note: 0 }, review: { blocker: 0, warning: 0, note: 0 } } }), ready: false,
      }),
    });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(panel()).not.toBeNull());
    expect(panel().querySelector("[data-checks-counts]")?.textContent).toBe("Checks · 3 to fix · 5 to look at");
    expect(panel().querySelectorAll("li[data-check]")).toHaveLength(1);
    expect(within(panel()).getByText("The sample was searched for an earlier question, years or languages.")).toBeInTheDocument();
    // The engine's English `message` is for logs only.
    expect(screen.queryByText(/for logs/)).toBeNull();
    await waitFor(() => expect(document.querySelector("[data-step-checks='scope']")?.textContent).toContain("8 to check"));
  });

  it("a blocker row has no Dismiss; a warning has; a Review target warning has none", async () => {
    const target: CheckIn = { check_id: "REVIEW_TARGET_HAS_WORKSPACE", step: "review", level: "warning", dismissible: false, action: { kind: "field", step: "review", field: "title" } };
    setUp({ draft: decided(), existing: "workspace", checks: () => [blocker, warning, target] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("SCOPE_TOPIC_MISSING")).not.toBeNull());
    expect(within(row("SCOPE_TOPIC_MISSING")).queryByRole("button", { name: "Dismiss" })).toBeNull();
    expect(within(row("EXPLORE_SCOPE_CHANGED")).getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    cleanup();
    setUp({ draft: decided(), existing: "workspace", checks: () => [blocker, warning, target] });
    render(<InceptionReview locale="en" />);
    await waitFor(() => expect(row("REVIEW_TARGET_HAS_WORKSPACE")).not.toBeNull());
    expect(within(row("REVIEW_TARGET_HAS_WORKSPACE")).queryByRole("button", { name: "Dismiss" })).toBeNull();
  });

  it("Why opens in place, has a visible word, aria-expanded, and keeps focus", async () => {
    setUp({ draft: decided(), checks: () => [{ ...warning, threshold: { name: "POOL_THIN_FLOOR", value: 12, default: 12, unit: "records" } }] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull());
    const why = within(row("EXPLORE_SCOPE_CHANGED")).getByRole("button", { name: "Why" });
    expect(why).toHaveAttribute("aria-expanded", "false");
    expect(why.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    why.focus();
    fireEvent.click(why);
    expect(why).toHaveAttribute("aria-expanded", "true");
    expect(why).toHaveFocus();
    const text = document.getElementById(why.getAttribute("aria-controls")!)!;
    expect(text.textContent).toContain("Counts and suggestions describe the earlier search, not the draft as it is now.");
    expect(text.textContent).toContain("Suggested: POOL_THIN_FLOOR 12");
    expect(row("EXPLORE_SCOPE_CHANGED").contains(text)).toBe(true);
  });

  it("Dismiss of a warning needs a reason; sends one POST with subject, digest and reason; moves the row to Dismissed with date and reason; Restore returns it", async () => {
    const { engine } = setUp({ draft: decided(), checks: () => [{ ...warning, subject: "years" }] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull());
    fireEvent.click(within(row("EXPLORE_SCOPE_CHANGED")).getByRole("button", { name: "Dismiss" }));
    const field = await screen.findByLabelText("Why are you dismissing this? It is kept in the record.");
    await waitFor(() => expect(field).toHaveFocus());
    fireEvent.click(screen.getByRole("button", { name: "Dismiss with this reason" }));
    expect(field).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("Write a short reason.")).toBeInTheDocument();
    expect(dismissPosts(engine)).toEqual([]);
    fireEvent.change(field, { target: { value: "The years changed on purpose; the pool is fine." } });
    fireEvent.click(screen.getByRole("button", { name: "Dismiss with this reason" }));
    await waitFor(() => expect(dismissPosts(engine)).toHaveLength(1));
    const [post] = dismissPosts(engine);
    expect(post.path).toBe(`${CHECKS}/EXPLORE_SCOPE_CHANGED/dismiss`);
    expect(post.body).toEqual({ subject: "years", evidence_digest: checkRow({ ...warning, subject: "years" }).evidence_digest, reason: "The years changed on purpose; the pool is fine." });
    const dismissed = (await waitFor(() => panel().querySelector("[data-dismissed]") as HTMLElement)) as HTMLElement;
    expect(dismissed.querySelector("summary")?.textContent).toBe("Dismissed (1)");
    expect(dismissed.querySelector("[data-dismissal]")?.textContent).toMatch(/^Dismissed 2026-11-\d{2}: The years changed on purpose; the pool is fine\.$/);
    expect(screen.getByText("Dismissed: The sample was searched for an earlier question, years or languages.")).toBeInTheDocument();
    fireEvent.click(within(dismissed).getByRole("button", { name: "Restore" }));
    await waitFor(() => expect(panel().querySelector("[data-open-rows] li[data-check='EXPLORE_SCOPE_CHANGED']")).not.toBeNull());
    expect(dismissPosts(engine).map((c) => c.path.split("/").at(-1))).toEqual(["dismiss", "restore"]);
  });

  it("Dismiss of a note sends one POST with no reason and opens no form", async () => {
    const { engine } = setUp({ draft: decided(), checks: () => [note] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("SCOPE_START_YEAR_DEFAULTED")).not.toBeNull());
    fireEvent.click(within(row("SCOPE_START_YEAR_DEFAULTED")).getByRole("button", { name: "Dismiss" }));
    expect(document.querySelector("[data-dismiss-form]")).toBeNull();
    await waitFor(() => expect(dismissPosts(engine)).toHaveLength(1));
    expect(dismissPosts(engine)[0].body).toEqual({ subject: "", evidence_digest: checkRow(note).evidence_digest });
    await waitFor(() => expect(panel().querySelector("[data-dismissed] [data-dismissal]")?.textContent).toMatch(/^Dismissed 2026-11-\d{2}$/));
  });

  it("CHECK_CHANGED re-reads and shows the polite line", async () => {
    const { engine } = setUp({ draft: decided(), checks: () => [note] });
    engine.refuseNext(`POST ${CHECKS}/SCOPE_START_YEAR_DEFAULTED/dismiss`, { status: 409, body: { detail: { code: "CHECK_CHANGED", message: "the data changed", details: { current: checkRow(note) } } } });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("SCOPE_START_YEAR_DEFAULTED")).not.toBeNull());
    const reads = () => engine.calls.filter((c) => c.method === "POST" && c.path === CHECKS).length;
    const before = reads();
    fireEvent.click(within(row("SCOPE_START_YEAR_DEFAULTED")).getByRole("button", { name: "Dismiss" }));
    expect(await screen.findByText("The data changed, so nothing was dismissed. Read it again.")).toBeInTheDocument();
    expect(reads()).toBeGreaterThan(before);
    expect(within(panel()).queryByRole("alert")).toBeNull();
    await waitFor(() => expect(row("SCOPE_START_YEAR_DEFAULTED").querySelector("[data-sentence]")).toHaveFocus());
  });

  it("previously_dismissed shows the changed-data line", async () => {
    const { engine } = setUp({ draft: decided(), checks: () => [{ ...warning, subject: "years", evidence: [{ kind: "words", value: "now" }] }] });
    engine.drafts.get(SESSION)!.check_dismissals = [{ check_id: "EXPLORE_SCOPE_CHANGED", subject: "years", evidence_digest: "sha256:old", action: "dismissed", reason: "fine", at: "2026-11-12T09:00:00+00:00" }];
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull());
    expect(row("EXPLORE_SCOPE_CHANGED")).toHaveAttribute("data-status", "open");
    expect(within(row("EXPLORE_SCOPE_CHANGED")).getByText("You dismissed this on 2026-11-12, but the data changed since.")).toBeInTheDocument();
  });

  it("an action of kind proposal opens the 01-proposals card and sends nothing", async () => {
    const { engine } = setUp({ draft: decided({ title: "UAV weed detection" }), checks: true });
    render(<InceptionCriteria locale="en" />);
    const button = (await waitFor(() => {
      const b = document.querySelector("[data-check='CONCEPT_TERM_MISSING'] [data-check-proposal]");
      if (!b) throw new Error("no proposal action yet");
      return b;
    })) as HTMLElement;
    const id = button.getAttribute("data-check-proposal")!;
    await waitFor(() => expect(document.querySelector(`li[data-proposal='${id}']`)).not.toBeNull());
    const before = engine.calls.length;
    fireEvent.click(button);
    expect(document.querySelector(`li[data-proposal='${id}'] [data-apply]`)).toHaveFocus();
    expect(engine.calls.slice(before).filter((c) => c.path.includes("/proposals/"))).toEqual([]);
    expect(button.textContent).toBe("Add it to the concepts");
  });

  it("an action of kind field links to the field's screen", async () => {
    setUp({ draft: decided(), checks: () => [{ check_id: "CONCEPTS_ONE_ONLY", step: "scope", level: "warning", action: { kind: "field", step: "criteria", field: "concepts" } }, blocker] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("CONCEPTS_ONE_ONLY")).not.toBeNull());
    expect(within(row("CONCEPTS_ONE_ONLY")).getByRole("link", { name: "Add a concept" })).toHaveAttribute("href", `/en/inception/criteria/?draft=${SESSION}#field-concepts`);
    // A field on this screen is focused in place.
    const topic = within(row("SCOPE_TOPIC_MISSING")).getByRole("link", { name: "Write your question" });
    expect(topic).toHaveAttribute("href", `/en/inception/scope/?draft=${SESSION}#field-topic`);
    fireEvent.click(topic);
    expect(screen.getByLabelText("Research topic, in one or two sentences")).toHaveFocus();
  });

  it("unsaved edits show the saved-draft line and keep the old rows", async () => {
    const { engine } = setUp({ draft: decided(), checks: () => [warning] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull());
    const reads = engine.calls.filter((c) => c.path === CHECKS).length;
    fireEvent.change(screen.getByLabelText("Research topic, in one or two sentences"), { target: { value: "on-device weed detection with drones" } });
    expect(await screen.findByText("You have changes that are not saved yet. These checks describe the saved draft and update when you save.")).toBeInTheDocument();
    expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull();
    expect(engine.calls.filter((c) => c.path === CHECKS).length).toBe(reads);
  });

  it("offline disables Dismiss and Restore and keeps the rows", async () => {
    const { engine } = setUp({ draft: decided(), checks: () => [warning, note] });
    engine.drafts.get(SESSION)!.check_dismissals = [{ check_id: "SCOPE_START_YEAR_DEFAULTED", subject: "", evidence_digest: checkRow(note).evidence_digest, action: "dismissed", reason: "", at: "2026-11-12T09:00:00+00:00" }];
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull());
    const real = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (String(url).includes("/checks")) throw new TypeError("Failed to fetch");
        return real(url, init);
      }),
    );
    fireEvent.click(within(row("EXPLORE_SCOPE_CHANGED")).getByRole("button", { name: "Dismiss" }));
    fireEvent.change(await screen.findByLabelText(/Why are you dismissing this/), { target: { value: "fine" } });
    fireEvent.click(screen.getByRole("button", { name: "Dismiss with this reason" }));
    await waitFor(() => expect(panel().querySelector("[data-checks-offline]")).not.toBeNull());
    expect(panel().querySelector("[data-checks-offline]")?.textContent).toMatch(/^As of \d{4}-\d{2}-\d{2} \d{2}:\d{2} · needs the engine on this computer$/);
    expect(within(row("EXPLORE_SCOPE_CHANGED")).getByRole("button", { name: "Dismiss" })).toBeDisabled();
    expect(within(panel().querySelector("[data-dismissed]") as HTMLElement).getByRole("button", { name: "Restore" })).toBeDisabled();
    expect(row("SCOPE_START_YEAR_DEFAULTED")).not.toBeNull();
  });

  it("the Review list groups Must fix / Look at / Notes / Dismissed, shows Step n chips, and the header sentence follows blockers and warnings; open warnings do not disable Create", async () => {
    const term: CheckIn = { check_id: "CONCEPT_TERM_MISSING", step: "criteria", level: "warning", subject: "UAV", params: { term: "UAV" }, action: { kind: "field", step: "criteria", field: "concepts" } };
    const old: CheckIn = { check_id: "DIRECTION_SEEDS_FEW", step: "direction", level: "note", params: { n: 1 }, action: { kind: "field", step: "direction", field: "golden_seeds" } };
    const notChosen: CheckIn = { check_id: "DIRECTION_NOT_CHOSEN", step: "direction", level: "note", action: { kind: "step", step: "direction" } };
    const { engine } = setUp({ draft: decided(), checks: () => [blocker, term, notChosen, old] });
    engine.drafts.get(SESSION)!.check_dismissals = [{ check_id: "DIRECTION_SEEDS_FEW", subject: "", evidence_digest: checkRow(old).evidence_digest, action: "dismissed", reason: "", at: "2026-11-12T09:00:00+00:00" }];
    render(<InceptionReview locale="en" />);
    const list = (await waitFor(() => {
      const l = document.querySelector("[data-checks-panel='review-ready']");
      if (!l) throw new Error("no list yet");
      return l;
    })) as HTMLElement;
    expect(within(list).getByRole("heading", { name: "Ready to create?" })).toBeInTheDocument();
    expect(list.querySelector("[data-ready-sentence]")?.textContent).toBe("Not ready: 1 must be fixed first.");
    expect(list.querySelector("[data-group='blocker'] h3")?.textContent).toBe("Must fix");
    expect(list.querySelector("[data-group='warning'] h3")?.textContent).toBe("Look at");
    expect(list.querySelector("[data-group-note] summary")?.textContent).toBe("Notes (1)");
    expect(list.querySelector("[data-dismissed] summary")?.textContent).toBe("Dismissed (1)");
    expect(row("SCOPE_TOPIC_MISSING", list).querySelector("[data-step-chip]")?.textContent).toBe("Step 1");
    expect(row("CONCEPT_TERM_MISSING", list).querySelector("[data-step-chip]")?.textContent).toBe("Step 5");
    expect(within(row("CONCEPT_TERM_MISSING", list)).getByRole("link", { name: "Add it to the concepts" })).toHaveAttribute("href", `/en/inception/criteria/?draft=${SESSION}#field-concepts`);

    cleanup();
    setUp({ draft: decided(), checks: () => [term] });
    render(<InceptionReview locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-ready-sentence]")?.textContent).toBe("Ready to create. 1 still to look at."));
    expect(await screen.findByRole("button", { name: "Create the workspace" })).toBeEnabled();

    cleanup();
    setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-ready-sentence]")?.textContent).toBe("Ready to create. Nothing is open."));
  });

  it("an unknown source renders with the generic label", async () => {
    setUp({ draft: decided(), checks: () => [{ ...warning, source: "agent" }, note] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("EXPLORE_SCOPE_CHANGED")).not.toBeNull());
    expect(within(row("EXPLORE_SCOPE_CHANGED")).getByText("Other source")).toBeInTheDocument();
    expect(within(row("EXPLORE_SCOPE_CHANGED")).queryByText("Assistant")).toBeNull();
    expect(within(row("SCOPE_START_YEAR_DEFAULTED")).getByText("Fixed check")).toBeInTheDocument();
  });

  it("level to role: blocker is text-only in the blocked role, warning unclear, note exclude, each with words", async () => {
    setUp({ draft: decided(), checks: () => [blocker, warning, note] });
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(row("SCOPE_TOPIC_MISSING")).not.toBeNull());
    const badge = (id: string) => row(id).querySelector("[data-role]") as HTMLElement;
    expect(badge("SCOPE_TOPIC_MISSING")).toHaveAttribute("data-role", "blocked");
    expect(badge("SCOPE_TOPIC_MISSING").className).toContain("text-blocked");
    expect(badge("SCOPE_TOPIC_MISSING").className).not.toMatch(/\bbg-/);
    expect(badge("SCOPE_TOPIC_MISSING").textContent).toBe("Must fix");
    expect(badge("EXPLORE_SCOPE_CHANGED")).toHaveAttribute("data-role", "unclear");
    expect(badge("EXPLORE_SCOPE_CHANGED").textContent).toBe("Look at this");
    expect(badge("SCOPE_START_YEAR_DEFAULTED")).toHaveAttribute("data-role", "exclude");
    expect(badge("SCOPE_START_YEAR_DEFAULTED").textContent).toBe("Note");
  });

  it("copy: every checks.* key and every checks.<ID>.* key exists in en; fr and ar fall back; no literal aria-label (N9 guard)", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    expect(CHECK_IDS).toHaveLength(50);
    for (const id of CHECK_IDS) {
      for (const part of ["sentence", "why", "action"]) expect(CHECKS_COPY.en, `${id}.${part}`).toHaveProperty([`checks.${id}.${part}`]);
    }
    for (const key of ["checks.HARVEST_ABOVE_TARGET_general.sentence", "checks.HARVEST_ABOVE_TARGET_general.why", "checks.counts", "checks.ready.blocked", "checks.dismiss.label", "checks.earlier"]) {
      expect(CHECKS_COPY.en).toHaveProperty([key]);
    }
    for (const [key, en] of Object.entries(CHECKS_COPY.en)) {
      for (const locale of ["fr", "ar"] as const) {
        const text = CHECKS_COPY[locale][key as keyof typeof CHECKS_COPY.en];
        expect(text, `${locale} ${key}`).toBeTruthy();
        expect(holes(text), `${locale} ${key}`).toEqual(holes(en));
      }
    }
    for (const file of ["components/checks-panel.tsx", "components/discovery-checks.tsx", "components/inception-assist.tsx", "components/checks-bus.ts"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });

  it("RTL: ids and codes dir=ltr, reasons dir=auto", async () => {
    const failed: CheckIn = { check_id: "EXPLORE_DATABASE_FAILED", step: "scope", level: "warning", subject: "crossref", params: { database: "crossref", code: "PROVIDER_TIMEOUT" }, action: { kind: "step", step: "explore" } };
    const term: CheckIn = { check_id: "CONCEPT_TERM_MISSING", step: "scope", level: "warning", subject: "UAV", params: { term: "UAV" }, action: { kind: "field", step: "criteria", field: "concepts" } };
    const { engine } = setUp({ draft: decided(), checks: () => [failed, term] });
    engine.drafts.get(SESSION)!.check_dismissals = [{ check_id: "CONCEPT_TERM_MISSING", subject: "UAV", evidence_digest: checkRow(term).evidence_digest, action: "dismissed", reason: "الطائرات المسيّرة خارج النطاق", at: "2026-11-12T09:00:00+00:00" }];
    render(<InceptionScope locale="ar" />);
    await waitFor(() => expect(row("EXPLORE_DATABASE_FAILED")).not.toBeNull());
    const sentence = row("EXPLORE_DATABASE_FAILED").querySelector("[data-sentence]") as HTMLElement;
    expect(within(sentence).getByText("PROVIDER_TIMEOUT")).toHaveAttribute("dir", "ltr");
    expect(within(sentence).getByText("Crossref").closest("bdi")).toHaveAttribute("dir", "ltr");
    const reason = within(row("CONCEPT_TERM_MISSING")).getByText("الطائرات المسيّرة خارج النطاق");
    expect(reason).toHaveAttribute("dir", "auto");
    expect(within(row("CONCEPT_TERM_MISSING")).getByText("UAV")).toHaveAttribute("dir", "auto");
  });

  it("a phone token gets the desktop pointer card", async () => {
    // Inception: the draft read is refused, the screen shows the shared card and no panel is drawn.
    const { engine } = setUp({ draft: decided(), checks: () => [warning] });
    engine.refuseNext(`GET /api/v1/inception/drafts/${SESSION}`, { status: 403, body: { detail: { code: "TOKEN_SCOPE_REFUSED", message: "not a phone route" } } });
    render(<InceptionScope locale="en" />);
    expect((await screen.findAllByText("Not available on this device")).length).toBeGreaterThan(0);
    expect(document.querySelector("[data-checks-panel]")).toBeNull();
    expect(engine.calls.some((c) => c.path === CHECKS)).toBe(false);

    // Discovery: the checks read is refused; the screen keeps its own card and no row is drawn.
    cleanup();
    vi.unstubAllGlobals();
    const discovery = setUpDiscovery({ checks: [{ check_id: "RECALL_NOT_RUN", step: "recall", level: "note", action: { kind: "step", step: "recall" } }] });
    const real = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) =>
        String(url).includes("/discovery/checks")
          ? new Response(JSON.stringify({ detail: { code: "TOKEN_SCOPE_REFUSED", message: "not a phone route" } }), { status: 403, headers: { "content-type": "application/json" } })
          : real(url, init),
      ),
    );
    render(<DiscoveryRecall locale="en" />);
    await screen.findByRole("heading", { level: 1 });
    await waitFor(() => expect(discovery.engine.calls.length).toBeGreaterThan(0));
    expect(document.querySelector("[data-checks-panel]")).toBeNull();
  });

  it("discovery: the Recall panel shows the engine's rows and a dismissal goes to the discovery route", async () => {
    const { engine } = setUpDiscovery({ checks: [{ check_id: "RECALL_NOT_RUN", step: "recall", level: "note", action: { kind: "step", step: "recall" } }] });
    render(<DiscoveryRecall locale="en" />);
    const recall = (await waitFor(() => {
      const p = document.querySelector("[data-checks-panel='recall']");
      if (!p) throw new Error("no panel yet");
      return p;
    })) as HTMLElement;
    expect(within(recall).getByText("No recall check yet.")).toBeInTheDocument();
    expect(within(recall).getByRole("link", { name: "Run a recall check" })).toHaveAttribute("href", "/en/discovery/recall/");
    fireEvent.click(within(recall).getByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(engine.calls.some((c) => c.method === "POST" && c.path === "/api/v1/discovery/checks/RECALL_NOT_RUN/dismiss")).toBe(true));
    await waitFor(() => expect(recall.querySelector("[data-dismissed] summary")?.textContent).toBe("Dismissed (1)"));
  });
});

describe("checks after a decision on the Concepts and criteria page (H-ui-findings F5)", () => {
  const undecided: CheckIn = { check_id: "CRITERIA_UNDECIDED", step: "criteria", level: "blocker", params: { n: 1 }, action: { kind: "step", step: "criteria" } };
  const criteriaRow = (id: string) => document.querySelector(`[data-checks-panel='criteria'] li[data-check='${id}']`) as HTMLElement | null;

  it("Apply on a suggestion saves on the server, so the checks are read again and nothing says 'unsaved'", async () => {
    const { engine } = setUp({ draft: completeDraft({ title: "UAV weed detection", concepts: [], criteria_decisions: { [proofId()]: true } }), checks: true });
    render(<InceptionCriteria locale="en" />);
    await waitFor(() => expect(criteriaRow("CONCEPT_TERM_MISSING")).not.toBeNull());
    const reads = engine.calls.filter((c) => c.path === CHECKS).length;
    fireEvent.click(within(document.querySelector("[data-proposals='criteria']") as HTMLElement).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(criteriaRow("CONCEPT_TERM_MISSING")).toBeNull());
    expect(engine.calls.filter((c) => c.path === CHECKS).length).toBeGreaterThan(reads);
    expect(document.querySelector("[data-checks-unsaved]")).toBeNull();
    expect(document.querySelector("[data-row-saved]")).toBeNull();
  });

  it("Accept on a criterion is not saved yet: each row says it describes the draft as saved, and the line says what to do", async () => {
    setUp({ draft: completeDraft(), checks: () => [undecided] });
    render(<InceptionCriteria locale="en" />);
    await waitFor(() => expect(criteriaRow("CRITERIA_UNDECIDED")).not.toBeNull());
    expect(document.querySelector("[data-row-saved]")).toBeNull();
    fireEvent.click((await screen.findAllByRole("button", { name: /^Accept/ }))[0]);
    const line = await waitFor(() => {
      const el = document.querySelector("[data-checks-unsaved]");
      expect(el).not.toBeNull();
      return el as HTMLElement;
    });
    expect(line.textContent).toBe("You have changes that are not saved yet. These checks describe the saved draft and update when you save.");
    expect(criteriaRow("CRITERIA_UNDECIDED")?.querySelector("[data-row-saved]")?.textContent).toContain("Before your changes");
  });
});
