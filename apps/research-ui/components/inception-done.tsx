"use client";

import { useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, useDraft, type Refusal } from "@/components/inception-frame";
import { genesisStorageKey } from "@/components/inception-review";
import type { GenesisResult } from "@/lib/inception-api";
import { inceptionT } from "@/lib/inception-copy";
import { currentWorkspacePath, openWorkspace } from "@/lib/workspaces";

/**
 * Done (spec 07, M4b): what genesis wrote, and the way into the new workspace
 * through the existing `POST /workspaces/open` (the engine restarts on it, as
 * on the Workspaces screen), landing on screening Home. The backup path and the
 * previous fingerprint come from the genesis answer kept for this tab; a later
 * visit shows what the draft records (`emitted`).
 */
export function InceptionDone({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const state = useDraft();
  const { record, origin, draftId } = state;
  const [result, setResult] = useState<GenesisResult | null>(null);
  const [opening, setOpening] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (!record) return;
    let kept: GenesisResult | null = null;
    try {
      const raw = window.sessionStorage.getItem(genesisStorageKey(record.session_id));
      kept = raw ? (JSON.parse(raw) as GenesisResult) : null;
    } catch {
      kept = null;
    }
    if (kept && kept.slug === record.emitted?.slug) setResult(kept);
    else if (record.emitted) setResult({ session_id: record.session_id, ...record.emitted });
  }, [record]);

  // Arriving from Review, focus is on the page's heading (spec 07, Keyboard).
  useEffect(() => {
    if (result) heading.current?.focus();
  }, [result]);

  const open = async () => {
    if (!result || opening) return;
    setRefusal(null);
    setOpening(true);
    const landing = `/${locale}/screening/home/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`;
    try {
      const answer = await openWorkspace(origin, result.slug);
      if (!answer.restarting) {
        window.location.assign(landing);
        return;
      }
      // The engine restarts on the folder; wait until the new one answers for it.
      for (let attempt = 0; attempt < 120; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        try {
          if ((await currentWorkspacePath(origin)) === answer.path) {
            window.location.assign(landing);
            return;
          }
        } catch {
          // The old engine has stopped and the new one is not up yet.
        }
      }
      setRefusal({ code: "ENGINE_UNREACHABLE", message: "" });
    } catch (error) {
      setRefusal(refusalOf(error));
    }
    setOpening(false);
  };

  return (
    <InceptionFrame locale={locale} current="done" draft={state}>
      {result ? (
        <div className="space-y-5" data-done>
          <header>
            <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("done.kicker")}</p>
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink">
              {result.replaced ? t("done.titleReplaced") : t("done.title")}
            </h1>
            <p className="mt-2 max-w-2xl text-ink-muted">{t("done.lede")}</p>
          </header>
          <dl className="grid gap-3 rounded-lg border border-rule bg-leaf p-4 text-sm">
            <div>
              <dt className="text-ink-muted">{t("done.folder")}</dt>
              <dd data-done-path>
                <DataCell>{result.path}</DataCell>
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">{t("done.fingerprint")}</dt>
              <dd>
                <DataCell>{result.protocol_fingerprint}</DataCell>
              </dd>
            </div>
            {result.previous_fingerprint ? (
              <div>
                <dt className="text-ink-muted">{t("done.previous")}</dt>
                <dd>
                  <DataCell>{result.previous_fingerprint}</DataCell>
                </dd>
              </div>
            ) : null}
            {result.backup_dir ? (
              <div>
                <dt className="text-ink-muted">{t("done.backup")}</dt>
                <dd data-backup>
                  <DataCell>{result.backup_dir}</DataCell>
                </dd>
              </div>
            ) : null}
            {result.archived?.length ? (
              <div data-archived>
                <dt className="text-ink-muted">{t("done.archived")}</dt>
                {result.archived.map((path) => (
                  <dd key={path}>
                    <DataCell>{path}</DataCell>
                  </dd>
                ))}
                <dd className="mt-1 text-ink">{t("done.archivedNote")}</dd>
              </div>
            ) : null}
          </dl>
          {opening ? (
            <p role="status" className="text-lg text-ink" data-opening>
              {t("done.opening", { slug: result.slug })}
            </p>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="primary" onClick={() => void open()} data-open>
                {t("done.open")}
              </Button>
              <a className="inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/workspaces${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}>
                {t("done.allWorkspaces")}
              </a>
              <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "", "", origin)}>
                {t("done.another")}
              </a>
            </div>
          )}
          {refusal ? (
            <InceptionRefusal
              locale={locale}
              refusal={refusal}
              draftId={draftId}
              origin={origin}
              onRetry={() => void open()}
              command={refusal.code === "RESTART_UNSUPPORTED" ? `nexus-scholar ui --workspace "${result.path}"` : undefined}
            />
          ) : null}
        </div>
      ) : record ? (
        <div className="space-y-3">
          <h1 className="font-display text-3xl text-ink">{t("done.notEmitted")}</h1>
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "review", draftId, origin)}>
            {t("done.toReview")}
          </a>
        </div>
      ) : null}
    </InceptionFrame>
  );
}
