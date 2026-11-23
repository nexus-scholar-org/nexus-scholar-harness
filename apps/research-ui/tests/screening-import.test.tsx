import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningImport } from "@/components/screening-import";
import { ScreeningHome } from "@/components/screening-home";
import { ScreeningSteps } from "@/components/screening-state-card";
import type { Corpus } from "@/lib/screening-v1";

/**
 * Import the corpus (spec 11, FINAL 2026-11-06). The engine's `GET /corpus`
 * shape is answered at the fetch boundary; every count on screen must be the
 * engine's number, and a label exported in parts is one database row.
 */

const LIMITS = { max_source_bytes: 50 * 1024 * 1024, label_max_length: 40 };

const EMPTY: Corpus = {
  shape: "screening.corpus-v1",
  state: "EMPTY",
  sources: [],
  databases: [],
  preview: { identified: 0, duplicates: 0, unique_studies: 0 },
  accepted: null,
  from_discovery: false,
  limits: LIMITS,
};

const STAGED: Corpus = {
  ...EMPTY,
  state: "STAGED",
  sources: [
    { id: "scopus-aaaa1111", label: "Scopus", file_name: "scopus-1.ris", records: 20, searched_on: "2026-11-06", query: "uav AND weed" },
    { id: "scopus-bbbb2222", label: "Scopus", file_name: "scopus-2.ris", records: 5, searched_on: "2026-11-06", query: "uav AND weed" },
    { id: "web-of-science-cccc3333", label: "Web of Science", file_name: "savedrecs.ris", records: 7, searched_on: null, query: null },
  ],
  databases: [
    { label: "Scopus", records: 25, files: 2, searched_on: ["2026-11-06"], search_details_missing: false },
    { label: "Web of Science", records: 7, files: 1, searched_on: [], search_details_missing: true },
  ],
  preview: { identified: 32, duplicates: 2, unique_studies: 30 },
};

const ACCEPTED: Corpus = {
  ...STAGED,
  state: "ACCEPTED",
  accepted: { artifact_id: "ART-corpus-0123456789abcdef", accepted_at: "2026-11-06T21:00:00Z", records: 32, studies: 30, duplicates: 2 },
};

type Call = { method: string; path: string; body: unknown };

function engine(routes: Record<string, unknown | ((body: unknown) => Response)>) {
  const log: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace(/^(\/api\/console)?\/api\/v1\/screening/, "");
      const method = init?.method ?? "GET";
      const body = init?.body ? JSON.parse(String(init.body)) : null;
      log.push({ method, path, body });
      const answer = routes[`${method} ${path}`] ?? routes[path];
      if (typeof answer === "function") return (answer as (b: unknown) => Response)(body);
      if (answer === undefined) return new Response(JSON.stringify({ detail: { code: "NOT_FOUND", message: path } }), { status: 404 });
      return new Response(JSON.stringify(answer), { status: 200, headers: { "content-type": "application/json" } });
    }),
  );
  return log;
}

const refused = (status: number, code: string) => () =>
  new Response(JSON.stringify({ detail: { code, message: code.toLowerCase() } }), { status, headers: { "content-type": "application/json" } });

afterEach(() => vi.unstubAllGlobals());

describe("import.empty", () => {
  it("opens with the form, search details closed, and the line that the corpus is accepted on the Hand-off (no link, no accept)", async () => {
    engine({ "/corpus": EMPTY });
    render(<ScreeningImport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Import your search results" });
    expect(screen.getByText("No databases added yet.")).toBeInTheDocument();
    const details = document.querySelector("[data-search-details]") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(within(details).getByText("Search details (optional)")).toBeInTheDocument();
    expect(await screen.findByText("Add at least one database. You accept the corpus on the Hand-off.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Review and accept on the Hand-off" })).toBeNull();
    expect(screen.queryByRole("button", { name: /Accept/ })).toBeNull();
    expect(screen.getByRole("button", { name: "Add this file" })).toBeDisabled();
  });
});

