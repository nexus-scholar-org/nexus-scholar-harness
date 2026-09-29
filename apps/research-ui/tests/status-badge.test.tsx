import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "@/components/status-badge";
import type { WorkflowState } from "@/lib/contracts";

import { ALL_WORKFLOW_STATES } from "./fixtures/presentation-fixture";

/**
 * The four-state matrix for `StatusBadge`.
 *
 * `lib/mock-project.ts` only ever uses `complete`, `active` and `waiting`, so
 * this component is driven directly by prop to cover the whole
 * `WorkflowState` union defined in `lib/contracts.ts`. Each state must be
 * distinguishable by text, not by colour alone.
 */
describe("StatusBadge", () => {
  it.each(ALL_WORKFLOW_STATES)("renders the %s state as its own visible text", (state: WorkflowState) => {
    render(<StatusBadge state={state} />);

    const badge = screen.getByText(state);
    expect(badge).toBeInTheDocument();
    expect(badge.tagName).toBe("SPAN");
    expect(badge.textContent).toBe(state);
  });

  it.each(ALL_WORKFLOW_STATES)("does not render any other state label for %s", (state: WorkflowState) => {
    render(<StatusBadge state={state} />);

    const otherStates = ALL_WORKFLOW_STATES.filter((candidate) => candidate !== state);
    for (const other of otherStates) {
      expect(screen.queryByText(other)).toBeNull();
    }
  });

  it("gives each state a distinct style set", () => {
    const classNames = ALL_WORKFLOW_STATES.map((state) => {
      const { unmount } = render(<StatusBadge state={state} />);
      const className = screen.getByText(state).getAttribute("class") ?? "";
      unmount();
      return className;
    });

    expect(new Set(classNames).size).toBe(ALL_WORKFLOW_STATES.length);
  });
});
