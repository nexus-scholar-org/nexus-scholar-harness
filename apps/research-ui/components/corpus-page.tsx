"use client";

import { useEffect, useRef, useState } from "react";

import { formatNumber, translate, type Locale } from "@/i18n";
import {
  getCorpusPage,
  getPublicationStatus,
  getWorkspaceStatus,
  isScreeningApiError,
  type CorpusPage,
  type CorpusRecord,
  type PublicationStatus,
  type WorkspaceStatus,
} from "@/lib/screening-api";
import { demoCorpusExcluded, demoCorpusIncluded } from "@/lib/mock-corpus";

/**
 * The screening corpus screen (packet UI-08, paged reads).
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
 * - `?source=live` swaps the counts for `GET /ui/workspace/status` and
 *   `GET /ui/publication-status`, and the rows for `GET /ui/corpus/{kind}`.
 *
 * The corpus route is paged and filtered **on the console**. The excluded set
 * is ~13.5k rows (~27 MB as the raw dump) on the pilot workspace, so the screen
 * must never download it whole: it asks for one 25-row page at a time, and a
 * filter query narrows the stored set before the page is cut. The excluded
 * page is only requested after the reader asks for it.
 *
 * Three presentation rules are load-bearing:
 *
 * 1. **No client-side counting as authority.** The headline numbers come from
 *    the status read. The filter and the page window decide which rows are
 *    printed, never what the corpus contains.
 * 2. **No inferred reason.** A row's reason is the console's `reason_code`, or
 *    the criterion it cites; when neither exists the row says the harness
 *    stored neither instead of guessing one.
 * 3. **No fixture fallback in live mode.** A refused read shows the server's
 *    typed code; demonstration rows never stand in for workspace data.
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

type BootState =
  | { status: "idle" }
  | { status: "loading"; origin: string }
  | {
      status: "ready";
      origin: string;
      workspace: WorkspaceStatus;
      publication: PublicationStatus;
    }
  | { status: "error"; origin: string; error: unknown };

type ListState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; page: CorpusPage; appending: boolean }
  | { status: "error"; error: unknown };

const PAGE_SIZE = 25;
/** Long enough to finish a word, short enough that the list feels responsive. */
const FILTER_DEBOUNCE_MS = 250;

/** The console origin the live source reads, or null when not requested. */
function readLiveOrigin(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "live") return null;
  return params.get("console") ?? "";
}

function decisionLabel(locale: Locale, decision: string): string {
  const token = decision.trim().toUpperCase();
  if (token === "INCLUDE") return translate(locale, "screening.decision.include");
  if (token === "EXCLUDE") return translate(locale, "screening.decision.exclude");
  return translate(locale, "screening.decision.unclear");
}

/** The stored reason, or the criterion the row cites, or nothing. */
function rowReason(row: CorpusRecord): string | null {
  const code = row.reason_code?.trim();
  return code ? code : null;
}

function rowCriterion(row: CorpusRecord): string | null {
  const criterion = row.criterion?.trim();
  return criterion ? criterion : null;
}

function rowTitle(row: CorpusRecord): string {
  return (row.title ?? row.workspace_id ?? "").trim();
}

