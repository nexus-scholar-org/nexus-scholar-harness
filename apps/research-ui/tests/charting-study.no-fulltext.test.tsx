import { within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { flush, installEngine, makeChartingTable, makeRow, press, renderStudy } from "./charting-helpers";

/**
 * Spec 02 "Partial", no full text (M12a Part B, decision item 8): charting is
 * allowed without a retrieved full text; the form shows the mark on top and says
 * the row is counted as having no full text; a retrieved study shows neither.
 */

afterEach(() => vi.unstubAllGlobals());

describe("charting-study.no-fulltext", () => {
  it("without a retrieved full text: the mark, the sentence, and the fields open", async () => {
    installEngine(makeChartingTable([makeRow(1, { abstract: "Weeds mapped from UAV images." })]));
    await renderStudy("STU-001");
    const line = document.querySelector("[data-from-abstract]") as HTMLElement;
    expect(line).toHaveTextContent("Charting from the abstract. This row is counted as having no full text.");
    const mark = line.querySelector("[data-mark=no-full-text]")!;
    expect(mark).toHaveTextContent("No full text");
    expect(mark.querySelector("svg[data-icon]")).not.toBeNull();
    expect((document.querySelector('[data-field="cameras"] [data-value-input]') as HTMLInputElement).disabled).toBe(false);
    // The full-text part says the same, with words and an icon.
    expect(within(document.querySelector("[data-file-line]") as HTMLElement).getByText("No full text")).toBeInTheDocument();
  });

  it("R (Retrieved) takes the mark away; a retrieved study has neither mark nor sentence", async () => {
    installEngine(makeChartingTable([makeRow(1)]));
    await renderStudy("STU-001");
    (document.querySelector("[data-region=study]") as HTMLElement).focus();
    await press("r");
    await flush();
    expect(document.querySelector("[data-from-abstract]")).toBeNull();
    expect(document.querySelector('[data-status="retrieved"]')).toHaveAttribute("aria-checked", "true");
  });
});
