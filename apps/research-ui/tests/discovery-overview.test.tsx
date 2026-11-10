import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryDedup } from "@/components/discovery-dedup";
import { DiscoveryOverview } from "@/components/discovery-overview";

import { setUp } from "./discovery-helpers";

/** The discovery entry and the shared step bar (spec docs/ux/phase1-discovery/final/01-plan.md, "Shared by 01–08"). */

afterEach(() => {
  vi.unstubAllGlobals();
});

const TITLE = "Where the search stands";
const step = (s: string) => document.querySelector(`a[data-step="${s}"]`) as HTMLAnchorElement;
const mark = (s: string) => step(s).querySelector("[data-mark]")?.getAttribute("data-mark") ?? null;

describe("discovery.overview", () => {
  it("marks nothing as done in a workspace without runs", async () => {
    setUp();
    render(<DiscoveryOverview locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    expect(mark("harvest")).toBeNull();
    expect(mark("handoff")).toBeNull();
    expect(document.querySelector('[data-line="harvest"]')).toHaveAttribute("data-mark", "none");
    expect(screen.getByText("No search run yet.")).toBeInTheDocument();
  });

  it("marks Harvest and Duplicates done once the engine lists a run", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryOverview locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    expect(mark("harvest")).toBe("done");
    expect(mark("dedup")).toBe("done");
    expect(mark("handoff")).toBeNull();
    expect(screen.getByText("Duplicates were removed in run_001.")).toBeInTheDocument();
  });

  it("marks the hand-off done once the corpus is accepted", async () => {
    setUp({ runs: 1, accepted: true });
    render(<DiscoveryOverview locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    expect(mark("handoff")).toBe("done");
    expect(screen.getByText("The corpus is accepted and frozen.")).toBeInTheDocument();
  });

  it("keeps ?console= on every step link and sends Import to the screening import with return=discovery", async () => {
    setUp({ search: "?console=http%3A%2F%2F127.0.0.1%3A8765" });
    render(<DiscoveryOverview locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    const links = [...document.querySelectorAll<HTMLAnchorElement>("[data-discovery-steps] a")];
    expect(links.length).toBe(9);
    for (const link of links) expect(new URL(link.getAttribute("href") ?? "", "http://ui.test").searchParams.get("console"), link.getAttribute("href") ?? "").toBe("http://127.0.0.1:8765");
    const imp = new URL(step("import").getAttribute("href") ?? "", "http://ui.test");
    expect(imp.pathname).toBe("/en/screening/import");
    expect(imp.searchParams.get("return")).toBe("discovery");
  });

  it("links Import to /en/screening/import?return=discovery without a console", async () => {
    setUp();
    render(<DiscoveryOverview locale="en" />);
    await screen.findByRole("heading", { level: 1, name: TITLE });
    expect(step("import")).toHaveAttribute("href", "/en/screening/import?return=discovery");
    expect(step("plan")).toHaveAttribute("href", "/en/discovery/plan/");
    // The entry page is no step: nothing is current.
    expect(document.querySelector('[aria-current="step"]')).toBeNull();
  });

  it("puts aria-current=step on the current step of another screen, and disables none", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryDedup locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "1453 records became 1060 works." });
    const current = [...document.querySelectorAll('[aria-current="step"]')];
    expect(current).toHaveLength(1);
    expect(current[0]).toBe(step("dedup"));
    expect(document.querySelectorAll("[data-discovery-steps] [aria-disabled], [data-discovery-steps] [disabled]")).toHaveLength(0);
  });
});
