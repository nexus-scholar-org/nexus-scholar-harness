"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge, Hint } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { StepAssist } from "@/components/inception-assist";

import {
  runStep,
  type AcceptedFrom,
  type CriteriaStep,
  type Criterion,
  type Draft,
  type MatrixColumnIn,
  type MatrixStep,
  type MethodBlinding,
  type MethodNotReported,
  type ReasonSuggestion,
} from "@/lib/inception-api";
import { getConcepts, getRecon, hasUsablePool, type ConceptReport, type ReconState } from "@/lib/recon-api";
import { QueryWorkbench, type WorkbenchUse } from "@/components/query-workbench";
import { inceptionCountT, inceptionT, sourceText } from "@/lib/inception-copy";
import { workbenchT } from "@/lib/workbench-copy";

/**
 * Step 5, Concepts and criteria (spec 05, M4b; INC-22). Every criterion comes
 * from `POST /steps/criteria` with its id, its verbatim text, its source and its
 * status; the screen only records the researcher's Accept or Reject in
 * `criteria_decisions`. A criterion the wizard wrote stays "waiting" (default
 * no) until accepted; one the researcher typed is accepted unless rejected.
 *
 * With a pool (M4d), each concept shows how many pool papers each of its terms
 * occurs in and the engine's co-occurring pool terms as unticked boxes; a tick
 * only adds the term to that concept's synonyms in the page, saved with it.
 */

/**
 * M10b (`05-criteria`): a reason code as the researcher types it. Lower case
 * becomes upper case and a space becomes `_`; any other character outside
 * `A-Z 0-9 _` is not entered. This shapes the typing only: whether a code is
 * valid is the engine's answer (`DRAFT_INVALID` on save).
 */
export function normaliseReason(text: string): { value: string; refused: boolean } {
  const upper = text.toUpperCase().replace(/ /g, "_");
  const value = upper.replace(/[^A-Z0-9_]/g, "");
  return { value, refused: value !== upper };
}

/** The engine's own rule, repeated only to keep Add disabled until a code has its shape. */
const REASON_SHAPE = /^[A-Z][A-Z0-9_]{2,39}$/;

const MATRIX_TYPES = ["free_text", "numeric", "categorical", "list"] as const;

/**
 * M10b (01-proposals, R1): the engine suggestions accepted on this page, sent
 * with the save that writes them as `accepted_from`. Only what is still in the
 * saved answers, exactly as offered, is sent; an edited value never is (the
 * engine records only what its mechanism offered for the stored draft).
 */
function stillAccepted(entry: AcceptedFrom, draft: Draft): boolean {
  const value = entry.value;
  if (entry.mechanism === "wizard_criterion") return draft.criteria_decisions?.[String(value)] === true;
  if (entry.mechanism === "suggested_concept") return (draft.concepts ?? []).some((c) => c.concept === value);
  if (entry.mechanism === "matrix_column") return (draft.matrix_columns ?? []).includes(String(value));
  if (entry.mechanism === "pool_synonym") {
    const concept = entry.field.slice("concepts[".length, -"].synonyms".length);
    return (draft.concepts ?? []).some((c) => c.concept === concept && (c.synonyms ?? []).includes(String(value)));
  }
  return false;
}

const sameEntry = (a: AcceptedFrom, b: AcceptedFrom) => a.mechanism === b.mechanism && a.field === b.field && JSON.stringify(a.value) === JSON.stringify(b.value);

