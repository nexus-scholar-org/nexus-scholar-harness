import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { mkdtempSync } from "node:fs";
import { execFileSync, spawn, type ChildProcess } from "node:child_process";
import { tmpdir } from "node:os";
import { delimiter, join, resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LINEAGE_CHROME, LineagePage, demoLineageNodes } from "@/components/lineage-trace";
import { LocaleDocument } from "@/components/locale-document";
import { SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CATALOGS } from "@/messages";
import type { LineageTrace } from "@/lib/screening-api";

vi.mock("next/navigation", () => ({
  usePathname: () => "/en/lineage",
}));

/**
 * The lineage trace view, in process (UI-05).
 *
 * The default stays the demonstration trace: no request, no storage write.
 * `?source=live` swaps it for a trace read from the console through
 * `@/lib/screening-api`, with the live stamp marking exactly which part is
 * live so the two sources can never be confused. Broken links render the
 * console typed refusal, never a guessed record.
 *
 * The last suite boots a real console over real HTTP on loopback and renders
 * the live trace against it end to end, then proves the server it spawned
 * is gone; everything before it stubs `fetch` at the network boundary with
 * shape-conformant payloads. No browser is needed for any of this: the
 * rendered-DOM claims are jsdom's, and the rendered-in-Chromium claims stay
 * with `tests-browser/` and the closure tester.
 */

const CONSOLE = "http://127.0.0.1:18997";

const LIVE_TRACE: LineageTrace = {
  shape: "ui07.lineage-trace-v1",
  complete: true,
  selector: { claim_id: "CLM-UI-LIVE-1" },
  claims: [
    {
      claim_id: "CLM-UI-LIVE-1",
      claim_text: "Live claim text served exactly as stored.",
      claim_kind: "finding",
      study_ids: ["STU-UI-LIVE-1"],
      evidence_ids: ["EV-UI-LIVE-1"],
      citation_tokens: [
        "[rag:v2:WSP-ffffffffffffffffffffffffffffffff:STU-UI-LIVE-1:CHK-UI-LIVE-1]",
      ],
      chunk_ids: ["CHK-UI-LIVE-1"],
      verification: {
        retrieval: "SOURCE_AVAILABLE",
        lexical_support: "SUPPORTED_VERBATIM",
        entailment: "NOT_ASSESSED",
        trust: "NOT_CHECKED",
      },
      legs: [
        {
          evidence: {
            evidence_id: "EV-UI-LIVE-1",
            quote: "Live quoted passage, served exactly as stored.",
            locator: "Results, paragraph 2",
            study_id: "STU-UI-LIVE-1",
            document_id: "DOC-UI-LIVE-1",
            source_hash: "sha256:live1",
            extraction_method: "HUMAN",
          },
          chunk_ids: ["CHK-UI-LIVE-1"],
          document: {
            document_id: "DOC-UI-LIVE-1",
            study_id: "STU-UI-LIVE-1",
            source_hash: "sha256:live1",
            content_status: "VALID",
            extracted_path: "extracted/live-1.md",
            extraction_method: "DETERMINISTIC_RULE",
          },
          study: {
            study_id: "STU-UI-LIVE-1",
            title: "Live study one, served exactly as stored.",
            alias_ids: ["SCI-000001"],
            external_ids: { doi: ["10.0000/live1"] },
            publication_year: 2025,
          },
          decision: {
            decision_id: "SCR-UI-LIVE-1",
            study_id: "SCI-000001",
            decision: "INCLUDE",
            reason: "Live reason, served exactly as stored.",
            method: "HUMAN",
            screener_id: "ui-live",
            decided_at: "2026-10-14T00:00:00+00:00",
          },
          refusal: null,
        },
      ],
    },
  ],
  publication: {
    shape: "ui07.publication-status-v1",
    status: "CURRENT",
    code: null,
    generation_id: "GEN-UI-LIVE-1",
    outputs: { "included.json": "sha256:live" },
    message: "screening generation is current",
    details: { generation_id: "GEN-UI-LIVE-1" },
  },
  missing: [],
};

