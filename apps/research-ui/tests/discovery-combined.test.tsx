import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryHandoff } from "@/components/discovery-handoff";
import { DiscoveryHarvest } from "@/components/discovery-harvest";
import { DiscoveryReport } from "@/components/discovery-report";
import { ScreeningImport } from "@/components/screening-import";
import { DISCOVERY_COPY } from "@/lib/discovery-copy";
import type { Corpus } from "@/lib/screening-v1";

import { sent, setUp } from "./discovery-helpers";

/**
 * M3f-combined-corpus: one corpus from a harvest and database exports (addenda to
 * docs/ux/phase1-discovery/final/03, 04, 06 and 08). Every number is the engine's.
 */

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("discovery.combined: Hand-off (08 addendum)", () => {
  it("shows both parts: the searched databases and the export, each with its kind in words, and the engine's count in the headline", async () => {
    setUp({ runs: 1, staged: true });
    render(<DiscoveryHandoff locale="en" />);
    // The fake's combined preview: 1060 works from the harvest + 80 from the export.
    await screen.findByRole("heading", { level: 1, name: "Accept these 1140 works as the corpus you will screen?" });
    const scopus = document.querySelector('[data-mix-row="Scopus"]') as HTMLElement;
    expect(scopus).toHaveAttribute("data-mix-kind", "import");
    expect(within(scopus).getByText("(your export)")).toBeInTheDocument();
    expect(within(scopus).getByText("110 records · 9.74 %")).toBeInTheDocument();
    expect(within(document.querySelector('[data-mix-row="openalex"]') as HTMLElement).getByText("(searched by the app)")).toBeInTheDocument();
    expect(screen.getByText("A work found in two databases is counted in both, so shares can add up to more than 100 %.")).toBeInTheDocument();
    const unchecked = document.querySelector("[data-imports-unchecked]") as HTMLElement;
    expect(unchecked).toHaveTextContent(
      "120 records come from your exports. They were not checked against Crossref or OpenAlex, and missing abstracts were not filled in.",
    );
    expect(unchecked.closest("[data-hint-body]")).toBeNull();
    expect(document.querySelector("[data-harvest-out]")).toBeNull();
    expect(screen.getByRole("button", { name: "Accept this corpus" })).toBeEnabled();
    // The From card names the run and the staged export.
    expect(screen.getByText("Staged exports: Scopus", { exact: false })).toBeInTheDocument();
  });

  it("says before the accept that an unfinished harvest is left out, links to it, and keeps Accept", async () => {
    setUp({ runs: 1, staged: true, preparation: "failed" });
    render(<DiscoveryHandoff locale="en" />);
    const note = await waitFor(() => {
      const el = document.querySelector("[data-harvest-out]");
      if (!el) throw new Error("no note yet");
      return el as HTMLElement;
    });
    expect(note).toHaveAttribute("role", "status");
    expect(note).toHaveTextContent(
      "The harvest run_001 is not prepared (preparation failed). If you accept now, the corpus holds your exports only and the harvest's records are left out for good.",
    );
    const open = within(note).getByRole("link", { name: "Open Harvest" });
    expect(new URL(open.getAttribute("href") ?? "", "http://ui.test").searchParams.get("run")).toBe("run_001");
    expect(screen.getByRole("button", { name: "Accept this corpus" })).toBeEnabled();
    // Only the export is in the mix: the unfinished harvest's works are not counted.
    expect([...document.querySelectorAll("[data-mix-row]")].map((r) => r.getAttribute("data-mix-row"))).toEqual(["Scopus"]);
  });

  it("offers no note and no unchecked line for a harvest alone", async () => {
    setUp({ runs: 1 });
    render(<DiscoveryHandoff locale="en" />);
    await screen.findByRole("button", { name: "Accept this corpus" });
    expect(document.querySelector("[data-harvest-out]")).toBeNull();
    expect(document.querySelector("[data-imports-unchecked]")).toBeNull();
  });

  it("accepts a combined corpus with one request", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ runs: 1, staged: true });
    render(<DiscoveryHandoff locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Accept this corpus" }));
    await screen.findByRole("heading", { level: 1, name: "This corpus is accepted." });
    expect(sent(engine).filter((c) => c === "POST /api/v1/screening/corpus/accept")).toHaveLength(1);
  });

  it("prints the state verbatim when the engine sends one the screen does not know", async () => {
    setUp({ runs: 1, staged: true, preparation: "paused-for-maintenance" as never });
    render(<DiscoveryHandoff locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-harvest-out]")).toHaveTextContent("(paused-for-maintenance)"));
  });
});

