import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Accessibility" (M12a Part F): the badge and the identity result are
 * words plus an icon, never colour alone; the draft mark is the dashed border
 * plus the word; the only tint is `unclear`, on its soft surface, for "Not
 * found in the file" and the duplicate warning.
 */

afterEach(() => vi.unstubAllGlobals());

describe("charting.fetch-not-by-colour", () => {
  it("every badge, identity result and warning of the look-up has words and an icon", async () => {
    installEngine(
      makeTable([
        waitingRow(1, { identity: "doi found" }),
        waitingRow(2, { identity: "title found" }),
        waitingRow(3, { identity: "not found: check it", duplicate_of: ["STU-004"] }),
        waitingRow(4, { identity: "not checked", duplicate_of: ["STU-003"] }),
        makeRow(5),
      ]),
    );
    await renderCharting();
    const desktop = document.querySelector("[data-desktop]") as HTMLElement;
    const marks = [
      ...desktop.querySelectorAll<HTMLElement>("[data-badge=fetch-to-confirm]"),
      ...desktop.querySelectorAll<HTMLElement>("[data-identity] > [data-role]"),
      ...desktop.querySelectorAll<HTMLElement>("[data-fetch-duplicate]"),
    ];
    expect(marks).toHaveLength(4 + 4 + 2);
    for (const mark of marks) {
      expect(mark.textContent?.trim(), mark.outerHTML.slice(0, 60)).not.toBe("");
      expect(mark.querySelector("svg[data-icon]"), mark.outerHTML.slice(0, 60)).not.toBeNull();
      expect(mark.getAttribute("data-role")).toMatch(/^(neutral|unclear)$/);
      // The unclear tint sits only on its soft surface; nothing of the look-up is green before a confirm.
      if (mark.getAttribute("data-role") === "unclear") expect(mark.className).toMatch(/bg-unclear-soft/);
      expect(mark.className).not.toMatch(/include/);
    }
    // The draft mark is the dashed border and the word.
    for (const badge of desktop.querySelectorAll<HTMLElement>("[data-badge=fetch-to-confirm]")) {
      expect(badge.className).toMatch(/border-dashed/);
      expect(badge).toHaveTextContent("Fetched, to confirm");
    }
  });
});
