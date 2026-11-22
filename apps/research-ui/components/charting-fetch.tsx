"use client";

import { Fragment, useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type MouseEvent as ReactMouseEvent, type ReactNode, type RefObject } from "react";
import {
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  DocumentMagnifyingGlassIcon,
  ExclamationTriangleIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/outline";

import type { Locale } from "@/i18n";
import { Button, Hint } from "@/components/ui/base";
import { isScreeningApiError } from "@/lib/screening-api";
import { localDate, localStamp } from "@/lib/local-time";
import {
  cancelFetch,
  fetchedHref,
  getFetchRun,
  getFetchTried,
  startFetch,
  type ChartingRow,
  type FetchPlan,
  type FetchRun,
  type FetchTried,
  type PendingFetch,
} from "@/lib/charting-api";
import { CHARTING_COPY, cc, refusalWords, type ChartingCopyKey } from "@/lib/charting-copy";
import {
  ACTIVE_STATES,
  ANNOUNCE_EVERY,
  ENDED_STATES,
  IDENTITY_KEY,
  addressPhrases,
  checksWords,
  discardedWords,
  errorCount,
  checkFailurePhrases,
  errorPhrases,
  identityOf,
  licenceOf,
  nowPhrase,
  openalexNotAsked,
  outcomePhrase,
  pmcGaveNoPdf,
  recentAnswer,
  serviceWords,
  servicePhrases,
  versionPhrase,
  type Identity,
  type Values,
  type Words,
} from "@/lib/charting-fetch";
import { UNREACHABLE_CODES, fileSize } from "@/lib/charting-logic";

import { FOCUS_RING } from "./charting-cells";

/**
 * The look-up of open-access copies (M12a Part F, spec 03), shared by the
 * charting table (spec 01) and the one-study view (spec 02): the plan panel, the
 * run card, the end summary, the "Fetched, to confirm" file of a row with its
 * Open, Confirm and Discard, the line of a row's last look-up and the panel of
 * what was tried. The engine decides every count and outcome; these pieces only
 * put its answers into words, with hosts, the e-mail and the names of settings
 * kept left to right.
 */

/** Polling while a run is running or cancelling (spec 03 "Data in"). */
export const POLL_MS = 2000;

const SETTING = /(SCHOLAR_[A-Z_]+|\.env\b)/;

/** Literal text with the names of settings and files kept left to right. */
function withSettings(text: string, key: string): ReactNode {
  const parts = text.split(SETTING);
  if (parts.length === 1) return text;
  return parts.map((part, i) =>
    SETTING.test(part) ? (
      <span key={`${key}-${i}`} dir="ltr" className="font-mono">
        {part}
      </span>
    ) : (
      <Fragment key={`${key}-${i}`}>{part}</Fragment>
    ),
  );
}

/**
 * One sentence of the copy with its holes filled; the holes named in `ltr`
 * (a host, the e-mail, a file name) are left-to-right islands, never translated.
 */
export function Say({ locale, k, values = {}, ltr = [], bdi = [] }: Readonly<{ locale: Locale; k: ChartingCopyKey; values?: Values; ltr?: readonly string[]; bdi?: readonly string[] }>) {
  const template = CHARTING_COPY[locale][k];
  const parts = template.split(/(\{\w+\})/);
  return (
    <>
      {parts.map((part, i) => {
        const hole = /^\{(\w+)\}$/.exec(part)?.[1];
        if (!hole) return <Fragment key={i}>{withSettings(part, String(i))}</Fragment>;
        if (!(hole in values)) throw new Error(`charting copy "${k}" needs {${hole}}`);
        const value = String(values[hole]);
        if (ltr.includes(hole)) {
          return (
            <span key={i} dir="ltr">
              {value}
            </span>
          );
        }
        // Record prose (a title) keeps its own direction.
        if (bdi.includes(hole)) return <bdi key={i}>{value}</bdi>;
        return <Fragment key={i}>{withSettings(value, String(i))}</Fragment>;
      })}
    </>
  );
}

function refusalOf(error: unknown): { code: string; message: string } {
  if (!isScreeningApiError(error)) return { code: "ENGINE_UNREACHABLE", message: "" };
  return { code: error.code, message: error.serverMessage };
}

// ---------------------------------------------------------------- the run, polled

export type FetchRunState = {
  run: FetchRun | null;
  /** The first read of the run answered (or failed). */
  loaded: boolean;
  /** A poll failed while a run was shown: the card says so and polls again. */
  lost: boolean;
  /** The run card's own live region: the start, every 25 records, the end. */
  announce: string;
  /** This page saw the run running: its end reads "finished" rather than "Last look-up". */
  watched: boolean;
  load: () => Promise<void>;
  start: (ids: readonly string[] | null) => Promise<FetchRun>;
  cancel: () => Promise<void>;
  refresh: () => Promise<void>;
};

/**
 * The run of this workspace: read once when the screen is ready, then every two
 * seconds while it runs or is cancelling. `onChange` hears each new answer, so
 * the screen can read its rows again as files arrive.
 */
export function useFetchRun(origin: string, t: Words, n: (value: number) => string, onChange?: (run: FetchRun, previous: FetchRun | null) => void): FetchRunState {
  const [run, setRun] = useState<FetchRun | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [lost, setLost] = useState(false);
  const [announce, setAnnounce] = useState("");
  const [watched, setWatched] = useState(false);
  const runRef = useRef<FetchRun | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bucket = useRef(-1);
  const alive = useRef(true);
  const changed = useRef(onChange);
  changed.current = onChange;
  const words = useRef({ t, n });
  words.current = { t, n };

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const adopt = useCallback((next: FetchRun) => {
    const previous = runRef.current;
    runRef.current = next;
    setRun(next);
    const { t: say, n: num } = words.current;
    if (ACTIVE_STATES.has(next.state)) {
      setWatched(true);
      const reached = next.reached ?? 0;
      const step = Math.floor(reached / ANNOUNCE_EVERY);
      if (bucket.current >= 0 && step > bucket.current && reached < (next.total ?? 0)) {
        setAnnounce(say("charting.fetch.announce.progress", { reached: num(reached), total: num(next.total ?? 0) }));
      }
      bucket.current = Math.max(bucket.current, step);
    } else if (previous && ACTIVE_STATES.has(previous.state) && ENDED_STATES.has(next.state)) {
      setAnnounce(say("charting.fetch.announce.done", { downloaded: num(next.downloaded ?? 0) }));
    }
    changed.current?.(next, previous);
  }, []);

  const poll = useCallback(async (): Promise<void> => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    try {
      const next = await getFetchRun(origin);
      if (!alive.current) return;
      setLost(false);
      adopt(next);
      if (ACTIVE_STATES.has(next.state)) timer.current = setTimeout(() => void poll(), POLL_MS);
    } catch {
      if (!alive.current) return;
      // Only a run on the screen is polled again; a first read that fails says nothing.
      if (runRef.current && ACTIVE_STATES.has(runRef.current.state)) {
        setLost(true);
        timer.current = setTimeout(() => void poll(), POLL_MS);
      }
    }
  }, [origin, adopt]);

  const load = useCallback(async () => {
    await poll();
    if (alive.current) setLoaded(true);
  }, [poll]);

  const start = useCallback(
    async (ids: readonly string[] | null) => {
      const next = await startFetch(origin, ids);
      bucket.current = 0;
      setLost(false);
      adopt(next);
      setAnnounce(words.current.t("charting.fetch.announce.started", { total: words.current.n(next.total ?? 0) }));
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void poll(), POLL_MS);
      return next;
    },
    [origin, adopt, poll],
  );

  const cancel = useCallback(async () => {
    const next = await cancelFetch(origin);
    adopt(next);
    if (ACTIVE_STATES.has(next.state) && !timer.current) timer.current = setTimeout(() => void poll(), POLL_MS);
  }, [origin, adopt, poll]);

  return { run, loaded, lost, announce, watched, load, start, cancel, refresh: poll };
}

