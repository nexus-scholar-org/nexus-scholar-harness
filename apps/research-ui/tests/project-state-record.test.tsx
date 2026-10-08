import { cleanup, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OverviewPage } from "@/components/overview-page";
import { ProjectStateRecord } from "@/components/project-state-record";
import { demoEvidence, demoProject } from "@/lib/mock-project";
import {
  demoOverviewState,
  errorOverviewState,
  loadingOverviewState,
  overviewStateFixtures,
  readyOverviewStateFixtures,
} from "@/lib/mock-project-states";
import type { OverviewCountField, ProjectOverviewPhase } from "@/lib/project-state";
import {
  SUPPORTED_LOCALES,
  countKey,
  formatNumber,
  navKey,
  phaseDescriptionKey,
  phaseKey,
  translate,
  type Locale,
} from "@/i18n";
import { CATALOGS } from "@/messages";

/**
 * The project-overview state model as the route renders it (packet UI-02).
 *
 * Three claims are asserted here, each one a failure the packet names:
 *
 * 1. **The two axes never collapse.** A loading or failed read renders no
 *    phase at all — and in particular the error branch renders neither the
 *    refusal word nor any other project state, because a failed read observed
 *    nothing. The refusal fixture renders the refusal word for exactly the
 *    opposite reason: an authority refused a step.
 * 2. **Counts are never inferred.** Every fixture renders all five statistic
 *    rows; a field the fixture omits reads the translated "unknown", never `0`
 *    and never a remainder computed in the browser.
 * 3. **The chrome is translated and the fixture is not.** Phase words, labels
 *    and the continuation sentence come from the locale's catalog; `note` is
 *    fixture prose and stays byte for byte inside `<bdi>` even in Arabic.
 *
 * A fourth, quieter claim is reconciliation: the demo fixture's numbers are
 * the frozen corpus numbers `lib/mock-project.ts` already carries, so the
 * timeline and the record cannot drift into two different projects.
 */

const PHASES: readonly ProjectOverviewPhase[] = [
  "empty",
  "setup",
  "search",
  "screening",
  "extraction",
  "indexing",
  "refusal",
  "degraded",
  "ready",
];

const COUNTS: readonly OverviewCountField[] = [
  "recordsDiscovered",
  "studiesIncluded",
  "decisionsPending",
  "documentsExtracted",
  "chunksIndexed",
];

/** The frozen demonstration corpus, as `lib/mock-project.ts` declares it. */
const FROZEN_COUNTS = new Set([143, 18]);

function phaseText(phase: ProjectOverviewPhase, locale: Locale): string {
  return CATALOGS[locale][phaseKey(phase)];
}

function countText(field: OverviewCountField, locale: Locale): string {
  return CATALOGS[locale][countKey(field)];
}

/** The named region this component owns, scoped to its heading. */
function sectionOf(locale: Locale): HTMLElement {
  const heading = screen.getByRole("heading", {
    name: CATALOGS[locale]["overview.stateHeading"],
  });
  const section = heading.closest("section");
  expect(section, "the current stage must live in its own labelled section").not.toBeNull();
  return section as HTMLElement;
}

function renderRecord(state: Parameters<typeof ProjectStateRecord>[0]["state"], locale: Locale) {
  return render(<ProjectStateRecord locale={locale} state={state} />);
}

