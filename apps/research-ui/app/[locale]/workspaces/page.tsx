import { notFound } from "next/navigation";

import { WorkspacesScreen } from "@/components/workspaces-screen";
import { isSupportedLocale } from "@/i18n";

/**
 * The minimal workspace screen (spec `phase2-screening/final/00-workspaces.md`,
 * `/workspaces`). Like the screening routes it only resolves the locale; the
 * screen reads the engine through the same-origin console path.
 */
export default async function WorkspacesRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <WorkspacesScreen locale={raw} />;
}
