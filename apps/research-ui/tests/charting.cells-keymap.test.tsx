import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { chartingKey } from "@/lib/charting-logic";

import { cellEvents, flush, installEngine, makeChartingTable, makeRow, postedEvents, press, renderCharting, uavColumns, withCells } from "./charting-helpers";

/**
 * Spec 01 "Keyboard", the Charting view (M12a Part B): arrows move between
 * cells; Enter edits the focused cell, Enter saves and moves down, Esc cancels;
 * Alt+N Not reported and Alt+A Not applicable on the focused cell; Enter on the
 * study cell opens the one-study view; Z undoes; one event per saved field.
 */

afterEach(() => {
  vi.unstubAllGlobals();
  document.documentElement.removeAttribute("dir");
});

const cellAt = (id: string, col: number) => document.querySelector(`[data-cell="${id}:${col}"]`) as HTMLElement;
const editorInput = () => document.querySelector("[data-cell-editor] input") as HTMLInputElement;

async function threeRows() {
  const engine = installEngine(makeChartingTable([makeRow(1), makeRow(2), makeRow(3)]));
  await renderCharting("en", "?view=charting");
  cellAt("STU-001", 0).focus();
  return engine;
}

describe("charting.cells-keymap", () => {
  it("the arrows move between cells, down and up between rows; the focus never leaves the grid", async () => {
    await threeRows();
    await press("ArrowRight");
    expect(document.activeElement).toBe(cellAt("STU-001", 1));
    await press("ArrowRight");
    await press("ArrowDown");
    expect(document.activeElement).toBe(cellAt("STU-002", 2));
    await press("j");
    expect(document.activeElement).toBe(cellAt("STU-003", 2));
    await press("ArrowDown");
    expect(document.activeElement).toBe(cellAt("STU-003", 2));
    await press("ArrowLeft");
    await press("ArrowLeft");
    await press("ArrowLeft");
    expect(document.activeElement).toBe(cellAt("STU-003", 0));
    await press("k");
    expect(document.activeElement).toBe(cellAt("STU-002", 0));
    // One tab stop: the focused cell.
    expect(document.querySelectorAll("[role=grid] [tabindex='0']")).toHaveLength(1);
  });

  it("in Arabic the arrows follow the mirrored columns", () => {
    const base = { ctrlKey: false, metaKey: false, altKey: false, shiftKey: false };
    expect(chartingKey({ ...base, key: "ArrowLeft" }, document.body, "rtl")).toBe("arrowEnd");
    expect(chartingKey({ ...base, key: "ArrowRight" }, document.body, "rtl")).toBe("arrowStart");
    expect(chartingKey({ ...base, key: "ArrowLeft" }, document.body, "ltr")).toBe("arrowStart");
    expect(chartingKey({ ...base, key: "n", altKey: true, code: "KeyN" }, document.body)).toBe("notReported");
    // macOS gives Alt+N as a dead key; the physical key still says N.
    expect(chartingKey({ ...base, key: "Dead", altKey: true, code: "KeyN" }, document.body)).toBe("notReported");
    expect(chartingKey({ ...base, key: "å", altKey: true, code: "KeyA" }, document.body)).toBe("notApplicable");
  });

  it("Enter edits a text cell; Enter saves it as one event and moves down; the value shows at once", async () => {
    const engine = await threeRows();
    await press("ArrowRight");
    await press("ArrowRight");
    await press("Enter");
    expect(document.activeElement).toBe(editorInput());
    expect(editorInput()).toHaveAccessibleName("Cameras and evaluation design, Study number 1");
    fireEvent.change(editorInput(), { target: { value: "RedEdge-M and Sequoia" } });
    await press("Enter");
    await flush();
    const sent = postedEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0]).toHaveLength(1);
    expect(sent[0][0]).toMatchObject({ study_id: "STU-001", kind: "cell", value: { column_id: "cameras", state: "value", value: "RedEdge-M and Sequoia" } });
    expect(sent[0][0].supersedes).toBeUndefined();
    expect(cellAt("STU-001", 2)).toHaveTextContent("RedEdge-M and Sequoia");
    expect(document.activeElement).toBe(cellAt("STU-002", 2));
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Saved");
    // A change of a charted cell supersedes the event that holds it.
    await press("ArrowUp");
    await press("Enter");
    fireEvent.change(editorInput(), { target: { value: "Sequoia" } });
    await press("Enter");
    await flush();
    expect(cellEvents(engine)[1].supersedes).toBe(cellEvents(engine)[0].event_id);
  });

  it("Esc cancels the edit: nothing is sent and the focus returns to the cell", async () => {
    const engine = await threeRows();
    await press("ArrowRight");
    await press("ArrowRight");
    await press("Enter");
    fireEvent.change(editorInput(), { target: { value: "Typed, then thought better of" } });
    await press("Escape");
    await flush();
    expect(document.querySelector("[data-cell-editor]")).toBeNull();
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.activeElement).toBe(cellAt("STU-001", 2));
    // An unchanged value sends nothing either.
    await press("Enter");
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(0);
  });

  it("a number cell sends a JSON number; words that are not a number stay here with their sentence", async () => {
    const engine = await threeRows();
    await press("ArrowRight");
    await press("ArrowRight");
    await press("ArrowRight");
    await press("Enter");
    fireEvent.change(editorInput(), { target: { value: "many" } });
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("Type a number, for example 1260 or 2.5.");
    expect(document.activeElement).toBe(cellAt("STU-001", 3));
    await press("Enter");
    fireEvent.change(editorInput(), { target: { value: "1 260" } });
    await press("Enter");
    await flush();
    expect(cellEvents(engine)[0].value).toEqual({ column_id: "n_images", state: "value", value: 1260 });
  });

  it("a list cell shows its options: one for One of a list, several for Several of a list, Yes and No translated", async () => {
    const engine = await threeRows();
    await press("ArrowRight");
    await press("Enter");
    const boxes = document.querySelectorAll<HTMLInputElement>("[data-cell-editor] input[type=checkbox]");
    expect(Array.from(boxes).map((b) => b.dataset.editorOption)).toEqual(["Misregistration", "Missing band", "Change of camera"]);
    fireEvent.click(boxes[2]);
    fireEvent.click(boxes[0]);
    await press("Enter");
    await flush();
    expect(cellEvents(engine)[0].value).toEqual({ column_id: "sensor_problems", state: "value", value: ["Misregistration", "Change of camera"] });
    // One of a list.
    await press("ArrowUp");
    await press("ArrowRight");
    await press("ArrowRight");
    await press("ArrowRight");
    await press("Enter");
    const radios = document.querySelectorAll<HTMLInputElement>("[data-cell-editor] input[type=radio]");
    fireEvent.click(radios[1]);
    await press("Enter");
    await flush();
    expect(cellEvents(engine)[1].value).toEqual({ column_id: "split", state: "value", value: "By field" });
    await press("ArrowUp");
    await press("ArrowRight");
    await press("Enter");
    expect(Array.from(document.querySelectorAll("[data-cell-editor] label")).map((l) => l.textContent)).toEqual(["Yes", "No"]);
  });

  it("Alt+N and Alt+A set Not reported and Not applicable on the focused cell; the same keys clear it", async () => {
    const engine = await threeRows();
    await press("ArrowRight");
    await press("n", { altKey: true, code: "KeyN" });
    await flush();
    expect(cellEvents(engine)[0].value).toEqual({ column_id: "sensor_problems", state: "not_reported", value: null });
    expect(cellAt("STU-001", 1)).toHaveTextContent("Not reported");
    await press("a", { altKey: true, code: "KeyA" });
    await flush();
    expect(cellEvents(engine)[1]).toMatchObject({ value: { state: "not_applicable" }, supersedes: cellEvents(engine)[0].event_id });
    expect(cellAt("STU-001", 1)).toHaveTextContent("Not applicable");
    await press("a", { altKey: true, code: "KeyA" });
    await flush();
    expect(cellEvents(engine)[2].value).toEqual({ column_id: "sensor_problems", state: null, value: null });
    expect(cellAt("STU-001", 1)).toHaveTextContent("Not charted");
    // On the study cell they do nothing.
    await press("ArrowLeft");
    await press("n", { altKey: true, code: "KeyN" });
    expect(cellEvents(engine)).toHaveLength(3);
  });

  it("Z undoes a cell with an event that carries the earlier value, its note and where-from", async () => {
    const columns = uavColumns();
    const engine = installEngine(
      makeChartingTable([withCells(makeRow(1), columns, { cameras: { state: "value", value: "Sequoia", note: "n", where_from: "p. 2", event_id: "0190a0a0-0000-7000-8000-000000000001" } })], columns, {}, { has_values: true }),
    );
    await renderCharting("en", "?view=charting");
    cellAt("STU-001", 2).focus();
    await press("n", { altKey: true, code: "KeyN" });
    await flush();
    // Not reported keeps the cell's note and where-from.
    expect(cellEvents(engine)[0]).toMatchObject({ value: { state: "not_reported" }, note: "n", where_from: "p. 2", supersedes: "0190a0a0-0000-7000-8000-000000000001" });
    await press("z");
    await flush();
    expect(cellEvents(engine)[1]).toMatchObject({ value: { column_id: "cameras", state: "value", value: "Sequoia" }, note: "n", where_from: "p. 2", supersedes: cellEvents(engine)[0].event_id });
    expect(cellAt("STU-001", 2)).toHaveTextContent("Sequoia");
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Undone");
  });

  it("Enter on the study cell opens the one-study view on the same view and filter", async () => {
    installEngine(makeChartingTable([makeRow(1), makeRow(2)]));
    const assign = vi.fn();
    await renderCharting("en", "?view=charting&show=notCharted");
    vi.stubGlobal("location", { ...window.location, assign, search: window.location.search, pathname: window.location.pathname });
    cellAt("STU-002", 0).focus();
    await press("Enter");
    expect(assign).toHaveBeenCalledWith("/en/charting/study?view=charting&show=notCharted&id=STU-002");
  });

  it("the full-text keys rest in the Charting view", async () => {
    const engine = await threeRows();
    for (const key of ["r", "g", "i", "e", "x", "a"]) await press(key);
    expect(postedEvents(engine)).toHaveLength(0);
  });
});