describe("record arrival", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`renders a pending read as pending, with no project state at all (${locale})`, () => {
      renderRecord(loadingOverviewState, locale);
      const section = sectionOf(locale);

      expect(within(section).getByText(CATALOGS[locale]["overview.recordLoadingLabel"])).toBeInTheDocument();
      expect(within(section).getByText(CATALOGS[locale]["overview.recordLoading"])).toBeInTheDocument();

      // No phase was observed, so no phase word may appear — the pending read
      // must not look like a project state, whichever way it is translated.
      for (const phase of PHASES) {
        expect(within(section).queryByText(phaseText(phase, locale)), locale).toBeNull();
      }
      // And with no record there is nothing to count from.
      expect(within(section).queryByText(CATALOGS[locale]["counts.heading"])).toBeNull();
      cleanup();
    });

    it(`renders a failed read as a failed read, never as a refusal (${locale})`, () => {
      renderRecord(errorOverviewState, locale);
      const section = sectionOf(locale);

      expect(within(section).getByText(CATALOGS[locale]["overview.recordErrorLabel"])).toBeInTheDocument();
      expect(within(section).getByText(CATALOGS[locale]["overview.recordError"])).toBeInTheDocument();

      // The negative path of the separation: the refusal phase and the refusal
      // fixture's prose must both be absent. The error copy itself says so in
      // words, and this is what makes those words true.
      const refusal = overviewStateFixtures["refusal"];
      const refusalNote = refusal?.record === "ready" ? refusal.note : undefined;
      expect(refusalNote, "the refusal fixture must carry a note").toBeTruthy();
      expect(within(section).queryByText(phaseText("refusal", locale))).toBeNull();
      expect(within(section).queryByText(refusalNote as string)).toBeNull();
      for (const phase of PHASES) {
        expect(within(section).queryByText(phaseText(phase, locale)), locale).toBeNull();
      }
      expect(within(section).queryByText(CATALOGS[locale]["counts.heading"])).toBeNull();
      cleanup();
    });
  }
});

describe("ready record — state matrix", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`renders every phase word, its description, and all five statistic rows (${locale})`, () => {
      expect(readyOverviewStateFixtures).toHaveLength(PHASES.length);

      for (const state of readyOverviewStateFixtures) {
        renderRecord(state, locale);
        const section = sectionOf(locale);

        expect(within(section).getByText(phaseText(state.phase, locale)), state.phase).toBeInTheDocument();
        expect(
          within(section).getByText(CATALOGS[locale][phaseDescriptionKey(state.phase)]),
          state.phase,
        ).toBeInTheDocument();
        expect(within(section).getByText(CATALOGS[locale]["counts.heading"])).toBeInTheDocument();

        // Every statistic has a row, in every state — including the ones with
        // no number. The row set is constant; only the value cell varies.
        for (const field of COUNTS) {
          expect(within(section).getByText(countText(field, locale)), `${state.phase}/${field}`).toBeInTheDocument();
        }
        cleanup();
      }
    });
  }
});

