"use client";

import { Fragment, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { copyNoticeSeen, markCopyNoticeSeen } from "@/lib/copy-notice";
import { getPreparation, type WorkspacePreparation } from "@/lib/workspaces";

/**
 * The copy made before a newer version opens a review (H-workspace-format-version).
 *
 * The engine answers every workspace route with `WORKSPACE_PREPARING` while it
 * saves the copy, so this wrapper asks `GET /workspaces/preparation` once per
 * page and, while a copy runs, shows which review is being copied and how far
 * it is instead of the page; when the copy is done the page is mounted afresh.
 * After a copy it shows a one-time notice naming the folder; a refused review
 * shows its state card. The Workspaces screen is never replaced: from there
 * the researcher can open another review. A failed read (an older engine, a
 * test without the route) leaves the page as it is: the engine still refuses.
 */

const POLL_MS = 1000;

const COPY = {
  en: {
    "panel.title": "Saving a copy of {title} before opening it",
    "panel.reason.build": "This version of Nexus Scholar is newer than the one that last opened this review. It saves a copy of the review first, in case you want to go back.",
    "panel.reason.format": "This version of Nexus Scholar stores reviews in a newer way. It saves a copy of the review first, in case you want to go back.",
    "panel.progress": "{done} of {total} MB",
    "panel.label": "Copy of the review",
    "panel.after": "The review opens by itself when the copy is done. Please keep this window open.",
    "notice.body": "Before opening this review, Nexus Scholar saved a copy of it in {folder}. You do not need to do anything.",
    "notice.dismiss": "Dismiss",
    "refused.workspaces": "Go to the workspaces",
  },
  fr: {
    "panel.title": "Enregistrement d'une copie de {title} avant de l'ouvrir",
    "panel.reason.build": "Cette version de Nexus Scholar est plus récente que celle qui a ouvert cette revue en dernier. Elle enregistre d'abord une copie de la revue, au cas où vous voudriez revenir en arrière.",
    "panel.reason.format": "Cette version de Nexus Scholar enregistre les revues d'une manière plus récente. Elle enregistre d'abord une copie de la revue, au cas où vous voudriez revenir en arrière.",
    "panel.progress": "{done} sur {total} Mo",
    "panel.label": "Copie de la revue",
    "panel.after": "La revue s'ouvre d'elle-même une fois la copie terminée. Gardez cette fenêtre ouverte.",
    "notice.body": "Avant d'ouvrir cette revue, Nexus Scholar en a enregistré une copie dans {folder}. Vous n'avez rien à faire.",
    "notice.dismiss": "Fermer",
    "refused.workspaces": "Aller aux espaces de travail",
  },
  ar: {
    "panel.title": "جارٍ حفظ نسخة من {title} قبل فتحها",
    "panel.reason.build": "هذا الإصدار من Nexus Scholar أحدث من الإصدار الذي فتح هذه المراجعة آخر مرة. يحفظ أولًا نسخة من المراجعة تحسّبًا لرغبتك في العودة إليها.",
    "panel.reason.format": "يحفظ هذا الإصدار من Nexus Scholar المراجعات بطريقة أحدث. يحفظ أولًا نسخة من المراجعة تحسّبًا لرغبتك في العودة إليها.",
    "panel.progress": "{done} من {total} ميغابايت",
    "panel.label": "نسخة المراجعة",
    "panel.after": "تُفتح المراجعة من تلقاء نفسها عند اكتمال النسخ. يُرجى إبقاء هذه النافذة مفتوحة.",
    "notice.body": "قبل فتح هذه المراجعة، حفظ Nexus Scholar نسخة منها في {folder}. لا تحتاج إلى فعل أي شيء.",
    "notice.dismiss": "إغلاق",
    "refused.workspaces": "الانتقال إلى مساحات العمل",
  },
} as const;

export type PreparationCopyKey = keyof (typeof COPY)["en"];
export const PREPARATION_COPY: Record<Locale, Record<PreparationCopyKey, string>> = COPY;

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => String(values[k] ?? `{${k}}`));
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function megabytes(locale: Locale, bytes: number): string {
  return formatNumber(locale, Math.round(bytes / 1e6));
}

