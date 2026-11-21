import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartingStudyPage } from "@/components/charting-study";

import { cellEvents, flush, installEngine, makeChartingTable, makeRow, postedEvents, press, renderStudy, uavColumns, withCells } from "./charting-helpers";

/**
 * Spec 02 "States" (M12a Part B): excluded at full text, no longer kept and
 * archived are read-only with their words; the loading, missing-study and
 * not-kept states; a record with no abstract; no charting columns.
 */

afterEach(() => vi.unstubAllGlobals());

const region = (name: string) => document.querySelector(`[data-region="${name}"]`) as HTMLElement;
const valueInputs = () => Array.from(region("form").querySelectorAll<HTMLInputElement | HTMLTextAreaElement>("input, textarea"));

describe("charting-study.readonly", () => {
  it("excluded at full text: the form is read-only with its words, the values stay visible, the decision is focused", async () => {
    const columns = uavColumns();
    const row = withCells(makeRow(1, { ft_decision: { outcome: "EXCLUDE", reason_code: "EXC-01" } }), columns, { cameras: { state: "value", value: "Sequoia", event_id: "0190a0a0-0000-7000-8000-000000000001" } });
    const engine = installEngine(makeChartingTable([row, makeRow(2)], columns, {}, { has_values: true }));
    await renderStudy("STU-001", "en", "&excluded=1");
    expect(document.querySelector("[data-locked=excluded]")).toHaveTextContent("Excluded at full text: EXC-01 Not a crop field. Change the decision to chart it.");
    expect(valueInputs().every((el) => el.matches(":disabled"))).toBe(true);
    expect((document.querySelector('[data-field="cameras"] [data-value-input]') as HTMLInputElement).value).toBe("Sequoia");
    expect(document.activeElement).toBe(document.querySelector("[data-decision-control] button"));
    await press("n", { altKey: true, code: "KeyN" });
    expect(cellEvents(engine)).toHaveLength(0);
    // The decision can still be changed: Include, and the form opens again.
    await press("i");
    await flush();
    expect(postedEvents(engine)[0][0]).toMatchObject({ kind: "fulltext_decision", value: { outcome: "INCLUDE" } });
    expect(document.querySelector("[data-locked]")).toBeNull();
    expect(valueInputs().some((el) => !el.matches(":disabled"))).toBe(true);
  });

  it("no longer kept: read-only with its words, nothing can be sent", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1), makeRow(2, { kept: false })]));
    await renderStudy("STU-002");
    expect(document.querySelector("[data-locked=not-kept]")).toHaveTextContent("No longer kept at title and abstract. Its values are kept and left out of exports.");
    expect(valueInputs().every((el) => el.matches(":disabled"))).toBe(true);
    expect(within(region("study")).queryByRole("button", { name: /Attach a PDF/ })).toBeNull();
    for (const key of ["r", "i", "e"]) await press(key);
    expect(postedEvents(engine)).toHaveLength(0);
  });

  it("archived: the whole page is read-only with its words and code; the PDF still opens", async () => {
    const row = makeRow(1, { fulltext: { ...makeRow(1).fulltext, status: "retrieved", attachment: { name: "Sa 2018.pdf", size: 2048, sha256: "a".repeat(64), path: "pdfs/STU-001.pdf", origin: "attached" } } });
    const engine = installEngine(makeChartingTable([row], uavColumns(), { read_only: true, read_only_code: "CHARTING_PROTOCOL_REPLACED" }));
    await renderStudy("STU-001");
    const banner = document.querySelector("[data-banner=archived]") as HTMLElement;
    expect(banner).toHaveTextContent("This study's table belongs to the old protocol.");
    expect(within(banner).getByText("CHARTING_PROTOCOL_REPLACED")).toHaveAttribute("dir", "ltr");
    expect(valueInputs().every((el) => el.matches(":disabled"))).toBe(true);
    expect(within(region("study")).getAllByRole("radio").every((r) => (r as HTMLButtonElement).disabled)).toBe(true);
    const open = region("study").querySelector("[data-open-file]") as HTMLElement;
    expect(open).toHaveAttribute("target", "_blank");
    expect(open).toHaveTextContent("opens in a new tab");
    for (const key of ["r", "i", "z"]) await press(key);
    expect(postedEvents(engine)).toHaveLength(0);
  });

  it("loading: the title, the study and the fields as skeletons", async () => {
    let release: () => void = () => undefined;
    installEngine(makeChartingTable([makeRow(1)]), { hold: new Promise<void>((resolve) => (release = resolve)) });
    window.history.replaceState(null, "", "/en/charting/study?id=STU-001");
    render(<ChartingStudyPage locale="en" />);
    await flush();
    expect(document.querySelector("[data-skeleton=title]")).not.toBeNull();
    expect(document.querySelector("[data-skeleton=study]")).not.toBeNull();
    expect(document.querySelector("[data-skeleton=fields]")).not.toBeNull();
    await act(async () => release());
    await flush();
    await flush();
    expect(document.querySelector("[data-skeleton=fields]")).toBeNull();
  });

  it("a study not in the kept set: its words, the code in Details, the way back", async () => {
    installEngine(makeChartingTable([makeRow(1)]));
    await renderStudy("STU-999");
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("That study is not in the kept set any more. Back to the table.");
    expect(within(alert).getByText("RECORD_NOT_KEPT")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to the table" })).toHaveAttribute("href", "/en/charting?view=charting&row=STU-999");
  });

  it("no study named: its words and the way back; not published: Go to Publish", async () => {
    installEngine(makeChartingTable([makeRow(1)]));
    window.history.replaceState(null, "", "/en/charting/study");
    const view = render(<ChartingStudyPage locale="en" />);
    await flush();
    expect(screen.getByRole("alert")).toHaveTextContent("No study was named. Back to the table.");
    view.unmount();
    installEngine(makeChartingTable([makeRow(1)]), { fail: { status: 409, code: "SCREENING_NOT_PUBLISHED" } });
    await renderStudy("STU-001");
    expect(screen.getByRole("link", { name: "Go to Publish" })).toHaveAttribute("href", "/en/screening/publish");
  });

  it("a record without an abstract says so; one with an abstract shows it as plain text", async () => {
    installEngine(makeChartingTable([makeRow(1, { abstract: "Weeds <b>mapped</b>." }), makeRow(2)]));
    await renderStudy("STU-001");
    const abstract = document.querySelector("[data-abstract]") as HTMLElement;
    expect(abstract).toHaveTextContent("Weeds <b>mapped</b>.");
    expect(abstract.querySelector("b")).toBeNull();
    (region("study")).focus();
    await press("j");
    expect(document.querySelector("[data-no-abstract]")).toHaveTextContent("This record has no abstract.");
  });

  it("no charting columns: the sentence and the brand button to add the first one on the table", async () => {
    installEngine(makeChartingTable([makeRow(1)], []));
    await renderStudy("STU-001");
    const state = document.querySelector("[data-state=no-columns]") as HTMLElement;
    expect(state).toHaveTextContent("Your protocol has no charting columns yet.");
    const add = within(state).getByRole("link", { name: "Add the first column" });
    expect(add).toHaveAttribute("href", "/en/charting?view=charting&form=open");
    expect(add).toHaveAttribute("data-variant", "primary");
    expect(document.querySelectorAll('[data-variant="primary"]')).toHaveLength(1);
  });

  it("offline: the sentence, and changes refused here without a request", async () => {
    const engine = installEngine(makeChartingTable([makeRow(1), makeRow(2)]));
    await renderStudy("STU-001");
    const input = document.querySelector('[data-field="cameras"] [data-value-input]') as HTMLInputElement;
    input.focus();
    fireEvent.change(input, { target: { value: "Sequoia" } });
    fireEvent.blur(input);
    await flush();
    engine.fail = "unreachable";
    fireEvent.change(input, { target: { value: "RedEdge" } });
    fireEvent.blur(input);
    await flush();
    const banner = document.querySelector("[data-banner=offline]") as HTMLElement;
    expect(banner.textContent).toMatch(/^The console is not answering\. Nothing is lost; last change saved at \d\d:\d\d\./);
    const before = engine.calls.length;
    fireEvent.change(input, { target: { value: "Altum" } });
    fireEvent.blur(input);
    await flush();
    expect(engine.calls.length).toBe(before);
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("The console is not answering, so the change was not sent.");
  });
});
