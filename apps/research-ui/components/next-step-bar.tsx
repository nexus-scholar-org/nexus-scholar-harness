"use client";

import { Fragment, useCallback, useEffect, useId, useRef, useState, type ComponentType, type ReactNode, type SVGProps } from "react";
import { ArrowPathIcon, ArrowRightIcon, ExclamationTriangleIcon, PauseCircleIcon, XCircleIcon } from "@heroicons/react/24/outline";

import { LOCALE_METADATA, type Locale } from "@/i18n";
import { DataCell } from "@/components/ui/base";
import { stamp } from "@/components/inception-frame";
import { REVIEW_CHANGED_EVENT } from "@/components/review-bus";
import { INCEPTION_COPY } from "@/lib/inception-copy";
import { isScreeningApiError } from "@/lib/screening-api";
import { stateCopy } from "@/lib/screening-states";
import { NEXT_STEP_COPY, ROUND_STATES, nextStepTemplate, type NextStepCopyKey } from "@/lib/next-step-copy";
import {
  NEXT_STEP_SHAPE,
  barScope,
  currentScreen,
  getNextStep,
  isGate,
  screenHref,
  type NextStep,
  type NextStepAction,
} from "@/lib/next-step";

/**
 * The next-step bar (`docs/ux/shared/final/04-next-step.md`, M10b Part C): one
 * sentence saying what comes next and one link to the screen that owns it.
 *
 * The engine computes everything the bar shows: the state, the waiting variant,
 * the params and the destination screen. The bar picks copy keys from the codes,
 * prints the params as sent (formatted as numbers, never derived), maps the
 * screen name to a route through `lib/next-step.ts`, and decides only between a
 * link and the naming form by comparing that screen with the current one. It
 * writes nothing.
 */

const POLL_MS = 5_000;
const STALE_MS = 30_000;
const ANNOUNCE_MS = 2_000;

/** Codes that mean the engine could not be reached (the proxy's 502 and 504, or the fetch itself). */
const UNREACHABLE = new Set(["ENGINE_UNREACHABLE", "CONSOLE_UNREACHABLE", "CONSOLE_TIMEOUT", "MALFORMED_JSON"]);

type View =
  | { status: "loading" }
  | { status: "hidden" }
  | { status: "ready"; answer: NextStep }
  | { status: "offline"; answer: NextStep };

/** One filled hole of a sentence: the engine's value as text, isolated in `bdi` (LTR for ids and numbers). */
export type Slot = { text: string; ltr?: boolean };

export interface Described {
  /** The waiting variant's word (`next.word.<kind>`), or `null` outside a waiting variant. */
  kind: "running" | "stopped" | "failed" | "interrupted" | null;
  template: string;
  slots: Record<string, Slot>;
}

function copy(locale: Locale, key: NextStepCopyKey): string {
  return NEXT_STEP_COPY[locale][key];
}

function numberSlot(locale: Locale, value: unknown): Slot {
  if (typeof value === "number" && Number.isFinite(value)) {
    return { text: new Intl.NumberFormat(LOCALE_METADATA[locale].tag, { numberingSystem: "latn" }).format(value), ltr: true };
  }
  return { text: value === null || value === undefined || value === "" ? "—" : String(value), ltr: true };
}

/** An inception field by its existing label (the labels the inception screens use); an unknown name as sent. */
function fieldLabel(locale: Locale, field: string): string {
  const inception = INCEPTION_COPY[locale] as Record<string, string>;
  return inception[`field.${field}`] ?? nextStepTemplate(locale, `next.field.${field}`) ?? field;
}

function stepLabel(locale: Locale, step: string): string {
  return (INCEPTION_COPY[locale] as Record<string, string>)[`step.${step}`] ?? step;
}

function listText(locale: Locale, items: string[]): string {
  if (!items.length) return "—";
  try {
    return new Intl.ListFormat(LOCALE_METADATA[locale].tag, { style: "long", type: "conjunction" }).format(items);
  } catch {
    return items.join(", ");
  }
}

function holes(template: string): string[] {
  return [...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]);
}

/** The sentence key for an answer: the waiting variant's when there is one, else the state's. */
function sentenceKey(answer: NextStep): string {
  const w = answer.waiting;
  if (!w) return `next.state.${answer.state}`;
  if (w.kind === "running" || w.stage === "accepting_chase") return `next.waiting.${w.stage}`;
  if (w.kind === "stopped") return w.stage === "searching" ? "next.stopped.searching" : "next.stopped.stage";
  if (w.kind === "failed") return w.stage === "searching" ? "next.failed.searching" : "next.failed.stage";
  if (w.kind === "interrupted") return "next.interrupted";
  return `next.state.${answer.state}`;
}