// ---------------------------------------------------------------- the waiting file of a row

/** "Fetched, to confirm": words and an icon on a plain surface with a dashed border, the draft mark (spec 03, question 2). */
export function FetchBadge({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <span
      data-badge="fetch-to-confirm"
      data-role="neutral"
      data-draft=""
      className="inline-flex items-center gap-1 rounded-sm border border-dashed border-ink-muted bg-leaf px-2 py-0.5 text-xs font-semibold leading-4 text-ink"
    >
      <DocumentMagnifyingGlassIcon aria-hidden="true" className="size-3.5 shrink-0" data-icon />
      <span>{cc(locale, "charting.fetch.status.toConfirm")}</span>
    </span>
  );
}

const IDENTITY_ICON: Record<Identity, typeof CheckCircleIcon> = {
  doi: CheckCircleIcon,
  title: CheckCircleIcon,
  notFound: ExclamationTriangleIcon,
  notChecked: QuestionMarkCircleIcon,
};

/** The identity result in words and an icon; "Not found in the file" is `unclear` text on its soft tint. */
export function IdentityLine({ locale, identity, hint = true }: Readonly<{ locale: Locale; identity: string | null | undefined; hint?: boolean }>) {
  const kind = identityOf(identity);
  const IconOf = IDENTITY_ICON[kind];
  const words = cc(locale, IDENTITY_KEY[kind]);
  return (
    <span className="inline-flex items-center gap-0.5" data-identity={kind}>
      <span className={`inline-flex items-center gap-1 rounded-sm px-1 ${kind === "notFound" ? "bg-unclear-soft text-unclear" : "text-ink"}`} data-role={kind === "notFound" ? "unclear" : "neutral"}>
        <IconOf aria-hidden="true" className="size-4 shrink-0" data-icon />
        <span>{words}</span>
      </span>
      {hint ? <Hint locale={locale} label={words} text={cc(locale, "charting.fetch.tip.identity")} textKey="charting.fetch.tip.identity" /> : null}
    </span>
  );
}

