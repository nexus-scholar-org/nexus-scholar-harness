import { cleanup, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "@/components/status-badge";
import type { WorkflowState } from "@/lib/contracts";
import { SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CATALOGS } from "@/messages";

import { ALL_WORKFLOW_STATES } from "./fixtures/presentation-fixture";

/**
 * The four-state matrix for `StatusBadge`.
 *
 * `lib/mock-project.ts` only ever uses `complete`, `active` and `waiting`, so
 * this component is driven directly by prop to cover the whole
 * `WorkflowState` union defined in `lib/contracts.ts`. Each state must be
 * distinguishable by text, not by colour alone.
 *
 * The four states are canonical tokens in the data and translated words on
 * screen (packet UI-01d, D-I18N-07), so the expected text is the catalog value
 * for the locale under test — never the token. In English the two coincide,
 * which is exactly why an English-only run cannot prove the translation happens.
 */
function badgeText(state: WorkflowState, locale: Locale): string {
  return CATALOGS[locale][`state.${state}` as "state.complete"];
}

describe("StatusBadge", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it.each(ALL_WORKFLOW_STATES)(
      `renders the %s state as its own visible text (${locale})`,
      (state: WorkflowState) => {
        render(<StatusBadge state={state} locale={locale} />);

        const badge = screen.getByText(badgeText(state, locale));
        expect(badge).toBeInTheDocument();
        expect(badge.tagName).toBe("SPAN");
        expect(badge.textContent).toBe(badgeText(state, locale));
        cleanup();
      },
    );

    it.each(ALL_WORKFLOW_STATES)(
      `does not render any other state label for %s (${locale})`,
      (state: WorkflowState) => {
        render(<StatusBadge state={state} locale={locale} />);

        const otherStates = ALL_WORKFLOW_STATES.filter((candidate) => candidate !== state);
        for (const other of otherStates) {
          expect(screen.queryByText(badgeText(other, locale))).toBeNull();
        }
        cleanup();
      },
    );
  }

  it("gives each state a distinct style set", () => {
    const classNames = ALL_WORKFLOW_STATES.map((state) => {
      const { unmount } = render(<StatusBadge state={state} locale="en" />);
      const className = screen.getByText(badgeText(state, "en")).getAttribute("class") ?? "";
      unmount();
      return className;
    });

    expect(new Set(classNames).size).toBe(ALL_WORKFLOW_STATES.length);
  });
});