/** Insert " in round {round}" before the first sentence's full stop. */
function withRound(template: string, suffix: string): string {
  const stop = template.indexOf(".");
  return stop < 0 ? template + suffix : template.slice(0, stop) + suffix + template.slice(stop);
}

/** Which copy and which of the engine's values make the sentence. Nothing is computed from the values. */
export function describe(locale: Locale, answer: NextStep): Described {
  const params = answer.params ?? {};
  const w = answer.waiting;
  let template = nextStepTemplate(locale, sentenceKey(answer)) ?? nextStepTemplate(locale, `next.state.${answer.state}`) ?? answer.state;
  if (!w && ROUND_STATES.has(answer.state) && typeof params.round === "number" && params.round > 1) {
    template = withRound(template, copy(locale, "next.inRound"));
  }
  const slots: Record<string, Slot> = {};
  for (const hole of holes(template)) {
    if (hole === "fields") {
      const fields = Array.isArray(params.fields) ? params.fields.map(String) : [];
      slots.fields = { text: listText(locale, fields.map((f) => fieldLabel(locale, f))) };
    } else if (hole === "what") {
      slots.what = { text: nextStepTemplate(locale, `next.state.SETUP_NEEDED.what.${String(params.what)}`) ?? String(params.what ?? "—") };
    } else if (hole === "stage") {
      const stage = String((params.stage as string | null | undefined) ?? w?.stage ?? "");
      slots.stage = { text: nextStepTemplate(locale, `next.stage.${stage}`) ?? stage };
    } else if (hole === "message") {
      slots.message = { text: w?.reason?.message ?? "", ltr: true };
    } else if (hole === "title") {
      slots.title = { text: String(params.title ?? params.slug ?? "—") };
    } else if (hole === "run") {
      slots.run = { text: String(params.run ?? "—"), ltr: true };
    } else {
      slots[hole] = numberSlot(locale, params[hole]);
    }
  }
  const kind = w && (w.kind === "running" || w.kind === "stopped" || w.kind === "failed" || w.kind === "interrupted") ? w.kind : null;
  return { kind, template, slots };
}

/** A button label: `next.action.<key>`, with `{step}` the inception step's existing name. */
export function actionLabel(locale: Locale, action: NextStepAction, answer: NextStep): string {
  const template = nextStepTemplate(locale, `next.action.${action.key}`);
  if (template === null) return action.key;
  return template.replace(/\{(\w+)\}/g, (_, hole: string) => {
    if (hole !== "step") return "";
    const step = typeof answer.params?.step === "string" ? answer.params.step : action.to.screen.split(".")[1] ?? "";
    return stepLabel(locale, step);
  });
}

function textOf(described: Pick<Described, "template" | "slots">): string {
  return described.template.replace(/\{(\w+)\}/g, (_, k: string) => described.slots[k]?.text ?? "");
}

function nodesOf(described: Pick<Described, "template" | "slots">): ReactNode {
  return described.template.split(/(\{\w+\})/g).map((part, index) => {
    const match = part.match(/^\{(\w+)\}$/);
    if (!match) return <Fragment key={index}>{part}</Fragment>;
    const slot = described.slots[match[1]];
    if (!slot || slot.text === "") return null;
    return (
      <bdi key={index} dir={slot.ltr ? "ltr" : undefined} data-slot={match[1]}>
        {slot.text}
      </bdi>
    );
  });
}

/** The sentence as plain text, for the live region and the offline line. */
export function sentenceText(locale: Locale, answer: NextStep): string {
  const described = describe(locale, answer);
  const extra = answer.state === "CORPUS_READY" && answer.params?.protocol_changed === true && !answer.waiting ? ` ${copy(locale, "next.protocolChanged")}` : "";
  return textOf(described) + extra;
}

function isOlder(candidate: string, shown: string): boolean {
  const a = Date.parse(candidate);
  const b = Date.parse(shown);
  if (Number.isNaN(a) || Number.isNaN(b)) return String(candidate) < String(shown);
  return a < b;
}

function unreachable(error: unknown): boolean {
  if (!isScreeningApiError(error)) return true;
  return UNREACHABLE.has(error.code) || error.status >= 500 || error.status === 0;
}

