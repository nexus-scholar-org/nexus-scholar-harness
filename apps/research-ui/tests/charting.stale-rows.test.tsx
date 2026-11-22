import { within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, postedEvents, press, renderCharting } from "./charting-helpers";

/**
 * Spec 01 "Stale / protocol changed" and DoD 2: a record that left the kept set
 * stays with its values, marked, out of the counts and off every action; a new
 * kept record is marked with the publication date; the banner says what changed.
 * The engine leaves the record out of the CSV (`test_charting_api.py`); the
 * screen asks for the file and never builds it.
 */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-study-row="${id}"]`) as HTMLElement;

describe("charting.stale-rows", () => {
  it("keeps a record that left the kept set, marked, with its values, out of the counts and of every action", async () => {
    const ft = makeRow(0).fulltext;
    const gone = makeRow(9, { kept: false, title: "A record kept earlier", fulltext: { ...ft, status: "requested" } });
    const table = makeTable([makeRow(1), makeRow(2, { new_since: "2026-11-21T09:00:00Z" }), gone], {
      changes: { published_at: "2026-11-21T09:00:00Z", added: 1, no_longer_kept: 1 },
    });
    const engine = installEngine(table);
    await renderCharting();
    expect(document.querySelector("[data-banner=changes]")).toHaveTextContent(
      "Screening was published again on 2026-11-21. 1 records were added, 1 are no longer kept.",
    );
    const row = rowOf("STU-009");
    expect(row).toHaveAttribute("data-kept", "false");
    expect(within(row).getByText("No longer kept at title and abstract")).toBeInTheDocument();
    expect(within(row).getByText("Requested")).toBeInTheDocument(); // its events are kept
    expect(within(row).queryByRole("button")).toBeNull();
    expect(within(row).getByRole("checkbox")).toBeDisabled();
    expect(document.querySelector("[data-counts]")).toHaveTextContent(/^2 kept · 0 retrieved · 0 not retrieved · 2 to get/);
    expect(within(rowOf("STU-002")).getByText("New since 2026-11-21")).toBeInTheDocument();
    expect(within(rowOf("STU-001")).queryByText(/New since/)).toBeNull();
    // A status or decision key on that row sends nothing.
    row.focus();
    await press("r");
    await press("i");
    expect(postedEvents(engine)).toHaveLength(0);
    // It appears only under All.
    const select = document.querySelector("#charting-show") as HTMLSelectElement;
    select.value = "requested";
    select.dispatchEvent(new Event("change", { bubbles: true }));
    await press("Shift");
    expect(rowOf("STU-009")).toBeNull();
  });
});
