import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryPlan } from "@/components/discovery-plan";
import type { Plan } from "@/lib/discovery-api";

import { discoveryEngine } from "./fixtures/discovery-engine";
import { sent, setUp } from "./discovery-helpers";

/** 01 Plan (spec docs/ux/phase1-discovery/final/01-plan.md) over the stateful fake. */

afterEach(() => {
  vi.unstubAllGlobals();
});

/** The plan the fake answers, read from a separate fake so the screen's call log stays clean. */
function enginePlan(): Plan {
  return discoveryEngine().handle("GET", "/api/v1/discovery/plan", null).body as Plan;
}

describe("discovery.plan", () => {
  it("renders one block per provider in the engine's order with the executed strings verbatim, and no approve control", async () => {
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const plan = enginePlan();
    const blocks = [...document.querySelectorAll<HTMLElement>("[data-provider]")];
    expect(blocks.map((b) => b.dataset.provider)).toEqual(plan.providers.map((p) => p.name));
    for (const p of plan.providers) {
      const block = document.querySelector(`[data-provider="${p.name}"]`) as HTMLElement;
      if (p.executed_query) expect(within(block).getByText(p.executed_query)).toBeInTheDocument();
      else expect(block.querySelector("[data-executed]")).toBeNull();
    }
    expect(within(document.querySelector('[data-provider="biorxiv"]') as HTMLElement).getByText("Off by default")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve|gate|confirm|accept|start/i })).toBeNull();
    expect(screen.queryByRole("checkbox")).toBeNull();
  });

  it("shows the protocol cap and has no override field", async () => {
    setUp();
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const cap = document.querySelector('[data-cap="protocol"]') as HTMLElement;
    expect(within(cap).getByText("500")).toBeInTheDocument();
    expect(within(cap).getByText(/Set in the protocol\./)).toBeInTheDocument();
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
    expect(screen.queryAllByRole("spinbutton")).toHaveLength(0);
    expect(screen.queryByLabelText(/cap/i)).toBeNull();
  });

  it("prints the SCHOLAR_MAILTO line and Check again re-reads the plan only", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ mailto: false });
    render(<DiscoveryPlan locale="en" />);
    const card = (await screen.findByText("SCHOLAR_MAILTO=<your email>")).closest("[data-mailto]") as HTMLElement;
    expect(within(card).getByText("Put this line in the console's environment, or in a .env file, then start the console again.")).toBeInTheDocument();
    // Let the first load's side reads settle before counting.
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/runs"));
    const before = engine.calls.length;
    engine.setMailto(true);
    await user.click(within(card).getByRole("button", { name: "Check again" }));
    await screen.findByText("Set");
    expect(document.querySelector("[data-mailto]")).toBeNull();
    expect(sent(engine).slice(before)).toEqual(["GET /api/v1/discovery/plan"]);
  });

  it("shows No preview for a selected database without a string, and an unknown status verbatim", async () => {
    const plan = enginePlan();
    const odd: Plan = {
      ...plan,
      providers: [
        { ...plan.providers[0], status: "selected", executed_query: null, request: null },
        { ...plan.providers[1], status: "translated_later" },
        ...plan.providers.slice(2),
      ],
    };
    setUp({ refuseOnce: { "GET /api/v1/discovery/plan": { status: 200, body: odd } } });
    render(<DiscoveryPlan locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "This is what each database will receive" });
    const first = document.querySelector(`[data-provider="${plan.providers[0].name}"]`) as HTMLElement;
    expect(within(first).getByText("No preview for this database.")).toBeInTheDocument();
    expect(first.querySelector("[data-executed]")).toBeNull();
    const second = document.querySelector(`[data-provider="${plan.providers[1].name}"]`) as HTMLElement;
    expect(within(second).getByText("translated_later")).toBeInTheDocument();
  });

  it.each([
    ["PROTOCOL_MISSING", "missing", "Write the protocol in inception"],
    ["PROTOCOL_INVALID", "invalid", "Open inception"],
  ] as const)("maps %s to its card with the code under Details and a link to inception", async (code, protocol, link) => {
    setUp({ protocol });
    render(<DiscoveryPlan locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", code);
    const details = card.querySelector("details") as HTMLDetailsElement;
    expect(within(details).getByText(code)).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: link })).toHaveAttribute("href", "/en/inception/");
    expect(document.querySelector("[data-provider]")).toBeNull();
  });

  it("copies all executed strings verbatim", async () => {
    const user = userEvent.setup();
    const { writeText } = setUp();
    render(<DiscoveryPlan locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Copy all executed strings" }));
    const plan = enginePlan();
    const text = (writeText.mock.calls as unknown as string[][])[0]?.[0] ?? "";
    for (const p of plan.providers) {
      if (p.executed_query) expect(text).toContain(p.executed_query);
    }
    expect(text.split("\n")).toHaveLength(plan.providers.filter((p) => p.executed_query).length);
    await screen.findByText("Copied");
  });
});