/**
 * The File column of a row whose fetched file waits (spec 03 "Fetched, to
 * confirm (row)"): size; source and host; version; licence; identity result; a
 * warning when the same bytes wait or sit on another record; Open, Confirm and
 * Discard. On a phone it is read-only: Open as a 44 px link and the desktop line.
 */
export function PendingFile({
  locale,
  origin,
  row,
  pending,
  titleOf,
  phone = false,
  responsive = false,
  disabled = false,
  hints = true,
  onConfirm,
  onDiscard,
  onOpen,
}: Readonly<{
  locale: Locale;
  origin: string;
  row: ChartingRow;
  pending: PendingFetch;
  titleOf: (studyId: string) => string;
  phone?: boolean;
  /** Confirm and Discard leave below 640 px, and the desktop line shows there (the one-study view). */
  responsive?: boolean;
  disabled?: boolean;
  hints?: boolean;
  onConfirm?: () => void;
  onDiscard?: () => void;
  onOpen?: (event: ReactMouseEvent<HTMLAnchorElement>) => void;
}>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const title = row.title ?? row.study_id;
  const version = versionPhrase({ ...pending, provider: pending.source });
  const licence = licenceOf(pending.licence);
  const service = serviceWords(t, pending.source);
  const line = "text-xs text-ink";
  return (
    <span className="flex flex-col items-start gap-0.5" data-pending-file={pending.manifest_row}>
      {pending.size ? (
        <span dir="ltr" className="text-xs text-ink-muted" data-fetch-size>
          {fileSize(pending.size)}
        </span>
      ) : null}
      <span className={`${line} max-w-full truncate`} data-fetch-source>
        {pending.host ? <Say locale={locale} k="charting.fetch.source" values={{ service, host: pending.host }} ltr={["host"]} /> : service}
      </span>
      <span className={`${line} inline-flex items-center gap-0.5`} data-fetch-version>
        <span>{t(version.key, version.values)}</span>
        {hints && !phone ? <Hint locale={locale} label={t(version.key, version.values)} text={t("charting.fetch.tip.version")} textKey="charting.fetch.tip.version" /> : null}
      </span>
      <span className={line} data-fetch-licence>
        {licence ? <Say locale={locale} k="charting.fetch.licence" values={{ licence }} ltr={["licence"]} /> : t("charting.fetch.licenceNone")}
      </span>
      <span className={line}>
        <IdentityLine locale={locale} identity={pending.identity} hint={hints && !phone} />
      </span>
      {(pending.duplicate_of ?? []).map((other) => (
        <span key={other} className="inline-flex items-start gap-1 rounded-sm bg-unclear-soft px-1 text-xs text-unclear" data-role="unclear" data-fetch-duplicate={other}>
          <ExclamationTriangleIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0" data-icon />
          <span>
            <Say locale={locale} k="charting.fetch.duplicate" values={{ title: titleOf(other) }} bdi={["title"]} />
          </span>
        </span>
      ))}
      <span className="flex flex-wrap items-center gap-1">
        <a
          href={fetchedHref(origin, row.study_id)}
          target="_blank"
          rel="noopener"
          onClick={onOpen}
          aria-label={t("charting.fetch.openFor", { title })}
          className={`inline-flex min-h-11 items-center gap-1 px-1 text-xs text-brand ${FOCUS_RING}`}
          data-open-fetched
        >
          <ArrowTopRightOnSquareIcon aria-hidden="true" className="size-4" />
          {t("charting.fetch.open")}
          {phone ? null : <kbd className="text-xs opacity-80">O</kbd>}
        </a>
        {phone ? null : (
          // In the one-study view the two actions leave below 640 px (the phone is read-only, question 7).
          <span className={`${responsive ? "hidden sm:inline-flex" : "inline-flex"} flex-wrap items-center gap-1`} data-fetch-actions>
            <Button variant="quiet" className="px-1 text-xs" disabled={disabled} onClick={onConfirm} aria-label={t("charting.fetch.confirmFor", { title })} data-fetch-confirm>
              <CheckCircleIcon aria-hidden="true" className="size-4" />
              {t("charting.fetch.confirm")} <kbd className="text-xs opacity-80">C</kbd>
            </Button>
            <Button variant="quiet" className="px-1 text-xs" disabled={disabled} onClick={onDiscard} aria-label={t("charting.fetch.discardFor", { title })} data-fetch-discard>
              {t("charting.fetch.discard")} <kbd className="text-xs opacity-80">D</kbd>
            </Button>
          </span>
        )}
      </span>
      {phone || responsive ? (
        <span className={`text-xs text-ink-muted ${responsive && !phone ? "sm:hidden" : ""}`} data-fetch-mobile>
          {t("charting.fetch.mobile")}
        </span>
      ) : null}
    </span>
  );
}

