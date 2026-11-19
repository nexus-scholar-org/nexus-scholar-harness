import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Hint } from "@/components/ui/base";

/** 03-guidance rule 1, the Hint (M10d). */

function form() {
  return render(
    <div>
      <label htmlFor="f">Topic</label>
      <Hint locale="en" label="Topic" text="One subject, in your words." textKey="scope.topicHelp" id="f-help" />
      <input id="f" aria-describedby="f-help" />
      <p>
        <span>Years</span>
        <Hint locale="en" label="Years" text="Empty means up to today." textKey="scope.toYearHelp" />
      </p>
      <button type="button">Elsewhere</button>
    </div>,
  );
}

const panel = (name: string) => document.getElementById(screen.getByRole("button", { name }).getAttribute("aria-controls")!)!;

describe("hint", () => {
  it("is a real button named after its label, with aria-expanded and aria-controls, outside any label", () => {
    form();
    const button = screen.getByRole("button", { name: "About Topic" });
    expect(button).toHaveAttribute("type", "button");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).toHaveAttribute("aria-controls", "f-help");
    expect(button.closest("label")).toBeNull();
    expect(button.className).toContain("size-11");
  });

  it("keeps its text in the DOM while closed, as the field's description, in a note", () => {
    form();
    const body = document.getElementById("f-help")!;
    expect(body).toHaveAttribute("role", "note");
    expect(body).toHaveAttribute("hidden");
    expect(body).toHaveAttribute("data-hint-body", "scope.topicHelp");
    expect(body).toHaveAttribute("dir", "auto");
    expect(body.textContent).toBe("One subject, in your words.");
    expect(screen.getByRole("textbox")).toHaveAccessibleDescription("One subject, in your words.");
  });

  it("opens and closes on click, and on Enter and Space", async () => {
    const user = userEvent.setup();
    form();
    const button = screen.getByRole("button", { name: "About Topic" });
    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(panel("About Topic")).not.toHaveAttribute("hidden");
    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
    button.focus();
    await user.keyboard("{Enter}");
    expect(button).toHaveAttribute("aria-expanded", "true");
    await user.keyboard(" ");
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on Escape and leaves focus on its button, also from inside the panel", async () => {
    const user = userEvent.setup();
    form();
    const button = screen.getByRole("button", { name: "About Topic" });
    await user.click(button);
    await user.keyboard("{Escape}");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(document.activeElement).toBe(button);
    await user.click(button);
    const body = panel("About Topic");
    body.tabIndex = -1;
    body.focus();
    fireEvent.keyDown(body, { key: "Escape" });
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(document.activeElement).toBe(button);
  });

  it("toggles on a touch tap, with no hover handler", async () => {
    const user = userEvent.setup();
    form();
    const button = screen.getByRole("button", { name: "About Topic" });
    await user.pointer({ keys: "[TouchA]", target: button });
    expect(button).toHaveAttribute("aria-expanded", "true");
    fireEvent.mouseEnter(screen.getByRole("button", { name: "About Years" }));
    expect(screen.getByRole("button", { name: "About Years" })).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on a click outside, and on Tab away", async () => {
    const user = userEvent.setup();
    form();
    const button = screen.getByRole("button", { name: "About Topic" });
    await user.click(button);
    await user.click(document.body);
    expect(button).toHaveAttribute("aria-expanded", "false");
    await user.click(button);
    await user.tab();
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("closes the open hint when another opens", async () => {
    const user = userEvent.setup();
    form();
    await user.click(screen.getByRole("button", { name: "About Topic" }));
    await user.click(screen.getByRole("button", { name: "About Years" }));
    expect(screen.getByRole("button", { name: "About Topic" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button", { name: "About Years" })).toHaveAttribute("aria-expanded", "true");
  });

  it("renders the text as text, never as markup, and renders nothing for an empty text", () => {
    render(
      <div>
        <Hint locale="en" label="A" text="<b>bold</b>" textKey="k.a" />
        <Hint locale="en" label="B" text="  " textKey="k.b" />
      </div>,
    );
    expect(document.querySelector("b")).toBeNull();
    expect(document.querySelector('[data-hint-body="k.a"]')?.textContent).toBe("<b>bold</b>");
    expect(screen.queryByRole("button", { name: "About B" })).toBeNull();
  });

  it("is named in French and Arabic from the guidance catalog", () => {
    render(
      <div>
        <Hint locale="fr" label="Sujet" text="x" textKey="k.fr" />
        <Hint locale="ar" label="الموضوع" text="x" textKey="k.ar" />
      </div>,
    );
    expect(screen.getByRole("button", { name: "À propos de « Sujet »" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "حول «الموضوع»" })).toBeInTheDocument();
  });
});
