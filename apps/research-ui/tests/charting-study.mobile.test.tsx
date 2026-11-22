import { afterEach, describe, expect, it, vi } from "vitest";

import { isOneScreenRoute } from "@/components/app-shell";

import { installEngine, makeChartingTable, makeRow, renderStudy } from "./charting-helpers";

/**
 * Spec 02 "Mobile layout" and "Desktop layout" (M12a Part B): one study stacked
 * on a phone (study, full-text part, abstract, then the form), 44 px targets,
 * Previous and Next at the bottom, no bulk action and no form panel; from
 * 1024 px a focus screen whose two columns scroll inside themselves.
 */

afterEach(() => vi.unstubAllGlobals());

describe("charting-study.mobile", () => {
  it("stacks the study before the form below 1024 px and splits them 55 / 45 above", async () => {
    installEngine(makeChartingTable([makeRow(1), makeRow(2)]));
    await renderStudy("STU-001");
    const study = document.querySelector("[data-region=study]") as HTMLElement;
    const form = document.querySelector("[data-region=form]") as HTMLElement;
    const columns = study.parentElement!;
    expect(columns.className).toMatch(/(^|\s)flex-col(\s|$)/);
    expect(columns.className).toMatch(/lg:grid-cols-\[minmax\(0,55fr\)_minmax\(0,45fr\)\]/);
    expect(study.compareDocumentPosition(form) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // Study first, then its full-text part, then the abstract.
    const order = ["[data-fulltext-block]", "[data-abstract]"].map((s) => study.querySelector(s)!);
    expect(order[0].compareDocumentPosition(order[1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // Each region scrolls inside itself from 1024 px and is reachable by keyboard.
    for (const region of [study, form]) {
      expect(region.className).toMatch(/lg:overflow-y-auto/);
      expect(region).toHaveAttribute("tabindex", "0");
      expect(region).toHaveAttribute("aria-labelledby");
    }
    expect(isOneScreenRoute("/en/charting/study")).toBe(true);
    expect(isOneScreenRoute("/en/charting")).toBe(false);
  });

  it("targets are 44 px; Previous and Next sit at the bottom; no bulk action, no form panel", async () => {
    installEngine(makeChartingTable([makeRow(1), makeRow(2)]));
    await renderStudy("STU-001");
    const targets = Array.from(document.querySelectorAll<HTMLElement>("[data-charting-study] button, [data-charting-study] [data-value-input][type=text], [data-charting-study] [data-where-from], [data-charting-study] [data-back]"))
      .filter((el) => !el.closest("[data-hint]"));
    expect(targets.length).toBeGreaterThan(10);
    for (const el of targets) expect(el.className, el.outerHTML.slice(0, 80)).toMatch(/min-h-11|size-11/);
    const bottom = document.querySelector("[data-study-status]") as HTMLElement;
    expect(bottom.querySelector("[data-previous-study]")).toHaveTextContent("Previous study");
    expect(bottom.querySelector("[data-next-study]")).toHaveTextContent("Next study");
    expect(document.querySelector("[data-form-button], [data-form-panel], [data-select-all], [data-confirm-line] [data-bulk]")).toBeNull();
    // Attach exists on a phone too (question 6, closed as proposed).
    expect(document.querySelector("[data-attach]")).not.toBeNull();
  });
});
