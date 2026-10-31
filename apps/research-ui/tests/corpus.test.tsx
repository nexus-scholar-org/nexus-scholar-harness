import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CORPUS_CHROME, CorpusPage } from "@/components/corpus-page";
import { SUPPORTED_LOCALES } from "@/i18n";
import { CATALOGS } from "@/messages";
import type { CorpusRecord } from "@/lib/screening-api";

/**
 * The corpus screen, in process (packet UI-08, paged reads).
 *
 * What these tests hold down:
 *
 * 1. the default is the demonstration corpus and it sends no request;
 * 2. filtering narrows only the loaded rows and never triggers a read;
 * 3. the headline counts are the ones the harness reported, even when the page
 *    has loaded fewer rows than that count - the page must not count its own
 *    list and call it the corpus;
 * 4. the excluded set is not requested until the reader asks for it;
 * 5. in live mode the filter is applied by the console (a `q` parameter) and
 *    "show more" asks for the next offset instead of re-downloading the set;
 * 6. a refused read shows the server code instead of an empty corpus, and
 *    never falls back to the demonstration rows;
 * 7. every request is a GET.
 *
 * The rendered-DOM claims are jsdom's. Chromium capture stays in
 * `tests-browser/`.
 */

const CONSOLE = "http://127.0.0.1:1899";

const LIVE_STATUS = {
  workspace: "/tmp/ws",
  title: "Live corpus workspace",
  phase: "PHASE_1_HARVESTING",
  discovered_count: 14413,
  deduped_count: 14150,
  verified_count: 0,
  included_count: 644,
  excluded_count: 13506,
};

const LIVE_PUBLICATION = {
  shape: "ui07.publication-status-v1",
  status: "LEGACY_UNVERIFIED",
  code: "GENERATION_LEGACY_UNVERIFIED",
  generation_id: null,
  outputs: {},
  message: "no publication generation is recorded",
  details: {},
};

function record(overrides: Partial<CorpusRecord> & { workspace_id: string }): CorpusRecord {
  return {
    shape: "ui07.corpus-record-v1",
    title: null,
    year: null,
    provider: null,
    doi: null,
    abstract: null,
    decision: "INCLUDE",
    confidence: null,
    reasoning: null,
    reason_code: null,
    criterion: null,
    lane: null,
    ...overrides,
  };
}

const LIVE_INCLUDED: CorpusRecord[] = [
  record({
    workspace_id: "SCI-LIVE-001",
    title: "Live included record one",
    year: 2024,
    provider: "crossref",
    abstract: "Stored abstract one.",
    decision: "INCLUDE",
    confidence: 0.9,
    reasoning: "stored reason",
    reason_code: "INC-01",
    criterion: "INC-01",
    lane: "mutual_include",
  }),
];

// More rows than one page, so "show more" has something to ask for.
const MANY_INCLUDED: CorpusRecord[] = Array.from({ length: 60 }, (_, index) =>
  record({
    workspace_id: `SCI-PAGE-${String(index + 1).padStart(3, "0")}`,
    title: index === 41 ? "The only yield row in this page set" : `Paged included record ${index + 1}`,
    year: 2020 + (index % 5),
    provider: "openalex",
    decision: "INCLUDE",
    reason_code: "INC-01",
    criterion: "INC-01",
  }),
);

const LIVE_EXCLUDED: CorpusRecord[] = [
  record({
    workspace_id: "SCI-LIVE-002",
    title: "Live excluded record two",
    year: 2021,
    provider: "openalex",
    abstract: "Stored abstract two.",
    decision: "EXCLUDE",
    confidence: 0.8,
    reasoning: "stored reason",
    reason_code: "WRONG_TASK",
    criterion: "EXC-02",
    lane: "mutual_exclude",
  }),
];

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function typedRefusal(code: string, message: string, status: number): Response {
  return jsonResponse({ detail: { code, message, details: {} } }, status);
}

function setQuery(query: string) {
  window.history.replaceState({}, "", `/en/corpus${query}`);
}

