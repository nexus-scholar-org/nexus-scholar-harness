import { notFound } from "next/navigation";

import { ScreeningPrepare } from "@/components/screening-prepare";
import { isSupportedLocale } from "@/i18n";

/** Prepare (spec 02): settings, the read-only rule table, batches and prepare. */
export default async function ScreeningPrepareRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningPrepare locale={raw} />;
}
