"use client";

import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge, RecommendedBadge } from "@/components/ui/base";
import { guidanceT } from "@/lib/guidance-copy";
import { fillNodes, fillText, tryFocus } from "@/components/assist-anchor";
import { isOfflineCode, refusalFrom, type AssistRefusal } from "@/components/assist-context";
import { CHECKS_COPY, checksCountTemplate, checksT, checksTemplate, hasChecksKey } from "@/lib/checks-copy";
import { fieldLabel, STEP_NUMBER, stepLabel } from "@/lib/assist-labels";
import { providerName } from "@/lib/discovery-copy";
import { localDate, localStamp } from "@/lib/local-time";
import type { Check, CheckList } from "@/lib/inception-api";

/**
 * The checks panel and the Review readiness list (`docs/ux/shared/final/02-checks.md`,
 * M10b B3). Every row, level, count and threshold is the engine's: the panel
 * renders the list it is given, by `message_key` from its own catalogue, and
 * computes no check. It reads on load and when `reloadKey` moves (a save, a
 * job's end, a proposal decision); never on keystrokes, never by polling.
 */

export interface CheckLink {
  /** A link to a field or a screen (with its hash, when the field is on this page it is focused instead). */
  href?: string;
  hash?: string;
  /** A proposal card of 01-proposals: opened, nothing sent. */
  proposal?: string;
}

export interface ChecksPanelProps {
  locale: Locale;
  /** `panel` on a step screen; `readiness` is the Review list (all steps, grouped, step chips). */
  mode: "panel" | "readiness";
  /** For the panel's data attribute and ids. */
  name: string;
  load: () => Promise<CheckList | null>;
  dismiss: (check: Check, reason?: string) => Promise<CheckList>;
  restore: (check: Check) => Promise<CheckList>;
  reloadKey: unknown;
  link: (check: Check) => CheckLink | null;
  /** After a dismissal or a restore: the screen re-reads what depends on the checks. */
  onDecided?: () => void;
  /** The answer of a dismissal is the list for that check's step; the readiness list re-reads instead. */
  adoptAnswers?: boolean;
  dirty?: boolean;
  readOnly?: boolean;
  /** Something the screen puts under the header (the hand-off's line about earlier steps). */
  extra?: ReactNode;
}

type RowNote = { key: string; text: string; alert?: boolean; details?: string };

const SUMMARY = "min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";
const LINK = "inline-flex min-h-11 items-center text-brand underline";

const keyOf = (c: Check) => `${c.check_id}|${c.subject}`;
const domId = (prefix: string, key: string) => `${prefix}-${key.replace(/[^A-Za-z0-9_-]/g, "_")}`;

function dateOf(at: string | null | undefined): string {
  return localDate(at);
}

function timeOf(at: string | null | undefined): string {
  return localStamp(at);
}

/** One slot of a check sentence: numbers and identifiers left to right, the researcher's words as written. */
function slot(locale: Locale, name: string, value: unknown): ReactNode {
  const t = checksT(locale);
  if (value === null || value === undefined) return null;
  if (typeof value === "number") return <bdi dir="ltr">{formatNumber(locale, value)}</bdi>;
  const text = Array.isArray(value) ? value.map(String).join(", ") : String(value);
  if (name === "database") return <bdi dir="ltr">{providerName(text)}</bdi>;
  if (name === "side" && hasChecksKey(`checks.side.${text}`)) return t(`checks.side.${text}` as "checks.side.inclusion");
  if (name === "state" && hasChecksKey(`checks.state.${text}`)) return t(`checks.state.${text}` as "checks.state.failed");
  if (name === "fields") return <bdi dir="auto">{text.split(/,\s*/).map((f) => fieldLabel(locale, f)).join(", ")}</bdi>;
  if (name === "steps") return <bdi dir="auto">{text.split(/,\s*/).map((s) => stepLabel(locale, s)).join(", ")}</bdi>;
  if (["term", "concept", "words", "lens"].includes(name)) return <bdi dir="auto">{text}</bdi>;
  return <bdi dir="ltr">{text}</bdi>;
}

/** The count a sentence is about: its `n` parameter when it is a number (H-ui-findings F4). */
function countOf(params: Record<string, unknown> | undefined): number | undefined {
  const n = params?.n;
  return typeof n === "number" ? n : undefined;
}

