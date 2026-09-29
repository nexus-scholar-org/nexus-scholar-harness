import { render } from "@testing-library/react";
import axe from "axe-core";
import type { AxeResults, ImpactValue, Result } from "axe-core";
import { describe, expect, it } from "vitest";

import HomePage from "@/app/page";

/** Renders a violation as a reviewable one-liner so a red build is diagnosable. */
function describeViolation(violation: Result): string {
  const targets = violation.nodes.map((node) => JSON.stringify(node.target)).join(" | ");
  return `[${violation.impact ?? "unknown"}] ${violation.id}: ${violation.help} -> ${targets}`;
}

/**
 * The severity policy of this gate, as a named pure function.
 *
 * It is exported (and unit-tested against a synthetic result set below) for one
 * reason: the predicate below decides what counts as a build-blocking defect,
 * so it must not be able to be weakened silently. When this filter was an inline
 * arrow inside the primary test, replacing it with `() => false` left the whole
 * suite green, because the assertion then degenerated into `expect([]).toEqual([])`.
 * As a named, directly-tested function, that same mutation is a red test.
 */
export function blockingViolations(results: AxeResults): Result[] {
  return results.violations.filter(
    (violation) => violation.impact === "critical" || violation.impact === "serious",
  );
}

/** Impact level to give a synthetic violation; `undefined` models an absent field. */
type SyntheticImpact = ImpactValue | undefined;

/** A minimal synthetic violation, carrying only what the filter and diagnostics read. */
function syntheticViolation(id: string, impact: SyntheticImpact): Result {
  return {
    id,
    impact,
    description: `synthetic ${id}`,
    help: `synthetic ${id}`,
    helpUrl: `https://example.invalid/rules/${id}`,
    tags: ["synthetic-fixture"],
    nodes: [],
  };
}

/** Wraps violations in an `AxeResults`-shaped object so the filter can be tested offline. */
function resultsWith(violations: Result[]): AxeResults {
  return {
    violations,
    passes: [],
    incomplete: [],
    inapplicable: [],
    toolOptions: {},
    testEngine: { name: "axe-core", version: "synthetic" },
    testRunner: { name: "synthetic" },
    testEnvironment: { userAgent: "synthetic", windowWidth: 0, windowHeight: 0 },
    url: "about:blank",
    timestamp: "1970-01-01T00:00:00.000Z",
  };
}

/**
 * In-process accessibility check: axe-core evaluated inside jsdom.
 *
 * This is NOT a rendered-CSS audit. jsdom does not lay out, does not compute
 * real contrast ratios, and has no visual viewport, so the following remain
 * UNVERIFIED here and are deferred to packet UI-00b (see `GATES.md`):
 *   - colour-contrast and any other computed-style rule (axe reports these as
 *     "incomplete", not "passed"),
 *   - focus order and focus visibility as actually rendered,
 *   - responsive rendering at 375px / 1440px.
 */
describe("in-process accessibility (jsdom + axe-core)", () => {
  it("reports zero critical and zero serious violations on the rendered / page", async () => {
    const { container } = render(<HomePage />);

    const results = await axe.run(container);

    // Non-vacuity guard, asserted BEFORE filtering: the engine really executed
    // against this render, so an empty `blocking` list below means "clean", not
    // "the runner returned nothing".
    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);

    // Filter-liveness guard: `blockingViolations` is armed. A refactor that
    // neuters the filter fails HERE as well, not only in the filter's unit test.
    expect(
      blockingViolations(
        resultsWith([syntheticViolation("synthetic-serious", "serious")]),
      ).map((violation) => violation.id),
    ).toEqual(["synthetic-serious"]);

    // A failure message that names the rule, help text and offending nodes.
    expect(blockingViolations(results).map(describeViolation)).toEqual([]);
  });

  it("actually ran the engine: the result set is populated and the rule engine executed", async () => {
    const { container } = render(<HomePage />);

    const results = await axe.run(container);

    // Without this, an empty result set would silently satisfy the assertion above.
    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);
    expect(results.passes.length).toBeGreaterThan(0);
  });

  it("control: a deliberately broken image IS reported as a critical violation", async () => {
    // This asserts nothing about the application. It exists so the check above
    // cannot pass vacuously: if this control ever reports zero critical
    // violations, the runner is broken and the green gate is meaningless.
    const { container } = render(<img src="probe.png" />);

    const results = await axe.run(container);
    const critical = results.violations.filter((violation) => violation.impact === "critical");

    expect(critical.map((violation) => violation.id)).toContain("image-alt");
  });

  it("filter: keeps exactly the critical and serious violations, in order, and drops the rest", () => {
    // One entry per impact level axe can report, plus an absent `impact`.
    const critical = syntheticViolation("synthetic-critical", "critical");
    const serious = syntheticViolation("synthetic-serious", "serious");
    const moderate = syntheticViolation("synthetic-moderate", "moderate");
    const minor = syntheticViolation("synthetic-minor", "minor");
    const absentImpact = syntheticViolation("synthetic-absent-impact", undefined);
    const nullImpact = syntheticViolation("synthetic-null-impact", null);

    // Deliberately shuffled: a pass proves both selection AND input order.
    const blocking = blockingViolations(
      resultsWith([moderate, critical, absentImpact, serious, nullImpact, minor]),
    );

    // Asserted on rule ids, not a count, so a wrong-but-same-length result fails.
    expect(blocking.map((violation) => violation.id)).toEqual([
      "synthetic-critical",
      "synthetic-serious",
    ]);
  });
});
