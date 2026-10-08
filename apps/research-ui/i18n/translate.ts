import type { EvidenceNode, WorkflowState } from "../lib/contracts";
import type { OverviewCountField, ProjectOverviewPhase } from "../lib/project-state";
import { CATALOGS, type MessageKey } from "../messages";
import { inflate } from "./long-strings";
import type { Locale } from "./locales";

export type { MessageKey };

/**
 * The values a message's named holes may take.
 *
 * `string | number`, and the number case exists only so a caller can hand
 * `translate` an already-`Intl`-formatted string or a raw integer. Nothing
 * else: no nested objects, no `null` for "leave it blank" (a hole that resolves
 * to nothing is a bug in the catalog, and it must fail loudly).
 */
export type MessageValues = Readonly<Record<string, string | number>>;

/**
 * Raised when a message cannot be rendered.
 *
 * It is an error, never a fallback. The two tempting alternatives are both
 * wrong in ways a reader pays for: rendering the raw key produces a document
 * full of `overview.eyebrow` in production, and rendering `""` or silently
 * substituting English produces chrome that looks translated while not being.
 * Failing at render makes the missing key a red test in the locale that lost
 * it, which is the moment it can still be fixed (N3).
 */
export class MissingMessageError extends Error {
  constructor(
    readonly key: string,
    readonly locale: Locale,
    reason: string,
  ) {
    super(
      `Missing message "${key}" for locale "${locale}": ${reason}. ` +
        `A message must never render as its key, as an empty string, or in ` +
        `another language.`,
    );
    this.name = "MissingMessageError";
  }
}

/**
 * Raised when a canonical token has no catalog key.
 *
 * A data error rather than a message error, so it is a separate class: the token
 * sets are frozen by packet UI-01c and a new token without a label is a decision
 * nobody made, not a translation that lost a string.
 */
export class UnmappedTokenError extends Error {
  constructor(
    readonly token: string,
    readonly namespace: string,
  ) {
    super(
      `Token "${token}" has no ${namespace}.* catalog key. Add the key to every ` +
        `catalog before the token can reach a view.`,
    );
    this.name = "UnmappedTokenError";
  }
}

/**
 * Token → catalog key maps, one per controlled vocabulary.
 *
 * Declared as `Record<Token, MessageKey>` rather than built by string
 * concatenation, so a vocabulary that gains a token without gaining a key is a
 * **compile** error in this file instead of a `state.wat` that renders. This is
 * the display-label half of D-I18N-07: the canonical token stays the data, and
 * only what a reader sees is translated.
 *
 * The types are imported from the presentation contracts with `import type`, so
 * this module keeps no runtime dependency on the view layer.
 */
const NAV_KEYS: Readonly<Record<string, MessageKey>> = {
  overview: "nav.overview",
  screening: "nav.screening",
  evidence: "nav.evidence",
  audit: "nav.audit",
};

const STATE_KEYS: Readonly<Record<WorkflowState, MessageKey>> = {
  complete: "state.complete",
  active: "state.active",
  waiting: "state.waiting",
  refused: "state.refused",
};

const EVIDENCE_KIND_KEYS: Readonly<Record<EvidenceNode["kind"], MessageKey>> = {
  claim: "evidenceKind.claim",
  chunk: "evidenceKind.chunk",
  document: "evidenceKind.document",
  study: "evidenceKind.study",
  decision: "evidenceKind.decision",
};

/**
 * The nine project-overview phases (packet UI-02), label and description kept
 * as two tables rather than one key built by string concatenation, because a
 * component must never assemble a `MessageKey` at runtime: a phase whose label
 * exists but whose description does not would then fail only in the locales
 * that lost the description, instead of failing to compile here.
 */
const PHASE_KEYS: Readonly<Record<ProjectOverviewPhase, MessageKey>> = {
  empty: "phase.empty",
  setup: "phase.setup",
  search: "phase.search",
  screening: "phase.screening",
  extraction: "phase.extraction",
  indexing: "phase.indexing",
  refusal: "phase.refusal",
  degraded: "phase.degraded",
  ready: "phase.ready",
};