/** Under a row's status: its last look-up ("Looked up 2026-11-22: no open copy listed") and a discard that stands. */
export function LookupLines({ locale, row }: Readonly<{ locale: Locale; row: ChartingRow }>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const ft = row.fulltext;
  const last = ft.last_lookup;
  const outcome = last && !ft.pending_fetch && !ft.attachment ? outcomePhrase(t, last) : null;
  const discarded = ft.discarded_fetch && !ft.pending_fetch ? discardedWords(t, ft.discarded_fetch) : null;
  if (!outcome && !discarded) return null;
  return (
    <>
      {outcome && last ? (
        <span className="mt-1 text-xs text-ink-muted" data-last-lookup={last.outcome ?? ""}>
          {t("charting.fetch.row.last", { date: localDate(last.at), outcome: t(outcome.key, outcome.values) })}
          {last.try_later ? <Hint locale={locale} label={t(outcome.key, outcome.values)} text={t("charting.fetch.tip.tryLater")} textKey="charting.fetch.tip.tryLater" /> : null}
        </span>
      ) : null}
      {discarded ? (
        <span className="mt-1 text-xs text-ink-muted" data-discarded>
          <bdi>{discarded}</bdi>
        </span>
      ) : null}
    </>
  );
}

/**
 * What was tried for one record (spec 03): its newest manifest row, read when
 * the panel opens: the run and time, each service and its answer, each address
 * (at most three), the checks, PubMed Central when it gave no PDF, and that
 * this is not a paywall determination. Nothing tried says so.
 */
