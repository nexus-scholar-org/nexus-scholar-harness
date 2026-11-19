import type { Locale } from "@/i18n";

import { consoleBase, readJson } from "./screening-api";

/**
 * The next-step bar's answer (`docs/ux/shared/final/04-next-step.md`, M10b Part C):
 * `GET /api/v1/review/next-step` for the open workspace and
 * `GET /api/v1/inception/drafts/{id}/next-step` for a draft. The engine
 * (`src/scholar_harness/console/next_step.py`) computes the state, the waiting
 * variant, the params and the destination screen; this file only types the
 * answer, reads it, and maps a screen name to a route.
 */

export const NEXT_STEP_SHAPE = "review.next-step-v1";

export interface NextStepAction {
  key: string;
  to: { screen: string; query: Record<string, string | number | null | undefined> };
}

export interface NextStepWaiting {
  kind: "running" | "stopped" | "failed" | "interrupted" | string;
  stage: string;
  job: { job_id?: string | null; kind?: string; action_id?: string; state?: string; started_at?: string | null } | null;
  reason: { code: string; message: string | null } | null;
  since: string | null;
  details?: { stage_known?: boolean } & Record<string, unknown>;
}

export interface NextStep {
  shape: typeof NEXT_STEP_SHAPE | string;
  scope: "workspace" | "draft" | string;
  phase: "inception" | "discovery" | "screening" | "published" | null | string;
  round: number;
  state: string;
  params: Record<string, unknown>;
  waiting: NextStepWaiting | null;
  action: NextStepAction | null;
  also: NextStepAction[];
  unknown: string[];
  protocol_fingerprint: string | null;
  computed_at: string;
}

/** The bar's two reads. No `If-None-Match` is sent: the engine sends no ETag and the bar keeps the newest `computed_at`. */
export function getNextStep(origin: string, draftId: string | null, signal?: AbortSignal): Promise<NextStep> {
  const path = draftId ? `/api/v1/inception/drafts/${encodeURIComponent(draftId)}/next-step` : "/api/v1/review/next-step";
  return readJson<NextStep>(path, consoleBase(origin), signal);
}

/**
 * The screen names the engine sends in `action.to.screen`, and the route of each.
 * This is the one table; the bar never builds a destination any other way.
 */
export const SCREEN_ROUTES: Record<string, string> = {
  workspaces: "workspaces",
  "inception.list": "inception/",
  "inception.scope": "inception/scope/",
  "inception.explore": "inception/explore/",
  "inception.direction": "inception/direction/",
  "inception.shape": "inception/shape/",
  "inception.criteria": "inception/criteria/",
  "inception.review": "inception/review/",
  "inception.done": "inception/done/",
  "discovery.plan": "discovery/plan/",
  "discovery.harvest": "discovery/harvest/",
  "discovery.handoff": "discovery/handoff/",
  "discovery.chase": "discovery/chase/",
  "screening.home": "screening/home",
  "screening.triage": "screening/triage",
  "screening.publish": "screening/publish",
};

/** The ids a destination may carry (`action.to.query`); the browser adds only `console`. */
const QUERY_KEYS = ["run", "job", "draft"] as const;

/** The link to a screen the engine named, or `null` for a name this page does not know. */
export function screenHref(locale: Locale, action: NextStepAction, origin = ""): string | null {
  const route = SCREEN_ROUTES[action.to.screen];
  if (route === undefined) return null;
  const query = new URLSearchParams();
  for (const key of QUERY_KEYS) {
    const value = action.to.query?.[key];
    if (value !== null && value !== undefined && value !== "") query.set(key, String(value));
  }
  if (origin) query.set("console", origin);
  const q = query.toString();
  return `/${locale}/${route}${q ? `?${q}` : ""}`;
}

/**
 * The screen name of the current route, in the engine's naming: `/en/discovery/handoff`
 * is `discovery.handoff`, `/en/inception` is `inception.list`. Used only to compare with
 * `action.to.screen` (the naming form), never to choose a state.
 */
export function currentScreen(pathname: string): string {
  const parts = pathname.split("/").filter(Boolean).slice(1);
  if (parts[0] === "workspaces") return "workspaces";
  if (parts[0] === "inception" && parts.length === 1) return "inception.list";
  if (parts[0] === "discovery" && parts.length === 1) return "discovery.overview";
  return parts.slice(0, 2).join(".");
}

/** The gates (spec "Desktop layout" rule 3): the bar names the gate's own button there. */
export function isGate(screen: string, state: string): boolean {
  return (
    (screen === "discovery.handoff" && state === "CORPUS_READY") ||
    (screen === "discovery.chase" && state === "CHASE_READY_TO_SEND") ||
    screen === "screening.publish"
  );
}

/**
 * Which answer the bar reads on a route: `draft` on an inception step, `workspace` on a
 * discovery or screening screen, `null` where the bar is not drawn (the workspaces list,
 * the drafts list, the triage focus screen and any other route).
 */
export function barScope(pathname: string): "draft" | "workspace" | null {
  const parts = pathname.split("/").filter(Boolean).slice(1);
  if (parts[0] === "inception") return parts.length > 1 ? "draft" : null;
  if (parts[0] === "discovery") return "workspace";
  if (parts[0] === "screening") return parts[1] === "triage" ? null : "workspace";
  return null;
}
