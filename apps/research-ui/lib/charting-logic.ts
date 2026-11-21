import type { ChartingCopyKey } from "./charting-copy";
import type { Cell, CellState, CellValue, ChartingRow, FormColumn, FulltextDecision, FulltextStatus, NotRetrievedReason } from "./charting-api";

/**
 * The charting screen's choices that are not the engine's (M12a Parts A and B):
 * which rows a filter shows, which key does what, the value an undo goes back to,
 * and how a typed draft becomes a cell value. The engine still judges every
 * event; nothing here decides a status, an outcome or whether a value fits.
 */

export type ShowFilter = "all" | "toGet" | "requested" | "notRetrieved" | "toDecide" | "included" | "excluded" | "notCharted" | "pilot";

export const SHOW_FILTERS: readonly ShowFilter[] = ["all", "toGet", "requested", "notRetrieved", "toDecide", "included", "excluded", "notCharted", "pilot"];

export function isShowFilter(value: string | null | undefined): value is ShowFilter {
  return SHOW_FILTERS.includes(value as ShowFilter);
}

export type TableView = "fulltext" | "charting";

export type StatusRole = "include" | "unclear" | "blocked" | "exclude" | "neutral";

export const STATUS_KEY: Record<FulltextStatus, ChartingCopyKey> = {
  to_get: "charting.status.toGet",
  requested: "charting.status.requested",
  retrieved: "charting.status.retrieved",
  not_retrieved: "charting.status.notRetrieved",
};

/** Spec 01 "Status roles": Requested is `unclear`, Not retrieved `blocked`, Retrieved `include`; To get has no role tint. */
export const STATUS_ROLE: Record<FulltextStatus, StatusRole> = {
  to_get: "neutral",
  requested: "unclear",
  retrieved: "include",
  not_retrieved: "blocked",
};

export const REASON_KEY: Record<NotRetrievedReason, ChartingCopyKey> = {
  no_access: "charting.notRetrieved.noAccess",
  not_found: "charting.notRetrieved.notFound",
  no_reply: "charting.notRetrieved.noReply",
  other: "charting.notRetrieved.other",
};

function excludedAtFullText(row: ChartingRow): boolean {
  return row.ft_decision?.outcome === "EXCLUDE";
}

/**
 * The rows a view shows, in the engine's order. A row excluded at full text is
 * left out unless "Show excluded" is on or the view is the excluded one; a row no
 * longer kept appears only under All (it is out of the counts).
 */
export function visibleRows(rows: readonly ChartingRow[], show: ShowFilter, showExcluded: boolean): ChartingRow[] {
  return rows.filter((row) => {
    if (show === "excluded") return row.kept && excludedAtFullText(row);
    if (excludedAtFullText(row) && !showExcluded) return false;
    if (show === "all") return true;
    if (!row.kept) return false;
    switch (show) {
      case "toGet":
        return row.fulltext.status === "to_get";
      case "requested":
        return row.fulltext.status === "requested";
      case "notRetrieved":
        return row.fulltext.status === "not_retrieved";
      case "toDecide":
        return row.ft_decision === null;
      case "included":
        return row.ft_decision?.outcome === "INCLUDE";
      case "notCharted":
        return !excludedAtFullText(row) && !row.charted;
      case "pilot":
        return row.pilot === true;
      default:
        return true;
    }
  });
}

export type ChartingKey =
  | "down" | "up" | "extendDown" | "extendUp" | "toggle" | "selectAll"
  | "toGet" | "requested" | "retrieved" | "notRetrieved"
  | "include" | "exclude" | "attach" | "open" | "undo" | "help" | "export"
  // Part B: the two views, the form panel, Enter, the arrows between cells and the two special cell values.
  | "viewFulltext" | "viewCharting" | "form" | "enter"
  | "arrowDown" | "arrowUp" | "arrowStart" | "arrowEnd"
  | "notReported" | "notApplicable";

const KEYMAP: Record<string, ChartingKey> = {
  j: "down", k: "up", x: "toggle", a: "selectAll",
  g: "toGet", q: "requested", r: "retrieved", n: "notRetrieved",
  i: "include", e: "exclude", p: "attach", o: "open", z: "undo", "?": "help",
  "1": "viewFulltext", "2": "viewCharting", f: "form", Enter: "enter",
  ArrowDown: "arrowDown", ArrowUp: "arrowUp",
};

