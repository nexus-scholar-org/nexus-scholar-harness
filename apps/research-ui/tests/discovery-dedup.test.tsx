import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryDedup } from "@/components/discovery-dedup";
import type { Dedup } from "@/lib/discovery-api";

import { setUp } from "./discovery-helpers";

/** 05 Duplicates (spec docs/ux/phase1-discovery/final/05-dedup.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

/** Counts that do not add up on purpose: the screen must print them as written, never recompute them. */
const ODD: Dedup = {
  shape: "discovery.dedup-v1",
  run: "run_001",
  input_records: 100,
  unique_works: 90,
  removed: 7,
  removed_rate: 0.0756,
  tiers: { identifier: 5, exact_title: 1, fuzzy_title: 4 },
  method: { title_similarity: 0.95, year_tolerance: 2, first_author: false, source: "protocol" },
  near_twins: null,
} as Dedup;

describe("discovery.dedup", () => {
  it("prints the engine's counts verbatim, even when they do not add up", async () => {
    setUp({ runs: 1, refuseOnce: { "GET /api/v1/discovery/dedup": { status: 200, body: ODD } } });
    render(<DiscoveryDedup locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "100 records became 90 works." });
    expect(document.querySelector("[data-in]")).toHaveTextContent("100");
    expect(document.querySelector("[data-out]")).toHaveTextContent("90");
    expect(document.querySelector("[data-removed]")).toHaveTextContent("7");
    expect(screen.queryByText("10")).toBeNull();
    expect(within(document.querySelector('[data-tier="identifier"]') as HTMLElement).getByText("5")).toBeInTheDocument();
    expect(within(document.querySelector('[data-tier="exact_title"]') as HTMLElement).getByText("1")).toBeInTheDocument();
    expect(within(document.querySelector('[data-tier="fuzzy_title"]') as HTMLElement).getByText("4")).toBeInTheDocument();
  });

  it("shows the share as a percentage and the written fraction under Details", async () => {
    setUp({ runs: 1, refuseOnce: { "GET /api/v1/discovery/dedup": { status: 200, body: ODD } } });
    render(<DiscoveryDedup locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "100 records became 90 works." });
    expect(document.querySelector("[data-rate]")).toHaveTextContent("7.56 %");
    const written = document.querySelector("[data-rate-written]") as HTMLElement;
    expect(written.closest("details")).not.toBeNull();
    expect(within(written).getByText("0.0756")).toBeInTheDocument();
  });

  it("says where the rules come from, protocol or default", async () => {
    setUp({ runs: 1, refuseOnce: { "GET /api/v1/discovery/dedup": { status: 200, body: ODD } } });
    const { unmount } = render(<DiscoveryDedup locale="en" />);
    expect(await screen.findByText("These values are set in the signed protocol.")).toBeInTheDocument();
    expect(screen.getByText("Title similarity at least 0.95")).toBeInTheDocument();
    expect(screen.getByText("Same first author: no")).toBeInTheDocument();
    unmount();
    vi.unstubAllGlobals();
    setUp({ runs: 1 });
    render(<DiscoveryDedup locale="en" />);
    expect(await screen.findByText("These values are the harness defaults.")).toBeInTheDocument();
  });

  it("has no merge, keep or undo control and says the pairs note", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryDedup locale="en" />);
    await screen.findByText("Records the rules did not prove to be the same work are not listed here and stay separate works.");
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryByRole("link", { name: /merge|keep|undo/i })).toBeNull();
    expect(screen.queryByRole("checkbox")).toBeNull();
  });

  it("prints Not recorded when the tiers are missing", async () => {
    setUp({ runs: 1, refuseOnce: { "GET /api/v1/discovery/dedup": { status: 200, body: { ...ODD, tiers: null } } } });
    render(<DiscoveryDedup locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "100 records became 90 works." });
    expect(screen.getAllByText("Not recorded for this deduplication")).toHaveLength(3);
  });

  it("shows DEDUP_NOT_RUN as a card with its code under Details and a link to Harvest", async () => {
    setUp();
    render(<DiscoveryDedup locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "DEDUP_NOT_RUN");
    expect(within(card.querySelector("details") as HTMLElement).getByText("DEDUP_NOT_RUN")).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: "Go to Harvest" })).toHaveAttribute("href", "/en/discovery/harvest/");
  });

  it("says which run the counts are for when the address names another", async () => {
    setUp({ runs: 2, search: "?run=run_001" });
    render(<DiscoveryDedup locale="en" />);
    expect(await screen.findByText("You are viewing run_001. Deduplication is shown for run_002 only.")).toBeInTheDocument();
    expect(screen.getByText("This is the newest deduplication, from run_002.")).toBeInTheDocument();
  });
});
