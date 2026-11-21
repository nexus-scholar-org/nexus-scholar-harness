import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { cellEvents, flush, installEngine, makeChartingTable, makeRow, renderCharting, renderStudy, uavColumns, withCells } from "./charting-helpers";

/**
 * Spec 02 "Partial", Chart again (M12a Part B, DoD 12): after a form amendment a
 * touched field carries "Chart again" and the earlier value under "Earlier
 * value", read-only; charting it again sends a new event that supersedes the
 * cell, and the mark goes. The table shows the same history (spec 01).
 */

afterEach(() => vi.unstubAllGlobals());

const ev = (n: number) => `0190a0a0-0000-7000-8000-${String(n).padStart(12, "0")}`;

function amended() {
  const columns = uavColumns();
  // "By date" was removed from the split options: the cell keeps its value and must be charted again.
  columns[3] = { ...columns[3], options: ["Random tiles", "By field", "By camera"] };
  // A split column: the new one is empty and shows the value of the column it came from.
  columns[1] = { ...columns[1], column_id: "camera_models", name: "Cameras", derived_from: ["cameras"], from_protocol: null };
  const row = withCells(makeRow(1), columns, {
    split: { state: "value", value: "By date", event_id: ev(1), chart_again: true, history: [{ state: "value", value: "By date", note: null, where_from: null, at: null, form_version: 1, event_id: ev(1) }] },
    camera_models: { chart_again: true, history: [{ state: "value", value: "RedEdge-M; no cross-camera test", note: null, where_from: null, at: null, form_version: 1, event_id: ev(2), column: "Cameras and evaluation design" }] },
  });
  return makeChartingTable([row], columns, {}, { has_values: true, version: 2 });
}

describe("charting-study.history", () => {
  it("each touched field carries Chart again and the earlier value, read-only", async () => {
    installEngine(amended());
    await renderStudy("STU-001");
    const split = document.querySelector('[data-field="split"]') as HTMLElement;
    expect(split.querySelector("[data-mark=chart-again]")).toHaveTextContent("Chart again");
    expect(split.querySelector("[data-history]")).toHaveTextContent("Earlier value: By date");
    const cameras = document.querySelector('[data-field="camera_models"]') as HTMLElement;
    expect(cameras.querySelector("[data-mark=chart-again]")).not.toBeNull();
    expect(cameras.querySelector("[data-history]")).toHaveTextContent("Earlier value, in Cameras and evaluation design: RedEdge-M; no cross-camera test");
    // The history is words, not a field.
    expect(cameras.querySelector("[data-history] input, [data-history] textarea")).toBeNull();
    // The removed option is not offered any more.
    expect(Array.from(split.querySelectorAll("[data-option]")).map((o) => o.getAttribute("data-option"))).toEqual(["Random tiles", "By field", "By camera"]);
  });

  it("charting the field again supersedes the cell and the mark goes; the earlier value stays in the history", async () => {
    const engine = installEngine(amended());
    await renderStudy("STU-001");
    const split = document.querySelector('[data-field="split"]') as HTMLElement;
    const radios = split.querySelectorAll<HTMLInputElement>("input[type=radio]");
    radios[2].focus();
    fireEvent.click(radios[2]);
    fireEvent.blur(split.querySelector("fieldset")!, { relatedTarget: document.body });
    await flush();
    expect(cellEvents(engine)[0]).toMatchObject({ value: { column_id: "split", state: "value", value: "By camera" }, supersedes: ev(1) });
    expect(split.querySelector("[data-mark=chart-again]")).toBeNull();
    expect(engine.table.rows[0].cells!.split.history.at(-1)).toMatchObject({ value: "By date" });
  });

  it("the table shows the same mark and earlier value in the cell", async () => {
    installEngine(amended());
    await renderCharting("en", "?view=charting");
    const cell = document.querySelector('[data-cell="STU-001:2"]') as HTMLElement;
    expect(cell.querySelector("[data-mark=chart-again]")).toHaveTextContent("Chart again");
    expect(cell.querySelector("[data-history]")).toHaveTextContent("Earlier value, in Cameras and evaluation design: RedEdge-M; no cross-camera test");
    expect(cell).toHaveTextContent("Not charted");
  });
});