export function isTextField(target: EventTarget | null): boolean {
  if (typeof HTMLElement === "undefined" || !(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "TEXTAREA" || tag === "SELECT" || (tag === "INPUT" && (target as HTMLInputElement).type !== "checkbox" && (target as HTMLInputElement).type !== "radio");
}

/** The letter of a key press, read from its physical key when Alt changed the character (macOS). */
function letterOf(event: { key: string; code?: string }): string {
  const fromCode = /^Key([A-Z])$/.exec(event.code ?? "")?.[1]?.toLowerCase();
  return fromCode ?? event.key.toLowerCase();
}

/**
 * The action of a key press, or null. Off in text fields; Ctrl+E (or Cmd+E) is
 * Export; Shift+J and Shift+K extend the selection; Alt+N and Alt+A set Not
 * reported and Not applicable on the focused cell (Part B). The arrows left and
 * right are given by where they point (`arrowStart`, `arrowEnd`), so the page can
 * mirror them in a right-to-left layout. The keys L, C and D stay free (Part F).
 */
export function chartingKey(
  event: Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "altKey" | "shiftKey"> & { code?: string },
  target: EventTarget | null,
  dir: "ltr" | "rtl" = "ltr",
): ChartingKey | null {
  if (isTextField(target)) return null;
  const key = event.key.toLowerCase();
  if ((event.ctrlKey || event.metaKey) && !event.altKey && key === "e") return "export";
  if (event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    const letter = letterOf(event);
    if (letter === "n") return "notReported";
    if (letter === "a") return "notApplicable";
    return null;
  }
  if (event.ctrlKey || event.metaKey || event.altKey) return null;
  if (event.shiftKey && key === "j") return "extendDown";
  if (event.shiftKey && key === "k") return "extendUp";
  if (event.key === "ArrowLeft") return dir === "rtl" ? "arrowEnd" : "arrowStart";
  if (event.key === "ArrowRight") return dir === "rtl" ? "arrowStart" : "arrowEnd";
  return KEYMAP[event.key] ?? KEYMAP[key] ?? null;
}

// ---------------------------------------------------------------- Part B: cells

/** A row can be charted when it is kept and not excluded at full text (spec 01, 02). */
export function chartable(row: ChartingRow): boolean {
  return row.kept && !excludedAtFullText(row);
}

/** The first row a researcher still has to chart, in the engine's order (spec 01 "Chart the next study"). */
export function nextToChart(rows: readonly ChartingRow[]): ChartingRow | null {
  return rows.find((row) => chartable(row) && !row.charted) ?? null;
}

/** Whether any cell of a row holds something (a value, Not reported or Not applicable). */
export function hasCellValue(row: ChartingRow): boolean {
  return Object.values(row.cells ?? {}).some((cell) => cell.state !== null);
}

/** Cells of kept, chartable rows that hold nothing yet (the export's "{n} cells are not charted yet"). */
export function openCells(rows: readonly ChartingRow[], columns: readonly FormColumn[]): number {
  let open = 0;
  for (const row of rows) {
    if (!chartable(row)) continue;
    for (const column of columns) {
      const cell = row.cells?.[column.column_id];
      if (!cell || cell.state === null || cell.chart_again) open += 1;
    }
  }
  return open;
}

export const EMPTY_CELL: Cell = {
  state: null, value: null, note: null, where_from: null, pilot: false, chart_again: false, history: [], event_id: null, form_version: null,
};

export function cellOf(row: ChartingRow, columnId: string): Cell {
  return row.cells?.[columnId] ?? EMPTY_CELL;
}

/** A cell's stored content in the exact shape a cell event carries it back (an undo restores it). */
export function cellContent(columnId: string, cell: Cell): { value: { column_id: string; state: CellState; value: CellValue }; note: string | null; whereFrom: string | null } {
  return {
    value: { column_id: columnId, state: cell.state, value: cell.state === "value" ? cell.value : null },
    note: cell.state === null ? null : cell.note,
    whereFrom: cell.state === null ? null : cell.where_from,
  };
}

/** What the researcher typed or chose, before it is sent. */
export type CellDraft = string | string[];

/** The draft an editor starts from: the stored value as text or as the chosen options. */
export function draftOf(column: FormColumn, cell: Cell): CellDraft {
  if (column.type === "several") return Array.isArray(cell.value) && cell.state === "value" ? [...cell.value] : [];
  if (cell.state !== "value" || cell.value === null) return "";
  return Array.isArray(cell.value) ? cell.value.join(", ") : String(cell.value);
}

/**
 * The value a draft sends, or why it cannot be sent. The engine still judges it
 * (`CHARTING_VALUE_INVALID`); here only an empty draft clears the cell and a
 * number that does not read as one stays on the screen with its words.
 */
export function valueOfDraft(column: FormColumn, draft: CellDraft): { kind: "clear" } | { kind: "value"; value: CellValue } | { kind: "notANumber" } {
  if (Array.isArray(draft)) {
    const chosen = column.options.filter((option) => draft.includes(option));
    return chosen.length === 0 ? { kind: "clear" } : { kind: "value", value: chosen };
  }
  const text = draft.trim();
  if (!text) return { kind: "clear" };
  if (column.type === "number") {
    const parsed = Number(text.replace(/\s/g, "").replace(/,(?=\d+$)/, "."));
    return Number.isFinite(parsed) ? { kind: "value", value: parsed } : { kind: "notANumber" };
  }
  return { kind: "value", value: column.type === "text" ? draft.trim() : text };
}

/** Whether two cell values are the same (a field that did not change sends nothing). */
export function sameValue(a: CellValue, b: CellValue): boolean {
  if (Array.isArray(a) || Array.isArray(b)) {
    return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((x, i) => x === b[i]);
  }
  return a === b;
}

/** The stored status value of a row, in the exact shape the engine accepts back (an undo restores it). */
export function statusValue(row: ChartingRow): Record<string, string> {
  const { status, requested_on: requestedOn, reason, reason_text: words } = row.fulltext;
  const value: Record<string, string> = { status };
  if (status === "requested" && requestedOn) value.requested_on = requestedOn;
  if (status === "not_retrieved" && reason) {
    value.reason = reason;
    if (reason === "other" && words) value.reason_text = words;
  }
  return value;
}

/** The stored decision of a row in the shape the engine accepts back, or null (undecided). */
export function decisionValue(decision: FulltextDecision | null): Record<string, string> | null {
  if (!decision) return null;
  const value: Record<string, string> = { outcome: decision.outcome };
  if (decision.outcome === "EXCLUDE" && decision.reason_code) {
    value.reason_code = decision.reason_code;
    if (decision.reason_code === "OTHER" && decision.reason_text) value.reason_text = decision.reason_text;
  }
  return value;
}

/** A size in bytes as words a reader knows (Latin digits; the unit is a symbol, not translated). */
export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Codes that mean the console could not be reached: changes are refused here until it answers. */
export const UNREACHABLE_CODES = new Set(["ENGINE_UNREACHABLE", "CONSOLE_UNREACHABLE", "CONSOLE_TIMEOUT", "MALFORMED_JSON"]);
