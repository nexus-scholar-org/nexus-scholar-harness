import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionExplore } from "@/components/inception-explore";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import type { ReconOptions } from "./fixtures/recon-engine";
import { setUp } from "./inception-helpers";

/** Spec 02 Explore (M4d) over the stateful fake of the recon routes. */

afterEach(() => vi.unstubAllGlobals());

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;
const ALL = ["openalex", "semanticscholar", "crossref", "arxiv"];
const SHORTEN = "Every word of the query must appear, so a long query can find nothing. Shorten the query above.";

function start(recon: ReconOptions = {}, draft: Record<string, unknown> = completeDraft(), probed = false) {
  const set = setUp({ draft, recon });
  if (probed) set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  render(<InceptionExplore locale="en" />);
  return { ...set, recon };
}

const posts = (engine: ReturnType<typeof setUp>["engine"], suffix: string) => engine.calls.filter((c) => c.method === "POST" && c.path === `${RECON}${suffix}`);

describe("inception.explore", () => {
  it("opens on the first-search card with one brand button when the draft has never searched", async () => {
    const { engine } = start();
    // The file's first render waits longer than the default second: the full suite runs it under load.
    await screen.findByRole("heading", { name: "Your first search" }, { timeout: 5000 });
    expect(screen.getByText("on-device weed detection")).toBeInTheDocument();
    expect(screen.getByText("Your draft has no from-year, so the search starts at 2000.")).toBeInTheDocument();
    expect(screen.getAllByRole("button").filter((b) => b.className.includes("bg-brand"))).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Search the literature" })).toBeEnabled();
    expect(engine.calls.some((c) => c.path.endsWith("/distill") || c.path.endsWith("/directions"))).toBe(false);
    const nav = screen.getByRole("navigation", { name: "Inception steps" });
    expect(within(nav).getByRole("link", { name: "2 Explore" })).toHaveAttribute("aria-current", "step");
  });

  it("disables the search without a question and says where to write it", async () => {
    start({}, {});
    const go = await screen.findByRole("button", { name: "Search the literature" });
    expect(go).toBeDisabled();
    expect(screen.getByRole("link", { name: "Write your question in step 1 first." })).toHaveAttribute("href", `/en/inception/scope/?draft=${SESSION}`);
  });

  it("sends refresh, semantic, the databases and the shown query, never the topic or years, then replaces the card with the pool", async () => {
    const { engine } = start();
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "Pool · 14 papers" })).toBeInTheDocument();
    expect(posts(engine, "/probe").map((c) => c.body)).toEqual([{ refresh: false, semantic: false, databases: ALL, query: "on-device weed detection" }]);
    expect(screen.queryByRole("heading", { name: "Your first search" })).toBeNull();
    // The fetch line is the pool's, not the draft's.
    expect(document.querySelector("[data-pool-meta]")?.textContent).toMatch(/Keyword · 2000 to present · en$/);
    expect(screen.getByRole("button", { name: "See 3 directions" })).toBeEnabled();
    expect(engine.calls.some((c) => c.path.endsWith("/delta"))).toBe(false);
  });

  it("sends semantic when the researcher chose it", async () => {
    const { engine } = start();
    fireEvent.click(await screen.findByRole("radio", { name: "Semantic" }));
    fireEvent.click(screen.getByRole("button", { name: "Search the literature" }));
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    expect(posts(engine, "/probe")[0].body).toEqual({ refresh: false, semantic: true, databases: ALL, query: "on-device weed detection" });
  });

  it("reads the job when its stream closes before the end", async () => {
    const { engine } = start({ holdStream: true });
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "Pool · 14 papers" })).toBeInTheDocument();
    expect(engine.calls.some((c) => c.method === "GET" && /\/recon\/jobs\/rjob_\d+$/.test(c.path))).toBe(true);
  });

  it("reads the session again when the job can no longer be followed", async () => {
    const set = setUp({
      draft: completeDraft(),
      recon: { holdStream: true },
      refuseOnce: { [`GET ${RECON}/jobs/rjob_0000000000000001`]: { status: 404, body: { detail: { code: "RECON_JOB_NOT_FOUND", message: "no recon job" } } } },
    });
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "The search can no longer be followed" })).toBeInTheDocument();
    await waitFor(() => expect(set.engine.calls.filter((c) => c.method === "GET" && c.path === RECON).length).toBeGreaterThanOrEqual(2));
  });

  it("shows MAILTO_NOT_SET, sends no probe, and still shows the pool on screen", async () => {
    const recon: ReconOptions = {};
    const set = setUp({ draft: completeDraft(), recon });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    recon.mailto = false;
    render(<InceptionExplore locale="en" />);
    expect(await screen.findByRole("heading", { name: "This console has no contact email for the literature databases" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Pool · 14 papers" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh pool" })).toBeDisabled();
    expect(posts(set.engine, "/probe")).toHaveLength(1);
  });

  it("shows the same card when the probe itself is refused MAILTO_NOT_SET", async () => {
    setUp({ draft: completeDraft(), refuseOnce: { [`POST ${RECON}/probe`]: { status: 409, body: { detail: { code: "MAILTO_NOT_SET", message: "set it" } } } } });
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    const card = await screen.findByRole("heading", { name: "This console has no contact email for the literature databases" });
    expect(card.closest("section")?.querySelector("details")?.textContent).toContain("MAILTO_NOT_SET");
  });

  it("lists each database of a search where every database failed, and shows no pool", async () => {
    start({ outcomes: ["failed"] });
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "Every database failed to answer" })).toBeInTheDocument();
    const failed = document.querySelector("[data-job-error='PROVIDERS_FAILED'] [data-legs]") as HTMLElement;
    expect(failed.querySelectorAll("[data-leg-status='failed']")).toHaveLength(4);
    expect(within(failed).getAllByText("failed")).toHaveLength(4);
    expect(within(failed).queryByText(/0 papers|no papers/)).toBeNull();
    expect(screen.queryByRole("heading", { name: /^Pool ·/ })).toBeNull();
  });

  it("shows an empty search as POOL_EMPTY: each database says 0 results with its query, never answered", async () => {
    start({ outcomes: ["empty"] });
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "The search found no papers" })).toBeInTheDocument();
    const table = document.querySelector("[data-job-error='POOL_EMPTY']") as HTMLElement;
    const legs = [...table.querySelectorAll("[data-leg]")] as HTMLElement[];
    expect(legs).toHaveLength(4);
    for (const leg of legs) {
      expect(within(leg).getByText("0 results")).toBeInTheDocument();
      expect(within(leg).queryByText("answered")).toBeNull();
      expect(leg.querySelector("[data-executed-query] [dir='ltr']")?.textContent).toBeTruthy();
    }
    // M10b Part C (C4): the three-word keyword query found nothing in every database, so the engine says shorten.
    expect(within(table).getByText(SHORTEN)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /^Pool ·/ })).toBeNull();
    fireEvent.click(within(table).getByRole("button", { name: "Edit the query" }));
    expect(screen.getByRole("textbox", { name: "Query sent to the databases" })).toHaveFocus();
  });

  // M10b Part C (C4, 02-explore "Explore on an empty search").
  it("POOL_EMPTY shows one Databases asked list", async () => {
    start({ outcomes: ["ok", "empty"] }, completeDraft(), true);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool" }));
    await screen.findByRole("heading", { name: "The search found no papers" });
    expect(screen.getAllByRole("heading", { name: "Databases asked" })).toHaveLength(1);
    expect(document.querySelector("[data-databases]")).toBeNull();
    expect(document.querySelectorAll("[data-job-error='POOL_EMPTY'] [data-leg]")).toHaveLength(4);
  });

  it("PROVIDERS_FAILED shows one Databases asked list", async () => {
    start({ outcomes: ["ok", "failed"] }, completeDraft(), true);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool" }));
    await screen.findByRole("heading", { name: "Every database failed to answer" });
    expect(screen.getAllByRole("heading", { name: "Databases asked" })).toHaveLength(1);
    expect(document.querySelector("[data-databases]")).toBeNull();
    expect(screen.queryByText(SHORTEN)).toBeNull();
  });

  it("the shorten advice shows with details.shorten true", async () => {
    const { engine } = start({ outcomes: ["empty"] });
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    await screen.findByRole("heading", { name: "The search found no papers" });
    const job = [...engine.recon.jobs.values()][0].job as { error: { details: { shorten: boolean } } };
    expect(job.error.details.shorten).toBe(true);
    expect(document.querySelector("[data-shorten]")?.textContent).toContain(SHORTEN);
  });

  it("no shorten advice on POOL_EMPTY without the flag, whatever the query length", async () => {
    // A semantic search of eight words: the engine does not say shorten, so the screen does not either.
    const { engine } = start({ outcomes: ["empty"] });
    fireEvent.click(await screen.findByRole("radio", { name: "Semantic" }));
    const field = screen.getByRole("textbox", { name: "Query sent to the databases" });
    fireEvent.change(field, { target: { value: "real time weed detection on embedded edge hardware" } });
    fireEvent.click(screen.getByRole("button", { name: "Search the literature" }));
    await screen.findByRole("heading", { name: "The search found no papers" });
    const job = [...engine.recon.jobs.values()][0].job as { error: { details: { shorten: boolean } } };
    expect(job.error.details.shorten).toBe(false);
    expect(screen.getByRole("textbox", { name: "Query sent to the databases" })).toBeInTheDocument();
    expect(screen.queryByText(SHORTEN)).toBeNull();
    expect(document.querySelector("[data-shorten]")).toBeNull();
  });

  it("no shorten advice when the query field is not shown", async () => {
    const set = setUp({ draft: completeDraft(), recon: { outcomes: ["ok", "empty"] } });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2025 }, base_updated_at: record.updated_at });
    // The pool read never answers, so neither the pool card nor the field alone is on screen.
    holdDistill();
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool for the new scope" }));
    await screen.findByRole("heading", { name: "The search found no papers" });
    const job = [...set.engine.recon.jobs.values()].at(-1)!.job as { error: { details: { shorten: boolean } } };
    expect(job.error.details.shorten).toBe(true);
    expect(screen.queryByRole("textbox", { name: "Query sent to the databases" })).toBeNull();
    expect(screen.queryByText(SHORTEN)).toBeNull();
  });

  it("names the failed database of a partial pool with its error, its code under Details and its notes", async () => {
    start({ outcomes: ["partial"] }, completeDraft(), true);
    const banner = (await screen.findByRole("heading", { name: "Some databases did not answer" })).closest("section") as HTMLElement;
    const crossref = banner.querySelector("[data-leg='crossref']") as HTMLElement;
    expect(within(crossref).getByText("Crossref")).toBeInTheDocument();
    expect(within(crossref).getByText("ConnectError: offline")).toBeInTheDocument();
    expect(crossref.querySelector("details [data-leg-code]")?.textContent).toBe("PROVIDER_UNAVAILABLE");
    expect(within(crossref).getByText("language (en): no language filter is sent to crossref")).toBeInTheDocument();
    expect(screen.getAllByText("Partial pool").length).toBeGreaterThan(0);
  });

  it("reads a rejected Semantic Scholar key as failed with its own sentence", async () => {
    start({ outcomes: ["keyRefused"] }, completeDraft(), true);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    const s2 = document.querySelector("[data-databases] [data-leg='semanticscholar']") as HTMLElement;
    expect(within(s2).getByText("failed")).toBeInTheDocument();
    expect(within(s2).getByText("Semantic Scholar rejected the key; it was not retried without it")).toBeInTheDocument();
  });

  it("prints the key lines as the discovery Plan does", async () => {
    start({ keys: { openalex_key_set: false, s2_key_set: true } });
    await screen.findByRole("heading", { name: "Your first search" });
    expect(screen.getByText("Not set — set SCHOLAR_OPENALEX_KEY")).toBeInTheDocument();
    expect(screen.getByText("Set, not yet verified")).toBeInTheDocument();
    expect(screen.getByText(/OpenAlex is still asked without a key/)).toBeInTheDocument();
  });

  it("keeps See directions for a thin pool and says why it is thin", async () => {
    start({ outcomes: ["thin"] }, completeDraft(), true);
    expect(await screen.findByText("Only 7 papers came back")).toBeInTheDocument();
    expect(screen.getByText("7 of 12 needed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^See/ })).toBeEnabled();
  });

  it("draws the echo tile without a pass or fail badge, and the one-paper school note without a thin badge", async () => {
    start({}, completeDraft(), true);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    const echo = document.querySelector("[data-tile='echo']") as HTMLElement;
    expect(echo.querySelector("[data-role]")).toBeNull();
    expect(within(echo).getByText("0.4 of the ten most frequent terms")).toBeInTheDocument();
    expect(screen.getByText(/A school with one paper cannot become a direction on its own/)).toBeInTheDocument();
    expect(document.querySelector("[data-school='Federated learning']")?.textContent).toContain("1 paper");
    expect(document.querySelector("[data-reading]")?.textContent).not.toMatch(/thin/i);
  });

  it("says No topic data when the purity is indeterminate", async () => {
    start({ noTopics: true }, completeDraft(), true);
    expect(await screen.findByText("No topic data")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "OpenAlex topics" })).toBeNull();
  });

  it("names the changed parts the engine reports, and compares nothing itself", async () => {
    const { engine } = start({}, completeDraft(), true);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    expect(document.querySelector("[data-scope-changed]")).toBeNull();
    expect(engine.calls.some((c) => c.path === RECON && c.method === "GET")).toBe(true);
  });

  it("shows the scope-changed note naming years and languages", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2025, languages: ["en", "ar"] }, base_updated_at: record.updated_at });
    render(<InceptionExplore locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-scope-changed]")).not.toBeNull());
    expect(document.querySelector("[data-scope-changed]")?.textContent).toContain("You changed your years, languages after this pool was searched.");
  });

  it("prints each concept's anchoring from the concepts route, labels suggested ones and a concept in no paper", async () => {
    start({}, completeDraft({ concepts: [{ concept: "weed detection" }, { concept: "quantum annealing" }] }), true);
    expect(await screen.findByText("weed detection: in 8 of 14 titles or abstracts")).toBeInTheDocument();
    const missing = document.querySelector("[data-concept-line='quantum annealing']") as HTMLElement;
    expect(within(missing).getByText("not in the pool")).toBeInTheDocument();
    expect(screen.queryByText(/embedded hardware ·/)).toBeNull();
    expect(screen.queryByText("Suggested from your question, not yet in your draft")).toBeNull();
  });

  it("labels the scope step's suggested concepts when the draft has none", async () => {
    start({}, completeDraft({ concepts: [] }), true);
    expect(await screen.findByText("Suggested from your question, not yet in your draft")).toBeInTheDocument();
  });

  it("warns before refreshing a pool a direction is bound on, and sends nothing until Search again", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("POST", `${RECON}/bind`, { direction: "weed detection", accept_thin_pool: false, base_updated_at: record.updated_at });
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool" }));
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByRole("button", { name: "Keep the current pool" })).toHaveFocus();
    expect(posts(set.engine, "/probe")).toHaveLength(1);
    fireEvent.click(within(dialog).getByRole("button", { name: "Search again" }));
    await waitFor(() => expect(posts(set.engine, "/probe")).toHaveLength(2));
    expect(posts(set.engine, "/probe")[1].body).toEqual({ refresh: true, semantic: false, databases: ALL, query: "on-device weed detection" });
  });

  it("re-attaches to a search that is already running", async () => {
    const set = setUp({ draft: completeDraft() });
    const started = set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false }).body as { job: { job_id: string } };
    set.engine.refuseNext(`POST ${RECON}/probe`, { status: 409, body: { detail: { code: "RECON_JOB_ACTIVE", message: "running", details: { job: { job_id: started.job.job_id, state: "running" } } } } });
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool" }));
    expect(await screen.findByRole("heading", { name: "A search for this draft is already running" })).toBeInTheDocument();
    await waitFor(() => expect(set.engine.calls.some((c) => c.path === `${RECON}/jobs/${started.job.job_id}/events`)).toBe(true));
  });

  it("keeps Arabic sentences in the page direction and isolates only their values left to right", async () => {
    setUp({ draft: completeDraft(), recon: {} }).engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    render(<InceptionExplore locale="ar" />);
    await waitFor(() => expect(document.querySelector("[data-pool-meta]")).not.toBeNull());
    const meta = document.querySelector("[data-pool-meta]") as HTMLElement;
    expect(meta.closest("[dir='ltr']")).toBeNull();
    const sentence = meta.firstElementChild as HTMLElement;
    expect(sentence).not.toHaveAttribute("dir");
    const values = [...sentence.querySelectorAll("[data-ltr-value]")];
    expect(values.every((v) => v.getAttribute("dir") === "ltr")).toBe(true);
    expect(values.map((v) => v.textContent)).toContain("en");
    expect(sentence.textContent).toMatch(/^جُلبت في /);
    // The latest-search line is a sentence; only its date is LTR.
    const latest = document.querySelector("[data-databases] p") as HTMLElement;
    expect(latest).not.toHaveAttribute("dir");
    expect(latest.textContent).toMatch(/^آخر بحث، /);
    expect(latest.querySelectorAll("[dir='ltr']")).toHaveLength(1);
    // No tile sentence carries dir="ltr"; the DOIs in the papers table do.
    for (const tile of document.querySelectorAll("[data-tile] p")) expect(tile).not.toHaveAttribute("dir", "ltr");
    const doi = document.querySelector("[data-doi]") as HTMLElement;
    expect(doi.querySelector("[dir='ltr']")?.textContent).toBe(doi.getAttribute("data-doi"));
  });
});

