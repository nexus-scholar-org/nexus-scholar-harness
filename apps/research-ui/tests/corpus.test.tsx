import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CORPUS_CHROME, CorpusPage } from "@/components/corpus-page";
import { SUPPORTED_LOCALES } from "@/i18n";
import { CATALOGS } from "@/messages";

/**
 * The corpus screen, in process (packet UI-08).
 *
 * What these tests hold down:
 *
 * 1. the default is the demonstration corpus and it sends no request;
 * 2. filtering narrows only the loaded rows and never triggers a read;
 * 3. the headline counts are the ones the harness reported, even when the page
 *    has loaded fewer rows than that count - the page must not count its own
 *    list and call it the corpus;
 * 4. the excluded set is not requested until the reader asks for it;
 * 5. a refused read shows the server code instead of an empty corpus;
 * 6. every request is a GET.
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

const LIVE_INCLUDED = [
  {
    workspace_id: "SCI-LIVE-001",
    title: "Live included record one",
    year: 2024,
    provider: "crossref",
    doi: null,
    abstract: "Stored abstract one.",
    screening: {
      workspace_id: "SCI-LIVE-001",
      decision: "INCLUDE",
      confidence: 0.9,
      screening_reasoning: "stored reason",
      matched_inclusion_criteria: ["INC-01"],
      violated_exclusion_criteria: [],
    },
    screening_provenance: { lane: "mutual_include", reason_code: "INC-01" },
  },
];

const LIVE_EXCLUDED = [
  {
    workspace_id: "SCI-LIVE-002",
    title: "Live excluded record two",
    year: 2021,
    provider: "openalex",
    doi: null,
    abstract: "Stored abstract two.",
    screening: {
      workspace_id: "SCI-LIVE-002",
      decision: "EXCLUDE",
      confidence: 0.8,
      screening_reasoning: "stored reason",
      matched_inclusion_criteria: [],
      violated_exclusion_criteria: ["EXC-02"],
    },
    screening_provenance: { lane: "mutual_exclude", reason_code: "WRONG_TASK" },
  },
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

function stubLiveFetch(
  overrides?: Partial<Record<string, Response>>,
): (input: unknown, init?: RequestInit) => Promise<Response> {
  const table: Record<string, Response> = {
    "/api/v1/workspace/status": jsonResponse(LIVE_STATUS),
    "/api/v1/ui/publication-status": jsonResponse(LIVE_PUBLICATION),
    "/api/v1/literature/included": jsonResponse(LIVE_INCLUDED),
    "/api/v1/literature/excluded": jsonResponse(LIVE_EXCLUDED),
    ...overrides,
  };
  return (input: unknown) => {
    const url = String(input);
    const path = new URL(url).pathname;
    const body = table[path];
    if (!body) return Promise.reject(new Error(`unexpected read: ${path}`));
    return Promise.resolve(body);
  };
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
  it("reports the harness counts even though fewer rows are loaded", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLiveFetch()));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() =>
      expect(screen.getByText(CORPUS_CHROME.en.liveStamp, { selector: "h2" })).toBeInTheDocument(),
    );

    const counts = screen.getByRole("heading", { name: CATALOGS.en["corpus.countsHeading"] })
      .closest("section") as HTMLElement;
    expect(within(counts).getByText("644")).toBeInTheDocument();
    expect(within(counts).getByText("13506")).toBeInTheDocument();
    expect(screen.getByText("Live included record one")).toBeInTheDocument();
  });

  it("reads the excluded set only when the reader asks for it", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Live included record one")).toBeInTheDocument());
    expect(screen.queryByText("Live excluded record two")).not.toBeInTheDocument();
    expect(
      fetchSpy.mock.calls.some(([url]) => String(url).endsWith("/api/v1/literature/excluded")),
    ).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: CATALOGS.en["corpus.loadExcluded"] }));

    await waitFor(() => expect(screen.getByText("Live excluded record two")).toBeInTheDocument());
    expect(
      fetchSpy.mock.calls.some(([url]) => String(url).endsWith("/api/v1/literature/excluded")),
    ).toBe(true);
  });

  it("shows the server's typed code when the read is refused", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        stubLiveFetch({
          "/api/v1/literature/included": typedRefusal(
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

  it("issues GET reads only, and none of them a path outside the corpus surface", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<CorpusPage locale="en" />);

    await waitFor(() => expect(screen.getByText("Live included record one")).toBeInTheDocument());

    for (const [, init] of fetchSpy.mock.calls) {
      expect(init?.method ?? "GET").toBe("GET");
    }
    const paths = fetchSpy.mock.calls.map(([url]) => new URL(String(url)).pathname).sort();
    expect(paths).toEqual([
      "/api/v1/literature/included",
      "/api/v1/ui/publication-status",
      "/api/v1/workspace/status",
    ]);
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
