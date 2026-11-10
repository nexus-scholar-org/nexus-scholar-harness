import { notFound } from "next/navigation";

import { DiscoveryHandoff } from "@/components/discovery-handoff";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 08 Hand-off (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryHandoffRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryHandoff locale={raw} />;
}
