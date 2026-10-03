import type { EvidenceNode } from "@/lib/contracts";

import { evidenceKindKey, formatNumber, translate, type Locale } from "@/i18n";

/**
 * The evidence trail (packet UI-01c, acceptance A12; localized in UI-01d).
 *
 * This is the signature motif: the visible path from a research claim back
 * through evidence to provenance, drawn as the annotated vertical trail a
 * reader of a paper would recognise — a continuous hairline spine, a marginal
 * ordinal in the leading margin, and the node's kind as a small stamp in the same
 * margin band — rather than as a stack of white cards.
 *
 * Three structural couplings constrain how that is built, and all are design
 * requirements rather than accidents (packet UI-01c §7, finding F6):
 *
 *   - `tests/evidence-chain.test.tsx` reads each `<li>`'s `firstElementChild`
 *     and requires its `textContent` to be the step number. So the marginal
 *     numeral is a REAL DOM element holding REAL text; the trail is not drawn
 *     with CSS counters, which would have satisfied the picture and failed the
 *     contract. It is formatted with `Intl` (F03) and left as bare text, which
 *     is also why it is not wrapped: it is a generated number, not fixture text.
 *   - `tests/home-page.test.tsx` pins the total `<li>` count on the route and
 *     the first N level-3 headings, so nothing here adds a nested list and the
 *     marginal label is a `<p>`, never an `<h3>`.
 *   - `tests-browser/` measures the ordinal column's alignment, so it aligns to
 *     the inline end with a logical utility (DC4) rather than to a physical side.
 *
 * Nothing was removed. Every node still renders its kind, its label as a level-3
 * heading, and its detail, in that order.
 *
 * **Direction and translation (packet UI-01d).** The spine is the clearest case
 * in the application for logical properties: it is drawn on the *inline start*
 * edge (`border-s`/`ps-*`), so in `ar` it runs down the right of the trail, where
 * the reading flow starts, and the ordinals line up on its outer side. Nothing
 * here declares `dir`; the document does, once. The node's `kind` is a canonical
 * token in the data and a translated word on screen (D-I18N-07): the token is
 * still what the React key and the record use, and only the label a reader sees
 * comes from the catalog. The label and detail are the fixture's own text and
 * stay byte for byte inside `<bdi>`.
 */
export function EvidenceChain({
  nodes,
  locale,
}: {
  nodes: EvidenceNode[];
  locale: Locale;
}) {
  return (
    <ol className="border-t border-rule-strong">
      {nodes.map((node, index) => (
        <li
          key={`${node.kind}-${index}`}
          className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 border-b border-rule py-4 lg:grid-cols-[1.75rem_minmax(0,1fr)] lg:gap-x-5"
        >
          {/*
            The marginal ordinal. First element child on purpose: it is the
            number the component test reads, and it is what makes the trail read
            as a numbered sequence rather than as a stack of panels.
          */}
          <span className="pt-0.5 text-end text-[0.6875rem] leading-4 text-ink-faint rtl:text-[0.75rem]">
            {formatNumber(locale, index + 1)}
          </span>

          {/*
            `border-s` on this wrapper, contiguous across siblings and with no
            vertical gap between them, is what draws one unbroken spine. It is a
            hairline in `--color-rule-strong` at both viewports, so the document
            form survives 375px instead of flattening into cards.
          */}
          <div className="min-w-0 border-s border-rule-strong ps-3 lg:ps-5">
            <div className="grid gap-x-4 lg:grid-cols-[6.5rem_minmax(0,1fr)]">
              {/*
                The marginal label. At 1440px it stands in its own margin column
                beside the entry; at 375px it sits directly above the label, which
                keeps the kind readable instead of hiding it behind a breakpoint.
                A `<p>`, not a heading: the route's level-3 headings are pinned.
              */}
              <p className="text-[0.6875rem] uppercase leading-4 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
                {translate(locale, evidenceKindKey(node.kind))}
              </p>
              <div className="mt-1 min-w-0 lg:mt-0">
                <h3 className="text-base font-medium text-ink">
                  <bdi>{node.label}</bdi>
                </h3>
                <p className="mt-1 text-sm leading-6 text-ink-muted">
                  <bdi>{node.detail}</bdi>
                </p>
              </div>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
