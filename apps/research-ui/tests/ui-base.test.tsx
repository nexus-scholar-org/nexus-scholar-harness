import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button, DataCell, DecisionBadge, EvidenceQuote, GatePanel } from "@/components/ui/base";

/**
 * Foundation components (production plan §3, M0): each pins the brand rule it
 * carries, so a screen built from them cannot drift from the brand book.
 */
describe("foundation components", () => {
  it("Button is a real button, 44px tall, brand-filled only when primary", () => {
    render(
      <>
        <Button variant="primary">Approve</Button>
        <Button>Dry run</Button>
      </>,
    );
    const primary = screen.getByRole("button", { name: "Approve" });
    const secondary = screen.getByRole("button", { name: "Dry run" });
    expect(primary).toHaveAttribute("type", "button");
    expect(primary.className).toContain("min-h-11");
    expect(primary.className).toContain("bg-brand");
    expect(primary.className).toContain("text-on-brand");
    expect(secondary.className).not.toContain("bg-brand");
  });

  it.each([
    ["include", "bg-include-soft", "text-include"],
    ["unclear", "bg-unclear-soft", "text-unclear"],
    ["blocked", "bg-blocked-soft", "text-blocked"],
    ["exclude", "bg-exclude-soft", "text-exclude"],
  ] as const)("DecisionBadge %s is a word on its tint in its full colour", (role, tint, ink) => {
    render(<DecisionBadge role={role}>{role} word</DecisionBadge>);
    const badge = screen.getByText(`${role} word`);
    expect(badge.className).toContain(tint);
    expect(badge.className).toContain(ink);
    expect(badge.className).not.toContain("text-ink");
  });

  it("GatePanel is brand-soft with a dashed brand border and its actions", () => {
    render(
      <GatePanel label="Gate" actions={<Button variant="primary">Publish</Button>}>
        Nothing is written until you confirm.
      </GatePanel>,
    );
    const panel = screen.getByText("Nothing is written until you confirm.").closest("section");
    expect(panel?.className).toContain("bg-brand-soft");
    expect(panel?.className).toContain("border-dashed");
    expect(panel?.className).toContain("border-brand");
    expect(screen.getByRole("button", { name: "Publish" })).toBeInTheDocument();
  });

  it("EvidenceQuote and DataCell mark provenance and identifiers", () => {
    render(
      <>
        <EvidenceQuote source={<DataCell>10.1000/uav-1</DataCell>}>A verbatim passage.</EvidenceQuote>
      </>,
    );
    expect(screen.getByText("A verbatim passage.").closest("figure")?.className).toContain("bg-anchor-soft");
    const id = screen.getByText("10.1000/uav-1");
    expect(id.className).toContain("font-mono");
    expect(id).toHaveAttribute("dir", "ltr");
  });
});
