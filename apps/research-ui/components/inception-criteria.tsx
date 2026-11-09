"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { runStep, type CriteriaStep, type Criterion, type Draft, type MatrixStep } from "@/lib/inception-api";
import { inceptionT, sourceText } from "@/lib/inception-copy";

/**
 * Step 5, Concepts and criteria (spec 05, M4b; INC-22). Every criterion comes
 * from `POST /steps/criteria` with its id, its verbatim text, its source and its
 * status; the screen only records the researcher's Accept or Reject in
 * `criteria_decisions`. A criterion the wizard wrote stays "waiting" (default
 * no) until accepted; one the researcher typed is accepted unless rejected.
 */

function synonymsOf(text: string): string[] {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

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
  const key = JSON.stringify([draft.paradigm, draft.playbook, draft.proof, draft.unit_of_analysis, draft.out_of_scope, draft.extra_inclusions, draft.extra_exclusions, draft.criteria_decisions, draft.matrix_columns]);
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

  const decide = (item: Criterion, accepted: boolean) =>
    setDraft((current) => ({ ...current, criteria_decisions: { ...(current.criteria_decisions ?? {}), [item.id]: accepted } }));

  const removeManual = (item: Criterion) => {
    if (item.kind === "inclusion") update({ extra_inclusions: (draft.extra_inclusions ?? []).filter((c) => c !== item.criterion) });
    else update({ extra_exclusions: (draft.extra_exclusions ?? []).filter((c) => c.criterion !== item.criterion) });
  };

  const concepts = draft.concepts ?? [];
  const setConcept = (index: number, patch: { concept?: string; synonyms?: string[] }) =>
    update({ concepts: concepts.map((c, i) => (i === index ? { ...c, ...patch } : c)) });
  const present = new Set(concepts.map((c) => c.concept.trim().toLowerCase()));

  const persist = async (next: "review" | "") => {
    const cleaned = concepts.filter((c) => c.concept.trim()).map((c) => ({ concept: c.concept.trim(), synonyms: c.synonyms ?? [] }));
    const stored = await save({ ...draft, concepts: cleaned });
    if (stored) window.location.assign(inceptionHref(locale, next, next ? draftId : "", origin));
  };

  const undecided = criteria?.undecided.length ?? 0;
  const paradigm = draft.paradigm ?? "";

  const renderSide = (kind: "inclusion" | "exclusion") => {
    const items = (criteria?.criteria ?? []).filter((c) => c.kind === kind);
    const prefix = kind === "inclusion" ? "I" : "E";
    const value = kind === "inclusion" ? newInclusion : newExclusion;
    const setValue = kind === "inclusion" ? setNewInclusion : setNewExclusion;
    const add = () => {
      const text = value.trim();
      if (!text) return;
      if (kind === "inclusion") update({ extra_inclusions: [...(draft.extra_inclusions ?? []), text] });
      else update({ extra_exclusions: [...(draft.extra_exclusions ?? []), { criterion: text, reason_category: "OUT_OF_SCOPE" }] });
      setValue("");
    };
    return (
      <section aria-labelledby={`criteria-${kind}`} className="rounded-lg border border-rule bg-leaf p-4" data-side={kind}>
        <h2 id={`criteria-${kind}`} className="font-semibold text-ink">
          {t(kind === "inclusion" ? "criteria.inclusion" : "criteria.exclusion")}
        </h2>
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
                  {item.reason_category ? <span className="font-mono text-ink-muted" dir="ltr">{item.reason_category}</span> : null}
                  <span className="text-ink-muted">{sourceText(locale, item.source, paradigm, item.source_label)}</span>
                  <DecisionBadge role={role}>{t(statusKey)}</DecisionBadge>
                </div>
                <p className="mt-2 text-ink" dir="ltr" data-verbatim>
                  {item.criterion}
                </p>
                {item.generated && item.status === "undecided" ? <p className="mt-1 text-xs text-ink-muted">{t("criteria.defaultNo")}</p> : null}
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
                {item.generated ? <p className="mt-1 text-xs text-ink-muted">{t("criteria.editHint")}</p> : null}
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
          <Button onClick={add} disabled={!value.trim()}>
            {t("criteria.add")}
          </Button>
        </div>
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
              {undecided > 0 ? t("criteria.needYou", { n: formatNumber(locale, undecided) }) : t("criteria.allDecided")}
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
        <section aria-labelledby="criteria-concepts" className="rounded-lg border border-rule bg-leaf p-4">
          <h2 id="criteria-concepts" className="font-semibold text-ink">
            {t("criteria.concepts")}
          </h2>
          <ol className="mt-3 space-y-3">
            {concepts.map((c, index) => (
              <li key={index} className="grid gap-2 sm:grid-cols-[1fr_2fr_auto] sm:items-end" data-concept={index}>
                <div>
                  <label htmlFor={`concept-${index}`} className="block text-xs text-ink-muted">
                    {t("criteria.concept")} {formatNumber(locale, index + 1)}
                  </label>
                  <input id={`concept-${index}`} value={c.concept} onChange={(event) => setConcept(index, { concept: event.target.value })} className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink" />
                </div>
                <div>
                  <label htmlFor={`concept-syn-${index}`} className="block text-xs text-ink-muted">
                    {t("criteria.synonyms")}
                  </label>
                  <input
                    id={`concept-syn-${index}`}
                    defaultValue={(c.synonyms ?? []).join(", ")}
                    onBlur={(event) => setConcept(index, { synonyms: synonymsOf(event.target.value) })}
                    className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                  />
                </div>
                <Button variant="quiet" onClick={() => update({ concepts: concepts.filter((_, i) => i !== index) })}>
                  {t("criteria.removeConcept", { n: formatNumber(locale, index + 1) })}
                </Button>
              </li>
            ))}
          </ol>
          <div className="mt-3">
            <Button onClick={() => update({ concepts: [...concepts, { concept: "", synonyms: [] }] })}>{t("criteria.addConcept")}</Button>
          </div>
          {suggested.filter((term) => !present.has(term.toLowerCase())).length > 0 ? (
            <div className="mt-3" data-suggested>
              <p className="text-xs text-ink-muted">{t("criteria.suggested")}</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {suggested
                  .filter((term) => !present.has(term.toLowerCase()))
                  .map((term) => (
                    <Button key={term} variant="secondary" className="border-dashed" onClick={() => update({ concepts: [...concepts, { concept: term, synonyms: [] }] })}>
                      {t("criteria.suggestedAdd", { term })}
                    </Button>
                  ))}
              </div>
            </div>
          ) : null}
        </section>

        {criteria ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {renderSide("inclusion")}
            {renderSide("exclusion")}
          </div>
        ) : !stepError ? (
          <p role="status" className="text-ink-muted">
            {t("asking")}
          </p>
        ) : null}

        {matrix ? (
          <fieldset className="rounded-lg border border-rule bg-leaf p-4" data-matrix>
            <legend className="px-1 font-semibold text-ink">{t("criteria.matrix")}</legend>
            <p className="text-xs text-ink-muted">{t("criteria.matrixHelp")}</p>
            <div className="mt-2">
              <Button onClick={() => update({ matrix_columns: matrix.columns.map((c) => c.name) })} data-tick-all>
                {t("criteria.tickAll")}
              </Button>
            </div>
            <div className="mt-2 space-y-2">
              {matrix.columns.map((column) => {
                const checked = (draft.matrix_columns ?? []).includes(column.name);
                return (
                  <label key={column.name} className="flex min-h-11 cursor-pointer items-start gap-3">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() =>
                        update({
                          matrix_columns: checked ? (draft.matrix_columns ?? []).filter((n) => n !== column.name) : [...(draft.matrix_columns ?? []), column.name],
                        })
                      }
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
          </fieldset>
        ) : null}

        <label className="flex min-h-11 cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            checked={draft.verification_checks ?? true}
            onChange={(event) => update({ verification_checks: event.target.checked })}
            className="mt-1 h-5 w-5 shrink-0"
          />
          <span className="text-sm text-ink">{t("criteria.verification")}</span>
        </label>

        {stepError ? <InceptionRefusal locale={locale} refusal={stepError} draftId={draftId} origin={origin} /> : null}
        {saveError ? <InceptionRefusal locale={locale} refusal={saveError} draftId={draftId} origin={origin} onRetry={() => void persist("review")} /> : null}

        <div className="flex flex-wrap gap-3">
          <Button variant="primary" type="submit" disabled={saving}>
            {saving ? t("saving") : t("criteria.continue")}
          </Button>
          <Button onClick={() => void persist("")} disabled={saving}>
            {t("saveAndExit")}
          </Button>
        </div>
      </form>
    </InceptionFrame>
  );
}
