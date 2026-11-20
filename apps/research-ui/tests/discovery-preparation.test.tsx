import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryHandoff } from "@/components/discovery-handoff";
import { DiscoveryHarvest } from "@/components/discovery-harvest";
import { discoveryT } from "@/lib/discovery-copy";
import { localStamp } from "@/lib/local-time";
import { stateCopy } from "@/lib/screening-states";

import { sent, setUp } from "./discovery-helpers";

/**
 * M3i-harvest-robustness over the stateful fake: the steps after a search
 * (duplicates, abstracts, checks) are named, and a harvest whose steps failed,
 * were stopped or never ended says so on Harvest and on the Hand-off, where
 * before the first read "finished" and the second "nothing to hand off".
 * Specs: docs/ux/phase1-discovery/final/03-harvest.md and 08-handoff.md (amended 2026-11-17).
 */

afterEach(() => {
  vi.unstubAllGlobals();
});

const FINISH = "Finish preparing this corpus";
const PREPARE = "POST /api/v1/discovery/runs/run_001/prepare";
const SEARCH = "POST /api/v1/discovery/runs";

/** The preparation card sits with the run's detail, which is read after the runs list. */
async function preparationCard(): Promise<HTMLElement> {
  return waitFor(() => {
    const card = document.querySelector("[data-preparation]");
    expect(card).not.toBeNull();
    return card as HTMLElement;
  });
}

