import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RootLayout from "@/app/layout";
import HomePage from "@/app/page";
import { demoEvidence, demoProject } from "@/lib/mock-project";

/**
 * Anti-fabrication guard.
 *
 * `apps/research-ui/AGENTS.md` forbids presenting mock data without the
 * visible `Demonstration data` label. This asserts against the actual rendered
 * output of the shell, not against a snapshot, so a future edit that drops the
 * label fails the build.
 *
 * UI-01 moved the label out of `app/page.tsx` and into the shell
 * (`components/app-shell.tsx`), so the guard now renders `RootLayout`. The
 * remaining cases still render `HomePage` on its own, so the page keeps its own
 * coverage.
 */
describe("/ route demonstration-data guard", () => {
  it("shows the literal Demonstration data label from the shell", () => {
    render(
      <RootLayout>
        <HomePage />
      </RootLayout>,
    );

    expect(screen.getByText("Demonstration data")).toBeInTheDocument();
  });

  it("keeps the label inside the banner header, not buried in the body copy", () => {
    render(
      <RootLayout>
        <HomePage />
      </RootLayout>,
    );

    const label = screen.getByText("Demonstration data");
    const header = label.closest("header");
    expect(header).not.toBeNull();
    expect(header?.querySelector("main")).toBeNull();
    expect(screen.getByRole("banner")).toBe(header);
  });

  it("renders the demonstration project summary it claims to show", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { level: 1, name: demoProject.title })).toBeInTheDocument();
    expect(screen.getByText(demoProject.researchQuestion)).toBeInTheDocument();
    expect(screen.getByText(`Latest: ${demoProject.lastEvent}`)).toBeInTheDocument();
  });

  it("renders both the workflow timeline and the evidence chain on the route", () => {
    render(<HomePage />);

    expect(screen.getByRole("list", { name: "Research workflow" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(demoProject.stages.length + demoEvidence.length);
  });

  it("renders every demonstration stage label the fixture declares", () => {
    render(<HomePage />);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels.slice(0, demoProject.stages.length)).toEqual(demoProject.stages.map((stage) => stage.label));
  });
});
