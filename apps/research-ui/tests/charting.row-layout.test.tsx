import { act, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Button } from "@/components/ui/base";

import { installEngine, lastLookup, makeRow, makeTable, renderCharting, waitingRow } from "./charting-helpers";

/**
 * H-charting-row-layout (2026-11-23). On the researcher's 443-study review a
 * table row was about five lines tall and the focused row looked cut in two.
 *
 * 1. The row's actions asked for `px-1 text-xs` through `className`, which lost
 *    to the Button's own `px-4 text-[0.9375rem]`, so each sat on a line of its
 *    own. They are now the Button's `small` size, side by side, never wrapping.
 * 2. The two pinned cells painted an opaque `bg-leaf` over the row's state and
 *    over the row's focus outline. They now take the row's own background, and
 *    the focused row's frame is drawn by its cells.
 *
 * jsdom does no layout, so these pin the classes and structure that give the
 * look; the heights were measured in a browser (the milestone record).
 */

afterEach(() => vi.unstubAllGlobals());

const classes = (el: Element | null) => (el?.getAttribute("class") ?? "").split(/\s+/).filter(Boolean);
const row = (id: string) => document.querySelector(`[data-desktop] [data-study-row="${id}"]`) as HTMLElement;
const bgOf = (el: Element) => classes(el).filter((c) => /^bg-/.test(c));
const shadowsOf = (el: Element) => classes(el).filter((c) => /(^|:)shadow-\[/.test(c));

describe("charting.row-layout: the Button's small size", () => {
  it("keeps the 44 px target and drops the regular size's padding and text size", () => {
    render(
      <>
        <Button data-testid="regular">Regular</Button>
        <Button size="small" variant="quiet" data-testid="small">
          Small
        </Button>
      </>,
    );
    const regular = classes(document.querySelector("[data-testid=regular]"));
    const small = classes(document.querySelector("[data-testid=small]"));
    expect(regular).toEqual(expect.arrayContaining(["min-h-11", "px-4", "text-[0.9375rem]"]));
    expect(small).toEqual(expect.arrayContaining(["min-h-11", "px-1", "text-xs", "whitespace-nowrap"]));
    expect(small).not.toContain("px-4");
    expect(small).not.toContain("text-[0.9375rem]");
    expect(small).not.toContain("gap-2");
    expect(document.querySelector("[data-testid=small]")).toHaveAttribute("data-size", "small");
    expect(document.querySelector("[data-testid=regular]")).not.toHaveAttribute("data-size");
  });
});

describe("charting.row-layout: the row's actions", () => {
  it("puts each cell's two actions side by side, at the table's size, with their names and hooks", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    const r = row("STU-001");
    const file = r.querySelector('[data-row-actions="file"]')!;
    const decision = r.querySelector('[data-row-actions="decision"]')!;
    for (const box of [file, decision]) {
      expect(classes(box)).toEqual(expect.arrayContaining(["flex", "flex-nowrap"]));
      expect(classes(box)).not.toContain("flex-wrap");
      expect(classes(box)).not.toContain("flex-col");
    }
    expect(file.querySelector("[data-attach]")).toHaveAccessibleName("Attach a PDF");
    expect(file.querySelector("[data-paste-link]")).toHaveAccessibleName("Paste a link");
    expect(decision.querySelector("[data-include]")?.getAttribute("aria-label")).toMatch(/^Include/);
    expect(decision.querySelector("[data-exclude]")?.getAttribute("aria-label")).toMatch(/^Exclude/);
    for (const button of r.querySelectorAll("[data-row-actions] button")) {
      expect(button).toHaveAttribute("data-size", "small");
      expect(classes(button)).toContain("min-h-11");
      expect(classes(button)).not.toContain("px-4");
    }
    // Keyboard order stays: the file's two actions, then the decision's two.
    const order = Array.from(r.querySelectorAll("button")).map((b) => Array.from(b.attributes).find((a) => a.name.startsWith("data-") && a.name !== "data-variant" && a.name !== "data-size")?.name);
    expect(order).toEqual(["data-attach", "data-paste-link", "data-include", "data-exclude"]);
  });

  it("the fetched file's Confirm and Discard and the What was tried disclosure are small too", async () => {
    installEngine(makeTable([waitingRow(1), makeRow(2, { fulltext: { ...makeRow(2).fulltext, last_lookup: lastLookup() } })]));
    await renderCharting();
    for (const hook of ["data-fetch-confirm", "data-fetch-discard"]) {
      expect(row("STU-001").querySelector(`[${hook}]`), hook).toHaveAttribute("data-size", "small");
    }
    expect(row("STU-002").querySelector("[data-tried-open]")).toHaveAttribute("data-size", "small");
  });
});