describe("discovery.harvest: the steps after the search (M3i)", () => {
  it("says a harvest whose checks failed is not prepared, and finishes it without a new search", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, preparation: "failed" });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The search finished, but preparing the corpus failed." });
    expect(screen.queryByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." })).toBeNull();

    const card = await preparationCard();
    expect(card).toHaveAttribute("data-preparation", "failed");
    expect(card).toHaveAttribute("data-preparation-stage", "verification");
    expect(within(card).getByText("Preparation failed")).toBeInTheDocument();
    expect(within(card).getByText(/The step “Checks” then failed, so screening has nothing to receive yet\./)).toBeInTheDocument();
    expect([...card.querySelectorAll("[data-stage-ended]")].map((li) => li.textContent)).toEqual(["Duplicates", "Abstracts"]);
    // The engine's own message, as written, under Details.
    expect(card.querySelector("[data-preparation-message]")).toHaveTextContent("RuntimeError: verifier down");
    // The records are still listed, and nothing points to the hand-off as if it were ready.
    expect(document.querySelector('[data-leg="openalex"]')).not.toBeNull();
    expect(document.querySelector("[data-next-links]")).toBeNull();
    expect(screen.queryByRole("link", { name: "Go to the hand-off" })).toBeNull();

    await user.click(within(card).getByRole("button", { name: FINISH }));
    await screen.findByRole("heading", { level: 1, name: "The harvest is finished. The corpus is not frozen yet." });
    expect(sent(engine)).toContain(PREPARE);
    expect(sent(engine)).not.toContain(SEARCH);
    expect(document.querySelector("[data-preparation]")).toBeNull();
    expect(screen.getByRole("link", { name: "Go to the hand-off" })).toBeInTheDocument();
  });

  it("a job that fails after its search ends on the preparation card, not as a failed search", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ preparation: "failed", preparationStage: "hydration" });
    render(<DiscoveryHarvest locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { level: 1, name: "The search finished, but preparing the corpus failed." });
    expect(screen.queryByRole("heading", { name: "The harvest did not finish" })).toBeNull();
    expect(document.querySelector('[data-refusal="DISCOVERY_FAILED"]')).toBeNull();
    const card = await preparationCard();
    expect(within(card).getByText(/The step “Abstracts” then failed/)).toBeInTheDocument();
    expect(sent(engine).filter((c) => c === SEARCH)).toHaveLength(1);
  });

  it("after a restart (no job in memory) a run made by an earlier version reads as unfinished, stage unknown", async () => {
    setUp({ runs: 1, preparation: "interrupted", legacyRun: true });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The search finished, but the corpus was not prepared." });
    const card = await preparationCard();
    expect(card).toHaveAttribute("data-preparation", "interrupted");
    expect(card).toHaveAttribute("data-preparation-stage", "");
    expect(within(card).getByText(/The console may have been closed while they ran\./)).toBeInTheDocument();
    expect(card.querySelector("[data-no-marker]")).toHaveTextContent("This run was made by an earlier version, which did not record the step it stopped at.");
    expect(card.querySelector("[data-stage-ended]")).toBeNull();
    expect(within(card).getByRole("button", { name: FINISH })).toBeEnabled();
  });

  it("keeps Stop after the search; a stop there ends the run as stopped before the next step", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ holdAfterSearch: true });
    render(<DiscoveryHarvest locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Start the harvest" }));
    // The held stream closes without an end: one reconnect, then the last state with Retry.
    await screen.findByText(/Connection lost/);
    expect(screen.getByRole("heading", { level: 1, name: "The corpus is being prepared" })).toBeInTheDocument();
    expect(screen.getByText("Preparing")).toBeInTheDocument();
    expect(document.querySelector("[data-stop-late]")).toHaveTextContent("A stop now takes effect when the current step ends");
    expect(screen.queryByRole("button", { name: "Stop the harvest and keep what was fetched" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Stop after the current step" }));
    expect(sent(engine)).toContain("POST /api/v1/discovery/jobs/djob_0000000000000000/cancel");
    await user.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("heading", { level: 1, name: "You stopped the harvest before the corpus was prepared." });
    const card = await preparationCard();
    expect(card).toHaveAttribute("data-preparation", "stopped");
    expect(within(card).getByText(/You stopped before the step “Checks”/)).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: FINISH })).toBeEnabled();
  });

  it("follows a finishing job, names what it does, and reattaches to it on load", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, preparation: "failed", holdPrepare: true });
    const first = render(<DiscoveryHarvest locale="en" />);
    await user.click(await screen.findByRole("button", { name: FINISH }));
    await screen.findByText(/Connection lost/);
    expect(screen.getByRole("heading", { level: 1, name: "The corpus is being prepared" })).toBeInTheDocument();
    expect(document.querySelector("[data-preparing]")).toHaveTextContent(
      "Removing duplicates, adding missing abstracts and checking the works of run_001. No database is searched.",
    );
    expect(screen.getByRole("button", { name: "Stop after the current step" })).toBeEnabled();
    first.unmount();

    render(<DiscoveryHarvest locale="en" />);
    await screen.findByText(/Connection lost/);
    expect(screen.getByRole("heading", { level: 1, name: "The corpus is being prepared" })).toBeInTheDocument();
    expect(document.querySelector("[data-preparing]")).toHaveTextContent("run_001");
    expect(sent(engine).filter((c) => c === PREPARE)).toHaveLength(1);
  });

  it("offers no finish when the saved records cannot be read; Harvest again stays", async () => {
    setUp({ runs: 1, preparation: "interrupted", recordsMissing: true });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The search finished, but the corpus was not prepared." });
    await preparationCard();
    expect(screen.queryByRole("button", { name: FINISH })).toBeNull();
    expect(document.querySelector("[data-cannot-finish]")).toHaveTextContent("The saved records of this run cannot be read, so it cannot be finished. Harvest again.");
    expect(screen.getByRole("button", { name: "Harvest again" })).toBeInTheDocument();
  });

  it("says the corpus is already accepted, not that the records are unreadable, when exports were accepted beside it (review finding 3)", async () => {
    setUp({ runs: 1, preparation: "failed", accepted: true });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The search finished, but preparing the corpus failed." });
    const card = await preparationCard();
    expect(within(card).queryByRole("button", { name: FINISH })).toBeNull();
    expect(card.querySelector("[data-cannot-finish]")).toHaveAttribute("data-cannot-finish", "corpus_accepted");
    expect(card.querySelector("[data-cannot-finish]")).toHaveTextContent("The corpus of this workspace is already accepted, so this run stays as a record and is not prepared.");
    expect(screen.queryByText(/cannot be read/)).toBeNull();
    // A frozen corpus is never searched again: no "Harvest again" either.
    expect(screen.queryByRole("button", { name: "Harvest again" })).toBeNull();
  });

  it("shows the engine's refusal when there is nothing to finish, and Check again re-reads", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, preparation: "stopped" });
    render(<DiscoveryHarvest locale="en" />);
    const finish = await screen.findByRole("button", { name: FINISH });
    // Another window finished it in the meantime.
    engine.handle("POST", "/api/v1/discovery/runs/run_001/prepare", {});
    await user.click(finish);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveAttribute("data-state", "PREPARATION_NOT_AVAILABLE");
    await user.click(within(alert).getByRole("button", { name: "Check again" }));
    await screen.findByRole("heading", { level: 1, name: "The harvest is finished. The corpus is not frozen yet." });
  });

  it.each(["fr", "ar"] as const)("says it in %s", async (locale) => {
    const t = discoveryT(locale);
    setUp({ runs: 1, preparation: "stopped" });
    render(<DiscoveryHarvest locale={locale} />);
    await screen.findByRole("heading", { level: 1, name: t("harvest.title.prep.stopped") });
    const card = await preparationCard();
    expect(within(card).getByText(t("harvest.prep.stopped", { stage: t("harvest.stage.verification") }))).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: t("harvest.prep.finish") })).toBeEnabled();
  });
});

