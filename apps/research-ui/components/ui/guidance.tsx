"use client";

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { guidanceT } from "@/lib/guidance-copy";

/**
 * The guidance components of `docs/ux/shared/final/03-guidance.md` (M10d).
 *
 * - `Hint` (rule 1): an icon-only button beside a label or heading that shows
 *   one plain sentence of help. The text stays in the DOM while closed (the
 *   field's `aria-describedby` reads it), so a screen reader hears it without
 *   opening anything. It holds a string, never markup: a warning, a refusal or
 *   a control cannot be put inside one.
 * - `RecommendedBadge` (rule 3): the word "Recommended" with its source, on a
 *   neutral dashed outline, followed by the hint that holds the why. It never
 *   selects anything.
 * - `Fold` (rule 4, use 2): a secondary card collapsed behind its own title and
 *   count; a failing item is named in the summary, so it is never one click away.
 */

const FOCUS = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

/** One open hint per page: opening one closes the others. */
const OPEN_EVENT = "nexus-hint-open";

export type HintPlacement = { side: "inline-end" | "below" | "inline-start"; left: number; top: number; width: number };

const GAP = 8;
const MARGIN = 16;
const MAX_WIDTH = 384;

/**
 * Where the panel goes (rule 1.5): beside the button on its inline-end side,
 * else below it, else on its inline-start side. Sides are logical, so in a
 * right-to-left page the first choice is the physical left. Below 640 px the
 * panel sits below the button and spans the content width.
 */
export function hintPlacement(
  rect: { left: number; right: number; top: number; bottom: number },
  viewport: { width: number; height: number },
  rtl: boolean,
  height = 0,
): HintPlacement {
  const width = Math.min(MAX_WIDTH, viewport.width - 2 * MARGIN);
  const clamp = (x: number) => Math.max(MARGIN, Math.min(x, viewport.width - MARGIN - width));
  const below = { side: "below" as const, top: rect.bottom + 4, width };
  if (viewport.width <= 640) return { ...below, left: MARGIN, width: viewport.width - 2 * MARGIN };
  const endLeft = rtl ? rect.left - GAP - width : rect.right + GAP;
  if (endLeft >= MARGIN && endLeft + width <= viewport.width - MARGIN) return { side: "inline-end", left: endLeft, top: rect.top, width };
  if (!height || rect.bottom + 4 + height <= viewport.height - MARGIN) return { ...below, left: clamp(rtl ? rect.right - width : rect.left) };
  const startLeft = rtl ? rect.right + GAP : rect.left - GAP - width;
  if (startLeft >= MARGIN && startLeft + width <= viewport.width - MARGIN) return { side: "inline-start", left: startLeft, top: rect.top, width };
  return { ...below, left: clamp(rtl ? rect.right - width : rect.left) };
}

function InfoGlyph() {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="8" cy="8" r="6.5" />
      <path d="M8 7.25v3.75" />
      <circle cx="8" cy="4.9" r="0.4" fill="currentColor" />
    </svg>
  );
}

/**
 * A hint (rule 1). `label` is the visible text of the label or heading it sits
 * beside, `text` the moved sentence, `textKey` its catalog key (written to
 * `data-hint-body` so the audit can check what is hidden). `id` lets a field
 * keep its `aria-describedby` on the same id as the paragraph it replaces.
 * An empty `text` renders nothing (never an empty popover).
 */