/** The console's paging contract, reproduced faithfully enough for the screen. */
function corpusPageResponse(kind: "included" | "excluded", records: CorpusRecord[], url: string) {
  const params = new URL(url).searchParams;
  const q = (params.get("q") ?? "").trim().toLowerCase();
  const reason = (params.get("reason") ?? "").trim().toUpperCase();
  const limit = Number(params.get("limit") ?? 25);
  const offset = Number(params.get("offset") ?? 0);
  const matched = records.filter((row) => {
    if (reason && (row.reason_code ?? "").toUpperCase() !== reason && (row.criterion ?? "").toUpperCase() !== reason) {
      return false;
    }
    if (q === "") return true;
    return [row.title, row.workspace_id, row.provider, row.reason_code, row.criterion, row.year]
      .join(" ")
      .toLowerCase()
      .includes(q);
  });
  return jsonResponse({
    shape: "ui07.corpus-page-v1",
    kind,
    total: matched.length,
    corpus_total: records.length,
    offset,
    limit,
    records: matched.slice(offset, offset + limit),
    missing: [],
  });
}

function stubLiveFetch(
  overrides?: Partial<Record<string, Response>>,
  includedRows: CorpusRecord[] = LIVE_INCLUDED,
): (input: unknown, init?: RequestInit) => Promise<Response> {
  return (input: unknown) => {
    const url = String(input);
    const uri = new URL(url);
    const overridden = overrides?.[uri.pathname];
    if (overridden) return Promise.resolve(overridden);
    if (uri.pathname === "/api/v1/workspace/status") {
      return Promise.resolve(jsonResponse(LIVE_STATUS));
    }
    if (uri.pathname === "/api/v1/ui/publication-status") {
      return Promise.resolve(jsonResponse(LIVE_PUBLICATION));
    }
    if (uri.pathname === "/api/v1/ui/corpus/included") {
      return Promise.resolve(corpusPageResponse("included", includedRows, url));
    }
    if (uri.pathname === "/api/v1/ui/corpus/excluded") {
      return Promise.resolve(corpusPageResponse("excluded", LIVE_EXCLUDED, url));
    }
    return Promise.reject(new Error(`unexpected read: ${uri.pathname}`));
  };
}

function paths(fetchSpy: ReturnType<typeof vi.fn>): string[] {
  return fetchSpy.mock.calls.map(([url]) => new URL(String(url)).pathname);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setQuery("");
});

describe("corpus screen — demonstration corpus", () => {
  it("renders the fixture rows and sends no request", () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);

    render(<CorpusPage locale="en" />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      CATALOGS.en["corpus.heading"],
    );
    expect(screen.getByText("Aerial imagery for crop and weed separation: an example method study")).toBeInTheDocument();
    expect(screen.getByText("A review of field robotics for weed control")).toBeInTheDocument();
    expect(screen.getByText(CATALOGS.en["corpus.fixtureLede"])).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("filters only the loaded rows and still sends no request", () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);

    render(<CorpusPage locale="en" />);

    fireEvent.change(screen.getByLabelText(CATALOGS.en["corpus.filterLabel"]), {
      target: { value: "review" },
    });

    expect(screen.getByText("A review of field robotics for weed control")).toBeInTheDocument();
    expect(
      screen.queryByText("Aerial imagery for crop and weed separation: an example method study"),
    ).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("states the stored reason and criterion for a row without inventing one", () => {
    render(<CorpusPage locale="en" />);

    expect(screen.getAllByText("WRONG_REPORT_TYPE").length).toBeGreaterThan(0);
    expect(screen.getAllByText("EXC-03").length).toBeGreaterThan(0);
  });
});

