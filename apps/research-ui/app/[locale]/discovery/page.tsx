import { notFound } from "next/navigation";

import { DiscoveryOverview } from "@/components/discovery-overview";
import { isSupportedLocale } from "@/i18n";

/** Discovery, The entry, where the search stands (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryOverviewRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryOverview locale={raw} />;
}
