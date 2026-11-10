import { notFound } from "next/navigation";

import { DiscoveryHarvest } from "@/components/discovery-harvest";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 03 Harvest (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryHarvestRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryHarvest locale={raw} />;
}
