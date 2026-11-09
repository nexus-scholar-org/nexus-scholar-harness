"use client";

import { useCallback, useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell } from "@/components/ui/base";
import { inceptionHref, InceptionRefusal, refusalOf, stamp, useLocationParams, type Refusal } from "@/components/inception-frame";
import { createDraft, listDrafts, type DraftListing } from "@/lib/inception-api";
import { inceptionT } from "@/lib/inception-copy";

/**
 * Inception start and resume (spec 08, M4b): the drafts under the workspaces
 * root and one way to start a new review. A draft that already created a
 * workspace links to Done; one the engine cannot read is listed, with no action.
 */
export function InceptionStart({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const { origin, ready } = useLocationParams();
  const [listing, setListing] = useState<DraftListing | null>(null);
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    setLoadError(null);
    if (!ready) return;
    try {
      setListing(await listDrafts(origin));
    } catch (error) {
      setLoadError(refusalOf(error));
    }
  }, [origin, ready]);

  useEffect(() => {
    void load();
  }, [load]);

  const start = async () => {
    if (starting) return;
    setStarting(true);
    setRefusal(null);
    try {
      const made = await createDraft(origin, {});
      window.location.assign(inceptionHref(locale, "scope", made.session_id, origin));
    } catch (error) {
      setRefusal(refusalOf(error));
      setStarting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
      <nav className="mb-6 text-sm">
        <a className="inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/workspaces${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}>
          {t("backToWorkspaces")}
        </a>
      </nav>
      <header className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
        <h1 className="mt-2 font-display text-3xl text-ink">{t("start.title")}</h1>
        <p className="mt-2 max-w-2xl text-ink-muted">{t("start.lede")}</p>
        <div className="mt-4">
          <Button variant="primary" onClick={() => void start()} disabled={starting || Boolean(loadError)} data-start>
            {starting ? t("start.creating") : t("start.new")}
          </Button>
        </div>
      </header>

      {refusal ? <InceptionRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void start()} /> : null}

      {loadError ? (
        <InceptionRefusal locale={locale} refusal={loadError} origin={origin} onRetry={() => void load()} />
      ) : !listing ? (
        <p role="status" className="text-ink-muted">
          {t("loading")}
        </p>
      ) : (
        <section aria-labelledby="drafts-title" className="space-y-3">
          <h2 id="drafts-title" className="font-semibold text-ink">
            {t("start.listTitle")}
          </h2>
          {listing.items.length === 0 ? (
            <p className="rounded-lg border border-rule bg-leaf p-5 text-ink-muted" data-empty>
              {t("start.empty")}
            </p>
          ) : (
            <ul className="divide-y divide-rule rounded-lg border border-rule bg-leaf" aria-label={t("start.listCaption", { root: listing.root })}>
              {listing.items.map((item) => (
                <li key={item.session_id} className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between" data-draft-row={item.session_id}>
                  <div className="min-w-0">
                    {item.readable ? (
                      <>
                        <p className="font-medium text-ink">{item.title || (item.topic ? t("start.untitled") : t("start.emptyDraft"))}</p>
                        <p className="text-sm text-ink-muted [overflow-wrap:anywhere]">{item.topic || t("start.noTopic")}</p>
                      </>
                    ) : (
                      <p className="text-ink" data-unreadable>
                        {t("start.unreadable")}
                      </p>
                    )}
                    <p className="mt-1 flex flex-wrap gap-x-3 text-xs text-ink-muted">
                      <DataCell>{item.session_id}</DataCell>
                      {item.updated_at ? (
                        <span>
                          {t("start.updated", { at: "" })}
                          <bdi dir="ltr">{stamp(item.updated_at)}</bdi>
                        </span>
                      ) : null}
                    </p>
                    {item.emitted ? (
                      <p className="mt-1 text-sm text-include" data-emitted>
                        {t("start.emitted", { slug: "" })}
                        <bdi dir="ltr">{item.emitted.slug}</bdi>
                      </p>
                    ) : null}
                  </div>
                  {item.readable ? (
                    <a
                      className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-md border border-rule-strong bg-leaf px-4 text-ink hover:bg-leaf-raised"
                      href={inceptionHref(locale, item.emitted ? "done" : "scope", item.session_id, origin)}
                    >
                      {item.emitted ? t("start.seeDone") : t("start.resume")}
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
          <p className="text-sm text-ink-muted">
            {t("start.terminal")} <code className="rounded-sm bg-paper px-1 font-mono text-[0.8125rem]" dir="ltr">uv run scholar-harness inception</code>
          </p>
        </section>
      )}
    </div>
  );
}
