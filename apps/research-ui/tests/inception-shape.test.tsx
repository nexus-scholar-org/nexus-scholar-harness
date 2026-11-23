import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionShape } from "@/components/inception-shape";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/** Spec 04 (M4b): lens cards with the engine's leaning, the playbook, the RQ template as a draft. */

afterEach(() => vi.unstubAllGlobals());

describe("inception.shape", () => {
  it("keeps Continue disabled until the researcher has chosen a playbook, and says so (H-ui-findings F2)", async () => {
    setUp({ draft: { topic: "weed detection" } });
    render(<InceptionShape locale="en" />);
    const lens = (await screen.findByText("Design Science")).closest("label")!;
    fireEvent.click(within(lens).getByRole("radio"));
    const playbook = (await screen.findByText("DESIGN_SCIENCE")).closest("label")!;
    // The matching playbook is marked, never selected for the researcher (spec 04).
    expect(within(playbook).getByText("Recommended · matches your lens")).toBeInTheDocument();
    expect(within(playbook).getByRole("radio")).not.toBeChecked();
    const next = screen.getByRole("button", { name: "Continue to concepts and criteria" });
    expect(next).toBeDisabled();
    expect(screen.getByText("Choose a playbook first.")).toBeInTheDocument();
    expect(next).toHaveAccessibleDescription("Choose a playbook first.");
    fireEvent.click(within(playbook).getByRole("radio"));
    expect(next).toBeEnabled();
    expect(screen.queryByText("Choose a playbook first.")).toBeNull();
  });

  it("offers the template only once the engine has answered for the answers on screen", async () => {
    setUp({ draft: { topic: "weed detection", paradigm: "Design Science", playbook: "DESIGN_SCIENCE", unit_of_analysis: "embedded cameras", proof: "mIoU" } });
    render(<InceptionShape locale="en" />);
    const card = (await screen.findByText("Template draft · not yet yours")).closest("[data-rq-draft]") as HTMLElement;
    const use = within(card).getByRole("button", { name: "Use this draft as RQ1" });
    await waitFor(() => expect(use).toBeEnabled());
    expect(within(card).getByText(/achieve mIoU for embedded cameras/)).toBeInTheDocument();

    // An edit makes the shown draft stale until the debounced step answers again.
    fireEvent.change(screen.getByLabelText("Proof a reviewer would accept"), { target: { value: "FPS on a public benchmark" } });
    expect(use).toBeDisabled();
    expect(card).toHaveAttribute("data-draft-current", "false");
    expect(within(card).getByText("Updating the draft from your answers…")).toBeInTheDocument();

    await waitFor(() => expect(use).toBeEnabled());
    expect(card).toHaveAttribute("data-draft-current", "true");
    fireEvent.click(use);
    expect((screen.getByLabelText("Research question 1") as HTMLTextAreaElement).value).toContain("achieve FPS on a public benchmark for embedded cameras");
  });

  it("shows DRAFT_INCOMPLETE as the fields the engine names, with links", async () => {
    setUp({ draft: {} });
    render(<InceptionShape locale="en" />);
    const card = await screen.findByRole("heading", { name: "A few answers are still missing" });
    const missing = card.closest("[data-refusal]")!.querySelector("[data-missing]") as HTMLElement;
    expect(within(missing).getByText("Research topic")).toBeInTheDocument();
    expect(within(missing).getByRole("link", { name: "Go to Scope" })).toHaveAttribute("href", `/en/inception/scope/?draft=${SESSION}`);
  });

  it("goes back to Direction, step 3 (M4d)", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionShape locale="en" />);
    expect(await screen.findByRole("link", { name: "Back to Direction" })).toHaveAttribute("href", `/en/inception/direction/?draft=${SESSION}`);
  });
});
