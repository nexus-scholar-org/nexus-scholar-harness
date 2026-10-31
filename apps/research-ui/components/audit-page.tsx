"use client";

import { useEffect, useState } from "react";

import { formatNumber, translate, type Locale } from "@/i18n";
import {
  getAuditFeed,
  isScreeningApiError,
  type AuditFeed,
  type AuditFeedItem,
} from "@/lib/screening-api";
import { demoAuditEvents } from "@/lib/mock-audit";

/**
 * The audit activity screen (packet UI-06).
 *
 * One job: show the journal the harness wrote, in the order it wrote it. The
 * console's feed is newest-first and this page prints the array it received;
 * it never sorts, retimes, merges, or appends an event. A failed journal line
 * is skipped by the server (reported in `GATES.md` and in the console tests),
 * not repaired here.
 *
 * Data sources, in order of precedence:
 *
 * - the default is the demonstration feed under `lib/mock-audit.ts`, covered
 *   by the shell's visible `Demonstration data` marker;
 * - `?source=live` reads `GET /api/v1/screening/ui/audit-feed` through the
 *   same-origin console proxy, so no port appears in the URL and the
 *   browser's request stays on this application's origin.
 *
 * Three presentation rules are load-bearing:
 *
 * 1. **Exact timestamps.** The stored string is printed verbatim inside a
 *    left-to-right isolate; it is never reformatted into a local timezone.
 * 2. **No inferred actor or outcome.** When the journal stored no agent or no
 *    status, the row says so rather than filling one in.
 * 3. **Technical provenance is available, not hidden.** The event id and the
 *    raw fields sit behind a disclosure so the feed stays readable while the
 *    provenance remains reachable.
 */

export const AUDIT_PAGE_SIZE = 25;

type SourceMode = { kind: "fixture" } | { kind: "live"; origin: string };

type LiveFeed =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; feed: AuditFeed }
  | { status: "error"; error: unknown };

/** The console origin the live source reads; empty means the same-origin proxy. */
function readLiveOrigin(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "live") return null;
  return params.get("console") ?? "";
}

function EventRow({ locale, event }: { locale: Locale; event: AuditFeedItem }) {
  const status = event.status?.trim().toUpperCase() ?? "";
  const failed = status === "FAILED";
  return (
    <li className="border-b border-rule py-5">
      <p className="text-sm leading-6">
        <bdi dir="ltr" className="font-medium text-ink">
          {event.action}
        </bdi>
        {status ? (
          <>
            {" · "}
            <span className={failed ? "text-warning" : "text-ink-muted"}>
              <bdi dir="ltr">{event.status}</bdi>
            </span>
          </>
        ) : (
          <>
            {" · "}
            <span className="text-ink-muted">{translate(locale, "audit.noStatus")}</span>
          </>
        )}
      </p>
      <p className="mt-1 text-sm leading-6 text-ink-muted">
        <bdi>{event.agent_or_tool?.trim() || translate(locale, "audit.noAgent")}</bdi>
      </p>
      <p className="mt-1 max-w-3xl text-sm leading-6 text-ink">
        {event.description?.trim() || translate(locale, "audit.noDescription")}
      </p>
      <details className="mt-2">
        <summary className="text-sm leading-6 text-ink-muted">
          {translate(locale, "audit.technical")}
        </summary>
        <dl className="mt-2 border-t border-rule">
          <div className="grid gap-x-6 gap-y-1 border-b border-rule py-2 lg:grid-cols-[9rem_minmax(0,1fr)]">
            <dt className="text-sm font-medium leading-6 text-ink">
              {translate(locale, "audit.timestampLabel")}
            </dt>
            <dd className="min-w-0 text-sm leading-6 text-ink-muted">
              <bdi dir="ltr">{event.timestamp ?? translate(locale, "audit.notRecorded")}</bdi>
            </dd>
          </div>
          <div className="grid gap-x-6 gap-y-1 border-b border-rule py-2 lg:grid-cols-[9rem_minmax(0,1fr)]">
            <dt className="text-sm font-medium leading-6 text-ink">
              {translate(locale, "audit.eventIdLabel")}
            </dt>
            <dd className="min-w-0 text-sm leading-6 text-ink-muted">
              <bdi dir="ltr">{event.event_id ?? translate(locale, "audit.notRecorded")}</bdi>
            </dd>
          </div>
          <div className="grid gap-x-6 gap-y-1 border-b border-rule py-2 lg:grid-cols-[9rem_minmax(0,1fr)]">
            <dt className="text-sm font-medium leading-6 text-ink">
              {translate(locale, "audit.actionLabel")}
            </dt>
            <dd className="min-w-0 text-sm leading-6 text-ink-muted">
              <bdi dir="ltr">{event.action}</bdi>
            </dd>
          </div>
        </dl>
      </details>
    </li>
  );
}

