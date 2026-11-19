"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import type { Locale } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { InceptionRefusal, refusalOf, stamp, type Refusal } from "@/components/inception-frame";
import { DoiLink, isOffline } from "@/components/inception-recon";
import { inceptionT } from "@/lib/inception-copy";
import { saveDraft, type Draft, type DraftRecord } from "@/lib/inception-api";
import { changeSample, getSample, SAMPLE_CALL_MAX, type DistilledPaper, type Sample, type SampleExcluded } from "@/lib/recon-api";

/**
 * Sample curation on Explore (M10b Part C, 02-explore "Sample curation"). The
 * researcher leaves a paper of the sample out ("Not relevant") or puts it back;
 * each change is one `POST .../recon/sample` with the engine's key. The screen
 * patches nothing: it takes the engine's `sample` answer and re-reads the pool,
 * the directions and the concepts once. Which papers replace a left-out one,
 * every count and both recommendations are the engine's.
 */

const TOAST_MS = 8000;
/** The next-step bar (another component) re-reads when the review changed. */
const REVIEW_CHANGED = "nexus:review-changed";

type Kind = "mark" | "put" | "putAll";

interface Change {
  kind: Kind;
  key: string;
  title: string;
  add: string[];
  remove: string[];
  /** The total of a "Put back all", for the polite line (sent in chunks of 25). */
  count?: number;
  /** A saved seed left out with "Leave it out and remove it from the seeds": the draft `PUT` after the change. */
  seedDoi?: string;
}

export type SampleDialog = { kind: "bound" | "seed"; paper: DistilledPaper; opener: HTMLElement | null; then: () => void };

export interface SampleToast {
  id: number;
  kind: "mark" | "put";
  key: string;
  title: string;
}

/** What the pool reads answered (null when a later read superseded them). */
export type PoolRead = { directions: number | null; papers: number | null } | null;

