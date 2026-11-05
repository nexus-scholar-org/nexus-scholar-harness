import { notFound } from "next/navigation";

import { TriagePage } from "@/components/triage-page";
import { isSupportedLocale } from "@/i18n";

/**
 * Desktop triage (spec 03, `/screening/triage`). Like the other routes it only
 * resolves the locale; the screen lives in `components/triage-page.tsx`, which
 * reads the console through the same-origin proxy.
 */
export default async function TriageRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <TriagePage locale={raw} />;
}
