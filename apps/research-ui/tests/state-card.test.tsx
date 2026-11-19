import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StateCard } from "@/components/screening-state-card";

/** H-ui-findings F7: the card names its state once. Its title was printed twice, as a badge and as the heading. */

describe("state card", () => {
  it("prints the title once, as the heading, for a known and for an unknown code", () => {
    const { unmount } = render(<StateCard locale="en" code="MAILTO_NOT_SET" />);
    expect(screen.getAllByText("Set a contact email before searching")).toHaveLength(1);
    expect(screen.getByRole("heading", { name: "Set a contact email before searching" })).toBeInTheDocument();
    unmount();
    render(<StateCard locale="en" code="SOME_NEW_CODE" />);
    expect(screen.getAllByText("Refused")).toHaveLength(1);
  });

  it("keeps the role as an attribute, the typed code behind Details, and the alert role", () => {
    render(<StateCard locale="en" code="MAILTO_NOT_SET" />);
    const card = document.querySelector("[data-state='MAILTO_NOT_SET']") as HTMLElement;
    expect(card).toHaveAttribute("role", "alert");
    expect(card).toHaveAttribute("data-role", "blocked");
    expect(card.querySelector("[data-state-details]")?.textContent).toContain("MAILTO_NOT_SET");
  });
});