const WORD: Record<NonNullable<Described["kind"]>, { icon: ComponentType<SVGProps<SVGSVGElement>>; className: string }> = {
  running: { icon: ArrowPathIcon, className: "text-brand" },
  stopped: { icon: PauseCircleIcon, className: "text-unclear" },
  failed: { icon: XCircleIcon, className: "text-blocked" },
  interrupted: { icon: ExclamationTriangleIcon, className: "text-unclear" },
};

const SUMMARY =
  "min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-xs text-ink-muted";

const ACTION =
  "inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md border border-brand bg-leaf px-4 text-sm font-medium text-brand hover:bg-brand-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus sm:w-auto";

/** The shell's bar: drawn on inception steps (a draft) and on discovery and screening screens (the workspace). */
export function NextStepBar({ locale, pathname }: Readonly<{ locale: Locale; pathname: string }>) {
  const scope = barScope(pathname);
  if (scope === null) return null;
  return <Bar key={scope} locale={locale} pathname={pathname} scope={scope} />;
}

function Bar({ locale, pathname, scope }: Readonly<{ locale: Locale; pathname: string; scope: "draft" | "workspace" }>) {
  const labelId = useId();
  const [view, setView] = useState<View>({ status: "loading" });
  const [tick, setTick] = useState(0);
  // `?console=` and `?draft=`, read after hydration (the pages are prerendered without a query) and again on each route.
  const [address, setAddress] = useState({ origin: "", draft: "", ready: false });
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setAddress({ origin: query.get("console") ?? "", draft: query.get("draft") ?? "", ready: true });
  }, [pathname]);

  const addressRef = useRef(address);
  addressRef.current = address;
  const shown = useRef<NextStep | null>(null);
  const inFlight = useRef(false);
  const again = useRef(false);
  const lastRead = useRef(0);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!address.ready) return;
    if (scope === "draft" && !address.draft) {
      shown.current = null;
      setView({ status: "hidden" });
      return;
    }
    // Never two requests at once: a refresh asked for meanwhile runs once after this one.
    if (inFlight.current) {
      again.current = true;
      return;
    }
    inFlight.current = true;
    try {
      do {
        again.current = false;
        try {
          // The newest address: a refresh queued by a route change reads the new route, not this one.
          const { origin, draft } = addressRef.current;
          const answer = await getNextStep(origin, scope === "draft" ? draft : null);
          lastRead.current = Date.now();
          if (!alive.current) return;
          if (!answer || answer.shape !== NEXT_STEP_SHAPE) {
            shown.current = null;
            setView({ status: "hidden" });
          } else if (!shown.current || !isOlder(answer.computed_at, shown.current.computed_at)) {
            shown.current = answer;
            setView({ status: "ready", answer });
          }
        } catch (error) {
          lastRead.current = Date.now();
          if (!alive.current) return;
          if (unreachable(error)) {
            // Offline keeps the last answer "as of" its time, without a button; with none, nothing is known to show.
            setView(shown.current ? { status: "offline", answer: shown.current } : { status: "hidden" });
          } else {
            // A phone token, a host or token refusal, a draft refusal, an older engine: no bar.
            shown.current = null;
            setView({ status: "hidden" });
          }
        }
      } while (again.current && alive.current);
    } finally {
      inFlight.current = false;
      if (alive.current) setTick((n) => n + 1);
    }
  }, [address, scope]);

  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;

  // On mount and on every route change (the address is read again).
  useEffect(() => {
    void refresh();
  }, [refresh]);

  // After a write or a job event a screen announces.
  useEffect(() => {
    const onChange = () => void refreshRef.current();
    window.addEventListener(REVIEW_CHANGED_EVENT, onChange);
    return () => window.removeEventListener(REVIEW_CHANGED_EVENT, onChange);
  }, []);

  // On focus and when the tab becomes visible, when the last answer is older than 30 s.
  useEffect(() => {
    const onWake = () => {
      if (document.visibilityState === "hidden") return;
      if (Date.now() - lastRead.current > STALE_MS) void refreshRef.current();
    };
    window.addEventListener("focus", onWake);
    document.addEventListener("visibilitychange", onWake);
    return () => {
      window.removeEventListener("focus", onWake);
      document.removeEventListener("visibilitychange", onWake);
    };
  }, []);

  // A 5 s poll only while something runs (a page with no stream gets no event).
  const running = (view.status === "ready" || view.status === "offline") && view.answer.waiting?.kind === "running";
  useEffect(() => {
    if (!running) return;
    const timer = window.setTimeout(() => void refreshRef.current(), POLL_MS);
    return () => window.clearTimeout(timer);
  }, [running, tick]);

  // The live region: announced only when the state or the waiting stage changes, 2 s after it settles.
  const [announce, setAnnounce] = useState("");
  const announced = useRef<string | null>(null);
  const liveKey =
    view.status === "ready" ? `${view.answer.state}|${view.answer.waiting?.stage ?? ""}` : view.status === "offline" ? "offline" : null;
  const liveText =
    view.status === "ready" ? sentenceText(locale, view.answer) : view.status === "offline" ? copy(locale, "next.offline") : "";
  useEffect(() => {
    if (liveKey === null) return;
    if (announced.current === null) {
      announced.current = liveKey; // the first answer is the page's own state, not a change
      return;
    }
    if (liveKey === announced.current) return;
    const timer = window.setTimeout(() => {
      announced.current = liveKey;
      setAnnounce(liveText);
    }, ANNOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [liveKey, liveText]);

  if (view.status === "hidden") return null;

  return (
    <section
      aria-labelledby={labelId}
      aria-busy={view.status === "loading" ? true : undefined}
      className="border-b border-rule bg-leaf text-ink"
      data-next-step={view.status}
      data-next-state={view.status === "ready" || view.status === "offline" ? view.answer.state : undefined}
    >
      <span id={labelId} className="sr-only">
        {copy(locale, "next.region")}
      </span>
      <div className="mx-auto flex min-h-12 max-w-7xl flex-col gap-2 px-4 py-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-6 lg:px-8">
        {view.status === "loading" ? (
          <div aria-hidden="true" className="h-5 w-2/3 animate-pulse rounded-sm bg-rule" data-next-skeleton />
        ) : view.status === "offline" ? (
          <Offline locale={locale} answer={view.answer} />
        ) : (
          <Ready locale={locale} answer={view.answer} pathname={pathname} origin={address.origin} />
        )}
      </div>
      <p className="sr-only" role="status" aria-live="polite" data-next-live>
        {announce}
      </p>
    </section>
  );
}

function Offline({ locale, answer }: Readonly<{ locale: Locale; answer: NextStep }>) {
  const last = describe(locale, answer);
  return (
    <p className="min-w-0 flex-1 text-sm" data-next-offline>
      {copy(locale, "next.offline")}{" "}
      {copy(locale, "next.offline.last").split(/(\{sentence\})/).map((part, index) =>
        part === "{sentence}" ? <Fragment key={index}>{nodesOf(last)}</Fragment> : <Fragment key={index}>{part}</Fragment>,
      )}{" "}
      <span className="text-ink-muted" data-next-as-of>
        <AsOf locale={locale} at={answer.computed_at} />
      </span>
    </p>
  );
}

function AsOf({ locale, at }: Readonly<{ locale: Locale; at: string }>) {
  return (
    <>
      {copy(locale, "next.asOf")
        .split(/(\{time\})/)
        .map((part, index) =>
          part === "{time}" ? (
            <bdi key={index} dir="ltr">
              {stamp(at)}
            </bdi>
          ) : (
            <Fragment key={index}>{part}</Fragment>
          ),
        )}
    </>
  );
}

function Ready({ locale, answer, pathname, origin }: Readonly<{ locale: Locale; answer: NextStep; pathname: string; origin: string }>) {
  const described = describe(locale, answer);
  const screen = currentScreen(pathname);
  const action = answer.action;
  const label = action ? actionLabel(locale, action, answer) : "";
  const href = action ? screenHref(locale, action, origin) : null;
  // Rules 2 and 3 of the layout: the screen's own control is named, never linked a second time.
  const naming = !!action && (action.to.screen === screen || isGate(screen, answer.state));
  const also = (answer.also ?? []).filter((a) => a.to.screen !== screen).slice(0, 1);
  const word = described.kind ? WORD[described.kind] : null;
  const Icon = word?.icon;

  return (
    <>
      <div className="min-w-0 flex-1">
        <p className="text-sm leading-6" data-next-sentence>
          {described.kind && word && Icon ? (
            <span className={`me-2 flex items-center gap-1 font-semibold sm:inline-flex ${word.className}`} data-next-word={described.kind}>
              <Icon aria-hidden="true" className="size-4 shrink-0" />
              {copy(locale, `next.word.${described.kind}`)}
            </span>
          ) : null}
          {nodesOf(described)}
          {answer.state === "CORPUS_READY" && answer.params?.protocol_changed === true && !answer.waiting ? (
            <> {copy(locale, "next.protocolChanged")}</>
          ) : null}
        </p>
        <Details locale={locale} answer={answer} />
      </div>
      {action && naming ? (
        <p className="text-sm text-ink-muted sm:max-w-sm" data-next-here>
          {copy(locale, "next.here").replace("{label}", label)}
        </p>
      ) : null}
      {(action && !naming && href) || also.length ? (
        <div className="flex flex-col items-stretch gap-1 sm:flex-row sm:items-center sm:gap-4">
          {also.map((a) => {
            const alsoHref = screenHref(locale, a, origin);
            return alsoHref ? (
              <a key={a.key} className="inline-flex min-h-11 items-center text-sm text-brand underline" href={alsoHref} data-next-also={a.key}>
                {actionLabel(locale, a, answer)}
              </a>
            ) : null;
          })}
          {action && !naming && href ? (
            <a className={ACTION} href={href} data-next-action={action.key}>
              {label}
              <ArrowRightIcon aria-hidden="true" className="size-4 shrink-0 rtl:-scale-x-100" />
            </a>
          ) : null}
        </div>
      ) : null}
    </>
  );
}

function Row({ label, children, attr }: Readonly<{ label: string; children: ReactNode; attr: string }>) {
  return (
    <div className="flex flex-wrap gap-x-2" {...{ [`data-next-detail-${attr}`]: "" }}>
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-ink">{children}</dd>
    </div>
  );
}

function Id({ value }: Readonly<{ value: string }>) {
  return (
    <DataCell>
      <bdi dir="ltr">{value}</bdi>
    </DataCell>
  );
}

function Details({ locale, answer }: Readonly<{ locale: Locale; answer: NextStep }>) {
  const w = answer.waiting;
  const reason = w?.reason ?? null;
  const known = reason ? nextStepTemplate(locale, `next.reason.${reason.code}`) : null;
  const registered = reason && !known ? stateCopy(locale, reason.code) : null;
  const run = typeof answer.params?.run === "string" ? answer.params.run : null;
  const job = w?.job?.job_id ?? null;
  const cannot = typeof answer.params?.cannot_finish === "string" ? answer.params.cannot_finish : null;
  // The stage of an interruption is named only when the engine's marker had one.
  const stageNamed = w?.kind === "interrupted" && w.details?.stage_known === true && typeof answer.params?.stage === "string" ? String(answer.params.stage) : null;
  return (
    <details className="text-xs" data-next-details>
      <summary className={SUMMARY}>{copy(locale, "next.details")}</summary>
      <dl className="space-y-1 pb-1">
        <Row label={copy(locale, "next.details.state")} attr="state">
          <Id value={answer.state} />
        </Row>
        {w ? (
          <Row label={copy(locale, "next.details.stage")} attr="stage">
            <Id value={w.stage} />
          </Row>
        ) : null}
        {stageNamed ? (
          <Row label={copy(locale, "next.details.stage")} attr="stage-named">
            {nextStepTemplate(locale, `next.stage.${stageNamed}`) ?? stageNamed}
          </Row>
        ) : null}
        {run ? (
          <Row label={copy(locale, "next.details.run")} attr="run">
            <Id value={run} />
          </Row>
        ) : null}
        {job ? (
          <Row label={copy(locale, "next.details.job")} attr="job">
            <Id value={job} />
          </Row>
        ) : null}
        {w?.since ? (
          <Row label={copy(locale, "next.details.since")} attr="since">
            <bdi dir="ltr">{stamp(w.since)}</bdi>
          </Row>
        ) : null}
        {reason ? (
          <Row label={copy(locale, "next.details.reason")} attr="reason">
            <Id value={reason.code} /> {known ?? (registered?.known ? registered.title : null)}{" "}
            {reason.message ? <bdi dir="ltr">{reason.message}</bdi> : null}
          </Row>
        ) : null}
        {cannot ? (
          <Row label={copy(locale, "next.details.cannotFinish")} attr="cannot-finish">
            <Id value={cannot} />
          </Row>
        ) : null}
      </dl>
      {answer.unknown?.length ? (
        <div className="pb-1" data-next-unknown>
          <p className="text-ink">{copy(locale, "next.unknown")}</p>
          <p className="text-ink-muted">
            {copy(locale, "next.details.notRead")}: <Id value={answer.unknown.join(", ")} />
          </p>
        </div>
      ) : null}
      <p className="pb-2 text-ink-muted" data-next-computed>
        <AsOf locale={locale} at={answer.computed_at} />
      </p>
    </details>
  );
}
