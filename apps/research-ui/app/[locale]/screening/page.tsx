import { notFound } from "next/navigation";

import { RouteRedirect } from "@/components/route-redirect";
import { isSupportedLocale, translate } from "@/i18n";

/**
 * `/screening` held the single-record demonstration page until 2026-11-05.
 * The address now forwards to the screening home, so older links and
 * bookmarks still land on the live screens.
 */
export default async function ScreeningRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <RouteRedirect locale={raw} to="/screening/home" label={translate(raw, "nav.screening")} />;
}
