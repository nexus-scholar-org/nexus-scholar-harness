import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import { isScreeningApiError } from "@/lib/screening-api";
import {
  decisionEvent,
  getConflicts,
  getPrismaPreview,
  getProposal,
  getQueue,
  getRecord,
  getSettings,
  getSummary,
  newEventId,
  postEvents,
  prepare,
} from "@/lib/screening-v1";

/**
 * The M1a client against the engine's own fixtures (`tests/fixtures/screening_api/`,
 * written by `scripts/generate_screening_api_fixtures.py` from a real console run).
 * Each call is answered with the recorded response for the recorded request, so a
 * drift in path, method, body or field names fails here, not in the browser.
 */

// vitest runs from apps/research-ui (jsdom gives import.meta.url a non-file scheme).
const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;

interface Fixture {
  name: string;
  request: { method: string; path: string; scope: string; json?: unknown };
  response: { status: number; body: unknown };
}

function fixture(name: string): Fixture {
  return JSON.parse(readFileSync(`${FIXTURES}${name}.json`, "utf-8")) as Fixture;
}

function answerWith(fx: Fixture) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return new Response(JSON.stringify(fx.response.body), {
        status: fx.response.status,
        headers: { "content-type": "application/json" },
      });
    }),
  );
  return calls;
}

function expectRequest(calls: { url: string; init?: RequestInit }[], fx: Fixture) {
  expect(calls).toHaveLength(1);
  const url = new URL(calls[0].url, "http://localhost");
  const want = new URL(fx.request.path, "http://localhost");
  expect(url.pathname).toBe(`/api/console${want.pathname}`);
  for (const [key, value] of want.searchParams) expect(url.searchParams.get(key)).toBe(value);
  expect((calls[0].init?.method ?? "GET").toUpperCase()).toBe(fx.request.method);
  if (fx.request.json !== undefined) expect(JSON.parse(String(calls[0].init?.body))).toEqual(fx.request.json);
}

afterEach(() => vi.unstubAllGlobals());

describe("screening v1 client against the engine fixtures", () => {
  it("reads every GET fixture through the proxy and returns the body unchanged", async () => {
    const reads: [string, () => Promise<unknown>, (body: never) => unknown][] = [
      ["summary_start", () => getSummary(""), (b) => b],
      ["summary_done", () => getSummary(""), (b) => b],
      ["queue_needs_you", () => getQueue("", { view: "needs_you" }), (b) => b],
      ["queue_decided_empty", () => getQueue("", { view: "decided" }), (b) => b],
      ["record_detail", () => getRecord("", "STU-5501d9dbf159a23a786423d1b11f46f4"), (b) => b],
      ["proposal_revealed", () => getProposal("", "STU-5501d9dbf159a23a786423d1b11f46f4"), (b: { proposal: unknown }) => b.proposal],
      ["settings_default", () => getSettings(""), (b) => b],
      ["prisma_preview", () => getPrismaPreview(""), (b) => b],
      ["conflicts_open", () => getConflicts(""), (b: { items: unknown }) => b.items],
    ];
    for (const [name, call, pick] of reads) {
      const fx = fixture(name);
      const calls = answerWith(fx);
      await expect(call(), name).resolves.toEqual(pick(fx.response.body as never));
      expectRequest(calls, fx);
      vi.unstubAllGlobals();
    }
  });

  it("posts the recorded event bodies and returns their per-event results", async () => {
    for (const name of ["events_accepted", "events_conflict", "events_duplicate", "events_refused_reason_code", "events_refused_stale_binding"]) {
      const fx = fixture(name);
      const calls = answerWith(fx);
      const events = (fx.request.json as { events: never[] }).events;
      await expect(postEvents("", events), name).resolves.toEqual((fx.response.body as { results: unknown }).results);
      expectRequest(calls, fx);
      vi.unstubAllGlobals();
    }
  });

  it("surfaces typed refusals with the engine's code, never one of its own", async () => {
    const hidden = fixture("proposal_hidden");
    answerWith(hidden);
    const error = await getProposal("", "STU-5501d9dbf159a23a786423d1b11f46f4").catch((e: unknown) => e);
    expect(isScreeningApiError(error) && error.code).toBe("PROPOSAL_HIDDEN");
    vi.unstubAllGlobals();

    const snapshot = fixture("prepare_snapshot_not_accepted");
    answerWith(snapshot);
    const refused = await prepare("", 20).catch((e: unknown) => e);
    expect(isScreeningApiError(refused) && [refused.code, refused.status]).toEqual(["SNAPSHOT_NOT_ACCEPTED", 409]);
  });

  it("covers every fixture the engine writes", () => {
    const used = new Set([
      "summary_start", "summary_done", "queue_needs_you", "queue_decided_empty", "record_detail",
      "proposal_revealed", "proposal_hidden", "settings_default", "prisma_preview", "conflicts_open",
      "events_accepted", "events_conflict", "events_duplicate", "events_refused_reason_code",
      "events_refused_stale_binding", "prepare_snapshot_not_accepted",
      // Covered elsewhere: the phone scope (M2), the resolve and "more decided" event sequences.
      "phone_scope_refused", "conflict_resolved", "events_more_decided",
    ]);
    const present = readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).map((f) => f.replace(/\.json$/, ""));
    expect(present.filter((name) => !used.has(name))).toEqual([]);
  });
});

describe("decision events built by the client", () => {
  it("writes a UUIDv7 event id ordered by time", () => {
    const id = newEventId(Date.UTC(2026, 10, 5), new Uint8Array(10));
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    expect(newEventId(1000) < newEventId(2000)).toBe(true);
  });

  it("is HUMAN, carries the record's binding, and keeps a reason only on EXCLUDE", () => {
    const record = JSON.parse(readFileSync(`${FIXTURES}record_detail.json`, "utf-8")).response.body;
    const include = decisionEvent({ record, screenerId: "researcher:local", outcome: "INCLUDE", reasonCode: "EXC-01", criteria: [] });
    expect(include).toMatchObject({ method: "HUMAN", reason_code: null, binding: record.binding, device: "desktop", proposal_shown: null });
    const exclude = decisionEvent({ record, screenerId: "researcher:local", outcome: "EXCLUDE", reasonCode: "EXC-01", criteria: [], supersedes: include.event_id });
    expect(exclude).toMatchObject({ reason_code: "EXC-01", supersedes: include.event_id });
    // Engine fields are never set by the client.
    for (const field of ["received_at", "token_scope", "changed_after_reveal"]) expect(exclude).not.toHaveProperty(field);
  });
});