export function useSampleCuration({
  locale,
  origin,
  draftId,
  record,
  draft,
  bound,
  grounded,
  directions,
  generation,
  searching,
  readPool,
  rereadRecon,
  adoptTime,
  adopt,
  bumpAssist,
}: {
  locale: Locale;
  origin: string;
  draftId: string;
  record: DraftRecord | null;
  draft: Draft;
  /** A direction is bound and not yet out of date: the first mark warns. */
  bound: boolean;
  /** The draft has a grounding: after a change the session is read again for its binding. */
  grounded: boolean;
  /** The directions count of the last read (the "before" of the polite line). */
  directions: number | null;
  /** Moves when the pool on screen is replaced (a new search): answers for the old pool are dropped. */
  generation: string;
  searching: boolean;
  readPool: () => Promise<PoolRead>;
  rereadRecon: () => Promise<void>;
  adoptTime: (updatedAt: string) => void;
  adopt: (record: DraftRecord) => void;
  bumpAssist: () => void;
}) {
  const t = inceptionT(locale);
  const [sample, setSample] = useState<Sample | null>(null);
  const [readError, setReadError] = useState<Refusal | null>(null);
  const [error, setError] = useState<Refusal | null>(null);
  const [rowError, setRowError] = useState<{ key: string; code: string } | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [announce, setAnnounce] = useState("");
  const [toast, setToast] = useState<SampleToast | null>(null);
  const [dialog, setDialog] = useState<SampleDialog | null>(null);
  const base = useRef<string | undefined>(record?.updated_at);
  const queue = useRef<Change[]>([]);
  const busy = useRef(false);
  const inFlight = useRef<string | null>(null);
  const epoch = useRef(0);
  const changeSeq = useRef(0);
  const readSeq = useRef(0);
  const toastId = useRef(0);
  const latest = useRef({ directions, draft, origin, draftId, readPool, rereadRecon, adoptTime, adopt, bumpAssist, bound, grounded });
  latest.current = { directions, draft, origin, draftId, readPool, rereadRecon, adoptTime, adopt, bumpAssist, bound, grounded };

  // The base of the next change is the draft's time as last read or answered.
  useEffect(() => {
    if (record?.updated_at) base.current = record.updated_at;
  }, [record?.updated_at]);

  // A new pool: nothing queued for the old one is sent, and an answer for it is dropped.
  useEffect(() => {
    epoch.current += 1;
    queue.current = [];
  }, [generation]);

  const read = useCallback(async () => {
    const mine = ++readSeq.current;
    try {
      const answer = await getSample(origin, draftId);
      if (mine !== readSeq.current) return;
      setSample(answer);
      setReadError(null);
    } catch (e) {
      if (mine !== readSeq.current) return;
      setReadError(refusalOf(e));
    }
  }, [origin, draftId]);

  const offline = isOffline(error?.code) || isOffline(readError?.code);
  const locked = error?.code === "DRAFT_CONFLICT" || error?.code === "DRAFT_EMITTED";
  const disabled = offline || locked || searching;

  const notify = () => {
    latest.current.bumpAssist();
    if (typeof window !== "undefined") window.dispatchEvent(new Event(REVIEW_CHANGED));
  };

  /** Re-read the pool, the directions and the concepts once; only the last change announces. */
  const reread = async (change: Change, before: number | null, answer: Sample) => {
    const mine = ++changeSeq.current;
    const after = await latest.current.readPool();
    if (!after || mine !== changeSeq.current) return;
    const values = { before: String(before ?? 0), after: String(after.directions ?? 0), n: String(after.papers ?? answer.n_docs) };
    setAnnounce(
      change.kind === "mark"
        ? t("sample.moved", { title: change.title, ...values })
        : change.kind === "put"
          ? t("sample.movedPut", { title: change.title, ...values })
          : t("sample.movedAll", { k: String(change.count ?? change.remove.length), ...values }),
    );
  };

  const pump = async (): Promise<void> => {
    if (busy.current) return;
    const change = queue.current.shift();
    if (!change) return;
    busy.current = true;
    inFlight.current = change.key;
    setPending(change.key);
    const at = epoch.current;
    const before = latest.current.directions;
    const { origin: o, draftId: id } = latest.current;
    try {
      const answer = await changeSample(o, id, {
        ...(change.add.length ? { add: change.add } : {}),
        ...(change.remove.length ? { remove: change.remove } : {}),
        ...(base.current ? { base_updated_at: base.current } : {}),
      });
      if (at !== epoch.current) return;
      base.current = answer.updated_at;
      latest.current.adoptTime(answer.updated_at);
      setSample(answer);
      setError(null);
      setRowError(null);
      if (change.seedDoi) {
        // As Direction saves seeds: the whole draft, every other field unchanged.
        const current = latest.current.draft;
        const seeds = (current.golden_seeds ?? []).filter((doi) => doi !== change.seedDoi);
        try {
          const { not_recorded: _missed, ...stored } = await saveDraft(o, id, { ...current, golden_seeds: seeds }, answer.updated_at);
          if (at !== epoch.current) return;
          base.current = stored.updated_at;
          latest.current.adopt(stored);
        } catch (e) {
          if (at !== epoch.current) return;
          setError(refusalOf(e));
          setRowError({ key: change.key, code: refusalOf(e).code });
        }
      }
      notify();
      if (change.kind === "mark") setToast({ id: ++toastId.current, kind: "mark", key: change.key, title: change.title });
      else if (change.kind === "put") setToast({ id: ++toastId.current, kind: "put", key: change.key, title: change.title });
      // A bound direction may now be out of date (`SAMPLE_CHANGED`), or current again after a put-back.
      if (latest.current.grounded) void latest.current.rereadRecon();
      void reread(change, before, answer);
    } catch (e) {
      if (at !== epoch.current) return;
      const refusal = refusalOf(e);
      setError(refusal);
      setRowError({ key: change.key, code: refusal.code });
      // Nothing waits behind a refusal: a change that is not saved is not shown as saved.
      queue.current = [];
    } finally {
      busy.current = false;
      inFlight.current = null;
      setPending(null);
      void pump();
    }
  };

  const enqueue = (change: Change) => {
    if (disabled) return;
    if (inFlight.current === change.key || queue.current.some((c) => c.key === change.key)) return;
    queue.current.push(change);
    void pump();
  };

  /** "Not relevant": the bound-direction warning first, then the seed warning, then the change. */
  const mark = (paper: DistilledPaper, opener: HTMLElement | null, focusNext: () => void) => {
    const key = paper.key;
    if (!key || disabled) return;
    const title = paper.title ?? key;
    const isSeed = !!paper.doi && (latest.current.draft.golden_seeds ?? []).includes(paper.doi);
    const send = (withSeed: boolean) => {
      enqueue({ kind: "mark", key, title, add: [key], remove: [], ...(withSeed && paper.doi ? { seedDoi: paper.doi } : {}) });
      setTimeout(focusNext, 0);
    };
    const afterBound = () => {
      if (isSeed) setDialog({ kind: "seed", paper, opener, then: () => send(true) });
      else send(false);
    };
    if (latest.current.bound) setDialog({ kind: "bound", paper, opener, then: afterBound });
    else afterBound();
  };

  const put = (item: SampleExcluded) => enqueue({ kind: "put", key: item.key, title: item.title ?? item.key, add: [], remove: [item.key] });

  const putAll = () => {
    const keys = (sample?.excluded ?? []).map((e) => e.key);
    for (let i = 0; i < keys.length; i += SAMPLE_CALL_MAX) {
      const chunk = keys.slice(i, i + SAMPLE_CALL_MAX);
      enqueue({ kind: "putAll", key: `*all*${i}`, title: "", add: [], remove: chunk, count: keys.length });
    }
  };

  const undo = (item: SampleToast) => {
    setToast(null);
    enqueue({ kind: "put", key: item.key, title: item.title, add: [], remove: [item.key] });
  };

  const confirmDialog = () => {
    const current = dialog;
    setDialog(null);
    current?.then();
  };

  const cancelDialog = () => {
    const opener = dialog?.opener ?? null;
    setDialog(null);
    setTimeout(() => opener?.focus(), 0);
  };

  /** `PAPER_UNKNOWN`'s "Reload the papers", and the offline card's "Try again": the papers and the sample again. */
  const reload = () => {
    setError(null);
    setRowError(null);
    void read();
    void latest.current.readPool();
  };

  return { sample, readError, error, rowError, pending, announce, toast, setToast, dialog, disabled, offline, locked, read, mark, put, putAll, undo, confirmDialog, cancelDialog, reload };
}

