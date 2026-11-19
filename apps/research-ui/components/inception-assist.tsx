"use client";

import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { fieldHash, fillNodes, proposalHash } from "@/components/assist-anchor";
import { isOfflineCode, refusalFrom, useAssist, type AssistRefusal } from "@/components/assist-context";
import { ChecksPanel, type CheckLink } from "@/components/checks-panel";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { fieldLabel, synonymConcept } from "@/lib/assist-labels";
import {
  applyEditedProposal,
  applyProposal,
  dismissCheck,
  listProposals,
  rejectProposal,
  restoreCheck,
  restoreProposal,
  runChecks,
  type Check,
  type Proposal,
  type ProposalDecision,
  type ProposalListing,
} from "@/lib/inception-api";
import { ScreeningApiError } from "@/lib/screening-api";
import { PROPOSALS_COPY, hasProposalsKey, proposalsT } from "@/lib/proposals-copy";

/**
 * The M10b Part B pieces of an inception screen: the per-step proposal list
 * (`docs/ux/shared/final/01-proposals.md`), the checks panel and the Review
 * readiness list (`02-checks.md`). Each reads through the draft's shared
 * assist state (`assist-context`), so the stepper badges, the list and the
 * panel describe the same saved draft. Nothing here decides a proposal, a
 * check, a level or a count: the engine answers, the screen shows.
 */

type InceptionStepId = "scope" | "explore" | "direction" | "shape" | "criteria" | "review";

function inceptionLink(locale: Locale, step: string, draftId: string, origin: string, hash = ""): string {
  const query = new URLSearchParams();
  if (draftId) query.set("draft", draftId);
  if (origin) query.set("console", origin);
  const q = query.toString();
  return `/${locale}/inception/${step}/${q ? `?${q}` : ""}${hash ? `#${hash}` : ""}`;
}

/** The value a proposal would write, as short text (values are shown as the engine sent them). */
export function valueText(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map(valueText).join(", ");
  if (typeof value === "object") {
    const o = value as Record<string, unknown>;
    return String(o.concept ?? o.criterion ?? o.name ?? JSON.stringify(value));
  }
  return String(value);
}

/** The source label (Copy); an unknown source gets the generic label; `agent:<model>` names the assistant (M10c). */
export function SourceLabel({ locale, source }: Readonly<{ locale: Locale; source: string }>) {
  const t = proposalsT(locale);
  const at = source.indexOf(":");
  const kind = at < 0 ? source : source.slice(0, at);
  const name = at < 0 ? "" : source.slice(at + 1);
  let label: ReactNode = t("proposals.source.generic");
  if (kind === "check" && name) label = fillNodes(PROPOSALS_COPY[locale]["proposals.source.check"], { name: <bdi dir="ltr">{name}</bdi> });
  else if (kind === "import" && name) label = fillNodes(PROPOSALS_COPY[locale]["proposals.source.import"], { name: <bdi dir="auto">{name}</bdi> });
  else if (kind === "engine" && hasProposalsKey(`proposals.source.engine.${name}`)) label = t(`proposals.source.engine.${name}` as "proposals.source.engine.pool_synonym");
  else if (kind === "agent") label = name ? fillNodes(PROPOSALS_COPY[locale]["proposals.source.agentModel"], { model: <bdi dir="ltr">{name}</bdi> }) : t("proposals.source.agent");
  return (
    <span className="text-ink-muted" data-proposal-source={kind}>
      {label}
    </span>
  );
}

function WhatLine({ locale, proposal, id }: Readonly<{ locale: Locale; proposal: Proposal; id: string }>) {
  const copy = PROPOSALS_COPY[locale];
  const value = <bdi dir="auto" className="font-mono text-[0.8125rem]" data-value>{valueText(proposal.status === "applied_edited" ? proposal.decided_value : proposal.value)}</bdi>;
  const field = <span data-field>{fieldLabel(locale, proposal.target.field)}</span>;
  const template = proposal.op === "add" ? copy["proposals.what.add"] : proposal.op === "remove" ? copy["proposals.what.remove"] : copy["proposals.what.replace"];
  return (
    <p id={id} className="mt-1 text-ink" data-what>
      {fillNodes(template, { value, field, now: <bdi dir="auto" className="font-mono text-[0.8125rem]">{proposal.current ?? proposal.base.shown}</bdi> })}
    </p>
  );
}