describe("discovery.combined: Report (06 addendum)", () => {
  it("lists the searched databases first, then the export with 'not stated' cells, and says what the combined count covers", async () => {
    setUp({ runs: 1, staged: true });
    render(<DiscoveryReport locale="en" />);
    const row = await waitFor(() => {
      const el = document.querySelector('[data-ident="Scopus"]');
      if (!el) throw new Error("no export row yet");
      return el as HTMLElement;
    });
    const kinds = [...document.querySelectorAll("[data-ident]")].map((r) => r.getAttribute("data-kind"));
    expect(kinds.at(-1)).toBe("import");
    expect(kinds.slice(0, -1).every((k) => k === "search")).toBe(true);
    expect(within(row).getByText("your export")).toBeInTheDocument();
    expect(row.querySelector('[data-not-stated="query"]')).toHaveTextContent("not stated");
    expect(row.querySelector('[data-not-stated="date"]')).toHaveTextContent("not stated");
    expect(row.querySelector("[data-import-limits]")).toHaveTextContent("Limits: not stated");
    expect(within(document.querySelector('[data-ident="openalex"]') as HTMLElement).getByText("searched by the app")).toBeInTheDocument();
    expect(document.querySelector("[data-dedup-combined]")).toHaveTextContent(
      "This count covers the harvest and your exports together, so it is not broken down by rule.",
    );
    expect(document.querySelector("[data-dedup]")?.textContent).not.toContain("Exact title");
  });
});

const LIMITS = { max_source_bytes: 50 * 1024 * 1024, label_max_length: 40 };
const STAGED: Corpus = {
  shape: "screening.corpus-v1",
  state: "STAGED",
  sources: [{ id: "scopus-aaaa1111", label: "Scopus", file_name: "scopus.ris", records: 20, searched_on: "2026-11-06", query: "uav", limits: null, rejected: [] }],
  databases: [
    { label: "OpenAlex", records: 40, files: 0, searched_on: ["2026-11-20"], search_details_missing: false, provider: "openalex", status: "ok", cap_hit: false },
    { label: "Scopus", records: 20, files: 1, searched_on: ["2026-11-06"], search_details_missing: false },
  ],
  preview: { identified: 60, duplicates: 5, unique_studies: 55 },
  accepted: null,
  from_discovery: true,
  origin: "combined",
  harvest: { run: "run_003", state: "ready", included: true },
  limits: LIMITS,
  staging_refused: null,
};

function fakeCorpus(corpus: Corpus) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const path = new URL(url, "http://ui.test").pathname.replace(/^\/api\/console/, "");
      const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
      if (path === "/api/v1/screening/corpus") return json(corpus);
      return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
    }),
  );
  vi.stubGlobal("location", { ...window.location, search: "?return=discovery", assign: vi.fn(), reload: vi.fn() });
}