export function TriedPanel({ locale, origin, studyId, id, onClose }: Readonly<{ locale: Locale; origin: string; studyId: string; id: string; onClose: () => void }>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; tried: FetchTried } | { status: "refused"; code: string }>({ status: "loading" });
  const heading = useId();
  useEffect(() => {
    const controller = new AbortController();
    getFetchTried(origin, studyId, controller.signal)
      .then((tried) => setState({ status: "ready", tried }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setState({ status: "refused", code: refusalOf(error).code });
      });
    return () => controller.abort();
  }, [origin, studyId]);

  const row = state.status === "ready" ? state.tried.rows[state.tried.rows.length - 1] : undefined;
  return (
    <div id={id} role="region" aria-labelledby={heading} className="mt-2 max-w-md space-y-1 rounded-md border border-rule bg-paper p-3 text-xs text-ink" data-tried>
      <p id={heading} className="font-semibold">
        {row ? t("charting.fetch.tried.title", { date: localStamp(row.time) }) : t("charting.fetch.tried.open")}
        {row?.run_id ? (
          <span className="ms-2 font-mono font-normal text-ink-muted" dir="ltr">
            {row.run_id}
          </span>
        ) : null}
      </p>
      {state.status === "loading" ? <p aria-busy="true">{t("charting.fetch.tried.loading")}</p> : null}
      {state.status === "refused" ? (
        <p role="alert" className="text-blocked" data-refusal={state.code}>
          {UNREACHABLE_CODES.has(state.code) || state.code === "ENGINE_UNREACHABLE" ? t("charting.refusal.OFFLINE") : refusalWords(locale, state.code)}
        </p>
      ) : null}
      {state.status === "ready" && !row ? <p data-tried-nothing>{t("charting.fetch.tried.nothing")}</p> : null}
      {row ? (
        <>
          <ul className="space-y-0.5" data-tried-services>
            {servicePhrases(t, row).map((line, i) => (
              <li key={i}>{t("charting.fetch.tried.service", line)}</li>
            ))}
          </ul>
          <ul className="space-y-0.5" data-tried-addresses>
            {addressPhrases(t, row).map((line, i) => (
              <li key={i} className="[overflow-wrap:anywhere]">
                <Say locale={locale} k={line.key} values={line.values} ltr={["host"]} />
              </li>
            ))}
          </ul>
          {checksWords(t, row) ? <p data-tried-checks>{checksWords(t, row)}</p> : null}
          {pmcGaveNoPdf(row) ? <p data-tried-pmc>{t("charting.fetch.tried.pmc")}</p> : null}
          <p className="font-medium" data-tried-not-paywall>
            {t("charting.fetch.tried.notPaywall")}
          </p>
        </>
      ) : null}
      <Button variant="quiet" className="px-1 text-xs" onClick={onClose} data-tried-close>
        {t("charting.fetch.tried.close")}
      </Button>
    </div>
  );
}

/** The quiet "What was tried" disclosure and its panel. */
export function TriedDisclosure({ locale, origin, row, open, onToggle }: Readonly<{ locale: Locale; origin: string; row: ChartingRow; open: boolean; onToggle: (open: boolean) => void }>) {
  const panelId = `tried-${row.study_id.replace(/[^A-Za-z0-9_-]/g, "")}`;
  return (
    <>
      <Button variant="quiet" className="px-1 text-xs" aria-expanded={open} aria-controls={panelId} onClick={() => onToggle(!open)} data-tried-open>
        {cc(locale, "charting.fetch.tried.open")}
      </Button>
      {open ? <TriedPanel locale={locale} origin={origin} studyId={row.study_id} id={panelId} onClose={() => onToggle(false)} /> : null}
    </>
  );
}

// ---------------------------------------------------------------- the plan, the run card and the summary

export type PlanState =
  | { status: "counting"; ids: string[] | null }
  | { status: "ready"; ids: string[] | null; plan: FetchPlan }
  | { status: "mailto"; ids: string[] | null };

/** Whether a plan asks any service at all (a record with a DOI or an arXiv id). */
export function planAsks(plan: FetchPlan): boolean {
  return plan.with_doi + plan.with_arxiv_only > 0;
}

/**
 * The look-up plan (spec 03 "Look-up plan"): the count, the services, the
 * e-mail and what is left out, before anything is sent. Enter starts, Esc
 * cancels; "Start the look-up" is a quiet bordered button (question 10).
 */
