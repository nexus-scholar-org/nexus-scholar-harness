import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ACTION_CHROME, PairingDialog } from "@/components/pairing-dialog";
import { ScreeningPage } from "@/components/screening-page";
import {
  getPairingStatus,
  postDeferBatch,
  postDraftDecisions,
  postPairingRedeem,
  postPublishScreening,
} from "@/lib/screening-api";
import type { Locale } from "@/i18n";

/**
 * The protected action wiring, in process (UI-07 action side).
 *
 * The client helpers POST against the console action routes (redeem, defer,
 * publish) or reuse the stored-decisions route for drafts; the dialog keeps
 * a typed code in memory only; the live panel threads request ids through
 * every write and shows server refusals verbatim. Reads stay GETs and the
 * fixture default stays request-free (pinned by `screening-live.test.tsx`).
 *
 * Everything here stubs `fetch` at the network boundary with
 * shape-conformant payloads. No browser is needed: the rendered-DOM claims
 * are jsdom's, and the rendered-in-Chromium claims stay with
 * `tests-browser/screening-actions.spec.ts`.
 */

const CONSOLE = "http://127.0.0.1:1899";
const CODE = "AB12C-DE34F-GH56J-KL78M-NP9QR2S";

const LIVE_SUMMARY = {
  shape: "ui07.project-summary-v1",
  workspace_id: "WSP-ffffffffffffffffffffffffffffffff",
  project_id: "ui-actions-demo",
  protocol: { present: true, fingerprint: "sha256:live" },
  run: { screening_run_id: "RUN-UI-ACT-1", batches: 1, batches_resolved: 1 },
  readiness: {
    screening_prepared: true,
    all_batches_resolved: true,
    publication: {
      shape: "ui07.publication-status-v1",
      status: "CURRENT",
      code: null,
      generation_id: "GEN-UI-ACT-1",
      outputs: { "included.json": "sha256:live" },
      message: "screening generation is current",
      details: { generation_id: "GEN-UI-ACT-1" },
    },
  },
  missing: [],
};