/** One printed row: the stored citation, provenance and verdict, nothing else. */
function CorpusRow({ locale, row }: { locale: Locale; row: CorpusRecord }) {
  const reason = rowReason(row);
  const criterion = rowCriterion(row);
  const showReason = reason !== null && reason !== criterion;
  return (
    <li className="border-b border-rule py-4">
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
        <span className="text-ink">{decisionLabel(locale, row.decision)}</span>
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
}

function CorpusRows({ locale, rows }: { locale: Locale; rows: CorpusRecord[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-sm leading-6 text-ink-muted">{translate(locale, "corpus.noMatch")}</p>
    );
  }
  return (
    <ol className="border-t border-rule-strong">
      {rows.map((row, index) => (
        <CorpusRow key={`${row.workspace_id}-${index}`} locale={locale} row={row} />
      ))}
    </ol>
  );
}

/** The server's typed refusal, or whatever the transport threw. */
function refusalText(error: unknown): { code: string; message: string } {
  if (isScreeningApiError(error)) {
    return {
      code: error.code,
      message: error.serverMessage ?? error.message,
    };
  }
  return { code: "UNKNOWN_ERROR", message: String(error) };
}

export function CorpusPage({ locale }: { locale: Locale }) {
  const [source] = useState<SourceMode>(() => {
    const origin = readLiveOrigin();
    return origin ? { kind: "live", origin } : { kind: "fixture" };
  });
  const [boot, setBoot] = useState<BootState>({ status: "idle" });
  const [included, setIncluded] = useState<ListState>({ status: "idle" });
  const [excluded, setExcluded] = useState<ListState>({ status: "idle" });
  const [filter, setFilter] = useState("");
  const [debouncedFilter, setDebouncedFilter] = useState("");
  const [includedLimit, setIncludedLimit] = useState(PAGE_SIZE);
  const [excludedLimit, setExcludedLimit] = useState(PAGE_SIZE);

  const includedAbort = useRef<AbortController | null>(null);
  const excludedAbort = useRef<AbortController | null>(null);
  const excludedStarted = useRef(false);
  const excludedFilter = useRef<string | null>(null);

  // Counts and currentness are read once per source; they do not change when
  // the reader types in the filter.
  useEffect(() => {
    if (source.kind !== "live") return;
    let cancelled = false;
    (async () => {
      setBoot({ status: "loading", origin: source.origin });
      try {
        const [workspace, publication] = await Promise.all([
          getWorkspaceStatus(source.origin),
          getPublicationStatus(source.origin),
        ]);
        if (!cancelled) {
          setBoot({ status: "ready", origin: source.origin, workspace, publication });
        }
      } catch (error: unknown) {
        if (!cancelled) setBoot({ status: "error", origin: source.origin, error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [source]);

  // Debounce the live filter: one request per settled word, not per keystroke.
  // The demonstration path filters locally and needs no timer.
  useEffect(() => {
    if (source.kind !== "live") return;
    const timer = setTimeout(() => setDebouncedFilter(filter.trim()), FILTER_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [filter, source]);

  // The included list loads whenever the console metadata is ready and the
  // settled filter changes. Every load asks for page 0; paging appends below.
  useEffect(() => {
    if (source.kind !== "live" || boot.status !== "ready") return;
    const origin = source.origin;
    includedAbort.current?.abort();
    const controller = new AbortController();
    includedAbort.current = controller;
    setIncluded({ status: "loading" });
    getCorpusPage(
      "included",
      origin,
      { q: debouncedFilter, limit: PAGE_SIZE, offset: 0 },
      controller.signal,
    )
      .then((page) => {
        if (!controller.signal.aborted) {
          setIncluded({ status: "ready", page, appending: false });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setIncluded({ status: "error", error });
      });
    return () => controller.abort();
  }, [source, boot.status, debouncedFilter]);

  // A settled filter re-cuts an already-loaded excluded list. The list stays
  // idle until the reader asks for it, so opening the screen pulls no page.
  useEffect(() => {
    if (source.kind !== "live") return;
    if (!excludedStarted.current) return;
    if (excludedFilter.current === debouncedFilter) return;
    excludedFilter.current = debouncedFilter;
    void loadExcludedPage(0, false);
    // `loadExcludedPage` is stable in behaviour; the guard above is what
    // keeps this effect from firing on unrelated renders.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedFilter, source]);

  async function loadIncludedPage(offset: number, append: boolean) {
    if (source.kind !== "live") return;
    includedAbort.current?.abort();
    const controller = new AbortController();
    includedAbort.current = controller;
    setIncluded((previous) =>
      append && previous.status === "ready"
        ? { ...previous, appending: true }
        : { status: "loading" },
    );
    try {
      const page = await getCorpusPage(
        "included",
        source.origin,
        { q: debouncedFilter, limit: PAGE_SIZE, offset },
        controller.signal,
      );
      if (controller.signal.aborted) return;
      setIncluded((previous) =>
        append && previous.status === "ready"
          ? {
              status: "ready",
              page: {
                ...page,
                offset: previous.page.offset,
                records: [...previous.page.records, ...page.records],
              },
              appending: false,
            }
          : { status: "ready", page, appending: false },
      );
    } catch (error: unknown) {
      if (controller.signal.aborted) return;
      setIncluded({ status: "error", error });
    }
  }

  async function loadExcludedPage(offset: number, append: boolean) {
    if (source.kind !== "live") return;
    excludedAbort.current?.abort();
    const controller = new AbortController();
    excludedAbort.current = controller;
    setExcluded((previous) =>
      append && previous.status === "ready"
        ? { ...previous, appending: true }
        : { status: "loading" },
    );
    try {
      const page = await getCorpusPage(
        "excluded",
        source.origin,
        { q: debouncedFilter, limit: PAGE_SIZE, offset },
        controller.signal,
      );
      if (controller.signal.aborted) return;
      setExcluded((previous) =>
        append && previous.status === "ready"
          ? {
              status: "ready",
              page: {
                ...page,
                offset: previous.page.offset,
                records: [...previous.page.records, ...page.records],
              },
              appending: false,
            }
          : { status: "ready", page, appending: false },
      );
    } catch (error: unknown) {
      if (controller.signal.aborted) return;
      setExcluded({ status: "error", error });
    }
  }

  function askForExcluded() {
    excludedStarted.current = true;
    excludedFilter.current = debouncedFilter;
    void loadExcludedPage(0, false);
  }

  // The demonstration rows are used only when the URL did not ask for live
  // data. In live mode an unfinished read is an unfinished read.
  const includedRows =
    source.kind === "live"
      ? included.status === "ready"
        ? included.page.records
        : []
      : demoCorpusIncluded;
  const excludedRows =
    source.kind === "live"
      ? excluded.status === "ready"
        ? excluded.page.records
        : []
      : demoCorpusExcluded;

  const needle = filter.trim().toLowerCase();
  const match = (row: CorpusRecord) => {
    if (needle === "") return true;
    const haystack = [
      rowTitle(row),
      row.provider ?? "",
      row.year ? String(row.year) : "",
      row.reason_code ?? "",
      row.criterion ?? "",
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  };
  const visibleIncluded = includedRows.filter(match);
  const visibleExcluded = excludedRows.filter(match);

  const chrome = CORPUS_CHROME[locale];
  const liveCounts = source.kind === "live" && boot.status === "ready" ? boot.workspace : null;
  const includedTotal = liveCounts ? liveCounts.included_count : demoCorpusIncluded.length;
  const excludedTotal = liveCounts ? liveCounts.excluded_count : demoCorpusExcluded.length;

  const liveFailure =
    source.kind === "live"
      ? boot.status === "error"
        ? boot.error
        : included.status === "error"
          ? included.error
          : null
      : null;
  const corpusReady =
    source.kind === "fixture" || (boot.status === "ready" && included.status !== "error");

  const includedPage = included.status === "ready" ? included.page : null;
  const excludedPage = excluded.status === "ready" ? excluded.page : null;

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
            {boot.status === "idle" || boot.status === "loading" ? (
              <p role="status" className="text-sm leading-6 text-ink-muted">
                {translate(locale, "overview.recordLoading")}
              </p>
            ) : liveFailure !== null ? (
              <div>
                <p className="text-sm leading-6 text-warning">{chrome.liveUnavailable}</p>
                <p className="mt-2 text-sm leading-6 text-ink-muted">
                  <bdi dir="ltr">{refusalText(liveFailure).code}</bdi>
                  {": "}
                  <bdi dir="ltr">{refusalText(liveFailure).message}</bdi>
                </p>
              </div>
            ) : boot.status === "ready" &&
              includedPage !== null &&
              includedPage.corpus_total === 0 &&
              (boot.workspace.excluded_count ?? 0) === 0 ? (
              <p className="text-sm leading-6 text-ink-muted">{chrome.liveEmpty}</p>
            ) : boot.status === "ready" ? (
              <div>
                <dl className="border-t border-rule-strong">
                  <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                    <dt className="text-sm font-medium leading-6 text-ink">Workspace</dt>
                    <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                      <bdi>{boot.workspace.workspace}</bdi>
                    </dd>
                  </div>
                  <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                    <dt className="text-sm font-medium leading-6 text-ink">Phase</dt>
                    <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                      <bdi>{boot.workspace.phase ?? "unknown"}</bdi>
                    </dd>
                  </div>
                  <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                    <dt className="text-sm font-medium leading-6 text-ink">Publication</dt>
                    <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                      <bdi>{boot.publication.status}</bdi>
                      {boot.publication.message ? (
                        <>
                          {" — "}
                          <bdi>{boot.publication.message}</bdi>
                        </>
                      ) : null}
                    </dd>
                  </div>
                </dl>
              </div>
            ) : null}
          </section>
        ) : null}

        {corpusReady ? (
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
                <label
                  htmlFor="corpus-filter"
                  className="block text-sm font-medium leading-6 text-ink"
                >
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
                {source.kind === "live" && included.status === "loading" ? (
                  <p role="status" className="text-sm leading-6 text-ink-muted">
                    {translate(locale, "overview.recordLoading")}
                  </p>
                ) : visibleIncluded.length === 0 ? (
                  <p className="text-sm leading-6 text-ink-muted">
                    {source.kind === "live"
                      ? includedPage !== null && includedPage.corpus_total === 0
                        ? translate(locale, "corpus.emptyIncluded")
                        : translate(locale, "corpus.noMatch")
                      : includedRows.length === 0
                        ? translate(locale, "corpus.emptyIncluded")
                        : translate(locale, "corpus.noMatch")}
                  </p>
                ) : (
                  <>
                    <CorpusRows
                      locale={locale}
                      rows={
                        source.kind === "live"
                          ? visibleIncluded
                          : visibleIncluded.slice(0, includedLimit)
                      }
                    />
                    {source.kind === "live"
                      ? includedPage !== null && includedPage.records.length < includedPage.total
                        ? (
                            <button
                              type="button"
                              onClick={() =>
                                void loadIncludedPage(includedPage.records.length, true)
                              }
                              disabled={included.status === "ready" && included.appending}
                              className="mt-4 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
                            >
                              {translate(locale, "corpus.showMore")}
                            </button>
                          )
                        : null
                      : visibleIncluded.length > includedLimit ? (
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
                    onClick={askForExcluded}
                    className="mt-3 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink"
                  >
                    {translate(locale, "corpus.loadExcluded")}
                  </button>
                </div>
              ) : source.kind === "live" && excluded.status === "loading" ? (
                <p role="status" className="mt-4 text-sm leading-6 text-ink-muted">
                  {translate(locale, "overview.recordLoading")}
                </p>
              ) : source.kind === "live" && excluded.status === "error" ? (
                <p className="mt-4 text-sm leading-6 text-warning">
                  <bdi dir="ltr">{refusalText(excluded.error).code}</bdi>
                  {": "}
                  <bdi dir="ltr">{refusalText(excluded.error).message}</bdi>
                </p>
              ) : visibleExcluded.length === 0 ? (
                <p className="mt-4 text-sm leading-6 text-ink-muted">
                  {source.kind === "live"
                    ? excludedPage !== null && excludedPage.corpus_total === 0
                      ? translate(locale, "corpus.emptyExcluded")
                      : translate(locale, "corpus.noMatch")
                    : excludedRows.length === 0
                      ? translate(locale, "corpus.emptyExcluded")
                      : translate(locale, "corpus.noMatch")}
                </p>
              ) : (
                <div className="mt-4">
                  <CorpusRows
                    locale={locale}
                    rows={
                      source.kind === "live"
                        ? visibleExcluded
                        : visibleExcluded.slice(0, excludedLimit)
                    }
                  />
                  {source.kind === "live"
                    ? excludedPage !== null && excludedPage.records.length < excludedPage.total
                      ? (
                          <button
                            type="button"
                            onClick={() => void loadExcludedPage(excludedPage.records.length, true)}
                            disabled={excluded.status === "ready" && excluded.appending}
                            className="mt-4 border border-rule-strong px-3 py-2 text-sm font-medium leading-6 text-ink disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
                          >
                            {translate(locale, "corpus.showMore")}
                          </button>
                        )
                      : null
                    : visibleExcluded.length > excludedLimit ? (
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
