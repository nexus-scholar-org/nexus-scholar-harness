import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { DatabasePicker } from "@/components/database-picker";

/**
 * The shared database picker (M10a, decided 2026-11-14, item 1a; spec 02
 * Keyboard and Accessibility, specs 01-plan and 03-harvest of Discovery): a
 * fieldset of checkboxes with real Move up / Move down buttons, focus kept on
 * the moved row's button, a polite announcement, and "at least one" in words.
 * The component owns no copy; every string here is the caller's.
 */

const ITEMS = [
  { id: "openalex", label: "OpenAlex" },
  { id: "semanticscholar", label: "Semantic Scholar" },
  { id: "crossref", label: "Crossref", note: "matches any word" },
  { id: "arxiv", label: "arXiv" },
];

const LABELS = {
  legend: "Databases to ask",
  orderHelp: "The order decides which papers fill the sample of 25 first.",
  check: (name: string) => `Ask ${name}`,
  up: (name: string) => `Move ${name} up`,
  down: (name: string) => `Move ${name} down`,
  moved: (name: string, position: number, total: number) => `${name} moved to position ${position} of ${total}`,
  none: "Pick at least one database.",
};

function Harness({ initial, spy = () => {}, disabled = false }: Readonly<{ initial: string[]; spy?: (next: string[]) => void; disabled?: boolean }>) {
  const [value, setValue] = useState(initial);
  return (
    <DatabasePicker
      items={ITEMS}
      value={value}
      disabled={disabled}
      labels={LABELS}
      onChange={(next) => {
        spy(next);
        setValue(next);
      }}
    />
  );
}

const ALL = ["openalex", "semanticscholar", "crossref", "arxiv"];
const rows = () => [...document.querySelectorAll("[data-picker-row]")].map((r) => `${r.getAttribute("data-picker-row")}:${r.getAttribute("data-selected")}`);

