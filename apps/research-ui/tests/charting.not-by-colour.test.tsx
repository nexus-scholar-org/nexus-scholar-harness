import { within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, renderCharting } from "./charting-helpers";

/**
 * Spec 01 "Accessibility": a status is words plus an icon, never colour alone.
 * Part A shows the full-text statuses, the decision, "No longer kept" and "New
 * since"; Not reported, Chart again and No full text are cells of Part B's view.
 */

afterEach(() => vi.unstubAllGlobals());

describe("charting.not-by-colour", () => {
  it("every status and decision badge carries words and an icon on its role", async () => {
    const ft = makeRow(0).fulltext;
    installEngine(
      makeTable([
        makeRow(1),
        makeRow(2, { fulltext: { ...ft, status: "requested", requested_on: "2026-11-20" } }),
        makeRow(3, { fulltext: { ...ft, status: "retrieved" }, ft_decision: { outcome: "INCLUDE" } }),
        makeRow(4, { fulltext: { ...ft, status: "not_retrieved", reason: "other", reason_text: "Library loan pending" } }),
        makeRow(5, { ft_decision: { outcome: "EXCLUDE", reason_code: "OTHER", reason_text: "Same study" } }),
      ]),
    );
    await renderCharting();
    document.querySelector("[data-show-excluded]")!.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    const desktop = document.querySelector("[data-desktop]") as HTMLElement;
    const badges = Array.from(desktop.querySelectorAll("[data-badge]"));
    expect(badges.length).toBeGreaterThanOrEqual(8);
    for (const badge of badges) {
      expect(badge.textContent?.trim(), badge.getAttribute("data-badge") ?? "").not.toBe("");
      expect(badge.querySelector("svg[data-icon]"), badge.getAttribute("data-badge") ?? "").not.toBeNull();
      expect(badge.getAttribute("data-role")).toMatch(/^(include|unclear|blocked|exclude|neutral)$/);
    }
    const word = (id: string) => (desktop.querySelector(`[data-study-row="${id}"] [data-badge^=status]`) as HTMLElement).textContent;
    expect([1, 2, 3, 4].map((i) => word(`STU-00${i}`))).toEqual(["To get", "Requested on 2026-11-20", "Retrieved", "Not retrieved"]);
    const role = (id: string, kind: string) => desktop.querySelector(`[data-study-row="${id}"] [data-badge^=${kind}]`)!.getAttribute("data-role");
    expect([role("STU-002", "status"), role("STU-003", "status"), role("STU-004", "status")]).toEqual(["unclear", "include", "blocked"]);
    expect([role("STU-001", "decision"), role("STU-003", "decision")]).toEqual(["unclear", "include"]);
    expect(within(desktop.querySelector('[data-study-row="STU-004"]') as HTMLElement).getByText("Library loan pending")).toBeInTheDocument();
  });

  it("No longer kept and New since are words, not a tint", async () => {
    installEngine(makeTable([makeRow(1, { new_since: "2026-11-21T09:00:00Z" }), makeRow(2, { kept: false })]));
    await renderCharting();
    expect(document.querySelector('[data-study-row="STU-001"] [data-new]')).toHaveTextContent("New since 2026-11-21");
    expect(document.querySelector('[data-study-row="STU-002"] [data-no-longer-kept]')).toHaveTextContent("No longer kept at title and abstract");
  });
});
