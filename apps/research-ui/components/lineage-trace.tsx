"use client";

import { useEffect, useState } from "react";

import { translate, type Locale } from "@/i18n";
import type { EvidenceNode } from "@/lib/contracts";
import {
  getLineageTrace,
  isScreeningApiError,
  normalizeConsoleOrigin,
  type LineageClaim,
  type LineageLeg,
  type LineageSelector,
  type LineageTrace,
  type ScreeningApiError,
} from "@/lib/screening-api";

import { EvidenceChain } from "./evidence-chain";

/**
 * The evidence lineage composition (packet UI-05).
 *
 * One read-only trace view: a claim with its quoted passages and locators,
 * the extracted documents those passages come from, the studies those
 * documents belong to, and the recorded screening decisions with reasons.
 * The ordered nodes reuse `EvidenceChain`, so the rail reads exactly as the
 * overview trail does; source details sit in a progressively disclosed
 * `details` element per claim and per leg, never in a second rendering of
 * the same record.
 *
 * Three boundaries are structural, not stylistic:
 *
 * - **No `main`.** The shell owns the single landmark, exactly as it does
 *   for the overview and the screening workspace; a nested `main` here
 *   would break the skip link's contract.
 * - **Two kinds of text.** Chrome comes from `LINEAGE_CHROME` below;
 *   every served value (claim text, quote, locator, identifier, DOI,
 *   reason, refusal code and message) renders byte for byte inside `<bdi>`.
 *   Nothing here translates record prose, and nothing here invents an
 *   identifier: the demonstration trace below carries no canonical id, no
 *   DOI, no fingerprint, and no verdict.
 * - **No entailment claim.** A verbatim quote is shown as a quote. The
 *   claim verification axes travel as stored annotations in their own
 *   record, never as scores and never as a statement that a passage
 *   proves its claim.
 *
 * Live read wiring mirrors the screening workspace: the default stays the
 * demonstration trace with no request sent; `?source=live` swaps it for
 * data read from the local console over HTTP through
 * `@/lib/screening-api`, with the live stamp marking exactly which part is
 * live so the two sources can never be confused. The selector comes from
 * the URL (`claim_id` or `chunk_id`, claim first when both are present);
 * a missing or refused trace renders the console typed code, never a
 * guessed record.
 */

/**
 * The lineage chrome strings that name the view itself.
 *
 * These live beside the component rather than in the catalogs because the
 * catalogs are frozen to earlier packets; they are demonstration-grade
 * translations pending fluent review (GATES section on translation
 * honesty), and every server-supplied value around them (identifiers,
 * codes, refusal text) keeps its own element, untranslated, exactly as
 * served. The shape mirrors the screening workspace live chrome.
 */
export const LINEAGE_CHROME = {
  en: {
    eyebrow: "Evidence lineage",
    heading: "Follow a claim to its decision",
    lede: "Each claim below is shown with the passages quoted for it, the documents those passages come from, the studies those documents belong to, and the recorded screening decision. Nothing here is inferred.",
    traceTitle: "Demonstration trace",
    liveStamp: "Live console data",
    liveLede:
      "The trace below was read from the local console over HTTP. It is live workspace data, not the demonstration trace.",
    liveUnavailable: "Live data unavailable",
    techIds: "Technical identifiers",
    refusalTitle: "Lineage refused",
  },
  fr: {
    eyebrow: "Filiation des preuves",
    heading: "Suivre une affirmation jusqu’à sa décision",
    lede: "Chaque affirmation ci-dessous est montrée avec les passages cités à son appui, les documents dont ces passages proviennent, les études auxquelles ces documents appartiennent, et la décision de sélection enregistrée. Rien ici n’est déduit.",
    traceTitle: "Trace de démonstration",
    liveStamp: "Données en direct de la console",
    liveLede:
      "La trace ci-dessous a été lue depuis la console locale via HTTP. Ce sont des données réelles de l’espace de travail, et non la trace de démonstration.",
    liveUnavailable: "Données en direct indisponibles",
    techIds: "Identifiants techniques",
    refusalTitle: "Filiation refusée",
  },
  ar: {
    eyebrow: "تسلسل الأدلة",
    heading: "تتبّع الادعاء حتى قراره",
    lede: "يُعرض كل ادعاء أدناه مع المقاطع المقتبسة له، والوثائق التي جاءت منها تلك المقاطع، والدراسات التي تنتمي إليها تلك الوثائق، وقرار الفرز المسجّل. لا شيء هنا مستنتَج.",
    traceTitle: "تسلسل العرض",
    liveStamp: "بيانات مباشرة من المنصة",
    liveLede:
      "قُرئ التسلسل أدناه من المنصة المحلية عبر HTTP. وهي بيانات حية من مساحة العمل وليست تسلسل العرض.",
    liveUnavailable: "تعذّر جلب البيانات المباشرة",
    techIds: "معرّفات تقنية",
    refusalTitle: "تعذّر عرض التسلسل",
  },
} as const;

