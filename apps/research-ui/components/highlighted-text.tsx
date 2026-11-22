import { Fragment, type ReactNode } from "react";

/**
 * A text with marks laid over it (M8b-triage-highlights, spec 03 point 1).
 *
 * Takes any text and two lists of spans: search-term spans, each with a mark
 * style, and quote spans, each with a key. Offsets count UTF-16 code units, as
 * the engine sends them. The text is never altered: a span out of range,
 * reversed, or cutting a surrogate pair is dropped. Term spans are drawn inside
 * quote spans, so both read where they overlap. Reused by full text (M12a).
 */

/** The five term mark styles: four concepts, then one shared by the rest. */
export const TERM_STYLES = 5;
export const OTHER_STYLE = TERM_STYLES - 1;

export interface TermSpan {
  start: number;
  end: number;
  /** 0 to 3 for the first four concepts, 4 for the others. */
  style: number;
}

export interface QuoteSpan {
  start: number;
  end: number;
  key: string;
}

export interface Segment {
  start: number;
  end: number;
  style: number | null;
  quotes: string[];
}

/** Classes of each term style: the line style carries the identity, colour only helps. */
const TERM_CLASS = [
  "underline decoration-solid decoration-brand decoration-2",
  "underline decoration-double decoration-ink decoration-1",
  "underline decoration-dashed decoration-brand decoration-2",
  "underline decoration-dotted decoration-ink decoration-2",
  "underline decoration-wavy decoration-ink-muted decoration-1",
];

export function termClass(style: number): string {
  return `${TERM_CLASS[Math.min(Math.max(style, 0), OTHER_STYLE)]} underline-offset-[0.2em] [text-decoration-skip-ink:none]`;
}

function splitsPair(text: string, at: number): boolean {
  if (at <= 0 || at >= text.length) return false;
  const before = text.charCodeAt(at - 1);
  const after = text.charCodeAt(at);
  return before >= 0xd800 && before <= 0xdbff && after >= 0xdc00 && after <= 0xdfff;
}

function valid(text: string, s: { start: number; end: number }): boolean {
  return (
    Number.isInteger(s.start) &&
    Number.isInteger(s.end) &&
    s.start >= 0 &&
    s.start < s.end &&
    s.end <= text.length &&
    !splitsPair(text, s.start) &&
    !splitsPair(text, s.end)
  );
}

/** The text cut at every span boundary, each piece with its term style and the quotes over it. */
export function segment(text: string, terms: readonly TermSpan[], quotes: readonly QuoteSpan[]): Segment[] {
  const t = terms.filter((s) => valid(text, s));
  const q = quotes.filter((s) => valid(text, s));
  const cuts = new Set<number>([0, text.length]);
  for (const s of [...t, ...q]) {
    cuts.add(s.start);
    cuts.add(s.end);
  }
  const points = [...cuts].sort((a, b) => a - b);
  const out: Segment[] = [];
  for (let i = 0; i < points.length - 1; i += 1) {
    const start = points[i];
    const end = points[i + 1];
    if (start === end) continue;
    const term = t.find((s) => s.start <= start && s.end >= end);
    const keys = [...new Set(q.filter((s) => s.start <= start && s.end >= end).map((s) => s.key))].sort();
    out.push({ start, end, style: term ? term.style : null, quotes: keys });
  }
  return out;
}

/** Consecutive segments that share the same quotes, so one quote is one element. */
function groups(segments: readonly Segment[]): Segment[][] {
  const out: Segment[][] = [];
  for (const s of segments) {
    const last = out.at(-1);
    if (last && last[0].quotes.join("\u0000") === s.quotes.join("\u0000")) last.push(s);
    else out.push([s]);
  }
  return out;
}

export function HighlightedText({
  text,
  terms = [],
  quotes = [],
  showTerms = true,
  renderQuote,
}: Readonly<{
  text: string;
  terms?: readonly TermSpan[];
  quotes?: readonly QuoteSpan[];
  showTerms?: boolean;
  /** Wraps the pieces under one set of quotes; return `children` to leave them unmarked. */
  renderQuote?: (keys: string[], children: ReactNode, at: number, quoted: string) => ReactNode;
}>) {
  const parts = groups(segment(text, showTerms ? terms : [], quotes));
  return (
    <>
      {parts.map((group) => {
        const at = group[0].start;
        const pieces = group.map((s) =>
          s.style === null ? (
            text.slice(s.start, s.end)
          ) : (
            <span key={s.start} data-term={s.style} className={termClass(s.style)}>
              {text.slice(s.start, s.end)}
            </span>
          ),
        );
        const keys = group[0].quotes;
        if (keys.length === 0 || !renderQuote) return <Fragment key={at}>{pieces}</Fragment>;
        return <Fragment key={at}>{renderQuote(keys, pieces, at, text.slice(at, group.at(-1)!.end))}</Fragment>;
      })}
    </>
  );
}