const PHASE_DESCRIPTION_KEYS: Readonly<Record<ProjectOverviewPhase, MessageKey>> = {
  empty: "phase.empty.description",
  setup: "phase.setup.description",
  search: "phase.search.description",
  screening: "phase.screening.description",
  extraction: "phase.extraction.description",
  indexing: "phase.indexing.description",
  refusal: "phase.refusal.description",
  degraded: "phase.degraded.description",
  ready: "phase.ready.description",
};

/** The five corpus statistics, each with its own catalog label. */
const COUNT_KEYS: Readonly<Record<OverviewCountField, MessageKey>> = {
  recordsDiscovered: "counts.recordsDiscovered",
  studiesIncluded: "counts.studiesIncluded",
  decisionsPending: "counts.decisionsPending",
  documentsExtracted: "counts.documentsExtracted",
  chunksIndexed: "counts.chunksIndexed",
};

function lookup<T extends string>(
  table: Readonly<Record<T, MessageKey>>,
  token: string,
  namespace: string,
): MessageKey {
  const key = table[token as T];
  if (!key) {
    throw new UnmappedTokenError(token, namespace);
  }
  return key;
}

/** The catalog key for a frozen nav id. */
export function navKey(id: string): MessageKey {
  return lookup(NAV_KEYS, id, "nav");
}

/** The catalog key for a `WorkflowState`, the canonical token preserved as data. */
export function stateKey(state: WorkflowState): MessageKey {
  return lookup(STATE_KEYS, state, "state");
}

/** The catalog key for an `EvidenceNode.kind`, the canonical token preserved as data. */
export function evidenceKindKey(kind: EvidenceNode["kind"]): MessageKey {
  return lookup(EVIDENCE_KIND_KEYS, kind, "evidenceKind");
}

/**
 * The catalog key for a `ProjectOverviewPhase` (packet UI-02).
 *
 * Same contract as {@link stateKey}: the phase token stays the data, only the
 * word a reader sees is translated, and a token with no key throws
 * {@link UnmappedTokenError} rather than rendering something invented.
 */
export function phaseKey(phase: string): MessageKey {
  return lookup(PHASE_KEYS, phase, "phase");
}

/** The catalog key for the one-sentence explanation of a phase. */
export function phaseDescriptionKey(phase: string): MessageKey {
  return lookup(PHASE_DESCRIPTION_KEYS, phase, "phase");
}

/**
 * The catalog key for one corpus statistic's label (packet UI-02).
 *
 * The *value* is never looked up here: a count is a fixture number formatted by
 * `Intl`, or it is absent and renders `counts.unknown`. This maps only the
 * label that sits beside it.
 */
export function countKey(field: string): MessageKey {
  return lookup(COUNT_KEYS, field, "counts");
}

/** Matches a `{name}` hole. Names are dotted-safe so keys can be reused. */
const PLACEHOLDER = /\{([a-zA-Z][a-zA-Z0-9_]*)\}/g;

/**
 * The hole names in a template, in order of appearance.
 *
 * Exported because placeholder drift is a failure mode the tests need to
 * observe directly (N4): if `fr` drops `{available}` from T39, the French
 * sentence silently reads `Available locales: .`, which renders fine and looks
 * broken. Comparing hole sets across the three catalogs is the mechanical
 * check.
 */
export function placeholdersOf(template: string): string[] {
  return [...template.matchAll(PLACEHOLDER)].map((match) => match[1] as string);
}

/**
 * One piece of a rendered message.
 *
 * `text` is the translator's own wording. `isolated` is a substituted value
 * whose provenance is not the product's — today only fixture content — and which
 * the caller must wrap in `<bdi>` so the bidirectional algorithm does not
 * reorder it inside a sentence in another script (D-I18N-02).
 */
export type MessagePart =
  | { readonly kind: "text"; readonly value: string }
  | { readonly kind: "isolated"; readonly value: string };

/**
 * Validate a lookup and return its template, or throw.
 *
 * Shared by {@link translate} and {@link translateParts} so the two cannot
 * disagree about what counts as a missing message (N3).
 */
