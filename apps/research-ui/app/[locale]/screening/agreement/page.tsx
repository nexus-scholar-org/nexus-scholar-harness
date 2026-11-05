import { notFound } from "next/navigation";

import { ScreeningAgreement } from "@/components/screening-agreement";
import { isSupportedLocale } from "@/i18n";

/** Agreement with the agent (spec 07): descriptive only, decisions made before the reveal. */
export default async function ScreeningAgreementRoute({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <ScreeningAgreement locale={raw} />;
}
