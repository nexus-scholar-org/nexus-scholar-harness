import { screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CHASING, DATABASES, TOTAL, installEngine, makeMethods, makeRow, makeTable, prismaGroup, renderReport } from "./charting-helpers";

/**
 * Spec 04 "PRISMA counts table" and "Still open": three columns, reason rows as
 * indented real rows that say "of which", the open counts apart and not summed,
 * zeros written "0", and every number the engine's.
 */

afterEach(() => vi.unstubAllGlobals());

const prisma = () => screen.getByRole("table", { name: "PRISMA 2020 full-text counts of the published screening" });
const row = (key: string) => document.querySelector(`[data-count-row="${key}"]`) as HTMLTableRowElement;
const cells = (key: string) => [...row(key).querySelectorAll("td")].map((c) => c.textContent);
const header = (key: string) => row(key).querySelector("th") as HTMLElement;

describe("charting.report.counts", () => {
  it("has the three columns, a caption, and the rows in PRISMA order", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport();
    const table = prisma();
    expect(within(table).getAllByRole("columnheader").map((h) => h.textContent)).toEqual(["Count (reports)", "Databases", "Citation chasing", "Total"]);
    for (const h of within(table).getAllByRole("columnheader")) expect(h).toHaveAttribute("scope", "col");
    const order = [...table.querySelectorAll("tbody tr")].map((r) => r.getAttribute("data-count-row"));
    expect(order).toEqual([
      "sought",
      "not_retrieved",
      "not_retrieved:No access or paywalled",
      "not_retrieved:Not found",
      "not_retrieved:Authors did not reply",
      "not_retrieved:Other",
      "assessed",
      "excluded",
      "excluded:EXC-01",
      "excluded:FAILS-INC-01",
      "excluded:OTHER",
      "included",
    ]);
    for (const r of table.querySelectorAll("tbody tr")) expect(r.querySelector("th")).toHaveAttribute("scope", "row");
    expect(header("sought")).toHaveTextContent("Reports sought for retrieval");
    expect(header("not_retrieved")).toHaveTextContent("Reports not retrieved");
    expect(header("assessed")).toHaveTextContent("Reports assessed for eligibility");
    expect(header("excluded")).toHaveTextContent("Reports excluded");
    expect(header("included")).toHaveTextContent("Reports included");
  });

  it("writes every number from the engine's answer, not from the rows the page holds", async () => {
    // The table answer holds one row; the counts are the methods block's 12, 5 and 17.
    installEngine(makeTable([makeRow(1)]));
    await renderReport();
    expect(cells("sought")).toEqual([String(DATABASES.sought), String(CHASING.sought), String(TOTAL.sought)]);
    expect(cells("not_retrieved")).toEqual(["2", "1", "3"]);
    expect(cells("assessed")).toEqual(["9", "3", "12"]);
    expect(cells("excluded")).toEqual(["3", "1", "4"]);
    expect(cells("included")).toEqual(["6", "2", "8"]);
    expect(cells("not_retrieved:No access or paywalled")).toEqual(["1", "0", "1"]);
    expect(cells("not_retrieved:Authors did not reply")).toEqual(["0", "1", "1"]);
    expect(cells("excluded:EXC-01")).toEqual(["2", "0", "2"]);
    expect(cells("excluded:FAILS-INC-01")).toEqual(["0", "1", "1"]);
  });

  it("makes reason rows indented real rows that say of which, with the protocol's label beside the code", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport();
    for (const key of ["not_retrieved:No access or paywalled", "not_retrieved:Not found", "not_retrieved:Authors did not reply", "not_retrieved:Other", "excluded:EXC-01", "excluded:OTHER"]) {
      expect(header(key).className, key).toMatch(/\bps-6\b/);
      expect(header(key).textContent, key).toMatch(/^of which /);
    }
    expect(header("sought").className).not.toMatch(/\bps-6\b/);
    expect(header("not_retrieved:No access or paywalled")).toHaveTextContent("of which No access or paywalled");
    expect(header("not_retrieved:Other")).toHaveTextContent("of which Other");
    expect(header("excluded:EXC-01")).toHaveTextContent("of which EXC-01 Not a crop field");
    expect(within(header("excluded:EXC-01")).getByText("EXC-01")).toHaveAttribute("dir", "ltr");
    expect(within(prisma()).getByRole("row", { name: "of which Not found 1 0 1" })).toBeInTheDocument();
  });

  it("keeps the open counts apart, under their own heading and note, and out of the PRISMA table", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport();
    const region = document.querySelector("[data-open-region]") as HTMLElement;
    expect(within(region).getByRole("heading", { level: 2, name: "Still open" })).toBeInTheDocument();
    expect(region).toHaveTextContent("Not PRISMA counts: what is not finished yet.");
    const open = [...region.querySelectorAll("[data-open-row]")].map((r) => [r.querySelector("dt")!.textContent, r.querySelector("dd")!.textContent]);
    expect(open).toEqual([
      ["Awaiting retrieval", "2"],
      ["Fetched, waiting for you to confirm", "1"],
      ["Retrieved, not yet assessed", "0"],
      ["Assessed without a full text", "1"],
    ]);
    expect(prisma().contains(region)).toBe(false);
    expect(within(prisma()).queryByText("Awaiting retrieval")).toBeNull();
    // Not summed: the table's rows are the PRISMA counts only.
    expect(cells("sought")[2]).toBe("17");
  });

  it("marks a non-zero waiting row with the unclear role in words and an icon, and only that row", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport();
    const waiting = document.querySelector('[data-open-row="to_confirm"]') as HTMLElement;
    expect(waiting).toHaveAttribute("data-role", "unclear");
    expect(waiting.querySelector("svg[data-icon]")).not.toBeNull();
    expect(document.querySelector('[data-open-row="awaiting_retrieval"]')).not.toHaveAttribute("data-role");
  });

  it("writes zeros as 0 and keeps the Citation chasing column when there is no such round", async () => {
    const databases = prismaGroup({ sought: 3, assessed: 1, included: 1 });
    installEngine(makeTable([makeRow(1)]), { methods: makeMethods({ databases, chasing: prismaGroup(), total: databases }) });
    await renderReport();
    expect(within(prisma()).getByRole("columnheader", { name: "Citation chasing" })).toBeInTheDocument();
    expect(cells("sought")).toEqual(["3", "0", "3"]);
    expect(cells("not_retrieved")).toEqual(["0", "0", "0"]);
    expect(cells("not_retrieved:Not found")).toEqual(["0", "0", "0"]);
    for (const cell of prisma().querySelectorAll("td")) expect(cell.textContent).toMatch(/^\d+$/);
    // No exclusion reason recorded: no indented exclusion row.
    expect(prisma().querySelector('[data-count-row^="excluded:"]')).toBeNull();
    expect(document.querySelector('[data-open-row="to_confirm"]')).not.toHaveAttribute("data-role");
  });

  it("uses Latin numerals and the same rows on an Arabic page", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport("ar");
    const table = screen.getByRole("table", { name: "أعداد PRISMA 2020 للنص الكامل للفرز المنشور" });
    expect(within(table).getAllByRole("columnheader").map((h) => h.textContent)).toEqual(["العدد (تقارير)", "قواعد البيانات", "تتبّع الاستشهادات", "المجموع"]);
    expect(cells("sought")).toEqual(["12", "5", "17"]);
    expect(header("not_retrieved:Not found").textContent).toMatch(/^منها /);
  });
});
