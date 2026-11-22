import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { FormColumn } from "@/lib/charting-api";

import { flush, installEngine, makeChartingTable, makeRow, press, renderCharting, uavColumns, withCells, type FakeEngine } from "./charting-helpers";

/**
 * Spec 01, the form panel and the pilot (M12a Part B, DoD 12 and 13): F opens a
 * labelled complementary region beside the rows and Esc gives the focus back to
 * the Form button; before any value a change saves at once; after, the changes
 * wait for "Why does the form change? One sentence." and "Record the amendment";
 * the amendments list says what changed, from what, to what; a split names its
 * parent, and "Merge with…" makes one column from two that names both; "End
 * pilot" is one recorded action; the cells a change touches are marked "Chart
 * again" with the earlier value kept.
 */

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

const panel = () => screen.getByRole("complementary", { name: "Charting form" });
const columnCard = (id: string) => document.querySelector(`[data-form-column="${id}"]`) as HTMLElement;
const puts = (engine: FakeEngine) => engine.calls.filter((c) => c.method === "PUT" && c.path === "/api/v1/charting/form");
const putBody = (engine: FakeEngine, i: number) => puts(engine)[i].body as { base_version: number; columns: FormColumn[]; reason?: string };
const ev = (n: number) => `0190a0a0-0000-7000-8000-${String(n).padStart(12, "0")}`;

async function openPanel() {
  (document.querySelector("[data-form-button]") as HTMLElement).focus();
  await press("f");
  return panel();
}

