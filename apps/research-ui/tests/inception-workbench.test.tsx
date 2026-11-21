import { readFileSync } from "node:fs";
import { join } from "node:path";

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionCriteria } from "@/components/inception-criteria";
import { WORKBENCH_COPY } from "@/lib/workbench-copy";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import type { WorkbenchOptions } from "./fixtures/workbench-engine";
import { setUp } from "./inception-helpers";

/**
 * The query workbench on Inception's step 5 (M11a part C; spec
 * `docs/ux/phase0-inception/final/10-query-workbench.md`, "Acceptance tests").
 * The engine is the stateful fake (`fixtures/workbench-engine.ts`); every
 * number the screen prints must be a field of its answers.
 */

afterEach(() => vi.unstubAllGlobals());

const FOUR = [
  { concept: "UAV", synonyms: ["unmanned aerial vehicle"] },
  { concept: "multispectral", synonyms: [] },
  { concept: "weed", synonyms: [] },
  { concept: "segmentation", synonyms: [] },
];
const BENCH = `/api/v1/inception/drafts/${SESSION}/workbench`;

/** Counts a browser-side sum or ratio would contradict: the screen must print these exactly. */
const ODD: WorkbenchOptions["total"] = (db, concepts) => {
  const names = concepts.map((c) => c.concept).join("+");
  const table: Record<string, number> = {
    "UAV+multispectral+weed+segmentation": 166, "multispectral+weed+segmentation": 236, "UAV+weed+segmentation": 512,
    "UAV+multispectral+segmentation": 300, "UAV+multispectral+weed": 170, "UAV+weed+segmentation#merged": 781,
  };
  // The run's merge (UAV OR multispectral in one concept) finds 781 in OpenAlex.
  const merged = concepts.some((c) => c.synonyms.includes("multispectral"));
  const base = merged ? 781 : (table[names] ?? 781);
  return db === "openalex" ? base : db === "semanticscholar" ? base - 59 : db === "arxiv" ? Math.max(1, Math.round(base / 22)) : 6221;
};

function open(options: WorkbenchOptions = {}, draft: Record<string, unknown> = {}) {
  const set = setUp({ draft: completeDraft({ concepts: FOUR, ...draft }), workbench: { total: ODD, ...options } });
  render(<InceptionCriteria locale="en" />);
  return set;
}

const calls = (engine: ReturnType<typeof setUp>["engine"], what = "/counts") =>
  engine.calls.filter((c) => c.method === "POST" && c.path === `${BENCH}${what}`);
const real = (engine: ReturnType<typeof setUp>["engine"], what = "/counts") => calls(engine, what).filter((c) => !(c.body as { dry_run?: boolean }).dry_run);
const row = (db: string) => document.querySelector(`[data-row='${db}']`) as HTMLElement;
/** Open one of the evidence column's sections once the workbench has drawn it. */
async function section(name: string) {
  const summary = await waitFor(() => {
    const el = document.querySelector(`[data-section='${name}'] summary`) as HTMLElement | null;
    if (!el) throw new Error(`no ${name} section yet`);
    return el;
  });
  fireEvent.click(summary);
}

async function counted() {
  fireEvent.click(await screen.findByRole("button", { name: "Count" }));
  await waitFor(() => expect(row("openalex")).not.toBeNull());
}