function withLegRefusal(
  code: string,
  message: string,
  keep: { document: boolean; study: boolean; decision: boolean },
): LineageTrace {
  const leg = LIVE_TRACE.claims[0]?.legs[0];
  if (!leg) throw new Error("live stub carries no leg");
  return {
    ...LIVE_TRACE,
    complete: false,
    claims: [
      {
        ...LIVE_TRACE.claims[0]!,
        legs: [
          {
            ...leg,
            document: keep.document ? leg.document : null,
            study: keep.study ? leg.study : null,
            decision: keep.decision ? leg.decision : null,
            refusal: { code, message },
          },
        ],
      },
    ],
  };
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function typedRefusal(code: string, message: string, status: number): Response {
  return jsonResponse({ detail: { code, message, details: {} } }, status);
}

/** Route a stubbed fetch at the single live endpoint the view reads. */
function stubLineageFetch(
  respond: (url: string) => Response = () => jsonResponse(LIVE_TRACE),
): (input: unknown) => Promise<Response> {
  return async (input: unknown) => {
    const url = String(input);
    const path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0] ?? url;
    if (path === "/api/v1/ui/lineage") return respond(url).clone();
    return typedRefusal("CLAIM_MISSING", `no recorded claim at ${path}`, 404);
  };
}

function setQuery(query: string): void {
  window.history.replaceState({}, "", `/en/lineage${query}`);
}

afterEach(() => {
  window.history.replaceState({}, "", "/en/lineage");
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("fixture mode is the default and stays request-free", () => {
  it("renders the demonstration trace and sends no request", async () => {
    const fetchSpy = vi.fn(stubLineageFetch());
    vi.stubGlobal("fetch", fetchSpy);
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);

    render(<LineagePage locale="en" />);

    expect(screen.getByText(demoLineageNodes[0]?.label ?? "")).toBeInTheDocument();
    expect(screen.getByText(demoLineageNodes[1]?.detail ?? "")).toBeInTheDocument();
    expect(screen.queryByText(LINEAGE_CHROME.en.liveStamp)).toBeNull();
    await waitFor(() => expect(fetchSpy).not.toHaveBeenCalled());
    expect(storageSpy).not.toHaveBeenCalled();
  });

  it("ignores a non-live source value without requesting", async () => {
    const fetchSpy = vi.fn(stubLineageFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery("?source=fixture");

    render(<LineagePage locale="en" />);

    expect(screen.getByText(demoLineageNodes[0]?.label ?? "")).toBeInTheDocument();
    await waitFor(() => expect(fetchSpy).not.toHaveBeenCalled());
  });

  it("contributes no tab stop of its own in fixture mode", () => {
    render(<LineagePage locale="en" />);

    expect(
      document.body.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])',
      ),
    ).toHaveLength(0);
  });
});

