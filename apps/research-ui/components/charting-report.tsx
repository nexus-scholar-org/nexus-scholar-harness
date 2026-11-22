"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { ArrowDownTrayIcon, ClockIcon } from "@heroicons/react/24/outline";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, PRIMARY_LINK } from "@/components/ui/base";
import { stepHref } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import { localStamp } from "@/lib/local-time";
import {
  chartingHref,
  exportFile,
  getCharting,
  getChartingMethods,
  type ChartingMethods,
  type ChartingTable,
  type ExportView,
  type PrismaGroup,
} from "@/lib/charting-api";
import { CHARTING_REFUSAL_CODES, cc, refusalWords, type ChartingCopyKey } from "@/lib/charting-copy";
import { UNREACHABLE_CODES } from "@/lib/charting-logic";

import { FOCUS_RING } from "./charting-cells";
import { ExportLines } from "./charting-export-lines";
import { useViewport } from "./charting-page";

/**
 * Export and methods for the charting table (spec 04, M12a Part C,
 * `/charting/report`): the three downloads, the PRISMA full-text counts and the
 * methods paragraph. The engine builds every file, computes every count and
 * writes every sentence (`report.py` `methods()`); this page shows them and
 * computes none. Reading and copying write nothing; each download is the
 * engine's own record (`CHARTING_EXPORTED`, `last_export.json`), after which the
 * table is read again for the last-export line.
 *
 * The paragraph, its notes and what it does not state are engine-written
 * English for a manuscript and are never translated: they sit in
 * `lang="en" dir="ltr"` with the draft styling, because the researcher checks
 * them before use. Desktop only; a phone gets one line and a link (question 4).
 */

type Refusal = { code: string; message: string };
type Kind = ExportView | "xlsx";
type Data = { table: ChartingTable; methods: ChartingMethods };
type Load =
  | { status: "loading" }
  | { status: "ready" }
  | { status: "not_published"; refusal: Refusal }
  | { status: "refused"; refusal: Refusal }
  | { status: "offline" };

const FILES: readonly { kind: Kind; name: ChartingCopyKey; body: ChartingCopyKey }[] = [
  { kind: "fulltext", name: "charting.report.download.csvFulltext", body: "charting.report.download.csvFulltext.body" },
  { kind: "charting", name: "charting.report.download.csvCharting", body: "charting.report.download.csvCharting.body" },
  { kind: "xlsx", name: "charting.report.download.xlsx", body: "charting.report.download.xlsx.body" },
];

/** The engine's own words for a "not retrieved" reason (`report.py` `NOT_RETRIEVED_WORDS`), each with this page's words. */
const NOT_RETRIEVED_ROWS: readonly [string, ChartingCopyKey][] = [
  ["No access or paywalled", "charting.notRetrieved.noAccess"],
  ["Not found", "charting.notRetrieved.notFound"],
  ["Authors did not reply", "charting.notRetrieved.noReply"],
  ["Other", "charting.report.counts.other"],
];

const OPEN_ROWS: readonly [keyof PrismaGroup, ChartingCopyKey][] = [
  ["awaiting_retrieval", "charting.report.open.awaiting"],
  ["to_confirm", "charting.report.open.toConfirm"],
  ["retrieved_not_assessed", "charting.report.open.notAssessed"],
  ["assessed_without_full_text", "charting.report.open.noFullText"],
];

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function refusalOf(error: unknown): Refusal {
  if (!isScreeningApiError(error)) return { code: "ENGINE_UNREACHABLE", message: "" };
  return { code: error.code, message: error.serverMessage };
}

