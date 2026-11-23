import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, noLongerKeptWaitingRow, postedEvents, press, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Confirm (C, or the button)" (M12a Part F): C confirms the focused
 * row's file in one keypress and one request for one study; the engine adds the
 * attachment and Retrieved; Z puts the file back to wait; a file whose identity
 * was not found, or whose bytes wait for another record, asks first; with
 * several rows selected C says one at a time; a row with no file says so;
 * FETCH_NOT_PENDING has its words.
 */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-desktop] [data-study-row="${id}"]`) as HTMLElement;
const announce = () => document.querySelector("[data-announce]")!.textContent;
const statusLine = () => document.querySelector("[data-status-line]")!.textContent;

function focusRow(id: string) {
  fireEvent.focus(rowOf(id));
  rowOf(id).focus();
}

describe("charting.fetch-confirm", () => {
  it("C confirms the focused row in one keypress: one request, one study; the row reads Retrieved with its file", async () => {
    const engine = installEngine(makeTable([waitingRow(1), waitingRow(2), makeRow(3)]));
    await renderCharting();
    focusRow("STU-001");
    await press("c");
    const sent = postedEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0]).toHaveLength(1);
    expect(sent[0][0]).toMatchObject({ study_id: "STU-001", kind: "fetched_confirm", value: { manifest_row: "FMR-000000000000000000000001" } });
    expect(rowOf("STU-001").querySelector("[data-badge^=status]")).toHaveTextContent("Retrieved");
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).toBeNull();
    expect(rowOf("STU-001").querySelector("[data-file-name]")).toHaveTextContent("STU-001.pdf");
    expect(announce()).toBe("Confirmed. 1 files to confirm.");
    expect(document.querySelector("[data-counts]")!.textContent).toContain("1 retrieved");
    expect(document.querySelector("[data-counts]")!.textContent).toContain("1 to confirm");
    // The focus goes on to the next row of the list.
    expect(document.activeElement).toBe(rowOf("STU-002"));
  });

  it("Z undoes the confirm: the file waits again and the row returns to its earlier status", async () => {
    const engine = installEngine(makeTable([waitingRow(1), makeRow(2)]));
    await renderCharting();
    focusRow("STU-001");
    await press("c");
    await press("z");
    const undo = postedEvents(engine)[1];
    expect(undo).toHaveLength(1);
    expect(undo[0]).toMatchObject({ kind: "fetched_confirm", value: null, supersedes: postedEvents(engine)[0][0].event_id });
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).toHaveTextContent("Fetched, to confirm");
    expect(rowOf("STU-001").querySelector("[data-badge^=status]")).toHaveTextContent("To get");
    expect(document.querySelector("[data-counts]")!.textContent).toContain("1 to confirm");
  });

  it("a preprint, a version not given or 'Not checked' does not ask", async () => {
    const engine = installEngine(makeTable([waitingRow(1, { identity: "not checked", version: null, version_label: null })]));
    await renderCharting();
    focusRow("STU-001");
    await press("c");
    expect(postedEvents(engine)).toHaveLength(1);
  });

  it("the Confirm button does what C does", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    fireEvent.click(within(rowOf("STU-001")).getByRole("button", { name: "Confirm the file of Study number 1" }));
    await press("Shift");
    expect(postedEvents(engine)[0][0]).toMatchObject({ kind: "fetched_confirm" });
  });

  it("FETCH_NOT_PENDING: the file is not waiting any more, in words with its code", async () => {
    installEngine(makeTable([waitingRow(1)]), { refuse: { "STU-001": "FETCH_NOT_PENDING" } });
    await renderCharting();
    focusRow("STU-001");
    await press("c");
    const alert = document.querySelector("[data-desktop] [data-refusal=FETCH_NOT_PENDING]") as HTMLElement;
    expect(alert).toHaveAttribute("role", "alert");
    expect(alert).toHaveTextContent("That file is not waiting for you any more. Reload the table.");
    expect(within(alert).getByText("FETCH_NOT_PENDING")).toHaveAttribute("dir", "ltr");
  });

  it("protocol replaced: the waiting file stays listed and can be opened; L, C, D and Cancel are off", async () => {
    const engine = installEngine(makeTable([waitingRow(1), makeRow(2)], { read_only: true, read_only_code: "CHARTING_PROTOCOL_REPLACED" }), {
      fetch: { runs: [{ state: "running", run_id: "FR-1", total: 2, reached: 1 }] },
    });
    await renderCharting();
    const desktop = document.querySelector("[data-desktop]") as HTMLElement;
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).not.toBeNull();
    expect(within(rowOf("STU-001")).getByRole("link", { name: "Open the file of Study number 1" })).toBeInTheDocument();
    expect(within(rowOf("STU-001")).getByRole("button", { name: "Confirm the file of Study number 1" })).toBeDisabled();
    expect(within(rowOf("STU-001")).getByRole("button", { name: "Discard the file of Study number 1" })).toBeDisabled();
    expect(within(desktop).getByRole("button", { name: /Look up open-access copies/ })).toBeDisabled();
    expect(within(desktop.querySelector("[data-fetch-run]") as HTMLElement).getByRole("button", { name: "Cancel the look-up" })).toBeDisabled();
    focusRow("STU-001");
    for (const key of ["l", "c", "d"]) await press(key);
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(0);
    expect(engine.calls.some((c) => c.path.startsWith("/api/v1/charting/fetch/plan"))).toBe(false);
    expect(statusLine()).toBe("This table belongs to the old protocol. It is kept, read-only, with that protocol.");
    expect(desktop.querySelector("[data-banner=archived]")).toHaveTextContent("CHARTING_PROTOCOL_REPLACED");
  });

  it("a record no longer kept keeps its waiting file, marked so; C and D are refused RECORD_NOT_KEPT, Open still works", async () => {
    const engine = installEngine(makeTable([noLongerKeptWaitingRow(1), makeRow(2)]));
    await renderCharting();
    expect(rowOf("STU-001").querySelector("[data-no-longer-kept]")).toHaveTextContent("No longer kept at title and abstract");
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).toHaveTextContent("Fetched, to confirm");
    expect(within(rowOf("STU-001")).getByRole("link", { name: "Open the file of Study number 1" })).toBeInTheDocument();
    expect(within(rowOf("STU-001")).getByRole("button", { name: "Confirm the file of Study number 1" })).toBeDisabled();
    // Not counted: the row is out of the kept set.
    expect(document.querySelector("[data-counts]")!.textContent).not.toMatch(/to confirm/);
    focusRow("STU-001");
    await press("c");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-desktop] [data-refusal=RECORD_NOT_KEPT]")).toHaveTextContent("That study is not in the kept set any more. Reload the table.");
    await press("d");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-confirm-line]")!.textContent).toBe("");
  });

  it("offline: Open of a waiting file says the console is not answering", async () => {
    const engine = installEngine(makeTable([waitingRow(1), makeRow(2)]));
    const open = vi.fn();
    vi.stubGlobal("open", open);
    await renderCharting();
    focusRow("STU-002");
    engine.fail = "unreachable";
    await press("r");
    focusRow("STU-001");
    await press("o");
    expect(open).not.toHaveBeenCalled();
    expect(statusLine()).toBe("The console is not answering, so the change was not sent.");
    const link = within(rowOf("STU-001")).getByRole("link", { name: "Open the file of Study number 1" });
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    link.dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
  });

  it("C and D do nothing in the Charting view", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting("en", "?view=charting");
    (document.querySelector("[data-desktop]") as HTMLElement).focus();
    await press("c");
    await press("d");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-confirm-line]")!.textContent).toBe("");
  });
});
