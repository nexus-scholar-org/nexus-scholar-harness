import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { CHARTING_COPY, refusalWords } from "@/lib/charting-copy";

import { PARAGRAPH, flush, installEngine, makeMethods, makeRow, makeTable, prismaGroup, renderReport } from "./charting-helpers";

/**
 * Spec 04 "States" (M12a Part C, `/charting/report`): each state renders with its
 * words, and every refusal the page can show maps to words of its own.
 */

afterEach(() => vi.unstubAllGlobals());

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const fileButton = (kind: string) => document.querySelector(`[data-file="${kind}"]`) as HTMLButtonElement;
const rows = () => [makeRow(1), makeRow(2, { ft_decision: { outcome: "INCLUDE" } })];

describe("charting.report.states", () => {
  it("default: the heading, the three downloads, the help line, the counts, the draft paragraph and the way back", async () => {
    installEngine(makeTable(rows()));
    await renderReport();
    const page = within(desktop());
    expect(page.getByRole("heading", { level: 1, name: "Export and methods" })).toBeInTheDocument();
    expect(page.getByText("For the charting table of the published screening.")).toBeInTheDocument();
    expect(page.getByRole("heading", { level: 2, name: "Download" })).toBeInTheDocument();
    for (const name of ["CSV, full text", "CSV, charting", "Spreadsheet (.xlsx)"]) expect(page.getByRole("button", { name })).toBeEnabled();
    expect(page.getByRole("button", { name: "Spreadsheet (.xlsx)" })).toHaveAccessibleDescription("Charting, Full text, PRISMA counts, Charting form, About and Methods, in one file.");
    expect(document.querySelector("[data-help]")).toHaveTextContent(
      "To read or share the table, open the spreadsheet (.xlsx) in Excel or LibreOffice. The CSV files are for programs such as R or Python; a spreadsheet program may read some values in them as formulas.",
    );
    expect(page.getByRole("table", { name: "PRISMA 2020 full-text counts of the published screening" })).toBeInTheDocument();
    expect(page.getByRole("heading", { level: 2, name: "Still open" })).toBeInTheDocument();
    expect(page.getByRole("heading", { level: 2, name: "Methods paragraph" })).toBeInTheDocument();
    expect(page.getByText("Draft · check before you submit")).toBeInTheDocument();
    expect(document.querySelector("[data-paragraph]")).toHaveTextContent(PARAGRAPH);
    expect(page.getByRole("link", { name: "Back to charting" })).toHaveAttribute("href", "/en/charting");
    // The page has no brand button outside the not-published state.
    expect(desktop().querySelectorAll('[data-variant="primary"]')).toHaveLength(0);
    expect(document.querySelector("[data-no-decisions]")).toBeNull();
  });

  it("nothing assessed yet: the counts with zeros, the engine's first sentence, the line, the downloads on", async () => {
    const first = "Of 4 reports sought for retrieval, none were not retrieved. No report has been assessed at full text yet.";
    installEngine(makeTable(rows()), {
      methods: makeMethods({
        databases: prismaGroup({ sought: 4, awaiting_retrieval: 4 }),
        chasing: prismaGroup(),
        total: prismaGroup({ sought: 4, awaiting_retrieval: 4 }),
        methods: { paragraph: first, sentences: [first], caveats: [], not_stated: [] },
      }),
    });
    await renderReport();
    expect(document.querySelector("[data-paragraph]")).toHaveTextContent(first);
    expect(screen.getByText("No full-text decision is recorded yet. The counts fill in as you decide.")).toBeInTheDocument();
    const assessed = document.querySelector('[data-count-row="assessed"]') as HTMLElement;
    expect([...assessed.querySelectorAll("td")].map((c) => c.textContent)).toEqual(["0", "0", "0"]);
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeEnabled();
  });

  it("not published: no region, the sentence, Go to Publish as the one brand button, the code in Details", async () => {
    const engine = installEngine(makeTable([]), { fail: { status: 409, code: "SCREENING_NOT_PUBLISHED" } });
    await renderReport();
    expect(screen.getByText("Screening is not published yet. The charting table lists the studies you kept, so publish first.")).toBeInTheDocument();
    const publish = screen.getByRole("link", { name: "Go to Publish" });
    expect(publish).toHaveAttribute("href", "/en/screening/publish");
    expect(publish).toHaveAttribute("data-variant", "primary");
    expect(screen.getByText("SCREENING_NOT_PUBLISHED")).toHaveAttribute("dir", "ltr");
    expect(document.querySelector("[data-file]")).toBeNull();
    expect(document.querySelector("[data-paragraph]")).toBeNull();
    expect(screen.queryByRole("table")).toBeNull();
    // The methods block is not asked for once the table refused.
    expect(engine.calls.some((c) => c.path === "/api/v1/charting/methods")).toBe(false);
  });

  it("nothing kept: the sentence, the link to triage, and the downloads off with their words", async () => {
    installEngine(makeTable([]), { methods: makeMethods({ databases: prismaGroup(), chasing: prismaGroup(), total: prismaGroup() }) });
    await renderReport();
    expect(screen.getByText("Nothing was kept at title and abstract, so there is nothing to chart.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to triage" })).toHaveAttribute("href", "/en/screening/triage");
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeDisabled();
    expect(document.querySelector("[data-no-export]")).toHaveTextContent("Nothing to export.");
  });

  it("loading: three region skeletons, the downloads off, no count before the methods answer", async () => {
    let release: () => void = () => undefined;
    installEngine(makeTable(rows()), { hold: new Promise<void>((resolve) => (release = resolve)) });
    await renderReport("en", { settle: false });
    expect(document.querySelector('[data-state="loading"]')).not.toBeNull();
    expect(document.querySelector("[data-skeleton=counts]")).not.toBeNull();
    expect(document.querySelector("[data-skeleton=methods]")).not.toBeNull();
    expect(document.querySelector("[data-skeleton=last-export]")).not.toBeNull();
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeDisabled();
    expect(document.querySelector("[data-prisma]")).toBeNull();
    expect(document.querySelector("[data-paragraph]")).toBeNull();
    await act(async () => release());
    await waitFor(() => expect(document.querySelector("[data-prisma]")).not.toBeNull());
    expect(document.querySelector("[data-skeleton=counts]")).toBeNull();
  });

  it("offline at the first read: the sentence with role alert, its code in Details, and Try again", async () => {
    installEngine(makeTable(rows()), { fail: "unreachable" });
    await renderReport();
    const alert = within(desktop()).getByRole("alert");
    expect(alert).toHaveTextContent("The console is not answering. Nothing is lost.");
    expect(within(alert).getByText("ENGINE_UNREACHABLE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("offline later: the counts and the paragraph stay with an as-of caption; the downloads are off; Copy still works", async () => {
    const engine = installEngine(makeTable(rows()));
    await renderReport();
    engine.fail = "unreachable";
    fireEvent.click(fileButton("xlsx"));
    await waitFor(() => expect(document.querySelector('[data-banner="offline"]')).not.toBeNull());
    const banner = document.querySelector('[data-banner="offline"]') as HTMLElement;
    expect(banner).toHaveAttribute("role", "alert");
    expect(banner).toHaveTextContent("The console is not answering. Nothing is lost.");
    expect(banner.querySelector("[data-as-of]")?.textContent).toMatch(/^As of \d{4}-\d{2}-\d{2} \d{2}:\d{2}$/);
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeDisabled();
    expect(document.querySelector("[data-downloads-offline]")).toHaveTextContent("The console is not answering. Nothing is lost.");
    expect(document.querySelector("[data-paragraph]")).toHaveTextContent(PARAGRAPH);
    expect(document.querySelector("[data-prisma]")).not.toBeNull();
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    fireEvent.click(screen.getByRole("button", { name: "Copy paragraph" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(PARAGRAPH));
  });

  it("stale: the line of the table, GENERATION_STALE in Details, nothing disabled", async () => {
    installEngine(makeTable(rows(), { stale: true }));
    await renderReport();
    const stale = document.querySelector('[data-banner="stale"]') as HTMLElement;
    expect(stale).toHaveTextContent("Decisions changed after publishing. This table follows the published screening.");
    expect(within(stale).getByText("GENERATION_STALE")).toBeInTheDocument();
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeEnabled();
  });

  it("published again: the line of the table with the way back to it", async () => {
    installEngine(makeTable(rows(), { changes: { published_at: "2026-11-21T10:00:00Z", added: 3, no_longer_kept: 2 } }));
    await renderReport();
    const line = document.querySelector('[data-banner="changes"]') as HTMLElement;
    expect(line).toHaveTextContent("Screening was published again on 2026-11-21. 3 records were added, 2 are no longer kept.");
    expect(within(line).getByRole("link", { name: "Back to charting" })).toHaveAttribute("href", "/en/charting");
  });

  it("archived: the old-protocol line with its code in Details; downloads, counts and Copy stay available", async () => {
    installEngine(makeTable(rows(), { read_only: true, read_only_code: "CHARTING_PROTOCOL_REPLACED" }));
    await renderReport();
    const archived = document.querySelector('[data-banner="archived"]') as HTMLElement;
    expect(archived).toHaveTextContent("This table belongs to the old protocol. It is kept, read-only, with that protocol.");
    expect(within(archived).getByText("CHARTING_PROTOCOL_REPLACED")).toBeInTheDocument();
    for (const kind of ["fulltext", "charting", "xlsx"]) expect(fileButton(kind)).toBeEnabled();
    expect(document.querySelector("[data-prisma]")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Copy paragraph" })).toBeEnabled();
  });

  it("a citation-chasing round being screened: the line above the counts", async () => {
    installEngine(makeTable(rows(), { chasing_pending: true }));
    await renderReport();
    const region = document.querySelector("[data-counts-region]") as HTMLElement;
    expect(within(region).getByText("A citation-chasing round is being screened. Its studies appear here when it is published.")).toBeInTheDocument();
  });

  it("a refused read: the words with role alert, the code in Details", async () => {
    installEngine(makeTable(rows()), { methodsFail: { status: 422, code: "BODY_INVALID" } });
    await renderReport();
    const alert = within(desktop()).getByRole("alert");
    expect(alert).toHaveTextContent(CHARTING_COPY.en["charting.refusal.BODY_INVALID"]);
    expect(within(alert).getByText("BODY_INVALID")).toHaveAttribute("dir", "ltr");
  });

  it("a host or token guard: a refused request with its code; a phone token: the desktop line", async () => {
    installEngine(makeTable(rows()), { fail: { status: 403, code: "HOST_REFUSED" } });
    const first = await renderReport();
    expect(within(desktop()).getByRole("alert")).toHaveTextContent("The console refused this request. Nothing was changed.");
    expect(screen.getByText("HOST_REFUSED")).toBeInTheDocument();
    first.unmount();
    vi.unstubAllGlobals();
    installEngine(makeTable(rows()), { fail: { status: 403, code: "TOKEN_SCOPE_REFUSED" } });
    await renderReport();
    expect(within(desktop()).getByRole("alert")).toHaveTextContent("Export and methods are on your desktop.");
  });

  it("a file that could not be made: the page stays, the sentence, the code's words and the code in Details", async () => {
    installEngine(makeTable(rows()), { exportFail: { status: 422, code: "CHARTING_EXPORT_FORMAT_INVALID" } });
    await renderReport();
    fireEvent.click(fileButton("fulltext"));
    await waitFor(() => expect(document.querySelector("[data-file-failed]")).not.toBeNull());
    const failed = document.querySelector("[data-file-failed]") as HTMLElement;
    expect(failed).toHaveAttribute("role", "alert");
    expect(failed).toHaveTextContent("The file could not be made. Nothing was exported.");
    expect(failed).toHaveTextContent(CHARTING_COPY.en["charting.refusal.CHARTING_EXPORT_FORMAT_INVALID"]);
    expect(within(failed).getByText("CHARTING_EXPORT_FORMAT_INVALID")).toBeInTheDocument();
    expect(document.querySelector("[data-paragraph]")).toHaveTextContent(PARAGRAPH);
    expect(document.querySelector("[data-last-export]")).toBeNull();
    await flush();
    expect(fileButton("fulltext")).toBeEnabled();
  });

  it("every refusal this page can show has words of its own in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const unknown = CHARTING_COPY[locale]["charting.refusal.unknown"];
      for (const code of ["SCREENING_NOT_PUBLISHED", "CHARTING_EXPORT_FORMAT_INVALID", "CHARTING_PROTOCOL_REPLACED", "GENERATION_STALE", "BODY_INVALID"]) {
        expect(refusalWords(locale, code), `${locale} ${code}`).not.toBe(unknown);
      }
      for (const key of ["charting.report.failed", "charting.report.refused", "charting.offlineNoChange", "charting.report.phone.desktopOnly"] as const) {
        expect(CHARTING_COPY[locale][key].trim(), `${locale} ${key}`).not.toBe("");
      }
    }
  });
});