export function InceptionCriteria({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const state = useDraft();
  const { draft, setDraft, update, save, saving, saveError, origin, draftId, record } = state;
  const [criteria, setCriteria] = useState<CriteriaStep | null>(null);
  const [matrix, setMatrix] = useState<MatrixStep | null>(null);
  const [suggested, setSuggested] = useState<string[]>([]);
  const [stepError, setStepError] = useState<Refusal | null>(null);
  const [newInclusion, setNewInclusion] = useState("");
  const [newExclusion, setNewExclusion] = useState("");
  const [recon, setRecon] = useState<ReconState | null>(null);
  const [report, setReport] = useState<ConceptReport | null>(null);
  // M11a (10-query-workbench): the workbench's unused edits, and the page's prompt before leaving them.
  const [workbenchDirty, setWorkbenchDirty] = useState(false);
  const [leaving, setLeaving] = useState<"review" | "" | null>(null);
  const useVersion = useRef<() => Promise<boolean>>(async () => false);
  const bindUse = useCallback((fn: () => Promise<boolean>) => {
    useVersion.current = fn;
  }, []);
  const [newExclusionReason, setNewExclusionReason] = useState("");
  const [reasonEditing, setReasonEditing] = useState<string | null>(null);
  const [accepted, setAccepted] = useState<AcceptedFrom[]>([]);
  // M11b part D (spec 11): the out-of-scope field as typed, until Add puts it in the page's draft.
  const [oosText, setOosText] = useState<string | null>(null);
  const [oosAnnounce, setOosAnnounce] = useState("");
  const mark = (entry: AcceptedFrom, on: boolean) =>
    setAccepted((list) => (on ? [...list.filter((e) => !sameEntry(e, entry)), entry] : list.filter((e) => !sameEntry(e, entry))));

  // The counts describe the saved draft: read once per stored version.
  useEffect(() => {
    if (!record) return;
    const controller = new AbortController();
    getRecon(origin, record.session_id, controller.signal).then(
      (read) => {
        setRecon(read);
        if (!hasUsablePool(read)) return setReport(null);
        getConcepts(origin, record.session_id, controller.signal).then(setReport, () => setReport(null));
      },
      () => {
        setRecon(null);
        setReport(null);
      },
    );
    return () => controller.abort();
  }, [origin, record]);

  useEffect(() => {
    if (!record) return;
    const controller = new AbortController();
    runStep(origin, "scope", { topic: record.draft.topic ?? "" }, controller.signal).then(
      (answer) => setSuggested(answer.default_concepts),
      () => setSuggested([]),
    );
    return () => controller.abort();
  }, [origin, record]);

  // The criteria and matrix follow every answer they are drafted from.
  const key = JSON.stringify([
    draft.paradigm, draft.playbook, draft.proof, draft.unit_of_analysis, draft.out_of_scope, draft.extra_inclusions,
    draft.extra_exclusions, draft.criteria_decisions, draft.matrix_columns, draft.out_of_scope_reasons,
    draft.default_exclusion_reason, draft.custom_matrix_columns, draft.method_blinding, draft.method_not_reported,
  ]);
  useEffect(() => {
    if (!record) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const ask: Draft = { ...draft, concepts: [] };
      runStep(origin, "criteria", ask, controller.signal).then(
        (answer) => {
          setCriteria(answer);
          setStepError(null);
        },
        (error) => {
          if (!controller.signal.aborted) setStepError(refusalOf(error));
        },
      );
      if (draft.playbook) {
        runStep(origin, "matrix", ask, controller.signal).then(setMatrix, () => setMatrix(null));
      }
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
    // `key` lists exactly what the two steps read.
  }, [origin, record, key]);

  const decide = (item: Criterion, yes: boolean) => {
    setDraft((current) => ({ ...current, criteria_decisions: { ...(current.criteria_decisions ?? {}), [item.id]: yes } }));
    if (item.generated) mark({ mechanism: "wizard_criterion", field: "criteria_decisions", value: item.id }, yes);
  };

  const removeManual = (item: Criterion) => {
    if (item.kind === "inclusion") update({ extra_inclusions: (draft.extra_inclusions ?? []).filter((c) => c !== item.criterion) });
    else update({ extra_exclusions: (draft.extra_exclusions ?? []).filter((c) => c.criterion !== item.criterion) });
  };

  const concepts = draft.concepts ?? [];
  const wt = workbenchT(locale);

  /** "Use this version" (M11a): the concepts and seeds go through the normal save (D7), with the suggestions taken. */
  const useWorkbench = async (use: WorkbenchUse): Promise<boolean> => {
    const body = { ...draft, concepts: use.concepts, golden_seeds: use.seeds };
    const stored = await save(body, [...accepted.filter((entry) => stillAccepted(entry, body)), ...use.accepted.filter((entry) => stillAccepted(entry, body))]);
    if (stored) setAccepted([]);
    return stored;
  };

  const persist = async (next: "review" | "", leave = false) => {
    if (workbenchDirty && !leave) return setLeaving(next);
    setLeaving(null);
    const cleaned = concepts.filter((c) => c.concept.trim()).map((c) => ({ concept: c.concept.trim(), synonyms: c.synonyms ?? [] }));
    // M11b part D: a save writes the visibility the screen shows, even for a draft that never stored it.
    const shown = draft.method_blinding ?? criteria?.method?.blinding ?? null;
    const body = { ...draft, concepts: cleaned, ...(shown ? { method_blinding: shown } : {}) };
    const stored = await save(body, accepted.filter((entry) => stillAccepted(entry, body)));
    if (stored) setAccepted([]);
    if (stored) window.location.assign(inceptionHref(locale, next, next ? draftId : "", origin));
  };

  /** Writes a new reason where the criterion's source keeps it (M10b). */
  const setReason = (item: Criterion, code: string) => {
    if (item.source === "manual") {
      update({ extra_exclusions: (draft.extra_exclusions ?? []).map((e) => (e.criterion === item.criterion ? { ...e, reason_category: code } : e)) });
    } else if (item.source === "out_of_scope") {
      update({ out_of_scope_reasons: { ...(draft.out_of_scope_reasons ?? {}), [item.criterion]: code } });
    } else if (item.source === "paradigm_default") {
      update({ default_exclusion_reason: code });
    }
    setReasonEditing(null);
  };

  const undecided = criteria?.undecided.length ?? 0;
  const paradigm = draft.paradigm ?? "";
  // M11b part D: the engine says whether the rule is chosen (answer 8: no default); the browser decides nothing.
  const ruleUnchosen = criteria?.method?.chosen === false;
  const waits = undecided > 0 || (criteria?.missing_sides.length ?? 0) > 0;
  const acceptedOn = (kind: "inclusion" | "exclusion") => (criteria?.criteria ?? []).filter((c) => c.kind === kind && c.status === "accepted").length;
  const oosValue = oosText ?? (draft.out_of_scope ?? []).join("\n");
  const addOutOfScope = () => {
    // Semicolons and line breaks separate items; commas do not (05).
    const items = oosValue.split(/[\n;]/).map((item) => item.trim()).filter(Boolean);
    const before = new Set(draft.out_of_scope ?? []);
    update({ out_of_scope: items });
    setOosText(null);
    setOosAnnounce(t("criteria.oos.announce", { n: formatNumber(locale, items.filter((item) => !before.has(item)).length) }));
  };

  const renderSide = (kind: "inclusion" | "exclusion") => {
    const items = (criteria?.criteria ?? []).filter((c) => c.kind === kind);
    const prefix = kind === "inclusion" ? "I" : "E";
    const value = kind === "inclusion" ? newInclusion : newExclusion;
    const setValue = kind === "inclusion" ? setNewInclusion : setNewExclusion;
    // M10b: an exclusion is added only with a reason, so OUT_OF_SCOPE is never applied silently.
    const reasonReady = kind === "inclusion" || REASON_SHAPE.test(newExclusionReason);
    const add = () => {
      const text = value.trim();
      if (!text || !reasonReady) return;
      if (kind === "inclusion") update({ extra_inclusions: [...(draft.extra_inclusions ?? []), text] });
      else {
        update({ extra_exclusions: [...(draft.extra_exclusions ?? []), { criterion: text, reason_category: newExclusionReason }] });
        setNewExclusionReason("");
      }
      setValue("");
    };
    return (
      <section aria-labelledby={`criteria-${kind}`} className="rounded-lg border border-rule bg-leaf p-4" data-side={kind}>
        <div className="flex items-center gap-1">
          <h2 id={`criteria-${kind}`} className="font-semibold text-ink">
            {t(kind === "inclusion" ? "criteria.inclusion" : "criteria.exclusion")}
          </h2>
          {/* M10d (03-guidance I-C14, rule 1.6): one hint on the list heading, not one per criterion. */}
          {items.some((c) => c.generated) ? (
            <Hint locale={locale} label={t(kind === "inclusion" ? "criteria.inclusion" : "criteria.exclusion")} text={t("criteria.editHint")} textKey="criteria.editHint" />
          ) : null}
        </div>
        <p className="text-xs text-ink-muted" data-side-count>
          {t("criteria.sideCount", { accepted: formatNumber(locale, items.filter((c) => c.status === "accepted").length), total: formatNumber(locale, items.length) })}
        </p>
        <ol className="mt-3 space-y-3">
          {items.map((item, index) => {
            const label = `${prefix}${formatNumber(locale, index + 1)}`;
            const role = item.status === "accepted" ? "include" : item.status === "rejected" ? "exclude" : "unclear";
            const statusKey = item.status === "accepted" ? "criteria.accepted" : item.status === "rejected" ? "criteria.rejected" : "criteria.undecided";
            return (
              <li key={item.id} className="rounded-md border border-rule bg-paper p-3" data-criterion={item.id} data-status={item.status} data-generated={item.generated}>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-mono text-ink-muted">{label}</span>
                  {item.reason_category ? (
                    <span className="font-mono text-ink-muted" dir="ltr" data-reason={item.reason_category}>
                      {t("criteria.reason.row", { code: item.reason_category })}
                    </span>
                  ) : null}
                  <span className="text-ink-muted">{sourceText(locale, item.source, paradigm, item.source_label)}</span>
                  <DecisionBadge role={role}>{t(statusKey)}</DecisionBadge>
                </div>
                <p className="mt-2 text-ink" dir="ltr" data-verbatim>
                  {item.criterion}
                </p>
                <div role="group" aria-label={t("criteria.decision", { id: label })} className="mt-2 flex flex-wrap gap-2">
                  <Button aria-pressed={item.status === "accepted"} onClick={() => decide(item, true)} data-accept>
                    {t("criteria.accept")}
                  </Button>
                  <Button aria-pressed={item.status === "rejected"} onClick={() => decide(item, false)} data-reject>
                    {t("criteria.reject")}
                  </Button>
                  {item.source === "manual" ? (
                    <Button variant="quiet" onClick={() => removeManual(item)}>
                      {t("criteria.remove")}
                    </Button>
                  ) : null}
                </div>
                {kind === "exclusion" ? (
                  <ReasonControl
                    locale={locale}
                    item={item}
                    label={label}
                    suggestions={criteria?.reason_suggestions ?? []}
                    open={reasonEditing === item.id}
                    onOpen={() => setReasonEditing(item.id)}
                    onCancel={() => setReasonEditing(null)}
                    onChoose={(code) => setReason(item, code)}
                  />
                ) : null}
              </li>
            );
          })}
        </ol>
        {criteria?.missing_sides.includes(kind) ? (
          <p className="mt-3 text-sm text-unclear" data-missing-side={kind}>
            {t(kind === "inclusion" ? "criteria.missingSide.inclusion" : "criteria.missingSide.exclusion")}
          </p>
        ) : null}
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1">
            <label htmlFor={`criteria-new-${kind}`} className="block text-sm text-ink">
              {t(kind === "inclusion" ? "criteria.addInclusion" : "criteria.addExclusion")}
            </label>
            <input
              id={`criteria-new-${kind}`}
              value={value}
              onChange={(event) => setValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  add();
                }
              }}
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
          </div>
          {kind === "exclusion" ? (
            <ReasonInput
              locale={locale}
              id="criteria-new-exclusion-reason"
              value={newExclusionReason}
              onChange={setNewExclusionReason}
              suggestions={criteria?.reason_suggestions ?? []}
            />
          ) : null}
          <Button onClick={add} disabled={!value.trim() || !reasonReady} aria-describedby={kind === "exclusion" && !reasonReady ? "criteria-choose-reason" : undefined}>
            {t("criteria.add")}
          </Button>
        </div>
        {kind === "exclusion" && value.trim() && !reasonReady ? (
          <p id="criteria-choose-reason" className="mt-1 text-xs text-ink-muted" data-choose-reason>
            {t("criteria.reason.choose")}
          </p>
        ) : null}
      </section>
    );
  };

  return (
    <InceptionFrame locale={locale} current="criteria" draft={state}>
      <StepHeader
        kicker={t("criteria.kicker")}
        title={t("criteria.title")}
        lede={t("criteria.lede")}
        extra={
          criteria ? (
            <p className="mt-2 text-ink" aria-live="polite" data-need-you={undecided}>
              {undecided > 0 ? inceptionCountT(locale)("criteria.needYou", undecided, { n: formatNumber(locale, undecided) }) : t("criteria.allDecided")}
            </p>
          ) : null
        }
      />
      <form
        className="space-y-6"
        onSubmit={(event) => {
          event.preventDefault();
          void persist("review");
        }}
      >
        {record ? (
          <QueryWorkbench
            key={record.session_id}
            locale={locale}
            origin={origin}
            place={{ kind: "draft", id: record.session_id }}
            saved={(record.draft.concepts ?? []).map((c) => ({ concept: c.concept, synonyms: c.synonyms ?? [] }))}
            startYear={draft.start_year ?? null}
            endYear={draft.end_year ?? null}
            languages={draft.languages}
            seeds={record.draft.golden_seeds ?? []}
            providers={recon?.session?.latest?.providers ?? null}
            pool={report}
            editableSeeds
            topicConcepts={suggested}
            onDirty={setWorkbenchDirty}
            onCounted={state.bumpAssist}
            onUse={useWorkbench}
            using={saving}
            bindUse={bindUse}
          />
        ) : null}
        {recon && !hasUsablePool(recon) ? (
          <p className="text-sm text-ink-muted" data-no-pool>
            {t("criteria.synonyms.noPool")}{" "}
            <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)}>
              {t("criteria.synonyms.goExplore")}
            </a>
          </p>
        ) : null}
        {recon?.scope_changed && report ? (
          <p className="text-sm text-unclear" data-scope-changed>
            {t("criteria.anchor.scopeChanged")}{" "}
            <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)}>
              {t("criteria.synonyms.goExplore")}
            </a>
          </p>
        ) : null}

        {criteria ? (
          <section aria-labelledby="criteria-block-title" className="space-y-4 rounded-lg border border-rule p-4" data-criteria-block>
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h2 id="criteria-block-title" className="font-semibold text-ink">
                {t("criteria.block.title")}
              </h2>
              <span className="text-sm text-ink-muted" data-criteria-written={waits ? "waiting" : "written"}>
                {waits
                  ? t("criteria.block.cannotWrite")
                  : t("criteria.block.written", { inclusions: formatNumber(locale, acceptedOn("inclusion")), exclusions: formatNumber(locale, acceptedOn("exclusion")) })}
              </span>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              {renderSide("inclusion")}
              {renderSide("exclusion")}
            </div>
            <div data-oos-question>
              <label htmlFor="criteria-oos" className="block text-sm font-medium text-ink">
                {t("criteria.oos.question")}
              </label>
              <p id="criteria-oos-help" className="text-xs text-ink-muted">
                {t("criteria.oos.help")}
              </p>
              <textarea
                id="criteria-oos"
                rows={3}
                dir="auto"
                value={oosValue}
                onChange={(event) => setOosText(event.target.value)}
                aria-describedby="criteria-oos-help"
                className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
              />
              <div className="mt-2">
                <Button onClick={addOutOfScope} disabled={oosText === null} data-oos-add>
                  {t("criteria.oos.add")}
                </Button>
              </div>
              <p className="sr-only" role="status" aria-live="polite">
                {oosAnnounce}
              </p>
            </div>
            {criteria.criteria.length > 0 ? (
              <p className="text-sm text-ink-muted" data-criteria-limits>
                {t("criteria.block.limits")}
              </p>
            ) : null}
            <MethodQuestions
              locale={locale}
              blinding={draft.method_blinding ?? criteria.method?.blinding ?? null}
              notReported={draft.method_not_reported ?? null}
              options={criteria.method_options ?? null}
              unchosen={ruleUnchosen}
              older={Boolean(criteria.method?.started_before_question) && ruleUnchosen}
              fromImport={(record?.origin?.report.carried ?? []).some((c) => c.field === "method_not_reported")}
              onBlinding={(value) => update({ method_blinding: value })}
              onNotReported={(value) => update({ method_not_reported: value })}
            />
          </section>
        ) : !stepError ? (
          <p role="status" className="text-ink-muted">
            {t("asking")}
          </p>
        ) : null}

        {matrix ? (
          <fieldset className="rounded-lg border border-rule bg-leaf p-4" aria-labelledby="criteria-matrix-legend" data-matrix>
            <legend className="px-1 font-semibold text-ink">
              <span id="criteria-matrix-legend">{t("criteria.matrix")}</span>
              <Hint locale={locale} label={t("criteria.matrix")} text={t("criteria.matrixHelp")} textKey="criteria.matrixHelp" className="ms-1" />
            </legend>
            <p className="mt-1 text-xs text-ink-muted" data-charting-note>
              {t("criteria.matrixCharting")}
            </p>
            <div className="mt-2">
              <Button
                onClick={() => {
                  update({ matrix_columns: matrix.columns.map((c) => c.name) });
                  for (const c of matrix.columns) if (!(draft.matrix_columns ?? []).includes(c.name)) mark({ mechanism: "matrix_column", field: "matrix_columns", value: c.name }, true);
                }}
                data-tick-all
              >
                {t("criteria.tickAll")}
              </Button>
            </div>
            <div className="mt-2 space-y-2">
              <p className="text-xs font-semibold text-ink-muted">{t("criteria.mine.suggestedTitle")}</p>
              {matrix.columns.map((column) => {
                const checked = (draft.matrix_columns ?? []).includes(column.name);
                return (
                  <label key={column.name} className="flex min-h-11 cursor-pointer items-start gap-3">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {
                        update({
                          matrix_columns: checked ? (draft.matrix_columns ?? []).filter((n) => n !== column.name) : [...(draft.matrix_columns ?? []), column.name],
                        });
                        mark({ mechanism: "matrix_column", field: "matrix_columns", value: column.name }, !checked);
                      }}
                      className="mt-1 h-5 w-5 shrink-0"
                    />
                    <span dir="ltr" className="min-w-0 text-sm">
                      <span className="font-medium text-ink">{column.name}</span>
                      {column.description ? <span className="block text-ink-muted">{String(column.description)}</span> : null}
                    </span>
                  </label>
                );
              })}
            </div>
            <OwnColumns
              locale={locale}
              columns={draft.custom_matrix_columns ?? []}
              derived={matrix.custom_columns ?? []}
              onChange={(next) => update({ custom_matrix_columns: next })}
            />
          </fieldset>
        ) : null}

        <label className="flex min-h-11 cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            checked={draft.verification_checks ?? true}
            onChange={(event) => update({ verification_checks: event.target.checked })}
            className="mt-1 h-5 w-5 shrink-0"
          />
          <span className="text-sm text-ink">
            {t("criteria.verification")}
            <span className="mt-1 block text-xs text-ink-muted" data-parked="verification">
              {t("criteria.verificationParked")}
            </span>
          </span>
        </label>

        {stepError ? <InceptionRefusal locale={locale} refusal={stepError} draftId={draftId} origin={origin} /> : null}
        {saveError ? <InceptionRefusal locale={locale} refusal={saveError} draftId={draftId} origin={origin} onRetry={() => void persist("review")} /> : null}

        <StepAssist locale={locale} step="criteria" />

        {leaving !== null ? (
          <div role="alertdialog" aria-labelledby="workbench-leave" className="rounded-md border border-unclear p-3" data-workbench-leave>
            <p id="workbench-leave" className="text-sm text-ink">
              {wt("workbench.leave")}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button
                onClick={async () => {
                  // Review C1: the version's own save already stored the page (concepts, seeds and every other answer);
                  // a second save from this render would carry the earlier time and be refused.
                  const target = leaving;
                  if (await useVersion.current()) {
                    setLeaving(null);
                    window.location.assign(inceptionHref(locale, target, target ? draftId : "", origin));
                  }
                }}
                data-leave-use
              >
                {wt("workbench.leave.use")}
              </Button>
              <Button onClick={() => void persist(leaving, true)} data-leave-leave>
                {wt("workbench.leave.leave")}
              </Button>
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap gap-3">
          {/* M11a: while the workbench holds unused edits, "Use this version" is the screen's one brand button. */}
          <Button
            variant={workbenchDirty ? "secondary" : "primary"}
            type="submit"
            disabled={saving || ruleUnchosen}
            aria-describedby={ruleUnchosen ? "criteria-rule-blocked" : undefined}
          >
            {saving ? t("saving") : t("criteria.continue")}
          </Button>
          <Button onClick={() => void persist("")} disabled={saving}>
            {t("saveAndExit")}
          </Button>
          {ruleUnchosen ? (
            <p id="criteria-rule-blocked" className="basis-full text-sm text-blocked" data-rule-blocked>
              {t("criteria.method.blocked")}
            </p>
          ) : null}
        </div>
      </form>
    </InceptionFrame>
  );
}

