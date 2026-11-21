import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartingPage } from "@/components/charting-page";
import { SUPPORTED_LOCALES } from "@/i18n";
import { CHARTING_COPY, CHARTING_REFUSAL_CODES, refusalWords, type ChartingCopyKey } from "@/lib/charting-copy";

import { flush, installEngine, makeRow, makeTable, postedEvents, press, renderCharting } from "./charting-helpers";

/** Spec 01 "States" (M12a Part A, Full text view): each state renders with its words; every refusal code has its own. */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-study-row="${id}"]`) as HTMLElement;
const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;

describe("charting.states", () => {
  it("default: the heading, the counts line with its charted part, the toolbar and the columns", async () => {
    const rows = [makeRow(1, { fulltext: { ...makeRow(1).fulltext, status: "retrieved" } }), makeRow(2), makeRow(3, { ft_decision: { outcome: "INCLUDE" } })];
    installEngine(makeTable(rows));
    await renderCharting();
    expect(screen.getByRole("heading", { level: 1, name: "Charting" })).toBeInTheDocument();
    const line = document.querySelector("[data-counts]")!.textContent;
    expect(line).toBe("3 kept · 1 retrieved · 0 not retrieved · 2 to get · 1 included at full text · 0 excluded · 0 charted");
    const grid = within(desktop()).getByRole("grid", { name: "Kept studies, full text" });
    expect(grid).toHaveAttribute("aria-rowcount", "4");
    expect(within(grid).getAllByRole("columnheader").map((h) => h.textContent)).toEqual(["", "Study", "Round", "Full text", "File", "Decision"]);
    const select = within(desktop()).getByRole("combobox", { name: "Show" });
    expect(within(select).getAllByRole("option").map((o) => o.textContent)).toEqual([
      "All", "To get", "Requested", "Not retrieved", "To decide at full text", "Included at full text", "Excluded at full text", "Not charted", "Pilot",
    ]);
    expect(within(desktop()).getByRole("checkbox", { name: "Show excluded" })).not.toBeChecked();
    expect(within(desktop()).getByRole("button", { name: "Export" })).toBeEnabled();
    // Part B: the two views as a radio group, the Full text view chosen.
    const views = within(desktop()).getByRole("radiogroup", { name: "View" });
    expect(within(views).getByRole("radio", { name: /Full text/ })).toBeChecked();
    expect(within(views).getByRole("radio", { name: /Charting/ })).not.toBeChecked();
    // DOIs are left to right.
    expect(within(rowOf("STU-001")).getByText("10.3390/rs1001")).toHaveAttribute("dir", "ltr");
    expect(within(rowOf("STU-001")).getByText("Databases")).toBeInTheDocument();
  });

  it("not published: the reason, Go to Publish, and the code in Details", async () => {
    installEngine(makeTable([]), { fail: { status: 409, code: "SCREENING_NOT_PUBLISHED" } });
    await renderCharting();
    expect(screen.getByText("Screening is not published yet. The charting table lists the studies you kept, so publish first.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Publish" })).toHaveAttribute("href", "/en/screening/publish");
    expect(screen.getByText("SCREENING_NOT_PUBLISHED")).toHaveAttribute("dir", "ltr");
    expect(screen.queryByRole("grid")).toBeNull();
  });

  it("nothing kept: the sentence and a link to triage", async () => {
    installEngine(makeTable([]));
    await renderCharting();
    expect(screen.getByText("Nothing was kept at title and abstract, so there is nothing to chart.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to triage" })).toHaveAttribute("href", "/en/screening/triage");
  });

  it("loading: the counts line and eight rows as skeletons, the toolbar off, no count before the answer", async () => {
    let release: () => void = () => undefined;
    installEngine(makeTable([makeRow(1)]), { hold: new Promise<void>((resolve) => (release = resolve)) });
    render(<ChartingPage locale="en" />);
    await flush();
    expect(document.querySelector("[data-skeleton=counts]")).not.toBeNull();
    expect(document.querySelectorAll("[data-skeleton=row]")).toHaveLength(8);
    expect(within(desktop()).getByRole("grid")).toHaveAttribute("aria-busy", "true");
    expect(within(desktop()).getByRole("combobox", { name: "Show" })).toBeDisabled();
    expect(within(desktop()).getByRole("button", { name: /Export/ })).toBeDisabled();
    expect(document.querySelector("[data-counts]")).toBeNull();
    await act(async () => release());
    await flush();
    expect(document.querySelector("[data-counts]")).not.toBeNull();
  });

  it("a refused change: its words with role alert, the code in Details, the row keeps its saved value and the focus", async () => {
    installEngine(makeTable([makeRow(1)]), { refuse: { "STU-001": "RECORD_NOT_KEPT" } });
    await renderCharting();
    rowOf("STU-001").focus();
    await press("r");
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("That study is not in the kept set any more. Reload the table.");
    expect(within(alert).getByText("RECORD_NOT_KEPT")).toHaveAttribute("dir", "ltr");
    expect(within(rowOf("STU-001")).getByText("To get")).toBeInTheDocument();
    expect(document.activeElement).toBe(rowOf("STU-001"));
  });

  it("an attachment that is not a PDF is refused with its words", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    engine.fail = { status: 422, code: "ATTACHMENT_NOT_PDF" };
    rowOf("STU-001").focus();
    await press("p");
    fireEvent.change(document.querySelector("[data-file-input]")!, { target: { files: [new File(["<html>"], "a.pdf")] } });
    await flush();
    expect(screen.getByRole("alert")).toHaveTextContent("Only a PDF can be attached. Paste a link instead.");
  });

  it("offline: the saved-at line, and new changes refused here without a request", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    rowOf("STU-001").focus();
    await press("r");
    engine.fail = "unreachable";
    await press("q");
    const banner = document.querySelector("[data-banner=offline]")!;
    expect(banner).toHaveAttribute("role", "alert");
    expect(banner.textContent).toMatch(/^The console is not answering\. Nothing is lost; last change saved at \d\d:\d\d\./);
    const before = engine.calls.length;
    await press("g");
    expect(engine.calls.length).toBe(before);
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("The console is not answering, so the change was not sent.");
    expect(within(desktop()).getByRole("button", { name: /Export/ })).toBeDisabled();
    engine.fail = undefined;
    fireEvent.click(within(banner as HTMLElement).getByRole("button", { name: "Try again" }));
    await flush();
    await flush();
    expect(document.querySelector("[data-banner=offline]")).toBeNull();
  });

  it("offline at the first read: the sentence and Try again", async () => {
    installEngine(makeTable([makeRow(1)]), { fail: "unreachable" });
    await renderCharting();
    expect(screen.getByRole("alert")).toHaveTextContent("The console is not answering. Nothing is lost.");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("read-only: the archived banner, no change control, keys send nothing, Export still works", async () => {
    const engine = installEngine(makeTable([makeRow(1)], { read_only: true, read_only_code: "CHARTING_PROTOCOL_REPLACED" }));
    await renderCharting();
    const banner = document.querySelector("[data-banner=archived]")!;
    expect(banner).toHaveTextContent("This table belongs to the old protocol. It is kept, read-only, with that protocol.");
    expect(within(banner as HTMLElement).getByText("CHARTING_PROTOCOL_REPLACED")).toBeInTheDocument();
    expect(within(rowOf("STU-001")).queryByRole("button", { name: /Attach|Include|Exclude|Paste/ })).toBeNull();
    rowOf("STU-001").focus();
    for (const key of ["r", "i", "e", "p"]) await press(key);
    expect(postedEvents(engine)).toHaveLength(0);
    fireEvent.click(within(desktop()).getByRole("button", { name: "Export" }));
    fireEvent.click(within(desktop()).getByRole("button", { name: "CSV of the Full text view" }));
    await flush();
    expect(engine.calls.some((c) => c.path.startsWith("/api/v1/charting/export"))).toBe(true);
  });

  it("stale and chasing banners carry their words; the stale one links to Publish with its code", async () => {
    installEngine(makeTable([makeRow(1)], { stale: true, chasing_pending: true }));
    await renderCharting();
    const stale = document.querySelector("[data-banner=stale]") as HTMLElement;
    expect(stale).toHaveTextContent("Decisions changed after publishing. This table follows the published screening.");
    expect(within(stale).getByRole("link", { name: "Go to Publish" })).toHaveAttribute("href", "/en/screening/publish");
    expect(within(stale).getByText("GENERATION_STALE")).toBeInTheDocument();
    expect(document.querySelector("[data-banner=chasing]")).toHaveTextContent(
      "A citation-chasing round is being screened. Its studies appear here when it is published.",
    );
  });

  it("the filters show what they name; excluded rows only with Show excluded", async () => {
    const ft = makeRow(0).fulltext;
    const rows = [
      makeRow(1),
      makeRow(2, { fulltext: { ...ft, status: "requested" } }),
      makeRow(3, { fulltext: { ...ft, status: "not_retrieved", reason: "no_access" } }),
      makeRow(4, { ft_decision: { outcome: "INCLUDE" } }),
      makeRow(5, { ft_decision: { outcome: "EXCLUDE", reason_code: "EXC-01" } }),
    ];
    installEngine(makeTable(rows));
    await renderCharting();
    const ids = () => Array.from(desktop().querySelectorAll("[data-study-row]")).map((r) => r.getAttribute("data-study-row"));
    expect(ids()).toEqual(["STU-001", "STU-002", "STU-003", "STU-004"]);
    const select = within(desktop()).getByRole("combobox", { name: "Show" });
    const pick = async (value: string) => {
      fireEvent.change(select, { target: { value } });
      await flush();
    };
    await pick("toGet");
    expect(ids()).toEqual(["STU-001", "STU-004"]);
    await pick("requested");
    expect(ids()).toEqual(["STU-002"]);
    await pick("notRetrieved");
    expect(ids()).toEqual(["STU-003"]);
    expect(within(rowOf("STU-003")).getByText("No access or paywalled")).toBeInTheDocument();
    await pick("toDecide");
    expect(ids()).toEqual(["STU-001", "STU-002", "STU-003"]);
    await pick("included");
    expect(ids()).toEqual(["STU-004"]);
    await pick("excluded");
    expect(ids()).toEqual(["STU-005"]);
    expect(within(rowOf("STU-005")).getByText("Not a crop field")).toBeInTheDocument();
    await pick("all");
    fireEvent.click(within(desktop()).getByRole("checkbox", { name: "Show excluded" }));
    await flush();
    expect(ids()).toContain("STU-005");
  });

  it("with several rows selected a decision key says to decide one study at a time", async () => {
    const engine = installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    rowOf("STU-001").focus();
    await press("a");
    await press("i");
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("Decide at full text one study at a time.");
    await press("e");
    expect(postedEvents(engine)).toHaveLength(0);
    expect(document.querySelector("[data-chip]")).toBeNull();
  });

  it("a pasted link is saved as text and opens from the File column", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    fireEvent.click(within(rowOf("STU-001")).getByRole("button", { name: "Paste a link" }));
    const input = within(rowOf("STU-001")).getByRole("textbox", { name: "Link to the full text" });
    expect(input).toHaveAttribute("dir", "ltr");
    fireEvent.change(input, { target: { value: "https://www.mdpi.com/2072-4292/10/9/1423" } });
    fireEvent.click(within(rowOf("STU-001")).getByRole("button", { name: "Save the link" }));
    await flush();
    const post = engine.calls.find((c) => c.method === "POST" && c.path === "/api/v1/charting/records/STU-001/attachment")!;
    expect(post.body).toMatchObject({ link: "https://www.mdpi.com/2072-4292/10/9/1423" });
    expect(within(rowOf("STU-001")).getByRole("link", { name: "Open the link" })).toHaveAttribute("href", "https://www.mdpi.com/2072-4292/10/9/1423");
    // A link is not a retrieved full text.
    expect(within(rowOf("STU-001")).getByText("To get")).toBeInTheDocument();
  });

  it("every refusal code maps to its own key in en, fr and ar", () => {
    for (const code of CHARTING_REFUSAL_CODES) {
      const key = `charting.refusal.${code}` as ChartingCopyKey;
      for (const locale of SUPPORTED_LOCALES) {
        expect(CHARTING_COPY[locale][key], `${locale} ${code}`).toBeTruthy();
        expect(refusalWords(locale, code)).toBe(CHARTING_COPY[locale][key]);
      }
    }
    expect(refusalWords("en", "SOMETHING_NEW")).toBe("The console refused the change.");
    expect(CHARTING_COPY.en["charting.refusal.FULLTEXT_REASON_REQUIRED"]).toBe("Choose one reason first.");
  });
});
