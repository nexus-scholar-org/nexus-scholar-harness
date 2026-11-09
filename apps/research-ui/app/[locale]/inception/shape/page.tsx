import { notFound } from "next/navigation";

import { InceptionShape } from "@/components/inception-shape";
import { isSupportedLocale } from "@/i18n";

/** Inception step 4, Shape (spec 04). The screen reads the engine through the same-origin console path. */
export default async function InceptionShapeRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionShape locale={raw} />;
}