export function PlanBlock({
  locale,
  state,
  one,
  scopeAll,
  busy,
  blockRef,
  onStart,
  onCancel,
}: Readonly<{
  locale: Locale;
  state: PlanState;
  one: boolean;
  scopeAll: boolean;
  busy: boolean;
  blockRef?: RefObject<HTMLElement | null>;
  onStart: () => void;
  onCancel: () => void;
}>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const heading = useId();
  const summaryClass = `min-h-11 cursor-pointer py-3 leading-5 rounded-sm ${FOCUS_RING}`;
  if (state.status === "mailto") {
    return (
      <section ref={blockRef as RefObject<HTMLElement>} tabIndex={-1} aria-labelledby={heading} className={`rounded-md bg-blocked-soft px-4 py-3 text-blocked ${FOCUS_RING}`} data-fetch-plan="mailto">
        <div role="alert" data-refusal="MAILTO_NOT_SET">
          <p id={heading}>
            <Say locale={locale} k="charting.refusal.MAILTO_NOT_SET" />
          </p>
          <details className="text-xs">
            <summary className={summaryClass}>{t("charting.details")}</summary>
            <span className="font-mono" dir="ltr">
              MAILTO_NOT_SET
            </span>
          </details>
        </div>
        <Button variant="quiet" onClick={onCancel} data-fetch-plan-cancel>
          {t("charting.fetch.plan.cancel")}
        </Button>
      </section>
    );
  }
  const counting = state.status === "counting";
  const plan = state.status === "ready" ? state.plan : null;
  const nothing = plan !== null && !planAsks(plan);
  const n = (value: number) => String(value);
  return (
    <section
      ref={blockRef as RefObject<HTMLElement>}
      tabIndex={-1}
      aria-labelledby={heading}
      aria-busy={counting || undefined}
      className={`space-y-2 rounded-md border border-rule-strong bg-leaf px-4 py-3 ${FOCUS_RING}`}
      data-fetch-plan={counting ? "counting" : nothing ? "nothing" : "ready"}
    >
      {counting ? (
        <p id={heading} className="text-ink">
          {t("charting.fetch.plan.counting")}
        </p>
      ) : plan && nothing ? (
        <p id={heading} className="text-ink">
          {t("charting.fetch.plan.nothing", { n: n(plan.total) })}
        </p>
      ) : plan ? (
        <>
          <p id={heading} className="font-medium text-ink">
            {one ? t("charting.fetch.plan.titleOne") : t("charting.fetch.plan.title", { n: n(plan.asked) })}
          </p>
          <ul className="space-y-1 text-sm text-ink" data-fetch-plan-lines>
            {scopeAll ? <li data-plan-line="scope">{t("charting.fetch.plan.scopeAll")}</li> : null}
            {plan.with_doi > 0 ? (
              <li data-plan-line="unpaywall">
                <Say locale={locale} k="charting.fetch.plan.unpaywall" values={{ email: plan.email, n: n(plan.with_doi) }} ltr={["email"]} />
              </li>
            ) : null}
            {plan.with_arxiv_only > 0 ? <li data-plan-line="arxiv">{t("charting.fetch.plan.arxiv", { n: n(plan.with_arxiv_only) })}</li> : null}
            {plan.services.openalex === "asked" ? <li data-plan-line="openalex">{t("charting.fetch.plan.openalexAsked")}</li> : null}
            {plan.services.openalex === "not_asked" ? (
              <li data-plan-line="openalex">
                <Say locale={locale} k="charting.fetch.plan.openalexNot" />
              </li>
            ) : null}
            {plan.neither > 0 ? <li data-plan-line="skipped">{t("charting.fetch.plan.skipped", { n: n(plan.neither) })}</li> : null}
            {plan.already_have_file + plan.waiting > 0 ? <li data-plan-line="already">{t("charting.fetch.plan.already", { n: n(plan.already_have_file + plan.waiting) })}</li> : null}
            {plan.discarded > 0 ? <li data-plan-line="discarded">{t("charting.fetch.plan.discarded", { n: n(plan.discarded) })}</li> : null}
            <li data-plan-line="only">{t("charting.fetch.plan.only")}</li>
          </ul>
        </>
      ) : null}
      <div className="flex flex-wrap items-center gap-3">
        {plan && !nothing ? (
          <>
            <span className="text-xs text-ink-muted">{t("charting.fetch.plan.keys")}</span>
            <Button variant="secondary" disabled={busy} onClick={onStart} data-fetch-start>
              {t("charting.fetch.plan.start")}
            </Button>
          </>
        ) : null}
        <Button variant="quiet" onClick={onCancel} data-fetch-plan-cancel>
          {t("charting.fetch.plan.cancel")}
        </Button>
      </div>
    </section>
  );
}

/**
 * The run card (spec 03 "Running"): a progress bar with its words, the counts,
 * what the run does now, the last eight requests behind "Requests", and "Cancel
 * the look-up". On a phone it is plain text, with no button.
 */
