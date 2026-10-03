import { cleanup, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WorkflowTimeline } from "@/components/workflow-timeline";
import type { WorkflowState } from "@/lib/contracts";
import { SUPPORTED_LOCALES, formatNumber, type Locale } from "@/i18n";
import { CATALOGS } from "@/messages";

import { ALL_STATES_STAGES, STAGE_WITH_COUNT, STAGE_WITHOUT_COUNT } from "./fixtures/presentation-fixture";

/**
 * The stage state is a canonical token and a translated word (packet UI-01d,
 * D-I18N-07); the stage label and description are the fixture's own text and
 * stay byte for byte inside `<bdi>`. So the expected visible state is the
 * catalog value, and the expected label is the raw fixture string — and in
 * English those two are equal for the label only, never for the state.
 */
function stateText(state: WorkflowState, locale: Locale): string {
  return CATALOGS[locale][`state.${state}` as "state.complete"];
}

/** The count as this locale's digits actually spell it (F01/F03). */
function countText(count: number, locale: Locale): string {
  return formatNumber(locale, count);
}

describe("WorkflowTimeline", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`exposes the stage sequence as a named list (${locale})`, () => {
      render(<WorkflowTimeline stages={ALL_STATES_STAGES} locale={locale} />);

      expect(
        screen.getByRole("list", { name: CATALOGS[locale]["workflow.listLabel"] }),
      ).toBeInTheDocument();
      expect(screen.getAllByRole("listitem")).toHaveLength(ALL_STATES_STAGES.length);
      cleanup();
    });

    it(`renders each stage description and its own state text inside that stage (${locale})`, () => {
      render(<WorkflowTimeline stages={ALL_STATES_STAGES} locale={locale} />);

      for (const stage of ALL_STATES_STAGES) {
        const item = screen.getByRole("heading", { name: stage.label }).closest("li");
        expect(item).not.toBeNull();

        // Scoped to the item, so this also proves the badge belongs to this stage
        // and not to a neighbour that happens to share a state.
        const scoped = within(item as HTMLElement);
        expect(scoped.getByText(stage.description, { selector: "bdi" })).toBeInTheDocument();
        expect(scoped.getByText(stateText(stage.state, locale))).toBeInTheDocument();
      }
      cleanup();
    });

    it(`renders the count in the locale's own digits when the stage defines one (${locale})`, () => {
      render(<WorkflowTimeline stages={[STAGE_WITH_COUNT]} locale={locale} />);

      expect(screen.getByText(countText(STAGE_WITH_COUNT.count as number, locale))).toBeInTheDocument();
      cleanup();
    });

    it(`renders no number when the stage omits count, while still rendering the stage (${locale})`, () => {
      const { container } = render(<WorkflowTimeline stages={[STAGE_WITHOUT_COUNT]} locale={locale} />);

      const item = screen.getByRole("listitem");
      expect(within(item).getByRole("heading", { name: STAGE_WITHOUT_COUNT.label })).toBeInTheDocument();
      // The stage is present; only the number is absent. Checked against the
      // locale's own spelling of 143, because "143" is not what `ar` renders.
      expect(container.textContent).not.toContain(countText(143, locale));
      expect(screen.queryByText(countText(143, locale))).toBeNull();
      cleanup();
    });

    it(`places each count inside its own stage item (${locale})`, () => {
      render(<WorkflowTimeline stages={ALL_STATES_STAGES} locale={locale} />);

      const counted = ALL_STATES_STAGES.filter((stage) => stage.count !== undefined);
      expect(counted.length).toBeGreaterThan(0);

      for (const stage of counted) {
        const item = screen.getByRole("heading", { name: stage.label }).closest("li");
        expect(item).not.toBeNull();
        expect(
          within(item as HTMLElement).getByText(countText(stage.count as number, locale)),
        ).toBeInTheDocument();
      }
      cleanup();
    });
  }

  it("renders every stage label from the fixture, in the given order", () => {
    render(<WorkflowTimeline stages={ALL_STATES_STAGES} locale="en" />);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels).toEqual(ALL_STATES_STAGES.map((stage) => stage.label));
  });
});