import type { Metadata } from "next";
import type { ReactNode } from "react";

import { LocaleDocument } from "@/components/locale-document";
import { SUPPORTED_LOCALES, resolveLocale, translate } from "@/i18n";

import "../globals.css";

/**
 * The locale layout (packet UI-01d, D-I18N-01a).
 *
 * `app/layout.tsx` is gone: the document's `<html>`/`<body>` pair now comes from
 * `app/[locale]/layout.tsx`, because the route that renders the overview is
 * `app/[locale]/page.tsx` and a root layout has to sit above the deepest segment
 * that needs it. Next permits exactly one such layout, which is why the previous
 * root layout was deleted rather than kept alongside this one.
 *
 * `dynamicParams = true` on purpose. The three shipped locales are prerendered
 * by `generateStaticParams`, so `/en`, `/fr` and `/ar` are served as prerendered
 * documents; every other
 * segment is still rendered on demand, and that is what lets an unsupported one
 * reach `notFound()` and produce the catalog-backed 404 (D-I18N-13) instead of
 * a framework 404 page with no chrome and no translated explanation.
 *
 * `resolveLocale` — not `notFound()` — is what decides the document language
 * here. An unsupported segment still has to render *some* document, and that
 * document's `lang`/`dir` must be real values, so the layout falls back to
 * English and left-to-right (D-I18N-13). The route below is what refuses.
 *
 * ## Open: the refused segment cannot be named from the boundary
 *
 * The layout renders exactly `children` and nothing else. That is the packet's
 * design, and it is also the only structure left standing once the measured
 * framework constraints below are taken seriously — but it means the refusal
 * cannot name what the reader typed, and the decision on how to fix that is
 * escalated to the packet owner rather than settled here. Measured on Next
 * 16.3.6 with temporary probes, not inferred:
 *
 * - `app/[locale]/not-found.tsx` receives **no props at all** — not an empty
 *   `params`, an absent one — so the boundary cannot read `locale`;
 * - a request for `/de` arrives carrying only `host`, `user-agent`, `accept`,
 *   `x-forwarded-host`, `x-forwarded-port`, `x-forwarded-proto` and
 *   `x-forwarded-for`. No header carries the path, so `headers()` cannot
 *   substitute;
 * - any `notFound()` response is served as Next's own error document
 *   (`<html id="__next_error__">`), which drops this layout's `lang`/`dir` and
 *   leaves the body empty until hydration;
 * - rendering the refusal from here *instead of* `children` keeps `lang`/`dir`,
 *   the pre-hydration text and the segment name, but the page that calls
 *   `notFound()` is then never rendered, so the status silently becomes 200;
 * - rendering it *alongside* `children` keeps the 404 but yields a served
 *   document whose only text is the brand.
 *
 * Separately, `/EN` and `/Fr` are answered with 200 and the English/French
 * overview: Next serves the prerendered `en.html`/`fr.html` case-insensitively
 * on Windows, ahead of the locale check. That belongs to the same amendment.
 */
export const dynamicParams = true;

export function generateStaticParams() {
  return SUPPORTED_LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale = resolveLocale(raw);

  return {
    title: translate(locale, "brand.productName"),
    description: translate(locale, "app.meta.description"),
  };
}

export default async function LocaleLayout({
  children,
  params,
}: Readonly<{ children: ReactNode; params: Promise<{ locale: string }> }>) {
  const { locale: raw } = await params;

  return <LocaleDocument locale={resolveLocale(raw)}>{children}</LocaleDocument>;
}