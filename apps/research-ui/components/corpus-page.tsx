"use client";

import { useEffect, useState } from "react";

import { formatNumber, translate, type Locale } from "@/i18n";
import {
  getCorpusRecords,
  getPublicationStatus,
  getWorkspaceStatus,
  isScreeningApiError,
  type CorpusRecord,
  type PublicationStatus,
  type WorkspaceStatus,
} from "@/lib/screening-api";
import { demoCorpusExcluded, demoCorpusIncluded } from "@/lib/mock-corpus";

/**
 * The screening corpus screen (packet UI-08).
 *
 * Two jobs, and nothing else: show what the harness recorded as the corpus,
 * and show why each excluded record left. The page never decides anything -
 * every verdict it prints was written by the screening step, and every count
 * it prints was computed by the harness from the workspace bytes.
 *
 * Data sources, in order of precedence:
 *
 * - the default is the demonstration corpus under `lib/mock-corpus.ts`, with
 *   the shell's visible `Demonstration data` marker covering it;
 * - `?source=live` swaps both lists and the counts for reads against the local
 *   console over HTTP: `GET /workspace/status` (counts, phase),
 *   `GET /ui/publication-status` (whether this is a current published
 *   generation), and `GET /literature/included`.
 * - The excluded set is read only after the reader asks for it. The file is
 *   large, and opening the screen must not pull it for someone who only wanted
 *   the included list.
 *
 * Two presentation rules are load-bearing:
 *
 * 1. **No client-side counting as authority.** The headline numbers come from
 *    the status read. The filter and the page-size window only decide which
 *    already-loaded rows are printed.
 * 2. **No inferred reason.** A row's reason is the stored `reason_code`, or the
 *    violated criterion it cites; when neither exists the row says the harness
 *    stored neither instead of guessing one.
 */

/** The few strings that describe the live panel itself, kept beside it. */
export const CORPUS_CHROME = {
  en: {
    liveStamp: "Live console data",
    liveLede:
      "The counts and records below were read from the local console over HTTP. They are live workspace data, not the demonstration corpus.",
    liveUnavailable: "Live data unavailable",
    liveEmpty: "The console reports no screening corpus for this workspace.",
  },
  fr: {
    liveStamp: "Données en direct de la console",
    liveLede:
      "Les totaux et les notices ci-dessous ont été lus depuis la console locale via HTTP. Ce sont des données réelles de l'espace de travail, et non le corpus de démonstration.",
    liveUnavailable: "Données en direct indisponibles",
    liveEmpty: "La console ne signale aucun corpus de sélection pour cet espace de travail.",
  },
  ar: {
    liveStamp: "بيانات مباشرة من المنصة",
    liveLede:
      "قُرئت الأعداد والسجلات أدناه من المنصة المحلية عبر HTTP. وهي بيانات حية من مساحة العمل وليست مجموعة العرض.",
    liveUnavailable: "تعذّر جلب البيانات المباشرة",
    liveEmpty: "لا تبلغ المنصة عن أي مجموعة فرز لهذه المساحة.",
  },
} as const;

type SourceMode = { kind: "fixture" } | { kind: "live"; origin: string };

type LiveCorpus =
  | { status: "idle" }
  | { status: "loading"; origin: string }
  | {
      status: "ready";
      origin: string;
      workspace: WorkspaceStatus;
      publication: PublicationStatus;
      included: CorpusRecord[];
    }
  | { status: "error"; origin: string; error: unknown };

type ExcludedState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; records: CorpusRecord[] }
  | { status: "error"; error: unknown };

const PAGE_SIZE = 25;

/** The console origin the live source reads, or null when not requested. */
function readLiveOrigin(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "live") return null;
  return params.get("console") ?? "http://127.0.0.1:8765";
}

function decisionLabel(locale: Locale, decision: string): string {
  const token = decision.trim().toUpperCase();
  if (token === "INCLUDE") return translate(locale, "screening.decision.include");
  if (token === "EXCLUDE") return translate(locale, "screening.decision.exclude");
  return translate(locale, "screening.decision.unclear");
}

