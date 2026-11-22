import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, postedEvents, renderCharting, runView, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Phone (≤ 640 px, read-only)" (M12a Part F, question 7): a card shows
 * the badge (words and icon), source, version, licence and identity result, and
 * "Open the file" as a 44 px link in a new tab; no look-up, no Cancel, no
 * Confirm or Discard, one desktop line instead; the run card and the summary
 * are plain text with no button.
 */

afterEach(() => vi.unstubAllGlobals());

const phone = () => document.querySelector("[data-phone]") as HTMLElement;

describe("charting.fetch-mobile", () => {
  it("a card with a waiting file is read-only: the facts, Open as a 44 px link, and the desktop line", async () => {
    installEngine(makeTable([waitingRow(1, { identity: "title found" }), makeRow(2)]));
    await renderCharting();
    const card = phone().querySelectorAll("[data-phone-card]")[0] as HTMLElement;
    const badge = card.querySelector("[data-badge=fetch-to-confirm]") as HTMLElement;
    expect(badge).toHaveTextContent("Fetched, to confirm");
    expect(badge.querySelector("svg[data-icon]")).not.toBeNull();
    const pending = card.querySelector("[data-phone-pending]") as HTMLElement;
    expect(pending.querySelector("[data-fetch-source]")).toHaveTextContent("Found by Unpaywall · europepmc.org");
    expect(pending.querySelector("[data-fetch-version]")).toHaveTextContent("Published version");
    expect(pending.querySelector("[data-fetch-licence]")).toHaveTextContent("Licence: cc-by");
    expect(pending.querySelector("[data-identity]")).toHaveTextContent("Title found in the file");
    const open = within(pending).getByRole("link", { name: "Open the file of Study number 1" });
    expect(open).toHaveAttribute("target", "_blank");
    expect(open.className).toMatch(/\bmin-h-11\b/);
    expect(pending.querySelector("[data-fetch-mobile]")).toHaveTextContent("Confirm or discard this file on your desktop.");
    // The card's own link and the file's link are siblings, never nested.
    expect(open.closest("[data-phone-link]")).toBeNull();
    expect(within(phone()).queryAllByRole("button")).toHaveLength(0);
  });

  it("the run card and the summary are plain text on a phone, with no button", async () => {
    installEngine(makeTable([makeRow(1)]), { fetch: { runs: [runView({ reached: 41, total: 214, found: 12, downloaded: 9 })] } });
    await renderCharting();
    const run = phone().querySelector("[data-fetch-run]") as HTMLElement;
    expect(run).toHaveTextContent("Looking up open-access copies");
    expect(run).toHaveTextContent("41 of 214 records");
    expect(run).toHaveTextContent("12 found · 9 downloaded · 0 failed checks · 0 errors");
    expect(within(run).queryAllByRole("button")).toHaveLength(0);
    expect(within(run).queryByRole("progressbar")).toBeNull();
  });

  it("the summary on a phone: its counts and no button", async () => {
    installEngine(makeTable([makeRow(1)]), { fetch: { runs: [runView({ state: "finished", reached: 214, total: 214, downloaded: 96, try_later: 8, finished_at: "2026-11-22T14:32:00Z" })] } });
    await renderCharting();
    const summary = phone().querySelector("[data-fetch-summary]") as HTMLElement;
    expect(summary).toHaveTextContent("96 downloaded, waiting for you");
    expect(within(summary).queryAllByRole("button")).toHaveLength(0);
  });

  it("on a phone window the keys of the look-up send nothing", async () => {
    const engine = installEngine(makeTable([waitingRow(1)]));
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: !query.includes("min-width"), media: query, addEventListener() {}, removeEventListener() {} }));
    await renderCharting();
    expect(document.querySelector("[data-desktop]")).toBeNull();
    (document.querySelector("[data-phone-link]") as HTMLElement).focus();
    for (const key of ["l", "c", "d"]) fireEvent.keyDown(document.activeElement!, { key });
    expect(engine.calls.some((c) => c.path.startsWith("/api/v1/charting/fetch/plan"))).toBe(false);
    expect(postedEvents(engine)).toHaveLength(0);
  });
});