export type Curation = ReturnType<typeof useSampleCuration>;

/** The change's refusal card (and the limit of `SAMPLE_EXCLUSIONS_FULL`, from the engine's details). */
export function SampleRefusal({ locale, curation, draftId, origin }: Readonly<{ locale: Locale; curation: Curation; draftId: string; origin: string }>) {
  const t = inceptionT(locale);
  const error = curation.error;
  if (!error) return null;
  const limit = (error.details as { limit?: unknown } | undefined)?.limit;
  const retry = error.code === "PAPER_UNKNOWN" || isOffline(error.code) ? curation.reload : undefined;
  return (
    <div className="mt-3 space-y-2" data-sample-refusal={error.code}>
      <InceptionRefusal locale={locale} refusal={error} draftId={draftId} origin={origin} onRetry={retry} />
      {error.code === "SAMPLE_EXCLUSIONS_FULL" && limit != null ? (
        <p className="text-sm text-ink" data-sample-limit>
          {t("sample.limit", { limit: String(limit) })}
        </p>
      ) : null}
    </div>
  );
}

/** "Left out · {k}": a disclosure listing every left-out paper, each with "Put back". */
export function LeftOutList({ locale, curation, toggleRef }: Readonly<{ locale: Locale; curation: Curation; toggleRef: RefObject<HTMLButtonElement | null> }>) {
  const t = inceptionT(locale);
  const [open, setOpen] = useState(false);
  const excluded = curation.sample?.excluded ?? [];
  if (!excluded.length) return null;
  const notInPool = excluded.filter((e) => !e.in_pool).length;
  return (
    <section className="mt-4 rounded-md border border-rule bg-paper p-3" data-left-out>
      <h3 className="text-sm">
        <button
          ref={toggleRef}
          type="button"
          className="inline-flex min-h-11 w-full items-center text-start font-semibold text-ink"
          aria-expanded={open}
          aria-controls="sample-left-out"
          onClick={() => setOpen(!open)}
          data-left-out-toggle
        >
          {t("sample.left.title", { k: String(excluded.length) })}
        </button>
      </h3>
      <div id="sample-left-out" hidden={!open}>
        <p className="text-xs text-ink-muted">{t("sample.left.help")}</p>
        {notInPool ? (
          <p className="mt-1 text-xs text-ink-muted" data-not-in-pool-count>
            {t("sample.left.notInPoolCount", { k: String(notInPool) })}
          </p>
        ) : null}
        <ul className="mt-2 space-y-3 text-sm">
          {excluded.map((item) => (
            <li key={item.key} className="border-t border-rule pt-2" data-left-out-item={item.key}>
              <span dir="auto" className="block text-ink [overflow-wrap:anywhere]">
                {item.title ?? item.key}
              </span>
              <span className="block text-xs text-ink-muted">
                {item.year != null ? <bdi dir="ltr">{String(item.year)}</bdi> : null}
                {item.year != null && item.provider ? " · " : null}
                {item.provider ? <bdi dir="ltr">{item.provider}</bdi> : null}
              </span>
              <span className="block text-xs text-ink" data-left-out-when>
                {t("sample.left.when", { date: "" })}
                <bdi dir="ltr">{stamp(item.excluded_at)}</bdi>
              </span>
              {!item.in_pool ? (
                <span className="mt-1 inline-block" data-not-in-pool>
                  <DecisionBadge role="exclude">{t("sample.left.notInPool")}</DecisionBadge>
                </span>
              ) : null}
              {item.doi ? <DoiLink locale={locale} doi={item.doi} title={item.title} /> : null}
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <Button
                  disabled={curation.disabled || curation.pending === item.key}
                  aria-busy={curation.pending === item.key || undefined}
                  aria-label={t("sample.put.label", { title: item.title ?? item.key })}
                  onClick={() => {
                    curation.put(item);
                    setTimeout(() => toggleRef.current?.focus(), 0);
                  }}
                  data-put={item.key}
                >
                  {t("sample.put")}
                </Button>
                <RowError locale={locale} curation={curation} rowKey={item.key} />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

/** The error beside the button of the row whose change was refused; the row is not moved. */
export function RowError({ locale, curation, rowKey }: Readonly<{ locale: Locale; curation: Curation; rowKey: string }>) {
  const t = inceptionT(locale);
  if (curation.rowError?.key !== rowKey) return null;
  return (
    <span className="text-xs text-blocked" data-row-error>
      {t("sample.notSaved")} · <bdi dir="ltr">{curation.rowError.code}</bdi>
    </span>
  );
}

/**
 * The toast after a change: "Left out: {title}" with Undo, for 8 seconds; it
 * does not time out while it has focus, and `Escape` closes it without undoing.
 */
export function SampleToastView({ locale, curation, onClosed }: Readonly<{ locale: Locale; curation: Curation; onClosed: () => void }>) {
  const t = inceptionT(locale);
  const toast = curation.toast;
  const [focused, setFocused] = useState(false);
  const { setToast } = curation;
  useEffect(() => {
    if (!toast || focused) return;
    const timer = setTimeout(() => setToast((current) => (current?.id === toast.id ? null : current)), TOAST_MS);
    return () => clearTimeout(timer);
  }, [toast, focused, setToast]);
  if (!toast) return null;
  const close = () => {
    setFocused(false);
    setToast(null);
    onClosed();
  };
  return (
    <div
      role="status"
      className="fixed bottom-24 end-4 z-40 flex max-w-sm flex-wrap items-center gap-3 rounded-lg border border-rule-strong bg-paper p-3 text-sm text-ink shadow-lg"
      onFocus={() => setFocused(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setFocused(false);
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          close();
        }
      }}
      data-sample-toast={toast.kind}
    >
      <span dir="auto">{toast.kind === "mark" ? t("sample.toast", { title: toast.title }) : t("sample.toast.put", { title: toast.title })}</span>
      {toast.kind === "mark" ? (
        <Button
          disabled={curation.disabled}
          onClick={() => {
            setFocused(false);
            curation.undo(toast);
            onClosed();
          }}
          data-undo
        >
          {t("sample.undo")}
        </Button>
      ) : null}
    </div>
  );
}

/** The two warnings before a mark: a bound direction would go out of date; the paper is a saved seed. */
export function SampleDialogView({ locale, curation, direction }: Readonly<{ locale: Locale; curation: Curation; direction: string }>) {
  const t = inceptionT(locale);
  const keep = useRef<HTMLButtonElement>(null);
  const dialog = curation.dialog;
  useEffect(() => {
    if (dialog) keep.current?.focus();
  }, [dialog]);
  if (!dialog) return null;
  const k = dialog.kind === "bound" ? "warnBound" : "warnSeed";
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="sample-warn-title"
        aria-describedby="sample-warn-body"
        className="w-full max-w-lg rounded-lg border border-rule bg-paper p-5"
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            curation.cancelDialog();
          }
        }}
        data-sample-warning={dialog.kind}
      >
        <h2 id="sample-warn-title" className="font-semibold text-ink">
          {t(`sample.${k}.title`)}
        </h2>
        <p id="sample-warn-body" className="mt-2 text-sm text-ink">
          <bdi>{dialog.kind === "bound" ? t("sample.warnBound.body", { direction }) : t("sample.warnSeed.body")}</bdi>
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button ref={keep} onClick={curation.cancelDialog} data-warn-keep>
            {t(`sample.${k}.keep`)}
          </Button>
          <Button onClick={curation.confirmDialog} data-warn-go>
            {t(`sample.${k}.go`)}
          </Button>
        </div>
      </div>
    </div>
  );
}
