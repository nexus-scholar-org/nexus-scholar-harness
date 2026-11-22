import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningExport } from "@/components/screening-export";

import { flush, installEngine, makeRow, makeTable, renderCharting, renderReport } from "./charting-helpers";

/**
 * Spec 04 "Toolbar addition on /charting" and "Data out": the Export menu offers
 * the CSVs and "Spreadsheet (.xlsx)"; the link "Export and methods" sits beside
 * Export and on screening's export page; each download on the page asks the
 * route with its own format and view, and saves the file under the engine's name.
 */

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const fileButton = (kind: string) => document.querySelector(`[data-file="${kind}"]`) as HTMLButtonElement;

/** Count the files handed to the browser, by their download names. */
function savedFiles(): string[] {
  const saved: string[] = [];
  Object.assign(URL, { createObjectURL: vi.fn(() => "blob:x"), revokeObjectURL: vi.fn() });
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
    saved.push(this.download);
  });
  return saved;
}

describe("charting.report.export-menu", () => {
  it("/charting: the Export menu lists the two CSVs and the spreadsheet; the spreadsheet asks format=xlsx", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2)]));
    const saved = savedFiles();
    await renderCharting();
    fireEvent.click(document.querySelector("[data-export]") as HTMLElement);
    const menu = document.querySelector("[data-export-menu]") as HTMLElement;
    expect(within(menu).getAllByRole("button").map((b) => b.textContent)).toEqual(["CSV of the Full text view", "CSV of the Charting view", "Spreadsheet (.xlsx)"]);
    fireEvent.click(within(menu).getByRole("button", { name: "Spreadsheet (.xlsx)" }));
    await waitFor(() => expect(saved).toEqual(["charting-20261121T100000Z.xlsx"]));
    expect(engine.calls.some((c) => c.method === "GET" && c.path === "/api/v1/charting/export?format=xlsx")).toBe(true);
    // The persistent line follows the engine's record of the file.
    await waitFor(() => expect(desktop().querySelector("[data-last-export]")).toHaveTextContent(/\(spreadsheet\): 2 rows\./));
  });

  it("/charting: the link Export and methods sits right after the Export button", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderCharting("fr");
    const link = within(desktop()).getByRole("link", { name: "Export et méthodes" });
    expect(link).toHaveAttribute("href", "/fr/charting/report");
    const exportButton = desktop().querySelector("[data-export]") as HTMLElement;
    expect(exportButton.compareDocumentPosition(link) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(exportButton.closest("span")?.nextElementSibling).toBe(link);
  });

  it("/charting/report: each download asks its own format and view and saves the engine's file", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2)]));
    const saved = savedFiles();
    await renderReport();
    fireEvent.click(fileButton("fulltext"));
    await waitFor(() => expect(saved).toHaveLength(1));
    await waitFor(() => expect(fileButton("charting")).toBeEnabled());
    fireEvent.click(fileButton("charting"));
    await waitFor(() => expect(saved).toHaveLength(2));
    await waitFor(() => expect(fileButton("xlsx")).toBeEnabled());
    fireEvent.click(fileButton("xlsx"));
    await waitFor(() => expect(saved).toHaveLength(3));
    expect(saved).toEqual(["charting-fulltext-20261121T100000Z.csv", "charting-charting-20261121T100000Z.csv", "charting-20261121T100000Z.xlsx"]);
    expect(engine.calls.filter((c) => c.path.startsWith("/api/v1/charting/export")).map((c) => c.path)).toEqual([
      "/api/v1/charting/export?format=csv&view=fulltext",
      "/api/v1/charting/export?format=csv&view=charting",
      "/api/v1/charting/export?format=xlsx",
    ]);
    expect(engine.calls.every((c) => c.method === "GET")).toBe(true);
  });

  it("/charting/report: a download in flight reads Preparing the file, is busy, and holds the other two", async () => {
    let release: () => void = () => undefined;
    installEngine(makeTable([makeRow(1)]), { exportHold: new Promise<void>((resolve) => (release = resolve)) });
    savedFiles();
    await renderReport();
    fireEvent.click(fileButton("xlsx"));
    await flush();
    expect(fileButton("xlsx")).toHaveTextContent("Preparing the file");
    expect(fileButton("xlsx")).toHaveAttribute("aria-busy", "true");
    expect(fileButton("fulltext")).toBeDisabled();
    expect(fileButton("charting")).toBeDisabled();
    expect(document.querySelector("[data-desktop] [data-announce]")).toHaveTextContent("Preparing the file");
    await act(async () => release());
    await waitFor(() => expect(fileButton("xlsx")).toHaveTextContent("Spreadsheet (.xlsx)"));
    expect(fileButton("xlsx")).toHaveAttribute("aria-busy", "false");
    // The browser announces its own download: the page says nothing more.
    expect(document.querySelector("[data-desktop] [data-announce]")?.textContent).toBe("");
  });

  it("screening's export page links to the charting table's Export and methods", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string) => {
        const path = new URL(String(input), "http://localhost").pathname.replace("/api/console", "");
        const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
        if (path === "/api/v1/ui/publication-status") {
          return json({ shape: "ui07.publication-status-v1", status: "CURRENT", code: null, generation_id: "GEN-1", outputs: {}, message: "", details: {} });
        }
        if (path === "/api/v1/screening/methods") {
          return json({
            generation_id: "GEN-1",
            generation_fingerprint: "sha256:feedface",
            published_at: "2026-11-05T10:00:00Z",
            language: "en",
            paragraph: "30 records were identified.",
            figures: { identified: 30, duplicates_removed: 0, screened: 30, excluded: 20, unclear: 4, included: 6, exclusion_reasons: {} },
            sources: [],
            caveats: [],
            not_stated: [],
          });
        }
        return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
      }),
    );
    render(<ScreeningExport locale="en" />);
    const link = await screen.findByRole("link", { name: "Export and methods" });
    expect(link).toHaveAttribute("href", "/en/charting/report");
    expect(screen.getByRole("link", { name: "Chart the included studies" })).toHaveAttribute("href", "/en/charting");
  });
});