describe("charting.row-layout: the pinned cells carry the row's state", () => {
  it("the row owns one opaque background and both pinned cells inherit it, selected or not", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    const pinned = (id: string) => [row(id).querySelector('[data-pinned="start"]')!, row(id).querySelector('[data-pinned="study"]')!];
    expect(bgOf(row("STU-001"))).toEqual(["bg-leaf"]);
    for (const cell of pinned("STU-001")) {
      expect(bgOf(cell)).toEqual(["bg-inherit"]);
      expect(classes(cell)).toContain("sticky");
    }
    await act(async () => {
      fireEvent.click(row("STU-001").querySelector('input[type="checkbox"]')!);
    });
    expect(row("STU-001")).toHaveAttribute("aria-selected", "true");
    expect(bgOf(row("STU-001"))).toEqual(["bg-brand-soft"]);
    for (const cell of pinned("STU-001")) expect(bgOf(cell)).toEqual(["bg-inherit"]);
    expect(bgOf(row("STU-002"))).toEqual(["bg-leaf"]);
  });

  it("a row no longer kept is muted as a whole, the pinned cells with it", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2, { kept: false })]));
    await renderCharting();
    expect(classes(row("STU-002"))).toEqual(expect.arrayContaining(["opacity-70", "text-ink-muted", "bg-leaf"]));
    for (const cell of row("STU-002").querySelectorAll("[data-pinned]")) expect(bgOf(cell)).toEqual(["bg-inherit"]);
  });

  it("the first pinned column is as wide as the second's offset, so nothing shows between them", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    const head = document.querySelector("[data-desktop] thead tr")!.children;
    for (const cell of [head[0], row("STU-001").querySelector('[data-pinned="start"]')!]) {
      expect(classes(cell)).toEqual(expect.arrayContaining(["sticky", "start-0", "w-12", "min-w-12"]));
    }
    for (const cell of [head[1], row("STU-001").querySelector('[data-pinned="study"]')!]) expect(classes(cell)).toEqual(expect.arrayContaining(["sticky", "start-12"]));
  });
});

describe("charting.row-layout: the focus frame goes round the whole row", () => {
  it("every cell of the focused row draws its edge, the first and last their sides in both directions", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    await act(async () => {
      fireEvent.click(row("STU-002").querySelector("td:nth-child(3)")!);
    });
    expect(row("STU-002")).toHaveAttribute("data-focused", "true");
    const cells = Array.from(row("STU-002").children);
    expect(cells).toHaveLength(6);
    const topAndBottom = ["inset_0_2px_0_var(--color-focus)", "inset_0_-2px_0_var(--color-focus)"];
    for (const cell of cells) {
      const shadows = shadowsOf(cell);
      expect(shadows.length, cell.outerHTML.slice(0, 80)).toBeGreaterThan(0);
      for (const s of shadows) for (const edge of topAndBottom) expect(s).toContain(edge);
    }
    const ltr = (cell: Element) => shadowsOf(cell).find((s) => !s.startsWith("rtl:"))!;
    const rtl = (cell: Element) => shadowsOf(cell).find((s) => s.startsWith("rtl:"))!;
    // Start edge: left in English, right in Arabic; the end edge the other way round.
    expect(ltr(cells[0])).toContain("inset_2px_0_0_var(--color-focus)");
    expect(rtl(cells[0])).toContain("inset_-2px_0_0_var(--color-focus)");
    expect(ltr(cells[5])).toContain("inset_-2px_0_0_var(--color-focus)");
    expect(rtl(cells[5])).toContain("inset_2px_0_0_var(--color-focus)");
    for (const cell of cells.slice(1, 5)) expect(shadowsOf(cell)).toHaveLength(1);
    // The row that lost the focus draws nothing.
    for (const cell of row("STU-001").children) expect(shadowsOf(cell)).toEqual([]);
  });

  it("the row's own outline, which the pinned cells and the next row painted over, is kept only for forced colours", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2)]));
    await renderCharting();
    await act(async () => {
      fireEvent.click(row("STU-001").querySelector("td:nth-child(3)")!);
    });
    const outlines = (id: string) => classes(row(id)).filter((c) => /outline/.test(c));
    // Normal colours: no outline of the row's own (the browser's default ring is switched off too).
    expect(outlines("STU-001").filter((c) => !c.startsWith("forced-colors:"))).toEqual(["not-forced-colors:focus-visible:outline-none"]);
    // Forced colours drop box shadows: the focused row keeps an outline there, the other row has none.
    expect(outlines("STU-001")).toEqual(expect.arrayContaining(["forced-colors:outline-2", "forced-colors:-outline-offset-2", "forced-colors:outline-focus"]));
    expect(outlines("STU-002")).toEqual(["not-forced-colors:focus-visible:outline-none"]);
  });
});
