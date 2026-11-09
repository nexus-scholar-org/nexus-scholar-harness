"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { previewDraft, runGenesis, runStep, type Criterion, type GenesisRequest, type Preview, type ScreeningBinding } from "@/lib/inception-api";
import { inceptionT, sourceText } from "@/lib/inception-copy";

/**
 * Step 6, Review and create (spec 06, M4b): the only write gate. `POST /preview`
 * compiles the saved draft and writes nothing; "Create the workspace" sends
 * `POST /drafts/{id}/genesis`. The engine's overwrite guard decides: an existing
 * workspace comes back `WORKSPACE_EXISTS` with `markers` (the gate then offers
 * "Replace and back up", which re-sends `replace`), and a workspace with
 * screening comes back `SCREENING_BOUND` (the researcher types the slug; the
 * engine compares it). One GatePanel and one brand button in every state.
 */

/** Where Done finds the genesis answer for this tab (the draft records it too). */
export function genesisStorageKey(sessionId: string): string {
  return `nexus.inception.genesis.${sessionId}`;
}

type Confirm = { kind: "replace"; path: string } | { kind: "bound"; path: string; slug: string; binding: ScreeningBinding };

export function InceptionReview({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const state = useDraft();
  const { draft, update, save, saving, saveError, origin, draftId, record } = state;
  const [preview, setPreview] = useState<Preview | null>(null);
  const [rejected, setRejected] = useState<Criterion[]>([]);
  const [checking, setChecking] = useState(false);
  const [previewError, setPreviewError] = useState<Refusal | null>(null);
  const [stale, setStale] = useState(false);
  const [creating, setCreating] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [confirm, setConfirm] = useState<Confirm | null>(null);
  const [typed, setTyped] = useState("");
  const confirmHeading = useRef<HTMLHeadingElement>(null);
  const createButton = useRef<HTMLButtonElement>(null);
  const checkedOnce = useRef(false);

  const check = useCallback(
    async (store: boolean) => {
      setChecking(true);
      setPreviewError(null);
      setRefusal(null);
      try {
        if (store && !(await save())) return;
        const [compiled, steps] = await Promise.all([previewDraft(origin, draft), runStep(origin, "criteria", draft)]);
        setPreview(compiled);
        setRejected(steps.criteria.filter((c) => c.status === "rejected"));
        setStale(false);
      } catch (error) {
        setPreview(null);
        setPreviewError(refusalOf(error));
      } finally {
        setChecking(false);
      }
    },
    [origin, draft, save],
  );

  // Preview the saved draft once it is read.
  useEffect(() => {
    if (!record || checkedOnce.current) return;
    checkedOnce.current = true;
    void check(false);
  }, [record, check]);

  useEffect(() => {
    if (confirm) confirmHeading.current?.focus();
  }, [confirm]);

  const editProject = (patch: Parameters<typeof update>[0]) => {
    update(patch);
    setStale(true);
  };

  const cancel = () => {
    setConfirm(null);
    setTyped("");
    setRefusal(null);
    setTimeout(() => createButton.current?.focus(), 0);
  };

  const create = async (request: GenesisRequest) => {
    if (!record || creating) return;
    setCreating(true);
    setRefusal(null);
    try {
      const made = await runGenesis(origin, record.session_id, request);
      try {
        window.sessionStorage.setItem(genesisStorageKey(record.session_id), JSON.stringify(made));
      } catch {
        // Done reads what the draft records.
      }
      window.location.assign(inceptionHref(locale, "done", record.session_id, origin));
    } catch (error) {
      const r = refusalOf(error);
      const details = (r.details ?? {}) as Record<string, unknown>;
      if (r.code === "WORKSPACE_EXISTS" && Array.isArray(details.markers)) {
        setConfirm({ kind: "replace", path: String(details.path ?? "") });
      } else if (r.code === "SCREENING_BOUND") {
        setConfirm({
          kind: "bound",
          path: String(details.path ?? ""),
          slug: preview?.target?.slug ?? "",
          binding: {
            bound: true,
            decision_events: Number(details.decision_events ?? 0),
            decision_files: Number(details.decision_files ?? 0),
            published: Boolean(details.published),
          },
        });
      } else {
        setRefusal(r);
      }
    } finally {
      setCreating(false);
    }
  };

  const target = preview?.target;
  const busy = saving || checking || creating;
  const blocked = busy || stale || !preview;
  const paradigm = String(draft.paradigm ?? "");

  const gateActions =
    confirm === null ? (
      <Button ref={createButton} variant="primary" onClick={() => void create({})} disabled={blocked} aria-busy={creating} data-create>
        {creating ? t("review.creating") : t("review.create")}
      </Button>
    ) : confirm.kind === "replace" ? (
      <>
        <Button variant="primary" onClick={() => void create({ replace: true })} disabled={blocked} data-replace>
          {t("review.replace")}
        </Button>
        <Button variant="quiet" onClick={cancel}>
          {t("review.cancel")}
        </Button>
      </>
    ) : (
      <>
        <Button
          variant="primary"
          onClick={() => void create({ replace: true, confirm_discard_screening_binding: typed })}
          disabled={blocked || !typed}
          data-bound-confirm
        >
          {t("review.boundConfirm")}
        </Button>
        <Button variant="quiet" onClick={cancel}>
          {t("review.cancel")}
        </Button>
      </>
    );

  return (
    <InceptionFrame locale={locale} current="review" draft={state}>
      <StepHeader kicker={t("review.kicker")} title={t("review.title")} lede={t("review.lede")} />
      <div
        className="grid gap-6 lg:grid-cols-[2fr_1fr]"
        onKeyDown={(event) => {
          if (event.key === "Escape" && confirm) cancel();
        }}
      >
        <div className="min-w-0 space-y-6">
          <section aria-labelledby="review-about" className="rounded-lg border border-rule bg-leaf p-4">
            <h2 id="review-about" className="font-semibold text-ink">
              {t("review.about")}
            </h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label htmlFor="review-title" className="block text-sm font-medium text-ink">
                  {t("review.reviewTitle")}
                </label>
                <input
                  id="review-title"
                  value={draft.title ?? ""}
                  onChange={(event) => editProject({ title: event.target.value })}
                  aria-describedby="review-title-help"
                  className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                />
                <p id="review-title-help" className="mt-1 text-xs text-ink-muted">
                  {t("review.reviewTitleHelp")}
                </p>
              </div>
              <div>
                <label htmlFor="review-lead" className="block text-sm font-medium text-ink">
                  {t("review.lead")}
                </label>
                <input
                  id="review-lead"
                  value={draft.lead_researcher ?? ""}
                  onChange={(event) => editProject({ lead_researcher: event.target.value })}
                  className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                />
              </div>
              <div>
                <label htmlFor="review-venue" className="block text-sm font-medium text-ink">
                  {t("review.venue")}
                </label>
                <input
                  id="review-venue"
                  value={draft.venue ?? ""}
                  onChange={(event) => editProject({ venue: event.target.value })}
                  className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                />
              </div>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <Button onClick={() => void check(true)} disabled={busy} data-check>
                {checking ? t("review.checking") : t("review.check")}
              </Button>
              {stale ? (
                <p className="text-sm text-unclear" aria-live="polite" data-stale>
                  {t("review.stale")}
                </p>
              ) : null}
            </div>
          </section>

          {saveError ? <InceptionRefusal locale={locale} refusal={saveError} draftId={draftId} origin={origin} /> : null}
          {previewError ? <InceptionRefusal locale={locale} refusal={previewError} draftId={draftId} origin={origin} onRetry={() => void check(true)} /> : null}

          {preview ? (
            <div className="space-y-4" data-preview>
              <dl className="grid gap-3 rounded-lg border border-rule bg-leaf p-4 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-ink-muted">{t("review.lens")}</dt>
                  <dd className="text-ink" dir="ltr">
                    {paradigm} · {String(draft.playbook ?? "")}
                  </dd>
                  <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "shape", draftId, origin)}>
                    {t("review.edit", { step: t("step.shape") })}
                  </a>
                </div>
                <div>
                  <dt className="text-ink-muted">{t("review.window")}</dt>
                  <dd className="text-ink">
                    {draft.start_year && draft.end_year
                      ? t("review.yearsRange", { from: String(draft.start_year), to: String(draft.end_year) })
                      : draft.start_year
                        ? t("review.yearsOpen", { from: String(draft.start_year) })
                        : t("review.yearsAny")}{" "}
                    · <bdi dir="ltr">{(draft.languages ?? []).join(", ")}</bdi>
                  </dd>
                  <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "scope", draftId, origin)}>
                    {t("review.edit", { step: t("step.scope") })}
                  </a>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-ink-muted">{t("review.questions")}</dt>
                  <dd>
                    <ol className="list-decimal ps-5 text-ink">
                      {(draft.rqs ?? []).map((rq) => (
                        <li key={rq} dir="auto">
                          {rq}
                        </li>
                      ))}
                    </ol>
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-ink-muted">{t("review.concepts")}</dt>
                  <dd className="text-ink" dir="auto">
                    {(draft.concepts ?? []).map((c) => c.concept).join(" · ")}
                  </dd>
                </div>
              </dl>

              <section aria-labelledby="review-criteria" className="rounded-lg border border-rule bg-leaf p-4">
                <h2 id="review-criteria" className="font-semibold text-ink">
                  {t("review.criteria")}
                </h2>
                <ul className="mt-2 space-y-2">
                  {preview.criteria.map((c) => (
                    <li key={c.id} className="rounded-md bg-paper p-3" data-review-criterion={c.id}>
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <DecisionBadge role="include">{t(c.kind === "inclusion" ? "criteria.inclusion" : "criteria.exclusion")}</DecisionBadge>
                        <span className="text-ink-muted">{sourceText(locale, c.source, paradigm, c.source_label)}</span>
                      </div>
                      <p className="mt-1 text-ink" dir="auto">
                        {c.criterion}
                      </p>
                    </li>
                  ))}
                  {rejected.map((c) => (
                    <li key={c.id} className="rounded-md border border-dashed border-rule p-3" data-review-rejected={c.id}>
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <DecisionBadge role="exclude">{t("review.rejected")}</DecisionBadge>
                        <span className="text-ink-muted">{sourceText(locale, c.source, paradigm, c.source_label)}</span>
                      </div>
                      <p className="mt-1 text-ink-muted" dir="auto">
                        {c.criterion}
                      </p>
                    </li>
                  ))}
                </ul>
                <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "criteria", draftId, origin)}>
                  {t("review.edit", { step: t("step.criteria") })}
                </a>
                <details className="mt-2 text-sm">
                  <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">
                    {DETAILS_LABEL[locale]} · {t("review.screeningText")}
                  </summary>
                  <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap rounded-md bg-paper p-3 font-mono text-[0.8125rem] text-ink [overflow-wrap:anywhere]" dir="ltr">
                    {preview.screening_criteria}
                  </pre>
                </details>
              </section>
            </div>
          ) : !previewError && !checking ? (
            <p className="text-sm text-ink-muted">{t("review.notChecked")}</p>
          ) : checking ? (
            <p role="status" className="text-ink-muted">
              {t("review.checking")}
            </p>
          ) : null}
        </div>

        {preview ? (
          <aside className="min-w-0 space-y-4">
            <dl className="grid gap-3 rounded-lg border border-rule bg-leaf p-4 text-sm">
              <div>
                <dt className="text-ink-muted">{t("review.folder")}</dt>
                <dd data-target-path>
                  <DataCell>{target?.path ?? ""}</DataCell>
                </dd>
              </div>
              <div>
                <dt className="text-ink-muted">{t("review.files")}</dt>
                <dd>
                  <ul className="space-y-1" data-files>
                    {preview.files.map((f) => (
                      <li key={f}>
                        <DataCell>{f}</DataCell>
                      </li>
                    ))}
                  </ul>
                </dd>
              </div>
              <div>
                <dt className="text-ink-muted">{t("review.fingerprint")}</dt>
                <dd data-fingerprint>
                  <DataCell>{preview.protocol_fingerprint}</DataCell>
                </dd>
              </div>
            </dl>

            <section aria-labelledby="review-checks" className="rounded-lg border border-rule bg-leaf p-4 text-sm">
              <h2 id="review-checks" className="font-semibold text-ink">
                {t("review.checks")}
              </h2>
              <ul className="mt-2 space-y-1" data-checks>
                <li className="text-include">{t("review.check.decided")}</li>
                <li className="text-include">{t("review.check.sides")}</li>
                <li className="text-include">{t("review.check.compiler")}</li>
                {!target?.exists ? (
                  <li className="text-include">{t("review.check.free")}</li>
                ) : target.screening?.bound ? (
                  <li className="text-blocked" data-target-bound>
                    {t("review.check.bound", { n: formatNumber(locale, target.screening.decision_events + target.screening.decision_files) })}
                  </li>
                ) : (
                  <li className="text-unclear" data-target-exists>
                    {t("review.check.exists")}
                  </li>
                )}
              </ul>
            </section>

            {confirm?.kind === "replace" ? (
              <section role="alert" aria-labelledby="confirm-title" className="rounded-lg border border-unclear bg-leaf p-4" data-confirm="replace">
                <h2 id="confirm-title" ref={confirmHeading} tabIndex={-1} className="font-semibold text-ink">
                  {t("review.replaceTitle")}
                </h2>
                <p className="mt-2 text-sm text-ink">{t("review.replaceBody", { path: "" })}</p>
                <p className="mt-1">
                  <DataCell>{confirm.path}</DataCell>
                </p>
              </section>
            ) : confirm?.kind === "bound" ? (
              <section role="alert" aria-labelledby="confirm-title" className="rounded-lg border border-blocked bg-leaf p-4" data-confirm="bound">
                <h2 id="confirm-title" ref={confirmHeading} tabIndex={-1} className="font-semibold text-ink">
                  {t("review.boundTitle")}
                </h2>
                <p className="mt-2 text-sm text-ink">
                  {t("review.boundBody", {
                    events: formatNumber(locale, confirm.binding.decision_events),
                    files: formatNumber(locale, confirm.binding.decision_files),
                    published: confirm.binding.published ? t("review.boundPublished") : t("review.boundNotPublished"),
                  })}
                </p>
                <p className="mt-1">
                  <DataCell>{confirm.path}</DataCell>
                </p>
              </section>
            ) : null}

            <GatePanel label={confirm ? t("review.gateReplacing") : t("review.gate")} actions={gateActions}>
              <p>
                {t("review.gateBody", { path: "" })}
                <DataCell>{target?.path ?? ""}</DataCell>
              </p>
              {confirm?.kind === "bound" ? (
                <div className="mt-3">
                  <label htmlFor="confirm-slug" className="block text-sm text-ink">
                    {t("review.boundType", { slug: "" })}
                    <bdi dir="ltr" className="font-mono">
                      {confirm.slug}
                    </bdi>
                  </label>
                  <input
                    id="confirm-slug"
                    dir="ltr"
                    autoComplete="off"
                    spellCheck={false}
                    value={typed}
                    aria-invalid={refusal?.code === "CONFIRMATION_MISMATCH"}
                    onChange={(event) => setTyped(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && typed && !blocked) {
                        event.preventDefault();
                        void create({ replace: true, confirm_discard_screening_binding: typed });
                      }
                    }}
                    className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 font-mono text-ink"
                  />
                </div>
              ) : null}
              {stale ? <p className="mt-2 text-sm text-unclear">{t("review.stale")}</p> : null}
            </GatePanel>
            {refusal ? <InceptionRefusal locale={locale} refusal={refusal} draftId={draftId} origin={origin} /> : null}
          </aside>
        ) : null}
      </div>
    </InceptionFrame>
  );
}
