"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { ArrowDownIcon, ArrowsPointingInIcon, ArrowUpIcon, PlusIcon, ScissorsIcon, TrashIcon, XMarkIcon } from "@heroicons/react/24/outline";

import type { Locale } from "@/i18n";
import { Button } from "@/components/ui/base";
import { isScreeningApiError } from "@/lib/screening-api";
import { localDate } from "@/lib/local-time";
import { putChartingForm, type Amendment, type ChartingForm, type ColumnType, type FormColumn } from "@/lib/charting-api";
import { cc, refusalWords, type ChartingCopyKey } from "@/lib/charting-copy";

import { COLUMN_TYPES, FOCUS_RING, TYPE_KEY } from "./charting-cells";

/**
 * The charting form panel (M12a Part B, spec 01 "Desktop layout"): about 360 px
 * beside the rows, a labelled complementary region. It edits the form that sits
 * beside the protocol (the protocol itself is never changed): columns with a name,
 * a definition, a type, options and "required"; add, remove, reorder, split one
 * column into two, merge two columns into one. Before any cell holds a value each change is saved at once;
 * after, the changes wait for one sentence ("Why does the form change?") and are
 * recorded as an amendment. The engine decides what an amendment is and which
 * cells must be charted again; this panel only sends the new columns.
 */

type Refusal = { code: string; message: string };

const CHANGE_KEY: Record<string, ChartingCopyKey> = {
  added: "charting.form.change.added",
  removed: "charting.form.change.removed",
  renamed: "charting.form.change.renamed",
  definition: "charting.form.change.definition",
  type: "charting.form.change.type",
  options_added: "charting.form.change.options_added",
  options_removed: "charting.form.change.options_removed",
  required: "charting.form.change.required",
  split: "charting.form.change.split",
  merged: "charting.form.change.merged",
  replaced: "charting.form.change.replaced",
  order: "charting.form.change.order",
};

/** The fields the engine accepts for a column, nothing else. */
function clean(columns: readonly FormColumn[]): FormColumn[] {
  return columns.map((c) => ({
    column_id: c.column_id,
    name: c.name,
    definition: c.definition ?? "",
    type: c.type,
    options: c.type === "one" || c.type === "several" ? [...c.options] : [],
    required: c.required,
    from_protocol: c.from_protocol ?? null,
    derived_from: [...(c.derived_from ?? [])],
  }));
}

function sameColumns(a: readonly FormColumn[], b: readonly FormColumn[]): boolean {
  return JSON.stringify(clean(a)) === JSON.stringify(clean(b));
}