/** The stored reason, or the criterion the row cites, or nothing. */
function rowReason(row: CorpusRecord): string | null {
  const provenance = row.screening_provenance?.reason_code?.trim();
  if (provenance) return provenance;
  const violated = row.screening.violated_exclusion_criteria?.[0]?.trim();
  if (violated) return violated;
  return null;
}

function rowCriterion(row: CorpusRecord): string | null {
  const violated = row.screening.violated_exclusion_criteria?.[0]?.trim();
  if (violated) return violated;
  const matched = row.screening.matched_inclusion_criteria?.[0]?.trim();
  if (matched) return matched;
  return null;
}

function rowTitle(row: CorpusRecord): string {
  return (row.title ?? row.screening.document_title ?? row.workspace_id ?? "").trim();
}

function CorpusRows({
  locale,
  rows,
  limit,
}: {
  locale: Locale;
  rows: CorpusRecord[];
  limit: number;
}) {
  if (rows.length === 0) {
    return (
      <p className="text-sm leading-6 text-ink-muted">{translate(locale, "corpus.noMatch")}</p>
    );
  }
  return (
    <ol className="border-t border-rule-strong">
      {rows.slice(0, limit).map((row, index) => {
        const reason = rowReason(row);
        const criterion = rowCriterion(row);
        const showReason = reason !== null && reason !== criterion;
        return (
          <li key={`${row.workspace_id}-${index}`} className="border-b border-rule py-4">
            <p className="text-sm leading-6 text-ink">
              <bdi>{rowTitle(row)}</bdi>
            </p>
            <p className="mt-1 text-sm leading-6 text-ink-muted">
              {row.year !== null && row.year !== undefined ? (
                <>
                  <bdi>{String(row.year)}</bdi>
                  {" · "}
                </>
              ) : null}
              {row.provider ? (
                <>
                  <bdi>{row.provider}</bdi>
                  {" · "}
                </>
              ) : null}
              <span className="text-ink">{decisionLabel(locale, row.screening.decision)}</span>
            </p>
            <p className="mt-1 text-sm leading-6 text-ink-muted">
              {showReason ? (
                <>
                  {translate(locale, "corpus.reasonLabel")}
                  {": "}
                  <bdi dir="ltr">{reason}</bdi>
                </>
              ) : null}
              {!showReason && !criterion ? (
                <span>{translate(locale, "corpus.noReason")}</span>
              ) : null}
              {criterion ? (
                <>
                  {showReason ? " · " : null}
                  {translate(locale, "corpus.criterionLabel")}
                  {": "}
                  <bdi dir="ltr">{criterion}</bdi>
                </>
              ) : null}
            </p>
          </li>
        );
      })}
    </ol>
  );
}

