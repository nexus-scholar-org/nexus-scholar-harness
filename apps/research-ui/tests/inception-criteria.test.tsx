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

  it("labels the matrix and the verification checks as parked", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("Parked: the Matrix phase that fills these columns is not in production.")).toBeInTheDocument();
    expect(screen.getByText(/Advisory: Phase 4 checks are parked/)).toBeInTheDocument();
    expect(screen.getByText("Ticked columns are saved in the protocol. With none ticked, the protocol has no matrix columns.")).toBeInTheDocument();
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

  it("shows each term's count in the pool and ticks a pool term into the synonyms only on a click (M4d)", async () => {
    const { engine } = setUp({ draft: completeDraft({ concepts: [{ concept: "weed detection", synonyms: ["quantum"] }] }) });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("weed detection: in 8 of 14")).toBeInTheDocument();
    const quantum = document.querySelector("[data-term='quantum']") as HTMLElement;
    expect(within(quantum).getByText("not in the pool")).toBeInTheDocument();
    const group = screen.getByRole("group", { name: "Terms from your first search for weed detection" });
    const boxes = within(group).getAllByRole("checkbox");
    expect(boxes.map((b) => b.getAttribute("data-suggestion"))).toEqual(["embedded hardware", "real-time"]);
    expect(boxes.every((b) => !(b as HTMLInputElement).checked)).toBe(true);
    const puts = () => engine.calls.filter((c) => c.method === "PUT");
    fireEvent.click(within(group).getByRole("checkbox", { name: "embedded hardware · 8 papers" }));
    expect(puts()).toHaveLength(0);
    fireEvent.click(within(group).getByRole("checkbox", { name: "real-time · 8 papers" }));
    fireEvent.click(within(group).getByRole("checkbox", { name: "real-time · 8 papers" }));
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    await waitFor(() => expect(puts()).toHaveLength(1));
    expect((puts()[0].body as { draft: { concepts: unknown } }).draft.concepts).toEqual([{ concept: "weed detection", synonyms: ["quantum", "embedded hardware"] }]);
  });

  it("with no pool shows no counts, no suggestions, a link to Explore, and never reads the concepts (M4d)", async () => {
    const { engine } = setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByRole("link", { name: "Go to Explore" })).toHaveAttribute("href", `/en/inception/explore/?draft=${SESSION}`);
    expect(document.querySelector("[data-anchoring]")).toBeNull();
    expect(engine.calls.some((c) => c.path.endsWith("/recon/concepts"))).toBe(false);
  });

  it("notes an earlier scope when the engine reports one (M4d)", async () => {
    const { engine } = setUp({ draft: completeDraft() });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    const record = engine.drafts.get(SESSION)!;
    engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), start_year: 2015 }, base_updated_at: record.updated_at });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText(/The pool was searched for an earlier scope; counts may not match./)).toBeInTheDocument();
  });
});
