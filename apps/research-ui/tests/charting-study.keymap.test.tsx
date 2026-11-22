import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { cellEvents, flush, installEngine, makeChartingTable, makeRow, press, renderStudy, uavColumns, withCells } from "./charting-helpers";

/**
 * Spec 02 "Keyboard" (M12a Part B): J/K and Ctrl+Down/Ctrl+Up save and move to the
 * next or previous study of the table's list; Esc goes back to the same row and
 * filter; Alt+N and Alt+A set the two special values on the focused field; Enter
 * in a single-line field saves and moves to the next field; Z undoes.
 */

afterEach(() => vi.unstubAllGlobals());

const field = (id: string) => document.querySelector(`[data-field="${id}"]`) as HTMLElement;
const input = (id: string) => field(id).querySelector("[data-value-input]") as HTMLInputElement;

function threeStudies() {
  return makeChartingTable([
    makeRow(1, { abstract: "Weeds were mapped from UAV images taken with a RedEdge-M camera." }),
    makeRow(2, { abstract: "Sugar beet rows." }),
    makeRow(3, { abstract: null }),
  ]);
}

describe("charting-study.keymap", () => {
  it("Ctrl+Down inside a field saves it first, then opens the next study and says where it is", async () => {
    const engine = installEngine(threeStudies());
    await renderStudy("STU-001");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Study number 1");
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 1 of 3");
    input("cameras").focus();
    fireEvent.change(input("cameras"), { target: { value: "RedEdge-M" } });
    await press("ArrowDown", { ctrlKey: true });
    await flush();
    const sent = cellEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0]).toMatchObject({ study_id: "STU-001", kind: "cell", value: { column_id: "cameras", state: "value", value: "RedEdge-M" } });
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 2 of 3");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Study number 2");
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Study 2 of 3. Saved.");
    // The focus lands on the first field of the next study.
    expect(field("sensor_problems").contains(document.activeElement)).toBe(true);
    expect(window.location.search).toContain("id=STU-002");
    await press("ArrowUp", { ctrlKey: true });
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 1 of 3");
    // The saved value is there when the study comes back.
    expect(input("cameras").value).toBe("RedEdge-M");
  });

  it("J and K move outside a text field; a field the researcher did not change sends nothing", async () => {
    const engine = installEngine(threeStudies());
    await renderStudy("STU-002");
    (document.querySelector("[data-region=study]") as HTMLElement).focus();
    await press("j");
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 3 of 3");
    // The last study: the brand button goes back to the table.
    expect(document.querySelector("[data-next-study]")).toHaveTextContent("Back to the table");
    (document.querySelector("[data-region=study]") as HTMLElement).focus();
    await press("k");
    await press("k");
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 1 of 3");
    expect(cellEvents(engine)).toHaveLength(0);
    // J and K are off in a text field.
    input("cameras").focus();
    await press("j");
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 1 of 3");
  });

  it("Esc saves and goes back to the table on the same row, view and filter", async () => {
    const engine = installEngine(threeStudies());
    const assign = vi.fn();
    await renderStudy("STU-002", "en", "&view=charting&show=notCharted");
    vi.stubGlobal("location", { ...window.location, assign, search: window.location.search, pathname: window.location.pathname });
    input("n_images").focus();
    fireEvent.change(input("n_images"), { target: { value: "1260" } });
    await press("Escape");
    await flush();
    expect(cellEvents(engine)[0]).toMatchObject({ value: { column_id: "n_images", state: "value", value: 1260 } });
    expect(assign).toHaveBeenCalledWith("/en/charting?view=charting&show=notCharted&row=STU-002");
  });

  it("the list is the table's Show list: a charted study is not a neighbour under Not charted", async () => {
    const columns = uavColumns();
    const done = Object.fromEntries(columns.map((c) => [c.column_id, { state: "not_reported" as const, event_id: "0190a0a0-0000-7000-8000-00000000000" + c.column_id.length }]));
    installEngine(makeChartingTable([makeRow(1), withCells(makeRow(2), columns, done), makeRow(3)], columns));
    await renderStudy("STU-001", "en", "&view=charting&show=notCharted");
    expect(document.querySelector("[data-position]")).toHaveTextContent("Study 1 of 2");
    (document.querySelector("[data-region=study]") as HTMLElement).focus();
    await press("j");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Study number 3");
  });

  it("Alt+N and Alt+A set Not reported and Not applicable on the focused field; the same key clears it", async () => {
    const engine = installEngine(threeStudies());
    await renderStudy("STU-001");
    input("n_images").focus();
    await press("n", { altKey: true, code: "KeyN" });
    await flush();
    expect(cellEvents(engine)[0]).toMatchObject({ value: { column_id: "n_images", state: "not_reported", value: null } });
    const notReported = field("n_images").querySelector("[data-special=not_reported]") as HTMLElement;
    expect(notReported).toHaveTextContent("Not reported");
    expect(notReported).toHaveAttribute("aria-pressed", "true");
    expect(input("n_images")).toBeDisabled();
    expect(document.activeElement).toBe(notReported);
    await press("a", { altKey: true, code: "KeyA" });
    await flush();
    expect(cellEvents(engine)[1]).toMatchObject({ value: { column_id: "n_images", state: "not_applicable" }, supersedes: cellEvents(engine)[0].event_id });
    expect(field("n_images").querySelector("[data-special=not_applicable]")).toHaveAttribute("aria-pressed", "true");
    await press("a", { altKey: true, code: "KeyA" });
    await flush();
    expect(cellEvents(engine)[2]).toMatchObject({ value: { column_id: "n_images", state: null, value: null } });
    expect(input("n_images")).toBeEnabled();
  });

  it("Enter in a single-line field saves it and moves to the next field; Shift+Enter in Note adds a line", async () => {
    const engine = installEngine(threeStudies());
    await renderStudy("STU-001");
    input("cameras").focus();
    fireEvent.change(input("cameras"), { target: { value: "Sequoia" } });
    await press("Enter");
    await flush();
    expect(cellEvents(engine)).toHaveLength(1);
    expect(document.activeElement).toBe(input("n_images"));
    const note = field("cameras").querySelector("[data-note]") as HTMLTextAreaElement;
    note.focus();
    fireEvent.change(note, { target: { value: "One model per camera" } });
    await press("Enter", { shiftKey: true });
    expect(cellEvents(engine)).toHaveLength(1);
    const where = field("cameras").querySelector("[data-where-from]") as HTMLInputElement;
    where.focus();
    fireEvent.change(where, { target: { value: "Methods, p. 4" } });
    await press("Enter");
    await flush();
    expect(cellEvents(engine)[1]).toMatchObject({ value: { column_id: "cameras", state: "value", value: "Sequoia" }, note: "One model per camera", where_from: "Methods, p. 4" });
  });

  it("a list field saves its choice when the focus leaves it; Z undoes the last change", async () => {
    const engine = installEngine(threeStudies());
    await renderStudy("STU-001");
    const options = field("sensor_problems").querySelectorAll<HTMLInputElement>("input[type=checkbox]");
    options[0].focus();
    fireEvent.click(options[0]);
    fireEvent.click(options[2]);
    fireEvent.blur(field("sensor_problems").querySelector("fieldset")!, { relatedTarget: document.body });
    await flush();
    expect(cellEvents(engine)[0]).toMatchObject({ value: { column_id: "sensor_problems", state: "value", value: ["Misregistration", "Change of camera"] } });
    (document.querySelector("[data-region=study]") as HTMLElement).focus();
    await press("z");
    await flush();
    expect(cellEvents(engine)[1]).toMatchObject({ value: { column_id: "sensor_problems", state: null, value: null }, supersedes: cellEvents(engine)[0].event_id });
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Undone");
    expect(field("sensor_problems").querySelectorAll("input:checked")).toHaveLength(0);
  });

  it("a number that does not read as one stays on the screen with its words and nothing is sent", async () => {
    const engine = installEngine(threeStudies());
    await renderStudy("STU-001");
    input("n_images").focus();
    fireEvent.change(input("n_images"), { target: { value: "many" } });
    fireEvent.blur(input("n_images"));
    await flush();
    expect(cellEvents(engine)).toHaveLength(0);
    expect(within(field("n_images")).getByRole("alert")).toHaveTextContent("Type a number, for example 1260 or 2.5.");
  });

  it("a value the engine refuses returns the field to its saved value with the refusal beside it", async () => {
    const engine = installEngine(threeStudies(), { refuse: { "STU-001": "CHARTING_VALUE_INVALID" } });
    await renderStudy("STU-001");
    // Spaces are an empty field: nothing to clear, nothing sent.
    input("cameras").focus();
    fireEvent.change(input("cameras"), { target: { value: "   " } });
    fireEvent.blur(input("cameras"));
    await flush();
    expect(cellEvents(engine)).toHaveLength(0);
    fireEvent.change(input("cameras"), { target: { value: "Sequoia" } });
    fireEvent.blur(input("cameras"));
    await flush();
    expect(cellEvents(engine)).toHaveLength(1);
    const alert = within(field("cameras")).getByRole("alert");
    expect(alert).toHaveTextContent("That value is not one of the options.");
    expect(within(alert).getByText("CHARTING_VALUE_INVALID")).toHaveAttribute("dir", "ltr");
    expect(input("cameras").value).toBe("");
  });
});
