import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { spawn, type ChildProcess } from "node:child_process";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LIVE_CHROME, ScreeningPage } from "@/components/screening-page";
import { SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { demoScreeningRecord } from "@/lib/mock-screening";
import { CATALOGS } from "@/messages";

/**
 * The live/fixture read wiring, in process (HCM-06, UI-07 presentation only).
 *
 * The default stays the demonstration record: no request, no storage write,
 * no submit. `?source=live` swaps the record and criteria sections for data
 * read from the console through `@/lib/screening-api`, with the live stamp
 * marking exactly which block is live so the two sources can never be
 * confused. Approval, mutation, and publishing are out of scope: the form
 * keeps submitting nowhere in both modes.
 *
 * The last test boots a real console over real HTTP on loopback and renders
 * the live panel against it end to end; everything before it stubs `fetch`
 * at the network boundary with shape-conformant payloads. No browser is
 * needed for any of this: the rendered-DOM claims are jsdom's, and the
 * rendered-in-Chromium claims stay with `tests-browser/` and the closure
 * tester.
 */

const CONSOLE = "http://127.0.0.1:1899";

const LIVE_SUMMARY = {
  shape: "ui07.project-summary-v1",
  workspace_id: "WSP-ffffffffffffffffffffffffffffffff",
  project_id: "ui-live-demo",
  protocol: { present: true, fingerprint: "sha256:live" },
  run: { screening_run_id: "RUN-UI-LIVE-1", batches: 1, batches_resolved: 1 },
  readiness: {
    screening_prepared: true,
    all_batches_resolved: true,
    publication: {
      shape: "ui07.publication-status-v1",
      status: "CURRENT",
      code: null,
      generation_id: "GEN-UI-LIVE-1",
      outputs: { "included.json": "sha256:live" },
      message: "screening generation is current",
      details: { generation_id: "GEN-UI-LIVE-1" },
    },
  },
  missing: [],
};

const LIVE_BATCHES = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-UI-LIVE-1",
  count: 1,
  batches: [
    {
      batch_index: 0,
      batch_file: "batch_000.json",
      items: 2,
      decisions_file: "batch_000_decisions.json",
      decisions_count: 2,
      collected: false,
      coverage: "COMPLETE",
      unresolved_rows: [],
    },
  ],
  missing: [],
};

const LIVE_PUBLICATION = {
  shape: "ui07.publication-status-v1",
  status: "CURRENT",
  code: null,
  generation_id: "GEN-UI-LIVE-1",
  outputs: { "included.json": "sha256:live" },
  message: "screening generation is current",
  details: { generation_id: "GEN-UI-LIVE-1" },
};

const LIVE_ROWS = {
  shape: "ui07.screening-rows-v1",
  batch_index: 0,
  batch_file: "batch_000.json",
  total: 2,
  offset: 0,
  limit: 100,
  rows: [
    {
      shape: "ui07.screening-row-v1",
      study_id: "STUDY-UI-LIVE-001",
      workspace_id: "WSP-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      citation: "Live Author A. A live read of console batch data. J Live; 2025.",
      abstract: "Live abstract one, served exactly as stored.",
      decision: "INCLUDE",
      reasons: ["Matches the population criterion."],
      uncertainty: "confidence 0.9",
      criterion_refs: { inclusion: ["INC-01"], exclusion: [] },
      source_locators: { doi: "10.0000/live1" },
    },
    {
      shape: "ui07.screening-row-v1",
      study_id: "STUDY-UI-LIVE-002",
      workspace_id: "WSP-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      citation: "Live Author B. A second live read of console batch data. J Live; 2025.",
      abstract: "Live abstract two, served exactly as stored.",
      decision: "EXCLUDE",
      reasons: ["No comparator arm."],
      uncertainty: "confidence 0.8",
      criterion_refs: { inclusion: [], exclusion: ["EXC-02"] },
      source_locators: { doi: "10.0000/live2" },
    },
  ],
  missing: [],
};