function slots(locale: Locale, params: Record<string, unknown>): Record<string, ReactNode> {
  return Object.fromEntries(Object.entries(params ?? {}).map(([k, v]) => [k, slot(locale, k, v)]));
}

/** The sentence of a check from this catalogue; a key the catalogue lacks shows the check id. */
export function CheckSentence({ locale, check }: Readonly<{ locale: Locale; check: Check }>) {
  // M10c: an assistant's finding is shown in its own words (the review's language), never translated.
  if (check.source === "agent") return <bdi dir="auto">{check.message}</bdi>;
  const template = checksTemplate(locale, check.message_key, countOf(check.params));
  return template ? <>{fillNodes(template, slots(locale, check.params))}</> : <bdi dir="ltr">{check.check_id}</bdi>;
}

/** The sentence as plain text, for the polite announcements. */
function sentenceText(locale: Locale, check: Check): string {
  if (check.source === "agent") return check.message;
  const template = checksTemplate(locale, check.message_key, countOf(check.params));
  if (!template) return check.check_id;
  return fillText(template, Object.fromEntries(Object.entries(check.params ?? {}).map(([k, v]) => [k, String(v ?? "")])));
}

/** Level as words; `blocker` is text in the blocked role with no fill behind it (BRAND_BOOK). */
export function LevelBadge({ locale, level }: Readonly<{ locale: Locale; level: Check["level"] }>) {
  const t = checksT(locale);
  if (level === "blocker") {
    return (
      <span data-role="blocked" data-level="blocker" className="inline-flex items-center gap-1 text-xs font-semibold leading-4 text-blocked">
        <svg aria-hidden="true" viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="8" cy="8" r="6.5" />
          <path d="M8 4.5v4M8 11v.5" strokeLinecap="round" />
        </svg>
        {t("checks.level.blocker")}
      </span>
    );
  }
  return (
    <span data-level={level}>
      <DecisionBadge role={level === "warning" ? "unclear" : "exclude"}>{t(level === "warning" ? "checks.level.warning" : "checks.level.note")}</DecisionBadge>
    </span>
  );
}

function actionLabel(locale: Locale, check: Check): string {
  const t = checksT(locale);
  if (check.check_id === "HANDOFF_PREPARATION_UNFINISHED" && check.action.finish) return t("checks.HANDOFF_PREPARATION_UNFINISHED.actionFinish");
  return hasChecksKey(check.action.label_key) ? t(check.action.label_key) : t("checks.suggested");
}

