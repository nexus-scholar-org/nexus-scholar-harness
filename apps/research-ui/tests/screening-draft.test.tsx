import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningPage } from "@/components/screening-page";
import { CATALOGS } from "@/messages";

/**
 * Live draft capture (packet UI-07 §3.2).
 *
 * `POST /api/v1/screening/batch/{n}/decisions` is the sanctioned *draft*
 * writer. These tests hold down the four claims that make wiring it safe:
 *
 * 1. only the two decisions the console accepts are offered — the
 *    demonstration form's third choice would be a button that always fails;
 * 2. a save is disabled until both a decision and a reason exist, so the
 *    console never substitutes its generic sentence for the researcher's;
 * 3. the request carries one record, the workspace id, the reason verbatim,
 *    and the `researcher-draft` author label — never an approval field;
 * 4. after saving, the page re-reads the batch instead of treating its own
 *    response as the new truth, and a refusal is shown as the server's typed
 *    code with no "saved" message.
 */

const CONSOLE = "http://127.0.0.1:1899";
const SAVED = "Draft saved for this record.";

const SUMMARY = {
  shape: "ui07.project-summary-v1",
  workspace_id: "WSP-ffffffffffffffffffffffffffffffff",
  run: { screening_run_id: "RUN-DRAFT-1", batches: 1, batches_resolved: 1 },
  missing: [],
};

const BATCHES = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-DRAFT-1",
  count: 1,
  batches: [
    {
      batch_index: 0,
      batch_file: "batch_000.json",
      items: 1,
      decisions_file: "batch_000_decisions.json",
      decisions_count: 0,
      collected: false,
      coverage: "INCOMPLETE",
      unresolved_rows: ["STUDY-DRAFT-001"],
    },
  ],
  missing: [],
};

const PUBLICATION = {
  shape: "ui07.publication-status-v1",
  status: "LEGACY_UNVERIFIED",
  code: "GENERATION_LEGACY_UNVERIFIED",
  generation_id: null,
  outputs: {},
  message: "no publication generation is recorded",
  details: {},
};

const ROWS = {
  shape: "ui07.screening-rows-v1",
  batch_index: 0,
  batch_file: "batch_000.json",
  total: 1,
  offset: 0,
  limit: 100,
  rows: [
    {
      shape: "ui07.screening-row-v1",
      study_id: "STUDY-DRAFT-001",
      workspace_id: "WSP-cccccccccccccccccccccccccccccccc",
      citation: "Draft Author. A record awaiting a researcher draft. J Draft; 2026.",
      abstract: "Draft abstract, stored exactly.",
      decision: "PENDING",
      reasons: [],
      uncertainty: "unreviewed",
    },
  ],
  missing: [],
};

const REFS = {
  shape: "ui07.criterion-refs-v1",
  protocol_fingerprint: "sha256:draft",
  inclusion: [{ id: "INC-01", text: "Names the population." }],
  exclusion: [],
  sources: [],
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

function setQuery(query: string): void {
  window.history.replaceState({}, "", `/en/screening${query}`);
}

type DraftCall = { path: string; body: Record<string, unknown> };

function stubFetch(
  postResponse: () => Response = () =>
    jsonResponse({ batch: 0, decisions_written: 1, decisions_total: 1, decisions_file: "batch_000_decisions.json" }),
): { fetch: ReturnType<typeof vi.fn>; posts: DraftCall[] } {
  const posts: DraftCall[] = [];
  const fetchSpy = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input);
    const path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0] ?? url;
    if (init?.method === "POST" || path.includes("/decisions")) {
      posts.push({ path, body: JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown> });
      return postResponse();
    }
    const table: Record<string, Response> = {
      "/api/v1/ui/project-summary": jsonResponse(SUMMARY),
      "/api/v1/screening/ui/batches": jsonResponse(BATCHES),
      "/api/v1/ui/publication-status": jsonResponse(PUBLICATION),
      "/api/v1/screening/ui/batch/0/rows": jsonResponse(ROWS),
      "/api/v1/screening/ui/batch/0/criterion-refs": jsonResponse(REFS),
    };
    return table[path]?.clone() ?? typedRefusal("BATCH_MISSING", `missing file: ${path}`, 404);
  });
  return { fetch: fetchSpy, posts };
}