export function Hint({
  locale,
  label,
  text,
  textKey,
  id,
  className = "",
}: Readonly<{ locale: Locale; label: string; text: string; textKey: string; id?: string; className?: string }>) {
  const t = guidanceT(locale);
  const own = useId();
  const panelId = id ?? `hint-${own.replace(/[^A-Za-z0-9_-]/g, "")}`;
  const [open, setOpen] = useState(false);
  const [place, setPlace] = useState<HintPlacement | null>(null);
  const button = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLSpanElement>(null);
  const wrapper = useRef<HTMLSpanElement>(null);

  const measure = useCallback(() => {
    const b = button.current;
    if (!b) return;
    const rtl = b.closest("[dir]")?.getAttribute("dir") === "rtl";
    setPlace(hintPlacement(b.getBoundingClientRect(), { width: window.innerWidth, height: window.innerHeight }, rtl, panel.current?.offsetHeight ?? 0));
  }, []);

  useLayoutEffect(() => {
    if (open) measure();
  }, [open, measure]);

  useEffect(() => {
    if (!open) return;
    const others = (event: Event) => {
      if ((event as CustomEvent<string>).detail !== panelId) setOpen(false);
    };
    const outside = (event: PointerEvent) => {
      if (wrapper.current && !wrapper.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener(OPEN_EVENT, others);
    document.addEventListener("pointerdown", outside);
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => {
      document.removeEventListener(OPEN_EVENT, others);
      document.removeEventListener("pointerdown", outside);
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
    };
  }, [open, panelId, measure]);

  if (!text.trim()) return null;

  const toggle = () => {
    const next = !open;
    if (next) document.dispatchEvent(new CustomEvent(OPEN_EVENT, { detail: panelId }));
    setOpen(next);
  };

  return (
    <span
      ref={wrapper}
      className={`relative inline-flex align-middle ${className}`.trim()}
      data-hint
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          event.stopPropagation();
          setOpen(false);
          button.current?.focus();
        }
      }}
      onBlur={(event) => {
        if (open && !wrapper.current?.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}
    >
      <button
        ref={button}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={t("guidance.hint.open", { label })}
        onClick={toggle}
        data-hint-button={textKey}
        className={`-my-3 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ink-muted hover:text-ink aria-expanded:bg-leaf-raised aria-expanded:text-ink ${FOCUS}`}
      >
        <InfoGlyph />
      </button>
      <span
        ref={panel}
        id={panelId}
        role="note"
        dir="auto"
        hidden={!open}
        data-hint-body={textKey}
        data-placement={open && place ? place.side : undefined}
        style={open && place ? { position: "fixed", left: place.left, top: place.top, width: place.width } : undefined}
        className="z-50 block max-w-[24rem] rounded-md border border-rule bg-leaf p-3 text-start text-[0.8125rem] font-normal normal-case leading-5 tracking-normal text-ink shadow-overlay"
      >
        {text}
      </span>
    </span>
  );
}

/**
 * The Recommended mark (rule 3): a word, never a colour alone, with its source
 * always visible and the why behind a hint. It renders nothing without a source.
 */
export function RecommendedBadge({
  locale,
  source,
  why,
  whyKey,
}: Readonly<{ locale: Locale; source: string; why?: string; whyKey?: string }>) {
  const t = guidanceT(locale);
  if (!source.trim()) return null;
  return (
    <span className="inline-flex items-center gap-0.5 align-middle" data-recommended>
      <span className="inline-flex items-center rounded-sm border border-dashed border-ink-muted bg-leaf-raised px-2 py-0.5 text-xs font-semibold leading-4 text-ink">
        {t("guidance.recommended.by", { source })}
      </span>
      {why && whyKey ? <Hint locale={locale} label={t("guidance.recommended")} text={why} textKey={whyKey} /> : null}
    </span>
  );
}

const SUMMARY = `flex min-h-11 cursor-pointer list-none items-center gap-2 rounded-sm py-2 ${FOCUS}`;

/**
 * A collapsed secondary card (rule 4, use 2): the summary is the card's own
 * title and count; `failed` (a count with its word) is a role badge inside the
 * summary. Closed by default; the content stays in the DOM.
 */
export function Fold({
  locale,
  title,
  count,
  failed,
  headingId,
  children,
  className = "",
  ...rest
}: Readonly<{ locale: Locale; title: string; count?: number; failed?: number; headingId?: string; children: ReactNode; className?: string } & Record<`data-${string}`, string | boolean | undefined>>) {
  const t = guidanceT(locale);
  return (
    <details className={`group rounded-lg border border-rule bg-leaf px-4 ${className}`.trim()} data-fold {...rest}>
      <summary className={SUMMARY}>
        <span aria-hidden="true" className="text-ink-muted transition-none group-open:rotate-90 rtl:-scale-x-100">
          ›
        </span>
        <h2 id={headingId} className="font-semibold text-ink">
          {count === undefined ? title : t("guidance.section.count", { title, n: count })}
        </h2>
        {failed ? (
          <span data-role="blocked" className="inline-flex items-center rounded-sm bg-blocked-soft px-2 py-0.5 text-xs font-semibold leading-4 text-blocked">
            {t("guidance.section.failed", { n: failed })}
          </span>
        ) : null}
      </summary>
      <div className="pb-4">{children}</div>
    </details>
  );
}
