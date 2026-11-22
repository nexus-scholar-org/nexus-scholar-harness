import { notFound } from "next/navigation";

import { ChartingStudyPage } from "@/components/charting-study";
import { isSupportedLocale } from "@/i18n";

/**
 * The one-study view (M12a Part B, spec 02, `/charting/study?id=STU-...`). The
 * study is a query parameter, not a path segment: the packaged app is exported
 * as prebuilt pages and cannot hold one page per study id. Like the other routes
 * it only resolves the locale; the screen reads the console through the
 * same-origin proxy.
 */
export default async function ChartingStudyRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ChartingStudyPage locale={raw} />;
}