describe("charting.form-panel", () => {
  it("F opens the panel beside the rows; Esc closes it and the focus goes back to the Form button", async () => {
    installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    const button = document.querySelector("[data-form-button]") as HTMLElement;
    expect(button).toHaveAttribute("aria-expanded", "false");
    const region = await openPanel();
    expect(region.tagName).toBe("ASIDE");
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(region.className).toMatch(/lg:w-\[360px\]/);
    expect(within(region).getAllByRole("listitem").filter((li) => li.hasAttribute("data-form-column"))).toHaveLength(5);
    expect(within(columnCard("sensor_problems")).getByRole("textbox", { name: "Name" })).toHaveValue("Sensor problems addressed");
    expect(within(columnCard("sensor_problems")).getByRole("combobox", { name: "Type" })).toHaveValue("several");
    expect(within(columnCard("sensor_problems")).getByRole("checkbox", { name: "Required" })).toBeChecked();
    expect(within(columnCard("cross_camera")).getByText("The options are Yes and No.")).toBeInTheDocument();
    expect(within(columnCard("cameras")).getByText("From the protocol: cameras")).toBeInTheDocument();
    await press("Escape");
    expect(screen.queryByRole("complementary", { name: "Charting form" })).toBeNull();
    expect(document.activeElement).toBe(button);
  });

  it("before any value each change saves at once, from the version it was made on, with no reason", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    await openPanel();
    const name = within(columnCard("cameras")).getByRole("textbox", { name: "Name" });
    fireEvent.change(name, { target: { value: "Cameras" } });
    expect(puts(engine)).toHaveLength(0);
    fireEvent.blur(name);
    await flush();
    expect(puts(engine)).toHaveLength(1);
    expect(putBody(engine, 0)).toMatchObject({ base_version: 1 });
    expect(putBody(engine, 0).reason).toBeUndefined();
    expect(putBody(engine, 0).columns[1]).toMatchObject({ column_id: "cameras", name: "Cameras" });
    expect(document.querySelector("[data-amendment-prompt]")).toBeNull();
    // The type: at once.
    fireEvent.change(within(columnCard("cameras")).getByRole("combobox", { name: "Type" }), { target: { value: "one" } });
    await flush();
    expect(putBody(engine, 1)).toMatchObject({ base_version: 2 });
    expect(putBody(engine, 1).columns[1]).toMatchObject({ type: "one", options: [] });
    // An option, added with Enter.
    const option = within(columnCard("cameras")).getByRole("textbox", { name: "New option" });
    fireEvent.change(option, { target: { value: "One camera" } });
    fireEvent.keyDown(option, { key: "Enter" });
    await flush();
    expect(putBody(engine, 2).columns[1].options).toEqual(["One camera"]);
    // Reorder, remove, add.
    fireEvent.click(within(columnCard("cameras")).getByRole("button", { name: "Move up" }));
    await flush();
    expect(putBody(engine, 3).columns.map((c) => c.column_id).slice(0, 2)).toEqual(["cameras", "sensor_problems"]);
    fireEvent.click(within(columnCard("cross_camera")).getByRole("button", { name: "Remove the column" }));
    await flush();
    expect(putBody(engine, 4).columns.map((c) => c.column_id)).not.toContain("cross_camera");
    fireEvent.click(within(panel()).getByRole("button", { name: "Add a column" }));
    await flush();
    expect(putBody(engine, 5).columns.at(-1)).toMatchObject({ name: "New column 5", type: "text", derived_from: [] });
    expect(document.activeElement).toBe(within(panel()).getAllByRole("textbox", { name: "Name" }).at(-1));
    // The rows follow each change, and the grid shows the new column.
    expect(document.querySelector("[role=grid]")!.textContent).toContain("New column 5");
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Form saved");
  });

  it("a column needs a name: an empty one is not sent", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    await openPanel();
    const name = within(columnCard("cameras")).getByRole("textbox", { name: "Name" });
    fireEvent.change(name, { target: { value: "  " } });
    fireEvent.blur(name);
    await flush();
    expect(puts(engine)).toHaveLength(0);
    expect(within(panel()).getByText("Every column needs a name.")).toBeInTheDocument();
  });

  it("after a value the change waits for one sentence and is recorded as an amendment", async () => {
    const columns = uavColumns();
    const engine = installEngine(
      makeChartingTable([withCells(makeRow(1), columns, { cameras: { state: "value", value: "Sequoia", event_id: ev(1) } })], columns, {}, { has_values: true }),
    );
    await renderCharting("en", "?view=charting");
    await openPanel();
    const name = within(columnCard("cameras")).getByRole("textbox", { name: "Name" });
    fireEvent.change(name, { target: { value: "Cameras" } });
    fireEvent.blur(name);
    await flush();
    expect(puts(engine)).toHaveLength(0);
    const prompt = document.querySelector("[data-amendment-prompt]") as HTMLElement;
    expect(prompt).toHaveTextContent("Changes not recorded yet.");
    const reason = within(prompt).getByRole("textbox", { name: "Why does the form change? One sentence." });
    // Without a sentence: its words, nothing sent.
    fireEvent.click(within(prompt).getByRole("button", { name: "Record the amendment" }));
    await flush();
    expect(puts(engine)).toHaveLength(0);
    expect(within(panel()).getByRole("alert")).toHaveTextContent("Say in one sentence why the form changes.");
    fireEvent.change(reason, { target: { value: "A shorter name reads better in the table." } });
    fireEvent.click(within(prompt).getByRole("button", { name: "Record the amendment" }));
    await flush();
    await flush();
    expect(putBody(engine, 0)).toMatchObject({ base_version: 1, reason: "A shorter name reads better in the table." });
    const list = document.querySelector("[data-amendments]") as HTMLElement;
    expect(within(list).getByText("Amended on 2026-11-21 by researcher:local: renamed, from “Cameras and evaluation design” to “Cameras”.")).toBeInTheDocument();
    expect(within(list).getByText("Reason: A shorter name reads better in the table.")).toBeInTheDocument();
    expect(document.querySelector("[data-amendment-prompt]")).toBeNull();
    // A rename keeps the values.
    expect(document.querySelector('[data-cell="STU-001:2"]')).toHaveTextContent("Sequoia");
    expect(document.querySelector('[data-cell="STU-001:2"] [data-mark=chart-again]')).toBeNull();
  });

  it("a changed type marks the charted cells Chart again with the earlier value; Undo these changes drops a draft", async () => {
    const columns = uavColumns();
    const engine = installEngine(
      makeChartingTable([withCells(makeRow(1), columns, { cameras: { state: "value", value: "Sequoia", event_id: ev(1) } }), makeRow(2)], columns, {}, { has_values: true }),
    );
    await renderCharting("en", "?view=charting");
    await openPanel();
    fireEvent.change(within(columnCard("split")).getByRole("textbox", { name: "Name" }), { target: { value: "Split" } });
    fireEvent.click(within(panel()).getByRole("button", { name: "Undo these changes" }));
    expect(within(columnCard("split")).getByRole("textbox", { name: "Name" })).toHaveValue("Data split");
    fireEvent.change(within(columnCard("cameras")).getByRole("combobox", { name: "Type" }), { target: { value: "number" } });
    const prompt = document.querySelector("[data-amendment-prompt]") as HTMLElement;
    fireEvent.change(within(prompt).getByRole("textbox"), { target: { value: "Count the cameras." } });
    fireEvent.click(within(prompt).getByRole("button", { name: "Record the amendment" }));
    await flush();
    await flush();
    expect(within(document.querySelector("[data-amendments]") as HTMLElement).getByText("Amended on 2026-11-21 by researcher:local: type changed (Cameras and evaluation design), from “Text” to “Number”.")).toBeInTheDocument();
    const cell = document.querySelector('[data-cell="STU-001:2"]') as HTMLElement;
    expect(cell.querySelector("[data-mark=chart-again]")).toHaveTextContent("Chart again");
    expect(cell).toHaveTextContent("Sequoia");
    expect(engine.calls.filter((c) => c.method === "GET" && c.path === "/api/v1/charting").length).toBeGreaterThanOrEqual(2);
  });

  it("a split makes two columns derived from the first; each shows the earlier value to chart again", async () => {
    const columns = uavColumns();
    const engine = installEngine(
      makeChartingTable([withCells(makeRow(1), columns, { cameras: { state: "value", value: "RedEdge-M; no cross-camera test", event_id: ev(1) } })], columns, {}, { has_values: true }),
    );
    await renderCharting("en", "?view=charting");
    await openPanel();
    fireEvent.click(within(columnCard("cameras")).getByRole("button", { name: "Split into two" }));
    const names = within(panel()).getAllByRole("textbox", { name: "Name" }).map((n) => (n as HTMLInputElement).value);
    expect(names).toContain("Cameras and evaluation design (1)");
    expect(names).toContain("Cameras and evaluation design (2)");
    const prompt = document.querySelector("[data-amendment-prompt]") as HTMLElement;
    fireEvent.change(within(prompt).getByRole("textbox"), { target: { value: "One value per question makes the table countable." } });
    fireEvent.click(within(prompt).getByRole("button", { name: "Record the amendment" }));
    await flush();
    await flush();
    const sent = putBody(engine, 0).columns;
    const parts = sent.filter((c) => c.derived_from?.includes("cameras"));
    expect(parts).toHaveLength(2);
    expect(sent.some((c) => c.column_id === "cameras")).toBe(false);
    expect(within(document.querySelector("[data-amendments]") as HTMLElement).getByText(/column split, from “Cameras and evaluation design” to “Cameras and evaluation design \(1\), Cameras and evaluation design \(2\)”\./)).toBeInTheDocument();
    for (const part of parts) {
      const col = sent.findIndex((c) => c.column_id === part.column_id) + 1;
      const cell = document.querySelector(`[data-cell="STU-001:${col}"]`) as HTMLElement;
      expect(cell.querySelector("[data-mark=chart-again]")).not.toBeNull();
      expect(cell.querySelector("[data-history]")).toHaveTextContent("Earlier value, in Cameras and evaluation design: RedEdge-M; no cross-camera test");
    }
    expect(within(panel()).getAllByText("Made from: Cameras and evaluation design")).toHaveLength(2);
  });

  it("Merge with… makes one Text column from two, recorded as a merge; its cells show both earlier values to chart again", async () => {
    const columns = uavColumns();
    const engine = installEngine(
      makeChartingTable(
        [withCells(makeRow(1), columns, { n_images: { state: "value", value: 1260, event_id: ev(1) }, split: { state: "value", value: "By field", event_id: ev(2) } }), makeRow(2)],
        columns,
        {},
        { has_values: true },
      ),
    );
    await renderCharting("en", "?view=charting");
    await openPanel();
    const mergeButton = within(columnCard("n_images")).getByRole("button", { name: "Merge with…" });
    expect(mergeButton).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(mergeButton);
    await flush();
    expect(mergeButton).toHaveAttribute("aria-expanded", "true");
    const target = within(columnCard("n_images")).getByRole("combobox", { name: "Merge Images with" });
    expect(document.activeElement).toBe(target);
    // Every other column can be chosen, never the column itself.
    expect(within(target).getAllByRole("option").map((o) => o.textContent)).toEqual(["Sensor problems addressed", "Cameras and evaluation design", "Data split", "Test camera absent from training"]);
    fireEvent.change(target, { target: { value: "split" } });
    fireEvent.click(within(columnCard("n_images")).getByRole("button", { name: "Merge the two columns" }));
    await flush();
    // One new column at the place of the first, the name focused; nothing sent before the reason.
    const cards = [...document.querySelectorAll<HTMLElement>("[data-form-column]")];
    expect(cards).toHaveLength(4);
    const merged = cards[2];
    expect(within(merged).getByRole("textbox", { name: "Name" })).toHaveValue("Images and Data split");
    expect(within(merged).getByRole("combobox", { name: "Type" })).toHaveValue("text");
    expect(document.activeElement).toBe(within(merged).getByRole("textbox", { name: "Name" }));
    expect(within(merged).getByText("Made from: Images, Data split")).toBeInTheDocument();
    expect(puts(engine)).toHaveLength(0);
    const prompt = document.querySelector("[data-amendment-prompt]") as HTMLElement;
    fireEvent.change(within(prompt).getByRole("textbox"), { target: { value: "Size and split read together." } });
    fireEvent.click(within(prompt).getByRole("button", { name: "Record the amendment" }));
    await flush();
    await flush();
    const sent = putBody(engine, 0);
    expect(sent.reason).toBe("Size and split read together.");
    expect(sent.columns.map((c) => c.column_id)).not.toContain("n_images");
    expect(sent.columns.map((c) => c.column_id)).not.toContain("split");
    expect(sent.columns[2]).toMatchObject({ name: "Images and Data split", type: "text", options: [], from_protocol: null, derived_from: ["n_images", "split"], definition: "Number of images; How the data are split" });
    const list = document.querySelector("[data-amendments]") as HTMLElement;
    expect(within(list).getByText("Amended on 2026-11-21 by researcher:local: columns merged, from “Images, Data split” to “Images and Data split”.")).toBeInTheDocument();
    expect(within(list).getByText("Reason: Size and split read together.")).toBeInTheDocument();
    // After the save the old columns are gone from the form; the amendment still names them.
    expect(within(columnCard(sent.columns[2].column_id)).getByText("Made from: Images, Data split")).toBeInTheDocument();
    const cell = document.querySelector('[data-cell="STU-001:3"]') as HTMLElement;
    expect(cell.querySelector("[data-mark=chart-again]")).toHaveTextContent("Chart again");
    expect(cell.querySelector("[data-history]")).toHaveTextContent("Earlier value, in Data split: By field");
    const history = engine.table.rows[0].cells![sent.columns[2].column_id].history;
    expect(history.map((h) => [h.column, h.value])).toEqual([["Images", 1260], ["Data split", "By field"]]);
    // Study 2 held nothing in either column: nothing to chart again.
    expect(document.querySelector('[data-cell="STU-002:3"] [data-mark=chart-again]')).toBeNull();
  });

  it("before any value a merge saves at once; Esc and Cancel close the chooser, not the panel", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    await openPanel();
    const button = within(columnCard("cameras")).getByRole("button", { name: "Merge with…" });
    fireEvent.click(button);
    await flush();
    await press("Escape");
    await flush();
    expect(document.querySelector("[data-form-merge-chooser]")).toBeNull();
    expect(panel()).toBeInTheDocument();
    expect(document.activeElement).toBe(button);
    fireEvent.click(button);
    await flush();
    fireEvent.click(within(columnCard("cameras")).getByRole("button", { name: "Cancel" }));
    await flush();
    expect(document.querySelector("[data-form-merge-chooser]")).toBeNull();
    expect(document.activeElement).toBe(button);
    // The chosen column comes first in the name when it comes first in the form.
    fireEvent.click(button);
    await flush();
    fireEvent.change(within(columnCard("cameras")).getByRole("combobox", { name: "Merge Cameras and evaluation design with" }), { target: { value: "sensor_problems" } });
    fireEvent.click(within(columnCard("cameras")).getByRole("button", { name: "Merge the two columns" }));
    await flush();
    expect(puts(engine)).toHaveLength(1);
    expect(putBody(engine, 0).reason).toBeUndefined();
    const first = putBody(engine, 0).columns[0];
    expect(first).toMatchObject({ name: "Sensor problems addressed and Cameras and evaluation design", type: "text", required: true, derived_from: ["sensor_problems", "cameras"] });
    expect(document.querySelector("[data-amendment-prompt]")).toBeNull();
    // Saved before any value: no amendment, and "Made from" still names the old columns.
    expect(within(columnCard(first.column_id)).getByText("Made from: Sensor problems addressed, Cameras and evaluation design")).toBeInTheDocument();
    expect(within(document.querySelector("[data-amendments]") as HTMLElement).getByText("No amendment yet.")).toBeInTheDocument();
  });

  it("a third column merged into a merge not yet recorded names all three sources", async () => {
    const columns = uavColumns();
    const engine = installEngine(
      makeChartingTable([withCells(makeRow(1), columns, { cameras: { state: "value", value: "Sequoia", event_id: ev(1) } })], columns, {}, { has_values: true }),
    );
    await renderCharting("en", "?view=charting");
    await openPanel();
    fireEvent.click(within(columnCard("n_images")).getByRole("button", { name: "Merge with…" }));
    await flush();
    fireEvent.change(within(columnCard("n_images")).getByRole("combobox", { name: "Merge Images with" }), { target: { value: "split" } });
    fireEvent.click(within(columnCard("n_images")).getByRole("button", { name: "Merge the two columns" }));
    await flush();
    const draftMerge = [...document.querySelectorAll<HTMLElement>("[data-form-column]")][2];
    fireEvent.click(within(draftMerge).getByRole("button", { name: "Merge with…" }));
    await flush();
    fireEvent.change(within(draftMerge).getByRole("combobox", { name: /^Merge / }), { target: { value: "cross_camera" } });
    fireEvent.click(within(draftMerge).getByRole("button", { name: "Merge the two columns" }));
    await flush();
    expect(within(panel()).getAllByRole("textbox", { name: "Name" }).map((n) => (n as HTMLInputElement).value)).toContain("Images and Data split and Test camera absent from training");
    const prompt = document.querySelector("[data-amendment-prompt]") as HTMLElement;
    fireEvent.change(within(prompt).getByRole("textbox"), { target: { value: "One column for the data." } });
    fireEvent.click(within(prompt).getByRole("button", { name: "Record the amendment" }));
    await flush();
    await flush();
    const sent = putBody(engine, 0).columns;
    expect(sent.map((c) => c.column_id).slice(0, 2)).toEqual(["sensor_problems", "cameras"]);
    expect(sent).toHaveLength(3);
    expect(sent[2].derived_from).toEqual(["n_images", "split", "cross_camera"]);
    expect(within(document.querySelector("[data-amendments]") as HTMLElement).getByText(/columns merged, from “Images, Data split, Test camera absent from training” to “Images and Data split and Test camera absent from training”\./)).toBeInTheDocument();
  });

  it("End pilot is one recorded action; the toolbar switch turns off and the panel says when", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    const pilotSwitch = screen.getByRole("switch", { name: "Pilot" });
    expect(pilotSwitch).toHaveAttribute("aria-checked", "true");
    await openPanel();
    fireEvent.click(within(panel()).getByRole("button", { name: "End pilot" }));
    await flush();
    const ends = engine.calls.filter((c) => c.path === "/api/v1/charting/form/pilot/end");
    expect(ends).toHaveLength(1);
    expect(ends[0].body).toEqual({ base_version: 1 });
    expect(within(panel()).getByText("Pilot ended on 2026-11-21")).toBeInTheDocument();
    expect(pilotSwitch).toHaveAttribute("aria-checked", "false");
    expect(pilotSwitch).toBeDisabled();
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Pilot ended");
  });

  it("the toolbar's Pilot switch ends the pilot too", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)]));
    await renderCharting("en", "?view=charting");
    fireEvent.click(screen.getByRole("switch", { name: "Pilot" }));
    await flush();
    expect(engine.calls.filter((c) => c.path === "/api/v1/charting/form/pilot/end")).toHaveLength(1);
  });

  it("a stale form and a reason the engine asks for are said in words, with the code", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1)]), { formFail: { status: 409, code: "CHARTING_FORM_STALE" } });
    await renderCharting("en", "?view=charting");
    await openPanel();
    const name = within(columnCard("cameras")).getByRole("textbox", { name: "Name" });
    fireEvent.change(name, { target: { value: "Cameras" } });
    fireEvent.blur(name);
    await flush();
    const alert = within(panel()).getByRole("alert");
    expect(alert).toHaveTextContent("The form changed since you opened it. Reload the table.");
    expect(within(alert).getByText("CHARTING_FORM_STALE")).toHaveAttribute("dir", "ltr");
    // The rows are read again.
    expect(engine.calls.filter((c) => c.method === "GET" && c.path === "/api/v1/charting").length).toBeGreaterThanOrEqual(2);
    // Another reader charted a value meanwhile: the engine asks for a reason, the prompt appears.
    engine.formFail = { status: 422, code: "CHARTING_AMENDMENT_REASON_REQUIRED" };
    fireEvent.change(within(columnCard("split")).getByRole("textbox", { name: "Name" }), { target: { value: "Split" } });
    fireEvent.blur(within(columnCard("split")).getByRole("textbox", { name: "Name" }));
    await flush();
    await flush();
    expect(document.querySelector("[data-amendment-prompt]")).not.toBeNull();
    expect(within(panel()).getByRole("alert")).toHaveTextContent("Say in one sentence why the form changes.");
  });
});