export function RunCard({
  locale,
  run,
  lost,
  offline,
  canCancel,
  phone = false,
  n,
  onCancel,
}: Readonly<{ locale: Locale; run: FetchRun; lost: boolean; offline: boolean; canCancel: boolean; phone?: boolean; n: (value: number) => string; onCancel: () => void }>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const [open, setOpen] = useState(false);
  const heading = useId();
  const listId = useId();
  const total = run.total ?? 0;
  const reached = run.reached ?? 0;
  const progress = t("charting.fetch.run.progress", { reached: n(reached), total: n(total) });
  const now = nowPhrase(t, run);
  const cancelling = run.state === "cancelling";
  const requests = (run.recent_requests ?? []).slice(-8);
  return (
    <section aria-labelledby={heading} className="space-y-2 rounded-md border border-rule bg-leaf px-4 py-3 text-sm text-ink" data-fetch-run={run.state}>
      <h2 id={heading} className="font-semibold">
        {t("charting.fetch.run.title")}
      </h2>
      {phone ? (
        <p data-fetch-progress-text>{progress}</p>
      ) : (
        <div className="flex flex-wrap items-center gap-3">
          <div
            role="progressbar"
            aria-labelledby={heading}
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={reached}
            aria-valuetext={progress}
            className="h-2 w-64 max-w-full overflow-hidden rounded-full border border-rule-strong bg-paper"
            data-fetch-progress
          >
            <span className="flex h-full bg-ink-muted" style={{ width: `${total > 0 ? Math.min(100, (reached / total) * 100) : 0}%` }} />
          </div>
          <span data-fetch-progress-text>{progress}</span>
        </div>
      )}
      <p data-fetch-counts>
        {t("charting.fetch.run.counts", { found: n(run.found ?? 0), downloaded: n(run.downloaded ?? 0), failed: n(run.failed_checks ?? 0), errors: n(errorCount(run)) })}
      </p>
      {cancelling ? (
        <p data-fetch-cancelling>{t("charting.fetch.run.cancelling")}</p>
      ) : now ? (
        <p data-fetch-now>
          <Say locale={locale} k={now.key} values={now.values} ltr={["host"]} />
        </p>
      ) : null}
      {lost ? <p data-fetch-lost>{t("charting.fetch.run.progressLost")}</p> : null}
      {offline ? <p data-fetch-offline>{t("charting.fetch.run.offline")}</p> : null}
      {phone ? null : (
        <div className="flex flex-wrap items-start gap-3">
          <Button variant="quiet" className="px-1" aria-expanded={open} aria-controls={listId} onClick={() => setOpen(!open)} data-fetch-requests>
            {t("charting.fetch.run.requests")}
          </Button>
          {cancelling ? null : (
            <Button variant="secondary" disabled={!canCancel} onClick={onCancel} data-fetch-cancel>
              {t("charting.fetch.run.cancel")}
            </Button>
          )}
        </div>
      )}
      {open && !phone ? (
        <ul id={listId} className="space-y-0.5 text-xs text-ink-muted" data-fetch-request-list>
          {requests.map((request, i) => (
            <li key={i}>
              <Say locale={locale} k="charting.fetch.run.request" values={{ host: request.host, answer: recentAnswer(t, request.answer) }} ltr={["host"]} />
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

/** The card of a run the console did not finish, or one that stopped with an error (questions 8). */
export function InterruptedCard({ locale, run, n, phone = false, onDismiss }: Readonly<{ locale: Locale; run: FetchRun; n: (value: number) => string; phone?: boolean; onDismiss: () => void }>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const values = { reached: n(run.reached ?? 0), total: n(run.total ?? 0) };
  return (
    <section className="space-y-2 rounded-md border border-rule bg-leaf px-4 py-3 text-sm text-ink" role="status" data-fetch-run={run.state}>
      <p>{run.state === "failed" ? t("charting.fetch.run.failed", values) : t("charting.fetch.run.interrupted", values)}</p>
      {phone ? null : (
        <Button variant="quiet" className="px-1" onClick={onDismiss} data-fetch-dismiss>
          {t("charting.fetch.summary.dismiss")}
        </Button>
      )}
    </section>
  );
}

/**
 * The end summary (spec 03 "End summary"), `role="status"`: every count with
 * its number, the errors by class in words, OpenAlex when it was not asked,
 * "Show the n to confirm", "Select the n to try later" (it selects; it never
 * starts a run) and "Dismiss". On a phone, plain text and no button.
 */
export function SummaryCard({
  locale,
  run,
  watched,
  toConfirm,
  tryLater,
  phone = false,
  n,
  onShow,
  onSelect,
  onDismiss,
}: Readonly<{
  locale: Locale;
  run: FetchRun;
  watched: boolean;
  toConfirm: number;
  tryLater: number;
  phone?: boolean;
  n: (value: number) => string;
  onShow: () => void;
  onSelect: () => void;
  onDismiss: () => void;
}>) {
  const t: Words = (key, values) => cc(locale, key, values);
  const heading = useId();
  const when = localStamp(run.finished_at ?? run.started_at ?? "");
  const title = !watched
    ? t("charting.fetch.summary.titleLast", { when })
    : run.state === "cancelled"
      ? t("charting.fetch.summary.titleCancelled", { when })
      : t("charting.fetch.summary.title", { when });
  const errors = errorPhrases(run, n, t);
  const checks = checkFailurePhrases(run, n, t);
  const line = (key: ChartingCopyKey, value: number | undefined, data: string, extra?: ReactNode) => (
    <li data-summary-line={data}>
      {t(key, { n: n(value ?? 0) })}
      {extra}
    </li>
  );
  return (
    <section role="status" aria-labelledby={heading} className="space-y-2 rounded-md border border-rule bg-leaf px-4 py-3 text-sm text-ink" data-fetch-summary={run.state}>
      <h2 id={heading} className="font-semibold">
        {title}
      </h2>
      <ul className="grid gap-x-6 gap-y-0.5 sm:grid-cols-2">
        {line("charting.fetch.summary.asked", run.total, "asked")}
        {line("charting.fetch.summary.found", run.found, "found")}
        {line("charting.fetch.summary.downloaded", run.downloaded, "downloaded")}
        {line(
          "charting.fetch.summary.failedChecks",
          run.failed_checks,
          "failedChecks",
          checks.length ? (
            <ul className="ms-4 list-disc text-ink-muted" data-summary-checks>
              {checks.map((c, i) => (
                <li key={i}>{t(c.key, c.values)}</li>
              ))}
            </ul>
          ) : null,
        )}
        {line(
          "charting.fetch.summary.errors",
          errorCount(run),
          "errors",
          errors.length ? (
            <ul className="ms-4 list-disc text-ink-muted" data-summary-errors>
              {errors.map((e, i) => (
                <li key={i}>{t(e.key, e.values)}</li>
              ))}
            </ul>
          ) : null,
        )}
        {line("charting.fetch.summary.noPdf", run.no_direct_pdf, "noPdf")}
        {line("charting.fetch.summary.noCopy", run.no_open_copy, "noCopy")}
        {line("charting.fetch.summary.skipped", run.skipped_no_id, "skipped")}
        {line("charting.fetch.summary.notReached", run.not_reached, "notReached")}
        {run.left_out?.changed_during_run ? line("charting.fetch.summary.changed", run.left_out.changed_during_run, "changed") : null}
        {line(
          "charting.fetch.summary.tryLater",
          run.try_later,
          "tryLater",
          phone ? null : <Hint locale={locale} label={t("charting.fetch.summary.tryLater", { n: n(run.try_later ?? 0) })} text={t("charting.fetch.tip.tryLater")} textKey="charting.fetch.tip.tryLater" />,
        )}
      </ul>
      {openalexNotAsked(run) ? <p data-summary-openalex>{t("charting.fetch.summary.openalexNot")}</p> : null}
      {phone ? null : (
        <div className="flex flex-wrap items-center gap-2">
          {toConfirm > 0 ? (
            <Button variant="secondary" onClick={onShow} data-summary-show>
              {t("charting.fetch.summary.showToConfirm", { n: n(toConfirm) })}
            </Button>
          ) : null}
          {tryLater > 0 ? (
            <Button variant="quiet" className="px-1" onClick={onSelect} data-summary-select>
              {t("charting.fetch.summary.selectTryLater", { n: n(tryLater) })}
            </Button>
          ) : null}
          <Button variant="quiet" className="px-1" onClick={onDismiss} data-fetch-dismiss>
            {t("charting.fetch.summary.dismiss")}
          </Button>
        </div>
      )}
    </section>
  );
}

/** Focus an element once it is on the page (the plan panel takes focus when it appears). */
export function useFocusOnShow(ref: RefObject<HTMLElement | null>, shown: boolean, key: unknown) {
  useLayoutEffect(() => {
    if (shown) ref.current?.focus();
  }, [ref, shown, key]);
}
