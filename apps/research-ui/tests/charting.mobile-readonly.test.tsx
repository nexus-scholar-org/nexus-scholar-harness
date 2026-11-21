import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, renderCharting } from "./charting-helpers";

/** Spec 01 "Mobile layout": at 640 px and below a read-only list, the Show select, and no action. */

afterEach(() => vi.unstubAllGlobals());

describe("charting.mobile-readonly", () => {
  it("lists one card per study with its round and status, says charting is on the desktop, and offers no action", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2, { arm: "citation_searching", round: 2, round_label: "Citation chasing" })]));
    await renderCharting("fr");
    const phone = document.querySelector("[data-phone]") as HTMLElement;
    expect(phone.className).toMatch(/\bsm:hidden\b/);
    expect((document.querySelector("[data-desktop]") as HTMLElement).className).toMatch(/\bhidden\b.*\bsm:block\b/);
    expect(within(phone).getByText("L’extraction se fait sur votre ordinateur.".replace("’", "'"))).toBeInTheDocument();
    const cards = phone.querySelectorAll("[data-phone-card]");
    expect(cards).toHaveLength(2);
    expect(within(cards[1] as HTMLElement).getByText("Recherche de citations")).toBeInTheDocument();
    expect(within(cards[0] as HTMLElement).getByText("À obtenir")).toBeInTheDocument();
    expect(within(phone).queryAllByRole("button")).toHaveLength(0);
    expect(within(phone).queryAllByRole("checkbox")).toHaveLength(0);
    expect(phone.querySelector("input")).toBeNull();
    const show = within(phone).getByRole("combobox", { name: "Afficher" });
    fireEvent.change(show, { target: { value: "requested" } });
    expect(phone.querySelectorAll("[data-phone-card]")).toHaveLength(0);
  });

  it("keys do nothing on a phone-sized screen", async () => {
    const engine = installEngine(makeTable([makeRow(1)]));
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: !query.includes("min-width"), media: query, addEventListener() {}, removeEventListener() {} }));
    await renderCharting();
    (document.querySelector('[data-study-row="STU-001"]') as HTMLElement).focus();
    fireEvent.keyDown(document.activeElement!, { key: "r" });
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(0);
  });
});