describe("counts are never inferred", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`renders an absent statistic as unknown, never as zero (${locale})`, () => {
      // The empty state declares no counts at all, so all five rows must still
      // exist and every value must be the unknown word.
      renderRecord(overviewStateFixtures["empty"], locale);
      const section = sectionOf(locale);
      const unknown = CATALOGS[locale]["counts.unknown"];

      for (const field of COUNTS) {
        const label = within(section).getByText(countText(field, locale));
        const row = label.closest("div");
        expect(row, `${field} must render as its own row`).not.toBeNull();
        const value = within(row as HTMLElement).getByText(unknown);
        expect(value, `${field} must read unknown rather than be filled in`).toBeInTheDocument();
        // Zero is the specific fabrication the packet forbids: it would read
        // as "we counted and found none", which nobody counted.
        expect(within(row as HTMLElement).queryByText(formatNumber(locale, 0))).toBeNull();
        expect(within(row as HTMLElement).queryByText("0")).toBeNull();
      }
      cleanup();
    });

    it(`renders a carried statistic as a number and leaves the rest unknown (${locale})`, () => {
      renderRecord(overviewStateFixtures["search"], locale);
      const section = sectionOf(locale);
      const unknown = CATALOGS[locale]["counts.unknown"];

      const discovered = within(section).getByText(formatNumber(locale, 143));
      expect(discovered.closest("div")).toContainElement(
        within(section).getByText(countText("recordsDiscovered", locale)),
      );

      for (const field of COUNTS.filter((candidate) => candidate !== "recordsDiscovered")) {
        const label = within(section).getByText(countText(field, locale));
        expect(within(label.closest("div") as HTMLElement).getByText(unknown), field).toBeInTheDocument();
      }
      cleanup();
    });
  }

  it("renders every fixture's every statistic as a number or the unknown word, never a third option", () => {
    // The uniform claim behind the two focused tests above: across all nine
    // phases and all three locales, each of the five rows holds either the
    // fixture's own number (locale-formatted) or the translated unknown — and
    // an absent field still never reads zero. This is the packet's negative
    // case exercised everywhere rather than at two representative states.
    for (const locale of SUPPORTED_LOCALES) {
      for (const state of readyOverviewStateFixtures) {
        renderRecord(state, locale);
        const section = sectionOf(locale);

        for (const field of COUNTS) {
          const label = within(section).getByText(countText(field, locale));
          const row = label.closest("div");
          expect(row, `${state.phase}/${field} must render as its own row`).not.toBeNull();

          const value = state.counts[field];
          const expected =
            value !== undefined ? formatNumber(locale, value) : CATALOGS[locale]["counts.unknown"];
          expect(
            within(row as HTMLElement).getByText(expected),
            `${locale} / ${state.phase} / ${field}`,
          ).toBeInTheDocument();
          if (value === undefined) {
            expect(
              within(row as HTMLElement).queryByText(formatNumber(locale, 0)),
              `${locale} / ${state.phase} / ${field} must not read zero`,
            ).toBeNull();
          }
        }
        cleanup();
      }
    }
  });

  it("copies every fixture count from the frozen corpus, computing nothing", () => {
    // The rule the fixtures document for themselves: a count is either one of
    // the frozen demonstration numbers or absent. A third number would mean
    // something derived this file, which is the boundary the UI may not cross.
    for (const [name, state] of Object.entries(overviewStateFixtures)) {
      if (state.record !== "ready") continue;
      for (const field of COUNTS) {
        const value = state.counts[field];
        if (value === undefined) continue;
        expect(FROZEN_COUNTS.has(value), `${name}.${field} = ${value} is not a frozen corpus number`).toBe(true);
      }
    }
  });
});

describe("reconciliation with the frozen demonstration project", () => {
  it("mirrors the stage counts the timeline already renders", () => {
    const stageCount = (id: string): number | undefined =>
      demoProject.stages.find((stage) => stage.id === id)?.count;

    expect(demoOverviewState.counts.recordsDiscovered).toBe(stageCount("search"));
    expect(demoOverviewState.counts.studiesIncluded).toBe(stageCount("screening"));
    expect(demoOverviewState.counts.documentsExtracted).toBe(stageCount("full-text"));
  });

  it("matches the workflow the frozen project is actually in", () => {
    // The record says `ready`: corpus assembled, report not started. That is
    // exactly what the fixture says with its synthesis stage still `waiting` —
    // if the timeline moved on, this fixture would have to move with it.
    const synthesis = demoProject.stages.find((stage) => stage.id === "synthesis");
    expect(synthesis?.state).toBe("waiting");
    expect(demoOverviewState.phase).toBe("ready");
  });

  it("renders those numbers on the route", () => {
    render(<OverviewPage locale="en" />);
    const section = sectionOf("en");

    expect(within(section).getByText(formatNumber("en", 143))).toBeInTheDocument();
    // 18 appears twice on purpose: included studies and extracted documents are
    // two different statistics that happen to share the frozen number.
    expect(within(section).getAllByText(formatNumber("en", 18))).toHaveLength(2);
    // And exactly two rows still read unknown: pending decisions and indexed
    // passages are what this fixture does not carry, so those two are the only
    // ones the record leaves for the reader to see as unknown.
    expect(within(section).getAllByText(CATALOGS.en["counts.unknown"])).toHaveLength(2);
  });
});

