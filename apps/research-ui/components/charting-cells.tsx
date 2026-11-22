"use client";

import { useEffect, useRef, useState, type ComponentType, type KeyboardEvent as ReactKeyboardEvent, type ReactNode, type SVGProps } from "react";
import { ArrowPathIcon, BeakerIcon, DocumentMinusIcon, EyeSlashIcon, MinusCircleIcon } from "@heroicons/react/24/outline";

import { formatNumber, type Locale } from "@/i18n";
import type { Cell, CellHistory, CellValue, ColumnType, FormColumn } from "@/lib/charting-api";
import { cc, type ChartingCopyKey } from "@/lib/charting-copy";
import type { CellDraft } from "@/lib/charting-logic";

/**
 * The charting cells (M12a Part B, spec 01 "Partial" and spec 02 "Partial"): a
 * cell's value in words, Not reported and Not applicable with an icon, a dash
 * whose accessible name says "Not charted", the "Chart again" mark with the
 * earlier value as history, and the editor a cell opens on Enter.
 * Nothing here judges a value: the engine does (`CHARTING_VALUE_INVALID`).
 */

type Icon = ComponentType<SVGProps<SVGSVGElement>>;

export const FOCUS_RING = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

export const TYPE_KEY: Record<ColumnType, ChartingCopyKey> = {
  text: "charting.type.text",
  one: "charting.type.one",
  several: "charting.type.several",
  yes_no: "charting.type.yesNo",
  number: "charting.type.number",
};

export const COLUMN_TYPES: readonly ColumnType[] = ["text", "one", "several", "yes_no", "number"];

/** A Yes/No option in the reader's language; the stored value stays the engine's "Yes" or "No". */
export function optionWords(locale: Locale, column: Pick<FormColumn, "type">, option: string): string {
  if (column.type === "yes_no" && option === "Yes") return cc(locale, "charting.cell.yes");
  if (column.type === "yes_no" && option === "No") return cc(locale, "charting.cell.no");
  return option;
}

/** A stored value as words (Latin numerals; the options of a "several" column joined). */
export function valueWords(locale: Locale, column: Pick<FormColumn, "type">, value: CellValue): string {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.map((v) => optionWords(locale, column, v)).join(", ");
  if (typeof value === "number") return formatNumber(locale, value);
  return optionWords(locale, column, value);
}

/** A cell as one line of words, for an accessible name or a phone card. */
export function cellWords(locale: Locale, column: Pick<FormColumn, "type">, cell: Pick<Cell, "state" | "value">): string {
  if (cell.state === "not_reported") return cc(locale, "charting.cell.notReported");
  if (cell.state === "not_applicable") return cc(locale, "charting.cell.notApplicable");
  if (cell.state === "value") return valueWords(locale, column, cell.value);
  return cc(locale, "charting.cell.notCharted");
}

/** A mark of words and an icon, never colour alone (spec 01 "Accessibility"). */
export function Mark({ icon: IconOf, tone, children, data }: Readonly<{ icon: Icon; tone: "neutral" | "unclear" | "brand"; children: ReactNode; data?: string }>) {
  const style = tone === "unclear" ? "bg-unclear-soft text-unclear" : tone === "brand" ? "bg-brand-soft text-brand" : "border border-rule bg-paper text-ink-muted";
  return (
    <span className={`inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-xs font-semibold leading-4 ${style}`} data-mark={data}>
      <IconOf aria-hidden="true" className="size-3.5 shrink-0" data-icon />
      <span>{children}</span>
    </span>
  );
}

export function NotReportedMark({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <Mark icon={EyeSlashIcon} tone="neutral" data="not-reported">
      {cc(locale, "charting.cell.notReported")}
    </Mark>
  );
}

export function NotApplicableMark({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <Mark icon={MinusCircleIcon} tone="neutral" data="not-applicable">
      {cc(locale, "charting.cell.notApplicable")}
    </Mark>
  );
}

export function ChartAgainMark({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <Mark icon={ArrowPathIcon} tone="unclear" data="chart-again">
      {cc(locale, "charting.cell.chartAgain")}
    </Mark>
  );
}

export function NoFullTextMark({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <Mark icon={DocumentMinusIcon} tone="neutral" data="no-full-text">
      {cc(locale, "charting.cell.noFullText")}
    </Mark>
  );
}

export function PilotMark({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <Mark icon={BeakerIcon} tone="brand" data="pilot">
      {cc(locale, "charting.pilot.label")}
    </Mark>
  );
}

/** One earlier value, as "Earlier value: …" or "Earlier value, in {column}: …" (read-only history). */
export function HistoryLine({ locale, column, entry }: Readonly<{ locale: Locale; column: Pick<FormColumn, "type">; entry: CellHistory }>) {
  const label = entry.column ? cc(locale, "charting.cell.historyIn", { column: entry.column }) : cc(locale, "charting.cell.history");
  return (
    <span className="text-xs text-ink-muted" data-history>
      {label}: <bdi>{cellWords(locale, entry.column ? { type: "text" } : column, entry)}</bdi>
    </span>
  );
}

