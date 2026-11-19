"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { StepAssist } from "@/components/inception-assist";

import { runStep, type AcceptedFrom, type CriteriaStep, type Criterion, type Draft, type MatrixColumnIn, type MatrixStep, type ReasonSuggestion } from "@/lib/inception-api";
import { getConcepts, getRecon, hasUsablePool, type ConceptReport, type ReconState } from "@/lib/recon-api";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { DoiLink } from "@/components/inception-recon";
import { inceptionCountT, inceptionT, sourceText } from "@/lib/inception-copy";

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
  const [newExclusionReason, setNewExclusionReason] = useState("");
  const [reasonEditing, setReasonEditing] = useState<string | null>(null);
  const [accepted, setAccepted] = useState<AcceptedFrom[]>([]);
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
    draft.default_exclusion_reason, draft.custom_matrix_columns,
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
  const setConcept = (index: number, patch: { concept?: string; synonyms?: string[] }) =>
    update({ concepts: concepts.map((c, i) => (i === index ? { ...c, ...patch } : c)) });
  const present = new Set(concepts.map((c) => c.concept.trim().toLowerCase()));

  const persist = async (next: "review" | "") => {
    const cleaned = concepts.filter((c) => c.concept.trim()).map((c) => ({ concept: c.concept.trim(), synonyms: c.synonyms ?? [] }));
    const body = { ...draft, concepts: cleaned };
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
                  onTick={(term, on) => {
                    setConcept(index, { synonyms: on ? [...(c.synonyms ?? []), term] : (c.synonyms ?? []).filter((x) => x !== term) });
                    mark({ mechanism: "pool_synonym", field: `concepts[${c.concept.trim()}].synonyms`, value: term }, on);
                  }}
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
                    <Button
                      key={term}
                      variant="secondary"
                      className="border-dashed"
                      onClick={() => {
                        update({ concepts: [...concepts, { concept: term, synonyms: [] }] });
                        mark({ mechanism: "suggested_concept", field: "concepts", value: term }, true);
                      }}
                    >
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