/** Hand the engine's file to the browser's download; a browser that cannot is left as it is. */
function saveFile(blob: Blob, filename: string) {
  try {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch {
    /* no object URLs here (a test page): the engine still wrote and journaled the file */
  }
}

/** A phone-sized window, read at once so a phone never asks the console for anything. */
function phoneNow(): boolean {
  return typeof window !== "undefined" && typeof window.matchMedia === "function" && !window.matchMedia("(min-width: 640px)").matches;
}

const EMPTY_GROUP: PrismaGroup = {
  sought: 0,
  not_retrieved: 0,
  not_retrieved_reasons: {},
  assessed: 0,
  excluded: 0,
  exclusion_reasons: {},
  included: 0,
  awaiting_retrieval: 0,
  to_confirm: 0,
  retrieved_not_assessed: 0,
  assessed_without_full_text: 0,
};

export function ChartingReport({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const viewport = useViewport();
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-lg border border-rule bg-leaf p-5 sm:hidden" data-phone>
        <h1 className="text-base font-normal text-ink">{t("charting.report.phone.desktopOnly")}</h1>
        <a className={`mt-3 inline-flex min-h-11 items-center text-brand underline ${FOCUS_RING}`} href={chartingHref(locale, origin)} data-phone-link>
          {t("charting.report.phone.link")}
        </a>
      </section>
      {viewport === "phone" ? null : (
        <div className="hidden sm:block" data-desktop>
          <ReportScreen locale={locale} origin={origin} />
        </div>
      )}
    </div>
  );
}

function ReportScreen({ locale, origin }: Readonly<{ locale: Locale; origin: string }>) {
  const t = useCallback((key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values), [locale]);
  // Spec 04 "Accessibility": numerals are Latin on every page of this report, Arabic included.
  const n = useCallback((value: number | undefined) => formatNumber("en", value ?? 0), []);
  const [load, setLoad] = useState<Load>({ status: "loading" });
  const [data, setData] = useState<Data | null>(null);
  const [asOf, setAsOf] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [downloading, setDownloading] = useState<Kind | null>(null);
  const [fileFailed, setFileFailed] = useState<Refusal | null>(null);
  const [announce, setAnnounce] = useState("");
  const dataRef = useRef<Data | null>(null);
  dataRef.current = data;
  const started = useRef(false);

  const read = useCallback(async () => {
    // A page that already shows its answer keeps it while it reads again (Offline: "as of").
    if (!dataRef.current) setLoad({ status: "loading" });
    try {
      const table = await getCharting(origin);
      const methods = await getChartingMethods(origin);
      setData({ table, methods });
      setAsOf(new Date().toISOString());
      setOffline(false);
      setLoad({ status: "ready" });
    } catch (error) {
      const r = refusalOf(error);
      if (UNREACHABLE_CODES.has(r.code)) {
        if (dataRef.current) setOffline(true);
        else setLoad({ status: "offline" });
      } else if (r.code === "SCREENING_NOT_PUBLISHED") setLoad({ status: "not_published", refusal: r });
      else setLoad({ status: "refused", refusal: r });
    }
  }, [origin]);

  useEffect(() => {
    if (started.current || phoneNow()) return;
    started.current = true;
    void read();
  }, [read]);

  async function download(kind: Kind) {
    if (offline || downloading || !data) return;
    setDownloading(kind);
    setFileFailed(null);
    setAnnounce(t("charting.report.preparing"));
    try {
      const { blob, filename } = kind === "xlsx" ? await exportFile(origin, "xlsx") : await exportFile(origin, "csv", kind);
      saveFile(blob, filename);
      // The browser announces its own download.
      setAnnounce("");
      try {
        const table = await getCharting(origin);
        setData((current) => (current ? { ...current, table } : current));
        setAsOf(new Date().toISOString());
      } catch (error) {
        if (UNREACHABLE_CODES.has(refusalOf(error).code)) setOffline(true);
      }
    } catch (error) {
      const r = refusalOf(error);
      if (UNREACHABLE_CODES.has(r.code)) setOffline(true);
      else setFileFailed(r);
      setAnnounce("");
    } finally {
      setDownloading(null);
    }
  }

  async function copy(paragraph: string) {
    try {
      await navigator.clipboard.writeText(paragraph);
      setAnnounce(t("charting.report.methods.copied"));
    } catch {
      setAnnounce(t("charting.report.methods.copyFailed"));
    }
  }

  /** A charting code has its own words; another code (a host or token guard) reads as a refused request, its code in Details. */
  const wordsOf = (code: string) => ((CHARTING_REFUSAL_CODES as readonly string[]).includes(code) ? refusalWords(locale, code) : t("charting.report.refused"));

  const summaryClass = `min-h-11 cursor-pointer py-3 leading-5 rounded-sm font-medium text-brand ${FOCUS_RING}`;
  const codeDetails = (code: string) => (
    <details className="text-xs">
      <summary className={summaryClass}>{t("charting.details")}</summary>
      <span className="font-mono" dir="ltr">
        {code}
      </span>
    </details>
  );
  const heading = (
    <header className="space-y-1">
      <h1 className="font-display text-[1.75rem] leading-[2.25rem] text-ink">{t("charting.report.title")}</h1>
      <p className="text-ink-muted">{t("charting.report.lede")}</p>
    </header>
  );
  const backLink = (
    <a className={`inline-flex min-h-11 items-center text-brand underline ${FOCUS_RING}`} href={chartingHref(locale, origin)} data-back>
      {t("charting.report.back")}
    </a>
  );
  const live = (
    <p role="status" aria-live="polite" className="sr-only" data-announce>
      {announce}
    </p>
  );

  if (load.status === "not_published") {
    return (
      <section aria-labelledby="report-empty" className="space-y-4" data-state="not-published">
        <h1 id="report-empty" className="font-display text-[1.75rem] leading-[2.25rem] text-ink">
          {t("charting.report.title")}
        </h1>
        <p className="max-w-2xl text-ink">{t("charting.empty.notPublished")}</p>
        <a className={`${PRIMARY_LINK} ${FOCUS_RING}`} data-variant="primary" href={stepHref(locale, "publish", origin)}>
          {t("charting.empty.goPublish")}
        </a>
        <div className="text-ink-muted">{codeDetails(load.refusal.code)}</div>
      </section>
    );
  }

  if (load.status === "refused" || load.status === "offline") {
    const code = load.status === "refused" ? load.refusal.code : "ENGINE_UNREACHABLE";
    const words =
      load.status === "offline"
        ? t("charting.offlineNoChange")
        : code === "TOKEN_SCOPE_REFUSED"
          ? t("charting.report.phone.desktopOnly")
          : wordsOf(code);
    return (
      <section className="space-y-4" data-state={load.status}>
        {heading}
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-refusal={code}>
          <p>{words}</p>
          {codeDetails(code)}
        </div>
        <Button onClick={() => void read()}>{t("charting.retry")}</Button>
        <p>{backLink}</p>
      </section>
    );
  }

  const ready = load.status === "ready" && data !== null;
  const table = data?.table ?? null;
  const methods = data?.methods ?? null;
  const nothingKept = ready && table !== null && table.rows.length === 0 && (table.counts.kept ?? 0) === 0;
  const canDownload = ready && !offline && !nothingKept && downloading === null;

  const downloadCard = (
    <section aria-labelledby="report-download-title" className="rounded-lg border border-rule bg-leaf p-5" data-download-region>
      <h2 id="report-download-title" className="font-semibold text-ink">
        {t("charting.report.download.title")}
      </h2>
      <ul className="mt-3 space-y-4">
        {FILES.map((file) => (
          <li key={file.kind} data-download-row={file.kind}>
            <Button
              className="w-full justify-start text-start"
              disabled={!canDownload}
              aria-busy={downloading === file.kind}
              aria-describedby={`report-file-${file.kind}`}
              onClick={() => void download(file.kind)}
              data-file={file.kind}
            >
              <ArrowDownTrayIcon aria-hidden="true" className="size-4 shrink-0" />
              {downloading === file.kind ? t("charting.report.preparing") : t(file.name)}
            </Button>
            <p id={`report-file-${file.kind}`} className="mt-1 text-xs text-ink-muted">
              {t(file.body)}
            </p>
          </li>
        ))}
      </ul>
      {nothingKept ? (
        <p className="mt-3 text-sm text-ink" data-no-export>
          {t("charting.report.empty.noExport")}
        </p>
      ) : null}
      {offline ? (
        <p className="mt-3 text-sm text-blocked" data-downloads-offline>
          {t("charting.offlineNoChange")}
        </p>
      ) : null}
      {fileFailed ? (
        <div role="alert" className="mt-3 rounded-md bg-blocked-soft px-4 py-3 text-sm text-blocked" data-file-failed={fileFailed.code}>
          <p>{t("charting.report.failed")}</p>
          {(CHARTING_REFUSAL_CODES as readonly string[]).includes(fileFailed.code) ? <p className="mt-1">{wordsOf(fileFailed.code)}</p> : null}
          {codeDetails(fileFailed.code)}
        </div>
      ) : null}
    </section>
  );

  const sideColumn = (
    <div className="w-full space-y-4 lg:order-2 lg:w-80 lg:shrink-0" data-side>
      {downloadCard}
      {ready && table ? (
        <ExportLines locale={locale} numberLocale="en" lastExport={table.last_export ?? null} counts={table.counts} />
      ) : (
        <p aria-hidden="true" className="h-5 w-64 max-w-full animate-pulse rounded-sm bg-rule" data-skeleton="last-export" />
      )}
      <p className="text-sm text-ink-muted" data-help>
        {t("charting.report.help")}
      </p>
    </div>
  );

  if (!ready || !table || !methods) {
    return (
      <div className="space-y-6" data-state="loading" aria-busy="true">
        {heading}
        {live}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
          {sideColumn}
          <div className="min-w-0 flex-1 space-y-6 lg:order-1">
            <div aria-hidden="true" className="h-64 animate-pulse rounded-lg bg-rule" data-skeleton="counts" />
            <div aria-hidden="true" className="h-48 animate-pulse rounded-lg bg-rule" data-skeleton="methods" />
          </div>
        </div>
        <p role="status" className="sr-only">
          {t("charting.loading")}
        </p>
      </div>
    );
  }

  const prisma = methods.figures.prisma;
  const total = prisma.total ?? EMPTY_GROUP;
  const groups: PrismaGroup[] = [prisma.arms?.databases ?? EMPTY_GROUP, prisma.arms?.citation_searching ?? EMPTY_GROUP, total];
  const labelOf = new Map(table.reason_options.map((o) => [o.code, o.label]));
  const knownWords = new Set(NOT_RETRIEVED_ROWS.map(([word]) => word));
  const otherWords = [...new Set(groups.flatMap((g) => Object.keys(g.not_retrieved_reasons ?? {})))].filter((w) => !knownWords.has(w)).sort();
  const codes = [...new Set(groups.flatMap((g) => Object.keys(g.exclusion_reasons ?? {})))].sort();

  const countRow = (key: string, label: ReactNode, values: number[], reason = false) => (
    <tr key={key} className="border-t border-rule" data-count-row={key}>
      <th scope="row" className={`py-2 text-start font-normal ${reason ? "ps-6 text-ink-muted" : "text-ink"}`}>
        {reason ? <span className="text-xs">{t("charting.report.counts.ofWhich")}</span> : null}
        {reason ? " " : null}
        {label}
      </th>
      {values.map((value, i) => (
        <td key={i} className="py-2 ps-4 text-end tabular-nums text-ink">
          {n(value)}
        </td>
      ))}
    </tr>
  );

  const onParagraphKey = (event: KeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    if (event.key === "c" && !event.ctrlKey && !event.metaKey && !event.altKey && target.tagName !== "INPUT" && target.tagName !== "TEXTAREA") {
      event.preventDefault();
      void copy(methods.paragraph);
    }
  };
  const onDetailsKey = (event: KeyboardEvent<HTMLDetailsElement>) => {
    const details = event.currentTarget;
    if (event.key === "Escape" && details.open) {
      event.preventDefault();
      details.open = false;
      details.querySelector<HTMLElement>("summary")?.focus();
    }
  };
  const fig = methods.figures;

  return (
    <div className="space-y-6" data-state="ready">
      {heading}
      {live}

      {offline ? (
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-banner="offline">
          <p>{t("charting.offlineNoChange")}</p>
          {asOf ? (
            <p className="mt-1 text-sm" data-as-of>
              {t("charting.report.asOf", { time: localStamp(asOf) })}
            </p>
          ) : null}
          <Button className="mt-2" onClick={() => void read()}>
            {t("charting.retry")}
          </Button>
        </div>
      ) : null}
      {table.read_only ? (
        <div className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-banner="archived">
          <p>{t("charting.archived")}</p>
          {codeDetails(table.read_only_code ?? "CHARTING_PROTOCOL_REPLACED")}
        </div>
      ) : null}
      {table.changes ? (
        <p className="rounded-md bg-brand-soft px-4 py-3 text-ink" data-banner="changes">
          {t("charting.changes", { date: localStamp(table.changes.published_at).slice(0, 10), added: n(table.changes.added), gone: n(table.changes.no_longer_kept) })}{" "}
          <a className={`text-brand underline ${FOCUS_RING}`} href={chartingHref(locale, origin)}>
            {t("charting.report.back")}
          </a>
        </p>
      ) : null}
      {table.stale ? (
        <div className="rounded-md bg-unclear-soft px-4 py-3 text-unclear" data-banner="stale">
          <p>{t("charting.stale")}</p>
          {codeDetails("GENERATION_STALE")}
        </div>
      ) : null}
      {nothingKept ? (
        <section className="rounded-md border border-rule bg-leaf p-5" data-state-line="nothing-kept">
          <p className="text-ink">{t("charting.empty.nothingKept")}</p>
          <a className={`mt-2 inline-flex min-h-11 items-center text-brand underline ${FOCUS_RING}`} href={stepHref(locale, "triage", origin)}>
            {t("charting.empty.goTriage")}
          </a>
        </section>
      ) : null}

      <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
        {sideColumn}

        <div className="min-w-0 flex-1 space-y-6 lg:order-1" data-main>
          <section aria-labelledby="report-counts-title" className="rounded-lg border border-rule bg-leaf p-5" data-counts-region>
            <h2 id="report-counts-title" className="font-semibold text-ink">
              {t("charting.report.counts.title")}
            </h2>
            {table.chasing_pending ? (
              <p className="mt-2 text-sm text-ink" data-banner="chasing">
                {t("charting.chasingPending")}
              </p>
            ) : null}
            <table className="mt-3 w-full text-sm" data-prisma>
              <caption className="pb-2 text-start text-xs text-ink-muted">{t("charting.report.counts.caption")}</caption>
              <thead>
                <tr className="text-ink-muted">
                  <th scope="col" className="py-1 text-start font-medium">
                    {t("charting.report.counts.col.what")}
                  </th>
                  <th scope="col" className="py-1 ps-4 text-end font-medium">
                    {t("charting.report.counts.col.databases")}
                  </th>
                  <th scope="col" className="py-1 ps-4 text-end font-medium">
                    {t("charting.report.counts.col.chasing")}
                  </th>
                  <th scope="col" className="py-1 ps-4 text-end font-medium">
                    {t("charting.report.counts.col.total")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {countRow("sought", t("charting.report.counts.row.sought"), groups.map((g) => g.sought))}
                {countRow("not_retrieved", t("charting.report.counts.row.notRetrieved"), groups.map((g) => g.not_retrieved))}
                {NOT_RETRIEVED_ROWS.map(([word, key]) =>
                  countRow(`not_retrieved:${word}`, t(key), groups.map((g) => g.not_retrieved_reasons?.[word] ?? 0), true),
                )}
                {otherWords.map((word) =>
                  countRow(`not_retrieved:${word}`, <bdi lang="en">{word}</bdi>, groups.map((g) => g.not_retrieved_reasons?.[word] ?? 0), true),
                )}
                {countRow("assessed", t("charting.report.counts.row.assessed"), groups.map((g) => g.assessed))}
                {countRow("excluded", t("charting.report.counts.row.excluded"), groups.map((g) => g.excluded))}
                {codes.map((code) => {
                  const label = labelOf.get(code);
                  return countRow(
                    `excluded:${code}`,
                    <>
                      <DataCell>{code}</DataCell>
                      {label && label !== code ? (
                        <>
                          {" "}
                          <bdi>{label}</bdi>
                        </>
                      ) : null}
                    </>,
                    groups.map((g) => g.exclusion_reasons?.[code] ?? 0),
                    true,
                  );
                })}
                {countRow("included", t("charting.report.counts.row.included"), groups.map((g) => g.included))}
              </tbody>
            </table>
            {Number(total.not_retrieved_decided ?? 0) > 0 ? (
              // Item 5 as changed by the researcher: the decisions taken from the abstract sit with the counts,
              // apart from the PRISMA rows and marked as not a PRISMA box (the one-box rule still holds).
              <table className="mt-4 w-full text-sm" data-abstract-decided>
                <caption className="pb-2 text-start text-xs text-ink-muted">{t("charting.report.abstract.caption")}</caption>
                <thead className="sr-only">
                  <tr>
                    <th scope="col">{t("charting.report.counts.col.what")}</th>
                    <th scope="col">{t("charting.report.counts.col.databases")}</th>
                    <th scope="col">{t("charting.report.counts.col.chasing")}</th>
                    <th scope="col">{t("charting.report.counts.col.total")}</th>
                  </tr>
                </thead>
                <tbody>
                  {countRow("abstract:decided", t("charting.report.abstract.row.decided"), groups.map((g) => Number(g.not_retrieved_decided ?? 0)))}
                  {countRow("abstract:included", t("charting.report.abstract.row.included"), groups.map((g) => Number(g.not_retrieved_included ?? 0)), true)}
                  {countRow("abstract:excluded", t("charting.report.abstract.row.excluded"), groups.map((g) => Number(g.not_retrieved_excluded ?? 0)), true)}
                </tbody>
              </table>
            ) : null}
            {total.assessed === 0 ? (
              <p className="mt-3 text-sm text-ink" data-no-decisions>
                {t("charting.report.counts.noDecisions")}
              </p>
            ) : null}
          </section>

          <section aria-labelledby="report-open-title" aria-describedby="report-open-note" className="rounded-lg border border-rule bg-leaf p-5" data-open-region>
            <h2 id="report-open-title" className="font-semibold text-ink">
              {t("charting.report.open.title")}
            </h2>
            <p id="report-open-note" className="mt-1 text-xs text-ink-muted">
              {t("charting.report.open.note")}
            </p>
            <dl className="mt-2 text-sm" data-still-open>
              {OPEN_ROWS.map(([field, key]) => {
                const value = Number(total[field] ?? 0);
                const waiting = field === "to_confirm" && value > 0;
                return (
                  <div key={field} className="flex items-center justify-between gap-4 border-t border-rule py-2" data-open-row={field} data-role={waiting ? "unclear" : undefined}>
                    <dt className={waiting ? "flex items-center gap-1.5 text-unclear" : "text-ink"}>
                      {waiting ? <ClockIcon aria-hidden="true" className="size-4 shrink-0" data-icon /> : null}
                      {t(key)}
                    </dt>
                    <dd className={`tabular-nums ${waiting ? "text-unclear" : "text-ink"}`}>{n(value)}</dd>
                  </div>
                );
              })}
            </dl>
          </section>

          <section aria-labelledby="report-methods-title" className="rounded-lg border border-rule bg-leaf p-5" onKeyDown={onParagraphKey} data-methods>
            <h2 id="report-methods-title" className="font-semibold text-ink">
              {t("charting.report.methods.title")}
            </h2>
            <div className="mt-4 rounded-lg border border-dashed border-brand bg-brand-soft p-4" data-draft>
              <span id="report-methods-draft">
                <DecisionBadge role="unclear">{t("charting.report.methods.draftBadge")}</DecisionBadge>
              </span>
              <p
                role="region"
                aria-labelledby="report-methods-title report-methods-draft"
                lang="en"
                dir="ltr"
                tabIndex={0}
                className={`mt-3 select-text text-[0.9375rem] leading-[1.5rem] text-ink ${FOCUS_RING}`}
                data-paragraph
              >
                {methods.paragraph}
              </p>
            </div>
            <p className="mt-2 text-xs text-ink-muted">{t("charting.report.methods.language")}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <Button onClick={() => void copy(methods.paragraph)} data-copy>
                {t("charting.report.methods.copy")}
              </Button>
            </div>

            {methods.caveats.length > 0 ? (
              <div className="mt-5" data-caveats>
                <h3 className="text-sm font-semibold text-ink">{t("charting.report.methods.notes")}</h3>
                <ul lang="en" dir="ltr" className="mt-1 list-disc space-y-1 ps-5 text-sm text-ink-muted">
                  {methods.caveats.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {methods.not_stated.length > 0 ? (
              <div className="mt-4" data-not-stated>
                <h3 className="text-sm font-semibold text-ink">{t("charting.report.methods.notStated")}</h3>
                <ul lang="en" dir="ltr" className="mt-1 list-disc space-y-1 ps-5 text-sm text-ink-muted">
                  {methods.not_stated.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <details className="mt-5 text-sm" onKeyDown={onDetailsKey} data-methods-details>
              <summary className={summaryClass}>{t("charting.report.methods.details")}</summary>
              <h3 className="mt-2 text-sm font-semibold text-ink">{t("charting.report.figures.title")}</h3>
              <ul className="mt-1 space-y-1 text-ink-muted" data-figures>
                <li>{t("charting.report.figures.openAccess", { used: n(fig.open_access?.used), discarded: n(fig.open_access?.discarded) })}</li>
                {(fig.open_access?.services ?? []).length > 0 ? (
                  <li>
                    {t("charting.report.figures.services", { list: "" })}
                    <bdi dir="ltr">{fig.open_access.services.join(", ")}</bdi>
                  </li>
                ) : null}
                <li>{t("charting.report.figures.reviewers", { decisions: n(fig.reviewers?.fulltext_decisions), charting: n(fig.reviewers?.charting) })}</li>
                <li>{t("charting.report.figures.charting", { charted: n(fig.charted), notCharted: n(fig.not_charted) })}</li>
                <li>{t("charting.report.figures.cells", { cellsOpen: n(fig.cells_open), requiredOpen: n(fig.required_open) })}</li>
                <li>{t("charting.report.figures.pilot", { pilot: n(fig.pilot) })}</li>
                <li>{t("charting.report.figures.amendments", { n: n((fig.amendments ?? []).length) })}</li>
                <li data-protocol-fingerprint>
                  {table.form?.protocol_fingerprint ? (
                    <>
                      {t("charting.report.figures.fingerprint")}
                      <bdi dir="ltr" className="font-mono">{table.form.protocol_fingerprint}</bdi>
                    </>
                  ) : (
                    t("charting.report.figures.fingerprintNone")
                  )}
                </li>
              </ul>
              <h3 className="mt-3 text-sm font-semibold text-ink">{t("charting.report.methods.basedOn")}</h3>
              <table className="mt-2 w-full text-xs" data-sources>
                <thead>
                  <tr className="text-ink-muted">
                    <th scope="col" className="py-1 text-start font-medium">
                      {t("charting.report.methods.file")}
                    </th>
                    <th scope="col" className="py-1 text-start font-medium">
                      {t("charting.report.methods.digest")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {methods.sources.map((source) => (
                    <tr key={source.path} className="border-t border-rule align-top">
                      <td className="py-1 pe-4">
                        <DataCell>{source.path}</DataCell>
                      </td>
                      <td className="py-1">{source.digest ? <DataCell>{source.digest}</DataCell> : null}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </section>
        </div>
      </div>

      <p>{backLink}</p>
    </div>
  );
}