describe("import.staged", () => {
  it("shows one row per database with its parts summed, and the engine's PRISMA counts as a draft", async () => {
    engine({ "/corpus": STAGED });
    render(<ScreeningImport locale="en" />);
    await screen.findByRole("heading", { name: "Databases added" });
    const scopus = document.querySelector('[data-database="Scopus"]') as HTMLElement;
    expect(within(scopus).getByText("scopus-1.ris")).toBeInTheDocument();
    expect(within(scopus).getByText("scopus-2.ris")).toBeInTheDocument();
    expect(within(scopus).getByText("25")).toBeInTheDocument();
    expect(document.querySelectorAll("[data-database]")).toHaveLength(2);

    const counts = document.querySelector("[data-import-counts]") as HTMLElement;
    expect(within(counts).getByText("Preview · not frozen")).toBeInTheDocument();
    expect(counts.querySelector('[data-count="identified"]')).toHaveTextContent("32");
    expect(counts.querySelector('[data-count="duplicates"]')).toHaveTextContent("2");
    expect(counts.querySelector('[data-count="studies"]')).toHaveTextContent("30");
    expect(counts.querySelector("[data-prisma-sentence]")).toHaveTextContent(
      "Records identified from: Scopus (n = 25); Web of Science (n = 7); duplicate records removed (n = 2). Studies to screen: 30.",
    );
    expect(counts.querySelector("[data-not-stated]")).toHaveTextContent("Search details not stated for: Web of Science.");
    const wos = document.querySelector('[data-database="Web of Science"]') as HTMLElement;
    expect(within(wos).getAllByText("Not stated").length).toBeGreaterThan(0);
  });

  it("removes one part by its id", async () => {
    const log = engine({ "/corpus": STAGED, "POST /corpus/sources/scopus-bbbb2222/remove": { ...STAGED, sources: STAGED.sources.filter((s) => s.id !== "scopus-bbbb2222") } });
    render(<ScreeningImport locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Remove scopus-2.ris" }));
    await waitFor(() => expect(log.some((c) => c.path === "/corpus/sources/scopus-bbbb2222/remove")).toBe(true));
  });
});

describe("import.add", () => {
  function choose(name: string, text: string, size?: number) {
    const file = new File([text], name, { type: "application/x-research-info-systems" });
    if (size !== undefined) Object.defineProperty(file, "size", { value: size });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    return file;
  }

  it("sends the file as text with its label; empty search details go as null", async () => {
    const log = engine({ "/corpus": EMPTY, "POST /corpus/sources": STAGED });
    render(<ScreeningImport locale="en" />);
    await screen.findByText("No databases added yet.");
    choose("scopus-1.ris", "TY  - JOUR\nTI  - A\nER  - \n");
    fireEvent.change(screen.getByLabelText("Database name (required)"), { target: { value: " Scopus " } });
    fireEvent.click(screen.getByRole("button", { name: "Add this file" }));
    await screen.findByText("scopus-2.ris");
    const post = log.find((c) => c.method === "POST" && c.path === "/corpus/sources");
    expect(post?.body).toEqual({
      label: "Scopus", file_name: "scopus-1.ris", content_base64: btoa("TY  - JOUR\nTI  - A\nER  - \n"), searched_on: null, query: null,
    });
  });

  it("stops a file over the limit in the browser without sending it", async () => {
    const log = engine({ "/corpus": EMPTY });
    render(<ScreeningImport locale="en" />);
    await screen.findByText("No databases added yet.");
    choose("huge.ris", "TY  - JOUR\nER  - \n", 60 * 1024 * 1024);
    fireEvent.change(screen.getByLabelText("Database name (required)"), { target: { value: "Scopus" } });
    fireEvent.click(screen.getByRole("button", { name: "Add this file" }));
    await screen.findByText("SOURCE_TOO_LARGE");
    expect(log.some((c) => c.method === "POST")).toBe(false);
  });

  it("a phone token gets the desktop pointer, not a refusal", async () => {
    engine({ "/corpus": refused(403, "TOKEN_SCOPE_REFUSED") });
    render(<ScreeningImport locale="en" />);
    expect(await screen.findByText("Importing is done on your desktop. Open this screen there to add your database files.")).toBeInTheDocument();
    expect(screen.queryByText("TOKEN_SCOPE_REFUSED")).toBeNull();
  });

  it("marks the field a refusal names", async () => {
    engine({ "/corpus": EMPTY, "POST /corpus/sources": refused(422, "SOURCE_LABEL_INVALID") });
    render(<ScreeningImport locale="en" />);
    await screen.findByText("No databases added yet.");
    choose("a.ris", "TY  - JOUR\nER  - \n");
    fireEvent.change(screen.getByLabelText("Database name (required)"), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: "Add this file" }));
    await screen.findByText("SOURCE_LABEL_INVALID");
    expect(screen.getByLabelText("Database name (required)")).toHaveAttribute("aria-invalid", "true");
  });

  it("shows the engine's refusal with its code", async () => {
    engine({ "/corpus": EMPTY, "POST /corpus/sources": refused(422, "SOURCE_NOT_RIS") });
    render(<ScreeningImport locale="en" />);
    await screen.findByText("No databases added yet.");
    choose("notes.txt", "hello");
    fireEvent.change(screen.getByLabelText("Database name (required)"), { target: { value: "Scopus" } });
    fireEvent.click(screen.getByRole("button", { name: "Add this file" }));
    await screen.findByText("SOURCE_NOT_RIS");
    expect(screen.getByRole("heading", { name: "No records in this file" })).toBeInTheDocument();
  });
});

