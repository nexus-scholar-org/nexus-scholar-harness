import { notFound } from "next/navigation";

import { DiscoveryRecall } from "@/components/discovery-recall";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 02 Recall check (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryRecallRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryRecall locale={raw} />;
}
