import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  flush,
  installEngine,
  makeChartingTable,
  makeColumn,
  makeRow,
  postedEvents,
  press,
  renderCharting,
  uavColumns,
  withCells,
} from "./charting-helpers";

/**
 * Spec 01, the Charting view (M12a Part B, DoD 14): the columns of the form,
 * each cell as a value, Not reported or Not applicable in words with an icon, a
 * dash read as "Not charted", "Chart again" with the earlier value, the counts
 * line's "charted", the "Not charted" and "Pilot" filters, the first-visit card,
 * the no-columns state, "Chart the next study" and Export, the Charting CSV, and
 * rows excluded at full text read-only.
 */

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const cellAt = (id: string, col: number) => document.querySelector(`[data-cell="${id}:${col}"]`) as HTMLElement;
const ev = (n: number) => `0190a0a0-0000-7000-8000-${String(n).padStart(12, "0")}`;

function fixture() {
  const columns = uavColumns();
  return makeChartingTable(
    [
      withCells(makeRow(1, { fulltext: { ...makeRow(1).fulltext, status: "retrieved" } }), columns, {
        sensor_problems: { state: "value", value: ["Misregistration", "Change of camera"], event_id: ev(1), pilot: true },
        cameras: { state: "value", value: "RedEdge-M", event_id: ev(2), pilot: true },
        n_images: { state: "value", value: 1260, event_id: ev(3), pilot: true },
        split: { state: "not_reported", event_id: ev(4), pilot: true },
        cross_camera: { state: "value", value: "No", event_id: ev(5), pilot: true },
      }),
      withCells(makeRow(2), columns, {
        n_images: { state: "not_applicable", event_id: ev(6) },
        split: {
          state: "value", value: "By date", event_id: ev(7), chart_again: true,
          history: [{ state: "value", value: "Random tiles", note: null, where_from: null, at: null, form_version: 1, event_id: ev(8) }],
        },
      }),
      makeRow(3),
      makeRow(4, { ft_decision: { outcome: "EXCLUDE", reason_code: "EXC-01" } }),
    ],
    columns,
    {},
    { has_values: true },
  );
}

