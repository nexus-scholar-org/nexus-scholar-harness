import { notFound } from "next/navigation";

import { ScreeningPage } from "@/components/screening-page";
import { isSupportedLocale } from "@/i18n";

/**
 * The screening workspace route (packet UI-04).
 *
 * The route is a deliberate copy of the overview route's single job: decide
 * whether the URL segment is a locale this application ships, then render in
 * that locale or hand the whole URL to `notFound()`. The refusal lands in
 * `app/[locale]/not-found.tsx`, which answers with a catalog-backed sentence in
 * English rather than the framework's default page — so `/de/screening` is
 * refused the same way `/de` is, for the same reason (D-I18N-01), instead of a
 * German path segment silently producing an English screen.
 *
 * Prerendered for the three supported locales like the overview (the layout's
 * `generateStaticParams`), reachable for anything else through `dynamicParams`,
 * and exact and case-sensitive: `/EN/screening` and `/de/screening` are 404s,
 * never a folded locale.
 *
 * What this file does not do is as load-bearing as what it does: no `main`
 * (the shell owns it), no fixture logic, no decision handling, no API call.
 * The screen's composition lives in `components/screening-page.tsx` so the
 * in-process suite can render it in any locale without a router.
 */
export default async function ScreeningRoute({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;

  if (!isSupportedLocale(raw)) {
    notFound();
  }

  return <ScreeningPage locale={raw} />;
}
