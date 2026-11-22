"use client";

import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ComponentType, type MutableRefObject, type ReactNode, type SVGProps } from "react";
import {
  AdjustmentsHorizontalIcon,
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
  chartingStudyHref,
  endChartingPilot,
  exportCsv,
  getCharting,
  postChartingEvents,
  postLink,
  type CellState,
  type CellValue,
  type ChartingEvent,
  type ChartingForm,
  type ChartingRow,
  type ChartingTable,
  type EventKind,
  type ExportView,
  type FormColumn,
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
  cellContent,
  cellOf,
  chartable,
  chartingKey,
  decisionValue,
  draftOf,
  fileSize,
  hasCellValue,
  isShowFilter,
  isTextField,
  nextToChart,
  openCells,
  sameValue,
  statusValue,
  valueOfDraft,
  visibleRows,
  type CellDraft,
  type ShowFilter,
  type StatusRole,
  type TableView,
} from "@/lib/charting-logic";
import { newEventId } from "@/lib/screening-v1";

import { CellEditor, CellView, FOCUS_RING, NoFullTextMark, PilotMark, TYPE_KEY, cellWords } from "./charting-cells";
import { ChartingFormPanel } from "./charting-form-panel";

/**
 * The charting screen (spec 01, M12a Parts A and B): one row per study kept at
 * title and abstract, in two views of the same rows. The Full text view (Part A)
 * holds the full-text status, the file or link and the full-text decision with
 * one reason. The Charting view (Part B) holds one column per column of the
 * charting form, edited in the cell (Enter, Esc, Alt+N, Alt+A); the form panel
 * (F) sits beside the rows; Enter on a row opens the one-study view. Every
 * change is one event, saved at once; the engine judges it and answers the rows
 * it touched. The keys L, C and D stay free for Part F.
 */

type Refusal = { code: string; message: string };

type Mode =
  | { kind: "bulk"; status: FulltextStatus; ids: string[] }
  | { kind: "notRetrieved"; ids: string[]; reason: NotRetrievedReason | null; words: string }
  | { kind: "exclude"; id: string; code: string | null; words: string };

/** What an undo sends back: the earlier value, and for a cell its note and where-from. */
type Before = { value: unknown; note?: string | null; whereFrom?: string | null };
type UndoStep = Before & { studyId: string; kind: EventKind; supersedes: string };
type UndoEntry = { steps: UndoStep[] };

/** The focused place in the Charting view: column 0 is the study, 1 to n the form's columns. */
type Editing = { row: string; col: number } | null;

/** The screen's place from the address (view, filter, row, form), read after mounting so the first paint matches the server's. */
function readPlace(): { view: TableView; show: ShowFilter; excluded: boolean; row: string | null; form: boolean } {
  const query = new URLSearchParams(window.location.search);
  const show = query.get("show");
  return {
    view: query.get("view") === "charting" ? "charting" : "fulltext",
    show: isShowFilter(show) ? show : "all",
    excluded: query.get("excluded") === "1",
    row: query.get("row"),
    form: query.get("form") === "open",
  };
}

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
  notCharted: "charting.table.show.notCharted",
  pilot: "charting.table.show.pilot",
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

/** What a row of the Charting view calls back; held in a ref so a row re-renders only when its own props change. */
type GridActions = {
  focusCell: (rowId: string, col: number) => void;
  startEdit: (rowId: string, col: number) => void;
  commit: (rowId: string, col: number, draft: CellDraft, how: "enter" | "blur") => void;
  cancel: (rowId: string, col: number) => void;
  studyCell: (row: ChartingRow) => ReactNode;
  decisionBadge: (row: ChartingRow) => ReactNode;
  statusBadge: (row: ChartingRow) => ReactNode;
  roundWords: (row: ChartingRow) => string;
  t: (key: ChartingCopyKey, values?: Record<string, string | number>) => string;
};

/**
 * One row of the Charting view (spec 01): the study as the row header, then one
 * cell per form column. Memoised: moving the focus re-renders the two rows it
 * leaves and enters, not every row (DoD 14, 150 rows by 5 columns).
 */
