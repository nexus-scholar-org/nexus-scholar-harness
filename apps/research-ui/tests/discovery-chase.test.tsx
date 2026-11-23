import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryChase } from "@/components/discovery-chase";
import { DiscoverySteps } from "@/components/discovery-frame";

import type { ChaseRun, ChaseState } from "@/lib/discovery-api";

import { discoveryEngine, refuse } from "./fixtures/discovery-engine";
import { sent, setUp } from "./discovery-helpers";

/** 09 Citation chase (spec docs/ux/phase1-discovery/final/09-chase.md, M3g) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

const START = "POST /api/v1/discovery/chase/runs";
const ACCEPT = "POST /api/v1/discovery/chase/accept";
const PUBLISHED = { runs: 1, accepted: true, published: true } as const;

describe("discovery.chase", () => {
  it("shows seeds, keys and defaults as the engine sent them and computes no count", async () => {
    setUp(PUBLISHED);
    render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Chase the citations of your included studies" });
    expect(document.querySelector("[data-seeds-count]")).toHaveTextContent("1 of 2 can be chased");
    expect(document.querySelectorAll("[data-not-chaseable-row]")).toHaveLength(1);
    expect(document.querySelector("[data-key-openalex]")).toHaveAttribute("data-key-openalex", "set");
    expect(document.querySelector("[data-key-s2]")).toHaveTextContent("Semantic Scholar: no key, slower and on a shared quota");
    expect(screen.getByLabelText("Cap per study (citing works)")).toHaveAttribute("placeholder", "500");
    expect(screen.getByLabelText("Run ceiling (new works)")).toHaveAttribute("placeholder", "5000");
    expect(document.querySelector("[data-seed-source]")).toHaveTextContent("Seeds used: Included studies.");
    // Decision: the Unclear seeds are CLI-only; no checkbox on this screen.
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Chase citations" })).toBeEnabled();
    expect(document.querySelector("[data-counts]")).toBeNull();
  });

  it("starts once with only the changed fields, then shows the engine's summary, counts and the gate", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ ...PUBLISHED, chaseCapped: true, chaseFailedLeg: { provider: "semanticscholar", direction: "backward", code: "PROVIDER_RATE_LIMITED", error: "HTTP 429" } });
    render(<DiscoveryChase locale="en" />);
    await user.click(await screen.findByLabelText("Forward and backward"));
    await user.type(screen.getByLabelText("Note for this run (optional)"), "first chase");
    await user.click(screen.getByRole("button", { name: "Chase citations" }));
    await screen.findByRole("heading", { level: 1, name: "The chase is finished. These works are new." });

    const post = engine.calls.filter((c) => `${c.method} ${c.path}` === START);
    expect(post).toHaveLength(1);
    expect(post[0].body).toEqual({ note: "first chase" });
    expect(document.querySelectorAll("[data-summary]")).toHaveLength(4);
    expect(within(document.querySelector('[data-summary="openalex|forward"]') as HTMLElement).getByText("at least 500")).toBeInTheDocument();
    expect(document.querySelector("[data-lower-bound-note]")).toHaveTextContent("lower bound");
    expect(document.querySelector("[data-failed-list]")).toHaveTextContent("Semantic Scholar, Cited by it");
    // The counts card prints the run's counts as written.
    const latest = engine.chases[0] as { counts: Record<string, number> };
    expect(document.querySelector('[data-count="raw"]')).toHaveTextContent(String(latest.counts.raw));
    expect(document.querySelector('[data-count="new"]')).toHaveTextContent(String(latest.counts.new));
    // The per-seed legs sit behind a disclosure; the in-corpus list is collapsed under the counts.
    expect(document.querySelector("[data-per-seed]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-in-corpus]")).not.toHaveAttribute("open");
    // A PARTIAL run keeps the gate.
    expect(screen.getByRole("button", { name: `Send these ${latest.counts.new} works to screening` })).toBeEnabled();
  });

  it("sends the works once and shows the round only from the engine's answer", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ ...PUBLISHED, chaseRuns: 1 });
    render(<DiscoveryChase locale="en" />);
    const gate = await screen.findByRole("button", { name: /Send these \d+ works to screening/ });
    await user.click(gate);
    await screen.findByRole("heading", { level: 1, name: "These works are with screening as round 2." });
    expect(sent(engine).filter((c) => c === ACCEPT)).toHaveLength(1);
    expect(engine.calls.find((c) => `${c.method} ${c.path}` === ACCEPT)?.body).toEqual({ chase: "chase_001" });
    expect(document.querySelector("[data-artifact]")).toHaveTextContent("ART-corpus-" + "2".repeat(12));
    expect(document.querySelector("[data-archived]")).toHaveTextContent("literature/screening_rounds/round_001/");
    expect(screen.getByRole("link", { name: "Go to screening" })).toHaveAttribute("href", "/en/screening/home");
    expect(screen.queryByRole("button", { name: /Chase again|Send these/ })).toBeNull();
  });

  it("re-reads on CHASE_ALREADY_ACCEPTED instead of showing an error", async () => {
    const user = userEvent.setup();
    setUp({ ...PUBLISHED, chaseRuns: 1, refuseOnce: { [ACCEPT]: refuse(409, "CHASE_ALREADY_ACCEPTED", "already sent") } });
    render(<DiscoveryChase locale="en" />);
    await user.click(await screen.findByRole("button", { name: /Send these \d+ works to screening/ }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it.each([
    ["PROTOCOL_CHANGED_SINCE_PUBLISH", "The protocol changed after the screening was published"],
    ["ARCHIVE_INCOMPLETE", "Archiving the old corpus stopped part way"],
    ["CHASE_STALE", "The screening changed after this chase ran."],
    ["SOMETHING_NEW", "Refused"],
  ])("shows %s above the gate with its code under Details and moves nothing", async (code, heading) => {
    const user = userEvent.setup();
    const { engine } = setUp({ ...PUBLISHED, chaseRuns: 1, refuseOnce: { [ACCEPT]: refuse(409, code, "engine says no", code === "ARCHIVE_INCOMPLETE" ? { moved: ["screening/"], not_moved: ["included.json"] } : undefined) } });
    render(<DiscoveryChase locale="en" />);
    await user.click(await screen.findByRole("button", { name: /Send these \d+ works to screening/ }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", code);
    expect(within(card).getByRole("heading", { name: heading })).toBeInTheDocument();
    expect(within(card.querySelector("details") as HTMLElement).getByText(code)).toBeInTheDocument();
    expect(engine.round).toBe(1);
    if (code === "ARCHIVE_INCOMPLETE") expect(document.querySelector("[data-archive-details]")).toHaveTextContent("not_moved");
    if (code === "PROTOCOL_CHANGED_SINCE_PUBLISH") expect(screen.getByRole("button", { name: /Send these/ })).toBeDisabled();
  });

  it("asks for the Publish screen before publication and offers no form", async () => {
    setUp({ runs: 1, accepted: true });
    render(<DiscoveryChase locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "SCREENING_NOT_PUBLISHED");
    expect(within(card).getByRole("heading", { level: 1, name: "Publish the screening first." })).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: "Go to the Publish screen" }).getAttribute("href")).toMatch(/^\/en\/screening\/publish/);
    expect(screen.queryByRole("button", { name: "Chase citations" })).toBeNull();
  });

  it("disables Start with the reason when no seed can be chased or the OpenAlex key is missing", async () => {
    setUp({ ...PUBLISHED, chaseNoSeeds: true });
    const { unmount } = render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 2, name: "No included study can be chased." });
    expect(screen.getByRole("button", { name: "Chase citations" })).toBeDisabled();
    expect(document.querySelector("[data-start-blocked]")).toHaveAttribute("data-start-blocked", "noSeeds");
    unmount();
    vi.unstubAllGlobals();

    setUp({ ...PUBLISHED, openalexKey: false });
    render(<DiscoveryChase locale="en" />);
    await screen.findByText("SCHOLAR_OPENALEX_KEY=<your key>");
    expect(screen.getByRole("button", { name: "Chase citations" })).toBeDisabled();
    expect(document.querySelector("[data-start-blocked]")).toHaveAttribute("data-start-blocked", "key");
  });

  it("follows a running chase, stops it once and shows the stopped state with no gate", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ ...PUBLISHED, activeChase: true });
    render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Chasing the citations of your included studies" });
    await waitFor(() => expect(document.querySelector('[data-leg="openalex|forward"] [data-count]')).toHaveTextContent("7 of 500"));
    expect(document.querySelector("[data-counts]")).toBeNull();
    // The fake's open stream ends without a done event: one reconnect, then the last state with Retry.
    await screen.findByText(/Connection lost/);
    await user.click(screen.getByRole("button", { name: "Stop the chase and keep what was fetched" }));
    await user.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("heading", { level: 1, name: "You stopped the chase. What was fetched is kept." });
    expect(screen.getByText("Nothing was published and nothing is sent to screening.")).toBeInTheDocument();
    expect(sent(engine).filter((c) => c.endsWith("/cancel"))).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /Send these/ })).toBeNull();
  });

  it("shows nothing-new with no gate", async () => {
    setUp({ ...PUBLISHED, chaseRuns: 1, chaseNothingNew: true });
    render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "The chase found nothing new." });
    expect(document.querySelector('[data-count="new"]')).toHaveTextContent("0");
    expect(screen.queryByRole("button", { name: /Send these/ })).toBeNull();
  });

  it("has one primary button and the gate last in focus order", async () => {
    setUp({ ...PUBLISHED, chaseRuns: 1 });
    render(<DiscoveryChase locale="en" />);
    const gate = await screen.findByRole("button", { name: /Send these \d+ works to screening/ });
    const primaries = [...document.querySelectorAll("button")].filter((b) => b.className.split(/\s+/).includes("bg-brand"));
    expect(primaries).toEqual([gate]);
    const focusables = [...document.querySelectorAll<HTMLElement>("main a, main button, a, button")].filter((el) => !el.hasAttribute("disabled"));
    const evidence = document.querySelector("[data-counts]") as HTMLElement;
    expect(evidence.compareDocumentPosition(gate) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(focusables.length).toBeGreaterThan(1);
  });
});

describe("discovery.chase 0 results (M10a)", () => {
  const FINISHED = "The chase is finished. These works are new.";
  const badge = (selector: string) => (document.querySelector(selector) as HTMLElement).querySelector("[data-role]") as HTMLElement;

  it("says 0 results for an ok leg with nothing fetched, Done for one that fetched, in the per-seed rows and the summary", async () => {
    setUp({ ...PUBLISHED, chaseRuns: 1 });
    render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 1, name: FINISHED });
    // The fake's Semantic Scholar backward leg ends ok with nothing fetched.
    const zero = badge('[data-leg="semanticscholar|backward"]');
    expect(zero).toHaveTextContent("0 results");
    expect(zero).toHaveAttribute("data-role", "unclear");
    expect(badge('[data-leg="openalex|forward"]')).toHaveTextContent("Done");
    const summary = document.querySelector('[data-summary="semanticscholar|backward"]') as HTMLElement;
    expect(within(summary).getByText("0 results")).toHaveAttribute("data-role", "unclear");
    expect(within(document.querySelector('[data-summary="openalex|backward"]') as HTMLElement).queryByText("0 results")).toBeNull();
  });

  // The engine's ChaseLeg has no `reported_total` yet: the openalex|forward leg below carries one only to
  // pin the screen's forward-compatible rule (a reported total above 0 keeps "Done"), not engine behaviour.
  it("never says 0 results for a failed or a skipped leg, or (forward-compatible, no engine total yet) a leg that reported more than 0", async () => {
    const base = discoveryEngine({ ...PUBLISHED, chaseRuns: 1 }).handle("GET", "/api/v1/discovery/chase", null).body as ChaseState;
    const latest = base.latest as ChaseRun;
    const legs = latest.legs.map((leg) =>
      leg.provider === "semanticscholar" && leg.direction === "backward"
        ? { ...leg, status: "skipped", notes: ["no Semantic Scholar id"] }
        : leg.provider === "semanticscholar" && leg.direction === "forward"
          ? { ...leg, status: "failed", fetched: 0, error_code: "PROVIDER_TIMEOUT" }
          : leg.provider === "openalex" && leg.direction === "forward"
            ? { ...leg, fetched: 0, reported_total: 42 }
            : leg,
    );
    const odd = { ...base, latest: { ...latest, legs } };
    setUp({ ...PUBLISHED, chaseRuns: 1, refuseOnce: { "GET /api/v1/discovery/chase": { status: 200, body: odd } } });
    render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 1, name: FINISHED });
    expect(badge('[data-leg="semanticscholar|backward"]')).toHaveTextContent("Skipped");
    expect(badge('[data-leg="semanticscholar|forward"]')).toHaveTextContent("Failed");
    expect(badge('[data-leg="openalex|forward"]')).toHaveTextContent("Done");
    expect(document.querySelector("[data-per-seed]")?.textContent).not.toContain("0 results");
  });

  it("says 0 results in a summary row only when every leg of the row ended ok with nothing fetched, never beside a failed or skipped leg", async () => {
    const base = discoveryEngine({ ...PUBLISHED, chaseRuns: 1 }).handle("GET", "/api/v1/discovery/chase", null).body as ChaseState;
    const latest = base.latest as ChaseRun;
    const row = { cap_hits: 0, fetched: 0, failed: 0, skipped: 0 };
    const legs_summary = [
      { ...row, provider: "openalex", direction: "forward", legs: 2, ok: 1, failed: 1 },
      { ...row, provider: "openalex", direction: "backward", legs: 2, ok: 1, skipped: 1 },
      { ...row, provider: "semanticscholar", direction: "forward", legs: 2, ok: 2 },
      { ...row, provider: "semanticscholar", direction: "backward", legs: 1, ok: 1, fetched: 4 },
    ];
    const odd = { ...base, latest: { ...latest, legs_summary } };
    setUp({ ...PUBLISHED, chaseRuns: 1, refuseOnce: { "GET /api/v1/discovery/chase": { status: 200, body: odd } } });
    render(<DiscoveryChase locale="en" />);
    await screen.findByRole("heading", { level: 1, name: FINISHED });
    const summary = (key: string) => document.querySelector(`[data-summary="${key}"]`) as HTMLElement;
    expect(within(summary("openalex|forward")).queryByText("0 results")).toBeNull();
    expect(within(summary("openalex|backward")).queryByText("0 results")).toBeNull();
    expect(within(summary("semanticscholar|forward")).getByText("0 results")).toHaveAttribute("data-role", "unclear");
    expect(within(summary("semanticscholar|backward")).queryByText("0 results")).toBeNull();
  });
});

describe("discovery.chase step and copy", () => {
  it("adds 8 Chase to the step bar only when asked", () => {
    const { unmount } = render(<DiscoverySteps locale="en" origin="" chase={false} />);
    expect(screen.queryByRole("link", { name: "8 Chase" })).toBeNull();
    unmount();
    render(<DiscoverySteps locale="en" origin="" chase current="chase" />);
    expect(screen.getByRole("link", { name: "8 Chase" })).toHaveAttribute("aria-current", "step");
    expect(screen.getByRole("link", { name: "8 Chase" })).toHaveAttribute("href", "/en/discovery/chase/");
  });
});