describe("database-picker", () => {
  it("is a fieldset with its legend: the selected databases first in their order, then the others in list order", () => {
    render(<Harness initial={["crossref", "openalex"]} />);
    const group = screen.getByRole("group", { name: "Databases to ask" });
    expect(group.tagName).toBe("FIELDSET");
    expect(group).toHaveAttribute("data-picker");
    expect(rows()).toEqual(["crossref:true", "openalex:true", "semanticscholar:false", "arxiv:false"]);
    expect(screen.getByRole("checkbox", { name: "Ask Crossref" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Ask arXiv" })).not.toBeChecked();
    // The order is stated in text: the position of each selected database.
    const crossref = document.querySelector("[data-picker-row='crossref']") as HTMLElement;
    expect(crossref.querySelector("[data-position]")?.textContent).toBe("1");
    expect(document.querySelector("[data-picker-row='arxiv'] [data-position]")).toBeNull();
    expect(within(crossref).getByText("matches any word")).toBeInTheDocument();
    expect(screen.getByText("The order decides which papers fill the sample of 25 first.")).toBeInTheDocument();
  });

  it("gives a row's note to its checkbox as the accessible description", () => {
    render(<Harness initial={ALL} />);
    const crossref = screen.getByRole("checkbox", { name: "Ask Crossref" });
    expect(crossref).toHaveAccessibleDescription("matches any word");
    const noteId = crossref.getAttribute("aria-describedby") as string;
    expect(document.getElementById(noteId)?.textContent).toBe("matches any word");
    // A row without a note has no description.
    expect(screen.getByRole("checkbox", { name: "Ask arXiv" })).not.toHaveAttribute("aria-describedby");
  });

  it("disables Move up on the first row, Move down on the last selected row, and both on unselected rows", () => {
    render(<Harness initial={["openalex", "semanticscholar", "crossref"]} />);
    expect(screen.getByRole("button", { name: "Move OpenAlex up" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move OpenAlex down" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Move Crossref up" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Move Crossref down" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move arXiv up" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move arXiv down" })).toBeDisabled();
    for (const button of screen.getAllByRole("button")) expect(button).toHaveAttribute("type", "button");
  });

  it("tabs through each row as checkbox, Move up, Move down", async () => {
    const user = userEvent.setup();
    render(<Harness initial={ALL} />);
    const order: string[] = [];
    for (let i = 0; i < 10; i++) {
      await user.tab();
      const el = document.activeElement as HTMLElement;
      order.push(el.getAttribute("aria-label") ?? el.textContent ?? "");
    }
    expect(order).toEqual([
      "Ask OpenAlex",
      "Move OpenAlex down",
      "Ask Semantic Scholar",
      "Move Semantic Scholar up",
      "Move Semantic Scholar down",
      "Ask Crossref",
      "Move Crossref up",
      "Move Crossref down",
      "Ask arXiv",
      "Move arXiv up",
    ]);
  });

  it("toggles with Space: unticking removes from the order, ticking appends to its end", async () => {
    const user = userEvent.setup();
    const spy = vi.fn();
    render(<Harness initial={ALL} spy={spy} />);
    screen.getByRole("checkbox", { name: "Ask Semantic Scholar" }).focus();
    await user.keyboard(" ");
    expect(spy).toHaveBeenLastCalledWith(["openalex", "crossref", "arxiv"]);
    expect(rows()).toEqual(["openalex:true", "crossref:true", "arxiv:true", "semanticscholar:false"]);
    screen.getByRole("checkbox", { name: "Ask Semantic Scholar" }).focus();
    await user.keyboard(" ");
    expect(spy).toHaveBeenLastCalledWith(["openalex", "crossref", "arxiv", "semanticscholar"]);
  });

  it("moves with Enter and Space, keeps focus on the moved row's button, and announces the new position", async () => {
    const user = userEvent.setup();
    const spy = vi.fn();
    render(<Harness initial={ALL} spy={spy} />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(status.textContent).toBe("");

    screen.getByRole("button", { name: "Move Crossref up" }).focus();
    await user.keyboard("{Enter}");
    expect(spy).toHaveBeenLastCalledWith(["openalex", "crossref", "semanticscholar", "arxiv"]);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move Crossref up" }));
    expect(status.textContent).toBe("Crossref moved to position 2 of 4");

    screen.getByRole("button", { name: "Move OpenAlex down" }).focus();
    await user.keyboard(" ");
    expect(spy).toHaveBeenLastCalledWith(["crossref", "openalex", "semanticscholar", "arxiv"]);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move OpenAlex down" }));
    expect(status.textContent).toBe("OpenAlex moved to position 2 of 4");
  });

  it("sends focus to the other move button when the moved row reaches an end", async () => {
    const user = userEvent.setup();
    render(<Harness initial={ALL} />);
    screen.getByRole("button", { name: "Move Crossref down" }).focus();
    await user.keyboard("{Enter}");
    expect(rows().slice(0, 4)).toEqual(["openalex:true", "semanticscholar:true", "arxiv:true", "crossref:true"]);
    expect(screen.getByRole("button", { name: "Move Crossref down" })).toBeDisabled();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Move Crossref up" }));
    expect(screen.getByRole("status").textContent).toBe("Crossref moved to position 4 of 4");
  });

  it("lets the last database be unticked and says at least one is needed, linked to the group", async () => {
    const user = userEvent.setup();
    const spy = vi.fn();
    render(<Harness initial={["arxiv"]} spy={spy} />);
    expect(screen.queryByRole("alert")).toBeNull();
    await user.click(screen.getByRole("checkbox", { name: "Ask arXiv" }));
    expect(spy).toHaveBeenLastCalledWith([]);
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toBe("Pick at least one database.");
    const group = screen.getByRole("group", { name: "Databases to ask" });
    expect(group.getAttribute("aria-describedby")?.split(" ")).toContain(alert.id);
  });

  it("disables every control while the caller is busy", () => {
    render(<Harness initial={ALL} disabled />);
    for (const box of screen.getAllByRole("checkbox")) expect(box).toBeDisabled();
    for (const button of screen.getAllByRole("button")) expect(button).toBeDisabled();
  });

  it("renders right to left with logical classes only and icons that are never mirrored", () => {
    const { container } = render(
      <div dir="rtl">
        <Harness initial={ALL} />
      </div>,
    );
    const picker = container.querySelector("[data-picker]") as HTMLElement;
    expect(picker).not.toHaveAttribute("dir");
    const classes = [...picker.querySelectorAll("[class]")].map((el) => el.getAttribute("class") ?? "").join(" ");
    expect(classes).not.toMatch(/(^|\s)(ml|mr|pl|pr|left|right)-|text-(left|right)|border-(l|r)(\s|-|$)|rounded-(l|r)-|scale-x|rotate-/);
    for (const row of picker.querySelectorAll("[data-picker-row]")) expect(row.className).toMatch(/min-h-11/);
    for (const svg of picker.querySelectorAll("svg")) {
      expect(svg).toHaveAttribute("aria-hidden", "true");
      expect(svg.getAttribute("style") ?? "").not.toMatch(/scale|rotate/);
    }
  });
});
