import type { ChartingCopyKey } from "./charting-copy";
import type { ChartingRow, FulltextDecision, FulltextStatus, NotRetrievedReason } from "./charting-api";

/**
 * The charting screen's choices that are not the engine's (M12a Part A): which
 * rows a filter shows, which key does what, and the value an undo goes back to.
 * The engine still judges every event; nothing here decides a status or an outcome.
 */

export type ShowFilter = "all" | "toGet" | "requested" | "notRetrieved" | "toDecide" | "included" | "excluded";

export const SHOW_FILTERS: readonly ShowFilter[] = ["all", "toGet", "requested", "notRetrieved", "toDecide", "included", "excluded"];

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
      default:
        return true;
    }
  });
}

export type ChartingKey =
  | "down" | "up" | "extendDown" | "extendUp" | "toggle" | "selectAll"
  | "toGet" | "requested" | "retrieved" | "notRetrieved"
  | "include" | "exclude" | "attach" | "open" | "undo" | "help" | "export";

const KEYMAP: Record<string, ChartingKey> = {
  j: "down", k: "up", x: "toggle", a: "selectAll",
  g: "toGet", q: "requested", r: "retrieved", n: "notRetrieved",
  i: "include", e: "exclude", p: "attach", o: "open", z: "undo", "?": "help",
};

export function isTextField(target: EventTarget | null): boolean {
  if (typeof HTMLElement === "undefined" || !(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "TEXTAREA" || tag === "SELECT" || (tag === "INPUT" && (target as HTMLInputElement).type !== "checkbox" && (target as HTMLInputElement).type !== "radio");
}

/**
 * The action of a key press, or null. Off in text fields; Ctrl+E (or Cmd+E) is
 * Export; Shift+J and Shift+K extend the selection. The keys L, C and D stay free
 * (Part F), and Enter belongs to the one-study view (Part B).
 */
export function chartingKey(event: Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "altKey" | "shiftKey">, target: EventTarget | null): ChartingKey | null {
  if (isTextField(target)) return null;
  const key = event.key.toLowerCase();
  if ((event.ctrlKey || event.metaKey) && !event.altKey && key === "e") return "export";
  if (event.ctrlKey || event.metaKey || event.altKey) return null;
  if (event.shiftKey && key === "j") return "extendDown";
  if (event.shiftKey && key === "k") return "extendUp";
  return KEYMAP[key] ?? KEYMAP[event.key] ?? null;
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