export function isWorkspacesRoute(pathname: string): boolean {
  return /^\/[^/]+\/workspaces\/?$/.test(pathname);
}

export function WorkspacePreparationGate({
  locale,
  pathname,
  children,
}: Readonly<{ locale: Locale; pathname: string; children: ReactNode }>) {
  const t = useCallback((key: PreparationCopyKey, values?: Record<string, string | number>) => fill(PREPARATION_COPY[locale][key], values), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [preparation, setPreparation] = useState<WorkspacePreparation | null>(null);
  const [generation, setGeneration] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const onWorkspaces = isWorkspacesRoute(pathname);

  useEffect(() => {
    if (onWorkspaces) return; // never replaced, and its rows show the state
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    let wasPreparing = false;
    const read = async () => {
      let next: WorkspacePreparation | null;
      try {
        next = await getPreparation(origin, controller.signal);
      } catch {
        return; // an older engine or no engine: leave the page as it is
      }
      if (controller.signal.aborted) return;
      setPreparation(next);
      if (next?.state === "preparing") {
        wasPreparing = true;
        timer = setTimeout(() => void read(), POLL_MS);
      } else if (wasPreparing) {
        setGeneration((g) => g + 1); // mount the page afresh: its reads were refused while copying
      }
    };
    void read();
    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [origin, onWorkspaces]);

  const copy = preparation?.state === "ready" ? preparation.result?.copy ?? null : null;
  const showNotice = copy !== null && !dismissed && !copyNoticeSeen(copy.name);

  if (preparation?.state === "preparing" && !onWorkspaces) {
    const total = Math.max(preparation.total_bytes, 1);
    const percent = Math.min(100, Math.round((preparation.done_bytes / total) * 100));
    return (
      <section className="mx-auto max-w-2xl px-4 py-16 sm:px-6" role="status" aria-live="polite" data-preparing={preparation.slug}>
        <h1 className="font-display text-2xl font-semibold text-ink">{t("panel.title", { title: preparation.title })}</h1>
        <p className="mt-3 text-ink-muted">{t(preparation.reason === "build" ? "panel.reason.build" : "panel.reason.format")}</p>
        <div
          className="mt-6 h-3 w-full overflow-hidden rounded-sm border border-rule bg-paper"
          role="progressbar"
          aria-label={t("panel.label")}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
        >
          <div className="h-full bg-brand" style={{ inlineSize: `${percent}%` }} />
        </div>
        <p className="mt-2 text-sm text-ink-muted">
          {t("panel.progress", { done: megabytes(locale, preparation.done_bytes), total: megabytes(locale, preparation.total_bytes) })}
        </p>
        <p className="mt-6 text-sm text-ink-muted">{t("panel.after")}</p>
      </section>
    );
  }

  if (preparation?.state === "refused" && preparation.refusal && !onWorkspaces) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6" data-preparation-refused={preparation.refusal.code}>
        <StateCard locale={locale} code={preparation.refusal.code} message={preparation.refusal.message} consoleOrigin={origin} pageHeading onRetry={() => window.location.reload()} />
        <p className="mt-4">
          <a className="inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/workspaces/`}>
            {t("refused.workspaces")}
          </a>
        </p>
      </div>
    );
  }

  return (
    <>
      {showNotice && copy ? (
        <div className="mx-auto max-w-7xl px-4 pt-4 sm:px-6 lg:px-8" data-copy-notice={copy.name}>
          <div className="flex flex-wrap items-start justify-between gap-3 rounded-lg border border-rule border-s-4 border-s-include bg-leaf p-4" role="status">
            <p className="text-sm text-ink">
              {PREPARATION_COPY[locale]["notice.body"].split("{folder}")[0]}
              <bdi dir="ltr" className="font-mono">{copy.folder}</bdi>
              {PREPARATION_COPY[locale]["notice.body"].split("{folder}")[1]}
            </p>
            <Button
              onClick={() => {
                markCopyNoticeSeen(copy.name);
                setDismissed(true);
              }}
            >
              {t("notice.dismiss")}
            </Button>
          </div>
        </div>
      ) : null}
      <Fragment key={generation}>{children}</Fragment>
    </>
  );
}
