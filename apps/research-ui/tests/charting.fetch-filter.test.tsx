import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, press, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "The To confirm filter" (M12a Part F): the Show option "Fetched, to
 * confirm" in the Full text view, its "n of m shown" line, its empty words (the
 * option stays), the rows leaving it as they are confirmed with the focus moving
 * on, and the waiting rows out of the To get list.
 */

afterEach(() => vi.unstubAllGlobals());

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const rowOf = (id: string) => desktop().querySelector(`[data-study-row="${id}"]`) as HTMLElement;
const shown = () => [...desktop().querySelectorAll<HTMLElement>("[data-study-row]")].map((r) => r.dataset.studyRow);

describe("charting.fetch-filter", () => {
  it("shows only the rows with a file waiting, with the n of m line", async () => {
    installEngine(makeTable([waitingRow(1), makeRow(2), waitingRow(3)]));
    await renderCharting();
    const select = within(desktop()).getByRole("combobox", { name: "Show" });
    expect(within(select).getByRole("option", { name: "Fetched, to confirm" })).toBeInTheDocument();
    fireEvent.change(select, { target: { value: "toConfirm" } });
    expect(shown()).toEqual(["STU-001", "STU-003"]);
    expect(desktop().querySelector("[data-shown]")).toHaveTextContent("2 of 3 shown");
    // The waiting rows are not in the To get list, as they are not in its count.
    fireEvent.change(select, { target: { value: "toGet" } });
    expect(shown()).toEqual(["STU-002"]);
  });

  it("a confirmed row leaves the list and the focus goes to the next one; empty, the option stays with its words", async () => {
    installEngine(makeTable([waitingRow(1), waitingRow(2)]));
    await renderCharting("en", "?show=toConfirm");
    fireEvent.focus(rowOf("STU-001"));
    rowOf("STU-001").focus();
    await press("c");
    expect(shown()).toEqual(["STU-002"]);
    expect(document.activeElement).toBe(rowOf("STU-002"));
    await press("c");
    expect(shown()).toEqual([]);
    expect(desktop().querySelector("[data-empty-filter]")).toHaveTextContent("No fetched file is waiting for you.");
    expect((within(desktop()).getByRole("combobox", { name: "Show" }) as HTMLSelectElement).value).toBe("toConfirm");
  });

  it("the option is the Full text view's", async () => {
    installEngine(makeTable([waitingRow(1)]));
    await renderCharting("en", "?view=charting");
    const select = within(desktop()).getByRole("combobox", { name: "Show" });
    expect(within(select).queryByRole("option", { name: "Fetched, to confirm" })).toBeNull();
  });
});
