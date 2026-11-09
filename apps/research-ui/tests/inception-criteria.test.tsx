import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionCriteria } from "@/components/inception-criteria";
import { completeDraft, proofId, SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/**
 * Spec 05 (M4b; INC-22): every criterion verbatim with its source; a generated
 * one waits for an explicit Accept (default no); typed ones are accepted unless
 * rejected; decisions are saved in `criteria_decisions` by the engine's ids.
 */

afterEach(() => vi.unstubAllGlobals());

const PROOF = "Reports the gold-standard proof — mIoU and FPS on a public benchmark";

describe("inception.criteria", () => {
  it("shows each criterion verbatim with its source; the generated one waits for you", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    const proof = (await screen.findByText(PROOF)).closest("li")!;
    expect(proof).toHaveAttribute("data-status", "undecided");
    expect(within(proof).getByText("Written by the wizard from your proof answer")).toBeInTheDocument();
    expect(within(proof).getByText("Waiting for you")).toBeInTheDocument();
    expect(within(proof).getByText("Written by the wizard: not in the protocol unless you accept it.")).toBeInTheDocument();
    expect(within(proof).getByRole("button", { name: "Accept" })).toHaveAttribute("aria-pressed", "false");
    const typed = screen.getByText("closed-source models").closest("li")!;
    expect(typed).toHaveAttribute("data-status", "accepted");
    expect(within(typed).getByText("Your out-of-scope answer")).toBeInTheDocument();
    expect(screen.getByText("1 still need you.")).toBeInTheDocument();
  });

  it("records Accept by the engine's id, then saves and goes to Review", async () => {
    const { engine, assign } = setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    const proof = (await screen.findByText(PROOF)).closest("li")!;
    fireEvent.click(within(proof).getByRole("button", { name: "Accept" }));
    await waitFor(() => expect(screen.getByText(PROOF).closest("li")).toHaveAttribute("data-status", "accepted"));
    expect(screen.getByText("Every criterion has your decision.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith(`/en/inception/review/?draft=${SESSION}`));
    const put = engine.calls.find((c) => c.method === "PUT")!;
    expect(put.body?.draft).toMatchObject({ criteria_decisions: { [proofId()]: true } });
  });

  it("adds and removes a typed criterion, names a missing side, and ticks every matrix column", async () => {
    setUp({ draft: completeDraft({ out_of_scope: [] }) });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("No exclusion criterion is accepted yet. Accept one above or add your own.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Add an exclusion criterion"), { target: { value: "Not peer reviewed" } });
    fireEvent.click(within(screen.getByText("Exclusion criteria").closest("section")!).getByRole("button", { name: "Add" }));
    const typed = (await screen.findByText("Not peer reviewed")).closest("li")!;
    expect(within(typed).getByText("Typed by you")).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText("No exclusion criterion is accepted yet. Accept one above or add your own.")).toBeNull());
    fireEvent.click(within(typed).getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(screen.queryByText("Not peer reviewed")).toBeNull());

    fireEvent.click(await screen.findByRole("button", { name: "Tick all suggested columns" }));
    expect(screen.getByRole("checkbox", { name: /Performance Metric/ })).toBeChecked();
  });

  it("offers the engine's suggested concepts as drafts", async () => {
    setUp({ draft: completeDraft({ concepts: [] }) });
    render(<InceptionCriteria locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Add weed" }));
    expect(screen.getByLabelText("Concept 1")).toHaveValue("weed");
  });

  it("shows source labels in Arabic, and keeps the criterion text as the engine wrote it", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="ar" />);
    const proof = (await screen.findByText(PROOF)).closest("li")!;
    expect(within(proof).getByText("كتبه المعالج من إجابتك عن الدليل")).toBeInTheDocument();
  });
});
