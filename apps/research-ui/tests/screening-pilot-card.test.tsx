import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PILOT_CARD_COPY, PilotCard } from "@/components/screening-pilot-card";
import { SUPPORTED_LOCALES } from "@/i18n";

/** Prepare's pilot card (spec 13, state A; M11b part C) against a fake engine. */

type Pilot = { pilot_id: string; n: number; decided: number; open: boolean; closed_at: string | null; closed_reason: string | null; pilots: number; recheck: number } | null;

function engine(options: { pilot?: Pilot; approved?: boolean; prepared?: boolean; recheck?: number; refuse?: string; handoff?: boolean } = {}) {
  const log: { method: string; path: string; body: Record<string, unknown> | null }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      log.push({ method, path, body });
      const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "content-type": "application/json" } });
      if (path === "/summary") {
        return json({
          total: 1062, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 1062, conflicts: 0,
          lanes: { agent: 0, you: 0, second_screener: "PARKED" }, protocol_changed: false, criteria_version: 1,
          recheck: options.recheck ?? 0, pilot: options.pilot ?? null,
        });
      }
      if (path === "/criteria") {
        return json({ criteria_version: 1, criteria: [], retired: [], amendments: [], can_amend: !options.approved && !options.handoff,
          batches_prepared: options.prepared ?? true, batch_approved: options.approved ?? false, handoff_batches: options.handoff ? [2] : [] });
      }
      if (path === "/pilot" && method === "POST") {
        if (options.refuse) return json({ detail: { code: options.refuse, message: "refused" } }, 409);
        const n = Number(body?.n);
        return json(body?.confirm ? { recorded: true, n, available: 1062, expected_minutes: 25, pilot_id: "pilot_001", seed: 7, drawn_at: "x" }
          : { recorded: false, n, available: 1062, expected_minutes: 25 });
      }
      return json({ detail: { code: "NOT_FOUND" } }, 404);
    }),
  );
  return log;
}

afterEach(() => vi.unstubAllGlobals());

