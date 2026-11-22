import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, postedEvents, press, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Deciding on such a row (I, E)" and "Other status keys on such a row"
 * (M12a Part F): I and E on a row whose fetched file waits ask to confirm it
 * first; Enter confirms and decides in one request; Esc changes nothing. G, Q,
 * R, N and P are refused on the page with FETCH_FILE_WAITING's words, and a bulk
 * action leaves those rows as they are and says how many.
 */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-desktop] [data-study-row="${id}"]`) as HTMLElement;
const line = () => document.querySelector("[data-confirm-line]") as HTMLElement;
const statusLine = () => document.querySelector("[data-status-line]")!.textContent;

function focusRow(id: string) {
  fireEvent.focus(rowOf(id));
  rowOf(id).focus();
}

describe("charting.fetch-decide-guard", () => {
  it("I asks first; Enter confirms the file and includes the study in one request", async () => {
    const engine = installEngine(makeTable([waitingRow(1), makeRow(2)]));
    await renderCharting();
    focusRow("STU-001");
    await press("i");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(line()).toHaveTextContent("Confirm this PDF as the full text? Enter to confirm and decide · Esc to cancel");
    await press("Enter");
    const sent = postedEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0].map((e) => [e.study_id, e.kind, e.value])).toEqual([
      ["STU-001", "fetched_confirm", { manifest_row: "FMR-000000000000000000000001" }],
      ["STU-001", "fulltext_decision", { outcome: "INCLUDE" }],
    ]);
    expect(rowOf("STU-001").querySelector("[data-badge^=status]")).toHaveTextContent("Retrieved");
    expect(rowOf("STU-001").querySelector("[data-badge^=decision]")).toHaveTextContent("Include");
    // One undo takes both back, the decision first (the engine refuses a decision on a waiting row).
    await press("z");
    expect(postedEvents(engine)[1].map((e) => [e.kind, e.value])).toEqual([["fulltext_decision", null], ["fetched_confirm", null]]);
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).not.toBeNull();
    expect(rowOf("STU-001").querySelector("[data-badge^=decision]")).toHaveTextContent("To decide");
  });

  it("E asks first; Enter goes on to the reason chips; the confirm and the exclusion go in one request", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("e");
    expect(line()).toHaveTextContent("Confirm this PDF as the full text? Enter to confirm and decide");
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(line()).toHaveTextContent("Choose one reason: press its number, then Enter");
    await press("1");
    await press("Enter");
    expect(postedEvents(engine)[0].map((e) => [e.kind, e.value])).toEqual([
      ["fetched_confirm", { manifest_row: "FMR-000000000000000000000001" }],
      ["fulltext_decision", { outcome: "EXCLUDE", reason_code: "EXC-01" }],
    ]);
  });

  it("Esc at the question changes nothing", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("i");
    await press("Escape");
    expect(line().textContent).toBe("");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).not.toBeNull();
  });

  it("G, Q, R, N and P are refused on a waiting row with FETCH_FILE_WAITING's words", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    const click = vi.spyOn(HTMLInputElement.prototype, "click");
    await renderCharting();
    focusRow("STU-001");
    for (const key of ["g", "q", "r", "n", "p"]) {
      await press(key);
      expect(statusLine(), key).toBe("A fetched file is waiting on this row. Confirm it or discard it first.");
      expect(line().textContent, key).toBe("");
    }
    expect(postedEvents(engine)).toHaveLength(0);
    expect(click).not.toHaveBeenCalled();
    click.mockRestore();
  });

  it("a bulk status skips the rows with a file waiting and says how many", async () => {
    const engine = installEngine(makeTable([waitingRow(1), makeRow(2), makeRow(3), waitingRow(4)]));
    await renderCharting();
    focusRow("STU-001");
    await press("a");
    await press("q");
    expect(line()).toHaveTextContent("Mark 2 records as Requested? Enter to confirm · Esc to cancel");
    expect(line().querySelector("[data-bulk-skipped]")).toHaveTextContent("2 of these have a fetched file waiting and are left as they are.");
    await press("Enter");
    expect(postedEvents(engine)[0].map((e) => e.study_id)).toEqual(["STU-002", "STU-003"]);
    // Not retrieved says it too, beside its reasons.
    await press("n");
    expect(line().querySelector("[data-bulk-skipped]")).toHaveTextContent("2 of these have a fetched file waiting and are left as they are.");
  });

  it("FETCH_FILE_WAITING from the engine has its words", async () => {
    installEngine(makeTable([makeRow(1)]), { refuse: { "STU-001": "FETCH_FILE_WAITING" } });
    await renderCharting();
    focusRow("STU-001");
    await press("r");
    expect(document.querySelector("[data-desktop] [data-refusal=FETCH_FILE_WAITING]")).toHaveTextContent("A fetched file is waiting on this row. Confirm it or discard it first.");
  });
});
