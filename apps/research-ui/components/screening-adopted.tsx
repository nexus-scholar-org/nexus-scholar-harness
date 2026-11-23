"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { LoadingFrame } from "@/components/loading-frame";
import { Button, DataCell, DecisionBadge } from "@/components/ui/base";
import { ScreeningSteps, StateCard, stepHref } from "@/components/screening-state-card";
import { adoptionText, type AdoptionCopyKey } from "@/lib/adoption-copy";
import { localDate } from "@/lib/local-time";
import { isScreeningApiError } from "@/lib/screening-api";
import { declareAdoption, getAdoption, recordAdoptionSample, type AdoptionState } from "@/lib/screening-v1";

/**
 * H-adopted-decisions-disclosure: the screen where the reviewer declares decisions
 * "stored from the agent's draft without being read one by one" (decision 2026-11-22).
 *
 * The engine offers the candidates (decisions whose note says adopted or stored in
 * bulk); nothing is declared until the reviewer selects, ticks "I did not read these
 * records one by one" and records it. A declaration is a line of the audit; the
 * decisions themselves are not changed. Desktop only: a phone token is refused by the engine.
 */

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function codeOf(error: unknown): { code: string; message: string } {
  return isScreeningApiError(error) ? { code: error.code, message: error.serverMessage } : { code: "ENGINE_UNREACHABLE", message: "" };
}

const OUTCOME_ROLE = { INCLUDE: "include", EXCLUDE: "exclude", MAYBE: "unclear" } as const;