async function openRowEditor() {
  render(<ScreeningPage locale="en" />);
  const citation = await screen.findByText(ROWS.rows[0]?.citation ?? "");
  const row = citation.closest("li");
  if (!row) throw new Error("row element not found");
  fireEvent.click(within(row).getByText(CATALOGS.en["screening.draftOpen"]));
  return row as HTMLElement;
}

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/en/screening");
  vi.unstubAllGlobals();
});

describe("live draft capture", () => {
  it("offers only the two decisions the console accepts", async () => {
    const { fetch } = stubFetch();
    vi.stubGlobal("fetch", fetch);
    setQuery(`?source=live&console=${CONSOLE}`);

    const row = await openRowEditor();

    expect(within(row).getByRole("radio", { name: CATALOGS.en["screening.decision.include"] })).toBeInTheDocument();
    expect(within(row).getByRole("radio", { name: CATALOGS.en["screening.decision.exclude"] })).toBeInTheDocument();
    expect(within(row).queryByRole("radio", { name: CATALOGS.en["screening.decision.unclear"] })).toBeNull();
  });

  it("keeps save disabled until a decision and a reason are both present", async () => {
    const { fetch } = stubFetch();
    vi.stubGlobal("fetch", fetch);
    setQuery(`?source=live&console=${CONSOLE}`);

    const row = await openRowEditor();
    const save = within(row).getByRole("button", { name: CATALOGS.en["screening.submit"] });

    expect(save).toBeDisabled();
    fireEvent.click(within(row).getByRole("radio", { name: CATALOGS.en["screening.decision.include"] }));
    expect(save).toBeDisabled();
    fireEvent.change(within(row).getByRole("textbox"), { target: { value: "   " } });
    expect(save).toBeDisabled();
    fireEvent.change(within(row).getByRole("textbox"), { target: { value: "matches the population" } });
    expect(save).toBeEnabled();
  });

  it("posts one researcher draft and then re-reads the batch", async () => {
    const { fetch, posts } = stubFetch();
    vi.stubGlobal("fetch", fetch);
    setQuery(`?source=live&console=${CONSOLE}`);

    const row = await openRowEditor();
    fireEvent.click(within(row).getByRole("radio", { name: CATALOGS.en["screening.decision.exclude"] }));
    fireEvent.change(within(row).getByRole("textbox"), {
      target: { value: "  no relevant intervention  " },
    });
    fireEvent.click(within(row).getByRole("button", { name: CATALOGS.en["screening.submit"] }));

    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0]?.path).toBe("/api/v1/screening/batch/0/decisions");
    expect(posts[0]?.body).toEqual({
      batch: 0,
      reviewed_by: "researcher-draft",
      decisions: [
        {
          workspace_id: "WSP-cccccccccccccccccccccccccccccccc",
          decision: "EXCLUDE",
          screening_reasoning: "no relevant intervention",
        },
      ],
    });
    // No approval-shaped field is invented anywhere in the payload.
    expect(JSON.stringify(posts[0]?.body)).not.toMatch(/approv|publish|generation/i);

    expect(await screen.findByText(SAVED)).toBeInTheDocument();

    // The stored draft earns its place by being read back, not by folding the
    // write response into the rows already on screen.
    const reads = fetch.mock.calls.filter(([input, init]) => {
      const path = String(input);
      return path.includes("/screening/ui/batch/0/rows") && (init as RequestInit | undefined)?.method !== "POST";
    });
    expect(reads.length).toBeGreaterThanOrEqual(2);
  });

  it("shows a refusal as the server's typed code and never claims a save", async () => {
    const { fetch } = stubFetch(() =>
      typedRefusal("COVERAGE_INCOMPLETE", "draft does not cover the batch", 422),
    );
    vi.stubGlobal("fetch", fetch);
    setQuery(`?source=live&console=${CONSOLE}`);

    const row = await openRowEditor();
    fireEvent.click(within(row).getByRole("radio", { name: CATALOGS.en["screening.decision.include"] }));
    fireEvent.change(within(row).getByRole("textbox"), {
      target: { value: "matches the population" },
    });
    fireEvent.click(within(row).getByRole("button", { name: CATALOGS.en["screening.submit"] }));

    const alert = await within(row).findByRole("alert");
    expect(alert).toHaveTextContent(CATALOGS.en["screening.draftError"]);
    expect(alert).toHaveTextContent("COVERAGE_INCOMPLETE");
    expect(alert).toHaveTextContent("draft does not cover the batch");
    expect(within(row).queryByText(SAVED)).toBeNull();
  });
});
