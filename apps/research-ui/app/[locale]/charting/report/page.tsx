import { notFound } from "next/navigation";

import { ChartingReport } from "@/components/charting-report";
import { isSupportedLocale } from "@/i18n";

/**
 * Export and methods for the charting table (M12a Part C, spec 04,
 * `/charting/report`): the downloads, the PRISMA full-text counts and the
 * methods paragraph. Like the other routes it only resolves the locale; the
 * screen reads the console through the same-origin proxy.
 */
export default async function ChartingReportRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ChartingReport locale={raw} />;
}
