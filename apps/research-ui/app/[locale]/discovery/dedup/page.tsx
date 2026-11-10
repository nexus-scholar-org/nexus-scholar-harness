import { notFound } from "next/navigation";

import { DiscoveryDedup } from "@/components/discovery-dedup";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 05 Duplicates (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryDedupRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryDedup locale={raw} />;
}