/**
 * The earlier values a "Chart again" cell shows: a column made from others carries
 * one entry per source column at the end of its history (the engine adds them in
 * the order of `derived_from`), so all of them are shown; otherwise the newest one.
 */
export function chartAgainHistory(cell: Pick<Cell, "chart_again" | "history">): CellHistory[] {
  if (!cell.chart_again || cell.history.length === 0) return [];
  let start = cell.history.length;
  while (start > 0 && cell.history[start - 1].column) start -= 1;
  return start < cell.history.length ? cell.history.slice(start) : cell.history.slice(-1);
}

/** What a cell shows: the value, the two special values, or a dash read as "Not charted". */
export function CellView({ locale, column, cell }: Readonly<{ locale: Locale; column: FormColumn; cell: Cell }>) {
  const earlier = chartAgainHistory(cell).filter((entry) => cell.state === null || entry.state !== null);
  return (
    <span className="flex flex-col items-start gap-1">
      {cell.state === "not_reported" ? (
        <NotReportedMark locale={locale} />
      ) : cell.state === "not_applicable" ? (
        <NotApplicableMark locale={locale} />
      ) : cell.state === "value" ? (
        <bdi className="text-ink [overflow-wrap:anywhere]" data-value>
          {valueWords(locale, column, cell.value)}
        </bdi>
      ) : (
        <>
          <span aria-hidden="true" className="text-ink-muted" data-dash>
            —
          </span>
          <span className="sr-only">{cc(locale, "charting.cell.notCharted")}</span>
        </>
      )}
      {cell.chart_again ? <ChartAgainMark locale={locale} /> : null}
      {earlier.map((entry, i) => (
        <HistoryLine key={`${entry.event_id}-${i}`} locale={locale} column={column} entry={entry} />
      ))}
    </span>
  );
}

/**
 * The editor a cell opens on Enter (spec 01 "Keyboard"): Enter saves and the
 * focus moves down, Esc cancels, leaving the editor saves. A text or number cell is
 * one line; a list cell shows its options (radios for one, checkboxes for several).
 * Keys inside the editor stay here: the screen's own keys wait until it closes.
 */
export function CellEditor({
  locale,
  column,
  initial,
  label,
  onCommit,
  onCancel,
}: Readonly<{
  locale: Locale;
  column: FormColumn;
  initial: CellDraft;
  label: string;
  onCommit: (draft: CellDraft, how: "enter" | "blur") => void;
  onCancel: () => void;
}>) {
  const [draft, setDraft] = useState<CellDraft>(initial);
  const done = useRef(false);
  const box = useRef<HTMLDivElement>(null);
  const draftRef = useRef(draft);
  draftRef.current = draft;

  useEffect(() => {
    const first = box.current?.querySelector<HTMLElement>("input:checked, input");
    first?.focus();
    if (first instanceof HTMLInputElement && (first.type === "text" || first.type === "number")) first.select();
  }, []);

  function finish(how: "enter" | "blur" | "cancel") {
    if (done.current) return;
    done.current = true;
    if (how === "cancel") onCancel();
    else onCommit(draftRef.current, how);
  }

  function onKeyDown(event: ReactKeyboardEvent) {
    event.stopPropagation();
    if (event.key === "Escape") {
      event.preventDefault();
      finish("cancel");
    } else if (event.key === "Enter") {
      event.preventDefault();
      finish("enter");
    }
  }

  const listId = `cell-editor-${column.column_id}`;
  return (
    <div
      ref={box}
      onKeyDown={onKeyDown}
      onBlur={(event) => {
        if (!box.current?.contains(event.relatedTarget as Node | null)) finish("blur");
      }}
      className="min-w-40 rounded-md border border-brand bg-leaf p-1"
      data-cell-editor
    >
      {column.type === "text" || column.type === "number" ? (
        <input
          type="text"
          inputMode={column.type === "number" ? "decimal" : undefined}
          dir="auto"
          value={typeof draft === "string" ? draft : ""}
          aria-label={label}
          onChange={(event) => setDraft(event.target.value)}
          className={`min-h-11 w-full rounded-sm border border-rule-strong bg-leaf px-2 text-sm text-ink ${FOCUS_RING}`}
          data-editor-input
        />
      ) : (
        <fieldset className="space-y-1" aria-label={label}>
          {column.options.map((option) => {
            const several = column.type === "several";
            const chosen = several ? Array.isArray(draft) && draft.includes(option) : draft === option;
            return (
              <label key={option} className="flex min-h-11 items-center gap-2 px-1 text-sm text-ink">
                <input
                  type={several ? "checkbox" : "radio"}
                  name={listId}
                  checked={chosen}
                  onChange={() => {
                    if (several) {
                      const list = Array.isArray(draft) ? draft : [];
                      setDraft(list.includes(option) ? list.filter((o) => o !== option) : [...list, option]);
                    } else setDraft(option);
                  }}
                  className="size-4 accent-[var(--color-brand)]"
                  data-editor-option={option}
                />
                <bdi>{optionWords(locale, column, option)}</bdi>
              </label>
            );
          })}
        </fieldset>
      )}
      <p className="px-1 pt-1 text-xs text-ink-muted">{cc(locale, "charting.cell.editHint")}</p>
    </div>
  );
}