const LIVE_REFS = {
  shape: "ui07.criterion-refs-v1",
  protocol_fingerprint: "sha256:live",
  inclusion: [{ id: "INC-01", text: "Names the population and outcome." }],
  exclusion: [{ id: "EXC-02", text: "No comparator arm." }],
  sources: [
    { workspace_id: "WSP-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", doi: "10.0000/live1" },
    { workspace_id: "WSP-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", doi: "10.0000/live2" },
  ],
  missing: [],
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function typedRefusal(code: string, message: string, status: number): Response {
  return jsonResponse({ detail: { code, message, details: {} } }, status);
}

/** Route a stubbed fetch at the five live endpoints used by the panel. */
function stubLiveFetch(
  overrides?: Partial<Record<string, Response | ((url: string) => Response)>>,
): (input: unknown) => Promise<Response> {
  const table: Record<string, Response | ((url: string) => Response)> = {
    "/api/v1/ui/project-summary": jsonResponse(LIVE_SUMMARY),
    "/api/v1/screening/ui/batches": jsonResponse(LIVE_BATCHES),
    "/api/v1/ui/publication-status": jsonResponse(LIVE_PUBLICATION),
    "/api/v1/screening/ui/batch/0/rows": jsonResponse(LIVE_ROWS),
    "/api/v1/screening/ui/batch/0/criterion-refs": jsonResponse(LIVE_REFS),
    ...overrides,
  };
  return async (input: unknown) => {
    const url = String(input);
    const path = (url.replace(/^https?:\/\/[^/]+/, "").replace(/^\/api\/console/, "")).split("?")[0] ?? url;
    const entry = table[path];
    if (typeof entry === "function") return entry(url);
    if (entry) return entry.clone();
    return typedRefusal("BATCH_MISSING", `missing file: ${path}`, 404);
  };
}

function setQuery(query: string): void {
  window.history.replaceState({}, "", `/en/screening${query}`);
}

afterEach(() => {
  window.history.replaceState({}, "", "/en/screening");
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("fixture mode is the default and stays request-free", () => {
  it("renders the demonstration record and sends no request", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);

    render(<ScreeningPage locale="en" />);

    expect(screen.getByText(demoScreeningRecord.citation)).toBeInTheDocument();
    expect(screen.queryByText(LIVE_CHROME.en.liveStamp)).toBeNull();
    await waitFor(() => expect(fetchSpy).not.toHaveBeenCalled());
    expect(storageSpy).not.toHaveBeenCalled();
  });

  it("ignores a non-live source value without requesting", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery("?source=fixture");

    render(<ScreeningPage locale="en" />);

    expect(screen.getByText(demoScreeningRecord.citation)).toBeInTheDocument();
    await waitFor(() => expect(fetchSpy).not.toHaveBeenCalled());
  });
});

