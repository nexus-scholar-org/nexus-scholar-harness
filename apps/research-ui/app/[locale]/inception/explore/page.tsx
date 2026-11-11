import { notFound } from "next/navigation";

import { InceptionExplore } from "@/components/inception-explore";
import { isSupportedLocale } from "@/i18n";

/** Inception step 2, Explore (spec 02), M4d. The screen reads the engine through the same-origin console path. */
export default async function InceptionExploreRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionExplore locale={raw} />;
}
