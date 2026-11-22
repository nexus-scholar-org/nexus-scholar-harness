import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { chartingKey } from "@/lib/charting-logic";

import { grid, installEngine, makeRow, makeTable, postedEvents, press, renderCharting } from "./charting-helpers";

/** Spec 01 "Keyboard" (M12a Part A): the Full text view's keys, and the budget of four keypresses for 23 rows. */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-study-row="${id}"]`) as HTMLElement;

function focusRow(id: string) {
  const row = rowOf(id);
  fireEvent.focus(row);
  row.focus();
}

describe("charting.keymap", () => {
  it("sets 23 rows to Retrieved in at most four keypresses, one event per record in one request", async () => {
    const engine = installEngine(makeTable(Array.from({ length: 23 }, (_, i) => makeRow(i + 1))));
    await renderCharting();
    focusRow("STU-001");
    const keys = ["a", "r", "Enter"];
    for (const key of keys) await press(key);
    expect(keys.length).toBeLessThanOrEqual(4);
    const sent = postedEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0]).toHaveLength(23);
    expect(new Set(sent[0].map((e) => e.study_id)).size).toBe(23);
    expect(sent[0].every((e) => e.kind === "fulltext_status" && (e.value as { status: string }).status === "retrieved")).toBe(true);
    expect(sent[0].every((e) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(e.event_id))).toBe(true);
    expect(screen.getByText(/23 retrieved/)).toBeInTheDocument();
    // Focus stays on the first changed row.
    expect(document.activeElement).toBe(rowOf("STU-001"));
  });

  it("J and K move the focused row; X toggles its selection; Shift+J and Shift+K extend it", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2), makeRow(3), makeRow(4)]));
    await renderCharting();
    focusRow("STU-001");
    await press("j");
    expect(document.activeElement).toBe(rowOf("STU-002"));
    await press("k");
    expect(document.activeElement).toBe(rowOf("STU-001"));
    await press("x");
    expect(rowOf("STU-001")).toHaveAttribute("aria-selected", "true");
    await press("x");
    expect(rowOf("STU-001")).toHaveAttribute("aria-selected", "false");
    await press("J", { shiftKey: true });
    await press("J", { shiftKey: true });
    expect(["STU-001", "STU-002", "STU-003"].map((id) => rowOf(id).getAttribute("aria-selected"))).toEqual(["true", "true", "true"]);
    expect(rowOf("STU-004")).toHaveAttribute("aria-selected", "false");
    await press("K", { shiftKey: true });
    expect(document.activeElement).toBe(rowOf("STU-002"));
  });

  it("one status key on the focused row saves at once; N asks for one reason first", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    focusRow("STU-002");
    await press("q");
    expect(postedEvents(engine)).toHaveLength(1);
    expect(postedEvents(engine)[0][0]).toMatchObject({ study_id: "STU-002", kind: "fulltext_status", value: { status: "requested" } });
    expect(within(rowOf("STU-002")).getByText("Requested")).toBeInTheDocument();
    await press("n");
    expect(postedEvents(engine)).toHaveLength(1);
    expect(screen.getByText(/choose one reason/i)).toBeInTheDocument();
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(1); // no reason, nothing sent
    await press("2");
    await press("Enter");
    expect(postedEvents(engine)[1][0].value).toEqual({ status: "not_retrieved", reason: "not_found" });
    // Other asks for words.
    await press("n");
    await press("4");
    const words = document.querySelector("[data-mode-words]") as HTMLInputElement;
    expect(words).toHaveFocus();
    fireEvent.change(words, { target: { value: "Library loan pending" } });
    await press("Enter");
    expect(postedEvents(engine)[2][0].value).toEqual({ status: "not_retrieved", reason: "other", reason_text: "Library loan pending" });
    await press("g");
    expect(postedEvents(engine)[3][0].value).toEqual({ status: "to_get" });
  });

  it("I includes the focused row; E then a number then Enter excludes it with that reason; OTHER asks for words", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    focusRow("STU-001");
    await press("i");
    expect(postedEvents(engine)[0][0]).toMatchObject({ kind: "fulltext_decision", value: { outcome: "INCLUDE" } });
    focusRow("STU-002");
    await press("e");
    expect(within(document.querySelector("[data-confirm-line]") as HTMLElement).getByRole("radiogroup")).toBeInTheDocument();
    await press("1");
    expect(screen.getByRole("radio", { name: /EXC-01/ })).toHaveAttribute("aria-checked", "true");
    await press("Enter");
    expect(postedEvents(engine)[1][0]).toMatchObject({ study_id: "STU-002", value: { outcome: "EXCLUDE", reason_code: "EXC-01" } });
    await press("e");
    await press("3");
    const words = document.querySelector("[data-mode-words]") as HTMLInputElement;
    fireEvent.change(words, { target: { value: "Same study as another report" } });
    await press("Enter");
    expect(postedEvents(engine)[2][0].value).toEqual({ outcome: "EXCLUDE", reason_code: "OTHER", reason_text: "Same study as another report" });
  });

  it("Z undoes the last change with a superseding event that carries the earlier value", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("r");
    const change = postedEvents(engine)[0][0];
    await press("z");
    const undo = postedEvents(engine)[1][0];
    expect(undo).toMatchObject({ study_id: "STU-001", kind: "fulltext_status", value: { status: "to_get" }, supersedes: change.event_id });
    expect(within(rowOf("STU-001")).getByText("To get")).toBeInTheDocument();
    expect(screen.getByText("Undone")).toBeInTheDocument();
    await press("z");
    expect(postedEvents(engine)).toHaveLength(2);
    expect(screen.getByText("Nothing to undo in this session.")).toBeInTheDocument();
  });

  it("P opens the file picker; an attachment and its Retrieved status undo together", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    const input = document.querySelector("[data-file-input]") as HTMLInputElement;
    const click = vi.spyOn(input, "click");
    await press("p");
    expect(click).toHaveBeenCalledTimes(1);
    const file = new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], "Sa 2018.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file] } });
    await press("Shift"); // let the upload settle
    const upload = engine.calls.find((c) => c.method === "POST" && c.path.includes("/attachment"))!;
    expect(upload.path).toMatch(/name=Sa\+2018\.pdf/);
    expect(within(rowOf("STU-001")).getByText("Sa 2018.pdf")).toHaveAttribute("dir", "ltr");
    expect(within(rowOf("STU-001")).getByText("Retrieved")).toBeInTheDocument();
    await press("z");
    const undo = postedEvents(engine)[0];
    expect(undo.map((e) => [e.kind, e.value])).toEqual([["attachment", null], ["fulltext_status", { status: "to_get" }]]);
  });

  it("keys are off in a text field; L, C and D stay free for Part F; Enter opens the study (Part B)", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });
    await renderCharting();
    focusRow("STU-001");
    for (const key of ["l", "c", "d"]) await press(key);
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(0);
    await press("Enter");
    expect(assign).toHaveBeenCalledWith("/en/charting/study?id=STU-001");
    fireEvent.click(within(rowOf("STU-001")).getByRole("button", { name: "Paste a link" }));
    const link = document.querySelector("[data-link-input]") as HTMLInputElement;
    link.focus();
    await press("r");
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(0);
    expect(chartingKey({ key: "r", ctrlKey: false, metaKey: false, altKey: false, shiftKey: false }, link)).toBeNull();
    expect(chartingKey({ key: "e", ctrlKey: true, metaKey: false, altKey: false, shiftKey: false }, document.body)).toBe("export");
    for (const key of ["l", "c", "d"]) {
      expect(chartingKey({ key, ctrlKey: false, metaKey: false, altKey: false, shiftKey: false }, document.body), key).toBeNull();
    }
    expect(chartingKey({ key: "Enter", ctrlKey: false, metaKey: false, altKey: false, shiftKey: false }, document.body)).toBe("enter");
    expect(chartingKey({ key: "1", ctrlKey: false, metaKey: false, altKey: false, shiftKey: false }, document.body)).toBe("viewFulltext");
    expect(chartingKey({ key: "2", ctrlKey: false, metaKey: false, altKey: false, shiftKey: false }, document.body)).toBe("viewCharting");
  });

  it("Ctrl+E opens the Export menu; its first item exports the Full text CSV", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("e", { ctrlKey: true });
    const menu = document.querySelector("[data-export-menu]") as HTMLElement;
    expect(within(menu).getAllByRole("button").map((b) => b.textContent)).toEqual(["CSV of the Full text view", "CSV of the Charting view"]);
    expect(document.activeElement).toBe(within(menu).getAllByRole("button")[0]);
    fireEvent.click(within(menu).getByRole("button", { name: "CSV of the Full text view" }));
    await press("Shift");
    expect(engine.calls.some((c) => c.method === "GET" && c.path === "/api/v1/charting/export?format=csv&view=fulltext")).toBe(true);
    expect(within(grid()).queryByRole("radiogroup")).toBeNull();
    expect(screen.getByText(/Exported .*: 1 rows/, { selector: "[data-status-line]" })).toBeInTheDocument();
  });
});
