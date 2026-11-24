import { notFound } from "next/navigation";

import { SettingsScreen } from "@/components/settings-screen";
import { isSupportedLocale } from "@/i18n";

/**
 * Settings and first-run setup (M13 Part B; spec `shared/final/05-settings.md`,
 * `/settings`, first run `/settings/?setup=1`). It only resolves the locale; the
 * screen reads the engine through the same-origin console path.
 */
export default async function SettingsRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <SettingsScreen locale={raw} />;
}