const ChartingGridRow = memo(function ChartingGridRow({
  row,
  index,
  columns,
  locale,
  focusCol,
  editCol,
  readOnly,
  actions,
}: Readonly<{
  row: ChartingRow;
  index: number;
  columns: FormColumn[];
  locale: Locale;
  focusCol: number | null;
  editCol: number | null;
  readOnly: boolean;
  actions: MutableRefObject<GridActions>;
}>) {
  const a = actions.current;
  const locked = readOnly || !chartable(row);
  const cellClass = "px-3 py-2 align-top";
  const ring = "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-focus";
  const focusedHere = (col: number) => (focusCol === col ? "outline-2 -outline-offset-2 outline-focus" : "");
  return (
    <tr
      aria-rowindex={index + 2}
      className={`border-t border-rule ${row.kept && chartable(row) ? "" : "text-ink-muted opacity-70"}`}
      data-study-row={row.study_id}
      data-kept={row.kept ? "true" : "false"}
      data-focused={focusCol !== null || undefined}
    >
      <th
        scope="row"
        aria-colindex={1}
        tabIndex={focusCol === 0 ? 0 : -1}
        onFocus={(event) => {
          if (event.target === event.currentTarget) actions.current.focusCell(row.study_id, 0);
        }}
        onClick={() => actions.current.focusCell(row.study_id, 0)}
        className={`${cellClass} sticky start-0 z-10 min-w-64 bg-leaf text-start font-normal ${focusedHere(0)} ${ring}`}
        data-cell={`${row.study_id}:0`}
      >
        {a.studyCell(row)}
        <span className="mt-1 flex flex-wrap items-center gap-1">
          {row.pilot ? <PilotMark locale={locale} /> : null}
          {row.no_full_text && hasCellValue(row) ? <NoFullTextMark locale={locale} /> : null}
          {row.kept && !chartable(row) ? a.decisionBadge(row) : null}
        </span>
      </th>
      {columns.map((column, i) => {
        const col = i + 1;
        const cell = cellOf(row, column.column_id);
        return (
          <td
            key={column.column_id}
            role="gridcell"
            aria-colindex={col + 1}
            aria-readonly={locked || undefined}
            tabIndex={focusCol === col && editCol !== col ? 0 : -1}
            onFocus={(event) => {
              if (event.target === event.currentTarget) actions.current.focusCell(row.study_id, col);
            }}
            onClick={() => actions.current.focusCell(row.study_id, col)}
            onDoubleClick={() => actions.current.startEdit(row.study_id, col)}
            className={`${cellClass} min-w-40 ${focusedHere(col)} ${ring}`}
            data-cell={`${row.study_id}:${col}`}
            data-cell-state={cell.state ?? "empty"}
          >
            {editCol === col ? (
              <CellEditor
                locale={locale}
                column={column}
                initial={draftOf(column, cell)}
                label={a.t("charting.cell.edit", { column: column.name, title: row.title ?? row.study_id })}
                onCommit={(draft, how) => actions.current.commit(row.study_id, col, draft, how)}
                onCancel={() => actions.current.cancel(row.study_id, col)}
              />
            ) : (
              <CellView locale={locale} column={column} cell={cell} />
            )}
          </td>
        );
      })}
    </tr>
  );
});

/** One card of the phone list (spec 01 "Mobile layout"): a link to the one-study view; memoised like the rows of the Charting view. */
const PhoneCard = memo(function PhoneCard({
  row,
  columns,
  locale,
  origin,
  view,
  show,
  excluded,
  actions,
}: Readonly<{ row: ChartingRow; columns: FormColumn[]; locale: Locale; origin: string; view: TableView; show: ShowFilter; excluded: boolean; actions: MutableRefObject<GridActions> }>) {
  const a = actions.current;
  const href = chartingStudyHref(locale, row.study_id, origin, { view, show, excluded });
  const filled = columns.filter((c) => cellOf(row, c.column_id).state !== null);
  return (
    <li className={`rounded-md border border-rule bg-leaf ${row.kept ? "" : "opacity-70"}`} data-phone-card>
      <a href={href} className={`flex min-h-11 flex-col gap-2 rounded-md px-3 py-2 ${FOCUS_RING}`} data-phone-link>
        {a.studyCell(row)}
        <span className="flex flex-wrap items-center gap-2 text-xs text-ink-muted">
          <span>{a.roundWords(row)}</span>
          {a.statusBadge(row)}
          {a.decisionBadge(row)}
        </span>
        {filled.length ? (
          <dl className="space-y-0.5 text-xs" data-phone-values>
            {filled.map((c) => (
              <div key={c.column_id} className="flex flex-wrap gap-1">
                <dt className="font-medium text-ink">
                  <bdi>{c.name}</bdi>:
                </dt>
                <dd className="text-ink-muted">
                  <bdi>{cellWords(locale, c, cellOf(row, c.column_id))}</bdi>
                </dd>
              </div>
            ))}
          </dl>
        ) : null}
      </a>
    </li>
  );
});

