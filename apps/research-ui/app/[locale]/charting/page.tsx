import { notFound } from "next/navigation";

import { ChartingPage } from "@/components/charting-page";
import { isSupportedLocale } from "@/i18n";

/**
 * The charting screen (M12a, spec 01, `/charting`), Full text view. Like the other
 * routes it only resolves the locale; the screen reads the console through the
 * same-origin proxy.
 */
export default async function ChartingRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ChartingPage locale={raw} />;
}
