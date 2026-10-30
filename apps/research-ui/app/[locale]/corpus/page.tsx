import { notFound } from "next/navigation";

import { CorpusPage } from "@/components/corpus-page";
import { isSupportedLocale } from "@/i18n";

/**
 * The screening corpus route (packet UI-08).
 *
 * Same single job as the overview and screening routes: decide whether the URL
 * segment is a locale this application ships, then render in that locale or
 * hand the whole URL to `notFound()`. The refusal lands in
 * `app/[locale]/not-found.tsx`, so an unsupported segment is refused in
 * English rather than silently rendering the screen under a segment the
 * application never declared (D-I18N-01).
 *
 * The screen's composition lives in `components/corpus-page.tsx` so the
 * in-process suite can render it in any locale without a router.
 */
export default async function CorpusRoute({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;

  if (!isSupportedLocale(raw)) {
    notFound();
  }

  return <CorpusPage locale={raw} />;
}
