import { within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { flush, installEngine, makeRow, makeTable, renderReport } from "./charting-helpers";

/**
 * Spec 04 "Mobile layout" (question 4): a phone that reaches `/charting/report`
 * gets one line and a 44 px link to `/charting`; no file, no paragraph, and no
 * call to the console.
 */

afterEach(() => vi.unstubAllGlobals());

const phoneWindow = () =>
  vi.stubGlobal("matchMedia", (query: string) => ({ matches: !query.includes("min-width"), media: query, addEventListener() {}, removeEventListener() {} }));

describe("charting.report.mobile", () => {
  it("at 390 px: the desktop line and the link only; no file call, no paragraph", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    phoneWindow();
    await renderReport("en", { settle: false });
    await flush();
    await flush();
    const phone = document.querySelector("[data-phone]") as HTMLElement;
    expect(within(phone).getByRole("heading", { level: 1, name: "Export and methods are on your desktop." })).toBeInTheDocument();
    const link = within(phone).getByRole("link", { name: "Go to charting" });
    expect(link).toHaveAttribute("href", "/en/charting");
    expect(link.className).toMatch(/\bmin-h-11\b/);
    expect(document.querySelector("[data-desktop]")).toBeNull();
    expect(document.querySelector("[data-paragraph]")).toBeNull();
    expect(document.querySelector("[data-file]")).toBeNull();
    expect(within(phone).queryAllByRole("button")).toHaveLength(0);
    expect(engine.calls).toEqual([]);
  });

  it("is a phone-only card by its classes, and the desktop page is hidden below 640 px", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderReport("fr");
    const phone = document.querySelector("[data-phone]") as HTMLElement;
    expect(phone.className).toMatch(/\bsm:hidden\b/);
    expect((document.querySelector("[data-desktop]") as HTMLElement).className).toMatch(/\bhidden\b.*\bsm:block\b/);
    expect(within(phone).getByText("L'export et les méthodes sont sur votre ordinateur.")).toBeInTheDocument();
    expect(within(phone).getByRole("link", { name: "Aller à l'extraction" })).toHaveAttribute("href", "/fr/charting");
  });
});
