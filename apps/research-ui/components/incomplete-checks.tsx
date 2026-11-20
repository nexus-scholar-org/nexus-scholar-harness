import type { Locale } from "@/i18n";
import type { PreparationChecks } from "@/lib/discovery-api";
import { discoveryT } from "@/lib/discovery-copy";
import { localStamp } from "@/lib/local-time";

/**
 * H-quota-hang: the checks after a harvest ended before every record was checked. Says why (a
 * database's quota is used up, with its reset time in the researcher's clock, or the researcher's
 * stop), how many records were not checked, and what to do. Every value is the engine's
 * (`preparation.checks`); the browser counts nothing. Shared by the Harvest card and the Hand-off.
 */
export function IncompleteChecks({
  locale,
  checks,
  canFinish,
}: Readonly<{ locale: Locale; checks: PreparationChecks; canFinish: boolean }>) {
  const t = discoveryT(locale);
  const stopped = checks.reason === "STOPPED_BY_RESEARCHER";
  return (
    <div className="mt-2 space-y-1 text-sm text-ink" data-incomplete-checks data-incomplete-reason={checks.reason ?? ""}>
      {stopped ? <p data-incomplete-stopped>{t("harvest.prep.incomplete.stopped")}</p> : null}
      {checks.paused.map((paused) => (
        <p key={paused.provider} data-paused={paused.provider} data-resets-at={paused.resets_at}>
          {t(paused.reason === "PROVIDER_QUOTA_EXHAUSTED" ? "harvest.prep.incomplete.quota" : "harvest.prep.incomplete.paused", {
            database: paused.database,
            time: localStamp(paused.resets_at),
          })}
        </p>
      ))}
      <p data-unchecked={checks.unchecked}>{t("harvest.prep.incomplete.count", { unchecked: checks.unchecked, records: checks.records })}</p>
      {canFinish ? (
        <p data-incomplete-todo>{t(checks.paused.length ? "harvest.prep.incomplete.afterReset" : "harvest.prep.incomplete.now")}</p>
      ) : null}
    </div>
  );
}
