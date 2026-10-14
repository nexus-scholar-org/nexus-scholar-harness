import { notFound } from "next/navigation";

import { LineagePage } from "@/components/lineage-trace";
import { isSupportedLocale } from "@/i18n";

/**
 * The evidence lineage route (packet UI-05).
 *
 * The route is a deliberate copy of the screening route's single job:
 * decide whether the URL segment is a locale this application ships, then
 * render in that locale or hand the whole URL to `notFound()`. The refusal
 * lands in `app/[locale]/not-found.tsx`, which answers with a catalog-backed
 * sentence in English rather than the framework's default page.
 *
 * What this file does not do is as load-bearing as what it does: no `main`
 * (the shell owns it), no fixture logic, no trace assembly, no API call.
 * The trace composition lives in `components/lineage-trace.tsx` so the
 * in-process suite can render it in any locale without a router.
 */
export default async function LineageRoute({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;

  if (!isSupportedLocale(raw)) {
    notFound();
  }

  return <LineagePage locale={raw} />;
}