/**
 * "How you will screen" (spec 11, M11b part D): two radio groups whose options and order are the
 * engine's (`method_options`). The visibility question is pre-selected (a proposal); the not-reported
 * question starts with nothing selected and blocks step 5 until chosen (answer 8). No option is
 * named as recommended.
 */
function MethodQuestions({
  locale,
  blinding,
  notReported,
  options,
  unchosen,
  older,
  fromImport,
  onBlinding,
  onNotReported,
}: Readonly<{
  locale: Locale;
  blinding: MethodBlinding | null;
  notReported: MethodNotReported | null;
  options: { blinding: MethodBlinding[]; not_reported: MethodNotReported[] } | null;
  unchosen: boolean;
  older: boolean;
  fromImport: boolean;
  onBlinding: (value: MethodBlinding) => void;
  onNotReported: (value: MethodNotReported) => void;
}>) {
  const t = inceptionT(locale);
  const key = (k: string) => k as Parameters<typeof t>[0];
  return (
    <section aria-labelledby="method-title" className="space-y-4 border-t border-rule pt-4" data-method>
      <div>
        <h3 id="method-title" className="font-semibold text-ink">
          {t("criteria.method.title")}
        </h3>
        <p className="text-sm text-ink-muted">{t("criteria.method.later")}</p>
        {fromImport ? <p className="text-sm text-ink-muted" data-method-import>{t("criteria.method.fromImport")}</p> : null}
      </div>
      <fieldset id="method-blinding" data-method-group="blinding">
        <legend className="text-sm font-medium text-ink">{t("criteria.method.blinding.q")}</legend>
        <div className="mt-2 space-y-2">
          {(options?.blinding ?? []).map((value) => (
            <label key={value} className="flex min-h-11 cursor-pointer items-start gap-3">
              <input
                type="radio"
                name="method-blinding"
                value={value}
                checked={blinding === value}
                onChange={() => onBlinding(value)}
                aria-describedby={`method-blinding-${value}-help`}
                className="mt-1 h-5 w-5 shrink-0"
              />
              <span className="text-sm">
                <span className="text-ink">{t(key(`criteria.method.blinding.${value}.label`))}</span>
                <span id={`method-blinding-${value}-help`} className="block text-ink-muted">
                  {t(key(`criteria.method.blinding.${value}.help`))}
                </span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <fieldset id="method-not-reported" aria-describedby={unchosen ? "method-rule-unchosen" : undefined} data-method-group="not_reported">
        <legend className="text-sm font-medium text-ink">{t("criteria.method.notReported.q")}</legend>
        {unchosen ? (
          <p id="method-rule-unchosen" className="mt-1 text-sm text-blocked" data-method-unchosen>
            {t("criteria.method.unchosen")}
            {older ? <span className="block text-ink-muted">{t("criteria.method.older")}</span> : null}
          </p>
        ) : null}
        <div className="mt-2 space-y-2">
          {(options?.not_reported ?? []).map((value) => (
            <label key={value} className="flex min-h-11 cursor-pointer items-start gap-3">
              <input
                type="radio"
                name="method-not-reported"
                value={value}
                checked={notReported === value}
                onChange={() => onNotReported(value)}
                aria-describedby={`method-nr-${value}-help`}
                className="mt-1 h-5 w-5 shrink-0"
              />
              <span className="text-sm">
                <span className="text-ink">{t(key(`criteria.method.notReported.${value}.label`))}</span>
                <span id={`method-nr-${value}-help`} className="block text-ink-muted">
                  {t(key(`criteria.method.notReported.${value}.help`))}
                </span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <p className="text-xs text-ink-muted">{t("criteria.method.savedWith")}</p>
    </section>
  );
}

/** The reason code input with the engine's suggestions (M10b, `05-criteria`). A native `list` input is a combobox. */
function ReasonInput({
  locale,
  id,
  value,
  onChange,
  suggestions,
}: Readonly<{ locale: Locale; id: string; value: string; onChange: (code: string) => void; suggestions: ReasonSuggestion[] }>) {
  const t = inceptionT(locale);
  const [refused, setRefused] = useState(false);
  const listId = `${id}-list`;
  return (
    <div className="min-w-0 sm:w-56">
      <label htmlFor={id} className="block text-sm text-ink">
        {t("criteria.reason.label")}
      </label>
      <input
        id={id}
        list={listId}
        value={value}
        dir="ltr"
        autoComplete="off"
        placeholder={t("criteria.reason.placeholder")}
        aria-describedby={`${id}-format`}
        onChange={(event) => {
          const next = normaliseReason(event.target.value);
          setRefused(next.refused);
          onChange(next.value.slice(0, 40));
        }}
        className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 font-mono text-ink"
        data-reason-input
      />
      <datalist id={listId}>
        {suggestions.map((s) => (
          <option key={s.code} value={s.code}>
            {s.source === "used" ? t("criteria.reason.used") : s.phrases ? t("criteria.reason.hasPhrases") : t("criteria.reason.noPhrases")}
          </option>
        ))}
      </datalist>
      <p id={`${id}-format`} className={`mt-1 text-xs ${refused ? "text-unclear" : "text-ink-muted"}`} aria-live="polite" data-reason-format={refused ? "refused" : "ok"}>
        {t("criteria.reason.format")}
      </p>
    </div>
  );
}

/** The reason of one exclusion row and "Change reason" (M10b). Not offered on a dropped row. */
function ReasonControl({
  locale,
  item,
  label,
  suggestions,
  open,
  onOpen,
  onCancel,
  onChoose,
}: Readonly<{
  locale: Locale;
  item: Criterion;
  label: string;
  suggestions: ReasonSuggestion[];
  open: boolean;
  onOpen: () => void;
  onCancel: () => void;
  onChoose: (code: string) => void;
}>) {
  const t = inceptionT(locale);
  const [code, setCode] = useState(item.reason_category ?? "");
  const invalidSaved = item.reason_valid === false;
  if (item.status === "rejected") {
    return <p className="mt-1 text-xs text-ink-muted" data-reason-dropped>{t("criteria.reason.droppedNote")}</p>;
  }
  return (
    <div className="mt-2" data-reason-control={item.id}>
      {invalidSaved ? (
        <p className="text-xs text-unclear" data-reason-invalid>
          {t("criteria.reason.invalidSaved")}
        </p>
      ) : null}
      {open ? (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <ReasonInput locale={locale} id={`reason-${item.id}`} value={code} onChange={setCode} suggestions={suggestions} />
          {item.generated && item.status === "accepted" ? (
            <p className="text-xs text-unclear" data-reason-regenerated>
              {t("criteria.reason.regenerated")}
            </p>
          ) : null}
          <Button onClick={() => onChoose(code)} disabled={!REASON_SHAPE.test(code)} data-reason-apply>
            {t("criteria.reason.apply")}
          </Button>
          <Button variant="quiet" onClick={onCancel}>
            {t("criteria.reason.cancel")}
          </Button>
        </div>
      ) : (
        <Button variant="quiet" className="px-0" onClick={onOpen} aria-label={t("criteria.reason.changeFor", { id: label })} data-reason-change>
          {t("criteria.reason.change")}
        </Button>
      )}
    </div>
  );
}

const EMPTY_COLUMN: MatrixColumnIn = { name: "", description: "", data_type: "free_text", required: false };

/** "Your columns": the researcher's own matrix columns (M10b, `05-criteria`). */
function OwnColumns({
  locale,
  columns,
  derived,
  onChange,
}: Readonly<{
  locale: Locale;
  columns: MatrixColumnIn[];
  derived: { id: string; name: string }[];
  onChange: (next: MatrixColumnIn[]) => void;
}>) {
  const t = inceptionT(locale);
  const [form, setForm] = useState<MatrixColumnIn>(EMPTY_COLUMN);
  const [editing, setEditing] = useState<number | null>(null);
  const [announce, setAnnounce] = useState("");
  const others = columns.filter((_, i) => i !== editing);
  // Presentation only: the engine refuses a clash (DRAFT_INVALID); this keeps Add from offering one.
  const clash = others.some((c) => c.name.trim().toLowerCase() === form.name.trim().toLowerCase()) && !!form.name.trim();
  const full = editing === null && columns.length >= 50;
  const ready = !!form.name.trim() && !!(form.description ?? "").trim() && !clash && !full;
  const submit = () => {
    if (!ready) return;
    const column = { ...form, name: form.name.trim(), description: (form.description ?? "").trim() };
    onChange(editing === null ? [...columns, column] : columns.map((c, i) => (i === editing ? { ...c, ...column } : c)));
    setAnnounce(t("criteria.mine.added", { name: column.name }));
    setForm(EMPTY_COLUMN);
    setEditing(null);
  };
  return (
    <div className="mt-4 border-t border-rule pt-3" data-own-columns>
      <h3 id="own-columns-title" className="text-sm font-semibold text-ink">
        {t("criteria.mine.title")}
      </h3>
      {columns.length === 0 ? <p className="text-sm text-ink-muted">{t("criteria.mine.none")}</p> : null}
      <ul aria-labelledby="own-columns-title" className="mt-2 space-y-2">
        {columns.map((column, index) => (
          <li key={`${column.name}-${index}`} className="rounded-md border border-rule bg-paper p-3" data-own-column={column.name}>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-ink" dir="auto">
                {column.name}
              </span>
              <DecisionBadge role="include">{t("criteria.mine.badge")}</DecisionBadge>
              {derived[index]?.id ? (
                <span className="font-mono text-xs text-ink-muted" dir="ltr" data-column-id>
                  {derived[index].id}
                </span>
              ) : null}
            </div>
            {column.description ? (
              <p className="mt-1 text-sm text-ink-muted" dir="auto">
                {column.description}
              </p>
            ) : null}
            <p className="mt-1 font-mono text-xs text-ink-muted" dir="ltr">
              {t(`criteria.mine.type.${column.data_type ?? "free_text"}` as "criteria.mine.type.free_text")}
              {column.required ? ` · ${t("criteria.mine.requiredShort")}` : ""}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button
                onClick={() => {
                  setEditing(index);
                  setForm({ ...EMPTY_COLUMN, ...column });
                }}
                aria-label={t("criteria.mine.edit", { name: column.name })}
              >
                {t("criteria.mine.editShort")}
              </Button>
              <Button variant="quiet" onClick={() => onChange(columns.filter((_, i) => i !== index))} aria-label={t("criteria.mine.remove", { name: column.name })} data-remove-column>
                {t("criteria.mine.removeShort")}
              </Button>
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-3 grid gap-2 sm:grid-cols-2" data-own-column-form>
        <p className="text-sm font-medium text-ink sm:col-span-2">{editing === null ? t("criteria.mine.add") : t("criteria.mine.editing", { name: columns[editing]?.name ?? "" })}</p>
        <div>
          <label htmlFor="own-column-name" className="block text-sm text-ink">
            {t("criteria.mine.name")}
          </label>
          <input
            id="own-column-name"
            value={form.name}
            maxLength={200}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            aria-invalid={clash || undefined}
            aria-describedby={clash ? "own-column-clash" : undefined}
            className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
          />
          {clash ? (
            <p id="own-column-clash" className="mt-1 text-xs text-unclear" data-column-clash>
              {t("criteria.mine.clash", { name: form.name.trim() })}
            </p>
          ) : null}
        </div>
        <div>
          <label htmlFor="own-column-type" className="block text-sm text-ink">
            {t("criteria.mine.type")}
          </label>
          <select
            id="own-column-type"
            value={form.data_type ?? "free_text"}
            onChange={(event) => setForm({ ...form, data_type: event.target.value })}
            className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
          >
            {MATRIX_TYPES.map((type) => (
              <option key={type} value={type}>
                {t(`criteria.mine.type.${type}` as "criteria.mine.type.free_text")}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="own-column-description" className="block text-sm text-ink">
            {t("criteria.mine.description")}
          </label>
          <textarea
            id="own-column-description"
            rows={2}
            maxLength={2000}
            value={form.description ?? ""}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            aria-describedby="own-column-description-help"
            className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
          />
          <p id="own-column-description-help" className="mt-1 text-xs text-ink-muted">
            {t("criteria.mine.descriptionHelp")}
          </p>
        </div>
        <label className="flex min-h-11 cursor-pointer items-center gap-3 sm:col-span-2">
          <input type="checkbox" checked={!!form.required} onChange={(event) => setForm({ ...form, required: event.target.checked })} className="h-5 w-5 shrink-0" />
          <span className="text-sm text-ink">{t("criteria.mine.required")}</span>
        </label>
        <div className="flex flex-wrap gap-2 sm:col-span-2">
          <Button onClick={submit} disabled={!ready} data-add-column>
            {editing === null ? t("criteria.mine.submit") : t("criteria.mine.save")}
          </Button>
          {editing !== null ? (
            <Button
              variant="quiet"
              onClick={() => {
                setEditing(null);
                setForm(EMPTY_COLUMN);
              }}
            >
              {t("criteria.reason.cancel")}
            </Button>
          ) : null}
          {full ? <p className="self-center text-xs text-ink-muted">{t("criteria.mine.limit", { n: "50" })}</p> : null}
        </div>
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {announce}
      </p>
    </div>
  );
}
