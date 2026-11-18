"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { isScreeningApiError } from "@/lib/screening-api";
import { listProposals, runChecks, type CheckList, type Draft, type DraftRecord, type ProposalListing } from "@/lib/inception-api";

/**
 * What the proposal list, the checks panel, the Review readiness list and the
 * stepper badges of one inception screen share (M10b Part B): the draft record
 * they describe, whether the page holds unsaved edits, whether the draft can
 * still change, and one all-steps read of the checks and of the proposals.
 *
 * Reads happen on page load and whenever `version` moves: after the screen's
 * save, after a proposal decision, after a check is dismissed or restored, and
 * after a search job ends. Nothing polls and nothing reads on keystrokes.
 */

export type AssistRefusal = { code: string; message: string; details?: unknown };

export interface AssistDraft {
  origin: string;
  record: DraftRecord | null;
  draft: Draft;
  saveError: AssistRefusal | null;
  assistVersion: number;
  bumpAssist: () => void;
  adoptDecision: (answer: { draft: Draft; updated_at: string }, field: string) => void;
}

export interface AssistState {
  locale: Locale;
  origin: string;
  sessionId: string;
  record: DraftRecord | null;
  /** The page holds edits the engine has not stored. */
  dirty: boolean;
  /** `DRAFT_CONFLICT` or `DRAFT_EMITTED`: the lists show decisions and offer no button. */
  readOnly: boolean;
  markReadOnly: () => void;
  version: number;
  bump: () => void;
  adoptDecision: AssistDraft["adoptDecision"];
  /** The all-steps checks (stepper badges, the Review list); `null` until read. */
  all: CheckList | null;
  allError: AssistRefusal | null;
  /** The all-steps proposals (stepper badges). */
  proposals: ProposalListing | null;
  /** Moves after each all-steps read, so the per-step lists read after the checks recorded their proposals. */
  loaded: number;
}

const AssistContext = createContext<AssistState | null>(null);

export function useAssist(): AssistState | null {
  return useContext(AssistContext);
}

export function refusalFrom(error: unknown): AssistRefusal {
  return isScreeningApiError(error) ? { code: error.code, message: error.serverMessage, details: error.serverDetails } : { code: "ENGINE_UNREACHABLE", message: "" };
}

export function isOfflineCode(code: string | undefined): boolean {
  return code === "ENGINE_UNREACHABLE" || code === "CONSOLE_UNREACHABLE" || code === "CONSOLE_TIMEOUT";
}

/** A draft compared as data: key order and absent keys do not make a page dirty. */
function stable(value: unknown): string {
  return JSON.stringify(value, (_key, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v as Record<string, unknown>).filter(([, x]) => x !== undefined).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
}

export function AssistProvider({ locale, state, active, children }: Readonly<{ locale: Locale; state: AssistDraft; active: boolean; children: ReactNode }>) {
  const { origin, record, draft, saveError, assistVersion, bumpAssist, adoptDecision } = state;
  const sessionId = record?.session_id ?? "";
  const [all, setAll] = useState<CheckList | null>(null);
  const [allError, setAllError] = useState<AssistRefusal | null>(null);
  const [proposals, setProposals] = useState<ProposalListing | null>(null);
  const [loaded, setLoaded] = useState(0);
  const [conflict, setConflict] = useState(false);

  useEffect(() => {
    if (!active || !sessionId) return;
    const controller = new AbortController();
    (async () => {
      try {
        const read = await runChecks(origin, sessionId, undefined, controller.signal);
        if (controller.signal.aborted) return;
        setAll(read);
        setAllError(null);
      } catch (error) {
        if (controller.signal.aborted) return;
        setAllError(refusalFrom(error));
      }
      try {
        const listing = await listProposals(origin, sessionId, undefined, controller.signal);
        if (!controller.signal.aborted) setProposals(listing);
      } catch {
        // The badges keep their last counts; the per-step list says what went wrong.
      }
      if (!controller.signal.aborted) setLoaded((n) => n + 1);
    })();
    return () => controller.abort();
  }, [active, origin, sessionId, assistVersion]);

  const markReadOnly = useCallback(() => setConflict(true), []);
  const dirty = !!record && stable(draft) !== stable(record.draft ?? {});
  const readOnly = conflict || !!record?.emitted || saveError?.code === "DRAFT_CONFLICT" || saveError?.code === "DRAFT_EMITTED";
  const value: AssistState = {
    locale,
    origin,
    sessionId,
    record,
    dirty,
    readOnly,
    markReadOnly,
    version: assistVersion,
    bump: bumpAssist,
    adoptDecision,
    all,
    allError,
    proposals,
    loaded,
  };
  return <AssistContext.Provider value={value}>{children}</AssistContext.Provider>;
}