/**
 * Which of the two layouts this window shows: the phone list below 640 px, the
 * desktop screen above. Both are drawn (and CSS picks one) until the window says,
 * and always where it cannot (the first paint, a test page without matchMedia);
 * drawing only the one shown keeps a key press from reconciling the other.
 */
function useViewport(): "phone" | "desktop" | "both" {
  const [viewport, setViewport] = useState<"phone" | "desktop" | "both">("both");
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia("(min-width: 640px)");
    const update = () => setViewport(query.matches ? "desktop" : "phone");
    update();
    query.addEventListener?.("change", update);
    return () => query.removeEventListener?.("change", update);
  }, []);
  return viewport;
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
  const viewport = useViewport();

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
  // Part B: the view, the focused cell, the cell being edited, the form panel, the export menu, the first-visit card.
  const [view, setView] = useState<TableView>("fulltext");
  const [focusCol, setFocusCol] = useState(0);
  const [editing, setEditing] = useState<Editing>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelAdd, setPanelAdd] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [cardClosed, setCardClosed] = useState(false);
  const undoStack = useRef<UndoEntry[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const attachFor = useRef<string | null>(null);
  const wordsInput = useRef<HTMLInputElement>(null);
  const focusRow = useRef(false);
  const formButton = useRef<HTMLButtonElement>(null);
  const exportButton = useRef<HTMLButtonElement>(null);
  const placeRead = useRef(false);
  const gridActions = useRef<GridActions>(null as unknown as GridActions);

  const boot = useCallback(async () => {
    setLoad({ status: "loading" });
    // The place in the address is read once, after mounting (the server's first paint has none).
    if (!placeRead.current) {
      placeRead.current = true;
      const place = readPlace();
      setView(place.view);
      setShow(place.show);
      setShowExcluded(place.excluded);
      if (place.row) setFocusId(place.row);
      if (place.row) focusRow.current = true;
      if (place.form) {
        setPanelOpen(true);
        setPanelAdd(true);
      }
    }
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

  /** Read the rows again without the loading state (after a form change, which may mark cells "Chart again"). */
  const reload = useCallback(async () => {
    try {
      const answer = await getCharting(origin);
      setTable(answer);
      setOffline(false);
    } catch (error) {
      const r = refusalOf(error);
      if (UNREACHABLE_CODES.has(r.code)) setOffline(true);
      else setRefusal(r);
    }
  }, [origin]);

  const rows = useMemo(() => (table ? visibleRows(table.rows, show, showExcluded) : []), [table, show, showExcluded]);
  const rowsRef = useRef(rows);
  rowsRef.current = rows;
  const byId = useMemo(() => new Map((table?.rows ?? []).map((r) => [r.study_id, r])), [table]);
  const readOnly = table?.read_only ?? false;
  const reasons = table?.reason_options ?? [];
  const notRetrievedReasons = table?.not_retrieved_reasons ?? ["no_access", "not_found", "no_reply", "other"];
  const form: ChartingForm | null = table?.form ?? null;
  const columns: FormColumn[] = useMemo(() => form?.columns ?? [], [form]);
  // The name of every column seen during this page load, kept here because the form
  // panel unmounts when it closes: its "Made from" can then still name a column that a
  // split or merge removed before any value existed (no amendment names it then).
  const seenColumnNames = useRef(new Map<string, string>());
  for (const c of columns) seenColumnNames.current.set(c.column_id, c.name);

  // The address follows the view and the filter, so Back from a study returns to them.
  useEffect(() => {
    if (!placeRead.current || typeof window === "undefined") return;
    try {
      const query = new URLSearchParams(window.location.search);
      for (const key of ["view", "show", "excluded", "row", "form"]) query.delete(key);
      if (view !== "fulltext") query.set("view", view);
      if (show !== "all") query.set("show", show);
      if (showExcluded) query.set("excluded", "1");
      const text = query.toString();
      window.history.replaceState(window.history.state, "", `${window.location.pathname}${text ? `?${text}` : ""}`);
    } catch {
      /* an address that cannot be rewritten (a test page) keeps the screen as it is */
    }
  }, [view, show, showExcluded]);

  // Keep the focused row on one that is shown.
  useEffect(() => {
    if (rows.length === 0) return;
    if (!focusId || !rows.some((r) => r.study_id === focusId)) setFocusId(rows[0].study_id);
  }, [rows, focusId]);

  // Keep the focused column inside the form.
  useEffect(() => {
    if (focusCol > columns.length) setFocusCol(columns.length);
  }, [columns.length, focusCol]);

  useEffect(() => {
    if (!focusRow.current || !focusId || load.status !== "ready") return;
    focusRow.current = false;
    const selector = view === "charting" && columns.length > 0 ? `[data-cell="${focusId}:${focusCol}"]` : `[data-study-row="${focusId}"]`;
    const element = document.querySelector<HTMLElement>(selector);
    element?.focus();
    element?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
  }, [focusId, focusCol, table, view, columns.length, editing, load.status]);

  function moveFocus(id: string | null, col?: number) {
    focusRow.current = true;
    setFocusId(id);
    if (col !== undefined) setFocusCol(col);
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
  async function send(events: ChartingEvent[], previous: (event: ChartingEvent) => Before, firstId: string | null) {
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
        pushUndo({ steps: accepted.map((e) => ({ studyId: e.study_id, kind: e.kind, supersedes: e.event_id, ...previous(e) })) });
        saved(accepted.length);
        // The first value turns later form changes into recorded amendments: read the form's answer again.
        if (accepted.some((e) => e.kind === "cell") && form && !form.has_values) void reload();
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
    void send(events, (e) => ({ value: before.get(e.study_id) }), targets[0].study_id);
  }

  function decide(id: string, value: Record<string, string>) {
    const row = byId.get(id);
    if (!table || !row || !row.kept || !changesAllowed()) return;
    const before = decisionValue(row.ft_decision);
    const event = chartingEvent({ studyId: id, screenerId: table.screener_id, kind: "fulltext_decision", value, supersedes: row.heads.fulltext_decision });
    void send([event], () => ({ value: before }), id);
  }

  // ------------------------------------------------------------ Part B: cells

  /** Why a row's cells cannot be changed here, as words for the status line, or null. */
  function lockedWords(row: ChartingRow): string | null {
    if (readOnly) return t("charting.archived");
    if (!row.kept) return t("charting.study.noLongerKept");
    if (!chartable(row)) return t("charting.cell.excludedRow");
    return null;
  }

  /** One cell event: the new state and value, the cell's note and where-from kept, superseding what holds the cell now. */
  function saveCell(rowId: string, column: FormColumn, next: { state: CellState; value: CellValue }) {
    const row = byId.get(rowId);
    if (!table || !row || !changesAllowed()) return;
    const locked = lockedWords(row);
    if (locked) {
      setStatusLine(locked);
      return;
    }
    const cell = cellOf(row, column.column_id);
    const before = cellContent(column.column_id, cell);
    const keepWords = next.state !== null;
    const event = chartingEvent({
      studyId: rowId,
      screenerId: table.screener_id,
      kind: "cell",
      value: { column_id: column.column_id, state: next.state, value: next.state === "value" ? next.value : null },
      note: keepWords ? cell.note : null,
      whereFrom: keepWords ? cell.where_from : null,
      supersedes: cell.event_id,
    });
    void send([event], () => before, null);
  }

  function startEdit(rowId: string, col: number) {
    const row = byId.get(rowId);
    const column = columns[col - 1];
    if (!row || !column) return;
    if (offline) {
      setStatusLine(t("charting.refusal.OFFLINE"));
      return;
    }
    const locked = lockedWords(row);
    if (locked) {
      setStatusLine(locked);
      return;
    }
    setStatusLine("");
    setEditing({ row: rowId, col });
  }

  function commitEdit(rowId: string, col: number, draft: CellDraft, how: "enter" | "blur") {
    setEditing(null);
    const row = byId.get(rowId);
    const column = columns[col - 1];
    if (!row || !column) return;
    const cell = cellOf(row, column.column_id);
    const parsed = valueOfDraft(column, draft);
    if (parsed.kind === "notANumber") {
      setStatusLine(t("charting.cell.numberInvalid"));
      moveFocus(rowId, col);
      return;
    }
    if (parsed.kind === "clear") {
      if (cell.state === "value") saveCell(rowId, column, { state: null, value: null });
    } else if (!(cell.state === "value" && sameValue(cell.value, parsed.value) && !cell.chart_again)) {
      saveCell(rowId, column, { state: "value", value: parsed.value });
    }
    if (how === "enter") {
      // Enter saves and moves down (spec 01 "Keyboard").
      const list = rowsRef.current;
      const at = list.findIndex((r) => r.study_id === rowId);
      moveFocus(list[Math.min(list.length - 1, at + 1)]?.study_id ?? rowId, col);
    }
  }

  function cancelEdit(rowId: string, col: number) {
    setEditing(null);
    moveFocus(rowId, col);
  }

  /** Alt+N and Alt+A: Not reported or Not applicable on the focused cell; the same key again clears it. */
  function special(rowId: string, col: number, state: "not_reported" | "not_applicable") {
    const row = byId.get(rowId);
    const column = columns[col - 1];
    if (!row || !column) return;
    const cell = cellOf(row, column.column_id);
    saveCell(rowId, column, cell.state === state && !cell.chart_again ? { state: null, value: null } : { state, value: null });
  }

  function openStudy(id: string) {
    window.location.assign(chartingStudyHref(locale, id, origin, { view, show, excluded: showExcluded }));
  }

  function openPanel(addFirst = false) {
    setPanelAdd(addFirst);
    setPanelOpen(true);
    setExportOpen(false);
    if (!cardClosed) setCardClosed(true);
    setTimeout(() => document.querySelector<HTMLElement>("[data-form-panel] [data-form-name], [data-form-panel] [data-end-pilot], [data-form-panel] [data-form-add]")?.focus(), 0);
  }

  function closePanel() {
    setPanelOpen(false);
    setPanelAdd(false);
    setTimeout(() => formButton.current?.focus(), 0);
  }

  async function endPilot() {
    if (!form || !changesAllowed()) return;
    setBusy(true);
    setRefusal(null);
    try {
      const answer = await endChartingPilot(origin, form.version);
      setTable((current) => (current ? { ...current, form: answer } : current));
      setAnnounce(t("charting.pilot.endedAnnounce"));
    } catch (error) {
      wentOffline(error);
    } finally {
      setBusy(false);
    }
  }

  function formSaved(next: ChartingForm) {
    setTable((current) => (current ? { ...current, form: next } : current));
    // A form change may mark cells "Chart again": read the rows again.
    void reload();
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
      chartingEvent({ studyId: s.studyId, screenerId: table.screener_id, kind: s.kind, value: s.value, supersedes: s.supersedes, note: s.note, whereFrom: s.whereFrom }),
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

  async function runExport(which: ExportView) {
    setExportOpen(false);
    if (offline) {
      setStatusLine(t("charting.refusal.OFFLINE"));
      return;
    }
    if (!table || exporting) return;
    setExporting(true);
    setRefusal(null);
    setAnnounce(t("charting.export.preparing"));
    try {
      const { blob, filename } = await exportCsv(origin, which);
      saveFile(blob, filename);
      // The Charting CSV holds every kept row not excluded at full text; the Full text CSV every kept row.
      const rowsInFile = which === "charting" ? table.counts.kept - table.counts.excluded : table.counts.kept;
      let message = t("charting.announce.exported", { when: localStamp(new Date().toISOString()), n: n(rowsInFile) });
      if (which === "charting") message = `${message} ${t("charting.export.cellsOpen", { n: n(openCells(table.rows, columns)) })}`;
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

  function changeView(next: TableView) {
    if (next === view) return;
    setView(next);
    setEditing(null);
    setMode(null);
    setSelected(new Set());
    focusRow.current = true;
  }

  function toggleExport() {
    setExportOpen((open) => {
      if (!open) setTimeout(() => document.querySelector<HTMLElement>("[data-export-menu] button")?.focus(), 0);
      return !open;
    });
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
      // A cell being edited keeps its keys (Enter, Esc, arrows in its options).
      if (editing) return;
      const target = event.target as HTMLElement | null;
      const inWords = target instanceof HTMLElement && target.dataset.modeWords !== undefined;
      // The row that has the keyboard's focus is the focused row, whatever the last click said.
      const rowTarget = target instanceof HTMLElement ? target.closest<HTMLElement>("[data-study-row]")?.dataset.studyRow ?? null : null;
      const here = rowTarget ?? focusId;
      if (rowTarget && rowTarget !== focusId) setFocusId(rowTarget);
      const cellTarget = target instanceof HTMLElement ? target.closest<HTMLElement>("[data-cell]")?.dataset.cell ?? null : null;
      const col = cellTarget ? Number(cellTarget.slice(cellTarget.lastIndexOf(":") + 1)) : focusCol;
      if (cellTarget && col !== focusCol) setFocusCol(col);
      const inPanel = target instanceof HTMLElement && target.closest("[data-form-panel]") !== null;
      const inMenu = target instanceof HTMLElement && target.closest("[data-export-menu]") !== null;
      if (event.key === "Escape") {
        if (help) setHelp(false);
        else if (exportOpen) {
          setExportOpen(false);
          exportButton.current?.focus();
        } else if (mode) setMode(null);
        else if (linkFor) setLinkFor(null);
        else if (panelOpen) closePanel();
        else if (selected.size > 0) setSelected(new Set());
        if (mode && here) moveFocus(here);
        return;
      }
      // The panel and the menu are forms of their own: the screen's letters do not reach them.
      if (inPanel || inMenu) return;
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
      const dir = document.documentElement.getAttribute("dir") === "rtl" ? "rtl" : "ltr";
      const key = chartingKey(event, target, dir);
      if (key === null) return;
      const charting = view === "charting" && columns.length > 0;
      // Enter on a button, a link or a field does what that control does.
      if (key === "enter" && target instanceof HTMLElement && target.closest("button, a, summary, input, select, textarea, label") !== null) return;
      // The arrows belong to the cells; elsewhere (the view switch, a select) they keep their own meaning.
      const arrow = key === "arrowDown" || key === "arrowUp" || key === "arrowStart" || key === "arrowEnd";
      const inGrid = target instanceof HTMLElement && (target.closest("[role=grid]") !== null || target === document.body);
      if (arrow && !inGrid) return;
      // The full-text keys act in the Full text view (spec 01 "Keyboard").
      const fullTextOnly = ["toGet", "requested", "retrieved", "notRetrieved", "include", "exclude", "attach", "toggle", "selectAll", "extendDown", "extendUp"];
      if (view === "charting" && fullTextOnly.includes(key)) return;
      event.preventDefault();
      if (key === "help") setHelp((h) => !h);
      else if (key === "down" || key === "up" || key === "arrowDown" || key === "arrowUp") {
        step(key === "down" || key === "arrowDown" ? 1 : -1, false, here);
      } else if (key === "arrowStart" || key === "arrowEnd") {
        if (charting && here) moveFocus(here, Math.min(columns.length, Math.max(0, col + (key === "arrowEnd" ? 1 : -1))));
      } else if (key === "extendDown" || key === "extendUp") step(key === "extendDown" ? 1 : -1, true, here);
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
      else if (key === "export") toggleExport();
      else if (key === "viewFulltext") changeView("fulltext");
      else if (key === "viewCharting") changeView("charting");
      else if (key === "form") {
        if (panelOpen) closePanel();
        else openPanel(columns.length === 0);
      } else if (key === "enter" && here) {
        if (charting && col > 0) startEdit(here, col);
        else openStudy(here);
      } else if ((key === "notReported" || key === "notApplicable") && charting && here && col > 0) {
        special(here, col, key === "notReported" ? "not_reported" : "not_applicable");
      }
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

  // Part B: the Charting view's pieces.
  const showCard = !loading && !nothingKept && !readOnly && form !== null && form.pilot.on && !form.has_values && columns.length > 0 && !cardClosed;
  const noColumns = !loading && form !== null && columns.length === 0;
  const nextRow = table ? nextToChart(table.rows) : null;
  const chartableRows = counts ? counts.kept - counts.excluded : 0;
  const primaryTaken = showCard || (view === "charting" && noColumns);
  const linkClass = primaryTaken ? `inline-flex min-h-11 items-center justify-center rounded-md border border-rule-strong bg-leaf px-4 font-medium text-ink ${FOCUS_RING}` : `${PRIMARY_LINK} ${FOCUS_RING}`;
  const nextAction =
    loading || nothingKept || noColumns || !table ? null : nextRow ? (
      <a
        className={linkClass}
        data-variant={primaryTaken ? "secondary" : "primary"}
        href={chartingStudyHref(locale, nextRow.study_id, origin, { view, show, excluded: showExcluded })}
        data-chart-next
      >
        {t("charting.next")}
      </a>
    ) : chartableRows > 0 ? (
      <Button variant={primaryTaken ? "secondary" : "primary"} disabled={exporting || offline} onClick={() => void runExport("charting")} data-next-export>
        <ArrowDownTrayIcon aria-hidden="true" className="size-4" />
        {t("charting.export.menu")}
      </Button>
    ) : null;

  gridActions.current = {
    // A focus that lands where the screen already is changes nothing (no second render per key press).
    focusCell: (rowId, col) => {
      if (rowId !== focusId) setFocusId(rowId);
      if (col !== focusCol) setFocusCol(col);
    },
    startEdit,
    commit: commitEdit,
    cancel: cancelEdit,
    studyCell,
    decisionBadge,
    statusBadge,
    roundWords,
    t,
  };

  const firstVisitCard = showCard ? (
    <section aria-labelledby="charting-first-visit" className="flex flex-wrap items-center gap-3 rounded-md border border-rule bg-leaf px-4 py-3" data-first-visit>
      <p id="charting-first-visit" className="text-ink">
        {t("charting.pilot.suggest")}
      </p>
      <div className="flex flex-wrap gap-2">
        <Button variant="primary" onClick={() => openPanel(false)} data-first-visit-open>
          {t("charting.form.open")}
        </Button>
        <Button
          variant="quiet"
          onClick={() => setCardClosed(true)}
          data-first-visit-close
        >
          {t("charting.pilot.notNow")}
        </Button>
      </div>
    </section>
  ) : null;

  const noColumnsState = (
    <section className="rounded-md border border-rule bg-leaf p-5" data-state="no-columns">
      <p className="text-ink">{t("charting.form.empty")}</p>
      {readOnly ? null : (
        <Button variant="primary" className="mt-3" onClick={() => openPanel(true)} data-add-first-column>
          {t("charting.form.addFirst")}
        </Button>
      )}
    </section>
  );

  const chartingGrid = (
    <div className="max-h-[70vh] overflow-auto rounded-md border border-rule" data-grid-scroll>
      <table
        role="grid"
        aria-label={t("charting.table.gridCharting")}
        aria-rowcount={rows.length + 1}
        aria-colcount={columns.length + 1}
        aria-readonly={readOnly || undefined}
        className="w-full border-collapse text-sm"
        data-grid="charting"
      >
        <thead className="sticky top-0 z-20 bg-paper">
          <tr aria-rowindex={1}>
            <th scope="col" aria-colindex={1} className={`${cell} sticky start-0 z-10 min-w-64 bg-paper text-start font-medium text-ink`}>
              {t("charting.col.study")}
            </th>
            {columns.map((column, i) => (
              <th key={column.column_id} scope="col" aria-colindex={i + 2} className={`${cell} min-w-40 text-start font-medium text-ink`} data-column={column.column_id}>
                <span className="flex flex-col">
                  <bdi>{column.name}</bdi>
                  <span className="text-xs font-normal text-ink-muted">
                    {t(TYPE_KEY[column.type])}
                    {column.required ? (
                      <>
                        {" · "}
                        <span data-required>{t("charting.col.required")}</span>
                      </>
                    ) : null}
                  </span>
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <ChartingGridRow
              key={row.study_id}
              row={row}
              index={index}
              columns={columns}
              locale={locale}
              focusCol={row.study_id === focusId ? focusCol : null}
              editCol={editing && editing.row === row.study_id ? editing.col : null}
              readOnly={readOnly}
              actions={gridActions}
            />
          ))}
        </tbody>
      </table>
      {rows.length === 0 ? <p className="px-4 py-6 text-ink-muted" data-empty-filter>{t("charting.empty.filter")}</p> : null}
    </div>
  );

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
              charted: n(counts.charted ?? 0),
            })}
          </p>
        )}
      </header>

      <p role="status" aria-live="polite" className="sr-only" data-announce>
        {announce}
      </p>

      {/* Phone: a read-only list (spec 01 "Mobile layout"); each card opens the one-study view (spec 02). */}
      <section className="space-y-3 sm:hidden" data-phone>
        <p className="rounded-md border border-rule bg-leaf px-4 py-3 text-ink">{t("charting.mobile")}</p>
        {showSelect("charting-show-phone")}
        {loading || viewport === "desktop" ? null : (
          <ul className="space-y-2" data-phone-list>
            {rows.map((row) => (
              <PhoneCard key={row.study_id} row={row} columns={columns} locale={locale} origin={origin} view={view} show={show} excluded={showExcluded} actions={gridActions} />
            ))}
          </ul>
        )}
      </section>

      {viewport === "phone" ? null : (
      <div className="hidden space-y-4 sm:block" data-desktop>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2" data-toolbar>
          <div role="radiogroup" aria-label={t("charting.table.view.label")} className="inline-flex rounded-md border border-rule-strong p-0.5" data-view-switch>
            {(["fulltext", "charting"] as const).map((v, i) => (
              <label
                key={v}
                className={`inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-sm px-3 text-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-focus ${view === v ? "bg-brand-soft font-semibold text-brand" : "text-ink"}`}
              >
                <input type="radio" name="charting-view" value={v} checked={view === v} disabled={loading} onChange={() => changeView(v)} className="sr-only" data-view={v} />
                {t(v === "fulltext" ? "charting.table.view.fulltext" : "charting.table.view.charting")}
                <kbd className="text-xs opacity-80">{i + 1}</kbd>
              </label>
            ))}
          </div>
          {showSelect("charting-show")}
          <label className="flex min-h-11 items-center gap-2 text-sm text-ink">
            <input type="checkbox" checked={showExcluded} disabled={loading} onChange={(event) => setShowExcluded(event.target.checked)} className="size-4 accent-[var(--color-brand)]" data-show-excluded />
            {t("charting.table.showExcluded")}
          </label>
          <Button
            ref={formButton}
            variant="quiet"
            disabled={loading || !form}
            aria-expanded={panelOpen}
            aria-controls="charting-form-panel"
            onClick={() => (panelOpen ? closePanel() : openPanel(columns.length === 0))}
            data-form-button
          >
            <AdjustmentsHorizontalIcon aria-hidden="true" className="size-4" />
            {t("charting.form.button")} <kbd className="text-xs opacity-80">F</kbd>
          </Button>
          {form ? (
            <span className="flex min-h-11 items-center gap-2 text-sm text-ink" data-pilot>
              <button
                type="button"
                role="switch"
                aria-checked={form.pilot.on}
                aria-labelledby="charting-pilot-name"
                aria-describedby="charting-pilot-state"
                disabled={loading || readOnly || busy || !form.pilot.on}
                onClick={() => void endPilot()}
                className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border border-rule-strong disabled:cursor-not-allowed ${form.pilot.on ? "bg-brand" : "bg-paper"} ${FOCUS_RING}`}
                data-pilot-switch
              >
                <span aria-hidden="true" className={`inline-flex size-4 rounded-full bg-leaf shadow-sm ${form.pilot.on ? "translate-x-6 rtl:-translate-x-6" : "translate-x-1 rtl:-translate-x-1"}`} />
              </button>
              <span id="charting-pilot-name">{t("charting.pilot.label")}</span>
              <span id="charting-pilot-state" className="text-xs text-ink-muted">
                {form.pilot.on ? t("charting.pilot.end") : t("charting.pilot.ended", { date: localDate(form.pilot.ended_at) })}
              </span>
            </span>
          ) : null}
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
            <span className="relative inline-flex">
              <Button ref={exportButton} disabled={loading || exporting || offline} onClick={toggleExport} aria-expanded={exportOpen} aria-controls="charting-export-menu" data-export>
                <ArrowDownTrayIcon aria-hidden="true" className="size-4" />
                {t("charting.export.menu")}
              </Button>
              {exportOpen ? (
                <span id="charting-export-menu" className="absolute end-0 top-full z-30 mt-1 flex w-64 flex-col gap-1 rounded-md border border-rule bg-leaf p-1 shadow-md" data-export-menu>
                  <Button variant="quiet" className="justify-start text-start text-sm" onClick={() => void runExport("fulltext")} data-export-fulltext>
                    {t("charting.export.csv")}
                  </Button>
                  <Button variant="quiet" className="justify-start text-start text-sm" onClick={() => void runExport("charting")} data-export-charting>
                    {t("charting.export.csvCharting")}
                  </Button>
                </span>
              ) : null}
            </span>
            {nextAction}
          </div>
        </div>

        {help ? (
          <section aria-labelledby="charting-help-title" className="rounded-md border border-rule bg-leaf p-4 text-sm" data-help>
            <h2 id="charting-help-title" className="font-semibold text-ink">
              {t("charting.help.title")}
            </h2>
            <p className="mt-2 text-ink-muted">{t("charting.help.body")}</p>
            <p className="mt-2 text-ink-muted">{t("charting.help.bodyCharting")}</p>
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

        {firstVisitCard}

        {nothingKept ? (
          <section className="rounded-md border border-rule bg-leaf p-5" data-state="nothing-kept">
            <p className="text-ink">{t("charting.empty.nothingKept")}</p>
            <a className={`mt-2 inline-flex min-h-11 items-center text-brand ${FOCUS_RING}`} href={stepHref(locale, "triage", origin)}>
              {t("charting.empty.goTriage")}
            </a>
          </section>
        ) : (
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start" data-table-area>
          <div className="min-w-0 flex-1">
          {view === "charting" && !loading ? (noColumns ? noColumnsState : chartingGrid) : (
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
          </div>
          {panelOpen && form ? (
            <ChartingFormPanel
              locale={locale}
              origin={origin}
              form={form}
              seenNames={seenColumnNames.current}
              readOnly={readOnly || offline}
              addOnOpen={panelAdd}
              onSaved={formSaved}
              onEndPilot={() => void endPilot()}
              onClose={closePanel}
              onAnnounce={setAnnounce}
              onReload={() => void reload()}
            />
          ) : null}
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
      )}
    </div>
  );
}
