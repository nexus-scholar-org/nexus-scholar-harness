import { notFound } from "next/navigation";

import { InceptionStart } from "@/components/inception-start";
import { isSupportedLocale } from "@/i18n";

/** Inception start and resume (spec 08): the drafts under the workspaces root and a new review. The screen reads the engine through the same-origin console path. */
export default async function InceptionStartRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <InceptionStart locale={raw} />;
}