describe("inception.workbench", () => {
  it("shows the block, the cost line and the sections, and sends no count on load or on a keystroke", async () => {
    const { engine } = open();
    expect(await screen.findByText("Count: 15 requests (OpenAlex 5, Semantic Scholar 5, arXiv 5)")).toBeInTheDocument();
    expect(screen.getByText("Nothing counted yet. Count asks each database how many records match; no records are fetched.")).toBeInTheDocument();
    expect(real(engine)).toHaveLength(0);
    const before = calls(engine).length;
    fireEvent.change(screen.getByLabelText("Add a term", { selector: "#wb-term-0" }), { target: { value: "drone" } });
    expect(calls(engine)).toHaveLength(before); // a keystroke sends nothing, not even the dry call
    fireEvent.keyDown(screen.getByLabelText("Add a term", { selector: "#wb-term-0" }), { key: "Enter" });
    await waitFor(() => expect(calls(engine).length).toBe(before + 1)); // the committed edit asks the cost only
    expect(real(engine)).toHaveLength(0);
    for (const section of ["counts", "seeds", "comparison"]) expect(document.querySelector(`[data-section='${section}']`)).not.toBeNull();
  });

  it("Count sends one request after the cost; the numbers are the engine's; a repeat costs nothing", async () => {
    const { engine } = open({}, {});
    expect(await screen.findByText(/Count: 15 requests/)).toBeInTheDocument();
    await counted();
    expect(real(engine)).toHaveLength(1);
    const oa = row("openalex");
    expect(within(oa).getByText("166 · counted 10:15 UTC")).toBeInTheDocument();
    const multi = oa.querySelector("[data-cell='drop-1']") as HTMLElement;
    expect(multi.textContent).toContain("512 · +346, ×3.1");
    expect(within(row("arxiv")).getByText(/^8 · counted/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Already counted, no request.")).toBeInTheDocument());
  });

  it("marks the largest effect in words, notes a concept that at least doubles a count, and never says to drop it", async () => {
    open();
    await counted();
    const largest = document.querySelectorAll("[data-row='openalex'] [data-largest]");
    expect(largest).toHaveLength(1);
    expect(largest[0].textContent).toBe("largest effect");
    expect(screen.getAllByText(/Without 'multispectral', OpenAlex finds 512 records instead of 166. Read a few of them before deciding whether they belong./).length).toBeGreaterThan(0);
    expect(document.body.textContent).not.toMatch(/remove it|drop it/i);
  });

  it("shows the exact string sent, left to right, as the engine wrote it", async () => {
    open();
    await counted();
    const code = row("openalex").querySelector("[data-string]") as HTMLElement;
    expect(code).toHaveAttribute("dir", "ltr");
    expect(code.textContent).toMatch(/^openalex:openalex\|/);
  });

  it("Crossref with two or more concepts is not counted until Count anyway, then reads 'any of the words' and is not summed", async () => {
    const { engine } = open({}, {});
    // The databases ticked on Explore: none here, so the engine's four.
    await counted();
    const cr = row("crossref");
    expect(within(cr).getByText("Crossref cannot combine concepts with AND. Its count would be for any of your words, so it is not shown.")).toBeInTheDocument();
    expect(real(engine).every((c) => !(c.body as { crossref_anyway?: boolean }).crossref_anyway)).toBe(true);
    fireEvent.click(within(cr).getByRole("button", { name: "Count anyway" }));
    await waitFor(() => expect(within(row("crossref")).getByText("6221 · any of the words, not your query")).toBeInTheDocument());
    const anyway = real(engine).at(-1)!.body as { providers: string[]; crossref_anyway: boolean };
    expect(anyway).toMatchObject({ providers: ["crossref"], crossref_anyway: true });
    expect(row("crossref").querySelector("[data-cell='drop-0']")?.textContent ?? "").toBe("");
    expect(document.querySelector("[data-size-line]")?.textContent).not.toContain("6221");
  });

  it.each([
    [{ status: "quota_used_up", resets_at: "2026-11-22T00:00:00+00:00", resets_in: { hours: 13, minutes: 45 } }, "Semantic Scholar's daily quota is used up. It resets at 00:00 UTC, in 13 h 45 min. No earlier count."],
    [{ status: "rate_limited", error_code: "PROVIDER_RATE_LIMITED" }, "Semantic Scholar is busy (it asked to slow down). Try again in a minute; the other counts stand."],
    [{ status: "refused", error_code: "PROVIDER_REFUSED", http_status: 403 }, "Semantic Scholar refused the request (HTTP 403)."],
    [{ status: "unavailable", error_code: "PROVIDER_UNAVAILABLE" }, "Semantic Scholar did not answer."],
    [{ status: "timeout", error_code: "PROVIDER_TIMEOUT" }, "Semantic Scholar did not answer within 45 s."],
    [{ status: "not_countable" }, "This database cannot report a total."],
  ])("prints a row state in words and never a 0: %o", async (fail, words) => {
    open({ fail: { semanticscholar: fail } });
    await counted();
    const ss = row("semanticscholar");
    expect(within(ss).getByText(words)).toBeInTheDocument();
    expect(ss.querySelector("[data-cell='query']")?.textContent).not.toMatch(/^0\b/);
  });

  it("names a budget that is used, and a database not in this search", async () => {
    open({ fail: { arxiv: { status: "budget_spent" } }, budget: { arxiv: { limit: 100, spent: 100, left: 0, renews_at: "2026-11-22T00:00:00+00:00", low: true } } });
    await counted();
    expect(within(row("arxiv")).getByText("Today's counting budget for arXiv is used (100 requests). It renews at 00:00 UTC. The harvest's quota is kept for the harvest.")).toBeInTheDocument();
    expect(screen.getByText("arXiv: 0 of 100 counting requests left today.")).toBeInTheDocument();
  });

  it("concept edits: rename, add and remove a term, split a term out, remove a concept; AND between, OR inside; an edit marks the counts as the previous version and sends nothing", async () => {
    const { engine } = open();
    await counted();
    const sent = real(engine).length;
    expect(document.querySelectorAll("[data-op='and']")).toHaveLength(3);
    expect(document.querySelector("[data-chips='0'] [data-op='or']")).not.toBeNull();
    expect(screen.queryByText(/\bNOT\b/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Make 'unmanned aerial vehicle' a concept of its own" }));
    await waitFor(() => expect(screen.getByLabelText("Concept 5")).toHaveValue("unmanned aerial vehicle"));
    expect(screen.getByText("Previous version")).toBeInTheDocument();
    expect(within(row("openalex")).getByText("166 · for the previous version. Count again.")).toBeInTheDocument();
    fireEvent.click(within(document.querySelector("[data-concept='4']") as HTMLElement).getByRole("button", { name: "Remove concept" }));
    fireEvent.change(screen.getByLabelText("Concept 3"), { target: { value: "weeds" } });
    fireEvent.blur(screen.getByLabelText("Concept 3"));
    const term = screen.getByLabelText("Add a term", { selector: "#wb-term-0" });
    fireEvent.change(term, { target: { value: "drone" } });
    fireEvent.keyDown(term, { key: "Enter" });
    expect(document.querySelector("[data-chips='0'] [data-chip='drone']")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Remove drone" }));
    expect(document.querySelector("[data-chip='drone']")).toBeNull();
    expect(real(engine)).toHaveLength(sent);
  });

  it("merges two concepts under a name that starts as the first's, and shows the last counted and this version side by side", async () => {
    open();
    await counted();
    fireEvent.click(screen.getByRole("checkbox", { name: "Select UAV to merge" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select multispectral to merge" }));
    fireEvent.click(screen.getByRole("button", { name: "Merge into one" }));
    expect(screen.getByLabelText("Name of the merged concept")).toHaveValue("UAV");
    expect([...(screen.getByLabelText("Name of the merged concept") as HTMLSelectElement).options].map((o) => o.value)).toEqual(["UAV", "unmanned aerial vehicle", "multispectral"]);
    fireEvent.click(screen.getByRole("button", { name: "Merge" }));
    expect(screen.getByLabelText("Concept 1")).toHaveValue("UAV");
    expect([...document.querySelectorAll("[data-chips='0'] [data-chip]")].map((c) => c.getAttribute("data-chip"))).toEqual(["UAV", "unmanned aerial vehicle", "multispectral"]);
    const versions = document.querySelector("[data-versions]") as HTMLElement;
    expect(within(versions).getByText("Last counted")).toBeInTheDocument();
    expect(within(versions).getByText("4 concepts, 5 terms · counted 10:15 UTC")).toBeInTheDocument();
    expect(within(versions).getByText("3 concepts, 5 terms · not counted")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Count" }));
    await waitFor(() => expect(within(document.querySelector("[data-version='now']") as HTMLElement).getByText("OpenAlex 781")).toBeInTheDocument());
    expect(within(document.querySelector("[data-version='last']") as HTMLElement).getByText("OpenAlex 166")).toBeInTheDocument();
  });

  it("what each synonym adds: the cost first, one request on confirm, and 'adds nothing' at gain 0", async () => {
    const { engine } = open({ total: (db, concepts) => (concepts[0]?.synonyms.includes("unmanned aerial vehicle") || concepts[0]?.concept === "unmanned aerial vehicle" ? 166 : 150) });
    await counted();
    fireEvent.click(screen.getByRole("button", { name: "What does each synonym add?" }));
    expect(await screen.findByText(/2 requests, one per term of this concept\./)).toBeInTheDocument();
    expect(real(engine, "/synonyms")).toHaveLength(0);
    fireEvent.click(within(document.querySelector("[data-syn-cost]") as HTMLElement).getByRole("button", { name: "Count" }));
    await waitFor(() => expect(real(engine, "/synonyms")).toHaveLength(1));
    expect(await screen.findByText("UAV: adds nothing in OpenAlex today")).toBeInTheDocument();
    expect(screen.getByText("unmanned aerial vehicle: 150 without it · adds 16")).toBeInTheDocument();
  });

  it("reads what a concept removes in one request and marks the absent concept", async () => {
    const { engine } = open({ removed: [{ title: "Weed segmentation from UAV RGB images", doi: "10.1/x", year: 2022, lacks: ["multispectral"] }] });
    await counted();
    fireEvent.change(screen.getByLabelText("Concept"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Read what this concept removes (1 request)" }));
    expect(await screen.findByText("Weed segmentation from UAV RGB images")).toBeInTheDocument();
    expect(screen.getByText("no term of 'multispectral' in the title or abstract")).toBeInTheDocument();
    expect(real(engine, "/removed")).toHaveLength(1);
  });

  it("known papers: each seed's concepts in words, the warning when they cannot test the query, and other databases not checked here", async () => {
    const strict = "Weed segmentation from UAV multispectral imagery";
    open({ seedTitles: { "10.1/a": strict, "10.1/b": strict, "10.1/c": strict } }, { golden_seeds: ["10.1/a", "10.1/b", "10.1/c"] });
    await section("seeds");
    expect(await screen.findByText("Your 3 known papers each use a term of every concept, so they cannot show a paper this query misses. Add a known paper that does not say 'UAV', or compare with an export from another database.")).toBeInTheDocument();
    expect(screen.getByText("3 of 3 use every concept")).toBeInTheDocument();
    expect(screen.getAllByText("multispectral · found").length).toBe(3);
    expect(screen.getByText(/Not checked here\. The recall check on Plan runs the full query\./)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Check seeds in OpenAlex" }));
    expect(await screen.findByText(/OpenAlex is not asked yet: this check waits for a first test with the real database\./)).toBeInTheDocument();
  });

  it("a seed that lacks a concept is missed by the words, with its own term offered; too few readable seeds say so", async () => {
    open({ seedTitles: { "10.1/a": "Weed segmentation from UAV RGB orthophotos" } }, { golden_seeds: ["10.1/a"] });
    await section("seeds");
    expect(await screen.findByText("Too few known papers to test the query.")).toBeInTheDocument();
    expect(screen.getByText(/missed by the words of this query: no term of 'multispectral' in its title or abstract/)).toBeInTheDocument();
    expect(screen.getByText("Suggested by a known paper · not yet yours")).toBeInTheDocument();
  });

  it("compares with a staged Scopus export: the report line, the measure, the missing records and their terms, applied only with a concept chosen", async () => {
    const { engine } = open();
    await section("comparison");
    const ris = [
      "TY  - JOUR\nTI  - Weed segmentation from UAV multispectral imagery\nDO  - 10.9/a\nER  - ",
      "TY  - JOUR\nTI  - Hyperspectral weed segmentation from a UAV\nAB  - hyperspectral imagery\nDO  - 10.9/b\nER  - ",
      "TY  - JOUR\nTI  - Hyperspectral weed segmentation in fields\nAB  - hyperspectral imagery\nDO  - 10.9/c\nER  - ",
    ].join("\n") + "\n";
    const file = new File([ris], "scopus.ris", { type: "application/x-research-info-systems" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode(ris).buffer });
    fireEvent.change(screen.getByLabelText("RIS or NBIB file"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Database it came from"), { target: { value: "Scopus" } });
    fireEvent.click(document.querySelector("[data-cmp-stage]") as HTMLElement);
    expect(await screen.findByText(/Staged: Scopus, 3 records/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Compare" }));
    expect(await screen.findByText("2 of 3 Scopus records are missing from what your query finds.")).toBeInTheDocument();
    expect(screen.getByText("Measure: matched by your query's words in the title, abstract and keywords")).toBeInTheDocument();
    expect(screen.getAllByText(/lacks (UAV, )?multispectral/).length).toBe(2);
    const rowHyper = document.querySelector("[data-suggestion-row='hyperspectral']") as HTMLElement;
    expect(within(rowHyper).getByText("hyperspectral · in 2 of 2 missing records")).toBeInTheDocument();
    const apply = within(rowHyper).getByRole("button", { name: "Apply" });
    expect(apply).toBeDisabled();
    expect(screen.queryByRole("button", { name: /Apply all/ })).toBeNull();
    fireEvent.change(within(rowHyper).getByLabelText("Add as synonym of"), { target: { value: "1" } });
    fireEvent.click(apply);
    expect(document.querySelector("[data-chips='1'] [data-chip='hyperspectral']")).not.toBeNull();
    expect(engine.calls.some((c) => c.method === "PUT")).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(screen.getByText("No export staged. Add one from Scopus, Web of Science or another database.")).toBeInTheDocument());
  });

  it("refuses a file that is not an export, with the words of the spec", async () => {
    open();
    await section("comparison");
    const file = new File(["hello"], "notes.ris");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode("hello").buffer });
    fireEvent.change(screen.getByLabelText("RIS or NBIB file"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Database it came from"), { target: { value: "Scopus" } });
    fireEvent.click(document.querySelector("[data-cmp-stage]") as HTMLElement);
    expect(await screen.findByText("This file is not RIS or NBIB. Export from the database as RIS (or NBIB for PubMed) and add it again.")).toBeInTheDocument();
  });

  it("suggestion keys act only on a focused row: A applies, R rejects, J and K move; nothing in a text field", async () => {
    const { engine } = setUp({ draft: completeDraft({ concepts: [{ concept: "weed detection", synonyms: [] }] }) });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    render(<InceptionCriteria locale="en" />);
    const first = (await screen.findByText(/embedded hardware · 8 papers/)).closest("[data-suggestion-row]") as HTMLElement;
    fireEvent.keyDown(screen.getByLabelText("Add a term", { selector: "#wb-term-0" }), { key: "a" });
    expect(document.querySelector("[data-chip='embedded hardware']")).toBeNull();
    first.focus();
    fireEvent.keyDown(first, { key: "j" });
    expect(document.activeElement?.getAttribute("data-suggestion-row")).toBe("real-time");
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "r" });
    await waitFor(() => expect(document.querySelector("[data-suggestion-row='real-time']")).toBeNull());
    const again = document.querySelector("[data-suggestion-row='embedded hardware']") as HTMLElement;
    again.focus();
    fireEvent.keyDown(again, { key: "a" });
    expect(document.querySelector("[data-chip='embedded hardware']")).not.toBeNull();
  });

  it("Use this version sends one PUT with the concepts replaced and every other field kept; it is the one brand button while edits are unused", async () => {
    const { engine } = open({}, { golden_seeds: ["10.1/a"], matrix_columns: ["Sensor"] });
    expect(await screen.findByRole("button", { name: "Continue to review" })).toHaveAttribute("data-variant", "primary");
    fireEvent.click(screen.getAllByRole("button", { name: "Remove concept" })[0]);
    await waitFor(() => expect(screen.getByRole("button", { name: "Use this version" })).toHaveAttribute("data-variant", "primary"));
    expect(screen.getByRole("button", { name: "Continue to review" })).toHaveAttribute("data-variant", "secondary");
    expect(document.querySelectorAll("button[data-variant='primary']")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Use this version" }));
    await waitFor(() => expect(engine.calls.filter((c) => c.method === "PUT")).toHaveLength(1));
    const put = engine.calls.find((c) => c.method === "PUT")!.body as { draft: Record<string, unknown> };
    expect(put.draft.concepts).toEqual(FOUR.slice(1));
    expect(put.draft.golden_seeds).toEqual(["10.1/a"]);
    expect(put.draft.matrix_columns).toEqual(["Sensor"]);
    expect(await screen.findByText("This version is now the draft's search.")).toBeInTheDocument();
  });

  it("asks once before leaving a version not used", async () => {
    const { engine, assign } = open();
    fireEvent.click((await screen.findAllByRole("button", { name: "Remove concept" }))[0]);
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    expect(await screen.findByText("You have a version you have not used. Use it, or leave it?")).toBeInTheDocument();
    expect(engine.calls.filter((c) => c.method === "PUT")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Leave it" }));
    await waitFor(() => expect(engine.calls.filter((c) => c.method === "PUT")).toHaveLength(1));
    expect((engine.calls.find((c) => c.method === "PUT")!.body as { draft: { concepts: unknown } }).draft.concepts).toEqual(FOUR);
    await waitFor(() => expect(assign).toHaveBeenCalled());
  });

  it("maps a running job and a missing contact email to their words, and keeps the chips usable", async () => {
    open({ refuse: { status: 409, code: "DISCOVERY_JOB_ACTIVE" } });
    fireEvent.click(await screen.findByRole("button", { name: "Count" }));
    expect(await screen.findByText("A search or a recall check is running on this computer, so counting waits. The databases' rate limits are its.")).toBeInTheDocument();
    expect(screen.getByLabelText("Concept 1")).not.toBeDisabled();
  });

  it("offers the Scopus and Web of Science strings to copy, marked to check in the database", async () => {
    open();
    fireEvent.click(await screen.findByText("Your query for other databases, to copy"));
    expect(screen.getByText("Check it in the database: these strings were not tried there.")).toBeInTheDocument();
    expect(document.querySelector("[data-external='scopus']")?.textContent).toMatch(/^TITLE-ABS-KEY\(\("UAV" OR "unmanned aerial vehicle"\) AND/);
  });
});

describe("inception.workbench checks (DoD 19)", () => {
  it("shows QUERY_NOT_COUNTED and SEEDS_CANNOT_TEST at the concepts field with their words; neither blocks Continue", async () => {
    const rows = [
      { check_id: "QUERY_NOT_COUNTED", step: "criteria", level: "note" as const, action: { kind: "field", step: "criteria", field: "concepts" } },
      { check_id: "SEEDS_CANNOT_TEST", step: "criteria", level: "warning" as const, subject: "all", params: { n: 4, concept: "UAV", concepts: "UAV" }, message_key: "checks.SEEDS_CANNOT_TEST_all.sentence", action: { kind: "step", step: "direction" } },
    ];
    setUp({ draft: completeDraft({ concepts: FOUR }), checks: () => rows });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("This search has not been counted in any database yet.")).toBeInTheDocument();
    await waitFor(() =>
      expect(document.querySelector("[data-check='SEEDS_CANNOT_TEST']")?.textContent).toContain(
        "known papers each use a term of every concept, so they cannot show a paper this query misses.",
      ),
    );
    expect(screen.getByRole("button", { name: "Continue to review" })).not.toBeDisabled();
  });
});

describe("workbench copy", () => {
  it("has every key in en, fr and ar with the same placeholders, and no literal labels in the component (N9)", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const [key, en] of Object.entries(WORKBENCH_COPY.en)) {
      for (const locale of ["fr", "ar"] as const) {
        const text = WORKBENCH_COPY[locale][key as keyof typeof WORKBENCH_COPY.en];
        expect(text, `${locale} ${key}`).toBeTruthy();
        expect(holes(text), `${locale} ${key}`).toEqual(holes(en));
      }
    }
    const component = readFileSync(join(process.cwd(), "components", "query-workbench.tsx"), "utf8");
    expect(component.match(/(aria-label|title|alt|placeholder)="/g)).toBeNull();
  });
});
