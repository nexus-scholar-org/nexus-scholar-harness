"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { runStep, type CriteriaStep, type Criterion, type Draft, type MatrixStep } from "@/lib/inception-api";
import { getConcepts, getRecon, hasUsablePool, type ConceptReport, type ReconState } from "@/lib/recon-api";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { DoiLink } from "@/components/inception-recon";
import { inceptionT, sourceText } from "@/lib/inception-copy";

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

const SUGGESTIONS_SHOWN = 5;

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
  const [recon, setRecon] = useState<ReconState | null>(null);
  const [report, setReport] = useState<ConceptReport | null>(null);
  const [allSuggestions, setAllSuggestions] = useState<Record<number, boolean>>({});

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
      else update({ extra_exclusions: [...(draft.extra_exclusions ?? []), { criterion: text }] });
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
              <li key={index} data-concept={index}>
              <div className="grid gap-2 sm:grid-cols-[1fr_2fr_auto] sm:items-end">
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
                    key={(c.synonyms ?? []).join("|")}
                    defaultValue={(c.synonyms ?? []).join(", ")}
                    onBlur={(event) => setConcept(index, { synonyms: synonymsOf(event.target.value) })}
                    className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                  />
                </div>
                <Button variant="quiet" onClick={() => update({ concepts: concepts.filter((_, i) => i !== index) })}>
                  {t("criteria.removeConcept", { n: formatNumber(locale, index + 1) })}
                </Button>
              </div>
              {report ? (
                <Anchoring
                  locale={locale}
                  index={index}
                  report={report}
                  concept={c.concept}
                  synonyms={c.synonyms ?? []}
                  all={!!allSuggestions[index]}
                  onAll={() => setAllSuggestions((a) => ({ ...a, [index]: !a[index] }))}
                  onTick={(term, on) => setConcept(index, { synonyms: on ? [...(c.synonyms ?? []), term] : (c.synonyms ?? []).filter((x) => x !== term) })}
                />
              ) : null}
              </li>
            ))}
          </ol>
          {report ? <p className="mt-2 text-xs text-ink-muted" data-anchor-note>{t("criteria.anchor.note")}</p> : null}
          {recon && !hasUsablePool(recon) ? (
            <p className="mt-2 text-sm text-ink-muted" data-no-pool>
              {t("criteria.synonyms.noPool")}{" "}
              <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)}>
                {t("criteria.synonyms.goExplore")}
              </a>
            </p>
          ) : null}
          {recon?.scope_changed && report ? (
            <p className="mt-2 text-sm text-unclear" data-scope-changed>
              {t("criteria.anchor.scopeChanged")}{" "}
              <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)}>
                {t("criteria.synonyms.goExplore")}
              </a>
            </p>
          ) : null}
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
            <p className="mt-1 inline-block rounded-sm border border-dashed border-rule px-2 text-xs text-ink-muted" data-parked="matrix">
              {t("criteria.matrixParked")}
            </p>
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
          <span className="text-sm text-ink">
            {t("criteria.verification")}
            <span className="mt-1 block text-xs text-ink-muted" data-parked="verification">
              {t("criteria.verificationParked")}
            </span>
          </span>
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

/** One concept's counts in the pool and the engine's co-occurring pool terms (spec 05, M4d). */
function Anchoring({
  locale,
  index,
  report,
  concept,
  synonyms,
  all,
  onAll,
  onTick,
}: Readonly<{
  locale: Locale;
  index: number;
  report: ConceptReport;
  concept: string;
  synonyms: string[];
  all: boolean;
  onAll: () => void;
  onTick: (term: string, on: boolean) => void;
}>) {
  const t = inceptionT(locale);
  const row = report.concepts.find((r) => r.source === "draft" && r.concept === concept.trim());
  if (!row) return null;
  const total = String(report.n_docs);
  const suggestions = all ? row.suggestions : row.suggestions.slice(0, SUGGESTIONS_SHOWN);
  return (
    <div className="mt-2 space-y-2 text-sm" data-anchoring={index}>
      <p className="text-ink" data-anchor-concept>
        <bdi dir="auto">{t("criteria.anchor.concept", { concept: row.concept, anchored: String(row.anchored_in), total })}</bdi>
        {row.anchored_in === 0 ? (
          <>
            {" "}
            <DecisionBadge role="unclear">{t("criteria.anchor.none")}</DecisionBadge>
          </>
        ) : null}
      </p>
      <ul className="flex flex-wrap gap-2">
        {row.terms.map((term) => (
          <li key={term.term} className="rounded-sm border border-rule px-2 py-1" data-term={term.term} data-observed={term.observed_in}>
            <span dir="auto" className="text-ink">
              {term.term}
            </span>{" "}
            {term.observed_in === 0 ? (
              <DecisionBadge role="unclear">{t("criteria.anchor.none")}</DecisionBadge>
            ) : (
              <span className="text-ink-muted" data-anchor-term>
                {t("criteria.anchor.term", { observed: String(term.observed_in), total })}
              </span>
            )}
            {term.anchor_dois.length ? (
              <details className="text-xs">
                <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
                  {DETAILS_LABEL[locale]} · {t("criteria.anchor.dois", { n: String(term.anchor_dois.length) })}
                </summary>
                <ul>
                  {term.anchor_dois.map((doi) => (
                    <li key={doi}>
                      <DoiLink locale={locale} doi={doi} />
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
          </li>
        ))}
      </ul>
      <div role="group" aria-label={t("criteria.synonyms.group", { concept: row.concept })} className="rounded-md border border-dashed border-ink-muted p-3" data-suggestions={index}>
        <p className="text-xs font-semibold text-ink-muted">{t("criteria.synonyms.title")}</p>
        <p className="text-xs text-ink-muted">{t("criteria.synonyms.help")}</p>
        {row.suggestions.length === 0 ? (
          <p className="mt-1 text-ink-muted">{t("criteria.synonyms.none")}</p>
        ) : (
          <ul className="mt-1">
            {suggestions.map((sug) => {
              const on = synonyms.includes(sug.term);
              return (
                <li key={sug.term}>
                  <label className="flex min-h-11 cursor-pointer items-center gap-3 text-ink">
                    <input type="checkbox" checked={on} onChange={() => onTick(sug.term, !on)} className="h-5 w-5 shrink-0" data-suggestion={sug.term} />
                    <bdi dir="auto">{t("criteria.synonyms.option", { term: sug.term, observed: String(sug.observed_in) })}</bdi>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
        {row.suggestions.length > SUGGESTIONS_SHOWN ? (
          <Button variant="quiet" className="px-0" aria-expanded={all} onClick={onAll}>
            {all ? t("criteria.synonyms.less") : t("criteria.synonyms.more", { n: String(row.suggestions.length) })}
          </Button>
        ) : null}
        {row.suggestions.some((sug) => synonyms.includes(sug.term)) ? <p className="text-xs text-ink-muted">{t("criteria.synonyms.unsaved")}</p> : null}
      </div>
    </div>
  );
}
