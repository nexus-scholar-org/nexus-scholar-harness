import { notFound } from "next/navigation";

import { ScreeningExport } from "@/components/screening-export";
import { isSupportedLocale } from "@/i18n";

/** Export and methods (spec 10): the published decisions as RIS or CSV, and the methods paragraph. */
export default async function ScreeningExportRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningExport locale={raw} />;
}