describe("discovery.handoff: an unfinished preparation (M3i)", () => {
  it("says the corpus is not prepared and links to the action, instead of 'nothing to hand off'", async () => {
    setUp({ runs: 1, preparation: "failed" });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." });
    expect(screen.queryByText("There is nothing to hand off yet.")).toBeNull();
    expect(document.querySelector("[data-empty]")).toBeNull();
    const pending = document.querySelector("[data-pending]") as HTMLElement;
    expect(pending).toHaveAttribute("data-pending", "failed");
    expect(pending.querySelector("[data-pending-body]")).toHaveTextContent(
      "The search of run_001 finished, but preparing its corpus failed at the step “Checks”.",
    );
    expect(within(pending).getByText("The records found are saved; nothing has to be searched again.")).toBeInTheDocument();
    expect(within(pending).getByRole("link", { name: "Finish preparing this corpus on Harvest" })).toHaveAttribute("href", "/en/discovery/harvest/?run=run_001");
    expect(screen.queryByRole("button", { name: "Accept this corpus" })).toBeNull();
    expect(document.querySelector("[data-mix-row]")).toBeNull();
  });

  it("says a run that never ended may have been closed with the console", async () => {
    setUp({ runs: 1, preparation: "interrupted", legacyRun: true });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." });
    expect(document.querySelector("[data-pending-body]")).toHaveTextContent(
      "The search of run_001 finished, but its corpus was not prepared. The console may have been closed while it ran.",
    );
  });

  it("says which step is running, then shows the corpus once the engine says it is ready", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, preparation: "stopped", holdPrepare: true });
    const started = engine.handle("POST", "/api/v1/discovery/runs/run_001/prepare", {});
    const jobId = (started.body as { job: { job_id: string } }).job.job_id;
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." });
    const pending = document.querySelector("[data-pending]") as HTMLElement;
    expect(pending).toHaveAttribute("data-pending", "running");
    expect(pending.querySelector("[data-pending-body]")).toHaveTextContent(
      "The works of run_001 are being prepared (step “Abstracts”). The hand-off opens when this ends.",
    );
    expect(within(pending).getByRole("link", { name: "Follow the harvest" })).toHaveAttribute("href", "/en/discovery/harvest/?run=run_001");

    // The researcher stops it: the hand-off then says so, with the step it stopped before.
    engine.handle("POST", `/api/v1/discovery/jobs/${jobId}/cancel`, {});
    await user.click(within(pending).getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(document.querySelector("[data-pending]")).toHaveAttribute("data-pending", "stopped"));
    expect(document.querySelector("[data-pending-body]")).toHaveTextContent("You stopped the harvest of run_001 before the step “Checks”.");
  });

  it("shows the works and the accept after the preparation is finished", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, preparation: "failed" });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The corpus is not ready to hand off yet." });
    engine.handle("POST", "/api/v1/discovery/runs/run_001/prepare", {});
    await user.click(screen.getByRole("button", { name: "Check again" }));
    await screen.findByRole("heading", { level: 1, name: "Accept this corpus for screening?" });
    expect(document.querySelectorAll("[data-mix-row]")).toHaveLength(5);
    expect(screen.getByRole("button", { name: "Accept this corpus" })).toBeEnabled();
  });

  it("keeps staged exports as the corpus when a harvest is unfinished beside them", async () => {
    setUp({ runs: 1, preparation: "failed", staged: true });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1 });
    expect(document.querySelector("[data-pending]")).toBeNull();
  });

  it.each(["fr", "ar"] as const)("says it in %s", async (locale) => {
    const t = discoveryT(locale);
    setUp({ runs: 1, preparation: "failed" });
    render(<DiscoveryHandoff locale={locale} />);
    await screen.findByRole("heading", { level: 1, name: t("handoff.pending.title") });
    expect(document.querySelector("[data-pending-body]")).toHaveTextContent(
      t("handoff.pending.failed", { run: "run_001", stage: t("harvest.stage.verification") }),
    );
    expect(screen.getByRole("link", { name: t("handoff.pending.finish") })).toBeInTheDocument();
  });
});

