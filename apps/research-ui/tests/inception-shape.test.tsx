import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionShape } from "@/components/inception-shape";
import { SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/** Spec 04 (M4b): lens cards with the engine's leaning, the playbook, the RQ template as a draft. */

afterEach(() => vi.unstubAllGlobals());

describe("inception.shape", () => {
  it("marks the engine's leaning, applies nothing, and drafts RQ1 only on request", async () => {
    const { engine, assign } = setUp({ draft: { topic: "weed detection" } });
    render(<InceptionShape locale="en" />);
    const card = (await screen.findByText("Design Science")).closest("label")!;
    expect(within(card).getByText("Leaning · word scan of your topic")).toBeInTheDocument();
    expect(within(card).getByRole("radio")).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Continue to concepts and criteria" })).toBeDisabled();
    expect(screen.getByText("Choose a lens to see the draft question.")).toBeInTheDocument();

    fireEvent.click(within(card).getByRole("radio"));
    const draftCard = await screen.findByText("Template draft · not yet yours");
    expect(screen.getByLabelText("Research question 1")).toHaveValue("");
    const playbook = screen.getByText("DESIGN_SCIENCE").closest("label")!;
    expect(within(playbook).getByText("Matches the lens")).toBeInTheDocument();
    expect(within(playbook).getByRole("radio")).not.toBeChecked();
    fireEvent.click(within(playbook).getByRole("radio"));

    // The template is filled from the unit and the proof: until both are answered it cannot be used.
    const card_ = draftCard.closest("[data-rq-draft]") as HTMLElement;
    const use = within(card_).getByRole("button", { name: "Use this draft as RQ1" });
    expect(use).toBeDisabled();
    expect(within(card_).getByText("Answer the unit and the proof first; the draft fills them in.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Unit of analysis"), { target: { value: "embedded cameras" } });
    fireEvent.change(screen.getByLabelText("Proof a reviewer would accept"), { target: { value: "mIoU and FPS" } });
    await waitFor(() => expect(use).toBeEnabled());
    fireEvent.click(use);
    expect((screen.getByLabelText("Research question 1") as HTMLTextAreaElement).value).toContain("weed detection");

    fireEvent.change(screen.getByLabelText("Out of scope"), { target: { value: "closed models\n\npre-2020" } });
    fireEvent.click(screen.getByRole("button", { name: "Continue to concepts and criteria" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith(`/en/inception/criteria/?draft=${SESSION}`));
    const put = engine.calls.find((c) => c.method === "PUT")!;
    expect(put.body?.draft).toMatchObject({ paradigm: "Design Science", playbook: "DESIGN_SCIENCE", out_of_scope: ["closed models", "pre-2020"] });
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
});
