"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, EvidenceQuote, type DecisionRole } from "@/components/ui/base";
import { ScreeningSteps, stepHref } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import {
  decisionEvent,
  getConflicts,
  getProposal,
  getQueue,
  getRecord,
  getSettings,
  postEvents,
  resolveConflict,
  type Answer,
  type Conflict,
  type IntakeResult,
  type Outcome,
  type Proposal,
  type QueueItem,
  type QueueView,
  type RecordDetail,
  type Settings,
  type StoredEvent,
} from "@/lib/screening-v1";
import { tc, type TriageCopyKey } from "@/lib/triage-copy";
import {
  answersInOrder,
  checklistComplete,
  compareAnswers,
  failedChecks,
  mayReadProposal,
  reasonOptions,
  triageKey,
  undoTarget,
} from "@/lib/triage-logic";

/**
 * Desktop triage (spec 03) with the record detail (spec 05), over the M1a API.
 *
 * The researcher decides every record. The screen never derives an outcome:
 * the checklist answers travel in the event, the engine validates the reason
 * code and the binding, and the agent's draft is requested only once it may be
 * shown (`mayReadProposal`), because the engine records each first read of a
 * draft as a reveal (M1b-0). Records are prefetched; drafts never are.
 *
 * Skip writes nothing. Undo and "Change my decision" are superseding events.
 * A `conflict` result locks the record until the researcher keeps one event;
 * nothing is resolved automatically.
 */

const VIEWS: QueueView[] = ["needs_you", "proposal_ready", "no_proposal", "title_only", "decided"];
const PREFETCH = 5;

type ProposalState =
  | { status: "hidden" }
  | { status: "none" }
  | { status: "loading" }
  | { status: "ready"; proposal: Proposal }
  | { status: "error"; code: string };

const OUTCOME_ROLE: Record<Outcome, DecisionRole> = { INCLUDE: "include", EXCLUDE: "exclude", MAYBE: "unclear" };
const OUTCOME_KEY: Record<Outcome, TriageCopyKey> = { INCLUDE: "include", EXCLUDE: "exclude", MAYBE: "unclear" };
const ANSWER_KEY: Record<Answer, TriageCopyKey> = { yes: "yes", no: "no", not_reported: "notReported" };

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function codeOf(error: unknown): string {
  return isScreeningApiError(error) ? error.code : "ENGINE_UNREACHABLE";
}

/** The abstract with criterion highlights as `<mark>` (spec 05); text is never altered. */
function Abstract({ text, highlights }: Readonly<{ text: string; highlights: RecordDetail["highlights"] }>) {
  const spans = [...highlights].filter((h) => h.start >= 0 && h.end <= text.length && h.start < h.end).sort((a, b) => a.start - b.start);
  const parts: React.ReactNode[] = [];
  let at = 0;
  for (const h of spans) {
    if (h.start < at) continue;
    parts.push(text.slice(at, h.start));
    parts.push(
      <mark key={`${h.start}-${h.end}`} className="bg-anchor-soft text-ink underline decoration-anchor">
        {text.slice(h.start, h.end)}
        <span className="sr-only"> ({h.criterion_id})</span>
      </mark>,
    );
    at = h.end;
  }
  parts.push(text.slice(at));
  return (
    <p dir="auto" className="text-[0.9375rem] leading-[1.5rem] text-ink">
      {parts}
    </p>
  );
}

export function TriagePage({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="triage" consoleOrigin={consoleOrigin()} />
      <TriageScreen locale={locale} />
    </div>
  );
}

