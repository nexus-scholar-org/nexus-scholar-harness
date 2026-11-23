"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ComponentType, type FocusEvent, type KeyboardEvent as ReactKeyboardEvent, type SVGProps } from "react";
import {
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentArrowUpIcon,
  EyeSlashIcon,
  InboxIcon,
  LinkIcon,
  MinusCircleIcon,
  NoSymbolIcon,
  QuestionMarkCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";

import { formatNumber, translate, type Locale } from "@/i18n";
import { Button, DataCell, Hint, PRIMARY_LINK } from "@/components/ui/base";
import { stepHref } from "@/components/screening-state-card";
import { notifyReviewChanged } from "@/components/review-bus";
import { isScreeningApiError } from "@/lib/screening-api";
import { localDate, localStamp } from "@/lib/local-time";
import { newEventId } from "@/lib/screening-v1";
import {
  attachPdf,
  attachmentHref,
  chartingEvent,
  chartingHref,
  fetchedHref,
  getCharting,
  getChartingRecord,
  getFetchPlan,
  postChartingEvents,
  postLink,
  type Cell,
  type CellState,
  type CellValue,
  type ChartingEvent,
  type ChartingRecord,
  type ChartingRow,
  type DiscardReason,
  type EventKind,
  type FetchRun,
  type FormColumn,
  type FulltextStatus,
  type NotRetrievedReason,
} from "@/lib/charting-api";
import { cc, refusalWords, type ChartingCopyKey } from "@/lib/charting-copy";
import { ACTIVE_STATES, DISCARD_KEY, DISCARD_REASONS, confirmAsksFirst } from "@/lib/charting-fetch";
import {
  REASON_KEY,
  STATUS_KEY,
  STATUS_ROLE,
  UNREACHABLE_CODES,
  cellContent,
  cellOf,
  chartingKey,
  decisionValue,
  draftOf,
  fileSize,

  isShowFilter,
  sameValue,
  statusValue,
  valueOfDraft,
  visibleRows,
  type CellDraft,
  type ShowFilter,
  type TableView,
} from "@/lib/charting-logic";

import { ChartAgainMark, FOCUS_RING, HistoryLine, NoFullTextMark, PilotMark, TYPE_KEY, chartAgainHistory, optionWords } from "./charting-cells";
import {
  FetchBadge,
  InterruptedCard,
  LookupLines,
  PendingFile,
  PlanBlock,
  RunCard,
  Say,
  SummaryCard,
  TriedDisclosure,
  planAsks,
  useFetchRun,
  useFocusOnShow,
  type PlanState,
} from "./charting-fetch";
import { RoleBadge, useViewport } from "./charting-page";

/**
 * The one-study view (spec 02, M12a Part B): one study read on the left (its
 * record, the full-text part of Part A and the abstract as plain text), the
 * charting form on the right, one field per form column with its definition,
 * Not reported and Not applicable as toggle buttons, a note and "where from".
 * A field is saved when it loses focus or on Enter, one event per field; J and
 * K (or Ctrl+Down and Ctrl+Up, also inside a field) save first and move to the
 * next or previous study of the list the screen was opened from; Esc goes back
 * to the same row, view and filter. The engine judges every event.
 *
 * The study travels as `?id=`: the packaged app is exported as prebuilt pages.
 *
 * Part F (spec 03 "One-study view"): a fetched file waiting on the study takes
 * the place of the status choice until it is confirmed (C) or discarded (D);
 * L asks the plan of a look-up of this one record.
 */

type Refusal = { code: string; message: string };
type Icon = ComponentType<SVGProps<SVGSVGElement>>;

type Load =
  | { status: "loading" }
  | { status: "ready" }
  | { status: "missing" }
  | { status: "not_kept"; refusal: Refusal }
  | { status: "not_published"; refusal: Refusal }
  | { status: "refused"; refusal: Refusal }
  | { status: "offline" };

type FieldDraft = { value: CellDraft; note: string; whereFrom: string };
type Before = { value: unknown; note?: string | null; whereFrom?: string | null };
type UndoStep = Before & { studyId: string; kind: EventKind; supersedes: string };
type Mode =
  | { kind: "notRetrieved"; reason: NotRetrievedReason | null; words: string }
  // `confirmRow`: the waiting file the decision confirms first, in the same request (spec 03, I and E).
  | { kind: "exclude"; code: string | null; words: string; confirmRow?: string | null }
  // Part F: confirm a fetched file after a question; discard it with one reason.
  | { kind: "fetchConfirm"; manifestRow: string; then: "INCLUDE" | "EXCLUDE" | null }
  | { kind: "discard"; manifestRow: string; reason: DiscardReason | null; words: string };

const STATUS_ICON: Record<FulltextStatus, Icon> = { to_get: InboxIcon, requested: ClockIcon, retrieved: CheckCircleIcon, not_retrieved: NoSymbolIcon };
const STATUSES: readonly FulltextStatus[] = ["to_get", "requested", "retrieved", "not_retrieved"];

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function refusalOf(error: unknown): Refusal {
  if (!isScreeningApiError(error)) return { code: "ENGINE_UNREACHABLE", message: "" };
  return { code: error.code, message: error.serverMessage };
}

function fieldDraft(column: FormColumn, cell: Cell): FieldDraft {
  return { value: draftOf(column, cell), note: cell.note ?? "", whereFrom: cell.where_from ?? "" };
}

function sameDraft(a: CellDraft, b: CellDraft): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function ChartingStudyPage({ locale }: Readonly<{ locale: Locale }>) {
  return (
    // From 1024 px the screen fills the shell's height and never scrolls; its two columns do (spec 02).
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:flex lg:min-h-0 lg:max-w-none lg:flex-1 lg:flex-col lg:px-6 lg:py-2">
      <StudyScreen locale={locale} />
    </div>
  );
}

function StudyScreen({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values), [locale]);
  const origin = useMemo(consoleOrigin, []);

  const [load, setLoad] = useState<Load>({ status: "loading" });
  const [place, setPlace] = useState<{ view: TableView; show: ShowFilter; excluded: boolean }>({ view: "charting", show: "all", excluded: false });
  const [studyId, setStudyId] = useState<string | null>(null);
  const [list, setList] = useState<string[]>([]);
  const [screener, setScreener] = useState("researcher:local");
  const [record, setRecord] = useState<ChartingRecord | null>(null);
  const [switching, setSwitching] = useState(false);
  const [drafts, setDrafts] = useState<Record<string, FieldDraft>>({});
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [fieldRefusal, setFieldRefusal] = useState<{ column: string; code: string } | null>(null);
  const [offline, setOffline] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [announce, setAnnounce] = useState("");
  const [statusLine, setStatusLine] = useState("");
  const [mode, setMode] = useState<Mode | null>(null);
  const [linkOpen, setLinkOpen] = useState(false);
  const [linkText, setLinkText] = useState("");
  const [busy, setBusy] = useState(false);
  const undoStack = useRef<UndoStep[][]>([]);
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const recordRef = useRef(record);
  recordRef.current = record;
  const draftsRef = useRef(drafts);
  draftsRef.current = drafts;
  const fileInput = useRef<HTMLInputElement>(null);
  const wordsInput = useRef<HTMLInputElement>(null);
  // Where the focus goes once a study is on screen, and for which study (H-charting-focus-fault).
  const focusAfterLoad = useRef<{ studyId: string; which: "first" | "decision" } | null>(null);
  // Part F: the plan panel of a look-up of this record, where Esc returns the focus, "What was tried", the run.
  const viewport = useViewport();
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const [plan, setPlan] = useState<PlanState | null>(null);
  const planRef = useRef<HTMLElement | null>(null);
  const planBack = useRef<HTMLElement | null>(null);
  const [triedOpen, setTriedOpen] = useState(false);
  const [dismissed, setDismissed] = useState<ReadonlySet<string>>(new Set());
  // The other records' titles, for "The same file is waiting for another record: <title>".
  const [titles, setTitles] = useState<ReadonlyMap<string, string>>(new Map());
  const runMark = useRef("");
  const runStarted = useRef(false);

  const row = record?.row ?? null;
  const form = record?.form ?? null;
  const columns = useMemo(() => form?.columns ?? [], [form]);
  const archived = record?.read_only ?? false;
  const notKept = row ? !row.kept : false;
  const excluded = row?.ft_decision?.outcome === "EXCLUDE";
  const formLocked = archived || notKept || excluded;
  const ftLocked = archived || notKept;
  const pending = row?.fulltext.pending_fetch ?? null;
  const reasons = record?.reason_options ?? [];
  const notRetrievedReasons = record?.not_retrieved_reasons ?? ["no_access", "not_found", "no_reply", "other"];

  const position = studyId ? list.indexOf(studyId) : -1;
  const total = list.length;

  const tableHref = useCallback(
    (rowId: string | null) => chartingHref(locale, origin, { view: place.view, show: place.show, excluded: place.excluded, row: rowId }),
    [locale, origin, place],
  );

  /** Read one study; drafts start from its stored cells. */
  const readStudy = useCallback(
    async (id: string) => {
      try {
        const answer = await getChartingRecord(origin, id);
        recordRef.current = answer;
        setRecord(answer);
        const fresh = Object.fromEntries(answer.form.columns.map((c) => [c.column_id, fieldDraft(c, cellOf(answer.row, c.column_id))]));
        draftsRef.current = fresh;
        setDrafts(fresh);
        setLoad({ status: "ready" });
        setOffline(false);
        if (answer.row.ft_decision?.outcome === "EXCLUDE" && answer.row.kept && !answer.read_only) focusAfterLoad.current = { studyId: answer.row.study_id, which: "decision" };
        return true;
      } catch (error) {
        const r = refusalOf(error);
        if (r.code === "RECORD_NOT_KEPT") setLoad({ status: "not_kept", refusal: r });
        else if (r.code === "SCREENING_NOT_PUBLISHED") setLoad({ status: "not_published", refusal: r });
        else if (UNREACHABLE_CODES.has(r.code)) setLoad({ status: "offline" });
        else setLoad({ status: "refused", refusal: r });
        return false;
      }
    },
    [origin],
  );

  // The study, the list's place and the neighbours, read once after mounting.
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const id = query.get("id");
    const show = query.get("show");
    const next = { view: (query.get("view") === "fulltext" ? "fulltext" : "charting") as TableView, show: isShowFilter(show) ? show : "all", excluded: query.get("excluded") === "1" };
    setPlace(next);
    if (!id) {
      setLoad({ status: "missing" });
      return;
    }
    setStudyId(id);
    void (async () => {
      try {
        const table = await getCharting(origin);
        setScreener(table.screener_id);
        setTitles(new Map(table.rows.map((r) => [r.study_id, r.title ?? r.study_id])));
        // The list is the charting screen's "Show" list when the study was opened, kept as it was then.
        let ids = visibleRows(table.rows, next.show, next.excluded).map((r) => r.study_id);
        if (!ids.includes(id)) ids = visibleRows(table.rows, "all", true).map((r) => r.study_id);
        setList(ids);
      } catch {
        // The record read below says what is wrong; without the list, J and K stay put.
      }
      focusAfterLoad.current = focusAfterLoad.current ?? { studyId: id, which: "first" };
      await readStudy(id);
    })();
  }, [origin, readStudy]);

  // After a move, the focus lands on the first field of the study (or its decision when it is excluded).
  // The request names its study: React may run this effect for a render made before a move (when the
  // move's first update starts, it runs the effects still waiting), and that render still shows the
  // previous study, whose fields are about to go. Only the render of the named study spends the request.
  useEffect(() => {
    const pendingFocus = focusAfterLoad.current;
    if (load.status !== "ready" || switching || !pendingFocus || record?.row.study_id !== pendingFocus.studyId) return;
    const which = pendingFocus.which;
    focusAfterLoad.current = null;
    const target =
      which === "decision"
        ? document.querySelector<HTMLElement>("[data-decision-control] button")
        : document.querySelector<HTMLElement>("[data-field] input:not(:disabled), [data-field] textarea:not(:disabled), [data-field] button:not(:disabled)");
    target?.focus();
  }, [load.status, switching, record]);

  // Part F: the workspace's look-up; while it runs, this study is read again as it moves (a file may arrive).
  const onRunChange = useCallback(
    (next: FetchRun, previous: FetchRun | null) => {
      const mark = `${next.run_id}:${next.reached ?? 0}:${next.downloaded ?? 0}:${next.state}`;
      const id = recordRef.current?.row.study_id;
      if (id && previous && previous.run_id === next.run_id && mark !== runMark.current) {
        void getChartingRecord(origin, id)
          .then((answer) => adoptRef.current(answer.row))
          .catch(() => undefined);
      }
      runMark.current = mark;
    },
    [origin],
  );
  const fetchRun = useFetchRun(origin, t, n, onRunChange);
  const loadRun = fetchRun.load;
  useEffect(() => {
    if (load.status !== "ready" || runStarted.current) return;
    runStarted.current = true;
    void loadRun();
  }, [load.status, loadRun]);
  useFocusOnShow(planRef, plan !== null, plan === null ? "" : plan.status === "mailto" ? "mailto" : "plan");
  const adoptRef = useRef<(changed: ChartingRow) => void>(() => undefined);

  function changesAllowed(): boolean {
    if (offline) {
      setStatusLine(t("charting.refusal.OFFLINE"));
      return false;
    }
    if (archived) {
      setStatusLine(t("charting.study.archived"));
      return false;
    }
    return recordRef.current !== null;
  }

  function wentOffline(error: unknown) {
    const r = refusalOf(error);
    if (UNREACHABLE_CODES.has(r.code)) setOffline(true);
    else setRefusal(r);
  }

  /** The engine's answer for this study: the row and counts; the drafts of the saved fields follow it. */
  function adopt(changed: ChartingRow | undefined, sent: Record<string, FieldDraft>) {
    if (!changed) return;
    const now = recordRef.current;
    if (!now || now.row.study_id !== changed.study_id) return;
    // The ref follows at once, so a save queued right behind this one compares against this answer.
    const updated = { ...now, row: changed };
    recordRef.current = updated;
    setRecord(updated);
    const formNow = updated.form;
    setDrafts((current) => {
      const next = { ...current };
      for (const [cid, was] of Object.entries(sent)) {
        const column = formNow.columns.find((c) => c.column_id === cid);
        if (!column || !next[cid]) continue;
        const fresh = fieldDraft(column, cellOf(changed, cid));
        // A part the researcher changed again while it was being saved keeps their newer words.
        next[cid] = {
          value: sameDraft(next[cid].value, was.value) ? fresh.value : next[cid].value,
          note: next[cid].note === was.note ? fresh.note : next[cid].note,
          whereFrom: next[cid].whereFrom === was.whereFrom ? fresh.whereFrom : next[cid].whereFrom,
        };
      }
      return next;
    });
  }
  adoptRef.current = (changed: ChartingRow) => adopt(changed, {});

  async function post(events: ChartingEvent[], before: Map<string, Before>, sent: Record<string, FieldDraft>, fieldOf: Map<string, string>): Promise<boolean> {
    setBusy(true);
    setRefusal(null);
    setFieldRefusal(null);
    try {
      const answer = await postChartingEvents(origin, events);
      const accepted = events.filter((e) => answer.results.some((r) => r.event_id === e.event_id && r.result !== "refused"));
      const refused = answer.results.find((r) => r.result === "refused");
      const mine = answer.rows.find((r) => r.study_id === recordRef.current?.row.study_id);
      // A refused field returns to its last saved value, with the refusal beside it (spec 02 "Error").
      const resetSent = { ...sent };
      adopt(mine, resetSent);
      if (refused) {
        const code = refused.refusal?.code ?? "REFUSED";
        const column = fieldOf.get(refused.event_id);
        if (column) setFieldRefusal({ column, code });
        else setRefusal({ code, message: refused.refusal?.message ?? "" });
      }
      if (accepted.length > 0) {
        undoStack.current.push(accepted.map((e) => ({ studyId: e.study_id, kind: e.kind, supersedes: e.event_id, ...(before.get(e.event_id) ?? { value: null }) })));
        setLastSaved(new Date().toISOString());
        setAnnounce(t("charting.announce.saved"));
        setStatusLine(t("charting.announce.saved"));
        notifyReviewChanged();
      }
      return !refused;
    } catch (error) {
      wentOffline(error);
      return false;
    } finally {
      setBusy(false);
    }
  }

  /** The cell event of one field, or null when nothing changed (a note waits for a value). */
  function cellEventFor(column: FormColumn, options: { special?: "not_reported" | "not_applicable"; force?: boolean } = {}): { event: ChartingEvent; before: Before } | "notANumber" | null {
    const current = recordRef.current;
    if (!current) return null;
    const cid = column.column_id;
    const cell = cellOf(current.row, cid);
    const draft = draftsRef.current[cid] ?? fieldDraft(column, cell);
    let state: CellState = cell.state;
    let value: CellValue = cell.state === "value" ? cell.value : null;
    if (options.special) {
      state = cell.state === options.special && !cell.chart_again ? null : options.special;
      value = null;
    } else if (cell.state !== "not_reported" && cell.state !== "not_applicable") {
      const parsed = valueOfDraft(column, draft.value);
      if (parsed.kind === "notANumber") return "notANumber";
      state = parsed.kind === "clear" ? null : "value";
      value = parsed.kind === "clear" ? null : parsed.value;
    }
    const note = state === null ? null : draft.note.trim() || null;
    const whereFrom = state === null ? null : draft.whereFrom.trim() || null;
    if (state === null && cell.state === null) return null;
    const unchanged = state === cell.state && sameValue(value, cell.state === "value" ? cell.value : null) && note === (cell.note ?? null) && whereFrom === (cell.where_from ?? null);
    if (unchanged && !(options.force && cell.chart_again)) return null;
    const event = chartingEvent({
      studyId: current.row.study_id,
      screenerId: screener,
      kind: "cell",
      value: { column_id: cid, state, value: state === "value" ? value : null },
      note,
      whereFrom,
      supersedes: cell.event_id,
    });
    const restore = cellContent(cid, cell);
    return { event, before: { value: restore.value, note: restore.note, whereFrom: restore.whereFrom } };
  }

  /** Save some fields of this study in one request, one event per field; queued so each sees the last answer. */
  function commit(cids: readonly string[], options: { special?: "not_reported" | "not_applicable"; force?: boolean } = {}): Promise<boolean> {
    const run = async () => {
      const current = recordRef.current;
      if (!current || formLocked || cids.length === 0) return true;
      if (offline) {
        setStatusLine(t("charting.refusal.OFFLINE"));
        return false;
      }
      const events: ChartingEvent[] = [];
      const before = new Map<string, Before>();
      const sent: Record<string, FieldDraft> = {};
      const fieldOf = new Map<string, string>();
      for (const cid of cids) {
        const column = current.form.columns.find((c) => c.column_id === cid);
        if (!column) continue;
        const built = cellEventFor(column, options);
        if (built === "notANumber") {
          setFieldRefusal({ column: cid, code: "NUMBER" });
          return false;
        }
        if (!built) continue;
        events.push(built.event);
        before.set(built.event.event_id, built.before);
        fieldOf.set(built.event.event_id, cid);
        sent[cid] = { ...(draftsRef.current[cid] ?? fieldDraft(column, cellOf(current.row, cid))) };
      }
      if (events.length === 0) return true;
      return post(events, before, sent, fieldOf);
    };
    const next = queue.current.then(run, run);
    queue.current = next.catch(() => undefined);
    return next;
  }

  function commitAll(): Promise<boolean> {
    return commit(columns.map((c) => c.column_id));
  }

  function setDraft(cid: string, patch: Partial<FieldDraft>) {
    setDrafts((current) => ({ ...current, [cid]: { ...(current[cid] ?? { value: "", note: "", whereFrom: "" }), ...patch } }));
  }

  /** Move to the next or previous study of the list, saving first; past the last one, back to the charting screen. */
  async function move(delta: number) {
    if (switching || !studyId) return;
    await commitAll();
    const at = list.indexOf(studyId);
    const nextId = at >= 0 ? list[at + delta] : undefined;
    if (!nextId) {
      if (delta > 0 && at === list.length - 1) window.location.assign(tableHref(studyId));
      return;
    }
    setSwitching(true);
    setMode(null);
    setLinkOpen(false);
    setRefusal(null);
    setFieldRefusal(null);
    setStatusLine("");
    try {
      const query = new URLSearchParams(window.location.search);
      query.set("id", nextId);
      window.history.replaceState(window.history.state, "", `${window.location.pathname}?${query.toString()}`);
    } catch {
      /* an address that cannot be rewritten keeps the study on screen all the same */
    }
    setStudyId(nextId);
    focusAfterLoad.current = { studyId: nextId, which: "first" };
    const ok = await readStudy(nextId);
    setSwitching(false);
    if (ok) setAnnounce(t("charting.study.announce.moved", { k: list.indexOf(nextId) + 1, total: list.length }));
  }

  async function back() {
    await commitAll();
    window.location.assign(tableHref(studyId));
  }

  // ---------------------------------------------------------- the full-text part (Part A events)

  async function sendOne(kind: EventKind, value: unknown, supersedes: string | null, previous: unknown) {
    const current = recordRef.current;
    if (!current || !changesAllowed() || ftLocked) return;
    const event = chartingEvent({ studyId: current.row.study_id, screenerId: screener, kind, value, supersedes });
    await post([event], new Map([[event.event_id, { value: previous }]]), {}, new Map());
  }

  function setStatus(value: Record<string, string>) {
    if (!row) return;
    void sendOne("fulltext_status", value, row.heads.fulltext_status, statusValue(row));
  }

  function decide(value: Record<string, string>) {
    if (!row) return;
    void sendOne("fulltext_decision", value, row.heads.fulltext_decision, decisionValue(row.ft_decision));
  }

  function askStatus(status: FulltextStatus) {
    if (!row || ftLocked || !changesAllowed()) return;
    // Part F (question 6): the status waits until the fetched file is confirmed or discarded.
    if (pending) {
      setStatusLine(t("charting.fetch.waiting"));
      return;
    }
    if (status === "not_retrieved") setMode({ kind: "notRetrieved", reason: null, words: "" });
    else setStatus({ status });
  }

  function askDecision(outcome: "INCLUDE" | "EXCLUDE") {
    if (!row || ftLocked || !changesAllowed()) return;
    if (pending) {
      setMode({ kind: "fetchConfirm", manifestRow: pending.manifest_row, then: outcome });
      return;
    }
    if (outcome === "INCLUDE") decide({ outcome: "INCLUDE" });
    else setMode({ kind: "exclude", code: null, words: "" });
  }

  // ---------------------------------------------------------- Part F: look up, confirm, discard

  /** A confirm or a discard, and the decision a confirm may carry: one request, one undo step (the decision undone first). */
  async function sendFetch(events: ChartingEvent[], before: Map<string, Before>, done: "confirmed" | "discarded") {
    setBusy(true);
    setRefusal(null);
    try {
      const answer = await postChartingEvents(origin, events);
      const accepted = events.filter((e) => answer.results.some((r) => r.event_id === e.event_id && r.result !== "refused"));
      const refused = answer.results.find((r) => r.result === "refused");
      adopt(answer.rows.find((r) => r.study_id === recordRef.current?.row.study_id), {});
      if (refused) setRefusal({ code: refused.refusal?.code ?? "REFUSED", message: refused.refusal?.message ?? "" });
      if (accepted.length > 0) {
        undoStack.current.push(accepted.map((e) => ({ studyId: e.study_id, kind: e.kind, supersedes: e.event_id, ...(before.get(e.event_id) ?? { value: null }) })).reverse());
        setLastSaved(new Date().toISOString());
        const words = t(done === "confirmed" ? "charting.fetch.announce.confirmed" : "charting.fetch.announce.discarded", { n: n(answer.counts.to_confirm ?? 0) });
        setAnnounce(words);
        setStatusLine(words);
        notifyReviewChanged();
      }
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
    }
  }

  function confirmFetched(decision?: Record<string, string>) {
    const current = recordRef.current;
    const waiting = current?.row.fulltext.pending_fetch;
    if (!current || !waiting || !changesAllowed()) return;
    const id = current.row.study_id;
    const confirm = chartingEvent({ studyId: id, screenerId: screener, kind: "fetched_confirm", value: { manifest_row: waiting.manifest_row }, supersedes: current.row.heads.fetched_confirm ?? null });
    const events = [confirm];
    const before = new Map<string, Before>([[confirm.event_id, { value: null }]]);
    if (decision) {
      const decided = chartingEvent({ studyId: id, screenerId: screener, kind: "fulltext_decision", value: decision, supersedes: current.row.heads.fulltext_decision });
      events.push(decided);
      before.set(decided.event_id, { value: decisionValue(current.row.ft_decision) });
    }
    void sendFetch(events, before, "confirmed");
  }

  function discardFetched(manifestRow: string, reason: DiscardReason, words: string) {
    const current = recordRef.current;
    if (!current || !changesAllowed()) return;
    const value: Record<string, string> = { manifest_row: manifestRow, reason };
    if (reason === "other") value.reason_text = words;
    const event = chartingEvent({ studyId: current.row.study_id, screenerId: screener, kind: "fetched_discard", value, supersedes: current.row.heads.fetched_discard ?? null });
    void sendFetch([event], new Map([[event.event_id, { value: null }]]), "discarded");
  }

  /** Whether C and D may act here; otherwise the words say why. */
  function waitingHere(): boolean {
    if (!row) return false;
    if (!pending) {
      setStatusLine(t("charting.fetch.noneWaiting"));
      return false;
    }
    if (notKept) {
      setRefusal({ code: "RECORD_NOT_KEPT", message: "" });
      return false;
    }
    return changesAllowed();
  }

  function askConfirm() {
    if (!waitingHere() || !pending) return;
    if (confirmAsksFirst(pending)) setMode({ kind: "fetchConfirm", manifestRow: pending.manifest_row, then: null });
    else confirmFetched();
  }

  function askDiscard() {
    if (!waitingHere() || !pending) return;
    setMode({ kind: "discard", manifestRow: pending.manifest_row, reason: null, words: "" });
  }

  /** L: the plan panel for this one record (question 9). */
  async function askLookup() {
    if (!row || !changesAllowed()) return;
    const ids = [row.study_id];
    planBack.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setMode(null);
    setTriedOpen(false);
    setRefusal(null);
    setPlan({ status: "counting", ids });
    try {
      const answer = await getFetchPlan(origin, ids);
      setPlan((current) => (current && current.ids === ids ? { status: "ready", ids, plan: answer } : current));
    } catch (error) {
      const r = refusalOf(error);
      if (r.code === "MAILTO_NOT_SET") setPlan((current) => (current && current.ids === ids ? { status: "mailto", ids } : current));
      else {
        setPlan(null);
        wentOffline(error);
      }
    }
  }

  function closePlan() {
    setPlan(null);
    const back = planBack.current;
    setTimeout(() => back?.focus(), 0);
  }

  async function startLookup() {
    if (!plan || plan.status !== "ready" || !planAsks(plan.plan) || busy || !changesAllowed()) return;
    const ids = plan.ids;
    setBusy(true);
    try {
      await fetchRun.start(ids);
      closePlan();
    } catch (error) {
      const r = refusalOf(error);
      if (r.code === "MAILTO_NOT_SET") setPlan({ status: "mailto", ids });
      else {
        setPlan(null);
        wentOffline(error);
      }
    } finally {
      setBusy(false);
    }
  }

  async function cancelRun() {
    if (!changesAllowed()) return;
    try {
      await fetchRun.cancel();
    } catch (error) {
      wentOffline(error);
    }
  }

  function pick(index: number) {
    if (!mode || mode.kind === "fetchConfirm") return;
    if (mode.kind === "discard") {
      const reason = DISCARD_REASONS[index];
      if (!reason) return;
      setMode({ ...mode, reason });
      if (reason === "other") setTimeout(() => wordsInput.current?.focus(), 0);
      return;
    }
    if (mode.kind === "notRetrieved") {
      const reason = notRetrievedReasons[index];
      if (!reason) return;
      setMode({ ...mode, reason });
      if (reason === "other") setTimeout(() => wordsInput.current?.focus(), 0);
      return;
    }
    const option = reasons[index];
    if (!option) return;
    setMode({ ...mode, code: option.code });
    if (option.code === "OTHER") setTimeout(() => wordsInput.current?.focus(), 0);
  }

  function confirmMode() {
    if (!mode) return;
    if (mode.kind === "fetchConfirm") {
      if (mode.then === "EXCLUDE") {
        setMode({ kind: "exclude", code: null, words: "", confirmRow: mode.manifestRow });
        return;
      }
      setMode(null);
      confirmFetched(mode.then === "INCLUDE" ? { outcome: "INCLUDE" } : undefined);
      return;
    }
    const words = mode.words.trim();
    if (mode.kind === "discard") {
      if (!mode.reason || (mode.reason === "other" && !words)) {
        setStatusLine(t("charting.refusal.DISCARD_REASON_REQUIRED"));
        return;
      }
      setMode(null);
      discardFetched(mode.manifestRow, mode.reason, words);
      return;
    }
    if (mode.kind === "notRetrieved") {
      if (!mode.reason || (mode.reason === "other" && !words)) {
        setStatusLine(t("charting.refusal.FULLTEXT_REASON_REQUIRED"));
        return;
      }
      setMode(null);
      setStatus(mode.reason === "other" ? { status: "not_retrieved", reason: "other", reason_text: words } : { status: "not_retrieved", reason: mode.reason });
      return;
    }
    if (!mode.code || (mode.code === "OTHER" && !words)) {
      setStatusLine(t("charting.refusal.FULLTEXT_REASON_REQUIRED"));
      return;
    }
    setMode(null);
    const decision: Record<string, string> = mode.code === "OTHER" ? { outcome: "EXCLUDE", reason_code: "OTHER", reason_text: words } : { outcome: "EXCLUDE", reason_code: mode.code };
    if (mode.confirmRow) confirmFetched(decision);
    else decide(decision);
  }

  async function attach(file: File) {
    const current = recordRef.current;
    if (!current || ftLocked || !changesAllowed()) return;
    const id = current.row.study_id;
    const previousAttachment = current.row.fulltext.attachment;
    const previousStatus = statusValue(current.row);
    setBusy(true);
    setRefusal(null);
    try {
      const answer = await attachPdf(origin, id, file, { eventId: newEventId(), statusEventId: newEventId() });
      if (answer.row) adopt(answer.row, {});
      if (answer.result === "accepted") {
        const steps: UndoStep[] = [];
        const attachmentEvent = answer.events.find((e) => e.kind === "attachment")?.event_id;
        const statusEvent = answer.events.find((e) => e.kind === "fulltext_status")?.event_id;
        if (attachmentEvent) steps.push({ studyId: id, kind: "attachment", value: previousAttachment, supersedes: attachmentEvent });
        if (statusEvent) steps.push({ studyId: id, kind: "fulltext_status", value: previousStatus, supersedes: statusEvent });
        if (steps.length) undoStack.current.push(steps);
      }
      setAnnounce(t("charting.announce.saved"));
      setStatusLine(t("charting.announce.saved"));
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
    }
  }

  async function saveLink() {
    const current = recordRef.current;
    const url = linkText.trim();
    if (!current || !url || ftLocked || !changesAllowed()) return;
    const previous = current.row.fulltext.link ? { url: current.row.fulltext.link } : null;
    const eventId = newEventId();
    setBusy(true);
    setRefusal(null);
    try {
      const answer = await postLink(origin, current.row.study_id, url, eventId);
      if (answer.row) adopt(answer.row, {});
      if (answer.result === "accepted") undoStack.current.push([{ studyId: current.row.study_id, kind: "link", value: previous, supersedes: answer.events.find((e) => e.kind === "link")?.event_id ?? eventId }]);
      setLinkOpen(false);
      setLinkText("");
      setAnnounce(t("charting.announce.saved"));
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
    }
  }

  function openFile() {
    if (!row) return;
    if (row.fulltext.attachment) window.open(attachmentHref(origin, row.study_id), "_blank", "noopener");
    else if (row.fulltext.pending_fetch) {
      if (offline) setStatusLine(t("charting.refusal.OFFLINE"));
      else window.open(fetchedHref(origin, row.study_id), "_blank", "noopener");
    } else if (row.fulltext.link) window.open(row.fulltext.link, "_blank", "noopener,noreferrer");
  }

  async function undo() {
    const steps = undoStack.current[undoStack.current.length - 1];
    if (!steps) {
      setStatusLine(t("charting.announce.nothingToUndo"));
      return;
    }
    if (!changesAllowed()) return;
    const events = steps.map((s) => chartingEvent({ studyId: s.studyId, screenerId: screener, kind: s.kind, value: s.value, supersedes: s.supersedes, note: s.note, whereFrom: s.whereFrom }));
    setBusy(true);
    try {
      const answer = await postChartingEvents(origin, events);
      const refused = answer.results.find((r) => r.result === "refused");
      const mine = answer.rows.find((r) => r.study_id === recordRef.current?.row.study_id);
      const now = recordRef.current;
      if (mine && now) {
        const updated = { ...now, row: mine };
        recordRef.current = updated;
        setRecord(updated);
        const fresh = Object.fromEntries(updated.form.columns.map((c) => [c.column_id, fieldDraft(c, cellOf(mine, c.column_id))]));
        draftsRef.current = fresh;
        setDrafts(fresh);
      }
      if (refused) setRefusal({ code: refused.refusal?.code ?? "REFUSED", message: refused.refusal?.message ?? "" });
      else {
        undoStack.current.pop();
        setAnnounce(t("charting.announce.undone"));
        setStatusLine(t("charting.announce.undone"));
        notifyReviewChanged();
      }
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
    }
  }

  // ---------------------------------------------------------- keyboard (spec 02 "Keyboard")

  const keyHandler = useRef<(event: KeyboardEvent) => void>(() => undefined);
  useEffect(() => {
    const listener = (event: KeyboardEvent) => keyHandler.current(event);
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);
  useLayoutEffect(() => {
    keyHandler.current = function onKey(event: KeyboardEvent) {
      if (load.status !== "ready" || !record) return;
      const target = event.target as HTMLElement | null;
      const field = target instanceof HTMLElement ? target.closest<HTMLElement>("[data-field]")?.dataset.field ?? null : null;
      // Ctrl+Down and Ctrl+Up work everywhere, inside a field too, and save it first.
      if ((event.ctrlKey || event.metaKey) && !event.altKey && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
        event.preventDefault();
        void move(event.key === "ArrowDown" ? 1 : -1);
        return;
      }
      // Alt+N and Alt+A on the focused field, inside its inputs too.
      if (event.altKey && !event.ctrlKey && !event.metaKey && field) {
        const letter = /^Key([A-Z])$/.exec(event.code ?? "")?.[1]?.toLowerCase() ?? event.key.toLowerCase();
        if (letter === "n" || letter === "a") {
          event.preventDefault();
          toggleSpecial(field, letter === "n" ? "not_reported" : "not_applicable");
          return;
        }
      }
      if (event.key === "Escape") {
        if (plan) {
          closePlan();
          return;
        }
        if (mode) {
          setMode(null);
          return;
        }
        if (linkOpen) {
          setLinkOpen(false);
          return;
        }
        if (triedOpen) {
          setTriedOpen(false);
          return;
        }
        if (target instanceof HTMLElement && target.closest("[data-hint]")) return;
        event.preventDefault();
        void back();
        return;
      }
      if (mode) {
        const inWords = target instanceof HTMLElement && target.dataset.modeWords !== undefined;
        if (event.key === "Enter" && (inWords || !(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) && !(target instanceof HTMLButtonElement)) {
          event.preventDefault();
          confirmMode();
          return;
        }
        if (/^[1-9]$/.test(event.key) && !inWords && !(target instanceof HTMLInputElement) && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          pick(Number(event.key) - 1);
        }
        return;
      }
      // Part F: while the plan panel is open, Enter starts the look-up and the other keys wait.
      if (plan) {
        if (event.key === "Enter" && !(target instanceof HTMLElement && target.closest("button, a, summary, input, select, textarea") !== null)) {
          event.preventDefault();
          void startLookup();
        }
        return;
      }
      if (switching) return;
      const key = chartingKey(event, target);
      if (key === null) return;
      // A phone is read-only for a fetched file: no look-up, no confirm, no discard (question 7).
      const phone = typeof window.matchMedia === "function" && !window.matchMedia("(min-width: 640px)").matches;
      if (phone && (key === "lookup" || key === "confirm" || key === "discard")) return;
      const map: Partial<Record<typeof key, () => void>> = {
        down: () => void move(1),
        up: () => void move(-1),
        toGet: () => askStatus("to_get"),
        requested: () => askStatus("requested"),
        retrieved: () => askStatus("retrieved"),
        notRetrieved: () => askStatus("not_retrieved"),
        include: () => askDecision("INCLUDE"),
        exclude: () => askDecision("EXCLUDE"),
        attach: () => {
          if (pending) setStatusLine(t("charting.fetch.waiting"));
          else if (!ftLocked && changesAllowed()) fileInput.current?.click();
        },
        open: openFile,
        undo: () => void undo(),
        lookup: () => void askLookup(),
        confirm: askConfirm,
        discard: askDiscard,
      };
      const action = map[key];
      if (!action) return;
      event.preventDefault();
      action();
    };
  });

  function toggleSpecial(cid: string, state: "not_reported" | "not_applicable") {
    if (formLocked) {
      setStatusLine(excluded ? t("charting.cell.excludedRow") : archived ? t("charting.study.archived") : t("charting.study.noLongerKept"));
      return;
    }
    if (!changesAllowed()) return;
    const studyAtKey = recordRef.current?.row.study_id ?? null;
    void commit([cid], { special: state }).then(() => {
      // The value input is off while the cell holds a special value; the focus stays on its button,
      // unless the researcher moved on while the value was saved (another field, another study).
      setTimeout(() => {
        if (!stillAt(studyAtKey, cid)) return;
        document.querySelector<HTMLElement>(`[data-field="${cid}"] [data-special="${state}"]`)?.focus();
      }, 0);
    });
  }

  /**
   * A focus asked for after a save lands only where the researcher still is: the same study, and the
   * focus still inside the field they acted on, or nowhere (its input was just switched off). A key
   * that arrives before the save's answer, Ctrl+Down or a move to another field, wins (H-charting-focus-fault).
   */
  function stillAt(studyId: string | null, cid: string): boolean {
    if (recordRef.current?.row.study_id !== studyId) return false;
    const active = document.activeElement;
    if (!active || active === document.body) return true;
    return document.querySelector(`[data-field="${cid}"]`)?.contains(active) ?? false;
  }

  /** Enter in a single-line field saves it and moves to the next field (spec 02 "Keyboard"). */
  function enterSaves(event: ReactKeyboardEvent, cid: string, allowShift = false) {
    if (event.key !== "Enter" || event.altKey || event.ctrlKey || event.metaKey) return;
    if (allowShift && event.shiftKey) return;
    event.preventDefault();
    const at = columns.findIndex((c) => c.column_id === cid);
    const studyAtKey = recordRef.current?.row.study_id ?? null;
    void commit([cid], { force: true }).then((ok) => {
      if (!ok || !stillAt(studyAtKey, cid)) return;
      const next = columns[at + 1];
      const nextTarget = next
        ? document.querySelector<HTMLElement>(`[data-field="${next.column_id}"] [data-value-input]:not(:disabled), [data-field="${next.column_id}"] [data-special]`)
        : document.querySelector<HTMLElement>("[data-next-study]");
      nextTarget?.focus();
    });
  }

  // ---------------------------------------------------------- render

  const summaryClass = `min-h-11 cursor-pointer py-3 leading-5 rounded-sm ${FOCUS_RING}`;
  const backLink = (words: string) => (
    <a href={tableHref(studyId)} className={`inline-flex min-h-11 items-center gap-2 rounded-md px-3 text-sm text-brand underline ${FOCUS_RING}`} data-back>
      {words}
    </a>
  );

  if (load.status === "missing" || load.status === "not_kept" || load.status === "not_published" || load.status === "refused" || load.status === "offline") {
    const code = load.status === "missing" ? null : load.status === "offline" ? "ENGINE_UNREACHABLE" : load.refusal.code;
    const words =
      load.status === "missing"
        ? t("charting.study.missing")
        : load.status === "not_kept"
          ? t("charting.study.notKept")
          : load.status === "offline"
            ? t("charting.offlineNoChange")
            : refusalWords(locale, load.refusal.code);
    return (
      <section className="space-y-4" data-state={load.status}>
        <h1 className="font-display text-[1.75rem] leading-[2.25rem] text-ink">{t("charting.table.title")}</h1>
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-refusal={code ?? undefined}>
          <p>{words}</p>
          {code ? (
            <details className="text-xs">
              <summary className={summaryClass}>{t("charting.details")}</summary>
              <span className="font-mono" dir="ltr">
                {code}
              </span>
            </details>
          ) : null}
        </div>
        {load.status === "not_published" ? (
          <a className={PRIMARY_LINK} data-variant="primary" href={stepHref(locale, "publish", origin)}>
            {t("charting.empty.goPublish")}
          </a>
        ) : (
          backLink(t("charting.study.back"))
        )}
      </section>
    );
  }

  const loading = load.status === "loading" || !record || !row || switching;
  const isLast = position >= 0 && position === total - 1;
  const roundWords = row ? (row.arm === "databases" ? t("charting.round.databases") : row.arm === "citation_searching" ? t("charting.round.chasing") : row.round_label) : "";
  const excludedReason = (() => {
    const d = row?.ft_decision;
    if (!d || d.outcome !== "EXCLUDE") return "";
    if (d.reason_code === "OTHER") return d.reason_text ?? "";
    const option = reasons.find((o) => o.code === d.reason_code);
    return option ? `${d.reason_code} ${option.label}` : d.reason_code ?? "";
  })();
  const noColumns = !loading && columns.length === 0;

  const pane = "lg:relative lg:min-h-0 lg:overflow-y-auto";

  // Part F: the run started here, then its summary until dismissed (the table keeps the full card).
  const run = fetchRun.run;
  const dismissRun = () => setDismissed((current) => new Set([...current, run?.run_id ?? ""]));
  const runCard =
    !run || !run.run_id ? null : ACTIVE_STATES.has(run.state) ? (
      <RunCard locale={locale} run={run} lost={fetchRun.lost} offline={offline} canCancel={!archived} phone={viewport === "phone"} n={n} onCancel={() => void cancelRun()} />
    ) : !fetchRun.watched || dismissed.has(run.run_id) ? null : run.state === "interrupted" || run.state === "failed" ? (
      <InterruptedCard locale={locale} run={run} n={n} phone={viewport === "phone"} onDismiss={dismissRun} />
    ) : run.state === "finished" || run.state === "cancelled" ? (
      <SummaryCard locale={locale} run={run} watched toConfirm={0} tryLater={0} phone={viewport === "phone"} n={n} onShow={() => undefined} onSelect={() => undefined} onDismiss={dismissRun} />
    ) : null;

  return (
    <div className="space-y-4 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col lg:gap-2 lg:space-y-0" data-charting-study>
      {/* The study bar: from 1024 px it replaces the site header (a focus screen, as triage). */}
      <header className="flex flex-wrap items-center gap-x-4 gap-y-1 lg:h-12 lg:flex-none lg:flex-nowrap lg:border-b lg:border-rule" data-study-bar>
        <a href={stepHref(locale, "home", origin)} className={`hidden shrink-0 rounded-sm font-display text-lg font-semibold text-ink lg:inline ${FOCUS_RING}`}>
          {translate(locale, "brand.productName")}
        </a>
        <h1 className="min-w-0 font-display text-xl leading-7 text-ink lg:flex-1 lg:truncate lg:font-sans lg:text-base lg:font-semibold" data-study-title>
          {loading ? <span aria-hidden="true" className="inline-flex h-5 w-72 max-w-full animate-pulse rounded-sm bg-rule" data-skeleton="title" /> : <bdi>{row.title ?? row.study_id}</bdi>}
        </h1>
        <p className="flex shrink-0 items-center gap-2 text-sm font-medium text-ink">
          {position >= 0 ? <span data-position>{t("charting.study.position", { k: position + 1, total })}</span> : null}
          {form?.pilot.on ? <PilotMark locale={locale} /> : null}
        </p>
        <span className="shrink-0 lg:ms-auto">{backLink(t("charting.study.back"))}</span>
      </header>

      {archived ? (
        <div className="rounded-md bg-blocked-soft px-4 py-2 text-blocked lg:flex-none" data-banner="archived">
          <p>{t("charting.study.archived")}</p>
          <details className="text-xs">
            <summary className={summaryClass}>{t("charting.details")}</summary>
            <span className="font-mono" dir="ltr">
              CHARTING_PROTOCOL_REPLACED
            </span>
          </details>
        </div>
      ) : null}
      {offline ? (
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-2 text-blocked lg:flex-none" data-banner="offline">
          <p>{lastSaved ? t("charting.offline", { time: localStamp(lastSaved).slice(11) }) : t("charting.offlineNoChange")}</p>
        </div>
      ) : null}
      {refusal ? (
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-2 text-blocked lg:flex-none" data-refusal={refusal.code}>
          <p>{refusal.code === "RECORD_NOT_KEPT" ? t("charting.study.notKept") : refusalWords(locale, refusal.code)}</p>
          <details className="text-xs">
            <summary className={summaryClass}>{t("charting.details")}</summary>
            <span className="font-mono" dir="ltr">
              {refusal.code}
            </span>
          </details>
        </div>
      ) : null}

      <div className="flex flex-col gap-4 lg:grid lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(0,55fr)_minmax(0,45fr)] lg:grid-rows-[minmax(0,1fr)] lg:gap-4">
        {/* The study (spec 02, left column): record, full-text part, abstract. */}
        <section aria-labelledby="study-region" tabIndex={0} className={`space-y-4 rounded-lg border border-rule bg-leaf p-4 ${pane} ${FOCUS_RING}`} data-region="study">
          <h2 id="study-region" className="sr-only">
            {t("charting.study.regionStudy")}
          </h2>
          {loading ? (
            <div aria-hidden="true" className="space-y-3" data-skeleton="study">
              {[0, 1, 2, 3].map((i) => (
                <span key={i} className="flex h-4 w-full animate-pulse rounded-sm bg-rule" />
              ))}
            </div>
          ) : (
            <>
              <div className="space-y-1 text-sm">
                {row.authors.length ? <p className="text-ink">{row.authors.join("; ")}</p> : null}
                <p className="flex flex-wrap gap-x-3 gap-y-1 text-ink-muted">
                  {row.year ? <span dir="ltr">{String(row.year)}</span> : null}
                  {row.venue ? <bdi>{row.venue}</bdi> : null}
                  <span>{t("charting.study.round", { round: roundWords })}</span>
                </p>
                {row.doi ? (
                  <a href={`https://doi.org/${row.doi}`} target="_blank" rel="noopener noreferrer" className={`inline-flex min-h-11 items-center gap-2 text-anchor ${FOCUS_RING}`} data-doi>
                    {t("charting.study.doi")}
                    <span dir="ltr" className="font-mono text-xs">
                      {row.doi}
                    </span>
                    <span className="sr-only">({t("charting.study.file.newTab")})</span>
                  </a>
                ) : null}
                <p className="flex flex-wrap items-center gap-2">
                  <RoleBadge role={row.ta_decision === "INCLUDE" ? "include" : "unclear"} icon={row.ta_decision === "INCLUDE" ? CheckCircleIcon : QuestionMarkCircleIcon} data="ta">
                    {t("charting.study.taDecision", { outcome: row.ta_decision === "INCLUDE" ? t("charting.study.taInclude") : t("charting.study.taMaybe") })}
                  </RoleBadge>
                  {row.ta_adopted ? (
                    <span className="rounded-sm bg-unclear-soft px-1.5 text-xs font-medium text-ink" data-ta-adopted>
                      {t("charting.study.taAdopted")}
                    </span>
                  ) : null}
                  {row.ta_reason ? <bdi className="text-ink-muted">{row.ta_reason}</bdi> : null}
                  {row.new_since ? (
                    <span className="rounded-sm bg-brand-soft px-1.5 text-xs font-medium text-brand" data-new>
                      {t("charting.new", { date: localDate(row.new_since) })}
                    </span>
                  ) : null}
                </p>
              </div>

              {/* The full-text part: status, file or link, and the decision (Part A events). */}
              <section aria-labelledby="study-fulltext" className="space-y-3 rounded-md border border-rule bg-paper p-3" data-fulltext-block>
                <h3 id="study-fulltext" className="text-sm font-semibold text-ink">
                  {t("charting.study.file.label")}
                </h3>
                {pending ? (
                  <p className="flex flex-wrap items-center gap-2 text-sm text-ink" data-note-waiting>
                    <FetchBadge locale={locale} />
                    <span>{t("charting.fetch.noteWaiting")}</span>
                  </p>
                ) : null}
                <div role="radiogroup" aria-label={t("charting.study.status")} aria-disabled={pending ? true : undefined} className="flex flex-wrap gap-1" data-status-control>
                  {STATUSES.map((status) => {
                    const IconOf = STATUS_ICON[status];
                    const chosen = row.fulltext.status === status;
                    return (
                      <button
                        key={status}
                        type="button"
                        role="radio"
                        aria-checked={chosen}
                        disabled={ftLocked || busy || pending !== null}
                        onClick={() => askStatus(status)}
                        className={`inline-flex min-h-11 items-center gap-1 rounded-md border px-2 text-sm disabled:opacity-60 ${chosen ? "border-brand bg-brand-soft font-semibold text-brand" : "border-rule-strong bg-leaf text-ink"} ${FOCUS_RING}`}
                        data-status={status}
                      >
                        <IconOf aria-hidden="true" className="size-4" />
                        {t(STATUS_KEY[status])}
                      </button>
                    );
                  })}
                </div>
                {row.fulltext.status === "not_retrieved" && row.fulltext.reason ? (
                  <p className="text-xs text-ink-muted">{row.fulltext.reason === "other" && row.fulltext.reason_text ? <bdi>{row.fulltext.reason_text}</bdi> : t(REASON_KEY[row.fulltext.reason])}</p>
                ) : null}
                {pending ? (
                  <PendingFile
                    locale={locale}
                    origin={origin}
                    row={row}
                    pending={pending}
                    titleOf={(id) => titles.get(id) ?? id}
                    responsive
                    disabled={ftLocked || busy}
                    onOpen={(event) => {
                      if (!offline) return;
                      event.preventDefault();
                      setStatusLine(t("charting.refusal.OFFLINE"));
                    }}
                    onConfirm={askConfirm}
                    onDiscard={askDiscard}
                  />
                ) : null}
                <div className={`flex flex-wrap items-center gap-2 text-sm ${pending ? "hidden" : ""}`} data-file-line>
                  {row.fulltext.attachment ? (
                    <>
                      <span dir="ltr" className="font-mono text-ink [overflow-wrap:anywhere]" data-file-name>
                        {row.fulltext.attachment.name}
                      </span>
                      <span dir="ltr" className="text-ink-muted">
                        {fileSize(row.fulltext.attachment.size)}
                      </span>
                      <a href={attachmentHref(origin, row.study_id)} target="_blank" rel="noopener" className={`inline-flex min-h-11 items-center gap-1 text-brand ${FOCUS_RING}`} data-open-file>
                        <ArrowTopRightOnSquareIcon aria-hidden="true" className="size-4" />
                        {t("charting.study.file.open")}
                        <span className="sr-only">({t("charting.study.file.newTab")})</span>
                      </a>
                    </>
                  ) : row.fulltext.link ? (
                    <a href={row.fulltext.link} target="_blank" rel="noopener noreferrer" className={`inline-flex min-h-11 items-center gap-1 text-brand ${FOCUS_RING}`} data-open-link>
                      <LinkIcon aria-hidden="true" className="size-4" />
                      {t("charting.file.openLink")}
                      <span className="sr-only">({t("charting.study.file.newTab")})</span>
                    </a>
                  ) : (
                    <NoFullTextMark locale={locale} />
                  )}
                  {ftLocked ? null : (
                    <>
                      <Button variant="quiet" className="px-1 text-sm" disabled={busy} onClick={() => changesAllowed() && fileInput.current?.click()} data-attach>
                        <DocumentArrowUpIcon aria-hidden="true" className="size-4" />
                        {t("charting.study.file.attach")}
                      </Button>
                      <Button variant="quiet" className="px-1 text-sm" disabled={busy} aria-expanded={linkOpen} onClick={() => { setLinkOpen(!linkOpen); setLinkText(row.fulltext.link ?? ""); }} data-paste-link>
                        <LinkIcon aria-hidden="true" className="size-4" />
                        {t("charting.study.file.link")}
                      </Button>
                    </>
                  )}
                </div>
                {linkOpen ? (
                  <form
                    className="flex flex-wrap items-end gap-2"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void saveLink();
                    }}
                  >
                    <label className="flex flex-col gap-1 text-xs text-ink">
                      <span>{t("charting.file.linkLabel")}</span>
                      <input type="url" dir="ltr" value={linkText} autoFocus onChange={(event) => setLinkText(event.target.value)} className={`min-h-11 w-64 rounded-md border border-rule-strong bg-leaf px-2 text-sm text-ink ${FOCUS_RING}`} data-link-input />
                    </label>
                    <Button type="submit" className="text-sm" disabled={busy || !linkText.trim()}>
                      {t("charting.file.save")}
                    </Button>
                  </form>
                ) : null}
                <div className="space-y-2" data-decision-control>
                  <p className="text-sm font-medium text-ink">{t("charting.study.decision")}</p>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button disabled={ftLocked || busy} aria-pressed={row.ft_decision?.outcome === "INCLUDE"} onClick={() => askDecision("INCLUDE")} data-include>
                      <CheckCircleIcon aria-hidden="true" className="size-4" />
                      {t("charting.decision.include")} <kbd className="text-xs opacity-80">I</kbd>
                    </Button>
                    <Button disabled={ftLocked || busy} aria-pressed={row.ft_decision?.outcome === "EXCLUDE"} onClick={() => askDecision("EXCLUDE")} data-exclude>
                      <XCircleIcon aria-hidden="true" className="size-4" />
                      {t("charting.decision.exclude")} <kbd className="text-xs opacity-80">E</kbd>
                    </Button>
                    {row.ft_decision ? (
                      <RoleBadge role={row.ft_decision.outcome === "INCLUDE" ? "include" : "exclude"} icon={row.ft_decision.outcome === "INCLUDE" ? CheckCircleIcon : XCircleIcon} data="decision">
                        {row.ft_decision.outcome === "INCLUDE" ? t("charting.decision.include") : t("charting.decision.exclude")}
                      </RoleBadge>
                    ) : (
                      <RoleBadge role="unclear" icon={QuestionMarkCircleIcon} data="decision-none">
                        {t("charting.decision.toDecide")}
                      </RoleBadge>
                    )}
                  </div>
                  {excluded && excludedReason ? <p className="text-xs text-ink-muted"><bdi>{excludedReason}</bdi></p> : null}
                </div>
                {/* Part F: the last look-up of this record and what was tried (spec 03 "One-study view"). */}
                <LookupLines locale={locale} row={row} />
                {row.fulltext.last_lookup ? <TriedDisclosure locale={locale} origin={origin} row={row} open={triedOpen} onToggle={setTriedOpen} /> : null}
                <div aria-live="polite" data-confirm-line>
                  {mode && mode.kind === "fetchConfirm" ? (
                    <div className="flex flex-wrap items-center gap-2 rounded-md border border-dashed border-brand bg-brand-soft p-3" data-fetch-ask={mode.then ?? "confirm"}>
                      <p className="text-sm font-medium text-ink">
                        {mode.then ? t("charting.fetch.confirm.beforeDecide") : <Say locale={locale} k="charting.fetch.confirm.line" values={{ title: row.title ?? row.study_id }} bdi={["title"]} />}
                      </p>
                      <Button onClick={confirmMode} disabled={busy}>
                        {t("charting.reason.confirm")}
                      </Button>
                      <Button variant="quiet" onClick={() => setMode(null)}>
                        {t("charting.reason.cancel")}
                      </Button>
                    </div>
                  ) : mode ? (
                    <div className="space-y-2 rounded-md border border-dashed border-brand bg-brand-soft p-3">
                      <p className="text-sm font-medium text-ink">
                        {mode.kind === "notRetrieved" ? t("charting.notRetrieved.choose") : mode.kind === "discard" ? t("charting.fetch.discard.choose") : t("charting.decision.choose")}
                      </p>
                      <div
                        role="radiogroup"
                        aria-label={mode.kind === "notRetrieved" ? t("charting.status.notRetrieved") : mode.kind === "discard" ? t("charting.fetch.discard") : t("charting.decision.exclude")}
                        className="flex flex-wrap gap-2"
                      >
                        {(mode.kind === "notRetrieved"
                          ? notRetrievedReasons.map((r, i) => ({ key: r, words: t(REASON_KEY[r]), code: null as string | null, chosen: mode.reason === r, i }))
                          : mode.kind === "discard"
                            ? DISCARD_REASONS.map((r, i) => ({ key: r, words: t(DISCARD_KEY[r]), code: null as string | null, chosen: mode.reason === r, i }))
                            : reasons.map((o, i) => ({ key: o.code, words: o.code === "OTHER" ? t("charting.decision.other") : o.label, code: o.code === "OTHER" ? null : o.code, chosen: mode.code === o.code, i }))
                        ).map((chip) => (
                          <button
                            key={chip.key}
                            type="button"
                            role="radio"
                            aria-checked={chip.chosen}
                            onClick={() => pick(chip.i)}
                            className={`inline-flex min-h-11 items-center gap-2 rounded-md border px-3 text-sm ${chip.chosen ? "border-brand bg-leaf text-brand" : "border-rule-strong bg-leaf text-ink"} ${FOCUS_RING}`}
                            data-chip={chip.key}
                          >
                            <kbd className="font-mono text-xs" dir="ltr">
                              {chip.i + 1}
                            </kbd>
                            {chip.code ? <DataCell>{chip.code}</DataCell> : null}
                            <bdi>{chip.words}</bdi>
                          </button>
                        ))}
                      </div>
                      {(mode.kind === "exclude" ? mode.code === "OTHER" : mode.reason === "other") ? (
                        <label className="flex flex-col gap-1 text-sm text-ink">
                          <span>{t(mode.kind === "notRetrieved" ? "charting.notRetrieved.words" : mode.kind === "discard" ? "charting.fetch.discard.words" : "charting.decision.words")}</span>
                          <input ref={wordsInput} data-mode-words="" value={mode.words} maxLength={500} onChange={(event) => setMode({ ...mode, words: event.target.value })} className={`min-h-11 rounded-md border border-rule-strong bg-leaf px-3 text-ink ${FOCUS_RING}`} />
                        </label>
                      ) : null}
                      <div className="flex flex-wrap gap-2">
                        <Button onClick={confirmMode} disabled={busy}>
                          {t("charting.reason.confirm")}
                        </Button>
                        <Button variant="quiet" onClick={() => setMode(null)}>
                          {t("charting.reason.cancel")}
                        </Button>
                      </div>
                    </div>
                  ) : null}
                  {plan ? (
                    <PlanBlock locale={locale} state={plan} one scopeAll={false} busy={busy} blockRef={planRef} onStart={() => void startLookup()} onCancel={closePlan} />
                  ) : null}
                </div>
                <p role="status" aria-live="polite" className="sr-only" data-fetch-announce>
                  {fetchRun.announce}
                </p>
                {runCard}
              </section>

              <section aria-labelledby="study-abstract" className="space-y-2" data-abstract>
                <h3 id="study-abstract" className="text-sm font-semibold text-ink">
                  {t("charting.study.abstract")}
                </h3>
                {row.abstract && row.abstract.trim() ? (
                  <p dir="auto" className="whitespace-pre-line text-[0.9375rem] leading-7 text-ink">
                    {row.abstract}
                  </p>
                ) : (
                  <p className="text-ink-muted" data-no-abstract>
                    {t("charting.study.noAbstract")}
                  </p>
                )}
              </section>
            </>
          )}
        </section>

        {/* The charting form for this study (spec 02, right column). */}
        <section aria-labelledby="form-region" tabIndex={0} className={`space-y-3 rounded-lg border border-rule bg-leaf p-4 ${pane} ${FOCUS_RING}`} data-region="form">
          <h2 id="form-region" className="text-sm font-semibold text-ink">
            {t("charting.study.regionForm")}
          </h2>
          {loading ? (
            <div aria-hidden="true" className="space-y-3" data-skeleton="fields">
              {[0, 1, 2].map((i) => (
                <span key={i} className="flex h-16 w-full animate-pulse rounded-md bg-rule" />
              ))}
            </div>
          ) : noColumns ? (
            <div className="space-y-3" data-state="no-columns">
              <p className="text-ink">{t("charting.study.noColumns")}</p>
              {archived ? null : (
                <a className={`${PRIMARY_LINK} ${FOCUS_RING}`} data-variant="primary" href={chartingHref(locale, origin, { view: "charting", form: true })} data-add-first-column>
                  {t("charting.study.addColumn")}
                </a>
              )}
            </div>
          ) : (
            <>
              {row.no_full_text ? (
                <div className="flex flex-wrap items-center gap-2 text-sm text-ink" data-from-abstract>
                  <NoFullTextMark locale={locale} />
                  <span>{t("charting.study.fromAbstract")}</span>
                </div>
              ) : null}
              {excluded ? (
                <p className="rounded-md bg-exclude-soft px-3 py-2 text-sm text-exclude" data-locked="excluded">
                  {t("charting.study.excluded", { reason: excludedReason })}
                </p>
              ) : notKept ? (
                <p className="rounded-md border border-dashed border-rule-strong px-3 py-2 text-sm text-ink" data-locked="not-kept">
                  {t("charting.study.noLongerKept")}
                </p>
              ) : null}
              {columns.map((column) => (
                <Field
                  key={column.column_id}
                  locale={locale}
                  column={column}
                  cell={cellOf(row, column.column_id)}
                  draft={drafts[column.column_id] ?? fieldDraft(column, cellOf(row, column.column_id))}
                  locked={formLocked || offline}
                  refusal={fieldRefusal && fieldRefusal.column === column.column_id ? fieldRefusal.code : null}
                  onDraft={(patch) => setDraft(column.column_id, patch)}
                  onCommit={() => void commit([column.column_id])}
                  onEnter={(event, allowShift) => enterSaves(event, column.column_id, allowShift)}
                  onSpecial={(state) => toggleSpecial(column.column_id, state)}
                />
              ))}
            </>
          )}
        </section>
      </div>

      <div className="flex flex-wrap items-center gap-3 border-t border-rule pt-2 lg:flex-none" data-study-status>
        <p role="status" aria-live="polite" className="min-h-5 text-sm text-ink" data-announce>
          {announce}
        </p>
        <p className="text-xs text-ink-muted" data-status-line>
          {statusLine && statusLine !== announce ? statusLine : ""}
        </p>
        <p className="hidden text-xs text-ink-muted lg:block">{t("charting.study.keys")}</p>
        <div className="ms-auto flex flex-wrap items-center gap-2">
          <Button variant="quiet" disabled={loading || position <= 0} onClick={() => void move(-1)} data-previous-study>
            {t("charting.study.previous")} <kbd className="text-xs opacity-80">K</kbd>
          </Button>
          {isLast || position < 0 ? (
            <a href={tableHref(studyId)} className={noColumns ? `inline-flex min-h-11 items-center rounded-md border border-rule-strong bg-leaf px-4 font-medium text-ink ${FOCUS_RING}` : `${PRIMARY_LINK} ${FOCUS_RING}`} data-variant={noColumns ? "secondary" : "primary"} data-next-study>
              {t("charting.study.back")}
            </a>
          ) : (
            <Button variant={noColumns ? "secondary" : "primary"} disabled={loading} onClick={() => void move(1)} data-next-study>
              {t("charting.study.next")} <kbd className="text-xs opacity-80">J</kbd>
            </Button>
          )}
        </div>
      </div>

      <input
        ref={fileInput}
        type="file"
        accept="application/pdf,.pdf"
        tabIndex={-1}
        className="sr-only"
        aria-label={t("charting.study.file.attach")}
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (file) void attach(file);
        }}
        data-file-input
      />
    </div>
  );
}

