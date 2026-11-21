"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DiscoveryChecksPanel } from "@/components/discovery-checks";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, Hint, PRIMARY_LINK, type DecisionRole } from "@/components/ui/base";
import { DatabasePicker, type PickerItem, type PickerLabels } from "@/components/database-picker";
import { EstimateCard } from "@/components/discovery-estimate";
import { DiscoveryProposals } from "@/components/discovery-proposals";
import { StateCard } from "@/components/screening-state-card";
import {
  DiscoveryFrame,
  DiscoveryRefusal,
  Eyebrow,
  LINK,
  Loading,
  MailtoCard,
  OpenAlexKeyCard,
  PLAN_SEARCH_ANCHOR,
  discoveryHref,
  planSearchHref,
  refusalOf,
  type Refusal,
} from "@/components/discovery-frame";
import { KNOWN_PROVIDERS, getPlan, getRuns, type Plan } from "@/lib/discovery-api";
import { PlanChangeSearch, PlanSearchToggle } from "@/components/plan-change-search";
import { getCorpus } from "@/lib/screening-v1";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 01 Plan (spec `docs/ux/phase1-discovery/final/01-plan.md`): what each
 * database will receive, from `GET /discovery/plan` (the engine's dry run). The
 * screen writes nothing: there is no approve action, starting a harvest is the
 * record. The cap shown is the protocol's only; a run override lives on Harvest.
 *
 * M10a (decided 2026-11-14, item 2a): a picker chooses and orders the databases
 * of this harvest only. A change re-reads `GET /discovery/plan?providers=...`;
 * the choice lives in this page and the link to Harvest (`?databases=`), never
 * in the protocol.
 */

const STATUS_ROLE: Record<string, DecisionRole> = { translated: "include", selected: "unclear", not_selected: "exclude", off_by_default: "exclude" };

// --------------------------------------------------------------------------- the picker, shared with 03 Harvest

/** Two lists hold the same names in the same order. */
export function sameList(a: readonly string[] | null | undefined, b: readonly string[] | null | undefined): boolean {
  return !!a && !!b && a.length === b.length && a.every((name, i) => name === b[i]);
}

/** The list a run sent no `providers` searches (`protocol_providers`); an older console's selected rows. */
export function protocolList(plan: Plan): string[] {
  return plan.protocol_providers ?? plan.providers.filter((p) => p.selected).map((p) => p.name);
}

/** The list the screens start from (H-run-small-fixes, finding 9); an older console's protocol list. */
export function defaultList(plan: Plan): string[] {
  return plan.default_providers ?? protocolList(plan);
}

/**
 * H-run-small-fixes (finding 9): a warning for each chosen database that drops the AND
 * between concepts, and a line when the default left one out. The engine names them.
 */
export function IgnoresAndNotes({ locale, plan, choice }: Readonly<{ locale: Locale; plan: Plan; choice: readonly string[] }>) {
  const t = discoveryT(locale);
  const n = plan.concepts ?? 0;
  const ignores = plan.ignores_and ?? [];
  const chosen = ignores.filter((p) => choice.includes(p));
  const leftOut = plan.default_reason ? ignores.filter((p) => !choice.includes(p) && protocolList(plan).includes(p)) : [];
  if (!chosen.length && !leftOut.length) return null;
  return (
    <div className="space-y-2">
      {chosen.map((p) => (
        <p key={p} role="status" className="rounded-md bg-unclear-soft p-3 text-sm text-ink" data-ignores-and={p}>
          {t("plan.ignoresAnd", { name: providerName(p), n })}
        </p>
      ))}
      {leftOut.map((p) => (
        <p key={p} className="text-sm text-ink-muted" data-default-without={p}>
          {t("plan.defaultWithout", { name: providerName(p), n })}
        </p>
      ))}
    </div>
  );
}

/** The six databases the engine knows, in its order; bioRxiv keeps its "Off by default" note. */
export function pickerItems(locale: Locale): PickerItem[] {
  const t = discoveryT(locale);
  return KNOWN_PROVIDERS.map((id) => ({ id, label: providerName(id), note: id === "biorxiv" ? t("plan.status.off_by_default") : undefined }));
}

/** Every picker string, from this module's copy: the picker itself has none. */
export function pickerLabels(locale: Locale): PickerLabels {
  const t = discoveryT(locale);
  const row = (kind: "check" | "up" | "down", name: string) => {
    const id = KNOWN_PROVIDERS.find((known) => providerName(known) === name);
    return id ? t(`plan.picker.${kind}.${id}` as DiscoveryCopyKey) : name;
  };
  return {
    legend: t("plan.picker.legend"),
    orderHelp: t("plan.picker.orderHelp"),
    orderHelpHint: { locale, textKey: "plan.picker.orderHelp" },
    check: (name) => row("check", name),
    up: (name) => row("up", name),
    down: (name) => row("down", name),
    moved: (name, position, total) => t("plan.picker.moved", { name, n: String(position), total: String(total) }),
    none: t("plan.picker.none"),
  };
}

/**
 * How a chosen list differs from the protocol's: the databases added, the ones
 * left out, and the order of the databases both hold. When only the order
 * differs the line says "order"; beside an addition or a removal it names the
 * moved databases (the shared ones not at their protocol place among the shared
 * ones). A comparison of two lists, never a judgement; `null` when they are the same.
 */
export function differsText(locale: Locale, chosen: readonly string[], protocol: readonly string[]): string | null {
  const t = discoveryT(locale);
  const comma = locale === "ar" ? "، " : ", ";
  const names = (list: readonly string[]) => list.map(providerName).join(comma);
  const added = chosen.filter((name) => !protocol.includes(name));
  const leftOut = protocol.filter((name) => !chosen.includes(name));
  const kept = chosen.filter((name) => protocol.includes(name));
  const keptInProtocolOrder = protocol.filter((name) => chosen.includes(name));
  const moved = kept.filter((name, i) => name !== keptInProtocolOrder[i]);
  const parts: string[] = [];
  if (added.length) parts.push(t("plan.picker.differs.added", { names: names(added) }));
  if (leftOut.length) parts.push(t("plan.picker.differs.leftOut", { names: names(leftOut) }));
  if (moved.length) parts.push(parts.length ? t("plan.picker.differs.moved", { names: names(moved) }) : t("plan.picker.differs.order"));
  return parts.length ? t("plan.picker.differs", { list: parts.join(locale === "ar" ? "؛ " : "; ") }) : null;
}

/** The "differs from the protocol" line, in the `unclear` role: informational, never a refusal. */
export function DiffersLine({ locale, chosen, protocol }: Readonly<{ locale: Locale; chosen: readonly string[]; protocol: readonly string[] }>) {
  const text = differsText(locale, chosen, protocol);
  if (!text) return null;
  return (
    <p className="text-sm text-unclear" data-role="unclear" data-picker-differs>
      {text}
    </p>
  );
}

/**
 * `PROVIDER_UNKNOWN` (422): the shared card, each name the engine did not know
 * under Details (an empty name, as from `?databases=a,,b`, shown as `""`), and
 * "Reset to the protocol".
 */
export function ProviderUnknownCard({
  locale,
  refusal,
  origin,
  onReset,
  pageHeading = false,
}: Readonly<{ locale: Locale; refusal: Refusal; origin: string; onReset: () => void; pageHeading?: boolean }>) {
  const t = discoveryT(locale);
  const unknown = (refusal.details as { unknown?: unknown[] } | undefined)?.unknown;
  return (
    <div className="space-y-2" data-refusal={refusal.code}>
      <StateCard
        locale={locale}
        code={refusal.code}
        message={refusal.message}
        consoleOrigin={origin}
        pageHeading={pageHeading}
        hideActionLabel
        details={
          Array.isArray(unknown) && unknown.length ? (
            <div className="mt-1 text-sm" data-unknown-providers>
              <p className="text-ink-muted">{t("plan.picker.unknown")}</p>
              <ul className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
                {unknown.map((name, i) => (
                  <li key={i}>
                    <code className="font-mono text-[0.8125rem] text-ink" dir="ltr" data-unknown-provider>
                      {String(name) === "" ? '""' : String(name)}
                    </code>
                  </li>
                ))}
              </ul>
            </div>
          ) : null
        }
      />
      <Button onClick={onReset} data-picker-reset>
        {t("plan.picker.reset")}
      </Button>
    </div>
  );
}

/** `?databases=` from the page address, read after hydration; `null` when absent. */
export function readDatabasesParam(): string[] | null {
  const raw = new URLSearchParams(window.location.search).get("databases");
  return raw === null ? null : raw.split(",").map((part) => part.trim());
}

function harvestHref(locale: Locale, origin: string, databases: string[] | null, cap?: number): string {
  let href = discoveryHref(locale, "harvest", origin);
  const add = (query: string) => (href = href.includes("?") ? `${href}&${query}` : `${href}?${query}`);
  if (databases) add(`databases=${databases.map(encodeURIComponent).join(",")}`);
  // M10b Part D: "Use {cap} for this harvest" opens Harvest with the cap field filled; nothing is sent.
  if (cap !== undefined) add(`cap=${cap}`);
  return href;
}

/** The inception drafts screen, where the protocol is changed (`?console=` kept). */
function inceptionHref(locale: Locale, origin: string): string {
  return `/${locale}/inception/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`;
}

// --------------------------------------------------------------------------- the screen

export function DiscoveryPlan({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const [origin, setOrigin] = useState("");
  const address = useRef<string[] | null>(null);
  const [ready, setReady] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [hasRun, setHasRun] = useState(false);
  // M10b Part D: the estimate card is removed (not disabled) once the corpus is accepted.
  const [accepted, setAccepted] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [changed, setChanged] = useState(false);
  const [copied, setCopied] = useState(false);
  const [choice, setChoice] = useState<string[] | null>(null);
  const [pending, setPending] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  // M11a part D: "Change the search", opened by its button or by the anchor other screens link to.
  const [searchOpen, setSearchOpen] = useState(false);
  const searchToggle = useRef<HTMLButtonElement>(null);
  const focusToggle = useRef(false);
  const fingerprint = useRef<string | null>(null);
  const protocolRef = useRef<string[] | null>(null);
  const sequence = useRef(0);
  const started = useRef(false);
  // "Reset to the protocol" removes the button pressed (the card, or the reset once nothing differs):
  // focus goes to the h1, as soon as it is on the page (M10a).
  const focusHeading = useRef(false);

  useEffect(() => {
    if (focusHeading.current && heading.current) {
      focusHeading.current = false;
      heading.current.focus();
    }
  });

  useEffect(() => {
    if (focusToggle.current && !searchOpen) {
      focusToggle.current = false;
      searchToggle.current?.focus();
    }
  }, [searchOpen]);

  useEffect(() => {
    const follow = () => {
      if (window.location.hash === `#${PLAN_SEARCH_ANCHOR}`) setSearchOpen(true);
    };
    follow();
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setOrigin(query.get("console") ?? "");
    address.current = readDatabasesParam();
    setReady(true);
  }, []);

  const load = useCallback(
    async (providers: string[] | null, focus = false): Promise<void> => {
      const id = ++sequence.current;
      setRefusal(null);
      setPending(true);
      try {
        let next = await getPlan(origin, providers);
        if (id !== sequence.current) return;
        if (fingerprint.current && fingerprint.current !== next.protocol_fingerprint) setChanged(true);
        fingerprint.current = next.protocol_fingerprint;
        const protocol = protocolList(next);
        const before = protocolRef.current;
        protocolRef.current = protocol;
        if (before && !sameList(before, protocol)) {
          // The protocol's own list changed since this page was read: the picker follows it.
          setChanged(true);
          setChoice(protocol);
          if (providers) {
            next = await getPlan(origin, null);
            if (id !== sequence.current) return;
          }
        }
        // H-run-small-fixes: the first read starts from the default choice (the
        // protocol's list, without Crossref for a joined query), previewed as such.
        const start = next.requested_providers ?? defaultList(next);
        if (!started.current) {
          if (!providers && !sameList(start, protocol)) {
            next = await getPlan(origin, start);
            if (id !== sequence.current) return;
          }
          // Only once the default choice was read: a refused second read is tried again on retry (review P3).
          started.current = true;
        }
        setPlan(next);
        setChoice((current) => current ?? start);
        if (focus) heading.current?.focus();
      } catch (error) {
        if (id !== sequence.current) return;
        setRefusal(refusalOf(error));
      } finally {
        if (id === sequence.current) setPending(false);
      }
    },
    [origin],
  );

  useEffect(() => {
    if (!ready) return;
    // The first read takes the choice the address carried (`?databases=`), else the protocol's.
    void load(address.current);
    // Read once on load: "Check again" re-reads the plan and nothing else (spec 01 acceptance).
    getRuns(origin).then(
      (runs) => setHasRun(runs.runs.length > 0),
      () => undefined,
    );
    getCorpus(origin).then(
      (corpus) => setAccepted(corpus.state === "ACCEPTED"),
      () => undefined,
    );
  }, [ready, load, origin]);

  const protocol = protocolRef.current ?? (plan ? protocolList(plan) : []);
  /** The `providers` a read or a run is sent for a choice: none when it is the protocol's own list. */
  const requestFor = (list: string[]) => (sameList(list, protocol) ? null : list);
  const current = () => (choice && choice.length ? requestFor(choice) : null);

  const choose = (next: string[]) => {
    setChoice(next);
    if (!next.length) {
      // At least one must stay ticked: say so inline and read nothing.
      sequence.current++;
      setPending(false);
      return;
    }
    void load(requestFor(next));
  };

  const reset = () => {
    focusHeading.current = true;
    address.current = null;
    setChoice(protocolRef.current);
    void load(null);
  };

  const copyAll = async () => {
    if (!plan) return;
    const text = plan.providers
      .filter((p) => p.executed_query)
      .map((p) => `${providerName(p.name)}: ${p.executed_query}`)
      .join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const differs = !!choice && !sameList(choice, protocol);

  return (
    <DiscoveryFrame locale={locale} current="plan" origin={origin}>
      {refusal && !plan ? (
        refusal.code === "PROVIDER_UNKNOWN" ? (
          <ProviderUnknownCard locale={locale} refusal={refusal} origin={origin} onReset={reset} pageHeading />
        ) : (
          <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load(current())} pageHeading />
        )
      ) : !plan ? (
        <Loading locale={locale} />
      ) : (
        <div className="space-y-6">
          <header>
            <Eyebrow locale={locale} step="plan" name={t("plan.eyebrowName")} />
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink">
              {t("plan.title")}
            </h1>
            <p className="mt-2 max-w-2xl text-ink-muted" data-copy="lede">{t("plan.lede")}</p>
          </header>
          {/* M11a part D (10-plan-amend-search): opened, "Change the search" is a full-width region above the two columns. */}
          {searchOpen && plan.search ? (
            <PlanChangeSearch
              locale={locale}
              origin={origin}
              search={plan.search}
              fingerprint={plan.protocol_fingerprint}
              providers={choice}
              accepted={accepted}
              onClose={() => {
                focusToggle.current = true;
                setSearchOpen(false);
                if (window.location.hash === `#${PLAN_SEARCH_ANCHOR}`) {
                  try {
                    window.history.replaceState(window.history.state, "", window.location.pathname + window.location.search);
                  } catch {
                    // An address that cannot be rewritten only keeps the anchor.
                  }
                }
              }}
              onRecorded={(answer) => {
                // The researcher's own amendment is not "changed since this page was read" (review D-R1 #11).
                fingerprint.current = answer.protocol_fingerprint;
                void load(current(), true);
              }}
              onProtocolChanged={() => void load(current())}
            />
          ) : null}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 min-w-0 lg:col-span-2">
            <section aria-labelledby="plan-picker" className="space-y-3 rounded-lg border border-rule bg-leaf p-5" data-plan-picker>
              <h2 id="plan-picker" className="font-semibold text-ink">
                {t("plan.picker.title")}
              </h2>
              {choice ? <DatabasePicker items={pickerItems(locale)} value={choice} onChange={choose} labels={pickerLabels(locale)} /> : null}
              {plan.requested_providers ? <DiffersLine locale={locale} chosen={plan.requested_providers} protocol={protocol} /> : null}
              {choice ? <IgnoresAndNotes locale={locale} plan={plan} choice={choice} /> : null}
              {differs ? (
                <Button onClick={reset} data-picker-reset>
                  {t("plan.picker.reset")}
                </Button>
              ) : null}
              {/* Picker Loading (M10a): always in the page and outside the busy strings section, so the change of text is announced. */}
              <p role="status" className={pending ? "text-sm text-ink-muted" : "sr-only"} data-plan-status data-plan-loading={pending ? "" : undefined}>
                {pending ? t("plan.picker.loading") : ""}
              </p>
            </section>
            {refusal ? (
              refusal.code === "PROVIDER_UNKNOWN" ? (
                <ProviderUnknownCard locale={locale} refusal={refusal} origin={origin} onReset={reset} />
              ) : (
                <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load(current())} />
              )
            ) : null}
            {changed ? (
              <p role="status" className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-plan-changed>
                {t("plan.changed")}
              </p>
            ) : null}
            <section aria-labelledby="plan-strings" aria-busy={pending || undefined} className="rounded-lg border border-rule bg-leaf p-5" data-plan-strings>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 id="plan-strings" className="font-semibold text-ink">
                  {t("plan.strings.title")}
                </h2>
                {plan.search ? (
                  <PlanSearchToggle
                    locale={locale}
                    open={searchOpen}
                    buttonRef={searchToggle}
                    onToggle={() => {
                      if (searchOpen) focusToggle.current = true;
                      setSearchOpen((o) => !o);
                    }}
                  />
                ) : null}
              </div>
              <p className="mt-1 text-xs text-ink-muted">
                {t("plan.fingerprint")} <DataCell>{plan.protocol_fingerprint}</DataCell>
              </p>
              {plan.providers.every((p) => !p.selected) ? <p className="mt-3 text-ink">{t("plan.noneSelected")}</p> : null}
              {/* Picker Loading (M10a): the last answer stays, dimmed, until the new one arrives; nothing is invented. */}
              <div className={`mt-4 space-y-4 ${pending ? "opacity-60" : ""}`.trim()} data-plan-blocks data-dimmed={pending ? "true" : undefined}>
                {plan.providers.map((p) => {
                  const statusKey = `plan.status.${p.status}` as DiscoveryCopyKey;
                  const known = p.status in STATUS_ROLE;
                  return (
                    <section key={p.name} aria-label={providerName(p.name)} className="border-t border-rule pt-4" data-provider={p.name} data-status={p.status}>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-ink">{providerName(p.name)}</h3>
                        <DecisionBadge role={STATUS_ROLE[p.status] ?? "exclude"}>{known ? t(statusKey) : p.status}</DecisionBadge>
                      </div>
                      {p.executed_query ? (
                        <div className="mt-2 rounded-md border border-rule bg-paper p-3">
                          <p className="text-xs text-ink-muted">{t("plan.string.badge")}</p>
                          <p className="mt-1" data-executed>
                            <DataCell>{p.executed_query}</DataCell>
                          </p>
                        </div>
                      ) : p.selected ? (
                        <p className="mt-2 text-sm text-ink">{t("plan.noPreview")}</p>
                      ) : (
                        <p className="mt-2 text-sm text-ink-muted">{p.notes.length ? null : t("plan.notSearched")}</p>
                      )}
                      {p.request ? (
                        <details className="mt-2 text-sm">
                          <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{t("plan.request.show")}</summary>
                          <pre className="overflow-x-auto rounded-sm bg-paper p-2 font-mono text-[0.8125rem] text-ink" dir="ltr">
                            {JSON.stringify(p.request, null, 2)}
                          </pre>
                        </details>
                      ) : null}
                      {p.selected ? (
                        p.cannot_express.length || p.notes.length ? (
                          <ul className="mt-2 space-y-1 text-sm text-ink-muted">
                            {p.cannot_express.length ? (
                              <li>
                                {t("plan.cannotExpress", { list: "" })}
                                <bdi dir="ltr">{p.cannot_express.join(", ")}</bdi>
                              </li>
                            ) : null}
                            {p.notes.map((note) => (
                              <li key={note}>
                                <bdi dir="ltr">{note}</bdi>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-2 text-sm text-ink-muted">{t("plan.nothingDropped")}</p>
                        )
                      ) : p.notes.length ? (
                        <ul className="mt-2 space-y-1 text-sm text-ink-muted">
                          {p.notes.map((note) => (
                            <li key={note}>
                              <bdi dir="ltr">{note}</bdi>
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </section>
                  );
                })}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-rule pt-4">
                <Button onClick={() => void copyAll()} data-copy-all>
                  {t("plan.copyAll")}
                </Button>
                <span aria-live="polite" className="text-sm text-ink-muted">
                  {copied ? t("copied") : ""}
                </span>
              </div>
              {/* M10d (03-guidance D-P7, D-P8): how to add Scopus or Web of Science is a hint on the Import link; after a run the harvest's own warning says it. */}
              {hasRun ? null : (
                <p className="mt-3 flex items-center gap-1 text-sm text-ink-muted">
                  <a className={LINK} href={discoveryHref(locale, "import", origin)}>
                    {t("steps.import")}
                  </a>
                  <Hint locale={locale} label={t("steps.import")} text={t("plan.imports.hint")} textKey="plan.imports.hint" />
                </p>
              )}
            </section>
          </div>
          <aside className="space-y-4">
            {/* M10c D5: an assistant's suggested changes to the search; Apply re-reads the plan. */}
            <DiscoveryProposals locale={locale} origin={origin} onAmended={() => void load(choice)} />
            <DiscoveryChecksPanel locale={locale} step="plan" origin={origin} />
            <section aria-labelledby="plan-limits" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="plan-limits" className="font-semibold text-ink">
                {t("plan.limits.title")}
              </h2>
              <dl className="mt-3 space-y-3 text-sm">
                <div>
                  <dt className="text-ink-muted">{t("plan.limits.window")}</dt>
                  <dd className="text-ink">
                    {plan.query.year_min == null && plan.query.year_max == null ? (
                      t("plan.limits.noLimit")
                    ) : (
                      <bdi dir="ltr">
                        {plan.query.year_min ?? "…"}–{plan.query.year_max ?? "…"}
                      </bdi>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-ink-muted">{t("plan.limits.language")}</dt>
                  <dd className="text-ink">{plan.query.language ? <bdi dir="ltr">{plan.query.language}</bdi> : t("plan.limits.noLimit")}</dd>
                </div>
                <div data-cap={plan.cap.source}>
                  <dt className="flex items-center gap-1 text-ink-muted">
                    <span>{t("plan.limits.cap")}</span>
                    {plan.cap.source === "protocol" ? <Hint locale={locale} label={t("plan.limits.cap")} text={t("plan.limits.cap.protocol")} textKey="plan.limits.cap.protocol" /> : null}
                  </dt>
                  <dd className="text-ink">
                    <bdi dir="ltr">{plan.cap.value}</bdi>
                  </dd>
                  {plan.cap.source === "protocol" ? null : (
                    <dd className="mt-1 text-xs text-ink-muted">{t("plan.limits.cap.engine_ceiling", { ceiling: plan.cap.ceiling })}</dd>
                  )}
                </div>
                <div>
                  <dt className="flex items-center gap-1 text-ink-muted">
                    <span>{t("mailto.title")}</span>
                    <Hint locale={locale} label={t("mailto.title")} text={t("plan.limits.mailto.help")} textKey="plan.limits.mailto.help" />
                  </dt>
                  <dd className="text-ink">
                    {plan.mailto_set ? (
                      <DecisionBadge role="include">{t("plan.limits.mailto.set")}</DecisionBadge>
                    ) : (
                      <DecisionBadge role="unclear">{t("plan.limits.mailto.notSet")}</DecisionBadge>
                    )}
                  </dd>
                </div>
                {plan.openalex_key_set === undefined ? null : (
                  <div data-openalex-key-set={plan.openalex_key_set ? "true" : "false"}>
                    <dt className="flex items-center gap-1 text-ink-muted">
                      <span>{t("openalexKey.title")}</span>
                      <Hint locale={locale} label={t("openalexKey.title")} text={t("plan.limits.openalexKey.help")} textKey="plan.limits.openalexKey.help" />
                    </dt>
                    <dd className="text-ink">
                      {plan.openalex_key_set ? (
                        <DecisionBadge role="include">{t("plan.limits.mailto.set")}</DecisionBadge>
                      ) : (
                        <DecisionBadge role="unclear">{t("plan.limits.mailto.notSet")}</DecisionBadge>
                      )}
                    </dd>
                  </div>
                )}
                {plan.s2_key_set === undefined ? null : (
                  <div data-s2-key-set={plan.s2_key_set ? "true" : "false"}>
                    <dt className="flex items-center gap-1 text-ink-muted">
                      <span>{t("s2Key.title")}</span>
                      <Hint locale={locale} label={t("s2Key.title")} text={t("plan.limits.s2Key.help")} textKey="plan.limits.s2Key.help" />
                    </dt>
                    <dd className="text-ink">
                      {plan.s2_key_set ? (
                        <DecisionBadge role="unclear">{t("plan.limits.s2Key.set")}</DecisionBadge>
                      ) : (
                        t("plan.limits.mailto.notSet")
                      )}
                    </dd>
                  </div>
                )}
              </dl>
            </section>
            {/* M10b Part D: the size estimate, under Limits; not drawn once a run exists or the corpus is accepted. */}
            {!hasRun && !accepted && choice && choice.length && plan.providers.some((p) => p.selected) ? (
              <EstimateCard
                locale={locale}
                origin={origin}
                fingerprint={plan.protocol_fingerprint}
                // H-run-small-fixes (review N1): the estimate always counts the choice on screen;
                // an estimate sent no list counts the default choice, which may leave Crossref out.
                providers={choice && choice.length ? choice : null}
                harvestHref={(cap) => harvestHref(locale, origin, differs ? choice : null, cap)}
                inceptionHref={inceptionHref(locale, origin)}
                // M11a part D (question 7): narrowing the query is "Change the search", opened here.
                searchHref={planSearchHref(locale, origin)}
                onSearch={() => setSearchOpen(true)}
              />
            ) : null}
            {!plan.mailto_set ? <MailtoCard locale={locale} onCheck={() => void load(current(), true)} /> : null}
            {plan.openalex_key_set === false && plan.providers.some((p) => p.name === "openalex" && p.selected) ? (
              <OpenAlexKeyCard locale={locale} onCheck={() => void load(current(), true)} />
            ) : null}
            <section className="rounded-lg border border-rule bg-leaf p-5">
              <p className="flex items-center gap-1">
                <a className={LINK} href={inceptionHref(locale, origin)} data-amend>
                  {t("amend.link")}
                </a>
                {/* M11a part D: on Plan the query is changed by "Change the search" (its own hint); this link is for the rest. */}
              </p>
              <p className="mt-3">
                {/* 03-guidance (M10d): Plan's one main action; while "Change the search" is open its own action is, so this is a plain link (never two). */}
                <a className={searchOpen ? LINK : PRIMARY_LINK} href={discoveryHref(locale, "recall", origin)} data-variant={searchOpen ? undefined : "primary"} data-next>
                  {t("plan.next")}
                </a>
              </p>
              {choice && choice.length ? (
                <p>
                  <a className={LINK} href={harvestHref(locale, origin, differs ? choice : null)} data-next-harvest>
                    {t("plan.next.harvest")}
                  </a>
                </p>
              ) : null}
            </section>
          </aside>
        </div>
        </div>
      )}
    </DiscoveryFrame>
  );
}
