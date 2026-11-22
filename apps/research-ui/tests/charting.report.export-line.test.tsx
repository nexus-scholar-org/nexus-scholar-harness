import { fireEvent, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ChartingTable } from "@/lib/charting-api";

import { counts, installEngine, lastExport, makeRow, makeTable, renderCharting, renderReport } from "./charting-helpers";

/**
 * Spec 04 "Partial": the last-export line from `last_export`, absent before the
 * first export; the open-cell and required-open lines from today's counts; what
 * the file held when that differs; and no line ever stops a download. The same
 * lines sit under the toolbar of `/charting` (spec 01, made persistent).
 */

afterEach(() => vi.unstubAllGlobals());

const rows = () => [makeRow(1), makeRow(2), makeRow(3, { ft_decision: { outcome: "EXCLUDE", reason_code: "EXC-01" } })];

function table(over: Partial<ChartingTable> = {}, open: { cells_open?: number; required_open?: number } = {}): ChartingTable {
  const r = rows();
  return makeTable(r, { counts: { ...counts(r), ...open }, ...over });
}

const line = (name: string) => document.querySelector(`[data-desktop] [data-${name}]`) as HTMLElement | null;
const fileButton = (kind: string) => document.querySelector(`[data-file="${kind}"]`) as HTMLButtonElement;

describe("charting.report.export-line", () => {
  it("says when, in which format and how many rows the last export held", async () => {
    installEngine(table({ last_export: lastExport() }, { cells_open: 7, required_open: 2 }));
    await renderReport();
    expect(line("last-export")).toHaveTextContent(/^Exported 2026-11-21 14:32 \(spreadsheet\): 68 rows\. Changes after this are not in that file\.$/);
    expect(line("file-had")).toBeNull();
  });

  it("names a CSV export as CSV", async () => {
    installEngine(table({ last_export: lastExport({ format: "csv", view: "fulltext", rows: 3, file_name: "charting-fulltext-20261121T143200Z.csv" }) }, { cells_open: 7, required_open: 2 }));
    await renderReport();
    expect(line("last-export")).toHaveTextContent("Exported 2026-11-21 14:32 (CSV): 3 rows.");
  });

  it("says one row and one cell in the singular (review of Part C, finding 5)", async () => {
    installEngine(table({ last_export: lastExport({ rows: 1, cells_open: 5 }) }, { cells_open: 1, required_open: 1 }));
    await renderReport();
    expect(line("last-export")).toHaveTextContent(/: 1 row\. Changes after this/);
    expect(line("cells-open")).toHaveTextContent(/^1 cell is not charted yet\.$/);
    expect(line("required-open")).toHaveTextContent(/^1 required cell is empty\.$/);
  });

  it("is absent, not 'never', before the first export", async () => {
    installEngine(table({ last_export: null }));
    await renderReport();
    expect(line("last-export")).toBeNull();
    expect(document.querySelector("[data-desktop]")).not.toHaveTextContent(/never/i);
  });

  it("shows the open-cell and required-open lines with today's counts, the second in the unclear role with an icon", async () => {
    installEngine(table({ last_export: null }, { cells_open: 9, required_open: 4 }));
    await renderReport();
    expect(line("cells-open")).toHaveTextContent("9 cells are not charted yet.");
    const required = line("required-open")!;
    expect(required).toHaveTextContent("4 required cells are empty.");
    expect(required).toHaveAttribute("data-role", "unclear");
    expect(required.querySelector("svg[data-icon]")).not.toBeNull();
  });

  it("leaves out an open line whose count is zero", async () => {
    installEngine(table({ last_export: null }, { cells_open: 3, required_open: 0 }));
    await renderReport();
    expect(line("cells-open")).toHaveTextContent("3 cells are not charted yet.");
    expect(line("required-open")).toBeNull();
  });

  it("says what the file held when its open cells differ from today's", async () => {
    installEngine(table({ last_export: lastExport({ cells_open: 12, required_open: 2 }) }, { cells_open: 7, required_open: 2 }));
    await renderReport();
    expect(line("last-export")).toHaveTextContent("Changes after this are not in that file. That file had 12 cells not charted.");
    expect(line("file-had")).toHaveTextContent("That file had 12 cells not charted.");
  });

  it("stops no download", async () => {
    installEngine(table({ last_export: lastExport({ cells_open: 12 }) }, { cells_open: 9, required_open: 4 }));
    await renderReport();
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeEnabled();
  });

  it("after a download, shows the engine's record of it, read again from the table", async () => {
    const engine = installEngine(table({ last_export: null }, { cells_open: 9, required_open: 4 }));
    await renderReport();
    expect(line("last-export")).toBeNull();
    fireEvent.click(fileButton("charting"));
    await waitFor(() => expect(line("last-export")).not.toBeNull());
    // The fake engine recorded 2 rows (3 kept, 1 excluded at full text) at 10:00.
    expect(line("last-export")).toHaveTextContent(/^Exported 2026-11-21 10:00 \(CSV\): 2 rows\./);
    const after = engine.calls.findIndex((c) => c.path === "/api/v1/charting/export?format=csv&view=charting");
    expect(after).toBeGreaterThan(-1);
    expect(engine.calls.slice(after + 1).some((c) => c.method === "GET" && c.path === "/api/v1/charting")).toBe(true);
  });

  it("is persistent under the toolbar of /charting too, with the open lines", async () => {
    installEngine(table({ last_export: lastExport() }, { cells_open: 9, required_open: 4 }));
    await renderCharting();
    expect(line("last-export")).toHaveTextContent("Exported 2026-11-21 14:32 (spreadsheet): 68 rows. Changes after this are not in that file.");
    expect(line("file-had")).toHaveTextContent("That file had 7 cells not charted.");
    expect(line("cells-open")).toHaveTextContent("9 cells are not charted yet.");
    expect(line("required-open")).toHaveTextContent("4 required cells are empty.");
    expect(document.querySelector("[data-desktop] [data-export]")).toBeEnabled();
  });

  it("is absent on /charting before the first export, with no open cell", async () => {
    installEngine(table({ last_export: null }));
    await renderCharting();
    expect(document.querySelector("[data-desktop] [data-export-lines]")).toBeNull();
  });
});
