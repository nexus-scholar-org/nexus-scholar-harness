import { notFound } from "next/navigation";

import { ScreeningAdopted } from "@/components/screening-adopted";
import { isSupportedLocale } from "@/i18n";

/** H-adopted-decisions-disclosure: declare decisions stored from the agent's drafts without being read one by one. */
export default async function ScreeningAdoptedRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningAdopted locale={raw} />;
}