export function CorpusPage({ locale }: { locale: Locale }) {
  const [source] = useState<SourceMode>(() => {
    const origin = readLiveOrigin();
    return origin ? { kind: "live", origin } : { kind: "fixture" };
  });
  const [live, setLive] = useState<LiveCorpus>({ status: "idle" });
  const [excluded, setExcluded] = useState<ExcludedState>({ status: "idle" });
  const [filter, setFilter] = useState("");
  const [includedLimit, setIncludedLimit] = useState(PAGE_SIZE);
  const [excludedLimit, setExcludedLimit] = useState(PAGE_SIZE);

  useEffect(() => {
    if (source.kind !== "live") return;
    let cancelled = false;
    (async () => {
      setLive({ status: "loading", origin: source.origin });
      try {
        const [workspace, publication, included] = await Promise.all([
          getWorkspaceStatus(source.origin),
          getPublicationStatus(source.origin),
          getCorpusRecords("included", source.origin),
        ]);
        if (!cancelled) {
          setLive({ status: "ready", origin: source.origin, workspace, publication, included });
        }
      } catch (error: unknown) {
        if (!cancelled) setLive({ status: "error", origin: source.origin, error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [source]);

  // In live mode an unfinished read is an unfinished read: the demonstration
  // rows may never stand in for workspace data the reader asked to see.
  const included =
    source.kind === "live" ? (live.status === "ready" ? live.included : []) : demoCorpusIncluded;
  const excludedRows =
    source.kind === "live" ? (excluded.status === "ready" ? excluded.records : []) : demoCorpusExcluded;

  const needle = filter.trim().toLowerCase();
  const match = (row: CorpusRecord) => {
    if (needle === "") return true;
    const haystack = [rowTitle(row), row.provider ?? "", row.year ? String(row.year) : "", rowReason(row) ?? ""]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  };
  const visibleIncluded = included.filter(match);
  const visibleExcluded = excludedRows.filter(match);

  const chrome = CORPUS_CHROME[locale];
  const liveCounts = source.kind === "live" && live.status === "ready" ? live.workspace : null;
  const includedTotal = liveCounts ? liveCounts.included_count : included.length;
  const excludedTotal = liveCounts ? liveCounts.excluded_count : excludedRows.length;

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
            {translate(locale, "corpus.eyebrow")}
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              {translate(locale, "corpus.heading")}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              {translate(locale, "corpus.lede")}
            </p>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-muted">
              {source.kind === "live" ? chrome.liveLede : translate(locale, "corpus.fixtureLede")}
            </p>
          </div>
        </section>

        {source.kind === "live" ? (
          <section className="mt-14" aria-labelledby="corpus-live-title">
            <div className="mb-5">
              <p className="mb-3">
                <span
                  aria-hidden="true"
                  className="inline-flex items-center border border-evidence/45 px-2 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]"
                >
                  {chrome.liveStamp}
                </span>
              </p>
              <h2 id="corpus-live-title" className="font-display text-xl leading-8 text-ink">
                {chrome.liveStamp}
              </h2>
            </div>
            {live.status === "idle" || live.status === "loading" ? (
              <p role="status" className="text-sm leading-6 text-ink-muted">
                {translate(locale, "overview.recordLoading")}
              </p>
            ) : live.status === "error" ? (
              <div>
                <p className="text-sm leading-6 text-warning">{chrome.liveUnavailable}</p>
                <p className="mt-2 text-sm leading-6 text-ink-muted">
                  <bdi dir="ltr">{isScreeningApiError(live.error) ? live.error.code : "UNKNOWN_ERROR"}</bdi>
                  {": "}
                  <bdi dir="ltr">
                    {isScreeningApiError(live.error) && live.error.serverMessage
                      ? live.error.serverMessage
                      : String(live.error)}
                  </bdi>
                </p>
              </div>
            ) : live.included.length === 0 && (live.workspace.excluded_count ?? 0) === 0 ? (
              <p className="text-sm leading-6 text-ink-muted">{chrome.liveEmpty}</p>
            ) : (
              <div>
                <dl className="border-t border-rule-strong">
                  <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                    <dt className="text-sm font-medium leading-6 text-ink">Workspace</dt>
                    <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                      <bdi>{live.workspace.workspace}</bdi>
                    </dd>
                  </div>
                  <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                    <dt className="text-sm font-medium leading-6 text-ink">Phase</dt>
                    <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                      <bdi>{live.workspace.phase ?? "unknown"}</bdi>
                    </dd>
                  </div>
                  <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                    <dt className="text-sm font-medium leading-6 text-ink">Publication</dt>
                    <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                      <bdi>{live.publication.status}</bdi>
                      {live.publication.message ? (
                        <>
                          {" — "}
                          <bdi>{live.publication.message}</bdi>
                        </>
                      ) : null}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </section>
        ) : null}

        {source.kind === "fixture" || live.status === "ready" ? (
          <>
        <section className="mt-14" aria-labelledby="corpus-counts-title">
          <h2 id="corpus-counts-title" className="font-display text-xl leading-8 text-ink">
            {translate(locale, "corpus.countsHeading")}
          </h2>
          <dl className="mt-4 border-t border-rule-strong">
            <div className="flex items-baseline justify-between gap-6 border-b border-rule py-4">
              <dt className="text-sm font-medium leading-6 text-ink">
                {translate(locale, "corpus.includedLabel")}
              </dt>
              <dd className="text-sm leading-6 text-ink-muted">
                <bdi>
                  {includedTotal === undefined
                    ? translate(locale, "counts.unknown")
                    : formatNumber(locale, includedTotal)}
                </bdi>
              </dd>
            </div>
            <div className="flex items-baseline justify-between gap-6 border-b border-rule py-4">
              <dt className="text-sm font-medium leading-6 text-ink">
                {translate(locale, "corpus.excludedLabel")}
              </dt>
              <dd className="text-sm leading-6 text-ink-muted">
                <bdi>
                  {excludedTotal === undefined
                    ? translate(locale, "counts.unknown")
                    : formatNumber(locale, excludedTotal)}
                </bdi>
              </dd>
            </div>
          </dl>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-muted">
            {translate(locale, "corpus.agentNote")}
          </p>
        </section>

        <section className="mt-14" aria-labelledby="corpus-included-title">
          <h2 id="corpus-included-title" className="font-display text-xl leading-8 text-ink">
            {translate(locale, "corpus.includedHeading")}
          </h2>
          <div className="mt-4">
            <label htmlFor="corpus-filter" className="block text-sm font-medium leading-6 text-ink">
              {translate(locale, "corpus.filterLabel")}
            </label>
            <input
              id="corpus-filter"
              type="search"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              className="mt-1 w-full max-w-md border border-rule-strong bg-paper px-3 py-2 text-sm leading-6 text-ink"
            />
            <p className="mt-1 max-w-3xl text-sm leading-6 text-ink-muted">
              {translate(locale, "corpus.filterHint")}
            </p>
          </div>
          <div className="mt-4">
            {visibleIncluded.length === 0 ? (
              <p className="text-sm leading-6 text-ink-muted">
                {included.length === 0
                  ? translate(locale, "corpus.emptyIncluded")
                  : translate(locale, "corpus.noMatch")}
              </p>
            ) : (
              <>
                <CorpusRows locale={locale} rows={visibleIncluded} limit={includedLimit} />
                {visibleIncluded.length > includedLimit ? (
                  <button
                    type="button"
                    onClick={() => setIncludedLimit((value) => value + PAGE_SIZE)}
                    className="mt-4 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink"
                  >
                    {translate(locale, "corpus.showMore")}
                  </button>
                ) : null}
              </>
            )}
          </div>
        </section>

        <section className="mt-14" aria-labelledby="corpus-excluded-title">
          <h2 id="corpus-excluded-title" className="font-display text-xl leading-8 text-ink">
            {translate(locale, "corpus.excludedHeading")}
          </h2>
          {source.kind === "live" && excluded.status === "idle" ? (
            <div className="mt-4">
              <p className="max-w-3xl text-sm leading-6 text-ink-muted">
                {translate(locale, "corpus.loadExcludedHint")}
              </p>
              <button
                type="button"
                onClick={async () => {
                  setExcluded({ status: "loading" });
                  try {
                    const records = await getCorpusRecords("excluded", source.origin);
                    setExcluded({ status: "ready", records });
                  } catch (error: unknown) {
                    setExcluded({ status: "error", error });
                  }
                }}
                className="mt-3 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink"
              >
                {translate(locale, "corpus.loadExcluded")}
              </button>
            </div>
          ) : excluded.status === "loading" ? (
            <p role="status" className="mt-4 text-sm leading-6 text-ink-muted">
              {translate(locale, "overview.recordLoading")}
            </p>
          ) : excluded.status === "error" ? (
            <p className="mt-4 text-sm leading-6 text-warning">
              <bdi dir="ltr">
                {isScreeningApiError(excluded.error) ? excluded.error.code : "UNKNOWN_ERROR"}
              </bdi>
              {": "}
              <bdi dir="ltr">
                {isScreeningApiError(excluded.error) && excluded.error.serverMessage
                  ? excluded.error.serverMessage
                  : String(excluded.error)}
              </bdi>
            </p>
          ) : visibleExcluded.length === 0 ? (
            <p className="mt-4 text-sm leading-6 text-ink-muted">
              {excludedRows.length === 0
                ? translate(locale, "corpus.emptyExcluded")
                : translate(locale, "corpus.noMatch")}
            </p>
          ) : (
            <div className="mt-4">
              <CorpusRows locale={locale} rows={visibleExcluded} limit={excludedLimit} />
              {visibleExcluded.length > excludedLimit ? (
                <button
                  type="button"
                  onClick={() => setExcludedLimit((value) => value + PAGE_SIZE)}
                  className="mt-4 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink"
                >
                  {translate(locale, "corpus.showMore")}
                </button>
              ) : null}
            </div>
          )}
        </section>
          </>
        ) : null}
      </div>
    </div>
  );
}
