import type { Locale } from "@/i18n";
import type { PreparationChecks } from "@/lib/discovery-api";
import { discoveryT } from "@/lib/discovery-copy";
import { Stamp } from "@/components/stamp";

const TIME = "{time}";

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
      {checks.paused.map((paused) => {
        // The time is a `Stamp` (`<time dir="ltr">`) inside the sentence, so it keeps its order in Arabic.
        const [before, after = ""] = t(
          paused.reason === "PROVIDER_QUOTA_EXHAUSTED" ? "harvest.prep.incomplete.quota" : "harvest.prep.incomplete.paused",
          { database: paused.database, time: TIME },
        ).split(TIME);
        return (
          <p key={paused.provider} data-paused={paused.provider} data-resets-at={paused.resets_at}>
            {before}
            <Stamp at={paused.resets_at} />
            {after}
          </p>
        );
      })}
      <p data-unchecked={checks.unchecked}>{t("harvest.prep.incomplete.count", { unchecked: checks.unchecked, records: checks.records })}</p>
      {checks.unverified ? <p data-unverified={checks.unverified}>{t("harvest.prep.incomplete.unverified", { n: checks.unverified })}</p> : null}
      {checks.unenriched ? <p data-unenriched={checks.unenriched}>{t("harvest.prep.incomplete.unenriched", { n: checks.unenriched })}</p> : null}
      {canFinish ? (
        <p data-incomplete-todo>{t(checks.paused.length ? "harvest.prep.incomplete.afterReset" : "harvest.prep.incomplete.now")}</p>
      ) : null}
    </div>
  );
}