const LIVE_BATCHES = {
  shape: "ui07.screening-batches-v1",
  run_id: "RUN-UI-ACT-1",
  count: 1,
  batches: [
    {
      batch_index: 0,
      batch_file: "batch_000.json",
      items: 1,
      decisions_file: "batch_000_decisions.json",
      decisions_count: 1,
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
  generation_id: "GEN-UI-ACT-1",
  outputs: { "included.json": "sha256:live" },
  message: "screening generation is current",
  details: { generation_id: "GEN-UI-ACT-1" },
};

const LIVE_ROWS = {
  shape: "ui07.screening-rows-v1",
  batch_index: 0,
  batch_file: "batch_000.json",
  total: 1,
  offset: 0,
  limit: 100,
  rows: [
    {
      shape: "ui07.screening-row-v1",
      study_id: "STUDY-UI-ACT-001",
      citation: "Action Author. A live read for the action panel. J Live; 2025.",
      abstract: "Live abstract for actions, served exactly as stored.",
      decision: "INCLUDE",
      reasons: ["Matches the population criterion."],
      uncertainty: "confidence 0.9",
      criterion_refs: { inclusion: ["INC-01"], exclusion: [] },
      source_locators: { doi: "10.0000/act1" },
    },
  ],
  missing: [],
};

const LIVE_REFS = {
  shape: "ui07.criterion-refs-v1",
  protocol_fingerprint: "sha256:live",
  inclusion: [{ id: "INC-01", text: "Names the population and outcome." }],
  exclusion: [],
  sources: [{ workspace_id: "STUDY-UI-ACT-001", doi: "10.0000/act1" }],
  missing: [],
};

const STAGED_STATUS = {
  shape: "screening-action-pairing-status-v1",
  batch_index: 0,
  state: "STAGED",
  expires_at: "2026-10-13T12:05:00+00:00",
  snapshot_fingerprint: "sha256:staged",
  attempts_remaining: 5,
  request_id: "REQ-STATUS-1",
};

const REDEEM_OK = {
  shape: "screening-action-redeem-v1",
  request_id: "REQ-ACT-1",
  journal_event_id: "EVT-20261013120000-abc123",
  batch_index: 0,
  snapshot_fingerprint: "sha256:staged",
  approval_fingerprint: "sha256:approval",
  publication_approval_fingerprint: "sha256:pubapproval",
  operator_identity: "ui07-operator@example",
  superseded: true,
};

const DEFER_OK = {
  shape: "screening-action-defer-v1",
  request_id: "REQ-ACT-2",
  journal_event_id: "EVT-20261013120000-def456",
  batch_index: 0,
  deferral_file: "batch_000_deferral.json",
  reason: "awaiting full text",
  cancelled: false,
  pairing_voided: true,
};

const PUBLISH_OK = {
  shape: "screening-action-publish-v1",
  request_id: "REQ-ACT-3",
  journal_event_id: "EVT-20261013120000-pub789",
  status: "CURRENT",
  generation_id: "GEN-UI-ACT-2",
  generation_fingerprint: "sha256:generation",
  outputs: { "included.json": "sha256:live" },
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

type RouteHandler = (url: string, init?: RequestInit) => Response;

function stubActionFetch(
  overrides?: Partial<Record<string, Response | RouteHandler>>,
): (input: unknown, init?: RequestInit) => Promise<Response> {
  const table: Record<string, Response | RouteHandler> = {
    "/api/v1/ui/project-summary": jsonResponse(LIVE_SUMMARY),
    "/api/v1/screening/ui/batches": jsonResponse(LIVE_BATCHES),
    "/api/v1/ui/publication-status": jsonResponse(LIVE_PUBLICATION),
    "/api/v1/screening/ui/batch/0/rows": jsonResponse(LIVE_ROWS),
    "/api/v1/screening/ui/batch/0/criterion-refs": jsonResponse(LIVE_REFS),
    "/api/v1/screening/actions/pairing/status": jsonResponse(STAGED_STATUS),
    "/api/v1/screening/actions/pairing/redeem": jsonResponse(REDEEM_OK),
    "/api/v1/screening/actions/defer": jsonResponse(DEFER_OK),
    "/api/v1/screening/actions/publish": jsonResponse(PUBLISH_OK),
    ...overrides,
  };
  return async (input: unknown, init?: RequestInit) => {
    const url = String(input);
    const path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0] ?? url;
    const entry = table[path];
    if (typeof entry === "function") return entry(url, init);
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

describe("action client calls", () => {
  it("redeems with batch and code over POST and returns the typed shape", async () => {
    const seen: { url: string; init?: RequestInit }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) => {
        seen.push({ url: String(input), init });
        return jsonResponse(REDEEM_OK);
      }),
    );
    const result = await postPairingRedeem(CONSOLE, 0, CODE, { requestId: "REQ-ACT-1" });
    expect(result.approval_fingerprint).toBe("sha256:approval");
    expect(result.request_id).toBe("REQ-ACT-1");
    expect(seen).toHaveLength(1);
    expect(seen[0]?.init?.method).toBe("POST");
    expect(seen[0]?.url).toBe(`${CONSOLE}/api/v1/screening/actions/pairing/redeem`);
    expect(String(seen[0]?.init?.body)).toContain(CODE);
  });

  it("reads pairing status over GET and never sends a code", async () => {
    const seen: { url: string; init?: RequestInit }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) => {
        seen.push({ url: String(input), init });
        return jsonResponse(STAGED_STATUS);
      }),
    );
    const status = await getPairingStatus(CONSOLE, 0);
    expect(status.state).toBe("STAGED");
    expect(seen).toHaveLength(1);
    expect(seen[0]?.init?.method ?? "GET").toBe("GET");
    expect(seen[0]?.url).toContain("/api/v1/screening/actions/pairing/status?batch=0");
    expect(seen[0]?.url).not.toContain(CODE);
    expect(String(seen[0]?.init?.body ?? "")).not.toContain(CODE);
  });

  it("reuses the stored-decisions route for drafts (no second writer)", async () => {
    const seen: { url: string; init?: RequestInit }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) => {
        seen.push({ url: String(input), init });
        return jsonResponse({ batch: 0, decisions_written: 1, decisions_file: "batch_000_decisions.json" });
      }),
    );
    const result = await postDraftDecisions(CONSOLE, 0, {
      reviewed_by: "browser-draft",
      decisions: [{ workspace_id: "STUDY-UI-ACT-001", decision: "INCLUDE" }],
    });
    expect(result.decisions_written).toBe(1);
    expect(seen[0]?.url).toBe(`${CONSOLE}/api/v1/screening/batch/0/decisions`);
    expect(seen[0]?.init?.method).toBe("POST");
  });

  it("defers and publishes over POST and surfaces typed refusals", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown) => {
        const url = String(input);
        if (url.endsWith("/actions/defer")) return typedRefusal("REVIEW_REASON_MISSING", "defer requires a reason", 422);
        return jsonResponse(PUBLISH_OK);
      }),
    );
    await expect(postDeferBatch(CONSOLE, 0, " ")).rejects.toMatchObject({ code: "REVIEW_REASON_MISSING" });
    const published = await postPublishScreening(CONSOLE);
    expect(published.generation_id).toBe("GEN-UI-ACT-2");
  });
});