export function ChecksPanel(props: Readonly<ChecksPanelProps>) {
  const { locale, mode, name, load, dismiss, restore, reloadKey, link, onDecided, adoptAnswers = true, dirty, readOnly, extra } = props;
  const t = checksT(locale);
  const uid = useId().replace(/:/g, "");
  const headingId = `checks-${name}-${uid}`;
  const offlineId = `checks-offline-${name}-${uid}`;
  const [list, setList] = useState<CheckList | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<AssistRefusal | null>(null);
  const [offline, setOffline] = useState(false);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [form, setForm] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [reasonInvalid, setReasonInvalid] = useState(false);
  const [notes, setNotes] = useState<RowNote | null>(null);
  const [announce, setAnnounce] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  const loadRef = useRef(load);
  loadRef.current = load;

  const read = useCallback(async () => {
    setLoading(true);
    try {
      const next = await loadRef.current();
      if (next) {
        setList(next);
        setLoadError(null);
        setOffline(false);
      }
    } catch (error) {
      const refusal = refusalFrom(error);
      if (isOfflineCode(refusal.code)) setOffline(true);
      else setLoadError(refusal);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void read();
  }, [read, reloadKey]);

  const focusLater = (fn: () => void) => setTimeout(fn, 0);

  const openRows = (l: CheckList | null) => (l?.checks ?? []).filter((c) => c.status === "open" && c.level !== "note");

  const afterRefusal = async (check: Check, error: unknown, restoring: boolean) => {
    const refusal = refusalFrom(error);
    const key = keyOf(check);
    if (isOfflineCode(refusal.code)) {
      setOffline(true);
      return;
    }
    if (refusal.code === "CHECK_REASON_REQUIRED") {
      setReasonInvalid(true);
      return;
    }
    if (refusal.code === "CHECK_CHANGED" || refusal.code === "CHECK_NOT_FOUND" || refusal.code === "CHECK_NOT_DISMISSED") {
      setForm(null);
      await read();
      onDecided?.();
      if (refusal.code === "CHECK_CHANGED") setNotes({ key, text: t("checks.err.changed") });
      else if (refusal.code === "CHECK_NOT_FOUND") setNotes({ key, text: t("checks.err.gone") });
      else setNotes(null);
      focusLater(() => document.getElementById(domId("check-sentence", key))?.focus());
      return;
    }
    if (refusal.code === "DRAFT_EMITTED" || refusal.code === "DRAFT_CONFLICT") {
      setForm(null);
      onDecided?.();
    }
    setNotes({ key, text: t("checks.err.other", { code: refusal.code }), alert: true, details: refusal.message });
    focusLater(() => document.getElementById(domId("check-sentence", key))?.focus());
    void restoring;
  };

  const doDismiss = async (check: Check, withReason: boolean) => {
    const text = reason.trim();
    if (withReason && !text) {
      setReasonInvalid(true);
      return;
    }
    const before = openRows(list).findIndex((c) => keyOf(c) === keyOf(check));
    setBusy(true);
    setNotes(null);
    try {
      const answer = await dismiss(check, withReason ? text : undefined);
      if (adoptAnswers) setList(answer);
      setForm(null);
      setReason("");
      setReasonInvalid(false);
      setAnnounce(t("checks.announce.dismissed", { check: sentenceText(locale, check) }));
      onDecided?.();
      const rest = adoptAnswers ? openRows(answer) : openRows(list).filter((c) => keyOf(c) !== keyOf(check));
      focusLater(() => {
        const next = rest[Math.max(0, Math.min(before, rest.length - 1))];
        const target = next ? document.getElementById(domId("check-why", keyOf(next))) : null;
        (target ?? heading.current)?.focus();
      });
    } catch (error) {
      await afterRefusal(check, error, false);
    } finally {
      setBusy(false);
    }
  };

  const doRestore = async (check: Check) => {
    setBusy(true);
    setNotes(null);
    try {
      const answer = await restore(check);
      if (adoptAnswers) setList(answer);
      setAnnounce(t("checks.announce.restored", { check: sentenceText(locale, check) }));
      onDecided?.();
      const key = keyOf(check);
      focusLater(() => document.getElementById(domId(check.level === "note" ? "check-sentence" : "check-why", key))?.focus());
    } catch (error) {
      await afterRefusal(check, error, true);
    } finally {
      setBusy(false);
    }
  };

  if (loadError?.code === "STEP_UNKNOWN") {
    return (
      <section className="rounded-lg border border-dashed border-ink-muted bg-leaf p-4 text-sm" data-checks-panel={name} data-card="checks">
        <p role="alert" className="text-ink">
          {t("checks.err.step")}
        </p>
        <Button className="mt-2" onClick={() => void read()}>
          {t("checks.reload")}
        </Button>
      </section>
    );
  }
  // The screen owns every other refusal of the read (a draft or protocol it cannot use): no rows.
  if (!list) {
    if (loadError || !loading) return null;
    return (
      <div aria-busy="true" className="space-y-2 rounded-lg border border-dashed border-rule p-4" data-checks-loading={name}>
        <span className="sr-only">{t("checks.loading")}</span>
        <div className="h-4 w-1/2 rounded-sm bg-rule" />
        <div className="h-3 w-5/6 rounded-sm bg-rule" />
        <div className="h-3 w-2/3 rounded-sm bg-rule" />
      </div>
    );
  }
  const rows = list.checks ?? [];
  const waiting = list.waiting ?? [];
  if (mode === "panel" && rows.length === 0 && waiting.length === 0) return null;

  const counts = list.counts ?? { blocker: 0, warning: 0, note: 0, dismissed: 0 };
  const blockers = rows.filter((c) => c.status === "open" && c.level === "blocker");
  const warnings = rows.filter((c) => c.status === "open" && c.level === "warning");
  const noteRows = rows.filter((c) => c.status === "open" && c.level === "note");
  const dismissedRows = rows.filter((c) => c.status === "dismissed");
  // M10d (03-guidance rule 3, Review): the first open check that has a fix is marked; the order stays the engine's.
  const firstFix = mode === "readiness" ? [...blockers, ...warnings, ...noteRows].find((c) => link(c) !== null) : undefined;
  const firstFixKey = firstFix ? keyOf(firstFix) : null;
  const disabled = busy || offline;
  const n = (value: number) => <bdi dir="ltr">{formatNumber(locale, value)}</bdi>;

  const needs = new Map<string, number>();
  for (const w of waiting) needs.set(w.needs, (needs.get(w.needs) ?? 0) + 1);
  const partialPool = (list.partial ?? []).filter((p) => p.kind === "pool_partial");

  const row = (check: Check, dismissedRow = false) => {
    const key = keyOf(check);
    const sentenceId = domId("check-sentence", key);
    const whyId = domId("check-why-text", key);
    const whyOpen = !!open[key];
    const target = link(check);
    const step = STEP_NUMBER[check.step];
    const sourceKnown = check.source === "check";
    const formOpen = form === key;
    const reasonId = domId("check-reason", key);
    const errorId = domId("check-reason-error", key);
    const note = notes?.key === key ? notes : null;
    const whyTemplate = checksTemplate(locale, check.why_key);
    return (
      <li key={key} className="rounded-md border border-rule bg-paper p-3" data-check={check.check_id} data-subject={check.subject} data-level={check.level} data-status={check.status}>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <LevelBadge locale={locale} level={check.level} />
          {mode === "readiness" && step ? (
            <span className="rounded-sm border border-rule px-1.5 py-0.5 text-ink-muted" data-step-chip={check.step}>
              {fillNodes(CHECKS_COPY[locale]["checks.step"], { n: n(step) })}
            </span>
          ) : null}
          <span className="text-ink-muted" data-source={check.source}>
            {sourceKnown
              ? t("checks.source.check")
              : check.source === "agent"
                ? check.agent?.model
                  ? fillNodes(CHECKS_COPY[locale]["checks.source.agentModel"], { model: <bdi dir="ltr">{check.agent.model}</bdi> })
                  : t("checks.source.agent")
                : t("checks.source.generic")}
          </span>
          {dirty && !dismissedRow ? (
            <span className="text-unclear" data-row-saved>
              · {t("checks.row.saved")}
            </span>
          ) : null}
        </div>
        <p id={sentenceId} tabIndex={-1} className="mt-1 text-[0.9375rem] leading-[1.375rem] text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus" data-sentence>
          <CheckSentence locale={locale} check={check} />
        </p>
        {check.outdated && !dismissedRow ? (
          <p className="mt-1 text-xs text-unclear" data-outdated>
            {t("checks.agent.outdated")}
          </p>
        ) : null}
        {check.previously_dismissed && !dismissedRow ? (
          <p className="mt-1 text-xs text-unclear" data-previously>
            {t("checks.previously", { date: dateOf(check.previously_dismissed.at) })}
          </p>
        ) : null}
        {dismissedRow && check.dismissal ? (
          <p className="mt-1 text-xs text-ink-muted" data-dismissal>
            {check.dismissal.reason
              ? fillNodes(CHECKS_COPY[locale]["checks.dismissedLine"], { date: <bdi dir="ltr">{dateOf(check.dismissal.at)}</bdi>, reason: <bdi dir="auto">{check.dismissal.reason}</bdi> })
              : fillNodes(CHECKS_COPY[locale]["checks.dismissedLine.noReason"], { date: <bdi dir="ltr">{dateOf(check.dismissal.at)}</bdi> })}
          </p>
        ) : null}
        <div className="mt-1 flex flex-wrap items-center gap-x-4">
          <button
            type="button"
            id={domId("check-why", key)}
            aria-expanded={whyOpen}
            aria-controls={whyId}
            onClick={() => setOpen((o) => ({ ...o, [key]: !o[key] }))}
            className="inline-flex min-h-11 items-center gap-1 rounded-sm text-sm text-brand underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
            data-why
          >
            <svg aria-hidden="true" viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="8" cy="8" r="6.5" />
              <path d="M6.5 6.2a1.6 1.6 0 1 1 2.2 1.5c-.5.2-.7.6-.7 1.1v.4M8 11v.5" strokeLinecap="round" />
            </svg>
            {t("checks.why")}
          </button>
          {!dismissedRow && key === firstFixKey ? (
            <RecommendedBadge locale={locale} source={guidanceT(locale)("guidance.recommended.source.check", { id: check.check_id })} />
          ) : null}
          {!dismissedRow && target?.proposal ? (
            <Button variant="quiet" className="px-0" disabled={offline} aria-describedby={offline ? offlineId : sentenceId} onClick={() => {
              if (!tryFocus(`proposal-${target.proposal}`) && target.href) window.location.assign(target.href);
            }} data-check-proposal={target.proposal}>
              {actionLabel(locale, check)}
            </Button>
          ) : !dismissedRow && target?.href ? (
            <a
              className={LINK}
              href={target.href}
              onClick={(event) => {
                if (target.hash && tryFocus(target.hash)) event.preventDefault();
              }}
              data-check-action={check.action.kind}
            >
              {actionLabel(locale, check)}
            </a>
          ) : null}
          {!dismissedRow && check.dismissible && check.status === "open" && !readOnly ? (
            <Button
              variant="quiet"
              className="px-0"
              id={domId("check-dismiss", key)}
              disabled={disabled}
              aria-describedby={offline ? `${sentenceId} ${offlineId}` : sentenceId}
              onClick={() => {
                if (check.level === "warning") {
                  setForm(key);
                  setReason("");
                  setReasonInvalid(false);
                  focusLater(() => document.getElementById(reasonId)?.focus());
                } else {
                  void doDismiss(check, false);
                }
              }}
              data-dismiss
            >
              {t("checks.act.dismiss")}
            </Button>
          ) : null}
          {dismissedRow && !readOnly ? (
            <Button variant="quiet" className="px-0" disabled={disabled} aria-describedby={offline ? `${sentenceId} ${offlineId}` : sentenceId} onClick={() => void doRestore(check)} data-restore>
              {t("checks.act.restore")}
            </Button>
          ) : null}
        </div>
        {whyOpen ? (
          <div id={whyId} className="mt-1 space-y-1 text-sm text-ink-muted" data-why-text>
            <p>
              {check.source === "agent"
                ? check.why
                  ? <bdi dir="auto">{check.why}</bdi>
                  : null
                : whyTemplate
                  ? fillNodes(whyTemplate, slots(locale, check.why_params ?? check.params))
                  : null}
            </p>
            {check.threshold ? (
              <p data-threshold>
                {fillNodes(CHECKS_COPY[locale]["checks.threshold"], {
                  name: <bdi dir="ltr">{check.threshold.name}</bdi>,
                  value: <bdi dir="ltr">{String(check.threshold.value)}</bdi>,
                })}
              </p>
            ) : null}
          </div>
        ) : (
          <div id={whyId} hidden />
        )}
        {formOpen ? (
          <div
            className="mt-2 space-y-2"
            data-dismiss-form
          >
            <label htmlFor={reasonId} className="block text-sm text-ink">
              {t("checks.dismiss.label")}
            </label>
            <textarea
              id={reasonId}
              rows={2}
              dir="auto"
              value={reason}
              aria-invalid={reasonInvalid}
              aria-describedby={reasonInvalid ? errorId : undefined}
              onChange={(event) => {
                setReason(event.target.value);
                if (reasonInvalid) setReasonInvalid(false);
              }}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  event.preventDefault();
                  setForm(null);
                  focusLater(() => document.getElementById(domId("check-dismiss", key))?.focus());
                }
              }}
              className="block w-full rounded-md border border-rule bg-paper p-2 text-ink"
            />
            {reasonInvalid ? (
              <p id={errorId} className="text-sm text-blocked" role="alert">
                {t("checks.err.reason")}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-2">
              <Button disabled={disabled} onClick={() => void doDismiss(check, true)} data-dismiss-submit>
                {t("checks.dismiss.submit")}
              </Button>
              <Button
                variant="quiet"
                onClick={() => {
                  setForm(null);
                  focusLater(() => document.getElementById(domId("check-dismiss", key))?.focus());
                }}
              >
                {t("checks.dismiss.cancel")}
              </Button>
            </div>
          </div>
        ) : null}
        {note ? (
          <div className="mt-1 text-sm" data-row-note>
            <p className={note.alert ? "text-blocked" : "text-ink-muted"} role={note.alert ? "alert" : undefined}>
              {note.text}
            </p>
            {note.details ? (
              <p className="text-xs text-ink-muted">
                <bdi dir="ltr">{note.details}</bdi>
              </p>
            ) : null}
          </div>
        ) : null}
      </li>
    );
  };

  const disclosure = (label: ReactNode, items: Check[], dismissedGroup: boolean, attr: string) =>
    items.length ? (
      <details className="mt-3 text-sm" {...{ [attr]: "" }}>
        <summary className={SUMMARY}>{label}</summary>
        <ul className="mt-2 space-y-2">{items.map((c) => row(c, dismissedGroup))}</ul>
      </details>
    ) : null;

  const header =
    mode === "readiness" ? (
      <>
        <h2 id={headingId} ref={heading} tabIndex={-1} className="font-semibold text-ink">
          {t("checks.ready.title")}
        </h2>
        <p className="mt-1 text-sm text-ink" aria-live="polite" data-ready-sentence={list.ready === false ? "blocked" : counts.warning ? "warnings" : "clear"}>
          {list.ready === false
            ? fillNodes(CHECKS_COPY[locale]["checks.ready.blocked"], { n: n(counts.blocker) })
            : counts.warning
              ? fillNodes(CHECKS_COPY[locale]["checks.ready.warnings"], { n: n(counts.warning) })
              : t("checks.ready.clear")}
        </p>
      </>
    ) : (
      <h2 id={headingId} ref={heading} tabIndex={-1} className="font-semibold text-ink" aria-live="polite" data-checks-counts>
        {fillNodes(CHECKS_COPY[locale]["checks.counts"], { blockers: n(counts.blocker), warnings: n(counts.warning) })}
      </h2>
    );

  return (
    <section
      aria-labelledby={headingId}
      aria-busy={loading || busy}
      className="rounded-lg border border-dashed border-ink-muted bg-leaf p-4 text-sm"
      data-checks-panel={name}
      data-card="checks"
      data-mode={mode}
    >
      {header}
      {extra}
      {dirty ? (
        <p className="mt-1 text-sm text-unclear" data-checks-unsaved>
          {t("checks.unsaved")}
        </p>
      ) : null}
      {offline ? (
        <p id={offlineId} className="mt-1 text-sm text-ink-muted" data-checks-offline>
          {t("checks.asOf", { time: timeOf(list.computed_at) })} · {t("checks.offline")}
        </p>
      ) : null}
      {readOnly ? <p className="mt-1 text-sm text-ink-muted">{t("checks.readOnly")}</p> : null}
      {partialPool.map((p, i) => (
        <p key={i} className="mt-1 text-sm text-unclear" data-partial-pool>
          {fillNodes(CHECKS_COPY[locale]["checks.partialPool"], {
            databases: <bdi dir="ltr">{(Array.isArray(p.databases) ? p.databases : []).map((d) => providerName(String(d))).join(", ")}</bdi>,
          })}
        </p>
      ))}
      {mode === "readiness" ? (
        <>
          {blockers.length ? (
            <div className="mt-3" data-group="blocker">
              <h3 className="text-xs font-semibold uppercase tracking-[0.05em] text-ink-muted rtl:tracking-normal">{t("checks.group.blocker")}</h3>
              <ul className="mt-1 space-y-2">{blockers.map((c) => row(c))}</ul>
            </div>
          ) : null}
          {warnings.length ? (
            <div className="mt-3" data-group="warning">
              <h3 className="text-xs font-semibold uppercase tracking-[0.05em] text-ink-muted rtl:tracking-normal">{t("checks.group.warning")}</h3>
              <ul className="mt-1 space-y-2">{warnings.map((c) => row(c))}</ul>
            </div>
          ) : null}
          {disclosure(t("checks.group.note") + ` (${formatNumber(locale, counts.note)})`, noteRows, false, "data-group-note")}
        </>
      ) : blockers.length + warnings.length ? (
        <ul aria-labelledby={headingId} className="mt-3 space-y-2" data-open-rows>
          {[...blockers, ...warnings].map((c) => row(c))}
        </ul>
      ) : null}
      {mode === "panel" ? disclosure(fillNodes(CHECKS_COPY[locale]["checks.notes"], { n: n(counts.note) }), noteRows, false, "data-notes") : null}
      {disclosure(fillNodes(CHECKS_COPY[locale]["checks.dismissed"], { n: n(counts.dismissed) }), dismissedRows, true, "data-dismissed")}
      {[...needs.entries()].map(([need, count]) => (
        <p key={need} className="mt-2 text-sm text-ink-muted" data-waiting={need}>
          {fillNodes(checksCountTemplate(locale, "checks.waiting", count), {
            n: n(count),
            need: hasChecksKey(`checks.need.${need}`) ? t(`checks.need.${need}` as "checks.need.pool") : <bdi dir="ltr">{need}</bdi>,
          })}
        </p>
      ))}
      <p className="sr-only" role="status" aria-live="polite" data-checks-announce>
        {announce}
      </p>
    </section>
  );
}
