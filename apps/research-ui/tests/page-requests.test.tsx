import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartingPage } from "@/components/charting-page";
import { ChartingStudyPage } from "@/components/charting-study";
import { NextStepBar } from "@/components/next-step-bar";
import { ScreeningAgreement } from "@/components/screening-agreement";
import { ScreeningExport } from "@/components/screening-export";
import { ScreeningHome } from "@/components/screening-home";
import { ScreeningImport } from "@/components/screening-import";
import { ScreeningPilot } from "@/components/screening-pilot";
import { ScreeningPrepare } from "@/components/screening-prepare";
import { ScreeningProposals } from "@/components/screening-proposals";
import { ScreeningPublish } from "@/components/screening-publish";
import { TriagePage } from "@/components/triage-page";
import { WorkspacesScreen } from "@/components/workspaces-screen";

/**
 * H-screening-read-performance, DoD 5 and 7: no page of Screening, Charting or
 * Workspaces sends the same GET twice while it loads. Every page is answered by
 * a real engine's recorded answers on a published three-record review
 * (`tests/fixtures/page-engine.json`, written by `tests/console/_record_page_engine.py`),
 * so it reaches the state a published review shows and sends what it sends there.
 */

type Recorded = { study: string; answers: Record<string, { status: number; body: unknown }> };
const ENGINE = JSON.parse(readFileSync(resolve(process.cwd(), "tests/fixtures/page-engine.json"), "utf-8")) as Recorded;

function answerFor(path: string, search: URLSearchParams): { status: number; body: unknown } | undefined {
  const study = path.match(/\/(records)\/([^/]+)/);
  const key = study ? path.replace(study[2], ENGINE.study) : path;
  const exact = ENGINE.answers[`${key}${search.toString() ? `?${search.toString()}` : ""}`];
  if (exact) return exact;
  if (key.endsWith("/queue")) {
    const view = search.get("view") ?? "needs_you";
    const match = Object.keys(ENGINE.answers).find((k) => k.startsWith(`${key}?view=${view}&`));
    return match ? ENGINE.answers[match] : undefined;
  }
  return ENGINE.answers[key];
}

function engine(): string[] {
  const gets: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, init?: RequestInit) => {
      const url = new URL(input, "http://localhost");
      const path = url.pathname.replace(/^\/api\/console/, "");
      const method = (init?.method ?? "GET").toUpperCase();
      if (method === "GET") gets.push(`${path}${url.search}`);
      const answer = method === "GET" ? answerFor(path, url.searchParams) : undefined;
      const status = answer?.status ?? 404;
      const body = answer?.body ?? { detail: { code: "NOT_FOUND", message: `${method} ${path}` } };
      return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
    }),
  );
  return gets;
}

/** Wait until no request was sent for a while: the page has finished loading. */
async function settled(gets: string[]): Promise<void> {
  let seen = -1;
  let quiet = 0;
  for (let i = 0; i < 100 && quiet < 4; i += 1) {
    await new Promise((r) => setTimeout(r, 50));
    if (gets.length === seen) quiet += 1;
    else {
      seen = gets.length;
      quiet = 0;
    }
  }
}

function repeated(gets: string[]): string[] {
  const counts = new Map<string, number>();
  for (const g of gets) counts.set(g, (counts.get(g) ?? 0) + 1);
  return [...counts].filter(([, n]) => n > 1).map(([g, n]) => `${g} ×${n}`);
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

const withBar = (page: ReactElement, pathname: string) => (
  <>
    <NextStepBar locale="en" pathname={pathname} />
    {page}
  </>
);

const PAGES: Array<[string, () => ReactElement, string?]> = [
  ["Screening home", () => withBar(<ScreeningHome locale="en" />, "/en/screening/home")],
  ["Screening import", () => withBar(<ScreeningImport locale="en" />, "/en/screening/import")],
  ["Screening prepare", () => withBar(<ScreeningPrepare locale="en" />, "/en/screening/prepare")],
  ["Screening proposals", () => withBar(<ScreeningProposals locale="en" />, "/en/screening/proposals")],
  ["Screening triage", () => <TriagePage locale="en" />],
  ["Screening agreement", () => withBar(<ScreeningAgreement locale="en" />, "/en/screening/agreement")],
  ["Screening publish", () => withBar(<ScreeningPublish locale="en" />, "/en/screening/publish")],
  ["Screening export", () => withBar(<ScreeningExport locale="en" />, "/en/screening/export")],
  ["Screening pilot", () => withBar(<ScreeningPilot locale="en" />, "/en/screening/pilot")],
  ["Charting table", () => <ChartingPage locale="en" />],
  ["Charting one study", () => <ChartingStudyPage locale="en" />, `/en/charting/study?id=${ENGINE.study}`],
  ["Workspaces", () => <WorkspacesScreen locale="en" />],
];

describe("page-requests: every page sends each GET once while it loads", () => {
  it.each(PAGES)("%s", async (_name, page, address) => {
    if (address) window.history.replaceState({}, "", address);
    const gets = engine();
    render(page());
    await settled(gets);
    expect(gets.length).toBeGreaterThan(0);
    expect(repeated(gets)).toEqual([]);
  });

  it("DoD 5: Screening home asks for the corpus once (the steps bar and the page share it)", async () => {
    const gets = engine();
    render(withBar(<ScreeningHome locale="en" />, "/en/screening/home"));
    await settled(gets);
    expect(gets.filter((g) => g === "/api/v1/screening/corpus")).toHaveLength(1);
    expect(gets.filter((g) => g === "/api/v1/review/next-step")).toHaveLength(1);
  });

  it("Publish asks for every batch's review in one request", async () => {
    const gets = engine();
    render(<ScreeningPublish locale="en" />);
    await settled(gets);
    expect(gets.filter((g) => g === "/api/v1/screening/ui/batches/review")).toHaveLength(1);
    expect(gets.filter((g) => /\/ui\/batch\/\d+\/review$/.test(g))).toEqual([]);
  });
});
