import { notFound } from "next/navigation";

import { DiscoveryReport } from "@/components/discovery-report";
import { isSupportedLocale } from "@/i18n";

/** Discovery, 06 Search report (docs/ux/phase1-discovery/final, M3c-screens). The screen reads the engine through the same-origin console path. */
export default async function DiscoveryReportRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <DiscoveryReport locale={raw} />;
}
