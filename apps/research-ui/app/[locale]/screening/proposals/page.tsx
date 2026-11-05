import { notFound } from "next/navigation";

import { ScreeningProposals } from "@/components/screening-proposals";
import { isSupportedLocale } from "@/i18n";

/** Agent proposals run (spec 06): provider, data flow, cost, consent, run and progress. */
export default async function ScreeningProposalsRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningProposals locale={raw} />;
}
