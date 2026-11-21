import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Cell, ChartingRow, FormColumn } from "@/lib/charting-api";

import { flush, installEngine, makeChartingTable, makeColumn, makeRow, press, renderCharting, withCells } from "./charting-helpers";

/**
 * DoD 14 (M12a Part B): "150 rows by 5 columns stay responsive". A fixture of
 * 150 kept studies and 5 form columns, about half the cells charted, is drawn in
 * the Charting view, then the focus walks the grid by keyboard and one cell is
 * edited and saved.
 *
 * The budget here is for this test runner: jsdom with the development build of
 * React, on a developer machine that may be busy with other work. It catches a
 * screen that redraws every row on each key, not the feel in a browser:
 *   - the first draw of the Charting view after the table's answer: under 4,000 ms;
 *   - one arrow key, with the focus moved to the next cell: under 150 ms on average
 *     over 120 moves (right, down and left through the grid);
 *   - one edit (Enter, a typed value, Enter): under 600 ms until the value shows.
 * The browser budget (the production build in Chromium) is in
 * `tests-browser/charting-study.spec.ts`: under 50 ms a move. Each row is a memoised
 * row, so a move re-renders the two rows the focus leaves and enters, and only the
 * desktop layout is drawn on a desktop window; the measured times are printed.
 */

afterEach(() => vi.unstubAllGlobals());

const ROWS = 150;
const BUDGET = { firstDrawMs: 4000, perMoveMs: 150, editMs: 600 };

function columns(): FormColumn[] {
  return [
    makeColumn("problems", { name: "Problems", type: "several", options: ["Misregistration", "Missing band", "Change of camera"] }),
    makeColumn("cameras", { name: "Cameras" }),
    makeColumn("images", { name: "Images", type: "number" }),
    makeColumn("split", { name: "Split", type: "one", options: ["Random tiles", "By field", "By date"] }),
    makeColumn("cross", { name: "Cross-camera", type: "yes_no", options: ["Yes", "No"] }),
  ];
}

function rows(cols: FormColumn[]): ChartingRow[] {
  return Array.from({ length: ROWS }, (_, i) => {
    const n = i + 1;
    if (n % 2 === 0) return makeRow(n);
    const cells: Record<string, Partial<Cell>> = {
      problems: { state: "value", value: ["Misregistration"], event_id: `0190a0a0-0000-7000-8000-${String(n * 10 + 1).padStart(12, "0")}` },
      cameras: { state: "value", value: `Camera ${n}`, event_id: `0190a0a0-0000-7000-8000-${String(n * 10 + 2).padStart(12, "0")}` },
      images: { state: n % 3 === 0 ? "not_reported" : "value", value: n % 3 === 0 ? null : n * 10, event_id: `0190a0a0-0000-7000-8000-${String(n * 10 + 3).padStart(12, "0")}` },
    };
    return withCells(makeRow(n), cols, cells);
  });
}

describe("charting.budget (DoD 14)", () => {
  it(`draws ${ROWS} rows by 5 columns and walks them by keyboard within the stated budget`, async () => {
    // A desktop window: the phone list is not drawn there.
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: query.includes("min-width"), media: query, addEventListener() {}, removeEventListener() {} }));
    const cols = columns();
    installEngine(makeChartingTable(rows(cols), cols, {}, { has_values: true, pilot: { on: false, ended_at: "2026-11-21T10:00:00Z", ended_by: "researcher:local" } }));

    const drawStart = performance.now();
    await renderCharting("en", "?view=charting");
    const firstDraw = performance.now() - drawStart;
    expect(document.querySelectorAll("[role=grid] tbody tr")).toHaveLength(ROWS);
    expect(document.querySelectorAll("[role=grid] [role=gridcell]")).toHaveLength(ROWS * 5);

    const first = document.querySelector('[data-cell="STU-001:0"]') as HTMLElement;
    first.focus();
    const keys = [...Array(5).fill("ArrowRight"), ...Array(50).fill("ArrowDown"), ...Array(5).fill("ArrowLeft"), ...Array(60).fill("ArrowDown")];
    const moveStart = performance.now();
    for (const key of keys) await press(key);
    const perMove = (performance.now() - moveStart) / keys.length;
    expect(document.activeElement).toBe(document.querySelector('[data-cell="STU-111:0"]'));

    // One edit: the cameras cell of an empty row.
    (document.querySelector('[data-cell="STU-112:2"]') as HTMLElement).focus();
    const editStart = performance.now();
    await press("Enter");
    fireEvent.change(document.querySelector("[data-cell-editor] input") as HTMLInputElement, { target: { value: "Sequoia" } });
    await press("Enter");
    await flush();
    const edit = performance.now() - editStart;
    expect(document.querySelector('[data-cell="STU-112:2"]')).toHaveTextContent("Sequoia");

    console.info(`[DoD 14] first draw ${firstDraw.toFixed(0)} ms (budget ${BUDGET.firstDrawMs}); per arrow move ${perMove.toFixed(1)} ms over ${keys.length} moves (budget ${BUDGET.perMoveMs}); one edit ${edit.toFixed(0)} ms (budget ${BUDGET.editMs})`);
    expect(firstDraw).toBeLessThan(BUDGET.firstDrawMs);
    expect(perMove).toBeLessThan(BUDGET.perMoveMs);
    expect(edit).toBeLessThan(BUDGET.editMs);
  }, 30_000);
});