describe("corpus screen — live source", () => {
  it("reports the harness counts even though only one page is loaded", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLiveFetch()));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() =>
      expect(screen.getByText(CORPUS_CHROME.en.liveStamp, { selector: "h2" })).toBeInTheDocument(),
    );
    await waitFor(() => expect(screen.getByText("Live included record one")).toBeInTheDocument());

    const counts = screen.getByRole("heading", { name: CATALOGS.en["corpus.countsHeading"] })
      .closest("section") as HTMLElement;
    expect(within(counts).getByText("644")).toBeInTheDocument();
    expect(within(counts).getByText("13506")).toBeInTheDocument();
    expect(screen.getByText("Live included record one")).toBeInTheDocument();
  });

  it("asks the console for one page, not the whole corpus", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Live included record one")).toBeInTheDocument());

    const pageCall = fetchSpy.mock.calls
      .map(([url]) => new URL(String(url)))
      .find((url) => url.pathname === "/api/v1/ui/corpus/included");
    expect(pageCall?.searchParams.get("limit")).toBe("25");
    expect(pageCall?.searchParams.get("offset")).toBe("0");
    expect(pageCall?.searchParams.get("q")).toBeNull();
  });

  it("reads the excluded set only when the reader asks for it", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Live included record one")).toBeInTheDocument());
    expect(screen.queryByText("Live excluded record two")).not.toBeInTheDocument();
    expect(paths(fetchSpy)).not.toContain("/api/v1/ui/corpus/excluded");

    fireEvent.click(screen.getByRole("button", { name: CATALOGS.en["corpus.loadExcluded"] }));

    await waitFor(() => expect(screen.getByText("Live excluded record two")).toBeInTheDocument());
    expect(paths(fetchSpy)).toContain("/api/v1/ui/corpus/excluded");
  });

  it("lets the console filter, one request per settled query", async () => {
    const fetchSpy = vi.fn(stubLiveFetch(undefined, MANY_INCLUDED));
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Paged included record 1")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(CATALOGS.en["corpus.filterLabel"]), {
      target: { value: "yield" },
    });

    await waitFor(() =>
      expect(screen.getByText("The only yield row in this page set")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Paged included record 1")).not.toBeInTheDocument();

    const filters = fetchSpy.mock.calls
      .map(([url]) => new URL(String(url)))
      .filter((url) => url.pathname === "/api/v1/ui/corpus/included")
      .map((url) => url.searchParams.get("q"));
    expect(filters).toContain("yield");
    // Page 0 is re-cut by the console; the screen never filters a full download.
    const filtered = fetchSpy.mock.calls
      .map(([url]) => new URL(String(url)))
      .filter((url) => url.pathname === "/api/v1/ui/corpus/included" && url.searchParams.get("q") === "yield");
    expect(filtered.every((url) => url.searchParams.get("offset") === "0")).toBe(true);
  });

  it("appends the next offset on show more", async () => {
    const fetchSpy = vi.fn(stubLiveFetch(undefined, MANY_INCLUDED));
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Paged included record 1")).toBeInTheDocument());
    expect(screen.queryByText("Paged included record 26")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: CATALOGS.en["corpus.showMore"] }));

    await waitFor(() => expect(screen.getByText("Paged included record 26")).toBeInTheDocument());
    // The first page stays on screen: show more appends, never replaces.
    expect(screen.getByText("Paged included record 1")).toBeInTheDocument();

    const offsets = fetchSpy.mock.calls
      .map(([url]) => new URL(String(url)))
      .filter((url) => url.pathname === "/api/v1/ui/corpus/included")
      .map((url) => url.searchParams.get("offset"));
    expect(offsets).toContain("25");
  });

  it("shows the server's typed code when the read is refused", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        stubLiveFetch({
          "/api/v1/ui/corpus/included": typedRefusal(
            "GENERATION_STALE",
            "the publication generation is stale",
            409,
          ),
        }),
      ),
    );
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("GENERATION_STALE")).toBeInTheDocument());
    expect(screen.getByText(CORPUS_CHROME.en.liveUnavailable)).toBeInTheDocument();
    // A refused live read must never fall back to the demonstration rows.
    expect(screen.queryByText("Aerial imagery for crop and weed separation: an example method study")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: CATALOGS.en["corpus.countsHeading"] })).not.toBeInTheDocument();
  });

  it("issues GET reads only, and none of them a legacy corpus dump", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Live included record one")).toBeInTheDocument());

    for (const [, init] of fetchSpy.mock.calls) {
      expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
    }
    expect(paths(fetchSpy).sort()).toEqual([
      "/api/v1/ui/corpus/included",
      "/api/v1/ui/publication-status",
      "/api/v1/workspace/status",
    ]);
    expect(paths(fetchSpy)).not.toContain("/api/v1/literature/included");
    expect(paths(fetchSpy)).not.toContain("/api/v1/literature/excluded");
  });

  it("renders every supported locale without a missing key", () => {
    for (const locale of SUPPORTED_LOCALES) {
      render(<CorpusPage locale={locale} />);
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        CATALOGS[locale]["corpus.heading"],
      );
      cleanup();
    }
  });
});
