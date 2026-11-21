import { act, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ChartingPage } from "@/components/charting-page";
import type { Locale } from "@/i18n";
import type { ChartingEvent, ChartingRow, ChartingTable } from "@/lib/charting-api";

/**
 * A small in-memory charting engine for the screen's tests (M12a Part A). It
 * answers in the shapes of `src/scholar_harness/console/api/charting.py`
 * (`tests/console/test_charting_api.py` shows each): the table, the events
 * route with per-event results and the touched rows, the attachment route and
 * the CSV. It applies status and decision events the way the engine does
 * (the value of the newest event, `heads` naming it) and refuses an event for a
 * record that is not kept (`RECORD_NOT_KEPT`).
 */

export interface Call {
  method: string;
  path: string;
  body?: unknown;
}

export interface FakeEngine {
  table: ChartingTable;
  calls: Call[];
  /** Answer every request with this instead (a code, or "unreachable" for a failed fetch). */
  fail?: { status: number; code: string } | "unreachable";
  /** Refuse each event of these studies with this code. */
  refuse?: Record<string, string>;
  /** Hold the table read until the test releases it. */
  hold?: Promise<void>;
}

export function makeRow(i: number, over: Partial<ChartingRow> = {}): ChartingRow {
  const id = `STU-${String(i).padStart(3, "0")}`;
  return {
    study_id: id,
    title: `Study number ${i}`,
    authors: ["Sa, I."],
    year: 2018 + (i % 5),
    venue: "Remote Sensing",
    doi: `10.3390/rs${1000 + i}`,
    url: null,
    abstract: null,
    arxiv_id: null,
    round: 1,
    arm: "databases",
    round_label: "Databases",
    generation_id: "gen-1",
    ta_decision: i % 3 === 0 ? "MAYBE" : "INCLUDE",
    ta_reason: "",
    kept: true,
    new_since: null,
    fulltext: { status: "to_get", requested_on: null, reason: null, reason_text: null, attachment: null, link: null },
    ft_decision: null,
    heads: { fulltext_status: null, fulltext_decision: null, attachment: null, link: null },
    ...over,
  };
}

export function counts(rows: ChartingRow[]): ChartingTable["counts"] {
  const live = rows.filter((r) => r.kept);
  const by = (test: (r: ChartingRow) => boolean) => live.filter(test).length;
  return {
    kept: live.length,
    to_get: by((r) => r.fulltext.status === "to_get"),
    requested: by((r) => r.fulltext.status === "requested"),
    retrieved: by((r) => r.fulltext.status === "retrieved"),
    not_retrieved: by((r) => r.fulltext.status === "not_retrieved"),
    included: by((r) => r.ft_decision?.outcome === "INCLUDE"),
    excluded: by((r) => r.ft_decision?.outcome === "EXCLUDE"),
    to_decide: by((r) => !r.ft_decision),
  };
}

