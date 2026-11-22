import { act, fireEvent, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POLL_MS } from "@/components/charting-fetch";

import { flush, installEngine, makeRow, makeTable, press, renderCharting, runView } from "./charting-helpers";

/**
 * Spec 03 "Running", "Cancel", "Interrupted", "Offline" and "Error" (M12a Part
 * F): the run card's progress bar and words, its counts and what it does now,
 * the last requests behind "Requests", one live announcement at the start, every
 * 25 records and at the end; Cancel says it stops after the record in hand (Esc
 * never cancels); a second start is FETCH_ALREADY_ACTIVE with "Show progress";
 * a run the console did not finish reads as interrupted; a poll that fails keeps
 * the card and says so.
 */

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const card = () => desktop().querySelector("[data-fetch-run]") as HTMLElement | null;
const live = () => desktop().querySelector("[data-fetch-announce]")!.textContent;
const rowOf = (id: string) => desktop().querySelector(`[data-study-row="${id}"]`) as HTMLElement;

async function poll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(POLL_MS);
  });
  await flush();
}

function focusRow(id: string) {
  fireEvent.focus(rowOf(id));
  rowOf(id).focus();
}

const table = () => makeTable([makeRow(1), makeRow(2), makeRow(3)]);

describe("charting.fetch-run", () => {
  it("shows the progress, the counts and what it does now; announces the start, every 25 records and the end", async () => {
    const started = runView({ total: 214 });
    const engine = installEngine(table(), {
      fetch: {
        started,
        afterStart: [
          runView({ total: 214, reached: 10, found: 4, downloaded: 3, now: { phase: "asking", host: "api.unpaywall.org" } }),
          runView({ total: 214, reached: 20, found: 8, downloaded: 6, now: { phase: "downloading", host: "europepmc.org" } }),
          runView({ total: 214, reached: 41, found: 12, downloaded: 9, failed_checks: 2, errors: { "HTTP 403": 2, "timed out": 1 }, now: { phase: "waiting", host: "arxiv.org", seconds: 3 } }),
          runView({ total: 214, reached: 60, found: 20, downloaded: 15 }),
          runView({ state: "finished", total: 214, reached: 214, found: 100, downloaded: 96, finished_at: "2026-11-22T14:32:00Z" }),
        ],
      },
    });
    await renderCharting();
    focusRow("STU-001");
    await press("l");
    await press("Enter");
    expect(card()).toHaveAttribute("data-fetch-run", "running");
    expect(within(card()!).getByRole("heading", { name: "Looking up open-access copies" })).toBeInTheDocument();
    expect(live()).toBe("Look-up started: 214 records");
    const bar = within(card()!).getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuemax", "214");
    expect(bar).toHaveAttribute("aria-valuenow", "0");
    expect(bar).toHaveAttribute("aria-valuetext", "0 of 214 records");

    await poll();
    expect(card()!.querySelector("[data-fetch-now]")).toHaveTextContent("Asking Unpaywall");
    expect(live()).toBe("Look-up started: 214 records");
    await poll();
    expect(card()!.querySelector("[data-fetch-now]")).toHaveTextContent("Downloading from europepmc.org");
    expect(within(card()!.querySelector("[data-fetch-now]") as HTMLElement).getByText("europepmc.org")).toHaveAttribute("dir", "ltr");
    await poll();
    expect(within(card()!).getByRole("progressbar")).toHaveAttribute("aria-valuetext", "41 of 214 records");
    expect(card()!.querySelector("[data-fetch-counts]")).toHaveTextContent("12 found · 9 downloaded · 2 failed checks · 3 errors");
    expect(card()!.querySelector("[data-fetch-now]")).toHaveTextContent("Waiting 3 s before the next request to arxiv.org");
    expect(live()).toBe("41 of 214 records looked up");
    await poll();
    expect(live()).toBe("60 of 214 records looked up");
    await poll();
    expect(card()).toBeNull();
    expect(live()).toBe("Look-up finished. 96 files wait for you.");
    expect(desktop().querySelector("[data-fetch-summary]")).toHaveTextContent("Look-up finished");
    // The rows were read again as the run moved, so files that arrived are on the screen.
    expect(engine.calls.filter((c) => c.method === "GET" && c.path === "/api/v1/charting").length).toBeGreaterThanOrEqual(4);
  });

  it("'Requests' is a disclosure with the last eight requests, each host and its answer in words", async () => {
    const requests = [
      { host: "a.org", answer: "HTTP 200" },
      { host: "b.org:8443", answer: "HTTP 403" },
      { host: "c.org", answer: "stored" },
      { host: "d.org", answer: "HTTP 429: the host asks to try later" },
      { host: "e.org", answer: "timed out" },
      { host: "f.org", answer: "network error (ClientConnectorError)" },
      { host: "g.org", answer: "not a PDF (no %PDF- header in the first 1024 bytes)" },
      { host: "h.org", answer: "HTTP 404" },
      { host: "i.org", answer: "too many redirects" },
    ];
    installEngine(table(), { fetch: { runs: [runView({ reached: 9, recent_requests: requests })] } });
    await renderCharting();
    const toggle = within(card()!).getByRole("button", { name: "Requests" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const items = [...card()!.querySelectorAll("[data-fetch-request-list] li")].map((li) => li.textContent);
    expect(items).toEqual([
      "b.org:8443: HTTP 403: the host refused",
      "c.org: a PDF",
      "d.org: HTTP 429: the host asks to try later",
      "e.org: the host did not answer in time",
      "f.org: the connection failed",
      "g.org: the file failed the checks: not a PDF (an HTML page, for example)",
      "h.org: HTTP 404: not found",
      "i.org: too many redirects",
    ]);
  });

  it("Cancel says it stops after the record in hand; Esc never cancels", async () => {
    const engine = installEngine(table(), { fetch: { runs: [runView({ reached: 5 })] } });
    await renderCharting();
    focusRow("STU-001");
    await press("Escape");
    expect(engine.calls.some((c) => c.path === "/api/v1/charting/fetch/cancel")).toBe(false);
    fireEvent.click(within(card()!).getByRole("button", { name: "Cancel the look-up" }));
    await flush();
    expect(engine.calls.some((c) => c.method === "POST" && c.path === "/api/v1/charting/fetch/cancel")).toBe(true);
    expect(card()).toHaveAttribute("data-fetch-run", "cancelling");
    expect(card()).toHaveTextContent("Stopping after the record in hand…");
    expect(within(card()!).queryByRole("button", { name: "Cancel the look-up" })).toBeNull();
  });

  it("a second start is FETCH_ALREADY_ACTIVE, with Show progress", async () => {
    const engine = installEngine(table(), { fetch: { startFail: { status: 409, code: "FETCH_ALREADY_ACTIVE" } } });
    await renderCharting();
    focusRow("STU-001");
    await press("l");
    await press("Enter");
    const alert = desktop().querySelector("[data-refusal=FETCH_ALREADY_ACTIVE]") as HTMLElement;
    expect(alert).toHaveAttribute("role", "alert");
    expect(alert).toHaveTextContent("A look-up is already running for this workspace. Wait for it to finish, or cancel it.");
    engine.fetch.runs = [runView({ reached: 12 })];
    fireEvent.click(within(alert).getByRole("button", { name: "Show progress" }));
    await flush();
    expect(card()).toHaveAttribute("data-fetch-run", "running");
    expect(desktop().querySelector("[data-refusal]")).toBeNull();
  });

  it("a run the console did not finish reads as interrupted, with what it reached", async () => {
    installEngine(table(), { fetch: { runs: [runView({ state: "interrupted", reached: 88, total: 214 })] } });
    await renderCharting();
    expect(desktop().querySelector("[data-fetch-run=interrupted]")).toHaveTextContent(
      "The last look-up stopped after 88 of 214 records, probably because the console was closed. What it reached is kept. Look up the rest with L.",
    );
  });

  it("a poll that fails keeps the card and says so; with the console gone, the offline words", async () => {
    const engine = installEngine(table(), { fetch: { runs: [runView({ reached: 30 })] } });
    await renderCharting();
    expect(card()).not.toBeNull();
    engine.fetch.pollFail = { status: 500, code: "ATOMIC_COMMIT_FAILED" };
    await poll();
    expect(card()).toHaveTextContent("Progress could not be read. Trying again.");
    expect(within(card()!).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "30");
    engine.fetch.pollFail = undefined;
    engine.fetch.runs = [runView({ reached: 40 })];
    await poll();
    expect(card()).not.toHaveTextContent("Progress could not be read.");
    expect(within(card()!).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "40");
  });

  it("offline: the card adds that a closed console stopped the run, and Cancel is refused here", async () => {
    const engine = installEngine(table(), { fetch: { runs: [runView({ reached: 30 })] } });
    await renderCharting();
    focusRow("STU-001");
    engine.fail = "unreachable";
    await press("r");
    expect(desktop().querySelector("[data-banner=offline]")).not.toBeNull();
    expect(card()).toHaveTextContent("If the console was closed, the look-up stopped with it; records reached are kept.");
    const before = engine.calls.length;
    fireEvent.click(within(card()!).getByRole("button", { name: "Cancel the look-up" }));
    await press("l");
    await press("c");
    expect(engine.calls.length).toBe(before);
    expect(document.querySelector("[data-status-line]")).toHaveTextContent("The console is not answering, so the change was not sent.");
  });
});
