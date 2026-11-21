import { fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, postedEvents, press, renderCharting } from "./charting-helpers";

/** Spec 01 "Keyboard" and "Accessibility": the inline confirmation line for a status on several rows. */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-study-row="${id}"]`) as HTMLElement;
const line = () => document.querySelector("[data-confirm-line]") as HTMLElement;

async function selectThree() {
  rowOf("STU-002").focus();
  await press("x");
  await press("J", { shiftKey: true });
  await press("J", { shiftKey: true });
}

describe("charting.bulk-confirm", () => {
  it("shows the inline line, announced politely, not a dialog; Enter sends one request with one event per record", async () => {
    const engine = installEngine(makeTable([1, 2, 3, 4, 5].map((i) => makeRow(i))));
    await renderCharting();
    await selectThree();
    await press("r");
    expect(line()).toHaveAttribute("aria-live", "polite");
    expect(line()).toHaveTextContent("Mark 3 records as Retrieved? Enter to confirm · Esc to cancel");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(postedEvents(engine)).toHaveLength(0);
    await press("Enter");
    const sent = postedEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0].map((e) => e.study_id)).toEqual(["STU-002", "STU-003", "STU-004"]);
    expect(line()).toBeEmptyDOMElement();
    expect(screen.getByText("3 records saved")).toBeInTheDocument();
    // Focus stays on the first changed row.
    expect(document.activeElement).toBe(rowOf("STU-002"));
  });

  it("Esc cancels: nothing is sent and the line closes", async () => {
    const engine = installEngine(makeTable([1, 2, 3, 4].map((i) => makeRow(i))));
    await renderCharting();
    await selectThree();
    await press("q");
    expect(line()).toHaveTextContent("Mark 3 records as Requested?");
    await press("Escape");
    expect(line()).toBeEmptyDOMElement();
    expect(postedEvents(engine)).toHaveLength(0);
  });

  it("Not retrieved on several rows asks one reason for all of them, then one event per record", async () => {
    const engine = installEngine(makeTable([1, 2, 3, 4].map((i) => makeRow(i))));
    await renderCharting();
    await selectThree();
    await press("n");
    expect(line()).toHaveTextContent("Mark 3 records as Not retrieved?");
    await press("3");
    await press("Enter");
    const sent = postedEvents(engine)[0];
    expect(sent).toHaveLength(3);
    expect(sent.every((e) => JSON.stringify(e.value) === JSON.stringify({ status: "not_retrieved", reason: "no_reply" }))).toBe(true);
  });

  it("the Confirm button does what Enter does; one undo takes the whole action back", async () => {
    const engine = installEngine(makeTable([1, 2, 3, 4].map((i) => makeRow(i))));
    await renderCharting();
    await selectThree();
    await press("g");
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    await press("Shift");
    expect(postedEvents(engine)).toHaveLength(1);
    await press("z");
    const undo = postedEvents(engine)[1];
    expect(undo).toHaveLength(3);
    expect(undo.every((e) => typeof e.supersedes === "string")).toBe(true);
  });

  it("a row no longer kept is left out of a bulk action", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2), makeRow(3, { kept: false })]));
    await renderCharting();
    rowOf("STU-001").focus();
    await press("a");
    await press("r");
    expect(line()).toHaveTextContent("Mark 2 records as Retrieved?");
    await press("Enter");
    expect(postedEvents(engine)[0].map((e) => e.study_id)).toEqual(["STU-001", "STU-002"]);
  });
});
