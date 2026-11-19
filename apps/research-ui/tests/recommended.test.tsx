import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Fold, RecommendedBadge } from "@/components/ui/base";

/**
 * 03-guidance rule 3 (the Recommended mark) and rule 4 use 2 (a folded card),
 * M10d. The screens' own "never preselected" cases are in
 * `guidance.screens.test.tsx` (Shape, Explore, Harvest, Review).
 */

describe("recommended", () => {
  it("carries its source in visible text and the why behind a hint", () => {
    render(<RecommendedBadge locale="en" source="word scan of your topic" why="The topic's words lean to this lens." whyKey="shape.leaningNote" />);
    const badge = document.querySelector("[data-recommended]") as HTMLElement;
    expect(badge.textContent).toContain("Recommended · word scan of your topic");
    expect(screen.getByRole("button", { name: "About Recommended" })).toBeInTheDocument();
    expect(document.querySelector('[data-hint-body="shape.leaningNote"]')).toHaveAttribute("hidden");
    // A word on a neutral dashed outline, not a colour: not brand, not include, not unclear.
    const word = badge.firstElementChild as HTMLElement;
    expect(word.className).toContain("border-dashed");
    expect(word.className).not.toMatch(/\b(bg|text|border)-(brand|include|unclear)\b/);
  });

  it("renders nothing without a source", () => {
    render(<RecommendedBadge locale="en" source=" " />);
    expect(document.querySelector("[data-recommended]")).toBeNull();
  });

  it("is translated", () => {
    render(<RecommendedBadge locale="ar" source="فحص كلمات موضوعك" />);
    expect(document.querySelector("[data-recommended]")?.textContent).toBe("موصى به · فحص كلمات موضوعك");
  });
});

describe("fold", () => {
  it("is closed by default, keeps its content in the DOM, and names its title, count and failures in the summary", () => {
    render(
      <Fold locale="en" title="Databases asked" count={4} failed={1}>
        <p>row</p>
      </Fold>,
    );
    const details = document.querySelector("details[data-fold]") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.querySelector("p")?.textContent).toBe("row");
    const summary = details.querySelector("summary")!;
    expect(summary.textContent).toContain("Databases asked · 4");
    expect(summary.querySelector('[data-role="blocked"]')?.textContent).toBe("1 failed");
    expect(summary.className).toContain("min-h-11");
    expect(summary.className).toContain("focus-visible:outline-2");
  });

  it("shows no failure badge when nothing failed", () => {
    render(
      <Fold locale="en" title="Papers" count={25}>
        <p>row</p>
      </Fold>,
    );
    expect(document.querySelector('summary [data-role="blocked"]')).toBeNull();
  });
});