describe("pairing dialog keeps the code in memory only", () => {
  it("submits the typed code once, then clears the field", async () => {
    const submitted: string[] = [];
    const closed: string[] = [];
    render(
      <PairingDialog
        locale="en"
        open
        pending={false}
        serverError={null}
        snapshotFingerprint="sha256:staged"
        onClose={() => closed.push("closed")}
        onSubmit={(code) => submitted.push(code)}
      />,
    );
    const field = screen.getByLabelText(ACTION_CHROME.en.codeLabel) as HTMLInputElement;
    expect(field).toHaveAttribute("autocomplete", "off");
    fireEvent.change(field, { target: { value: CODE } });
    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton }));
    expect(submitted).toEqual([CODE]);
    await waitFor(() => expect(field.value).toBe(""));
    // A cleared field cannot be resubmitted without retyping.
    expect(screen.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton })).toBeDisabled();
    expect(closed).toEqual([]);
  });

  it("closes without submitting and wipes the field, writing no storage", async () => {
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);
    const submitted: string[] = [];
    let open = true;
    const { rerender } = render(
      <PairingDialog
        locale="en"
        open={open}
        pending={false}
        serverError={null}
        snapshotFingerprint={null}
        onClose={() => {
          open = false;
        }}
        onSubmit={(code) => submitted.push(code)}
      />,
    );
    fireEvent.change(screen.getByLabelText(ACTION_CHROME.en.codeLabel), {
      target: { value: CODE },
    });
    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.cancelButton }));
    expect(submitted).toEqual([]);
    expect(storageSpy).not.toHaveBeenCalled();
    rerender(
      <PairingDialog
        locale="en"
        open={open}
        pending={false}
        serverError={null}
        snapshotFingerprint={null}
        onClose={() => undefined}
        onSubmit={(code) => submitted.push(code)}
      />,
    );
    expect(screen.queryByLabelText(ACTION_CHROME.en.codeLabel)).toBeNull();
  });

  it("shows the server refusal verbatim and keeps the dialog open", async () => {
    render(
      <PairingDialog
        locale="en"
        open
        pending={false}
        serverError={{ code: "PAIRING_CODE_INVALID", message: "that code is expired" }}
        snapshotFingerprint={null}
        onClose={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("PAIRING_CODE_INVALID");
    expect(alert).toHaveTextContent("that code is expired");
    expect(screen.getByLabelText(ACTION_CHROME.en.codeLabel)).toBeInTheDocument();
  });

  it("wipes the typed code on unmount, writing no storage", async () => {
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);
    const submitted: string[] = [];
    const first = render(
      <PairingDialog
        locale="en"
        open
        pending={false}
        serverError={null}
        snapshotFingerprint={null}
        onClose={() => undefined}
        onSubmit={(code) => submitted.push(code)}
      />,
    );
    const field = screen.getByLabelText(ACTION_CHROME.en.codeLabel) as HTMLInputElement;
    fireEvent.change(field, { target: { value: CODE } });
    expect(field.value).toBe(CODE);
    first.unmount();
    render(
      <PairingDialog
        locale="en"
        open
        pending={false}
        serverError={null}
        snapshotFingerprint={null}
        onClose={() => undefined}
        onSubmit={(code) => submitted.push(code)}
      />,
    );
    // A remount starts empty: the typed code lived in memory only and died
    // with the unmounted dialog; nothing was submitted or stored.
    expect(
      (screen.getByLabelText(ACTION_CHROME.en.codeLabel) as HTMLInputElement).value,
    ).toBe("");
    expect(submitted).toEqual([]);
    expect(storageSpy).not.toHaveBeenCalled();
  });
});

