import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionCriteria, normaliseReason } from "@/components/inception-criteria";
import { InceptionReview } from "@/components/inception-review";
import { InceptionShape } from "@/components/inception-shape";
import { completeDraft, outOfScopeId, proofId, SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/**
 * M10b Part A: the draft's own answers. The planned number of records and the
 * optional proof (`04-shape`), a reason on every exclusion and the researcher's
 * own matrix columns (`05-criteria`), and the Review wording of the strict run
 * of 2026-11-13 (findings 8 and 9).
 */

afterEach(() => vi.unstubAllGlobals());

const putDraft = (engine: ReturnType<typeof setUp>["engine"]) => engine.calls.filter((c) => c.method === "PUT").at(-1)?.body?.draft as Record<string, unknown>;

describe("inception.shape planned records (M10b)", () => {
  it("is empty on load although a playbook is chosen; the preset is offered, not filled", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionShape locale="en" />);
    const card = (await screen.findByText("This playbook usually plans 50 to 200.")).closest("[data-planned]") as HTMLElement;
    expect(within(card).getByLabelText("from")).toHaveValue(null);
    expect(within(card).getByLabelText("up to")).toHaveValue(null);
    expect(within(card).queryByText(/Recommended/)).toBeNull();
  });

  it("'Use this range' fills both numbers and sends nothing until the save", async () => {
    const { engine, assign } = setUp({ draft: completeDraft() });
    render(<InceptionShape locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Use this range" }, { timeout: 5000 }));
    expect(screen.getByLabelText("from")).toHaveValue(50);
    expect(screen.getByLabelText("up to")).toHaveValue(200);
    expect(engine.calls.filter((c) => c.method === "PUT")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Continue to concepts and criteria" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(putDraft(engine)).toMatchObject({ pool_min: 50, pool_max: 200 });
  });

  it("says what to fix in an impossible range and keeps Continue from saving it", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionShape locale="en" />);
    fireEvent.change(await screen.findByLabelText("from"), { target: { value: "300" } });
    fireEvent.change(screen.getByLabelText("up to"), { target: { value: "150" } });
    expect(screen.getByRole("alert")).toHaveTextContent("The first number cannot be larger than the second.");
    expect(screen.getByRole("button", { name: "Continue to concepts and criteria" })).toBeDisabled();
  });

  it("Continue is enabled with the card empty", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionShape locale="en" />);
    await screen.findByText("This playbook usually plans 50 to 200.");
    expect(screen.getByRole("button", { name: "Continue to concepts and criteria" })).toBeEnabled();
  });
});

describe("inception.shape optional proof (M10b)", () => {
  it("marks the proof optional only when the engine says proof_required is false", async () => {
    setUp({ draft: completeDraft({ proof: "", extra_inclusions: ["Field trials with UAV imagery"] }) });
    render(<InceptionShape locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-proof-optional]")).not.toBeNull());
    expect(screen.getByLabelText(/Proof a reviewer would accept/, { selector: "input" })).toHaveAccessibleName(/optional: this review already has an inclusion criterion/);
    // No proof answer: no template question is offered.
    expect(screen.getByRole("button", { name: /Use this draft as RQ/ })).toBeDisabled();
  });

  it("is not optional without a typed inclusion", async () => {
    setUp({ draft: completeDraft({ proof: "" }) });
    render(<InceptionShape locale="en" />);
    await screen.findByText("This playbook usually plans 50 to 200.");
    expect(document.querySelector("[data-proof-optional]")).toBeNull();
  });
});

describe("inception.criteria reasons (M10b)", () => {
  it("normalises typing: lower case to upper, spaces to _, other characters refused", () => {
    expect(normaliseReason("wrong task")).toEqual({ value: "WRONG_TASK", refused: false });
    expect(normaliseReason("wrong-task!")).toEqual({ value: "WRONGTASK", refused: true });
  });

  it("shows every exclusion's reason and lets the researcher change an out-of-scope line's", async () => {
    const { engine, assign } = setUp({ draft: completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } }) });
    render(<InceptionCriteria locale="en" />);
    const row = (await screen.findByText("closed-source models")).closest("li") as HTMLElement;
    expect(within(row).getByText("Reason OUT_OF_SCOPE")).toBeInTheDocument();
    fireEvent.click(within(row).getByRole("button", { name: /Change the reason of E1/ }));
    fireEvent.change(within(row).getByLabelText("Reason"), { target: { value: "wrong platform" } });
    fireEvent.click(within(row).getByRole("button", { name: "Use this reason" }));
    await waitFor(() => expect(screen.getByText("Reason WRONG_PLATFORM")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(putDraft(engine)).toMatchObject({ out_of_scope_reasons: { "closed-source models": "WRONG_PLATFORM" } });
  });

  it("adds an exclusion only with a reason, and the reason list is the engine's with nothing chosen", async () => {
    const { engine } = setUp({ draft: completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } }) });
    render(<InceptionCriteria locale="en" />);
    const side = (await screen.findByText("closed-source models")).closest("[data-side]") as HTMLElement;
    fireEvent.change(within(side).getByLabelText("Add an exclusion criterion"), { target: { value: "Simulation only" } });
    const add = within(side).getByRole("button", { name: "Add" });
    expect(add).toBeDisabled();
    expect(within(side).getByText("Choose a reason before you add this exclusion.")).toBeInTheDocument();
    const reason = within(side).getAllByLabelText("Reason").at(-1) as HTMLInputElement;
    expect(reason.value).toBe("");
    const options = [...document.querySelectorAll("#criteria-new-exclusion-reason-list option")].map((o) => (o as HTMLOptionElement).value);
    expect(options).toContain("WRONG_POPULATION");
    fireEvent.change(reason, { target: { value: "wrong report type" } });
    expect(add).toBeEnabled();
    fireEvent.click(add);
    await waitFor(() => expect(screen.getByText("Simulation only")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    await waitFor(() => expect(putDraft(engine)?.extra_exclusions).toEqual([{ criterion: "Simulation only", reason_category: "WRONG_REPORT_TYPE" }]));
  });

  it("offers no Change reason on a dropped row and flags a saved code that breaks the rule", async () => {
    setUp({ draft: completeDraft({ out_of_scope: [], extra_exclusions: [{ criterion: "Old", reason_category: "old" }], criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } }) });
    render(<InceptionCriteria locale="en" />);
    const row = (await screen.findByText("Old")).closest("li") as HTMLElement;
    expect(within(row).getByText("This code does not follow the rule; fix it before you save.")).toBeInTheDocument();
    fireEvent.click(within(row).getByRole("button", { name: "Reject" }));
    await waitFor(() => expect(within(row).getByText("Restore it to change its reason.")).toBeInTheDocument());
    expect(within(row).queryByRole("button", { name: /Change the reason/ })).toBeNull();
  });
});

