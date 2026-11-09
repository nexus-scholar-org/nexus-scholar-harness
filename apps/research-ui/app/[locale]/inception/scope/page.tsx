import { notFound } from "next/navigation";

import { InceptionScope } from "@/components/inception-scope";
import { isSupportedLocale } from "@/i18n";

/** Inception step 1, Scope (spec 01). The screen reads the engine through the same-origin console path. */
export default async function InceptionScopeRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionScope locale={raw} />;
}
