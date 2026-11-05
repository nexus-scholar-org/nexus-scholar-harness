import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HOME_COPY, ScreeningHome } from "@/components/screening-home";
import { StateCard } from "@/components/screening-state-card";
import { SUPPORTED_LOCALES } from "@/i18n";
import { STATES, stateCopy } from "@/lib/screening-states";

/**
 * Screening home (spec 01) and the state cards (spec 08). The summary is the
 * engine's recorded fixture, so the counts on screen are the engine's counts.
 */

const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;
const body = (name: string) => JSON.parse(readFileSync(`${FIXTURES}${name}.json`, "utf-8")).response.body;

const BATCHES = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-1",
  count: 1,
  batches: [{ batch_index: 1, batch_file: "batch_001.json", items: 3, decisions_file: null, decisions_count: null, collected: false, coverage: "INCOMPLETE", unresolved_rows: [] }],
  missing: [],
};

function engine(overrides: Record<string, unknown> = {}) {
  const routes: Record<string, unknown> = {
    "/summary": { ...body("summary_start"), agent_proposed: 2, lanes: { agent: 2, you: 0, second_screener: "PARKED" } },
    "/ui/batches": BATCHES,
    "/decisions/conflicts": { items: [] },
    "/settings": body("settings_default"),
    ...overrides,
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const answer = routes[path];
      if (answer instanceof Response) return answer;
      return new Response(JSON.stringify(answer ?? { detail: { code: "NOT_FOUND" } }), { status: answer ? 200 : 404, headers: { "content-type": "application/json" } });
    }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("screening-home.summary", () => {
  it("prints the engine's counts and links to triage", async () => {
    engine();
    render(<ScreeningHome locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "0 of 3 records are decided; 3 still need you." });
    expect(screen.getByRole("link", { name: "Open triage · 3 need you" })).toHaveAttribute("href", "/en/screening/triage");
    expect(screen.getByRole("img", { name: "0 of 3 records decided" })).toBeInTheDocument();
    expect(screen.getByText("batch_001.json")).toBeInTheDocument();
  });

  it("shows the protocol-changed card and sends the button to prepare when a batch is stale", async () => {
    engine({ "/ui/batches": { ...BATCHES, batches: [{ ...BATCHES.batches[0], binding: { state: "STALE_BINDING", reason: "x" } }] } });
    render(<ScreeningHome locale="en" />);
    await screen.findByText("STALE_BINDING");
    expect(screen.getByRole("link", { name: "See the change" })).toHaveAttribute("href", "/en/screening/prepare");
    expect(screen.queryByRole("link", { name: /Open triage/ })).toBeNull();
  });

  it("shows the engine's code when it cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("fetch failed"))));
    render(<ScreeningHome locale="en" />);
    // A failed first read replaces the screen, so its title is the page h1.
    await screen.findByText("Engine unreachable", { selector: "h1" });
    expect(screen.getByText("CONSOLE_UNREACHABLE")).toBeInTheDocument();
  });
});

describe("review 6: the engine's code is shown verbatim", () => {
  it("shows SNAPSHOT_NOT_ACCEPTED as itself, not renamed", async () => {
    engine({ "/summary": new Response(JSON.stringify({ detail: { code: "SNAPSHOT_NOT_ACCEPTED", message: "no prepared batches" } }), { status: 409, headers: { "content-type": "application/json" } }) });
    render(<ScreeningHome locale="en" />);
    await screen.findByText("SNAPSHOT_NOT_ACCEPTED");
    expect(screen.queryByText("NOT_PREPARED")).toBeNull();
  });
});

describe("screening-home.no-agent-call-leak", () => {
  it("counts drafts without saying what any draft proposes", async () => {
    engine();
    render(<ScreeningHome locale="en" />);
    await screen.findByText("Records with an agent draft");
    await waitFor(() => expect(document.body.textContent).toContain("2 drafts so far"));
    // The page never requests a draft, and nothing names an agent outcome.
    const calls = (fetch as unknown as { mock: { calls: [string][] } }).mock.calls.map((c) => c[0]);
    expect(calls.some((u) => u.includes("/proposal"))).toBe(false);
    expect(document.body.textContent).not.toMatch(/agent (says|proposes) (include|exclude)/i);
  });
});

describe("screening-home.not-prepared", () => {
  it("does not call an unprepared workspace decided (golden run)", async () => {
    engine({
      "/summary": { total: 0, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 0, conflicts: 0, lanes: { agent: 0, you: 0, second_screener: "PARKED" } },
      "/ui/batches": { ...BATCHES, count: 0, batches: [] },
    });
    render(<ScreeningHome locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Nothing to screen yet: prepare the batches first." });
    expect(screen.getByText("NOT_PREPARED")).toBeInTheDocument();
  });
});

describe("states.copy-for-every-code", () => {
  it("has a title, body, affects and action for every code in every locale", () => {
    for (const [code, entry] of Object.entries(STATES)) {
      for (const locale of SUPPORTED_LOCALES) {
        for (const field of ["title", "body", "affects", "action"] as const) {
          expect(entry.copy[locale][field].trim(), `${code}/${locale}/${field}`).not.toBe("");
        }
      }
    }
  });

  it("renders an unknown code verbatim instead of another card", () => {
    render(<StateCard locale="en" code="SOMETHING_NEW" message="details from the engine" />);
    expect(screen.getByText("SOMETHING_NEW")).toBeInTheDocument();
    expect(screen.getByText("details from the engine")).toBeInTheDocument();
    expect(stateCopy("en", "SOMETHING_NEW").known).toBe(false);
  });

  it("home copy has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(HOME_COPY[locale]).sort()).toEqual(Object.keys(HOME_COPY.en).sort());
      for (const [key, value] of Object.entries(HOME_COPY[locale])) {
        expect(holes(value), `${locale}/${key}`).toEqual(holes(HOME_COPY.en[key as keyof typeof HOME_COPY.en]));
      }
    }
  });
});

describe("states.conflict-not-a-refusal", () => {
  it("shows a conflict as unclear, never in the blocked role", () => {
    expect(stateCopy("en", "conflict").role).toBe("unclear");
    render(<StateCard locale="en" code="conflict" />);
    expect(screen.getByText("Decided differently on two devices", { selector: "h2" })).toBeInTheDocument();
    expect(document.querySelector('[data-role="blocked"]')).toBeNull();
  });
});
