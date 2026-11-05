import { notFound } from "next/navigation";

import { ScreeningPublish } from "@/components/screening-publish";
import { isSupportedLocale } from "@/i18n";

/** Publish (spec 09): PRISMA preview, per-batch approval with the terminal code, publish. */
export default async function ScreeningPublishRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningPublish locale={raw} />;
}
