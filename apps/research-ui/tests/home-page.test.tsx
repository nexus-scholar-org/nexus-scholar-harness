import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LocaleDocument } from "@/components/locale-document";
import { OverviewPage } from "@/components/overview-page";
import { demoEvidence, demoProject } from "@/lib/mock-project";
import { SUPPORTED_LOCALES } from "@/i18n";
import { CATALOGS } from "@/messages";

/**
 * `LocaleSwitcher` is a client component that reads the current path with
 * `usePathname()`, which has no meaning outside a running app. The mock returns
 * the path the test rendered, so the selector's links and the document agree.
 */
vi.mock("next/navigation", () => ({
  usePathname: () => "/en",
}));

/** Renders the real English locale route: document plus overview page. */
function renderRoute() {
  return render(
    <LocaleDocument locale="en">
      <OverviewPage locale="en" />
    </LocaleDocument>,
  );
}

/**
 * Anti-fabrication guard.
 *
 * `apps/research-ui/AGENTS.md` forbids presenting mock data without the
 * visible `Demonstration data` label. This asserts against the actual rendered
 * output of the shell, not against a snapshot, so a future edit that drops the
 * label fails the build.
 *
 * UI-01 moved the label out of the page and into the shell
 * (`components/app-shell.tsx`), so the guard renders the whole document. UI-01d
 * moved both the document and the page under `app/[locale]/`, so the guard
 * renders `LocaleDocument` + `OverviewPage` — the same two components the real
 * server render composes, in the same order. The remaining cases still render
 * `OverviewPage` on its own, so the page keeps its own coverage.
 *
 * The `Demonstration data` label is chrome, and chrome is translated: the guard
 * therefore checks the catalog value in every locale rather than the English
 * pin. It is still the same guard — a page that dropped the label fails in all
 * three locales, not just the one the pin came from.
 */
describe("locale route demonstration-data guard", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`shows the literal Demonstration data label from the shell (${locale})`, () => {
      render(
        <LocaleDocument locale={locale}>
          <OverviewPage locale={locale} />
        </LocaleDocument>,
      );

      expect(screen.getByText(CATALOGS[locale]["safety.demoDataLabel"])).toBeInTheDocument();
    });
  }

  it("shows the literal Demonstration data label from the shell", () => {
    renderRoute();

    expect(screen.getByText("Demonstration data")).toBeInTheDocument();
  });

  it("keeps the label inside the banner header, not buried in the body copy", () => {
    renderRoute();

    const label = screen.getByText("Demonstration data");
    const header = label.closest("header");
    expect(header).not.toBeNull();
    expect(header?.querySelector("main")).toBeNull();
    expect(screen.getByRole("banner")).toBe(header);
  });

  it("renders the demonstration project summary it claims to show", () => {
    render(<OverviewPage locale="en" />);

    expect(screen.getByRole("heading", { level: 1, name: demoProject.title })).toBeInTheDocument();
    expect(screen.getByText(demoProject.researchQuestion, { selector: "bdi" })).toBeInTheDocument();
    // The ledger caption is one translated sentence with the record's own event
    // substituted into it, so it is no longer a single text node: the assertion
    // is on the paragraph's whole `textContent`, which is also what a reader gets
    // — the same string, with the event marked up rather than quoted.
    expect(
      screen.getByText(
        (_content, element) =>
          element?.tagName === "P" &&
          element.textContent === `Latest: ${demoProject.lastEvent}`,
      ),
    ).toBeInTheDocument();
  });

  it("renders both the workflow timeline and the evidence chain on the route", () => {
    render(<OverviewPage locale="en" />);

    expect(screen.getByRole("list", { name: "Research workflow" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(demoProject.stages.length + demoEvidence.length);
  });

  it("renders every demonstration stage label the fixture declares", () => {
    render(<OverviewPage locale="en" />);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels.slice(0, demoProject.stages.length)).toEqual(demoProject.stages.map((stage) => stage.label));
  });
});