describe("discovery.combined: Import (04 addendum)", () => {
  it("says the exports will be combined with a ready harvest and keeps the add form", async () => {
    fakeCorpus(STAGED);
    render(<ScreeningImport locale="en" />);
    const line = await screen.findByText("These exports will be combined with the harvest run_003 when you accept the corpus on the Hand-off.");
    expect(line.closest('[role="status"]')).not.toBeNull();
    expect(screen.getByRole("button", { name: "Add this file" })).toBeInTheDocument();
    expect(document.querySelector("[data-staging-refused]")).toBeNull();
  });

  it("names a harvest that is not prepared, with its state in words and a link to it, and keeps the add form", async () => {
    fakeCorpus({ ...STAGED, origin: "imports", from_discovery: false, harvest: { run: "run_003", state: "failed", included: false } });
    render(<ScreeningImport locale="en" />);
    const line = await waitFor(() => {
      const el = document.querySelector('[data-import-combined="not-ready"]');
      if (!el) throw new Error("no line yet");
      return el as HTMLElement;
    });
    expect(line).toHaveTextContent("The harvest run_003 is not prepared (preparation failed), so it is not part of this corpus yet.");
    expect(new URL(within(line).getByRole("link", { name: "Open Harvest" }).getAttribute("href") ?? "", "http://ui.test").searchParams.get("run")).toBe("run_003");
    expect(screen.getByRole("button", { name: "Add this file" })).toBeInTheDocument();
  });

  it("shows no harvest line without a harvest", async () => {
    fakeCorpus({ ...STAGED, origin: "imports", from_discovery: false, harvest: null });
    render(<ScreeningImport locale="en" />);
    await screen.findByRole("button", { name: "Add this file" });
    expect(document.querySelector("[data-import-combined]")).toBeNull();
  });

  it("lists the exports of an accepted combined corpus and says it was combined", async () => {
    fakeCorpus({
      ...STAGED, state: "ACCEPTED", staging_refused: { code: "CORPUS_ALREADY_ACCEPTED", message: "accepted" },
      accepted: { artifact_id: "ART-corpus-1", accepted_at: "2026-11-20T10:00:00Z", records: 60, studies: 55, duplicates: 5 },
    });
    render(<ScreeningImport locale="en" />);
    await screen.findByText("Combined with the harvest run_003.");
    expect(document.querySelector("[data-import-databases]")).not.toBeNull();
    expect(document.querySelector("[data-import-discovery]")).toBeNull();
  });

  it("keeps the reworded card for records of unknown origin", async () => {
    fakeCorpus({ ...STAGED, sources: [], databases: [], origin: null, harvest: null, staging_refused: { code: "VERIFIED_EXISTS", message: "unknown origin" } });
    render(<ScreeningImport locale="en" />);
    await waitFor(() => expect(document.querySelector('[data-staging-refused="VERIFIED_EXISTS"]')).not.toBeNull());
    expect(screen.queryByText(/only before the first harvest/)).toBeNull();
  });
});

describe("discovery.combined: copy (finding 26)", () => {
  it("no catalog string says an export cannot be added after a harvest, in any locale", () => {
    for (const locale of ["en", "fr", "ar"] as const) {
      const copy = DISCOVERY_COPY[locale];
      expect(copy["harvest.warn.imports"]).not.toMatch(/can no longer be added|ne peuvent plus|لم يعد ممكنًا/);
      expect(copy["plan.imports.afterRun"]).not.toMatch(/cannot be added|ne peut pas être ajouté|لا يمكن إضافة/);
    }
    expect(DISCOVERY_COPY.en["harvest.warn.imports"]).toBe(
      "Database exports you add on the Import step, before or after this harvest, are combined with it when you accept the corpus on the Hand-off, and duplicates across both are removed.",
    );
  });
});

describe("discovery.combined: Harvest (03 addendum)", () => {
  it("says on an empty corpus that exports added before or after the harvest are combined with it", async () => {
    setUp();
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: "Search the databases your protocol selects" });
    const warn = document.querySelector("[data-warn-imports]") as HTMLElement;
    expect(warn).toHaveTextContent("before or after this harvest, are combined with it when you accept the corpus on the Hand-off");
    expect(warn).not.toHaveTextContent("can no longer be added");
    expect(warn.closest("[data-hint-body]")).toBeNull();
  });

  it("runs with exports staged and shows no STAGED_IMPORT_PENDING card", async () => {
    const user = userEvent.setup();
    const { engine } = setUp({ staged: true });
    render(<DiscoveryHarvest locale="en" />);
    await screen.findByRole("heading", { name: "Search the databases your protocol selects" });
    await user.click(screen.getByRole("button", { name: "Start the harvest" }));
    await screen.findByRole("heading", { name: "The harvest is finished. The corpus is not frozen yet." });
    expect(sent(engine)).toContain("POST /api/v1/discovery/runs");
    expect(document.querySelector('[data-state="STAGED_IMPORT_PENDING"]')).toBeNull();
  });
});

describe("discovery.combined: counted copy (review F8)", () => {
  it("says one record in the singular", async () => {
    const { discoveryCountT } = await import("@/lib/discovery-copy");
    expect(discoveryCountT("en")("handoff.imports.unchecked", 1, { n: 1 })).toBe(
      "1 record comes from your exports. It was not checked against Crossref or OpenAlex, and a missing abstract was not filled in.",
    );
    expect(discoveryCountT("en")("handoff.imports.unchecked", 618, { n: 618 })).toMatch(/^618 records come from your exports\./);
    expect(discoveryCountT("ar")("handoff.imports.unchecked", 2, { n: 2 })).toMatch(/^سجلان/);
  });
});
