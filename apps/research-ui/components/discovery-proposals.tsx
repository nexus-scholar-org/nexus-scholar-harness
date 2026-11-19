"use client";

import { useCallback, useEffect, useId, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button } from "@/components/ui/base";
import { fillNodes } from "@/components/assist-anchor";
import { refusalOf } from "@/components/discovery-frame";
import { SourceLabel, valueText } from "@/components/inception-assist";
import { fieldLabel } from "@/lib/assist-labels";
import {
  applyWorkspaceProposal,
  getWorkspaceProposals,
  rejectWorkspaceProposal,
  type WorkspaceProposal,
  type WorkspaceProposals,
} from "@/lib/discovery-api";
import { PROPOSALS_COPY, proposalsT } from "@/lib/proposals-copy";

/**
 * Discovery Plan's cards for an assistant's suggested change to the protocol's
 * search (M10c D5; decision 2026-11-19, item 9 option (a)). The engine decides
 * everything: which suggestions are open or out of date, whether Apply is
 * allowed (a running search, an accepted corpus) and what an Apply changed.
 * Nothing is applied without the researcher's click; there is no Edit and no
 * "Apply all". Renders nothing while the workspace has no suggestion.
 */
export function DiscoveryProposals({
  locale,
  origin,
  onAmended,
}: Readonly<{ locale: Locale; origin: string; onAmended?: () => void }>) {
  const t = proposalsT(locale);
  const copy = PROPOSALS_COPY[locale];
  const headingId = `plan-proposals-${useId().replace(/:/g, "")}`;
  const [listing, setListing] = useState<WorkspaceProposals | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<{ id: string; text: string } | null>(null);
  const [announce, setAnnounce] = useState("");

  const read = useCallback(async () => {
    try {
      setListing(await getWorkspaceProposals(origin));
    } catch {
      setListing(null); // an older console, or the engine is away: the cards are simply not shown
    }
  }, [origin]);

  useEffect(() => {
    void read();
  }, [read]);

  if (!listing) return null;
  const live = listing.proposals.filter((p) => p.status === "open" || p.status === "stale");
  if (live.length === 0) return null;
  const blocked = listing.frozen || Boolean(listing.active_job);
  const n = (value: number) => <bdi dir="ltr">{formatNumber(locale, value)}</bdi>;

  const act = async (proposal: WorkspaceProposal, action: "apply" | "reject") => {
    const field = fieldLabel(locale, proposal.target.field);
    setBusy(true);
    setNote(null);
    try {
      const answer = action === "apply" ? await applyWorkspaceProposal(origin, proposal.proposal_id) : await rejectWorkspaceProposal(origin, proposal.proposal_id);
      setListing(answer);
      setAnnounce(action === "apply" ? t("proposals.act.announceApplied", { field }) : t("proposals.act.announceRejected", { field }));
      if (action === "apply") onAmended?.();
    } catch (error) {
      const refusal = refusalOf(error);
      const details = (refusal.details ?? {}) as { reason?: string; errors?: unknown[] };
      if (refusal.code === "PROTOCOL_AMENDMENT_REFUSED") {
        setNote({
          id: proposal.proposal_id,
          text: details.reason === "outside_search" ? t("proposals.plan.outsideSearch") : t("proposals.plan.invalid", { error: String(details.errors?.[0] ?? refusal.message) }),
        });
      } else if (refusal.code === "PROPOSAL_STALE") {
        setAnnounce(t("proposals.act.announceStale", { field }));
      } else if (refusal.code !== "CORPUS_ALREADY_ACCEPTED" && refusal.code !== "DISCOVERY_JOB_ACTIVE" && refusal.code !== "PROPOSAL_NOT_OPEN") {
        setNote({ id: proposal.proposal_id, text: t("proposals.err.other") });
      }
      await read();
    } finally {
      setBusy(false);
    }
  };

  const card = (proposal: WorkspaceProposal) => {
    const id = proposal.proposal_id;
    const stale = proposal.status === "stale";
    const whatId = `plan-proposal-what-${id}`;
    const value = <bdi dir="auto" className="font-mono text-[0.8125rem]" data-value>{valueText(proposal.value)}</bdi>;
    const field = <span data-field>{fieldLabel(locale, proposal.target.field)}</span>;
    const template = proposal.op === "add" ? copy["proposals.what.add"] : proposal.op === "remove" ? copy["proposals.what.remove"] : copy["proposals.what.replace"];
    return (
      <li key={id} className={`rounded-md border border-dashed border-ink-muted bg-paper p-3 ${stale ? "opacity-80" : ""}`} data-plan-proposal={id} data-status={proposal.status}>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <SourceLabel locale={locale} source={proposal.source} />
          <span className="text-ink-muted">{t("proposals.draftLabel")}</span>
          {stale ? <span className="rounded-sm border border-rule px-1 text-ink" data-stale-badge>{t("proposals.status.stale")}</span> : null}
        </div>
        <p id={whatId} className="mt-1 text-ink" data-what>
          {fillNodes(template, { value, field, now: <bdi dir="auto" className="font-mono text-[0.8125rem]">{proposal.current ?? proposal.base.shown}</bdi> })}
        </p>
        {proposal.why ? (
          <p className="mt-1 text-sm text-ink-muted">
            <span className="font-medium">{t("proposals.why")}: </span>
            <bdi dir="auto">{proposal.why}</bdi>
          </p>
        ) : null}
        {stale ? <p className="mt-1 text-sm text-ink" data-stale-line>{t("proposals.stale.protocol")}</p> : null}
        {note?.id === id ? (
          <p role="alert" className="mt-1 text-sm text-ink" data-plan-proposal-note>
            {note.text}
          </p>
        ) : null}
        <div className="mt-2 flex flex-wrap gap-2">
          {stale ? null : (
            <Button type="button" variant="primary" onClick={() => void act(proposal, "apply")} disabled={busy || blocked} aria-describedby={whatId} data-apply>
              {t("proposals.act.apply")}
            </Button>
          )}
          <Button type="button" variant="quiet" onClick={() => void act(proposal, "reject")} disabled={busy} aria-describedby={whatId} data-reject>
            {stale ? t("proposals.act.dismiss") : t("proposals.act.reject")}
          </Button>
        </div>
      </li>
    );
  };

  return (
    <section aria-labelledby={headingId} className="rounded-lg border border-rule bg-leaf p-5" data-plan-proposals>
      <h2 id={headingId} className="font-semibold text-ink">
        {fillNodes(copy["proposals.plan.title"], { n: n(listing.counts.open) })}
      </h2>
      {listing.counts.stale ? <p className="text-sm text-ink-muted">{fillNodes(copy["proposals.outOfDate"], { n: n(listing.counts.stale) })}</p> : null}
      <p className="mt-1 text-sm text-ink-muted">{t("proposals.plan.intro")}</p>
      {listing.frozen ? (
        <p className="mt-1 text-sm text-ink" data-plan-proposals-frozen>
          {t("proposals.plan.frozen")}
        </p>
      ) : listing.active_job ? (
        <p className="mt-1 text-sm text-ink" data-plan-proposals-running>
          {t("proposals.plan.running")}
        </p>
      ) : null}
      <ul className="mt-3 space-y-3">{live.map(card)}</ul>
      <p className="sr-only" role="status" aria-live="polite">
        {announce}
      </p>
    </section>
  );
}
