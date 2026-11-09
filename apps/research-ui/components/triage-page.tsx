"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { translate, type Locale } from "@/i18n";
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
  getSummary,
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
  type Summary,
} from "@/lib/screening-v1";
import { stateCopy } from "@/lib/screening-states";
import { tc, type TriageCopyKey } from "@/lib/triage-copy";
import {
  answersInOrder,
  compareAnswers,
  contradicts,
  criterionOfReason,
  decisiveFor,
  failedChecks,
  firstClause,
  mayReadProposal,
  positionOf,
  proposalAnswersOpenFirst,
  reasonFromChecklist,
  reasonOptions,
  triageKey,
  isTextField,
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
const QUEUE_OPEN_KEY = "nexus.triage.queueOpen";
const CHECKLIST_OPEN_KEY = "nexus.triage.checklistOpen";

function remembered(key: string): boolean {
  try {
    return typeof window !== "undefined" && window.sessionStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

function remember(key: string, value: boolean) {
  try {
    window.sessionStorage.setItem(key, value ? "1" : "0");
  } catch {
    /* private window: the choice simply is not remembered */
  }
}

type ProposalState =
  | { status: "hidden" }
  | { status: "none" }
  | { status: "loading" }
  | { status: "ready"; proposal: Proposal; studyId: string }
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

/** The next record still to decide after `study` in the loaded list, wrapping around. */
function nextUndecided(list: readonly QueueItem[], study: string): QueueItem | null {
  const at = list.findIndex((i) => i.study_id === study);
  const ordered = [...list.slice(at + 1), ...list.slice(0, Math.max(at, 0))];
  return ordered.find((i) => !i.decided && i.study_id !== study) ?? null;
}

export function TriagePage({ locale }: Readonly<{ locale: Locale }>) {
  return (
    // From 1024 px the screen fills the shell's height and never scrolls (spec 03, M8-triage 1).
    <div className="mx-auto w-full max-w-7xl px-6 py-10 lg:flex lg:min-h-0 lg:max-w-none lg:flex-1 lg:flex-col lg:px-6 lg:py-3">
      <ScreeningSteps locale={locale} current="triage" consoleOrigin={consoleOrigin()} className="mb-6 lg:hidden" />
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
  const [summary, setSummary] = useState<Summary | null>(null);
  // Skips in this browser session, for the counts rail; a skip writes nothing (spec 03).
  const [skippedCount, setSkippedCount] = useState(0);
  // "All decided" may be claimed only once the queue has answered (review P2-1).
  const [queueLoaded, setQueueLoaded] = useState(false);
  // Focus the next record's title once it is on screen (review P2-3).
  const focusNextTitle = useRef(false);
  // The queue card is collapsed by default; the choice lasts the browser session (spec 03, amendment 4).
  const [queueOpen, setQueueOpenState] = useState<boolean>(() => remembered(QUEUE_OPEN_KEY));
  const setQueueOpen = useCallback((value: boolean) => {
    setQueueOpenState(value);
    remember(QUEUE_OPEN_KEY, value);
  }, []);
  // The checklist is collapsed by default (spec 03, M8-triage 2). E and 1/2/3 open it
  // for the record on screen; only its toggle's choice lasts the browser session.
  const checklistChoice = useRef<boolean>(remembered(CHECKLIST_OPEN_KEY));
  const [checklistOpen, setChecklistOpen] = useState<boolean>(checklistChoice.current);
  const toggleChecklist = useCallback(() => {
    setChecklistOpen((open) => {
      checklistChoice.current = !open;
      remember(CHECKLIST_OPEN_KEY, !open);
      return !open;
    });
  }, []);
  const cache = useRef(new Map<string, RecordDetail>());
  const recordHeading = useRef<HTMLParagraphElement>(null);
  const revealedHeading = useRef<HTMLHeadingElement>(null);
  // The record on screen. Every async result checks it, so a late response for a
  // record the researcher has left never lands on the one now shown (review 1).
  const current = useRef<string | null>(null);

  const item = items.find((i) => i.study_id === selected) ?? null;
  useEffect(() => {
    if (record && focusNextTitle.current) {
      focusNextTitle.current = false;
      recordHeading.current?.focus();
    }
  }, [record]);
  // The latest queue for key handlers that may run before the next render.
  const itemsRef = useRef(items);
  itemsRef.current = items;

  const loadQueue = useCallback(
    async (nextView: QueueView, append = false, from = 0) => {
      const page = await getQueue(origin, { view: nextView, cursor: from, limit: 50 });
      setItems((prev) => (append ? [...prev, ...page.items] : page.items));
      setCursor(page.next_cursor);
      setQueueLoaded(true);
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
    async (detail: RecordDetail, queueItem: QueueItem | null, active: Settings) => {
      const hasProposal = queueItem?.has_proposal ?? false;
      if (!hasProposal) {
        setProposal({ status: detail.my_decision || active.blinding === "show" ? "none" : "hidden" });
        return;
      }
      if (!mayReadProposal({ hasProposal, decided: detail.my_decision !== null, blinding: active.blinding })) {
        setProposal({ status: "hidden" });
        return;
      }
      const study = detail.study_id;
      if (current.current !== study) return;
      setProposal({ status: "loading" });
      try {
        const draft = await getProposal(origin, study);
        if (current.current !== study) return;
        setProposal(draft ? { status: "ready", proposal: draft, studyId: study } : { status: "none" });
      } catch (error) {
        if (current.current !== study) return;
        const code = codeOf(error);
        setProposal(code === "PROPOSAL_HIDDEN" ? { status: "hidden" } : { status: "error", code });
      }
    },
    [origin],
  );

  const open = useCallback(
    async (studyId: string, list: QueueItem[], active: Settings, fresh = false) => {
      current.current = studyId;
      setSelected(studyId);
      setReasonOpen(false);
      setReason(null);
      setNote("");
      setEditing(false);
      setRefusal(null);
      setConflict(null);
      setFocusIndex(0);
      setChecklistOpen(checklistChoice.current);
      setRecord(null);
      setProposal({ status: "hidden" });
      try {
        const [detail, open] = await Promise.all([fetchRecord(studyId, fresh), getConflicts(origin)]);
        if (current.current !== studyId) return;
        setRecord(detail);
        const own = detail.my_decision?.criteria ?? [];
        setAnswers(Object.fromEntries(own.map((a) => [a.id, a.answer])));
        // A conflict from another device locks the record too, not only one this tab caused.
        const rival = open.find((c) => c.study_id === studyId) ?? null;
        setConflict(rival);
        if (rival === null) await showProposal(detail, list.find((i) => i.study_id === studyId) ?? null, active);
      } catch (error) {
        if (current.current === studyId) setRefusal(codeOf(error));
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
      const [current, counts] = await Promise.all([getSettings(origin), getSummary(origin).catch(() => null)]);
      setSettings(current);
      setSummary(counts);
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

  /** N after a decision: in "Needs you", the next undecided record, else the hand-off (review P2-2). */
  async function nextAfterDecision() {
    if (!settings) return;
    if (view !== "needs_you") return move(1);
    focusNextTitle.current = true;
    const next = nextUndecided(itemsRef.current, current.current ?? "");
    if (next) return void open(next.study_id, itemsRef.current, settings);
    const list = await loadQueue(view);
    const remaining = list.find((i) => !i.decided) ?? null;
    if (remaining) await open(remaining.study_id, list, settings);
    else {
      focusNextTitle.current = false;
      current.current = null;
      setSelected(null);
      setRecord(null);
    }
  }

  function move(step: number) {
    const list = itemsRef.current;
    if (!settings || list.length === 0) return;
    // From the record actually on screen (`current`), not this render's `selected`:
    // a key pressed right after triage advanced must not move from the old record.
    const at = Math.max(0, list.findIndex((i) => i.study_id === current.current));
    const next = list[(at + step + list.length) % list.length];
    void open(next.study_id, list, settings);
  }

  async function submit(outcome: Outcome, options: { reasonCode?: string | null; restore?: StoredEvent } = {}) {
    if (!record || !settings || busy || stale) return;
    const restore = options.restore;
    const study = record.study_id;
    const wasUndecided = record.my_decision === null;
    const shown = visibleProposal;
    const event = decisionEvent({
      record,
      screenerId: settings.screener_id,
      outcome,
      reasonCode: restore ? restore.reason_code : (options.reasonCode ?? null),
      criteria: restore ? restore.criteria : answersInOrder(record.criteria, answers),
      note: restore ? restore.note : note.trim() || null,
      supersedes: record.my_decision?.event_id ?? null,
      // Contract §3.1: name the draft that was on screen when deciding (review 2).
      proposalShown: shown ? { proposal_id: shown.proposal_id, revealed_after_decision: record.my_decision !== null } : null,
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
    const accepted = result.result !== "refused";
    const decidedItems = items.map((i) => (i.study_id === study && accepted ? { ...i, decided: true } : i));
    setItems(decidedItems);
    // The researcher may have moved on while the event was in flight.
    if (current.current !== study) return;
    if (result.result === "refused") {
      const code = result.refusal?.code ?? "REFUSED";
      if (code === "STALE_BINDING") setStale(true);
      setRefusal(code);
      setMessage(t("refused", { code }));
      return;
    }
    const detail = await fetchRecord(study, true);
    if (current.current !== study) return;
    setRecord(detail);
    setReasonOpen(false);
    setEditing(false);
    if (result.result === "conflict") {
      const open = await getConflicts(origin);
      if (current.current !== study) return;
      setConflict(open.find((c) => c.study_id === study) ?? null);
      setMessage(t("conflictTitle"));
      return;
    }
    // Refresh the counts behind "Record k of total"; a failed read keeps the old ones.
    void getSummary(origin).then(setSummary, () => undefined);
    // Advance on decide (spec 03 amendment 3): a first decision with no draft to
    // reveal, or with "move on at once", opens the next record. Otherwise the
    // revealed draft shows and N advances, as before. Under "move on at once"
    // the draft is not requested, so no reveal is recorded.
    const queueItem = decidedItems.find((i) => i.study_id === study) ?? null;
    const draftToReveal = (queueItem?.has_proposal ?? false) && settings.blinding !== "show";
    const moveOn = settings.advance_on_decide === "next_at_once";
    if (wasUndecided && !restore && (!draftToReveal || moveOn)) {
      const decidedNow = (summary?.decided ?? 0) + 1;
      const total = summary?.total ?? decidedItems.length;
      const next = nextUndecided(decidedItems, study);
      if (next) {
        focusNextTitle.current = true;
        await open(next.study_id, decidedItems, settings);
        setMessage(t("savedNext", { k: Math.min(decidedNow + 1, Math.max(total, 1)), total }));
        return;
      }
      const list = await loadQueue(view);
      const remaining = list.find((i) => !i.decided) ?? null;
      if (remaining) await open(remaining.study_id, list, settings);
      else {
        setSelected(null);
        setRecord(null);
      }
      setMessage(t("saved"));
      return;
    }
    setMessage(t("saved"));
    await showProposal(detail, queueItem, settings);
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
    setSkippedCount((n) => n + 1);
    setMessage(t("skipped"));
    move(1);
  }

  function undo() {
    if (!record) return;
    const target = undoTarget(record.my_decision, record.history);
    if (!target) return; // absent until there is something to undo (spec 03 amendment 5)
    void submit(target.outcome, { restore: target });
  }

  const decided = record?.my_decision ?? null;
  const deciding = record !== null && (decided === null || editing) && conflict === null;
  // The checklist is a tool for the reason, not a gate for the decision (spec 03, M8-triage 3):
  // Include is off only while an answer given fails; Exclude is always there and needs a reason.
  const decisive = record !== null ? decisiveFor(record.criteria, answers, record.not_reported_policy ?? "unclear") : null;
  const canInclude = decisive?.include ?? false;
  const canExclude = record !== null;
  // A reason the answers contradict would be refused (`REASON_CODE_INCONSISTENT`).
  const reasonUsable = reason !== null && !contradicts(reason, answers);
  const reasons = record ? reasonOptions(record.criteria) : [];
  const criterionText = (id: string) => record?.criteria.find((c) => c.id === id)?.text ?? "";
  const undoable = record?.my_decision ? undoTarget(record.my_decision, record.history) !== null : false;
  const allDone = queueLoaded && view === "needs_you" && items.length === 0;

  function openExclude() {
    // The reason comes from the checklist (amendment 2): the first failed criterion, pre-selected.
    // With no failed criterion, none is chosen: the chips are offered (M8-triage 3).
    setReason((chosen) => chosen ?? reasonFromChecklist(decisive?.failed ?? null));
    setReasonOpen(true);
    setChecklistOpen(true);
  }
  // The draft may be on screen only for the record it belongs to, once that
  // record is decided or the researcher chose to see drafts beside records.
  const visibleProposal =
    proposal.status === "ready" &&
    record !== null &&
    proposal.studyId === record.study_id &&
    (record.my_decision !== null || settings?.blinding === "show")
      ? proposal.proposal
      : null;

  function answer(value: Answer) {
    if (!record || !deciding) return;
    const criterion = record.criteria[focusIndex];
    if (!criterion) return;
    setChecklistOpen(true); // a number key opens a closed checklist and answers (M8-triage 2)
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
  // Swapped in a layout effect, before paint (M7b, the deferred triage race): with
  // a passive effect a key pressed once the next record was visible could still
  // reach the previous record's handler, and the decision was silently dropped.
  useLayoutEffect(() => {
    keyHandler.current = function onKey(event: KeyboardEvent) {
      // Enter confirms the chosen reason, but never from a text field or a
      // focused button, which keep their own Enter (review 7).
      if (event.key === "Enter") {
        const target = event.target;
        const own = isTextField(target) || (typeof HTMLButtonElement !== "undefined" && target instanceof HTMLButtonElement);
        if (!own && reasonOpen && reason && reasonUsable && deciding && canExclude) {
          event.preventDefault();
          void submit("EXCLUDE", { reasonCode: reason });
        }
        return;
      }
      // Reason chips take 1-9 while the panel is open (spec 03: chips 1-7; review 3).
      if (reasonOpen && /^[1-9]$/.test(event.key) && !isTextField(event.target) && !event.ctrlKey && !event.metaKey && !event.altKey) {
        const pick = reasons[Number(event.key) - 1];
        if (pick && !contradicts(pick, answers)) setReason(pick);
        event.preventDefault();
        return;
      }
      if (event.key === "Escape") {
        setHelp(false);
        setReasonOpen(false);
        return;
      }
      const key = triageKey(event, event.target);
      if (key === null) return;
      event.preventDefault();
      if (key === "help") setHelp((h) => !h);
      else if (key === "down" || key === "up") {
        if (!queueOpen) setQueueOpen(true); // the first J or K opens the queue (amendment 4)
        move(key === "down" ? 1 : -1);
      }
      else if (key === "skip" && deciding) skip();
      else if (key === "next" && !deciding) void nextAfterDecision();
      else if (key === "undo" && decided && undoable) undo();
      else if (key === "yes") answer("yes");
      else if (key === "no") answer("no");
      else if (key === "notReported") answer("not_reported");
      else if (deciding) {
        if (key === "include" && canInclude) void submit("INCLUDE");
        else if (key === "unclear") void submit("MAYBE");
        else if (key === "exclude" && canExclude) openExclude();
      }
    };
  });

  if (bootError) {
    return (
      <section role="alert" className="rounded-lg border border-rule-strong bg-leaf p-6">
        <h1 className="text-ink">{t("unreachable", { code: bootError })}</h1>
        <p className="mt-2 font-mono text-[0.8125rem] text-blocked" dir="ltr">
          {bootError}
        </p>
        <p className="mt-4 flex flex-wrap items-center gap-4">
          <Button onClick={() => void boot()}>{t("retry")}</Button>
          {/* The site header is hidden on desktop triage (decision 2026-11-09): keep a way out. */}
          <a href={stepHref(locale, "home", origin)} className="inline-flex min-h-11 items-center text-brand underline">
            {t("leave")}
          </a>
        </p>
      </section>
    );
  }

  if (!settings) return <p className="text-ink-muted">{t("loading")}</p>;

  const comparison = visibleProposal && decided ? compareAnswers(record!.criteria, decided.criteria ?? [], visibleProposal) : [];
  // What the answers allow (spec 03, M8-triage 4); it never asks for answers before a decision.
  const statusLine = !decisive
    ? ""
    : decisive.failed
      ? `${
          decisive.failed.answer === "not_reported"
            ? t("excludeReadyNotReported", { id: decisive.failed.id })
            : t("excludeReady", { id: decisive.failed.id, answer: t(ANSWER_KEY[decisive.failed.answer]).toLocaleLowerCase(locale) })
        }. ${t("includeOff")}`
      : decisive.answered === 0
        ? t("checklistOptional")
        : decisive.includeReady
          ? t("includeReady")
          : t("answeredSome", { n: decisive.answered, m: decisive.total });
  const checklistSummary = !decisive || decisive.answered === 0 ? t("summaryNone") : t("summarySome", { n: decisive.answered, m: decisive.total });
  const batch = record?.batch_index ?? item?.batch_index;
  const position = (() => {
    if (!record || !summary || batch === undefined) return null;
    if (view === "decided") {
      const at = items.findIndex((i) => i.study_id === record.study_id);
      return t("positionDecided", { k: at + 1, total: summary.decided, batch });
    }
    if (view !== "needs_you") return null;
    const before = items.slice(0, Math.max(items.findIndex((i) => i.study_id === record.study_id), 0)).filter((i) => !i.decided).length;
    const decidedNow = record.my_decision ? summary.decided - 1 : summary.decided;
    const { k, total } = positionOf({ decided: Math.max(decidedNow, 0), total: summary.total, indexInView: before });
    return t("position", { k, total, batch });
  })();
  const nextItem = selected ? nextUndecided(items, selected) : null;
  const failed = visibleProposal ? failedChecks(visibleProposal) : [];

  const summaryClass = "min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";
  // Panes scroll inside themselves from 1024 px; the page never does (spec 03, M8-triage 1).
  // `relative`: visually hidden text inside a pane (sr-only is absolute) must not reach past it.
  const pane = "lg:relative lg:min-h-0 lg:overflow-y-auto";

  return (
    <div className="space-y-6 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col lg:gap-3 lg:space-y-0">
      {/* The triage bar (decision 2026-11-09): from 1024 px it replaces the site header and the step bar. */}
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2 lg:flex-none lg:border-b lg:border-rule lg:pb-2" data-triage-bar>
        <a href={stepHref(locale, "home", origin)} className="hidden rounded-sm font-display text-lg font-semibold text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus lg:inline">
          {translate(locale, "brand.productName")}
        </a>
        <div className="w-full lg:w-auto">
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand lg:hidden rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink lg:mt-0 lg:font-sans lg:text-sm lg:font-medium lg:leading-5 lg:text-ink-muted">
            <span className="lg:hidden">{t("title")}</span>
            <span className="hidden lg:inline">{t("barTitle")}</span>
          </h1>
          <p className={`mt-1 text-ink-muted ${allDone ? "" : "lg:hidden"}`}>{allDone ? t("allDecidedLede") : settings.blinding === "show" ? t("ledeShow") : t("lede")}</p>
        </div>
        {position && !allDone ? (
          <p className="flex items-center gap-3 text-sm font-medium text-ink lg:mx-auto">
            <span data-position>{position}</span>
            {summary && summary.total > 0 ? (
              <span aria-hidden="true" className="hidden h-1.5 w-40 overflow-hidden rounded-full bg-rule lg:block" data-progress>
                <span className="block h-full bg-brand" style={{ width: `${Math.round((100 * summary.decided) / summary.total)}%` }} />
              </span>
            ) : null}
          </p>
        ) : null}
        {/* The shell's demonstration marker covers the fixture screens; this one is live (as corpus and lineage say). */}
        <p className="inline-block border border-rule-strong px-2 py-0.5 text-xs text-ink-muted lg:hidden">{t("liveStamp")}</p>
        <div className="flex flex-wrap items-center gap-1 lg:ms-auto">
          {/* Always shown: with an empty view, Queue is the way to the Decided view (review 2026-11-09). */}
          <Button variant="quiet" aria-expanded={queueOpen} aria-controls="triage-queue-list" onClick={() => setQueueOpen(!queueOpen)}>
            {t("queueToggle")} <kbd className="text-xs opacity-80">J K</kbd>
          </Button>
          <Button variant="quiet" onClick={() => setHelp(true)}>
            {t("helpButton")} <kbd className="text-xs opacity-80">?</kbd>
          </Button>
          <a href={stepHref(locale, "home", origin)} className="inline-flex min-h-11 items-center rounded-md px-3 text-sm text-brand underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
            {t("leave")}
          </a>
        </div>
      </header>

      <p role="status" aria-live="polite" className="sr-only">
        {message}
      </p>

      {stale ? (
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-2 text-blocked lg:flex-none">
          <p>{t("staleBanner")}</p>
          <details className="text-xs">
            <summary className={summaryClass}>{t("details")}</summary>
            <span className="font-mono" dir="ltr">
              STALE_BINDING
            </span>
          </details>
        </div>
      ) : null}
      {refusal && !stale ? (
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-2 text-blocked lg:flex-none" data-refusal={refusal}>
          <p>{stateCopy(locale, refusal).known ? `${stateCopy(locale, refusal).title}. ${stateCopy(locale, refusal).body}` : t("refused", { code: "" }).replace(/[:：]\s*$/, "")}</p>
          <details className="text-xs">
            <summary className={summaryClass}>{t("details")}</summary>
            <span className="font-mono" dir="ltr">
              {refusal}
            </span>
          </details>
        </div>
      ) : null}

      <div className="flex flex-col gap-6 lg:grid lg:min-h-0 lg:flex-1 lg:grid-cols-[200px_minmax(0,1fr)_300px] lg:grid-rows-[minmax(0,1fr)] lg:gap-4 xl:grid-cols-[220px_minmax(0,1fr)_340px]">
        {/* Queue (spec 03, left column); the expanded list scrolls inside it */}
        <nav aria-labelledby="triage-queue" className={`w-full rounded-lg border border-rule bg-leaf p-4 lg:max-w-none ${pane}`}>
          <h2 id="triage-queue" className="sr-only">
            {t("queueHeading")}
          </h2>
          {/* The counts rail (decision 2026-11-09): the numbers, not five filter buttons. */}
          <dl className="grid grid-cols-3 gap-2 text-center lg:grid-cols-1 lg:text-start" data-rail>
            {[
              { label: t("railNeedsYou"), value: summary?.needs_you },
              { label: t("railDecided"), value: summary?.decided },
              { label: t("railSkipped"), value: skippedCount },
            ].map((row) => (
              <div key={row.label} className="flex flex-col-reverse">
                <dt className="text-xs text-ink-muted">{row.label}</dt>
                <dd className="font-mono text-2xl leading-8 text-ink">{row.value ?? "–"}</dd>
              </div>
            ))}
          </dl>
          {queueOpen ? (
            <label className="mt-4 block text-xs text-ink-muted">
              {t("viewLabel")}
              <select
                value={view}
                onChange={(e) => void changeView(e.target.value as QueueView)}
                className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-sm text-ink"
              >
                {VIEWS.map((v) => (
                  <option key={v} value={v}>
                    {t(`view.${v}` as TriageCopyKey)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {items.length === 0 ? (
            <div id="triage-queue-list" className="mt-4 text-sm text-ink-muted">
              <p>{view === "needs_you" ? t("allDecided") : t("queueEmpty")}</p>
            </div>
          ) : !queueOpen ? (
            <ul id="triage-queue-list" className="mt-4 space-y-1" data-queue-collapsed>
              {[
                { key: "queueCurrent" as const, row: item },
                { key: "queueNext" as const, row: nextItem },
              ]
                .filter((r) => r.row !== null)
                .map(({ key, row }) => (
                  <li key={key}>
                    <button
                      type="button"
                      aria-current={row!.study_id === selected ? "true" : undefined}
                      onClick={() => void open(row!.study_id, items, settings)}
                      className={`w-full rounded-md px-2 py-2 text-start text-sm ${row!.study_id === selected ? "bg-brand-soft" : "hover:bg-leaf-raised"}`}
                    >
                      <span className="block text-xs text-ink-muted">{t(key)}</span>
                      <bdi className="line-clamp-2 text-ink">{row!.title}</bdi>
                    </button>
                  </li>
                ))}
            </ul>
          ) : (
            <ul id="triage-queue-list" className="mt-4 space-y-1">
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
          {queueOpen && cursor !== null ? (
            <Button variant="quiet" className="mt-2" onClick={() => void loadQueue(view, true, cursor)}>
              {t("queueMore")}
            </Button>
          ) : null}
        </nav>

        {allDone ? (
          <section aria-labelledby="triage-all-decided" className="rounded-lg border border-rule bg-leaf p-6 lg:col-span-2 lg:self-start" data-all-decided>
            <h2 id="triage-all-decided" className="font-display text-[1.375rem] leading-[1.75rem] text-ink">
              {t("allDecidedTitle", { total: summary?.total ?? 0 })}
            </h2>
            <p className="mt-4 flex flex-wrap items-center gap-4">
              <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={stepHref(locale, "publish", origin)}>
                {t("toPublish")}
              </a>
              <a className="text-brand underline" href={stepHref(locale, "agreement", origin)}>
                {t("toAgreement")}
              </a>
              <a className="text-brand underline" href={stepHref(locale, "home", origin)}>
                {t("toHome")}
              </a>
            </p>
          </section>
        ) : (
          <>
            {/* The record (spec 05): its own scrolling pane, reachable by keyboard */}
            <section
              aria-label={t("recordPane")}
              tabIndex={record ? 0 : undefined}
              className={`min-w-0 rounded-lg border border-rule bg-leaf p-5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus ${pane}`}
              data-record-pane
            >
              {record === null ? (
                selected ? <p className="text-ink-muted">{t("loading")}</p> : null
              ) : (
                <article>
                  <h2 id="triage-record" className="sr-only">
                    {t("recordHeading")}
                  </h2>
                  <p ref={recordHeading} tabIndex={-1} className="font-display text-[1.375rem] leading-[1.75rem] text-ink">
                    <bdi>{record.title}</bdi>
                  </p>
                  <p className="mt-1 flex flex-wrap gap-x-3 text-sm text-ink-muted">
                    <span>{record.year ?? t("notStored")}</span>
                    <span>
                      <bdi>{record.venue ?? t("notStored")}</bdi>
                    </span>
                  </p>
                  <details className="mt-1 text-xs text-ink-muted" data-record-details>
                    <summary className={summaryClass}>{t("details")}</summary>
                    <DataCell>{record.study_id}</DataCell>
                    {record.doi ? (
                      <a className="ms-2 font-mono text-anchor underline" href={`https://doi.org/${record.doi}`} dir="ltr">
                        {record.doi}
                      </a>
                    ) : null}
                  </details>
                  <div className="mt-3">
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
              )}
            </section>

            {/* The right column: reason, checklist, comparison, draft, note, history (M8-triage 1) */}
            <div className={`min-w-0 space-y-4 ${pane}`} data-right-column>
              {record && conflict ? (
                <section role="alert" className="rounded-lg border border-rule-strong bg-unclear-soft p-4">
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

              {record && deciding && reasonOpen ? (
                <fieldset className="space-y-2 rounded-lg border border-rule bg-leaf p-4">
                  <legend className="px-1 text-sm font-semibold text-ink">{t("reasonLegend")}</legend>
                  {reason ? (
                    <p className="text-sm text-ink" data-reason={reason}>
                      {(() => {
                        const { id, fails } = criterionOfReason(reason);
                        return t(fails ? "reasonFails" : "reasonMeets", { id, text: firstClause(criterionText(id)) });
                      })()}
                      <span className="block font-mono text-xs text-ink-muted" dir="ltr">
                        {reason}
                      </span>
                    </p>
                  ) : (
                    <p className="text-sm text-ink-muted">{t("reasonRequired")}</p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {reasons.map((code, index) => (
                      <button
                        key={code}
                        type="button"
                        aria-pressed={reason === code}
                        disabled={contradicts(code, answers)}
                        onClick={() => setReason(code)}
                        className={`min-h-11 rounded-md border px-3 py-1 text-start text-sm disabled:cursor-not-allowed disabled:opacity-50 ${reason === code ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
                      >
                        <span className="block">
                          {index + 1}. <bdi>{firstClause(criterionText(criterionOfReason(code).id)) || code}</bdi>
                        </span>
                        <span className="block font-mono text-xs opacity-80" dir="ltr">
                          {code}
                        </span>
                      </button>
                    ))}
                  </div>
                  <Button disabled={!reasonUsable || busy || !canExclude} onClick={() => reason && void submit("EXCLUDE", { reasonCode: reason })}>
                    {t("reasonConfirm")}
                  </Button>
                </fieldset>
              ) : null}

              {record ? (
                <section className="rounded-lg border border-rule bg-leaf p-4" data-checklist>
                  <button
                    type="button"
                    aria-expanded={checklistOpen}
                    aria-controls="triage-checklist"
                    onClick={toggleChecklist}
                    className="flex min-h-11 w-full flex-wrap items-center justify-between gap-x-3 rounded-md text-start focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                  >
                    <span className="font-semibold text-ink">{t("checklistToggle")}</span>
                    <span className="text-sm text-ink-muted">{checklistSummary}</span>
                  </button>
                  <div id="triage-checklist" hidden={!checklistOpen}>
                    {checklistOpen ? (
                      <fieldset className="mt-2" disabled={!deciding || stale}>
                        <legend className="sr-only">{t("checklistHeading")}</legend>
                        <ul className="space-y-2">
                          {record.criteria.map((c, index) => (
                            <li key={c.id} className={`rounded-md p-2 ${index === focusIndex && deciding ? "ring-2 ring-focus" : ""}`}>
                              <p className="text-sm">
                                <span className="font-mono text-ink-muted" dir="ltr">
                                  {c.id}
                                </span>{" "}
                                <span className="text-ink-muted">· {c.kind === "inclusion" ? t("inclusion") : t("exclusion")}</span>
                              </p>
                              {c.text ? (
                                <p dir="auto" className="text-sm text-ink">
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
                      </fieldset>
                    ) : null}
                  </div>
                </section>
              ) : null}

              {record && visibleProposal && decided ? (
                <section className="rounded-lg border border-rule bg-leaf p-4">
                  <h2 ref={revealedHeading} tabIndex={-1} className="font-semibold text-ink">
                    {visibleProposal.derived_outcome === decided.outcome ? t("agrees") : t("disagrees")}
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

              {/* The agent's draft (spec 05 aside): plain surface, never an include tint */}
              <aside
                aria-label={visibleProposal ? t("proposalRevealed") : t("proposalHiddenTitle")}
                className="w-full rounded-lg border border-dashed border-rule-strong bg-leaf p-4"
                data-testid="proposal-aside"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.05em] text-ink-muted rtl:tracking-normal">{t("proposalHiddenTitle")}</p>
                {visibleProposal === null && (proposal.status === "hidden" || proposal.status === "ready") ? (
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
                        {t(OUTCOME_KEY[visibleProposal!.derived_outcome])}
                        {visibleProposal!.reason_code ? ` · ${visibleProposal!.reason_code}` : ""}
                      </span>
                      <span className="text-xs text-ink-muted">{t("notADecision")}</span>
                    </p>
                    {failed.length > 0 ? (
                      <p className="text-blocked">
                        {t("proposalRejected")} · {t("failedChecks", { checks: failed.join(", ") })}
                      </p>
                    ) : null}
                    {visibleProposal!.cannot_decide ? <p className="text-unclear">{t("cannotDecide")}</p> : null}
                    {/* Every criterion with the agent's answer, open ones first: a quote alone does not say whether it supports or refutes */}
                    <section aria-labelledby="proposal-answers" className="space-y-2">
                      <p id="proposal-answers" className="text-xs font-semibold text-ink-muted">
                        {t("agentAnswers")}
                      </p>
                      <ul className="space-y-2">
                        {proposalAnswersOpenFirst(visibleProposal!.criteria).map((c) => (
                          <li key={c.id} data-criterion={c.id} data-answer={c.answer} className="space-y-1">
                            <p className="flex flex-wrap items-center gap-2 text-xs">
                              <span className="font-mono text-ink-muted" dir="ltr">
                                {c.id}
                              </span>
                              <span
                                className={`rounded-sm border px-1.5 py-0.5 font-semibold ${c.answer === "not_reported" ? "border-unclear text-unclear" : "border-rule-strong text-ink"}`}
                              >
                                {t(ANSWER_KEY[c.answer])}
                              </span>
                            </p>
                            {c.evidence?.text ? (
                              <EvidenceQuote>
                                <bdi>{c.evidence.text}</bdi>
                              </EvidenceQuote>
                            ) : (
                              <p className="text-xs text-ink-muted">{t(c.answer === "not_reported" ? "recordSilent" : "noQuote")}</p>
                            )}
                          </li>
                        ))}
                      </ul>
                    </section>
                    <details className="text-xs" data-proposal-details>
                      <summary className={`${summaryClass} text-ink-muted`}>{t("details")}</summary>
                      <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
                        <dt className="text-ink-muted">{t("model")}</dt>
                        <dd>
                          <DataCell>{visibleProposal!.model ?? t("notStored")}</DataCell>
                        </dd>
                        <dt className="text-ink-muted">{t("prompt")}</dt>
                        <dd>
                          <DataCell>{(visibleProposal!.prompt_sha256 ?? t("notStored")).slice(0, 19)}</DataCell>
                        </dd>
                        <dt className="text-ink-muted">{t("proposalId")}</dt>
                        <dd>
                          <DataCell>{visibleProposal!.proposal_id}</DataCell>
                        </dd>
                      </dl>
                    </details>
                  </div>
                )}
              </aside>

              {record && deciding ? (
                <label className="block rounded-lg border border-rule bg-leaf p-4 text-sm text-ink">
                  {t("noteLabel")}
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    rows={2}
                    className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
                  />
                </label>
              ) : null}

              {record && decided && !editing && record.history.length > 1 ? (
                <details className="rounded-lg border border-rule bg-leaf px-4 text-sm">
                  <summary className={`${summaryClass} text-brand`}>{t("history")}</summary>
                  <ol className="mb-3 space-y-1">
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
          </>
        )}
      </div>

      {/* The decision bar: never scrolls away (spec 03, M8-triage 1) */}
      {record && !allDone ? (
        <section aria-labelledby="triage-decision" className="rounded-lg border border-rule bg-leaf px-4 py-3 lg:flex-none" data-decision-bar>
          <h2 id="triage-decision" className="sr-only">
            {t("decisionHeading")}
          </h2>
          {decided && !editing ? (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <p className="flex flex-wrap items-center gap-2 text-ink">
                {t("decidedAs")}
                <DecisionBadge role={OUTCOME_ROLE[decided.outcome]}>
                  {t(OUTCOME_KEY[decided.outcome])}
                  {decided.reason_code ? ` · ${decided.reason_code}` : ""}
                </DecisionBadge>
                {decided.changed_after_reveal ? <DecisionBadge role="unclear">{t("changedAfterReveal")}</DecisionBadge> : null}
                <span className="text-xs text-ink-muted" title={`${t("savedWord")} ${new Date(decided.decided_at).toLocaleString(locale)}`}>
                  {t("savedWord")}
                </span>
              </p>
              <div className="flex flex-wrap gap-2">
                <Button variant="primary" onClick={() => void nextAfterDecision()} disabled={conflict !== null}>
                  {t("next")} <kbd className="text-xs opacity-80">N</kbd>
                </Button>
                <Button onClick={() => setEditing(true)} disabled={conflict !== null || stale}>
                  {t("change")}
                </Button>
                {undoable ? (
                  <Button onClick={undo} disabled={conflict !== null || stale}>
                    {t("undo")} <kbd className="text-xs opacity-80">Z</kbd>
                  </Button>
                ) : null}
              </div>
              <details className="text-xs text-ink-muted" data-decision-details>
                <summary className={summaryClass}>{t("details")}</summary>
                <p className="pb-2">
                  {t("recordedAs", {
                    time: new Date(decided.decided_at).toLocaleString(locale),
                    fingerprint: decided.binding.protocol_fingerprint.slice(0, 19),
                  })}
                </p>
              </details>
            </div>
          ) : deciding ? (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <div className="flex flex-wrap gap-2">
                <Button variant="primary" disabled={!canInclude || busy || stale} onClick={() => void submit("INCLUDE")}>
                  {t("include")} <kbd className="text-xs opacity-80">I</kbd>
                </Button>
                <Button disabled={!canExclude || busy || stale} aria-expanded={reasonOpen} onClick={openExclude}>
                  {t("exclude")} <kbd className="text-xs opacity-80">E</kbd>
                </Button>
                <Button disabled={busy || stale} onClick={() => void submit("MAYBE")}>
                  {t("unclear")} <kbd className="text-xs opacity-80">U</kbd>
                </Button>
                <Button variant="quiet" onClick={skip}>
                  {t("skip")} <kbd className="text-xs opacity-80">S</kbd>
                </Button>
              </div>
              {statusLine ? (
                <p className="min-w-0 flex-1 text-sm text-ink-muted" role="status" aria-live="polite" data-decisive>
                  {statusLine}
                </p>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

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
