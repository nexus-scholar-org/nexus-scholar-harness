import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryHandoff } from "@/components/discovery-handoff";

import { FINGERPRINT, discoveryEngine, refuse } from "./fixtures/discovery-engine";
import { sent, setUp } from "./discovery-helpers";

/** 08 Hand-off (spec docs/ux/phase1-discovery/final/08-handoff.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

const ACCEPT = "POST /api/v1/screening/corpus/accept";

describe("discovery.handoff", () => {
  it("shows what a staged harvest hands to screening, as the engine wrote it, with no number in the headline", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Accept this corpus for screening?" });
    expect(document.querySelectorAll("[data-mix-row]")).toHaveLength(5);
    expect(within(document.querySelector('[data-mix-row="openalex"]') as HTMLElement).getByText("402 records · 35.61 %")).toBeInTheDocument();
    expect(screen.getByText("A work found in two databases is counted in both, so shares can add up to more than 100 %.")).toBeInTheDocument();
    // 1453 records in, 393 removed, 1060 works; the fake writes 84 title-only.
    expect(document.querySelector("[data-with-abstract]")).toHaveTextContent("976");
    expect(document.querySelector("[data-title-only]")).toHaveTextContent("84");
    expect(document.querySelector("[data-window]")).toHaveTextContent("6");
    expect(document.querySelector("[data-lower-bound-note]")).toHaveTextContent("Crossref: a count stopped at its cap is a lower bound. The report says so.");
    expect(screen.getByText(FINGERPRINT)).toBeInTheDocument();
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(screen.queryByText(/hydrat|blind|near.twin/i)).toBeNull();
    // The lower-bound note does not disable the gate.
    expect(screen.getByRole("button", { name: "Accept this corpus" })).toBeEnabled();
  });

  it("has one primary button", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("button", { name: "Accept this corpus" });
    const primaries = [...document.querySelectorAll("button")].filter((b) => b.className.split(/\s+/).includes("bg-brand"));
    expect(primaries).toHaveLength(1);
    expect(primaries[0]).toHaveTextContent("Accept this corpus");
  });

  it("accepts once and shows Accepted from the engine, with no way to search again", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1 });
    render(<DiscoveryHandoff locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Accept this corpus" }));
    await screen.findByRole("heading", { level: 1, name: "This corpus is accepted." });
    expect(sent(engine).filter((c) => c === ACCEPT)).toHaveLength(1);
    expect(document.querySelector("[data-artifact]")).toHaveTextContent("ART-corpus-" + "1".repeat(12));
    expect(screen.getByRole("link", { name: "Go to screening" })).toHaveAttribute("href", "/en/screening/home");
    expect(screen.queryByRole("link", { name: /Search again|Stage an export|Prepare/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Accept|Run again|Harvest/ })).toBeNull();
  });

  it("shows Accepted only when the re-read says so", async () => {
    const user = userEvent.setup();
    const staged = (discoveryEngine({ runs: 1 }).handle("GET", "/api/v1/screening/corpus", null).body);
    setUp({ runs: 1, refuseOnce: { [ACCEPT]: { status: 200, body: staged } } });
    render(<DiscoveryHandoff locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Accept this corpus" }));
    await screen.findByRole("heading", { level: 1, name: "Accept this corpus for screening?" });
    expect(screen.queryByText("This corpus is accepted.")).toBeNull();
  });

  it("refuses PROTOCOL_CHANGED_SINCE_RUN with a link to search again and freezes nothing", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, protocolChangedSinceRun: true });
    render(<DiscoveryHandoff locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Accept this corpus" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "PROTOCOL_CHANGED_SINCE_RUN");
    expect(within(card).getByRole("link", { name: "Search again" })).toHaveAttribute("href", "/en/discovery/harvest/");
    expect(within(card.querySelector("details") as HTMLElement).getByText("PROTOCOL_CHANGED_SINCE_RUN")).toBeInTheDocument();
    expect(engine.accepted).toBe(false);
    expect(screen.queryByText("This corpus is accepted.")).toBeNull();
  });

  it("re-reads after CORPUS_ALREADY_ACCEPTED and shows Accepted", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1 });
    render(<DiscoveryHandoff locale="en" />);
    const accept = await screen.findByRole("button", { name: "Accept this corpus" });
    // Another tab accepts first.
    engine.handle("POST", "/api/v1/screening/corpus/accept", null);
    await user.click(accept);
    await screen.findByRole("heading", { level: 1, name: "This corpus is accepted." });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("says there is nothing to hand off in an empty workspace", async () => {
    setUp();
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "There is nothing to hand off yet." });
    expect(screen.queryByRole("button", { name: "Accept this corpus" })).toBeNull();
  });

  it("keeps the engine's message under Details for a known refusal: ACCEPT_CORPUS_REFUSED (review 1)", async () => {
    const user = userEvent.setup();
    setUp({ runs: 1, refuseOnce: { "POST /api/v1/screening/corpus/accept": refuse(409, "ACCEPT_CORPUS_REFUSED", "the corpus has no unique study") } });
    render(<DiscoveryHandoff locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Accept this corpus" }));
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "ACCEPT_CORPUS_REFUSED");
    const details = card.querySelector("details") as HTMLElement;
    expect(within(details).getByText("the corpus has no unique study")).toBeInTheDocument();
  });

  it("does not offer the accept while a harvest runs (review follow-up)", async () => {
    setUp({ runs: 1, activeJob: true });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByText("A harvest is running. Accept after it ends, so the corpus you freeze is the one you read here.");
    expect(screen.getByRole("button", { name: "Accept this corpus" })).toBeDisabled();
  });
});