describe("inception.criteria own matrix columns (M10b)", () => {
  it("adds a column apart from the suggestions, without a checkbox, and saves it", async () => {
    const { engine, assign } = setUp({ draft: completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } }) });
    render(<InceptionCriteria locale="en" />);
    const group = (await screen.findByText("Your columns")).closest("[data-own-columns]") as HTMLElement;
    expect(within(group).getByText("None yet. Add the columns your review needs.")).toBeInTheDocument();
    const addColumn = within(group).getByRole("button", { name: "Add column" });
    fireEvent.change(within(group).getByLabelText("Column name"), { target: { value: "Sensor" } });
    expect(addColumn).toBeDisabled(); // a description is needed
    fireEvent.change(within(group).getByLabelText("What should be extracted?"), { target: { value: "Camera on the UAV" } });
    fireEvent.change(within(group).getByLabelText("Type of value"), { target: { value: "categorical" } });
    fireEvent.click(within(group).getByLabelText("Required: flag papers that do not report it"));
    fireEvent.click(addColumn);
    const card = await within(group).findByText("Sensor");
    const item = card.closest("li") as HTMLElement;
    expect(within(item).getByText("Typed by you")).toBeInTheDocument();
    expect(within(item).queryByRole("checkbox")).toBeNull();
    await waitFor(() => expect(within(item).getByText("sensor")).toBeInTheDocument()); // the engine's derived id
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(putDraft(engine).custom_matrix_columns).toEqual([{ name: "Sensor", description: "Camera on the UAV", data_type: "categorical", required: true }]);
  });

  it("refuses a second column of the same name before the engine does, and removes one", async () => {
    setUp({ draft: completeDraft({ custom_matrix_columns: [{ name: "Sensor", description: "d" }], criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } }) });
    render(<InceptionCriteria locale="en" />);
    const group = (await screen.findByText("Your columns")).closest("[data-own-columns]") as HTMLElement;
    fireEvent.change(within(group).getByLabelText("Column name"), { target: { value: "sensor" } });
    expect(within(group).getByText("A column named sensor already exists.")).toBeInTheDocument();
    fireEvent.click(within(group).getByRole("button", { name: "Remove Sensor" }));
    await waitFor(() => expect(within(group).getByText("None yet. Add the columns your review needs.")).toBeInTheDocument());
  });
});

describe("inception.review wording (M10b, strict run findings 8 and 9)", () => {
  const decided = (extra: Record<string, unknown> = {}) => completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true }, ...extra });

  it("lists each concept with its synonyms", async () => {
    setUp({ draft: decided({ concepts: [{ concept: "weed detection", synonyms: ["weed mapping", "weed segmentation"] }, { concept: "UAV", synonyms: [] }] }) });
    render(<InceptionReview locale="en" />);
    await waitFor(() => expect(document.querySelector('[data-review-concept="weed detection"]')).not.toBeNull(), { timeout: 5000 });
    const row = document.querySelector('[data-review-concept="weed detection"]') as HTMLElement;
    expect(row).toHaveTextContent("weed detection · synonyms: weed mapping, weed segmentation");
    expect(document.querySelector('[data-review-concept="UAV"]')).toHaveTextContent("UAV · no synonyms");
  });

  it("puts the folder path inside the gate sentence, with no full stop before it", async () => {
    setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    const body = (await screen.findByText(/Writes the protocol, the criteria and the first audit journal entries into/)).closest("p") as HTMLElement;
    await waitFor(() => expect(body.textContent).toMatch(/on-device-weed-detection\.$/));
    expect(body.textContent).not.toMatch(/into \./);
  });

  it("says the planned records, stated or not", async () => {
    setUp({ draft: decided({ pool_min: 150, pool_max: 300 }) });
    const { unmount } = render(<InceptionReview locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-review-planned]")).toHaveTextContent("Planned records150 to 300"));
    unmount();
    vi.unstubAllGlobals();
    setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-review-planned]")).toHaveTextContent("Not stated (the playbook's 50 to 200 is written)"));
  });
});

void SESSION;
