"use client";

import { useId, useLayoutEffect, useRef, useState } from "react";
import { ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/outline";

import type { Locale } from "@/i18n";
import { Hint } from "@/components/ui/guidance";

/**
 * The databases to ask, ticked and ordered (M10a, decided 2026-11-14; spec 02
 * Explore, specs 01 Plan and 03 Harvest of Discovery). Shared by Explore and
 * Discovery; it decides nothing: the caller passes every database, the chosen
 * ids in order and every string, and disables its own action when none is
 * chosen.
 *
 * One row per database: a checkbox, then "Move up" and "Move down" as real
 * buttons (no drag-only path). The chosen databases come first in their order,
 * with their position in text, then the others in list order. Ticking appends
 * to the end of the order. After a move, focus stays on the same button of the
 * moved row (or its other move button once the row reached an end), and a
 * polite live region announces the new position. Up and down are vertical, so
 * their icons are never mirrored.
 */

export interface PickerItem {
  id: string;
  label: string;
  note?: string;
}

export interface PickerLabels {
  legend: string;
  orderHelp?: string;
  /** M10d (03-guidance rule 1): with a locale and the catalog key, the help about the sequence is a hint beside the legend. */
  orderHelpHint?: { locale: Locale; textKey: string };
  check(name: string): string;
  up(name: string): string;
  down(name: string): string;
  moved(name: string, position: number, total: number): string;
  none: string;
}

type Move = "up" | "down";

export function DatabasePicker({
  items,
  value,
  onChange,
  disabled = false,
  labels,
}: Readonly<{ items: PickerItem[]; value: string[]; onChange: (next: string[]) => void; disabled?: boolean; labels: PickerLabels }>) {
  const id = useId();
  const [announcement, setAnnouncement] = useState("");
  const buttons = useRef(new Map<string, HTMLButtonElement | null>());
  const pending = useRef<{ id: string; move: Move } | null>(null);

  const known = new Map(items.map((item) => [item.id, item]));
  const selected = value.filter((v) => known.has(v));
  const rows = [...selected.map((v) => known.get(v)!), ...items.filter((item) => !selected.includes(item.id))];

  // The moved row is the same element, re-keyed by its id; React may still move
  // it in the document, so focus is put back where the key press left it.
  useLayoutEffect(() => {
    const target = pending.current;
    if (!target) return;
    pending.current = null;
    const same = buttons.current.get(`${target.id}:${target.move}`);
    const other = buttons.current.get(`${target.id}:${target.move === "up" ? "down" : "up"}`);
    (same && !same.disabled ? same : other && !other.disabled ? other : same)?.focus();
  }, [value]);

  const toggle = (item: PickerItem) => {
    onChange(selected.includes(item.id) ? selected.filter((v) => v !== item.id) : [...selected, item.id]);
  };

  const move = (item: PickerItem, direction: Move) => {
    const from = selected.indexOf(item.id);
    const to = direction === "up" ? from - 1 : from + 1;
    if (from < 0 || to < 0 || to >= selected.length) return;
    const next = [...selected];
    [next[from], next[to]] = [next[to], next[from]];
    pending.current = { id: item.id, move: direction };
    setAnnouncement(labels.moved(item.label, to + 1, next.length));
    onChange(next);
  };

  const helpId = `${id}-help`;
  const noneId = `${id}-none`;
  const describedBy = [labels.orderHelp ? helpId : "", selected.length === 0 ? noneId : ""].filter(Boolean).join(" ") || undefined;

  return (
    <fieldset className="min-w-0" disabled={disabled} aria-labelledby={`${id}-legend`} aria-describedby={describedBy} data-picker>
      <legend className="text-sm text-ink-muted">
        <span id={`${id}-legend`}>{labels.legend}</span>
        {labels.orderHelp && labels.orderHelpHint ? (
          <Hint locale={labels.orderHelpHint.locale} label={labels.legend} text={labels.orderHelp} textKey={labels.orderHelpHint.textKey} id={helpId} className="ms-1" />
        ) : null}
      </legend>
      {labels.orderHelp && !labels.orderHelpHint ? (
        <p id={helpId} className="text-xs text-ink-muted">
          {labels.orderHelp}
        </p>
      ) : null}
      <ul className="mt-2 space-y-1">
        {rows.map((item) => {
          const position = selected.indexOf(item.id);
          const on = position >= 0;
          // A row's note (for example how that database reads the query) describes its checkbox.
          const noteId = item.note ? `${id}-note-${item.id}` : undefined;
          const button = (direction: Move) => {
            const blocked = !on || (direction === "up" ? position === 0 : position === selected.length - 1);
            const Icon = direction === "up" ? ChevronUpIcon : ChevronDownIcon;
            return (
              <button
                type="button"
                ref={(el) => {
                  buttons.current.set(`${item.id}:${direction}`, el);
                }}
                disabled={disabled || blocked}
                aria-label={direction === "up" ? labels.up(item.label) : labels.down(item.label)}
                onClick={() => move(item, direction)}
                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-rule-strong bg-leaf text-ink hover:bg-leaf-raised disabled:cursor-not-allowed disabled:opacity-40"
                data-move={direction}
              >
                <Icon aria-hidden="true" className="h-5 w-5" />
              </button>
            );
          };
          return (
            <li key={item.id} className="flex min-h-11 flex-wrap items-center gap-x-3 gap-y-1" data-picker-row={item.id} data-selected={on ? "true" : "false"}>
              <span className="w-6 shrink-0 text-center text-sm text-ink-muted" dir="ltr">
                {on ? <span data-position>{String(position + 1)}</span> : null}
              </span>
              <label className="inline-flex min-h-11 min-w-0 flex-1 cursor-pointer items-center gap-2 text-sm text-ink">
                <input type="checkbox" className="h-5 w-5 shrink-0" checked={on} onChange={() => toggle(item)} aria-label={labels.check(item.label)} aria-describedby={noteId} />
                <span className="min-w-0">
                  <span className="block">{item.label}</span>
                  {item.note ? (
                    <span id={noteId} className="block text-xs text-ink-muted">
                      {item.note}
                    </span>
                  ) : null}
                </span>
              </label>
              <span className="flex gap-2">
                {button("up")}
                {button("down")}
              </span>
            </li>
          );
        })}
      </ul>
      {selected.length === 0 ? (
        <p id={noneId} role="alert" className="mt-2 text-sm text-unclear" data-picker-none>
          {labels.none}
        </p>
      ) : null}
      <p role="status" aria-live="polite" className="sr-only" data-picker-status>
        {announcement}
      </p>
    </fieldset>
  );
}