describe("charting.charting-view", () => {
  it("shows one column per form column and each cell in words, never colour alone", async () => {
    installEngine(fixture());
    await renderCharting("en", "?view=charting");
    expect(document.querySelector("[data-counts]")).toHaveTextContent("4 kept · 1 retrieved · 0 not retrieved · 3 to get · 0 included at full text · 1 excluded · 1 charted");
    const grid = within(desktop()).getByRole("grid", { name: "Kept studies, charting" });
    expect(grid).toHaveAttribute("aria-colcount", "6");
    const headers = within(grid).getAllByRole("columnheader").map((h) => h.textContent);
    expect(headers).toEqual([
      "Study",
      "Sensor problems addressedSeveral of a list · Required",
      "Cameras and evaluation designText",
      "ImagesNumber",
      "Data splitOne of a list",
      "Test camera absent from trainingYes or No",
    ]);
    expect(cellAt("STU-001", 1)).toHaveTextContent("Misregistration, Change of camera");
    expect(cellAt("STU-001", 3)).toHaveTextContent("1260");
    expect(cellAt("STU-001", 5)).toHaveTextContent("No");
    // Not reported and Not applicable: words and an icon.
    const nr = cellAt("STU-001", 4).querySelector("[data-mark=not-reported]")!;
    expect(nr).toHaveTextContent("Not reported");
    expect(nr.querySelector("svg[data-icon]")).not.toBeNull();
    expect(cellAt("STU-002", 3).querySelector("[data-mark=not-applicable]")).toHaveTextContent("Not applicable");
    // An empty cell is a dash whose accessible name says "Not charted".
    expect(cellAt("STU-003", 2).querySelector("[data-dash]")).toHaveAttribute("aria-hidden", "true");
    expect(within(cellAt("STU-003", 2)).getByText("Not charted")).toHaveClass("sr-only");
    expect(within(grid).getAllByRole("gridcell").filter((c) => c.textContent === "—Not charted").length).toBeGreaterThan(0);
    // Chart again keeps the earlier value visible as history.
    expect(cellAt("STU-002", 4).querySelector("[data-mark=chart-again]")).toHaveTextContent("Chart again");
    expect(cellAt("STU-002", 4).querySelector("[data-history]")).toHaveTextContent("Earlier value: Random tiles");
    // The row marks: Pilot on a row charted in the pilot; the excluded row is hidden until Show excluded.
    expect(within(cellAt("STU-001", 0)).getByText("Pilot")).toBeInTheDocument();
    expect(cellAt("STU-004", 0)).toBeNull();
  });

  it("keys 1 and 2 switch the two views of the same rows", async () => {
    installEngine(fixture());
    await renderCharting();
    (document.querySelector('[data-study-row="STU-001"]') as HTMLElement).focus();
    await press("2");
    expect(within(desktop()).getByRole("radio", { name: /Charting/ })).toBeChecked();
    expect(within(desktop()).getByRole("grid", { name: "Kept studies, charting" })).toBeInTheDocument();
    expect(document.activeElement).toBe(cellAt("STU-001", 0));
    expect(window.location.search).toContain("view=charting");
    await press("1");
    expect(within(desktop()).getByRole("grid", { name: "Kept studies, full text" })).toBeInTheDocument();
  });

  it("the Not charted and Pilot filters show what they name", async () => {
    installEngine(fixture());
    await renderCharting("en", "?view=charting");
    const ids = () => Array.from(desktop().querySelectorAll("[data-study-row]")).map((r) => r.getAttribute("data-study-row"));
    const select = within(desktop()).getByRole("combobox", { name: "Show" });
    fireEvent.change(select, { target: { value: "notCharted" } });
    await flush();
    expect(ids()).toEqual(["STU-002", "STU-003"]);
    fireEvent.change(select, { target: { value: "pilot" } });
    await flush();
    expect(ids()).toEqual(["STU-001"]);
    fireEvent.click(within(desktop()).getByRole("checkbox", { name: "Show excluded" }));
    fireEvent.change(select, { target: { value: "all" } });
    await flush();
    expect(ids()).toContain("STU-004");
    // An excluded row is read-only, with its decision on the row.
    expect(within(cellAt("STU-004", 0)).getByText("Exclude")).toBeInTheDocument();
    expect(cellAt("STU-004", 1)).toHaveAttribute("aria-readonly", "true");
  });

  it("a row excluded at full text cannot be charted here: its words, no editor, no event", async () => {
    const engine = installEngine(fixture());
    await renderCharting("en", "?view=charting&excluded=1");
    cellAt("STU-004", 1).focus();
    await press("Enter");
    expect(document.querySelector("[data-cell-editor]")).toBeNull();
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("Excluded at full text. Change the decision to chart it.");
    await press("n", { altKey: true, code: "KeyN" });
    expect(postedEvents(engine)).toHaveLength(0);
  });

  it("first visit: the card suggests the pilot; Open the charting form opens the panel, Not now closes it for good", async () => {
    const columns = uavColumns();
    installEngine(makeChartingTable([makeRow(1), makeRow(2)], columns));
    await renderCharting("en", "?view=charting");
    const card = document.querySelector("[data-first-visit]") as HTMLElement;
    expect(card).toHaveTextContent("Try the form on about five studies, then revise it.");
    // While the card is shown, its button is the one brand button.
    expect(within(card).getByRole("button", { name: "Open the charting form" })).toHaveAttribute("data-variant", "primary");
    expect(document.querySelector("[data-chart-next]")).toHaveAttribute("data-variant", "secondary");
    expect(desktop().querySelectorAll('[data-variant="primary"]')).toHaveLength(1);
    fireEvent.click(within(card).getByRole("button", { name: "Open the charting form" }));
    await flush();
    expect(screen.getByRole("complementary", { name: "Charting form" })).toBeInTheDocument();
    expect(document.querySelector("[data-first-visit]")).toBeNull();
    expect(document.querySelector("[data-chart-next]")).toHaveAttribute("data-variant", "primary");
  });

  it("first visit: Not now closes the card for this page load; it is not stored in the browser (N12)", async () => {
    installEngine(makeChartingTable([makeRow(1)]));
    const view = await renderCharting("en", "?view=charting");
    fireEvent.click(within(document.querySelector("[data-first-visit]") as HTMLElement).getByRole("button", { name: "Not now" }));
    expect(document.querySelector("[data-first-visit]")).toBeNull();
    view.unmount();
    installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    expect(document.querySelector("[data-first-visit]")).not.toBeNull();
  });

  it("no charting columns: the sentence and a brand button that opens the form with one new column", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)], []));
    await renderCharting("en", "?view=charting");
    const state = document.querySelector("[data-state=no-columns]") as HTMLElement;
    expect(state).toHaveTextContent("Your protocol has no charting columns yet. Add the first one.");
    expect(document.querySelector("[data-chart-next]")).toBeNull();
    fireEvent.click(within(state).getByRole("button", { name: "Add the first column" }));
    await flush();
    await flush();
    const put = engine.calls.find((c) => c.method === "PUT" && c.path === "/api/v1/charting/form")!;
    expect((put.body as { columns: { name: string }[] }).columns.map((c) => c.name)).toEqual(["New column 1"]);
    expect(screen.getByRole("complementary", { name: "Charting form" })).toBeInTheDocument();
    // The Full text view works as before.
    fireEvent.click(within(desktop()).getByRole("radio", { name: /Full text/ }));
    await flush();
    expect(within(desktop()).getByRole("grid", { name: "Kept studies, full text" })).toBeInTheDocument();
  });

  it("Chart the next study opens the first kept row not charted; once all are charted it becomes Export", async () => {
    const columns = [makeColumn("a", { name: "A" })];
    installEngine(makeChartingTable([withCells(makeRow(1), columns, { a: { state: "value", value: "x", event_id: ev(1) } }), makeRow(2)], columns, {}, { has_values: true }));
    const first = await renderCharting("en", "?view=charting&show=notCharted");
    const next = document.querySelector("[data-chart-next]") as HTMLAnchorElement;
    expect(next).toHaveTextContent("Chart the next study");
    expect(next.getAttribute("href")).toBe("/en/charting/study?view=charting&show=notCharted&id=STU-002");
    first.unmount();
    const engine = installEngine(makeChartingTable([withCells(makeRow(1), columns, { a: { state: "not_reported", event_id: ev(1) } })], columns, {}, { has_values: true }));
    await renderCharting("en", "?view=charting");
    const exportNow = within(desktop()).getAllByRole("button", { name: "Export" }).find((b) => b.hasAttribute("data-next-export"))!;
    expect(exportNow).toHaveAttribute("data-variant", "primary");
    fireEvent.click(exportNow);
    await flush();
    expect(engine.calls.some((c) => c.path === "/api/v1/charting/export?format=csv&view=charting")).toBe(true);
  });

  it("the Export menu offers both CSVs; the Charting one says how many cells are not charted yet", async () => {
    const engine = installEngine(fixture());
    await renderCharting("en", "?view=charting");
    fireEvent.click(document.querySelector("[data-export]") as HTMLElement);
    const menu = document.querySelector("[data-export-menu]") as HTMLElement;
    expect(within(menu).queryByText(/xlsx/i)).toBeNull();
    fireEvent.click(within(menu).getByRole("button", { name: "CSV of the Charting view" }));
    await flush();
    expect(engine.calls.some((c) => c.path === "/api/v1/charting/export?format=csv&view=charting")).toBe(true);
    // Rows 2 and 3 are open: 3 empty cells and 1 to chart again in row 2, 5 in row 3.
    expect(document.querySelector("[data-status-line]")).toHaveTextContent(/^Exported .*: 3 rows\. Changes after this are not in that file\. 9 cells are not charted yet\.$/);
  });

  it("a row charted without a retrieved full text carries the No full text mark", async () => {
    const columns = [makeColumn("a", { name: "A" })];
    installEngine(makeChartingTable([withCells(makeRow(1), columns, { a: { state: "value", value: "x", event_id: ev(1) } }), makeRow(2)], columns, {}, { has_values: true }));
    await renderCharting("en", "?view=charting");
    const mark = cellAt("STU-001", 0).querySelector("[data-mark=no-full-text]")!;
    expect(mark).toHaveTextContent("No full text");
    expect(mark.querySelector("svg[data-icon]")).not.toBeNull();
    expect(cellAt("STU-002", 0).querySelector("[data-mark=no-full-text]")).toBeNull();
  });

  it("archived: the cells cannot be edited and the Form button opens a read-only panel", async () => {
    const engine = installEngine({ ...fixture(), read_only: true, read_only_code: "CHARTING_PROTOCOL_REPLACED" });
    await renderCharting("en", "?view=charting");
    cellAt("STU-003", 2).focus();
    await press("Enter");
    expect(document.querySelector("[data-cell-editor]")).toBeNull();
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("This table belongs to the old protocol.");
    await press("f");
    const panel = screen.getByRole("complementary", { name: "Charting form" });
    expect(within(panel).getAllByRole("textbox").every((box) => (box as HTMLInputElement).disabled)).toBe(true);
    expect(engine.calls.filter((c) => c.method !== "GET")).toHaveLength(0);
  });
});