describe("live mode renders console data and never the fixture", () => {
  it("marks the live block and shows real batch rows", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLiveFetch()));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);

    // The live stamp is the visible distinction (HCM06-07): heading plus the
    // reinforcement marker, both carrying the same live wording.
    const heading = await screen.findByRole("heading", { name: LIVE_CHROME.en.liveStamp });
    expect(heading.tagName).toBe("H2");
    expect(screen.getByText(LIVE_CHROME.en.liveLede)).toBeInTheDocument();

    // Real batch data, end to end through the typed client shapes.
    expect(await screen.findByText(LIVE_ROWS.rows[0]?.citation ?? "")).toBeInTheDocument();
    expect(screen.getByText(LIVE_ROWS.rows[1]?.abstract ?? "")).toBeInTheDocument();
    // Each row carries the stored decision text and its draft editor offers the
    // same two labels, so presence is asserted rather than a unique match.
    expect(screen.getAllByText(CATALOGS.en["screening.decision.include"]).length).toBeGreaterThan(0);
    expect(screen.getAllByText(CATALOGS.en["screening.decision.exclude"]).length).toBeGreaterThan(0);

    // Fixture/live confusion is refused in both directions: the demonstration
    // citation is gone, and the live stamp was absent in fixture mode above.
    expect(screen.queryByText(demoScreeningRecord.citation)).toBeNull();
    for (const criterion of demoScreeningRecord.criteria) {
      expect(screen.queryByText(criterion)).toBeNull();
    }
  });

  it("defaults ?source=live to the same-origin console proxy when no console is named", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery("?source=live");

    render(<ScreeningPage locale="en" />);

    expect(await screen.findByText(LIVE_ROWS.rows[0]?.citation ?? "")).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalled();
    for (const call of fetchSpy.mock.calls) {
      expect(String(call[0])).toMatch(/^\/api\/console\//);
    }
  });

  it("keeps technical identifiers inspectable, not primary navigation", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLiveFetch()));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);

    const disclosure = await screen.findByText(LIVE_CHROME.en.liveTechIds);
    expect(disclosure.tagName).toBe("SUMMARY");
    expect(disclosure.closest("details")).not.toBeNull();
    // Served identifiers render exactly, isolated for direction.
    expect(screen.getByText("WSP-ffffffffffffffffffffffffffffffff")).toBeInTheDocument();
    expect(screen.getByText("batch_000.json")).toBeInTheDocument();
    // The generation id is inspectable twice: the publication summary line
    // and the technical-identifiers disclosure. Both are data, neither is nav.
    expect(screen.getAllByText("GEN-UI-LIVE-1")).toHaveLength(2);
  });

  it("renders loading while the console has not answered", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);

    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent(CATALOGS.en["overview.recordLoading"]);
    expect(screen.queryByText(demoScreeningRecord.citation)).toBeNull();
  });

  it("renders an empty console explicitly, with the missing reason", async () => {
    vi.stubGlobal(
      "fetch",
      stubLiveFetch({
        "/api/v1/screening/ui/batches": jsonResponse({
          shape: "ui07.screening-batches-v1",
          run_id: null,
          count: 0,
          batches: [],
          missing: [{ file: "literature/screening/MANIFEST.json", reason: "NOT_PREPARED" }],
        }),
      }),
    );
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);

    expect(await screen.findByText(LIVE_CHROME.en.liveEmpty)).toBeInTheDocument();
    expect(screen.getByText("NOT_PREPARED")).toBeInTheDocument();
  });

  it("refuses an invalid console origin without requesting", async () => {
    const fetchSpy = vi.fn(stubLiveFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery("?source=live&console=ftp://example.invalid/console");

    render(<ScreeningPage locale="en" />);

    expect(await screen.findByText("INVALID_CONSOLE_ORIGIN")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe("live error states carry the typed refusal, never invented values", () => {
  for (const [title, path, refusal, status] of [
    ["missing batches", "/api/v1/screening/ui/batches", "BATCH_MISSING", 404],
    ["stale generation", "/api/v1/ui/publication-status", "GENERATION_STALE", 409],
    ["refused identity", "/api/v1/ui/project-summary", "CALLER_IDENTITY_REFUSED", 422],
  ] as const) {
    it(`explains ${title} (${refusal})`, async () => {
      vi.stubGlobal(
        "fetch",
        stubLiveFetch({ [path]: typedRefusal(refusal, `Illustrative ${refusal} from the console.`, status) }),
      );
      setQuery(`?source=live&console=${CONSOLE}`);

      render(<ScreeningPage locale="en" />);

      expect(await screen.findByText(LIVE_CHROME.en.liveUnavailable)).toBeInTheDocument();
      expect(screen.getByText(refusal)).toBeInTheDocument();
      expect(screen.queryByText(demoScreeningRecord.citation)).toBeNull();
    });
  }

  it("names an unreachable console instead of hanging silently", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);

    expect(await screen.findByText("CONSOLE_UNREACHABLE")).toBeInTheDocument();
  });

  it("names malformed console bytes instead of rendering them", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{not json", { status: 200 })));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);

    expect(await screen.findByText("MALFORMED_JSON")).toBeInTheDocument();
  });

  it("only ever sends GET, and writes no browser storage", async () => {
    const methods: string[] = [];
    const handler = stubLiveFetch();
    const fetchSpy = vi.fn(async (input: unknown, init?: RequestInit) => {
      methods.push(init?.method ?? "GET");
      return handler(input);
    });
    vi.stubGlobal("fetch", fetchSpy);
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);
    await screen.findByText(LIVE_ROWS.rows[0]?.citation ?? "");

    expect(fetchSpy).toHaveBeenCalled();
    expect(new Set(methods)).toEqual(new Set(["GET"]));
    expect(storageSpy).not.toHaveBeenCalled();
  });
});

describe("live chrome is localised without touching the catalogs", () => {
  it("carries all five live strings in every locale, none of them English in translation", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const chrome = LIVE_CHROME[locale];
      expect(Object.keys(chrome).sort()).toEqual([
        "liveEmpty",
        "liveLede",
        "liveStamp",
        "liveTechIds",
        "liveUnavailable",
      ]);
      for (const value of Object.values(chrome)) {
        expect(value.trim()).not.toBe("");
      }
    }
    for (const locale of SUPPORTED_LOCALES.filter((code) => code !== "en")) {
      for (const key of Object.keys(LIVE_CHROME.en) as (keyof typeof LIVE_CHROME.en)[]) {
        expect(LIVE_CHROME[locale][key]).not.toBe(LIVE_CHROME.en[key]);
      }
    }
  });

  it("renders the live stamp in the requested locale", async () => {
    for (const locale of SUPPORTED_LOCALES) {
      const typedLocale = locale as Locale;
      vi.stubGlobal("fetch", vi.fn(stubLiveFetch()));
      setQuery(`?source=live&console=${CONSOLE}`);

      render(<ScreeningPage locale={typedLocale} />);
      expect(await screen.findByRole("heading", { name: LIVE_CHROME[typedLocale].liveStamp })).toBeInTheDocument();

      cleanup();
      window.history.replaceState({}, "", "/en/screening");
      vi.unstubAllGlobals();
    }
  });
});

