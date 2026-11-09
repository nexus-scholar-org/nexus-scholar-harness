import { notFound } from "next/navigation";

import { InceptionDone } from "@/components/inception-done";
import { isSupportedLocale } from "@/i18n";

/** Inception done (spec 07): what was written, then open the workspace. The screen reads the engine through the same-origin console path. */
export default async function InceptionDoneRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionDone locale={raw} />;
}