describe("the two M3i refusals have their own cards", () => {
  it.each(["en", "fr", "ar"] as const)("in %s", (locale) => {
    for (const code of ["PREPARATION_UNFINISHED", "PREPARATION_NOT_AVAILABLE"]) {
      const copy = stateCopy(locale, code);
      expect(copy.known).toBe(true);
      expect(copy.title.length).toBeGreaterThan(5);
      expect(copy.actionLabel.length).toBeGreaterThan(2);
    }
  });
});

describe("H-quota-hang: the checks ended before every record was checked", () => {
  const RESET = "2026-11-21T00:00:00+00:00";

  it("Harvest says which database's quota is used up, when it resets, how many records, and what to do", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, preparation: "incomplete" });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The search finished, but not every work could be checked." });
    const card = await preparationCard();
    expect(card).toHaveAttribute("data-preparation", "incomplete");
    expect(within(card).getByText("Checks unfinished")).toBeInTheDocument();
    const paused = card.querySelector('[data-paused="openalex"]');
    expect(paused).toHaveAttribute("data-resets-at", RESET);
    expect(paused).toHaveTextContent(`The OpenAlex quota is used up. It resets at ${localStamp(RESET)}.`);
    expect(card.querySelector("[data-unchecked]")).toHaveTextContent(
      "120 of 166 records were not checked. They are kept as they were found and marked as not checked; none was dropped.",
    );
    expect(card.querySelector("[data-incomplete-todo]")).toHaveTextContent(
      "After the reset, press “Finish preparing this corpus”: only those records are checked again.",
    );
    // Every step is recorded as ended: the checks ended, early.
    expect([...card.querySelectorAll("[data-stage-ended]")].map((li) => li.textContent)).toEqual(["Duplicates", "Abstracts", "Checks"]);
    expect(screen.queryByRole("link", { name: "Go to the hand-off" })).toBeNull();

    await user.click(within(card).getByRole("button", { name: FINISH }));
    await screen.findByRole("heading", { level: 1, name: "The harvest is finished. The corpus is not frozen yet." });
    expect(sent(engine)).toContain(PREPARE);
    expect(sent(engine)).not.toContain(SEARCH);
  });

  it("a stop between two records says so, with no reset to wait for", async () => {
    setUp({ runs: 1, preparation: "incomplete", incompleteReason: "stopped" });
    render(<DiscoveryHarvest locale="en" />);
    const card = await preparationCard();
    expect(card.querySelector("[data-incomplete-stopped]")).toHaveTextContent("You stopped the checks between two records.");
    expect(card.querySelector("[data-paused]")).toBeNull();
    expect(card.querySelector("[data-unchecked]")).toHaveTextContent("7 of 10 records were not checked.");
    expect(card.querySelector("[data-incomplete-todo]")).toHaveTextContent(
      "Press “Finish preparing this corpus” to check them: only those records are checked again.",
    );
  });

  it.each(["en", "fr", "ar"] as const)("the Hand-off says it in %s and points to finishing", async (locale) => {
    const t = discoveryT(locale);
    setUp({ runs: 1, preparation: "incomplete" });
    render(<DiscoveryHandoff locale={locale} />);
    await screen.findByRole("heading", { level: 1, name: t("handoff.pending.title") });
    const pending = document.querySelector("[data-pending]") as HTMLElement;
    expect(pending).toHaveAttribute("data-pending", "incomplete");
    expect(pending.querySelector("[data-pending-body]")).toHaveTextContent(
      t("handoff.pending.incomplete", { run: "run_001", unchecked: 120, records: 166 }),
    );
    expect(pending.querySelector('[data-paused="openalex"]')).toHaveTextContent(
      t("harvest.prep.incomplete.quota", { database: "OpenAlex", time: localStamp(RESET) }),
    );
    expect(pending.querySelector("[data-incomplete-todo]")).toHaveTextContent(t("harvest.prep.incomplete.afterReset"));
    expect(screen.getByRole("link", { name: t("handoff.pending.finish") })).toBeInTheDocument();
  });
});
