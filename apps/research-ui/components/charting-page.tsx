"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ComponentType, type ReactNode, type SVGProps } from "react";
import {
  ArrowDownTrayIcon,
  ArrowTopRightOnSquareIcon,
  ArrowUturnLeftIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentArrowUpIcon,
  InboxIcon,
  LinkIcon,
  NoSymbolIcon,
  QuestionMarkCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, PRIMARY_LINK } from "@/components/ui/base";
import { stepHref } from "@/components/screening-state-card";
import { notifyReviewChanged } from "@/components/review-bus";
import { isScreeningApiError } from "@/lib/screening-api";
import { localDate, localStamp } from "@/lib/local-time";
import {
  attachPdf,
  attachmentHref,
  chartingEvent,
  exportFulltextCsv,
  getCharting,
  postChartingEvents,
  postLink,
  type ChartingEvent,
  type ChartingRow,
  type ChartingTable,
  type EventKind,
  type FulltextStatus,
  type NotRetrievedReason,
} from "@/lib/charting-api";
import { cc, refusalWords, type ChartingCopyKey } from "@/lib/charting-copy";
import {
  REASON_KEY,
  SHOW_FILTERS,
  STATUS_KEY,
  STATUS_ROLE,
  UNREACHABLE_CODES,
  chartingKey,
  decisionValue,
  fileSize,
  isTextField,
  statusValue,
  visibleRows,
  type ShowFilter,
  type StatusRole,
} from "@/lib/charting-logic";
import { newEventId } from "@/lib/screening-v1";

/**
 * The charting screen, Full text view (spec 01, M12a Part A): one row per study
 * kept at title and abstract, its full-text status, its file or link, and the
 * full-text decision with one reason. Every change is one event, saved at once;
 * the engine judges it and answers the rows it touched.
 *
 * Part B adds the Charting view beside this one (the "Full text / Charting"
 * switch on 1 and 2), the form panel, the pilot and the one-study view on Enter;
 * none of them is drawn here, not even switched off. The keys L, C and D stay
 * free for Part F.
 */

type Refusal = { code: string; message: string };

type Mode =
  | { kind: "bulk"; status: FulltextStatus; ids: string[] }
  | { kind: "notRetrieved"; ids: string[]; reason: NotRetrievedReason | null; words: string }
  | { kind: "exclude"; id: string; code: string | null; words: string };

type UndoStep = { studyId: string; kind: EventKind; value: unknown; supersedes: string };
type UndoEntry = { steps: UndoStep[] };

type Load =
  | { status: "loading" }
  | { status: "ready" }
  | { status: "not_published"; refusal: Refusal }
  | { status: "refused"; refusal: Refusal }
  | { status: "offline" };

const SHOW_KEY: Record<ShowFilter, ChartingCopyKey> = {
  all: "charting.table.show.all",
  toGet: "charting.table.show.toGet",
  requested: "charting.table.show.requested",
  notRetrieved: "charting.table.show.notRetrieved",
  toDecide: "charting.table.show.toDecide",
  included: "charting.table.show.included",
  excluded: "charting.table.show.excluded",
};

const ROLE_STYLE: Record<StatusRole, string> = {
  include: "bg-include-soft text-include",
  unclear: "bg-unclear-soft text-unclear",
  blocked: "bg-blocked-soft text-blocked",
  exclude: "bg-exclude-soft text-exclude",
  neutral: "border border-rule bg-paper text-ink-muted",
};

type Icon = ComponentType<SVGProps<SVGSVGElement>>;

const STATUS_ICON: Record<FulltextStatus, Icon> = {
  to_get: InboxIcon,
  requested: ClockIcon,
  retrieved: CheckCircleIcon,
  not_retrieved: NoSymbolIcon,
};

const FOCUS_RING = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
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
    /* no object URLs here (a test page): the file was still written and journaled by the engine */
  }
}

function refusalOf(error: unknown): Refusal {
  if (!isScreeningApiError(error)) return { code: "ENGINE_UNREACHABLE", message: "" };
  return { code: error.code, message: error.serverMessage };
}

/** A status or decision as words and an icon on its role's tint: never colour alone. */
export function RoleBadge({ role, icon: IconOf, children, data }: Readonly<{ role: StatusRole; icon: Icon; children: ReactNode; data?: string }>) {
  return (
    <span data-role={role} data-badge={data} className={`inline-flex items-center gap-1 rounded-sm px-2 py-0.5 text-xs font-semibold leading-4 ${ROLE_STYLE[role]}`}>
      <IconOf aria-hidden="true" className="size-3.5 shrink-0" data-icon />
      <span>{children}</span>
    </span>
  );
}

export function ChartingPage({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <ChartingScreen locale={locale} />
    </div>
  );
}

