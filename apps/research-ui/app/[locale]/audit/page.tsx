import { notFound } from "next/navigation";

import { AuditPage } from "@/components/audit-page";
import { isSupportedLocale } from "@/i18n";

/**
 * The audit activity route (packet UI-06).
 *
 * Like the screening and corpus routes, this file has one job: decide whether
 * the URL segment is a locale this application ships, then render in that
 * locale or hand the whole URL to `notFound()`. The refusal lands in
 * `app/[locale]/not-found.tsx`, which answers in English rather than with the
 * framework default, so `/de/audit` is refused the same way `/de` is.
 *
 * No `main` (the shell owns it), no fixture logic, no read, no ordering, and
 * no timestamp handling: those live in `components/audit-page.tsx` so the
 * in-process suite can render the screen in any locale without a router.
 */
export default async function AuditRoute({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;

  if (!isSupportedLocale(raw)) {
    notFound();
  }

  return <AuditPage locale={raw} />;
}
