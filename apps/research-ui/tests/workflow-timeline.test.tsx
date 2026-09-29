import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WorkflowTimeline } from "@/components/workflow-timeline";

import { ALL_STATES_STAGES, STAGE_WITH_COUNT, STAGE_WITHOUT_COUNT } from "./fixtures/presentation-fixture";

describe("WorkflowTimeline", () => {
  it("exposes the stage sequence as a named list", () => {
    render(<WorkflowTimeline stages={ALL_STATES_STAGES} />);

    expect(screen.getByRole("list", { name: "Research workflow" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(ALL_STATES_STAGES.length);
  });

  it("renders every stage label from the fixture, in the given order", () => {
    render(<WorkflowTimeline stages={ALL_STATES_STAGES} />);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels).toEqual(ALL_STATES_STAGES.map((stage) => stage.label));
  });

  it("renders each stage description and its own state text inside that stage", () => {
    render(<WorkflowTimeline stages={ALL_STATES_STAGES} />);

    for (const stage of ALL_STATES_STAGES) {
      const item = screen.getByRole("heading", { name: stage.label }).closest("li");
      expect(item).not.toBeNull();

      // Scoped to the item, so this also proves the badge belongs to this stage
      // and not to a neighbour that happens to share a state.
      const scoped = within(item as HTMLElement);
      expect(scoped.getByText(stage.description)).toBeInTheDocument();
      expect(scoped.getByText(stage.state)).toBeInTheDocument();
    }
  });

  it("renders the count when the stage defines one", () => {
    render(<WorkflowTimeline stages={[STAGE_WITH_COUNT]} />);

    expect(screen.getByText("143")).toBeInTheDocument();
  });

  it("renders no number when the stage omits count, while still rendering the stage", () => {
    const { container } = render(<WorkflowTimeline stages={[STAGE_WITHOUT_COUNT]} />);

    const item = screen.getByRole("listitem");
    expect(within(item).getByRole("heading", { name: STAGE_WITHOUT_COUNT.label })).toBeInTheDocument();
    // The stage is present; only the number is absent.
    expect(container.textContent).not.toContain("143");
    expect(screen.queryByText("143")).toBeNull();
  });

  it("places each count inside its own stage item", () => {
    render(<WorkflowTimeline stages={ALL_STATES_STAGES} />);

    const counted = ALL_STATES_STAGES.filter((stage) => stage.count !== undefined);
    expect(counted.length).toBeGreaterThan(0);

    for (const stage of counted) {
      const item = screen.getByRole("heading", { name: stage.label }).closest("li");
      expect(item).not.toBeNull();
      expect(within(item as HTMLElement).getByText(String(stage.count))).toBeInTheDocument();
    }
  });
});