/**
 * The demonstration trace the lineage view renders by default (UI-05).
 *
 * Demonstration prose only: no canonical identifier, no DOI, no
 * fingerprint, no verdict. The shell's `Demonstration data` marker covers
 * it, and the live source replaces it wholesale rather than mixing with
 * it. The decision node names its reason without stating a verdict, so no
 * machine default is presented as a human decision.
 */
export const demoLineageNodes: EvidenceNode[] = [
  {
    kind: "claim",
    label: "Reviewers resolve disagreements through recorded discussion.",
    detail: "finding",
    status: "accepted",
  },
  {
    kind: "chunk",
    label: "Each decision records the reason given at review time.",
    detail: "Methods, paragraph 4",
    status: "source",
  },
  {
    kind: "document",
    label: "Extracted text of the screened report",
    detail: "Usable extraction",
    status: "source",
  },
  {
    kind: "study",
    label: "A replication of machine-assisted screening",
    detail: "Study record described by the cited passages",
    status: "reviewed",
  },
  {
    kind: "decision",
    label: "Decision recorded with its reason",
    detail: "The record names the population and the outcome.",
    status: "reviewed",
  },
];

/** The ordered nodes for one served leg: the resolved prefix, nothing more. */
function legNodes(claim: LineageClaim, leg: LineageLeg): EvidenceNode[] {
  const nodes: EvidenceNode[] = [
    { kind: "claim", label: claim.claim_text, detail: claim.claim_kind, status: "accepted" },
  ];
  if (leg.evidence !== null) {
    nodes.push({
      kind: "chunk",
      label: leg.evidence.quote,
      detail: leg.evidence.locator,
      status: "source",
    });
  }
  if (leg.document !== null) {
    nodes.push({
      kind: "document",
      label: leg.document.extracted_path ?? leg.document.document_id,
      detail: leg.document.content_status,
      status: "source",
    });
  }
  if (leg.study !== null) {
    nodes.push({
      kind: "study",
      label: leg.study.title,
      detail: leg.study.study_id,
      status: "reviewed",
    });
  }
  if (leg.decision !== null) {
    nodes.push({
      kind: "decision",
      label: leg.decision.decision,
      detail: leg.decision.reason,
      status: "reviewed",
    });
  }
  return nodes;
}

/**
 * One row of the technical-identifiers record: the field name and its
 * stored values, each in its own isolated element so direction never
 * reorders them. Names are the payload's own keys, values its own bytes.
 */
function TechRow({ name, values }: Readonly<{ name: string; values: string[] }>) {
  if (values.length === 0) return null;
  return (
    <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
      <dt className="text-sm font-medium leading-6 text-ink">
        <bdi>{name}</bdi>
      </dt>
      <dd className="min-w-0 text-sm leading-6 text-ink-muted">
        {values.map((value, index) => (
          <span key={`${name}-${index}`}>
            {index > 0 ? " · " : null}
            <bdi>{value}</bdi>
          </span>
        ))}
      </dd>
    </div>
  );
}

/** Deduplicated in order; the record shows each stored value once. */
function unique(values: (string | null | undefined)[]): string[] {
  const seen: string[] = [];
  for (const value of values) {
    if (typeof value === "string" && value !== "" && !seen.includes(value)) {
      seen.push(value);
    }
  }
  return seen;
}

/** The claim-level identifiers: which claim, which evidence, which tokens. */
function ClaimTechRecord({ claim }: Readonly<{ claim: LineageClaim }>) {
  return (
    <dl className="mt-3 border-t border-rule-strong">
      <TechRow name="claim_id" values={[claim.claim_id]} />
      <TechRow name="evidence_ids" values={claim.evidence_ids} />
      <TechRow name="citation_tokens" values={claim.citation_tokens} />
      <TechRow name="chunk_ids" values={claim.chunk_ids} />
    </dl>
  );
}