describe("import.accept", () => {
  afterEach(() => window.history.replaceState({}, "", "/"));

  it("M10b: a staged export links to the Hand-off with ?console=; no accept button, no dialog, no accept sent from here", async () => {
    window.history.replaceState({}, "", "/en/screening/import?console=http://127.0.0.1:8765");
    const log = engine({ "/corpus": STAGED, "POST /corpus/accept": ACCEPTED });
    render(<ScreeningImport locale="en" />);
    const link = await screen.findByRole("link", { name: "Review and accept on the Hand-off" });
    expect(link).toHaveAttribute("href", "/en/discovery/handoff/?console=http%3A%2F%2F127.0.0.1%3A8765");
    expect(screen.getByText("The Hand-off shows these counts again, explains the freeze and asks you to confirm.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Accept|Freeze/ })).toBeNull();
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(screen.queryByText("What happens when you accept")).toBeNull();
    expect(screen.queryByText("Add at least one database. You accept the corpus on the Hand-off.")).toBeNull();
    fireEvent.click(link);
    await new Promise((r) => setTimeout(r, 0));
    expect(log.some((c) => c.method === "POST" && c.path === "/corpus/accept")).toBe(false);
    expect(log.some((c) => c.path.endsWith("/review/next-step"))).toBe(false);
  });

  it("M10b: with nothing staged while a harvest is unfinished, the line is the next-step bar's sentence from the engine", async () => {
    engine({
      "/corpus": EMPTY,
      "/api/console/api/v1/review/next-step": {
        shape: "review.next-step-v1", scope: "workspace", phase: "discovery", round: 1, state: "CORPUS_PENDING",
        params: { run: "run_003", records: 1074, works: 1050, databases: 5, stage: "verifying" },
        waiting: { kind: "interrupted", stage: "verifying", job: null, reason: { code: "INTERRUPTED", message: null }, since: null, details: { stage_known: true } },
        action: { key: "finishPreparing", to: { screen: "discovery.harvest", query: { run: "run_003" } } }, also: [], unknown: [],
        protocol_fingerprint: null, computed_at: "2026-11-13T09:52:41+00:00",
      },
    });
    render(<ScreeningImport locale="en" />);
    expect(await screen.findByText("The search finished, but the corpus was not prepared. The console may have been closed while it ran.")).toBeInTheDocument();
    expect(screen.queryByText("Add at least one database. You accept the corpus on the Hand-off.")).toBeNull();
    expect(screen.queryByRole("link", { name: "Review and accept on the Hand-off" })).toBeNull();
  });

  it("adding or removing a file tells the next-step bar to read again", async () => {
    engine({ "/corpus": STAGED, "POST /corpus/sources/scopus-bbbb2222/remove": STAGED });
    let heard = 0;
    const listener = () => (heard += 1);
    window.addEventListener("nexus:review-changed", listener);
    try {
      render(<ScreeningImport locale="en" />);
      fireEvent.click(await screen.findByRole("button", { name: "Remove scopus-2.ris" }));
      await waitFor(() => expect(heard).toBe(1));
    } finally {
      window.removeEventListener("nexus:review-changed", listener);
    }
  });

  it("has no add, remove or accept control once accepted", async () => {
    engine({ "/corpus": ACCEPTED });
    render(<ScreeningImport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "What was imported" });
    expect(document.querySelector("[data-import-form]")).toBeNull();
    expect(screen.queryByRole("button", { name: /Remove/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Accept and freeze the corpus" })).toBeNull();
    expect(screen.getByText("Counted when frozen")).toBeInTheDocument();
  });

  it("an accepted corpus from the app's search says so, with the engine's counts, instead of an empty table", async () => {
    engine({
      "/corpus": {
        ...EMPTY,
        state: "ACCEPTED",
        from_discovery: true,
        accepted: { artifact_id: "ART-corpus-golden", accepted_at: "2026-11-04T16:49:16Z", records: 30, studies: 30, duplicates: 0 },
      },
    });
    render(<ScreeningImport locale="en" />);
    const card = await screen.findByRole("heading", { level: 2, name: "This workspace's corpus came from the app's own search, not from database files." });
    expect(card.parentElement).toHaveTextContent("30 records, 0 duplicates removed, 30 studies to screen.");
    expect(document.querySelector("[data-import-databases]")).toBeNull();
    expect(screen.queryByText("No databases added yet.")).toBeNull();
    expect(screen.getByRole("link", { name: "Continue to Prepare" })).toBeInTheDocument();
  });

  it("shows the discovery card and no form when the corpus came from the app's search", async () => {
    engine({ "/corpus": { ...EMPTY, from_discovery: true } });
    render(<ScreeningImport locale="en" />);
    await screen.findByText("VERIFIED_EXISTS");
    expect(document.querySelector("[data-import-form]")).toBeNull();
  });
});

describe("import.entry", () => {
  const HOME = {
    "/summary": { total: 0, decided: 0, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 0, needs_you: 0, conflicts: 0, lanes: { agent: 0, you: 0, second_screener: "PARKED" } },
    "/ui/batches": { shape: "ui07.screening-batches-v1", run_id: null, count: 0, batches: [], missing: [] },
    "/decisions/conflicts": { items: [] },
    "/settings": { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" },
  };

  it("home sends to Import until the corpus is accepted", async () => {
    engine({ ...HOME, "/corpus": STAGED });
    render(<ScreeningHome locale="en" />);
    expect(await screen.findByRole("link", { name: "Import your search results" })).toHaveAttribute("href", "/en/screening/import");
    expect(document.querySelector('[data-state="NOT_PREPARED"]')).toBeNull();
  });

  it("home shows one line of what was imported once accepted", async () => {
    engine({ ...HOME, "/corpus": ACCEPTED });
    render(<ScreeningHome locale="en" />);
    const line = await waitFor(() => {
      const el = document.querySelector("[data-imported-line]");
      if (!el) throw new Error("no line yet");
      return el;
    });
    expect(line).toHaveTextContent("32 records from Scopus and Web of Science, 2 duplicates removed.");
    expect(within(line as HTMLElement).getByRole("link", { name: "What was imported" })).toHaveAttribute("href", "/en/screening/import");
    expect(screen.queryByRole("link", { name: "Import your search results" })).toBeNull();
  });

  it("the steps bar shows Import until the corpus is accepted", async () => {
    engine({ "/corpus": STAGED });
    const { unmount } = render(<ScreeningSteps locale="en" current="home" />);
    expect(await screen.findByRole("link", { name: "Import" })).toHaveAttribute("href", "/en/screening/import");
    unmount();
    engine({ "/corpus": ACCEPTED });
    render(<ScreeningSteps locale="en" current="home" />);
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByRole("link", { name: "Import" })).toBeNull();
  });
});
