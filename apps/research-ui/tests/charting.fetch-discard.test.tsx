import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, postedEvents, press, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Discard (D)" (M12a Part F): D opens the four reason chips in the
 * existing mode (1 to 4, Enter, Esc); Other needs words; without a reason the
 * page says DISCARD_REASON_REQUIRED's words and sends nothing; the row returns to
 * its earlier status with "Discarded: <reason>"; Z brings the file back.
 */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-desktop] [data-study-row="${id}"]`) as HTMLElement;
const statusLine = () => document.querySelector("[data-status-line]")!.textContent;

function focusRow(id: string) {
  fireEvent.focus(rowOf(id));
  rowOf(id).focus();
}

describe("charting.fetch-discard", () => {
  it("offers the four reasons as numbered chips", async () => {
    installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("d");
    const line = document.querySelector("[data-confirm-line]") as HTMLElement;
    expect(line).toHaveTextContent("Discard: Study number 1 · Why discard it? Press a number, then Enter");
    const group = within(line).getByRole("radiogroup", { name: "Discard" });
    expect(within(group).getAllByRole("radio").map((r) => r.textContent)).toEqual([
      "1Wrong paper",
      "2Not the full text (abstract, supplement, landing page)",
      "3Unreadable",
      "4Other, with words",
    ]);
  });

  it("Enter without a reason sends nothing and says to choose one; a number then Enter discards", async () => {
    const engine = installEngine(makeTable([waitingRow(1, {}, { fulltext: { ...makeRow(1).fulltext, status: "requested", requested_on: "2026-11-20" } }), makeRow(2)]));
    await renderCharting();
    focusRow("STU-001");
    await press("d");
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(statusLine()).toBe("Choose one reason first, then discard.");
    await press("1");
    await press("Enter");
    const sent = postedEvents(engine);
    expect(sent).toHaveLength(1);
    expect(sent[0][0]).toMatchObject({ study_id: "STU-001", kind: "fetched_discard", value: { manifest_row: "FMR-000000000000000000000001", reason: "wrong_paper" } });
    expect(sent[0][0].value).not.toHaveProperty("reason_text");
    // The row is back to its earlier status, with the reason.
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).toBeNull();
    expect(rowOf("STU-001").querySelector("[data-badge^=status]")).toHaveTextContent("Requested on 2026-11-20");
    expect(rowOf("STU-001").querySelector("[data-discarded]")).toHaveTextContent("Discarded: wrong paper");
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Discarded. 0 files to confirm.");
  });

  it("Other needs words: the field takes focus, Enter with it empty sends nothing", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("d");
    await press("4");
    const words = document.querySelector("[data-mode-words]") as HTMLInputElement;
    expect(words).toHaveFocus();
    expect(within(document.querySelector("[data-confirm-line]") as HTMLElement).getByText("Why it is discarded")).toBeInTheDocument();
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(statusLine()).toBe("Choose one reason first, then discard.");
    fireEvent.change(words, { target: { value: "A poster of the same study" } });
    await press("Enter");
    expect(postedEvents(engine)[0][0].value).toEqual({ manifest_row: "FMR-000000000000000000000001", reason: "other", reason_text: "A poster of the same study" });
    expect(rowOf("STU-001").querySelector("[data-discarded]")).toHaveTextContent("Discarded: A poster of the same study");
  });

  it("DISCARD_REASON_REQUIRED from the engine has its words", async () => {
    installEngine(makeTable([waitingRow(1)]), { refuse: { "STU-001": "DISCARD_REASON_REQUIRED" } });
    await renderCharting();
    focusRow("STU-001");
    await press("d");
    await press("3");
    await press("Enter");
    expect(document.querySelector("[data-desktop] [data-refusal=DISCARD_REASON_REQUIRED]")).toHaveTextContent("Choose one reason first, then discard.");
  });

  it("Esc closes the chips and changes nothing; Z brings a discarded file back", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("d");
    await press("Escape");
    expect(document.querySelector("[data-confirm-line]")!.textContent).toBe("");
    expect(postedEvents(engine)).toHaveLength(0);
    await press("d");
    await press("3");
    await press("Enter");
    await press("z");
    const undo = postedEvents(engine)[1][0];
    expect(undo).toMatchObject({ kind: "fetched_discard", value: null, supersedes: postedEvents(engine)[0][0].event_id });
    expect(rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]")).toHaveTextContent("Fetched, to confirm");
    expect(rowOf("STU-001").querySelector("[data-discarded]")).toBeNull();
  });

  it("the Discard button opens the same chips", async () => {
    installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    fireEvent.click(within(rowOf("STU-001")).getByRole("button", { name: "Discard the file of Study number 1" }));
    await press("Shift");
    expect(within(document.querySelector("[data-confirm-line]") as HTMLElement).getByRole("radiogroup", { name: "Discard" })).toBeInTheDocument();
  });
});