export function makeTable(rows: ChartingRow[], over: Partial<ChartingTable> = {}): ChartingTable {
  return {
    shape: "charting.table-v1",
    screener_id: "researcher:local",
    publication: { status: "CURRENT", code: null, generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z", round: 1 },
    rounds: [{ round: 1, arm: "databases", generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z" }],
    chasing_pending: false,
    stale: false,
    changes: null,
    read_only: false,
    read_only_code: null,
    reason_options: [
      { code: "EXC-01", label: "Not a crop field", kind: "exclusion", category: null },
      { code: "FAILS-INC-01", label: "UAV imagery", kind: "fails_inclusion", category: null },
      { code: "OTHER", label: "Other", kind: "other", category: null },
    ],
    not_retrieved_reasons: ["no_access", "not_found", "no_reply", "other"],
    counts: counts(rows),
    rows,
    ...over,
  };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function apply(engine: FakeEngine, event: ChartingEvent): { event_id: string; result: string; refusal?: { code: string; message: string } } {
  const row = engine.table.rows.find((r) => r.study_id === event.study_id);
  const refused = engine.refuse?.[event.study_id];
  if (refused) return { event_id: event.event_id, result: "refused", refusal: { code: refused, message: refused.toLowerCase() } };
  if (!row || !row.kept) return { event_id: event.event_id, result: "refused", refusal: { code: "RECORD_NOT_KEPT", message: "not kept" } };
  const value = event.value as Record<string, string> | null;
  if (event.kind === "fulltext_status") {
    const v = value ?? { status: "to_get" };
    row.fulltext = { ...row.fulltext, status: v.status as never, requested_on: v.requested_on ?? null, reason: (v.reason ?? null) as never, reason_text: v.reason_text ?? null };
    row.heads = { ...row.heads, fulltext_status: event.event_id };
  } else if (event.kind === "fulltext_decision") {
    row.ft_decision = value ? ({ outcome: value.outcome, reason_code: value.reason_code ?? null, reason_text: value.reason_text ?? null } as never) : null;
    row.heads = { ...row.heads, fulltext_decision: event.event_id };
  } else if (event.kind === "attachment") {
    row.fulltext = { ...row.fulltext, attachment: (value as never) ?? null };
    row.heads = { ...row.heads, attachment: event.event_id };
  } else if (event.kind === "link") {
    row.fulltext = { ...row.fulltext, link: value ? (value as unknown as { url: string }).url : null };
    row.heads = { ...row.heads, link: event.event_id };
  }
  return { event_id: event.event_id, result: "accepted" };
}

/** Stub `fetch` with the fake engine; returns the engine so a test can read `calls`. */
export function installEngine(table: ChartingTable, over: Partial<FakeEngine> = {}): FakeEngine {
  const engine: FakeEngine = { table: structuredClone(table), calls: [], ...over };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, init?: RequestInit) => {
      const url = new URL(String(input), "http://localhost");
      const path = url.pathname.replace(/^\/api\/console/, "");
      const method = (init?.method ?? "GET").toUpperCase();
      let body: unknown;
      if (typeof init?.body === "string") body = JSON.parse(init.body);
      else if (init?.body) body = init.body;
      engine.calls.push({ method, path: `${path}${url.search}`, body });
      if (engine.fail === "unreachable") throw new TypeError("fetch failed");
      if (engine.fail) return json({ detail: { code: engine.fail.code, message: engine.fail.code.toLowerCase() } }, engine.fail.status);
      if (method === "GET" && path === "/api/v1/charting") {
        if (engine.hold) await engine.hold;
        return json(structuredClone(engine.table));
      }
      if (method === "POST" && path === "/api/v1/charting/events") {
        const events = (body as { events: ChartingEvent[] }).events;
        const results = events.map((e) => apply(engine, e));
        engine.table.counts = counts(engine.table.rows);
        const touched = new Set(events.map((e) => e.study_id));
        return json({ results, counts: engine.table.counts, rows: structuredClone(engine.table.rows.filter((r) => touched.has(r.study_id))) });
      }
      const attach = /^\/api\/v1\/charting\/records\/([^/]+)\/attachment$/.exec(path);
      if (attach && method === "POST") {
        const row = engine.table.rows.find((r) => r.study_id === attach[1])!;
        if (init?.headers && (init.headers as Record<string, string>)["content-type"] === "application/json") {
          const link = (body as { link: string; event_id: string });
          if (!/^https?:\/\//.test(link.link)) return json({ detail: { code: "LINK_INVALID", message: "bad link" } }, 422);
          apply(engine, { event_id: link.event_id, study_id: row.study_id, screener_id: "researcher:local", at: "", kind: "link", value: { url: link.link } });
          engine.table.counts = counts(engine.table.rows);
          return json({ result: "accepted", event_ids: [link.event_id], row: structuredClone(row), counts: engine.table.counts });
        }
        const eventId = url.searchParams.get("event_id")!;
        const statusId = url.searchParams.get("status_event_id")!;
        const ids = [eventId];
        const wasToGet = row.fulltext.status === "to_get";
        apply(engine, { event_id: eventId, study_id: row.study_id, screener_id: "researcher:local", at: "", kind: "attachment", value: { name: url.searchParams.get("name"), size: 2048, sha256: "a".repeat(64), path: `pdfs/${row.study_id}.pdf`, origin: "attached" } });
        if (wasToGet) {
          apply(engine, { event_id: statusId, study_id: row.study_id, screener_id: "researcher:local", at: "", kind: "fulltext_status", value: { status: "retrieved" } });
          ids.push(statusId);
        }
        engine.table.counts = counts(engine.table.rows);
        return json({ result: "accepted", event_ids: ids, row: structuredClone(row), counts: engine.table.counts });
      }
      if (method === "GET" && path === "/api/v1/charting/export") {
        return new Response("﻿study_id\r\n", { status: 200, headers: { "content-type": "text/csv; charset=utf-8", "content-disposition": 'attachment; filename="charting-fulltext-20261121T100000Z.csv"' } });
      }
      return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
    }),
  );
  return engine;
}

export async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

/** Render the screen and wait for the table's first answer. */
export async function renderCharting(locale: Locale = "en") {
  const view = render(<ChartingPage locale={locale} />);
  await flush();
  await flush();
  return view;
}

export function grid(): HTMLElement {
  return screen.getByRole("grid");
}

export function postedEvents(engine: FakeEngine): ChartingEvent[][] {
  return engine.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/charting/events").map((c) => (c.body as { events: ChartingEvent[] }).events);
}

/** Press a key on the element that has focus (the window listener hears it), as a person would. */
export async function press(key: string, init: Partial<KeyboardEventInit> = {}) {
  const target = (document.activeElement as HTMLElement | null) ?? document.body;
  await act(async () => {
    target.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...init }));
  });
  await flush();
}