describe("live action panel", () => {
  it("redeems a staged code and shows the approval with its request id", async () => {
    const methods: string[] = [];
    const handler = stubActionFetch();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) => {
        methods.push(init?.method ?? "GET");
        return handler(input, init);
      }),
    );
    const storageSpy = vi.fn();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);
    await screen.findByText(LIVE_ROWS.rows[0]?.citation ?? "");
    expect(await screen.findByText("STAGED")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.approveButton }));
    const field = await screen.findByLabelText(ACTION_CHROME.en.codeLabel);
    fireEvent.change(field, { target: { value: CODE } });
    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton }));

    expect(await screen.findByText(ACTION_CHROME.en.approvedNote)).toBeInTheDocument();
    expect(screen.getByText("sha256:approval")).toBeInTheDocument();
    expect(screen.getByText("REQ-ACT-1")).toBeInTheDocument();
    expect(methods).toContain("POST");
    expect(storageSpy).not.toHaveBeenCalled();
  });

  it("explains an expired code with the typed refusal and keeps the dialog open", async () => {
    vi.stubGlobal(
      "fetch",
      stubActionFetch({
        "/api/v1/screening/actions/pairing/redeem": typedRefusal(
          "PAIRING_CODE_INVALID",
          "that code is expired; begin again in the terminal",
          403,
        ),
      }),
    );
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);
    await screen.findByText("STAGED");
    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.approveButton }));
    fireEvent.change(await screen.findByLabelText(ACTION_CHROME.en.codeLabel), {
      target: { value: CODE },
    });
    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.submitCodeButton }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("PAIRING_CODE_INVALID");
    expect(screen.getByLabelText(ACTION_CHROME.en.codeLabel)).toBeInTheDocument();
  });

  it("defers with a reason and publishes to a current generation", async () => {
    vi.stubGlobal("fetch", vi.fn(stubActionFetch()));
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);
    await screen.findByText("STAGED");

    fireEvent.change(screen.getByLabelText(ACTION_CHROME.en.reasonLabel), {
      target: { value: "awaiting full text" },
    });
    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.deferButton }));
    expect(await screen.findByText(ACTION_CHROME.en.deferredNote)).toBeInTheDocument();
    expect(screen.getByText("REQ-ACT-2")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: ACTION_CHROME.en.publishButton }));
    expect(await screen.findByText(ACTION_CHROME.en.publishedNote)).toBeInTheDocument();
    expect(screen.getByText("GEN-UI-ACT-2")).toBeInTheDocument();
  });

  it("sends one request on a double press while pending", async () => {
    let posts = 0;
    let release: (value: Response) => void = () => undefined;
    const gate = new Promise<Response>((resolve) => {
      release = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) => {
        const url = String(input);
        if ((init?.method ?? "GET") === "POST" && url.endsWith("/actions/publish")) {
          posts += 1;
          return gate;
        }
        return stubActionFetch()(input, init);
      }),
    );
    setQuery(`?source=live&console=${CONSOLE}`);

    render(<ScreeningPage locale="en" />);
    await screen.findByText("STAGED");
    const publish = screen.getByRole("button", { name: ACTION_CHROME.en.publishButton });
    fireEvent.click(publish);
    fireEvent.click(publish);
    await waitFor(() => expect(posts).toBe(1));
    expect(publish).toBeDisabled();
    release(jsonResponse(PUBLISH_OK));
    expect(await screen.findByText(ACTION_CHROME.en.publishedNote)).toBeInTheDocument();
  });
});

describe("action chrome is localised without touching the catalogs", () => {
  it("carries every action string in every locale, none of them English in translation", () => {
    for (const locale of ["en", "fr", "ar"] as Locale[]) {
      const chrome = ACTION_CHROME[locale];
      expect(Object.keys(chrome).length).toBeGreaterThan(10);
      for (const value of Object.values(chrome)) {
        expect(value.trim()).not.toBe("");
      }
    }
    for (const locale of ["fr", "ar"] as Locale[]) {
      for (const key of Object.keys(ACTION_CHROME.en) as (keyof typeof ACTION_CHROME.en)[]) {
        expect(ACTION_CHROME[locale][key]).not.toBe(ACTION_CHROME.en[key]);
      }
    }
  });
});
