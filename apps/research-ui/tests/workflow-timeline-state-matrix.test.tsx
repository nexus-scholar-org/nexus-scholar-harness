import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WorkflowTimeline } from "@/components/workflow-timeline";
import type { WorkflowStage, WorkflowState } from "@/lib/contracts";
import { demoProject } from "@/lib/mock-project";
import { SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CATALOGS, type MessageKey } from "@/messages";

import { ALL_STATES_STAGES } from "./fixtures/presentation-fixture";

/**
 * The packet UI-03 state matrix: four states × three locales, on the row that
 * renders them.
 *
 * Packet UI-03's deliverable is "an accessible stage sequence showing complete,
 * active, waiting, and refused states with text **and icons**, not colour
 * alone", its negative cases are "no claim that a future stage is complete" and
 * "refused is distinct from failed infrastructure", and its gate is a
 * "state matrix test and narrow-width visual check". The narrow-width half of
 * that gate lives in `tests-browser/workflow-timeline-narrow.spec.ts`; this file
 * is the matrix half, and it is deliberately *not* a copy of
 * `tests/workflow-timeline.test.tsx` — that file stays byte-identical as the
 * evidence that the existing assertions still hold against the same fixture.
 *
 * Three properties are load-bearing and each is asserted rather than assumed:
 *
 * 1. **The icon accompanies, never replaces (N3).** Every row carries exactly
 *    one `svg[data-stage-state-icon]` *and* the stamp word, scoped to that
 *    row's `<li>`. The icon is `aria-hidden`, carries no `role`, no `title`,
 *    and no `aria-label`, so it adds a shape channel and contributes nothing to
 *    the accessible text.
 * 2. **The component never promotes a state (N1).** The fidelity rows below are
 *    driven by a deliberately hostile input order — `waiting`, `refused`,
 *    `complete`, `active` — so a component that normalised, sorted or guessed
 *    would fail here rather than in review.
 * 3. **The stamp stays the assertion, and the colour stays in one place (P3,
 *    D2).** The icon's class string is identical for all four states and
 *    carries only the `text-ink-muted` role, so this file introduces no second
 *    state-to-colour definition; `components/status-badge.tsx` remains the only
 *    one.
 *
 * The refused-vs-failed-infrastructure check (negative case 2) is mechanical
 * and locale-honest: the error-ish keys are *discovered* from the English
 * catalog by key pattern, and the words to reject are derived from each locale's
 * own catalog values. Nothing about French or Arabic is spelled out here, which
 * is the point — an English regex would silently check nothing in `fr` and `ar`.
 */

/** The four canonical states, in contract order. */
const STATES: readonly WorkflowState[] = ["complete", "active", "waiting", "refused"];

/** The stamp word for a state, exactly as this locale renders it. */
function stateWord(state: WorkflowState, locale: Locale): string {
  return CATALOGS[locale][`state.${state}` as "state.complete"];
}

/**
 * One stage per state, each with its own label so a row can be located by its
 * heading. The labels and descriptions are fixture prose with no state word in
 * them, so `getByText(stateWord)` inside a row can only be the stamp.
 */
function stagesFor(states: readonly WorkflowState[]): WorkflowStage[] {
  return states.map((state, index) => ({
    id: `matrix-${index}`,
    label: `Matrix row ${index}`,
    description: `Fixture row ${index} of the state matrix`,
    state,
  }));
}

/**
 * The application root, resolved rather than assumed — the suite may be started
 * from `apps/research-ui/` (`npm test`) or from the repository root.
 *
 * It is read for real rather than mocked: the D2 assertion below is about the
 * bytes of `components/workflow-timeline.tsx`, and a fixture copy of those bytes
 * would let the check pass against a file nobody ships.
 */
function appRoot(): string {
  const candidates = [process.cwd(), join(process.cwd(), "apps", "research-ui")];
  for (const candidate of candidates) {
    try {
      readFileSync(join(candidate, "components", "workflow-timeline.tsx"), "utf8");
      return candidate;
    } catch {
      // Not this candidate; the loop's throw is the failure.
    }
  }
  throw new Error(
    `no application root among ${JSON.stringify(candidates)}: expected components/workflow-timeline.tsx`,
  );
}