/** M10a (decided 2026-11-14, item 1a): the query sent and the databases asked are probe parameters, never draft fields. */
describe("inception.explore query and databases", () => {
  const field = () => screen.getByRole("textbox", { name: "Query sent to the databases" }) as HTMLInputElement;
  const pickerRows = () => [...document.querySelectorAll("[data-picker-row]")].map((r) => `${r.getAttribute("data-picker-row")}:${r.getAttribute("data-selected")}`);
  const untickAll = () => {
    for (const name of ["OpenAlex", "Semantic Scholar", "Crossref", "arXiv"]) {
      const box = screen.getByRole("checkbox", { name: `Ask ${name}` });
      if ((box as HTMLInputElement).checked) fireEvent.click(box);
    }
  };

  it("lists the four databases in the engine's order, all ticked, and names none of them in a sentence", async () => {
    start();
    await screen.findByRole("heading", { name: "Your first search" });
    expect(screen.getByRole("group", { name: "Databases to ask" })).toBeInTheDocument();
    expect(pickerRows()).toEqual(ALL.map((id) => `${id}:true`));
    for (const name of ["OpenAlex", "Semantic Scholar", "Crossref", "arXiv"]) expect(screen.getByRole("checkbox", { name: `Ask ${name}` })).toBeChecked();
    expect(screen.getByText("This sends your question to the databases you ticked and keeps up to 25 papers.")).toBeInTheDocument();
    expect(screen.queryByText(/OpenAlex, Semantic Scholar, Crossref and arXiv/)).toBeNull();
    expect(screen.getByText("The order decides which papers fill the sample of 25 first.")).toBeInTheDocument();
  });

  it("pre-fills the query with the engine's derived query, left to right in mono; Use the derived query only after an edit", async () => {
    const { engine } = start({}, completeDraft({ topic: "How does the weed detection work on a drone?" }));
    await screen.findByRole("heading", { name: "Your first search" });
    expect(field().value).toBe("weed detection work drone");
    expect(field()).toHaveAttribute("dir", "ltr");
    expect(field().className).toMatch(/font-mono/);
    expect(screen.getByText("The keywords below are sent to the databases. Your question above is not changed.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Use the derived query" })).toBeNull();
    fireEvent.change(field(), { target: { value: "weed drone" } });
    fireEvent.click(screen.getByRole("button", { name: "Use the derived query" }));
    expect(field().value).toBe("weed detection work drone");
    expect(screen.queryByRole("button", { name: "Use the derived query" })).toBeNull();
    // A probe parameter: the draft is never written.
    expect(engine.calls.some((c) => c.method === "PUT")).toBe(false);
  });

  it("leaves the field empty with the hint when the engine derives no query", async () => {
    start({}, {});
    await screen.findByRole("heading", { name: "Your first search" });
    expect(field().value).toBe("");
    // M10d (rule 1.7): the how-to sentence is part of the one hint on the field, and so its description.
    expect(field()).toHaveAccessibleDescription(/Leave empty and the engine derives a keyword query from your question./);
    expect(screen.queryByRole("button", { name: "Use the derived query" })).toBeNull();
  });

  it("sends the edited query trimmed, leaves the topic untouched, and sends no query when the field is empty", async () => {
    const { engine } = start({ outcomes: ["empty", "empty"] });
    await screen.findByRole("heading", { name: "Your first search" });
    fireEvent.change(field(), { target: { value: "  weed AND camera  " } });
    fireEvent.click(screen.getByRole("button", { name: "Search the literature" }));
    await screen.findByRole("heading", { name: "The search found no papers" });
    expect(posts(engine, "/probe")[0].body).toEqual({ refresh: false, semantic: false, databases: ALL, query: "weed AND camera" });
    expect((engine.drafts.get(SESSION)!.draft as { topic: string }).topic).toBe("on-device weed detection");
    expect(screen.getByText("on-device weed detection")).toBeInTheDocument();
    fireEvent.change(field(), { target: { value: "   " } });
    fireEvent.click(screen.getByRole("button", { name: "Search the literature" }));
    await waitFor(() => expect(posts(engine, "/probe")).toHaveLength(2));
    expect(posts(engine, "/probe")[1].body).toEqual({ refresh: false, semantic: false, databases: ALL });
  });

  it("refuses a query over 2000 characters on the screen and sends nothing", async () => {
    const { engine } = start();
    await screen.findByRole("heading", { name: "Your first search" });
    fireEvent.change(field(), { target: { value: "w".repeat(2001) } });
    expect(screen.getByText("The query can have at most 2000 characters.")).toBeInTheDocument();
    const go = screen.getByRole("button", { name: "Search the literature" });
    expect(go).toBeDisabled();
    fireEvent.click(go);
    expect(posts(engine, "/probe")).toHaveLength(0);
    fireEvent.change(field(), { target: { value: "w".repeat(2000) } });
    expect(screen.queryByText("The query can have at most 2000 characters.")).toBeNull();
    expect(go).toBeEnabled();
  });

  it("prints each database's own query, left to right, on its row", async () => {
    start({}, completeDraft(), true);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    const arxiv = document.querySelector("[data-databases] [data-leg='arxiv'] [data-executed-query] [dir='ltr']") as HTMLElement;
    expect(arxiv.textContent).toBe("all:on-device AND all:weed AND all:detection");
    expect(arxiv.className).toMatch(/font-mono/);
    expect(document.querySelector("[data-databases] [data-leg='crossref'] [data-executed-query]")?.textContent).toBe("on-device weed detection");
  });

  it("disables Move up on the first row and Move down on the last, keeps focus on a moved row and announces it", async () => {
    const user = userEvent.setup();
    start();
    await screen.findByRole("heading", { name: "Your first search" });
    expect(screen.getByRole("button", { name: "Move OpenAlex up" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move arXiv down" })).toBeDisabled();
    screen.getByRole("button", { name: "Move Crossref up" }).focus();
    await user.keyboard("{Enter}");
    expect(pickerRows()).toEqual(["openalex:true", "crossref:true", "semanticscholar:true", "arxiv:true"]);
    expect(screen.getByRole("button", { name: "Move Crossref up" })).toHaveFocus();
    expect(document.querySelector("[data-picker-status]")?.textContent).toBe("Crossref moved to position 2 of 4");
    // Tab order per row: checkbox, up, down.
    screen.getByRole("checkbox", { name: "Ask Crossref" }).focus();
    await user.tab();
    expect(screen.getByRole("button", { name: "Move Crossref up" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "Move Crossref down" })).toHaveFocus();
  });

  it("says Pick at least one database when none is ticked, disables Search with that reason and sends nothing", async () => {
    const { engine } = start();
    await screen.findByRole("heading", { name: "Your first search" });
    untickAll();
    expect(screen.getByRole("alert")).toHaveTextContent("Pick at least one database.");
    const go = screen.getByRole("button", { name: "Search the literature" });
    expect(go).toBeDisabled();
    expect(go).toHaveAccessibleDescription("Pick at least one database.");
    fireEvent.click(go);
    expect(posts(engine, "/probe")).toHaveLength(0);
  });

  it("disables Refresh pool and the thin-pool semantic search with no database ticked, says why, and sends nothing", async () => {
    const { engine } = start({ outcomes: ["thin"] }, completeDraft(), true);
    await screen.findByText("Only 7 papers came back");
    untickAll();
    for (const name of ["Refresh pool", "Search again with semantic search"]) {
      const button = screen.getByRole("button", { name });
      expect(button, name).toBeDisabled();
      expect(button, name).toHaveAccessibleDescription("Pick at least one database.");
      fireEvent.click(button);
    }
    expect(posts(engine, "/probe")).toHaveLength(1);
  });

  it("disables the partial pool's Search again with no database ticked and says why", async () => {
    const { engine } = start({ outcomes: ["partial"] }, completeDraft(), true);
    const banner = (await screen.findByRole("heading", { name: "Some databases did not answer" })).closest("section") as HTMLElement;
    untickAll();
    const again = within(banner).getByRole("button", { name: "Search again" });
    expect(again).toBeDisabled();
    expect(again).toHaveAccessibleDescription("Pick at least one database.");
    fireEvent.click(again);
    expect(posts(engine, "/probe")).toHaveLength(1);
  });

  it("follows the engine's order of databases_available before the first search, and sends it", async () => {
    const order = ["crossref", "arxiv", "openalex", "semanticscholar"];
    const { engine } = start({ databasesAvailable: order });
    await screen.findByRole("heading", { name: "Your first search" });
    expect(pickerRows()).toEqual(order.map((id) => `${id}:true`));
    fireEvent.click(screen.getByRole("button", { name: "Search the literature" }));
    await waitFor(() => expect(posts(engine, "/probe")).toHaveLength(1));
    expect((posts(engine, "/probe")[0].body as { databases: string[] }).databases).toEqual(order);
  });

  it("after the question changed, pre-fills the new question's derived query, keeps the databases asked, and Refresh pool for the new scope sends it", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false, databases: ["crossref", "openalex"], query: "on-device weed detection" });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), topic: "How do drones detect weeds in real time?" }, base_updated_at: record.updated_at });
    render(<InceptionExplore locale="en" />);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    expect(document.querySelector("[data-scope-changed]")?.textContent).toContain("You changed your question after this pool was searched.");
    expect(field().value).toBe("drones detect weeds real time");
    expect(pickerRows()).toEqual(["crossref:true", "openalex:true", "semanticscholar:false", "arxiv:false"]);
    fireEvent.click(screen.getByRole("button", { name: "Refresh pool for the new scope" }));
    await waitFor(() => expect(posts(set.engine, "/probe")).toHaveLength(2));
    expect(posts(set.engine, "/probe")[1].body).toEqual({ refresh: true, semantic: false, databases: ["crossref", "openalex"], query: "drones detect weeds real time" });
  });

  it("pre-fills from the latest topic search, never from a narrower search's direction label", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false, databases: ["arxiv", "crossref"], query: "weed AND camera" });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: true, semantic: false, narrower: "weed detection" });
    render(<InceptionExplore locale="en" />);
    await screen.findByRole("heading", { name: "Pool · 10 papers" });
    expect(field().value).toBe("weed AND camera");
    expect(pickerRows()).toEqual(["arxiv:true", "crossref:true", "openalex:false", "semanticscholar:false"]);
  });

  it("shows the query field when the pool cannot be read, so Edit the query has a field to focus", async () => {
    const set = setUp({ draft: completeDraft(), refuseOnce: { [`POST ${RECON}/distill`]: { status: 500, body: { detail: { code: "DISTILL_BROKE", message: "boom" } } } } });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2025 }, base_updated_at: record.updated_at });
    set.engine.refuseNext(`POST ${RECON}/probe`, { status: 422, body: { detail: { code: "BODY_INVALID", message: "query too long", details: { errors: [] } } } });
    render(<InceptionExplore locale="en" />);
    await screen.findByRole("heading", { name: "Refused" });
    expect(screen.queryByRole("heading", { name: /^Pool ·/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Refresh pool for the new scope" }));
    await screen.findByRole("heading", { name: "That search request was not valid" });
    fireEvent.click(screen.getByRole("button", { name: "Edit the query" }));
    expect(field()).toHaveFocus();
  });

  it("sends the chosen databases in order with the query on Refresh pool", async () => {
    const { engine } = start({}, completeDraft(), true);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    fireEvent.click(screen.getByRole("checkbox", { name: "Ask Semantic Scholar" }));
    fireEvent.click(screen.getByRole("button", { name: "Move arXiv up" }));
    fireEvent.change(field(), { target: { value: "weed camera" } });
    fireEvent.click(screen.getByRole("button", { name: "Refresh pool" }));
    await waitFor(() => expect(posts(engine, "/probe")).toHaveLength(2));
    expect(posts(engine, "/probe")[1].body).toEqual({ refresh: true, semantic: false, databases: ["openalex", "arxiv", "crossref"], query: "weed camera" });
  });

  it("pre-fills the query and the picker from the latest probe on reload", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false, databases: ["arxiv", "crossref"], query: "weed AND camera" });
    render(<InceptionExplore locale="en" />);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    expect(field().value).toBe("weed AND camera");
    expect(pickerRows()).toEqual(["arxiv:true", "crossref:true", "openalex:false", "semanticscholar:false"]);
    // The edited query differs from the derived one, so the way back is offered.
    expect(screen.getByRole("button", { name: "Use the derived query" })).toBeInTheDocument();
    expect(document.querySelectorAll("[data-databases] [data-leg]")).toHaveLength(2);
  });

  it("disables the query, Use the derived query, the boxes and the move buttons while a search runs, and enables them again after it", async () => {
    const recon: ReconOptions = {};
    const set = setUp({
      draft: completeDraft(),
      recon,
      refuseOnce: {
        [`GET ${RECON}/jobs/rjob_0000000000000002/events`]: { status: 503, body: { detail: { code: "ENGINE_UNREACHABLE", message: "down" } } },
        [`GET ${RECON}/jobs/rjob_0000000000000002`]: { status: 503, body: { detail: { code: "ENGINE_UNREACHABLE", message: "down" } } },
      },
    });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false, query: "weed AND camera" });
    recon.holdStream = true;
    set.engine.handle("POST", `${RECON}/probe`, { refresh: true, semantic: false, query: "weed AND camera" });
    render(<InceptionExplore locale="en" />);
    await screen.findByText("Lost contact with the engine. The search may still be running.");
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    const group = () => screen.getByRole("group", { name: "Databases to ask" });
    const controls = () => [
      field(),
      screen.getByRole("button", { name: "Use the derived query" }),
      ...within(group()).getAllByRole("checkbox"),
      ...within(group()).getAllByRole("button", { name: /^Move / }),
    ];
    expect(field().value).toBe("weed AND camera");
    for (const control of controls()) expect(control).toBeDisabled();
    // The job ends on the next read (every two seconds); then everything is usable again.
    await waitFor(() => expect(field()).toBeEnabled(), { timeout: 6000 });
    for (const control of [field(), screen.getByRole("button", { name: "Use the derived query" }), ...within(group()).getAllByRole("checkbox")]) expect(control).toBeEnabled();
    expect(screen.getByRole("button", { name: "Move Semantic Scholar up" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Move Crossref down" })).toBeEnabled();
  }, 10000);

  it("retries an unreachable engine at start by reading the session again, sends no probe, and enables Search again", async () => {
    const set = setUp({
      draft: completeDraft(),
      refuseOnce: { [`POST ${RECON}/probe`]: { status: 503, body: { detail: { code: "ENGINE_UNREACHABLE", message: "down" } } } },
    });
    render(<InceptionExplore locale="en" />);
    const go = await screen.findByRole("button", { name: "Search the literature" });
    fireEvent.click(go);
    const card = (await screen.findByRole("heading", { name: "Engine unreachable" })).closest("[data-refusal]") as HTMLElement;
    expect(screen.getByRole("button", { name: "Search the literature" })).toBeDisabled();
    const reads = set.engine.calls.filter((c) => c.method === "GET" && c.path === RECON).length;
    fireEvent.click(within(card).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(set.engine.calls.filter((c) => c.method === "GET" && c.path === RECON).length).toBe(reads + 1));
    await waitFor(() => expect(screen.getByRole("button", { name: "Search the literature" })).toBeEnabled());
    expect(screen.queryByRole("heading", { name: "Engine unreachable" })).toBeNull();
    // The one refused attempt only: the retry sent no probe.
    expect(posts(set.engine, "/probe")).toHaveLength(1);
  });

  it("disables Refresh pool for the new scope with no database ticked and says why", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2025 }, base_updated_at: record.updated_at });
    render(<InceptionExplore locale="en" />);
    await screen.findByRole("heading", { name: "Pool · 14 papers" });
    untickAll();
    const refresh = screen.getByRole("button", { name: "Refresh pool for the new scope" });
    expect(refresh).toBeDisabled();
    expect(refresh).toHaveAccessibleDescription("Pick at least one database.");
    fireEvent.click(refresh);
    expect(posts(set.engine, "/probe")).toHaveLength(1);
  });

  it("offers no Edit the query, not even as text, for a BODY_INVALID while the query field is not on screen", async () => {
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2025 }, base_updated_at: record.updated_at });
    set.engine.refuseNext(`POST ${RECON}/probe`, { status: 422, body: { detail: { code: "BODY_INVALID", message: "query too long", details: { errors: [] } } } });
    // The pool read never answers, so neither the pool card nor the field alone is on screen.
    holdDistill();
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool for the new scope" }));
    await screen.findByRole("heading", { name: "That search request was not valid" });
    expect(screen.queryByRole("textbox", { name: "Query sent to the databases" })).toBeNull();
    expect(screen.queryByText("Edit the query")).toBeNull();
  });

  it("sends no probe from the refresh warning's Search again once no database is ticked behind it", async () => {
    // The warning traps no focus, so the picker behind it stays reachable from the keyboard.
    const set = setUp({ draft: completeDraft() });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("POST", `${RECON}/bind`, { direction: "weed detection", accept_thin_pool: false, base_updated_at: record.updated_at });
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Refresh pool" }));
    const dialog = await screen.findByRole("alertdialog");
    untickAll();
    expect(screen.getByRole("button", { name: "Refresh pool" })).toBeDisabled();
    const go = within(dialog).getByRole("button", { name: "Search again" });
    expect(go).toBeDisabled();
    expect(go).toHaveAccessibleDescription("Pick at least one database.");
    fireEvent.click(go);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(posts(set.engine, "/probe")).toHaveLength(1);
  });

  it("maps BODY_INVALID to the spec card with the code under Details; Edit the query focuses the field", async () => {
    setUp({
      draft: completeDraft(),
      refuseOnce: { [`POST ${RECON}/probe`]: { status: 422, body: { detail: { code: "BODY_INVALID", message: "refused", details: { errors: [{ loc: ["body", "query"], msg: "too long", type: "value_error" }] } } } } },
    });
    render(<InceptionExplore locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    const card = (await screen.findByRole("heading", { name: "That search request was not valid" })).closest("[data-refusal]") as HTMLElement;
    expect(within(card).getByText("The query must be 1 to 2000 characters and cannot be sent with a narrower search. Nothing was sent.")).toBeInTheDocument();
    expect(card.querySelector("details")?.textContent).toContain("BODY_INVALID");
    expect(screen.getAllByText("Edit the query")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Edit the query" }));
    expect(field()).toHaveFocus();
  });

  it("refuses a database id that is not a string as BODY_INVALID, as the engine's ProbeBody does (fake)", () => {
    const set = setUp({ draft: completeDraft() });
    const answer = set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false, databases: ["openalex", 3] });
    expect(answer.status).toBe(422);
    expect((answer.body as { detail: { code: string } }).detail.code).toBe("BODY_INVALID");
  });

  it("compares the question with the topic of the latest search, as the session records it (fake)", () => {
    const set = setUp({ draft: completeDraft(), recon: { outcomes: ["ok", "failed"] } });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const record = set.engine.drafts.get(SESSION)!;
    set.engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), topic: "drone weed detection" }, base_updated_at: record.updated_at });
    const read = () => set.engine.handle("GET", RECON, null).body as { scope_changes: string[]; session: { topic: string } };
    expect(read().scope_changes).toEqual(["topic"]);
    // A failed search still records the session's topic, so the question no longer reads as changed.
    set.engine.handle("POST", `${RECON}/probe`, { refresh: true, semantic: false });
    expect(read().session.topic).toBe("drone weed detection");
    expect(read().scope_changes).toEqual([]);
  });
});

/** Every `POST .../recon/distill` stays unanswered (the pool read never ends); other calls reach the fake. */
function holdDistill(): void {
  const inner = globalThis.fetch;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      if (url.includes("/recon/distill")) return new Promise<Response>(() => undefined);
      return inner(input, init);
    }),
  );
}
