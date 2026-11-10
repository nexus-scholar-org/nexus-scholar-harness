import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningImport } from "@/components/screening-import";
import type { Corpus } from "@/lib/screening-v1";

/**
 * 04 Import, the discovery visit of the screening import screen (spec
 * docs/ux/phase1-discovery/final/04-import.md). A small inline fake answers
 * the corpus routes; every count on screen is the fake's.
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
  staging_refused: null,
};

const STAGED: Corpus = {
  ...EMPTY,
  state: "STAGED",
  sources: [
    {
      id: "scopus-aaaa1111", label: "Scopus", file_name: "scopus.ris", records: 20, searched_on: "2026-11-06", query: "uav AND weed", limits: "English; articles only",
      rejected: [
        { line: 12, code: "IMPORT_NO_TITLE", reason: "record without TI" },
        { line: 40, code: "IMPORT_SOMETHING_NEW", reason: "a code the screen does not know" },
      ],
    },
    { id: "wos-bbbb2222", label: "Web of Science", file_name: "savedrecs.ris", records: 7, searched_on: null, query: null, limits: null, rejected: [] },
  ],
  databases: [
    { label: "Scopus", records: 20, files: 1, searched_on: ["2026-11-06"], search_details_missing: false },
    { label: "Web of Science", records: 7, files: 1, searched_on: [], search_details_missing: true },
  ],
  preview: { identified: 27, duplicates: 1, unique_studies: 26 },
};

type Call = { method: string; path: string; body: Record<string, unknown> | null };

function fake(corpus: Corpus, search = "") {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://ui.test").pathname.replace(/^\/api\/console/, "");
      const method = init?.method ?? "GET";
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      calls.push({ method, path, body });
      const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
      if (method === "GET" && path === "/api/v1/screening/corpus") return json(corpus);
      if (method === "POST" && path === "/api/v1/screening/corpus/sources") return json(STAGED);
      return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
    }),
  );
  vi.stubGlobal("location", { ...window.location, search, assign: vi.fn(), reload: vi.fn() });
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

async function addFile(user: ReturnType<typeof userEvent.setup>, limits: string) {
  const file = new File(["TY  - JOUR\nTI  - A\nER  - \n"], "scopus.ris", { type: "application/x-research-info-systems" });
  await user.upload(document.querySelector('input[type="file"]') as HTMLInputElement, file);
  await user.type(screen.getByLabelText("Database name (required)"), "Scopus");
  await user.click(screen.getByText("Search details (optional)"));
  if (limits) await user.type(screen.getByLabelText("Limits you applied there, if any"), limits);
  await user.click(screen.getByRole("button", { name: "Add this file" }));
}

describe("discovery.import", () => {
  it("shows the discovery step bar with 4 Import current and the way back when visited from discovery", async () => {
    fake(EMPTY, "?return=discovery&console=http%3A%2F%2F127.0.0.1%3A8765");
    render(<ScreeningImport locale="en" />);
    const current = await waitFor(() => {
      const el = document.querySelector('[data-discovery-steps] [aria-current="step"]');
      if (!el) throw new Error("no discovery bar yet");
      return el;
    });
    expect(current).toHaveTextContent("4 Import");
    const back = screen.getByRole("link", { name: "Back to discovery" });
    expect(new URL(back.getAttribute("href") ?? "", "http://ui.test").searchParams.get("console")).toBe("http://127.0.0.1:8765");
    expect(await screen.findByText("Step 4 of 7 · Import")).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Screening steps" })).toBeNull();
  });

  it("shows the screening step bar without return=discovery", async () => {
    fake(EMPTY);
    render(<ScreeningImport locale="en" />);
    await screen.findByRole("navigation", { name: "Screening steps" });
    expect(document.querySelector("[data-discovery-steps]")).toBeNull();
    expect(screen.queryByRole("link", { name: "Back to discovery" })).toBeNull();
  });

  it("replaces the add form with the VERIFIED_EXISTS card and posts nothing", async () => {
    const calls = fake(
      { ...EMPTY, from_discovery: true, staging_refused: { code: "VERIFIED_EXISTS", message: "literature/verified.json already exists" } },
      "?return=discovery",
    );
    render(<ScreeningImport locale="en" />);
    const card = await screen.findByRole("alert");
    expect(card).toHaveAttribute("data-state", "VERIFIED_EXISTS");
    expect(within(card).getByText("Exports cannot be added after a harvest", { selector: "h2" })).toBeInTheDocument();
    expect(within(card.querySelector("details") as HTMLElement).getByText("VERIFIED_EXISTS")).toBeInTheDocument();
    expect(document.querySelector("[data-import-form]")).toBeNull();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("shows the importer's noted lines with their codes for a file that has some, and nothing for one that has none", async () => {
    fake(STAGED, "?return=discovery");
    render(<ScreeningImport locale="en" />);
    const disclosure = (await screen.findByText("Lines the importer noted")).closest("details") as HTMLElement;
    expect(disclosure).toHaveAttribute("data-rejected", "scopus-aaaa1111");
    expect(within(disclosure).getByText("IMPORT_NO_TITLE")).toBeInTheDocument();
    expect(within(disclosure).getByText("IMPORT_SOMETHING_NEW")).toBeInTheDocument();
    expect(disclosure.querySelectorAll("[data-rejected-code]")).toHaveLength(2);
    expect(document.querySelector('[data-rejected="wos-bbbb2222"]')).toBeNull();
    expect(screen.getAllByText("Lines the importer noted")).toHaveLength(1);
    expect(within(document.querySelector('[data-database="Scopus"]') as HTMLElement).getByText("English; articles only")).toBeInTheDocument();
  });

  it("sends the limits as typed", async () => {
    const user = userEvent.setup();
    const calls = fake(EMPTY, "?return=discovery");
    render(<ScreeningImport locale="en" />);
    await screen.findByText("No databases added yet.");
    await addFile(user, "English;  articles only");
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    const post = calls.find((c) => c.method === "POST" && c.path === "/api/v1/screening/corpus/sources");
    expect(post?.body?.limits).toBe("English;  articles only");
    expect(post?.body?.label).toBe("Scopus");
  });

  it("omits the limits when the field is blank", async () => {
    const user = userEvent.setup();
    const calls = fake(EMPTY, "?return=discovery");
    render(<ScreeningImport locale="en" />);
    await screen.findByText("No databases added yet.");
    await addFile(user, "");
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    const post = calls.find((c) => c.method === "POST" && c.path === "/api/v1/screening/corpus/sources");
    expect(post?.body).not.toHaveProperty("limits");
  });
});
