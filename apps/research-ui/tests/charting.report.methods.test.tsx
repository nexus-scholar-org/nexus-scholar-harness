import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CHARTING_COPY } from "@/lib/charting-copy";

import { PARAGRAPH, installEngine, makeMethods, makeRow, makeTable, renderReport } from "./charting-helpers";

/**
 * Spec 04 "Methods paragraph": the engine's English draft in `lang="en" dir="ltr"`
 * with the draft treatment, Copy paragraph to the clipboard only, the notes and
 * what is not stated, and Details with the figures and the files they come from.
 * Reading and copying send only GETs: no workspace write, no journal row.
 */

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function clipboard(fails = false) {
  const writeText = vi.fn(async () => {
    if (fails) throw new Error("blocked");
  });
  Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
  return writeText;
}

const announce = () => document.querySelector("[data-desktop] [data-announce]") as HTMLElement;

describe("charting.report.methods", () => {
  it("shows the engine's paragraph as a labelled draft region with the dashed treatment", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport();
    const paragraph = document.querySelector("[data-paragraph]") as HTMLElement;
    expect(paragraph.textContent).toBe(PARAGRAPH);
    expect(paragraph).toHaveAttribute("role", "region");
    expect(screen.getByRole("region", { name: "Methods paragraph Draft · check before you submit" })).toBe(paragraph);
    const draft = document.querySelector("[data-draft]") as HTMLElement;
    expect(draft.className).toMatch(/\bborder-dashed\b/);
    expect(draft.className).toMatch(/\bbg-brand-soft\b/);
    expect(within(draft).getByText("Draft · check before you submit")).toBeInTheDocument();
    expect(screen.getByText("Written in English for a manuscript. Check every number against your PRISMA flow diagram.")).toBeInTheDocument();
  });

  it("keeps the paragraph, the notes and what is not stated in lang=en dir=ltr on an Arabic page", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport("ar");
    const paragraph = document.querySelector("[data-paragraph]") as HTMLElement;
    expect(paragraph).toHaveAttribute("lang", "en");
    expect(paragraph).toHaveAttribute("dir", "ltr");
    for (const list of document.querySelectorAll("[data-caveats] ul, [data-not-stated] ul")) {
      expect(list).toHaveAttribute("lang", "en");
      expect(list).toHaveAttribute("dir", "ltr");
    }
    expect(screen.getByRole("button", { name: CHARTING_COPY.ar["charting.report.methods.copy"] })).toBeInTheDocument();
    expect(screen.getByText(CHARTING_COPY.ar["charting.report.methods.language"])).toBeInTheDocument();
  });

  it("Copy paragraph writes the paragraph to the clipboard, announces Copied and keeps the focus on the button", async () => {
    installEngine(makeTable([makeRow(1)]));
    const writeText = clipboard();
    await renderReport();
    const button = screen.getByRole("button", { name: "Copy paragraph" });
    button.focus();
    fireEvent.click(button);
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(PARAGRAPH));
    await waitFor(() => expect(announce()).toHaveTextContent("Copied"));
    expect(announce()).toHaveAttribute("aria-live", "polite");
    expect(document.activeElement).toBe(button);
  });

  it("c inside the paragraph card copies it too", async () => {
    installEngine(makeTable([makeRow(1)]));
    const writeText = clipboard();
    await renderReport();
    const paragraph = document.querySelector("[data-paragraph]") as HTMLElement;
    paragraph.focus();
    fireEvent.keyDown(paragraph, { key: "c" });
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(PARAGRAPH));
    writeText.mockClear();
    fireEvent.keyDown(paragraph, { key: "c", ctrlKey: true });
    expect(writeText).not.toHaveBeenCalled();
  });

  it("says so when the clipboard refuses", async () => {
    installEngine(makeTable([makeRow(1)]));
    clipboard(true);
    await renderReport();
    fireEvent.click(screen.getByRole("button", { name: "Copy paragraph" }));
    await waitFor(() => expect(announce()).toHaveTextContent("Copying is blocked here; select the paragraph and copy it yourself."));
  });

  it("lists the engine's caveats under Notes and its not_stated under Not stated", async () => {
    const methods = makeMethods();
    installEngine(makeTable([makeRow(1)]), { methods });
    await renderReport();
    const notes = document.querySelector("[data-caveats]") as HTMLElement;
    expect(within(notes).getByRole("heading", { level: 3, name: "Notes" })).toBeInTheDocument();
    expect(within(notes).getAllByRole("listitem").map((li) => li.textContent)).toEqual(methods.caveats);
    const notStated = document.querySelector("[data-not-stated]") as HTMLElement;
    expect(within(notStated).getByRole("heading", { level: 3, name: "Not stated" })).toBeInTheDocument();
    expect(within(notStated).getAllByRole("listitem").map((li) => li.textContent)).toEqual(methods.not_stated);
  });

  it("leaves Notes and Not stated out when the engine has none", async () => {
    installEngine(makeTable([makeRow(1)]), { methods: makeMethods({ methods: { caveats: [], not_stated: [] } }) });
    await renderReport();
    expect(document.querySelector("[data-caveats]")).toBeNull();
    expect(document.querySelector("[data-not-stated]")).toBeNull();
  });

  it("puts the figures and the files with their digests behind Details, closed, and Esc closes it", async () => {
    const methods = makeMethods();
    installEngine(makeTable([makeRow(1)]), { methods });
    await renderReport();
    const details = document.querySelector("[data-methods-details]") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(within(details).getByText("Details")).toBeInTheDocument();
    const figures = [...details.querySelectorAll("[data-figures] li")].map((li) => li.textContent);
    expect(figures).toEqual([
      "Open-access copies used: 1; discarded: 0",
      "Services: Unpaywall",
      "Reviewers who decided at full text: 1; who charted: 1",
      "Studies charted: 5; not charted: 3",
      "Cells not charted: 7; of them required: 2",
      "Studies charted in the pilot: 2",
      "Form amendments: 0",
    ]);
    expect(within(details).getByText("What this statement is based on")).toBeInTheDocument();
    for (const source of methods.sources) {
      expect(within(details).getByText(source.path)).toHaveAttribute("dir", "ltr");
      expect(within(details).getByText(source.digest)).toHaveAttribute("dir", "ltr");
    }
    details.open = true;
    fireEvent.keyDown(details.querySelector("summary")!, { key: "Escape" });
    expect(details.open).toBe(false);
  });

  it("reads and copies with GETs only: no write, no journal row", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    clipboard();
    await renderReport();
    fireEvent.click(screen.getByRole("button", { name: "Copy paragraph" }));
    await waitFor(() => expect(announce()).toHaveTextContent("Copied"));
    expect(engine.calls.length).toBeGreaterThan(0);
    expect(engine.calls.every((c) => c.method === "GET")).toBe(true);
    expect([...new Set(engine.calls.map((c) => c.path))].sort()).toEqual(["/api/v1/charting", "/api/v1/charting/methods"]);
  });
});
