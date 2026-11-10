import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoverySteps, RunSelector, discoveryHref, useJobStream } from "@/components/discovery-frame";
import type { RunSummary } from "@/lib/discovery-api";

/** The shared discovery frame (spec 01 "Shared by 01–08"): step bar, run selector, job stream rules. */

afterEach(() => {
  vi.unstubAllGlobals();
});

const sse = (events: { event: string; data: unknown }[]) => events.map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`).join("");
const job = (state: string) => ({ job_id: "djob_a", kind: "run", state, started_at: "2026-11-10T09:00:00+00:00", finished_at: null, result: null, error: null });
const stream = (body: string) => new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } });
const json = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

describe("discovery.frame", () => {
  it("orders the steps, marks the current one and keeps ?console= on every link", () => {
    render(<DiscoverySteps locale="en" current="dedup" origin="http://127.0.0.1:8765" />);
    const links = screen.getAllByRole("link");
    expect(links.map((l) => l.textContent)).toEqual(["All workspaces", "Discovery overview", "1 Plan", "2 Recall", "3 Harvest", "4 Import", "5 Duplicates", "6 Report", "7 Hand-off"]);
    expect(screen.getByRole("link", { name: "5 Duplicates" })).toHaveAttribute("aria-current", "step");
    for (const link of links) expect(link.getAttribute("href")).toContain("console=");
    expect(screen.getByRole("link", { name: "4 Import" }).getAttribute("href")).toMatch(/^\/en\/screening\/import\?return=discovery&console=/);
  });

  it("lists the runs newest first, links an older run by ?run= and marks a stale one", () => {
    const runs: RunSummary[] = [
      { run: "run_002", status: "PENDING_CORPUS_ACCEPT", started_at: "2026-11-10T10:00:00+00:00", finished_at: null, legs_total: 5, fetched_total: 10, raw_published: true, cap_override: null, stale: false },
      { run: "run_001", status: "PARTIAL", started_at: "2026-11-09T10:00:00+00:00", finished_at: null, legs_total: 5, fetched_total: 8, raw_published: true, cap_override: null, stale: true },
    ];
    render(<RunSelector locale="en" runs={runs} selected="run_001" origin="" step="report" />);
    expect(document.querySelector('[data-run-option="run_002"]')).toHaveAttribute("href", "/en/discovery/report/");
    expect(document.querySelector('[data-run-option="run_001"]')).toHaveAttribute("href", "/en/discovery/report/?run=run_001");
    expect(document.querySelector('[data-run-option="run_001"]')).toHaveAttribute("aria-current", "true");
    expect(screen.getByText("Stale")).toBeInTheDocument();
    expect(discoveryHref("en", "harvest", "", "run_001")).toBe("/en/discovery/harvest/?run=run_001");
  });

  it("rebuilds the view from the replayed events, the last leg event per database winning", async () => {
    const body = sse([
      { event: "snapshot", data: { job: job("running") } },
      { event: "leg", data: { job_id: "djob_a", provider: "openalex", fetched: 1, reported_total: 40, cap: 500, cap_hit: false, status: "running", error_code: null } },
      { event: "leg", data: { job_id: "djob_a", provider: "openalex", fetched: 40, reported_total: 40, cap: 500, cap_hit: false, status: "ok", error_code: null } },
      { event: "stage", data: { job_id: "djob_a", stage: "discovery", status: "COMPLETED", detail: {} } },
      { event: "done", data: { job: job("succeeded") } },
    ]);
    vi.stubGlobal("fetch", vi.fn(async () => stream(body)));
    const onEnd = vi.fn();
    const { result } = renderHook(() => useJobStream("", "djob_a", onEnd));
    await waitFor(() => expect(result.current.ended).toBe(true));
    expect(result.current.legs).toEqual([{ provider: "openalex", fetched: 40, reported_total: 40, cap: 500, cap_hit: false, status: "ok", error_code: null }]);
    expect(result.current.stages.map((s) => s.stage)).toEqual(["discovery"]);
    expect(onEnd).toHaveBeenCalledWith(expect.objectContaining({ state: "succeeded" }));
  });

  it("reconnects once, then shows the last state as connection lost and retries on demand", async () => {
    const open = sse([
      { event: "snapshot", data: { job: job("running") } },
      { event: "leg", data: { job_id: "djob_a", provider: "crossref", fetched: 25, reported_total: 900, cap: 500, cap_hit: false, status: "running", error_code: null } },
    ]);
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => (String(input).endsWith("/events") ? stream(open) : json(200, { job: job("running") })));
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useJobStream("", "djob_a"));
    await waitFor(() => expect(result.current.lost).toBe(true));
    const urls = fetchMock.mock.calls.map((c) => String(c[0]));
    expect(urls.filter((u) => u.endsWith("/events"))).toHaveLength(2);
    expect(urls.filter((u) => u.endsWith("/jobs/djob_a"))).toHaveLength(1);
    expect(result.current.legs[0]?.fetched).toBe(25);
    act(() => result.current.retry());
    await waitFor(() => expect(fetchMock.mock.calls.filter((c) => String(c[0]).endsWith("/events")).length).toBeGreaterThan(2));
  });

  it("says the console no longer knows the job: DISCOVERY_JOB_NOT_FOUND", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json(404, { detail: { code: "DISCOVERY_JOB_NOT_FOUND", message: "No discovery job djob_a in this workspace." } })),
    );
    const { result } = renderHook(() => useJobStream("", "djob_a"));
    await waitFor(() => expect(result.current.error?.code).toBe("DISCOVERY_JOB_NOT_FOUND"));
    expect(result.current.lost).toBe(false);
  });
});
