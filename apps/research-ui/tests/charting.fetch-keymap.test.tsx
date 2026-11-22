import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { chartingKey } from "@/lib/charting-logic";

import { installEngine, makeRow, makeTable, postedEvents, press, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Keyboard" (M12a Part F): L, C and D act in the Full text view only;
 * every key of Parts A and B keeps its meaning; Ctrl+C and Ctrl+D stay the
 * browser's; the keys are off in a text field; `?` help names them.
 */

afterEach(() => vi.unstubAllGlobals());

const plain = { ctrlKey: false, metaKey: false, altKey: false, shiftKey: false };
const rowOf = (id: string) => document.querySelector(`[data-desktop] [data-study-row="${id}"]`) as HTMLElement;

function focusRow(id: string) {
  fireEvent.focus(rowOf(id));
  rowOf(id).focus();
}

describe("charting.fetch-keymap", () => {
  it("maps L, C and D, leaves every other key as it was, and leaves Ctrl+C and Ctrl+D to the browser", () => {
    expect(chartingKey({ ...plain, key: "l" }, document.body)).toBe("lookup");
    expect(chartingKey({ ...plain, key: "c" }, document.body)).toBe("confirm");
    expect(chartingKey({ ...plain, key: "d" }, document.body)).toBe("discard");
    expect(chartingKey({ ...plain, key: "L", shiftKey: true }, document.body)).toBe("lookup");
    expect(chartingKey({ ...plain, key: "c", ctrlKey: true }, document.body)).toBeNull();
    expect(chartingKey({ ...plain, key: "d", ctrlKey: true }, document.body)).toBeNull();
    expect(chartingKey({ ...plain, key: "c", metaKey: true }, document.body)).toBeNull();
    const before: Record<string, string> = {
      j: "down", k: "up", x: "toggle", a: "selectAll", g: "toGet", q: "requested", r: "retrieved", n: "notRetrieved",
      i: "include", e: "exclude", p: "attach", o: "open", z: "undo", "?": "help", "1": "viewFulltext", "2": "viewCharting", f: "form", Enter: "enter",
    };
    for (const [key, action] of Object.entries(before)) expect(chartingKey({ ...plain, key }, document.body), key).toBe(action);
    const input = document.createElement("input");
    for (const key of ["l", "c", "d"]) expect(chartingKey({ ...plain, key }, input), key).toBeNull();
  });

  it("act in the Full text view only; in the Charting view they do nothing", async () => {
    const engine = installEngine(makeTable([waitingRow(1), makeRow(2)]));
    await renderCharting("en", "?view=charting");
    for (const key of ["l", "c", "d"]) await press(key);
    expect(engine.calls.some((c) => c.path.startsWith("/api/v1/charting/fetch/plan"))).toBe(false);
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-fetch-plan]")).toBeNull();
    expect(document.querySelector("[data-confirm-line]")!.textContent).toBe("");
  });

  it("are off in a text field (the words of Other)", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("d");
    await press("4");
    const words = document.querySelector("[data-mode-words]") as HTMLInputElement;
    expect(words).toHaveFocus();
    for (const key of ["l", "c", "d"]) await press(key);
    expect(engine.calls.some((c) => c.path.startsWith("/api/v1/charting/fetch/plan"))).toBe(false);
    expect(postedEvents(engine)).toHaveLength(0);
  });

  it("Ctrl+C on a waiting row confirms nothing", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("c", { ctrlKey: true });
    await press("d", { ctrlKey: true });
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-confirm-line]")!.textContent).toBe("");
  });

  it("O opens the waiting file in a new tab", async () => {
    installEngine(makeTable([waitingRow(1)]));
    const open = vi.fn();
    vi.stubGlobal("open", open);
    await renderCharting();
    focusRow("STU-001");
    await press("o");
    expect(open).toHaveBeenCalledWith("/api/console/api/v1/charting/records/STU-001/fetched", "_blank", "noopener");
  });

  it("? help names the keys of the look-up", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    focusRow("STU-001");
    await press("?");
    expect(document.querySelector("[data-help-fetch]")).toHaveTextContent("L look up open-access copies · C confirm the fetched file · D discard it, then a number · O open it");
  });
});
