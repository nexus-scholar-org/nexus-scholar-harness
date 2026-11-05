import { notFound } from "next/navigation";

import { ScreeningHome } from "@/components/screening-home";
import { isSupportedLocale } from "@/i18n";

/** Screening home (spec 01). Sits beside the legacy `/screening` page until M5-slim. */
export default async function ScreeningHomeRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningHome locale={raw} />;
}
