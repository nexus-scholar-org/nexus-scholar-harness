import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionExplore } from "@/components/inception-explore";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import type { ReconOptions } from "./fixtures/recon-engine";
import { setUp } from "./inception-helpers";

/** Spec 02 Explore (M4d) over the stateful fake of the recon routes. */

afterEach(() => vi.unstubAllGlobals());

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;

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
    await screen.findByRole("heading", { name: "Your first search" });
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

  it("sends exactly refresh and semantic, then replaces the card with the pool", async () => {
    const { engine } = start();
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "Pool · 14 papers" })).toBeInTheDocument();
    expect(posts(engine, "/probe").map((c) => c.body)).toEqual([{ refresh: false, semantic: false }]);
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
    expect(posts(engine, "/probe")[0].body).toEqual({ refresh: false, semantic: true });
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

  it("shows an empty search as POOL_EMPTY with the databases' answers", async () => {
    start({ outcomes: ["empty"] });
    fireEvent.click(await screen.findByRole("button", { name: "Search the literature" }));
    expect(await screen.findByRole("heading", { name: "The search found no papers" })).toBeInTheDocument();
    expect(document.querySelectorAll("[data-job-error='POOL_EMPTY'] [data-leg]")).toHaveLength(4);
    expect(screen.queryByRole("heading", { name: /^Pool ·/ })).toBeNull();
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
    expect(posts(set.engine, "/probe")[1].body).toEqual({ refresh: true, semantic: false });
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
});