function Evidence({ locale, proposal, startOpen }: Readonly<{ locale: Locale; proposal: Proposal; startOpen: boolean }>) {
  const t = proposalsT(locale);
  const [open, setOpen] = useState(startOpen);
  const id = `proposal-evidence-${proposal.proposal_id}`;
  if (!proposal.evidence.length) return null;
  const copy = PROPOSALS_COPY[locale];
  return (
    <div className="mt-1 text-sm">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
        className="inline-flex min-h-11 items-center rounded-sm text-ink-muted underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
        data-evidence-toggle
      >
        {fillNodes(copy["proposals.evidence"], { n: <bdi dir="ltr">{formatNumber(locale, proposal.evidence.length)}</bdi> })}
      </button>
      <ul id={id} hidden={!open} className="ms-4 list-disc text-ink-muted" data-evidence>
        {proposal.evidence.map((e, i) => (
          <li key={i}>
            {e.kind === "doi" ? (
              <a className="text-brand underline" href={`https://doi.org/${String(e.doi ?? e.value ?? "")}`} target="_blank" rel="noopener noreferrer">
                {fillNodes(copy["proposals.evidence.doi"], { doi: <bdi dir="ltr">{String(e.doi ?? e.value ?? "")}</bdi> })}
              </a>
            ) : e.kind === "check" ? (
              fillNodes(copy["proposals.evidence.check"], { id: <bdi dir="ltr">{String(e.check_id ?? e.id ?? "")}</bdi> })
            ) : e.kind === "count" ? (
              fillNodes(copy["proposals.evidence.count"], { value: <bdi dir="ltr">{String(e.value ?? "")}</bdi>, unit: String(e.unit ?? "") })
            ) : e.kind === "file" ? (
              fillNodes(copy["proposals.evidence.file"], { path: <bdi dir="ltr">{String(e.path ?? e.value ?? "")}</bdi> })
            ) : (
              <bdi dir="ltr">{JSON.stringify(e)}</bdi>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** What the inline editor edits: a concept's name, a synonym, a text, a number, or anything else as JSON. */
function editShape(proposal: Proposal): "concept" | "synonym" | "text" | "number" | "json" {
  const v = proposal.value;
  if (proposal.target.field === "concepts" && v && typeof v === "object" && !Array.isArray(v) && "concept" in v) return "concept";
  if (synonymConcept(proposal.target.field) !== null && typeof v === "string") return "synonym";
  if (typeof v === "string") return "text";
  if (typeof v === "number") return "number";
  return "json";
}

function editText(proposal: Proposal): string {
  const shape = editShape(proposal);
  if (shape === "concept") return String((proposal.value as { concept: unknown }).concept ?? "");
  if (shape === "json") return JSON.stringify(proposal.value);
  return String(proposal.value ?? "");
}

/** The edited text as the value to send; `undefined` while it cannot be one. */
function editValue(proposal: Proposal, text: string): unknown {
  const shape = editShape(proposal);
  if (shape === "concept") return text.trim() ? { ...(proposal.value as object), concept: text.trim() } : undefined;
  if (shape === "synonym" || shape === "text") return text.trim() ? text.trim() : undefined;
  if (shape === "number") return /^-?\d+$/.test(text.trim()) ? Number(text.trim()) : undefined;
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

type CardNote = { id: string; text: string; alert?: boolean; details?: string[] };

/**
 * The per-step proposal list (01-proposals "States", "Desktop layout", "Keyboard").
 * Draws nothing on a step with no proposal. Apply, Edit then Apply my edit, and
 * Reject send one POST each; Restore returns a rejected one to open.
 */
export function ProposalList({ locale, step }: Readonly<{ locale: Locale; step: InceptionStepId }>) {
  const assist = useAssist();
  const t = proposalsT(locale);
  const uid = useId().replace(/:/g, "");
  const headingId = `proposals-${step}-${uid}`;
  const offlineId = `proposals-offline-${step}-${uid}`;
  const [listing, setListing] = useState<ProposalListing | null>(null);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [asOf, setAsOf] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [edited, setEdited] = useState("");
  const [note, setNote] = useState<CardNote | null>(null);
  const [listNote, setListNote] = useState("");
  const [announce, setAnnounce] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  const origin = assist?.origin ?? "";
  const sessionId = assist?.sessionId ?? "";
  const loaded = assist?.loaded ?? 0;

  const read = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      setListing(await listProposals(origin, sessionId, step));
      setOffline(false);
      setAsOf(new Date().toISOString());
    } catch (error) {
      if (isOfflineCode(refusalFrom(error).code)) setOffline(true);
    } finally {
      setLoading(false);
    }
  }, [origin, sessionId, step]);

  // After the frame's checks read: the checks record the proposals they recommend first.
  useEffect(() => {
    if (loaded > 0) void read();
  }, [read, loaded]);

  if (!assist) return null;
  const mine = (listing?.proposals ?? []).filter((p) => p.step === step);
  if (!listing) {
    return loading && loaded === 0 ? null : loading ? (
      <div aria-busy="true" className="h-24 rounded-lg border border-dashed border-rule" data-proposals-loading>
        <span className="sr-only">{t("proposals.loading")}</span>
      </div>
    ) : null;
  }
  if (mine.length === 0) return null;

  const readOnly = assist.readOnly;
  const counts = listing.by_step?.[step] ?? { open: 0, stale: 0 };
  const openCards = mine.filter((p) => (p.status === "open" || p.status === "stale") && !p.source.startsWith("engine:"));
  const decided = mine.filter((p) => !openCards.includes(p));
  const disabled = busy || offline;
  const n = (value: number) => <bdi dir="ltr">{formatNumber(locale, value)}</bdi>;

  const focusNext = (after: ProposalListing, index: number) =>
    setTimeout(() => {
      const left = (after.proposals ?? []).filter((p) => p.step === step && (p.status === "open" || p.status === "stale") && !p.source.startsWith("engine:"));
      const next = left[Math.max(0, Math.min(index, left.length - 1))];
      const button = next ? (document.getElementById(proposalHash(next.proposal_id))?.querySelector("button:not([disabled])") as HTMLElement | null) : null;
      (button ?? heading.current)?.focus();
    }, 0);

  const adopt = (answer: ProposalDecision) => setListing({ session_id: answer.session_id, updated_at: answer.updated_at, proposals: answer.proposals, by_step: answer.by_step });

  const run = async (proposal: Proposal, action: "apply" | "edit" | "reject" | "restore", value?: unknown) => {
    const record = assist.record;
    if (!record) return;
    const index = openCards.findIndex((p) => p.proposal_id === proposal.proposal_id);
    const field = fieldLabel(locale, proposal.target.field);
    setBusy(true);
    setNote(null);
    setListNote("");
    try {
      const answer =
        action === "apply"
          ? await applyProposal(origin, sessionId, proposal.proposal_id, record.updated_at)
          : action === "edit"
            ? await applyEditedProposal(origin, sessionId, proposal.proposal_id, record.updated_at, value)
            : action === "reject"
              ? await rejectProposal(origin, sessionId, proposal.proposal_id)
              : await restoreProposal(origin, sessionId, proposal.proposal_id);
      adopt(answer);
      setEditing(null);
      if (action === "apply" || action === "edit") assist.adoptDecision(answer, proposal.target.field);
      setAnnounce(
        action === "reject"
          ? t("proposals.act.announceRejected", { field })
          : action === "restore"
            ? t("proposals.act.announceRestored", { field })
            : t("proposals.act.announceApplied", { field }),
      );
      assist.bump();
      if (action === "restore") {
        setTimeout(() => (document.getElementById(proposalHash(proposal.proposal_id))?.querySelector("button:not([disabled])") as HTMLElement | null)?.focus(), 0);
      } else {
        focusNext(answer, index);
      }
    } catch (error) {
      const refusal = refusalFrom(error);
      await refused(proposal, refusal, field);
    } finally {
      setBusy(false);
    }
  };

  const refused = async (proposal: Proposal, refusal: AssistRefusal, field: string) => {
    const id = proposal.proposal_id;
    if (isOfflineCode(refusal.code)) {
      setOffline(true);
      return;
    }
    if (refusal.code === "PROPOSAL_STALE") {
      setEditing(null);
      await read();
      setAnnounce(t("proposals.act.announceStale", { field }));
      return;
    }
    if (refusal.code === "PROPOSAL_NOT_OPEN" || refusal.code === "PROPOSAL_NOT_FOUND") {
      setEditing(null);
      const again = await listProposals(origin, sessionId, step).catch(() => null);
      if (again) setListing(again);
      const now = again?.proposals.find((p) => p.proposal_id === id);
      if (refusal.code === "PROPOSAL_NOT_FOUND" || !now) setListNote(t("proposals.err.gone"));
      else if (now.status === "rejected" || now.status === "applied" || now.status === "applied_edited") {
        setNote({ id, text: t("proposals.err.already", { status: t(now.status === "rejected" ? "proposals.word.rejected" : "proposals.word.applied") }) });
      }
      return;
    }
    if (refusal.code === "DRAFT_INVALID" || refusal.code === "DRAFT_TOO_LARGE") {
      const errors = ((refusal.details as { errors?: unknown[] } | undefined)?.errors ?? []).map((e) =>
        typeof e === "string" ? e : String((e as { msg?: unknown; message?: unknown })?.msg ?? (e as { message?: unknown })?.message ?? JSON.stringify(e)),
      );
      setNote({ id, text: t("proposals.err.invalid", { error: errors[0] ?? refusal.message }), alert: true, details: errors });
      return;
    }
    if (refusal.code === "DRAFT_CONFLICT" || refusal.code === "DRAFT_EMITTED") {
      setEditing(null);
      assist.markReadOnly();
      return;
    }
    setNote({ id, text: t("proposals.err.other"), alert: true, details: [refusal.code, refusal.message].filter(Boolean) });
  };

  const card = (proposal: Proposal) => {
    const id = proposal.proposal_id;
    const whatId = `proposal-what-${id}`;
    const stale = proposal.status === "stale";
    const isEditing = editing === id;
    const shape = editShape(proposal);
    const editorId = `proposal-edit-${id}`;
    const value = isEditing ? editValue(proposal, edited) : undefined;
    const cardNote = note?.id === id ? note : null;
    const describedBy = offline ? `${whatId} ${offlineId}` : whatId;
    return (
      <li key={id} id={proposalHash(id)} className={`rounded-md border border-dashed border-ink-muted bg-paper p-3 ${stale ? "opacity-80" : ""}`} data-proposal={id} data-status={proposal.status}>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <SourceLabel locale={locale} source={proposal.source} />
          <span className="text-ink-muted">· {t("proposals.draftLabel")}</span>
          {stale ? <DecisionBadge role="unclear">{t("proposals.status.stale")}</DecisionBadge> : null}
        </div>
        <WhatLine locale={locale} proposal={proposal} id={whatId} />
        {proposal.why ? (
          <p className="mt-1 text-[0.9375rem] leading-[1.375rem] text-ink" dir="auto" data-why>
            {proposal.why}
          </p>
        ) : null}
        {stale ? (
          <div className="mt-2 space-y-1 text-sm" data-stale>
            <p className="text-ink-muted" data-was>
              {fillNodes(PROPOSALS_COPY[locale]["proposals.stale.was"], { shown: <bdi dir="auto">{proposal.base.shown}</bdi> })}
            </p>
            <p className="text-ink" data-now>
              {fillNodes(PROPOSALS_COPY[locale]["proposals.stale.now"], { shown: <bdi dir="auto">{proposal.current ?? ""}</bdi> })}
            </p>
            <p className="text-ink-muted">{t("proposals.stale.line")}</p>
          </div>
        ) : null}
        {readOnly ? null : isEditing ? (
          <div
            className="mt-2 space-y-2"
            data-proposal-editor
          >
            <label htmlFor={editorId} className="block text-sm text-ink">
              {t(shape === "concept" ? "proposals.edit.concept" : shape === "synonym" ? "proposals.edit.synonym" : "proposals.edit.value")}
            </label>
            <input
              id={editorId}
              dir="auto"
              value={edited}
              onChange={(event) => setEdited(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  // The screen around the card is a form: Enter applies the edit, never submits the screen.
                  event.preventDefault();
                  if (value !== undefined && !disabled) void run(proposal, "edit", value);
                } else if (event.key === "Escape") {
                  event.preventDefault();
                  setEditing(null);
                  setTimeout(() => document.getElementById(`proposal-edit-button-${id}`)?.focus(), 0);
                }
              }}
              className="block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button disabled={disabled || value === undefined} aria-describedby={describedBy} onClick={() => value !== undefined && void run(proposal, "edit", value)} data-apply-edit>
                {t("proposals.act.applyEdit")}
              </Button>
              <Button
                variant="quiet"
                onClick={() => {
                  setEditing(null);
                  setTimeout(() => document.getElementById(`proposal-edit-button-${id}`)?.focus(), 0);
                }}
              >
                {t("proposals.act.cancel")}
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            {stale ? (
              <Button variant="quiet" disabled={disabled} aria-describedby={describedBy} onClick={() => void run(proposal, "reject")} data-reject>
                {t("proposals.act.dismiss")}
              </Button>
            ) : (
              <>
                <Button disabled={disabled} aria-describedby={describedBy} onClick={() => void run(proposal, "apply")} data-apply>
                  {t("proposals.act.apply")}
                </Button>
                <Button
                  id={`proposal-edit-button-${id}`}
                  disabled={disabled}
                  aria-describedby={describedBy}
                  onClick={() => {
                    setEditing(id);
                    setEdited(editText(proposal));
                    setTimeout(() => document.getElementById(editorId)?.focus(), 0);
                  }}
                  data-edit
                >
                  {t("proposals.act.edit")}
                </Button>
                <Button variant="quiet" disabled={disabled} aria-describedby={describedBy} onClick={() => void run(proposal, "reject")} data-reject>
                  {t("proposals.act.reject")}
                </Button>
              </>
            )}
          </div>
        )}
        <Evidence locale={locale} proposal={proposal} startOpen={!proposal.why} />
        {cardNote ? (
          <div className="mt-1 text-sm" data-card-note>
            <p className={cardNote.alert ? "text-blocked" : "text-ink-muted"} role={cardNote.alert ? "alert" : "status"}>
              {cardNote.text}
            </p>
            {cardNote.details?.length ? (
              <details className="text-xs">
                <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
                  {DETAILS_LABEL[locale]}
                </summary>
                <ul className="ms-4 list-disc">
                  {cardNote.details.map((d) => (
                    <li key={d}>
                      <bdi dir="ltr">{d}</bdi>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
          </div>
        ) : null}
      </li>
    );
  };

  const decidedRow = (proposal: Proposal) => {
    const id = proposal.proposal_id;
    const role = proposal.status === "rejected" ? "exclude" : "include";
    const status = proposal.status === "rejected" ? t("proposals.status.rejected") : proposal.status === "applied_edited" ? t("proposals.status.appliedEdited") : t("proposals.status.applied");
    const cardNote = note?.id === id ? note : null;
    return (
      <li key={id} id={proposalHash(id)} className="rounded-md border border-rule bg-paper p-3" data-proposal={id} data-status={proposal.status}>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <SourceLabel locale={locale} source={proposal.source} />
          <DecisionBadge role={role}>{status}</DecisionBadge>
        </div>
        <WhatLine locale={locale} proposal={proposal} id={`proposal-what-${id}`} />
        {proposal.status === "rejected" && !readOnly ? (
          <Button variant="quiet" className="px-0" disabled={disabled} aria-describedby={`proposal-what-${id}`} onClick={() => void run(proposal, "restore")} data-restore>
            {t("proposals.act.restore")}
          </Button>
        ) : null}
        {cardNote ? (
          <p className="mt-1 text-sm text-ink-muted" role="status">
            {cardNote.text}
          </p>
        ) : null}
      </li>
    );
  };

  return (
    <section aria-labelledby={headingId} aria-busy={loading || busy} className="rounded-lg border border-dashed border-ink-muted bg-leaf p-4 text-sm" data-proposals={step}>
      <h2 id={headingId} ref={heading} tabIndex={-1} className="font-semibold text-ink" data-proposals-heading>
        {fillNodes(PROPOSALS_COPY[locale]["proposals.title"], { n: n(counts.open) })}
        {counts.stale ? (
          <span className="ms-2 text-sm font-normal text-unclear" data-out-of-date>
            · {fillNodes(PROPOSALS_COPY[locale]["proposals.outOfDate"], { n: n(counts.stale) })}
          </span>
        ) : null}
      </h2>
      {offline ? (
        <p id={offlineId} className="mt-1 text-ink-muted" data-proposals-offline>
          {t("proposals.asOf", { time: asOf.slice(0, 16).replace("T", " ") })} · {t("proposals.offline")}
        </p>
      ) : null}
      {readOnly ? <p className="mt-1 text-ink-muted">{t("proposals.readOnly")}</p> : null}
      {listNote ? (
        <p className="mt-1 text-ink-muted" role="status">
          {listNote}
        </p>
      ) : null}
      {openCards.length ? (
        <ul aria-labelledby={headingId} className="mt-3 space-y-3">
          {openCards.map(card)}
        </ul>
      ) : (
        <p className="mt-1 text-ink-muted" data-proposals-none>
          {t("proposals.none")}
        </p>
      )}
      {decided.length ? (
        <details className="mt-3" data-decided>
          <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
            {fillNodes(PROPOSALS_COPY[locale]["proposals.decided"], { n: n(decided.length) })}
          </summary>
          <ul className="mt-2 space-y-2">{decided.map(decidedRow)}</ul>
        </details>
      ) : null}
      <p className="sr-only" role="status" aria-live="polite" data-proposals-announce>
        {announce}
      </p>
    </section>
  );
}

/** Where a check's action leads on the inception screens. */
function useInceptionLink(locale: Locale) {
  const assist = useAssist();
  return (check: Check): CheckLink | null => {
    if (!assist) return null;
    const { origin, sessionId } = assist;
    const action = check.action;
    if (action.kind === "proposal" && action.proposal_id) {
      const step = assist.proposals?.proposals.find((p) => p.proposal_id === action.proposal_id)?.step ?? check.step;
      const hash = proposalHash(action.proposal_id);
      return { proposal: action.proposal_id, href: inceptionLink(locale, String(step), sessionId, origin, hash), hash };
    }
    if (action.kind === "field" && action.step && action.field) {
      const hash = fieldHash(action.field, action.criterion_id);
      return { href: inceptionLink(locale, action.step, sessionId, origin, hash), hash };
    }
    if (action.step) return { href: inceptionLink(locale, action.step, sessionId, origin) };
    return null;
  };
}

function engineError(refusal: AssistRefusal): ScreeningApiError {
  return new ScreeningApiError(refusal.code, 0, refusal.message, refusal.details);
}

/** The checks panel of one inception step (02-checks "The panel on each step"). */
export function InceptionChecksPanel({ locale, step }: Readonly<{ locale: Locale; step: InceptionStepId }>) {
  const assist = useAssist();
  const link = useInceptionLink(locale);
  const origin = assist?.origin ?? "";
  const sessionId = assist?.sessionId ?? "";
  const loaded = assist?.loaded ?? 0;
  const load = useCallback(async () => (loaded > 0 && sessionId ? runChecks(origin, sessionId, step) : null), [origin, sessionId, step, loaded]);
  if (!assist) return null;
  return (
    <ChecksPanel
      locale={locale}
      mode="panel"
      name={step}
      load={load}
      reloadKey={loaded}
      dismiss={(check, reason) => dismissCheck(origin, sessionId, check.check_id, { subject: check.subject, evidence_digest: check.evidence_digest, ...(reason ? { reason } : {}) })}
      restore={(check) => restoreCheck(origin, sessionId, check.check_id, check.subject)}
      link={link}
      onDecided={assist.bump}
      dirty={assist.dirty}
      readOnly={assist.readOnly}
    />
  );
}

/** Review's "Ready to create?" list: every step's checks from the all-steps read, grouped, with step chips. */
export function ReadinessList({ locale }: Readonly<{ locale: Locale }>) {
  const assist = useAssist();
  const link = useInceptionLink(locale);
  const all = assist?.all ?? null;
  const allError = assist?.allError ?? null;
  const loaded = assist?.loaded ?? 0;
  const load = useCallback(async () => {
    if (!loaded) return null;
    if (allError) throw engineError(allError);
    return all;
  }, [all, allError, loaded]);
  if (!assist) return null;
  const { origin, sessionId } = assist;
  return (
    <ChecksPanel
      locale={locale}
      mode="readiness"
      name="review-ready"
      load={load}
      reloadKey={loaded}
      adoptAnswers={false}
      dismiss={(check, reason) => dismissCheck(origin, sessionId, check.check_id, { subject: check.subject, evidence_digest: check.evidence_digest, ...(reason ? { reason } : {}) })}
      restore={(check) => restoreCheck(origin, sessionId, check.check_id, check.subject)}
      link={link}
      onDecided={assist.bump}
      dirty={assist.dirty}
      readOnly={assist.readOnly}
    />
  );
}

/** The proposals, then the checks, of one inception step: placed by each screen above its button row. */
export function StepAssist({ locale, step }: Readonly<{ locale: Locale; step: InceptionStepId }>) {
  return (
    <div className="space-y-4" data-step-assist={step}>
      <ProposalList locale={locale} step={step} />
      {step === "review" ? null : <InceptionChecksPanel locale={locale} step={step} />}
    </div>
  );
}