/**
 * The catalog keys whose *name* says "error" or "fail", discovered rather than
 * enumerated.
 *
 * `messages/en.ts` is the structural source of truth (D-I18N-03), so its key set
 * is where this question is answered; today the pattern finds
 * `overview.recordError` and `overview.recordErrorLabel` — UI-02's failed-read
 * copy, which is exactly the "failed infrastructure" the packet requires
 * `refused` to stay distinct from. A key added later is picked up here without
 * this test being edited, and the non-vacuity assertion below fails loudly if
 * the pattern ever finds nothing (which would make every assertion here green
 * while proving nothing).
 */
const ERROR_KEYS: readonly MessageKey[] = (Object.keys(CATALOGS.en) as MessageKey[]).filter((key) =>
  /error|fail/i.test(key),
);

/** Letter runs of a catalog value; diacritics stay attached to their word. */
function wordsOf(value: string): string[] {
  return value.split(/[^\p{L}\p{M}]+/u).filter((word) => word.length > 0);
}

describe("WorkflowTimeline state matrix (packet UI-03)", () => {
  const MATRIX = stagesFor(STATES);

  for (const locale of SUPPORTED_LOCALES) {
    it(`renders one icon and one stamp word per state, each in its own row (${locale})`, () => {
      render(<WorkflowTimeline stages={MATRIX} locale={locale} />);
      const rows = screen.getAllByRole("listitem");
      expect(rows).toHaveLength(MATRIX.length);

      MATRIX.forEach((stage, index) => {
        const row = rows[index];

        // Exactly one state icon, and it names this row's own state (A1, A2).
        const icons = row.querySelectorAll<SVGSVGElement>("svg[data-stage-state-icon]");
        expect(icons, `row ${index} must carry exactly one state icon`).toHaveLength(1);
        expect(icons[0].getAttribute("data-stage-state-icon")).toBe(stage.state);

        // Visible to the eye, silent to the accessibility tree (A1, N8, N3).
        expect(icons[0].getAttribute("aria-hidden")).toBe("true");
        expect(icons[0].hasAttribute("role")).toBe(false);
        expect(icons[0].hasAttribute("aria-label")).toBe(false);
        expect(icons[0].hasAttribute("aria-labelledby")).toBe(false);
        expect(icons[0].querySelector("title")).toBeNull();
        expect(icons[0].textContent, "the icon must contribute no accessible text").toBe("");

        // The stamp word is this state's catalog value, and only that state's.
        const word = stateWord(stage.state, locale);
        const stamp = within(row).getByText(word);
        expect(stamp.textContent).toBe(word);
        for (const other of STATES.filter((candidate) => candidate !== stage.state)) {
          expect(
            within(row).queryByText(stateWord(other, locale)),
            `row ${index} must not claim ${other} in ${locale}`,
          ).toBeNull();
        }
      });
      cleanup();
    });
  }

  it("renders four mutually distinct icon markups", () => {
    const asRendered: string[] = [];
    const shapes: string[] = [];

    for (const state of STATES) {
      const { unmount } = render(<WorkflowTimeline stages={stagesFor([state])} locale="en" />);
      const icon = document.querySelector<SVGSVGElement>("svg[data-stage-state-icon]");
      expect(icon, `state ${state} must render an icon`).not.toBeNull();
      asRendered.push(icon!.outerHTML);

      // The token attribute differs by construction, so it is removed: the
      // second set is the claim that the *drawn shape* differs per state. If it
      // ever collapsed, the four states would be distinguishable only by a
      // data attribute no reader can see.
      const shape = icon!.cloneNode(true) as SVGSVGElement;
      shape.removeAttribute("data-stage-state-icon");
      shapes.push(shape.outerHTML);
      unmount();
    }

    expect(new Set(asRendered).size).toBe(STATES.length);
    expect(new Set(shapes).size).toBe(STATES.length);
  });

  it("gives every state the same neutral class string, and no state hue (D2)", () => {
    const classNames: string[] = [];

    for (const state of STATES) {
      const { unmount } = render(<WorkflowTimeline stages={stagesFor([state])} locale="en" />);
      const icon = document.querySelector<SVGSVGElement>("svg[data-stage-state-icon]");
      expect(icon).not.toBeNull();
      classNames.push(icon!.getAttribute("class") ?? "");
      unmount();
    }

    // One class string for four states: the icon channel carries shape, never
    // colour, so no per-state class map can exist here.
    expect(new Set(classNames).size).toBe(1);
    expect(classNames[0]).not.toBe("");
    expect(
      classNames[0].split(/\s+/).filter((cls) => cls.startsWith("text-")),
    ).toEqual(["text-ink-muted"]);
    for (const hue of ["success", "evidence", "warning", "refusal"]) {
      expect(classNames[0], `the icon must not take the ${hue} role`).not.toContain(hue);
    }
  });

  it("the timeline source defines no second state-to-colour map (N4, D2)", () => {
    const source = readFileSync(join(appRoot(), "components", "workflow-timeline.tsx"), "utf8");

    // The map itself, in the shape decision D2 names.
    expect(source).not.toMatch(/Record<\s*WorkflowState\s*,\s*string\s*>/);

    // Nor any of the four state hues *as a utility* — in code or quoted in a
    // comment, since Tailwind harvests both. The bare hue words are not banned:
    // `tests/evidence-chain.test.tsx` is named in this file's own header, and a
    // guard that failed on a file name would be a guard people route around.
    // `components/status-badge.tsx` remains the only definition of state colour.
    const colourPrefix = "(?:text|bg|border|ring|fill|stroke|outline|decoration|divide)";
    for (const hue of ["success", "evidence", "warning", "refusal"]) {
      expect(
        source,
        `workflow-timeline.tsx must not use a ${hue} colour utility`,
      ).not.toMatch(new RegExp(`${colourPrefix}-${hue}(?![\\w-])`));
    }
  });

  it("adds no focusable element and changes no list role (N8)", () => {
    const { container } = render(<WorkflowTimeline stages={MATRIX} locale="en" />);

    expect(
      screen.getByRole("list", { name: CATALOGS.en["workflow.listLabel"] }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(MATRIX.length);
    expect(
      container.querySelectorAll("a, button, input, select, textarea, [tabindex]"),
      "the timeline must gain no focusable element",
    ).toHaveLength(0);
    for (const icon of container.querySelectorAll("svg[data-stage-state-icon]")) {
      expect(icon.getAttribute("tabindex")).toBeNull();
      expect(icon.getAttribute("aria-hidden")).toBe("true");
    }
  });

  it("pins the icon's props in our own JSX, not only in the library default (A1)", () => {
    const source = readFileSync(join(appRoot(), "components", "workflow-timeline.tsx"), "utf8");
    const openTag = source.match(/<StateIcon[\s\S]*?\/>/);
    expect(openTag, "the timeline must render its state icon through <StateIcon .../>").not.toBeNull();
    const tag = openTag![0];

    // `@heroicons/react` 2.2.0 defaults `"aria-hidden": "true"` on every svg it
    // renders, so the DOM assertion above stays green even if this prop is
    // deleted — a mutation check (delete the prop → focused run) proved it. That
    // is precisely why the prop is asserted *as bytes here*: the component must
    // own the declaration rather than free-ride on a library default it does not
    // control, and this is the assertion that would fail if it stopped.
    expect(tag).toContain('aria-hidden="true"');
    expect(tag).toContain("data-stage-state-icon={stage.state}");
    expect(tag).toContain('className="size-4 shrink-0 text-ink-muted"');
  });

  for (const locale of SUPPORTED_LOCALES) {
    it(`renders each row's icon and stamp word exactly as the input state (${locale})`, () => {
      // Hostile on purpose: `complete` sits *after* a refused and a waiting
      // stage, so a component that promoted a state, or that inferred
      // completeness from position, fails here (N1 / negative case 1).
      const order: readonly WorkflowState[] = ["waiting", "refused", "complete", "active"];
      const stages = stagesFor(order);

      render(<WorkflowTimeline stages={stages} locale={locale} />);
      const rows = screen.getAllByRole("listitem");
      expect(rows).toHaveLength(order.length);

      rows.forEach((row, index) => {
        const state = order[index];
        const icons = row.querySelectorAll<SVGSVGElement>("svg[data-stage-state-icon]");
        expect(icons).toHaveLength(1);
        expect(icons[0].getAttribute("data-stage-state-icon")).toBe(state);

        expect(within(row).getByText(stateWord(state, locale)).textContent).toBe(
          stateWord(state, locale),
        );
        for (const other of STATES.filter((candidate) => candidate !== state)) {
          expect(
            within(row).queryByText(stateWord(other, locale)),
            `row ${index} was given ${state} and must not claim ${other}`,
          ).toBeNull();
        }
      });
      cleanup();
    });
  }

  it("the demo workflow claims no complete stage after a non-complete stage (A3b)", () => {
    const stages = demoProject.stages;
    // Non-vacuity: a fixture of six complete stages would pass vacuously.
    expect(stages.some((stage) => stage.state === "complete")).toBe(true);
    expect(stages.some((stage) => stage.state !== "complete")).toBe(true);

    let stopped: string | null = null;
    for (const stage of stages) {
      if (stage.state !== "complete") {
        stopped = stage.id;
        continue;
      }
      expect(
        stopped,
        `demo stage "${stage.id}" claims complete after "${stopped}" stopped being complete`,
      ).toBeNull();
    }
  });

  it("discovers the catalog's error-ish keys instead of assuming them (A4 non-vacuity)", () => {
    expect(ERROR_KEYS.length).toBeGreaterThan(0);
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of ERROR_KEYS) {
        expect(CATALOGS[locale][key], `${locale}:${key} must be a real value`).not.toBe("");
      }
    }
  });

  for (const locale of SUPPORTED_LOCALES) {
    it(`keeps refused distinct from failed infrastructure (${locale})`, () => {
      const refusedWord = CATALOGS[locale]["state.refused"];

      // (a) The refused stamp is never spelled as an error value.
      for (const key of ERROR_KEYS) {
        expect(
          CATALOGS[locale][key],
          `${locale}:${key} must not be spelled exactly like state.refused`,
        ).not.toBe(refusedWord);
      }

      // (b) The rendered refused row contains neither an error value nor any
      // distinctive word inside one. Both are derived from the catalog of the
      // locale under test, so French and Arabic are checked in French and
      // Arabic rather than against an English pattern that matches nothing.
      const refusedStage = ALL_STATES_STAGES.find((stage) => stage.state === "refused");
      expect(refusedStage, "the presentation fixture must carry a refused stage (A5)").toBeDefined();

      render(<WorkflowTimeline stages={[refusedStage!]} locale={locale} />);
      const row = screen.getByRole("listitem");
      expect(row.querySelector('svg[data-stage-state-icon="refused"]')).not.toBeNull();
      const text = (row.textContent ?? "").replace(/\s+/g, " ").trim().toLowerCase();

      for (const key of ERROR_KEYS) {
        const value = CATALOGS[locale][key].replace(/\s+/g, " ").trim().toLowerCase();
        expect(text, `${locale}: the refused row must not carry ${key}`).not.toContain(value);
      }

      const errorWords = ERROR_KEYS.flatMap((key) => wordsOf(CATALOGS[locale][key]))
        .filter((word) => word.length >= 5)
        // A word that *is* the refused stamp is shared vocabulary, not an error
        // claim: `overview.recordError` itself says "not a refused decision" in
        // English and "non d'une décision refusée" in French, so rejecting the
        // stamp's own word would reject the very sentence that distinguishes
        // the two concepts.
        .filter((word) => !(word.includes(refusedWord) || refusedWord.includes(word)));
      expect(errorWords.length, `${locale}: no error words were derived`).toBeGreaterThan(0);

      for (const word of errorWords) {
        expect(
          text,
          `${locale}: the refused row must not contain the error word "${word}"`,
        ).not.toContain(word.toLowerCase());
      }
      cleanup();
    });
  }
});
