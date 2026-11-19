import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryPlan } from "@/components/discovery-plan";
import { DiscoveryProposals } from "@/components/discovery-proposals";

import { sent, setUp } from "./discovery-helpers";

/** M10c D5: an assistant's suggested changes to the protocol's search, as cards on Discovery Plan. */

afterEach(() => {
  vi.unstubAllGlobals();
});

const SYN = { proposal_id: "prop_0123456789ab", field: "core_concepts[weed detection].synonyms", op: "add" as const, value: "UAV", why: "Three seeds say UAV." };
const YEAR = { proposal_id: "prop_ba9876543210", field: "start_year", op: "replace" as const, value: 2015 };

function cards(): HTMLElement[] {
  return [...document.querySelectorAll<HTMLElement>("[data-plan-proposal]")];
}

describe("discovery.plan proposals", () => {
  it("shows nothing when the workspace has no suggestion", async () => {
    const { engine } = setUp();
    render(<DiscoveryProposals locale="en" origin="" />);
    await waitFor(() => expect(sent(engine)).toContain("GET /api/v1/discovery/proposals"));
    expect(document.querySelector("[data-plan-proposals]")).toBeNull();
  });

  it("names the assistant and its model, says what would change, and applies only on the researcher's click", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ workspaceProposals: [SYN, YEAR] });
    render(<DiscoveryPlan locale="en" />);
    const heading = await screen.findByRole("heading", { name: "Suggested changes to the search · 2" });
    const section = heading.closest("section") as HTMLElement;
    expect([...section.querySelectorAll('[data-proposal-source="agent"]')].map((e) => e.textContent)).toEqual([
      "Suggested by an assistant (claude-opus-5-5)",
      "Suggested by an assistant (claude-opus-5-5)",
    ]);
    const first = cards()[0];
    expect(first.querySelector("[data-what]")?.textContent).toBe("Add UAV to Synonyms of weed detection");
    expect(within(first).getByText("Three seeds say UAV.")).toBeInTheDocument();
    expect(sent(engine).filter((c) => c.startsWith("POST"))).toEqual([]);

    await user.click(within(first).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(sent(engine)).toContain("POST /api/v1/discovery/proposals/prop_0123456789ab/apply"));
    // The fingerprint moved: the other suggestion is out of date and offers only Dismiss; the plan is read again.
    await waitFor(() => expect(cards().map((c) => c.dataset.status)).toEqual(["stale"]));
    const stale = cards()[0];
    expect(within(stale).getByText("The protocol changed after the suggestion was made.")).toBeInTheDocument();
    expect(within(stale).queryByRole("button", { name: "Apply" })).toBeNull();
    expect(within(stale).getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    expect(sent(engine).filter((c) => c.startsWith("GET /api/v1/discovery/plan")).length).toBeGreaterThan(1);
  });

  it("says why an Apply that would change more than the search wrote nothing", async () => {
    const user = userEvent.setup();
    setUp({ workspaceProposals: [SYN], amendmentRefusal: { status: 422, code: "PROTOCOL_AMENDMENT_REFUSED", details: { reason: "outside_search", paths: ["metadata.title"] } } });
    render(<DiscoveryProposals locale="en" origin="" />);
    await user.click(await screen.findByRole("button", { name: "Apply" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Applying this would change more than the search, so nothing was written.");
    expect(cards().map((c) => c.dataset.status)).toEqual(["open"]);
  });

  it("disables Apply once the corpus is accepted and keeps Reject", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ workspaceProposals: [SYN], accepted: true });
    render(<DiscoveryProposals locale="en" origin="" />);
    expect(await screen.findByText("The corpus is accepted, so the protocol's search is no longer changed here.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Reject" }));
    await waitFor(() => expect(sent(engine)).toContain("POST /api/v1/discovery/proposals/prop_0123456789ab/reject"));
    await waitFor(() => expect(document.querySelector("[data-plan-proposals]")).toBeNull());
  });

  it("puts the assistant's words and values in bidi isolation in Arabic", async () => {
    setUp({ workspaceProposals: [SYN] });
    render(<DiscoveryProposals locale="ar" origin="" />);
    await screen.findByRole("heading", { name: /تعديلات مقترحة على البحث/ });
    const card = cards()[0];
    expect(card.querySelector('[data-value][dir="auto"]')?.textContent).toBe("UAV");
    expect(card.querySelector('bdi[dir="ltr"]')?.textContent).toBe("claude-opus-5-5");
  });
});
