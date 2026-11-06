import { notFound } from "next/navigation";

import { ScreeningImport } from "@/components/screening-import";
import { isSupportedLocale } from "@/i18n";

/** Import the corpus (spec 11): one RIS file per database, counted, then accepted and frozen. */
export default async function ScreeningImportRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningImport locale={raw} />;
}
