import { notFound } from "next/navigation";

import { ScreeningPilot } from "@/components/screening-pilot";
import { isSupportedLocale } from "@/i18n";

/** The criteria pilot's result (spec 13, state C): counts only, from your own pilot decisions. */
export default async function ScreeningPilotRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningPilot locale={raw} />;
}