describe("live mode against a real console over real HTTP", () => {
  it(
    "renders served batch data end to end from a synthetic registered workspace",
    async () => {
      const repoRoot = resolve(import.meta.dirname, "..", "..", "..");
      const ws = mkdtempSync(join(tmpdir(), "hcm06-ui-live-"));
      const wsId = "WSP-eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
      const screening = join(ws, "literature", "screening");
      mkdirSync(screening, { recursive: true });
      mkdirSync(join(ws, "audit"), { recursive: true });
      writeFileSync(
        join(ws, "project.json"),
        JSON.stringify({ project_id: "ui-live", registered_workspace_id: wsId }),
      );
      writeFileSync(
        join(ws, "protocol.json"),
        JSON.stringify({ note: "synthetic protocol the canonical fingerprint cannot resolve" }),
      );
      writeFileSync(
        join(screening, "MANIFEST.json"),
        JSON.stringify({
          screening_run_id: "RUN-UI-HTTP-1",
          total_papers: 1,
          batch_size: 1,
          total_batches: 1,
          batches: [
            {
              batch_index: 0,
              file: "batch_000.json",
              decisions_file: "batch_000_decisions.json",
              paper_count: 1,
              status: "DONE",
            },
          ],
        }),
      );
      writeFileSync(
        join(screening, "batch_000.json"),
        JSON.stringify({
          batch_index: 0,
          papers: [
            {
              workspace_id: "SCI-000001",
              citation: "HTTP Author. Served over real HTTP from a synthetic workspace. J HTTP; 2026.",
              abstract: "HTTP abstract, served exactly as stored.",
              venue: "J HTTP",
              year: 2026,
              doi: "10.0000/http",
            },
          ],
        }),
      );
      writeFileSync(
        join(screening, "batch_000_decisions.json"),
        JSON.stringify({
          batch: 0,
          decisions: [
            {
              workspace_id: "SCI-000001",
              decision: "INCLUDE",
              screening_reasoning: "Matches over the wire.",
            },
          ],
          reviewed_by: "hcm06-http",
          timestamp: "2026-10-13T00:00:00+00:00",
        }),
      );
      writeFileSync(join(ws, "audit", "journal.jsonl"), "");

      const port = 18999;
      const origin = `http://127.0.0.1:${port}`;
      let child: ChildProcess | null = null;
      try {
        child = spawn("uv", ["run", "scholar-harness", "serve", "--workspace", ws, "--port", String(port)], {
          cwd: repoRoot,
          stdio: "ignore",
          shell: false,
        });
        const ready = await waitForConsole(`${origin}/healthz`, 90000);
        expect(ready).toBe(true);

        setQuery(`?source=live&console=${origin}`);
        render(<ScreeningPage locale="en" />);

        expect(
          await screen.findByText("HTTP Author. Served over real HTTP from a synthetic workspace. J HTTP; 2026.", {}, { timeout: 30000 }),
        ).toBeInTheDocument();
        expect(screen.getByText("LEGACY_UNVERIFIED")).toBeInTheDocument();
        expect(screen.getByText(wsId)).toBeInTheDocument();
        expect(screen.queryByText(demoScreeningRecord.citation)).toBeNull();
      } finally {
        if (child !== null) {
          child.kill();
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }
    },
    150000,
  );
});

async function waitForConsole(url: string, budgetMs: number): Promise<boolean> {
  const started = Date.now();
  while (Date.now() - started < budgetMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return true;
    } catch {
      // The server is still starting; keep polling inside the budget.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return false;
}

describe("headings and landmarks survive the wiring", () => {
  it("keeps h1 → h2 with no main of its own in fixture mode", () => {
    const { container } = render(<ScreeningPage locale="en" />);
    expect(container.querySelector("main")).toBeNull();
    expect(screen.getAllByRole("heading").map((heading) => heading.tagName)).toEqual([
      "H1",
      "H2",
      "H2",
      "H2",
    ]);
  });

  it("keeps the live panel inside one h2 under the same h1", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLiveFetch()));
    setQuery(`?source=live&console=${CONSOLE}`);

    const { container } = render(<ScreeningPage locale="en" />);
    await screen.findByRole("heading", { name: LIVE_CHROME.en.liveStamp });

    expect(container.querySelector("main")).toBeNull();
    expect(screen.getAllByRole("heading").map((heading) => heading.tagName)).toEqual(["H1", "H2", "H2"]);
    // One ordered list only: the live criteria. The demonstration criteria
    // list is replaced, never doubled.
    expect(container.querySelectorAll("ol")).toHaveLength(1);
  });
});