export function ScreeningAdopted({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: AdoptionCopyKey, values?: Record<string, string | number>) => adoptionText(locale, key, values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; data: AdoptionState } | { status: "error"; code: string; message: string }>({ status: "loading" });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [note, setNote] = useState("");
  const [size, setSize] = useState("");
  // A seed drawn after the first render (a value drawn while rendering would differ between the
  // pre-rendered page and the browser); the reviewer may type their own.
  const [seed, setSeed] = useState("");
  useEffect(() => setSeed((s) => s || String(Math.floor(Math.random() * 90_000_000) + 10_000_000)), []);
  const [confirming, setConfirming] = useState(false);
  const [notRead, setNotRead] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const [recorded, setRecorded] = useState(false);
  const [sampleConfirm, setSampleConfirm] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getAdoption(origin);
      setState({ status: "ready", data });
      // Offered, not applied: every undeclared candidate starts selected, and nothing is sent until confirmed.
      setSelected(new Set((data.candidate_list ?? []).filter((c) => !c.declared).map((c) => c.event_id)));
    } catch (error) {
      setState({ status: "error", ...codeOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  async function act(run: () => Promise<unknown>) {
    setBusy(true);
    setRefusal(null);
    try {
      await run();
      setRecorded(true);
      setConfirming(false);
      setNotRead(false);
      setSampleConfirm(null);
      await load();
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }

  const body = (() => {
    if (state.status === "loading") return <LoadingFrame heading={t("eyebrow")} sentence={t("loading")} />;
    if (state.status === "error") return <StateCard pageHeading locale={locale} code={state.code} message={state.message} consoleOrigin={origin} onRetry={() => void load()} />;
    const a = state.data;
    const open = (a.candidate_list ?? []).filter((c) => !c.declared);
    const chosen = open.filter((c) => selected.has(c.event_id));
    const exclusions = chosen.filter((c) => c.outcome === "EXCLUDE").length;
    const sizeValue = size.trim() === "" ? null : Number(size);
    const sampleValid = sizeValue === null || (Number.isInteger(sizeValue) && sizeValue >= 1 && sizeValue <= exclusions && /^\d+$/.test(seed));
    const outcomes = (o: Record<"INCLUDE" | "EXCLUDE" | "MAYBE", number>) => t("byOutcome", { e: n(o.EXCLUDE), i: n(o.INCLUDE), u: n(o.MAYBE) });

    return (
      <div className="space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{t("title")}</h1>
          <p className="mt-2 max-w-3xl text-ink-muted">{t("lede")}</p>
        </header>

        {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
        {recorded && !refusal ? <p role="status" className="rounded-md bg-include-soft px-4 py-3 text-include" data-recorded>{t("recorded")}</p> : null}
        {a.integrity.removed.length + a.integrity.unconfirmed.length > 0 ? (
          <p role="alert" className="rounded-md bg-unclear-soft px-4 py-3 text-ink" data-integrity>{t("integrity")}</p>
        ) : null}

        <section aria-labelledby="adopted-candidates" className="rounded-lg border border-rule bg-leaf p-5" data-candidates={open.length}>
          <h2 id="adopted-candidates" className="font-semibold text-ink">{t("candidatesTitle")}</h2>
          {open.length === 0 ? (
            <p className="mt-2 text-sm text-ink-muted">{t("candidatesNone")}</p>
          ) : (
            <>
              <p className="mt-2 text-sm text-ink">{t("candidatesBody", { n: n(open.length) })}</p>
              <p className="mt-1 text-sm text-ink-muted">{outcomes(a.undeclared_by_outcome)}</p>
              <details className="mt-3 text-sm">
                <summary className="min-h-11 cursor-pointer py-3 leading-5 text-brand rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("list")}</summary>
                <div className="mt-2 flex flex-wrap gap-3">
                  <Button variant="quiet" onClick={() => setSelected(new Set(open.map((c) => c.event_id)))}>{t("selectAll")}</Button>
                  <Button variant="quiet" onClick={() => setSelected(new Set())}>{t("selectNone")}</Button>
                </div>
                <ul className="mt-2 max-h-96 space-y-1 overflow-y-auto">
                  {open.map((c) => (
                    <li key={c.event_id} className="flex flex-wrap items-center gap-2" data-candidate={c.study_id}>
                      <label className="inline-flex min-h-11 items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selected.has(c.event_id)}
                          onChange={(e) => {
                            const next = new Set(selected);
                            if (e.target.checked) next.add(c.event_id);
                            else next.delete(c.event_id);
                            setSelected(next);
                          }}
                        />
                        <DataCell>{c.study_id}</DataCell>
                      </label>
                      <DecisionBadge role={OUTCOME_ROLE[c.outcome]}>{c.outcome}</DecisionBadge>
                      {c.note ? <bdi className="text-xs text-ink-muted">{c.note}</bdi> : null}
                    </li>
                  ))}
                </ul>
              </details>
              <p className="mt-3 text-sm text-ink" data-selected={chosen.length}>{t("selected", { n: n(chosen.length) })}</p>

              <label className="mt-3 block text-sm">
                {t("note")}
                <textarea value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} className="mt-1 block w-full max-w-xl rounded-md border border-rule bg-paper p-2 text-ink" rows={2} />
              </label>

              <fieldset className="mt-4 rounded-md border border-rule p-3">
                <legend className="px-1 text-sm font-semibold text-ink">{t("sampleTitle")}</legend>
                <p className="text-sm text-ink-muted">{t("sampleBody")}</p>
                <div className="mt-2 flex flex-wrap gap-4">
                  <label className="text-sm">
                    {t("sampleSize")}
                    <input type="number" min={1} max={Math.max(1, exclusions)} value={size} onChange={(e) => setSize(e.target.value)} className="mt-1 block w-28 rounded-md border border-rule bg-paper p-2 text-ink" data-sample-size />
                  </label>
                  <label className="text-sm">
                    {t("sampleSeed")}
                    <input inputMode="numeric" value={seed} onChange={(e) => setSeed(e.target.value.replace(/\D/g, ""))} className="mt-1 block w-36 rounded-md border border-rule bg-paper p-2 text-ink" dir="ltr" />
                  </label>
                </div>
              </fieldset>

              {confirming ? (
                <div role="alertdialog" aria-labelledby="adopted-confirm" className="mt-4 rounded-md border border-dashed border-brand bg-brand-soft p-4" onKeyDown={(e) => e.key === "Escape" && setConfirming(false)}>
                  <p id="adopted-confirm" className="font-semibold text-ink">{t("confirmTitle", { n: n(chosen.length) })}</p>
                  <p className="mt-1 text-sm text-ink">{t("confirmBody")}</p>
                  <label className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm text-ink">
                    {/* Focus moves into the dialog, on the confirmation the reviewer must give. */}
                    <input type="checkbox" autoFocus checked={notRead} onChange={(e) => setNotRead(e.target.checked)} />
                    {t("confirmCheck")}
                  </label>
                  <div className="mt-3 flex flex-wrap gap-3">
                    <Button
                      variant="primary"
                      disabled={busy || !notRead}
                      onClick={() =>
                        void act(() =>
                          declareAdoption(origin, {
                            event_ids: chosen.map((c) => c.event_id),
                            ...(note.trim() ? { note: note.trim() } : {}),
                            ...(sizeValue !== null ? { sample: { size: sizeValue, seed: Number(seed) } } : {}),
                          }),
                        )
                      }
                    >
                      {t("confirm")}
                    </Button>
                    <Button onClick={() => setConfirming(false)}>{t("cancel")}</Button>
                  </div>
                </div>
              ) : (
                <Button className="mt-4" variant="primary" disabled={chosen.length === 0 || !sampleValid} onClick={() => setConfirming(true)}>
                  {t("declare", { n: n(chosen.length) })}
                </Button>
              )}
            </>
          )}
        </section>

        <section aria-labelledby="adopted-declared" className="rounded-lg border border-rule bg-leaf p-5" data-declared={a.declared}>
          <h2 id="adopted-declared" className="font-semibold text-ink">{t("declaredTitle")}</h2>
          {a.declarations.length === 0 ? (
            <p className="mt-2 text-sm text-ink-muted">{t("declaredNone")}</p>
          ) : (
            <>
              <p className="mt-2 text-sm text-ink">{t("notCounted", { n: n(a.declared) })}</p>
              <ul className="mt-3 space-y-4 text-sm">
                {a.declarations.map((d) => {
                  const sample = a.samples.find((s) => s.declaration_id === d.declaration_id);
                  const total = d.counts.INCLUDE + d.counts.EXCLUDE + d.counts.MAYBE;
                  return (
                    <li key={d.declaration_id} className="border-t border-rule pt-3" data-declaration={d.declaration_id}>
                      <p className="text-ink">{t("declaredRow", { date: localDate(d.declared_at), n: n(total) })}</p>
                      <p className="text-ink-muted">{outcomes(d.counts)}</p>
                      {d.note ? <p className="text-ink-muted"><bdi>{d.note}</bdi></p> : null}
                      {sample ? (
                        <div className="mt-2" data-sample={sample.read ? "read" : "owed"}>
                          <p className="text-ink">{t("sampleOf", { k: n(sample.size), seed: String(sample.seed) })}</p>
                          <p className="text-ink-muted">
                            {sample.read ? t("sampleStatusRead", { c: n(sample.changed ?? 0), k: n(sample.size) }) : t("sampleStatusOwed")}
                          </p>
                          {!sample.read ? (
                            <>
                              <ul className="mt-1 flex flex-wrap gap-2">
                                {sample.study_ids.map((s) => (
                                  <li key={s}><DataCell>{s}</DataCell></li>
                                ))}
                              </ul>
                              <a className="mt-2 inline-flex min-h-11 items-center text-brand underline" href={`${stepHref(locale, "triage", origin)}${origin ? "&" : "?"}view=decided`}>{t("openTriage")}</a>
                              {sampleConfirm === sample.declaration_id ? (
                                <div role="alertdialog" aria-labelledby={`sample-${sample.declaration_id}`} className="mt-2 rounded-md border border-dashed border-brand bg-brand-soft p-3">
                                  <p id={`sample-${sample.declaration_id}`} className="text-ink">{t("recordSampleConfirm", { k: n(sample.size) })}</p>
                                  <div className="mt-2 flex flex-wrap gap-3">
                                    <Button variant="primary" disabled={busy} onClick={() => void act(() => recordAdoptionSample(origin, sample.declaration_id))}>{t("confirm")}</Button>
                                    <Button onClick={() => setSampleConfirm(null)}>{t("cancel")}</Button>
                                  </div>
                                </div>
                              ) : (
                                <Button className="mt-2" onClick={() => setSampleConfirm(sample.declaration_id)}>{t("recordSample", { k: n(sample.size) })}</Button>
                              )}
                            </>
                          ) : null}
                        </div>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>

        <a className="inline-block text-brand underline" href={stepHref(locale, "publish", origin)}>{t("toPublish")}</a>
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} consoleOrigin={origin} />
      {body}
    </div>
  );
}
