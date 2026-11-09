import { notFound } from "next/navigation";

import { InceptionCriteria } from "@/components/inception-criteria";
import { isSupportedLocale } from "@/i18n";

/** Inception step 5, Concepts and criteria (spec 05; INC-22). The screen reads the engine through the same-origin console path. */
export default async function InceptionCriteriaRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionCriteria locale={raw} />;
}
