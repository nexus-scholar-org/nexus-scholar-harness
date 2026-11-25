import { act, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { flush, installEngine, makeRow, makeTable, press, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Look-up plan" (M12a Part F): L opens an inline block fed by the
 * plan; it counts the records by DOI and by arXiv id and those with neither,
 * names the e-mail (left to right) and whether OpenAlex is asked, and what it
 * leaves out; Enter starts with `confirm: true`, Esc cancels; "Counting…" until
 * the plan answers; nothing to look up says so with no Start; MAILTO_NOT_SET is
 * an alert card with no Start. The Start button is quiet and bordered.
 */

afterEach(() => vi.unstubAllGlobals());

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const rowOf = (id: string) => desktop().querySelector(`[data-study-row="${id}"]`) as HTMLElement;
const block = () => desktop().querySelector("[data-fetch-plan]") as HTMLElement | null;
const lines = () => [...desktop().querySelectorAll<HTMLElement>("[data-plan-line]")].map((l) => l.textContent);

function focusRow(id: string) {
  fireEvent.focus(rowOf(id));
  rowOf(id).focus();
}

/** Three records with a DOI, one with only an arXiv id, one with neither; one already retrieved, one waiting. */
function rows() {
  const ft = makeRow(0).fulltext;
  return [
    makeRow(1),
    makeRow(2),
    makeRow(3),
    makeRow(4, { doi: null, arxiv_id: "2101.00001" }),
    makeRow(5, { doi: null }),
    makeRow(6, { fulltext: { ...ft, status: "retrieved" } }),
    waitingRow(7),
  ];
}

describe("charting.fetch-plan", () => {
  it("L with nothing selected: every record To get, counted by DOI, arXiv id and neither, with the e-mail and OpenAlex not asked", async () => {
    const engine = installEngine(makeTable(rows()));
    await renderCharting();
    focusRow("STU-001");
    await press("l");
    expect(engine.calls.some((c) => c.method === "GET" && c.path === "/api/v1/charting/fetch/plan")).toBe(true);
    expect(block()).toHaveAttribute("data-fetch-plan", "ready");
    expect(block()).toHaveTextContent("Look up open-access copies of 5 records?");
    expect(lines()).toEqual([
      "No rows are selected, so this covers every record that is To get.",
      "Asks Unpaywall with your contact e-mail you@example.org, for the 3 records with a DOI.",
      "Asks arXiv for the 1 records with only an arXiv id, one request every three seconds.",
      "OpenAlex is not asked: SCHOLAR_OPENALEX_KEY is not set.",
      "1 have neither a DOI nor an arXiv id and are skipped.",
      // The waiting row is still To get underneath: the plan counts it as left out.
      "1 already have a file or one waiting and are not asked.",
      "It downloads only PDFs these services list as open access, and nothing else.",
    ]);
    expect(within(block()!).getByText("you@example.org")).toHaveAttribute("dir", "ltr");
    expect(within(block()!).getByText("SCHOLAR_OPENALEX_KEY")).toHaveAttribute("dir", "ltr");
    // The block is announced and takes focus.
    expect(desktop().querySelector("[data-confirm-line]")).toHaveAttribute("aria-live", "polite");
    expect(document.activeElement).toBe(block());
    // Start is quiet and bordered; the screen keeps its one brand button.
    const start = within(block()!).getByRole("button", { name: "Start the look-up" });
    expect(start).toHaveAttribute("data-variant", "secondary");
    expect(within(block()!).getByText("Enter to start · Esc to cancel")).toBeInTheDocument();
    expect(desktop().querySelectorAll("[data-variant=primary]").length).toBeLessThanOrEqual(1);
    await press("Enter");
    expect(engine.fetch.starts).toEqual([{ scope: "to_get", confirm: true }]);
    expect(block()).toBeNull();
  });

  it("a selection is planned by its ids; with no DOI or arXiv id left, nothing to look up and no Start", async () => {
    const engine = installEngine(makeTable(rows()), { fetch: { openalexKey: true } });
    await renderCharting();
    focusRow("STU-005");
    await press("x");
    await press("j");
    await press("x");
    await press("j");
    await press("x");
    await press("l");
    expect(engine.calls.find((c) => c.path.startsWith("/api/v1/charting/fetch/plan"))!.path).toBe("/api/v1/charting/fetch/plan?ids=STU-005%2CSTU-006%2CSTU-007");
    expect(lines()).toEqual([]);
    expect(block()).toHaveAttribute("data-fetch-plan", "nothing");
    expect(block()).toHaveTextContent("Nothing to look up: the 3 records have a file, or no DOI or arXiv id.");
    expect(within(block()!).queryByRole("button", { name: "Start the look-up" })).toBeNull();
    await press("Enter");
    expect(engine.fetch.starts).toHaveLength(0);
  });

  it("names what is left out, OpenAlex with the key, and starts the selection by its ids", async () => {
    const engine = installEngine(makeTable(rows()), { fetch: { openalexKey: true } });
    await renderCharting();
    focusRow("STU-001");
    await press("x");
    for (let i = 0; i < 6; i++) {
      await press("j");
      await press("x");
    }
    await press("l");
    expect(lines()).toEqual([
      "Asks Unpaywall with your contact e-mail you@example.org, for the 3 records with a DOI.",
      "Asks arXiv for the 1 records with only an arXiv id, one request every three seconds.",
      "Asks OpenAlex too, with your key.",
      "1 have neither a DOI nor an arXiv id and are skipped.",
      "2 already have a file or one waiting and are not asked.",
      "It downloads only PDFs these services list as open access, and nothing else.",
    ]);
    fireEvent.click(within(block()!).getByRole("button", { name: "Start the look-up" }));
    await flush();
    expect(engine.fetch.starts).toEqual([{ ids: ["STU-001", "STU-002", "STU-003", "STU-004", "STU-005", "STU-006", "STU-007"], confirm: true }]);
  });

  it("Counting… until the plan answers; Enter does nothing until then", async () => {
    let release: () => void = () => undefined;
    const engine = installEngine(makeTable(rows()), { fetch: { planHold: new Promise<void>((resolve) => (release = resolve)) } });
    await renderCharting();
    focusRow("STU-001");
    await press("l");
    expect(block()).toHaveAttribute("data-fetch-plan", "counting");
    expect(block()).toHaveAttribute("aria-busy", "true");
    expect(block()).toHaveTextContent("Counting…");
    await press("Enter");
    expect(engine.fetch.starts).toHaveLength(0);
    await act(async () => release());
    await flush();
    expect(block()).toHaveAttribute("data-fetch-plan", "ready");
  });

  it("Esc cancels: nothing is started and the focus goes back to the row, or to the button that opened it", async () => {
    const engine = installEngine(makeTable(rows()));
    await renderCharting();
    focusRow("STU-002");
    await press("l");
    await press("Escape");
    expect(block()).toBeNull();
    expect(document.activeElement).toBe(rowOf("STU-002"));
    const button = within(desktop()).getByRole("button", { name: /Look up open-access copies/ });
    fireEvent.click(button);
    await flush();
    expect(block()).not.toBeNull();
    await press("Escape");
    await flush();
    expect(document.activeElement).toBe(button);
    expect(engine.fetch.starts).toHaveLength(0);
  });

  it("MAILTO_NOT_SET: an alert card with the words and the code, no Start", async () => {
    const engine = installEngine(makeTable(rows()), { fetch: { mailto: false } });
    await renderCharting();
    focusRow("STU-001");
    await press("l");
    const card = block()!;
    expect(card).toHaveAttribute("data-fetch-plan", "mailto");
    const alert = within(card).getByRole("alert");
    expect(alert).toHaveTextContent(
      "A look-up needs a contact e-mail: the open-access services ask for it on every request. Save it on the Settings screen; it applies at once. Or set SCHOLAR_MAILTO for the console (environment or .env) and start it again. Nothing was sent.",
    );
    expect(within(alert).getByText("MAILTO_NOT_SET", { selector: "details span" })).toHaveAttribute("dir", "ltr");
    expect(within(card).queryByRole("button", { name: "Start the look-up" })).toBeNull();
    await press("Enter");
    expect(engine.fetch.starts).toHaveLength(0);
  });

  it("the button is disabled with its words when every record has a file or is not To get", async () => {
    const ft = makeRow(0).fulltext;
    installEngine(makeTable([makeRow(1, { fulltext: { ...ft, status: "retrieved" } }), waitingRow(2)]));
    await renderCharting();
    expect(within(desktop()).getByRole("button", { name: /Look up open-access copies/ })).toBeDisabled();
    expect(desktop().querySelector("[data-fetch-look-disabled]")).toHaveTextContent("Every record has a file or is not To get");
  });

  it("the button is the Full text view's only", async () => {
    installEngine(makeTable(rows()));
    await renderCharting("en", "?view=charting");
    expect(within(desktop()).queryByRole("button", { name: /Look up open-access copies/ })).toBeNull();
  });
});
