import { notFound } from "next/navigation";

import { DiscoveryPlan } from "@/components/discovery-plan";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 01 Plan (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryPlanRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryPlan locale={raw} />;
}
