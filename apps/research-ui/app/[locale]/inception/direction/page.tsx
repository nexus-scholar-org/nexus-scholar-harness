import { notFound } from "next/navigation";

import { InceptionDirection } from "@/components/inception-direction";
import { isSupportedLocale } from "@/i18n";

/** Inception step 3, Direction (spec 03), M4d. The screen reads the engine through the same-origin console path. */
export default async function InceptionDirectionRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionDirection locale={raw} />;
}
