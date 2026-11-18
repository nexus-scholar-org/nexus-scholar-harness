import { notFound } from "next/navigation";

import { InceptionImport } from "@/components/inception-import";
import { isSupportedLocale } from "@/i18n";

/** Start from an existing review (spec 09, M10b). The screen reads the engine through the same-origin console path. */
export default async function InceptionImportRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionImport locale={raw} />;
}
