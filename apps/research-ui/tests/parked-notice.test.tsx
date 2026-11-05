import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { OverviewPage } from "@/components/overview-page";
import { ParkedNotice } from "@/components/parked-notice";
import { translate } from "@/i18n";

vi.mock("next/navigation", () => ({ usePathname: () => "/en" }));

/**
 * Production plan §8: a surface that shows parked work (synthesis, extraction,
 * full text) says so in words, through one shared notice.
 */
describe("parked notice", () => {
  it("is on the overview, as a note that names the parked work", () => {
    render(<OverviewPage locale="en" />);
    const note = screen.getByRole("note");
    expect(note).toHaveAttribute("data-parked", "overview");
    expect(note).toHaveTextContent("Not production — parked");
    expect(note).toHaveTextContent("only screening is production");
  });

  it("renders the lineage text from the catalog", () => {
    render(<ParkedNotice locale="ar" feature="lineage" />);
    expect(screen.getByRole("note")).toHaveTextContent(translate("ar", "parked.lineage"));
  });
});
