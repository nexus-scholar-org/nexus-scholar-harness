import { notFound } from "next/navigation";

import { DiscoveryChase } from "@/components/discovery-chase";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 09 Citation chase (docs/ux/phase1-discovery/final/09-chase.md, M3g-citation-chasing). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryChaseRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryChase locale={raw} />;
}