function resolveTemplate(
  locale: Locale,
  key: MessageKey,
  values?: MessageValues,
): string {
  const catalog = CATALOGS[locale] as Readonly<Record<string, string>> | undefined;
  if (!catalog) {
    throw new MissingMessageError(key, locale, "there is no catalog for it");
  }
  const template = catalog[key];
  if (typeof template !== "string") {
    throw new MissingMessageError(key, locale, "the key is absent from the catalog");
  }
  if (template.trim() === "") {
    throw new MissingMessageError(key, locale, "the template is empty");
  }

  if (values) {
    for (const [name, value] of Object.entries(values)) {
      if (typeof value === "string" && value.trim() === "") {
        throw new MissingMessageError(key, locale, `the value for "{${name}}" is empty`);
      }
    }
  }

  const unfilled = placeholdersOf(template).filter((name) => values?.[name] === undefined);
  if (unfilled.length > 0) {
    throw new MissingMessageError(
      key,
      locale,
      `no value was supplied for ${unfilled.map((name) => `"{${name}}"`).join(", ")}`,
    );
  }

  return template;
}

/** Substitute one named hole, everywhere it occurs. */
function substitute(template: string, name: string, value: string | number): string {
  return template.replaceAll(`{${name}}`, String(value));
}

/**
 * Look up one message and substitute its holes.
 *
 * Pure, synchronous and React-free on purpose (D-I18N-03): the same call
 * serves a server component, `generateMetadata`, and vitest, so there is no
 * second code path that could render a different string than the one the tests
 * asserted.
 *
 * Failure modes, all loud (N3):
 *
 * - an unknown key (reachable only through a cast) throws;
 * - a value that is absent, empty or whitespace-only throws;
 * - a hole left unreplaced after interpolation throws, which is how placeholder
 *   drift is caught at render instead of on screen.
 *
 * A returned string is always complete: no key, no empty string, no leftover
 * hole, no other language.
 */
export function translate(
  locale: Locale,
  key: MessageKey,
  values?: MessageValues,
): string {
  const template = resolveTemplate(locale, key, values);
  let message = template;
  if (values) {
    for (const [name, value] of Object.entries(values)) {
      message = substitute(message, name, value);
    }
  }
  return inflate(locale, message);
}

/**
 * The same message, but as the ordered pieces a renderer needs when a
 * substituted value has to stay its own element.
 *
 * The only current caller is `overview.lastEvent`, whose `{event}` is fixture
 * text that must sit inside a `<bdi>` next to a translated prefix (D-I18N-02).
 * Slicing the *rendered* string to find the value would break the moment a
 * translation put the hole first, inside a quotation mark, or twice; reading the
 * hole's position from the template does not, because the template is where the
 * translator put it. So the parts come from the template, never from a search
 * over the output, and the caller's markup cannot change what the sentence says
 * or in which order.
 *
 * Word order is still entirely the translator's: for `ar` the parts come back
 * prefix-then-hole or hole-then-prefix depending on which template they came
 * from, and this function does not reorder them.
 *
 * One difference from {@link translate} is deliberate: only the translator's
 * literals are inflated here, never a substituted value. That value is fixture
 * text whose bytes are frozen (D-I18N-02), and the long-string build inflates
 * chrome, not records. `translate` inflates the whole rendered message, which is
 * what the long-string gate measures; both messages it measures
 * (`overview.traceLede`, `overview.asideBody`) are pure-literal templates, so
 * the two rules cannot be observed to disagree.
 */
export function translateParts(
  locale: Locale,
  key: MessageKey,
  values: MessageValues,
): MessagePart[] {
  const template = resolveTemplate(locale, key, values);
  const parts: MessagePart[] = [];
  let cursor = 0;
  for (const match of template.matchAll(PLACEHOLDER)) {
    const literal = template.slice(cursor, match.index);
    if (literal !== "") {
      parts.push({ kind: "text", value: inflate(locale, literal) });
    }
    parts.push({
      kind: "isolated",
      value: String(values[match[1] as string]),
    });
    cursor = (match.index ?? 0) + match[0].length;
  }
  const tail = template.slice(cursor);
  if (tail !== "") {
    parts.push({ kind: "text", value: inflate(locale, tail) });
  }
  return parts;
}