import { notFound } from "next/navigation";

import { RouteRedirect } from "@/components/route-redirect";
import { isSupportedLocale, translate } from "@/i18n";

/**
 * The locale root (D-I18N-01). An unsupported segment is refused by
 * `not-found.tsx`; a supported one forwards to the workspaces screen, which
 * is where the app starts.
 */
export default async function LocalePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <RouteRedirect locale={raw} to="/workspaces" label={translate(raw, "nav.workspaces")} />;
}