/** The leg-level identifiers: document, study, decision, and their hashes. */
function LegTechRecord({ leg }: Readonly<{ leg: LineageLeg }>) {
  const idRows =
    leg.study !== null ? Object.entries(leg.study.external_ids) : [];
  return (
    <dl className="mt-3 border-t border-rule-strong">
      {leg.evidence !== null ? (
        <TechRow name="evidence_id" values={[leg.evidence.evidence_id]} />
      ) : null}
      <TechRow name="chunk_ids" values={leg.chunk_ids} />
      {leg.evidence !== null ? (
        <TechRow name="document_id" values={[leg.evidence.document_id]} />
      ) : null}
      <TechRow
        name="source_hash"
        values={unique([
          leg.evidence?.source_hash,
          leg.document?.source_hash,
        ])}
      />
      {leg.evidence !== null ? (
        <TechRow name="study_id" values={[leg.evidence.study_id]} />
      ) : null}
      <TechRow name="alias_ids" values={leg.study?.alias_ids ?? []} />
      {idRows.map(([provider, listed]) => (
        <TechRow key={provider} name={provider} values={listed} />
      ))}
      {leg.document !== null ? (
        <TechRow
          name="extraction_method"
          values={unique([
            leg.evidence?.extraction_method,
            leg.document.extraction_method,
          ])}
        />
      ) : null}
      {leg.decision !== null ? (
        <TechRow name="decision_id" values={[leg.decision.decision_id]} />
      ) : null}
      {leg.decision !== null ? (
        <TechRow name="decided_at" values={[leg.decision.decided_at]} />
      ) : null}
    </dl>
  );
}

/**
 * The stored verification axes for one claim, shown as annotations.
 *
 * Each axis name and value is the payload's own text. Absent axes are
 * absent rows, never placeholders; a claim with no verification record
 * shows no record rather than an invented one.
 */
