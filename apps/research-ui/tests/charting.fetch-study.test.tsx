import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { flush, installEngine, lastLookup, makeChartingTable, makeRow, manifestRow, postedEvents, press, renderStudy, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "One-study view (02)" (M12a Part F): a waiting file takes the place
 * of the status choice (disabled, with its note); the same badge, source,
 * version, licence, size, identity, Open, Confirm and Discard (with the chips
 * inline), then "What was tried"; "Charting from the abstract" stays until the
 * file is confirmed; L asks the plan of this one record; C, D, I, E and Z as in
 * the table.
 */

afterEach(() => vi.unstubAllGlobals());

const block = () => document.querySelector("[data-fulltext-block]") as HTMLElement;

/** Keys act outside the form's fields: the study region holds the focus. */
function focusStudy() {
  (document.querySelector("[data-region=study]") as HTMLElement).focus();
}

describe("charting.fetch-study", () => {
  it("shows the waiting file in place of the status choice, which is off with its note", async () => {
    installEngine(makeChartingTable([waitingRow(1, { identity: "not checked", duplicate_of: ["STU-002"] }), makeRow(2)]));
    await renderStudy("STU-001");
    expect(block().querySelector("[data-note-waiting]")).toHaveTextContent("Fetched, to confirmA fetched file is waiting");
    for (const radio of within(block().querySelector("[data-status-control]") as HTMLElement).getAllByRole("radio")) expect(radio).toBeDisabled();
    const file = block().querySelector("[data-pending-file]") as HTMLElement;
    expect(file.querySelector("[data-fetch-size]")).toHaveTextContent("1.2 MB");
    expect(file.querySelector("[data-fetch-source]")).toHaveTextContent("Found by Unpaywall · europepmc.org");
    expect(file.querySelector("[data-fetch-version]")).toHaveTextContent("Published version");
    expect(file.querySelector("[data-fetch-licence]")).toHaveTextContent("Licence: cc-by");
    expect(file.querySelector("[data-identity]")).toHaveTextContent("Not checked: open it");
    expect(file.querySelector("[data-fetch-duplicate]")).toHaveTextContent("The same file is waiting for another record: Study number 2");
    expect(within(file).getByRole("link", { name: "Open the file of Study number 1" })).toBeInTheDocument();
    expect(within(file).getByRole("button", { name: "Confirm the file of Study number 1" })).toBeInTheDocument();
    expect(within(file).getByRole("button", { name: "Discard the file of Study number 1" })).toBeInTheDocument();
    // Below 640 px the two actions leave and the desktop line shows (CSS picks).
    expect((file.querySelector("[data-fetch-actions]") as HTMLElement).className).toMatch(/\bhidden\b.*\bsm:inline-flex\b/);
    expect(file.querySelector("[data-fetch-mobile]")).toHaveTextContent("Confirm or discard this file on your desktop.");
    expect((file.querySelector("[data-fetch-mobile]") as HTMLElement).className).toMatch(/\bsm:hidden\b/);
    // Charting stays allowed, from the abstract until the file is confirmed.
    expect(document.querySelector("[data-from-abstract]")).toHaveTextContent("Charting from the abstract. This row is counted as having no full text.");
  });

  it("C confirms in one request; the study reads Retrieved and charts from the file; Z puts the file back", async () => {
    const engine = installEngine(makeChartingTable([waitingRow(1), makeRow(2)]));
    await renderStudy("STU-001");
    focusStudy();
    await press("c");
    expect(postedEvents(engine)[0].map((e) => [e.study_id, e.kind])).toEqual([["STU-001", "fetched_confirm"]]);
    expect(block().querySelector("[data-pending-file]")).toBeNull();
    expect(block().querySelector("[data-status=retrieved]")).toHaveAttribute("aria-checked", "true");
    expect(document.querySelector("[data-from-abstract]")).toBeNull();
    expect(document.querySelector("[data-announce]")).toHaveTextContent("Confirmed. 0 files to confirm.");
    focusStudy();
    await press("z");
    expect(postedEvents(engine)[1][0]).toMatchObject({ kind: "fetched_confirm", value: null });
    expect(block().querySelector("[data-pending-file]")).not.toBeNull();
    expect(document.querySelector("[data-from-abstract]")).not.toBeNull();
  });

  it("D opens the four reasons inline; a number and Enter discard; the earlier status returns", async () => {
    const engine = installEngine(makeChartingTable([waitingRow(1)]));
    await renderStudy("STU-001");
    focusStudy();
    await press("d");
    const chips = within(block()).getByRole("radiogroup", { name: "Discard" });
    expect(within(chips).getAllByRole("radio")).toHaveLength(4);
    await press("Enter");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("Choose one reason first, then discard.");
    await press("2");
    await press("Enter");
    expect(postedEvents(engine)[0][0].value).toEqual({ manifest_row: "FMR-000000000000000000000001", reason: "not_full_text" });
    expect(block().querySelector("[data-pending-file]")).toBeNull();
    expect(block().querySelector("[data-status=to_get]")).toHaveAttribute("aria-checked", "true");
    expect(block().querySelector("[data-discarded]")).toHaveTextContent("Discarded: not the full text");
  });

  it("I asks first, then confirms and includes in one request; G is refused with its words", async () => {
    const engine = installEngine(makeChartingTable([waitingRow(1)]));
    await renderStudy("STU-001");
    focusStudy();
    await press("g");
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("A fetched file is waiting on this row. Confirm it or discard it first.");
    await press("i");
    expect(block().querySelector("[data-confirm-line]")).toHaveTextContent("Confirm this PDF as the full text? Enter to confirm and decide · Esc to cancel");
    await press("Enter");
    expect(postedEvents(engine)[0].map((e) => [e.kind, e.value])).toEqual([
      ["fetched_confirm", { manifest_row: "FMR-000000000000000000000001" }],
      ["fulltext_decision", { outcome: "INCLUDE" }],
    ]);
  });

  it("L asks the plan of this one record; Enter starts it by its id", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1), makeRow(2)]));
    await renderStudy("STU-001");
    focusStudy();
    await press("l");
    expect(engine.calls.some((c) => c.path === "/api/v1/charting/fetch/plan?ids=STU-001")).toBe(true);
    const plan = block().querySelector("[data-fetch-plan]") as HTMLElement;
    expect(plan).toHaveTextContent("Look up open-access copies of 1 record?");
    expect(plan).not.toHaveTextContent("No rows are selected");
    expect(document.activeElement).toBe(plan);
    await press("Enter");
    expect(engine.fetch.starts).toEqual([{ ids: ["STU-001"], confirm: true }]);
    expect(block().querySelector("[data-fetch-run]")).not.toBeNull();
  });

  it("after a failed look-up: the same line and the same panel as the table", async () => {
    installEngine(makeChartingTable([makeRow(1, { fulltext: { ...makeRow(1).fulltext, last_lookup: lastLookup({ outcome: "NO_OPEN_COPY_LISTED" }) } })]), {
      fetch: { manifest: { "STU-001": [manifestRow()] } },
    });
    await renderStudy("STU-001");
    expect(block().querySelector("[data-last-lookup]")!.textContent).toMatch(/: no open copy listed$/);
    fireEvent.click(within(block()).getByRole("button", { name: "What was tried" }));
    await flush();
    expect(block().querySelector("[data-tried-not-paywall]")).toHaveTextContent("This is not a paywall determination.");
    focusStudy();
    await press("Escape");
    expect(block().querySelector("[data-tried]")).toBeNull();
  });
});