/** A new column id the engine accepts (letters, digits, '-' and '_'). */
function newColumnId(): string {
  return `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

/** One amendment row as the spec's sentence: "Amended on {date} by {who}: {change}, from “…” to “…”." */
export function amendmentLine(locale: Locale, row: Amendment, names: ReadonlyMap<string, string>): string {
  const t = (key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values);
  const words = (value: unknown): string => {
    if (value === null || value === undefined || value === "") return t("charting.form.nothing");
    if (typeof value === "boolean") return value ? t("charting.cell.yes") : t("charting.cell.no");
    if (Array.isArray(value)) {
      const list = value.map((v) => (row.change === "order" ? names.get(String(v)) ?? String(v) : String(v)));
      return list.length ? list.join(", ") : t("charting.form.nothing");
    }
    if (row.change === "type" && typeof value === "string" && value in TYPE_KEY) return t(TYPE_KEY[value as ColumnType]);
    return String(value);
  };
  const word = t(CHANGE_KEY[row.change] ?? "charting.form.change.other");
  const column = row.column_id ? names.get(row.column_id) : undefined;
  const named = column && !["added", "removed", "renamed", "split", "merged", "replaced", "order"].includes(row.change) ? `${word} (${column})` : word;
  return t("charting.form.amended", { date: localDate(row.amended_at), who: row.amended_by, change: named, from: words(row.from), to: words(row.to) });
}

export function ChartingFormPanel({
  locale,
  origin,
  form,
  seenNames,
  readOnly,
  addOnOpen,
  onSaved,
  onEndPilot,
  onClose,
  onAnnounce,
  onReload,
  closeRef,
}: Readonly<{
  locale: Locale;
  origin: string;
  form: ChartingForm;
  /** Column names seen during this page load, kept by the page (the panel unmounts on close). */
  seenNames?: Map<string, string>;
  readOnly: boolean;
  /** Opened from "Add the first column": start with one new column. */
  addOnOpen: boolean;
  onSaved: (form: ChartingForm) => void;
  onEndPilot: () => void;
  onClose: () => void;
  onAnnounce: (words: string) => void;
  /** The form changed elsewhere (`CHARTING_FORM_STALE`): read the rows again. */
  onReload: () => void;
  closeRef?: RefObject<HTMLButtonElement | null>;
}>) {
  const t = useCallback((key: ChartingCopyKey, values?: Record<string, string | number>) => cc(locale, key, values), [locale]);
  const [draft, setDraft] = useState<FormColumn[]>(() => clean(form.columns));
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [needsReason, setNeedsReason] = useState(false);
  const [optionText, setOptionText] = useState<Record<string, string>>({});
  const [line, setLine] = useState("");
  /** The column whose "Merge with…" chooser is open, and the column chosen in it. */
  const [mergeFrom, setMergeFrom] = useState<string | null>(null);
  const [mergeTarget, setMergeTarget] = useState("");
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const formRef = useRef(form);
  formRef.current = form;
  const focusNext = useRef<string | null>(null);
  const reasonInput = useRef<HTMLInputElement>(null);

  const amend = form.has_values || needsReason;
  const dirty = !sameColumns(draft, form.columns);
  const nameMissing = draft.some((c) => !c.name.trim());

  // A newer form from the engine (a reload after CHARTING_FORM_STALE) replaces the
  // draft, unless the researcher has changes of their own against the earlier one.
  const previous = useRef(form);
  useEffect(() => {
    const before = previous.current;
    previous.current = form;
    if (before.version === form.version) return;
    setDraft((current) => (sameColumns(current, before.columns) ? clean(form.columns) : current));
  }, [form]);

  // Saves run one after another, each from the version the one before it answered.
  const queue = useRef<Promise<unknown>>(Promise.resolve());

  const saveNow = useCallback(
    async (given: FormColumn[] | null, withReason: string | null) => {
      if (readOnly) return;
      // A change saved at once sends the newest draft, so quick changes in a row are one save each, in order.
      const columns = given ?? draftRef.current;
      if (columns.some((c) => !c.name.trim())) {
        setLine(t("charting.form.needsName"));
        return;
      }
      if (sameColumns(columns, formRef.current.columns)) return;
      setSaving(true);
      setRefusal(null);
      setLine("");
      try {
        const sent = clean(columns);
        const answer = await putChartingForm(origin, { baseVersion: formRef.current.version, columns: sent, reason: withReason });
        formRef.current = answer;
        if (sameColumns(draftRef.current, sent)) {
          draftRef.current = clean(answer.columns);
          setDraft(draftRef.current);
        }
        setReason("");
        setNeedsReason(false);
        onSaved(answer);
        onAnnounce(withReason ? t("charting.form.recorded") : t("charting.form.saved"));
      } catch (error) {
        const code = isScreeningApiError(error) ? error.code : "ENGINE_UNREACHABLE";
        if (code === "CHARTING_AMENDMENT_REASON_REQUIRED") {
          setNeedsReason(true);
          setTimeout(() => reasonInput.current?.focus(), 0);
        }
        if (code === "CHARTING_FORM_STALE") onReload();
        setRefusal({ code, message: isScreeningApiError(error) ? error.serverMessage : "" });
      } finally {
        setSaving(false);
      }
    },
    [origin, readOnly, onSaved, onAnnounce, onReload, t],
  );

  const save = useCallback(
    (columns: FormColumn[] | null, withReason: string | null) => {
      const run = () => saveNow(columns, withReason);
      const next = queue.current.then(run, run);
      queue.current = next.catch(() => undefined);
      return next;
    },
    [saveNow],
  );

  /** A change: saved at once before any value exists, else kept for the amendment. */
  function change(next: FormColumn[], immediate: boolean) {
    draftRef.current = next;
    setDraft(next);
    setLine("");
    if (immediate && !amend) void save(null, null);
  }

  function update(index: number, patch: Partial<FormColumn>, immediate: boolean) {
    change(draftRef.current.map((c, i) => (i === index ? { ...c, ...patch } : c)), immediate);
  }

  function addColumn() {
    const column: FormColumn = {
      column_id: newColumnId(),
      name: t("charting.form.newColumn", { n: draftRef.current.length + 1 }),
      definition: "",
      type: "text",
      options: [],
      required: false,
      from_protocol: null,
      derived_from: [],
    };
    focusNext.current = column.column_id;
    change([...draftRef.current, column], true);
  }

  const added = useRef(false);
  useEffect(() => {
    if (!addOnOpen || added.current || readOnly) return;
    added.current = true;
    if (form.columns.length === 0) addColumn();
    // Only on opening.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [addOnOpen]);

  useEffect(() => {
    if (!focusNext.current) return;
    const id = focusNext.current;
    focusNext.current = null;
    document.querySelector<HTMLInputElement>(`[data-form-column="${id}"] [data-form-name]`)?.focus();
  }, [draft]);

  function move(index: number, delta: number) {
    const current = draftRef.current;
    const to = index + delta;
    if (to < 0 || to >= current.length) return;
    const next = [...current];
    [next[index], next[to]] = [next[to], next[index]];
    change(next, true);
  }

  function remove(index: number) {
    change(draftRef.current.filter((_, i) => i !== index), true);
  }

  function split(index: number) {
    const current = draftRef.current;
    const source = current[index];
    const parts = [1, 2].map((n) => ({
      ...source,
      column_id: newColumnId() + n,
      name: t("charting.form.splitName", { name: source.name, n }),
      from_protocol: null,
      derived_from: [source.column_id],
      options: [...source.options],
    }));
    focusNext.current = parts[0].column_id;
    change([...current.slice(0, index), ...parts, ...current.slice(index + 1)], true);
  }

  function openMerge(column: FormColumn) {
    const other = draftRef.current.find((c) => c.column_id !== column.column_id);
    if (!other) return;
    setMergeTarget(other.column_id);
    setMergeFrom(column.column_id);
  }

  function closeMerge(focusId: string | null) {
    setMergeFrom(null);
    if (focusId) setTimeout(() => document.querySelector<HTMLElement>(`[data-form-column="${focusId}"] [data-form-merge]`)?.focus(), 0);
  }

  // The chooser takes the focus when it opens.
  useEffect(() => {
    if (mergeFrom) document.querySelector<HTMLSelectElement>(`[data-form-column="${mergeFrom}"] [data-form-merge-target]`)?.focus();
  }, [mergeFrom]);

  /**
   * Two columns into one: a new Text column, at the place of the first, that names
   * both as its sources. The engine reads it as a merge (several columns into one)
   * and marks its cells "Chart again" with the earlier values. A source not yet in
   * the saved form (a draft waiting for its amendment) gives its own sources instead,
   * so a third column can be merged into a merge that is not recorded yet.
   */
  function merge(fromId: string, intoId: string) {
    const current = draftRef.current;
    const at = [fromId, intoId].map((id) => current.findIndex((c) => c.column_id === id)).sort((x, y) => x - y);
    if (at[0] < 0 || at[0] === at[1]) return;
    const [first, second] = [current[at[0]], current[at[1]]];
    const saved = new Set(formRef.current.columns.map((c) => c.column_id));
    const sources = (c: FormColumn) => (saved.has(c.column_id) ? [c.column_id] : (c.derived_from ?? []).filter((p) => saved.has(p)));
    const column: FormColumn = {
      column_id: newColumnId(),
      name: t("charting.form.mergeName", { a: first.name, b: second.name }).slice(0, 200),
      definition: [first.definition, second.definition].map((d) => (d ?? "").trim()).filter(Boolean).join("; ").slice(0, 2000),
      type: "text",
      options: [],
      required: first.required || second.required,
      from_protocol: null,
      derived_from: [...new Set([...sources(first), ...sources(second)])],
    };
    setMergeFrom(null);
    focusNext.current = column.column_id;
    change([...current.slice(0, at[0]), column, ...current.slice(at[0] + 1).filter((c) => c.column_id !== second.column_id)], true);
  }

  function setType(index: number, type: ColumnType) {
    const current = draftRef.current[index];
    const options = type === "one" || type === "several" ? (current.type === "one" || current.type === "several" ? current.options : []) : [];
    update(index, { type, options }, true);
  }

  function addOption(index: number) {
    const column = draftRef.current[index];
    const text = (optionText[column.column_id] ?? "").trim();
    if (!text || column.options.includes(text)) return;
    setOptionText({ ...optionText, [column.column_id]: "" });
    update(index, { options: [...column.options, text] }, true);
  }

  const names = useMemo(() => {
    const map = new Map<string, string>();
    for (const c of form.columns) {
      map.set(c.column_id, c.name);
      seenNames?.set(c.column_id, c.name);
    }
    // As the engine reads them: a split names its old column, a replacement its one
    // source, a merge each source in turn.
    for (const a of form.amendments) {
      const put = (id: unknown, name: unknown) => {
        if (typeof id === "string" && id && !map.has(id) && typeof name === "string") map.set(id, name);
      };
      if (a.change === "replaced" || a.change === "merged") {
        const from = Array.isArray(a.from) ? a.from : [a.from];
        (a.columns ?? []).forEach((id, i) => put(id, from[i]));
      } else put(a.column_id, a.from);
    }
    // Then the names the page saw earlier in this page load, for a split or merge
    // saved before any value (no amendment names its old columns then).
    for (const [id, name] of seenNames ?? []) if (!map.has(id)) map.set(id, name);
    return map;
  }, [form.columns, form.amendments, seenNames]);

  const groups = useMemo(() => {
    const out: { id: string; rows: Amendment[] }[] = [];
    for (const row of form.amendments) {
      const last = out[out.length - 1];
      if (last && last.id === row.amendment_id) last.rows.push(row);
      else out.push({ id: row.amendment_id, rows: [row] });
    }
    return out.reverse();
  }, [form.amendments]);

  const input = `min-h-11 w-full rounded-md border border-rule-strong bg-leaf px-2 text-sm text-ink disabled:opacity-60 ${FOCUS_RING}`;
  const locked = readOnly;

  return (
    <aside
      id="charting-form-panel"
      aria-labelledby="charting-form-title"
      className="w-full shrink-0 space-y-4 rounded-md border border-rule bg-leaf p-4 lg:max-h-[70vh] lg:w-[360px] lg:overflow-y-auto"
      data-form-panel
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 id="charting-form-title" className="font-semibold text-ink">
            {t("charting.form.title")}
          </h2>
          <p className="text-xs text-ink-muted">{t("charting.form.lede")}</p>
        </div>
        <Button ref={closeRef} variant="quiet" className="px-2" onClick={onClose} aria-label={t("charting.form.close")} data-form-close>
          <XMarkIcon aria-hidden="true" className="size-5" />
        </Button>
      </div>

      <section aria-labelledby="charting-pilot-title" className="space-y-2 rounded-md border border-rule p-3" data-form-pilot>
        <h3 id="charting-pilot-title" className="text-sm font-semibold text-ink">
          {t("charting.pilot.label")}
        </h3>
        {form.pilot.on ? (
          <>
            <p className="text-sm text-ink-muted">{t("charting.pilot.suggest")} {t("charting.pilot.on")}</p>
            <Button disabled={readOnly} onClick={onEndPilot} data-end-pilot>
              {t("charting.pilot.end")}
            </Button>
          </>
        ) : (
          <p className="text-sm text-ink" data-pilot-ended>
            {t("charting.pilot.ended", { date: localDate(form.pilot.ended_at) })}
          </p>
        )}
      </section>

      {refusal ? (
        <div role="alert" className="rounded-md bg-blocked-soft px-3 py-2 text-sm text-blocked" data-form-refusal={refusal.code}>
          <p>{refusalWords(locale, refusal.code)}</p>
          <details className="text-xs">
            <summary className={`min-h-11 cursor-pointer py-3 ${FOCUS_RING}`}>{t("charting.details")}</summary>
            <span className="font-mono" dir="ltr">
              {refusal.code}
            </span>
          </details>
        </div>
      ) : null}

      {draft.length === 0 ? <p className="text-sm text-ink" data-form-empty>{t("charting.form.empty")}</p> : null}

      <ol className="space-y-3">
        {draft.map((column, index) => {
          const nameId = `form-name-${column.column_id}`;
          const defId = `form-def-${column.column_id}`;
          const typeId = `form-type-${column.column_id}`;
          const optionId = `form-option-${column.column_id}`;
          const mergeId = `form-merge-${column.column_id}`;
          const parents = (column.derived_from ?? []).map((p) => names.get(p) ?? p);
          return (
            <li key={column.column_id} className="space-y-2 rounded-md border border-rule bg-paper p-3" data-form-column={column.column_id}>
              <p className="text-xs font-semibold text-ink-muted">{t("charting.form.column", { n: index + 1 })}</p>
              <div className="space-y-1">
                <label htmlFor={nameId} className="text-sm text-ink">
                  {t("charting.form.name")}
                </label>
                <input
                  id={nameId}
                  value={column.name}
                  maxLength={200}
                  disabled={locked}
                  dir="auto"
                  onChange={(event) => update(index, { name: event.target.value }, false)}
                  onBlur={() => {
                    if (!amend) void save(null, null);
                  }}
                  className={input}
                  data-form-name
                />
              </div>
              <div className="space-y-1">
                <label htmlFor={defId} className="text-sm text-ink">
                  {t("charting.form.definition")}
                </label>
                <textarea
                  id={defId}
                  value={column.definition}
                  maxLength={2000}
                  rows={2}
                  disabled={locked}
                  dir="auto"
                  onChange={(event) => update(index, { definition: event.target.value }, false)}
                  onBlur={() => {
                    if (!amend) void save(null, null);
                  }}
                  className={`${input} py-2`}
                  data-form-definition
                />
              </div>
              <div className="flex flex-wrap items-end gap-3">
                <div className="space-y-1">
                  <label htmlFor={typeId} className="text-sm text-ink">
                    {t("charting.form.type")}
                  </label>
                  <select
                    id={typeId}
                    value={column.type}
                    disabled={locked}
                    onChange={(event) => setType(index, event.target.value as ColumnType)}
                    className={input}
                    data-form-type
                  >
                    {COLUMN_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {t(TYPE_KEY[type])}
                      </option>
                    ))}
                  </select>
                </div>
                <label className="flex min-h-11 items-center gap-2 text-sm text-ink">
                  <input
                    type="checkbox"
                    checked={column.required}
                    disabled={locked}
                    onChange={(event) => update(index, { required: event.target.checked }, true)}
                    className="size-4 accent-[var(--color-brand)]"
                    data-form-required
                  />
                  {t("charting.form.required")}
                </label>
              </div>
              {column.type === "one" || column.type === "several" ? (
                <fieldset className="space-y-2">
                  <legend className="text-sm text-ink">{t("charting.form.options")}</legend>
                  <ul className="flex flex-wrap gap-1">
                    {column.options.map((option) => (
                      <li key={option} className="inline-flex items-center gap-1 rounded-sm border border-rule bg-leaf ps-2 text-sm text-ink" data-form-option={option}>
                        <bdi>{option}</bdi>
                        <button
                          type="button"
                          disabled={locked}
                          onClick={() => update(index, { options: column.options.filter((o) => o !== option) }, true)}
                          aria-label={t("charting.form.removeOption", { option })}
                          className={`inline-flex size-11 items-center justify-center text-ink-muted hover:text-ink ${FOCUS_RING}`}
                        >
                          <XMarkIcon aria-hidden="true" className="size-4" />
                        </button>
                      </li>
                    ))}
                  </ul>
                  <div className="flex items-end gap-2">
                    <label htmlFor={optionId} className="sr-only">
                      {t("charting.form.newOption")}
                    </label>
                    <input
                      id={optionId}
                      value={optionText[column.column_id] ?? ""}
                      maxLength={200}
                      disabled={locked}
                      dir="auto"
                      onChange={(event) => setOptionText({ ...optionText, [column.column_id]: event.target.value })}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          addOption(index);
                        }
                      }}
                      className={input}
                      data-form-new-option
                    />
                    <Button disabled={locked || !(optionText[column.column_id] ?? "").trim()} onClick={() => addOption(index)} className="shrink-0 px-3" data-form-add-option>
                      <PlusIcon aria-hidden="true" className="size-4" />
                      {t("charting.form.addOption")}
                    </Button>
                  </div>
                </fieldset>
              ) : column.type === "yes_no" ? (
                <p className="text-sm text-ink-muted">{t("charting.form.yesNoFixed")}</p>
              ) : null}
              {column.from_protocol ? (
                <p className="text-xs text-ink-muted">
                  <bdi>{t("charting.form.fromProtocol", { id: column.from_protocol })}</bdi>
                </p>
              ) : null}
              {parents.length ? <p className="text-xs text-ink-muted">{t("charting.form.derivedFrom", { names: parents.join(", ") })}</p> : null}
              <div className="flex flex-wrap gap-1">
                <Button variant="quiet" className="px-2 text-sm" disabled={locked || index === 0} onClick={() => move(index, -1)} data-form-up>
                  <ArrowUpIcon aria-hidden="true" className="size-4" />
                  {t("charting.form.moveUp")}
                </Button>
                <Button variant="quiet" className="px-2 text-sm" disabled={locked || index === draft.length - 1} onClick={() => move(index, 1)} data-form-down>
                  <ArrowDownIcon aria-hidden="true" className="size-4" />
                  {t("charting.form.moveDown")}
                </Button>
                <Button variant="quiet" className="px-2 text-sm" disabled={locked} onClick={() => split(index)} data-form-split>
                  <ScissorsIcon aria-hidden="true" className="size-4" />
                  {t("charting.form.split")}
                </Button>
                <Button
                  variant="quiet"
                  className="px-2 text-sm"
                  disabled={locked || draft.length < 2}
                  aria-expanded={mergeFrom === column.column_id}
                  aria-controls={mergeFrom === column.column_id ? mergeId : undefined}
                  onClick={() => (mergeFrom === column.column_id ? closeMerge(null) : openMerge(column))}
                  data-form-merge
                >
                  <ArrowsPointingInIcon aria-hidden="true" className="size-4" />
                  {t("charting.form.merge")}
                </Button>
                <Button variant="quiet" className="px-2 text-sm" disabled={locked} onClick={() => remove(index)} data-form-remove>
                  <TrashIcon aria-hidden="true" className="size-4" />
                  {t("charting.form.remove")}
                </Button>
              </div>
              {mergeFrom === column.column_id && !locked ? (
                <div
                  id={mergeId}
                  className="flex flex-wrap items-end gap-2 rounded-md border border-rule bg-leaf p-2"
                  onKeyDown={(event) => {
                    // Esc closes the chooser only, not the whole panel.
                    if (event.key === "Escape") {
                      event.stopPropagation();
                      event.preventDefault();
                      closeMerge(column.column_id);
                    }
                  }}
                  data-form-merge-chooser
                >
                  <div className="min-w-0 grow space-y-1">
                    <label htmlFor={`${mergeId}-target`} className="text-sm text-ink">
                      <bdi>{t("charting.form.mergeWith", { name: column.name })}</bdi>
                    </label>
                    <select
                      id={`${mergeId}-target`}
                      value={mergeTarget}
                      onChange={(event) => setMergeTarget(event.target.value)}
                      className={input}
                      data-form-merge-target
                    >
                      {draft.map((other, n) =>
                        other.column_id === column.column_id ? null : (
                          <option key={other.column_id} value={other.column_id}>
                            {other.name.trim() || t("charting.form.column", { n: n + 1 })}
                          </option>
                        ),
                      )}
                    </select>
                  </div>
                  <Button className="px-2 text-sm" disabled={!mergeTarget} onClick={() => merge(column.column_id, mergeTarget)} data-form-merge-confirm>
                    {t("charting.form.mergeConfirm")}
                  </Button>
                  <Button variant="quiet" className="px-2 text-sm" onClick={() => closeMerge(column.column_id)} data-form-merge-cancel>
                    {t("charting.form.mergeCancel")}
                  </Button>
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>

      <Button disabled={locked} onClick={addColumn} data-form-add>
        <PlusIcon aria-hidden="true" className="size-4" />
        {t("charting.form.addColumn")}
      </Button>

      {line ? (
        <p className="text-sm text-blocked" data-form-line>
          {line}
        </p>
      ) : null}

      {amend && dirty && !readOnly ? (
        <form
          className="space-y-2 rounded-md border border-dashed border-brand bg-brand-soft p-3"
          aria-live="polite"
          onSubmit={(event) => {
            event.preventDefault();
            const sentence = reason.trim();
            if (!sentence) {
              setRefusal({ code: "CHARTING_AMENDMENT_REASON_REQUIRED", message: "" });
              reasonInput.current?.focus();
              return;
            }
            void save(draftRef.current, sentence);
          }}
          data-amendment-prompt
        >
          <p className="text-sm text-ink">{t("charting.form.pending")}</p>
          <label htmlFor="charting-amendment-reason" className="text-sm font-medium text-ink">
            {t("charting.form.reasonLabel")}
          </label>
          <input
            id="charting-amendment-reason"
            ref={reasonInput}
            value={reason}
            maxLength={500}
            dir="auto"
            onChange={(event) => setReason(event.target.value)}
            className={input}
            data-amendment-reason
          />
          <div className="flex flex-wrap gap-2">
            <Button type="submit" variant="primary" disabled={saving || nameMissing} data-record-amendment>
              {t("charting.form.record")}
            </Button>
            <Button
              variant="quiet"
              onClick={() => {
                setDraft(clean(form.columns));
                setReason("");
                setRefusal(null);
              }}
              data-discard-amendment
            >
              {t("charting.form.discard")}
            </Button>
          </div>
        </form>
      ) : null}

      <section aria-labelledby="charting-amendments-title" className="space-y-2" data-amendments>
        <h3 id="charting-amendments-title" className="text-sm font-semibold text-ink">
          {t("charting.form.amendments")}
        </h3>
        {groups.length === 0 ? (
          <p className="text-sm text-ink-muted">{t("charting.form.noAmendments")}</p>
        ) : (
          <ul className="space-y-2">
            {groups.map((group) => (
              <li key={group.id} className="space-y-1 text-sm text-ink" data-amendment={group.id}>
                {group.rows.map((row, i) => (
                  <p key={`${group.id}-${i}`} data-amendment-line>
                    <bdi>{amendmentLine(locale, row, names)}</bdi>
                  </p>
                ))}
                <p className="text-xs text-ink-muted">
                  <bdi>{t("charting.form.amendedReason", { reason: group.rows[0].reason })}</bdi>
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </aside>
  );
}