function VerificationRecord({ claim }: Readonly<{ claim: LineageClaim }>) {
  if (claim.verification === null) return null;
  const rows: [string, string][] = [];
  for (const [name, value] of Object.entries(claim.verification)) {
    if (typeof value === "string" || typeof value === "number") {
      rows.push([name, String(value)]);
    }
  }
  if (rows.length === 0) return null;
  return (
    <dl className="mt-8 border-t border-rule-strong">
      {rows.map(([name, text]) => (
        <div
          key={name}
          className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]"
        >
          <dt className="text-sm font-medium leading-6 text-ink">
            <bdi>{name}</bdi>
          </dt>
          <dd className="min-w-0 text-sm leading-6 text-ink-muted">
            <bdi>{text}</bdi>
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** One served leg: its resolved rail, its refusal where the rail breaks. */
function ServedLeg({
  locale,
  claim,
  leg,
}: Readonly<{ locale: Locale; claim: LineageClaim; leg: LineageLeg }>) {
  const chrome = LINEAGE_CHROME[locale];
  return (
    <div className="mt-14">
      <EvidenceChain locale={locale} nodes={legNodes(claim, leg)} />
      {leg.refusal !== null ? (
        <div role="alert" className="mt-4 border-s-2 border-refusal ps-5">
          <p className="text-sm font-medium leading-6 text-refusal">
            {chrome.refusalTitle}
          </p>
          <p className="mt-1 text-sm leading-6 text-ink-muted">
            <bdi dir="ltr">{leg.refusal.code}</bdi>
            {": "}
            <bdi dir="ltr">{leg.refusal.message}</bdi>
          </p>
        </div>
      ) : null}
      <details className="mt-8">
        <summary className="text-sm font-medium text-evidence underline decoration-2 underline-offset-4">
          {chrome.techIds}
        </summary>
        <LegTechRecord leg={leg} />
      </details>
    </div>
  );
}

/** One served claim: its annotations, its identifiers, and its legs. */
function ServedClaim({
  locale,
  claim,
}: Readonly<{ locale: Locale; claim: LineageClaim }>) {
  const chrome = LINEAGE_CHROME[locale];
  return (
    <div className="mt-14">
      <VerificationRecord claim={claim} />
      <details className="mt-8">
        <summary className="text-sm font-medium text-evidence underline decoration-2 underline-offset-4">
          {chrome.techIds}
        </summary>
        <ClaimTechRecord claim={claim} />
      </details>
      {claim.legs.map((leg, index) => (
        <ServedLeg key={`${claim.claim_id}-${index}`} locale={locale} claim={claim} leg={leg} />
      ))}
    </div>
  );
}

function LiveErrorBody({ locale, error }: { locale: Locale; error: unknown }) {
  const chrome = LINEAGE_CHROME[locale];
  const code = isScreeningApiError(error) ? error.code : "UNKNOWN_ERROR";
  const message =
    isScreeningApiError(error) && error.serverMessage ? error.serverMessage : String(error);
  return (
    <div role="alert">
      <p className="text-sm leading-6 text-refusal">{chrome.liveUnavailable}</p>
      <p className="mt-2 text-sm leading-6 text-ink-muted">
        <bdi dir="ltr">{code}</bdi>
        {": "}
        <bdi dir="ltr">{message}</bdi>
      </p>
    </div>
  );
}

function LiveReadyBody({
  locale,
  trace,
}: {
  locale: Locale;
  trace: LineageTrace;
}) {
  return (
    <div>
      <dl className="border-t border-rule-strong">
        <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <dt className="text-sm font-medium leading-6 text-ink">Publication</dt>
          <dd className="min-w-0 text-sm leading-6 text-ink-muted">
            <bdi>{trace.publication.status}</bdi>
            {trace.publication.generation_id ? (
              <>
                {" · "}
                <bdi>{trace.publication.generation_id}</bdi>
              </>
            ) : null}
          </dd>
        </div>
      </dl>
      {trace.claims.map((claim) => (
        <ServedClaim key={claim.claim_id} locale={locale} claim={claim} />
      ))}
    </div>
  );
}

type SourceMode = { kind: "fixture" } | { kind: "live"; origin: string };

type LiveState =
  | { status: "idle" }
  | { status: "loading"; origin: string }
  | { status: "ready"; origin: string; trace: LineageTrace }
  | { status: "error"; origin: string; error: unknown };

/** The console origin and trace selector the live source reads, if requested. */
function readLiveRequest(): { origin: string; selector: LineageSelector } | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "live") return null;
  const origin = params.get("console") ?? "";
  const claimId = params.get("claim_id") ?? "";
  const chunkId = params.get("chunk_id") ?? "";
  if (claimId !== "") return { origin, selector: { claim_id: claimId } };
  if (chunkId !== "") return { origin, selector: { chunk_id: chunkId } };
  // No selector is still a request: the console answers the typed
  // MISSING_SELECTOR refusal rather than this view guessing one.
  return { origin, selector: { claim_id: "" } };
}

export function LineagePage({ locale }: Readonly<{ locale: Locale }>) {
  const [mode, setMode] = useState<SourceMode>({ kind: "fixture" });
  const [live, setLive] = useState<LiveState>({ status: "idle" });

  useEffect(() => {
    // Fixture is the default and stays request-free: this effect only arms
    // the live source when the URL explicitly asks for it, so the default
    // render performs no request and changes no state.
    const requested = readLiveRequest();
    if (requested === null) return;
    let origin: string;
    try {
      origin = normalizeConsoleOrigin(requested.origin);
    } catch (error: unknown) {
      const failure: ScreeningApiError = error as ScreeningApiError;
      setMode({ kind: "live", origin: requested.origin });
      setLive({ status: "error", origin: requested.origin, error: failure });
      return;
    }
    const selector = requested.selector;
    setMode({ kind: "live", origin });
    setLive({ status: "loading", origin });
    let cancelled = false;
    (async () => {
      try {
        const trace = await getLineageTrace(origin, selector);
        if (!cancelled) setLive({ status: "ready", origin, trace });
      } catch (error: unknown) {
        if (!cancelled) setLive({ status: "error", origin, error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const chrome = LINEAGE_CHROME[locale];
  const liveActive = mode.kind === "live";

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        {/* ---- masthead: eyebrow in the leading margin, as on the overview --- */}
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
            {chrome.eyebrow}
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              {chrome.heading}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              {chrome.lede}
            </p>
          </div>
        </section>

        {liveActive ? (
          /* ---- the live source: console data over HTTP, never the record ---- */
          <section className="mt-14" aria-labelledby="lineage-live-title">
            <div className="mb-5">
              <p className="mb-3">
                <span
                  aria-hidden="true"
                  className="inline-flex items-center border border-evidence/45 px-2 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]"
                >
                  {chrome.liveStamp}
                </span>
              </p>
              <h2 id="lineage-live-title" className="font-display text-xl leading-8 text-ink">
                {chrome.liveStamp}
              </h2>
              <p className="mt-1 text-sm leading-6 text-ink-muted">{chrome.liveLede}</p>
            </div>
            {live.status === "idle" || live.status === "loading" ? (
              <p role="status" className="text-sm leading-6 text-ink-muted">
                {translate(locale, "overview.recordLoading")}
              </p>
            ) : live.status === "error" ? (
              <LiveErrorBody locale={locale} error={live.error} />
            ) : (
              <LiveReadyBody locale={locale} trace={live.trace} />
            )}
          </section>
        ) : (
          /* ---- the demonstration trace: prose only, no request sent --------- */
          <section className="mt-14" aria-labelledby="lineage-trace-title">
            <div className="mb-5">
              <h2 id="lineage-trace-title" className="font-display text-xl leading-8 text-ink">
                {chrome.traceTitle}
              </h2>
            </div>
            <EvidenceChain locale={locale} nodes={demoLineageNodes} />
          </section>
        )}
      </div>
    </div>
  );
}