function TriageScreen({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: TriageCopyKey, values?: Record<string, string | number>) => tc(locale, key, values), [locale]);
  const origin = useMemo(consoleOrigin, []);

  const [settings, setSettings] = useState<Settings | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [view, setView] = useState<QueueView>("needs_you");
  const [items, setItems] = useState<QueueItem[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [record, setRecord] = useState<RecordDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [focusIndex, setFocusIndex] = useState(0);
  const [reasonOpen, setReasonOpen] = useState(false);
  const [reason, setReason] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [editing, setEditing] = useState(false);
  const [proposal, setProposal] = useState<ProposalState>({ status: "hidden" });
  const [conflict, setConflict] = useState<Conflict | null>(null);
  const [stale, setStale] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [refusal, setRefusal] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [help, setHelp] = useState(false);
  const cache = useRef(new Map<string, RecordDetail>());
  const revealedHeading = useRef<HTMLHeadingElement>(null);

  const item = items.find((i) => i.study_id === selected) ?? null;

  const loadQueue = useCallback(
    async (nextView: QueueView, append = false, from = 0) => {
      const page = await getQueue(origin, { view: nextView, cursor: from, limit: 50 });
      setItems((prev) => (append ? [...prev, ...page.items] : page.items));
      setCursor(page.next_cursor);
      return page.items;
    },
    [origin],
  );

  const fetchRecord = useCallback(
    async (studyId: string, fresh = false) => {
      if (!fresh && cache.current.has(studyId)) return cache.current.get(studyId)!;
      const detail = await getRecord(origin, studyId);
      cache.current.set(studyId, detail);
      return detail;
    },
    [origin],
  );

  const showProposal = useCallback(
    async (detail: RecordDetail, queueItem: QueueItem | null, current: Settings) => {
      const hasProposal = queueItem?.has_proposal ?? false;
      if (!hasProposal) {
        setProposal({ status: detail.my_decision || current.blinding === "show" ? "none" : "hidden" });
        return;
      }
      if (!mayReadProposal({ hasProposal, decided: detail.my_decision !== null, blinding: current.blinding })) {
        setProposal({ status: "hidden" });
        return;
      }
      setProposal({ status: "loading" });
      try {
        const draft = await getProposal(origin, detail.study_id);
        setProposal(draft ? { status: "ready", proposal: draft } : { status: "none" });
      } catch (error) {
        const code = codeOf(error);
        setProposal(code === "PROPOSAL_HIDDEN" ? { status: "hidden" } : { status: "error", code });
      }
    },
    [origin],
  );

  const open = useCallback(
    async (studyId: string, list: QueueItem[], current: Settings, fresh = false) => {
      setSelected(studyId);
      setReasonOpen(false);
      setReason(null);
      setNote("");
      setEditing(false);
      setRefusal(null);
      setConflict(null);
      setFocusIndex(0);
      setRecord(null);
      setProposal({ status: "hidden" });
      try {
        const [detail, open] = await Promise.all([fetchRecord(studyId, fresh), getConflicts(origin)]);
        setRecord(detail);
        const own = detail.my_decision?.criteria ?? [];
        setAnswers(Object.fromEntries(own.map((a) => [a.id, a.answer])));
        // A conflict from another device locks the record too, not only one this tab caused.
        const rival = open.find((c) => c.study_id === studyId) ?? null;
        setConflict(rival);
        if (rival === null) await showProposal(detail, list.find((i) => i.study_id === studyId) ?? null, current);
      } catch (error) {
        setRefusal(codeOf(error));
      }
      // Prefetch the next records' text only (spec 03); never their drafts.
      const at = list.findIndex((i) => i.study_id === studyId);
      for (const next of list.slice(at + 1, at + 1 + PREFETCH)) {
        if (!cache.current.has(next.study_id)) void fetchRecord(next.study_id).catch(() => undefined);
      }
    },
    [fetchRecord, origin, showProposal],
  );

  const boot = useCallback(async () => {
    setBootError(null);
    try {
      const current = await getSettings(origin);
      setSettings(current);
      const list = await loadQueue("needs_you");
      if (list.length > 0) await open(list[0].study_id, list, current);
    } catch (error) {
      setBootError(codeOf(error));
    }
  }, [loadQueue, open, origin]);

  useEffect(() => {
    void boot();
  }, [boot]);

  async function changeView(next: QueueView) {
    if (!settings) return;
    setView(next);
    try {
      const list = await loadQueue(next);
      if (list.length > 0) await open(list[0].study_id, list, settings);
      else {
        setSelected(null);
        setRecord(null);
      }
    } catch (error) {
      setRefusal(codeOf(error));
    }
  }

  function move(step: number) {
    if (!settings || items.length === 0) return;
    const at = Math.max(0, items.findIndex((i) => i.study_id === selected));
    const next = items[(at + step + items.length) % items.length];
    void open(next.study_id, items, settings);
  }

  async function submit(outcome: Outcome, options: { reasonCode?: string | null; restore?: StoredEvent } = {}) {
    if (!record || !settings || busy || stale) return;
    const restore = options.restore;
    const event = decisionEvent({
      record,
      screenerId: settings.screener_id,
      outcome,
      reasonCode: restore ? restore.reason_code : (options.reasonCode ?? null),
      criteria: restore ? restore.criteria : answersInOrder(record.criteria, answers),
      note: restore ? restore.note : note.trim() || null,
      supersedes: record.my_decision?.event_id ?? null,
    });
    setBusy(true);
    setRefusal(null);
    let result: IntakeResult | undefined;
    try {
      [result] = await postEvents(origin, [event]);
    } catch (error) {
      setRefusal(codeOf(error));
      setBusy(false);
      return;
    }
    setBusy(false);
    if (!result) return;
    if (result.result === "refused") {
      const code = result.refusal?.code ?? "REFUSED";
      if (code === "STALE_BINDING") setStale(true);
      setRefusal(code);
      setMessage(t("refused", { code }));
      return;
    }
    const decidedItems = items.map((i) => (i.study_id === record.study_id ? { ...i, decided: true } : i));
    setItems(decidedItems);
    const detail = await fetchRecord(record.study_id, true);
    setRecord(detail);
    setReasonOpen(false);
    setEditing(false);
    if (result.result === "conflict") {
      const open = await getConflicts(origin);
      setConflict(open.find((c) => c.study_id === record.study_id) ?? null);
      setMessage(t("conflictTitle"));
      return;
    }
    setMessage(t("saved"));
    await showProposal(detail, decidedItems.find((i) => i.study_id === record.study_id) ?? null, settings);
    revealedHeading.current?.focus();
  }

  async function keep(eventId: string) {
    if (!record || !settings) return;
    try {
      await resolveConflict(origin, record.study_id, eventId);
      await open(record.study_id, items, settings, true);
      setMessage(t("saved"));
    } catch (error) {
      setRefusal(codeOf(error));
    }
  }

  function skip() {
    setMessage(t("skipped"));
    move(1);
  }

  function undo() {
    if (!record) return;
    const target = undoTarget(record.my_decision, record.history);
    if (!target) {
      setMessage(t("undoUnavailable"));
      return;
    }
    void submit(target.outcome, { restore: target });
  }

  const decided = record?.my_decision ?? null;
  const deciding = record !== null && (decided === null || editing) && conflict === null;
  const complete = record !== null && checklistComplete(record.criteria, answers);
  const reasons = record ? reasonOptions(record.criteria) : [];

  function answer(value: Answer) {
    if (!record || !deciding) return;
    const criterion = record.criteria[focusIndex];
    if (!criterion) return;
    setAnswers((prev) => ({ ...prev, [criterion.id]: value }));
    setFocusIndex((i) => Math.min(i + 1, record.criteria.length - 1));
  }

  // The keyboard map (spec 03); off inside text fields. One listener for the
  // screen's life calls the latest handler, so no key reads a stale render.
  const keyHandler = useRef<(event: KeyboardEvent) => void>(() => undefined);
  useEffect(() => {
    const listener = (event: KeyboardEvent) => keyHandler.current(event);
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);
  useEffect(() => {
    keyHandler.current = function onKey(event: KeyboardEvent) {
      if (event.key === "Enter" && reasonOpen && reason && deciding && complete) {
        event.preventDefault();
        void submit("EXCLUDE", { reasonCode: reason });
        return;
      }
      if (event.key === "Escape") {
        setHelp(false);
        setReasonOpen(false);
        return;
      }
      const key = triageKey(event, event.target);
      if (key === null) return;
      if (reasonOpen && /^[1-9]$/.test(event.key)) {
        const pick = reasons[Number(event.key) - 1];
        if (pick) setReason(pick);
        event.preventDefault();
        return;
      }
      event.preventDefault();
      if (key === "help") setHelp((h) => !h);
      else if (key === "down") move(1);
      else if (key === "up") move(-1);
      else if (key === "skip" && deciding) skip();
      else if (key === "next" && !deciding) move(1);
      else if (key === "undo" && decided) undo();
      else if (key === "yes") answer("yes");
      else if (key === "no") answer("no");
      else if (key === "notReported") answer("not_reported");
      else if (deciding && complete) {
        if (key === "include") void submit("INCLUDE");
        else if (key === "unclear") void submit("MAYBE");
        else if (key === "exclude") setReasonOpen(true);
      }
    };
  });

  if (bootError) {
    return (
      <section role="alert" className="rounded-lg border border-rule-strong bg-leaf p-6">
        <p className="text-ink">{t("unreachable", { code: bootError })}</p>
        <p className="mt-2 font-mono text-[0.8125rem] text-blocked" dir="ltr">
          {bootError}
        </p>
        <Button className="mt-4" onClick={() => void boot()}>
          {t("retry")}
        </Button>
      </section>
    );
  }

  if (!settings) return <p className="text-ink-muted">{t("loading")}</p>;

  const comparison = proposal.status === "ready" && decided ? compareAnswers(record!.criteria, decided.criteria, proposal.proposal) : [];
  const failed = proposal.status === "ready" ? failedChecks(proposal.proposal) : [];

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
        <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{settings.blinding === "show" ? t("ledeShow") : t("lede")}</p>
        {/* The shell's demonstration marker covers the fixture screens; this one is live (as corpus and lineage say). */}
        <p className="mt-2 inline-block border border-rule-strong px-2 py-0.5 text-xs text-ink-muted">{t("liveStamp")}</p>
      </header>

      <p role="status" aria-live="polite" className="sr-only">
        {message}
      </p>

      {stale ? (
        <p role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked">
          {t("staleBanner")} <span className="font-mono" dir="ltr">STALE_BINDING</span>
        </p>
      ) : null}

      <div className="flex flex-wrap gap-6">
        {/* Queue (spec 03, left zone) */}
        <nav aria-labelledby="triage-queue" className="w-full max-w-[260px] flex-none rounded-lg border border-rule bg-leaf p-4">
          <h2 id="triage-queue" className="text-sm font-semibold text-ink">
            {t("queueHeading")}
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {VIEWS.map((v) => (
              <button
                key={v}
                type="button"
                aria-pressed={view === v}
                onClick={() => void changeView(v)}
                className={`min-h-11 rounded-md border px-2 text-xs ${view === v ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
              >
                {t(`view.${v}` as TriageCopyKey)}
              </button>
            ))}
          </div>
          {items.length === 0 ? (
            <div className="mt-4 text-sm text-ink-muted">
              <p>{view === "needs_you" ? t("allDecided") : t("queueEmpty")}</p>
              {view === "needs_you" ? (
                <p className="mt-2 flex flex-col gap-1">
                  <a className="text-brand underline" href={stepHref(locale, "publish", origin)}>
                    {t("toPublish")}
                  </a>
                  <a className="text-brand underline" href={stepHref(locale, "home", origin)}>
                    {t("toHome")}
                  </a>
                </p>
              ) : null}
            </div>
          ) : (
            <ul className="mt-4 space-y-1">
              {items.map((i) => (
                <li key={i.study_id}>
                  <button
                    type="button"
                    aria-current={i.study_id === selected ? "true" : undefined}
                    onClick={() => void open(i.study_id, items, settings)}
                    className={`w-full rounded-md px-2 py-2 text-start text-sm ${i.study_id === selected ? "bg-brand-soft" : "hover:bg-leaf-raised"}`}
                  >
                    <bdi className="line-clamp-2 text-ink">{i.title}</bdi>
                    <span className="mt-0.5 block text-xs text-ink-muted">
                      {i.decided ? t("queueDecided") : i.has_proposal ? t("queueHiddenRow") : t("queueNoProposal")}
                      {i.flags.includes("title_only") ? ` · ${t("titleOnly")}` : ""}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {cursor !== null ? (
            <Button variant="quiet" className="mt-2" onClick={() => void loadQueue(view, true, cursor)}>
              {t("queueMore")}
            </Button>
          ) : null}
        </nav>

        {/* Record and checklist (spec 05) */}
        <section aria-labelledby="triage-record" className="min-w-0 flex-[999_1_420px] space-y-4">
          {refusal && !stale ? (
            <p role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked">
              {t("refused", { code: refusal })}
            </p>
          ) : null}
          {record === null ? (
            selected ? <p className="text-ink-muted">{t("loading")}</p> : null
          ) : (
            <>
              <article className="rounded-lg border border-rule bg-leaf p-5">
                <h2 id="triage-record" className="sr-only">
                  {t("recordHeading")}
                </h2>
                <p className="font-display text-[1.375rem] leading-[1.75rem] text-ink">
                  <bdi>{record.title}</bdi>
                </p>
                <p className="mt-1 flex flex-wrap gap-x-3 text-sm text-ink-muted">
                  <span>{record.year ?? t("notStored")}</span>
                  <span>
                    <bdi>{record.venue ?? t("notStored")}</bdi>
                  </span>
                  {record.doi ? (
                    <a className="text-anchor underline" href={`https://doi.org/${record.doi}`} dir="ltr">
                      {record.doi}
                    </a>
                  ) : null}
                  <DataCell>{record.study_id}</DataCell>
                </p>
                <div className="mt-4">
                  {record.abstract && record.abstract.trim() && record.abstract !== "No abstract available." ? (
                    <Abstract text={record.abstract} highlights={record.highlights} />
                  ) : (
                    <div className="space-y-2">
                      <DecisionBadge role="unclear">{t("titleOnly")}</DecisionBadge>
                      <p className="text-ink-muted">{t("noAbstract")}</p>
                      <p className="text-sm text-ink-muted">{t("titleOnlyNote")}</p>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-xs text-ink-faint">{t("originHidden")}</p>
              </article>

              {conflict ? (
                <section role="alert" className="rounded-lg border border-rule-strong bg-unclear-soft p-5">
                  <h2 className="font-semibold text-unclear">{t("conflictTitle")}</h2>
                  <p className="mt-1 text-ink">{t("conflictBody")}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {conflict.events.map((e) => (
                      <Button key={e.event_id} onClick={() => void keep(e.event_id)}>
                        {t("keep", { outcome: t(OUTCOME_KEY[e.outcome]) + (e.reason_code ? ` · ${e.reason_code}` : "") })}
                      </Button>
                    ))}
                  </div>
                </section>
              ) : null}

              {proposal.status === "ready" && decided ? (
                <section className="rounded-lg border border-rule bg-leaf p-5">
                  <h2 ref={revealedHeading} tabIndex={-1} className="font-semibold text-ink">
                    {proposal.proposal.derived_outcome === decided.outcome ? t("agrees") : t("disagrees")}
                  </h2>
                  <table className="mt-3 w-full text-sm">
                    <caption className="text-start text-ink-muted">{t("compareTitle")}</caption>
                    <thead>
                      <tr className="text-start text-ink-muted">
                        <th scope="col" className="py-1 text-start">{t("criterion")}</th>
                        <th scope="col" className="py-1 text-start">{t("you")}</th>
                        <th scope="col" className="py-1 text-start">{t("agent")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.map((row) => (
                        <tr key={row.id} className={row.differs ? "bg-unclear-soft" : ""}>
                          <th scope="row" className="py-1 text-start font-mono" dir="ltr">{row.id}</th>
                          <td className="py-1">{row.mine ? t(ANSWER_KEY[row.mine]) : t("notStored")}</td>
                          <td className="py-1">
                            {row.agent ? t(ANSWER_KEY[row.agent]) : t("notStored")}
                            {row.differs ? (
                              <span className="ms-2">
                                <DecisionBadge role="unclear">{t("differs")}</DecisionBadge>
                              </span>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>
              ) : null}

              {/* Checklist: required on desktop (spec 05, contract §9.3) */}
              <fieldset className="rounded-lg border border-rule bg-leaf p-5" disabled={!deciding || stale}>
                <legend className="px-1 font-semibold text-ink">{t("checklistHeading")}</legend>
                <ul className="space-y-3">
                  {record.criteria.map((c, index) => (
                    <li key={c.id} className={`rounded-md p-2 ${index === focusIndex && deciding ? "ring-2 ring-focus" : ""}`}>
                      <p className="text-sm">
                        <span className="font-mono text-ink-muted" dir="ltr">
                          {c.id}
                        </span>{" "}
                        <span className="text-ink-muted">· {c.kind === "inclusion" ? t("inclusion") : t("exclusion")}</span>
                      </p>
                      {c.text ? (
                        <p dir="auto" className="text-ink">
                          {c.text}
                        </p>
                      ) : null}
                      <div role="group" aria-label={c.id} className="mt-2 flex flex-wrap gap-2">
                        {(["yes", "no", "not_reported"] as Answer[]).map((a) => (
                          <button
                            key={a}
                            type="button"
                            aria-pressed={answers[c.id] === a}
                            onFocus={() => setFocusIndex(index)}
                            onClick={() => {
                              setFocusIndex(index);
                              setAnswers((prev) => ({ ...prev, [c.id]: a }));
                            }}
                            className={`min-h-11 min-w-11 rounded-md border px-3 text-sm ${answers[c.id] === a ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
                          >
                            {t(ANSWER_KEY[a])}
                          </button>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
                {deciding && !complete ? <p className="mt-3 text-sm text-ink-muted">{t("checklistRequired")}</p> : null}
              </fieldset>

              {/* Decision card */}
              <section aria-labelledby="triage-decision" className="rounded-lg border border-rule bg-leaf p-5">
                <h2 id="triage-decision" className="font-semibold text-ink">
                  {t("decisionHeading")}
                </h2>
                {decided && !editing ? (
                  <div className="mt-2 space-y-2">
                    <p className="flex flex-wrap items-center gap-2 text-ink">
                      {t("decidedAs")}
                      <DecisionBadge role={OUTCOME_ROLE[decided.outcome]}>
                        {t(OUTCOME_KEY[decided.outcome])}
                        {decided.reason_code ? ` · ${decided.reason_code}` : ""}
                      </DecisionBadge>
                      {decided.changed_after_reveal ? <DecisionBadge role="unclear">{t("changedAfterReveal")}</DecisionBadge> : null}
                    </p>
                    <p className="text-xs text-ink-muted">
                      {t("recordedAs", {
                        time: new Date(decided.decided_at).toLocaleString(locale),
                        fingerprint: decided.binding.protocol_fingerprint.slice(0, 19),
                      })}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="primary" onClick={() => move(1)} disabled={conflict !== null}>
                        {t("next")} <kbd className="text-xs opacity-80">N</kbd>
                      </Button>
                      <Button onClick={() => setEditing(true)} disabled={conflict !== null || stale}>
                        {t("change")}
                      </Button>
                      <Button onClick={undo} disabled={conflict !== null || stale || undoTarget(decided, record.history) === null} title={undoTarget(decided, record.history) === null ? t("undoUnavailable") : undefined}>
                        {t("undo")} <kbd className="text-xs opacity-80">Z</kbd>
                      </Button>
                    </div>
                    {record.history.length > 1 ? (
                      <details className="text-sm">
                        <summary className="cursor-pointer text-brand">{t("history")}</summary>
                        <ol className="mt-2 space-y-1">
                          {record.history.map((e) => (
                            <li key={e.event_id} className="text-ink-muted">
                              {new Date(e.decided_at).toLocaleString(locale)} · {t(OUTCOME_KEY[e.outcome])}
                              {e.reason_code ? ` · ${e.reason_code}` : ""}
                              {e.changed_after_reveal ? ` · ${t("changedAfterReveal")}` : ""}
                            </li>
                          ))}
                        </ol>
                      </details>
                    ) : null}
                  </div>
                ) : deciding ? (
                  <div className="mt-3 space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Button variant="primary" disabled={!complete || busy || stale} onClick={() => void submit("INCLUDE")}>
                        {t("include")} <kbd className="text-xs opacity-80">I</kbd>
                      </Button>
                      <Button disabled={!complete || busy || stale} aria-expanded={reasonOpen} onClick={() => setReasonOpen(true)}>
                        {t("exclude")} <kbd className="text-xs opacity-80">E</kbd>
                      </Button>
                      <Button disabled={!complete || busy || stale} onClick={() => void submit("MAYBE")}>
                        {t("unclear")} <kbd className="text-xs opacity-80">U</kbd>
                      </Button>
                      <Button variant="quiet" onClick={skip}>
                        {t("skip")} <kbd className="text-xs opacity-80">S</kbd>
                      </Button>
                    </div>
                    {reasonOpen ? (
                      <fieldset className="space-y-2">
                        <legend className="text-sm font-semibold text-ink">{t("reasonLegend")}</legend>
                        <div className="flex flex-wrap gap-2">
                          {reasons.map((code, index) => (
                            <button
                              key={code}
                              type="button"
                              aria-pressed={reason === code}
                              onClick={() => setReason(code)}
                              className={`min-h-11 rounded-md border px-3 font-mono text-sm ${reason === code ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
                              dir="ltr"
                            >
                              {index + 1}. {code}
                            </button>
                          ))}
                        </div>
                        <Button disabled={!reason || busy} onClick={() => reason && void submit("EXCLUDE", { reasonCode: reason })}>
                          {t("reasonConfirm")}
                        </Button>
                        {!reason ? <p className="text-sm text-ink-muted">{t("reasonRequired")}</p> : null}
                      </fieldset>
                    ) : null}
                    <label className="block text-sm text-ink">
                      {t("noteLabel")}
                      <textarea
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        rows={2}
                        className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
                      />
                    </label>
                  </div>
                ) : null}
              </section>
            </>
          )}
        </section>

        {/* The agent's draft (spec 05 aside): plain surface, never an include tint */}
        <aside
          aria-label={proposal.status === "ready" ? t("proposalRevealed") : t("proposalHiddenTitle")}
          className="w-full flex-[1_1_260px] rounded-lg border border-dashed border-rule-strong bg-leaf p-5"
          data-testid="proposal-aside"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-ink-muted rtl:tracking-normal">{t("proposalHiddenTitle")}</p>
          {proposal.status === "hidden" ? (
            <div className="mt-3 space-y-2" aria-hidden="false">
              <p className="text-ink-muted">{t("proposalHiddenBody")}</p>
              <div className="h-3 w-3/4 rounded-sm bg-rule" />
              <div className="h-3 w-1/2 rounded-sm bg-rule" />
            </div>
          ) : proposal.status === "none" ? (
            <p className="mt-3 text-ink-muted">{t("proposalNone")}</p>
          ) : proposal.status === "loading" ? (
            <p className="mt-3 text-ink-muted">{t("loading")}</p>
          ) : proposal.status === "error" ? (
            <p className="mt-3 text-blocked">{t("proposalUnavailable", { code: proposal.code })}</p>
          ) : (
            <div className="mt-3 space-y-3 text-sm">
              <p className="flex flex-wrap items-center gap-2">
                <span className="text-ink-muted">{t("draftOutcome")}</span>
                <span className="rounded-sm border border-rule-strong px-2 py-0.5 text-xs font-semibold text-ink">
                  {t(OUTCOME_KEY[proposal.proposal.derived_outcome])}
                  {proposal.proposal.reason_code ? ` · ${proposal.proposal.reason_code}` : ""}
                </span>
                <span className="text-xs text-ink-muted">{t("notADecision")}</span>
              </p>
              {failed.length > 0 ? (
                <p className="text-blocked">
                  {t("proposalRejected")} · {t("failedChecks", { checks: failed.join(", ") })}
                </p>
              ) : null}
              {proposal.proposal.cannot_decide ? <p className="text-unclear">{t("cannotDecide")}</p> : null}
              {proposal.proposal.criteria
                .filter((c) => c.evidence?.text)
                .slice(0, 3)
                .map((c) => (
                  <EvidenceQuote key={c.id} source={c.id}>
                    <bdi>{c.evidence!.text}</bdi>
                  </EvidenceQuote>
                ))}
              <dl className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
                <dt className="text-ink-muted">{t("model")}</dt>
                <dd>
                  <DataCell>{proposal.proposal.model ?? t("notStored")}</DataCell>
                </dd>
                <dt className="text-ink-muted">{t("prompt")}</dt>
                <dd>
                  <DataCell>{(proposal.proposal.prompt_sha256 ?? t("notStored")).slice(0, 19)}</DataCell>
                </dd>
                <dt className="text-ink-muted">{t("proposalId")}</dt>
                <dd>
                  <DataCell>{proposal.proposal.proposal_id}</DataCell>
                </dd>
              </dl>
            </div>
          )}
        </aside>
      </div>

      {help ? (
        <div role="dialog" aria-modal="true" aria-labelledby="triage-help" className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
          <div className="max-w-lg rounded-lg bg-paper p-6">
            <h2 id="triage-help" className="font-semibold text-ink">
              {t("helpTitle")}
            </h2>
            <p className="mt-2 text-ink">
              {t("helpBody")}
            </p>
            <Button className="mt-4" onClick={() => setHelp(false)} autoFocus>
              {t("close")}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