describe("pilot card", () => {
  it("before a pilot: the brand button names the size, and nothing is drawn before the confirmation", async () => {
    const log = engine();
    render(<PilotCard locale="en" origin="" />);
    const draw = await screen.findByRole("button", { name: "Draw a pilot of 50" });
    expect(draw.getAttribute("data-variant")).toBe("primary");
    expect(screen.getByRole("link", { name: "Screen everything" }).getAttribute("href")).toContain("view=needs_you");
    fireEvent.change(screen.getByLabelText("Records in the pilot"), { target: { value: "30" } });
    fireEvent.click(screen.getByRole("button", { name: "Draw a pilot of 30" }));
    const dialog = await screen.findByRole("alertdialog");
    const text = dialog.textContent ?? "";
    for (const word of ["random", "seed", "not counted"]) expect(text).toContain(word);
    expect(text).toMatch(/30 records at random from the 1.?062/);
    expect(log.filter((l) => l.path === "/pilot").map((l) => l.body?.confirm)).toEqual([false]);
    fireEvent.click(within(dialog).getByRole("button", { name: "Not now" }));
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(log.filter((l) => l.path === "/pilot" && l.body?.confirm === true)).toHaveLength(0);
  });

  it("confirming draws the pilot (one POST with confirm true)", async () => {
    const log = engine();
    render(<PilotCard locale="en" origin="" />);
    fireEvent.click(await screen.findByRole("button", { name: "Draw a pilot of 50" }));
    fireEvent.click(await screen.findByRole("button", { name: "Draw the pilot" }));
    await vi.waitFor(() => expect(log.filter((l) => l.path === "/pilot" && l.body?.confirm === true)).toHaveLength(1));
  });

  it("a refused draw shows the engine's code", async () => {
    engine({ refuse: "PILOT_OPEN" });
    render(<PilotCard locale="en" origin="" />);
    fireEvent.click(await screen.findByRole("button", { name: "Draw a pilot of 50" }));
    expect(await screen.findByText(/PILOT_OPEN/)).toBeTruthy();
  });

  it("while a pilot is open: its progress, Continue the pilot (brand) and the result so far", async () => {
    engine({ pilot: { pilot_id: "pilot_001", n: 50, decided: 12, open: true, closed_at: null, closed_reason: null, pilots: 1, recheck: 0 } });
    render(<PilotCard locale="en" origin="" />);
    expect(await screen.findByRole("heading", { name: "Pilot in progress · 12 of 50 decided" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Continue the pilot" }).getAttribute("href")).toContain("view=pilot");
    expect(screen.getByRole("link", { name: "See the result so far" }).getAttribute("href")).toContain("/screening/pilot?id=pilot_001");
    expect(screen.queryByRole("button", { name: /Draw a pilot/ })).toBeNull();
  });

  it("an ended pilot leads to its result and the rest; records shown again have their line", async () => {
    engine({ pilot: { pilot_id: "pilot_001", n: 50, decided: 38, open: false, closed_at: "x", closed_reason: "ended", pilots: 1, recheck: 3 }, recheck: 3 });
    render(<PilotCard locale="en" origin="" />);
    expect(await screen.findByRole("heading", { name: "Pilot ended · 38 of 50 decided" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "See the result" })).toBeTruthy();
    expect(screen.getByText(/3 records are shown again because a criterion changed/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open them" }).getAttribute("href")).toContain("view=recheck");
  });

  it("after an approval the criteria are fixed and nothing can be drawn", async () => {
    engine({ approved: true });
    render(<PilotCard locale="en" origin="" />);
    expect(await screen.findByText(/A batch is already approved, so the criteria are fixed/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Draw a pilot/ })).toBeNull();
  });

  it("before batches exist the card is not shown", async () => {
    const log = engine({ prepared: false });
    const { container } = render(<PilotCard locale="en" origin="" />);
    await vi.waitFor(() => expect(log.some((l) => l.path === "/criteria")).toBe(true));
    await vi.waitFor(() => expect(container.querySelector("[data-pilot-card]")).toBeNull());
  });

  it("every locale has every key with the same holes", () => {
    const keys = Object.keys(PILOT_CARD_COPY.en).sort();
    const holes = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort().join(",");
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PILOT_CARD_COPY[locale]).sort()).toEqual(keys);
      for (const key of keys) {
        const value = PILOT_CARD_COPY[locale][key as keyof (typeof PILOT_CARD_COPY)["en"]];
        expect(value.length, `${locale}.${key}`).toBeGreaterThan(0);
        expect(holes(value), `${locale}.${key}`).toBe(holes(PILOT_CARD_COPY.en[key as keyof (typeof PILOT_CARD_COPY)["en"]]));
      }
    }
  });
});

describe("pilot card, review C round 1", () => {
  it("finding 5: the size field keeps what is typed, and takes its step when it loses focus", async () => {
    engine();
    render(<PilotCard locale="en" origin="" />);
    const field = (await screen.findByLabelText("Records in the pilot")) as HTMLInputElement;
    fireEvent.change(field, { target: { value: "3" } });
    expect(field.value).toBe("3");
    fireEvent.change(field, { target: { value: "30" } });
    expect(field.value).toBe("30");
    expect(screen.getByRole("button", { name: "Draw a pilot of 30" })).toBeTruthy();
    fireEvent.change(field, { target: { value: "37" } });
    fireEvent.blur(field);
    expect(field.value).toBe("40");
  });

  it("finding 2: Not now and Esc give focus back to the draw button", async () => {
    engine();
    render(<PilotCard locale="en" origin="" />);
    fireEvent.click(await screen.findByRole("button", { name: "Draw a pilot of 50" }));
    const dialog = await screen.findByRole("alertdialog");
    fireEvent.keyDown(dialog, { key: "Escape" });
    await vi.waitFor(() => expect(document.activeElement).toBe(screen.getByRole("button", { name: "Draw a pilot of 50" })));
    fireEvent.click(screen.getByRole("button", { name: "Draw a pilot of 50" }));
    fireEvent.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Not now" }));
    await vi.waitFor(() => expect(document.activeElement).toBe(screen.getByRole("button", { name: "Draw a pilot of 50" })));
  });

  it("finding 4: with batches decided through the hand-off the card offers no draw and names why", async () => {
    engine({ handoff: true });
    render(<PilotCard locale="en" origin="" />);
    expect(await screen.findByText(/decisions made through the file hand-off/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Draw a pilot/ })).toBeNull();
  });
});