describe("fixture prose stays byte for byte", () => {
  it("keeps a note isolated inside bdi, untranslated, in a right-to-left document", () => {
    const state = overviewStateFixtures["refusal"];
    if (state?.record !== "ready" || !state.note) {
      throw new Error("the refusal fixture must carry a note");
    }

    renderRecord(state, "ar");
    const section = sectionOf("ar");

    // The chrome around it is Arabic; the record's own sentence is not.
    expect(within(section).getByText(phaseText("refusal", "ar"))).toBeInTheDocument();
    expect(within(section).getByText(state.note, { selector: "bdi" })).toBeInTheDocument();
    const bdi = within(section).getByText((content) => content === state.note);
    expect(bdi.tagName.toLowerCase()).toBe("bdi");
    expect(bdi.textContent).toBe(state.note);
  });

  it("keeps every fixture note byte-identical in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const state of readyOverviewStateFixtures) {
        if (!state.note) continue;
        renderRecord(state, locale);
        const section = sectionOf(locale);
        expect(
          within(section).getByText(state.note, { selector: "bdi" }),
          `${locale} / ${state.phase}`,
        ).toBeInTheDocument();
        cleanup();
      }
    }
  });
});

describe("the continuation surface is named, never linked", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`renders the destination as translated text plus the availability tag (${locale})`, () => {
      renderRecord(overviewStateFixtures["search"], locale);
      const section = sectionOf(locale);

      const destination = translate(locale, navKey("screening"));
      expect(section.textContent).toContain(
        translate(locale, "overview.nextDestination", { destination }),
      );
      expect(within(section).getByText(CATALOGS[locale]["nav.unavailable"])).toBeInTheDocument();

      // No route exists yet for screening/evidence/audit, so the record must
      // offer no link and no focusable element at all: a destination the
      // keyboard can reach but the router cannot serve is the dead link the
      // shell's navigation gate forbids.
      expect(section.querySelectorAll("a")).toHaveLength(0);
      expect(
        section.querySelectorAll("button, input, select, textarea, [tabindex]"),
      ).toHaveLength(0);
      cleanup();
    });
  }

  it("names no destination when the fixture declares none", () => {
    renderRecord(overviewStateFixtures["empty"], "en");
    const section = sectionOf("en");

    expect(section.textContent).not.toContain(CATALOGS.en["nav.unavailable"]);
    expect(within(section).queryByText(CATALOGS.en["nav.unavailable"])).toBeNull();
  });
});

describe("fixture inventory", () => {
  it("ships the two arrival states and the nine phases, once each", () => {
    expect(Object.keys(overviewStateFixtures)).toHaveLength(11);
    expect(loadingOverviewState.record).toBe("loading");
    expect(errorOverviewState.record).toBe("error");

    const phases = readyOverviewStateFixtures.map((state) => state.phase);
    expect(new Set(phases).size).toBe(PHASES.length);
    for (const phase of PHASES) {
      expect(phases).toContain(phase);
    }
    for (const state of readyOverviewStateFixtures) {
      expect(state.record).toBe("ready");
      expect(state.counts, state.phase).toBeDefined();
    }
  });
});

describe("the route", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`renders the current stage as one named region at the second heading level (${locale})`, () => {
      render(<OverviewPage locale={locale} />);
      const section = sectionOf(locale);

      // One region, named by its heading — the same contract the workflow and
      // evidence sections already keep.
      expect(
        screen.getByRole("region", { name: CATALOGS[locale]["overview.stateHeading"] }),
      ).toBe(section);

      // The record adds no heading beyond its own level-2, so the workflow's
      // level-3 stage headings keep their place in the outline: stage labels
      // remain the first thing a heading list meets after this section.
      const headings = within(section).getAllByRole("heading");
      expect(headings).toHaveLength(1);
      expect(headings[0]).toHaveAttribute("id", "project-state-title");

      // And it adds no list: the route's listitem count stays exactly the six
      // stages plus the five evidence nodes.
      expect(within(section).queryAllByRole("listitem")).toHaveLength(0);
      cleanup();
    });
  }

  it("leaves the workflow timeline and evidence chain untouched", () => {
    render(<OverviewPage locale="en" />);

    expect(screen.getByRole("list", { name: "Research workflow" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(demoProject.stages.length + demoEvidence.length);
  });
});