/**
 * One field of the form (spec 02 "Default"): the column's name with its
 * definition as description, the value input of its type, Not reported and Not
 * applicable as toggle buttons, a note and "where from", and the earlier value
 * when the column must be charted again.
 */
function Field({
  locale,
  column,
  cell,
  draft,
  locked,
  refusal,
  onDraft,
  onCommit,
  onEnter,
  onSpecial,
}: Readonly<{
  locale: Locale;
  column: FormColumn;
  cell: Cell;
  draft: FieldDraft;
  locked: boolean;
  refusal: string | null;
  onDraft: (patch: Partial<FieldDraft>) => void;
  onCommit: () => void;
  onEnter: (event: ReactKeyboardEvent, allowShift?: boolean) => void;
  onSpecial: (state: "not_reported" | "not_applicable") => void;
}>) {
  const t = (key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values);
  const cid = column.column_id;
  const labelId = `field-${cid}-label`;
  const defId = `field-${cid}-def`;
  const inputId = `field-${cid}-value`;
  const special = cell.state === "not_reported" || cell.state === "not_applicable";
  const valueOff = locked || special;
  const describedBy = column.definition ? defId : undefined;
  const input = `min-h-11 w-full rounded-md border border-rule-strong bg-leaf px-2 text-sm text-ink disabled:opacity-60 ${FOCUS_RING}`;
  // A "Chart again" field shows each earlier value: one per source column after a merge.
  const earlier = chartAgainHistory(cell);
  const leaveGroup = (event: FocusEvent<HTMLElement>) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) onCommit();
  };

  return (
    <div className="space-y-2 rounded-md border border-rule bg-paper p-3" data-field={cid} data-cell-state={cell.state ?? "empty"}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          {column.type === "text" || column.type === "number" ? (
            <label id={labelId} htmlFor={inputId} className="font-medium text-ink">
              <bdi>{column.name}</bdi>
            </label>
          ) : (
            <p id={labelId} className="font-medium text-ink">
              <bdi>{column.name}</bdi>
            </p>
          )}
          <p className="text-xs text-ink-muted">
            {t(TYPE_KEY[column.type])}
            {column.required ? ` · ${t("charting.col.required")}` : ""}
            {cell.pilot ? ` · ${t("charting.pilot.label")}` : ""}
          </p>
          {column.definition ? (
            <p id={defId} className="text-sm text-ink-muted">
              <bdi>{column.definition}</bdi>
            </p>
          ) : null}
        </div>
        {cell.chart_again ? <ChartAgainMark locale={locale} /> : null}
      </div>

      {column.type === "text" || column.type === "number" ? (
        <input
          id={inputId}
          type="text"
          inputMode={column.type === "number" ? "decimal" : undefined}
          dir="auto"
          value={typeof draft.value === "string" ? draft.value : ""}
          disabled={valueOff}
          aria-describedby={describedBy}
          aria-invalid={refusal ? true : undefined}
          onChange={(event) => onDraft({ value: event.target.value })}
          onBlur={onCommit}
          onKeyDown={(event) => onEnter(event)}
          className={input}
          data-value-input
        />
      ) : (
        <fieldset aria-labelledby={labelId} aria-describedby={describedBy} disabled={valueOff} onBlur={leaveGroup} onKeyDown={(event) => onEnter(event)} className="flex flex-wrap gap-x-4 gap-y-1">
          {column.options.map((option) => {
            const several = column.type === "several";
            const chosen = several ? Array.isArray(draft.value) && draft.value.includes(option) : draft.value === option;
            return (
              <label key={option} className="flex min-h-11 items-center gap-2 text-sm text-ink">
                <input
                  type={several ? "checkbox" : "radio"}
                  name={`field-${cid}`}
                  checked={chosen}
                  onChange={() => {
                    if (several) {
                      const list = Array.isArray(draft.value) ? draft.value : [];
                      onDraft({ value: list.includes(option) ? list.filter((o) => o !== option) : [...list, option] });
                    } else onDraft({ value: option });
                  }}
                  className="size-4 accent-[var(--color-brand)]"
                  data-value-input
                  data-option={option}
                />
                <bdi>{optionWords(locale, column, option)}</bdi>
              </label>
            );
          })}
        </fieldset>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {(["not_reported", "not_applicable"] as const).map((state) => {
          const pressed = cell.state === state;
          const IconOf = state === "not_reported" ? EyeSlashIcon : MinusCircleIcon;
          return (
            <button
              key={state}
              type="button"
              aria-pressed={pressed}
              disabled={locked}
              onClick={() => onSpecial(state)}
              className={`inline-flex min-h-11 items-center gap-1 rounded-md border px-3 text-sm disabled:opacity-60 ${pressed ? "border-ink bg-leaf-raised font-semibold text-ink" : "border-rule-strong bg-leaf text-ink-muted"} ${FOCUS_RING}`}
              data-special={state}
            >
              <IconOf aria-hidden="true" className="size-4" />
              {t(state === "not_reported" ? "charting.cell.notReported" : "charting.cell.notApplicable")}
              <kbd className="text-xs">{state === "not_reported" ? "Alt+N" : "Alt+A"}</kbd>
            </button>
          );
        })}
        <Hint locale={locale} label={t("charting.cell.notReported")} text={t("charting.study.tip.notReported")} textKey="charting.study.tip.notReported" />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm text-ink">
          <span>{t("charting.cell.note")}</span>
          <textarea
            rows={1}
            dir="auto"
            value={draft.note}
            maxLength={2000}
            disabled={locked}
            onChange={(event) => onDraft({ note: event.target.value })}
            onBlur={onCommit}
            onKeyDown={(event) => onEnter(event, true)}
            className={`${input} py-2`}
            data-note
          />
        </label>
        <div className="flex flex-col gap-1 text-sm text-ink">
          <span className="flex items-center gap-1">
            <label htmlFor={`field-${cid}-where`}>{t("charting.cell.whereFrom")}</label>
            <Hint locale={locale} label={t("charting.cell.whereFrom")} text={t("charting.study.tip.whereFrom")} textKey="charting.study.tip.whereFrom" />
          </span>
          <input
            id={`field-${cid}-where`}
            dir="auto"
            value={draft.whereFrom}
            maxLength={500}
            disabled={locked}
            onChange={(event) => onDraft({ whereFrom: event.target.value })}
            onBlur={onCommit}
            onKeyDown={(event) => onEnter(event)}
            className={input}
            data-where-from
          />
        </div>
      </div>

      {refusal ? (
        <p role="alert" className="rounded-md bg-blocked-soft px-3 py-2 text-sm text-blocked" data-field-refusal={refusal}>
          {refusal === "NUMBER" ? t("charting.cell.numberInvalid") : refusalWords(locale, refusal)}
          {refusal !== "NUMBER" ? (
            <span className="ms-2 font-mono text-xs" dir="ltr">
              {refusal}
            </span>
          ) : null}
        </p>
      ) : null}

      {earlier.length ? (
        <div className="space-y-0.5" data-history-list>
          {earlier.map((entry, i) => (
            <p key={`${entry.event_id}-${i}`}>
              <HistoryLine locale={locale} column={column} entry={entry} />
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}
