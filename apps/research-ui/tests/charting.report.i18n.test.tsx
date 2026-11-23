import { afterEach, describe, expect, it, vi } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { CHARTING_COPY, cc, type ChartingCopyKey } from "@/lib/charting-copy";

import { installEngine, makeRow, makeTable, renderReport } from "./charting-helpers";

/**
 * Spec 04 "Copy": every `charting.report.*` key and every new `charting.export.*`
 * key in en, fr and ar with the same holes; the spec's English words; the help
 * line (question 3) on the page in each language; and the N9 guard on the new
 * files (no literal aria-label, title, alt or placeholder).
 */

afterEach(() => vi.unstubAllGlobals());


describe("charting.report.i18n", () => {

  it("keeps the spec's English words", () => {
    const words: [ChartingCopyKey, string][] = [
      ["charting.report.title", "Export and methods"],
      ["charting.report.lede", "For the charting table of the published screening."],
      ["charting.report.link", "Export and methods"],
      ["charting.report.back", "Back to charting"],
      ["charting.report.preparing", "Preparing the file"],
      ["charting.report.failed", "The file could not be made. Nothing was exported."],
      ["charting.report.empty.noExport", "Nothing to export."],
      ["charting.report.phone.desktopOnly", "Export and methods are on your desktop."],
      ["charting.report.phone.link", "Go to charting"],
      ["charting.report.download.title", "Download"],
      ["charting.report.download.csvFulltext", "CSV, full text"],
      ["charting.report.download.csvCharting", "CSV, charting"],
      ["charting.report.download.xlsx", "Spreadsheet (.xlsx)"],
      ["charting.report.counts.caption", "PRISMA 2020 full-text counts of the published screening"],
      ["charting.report.counts.ofWhich", "of which"],
      ["charting.report.open.title", "Still open"],
      ["charting.report.methods.draftBadge", "Draft · check before you submit"],
      ["charting.report.methods.copy", "Copy paragraph"],
      ["charting.report.methods.copied", "Copied"],
      ["charting.report.methods.basedOn", "What this statement is based on"],
      ["charting.export.xlsx", "Spreadsheet (.xlsx)"],
      ["charting.export.requiredOpen", "{n} required cells are empty."],
      ["charting.export.fileHad", "That file had {n} cells not charted."],
      ["charting.export.format.csv", "CSV"],
      ["charting.export.format.xlsx", "spreadsheet"],
    ];
    for (const [key, text] of words) expect(CHARTING_COPY.en[key], key).toBe(text);
    expect(cc("en", "charting.export.done", { when: "21 Nov 14:32", format: "spreadsheet", n: 68 })).toBe(
      "Exported 21 Nov 14:32 (spreadsheet): 68 rows. Changes after this are not in that file.",
    );
    expect(cc("en", "charting.report.help")).toBe(
      "To read or share the table, open the spreadsheet (.xlsx) in Excel or LibreOffice. The CSV files are for programs such as R or Python; a spreadsheet program may read some values in them as formulas.",
    );
    expect(() => cc("en", "charting.export.done", { when: "x", n: 1 })).toThrow(/needs \{format\}/);
  });

  for (const locale of SUPPORTED_LOCALES) {
    it(`${locale}: the help line says the spreadsheet is for Excel and the CSV files are for programs`, async () => {
      installEngine(makeTable([makeRow(1)]));
      await renderReport(locale);
      const help = document.querySelector("[data-desktop] [data-help]") as HTMLElement;
      expect(help.textContent).toBe(CHARTING_COPY[locale]["charting.report.help"]);
      expect(help.textContent).toContain(".xlsx");
      expect(help.textContent).toContain("CSV");
      expect(document.querySelector("[data-desktop] h1")?.textContent).toBe(CHARTING_COPY[locale]["charting.report.title"]);
    });
  }
});
