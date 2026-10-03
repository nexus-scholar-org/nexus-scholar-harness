import { notFound } from "next/navigation";

import { OverviewPage } from "@/components/overview-page";
import { isSupportedLocale } from "@/i18n";

/**
 * The locale overview route (packet UI-01d, D-I18N-01).
 *
 * The route does one thing: decide whether the URL segment is a locale this
 * application ships. If it is, the overview is rendered in that locale; if it is
 * not, `notFound()` hands over to `app/[locale]/not-found.tsx`, which renders
 * the catalog-backed refusal in English.
 *
 * The check is exact and case-sensitive (D-I18N-01): `/EN`, `/en-US` and `/fr-FR`
 * are refused rather than folded into a supported locale. A URL segment is a
 * machine identifier, and silently accepting a spelling the application never
 * declared would mean two different URLs rendering one document with nothing
 * recording which one the reader actually used.
 *
 * `dynamicParams` on the layout above is what makes this reachable for a segment
 * that was not prerendered; with it off, Next would answer an unlisted segment
 * with its own 404 and the refusal sentence would never be read.
 */
export default async function LocalePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;

  if (!isSupportedLocale(raw)) {
    notFound();
  }

  return <OverviewPage locale={raw} />;
}