export function AuditPage({ locale }: { locale: Locale }) {
  const [source] = useState<SourceMode>(() => {
    const origin = readLiveOrigin();
    return origin === null ? { kind: "fixture" } : { kind: "live", origin };
  });
  const [live, setLive] = useState<LiveFeed>({ status: "idle" });
  const [limit, setLimit] = useState(AUDIT_PAGE_SIZE);

  useEffect(() => {
    if (source.kind !== "live") return;
    let cancelled = false;
    setLive({ status: "loading" });
    (async () => {
      try {
        const feed = await getAuditFeed(source.origin, { limit });
        if (!cancelled) setLive({ status: "ready", feed });
      } catch (error: unknown) {
        if (!cancelled) setLive({ status: "error", error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [source, limit]);

  const events = source.kind === "live" ? (live.status === "ready" ? live.feed.items : []) : demoAuditEvents;
  const total =
    source.kind === "live" && live.status === "ready" ? live.feed.total : demoAuditEvents.length;

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
            {translate(locale, "audit.eyebrow")}
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              {translate(locale, "audit.heading")}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              {translate(locale, "audit.lede")}
            </p>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-muted">
              {source.kind === "live"
                ? translate(locale, "audit.liveLede")
                : translate(locale, "audit.fixtureLede")}
            </p>
          </div>
        </section>

        {source.kind === "live" ? (
          <section className="mt-14" aria-labelledby="audit-live-title">
            <div className="mb-5">
              <p className="mb-3">
                <span
                  aria-hidden="true"
                  className="inline-flex items-center border border-evidence/45 px-2 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]"
                >
                  {translate(locale, "audit.liveStamp")}
                </span>
              </p>
              <h2 id="audit-live-title" className="font-display text-xl leading-8 text-ink">
                {translate(locale, "audit.liveStamp")}
              </h2>
            </div>
            {live.status === "idle" || live.status === "loading" ? (
              <p role="status" className="text-sm leading-6 text-ink-muted">
                {translate(locale, "overview.recordLoading")}
              </p>
            ) : live.status === "error" ? (
              <div>
                <p className="text-sm leading-6 text-warning">
                  {translate(locale, "audit.liveUnavailable")}
                </p>
                <p className="mt-2 text-sm leading-6 text-ink-muted">
                  <bdi dir="ltr">
                    {isScreeningApiError(live.error) ? live.error.code : "UNKNOWN_ERROR"}
                  </bdi>
                  {": "}
                  <bdi dir="ltr">
                    {isScreeningApiError(live.error) && live.error.serverMessage
                      ? live.error.serverMessage
                      : String(live.error)}
                  </bdi>
                </p>
              </div>
            ) : null}
          </section>
        ) : null}

        <section className="mt-14" aria-labelledby="audit-feed-title">
          <h2 id="audit-feed-title" className="font-display text-xl leading-8 text-ink">
            {translate(locale, "audit.feedHeading")}
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-muted">
            {translate(locale, "audit.newestNote")}
          </p>
          <p className="mt-2 text-sm leading-6 text-ink-muted">
            {translate(locale, "audit.countLabel")}
            {": "}
            <bdi>{formatNumber(locale, total)}</bdi>
          </p>

          {source.kind === "fixture" || live.status === "ready" ? (
            events.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-ink-muted">
                {translate(locale, "audit.empty")}
              </p>
            ) : (
              <>
                <ol className="mt-6 border-t border-rule-strong">
                  {events.map((event, index) => (
                    <EventRow
                      key={`${event.action}-${event.timestamp ?? "none"}-${index}`}
                      locale={locale}
                      event={event}
                    />
                  ))}
                </ol>
                {source.kind === "live" && live.status === "ready" && events.length < total ? (
                  <button
                    type="button"
                    onClick={() => setLimit((value) => value + AUDIT_PAGE_SIZE)}
                    className="mt-4 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink"
                  >
                    {translate(locale, "audit.showMore")}
                  </button>
                ) : null}
              </>
            )
          ) : null}
        </section>
      </div>
    </div>
  );
}