function ChartingScreen({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);

  const [load, setLoad] = useState<Load>({ status: "loading" });
  const [table, setTable] = useState<ChartingTable | null>(null);
  const [show, setShow] = useState<ShowFilter>("all");
  const [showExcluded, setShowExcluded] = useState(false);
  const [focusId, setFocusId] = useState<string | null>(null);
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());
  const [mode, setMode] = useState<Mode | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [statusLine, setStatusLine] = useState("");
  const [announce, setAnnounce] = useState("");
  const [offline, setOffline] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [help, setHelp] = useState(false);
  const [linkFor, setLinkFor] = useState<string | null>(null);
  const [linkText, setLinkText] = useState("");
  const [attaching, setAttaching] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [undoCount, setUndoCount] = useState(0);
  const undoStack = useRef<UndoEntry[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const attachFor = useRef<string | null>(null);
  const wordsInput = useRef<HTMLInputElement>(null);
  const focusRow = useRef(false);

  const boot = useCallback(async () => {
    setLoad({ status: "loading" });
    try {
      const answer = await getCharting(origin);
      setTable(answer);
      setOffline(false);
      setLoad({ status: "ready" });
      setFocusId((current) => current ?? answer.rows[0]?.study_id ?? null);
    } catch (error) {
      const r = refusalOf(error);
      if (r.code === "SCREENING_NOT_PUBLISHED") setLoad({ status: "not_published", refusal: r });
      else if (UNREACHABLE_CODES.has(r.code)) setLoad({ status: "offline" });
      else setLoad({ status: "refused", refusal: r });
    }
  }, [origin]);

  useEffect(() => {
    void boot();
  }, [boot]);

  const rows = useMemo(() => (table ? visibleRows(table.rows, show, showExcluded) : []), [table, show, showExcluded]);
  const rowsRef = useRef(rows);
  rowsRef.current = rows;
  const byId = useMemo(() => new Map((table?.rows ?? []).map((r) => [r.study_id, r])), [table]);
  const readOnly = table?.read_only ?? false;
  const reasons = table?.reason_options ?? [];
  const notRetrievedReasons = table?.not_retrieved_reasons ?? ["no_access", "not_found", "no_reply", "other"];

  // Keep the focused row on one that is shown.
  useEffect(() => {
    if (rows.length === 0) return;
    if (!focusId || !rows.some((r) => r.study_id === focusId)) setFocusId(rows[0].study_id);
  }, [rows, focusId]);

  useEffect(() => {
    if (!focusRow.current || !focusId) return;
    focusRow.current = false;
    const element = document.querySelector<HTMLElement>(`[data-study-row="${focusId}"]`);
    element?.focus();
    element?.scrollIntoView?.({ block: "nearest" });
  }, [focusId, table]);

  function moveFocus(id: string | null) {
    focusRow.current = true;
    setFocusId(id);
  }

  function merge(changed: ChartingRow[], counts: ChartingTable["counts"]) {
    setTable((current) => {
      if (!current) return current;
      const fresh = new Map(changed.map((r) => [r.study_id, r]));
      return { ...current, counts, rows: current.rows.map((r) => fresh.get(r.study_id) ?? r) };
    });
  }

  function changesAllowed(): boolean {
    if (offline) {
      setStatusLine(t("charting.refusal.OFFLINE"));
      return false;
    }
    if (readOnly) {
      setStatusLine(t("charting.archived"));
      return false;
    }
    return !busy && table !== null;
  }

  function wentOffline(error: unknown): boolean {
    const r = refusalOf(error);
    if (UNREACHABLE_CODES.has(r.code)) {
      setOffline(true);
      return true;
    }
    setRefusal(r);
    return false;
  }

  function saved(count: number) {
    setLastSaved(new Date().toISOString());
    setAnnounce(count > 1 ? t("charting.announce.bulkSaved", { n: n(count) }) : t("charting.announce.saved"));
    notifyReviewChanged();
  }

  function pushUndo(entry: UndoEntry) {
    if (entry.steps.length === 0) return;
    undoStack.current.push(entry);
    setUndoCount(undoStack.current.length);
  }

  /** Send events; the accepted ones become one undo step. */
  async function send(events: ChartingEvent[], previous: (event: ChartingEvent) => unknown, firstId: string | null) {
    setBusy(true);
    setRefusal(null);
    setStatusLine("");
    try {
      const answer = await postChartingEvents(origin, events);
      merge(answer.rows, answer.counts);
      const accepted = events.filter((e) => answer.results.some((r) => r.event_id === e.event_id && r.result !== "refused"));
      const refused = answer.results.find((r) => r.result === "refused");
      if (refused) setRefusal({ code: refused.refusal?.code ?? "REFUSED", message: refused.refusal?.message ?? "" });
      if (accepted.length > 0) {
        pushUndo({ steps: accepted.map((e) => ({ studyId: e.study_id, kind: e.kind, value: previous(e), supersedes: e.event_id })) });
        saved(accepted.length);
      }
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
      if (firstId) moveFocus(firstId);
    }
  }

  function setStatus(ids: string[], value: Record<string, string>) {
    if (!table || !changesAllowed()) return;
    const targets = ids.map((id) => byId.get(id)).filter((r): r is ChartingRow => r !== undefined && r.kept);
    if (targets.length === 0) return;
    const before = new Map(targets.map((r) => [r.study_id, statusValue(r)]));
    const events = targets.map((r) =>
      chartingEvent({ studyId: r.study_id, screenerId: table.screener_id, kind: "fulltext_status", value, supersedes: r.heads.fulltext_status }),
    );
    void send(events, (e) => before.get(e.study_id), targets[0].study_id);
  }

  function decide(id: string, value: Record<string, string>) {
    const row = byId.get(id);
    if (!table || !row || !row.kept || !changesAllowed()) return;
    const before = decisionValue(row.ft_decision);
    const event = chartingEvent({ studyId: id, screenerId: table.screener_id, kind: "fulltext_decision", value, supersedes: row.heads.fulltext_decision });
    void send([event], () => before, id);
  }

  async function undo() {
    if (!table) return;
    const entry = undoStack.current[undoStack.current.length - 1];
    if (!entry) {
      setStatusLine(t("charting.announce.nothingToUndo"));
      return;
    }
    if (!changesAllowed()) return;
    const events = entry.steps.map((s) =>
      chartingEvent({ studyId: s.studyId, screenerId: table.screener_id, kind: s.kind, value: s.value, supersedes: s.supersedes }),
    );
    setBusy(true);
    setRefusal(null);
    setStatusLine("");
    try {
      const answer = await postChartingEvents(origin, events);
      merge(answer.rows, answer.counts);
      const refused = answer.results.find((r) => r.result === "refused");
      if (refused) setRefusal({ code: refused.refusal?.code ?? "REFUSED", message: refused.refusal?.message ?? "" });
      else {
        undoStack.current.pop();
        setUndoCount(undoStack.current.length);
        setLastSaved(new Date().toISOString());
        setAnnounce(t("charting.announce.undone"));
        notifyReviewChanged();
      }
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
      moveFocus(entry.steps[0].studyId);
    }
  }

  function startAttach(id: string) {
    const row = byId.get(id);
    if (!row || !row.kept || !changesAllowed()) return;
    attachFor.current = id;
    fileInput.current?.click();
  }

  async function attach(file: File) {
    const id = attachFor.current;
    attachFor.current = null;
    const row = id ? byId.get(id) : undefined;
    if (!table || !id || !row || !changesAllowed()) return;
    const previousAttachment = row.fulltext.attachment;
    const previousStatus = statusValue(row);
    setBusy(true);
    setAttaching(id);
    setRefusal(null);
    setStatusLine("");
    try {
      const answer = await attachPdf(origin, id, file, { eventId: newEventId(), statusEventId: newEventId() });
      if (answer.row) merge([answer.row], answer.counts);
      if (answer.result === "accepted") {
        const attachmentEvent = answer.events.find((event) => event.kind === "attachment")?.event_id;
        const statusEvent = answer.events.find((event) => event.kind === "fulltext_status")?.event_id;
        const steps: UndoStep[] = [];
        if (attachmentEvent) steps.push({ studyId: id, kind: "attachment", value: previousAttachment, supersedes: attachmentEvent });
        if (statusEvent) steps.push({ studyId: id, kind: "fulltext_status", value: previousStatus, supersedes: statusEvent });
        pushUndo({ steps });
      }
      saved(1);
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
      setAttaching(null);
      moveFocus(id);
    }
  }

  async function saveLink(id: string) {
    const row = byId.get(id);
    const url = linkText.trim();
    if (!row || !url || !changesAllowed()) return;
    const previous = row.fulltext.link ? { url: row.fulltext.link } : null;
    const eventId = newEventId();
    setBusy(true);
    setRefusal(null);
    try {
      const answer = await postLink(origin, id, url, eventId);
      if (answer.row) merge([answer.row], answer.counts);
      if (answer.result === "accepted") pushUndo({ steps: [{ studyId: id, kind: "link", value: previous, supersedes: answer.events.find((event) => event.kind === "link")?.event_id ?? eventId }] });
      setLinkFor(null);
      setLinkText("");
      saved(1);
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
    }
  }

  function open(id: string) {
    const row = byId.get(id);
    if (!row) return;
    if (row.fulltext.attachment) window.open(attachmentHref(origin, id), "_blank", "noopener");
    else if (row.fulltext.link) window.open(row.fulltext.link, "_blank", "noopener,noreferrer");
  }

  async function runExport() {
    if (offline) {
      setStatusLine(t("charting.refusal.OFFLINE"));
      return;
    }
    if (!table || exporting) return;
    setExporting(true);
    setRefusal(null);
    setAnnounce(t("charting.export.preparing"));
    try {
      const { blob, filename } = await exportFulltextCsv(origin);
      saveFile(blob, filename);
      const message = t("charting.announce.exported", { when: localStamp(new Date().toISOString()), n: n(table.counts.kept) });
      setAnnounce(message);
      setStatusLine(message);
    } catch (error) {
      wentOffline(error);
      setAnnounce("");
    } finally {
      setExporting(false);
    }
  }

  /** The rows a status key acts on: the selection when there is one, else the focused row. */
  function statusTargets(here: string | null): string[] {
    if (selected.size > 0) return rows.filter((r) => selected.has(r.study_id) && r.kept).map((r) => r.study_id);
    const row = here ? byId.get(here) : undefined;
    return row && row.kept ? [row.study_id] : [];
  }

  function askStatus(status: FulltextStatus, here: string | null) {
    if (!changesAllowed()) return;
    const ids = statusTargets(here);
    if (ids.length === 0) return;
    if (status === "not_retrieved") {
      setMode({ kind: "notRetrieved", ids, reason: null, words: "" });
      return;
    }
    if (ids.length > 1) setMode({ kind: "bulk", status, ids });
    else setStatus(ids, { status });
  }

  function askDecision(outcome: "INCLUDE" | "EXCLUDE", id = focusId) {
    if (selected.size > 1) {
      setStatusLine(t("charting.decision.oneAtATime"));
      return;
    }
    if (!id || !changesAllowed()) return;
    const row = byId.get(id);
    if (!row || !row.kept) return;
    if (outcome === "INCLUDE") decide(id, { outcome: "INCLUDE" });
    else setMode({ kind: "exclude", id, code: null, words: "" });
  }

  function confirmMode() {
    if (!mode) return;
    if (mode.kind === "bulk") {
      setMode(null);
      setStatus(mode.ids, { status: mode.status });
      return;
    }
    if (mode.kind === "notRetrieved") {
      if (!mode.reason) {
        setStatusLine(t("charting.refusal.FULLTEXT_REASON_REQUIRED"));
        return;
      }
      const words = mode.words.trim();
      if (mode.reason === "other" && !words) {
        setStatusLine(t("charting.refusal.FULLTEXT_REASON_REQUIRED"));
        wordsInput.current?.focus();
        return;
      }
      setMode(null);
      setStatus(mode.ids, mode.reason === "other" ? { status: "not_retrieved", reason: "other", reason_text: words } : { status: "not_retrieved", reason: mode.reason });
      return;
    }
    if (!mode.code) {
      setStatusLine(t("charting.refusal.FULLTEXT_REASON_REQUIRED"));
      return;
    }
    const words = mode.words.trim();
    if (mode.code === "OTHER" && !words) {
      setStatusLine(t("charting.refusal.FULLTEXT_REASON_REQUIRED"));
      wordsInput.current?.focus();
      return;
    }
    setMode(null);
    decide(mode.id, mode.code === "OTHER" ? { outcome: "EXCLUDE", reason_code: "OTHER", reason_text: words } : { outcome: "EXCLUDE", reason_code: mode.code });
  }

  function pick(index: number) {
    if (!mode || mode.kind === "bulk") return;
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

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function step(delta: number, extend: boolean, here: string | null) {
    const list = rowsRef.current;
    if (list.length === 0) return;
    const at = Math.max(0, list.findIndex((r) => r.study_id === here));
    const next = list[Math.min(list.length - 1, Math.max(0, at + delta))];
    if (extend) {
      setSelected((current) => new Set([...current, list[at].study_id, next.study_id]));
    }
    moveFocus(next.study_id);
  }

  function selectAll() {
    const ids = rows.filter((r) => r.kept).map((r) => r.study_id);
    setSelected((current) => (ids.length > 0 && ids.every((id) => current.has(id)) ? new Set() : new Set(ids)));
  }

  function changeShow(next: ShowFilter) {
    setShow(next);
    setSelected(new Set());
    setMode(null);
  }

  // The keyboard map (spec 01 "Keyboard"), off in text fields. One listener for
  // the screen's life calls the newest handler, swapped before paint.
  const keyHandler = useRef<(event: KeyboardEvent) => void>(() => undefined);
  useEffect(() => {
    const listener = (event: KeyboardEvent) => keyHandler.current(event);
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);
  useLayoutEffect(() => {
    keyHandler.current = function onKey(event: KeyboardEvent) {
      if (load.status !== "ready" || !table) return;
      // A phone shows the read-only list; keys act only on the desktop screen.
      if (typeof window.matchMedia === "function" && !window.matchMedia("(min-width: 640px)").matches) return;
      const target = event.target as HTMLElement | null;
      const inWords = target instanceof HTMLElement && target.dataset.modeWords !== undefined;
      // The row that has the keyboard's focus is the focused row, whatever the last click said.
      const rowTarget = target instanceof HTMLElement ? target.closest<HTMLElement>("[data-study-row]")?.dataset.studyRow ?? null : null;
      const here = rowTarget ?? focusId;
      if (rowTarget && rowTarget !== focusId) setFocusId(rowTarget);
      if (event.key === "Escape") {
        if (help) setHelp(false);
        else if (mode) setMode(null);
        else if (linkFor) setLinkFor(null);
        else if (selected.size > 0) setSelected(new Set());
        if (mode && here) moveFocus(here);
        return;
      }
      if (mode) {
        if (event.key === "Enter" && (inWords || !isTextField(target)) && !(target instanceof HTMLButtonElement)) {
          event.preventDefault();
          confirmMode();
          return;
        }
        if (/^[1-9]$/.test(event.key) && !isTextField(target) && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          pick(Number(event.key) - 1);
        }
        return;
      }
      const key = chartingKey(event, target);
      if (key === null) return;
      event.preventDefault();
      if (key === "help") setHelp((h) => !h);
      else if (key === "down" || key === "up") step(key === "down" ? 1 : -1, false, here);
      else if (key === "extendDown" || key === "extendUp") step(key === "extendDown" ? 1 : -1, true, here);
      else if (key === "toggle" && here) toggle(here);
      else if (key === "selectAll") selectAll();
      else if (key === "toGet") askStatus("to_get", here);
      else if (key === "requested") askStatus("requested", here);
      else if (key === "retrieved") askStatus("retrieved", here);
      else if (key === "notRetrieved") askStatus("not_retrieved", here);
      else if (key === "include") askDecision("INCLUDE", here);
      else if (key === "exclude") askDecision("EXCLUDE", here);
      else if (key === "attach" && here) startAttach(here);
      else if (key === "open" && here) open(here);
      else if (key === "undo") void undo();
      else if (key === "export") void runExport();
    };
  });

  const summaryClass = `min-h-11 cursor-pointer py-3 leading-5 rounded-sm ${FOCUS_RING}`;

  const heading = (
    <h1 className="font-display text-[1.75rem] leading-[2.25rem] text-ink">
      {t("charting.table.title")}
    </h1>
  );

  if (load.status === "not_published") {
    return (
      <section aria-labelledby="charting-empty" className="space-y-4" data-state="not-published">
        <h1 id="charting-empty" className="font-display text-[1.75rem] leading-[2.25rem] text-ink">
          {t("charting.table.title")}
        </h1>
        <p className="max-w-2xl text-ink">{t("charting.empty.notPublished")}</p>
        <a className={PRIMARY_LINK} data-variant="primary" href={stepHref(locale, "publish", origin)}>
          {t("charting.empty.goPublish")}
        </a>
        <details className="text-xs text-ink-muted">
          <summary className={summaryClass}>{t("charting.details")}</summary>
          <span className="font-mono" dir="ltr">
            {load.refusal.code}
          </span>
        </details>
      </section>
    );
  }

  if (load.status === "refused" || load.status === "offline") {
    const code = load.status === "refused" ? load.refusal.code : "ENGINE_UNREACHABLE";
    return (
      <section className="space-y-4" data-state={load.status}>
        {heading}
        <div role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-refusal={code}>
          <p>{load.status === "offline" ? t("charting.offlineNoChange") : refusalWords(locale, code)}</p>
          <details className="text-xs">
            <summary className={summaryClass}>{t("charting.details")}</summary>
            <span className="font-mono" dir="ltr">
              {code}
            </span>
          </details>
        </div>
        <Button onClick={() => void boot()}>{t("charting.retry")}</Button>
      </section>
    );
  }

  const loading = load.status === "loading" || table === null;
  const counts = table?.counts;
  const nothingKept = !loading && table !== null && table.rows.length === 0;

  const showSelect = (id: string) => (
    <label className="flex items-center gap-2 text-sm text-ink" htmlFor={id}>
      <span>{t("charting.table.show.label")}</span>
      <select
        id={id}
        value={show}
        disabled={loading}
        onChange={(event) => changeShow(event.target.value as ShowFilter)}
        className={`min-h-11 rounded-md border border-rule-strong bg-leaf px-2 text-sm text-ink ${FOCUS_RING}`}
        data-show
      >
        {SHOW_FILTERS.map((filter) => (
          <option key={filter} value={filter}>
            {t(SHOW_KEY[filter])}
          </option>
        ))}
      </select>
    </label>
  );

  const statusWords = (row: ChartingRow) => {
    const ft = row.fulltext;
    if (ft.status === "requested" && ft.requested_on) return t("charting.status.requestedOn", { date: ft.requested_on });
    return t(STATUS_KEY[ft.status]);
  };

  const statusBadge = (row: ChartingRow) => (
    <RoleBadge role={STATUS_ROLE[row.fulltext.status]} icon={STATUS_ICON[row.fulltext.status]} data={`status-${row.fulltext.status}`}>
      {statusWords(row)}
    </RoleBadge>
  );

  const reasonLine = (row: ChartingRow) => {
    const ft = row.fulltext;
    if (ft.status !== "not_retrieved" || !ft.reason) return null;
    return (
      <span className="mt-1 text-xs text-ink-muted" data-reason>
        {ft.reason === "other" && ft.reason_text ? <bdi>{ft.reason_text}</bdi> : t(REASON_KEY[ft.reason])}
      </span>
    );
  };

  const decisionBadge = (row: ChartingRow) => {
    const d = row.ft_decision;
    if (!d) {
      return (
        <RoleBadge role="unclear" icon={QuestionMarkCircleIcon} data="decision-none">
          {t("charting.decision.toDecide")}
        </RoleBadge>
      );
    }
    if (d.outcome === "INCLUDE") {
      return (
        <RoleBadge role="include" icon={CheckCircleIcon} data="decision-include">
          {t("charting.decision.include")}
        </RoleBadge>
      );
    }
    const option = reasons.find((o) => o.code === d.reason_code);
    return (
      <span className="flex flex-col items-start gap-1">
        <RoleBadge role="exclude" icon={XCircleIcon} data="decision-exclude">
          {t("charting.decision.exclude")}
        </RoleBadge>
        <span className="text-xs text-ink-muted" data-decision-reason>
          {d.reason_code === "OTHER" ? (
            <bdi>{d.reason_text}</bdi>
          ) : (
            <>
              <DataCell>{d.reason_code}</DataCell> <bdi>{option?.label ?? ""}</bdi>
            </>
          )}
        </span>
      </span>
    );
  };

  const roundWords = (row: ChartingRow) =>
    row.arm === "databases" ? t("charting.round.databases") : row.arm === "citation_searching" ? t("charting.round.chasing") : row.round_label;

  const studyCell = (row: ChartingRow) => (
    <span className="flex min-w-0 flex-col gap-1">
      <bdi className="font-medium text-ink">{row.title ?? row.study_id}</bdi>
      <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-ink-muted">
        {row.year ? <span dir="ltr">{String(row.year)}</span> : null}
        {row.doi ? (
          <a href={`https://doi.org/${row.doi}`} target="_blank" rel="noopener noreferrer" className={`text-anchor ${FOCUS_RING}`} dir="ltr" data-doi>
            {row.doi}
          </a>
        ) : null}
        {row.new_since ? (
          <span className="rounded-sm bg-brand-soft px-1.5 font-medium text-brand" data-new>
            {t("charting.new", { date: localDate(row.new_since) })}
          </span>
        ) : null}
        {!row.kept ? (
          <span className="rounded-sm border border-dashed border-rule-strong px-1.5 font-medium text-ink" data-no-longer-kept>
            {t("charting.noLongerKept")}
          </span>
        ) : null}
      </span>
    </span>
  );

  const confirmLine = (() => {
    if (!mode) return null;
    if (mode.kind === "bulk") {
      return (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <p className="font-medium text-ink">{t("charting.bulk.confirm", { n: n(mode.ids.length), status: t(STATUS_KEY[mode.status]) })}</p>
          <Button onClick={confirmMode} disabled={busy}>
            {t("charting.reason.confirm")}
          </Button>
          <Button variant="quiet" onClick={() => setMode(null)}>
            {t("charting.reason.cancel")}
          </Button>
        </div>
      );
    }
    const chips =
      mode.kind === "notRetrieved"
        ? notRetrievedReasons.map((reason, i) => ({ key: reason, words: t(REASON_KEY[reason]), chosen: mode.reason === reason, code: null as string | null, i }))
        : reasons.map((o, i) => ({ key: o.code, words: o.code === "OTHER" ? t("charting.decision.other") : o.label, chosen: mode.code === o.code, code: o.code === "OTHER" ? null : o.code, i }));
    const needsWords = mode.kind === "notRetrieved" ? mode.reason === "other" : mode.code === "OTHER";
    const target = mode.kind === "exclude" ? byId.get(mode.id) : undefined;
    return (
      <div className="space-y-2">
        <p className="font-medium text-ink">
          {mode.kind === "notRetrieved"
            ? mode.ids.length > 1
              ? `${t("charting.bulk.confirm", { n: n(mode.ids.length), status: t("charting.status.notRetrieved") })} ${t("charting.notRetrieved.choose")}`
              : t("charting.notRetrieved.choose")
            : (
              <>
                {t("charting.decision.exclude")}: <bdi>{target?.title ?? mode.id}</bdi> · {t("charting.decision.choose")}
              </>
            )}
        </p>
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={mode.kind === "notRetrieved" ? t("charting.status.notRetrieved") : t("charting.decision.exclude")}>
          {chips.map((chip) => (
            <button
              key={chip.key}
              type="button"
              role="radio"
              aria-checked={chip.chosen}
              onClick={() => pick(chip.i)}
              className={`inline-flex min-h-11 items-center gap-2 rounded-md border px-3 text-sm ${chip.chosen ? "border-brand bg-brand-soft text-brand" : "border-rule-strong bg-leaf text-ink"} ${FOCUS_RING}`}
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
        {needsWords ? (
          <label className="flex flex-col gap-1 text-sm text-ink">
            <span>{t(mode.kind === "notRetrieved" ? "charting.notRetrieved.words" : "charting.decision.words")}</span>
            <input
              ref={wordsInput}
              data-mode-words=""
              value={mode.words}
              maxLength={500}
              onChange={(event) => setMode({ ...mode, words: event.target.value })}
              className={`min-h-11 max-w-xl rounded-md border border-rule-strong bg-leaf px-3 text-ink ${FOCUS_RING}`}
            />
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
    );
  })();

  const fileCell = (row: ChartingRow) => {
    const ft = row.fulltext;
    const disabled = readOnly || !row.kept || busy;
    return (
      <span className="flex flex-col items-start gap-1">
        {ft.attachment ? (
          <span className="flex flex-wrap items-center gap-2 text-xs">
            <span dir="ltr" className="font-mono text-ink [overflow-wrap:anywhere]" data-file-name>
              {ft.attachment.name}
            </span>
            <span dir="ltr" className="text-ink-muted">
              {fileSize(ft.attachment.size)}
            </span>
            <a href={attachmentHref(origin, row.study_id)} target="_blank" rel="noopener" className={`inline-flex min-h-11 items-center gap-1 text-brand ${FOCUS_RING}`} data-open-file>
              <ArrowTopRightOnSquareIcon aria-hidden="true" className="size-4" />
              {t("charting.file.open")}
            </a>
          </span>
        ) : ft.link ? (
          <a href={ft.link} target="_blank" rel="noopener noreferrer" className={`inline-flex min-h-11 items-center gap-1 text-xs text-brand ${FOCUS_RING}`} data-open-link>
            <LinkIcon aria-hidden="true" className="size-4" />
            {t("charting.file.openLink")}
          </a>
        ) : (
          <span className="text-xs text-ink-muted">{attaching === row.study_id ? t("charting.file.attaching") : t("charting.file.none")}</span>
        )}
        {row.kept && !readOnly ? (
          <span className="flex flex-wrap gap-1">
            <Button variant="quiet" className="px-1 text-xs" disabled={disabled} onClick={() => startAttach(row.study_id)} data-attach>
              <DocumentArrowUpIcon aria-hidden="true" className="size-4" />
              {t("charting.file.attach")}
            </Button>
            <Button
              variant="quiet"
              className="px-1 text-xs"
              disabled={disabled}
              aria-expanded={linkFor === row.study_id}
              onClick={() => {
                setLinkFor(linkFor === row.study_id ? null : row.study_id);
                setLinkText(ft.link ?? "");
              }}
              data-paste-link
            >
              <LinkIcon aria-hidden="true" className="size-4" />
              {t("charting.file.pasteLink")}
            </Button>
          </span>
        ) : null}
        {linkFor === row.study_id ? (
          <form
            className="flex flex-wrap items-end gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void saveLink(row.study_id);
            }}
          >
            <label className="flex flex-col gap-1 text-xs text-ink">
              <span>{t("charting.file.linkLabel")}</span>
              <input
                type="url"
                dir="ltr"
                value={linkText}
                autoFocus
                onChange={(event) => setLinkText(event.target.value)}
                className={`min-h-11 w-64 rounded-md border border-rule-strong bg-leaf px-2 text-sm text-ink ${FOCUS_RING}`}
                data-link-input
              />
            </label>
            <Button type="submit" className="text-sm" disabled={busy || !linkText.trim()}>
              {t("charting.file.save")}
            </Button>
          </form>
        ) : null}
      </span>
    );
  };

  const decisionCell = (row: ChartingRow) => (
    <span className="flex flex-col items-start gap-1">
      {decisionBadge(row)}
      {row.kept && !readOnly ? (
        <span className="flex flex-wrap gap-1">
          <Button variant="quiet" className="px-1 text-xs" disabled={busy} onClick={() => askDecision("INCLUDE", row.study_id)} aria-label={t("charting.decision.includeFor", { title: row.title ?? row.study_id })} data-include>
            {t("charting.decision.include")}
          </Button>
          <Button
            variant="quiet"
            className="px-1 text-xs"
            disabled={busy}
            onClick={() => {
              setFocusId(row.study_id);
              askDecision("EXCLUDE", row.study_id);
            }}
            aria-label={t("charting.decision.excludeFor", { title: row.title ?? row.study_id })}
            data-exclude
          >
            {t("charting.decision.exclude")}
          </Button>
        </span>
      ) : null}
    </span>
  );

  const cell = "px-3 py-2 align-top";
  const stickyStart = "sticky start-0 z-10 bg-leaf";
  const stickyStudy = "sticky start-12 z-10 bg-leaf";

  return (
    <div className="space-y-4" data-charting>
      <header className="space-y-1">
        {heading}
        {loading || !counts ? (
          <p aria-hidden="true" className="h-5 w-96 max-w-full animate-pulse rounded-sm bg-rule" data-skeleton="counts" />
        ) : (
          <p className="text-sm text-ink-muted" data-counts>
            {t("charting.table.counts", {
              kept: n(counts.kept),
              retrieved: n(counts.retrieved),
              notRetrieved: n(counts.not_retrieved),
              toGet: n(counts.to_get),
              included: n(counts.included),
              excluded: n(counts.excluded),
            })}
          </p>
        )}
      </header>

      <p role="status" aria-live="polite" className="sr-only" data-announce>
        {announce}
      </p>

      {/* Phone: a read-only list (spec 01 "Mobile layout"); the one-study view arrives with Part B. */}
      <section className="space-y-3 sm:hidden" data-phone>
        <p className="rounded-md border border-rule bg-leaf px-4 py-3 text-ink">{t("charting.mobile")}</p>
        {showSelect("charting-show-phone")}
        {loading ? null : (
          <ul className="space-y-2" data-phone-list>
            {rows.map((row) => (
              <li key={row.study_id} className={`min-h-11 rounded-md border border-rule bg-leaf px-3 py-2 ${row.kept ? "" : "opacity-70"}`} data-phone-card>
                {studyCell(row)}
                <span className="mt-2 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
                  <span>{roundWords(row)}</span>
                  {statusBadge(row)}
                  {decisionBadge(row)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="hidden space-y-4 sm:block" data-desktop>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2" data-toolbar>
          {/* Part B puts the Full text / Charting switch here (keys 1 and 2). */}
          {showSelect("charting-show")}
          <label className="flex min-h-11 items-center gap-2 text-sm text-ink">
            <input type="checkbox" checked={showExcluded} disabled={loading} onChange={(event) => setShowExcluded(event.target.checked)} className="size-4 accent-[var(--color-brand)]" data-show-excluded />
            {t("charting.table.showExcluded")}
          </label>
          <div className="ms-auto flex flex-wrap items-center gap-2">
            {undoCount > 0 ? (
              <Button variant="quiet" disabled={busy || readOnly} onClick={() => void undo()} data-undo>
                <ArrowUturnLeftIcon aria-hidden="true" className="size-4" />
                {t("charting.undo")} <kbd className="text-xs opacity-80">Z</kbd>
              </Button>
            ) : null}
            <Button variant="quiet" disabled={loading} onClick={() => setHelp((h) => !h)} aria-expanded={help} data-help-button>
              {t("charting.help.button")} <kbd className="text-xs opacity-80">?</kbd>
            </Button>
            <Button disabled={loading || exporting || offline} onClick={() => void runExport()} data-export>
              <ArrowDownTrayIcon aria-hidden="true" className="size-4" />
              {t("charting.export.menu")}
              <span className="text-xs text-ink-muted">{t("charting.export.csv")}</span>
            </Button>
          </div>
        </div>

        {help ? (
          <section aria-labelledby="charting-help-title" className="rounded-md border border-rule bg-leaf p-4 text-sm" data-help>
            <h2 id="charting-help-title" className="font-semibold text-ink">
              {t("charting.help.title")}
            </h2>
            <p className="mt-2 text-ink-muted">{t("charting.help.body")}</p>
            <Button variant="quiet" className="mt-2" onClick={() => setHelp(false)}>
              {t("charting.help.close")}
            </Button>
          </section>
        ) : null}

        {table?.changes ? (
          <p className="rounded-md bg-brand-soft px-4 py-3 text-ink" data-banner="changes">
            {t("charting.changes", { date: localDate(table.changes.published_at), added: n(table.changes.added), gone: n(table.changes.no_longer_kept) })}
          </p>
        ) : null}
        {table?.stale ? (
          <div className="rounded-md bg-unclear-soft px-4 py-3 text-unclear" data-banner="stale">
            <p>
              {t("charting.stale")}{" "}
              <a className={`inline-flex min-h-11 items-center text-brand ${FOCUS_RING}`} href={stepHref(locale, "publish", origin)}>
                {t("charting.empty.goPublish")}
              </a>
            </p>
            <details className="text-xs">
              <summary className={summaryClass}>{t("charting.details")}</summary>
              <span className="font-mono" dir="ltr">
                GENERATION_STALE
              </span>
            </details>
          </div>
        ) : null}
        {table?.chasing_pending ? (
          <p className="rounded-md border border-rule bg-leaf px-4 py-3 text-ink" data-banner="chasing">
            {t("charting.chasingPending")}
          </p>
        ) : null}
        {readOnly ? (
          <div className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-banner="archived">
            <p>{t("charting.archived")}</p>
            <details className="text-xs">
              <summary className={summaryClass}>{t("charting.details")}</summary>
              <span className="font-mono" dir="ltr">
                {table?.read_only_code ?? "CHARTING_PROTOCOL_REPLACED"}
              </span>
            </details>
          </div>
        ) : null}
        {offline ? (
          <div role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-banner="offline">
            <p>{lastSaved ? t("charting.offline", { time: localStamp(lastSaved).slice(11) }) : t("charting.offlineNoChange")}</p>
            <Button className="mt-2" onClick={() => void boot()}>
              {t("charting.retry")}
            </Button>
          </div>
        ) : null}
        {refusal ? (
          <div role="alert" className="rounded-md bg-blocked-soft px-4 py-3 text-blocked" data-refusal={refusal.code}>
            <p>{refusalWords(locale, refusal.code)}</p>
            <details className="text-xs">
              <summary className={summaryClass}>{t("charting.details")}</summary>
              <span className="font-mono" dir="ltr">
                {refusal.code}
              </span>
            </details>
          </div>
        ) : null}

        <div aria-live="polite" className="min-h-0" data-confirm-line>
          {confirmLine ? <div className="rounded-md border border-dashed border-brand bg-brand-soft px-4 py-3">{confirmLine}</div> : null}
        </div>

        {nothingKept ? (
          <section className="rounded-md border border-rule bg-leaf p-5" data-state="nothing-kept">
            <p className="text-ink">{t("charting.empty.nothingKept")}</p>
            <a className={`mt-2 inline-flex min-h-11 items-center text-brand ${FOCUS_RING}`} href={stepHref(locale, "triage", origin)}>
              {t("charting.empty.goTriage")}
            </a>
          </section>
        ) : (
          <div className="max-h-[70vh] overflow-auto rounded-md border border-rule" data-grid-scroll>
            <table
              role="grid"
              aria-label={t("charting.table.grid")}
              aria-rowcount={loading ? -1 : rows.length + 1}
              aria-multiselectable="true"
              aria-busy={loading || undefined}
              className="w-full border-collapse text-sm"
            >
              <thead className="sticky top-0 z-20 bg-paper">
                <tr aria-rowindex={1}>
                  <th scope="col" className={`${cell} ${stickyStart} w-12 bg-paper`}>
                    <input
                      type="checkbox"
                      disabled={loading || rows.length === 0}
                      checked={rows.length > 0 && rows.filter((r) => r.kept).every((r) => selected.has(r.study_id)) && rows.some((r) => r.kept)}
                      onChange={selectAll}
                      aria-label={t("charting.select.all")}
                      className="size-4 accent-[var(--color-brand)]"
                      data-select-all
                    />
                  </th>
                  <th scope="col" className={`${cell} ${stickyStudy} min-w-64 bg-paper text-start font-medium text-ink`}>{t("charting.col.study")}</th>
                  <th scope="col" className={`${cell} text-start font-medium text-ink`}>{t("charting.col.round")}</th>
                  <th scope="col" className={`${cell} text-start font-medium text-ink`}>{t("charting.col.fulltext")}</th>
                  <th scope="col" className={`${cell} text-start font-medium text-ink`}>{t("charting.col.file")}</th>
                  <th scope="col" className={`${cell} text-start font-medium text-ink`}>{t("charting.col.decision")}</th>
                </tr>
              </thead>
              <tbody>
                {loading
                  ? Array.from({ length: 8 }, (_, i) => (
                      <tr key={i} aria-hidden="true" data-skeleton="row">
                        {Array.from({ length: 6 }, (__, j) => (
                          <td key={j} className={cell}>
                            <span className="inline-flex h-4 w-full min-w-8 animate-pulse rounded-sm bg-rule" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : rows.map((row, index) => {
                      const focused = row.study_id === focusId;
                      const isSelected = selected.has(row.study_id);
                      return (
                        <tr
                          key={row.study_id}
                          aria-rowindex={index + 2}
                          aria-selected={isSelected}
                          tabIndex={focused ? 0 : -1}
                          onClick={() => setFocusId(row.study_id)}
                          onFocus={(event) => {
                            if (event.target === event.currentTarget) setFocusId(row.study_id);
                          }}
                          className={`border-t border-rule ${isSelected ? "bg-brand-soft" : ""} ${focused ? "outline-2 -outline-offset-2 outline-focus" : ""} ${row.kept ? "" : "text-ink-muted opacity-70"} focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-focus`}
                          data-study-row={row.study_id}
                          data-kept={row.kept ? "true" : "false"}
                          data-focused={focused || undefined}
                        >
                          <td className={`${cell} ${stickyStart} ${isSelected ? "bg-brand-soft" : ""}`}>
                            <input
                              type="checkbox"
                              tabIndex={-1}
                              checked={isSelected}
                              disabled={!row.kept}
                              onChange={() => toggle(row.study_id)}
                              aria-label={t("charting.select.row", { title: row.title ?? row.study_id })}
                              className="size-4 accent-[var(--color-brand)]"
                            />
                          </td>
                          <th scope="row" className={`${cell} ${stickyStudy} min-w-64 text-start font-normal ${isSelected ? "bg-brand-soft" : ""}`}>
                            {studyCell(row)}
                          </th>
                          <td className={cell}>{roundWords(row)}</td>
                          <td className={cell}>
                            <span className="flex flex-col items-start">
                              {statusBadge(row)}
                              {reasonLine(row)}
                            </span>
                          </td>
                          <td className={cell}>{fileCell(row)}</td>
                          <td className={cell}>{decisionCell(row)}</td>
                        </tr>
                      );
                    })}
              </tbody>
            </table>
            {!loading && rows.length === 0 ? <p className="px-4 py-6 text-ink-muted" data-empty-filter>{t("charting.empty.filter")}</p> : null}
          </div>
        )}

        <p className="min-h-5 text-sm text-ink" data-status-line>
          {statusLine}
        </p>

        <input
          ref={fileInput}
          type="file"
          accept="application/pdf,.pdf"
          tabIndex={-1}
          className="sr-only"
          aria-label={t("charting.file.attach")}
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void attach(file);
            else attachFor.current = null;
          }}
          data-file-input
        />
      </div>
    </div>
  );
}
