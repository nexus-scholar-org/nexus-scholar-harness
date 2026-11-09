import { notFound } from "next/navigation";

import { InceptionReview } from "@/components/inception-review";
import { isSupportedLocale } from "@/i18n";

/** Inception step 6, Review and create (spec 06): the only write gate. The screen reads the engine through the same-origin console path. */
export default async function InceptionReviewRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionReview locale={raw} />;
}