describe("live mode renders the served trace and never the fixture", () => {
  it("marks the live block and shows the complete rail end to end", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(<LineagePage locale="en" />);

    const heading = await screen.findByRole("heading", {
      name: LINEAGE_CHROME.en.liveStamp,
    });
    expect(heading.tagName).toBe("H2");
    expect(screen.getByText(LINEAGE_CHROME.en.liveLede)).toBeInTheDocument();

    const leg = LIVE_TRACE.claims[0]?.legs[0];
    expect(
      await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? ""),
    ).toBeInTheDocument();
    expect(screen.getByText(leg?.evidence?.quote ?? "")).toBeInTheDocument();
    expect(screen.getByText(leg?.evidence?.locator ?? "")).toBeInTheDocument();
    expect(screen.getByText(leg?.document?.extracted_path ?? "")).toBeInTheDocument();
    expect(screen.getByText(leg?.study?.title ?? "")).toBeInTheDocument();
    // The study id is inspectable twice: the rail detail and the
    // technical-identifiers record. Both are data, neither is nav.
    expect(screen.getAllByText(leg?.study?.study_id ?? "")).toHaveLength(2);
    expect(screen.getByText("INCLUDE")).toBeInTheDocument();
    expect(screen.getByText(leg?.decision?.reason ?? "")).toBeInTheDocument();
    expect(screen.getByText("10.0000/live1")).toBeInTheDocument();
    expect(screen.getByText("CURRENT")).toBeInTheDocument();
    expect(screen.getByText("GEN-UI-LIVE-1")).toBeInTheDocument();

    expect(screen.queryByText(demoLineageNodes[0]?.label ?? "")).toBeNull();
  });

  it("orders the rail claim, chunk, document, study, decision", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    const { container } = render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    expect(container.querySelectorAll("li")).toHaveLength(5);
    const leg = LIVE_TRACE.claims[0]?.legs[0];
    expect(
      screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent),
    ).toEqual([
      LIVE_TRACE.claims[0]?.claim_text,
      leg?.evidence?.quote,
      leg?.document?.extracted_path,
      leg?.study?.title,
      leg?.decision?.decision,
    ]);
  });

  it("shows the stored verification axes as annotations, never as scores", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&chunk_id=CHK-UI-LIVE-1`);

    render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    expect(screen.getByText("SOURCE_AVAILABLE")).toBeInTheDocument();
    expect(screen.getByText("SUPPORTED_VERBATIM")).toBeInTheDocument();
    expect(screen.getByText("NOT_ASSESSED")).toBeInTheDocument();
  });

  it("renders every served id, quote, and DOI from the payload and nothing else", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    const { container } = render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    const payloadText = JSON.stringify(LIVE_TRACE);
    const rendered = Array.from(container.querySelectorAll("bdi"))
      .map((element) => element.textContent ?? "")
      .filter((text) => text !== "");
    expect(rendered.length).toBeGreaterThan(10);
    for (const text of rendered) {
      expect(payloadText, `rendered value outside the payload: ${text}`).toContain(text);
    }
  });

  it("keeps technical identifiers inspectable behind disclosures", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    const disclosures = screen.getAllByText(LINEAGE_CHROME.en.techIds);
    expect(disclosures).toHaveLength(2);
    for (const disclosure of disclosures) {
      expect(disclosure.tagName).toBe("SUMMARY");
      expect(disclosure.closest("details")).not.toBeNull();
    }
    expect(screen.getByText("CLM-UI-LIVE-1")).toBeInTheDocument();
    // The evidence id is inspectable twice: the claim record names it and
    // the leg record carries it.
    expect(screen.getAllByText("EV-UI-LIVE-1")).toHaveLength(2);
    // The chunk id is inspectable twice: the claim record and the leg
    // record name the same stored token segment.
    expect(screen.getAllByText("CHK-UI-LIVE-1")).toHaveLength(2);
    expect(screen.getByText("DOC-UI-LIVE-1")).toBeInTheDocument();
    expect(screen.getByText("SCR-UI-LIVE-1")).toBeInTheDocument();
  });
});

describe("broken links render their typed refusal, never a guessed record", () => {
  const liveClaim = LIVE_TRACE.claims[0];
  const liveLeg = liveClaim?.legs[0];
  for (const [title, trace, keptLabels] of [
    [
      "unlinked document",
      withLegRefusal("UNLINKED_DOCUMENT", "Illustrative unlinked document.", {
        document: false,
        study: false,
        decision: false,
      }),
      [liveClaim?.claim_text ?? "", liveLeg?.evidence?.quote ?? ""],
    ],
    [
      "unknown study",
      withLegRefusal("UNKNOWN_STUDY", "Illustrative unknown study.", {
        document: true,
        study: false,
        decision: false,
      }),
      [
        liveClaim?.claim_text ?? "",
        liveLeg?.evidence?.quote ?? "",
        liveLeg?.document?.extracted_path ?? "",
      ],
    ],
    [
      "missing decision",
      withLegRefusal("MISSING_DECISION", "Illustrative missing decision.", {
        document: true,
        study: true,
        decision: false,
      }),
      [
        liveClaim?.claim_text ?? "",
        liveLeg?.evidence?.quote ?? "",
        liveLeg?.document?.extracted_path ?? "",
        liveLeg?.study?.title ?? "",
      ],
    ],
  ] as const) {
    it(`refuses an ${title} leg (${trace.claims[0]?.legs[0]?.refusal?.code})`, async () => {
      vi.stubGlobal("fetch", vi.fn(stubLineageFetch(() => jsonResponse(trace))));
      setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

      const { container } = render(<LineagePage locale="en" />);
      const alert = await screen.findByRole("alert");

      expect(alert).toHaveTextContent(LINEAGE_CHROME.en.refusalTitle);
      expect(alert).toHaveTextContent(trace.claims[0]?.legs[0]?.refusal?.code ?? "");
      expect(alert).toHaveTextContent(
        trace.claims[0]?.legs[0]?.refusal?.message ?? "",
      );
      // The resolved prefix stays with its labels; the missing nodes never appear.
      expect(container.querySelectorAll("li")).toHaveLength(keptLabels.length);
      expect(
        screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent),
      ).toEqual([...keptLabels]);
      expect(screen.queryByText("Live reason, served exactly as stored.")).toBeNull();
      expect(screen.queryByText(demoLineageNodes[0]?.label ?? "")).toBeNull();
    });
  }

  for (const [title, refusal, status] of [
    ["unknown claim", "CLAIM_MISSING", 404],
    ["unknown chunk", "CHUNK_MISSING", 404],
    ["stale generation", "GENERATION_STALE", 409],
    ["refused identity", "CALLER_IDENTITY_REFUSED", 422],
  ] as const) {
    it(`explains an entry-level ${title} (${refusal})`, async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn(
          stubLineageFetch(() =>
            typedRefusal(refusal, `Illustrative ${refusal} from the console.`, status),
          ),
        ),
      );
      setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

      render(<LineagePage locale="en" />);

      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent(LINEAGE_CHROME.en.liveUnavailable);
      expect(alert).toHaveTextContent(refusal);
      expect(screen.queryByText(demoLineageNodes[0]?.label ?? "")).toBeNull();
    });
  }

  it("names an unreachable console instead of hanging silently", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(<LineagePage locale="en" />);

    expect(await screen.findByText("CONSOLE_UNREACHABLE")).toBeInTheDocument();
  });

  it("names malformed console bytes instead of rendering them", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{not json", { status: 200 })));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(<LineagePage locale="en" />);

    expect(await screen.findByText("MALFORMED_JSON")).toBeInTheDocument();
  });

  it("refuses an invalid console origin without requesting", async () => {
    const fetchSpy = vi.fn(stubLineageFetch());
    vi.stubGlobal("fetch", fetchSpy);
    setQuery("?source=live&console=ftp://example.invalid/console&claim_id=x");

    render(<LineagePage locale="en" />);

    expect(await screen.findByText("INVALID_CONSOLE_ORIGIN")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("only ever sends GET, and writes no browser storage", async () => {
    const methods: string[] = [];
    const handler = stubLineageFetch();
    const fetchSpy = vi.fn(async (input: unknown, init?: RequestInit) => {
      methods.push(init?.method ?? "GET");
      return handler(input);
    });
    vi.stubGlobal("fetch", fetchSpy);
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    expect(fetchSpy).toHaveBeenCalled();
    expect(new Set(methods)).toEqual(new Set(["GET"]));
    expect(storageSpy).not.toHaveBeenCalled();
  });
});

describe("live chrome is localised without touching the catalogs", () => {  it("carries all nine lineage strings in every locale, none of them English in translation", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const chrome = LINEAGE_CHROME[locale];
      expect(Object.keys(chrome).sort()).toEqual([
        "eyebrow",
        "heading",
        "lede",
        "liveLede",
        "liveStamp",
        "liveUnavailable",
        "refusalTitle",
        "techIds",
        "traceTitle",
      ]);
      for (const value of Object.values(chrome)) {
        expect(value.trim()).not.toBe("");
      }
    }
    for (const locale of SUPPORTED_LOCALES.filter((code) => code !== "en")) {
      for (const key of Object.keys(LINEAGE_CHROME.en) as (keyof typeof LINEAGE_CHROME.en)[]) {
        expect(LINEAGE_CHROME[locale][key]).not.toBe(LINEAGE_CHROME.en[key]);
      }
    }
  });

  it("renders the live stamp in the requested locale", async () => {
    for (const locale of SUPPORTED_LOCALES) {
      const typedLocale = locale as Locale;
      vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
      setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

      render(<LineagePage locale={typedLocale} />);
      expect(
        await screen.findByRole("heading", { name: LINEAGE_CHROME[typedLocale].liveStamp }),
      ).toBeInTheDocument();

      cleanup();
      window.history.replaceState({}, "", "/en/lineage");
      vi.unstubAllGlobals();
    }
  });
});

describe("fixture and live labels stay distinct through the shell", () => {
  it("shows both the demonstration marker and the live stamp in live mode", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(
      <LocaleDocument locale="en">
        <LineagePage locale="en" />
      </LocaleDocument>,
      { container: document },
    );
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    expect(
      screen.getByRole("heading", { name: LINEAGE_CHROME.en.liveStamp }),
    ).toBeInTheDocument();
    expect(screen.getByText(CATALOGS.en["safety.demoDataLabel"])).toBeInTheDocument();
  });

  it("shows the demonstration marker without any live stamp in fixture mode", () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));

    render(
      <LocaleDocument locale="en">
        <LineagePage locale="en" />
      </LocaleDocument>,
      { container: document },
    );

    expect(screen.getByText(CATALOGS.en["safety.demoDataLabel"])).toBeInTheDocument();
    expect(screen.queryByText(LINEAGE_CHROME.en.liveStamp)).toBeNull();
  });
});

describe("keyboard traversal of the disclosure rail", () => {
  it("tabs through both disclosures, opens one, and walks back without a trap", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    const summaries = screen
      .getAllByText(LINEAGE_CHROME.en.techIds)
      .filter((element) => element.tagName === "SUMMARY");
    expect(summaries).toHaveLength(2);
    const [first, second] = summaries as [HTMLElement, HTMLElement];

    expect(document.body).toHaveFocus();
    await user.tab();
    expect(document.activeElement).toBe(first);
    await user.tab();
    expect(document.activeElement).toBe(second);
    await user.tab();
    expect(document.activeElement).not.toBe(first);
    expect(document.activeElement).not.toBe(second);

    await user.tab({ shift: true });
    expect(document.activeElement).toBe(second);
    await user.tab({ shift: true });
    expect(document.activeElement).toBe(first);

    // Expansion itself is the native disclosure activation, exercised here
    // through its click behavior (jsdom performs no keyboard activation on
    // a summary); reaching and leaving the control above is the keyboard
    // half, and it stays keyboard-only. The second record is the leg one,
    // which is where the decision identifier lives.
    await user.click(second);
    expect(second.closest("details")?.hasAttribute("open")).toBe(true);
    expect(screen.getByText("SCR-UI-LIVE-1")).toBeVisible();
  });
});

describe("in-process accessibility of the new route", () => {
  function blocking(results: axe.AxeResults): axe.Result[] {
    return results.violations.filter(
      (violation) => violation.impact === "critical" || violation.impact === "serious",
    );
  }

  it("reports zero critical and zero serious violations on the fixture trace", async () => {
    const { container } = render(<LineagePage locale="en" />);

    const results = await axe.run(container);

    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);
    expect(blocking(results).map((violation) => violation.id)).toEqual([]);
  });

  it("reports zero critical and zero serious violations on a served trace", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    const { container } = render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    const results = await axe.run(container);

    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);
    expect(blocking(results).map((violation) => violation.id)).toEqual([]);
  });

  it("reports zero critical and zero serious violations on a refused leg", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        stubLineageFetch(() =>
          jsonResponse(
            withLegRefusal("MISSING_DECISION", "Illustrative missing decision.", {
              document: true,
              study: true,
              decision: false,
            }),
          ),
        ),
      ),
    );
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    const { container } = render(<LineagePage locale="en" />);
    await screen.findByRole("alert");

    const results = await axe.run(container);

    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);
    expect(blocking(results).map((violation) => violation.id)).toEqual([]);
  });

  it("control: a deliberately broken image IS reported as a critical violation", async () => {
    const { container } = render(<img src="probe.png" />);

    const results = await axe.run(container);
    const critical = results.violations.filter(
      (violation) => violation.impact === "critical",
    );

    expect(critical.map((violation) => violation.id)).toContain("image-alt");
  });
});

describe("headings and landmarks survive the wiring", () => {
  it("keeps h1 then h2 with no main of its own in fixture mode", () => {
    const { container } = render(<LineagePage locale="en" />);
    expect(container.querySelector("main")).toBeNull();
    expect(screen.getAllByRole("heading").map((heading) => heading.tagName)).toEqual([
      "H1",
      "H2",
      "H3",
      "H3",
      "H3",
      "H3",
      "H3",
    ]);
  });

  it("keeps the live trace inside one h2 under the same h1", async () => {
    vi.stubGlobal("fetch", vi.fn(stubLineageFetch()));
    setQuery(`?source=live&console=${CONSOLE}&claim_id=CLM-UI-LIVE-1`);

    const { container } = render(<LineagePage locale="en" />);
    await screen.findByText(LIVE_TRACE.claims[0]?.claim_text ?? "");

    expect(container.querySelector("main")).toBeNull();
    expect(screen.getAllByRole("heading").map((heading) => heading.tagName)).toEqual([
      "H1",
      "H2",
      "H3",
      "H3",
      "H3",
      "H3",
      "H3",
    ]);
    // One ordered rail only: the served claim, chunk, document, study, decision.
    expect(container.querySelectorAll("ol")).toHaveLength(1);
  });
});

describe("live mode against a real console over real HTTP", () => {
  let child: ChildProcess | null = null;

  /** Stop a spawned console and wait until it is reaped, bounded. */
  async function stopConsole(running: ChildProcess): Promise<void> {
    if (running.exitCode !== null || running.signalCode !== null) return;
    try {
      // `uv run` parents the server: killing the parent alone orphans the
      // listener on Windows, so the whole tree goes (`/T`), by force (`/F`).
      if (process.platform === "win32" && running.pid !== undefined) {
        execFileSync("taskkill", ["/pid", String(running.pid), "/T", "/F"], {
          stdio: "ignore",
        });
      } else {
        running.kill();
      }
    } catch {
      // Already gone; the bounded wait below confirms it.
    }
    const started = Date.now();
    while (
      running.exitCode === null &&
      running.signalCode === null &&
      Date.now() - started < 15000
    ) {
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }

  /** True once no listener answers, bounded; false when one still does. */
  async function waitForPortFree(url: string, budgetMs: number): Promise<boolean> {
    const started = Date.now();
    while (Date.now() - started < budgetMs) {
      try {
        const response = await fetch(url);
        if (!response.ok) return true;
      } catch {
        return true;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    return false;
  }

  afterEach(async () => {
    if (child !== null) {
      const running = child;
      child = null;
      await stopConsole(running);
    }
  });

  it(
    "renders the served trace end to end, then leaves no server behind",
    async () => {
      const repoRoot = resolve(import.meta.dirname, "..", "..", "..");
      const parent = mkdtempSync(join(tmpdir(), "ui05-lineage-live-"));
      const pythonPath = [
        join(repoRoot, "src"),
        join(repoRoot, "tools", "scholar-protocol-kit", "src"),
        join(repoRoot, "tools", "scholar-search-kit", "src"),
        join(repoRoot, "tools", "scholar-pdf-kit", "src"),
        join(repoRoot, "tools", "scholar-bib-kit", "src"),
        join(repoRoot, "tools", "scholar-rag-kit", "src"),
        join(repoRoot, "tools", "scholar-graph-kit", "src"),
        join(repoRoot, "tools", "scholar-agent-kit", "src"),
      ].join(delimiter);
      execFileSync(
        "uv",
        ["run", "python", "tests/console/test_lineage_api.py", "build", parent, "complete"],
        { cwd: repoRoot, env: { ...process.env, PYTHONPATH: pythonPath }, stdio: "ignore" },
      );

      const port = 18997 + (process.pid % 50);
      const origin = `http://127.0.0.1:${port}`;
      try {
        child = spawn(
          "uv",
          ["run", "scholar-harness", "serve", "--workspace", join(parent, "ws"), "--port", String(port)],
          { cwd: repoRoot, stdio: "ignore", shell: false },
        );
        const ready = await waitForConsole(`${origin}/healthz`, 90000);
        expect(ready).toBe(true);

        setQuery(`?source=live&console=${origin}&claim_id=CLM-LIN-1`);
        render(<LineagePage locale="en" />);

        expect(
          await screen.findByText("Structured extraction improves auditability.", {}, { timeout: 30000 }),
        ).toBeInTheDocument();
        expect(screen.getByText("We recorded every decision with its provenance.")).toBeInTheDocument();
        expect(screen.getByText("Methods, paragraph 4")).toBeInTheDocument();
        expect(screen.getByText("10.0000/lineage1")).toBeInTheDocument();
        expect(
          screen.getByText("include during console verification review"),
        ).toBeInTheDocument();
        expect(screen.getByText("CURRENT")).toBeInTheDocument();
        expect(
          screen.getByRole("heading", { name: LINEAGE_CHROME.en.liveStamp }),
        ).toBeInTheDocument();
        expect(
          screen.queryByText(demoLineageNodes[0]?.label ?? ""),
        ).toBeNull();
      } finally {
        if (child !== null) {
          const running = child;
          child = null;
          await stopConsole(running);
          // The spawned console is reaped: the process ended and its port
          // answers nothing afterwards.
          expect(running.exitCode !== null || running.signalCode !== null).toBe(true);
          expect(await waitForPortFree(`${origin}/healthz`, 15000)).toBe(true);
        }
      }
    },
    240000,
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
