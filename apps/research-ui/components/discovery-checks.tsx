"use client";

import { useCallback, useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { fillNodes } from "@/components/assist-anchor";
import { notifyDiscoveryChecks, useDiscoveryChecksVersion } from "@/components/checks-bus";
import { ChecksPanel, type CheckLink } from "@/components/checks-panel";
import { discoveryHref, LINK, type DiscoveryStep } from "@/components/discovery-frame";
import { checksCountTemplate } from "@/lib/checks-copy";
import { dismissDiscoveryCheck, getDiscoveryChecks, restoreDiscoveryCheck } from "@/lib/discovery-api";
import type { Check, CheckList } from "@/lib/inception-api";

/**
 * The checks panel on the discovery screens (02-checks, M10b B3): a pure read of
 * `GET /discovery/checks?step=` for the open workspace, dismissal and restore
 * through the discovery routes. It adds a reading of the facts the screen
 * prints and never disables a button the screen did not already disable.
 */

const DISCOVERY_STEPS = ["plan", "recall", "harvest", "dedup", "report", "handoff"] as const;
type CheckStep = (typeof DISCOVERY_STEPS)[number];

function link(locale: Locale, origin: string) {
  return (check: Check): CheckLink | null => {
    const step = check.action.step;
    if (!step) return null;
    if (step === "inception") return { href: `/${locale}/inception/${origin ? `?console=${encodeURIComponent(origin)}` : ""}` };
    if ((DISCOVERY_STEPS as readonly string[]).includes(step)) return { href: discoveryHref(locale, step as DiscoveryStep, origin) };
    return null;
  };
}

export function DiscoveryChecksPanel({ locale, step, origin, run = "" }: Readonly<{ locale: Locale; step: CheckStep; origin: string; run?: string }>) {
  const version = useDiscoveryChecksVersion();
  const load = useCallback(() => getDiscoveryChecks(origin, step, run || undefined), [origin, step, run]);
  return (
    <ChecksPanel
      locale={locale}
      mode="panel"
      name={step}
      load={load}
      reloadKey={`${version}|${origin}|${step}|${run}`}
      dismiss={(check, reason) => dismissDiscoveryCheck(origin, check.check_id, { subject: check.subject, evidence_digest: check.evidence_digest, ...(reason ? { reason } : {}) })}
      restore={(check) => restoreDiscoveryCheck(origin, check.check_id, check.subject)}
      link={link(locale, origin)}
      onDecided={notifyDiscoveryChecks}
    />
  );
}

/** The hand-off's one line about earlier steps: the engine's open counts of Plan to Report, linking to the first. */
export function EarlierChecksLine({ locale, origin }: Readonly<{ locale: Locale; origin: string }>) {
  const version = useDiscoveryChecksVersion();
  const [all, setAll] = useState<CheckList | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    getDiscoveryChecks(origin, undefined, undefined, controller.signal).then(setAll, () => setAll(null));
    return () => controller.abort();
  }, [origin, version]);
  const byStep = all?.by_step;
  if (!byStep) return null;
  const earlier = DISCOVERY_STEPS.filter((s) => s !== "handoff").map((s) => ({ step: s, n: (byStep[s]?.blocker ?? 0) + (byStep[s]?.warning ?? 0) }));
  const total = earlier.reduce((sum, e) => sum + e.n, 0);
  const first = earlier.find((e) => e.n > 0);
  if (!total || !first) return null;
  return (
    <p className="mt-1 text-sm" data-earlier-checks>
      <a className={LINK} href={discoveryHref(locale, first.step, origin)}>
        {fillNodes(checksCountTemplate(locale, "checks.earlier", total), { n: <bdi dir="ltr">{formatNumber(locale, total)}</bdi> })}
      </a>
    </p>
  );
}
