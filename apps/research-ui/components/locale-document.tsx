import type { ReactNode } from "react";

import { LOCALE_METADATA, translate, type Locale } from "@/i18n";

import { AppShell } from "./app-shell";

/**
 * The document owner (packet UI-01d, D-I18N-01a).
 *
 * `app/layout.tsx` is deleted by this packet: the route is now
 * `app/[locale]/*`, and Next needs the `<html>`/`<body>` pair to come from a
 * layout at that segment. Keeping the pair in a *component* rather than inlining
 * it in the layout is what makes the two halves of the feature testable apart:
 *
 * - the layout is the only async part — it awaits `params`, resolves the locale,
 *   and owns `generateStaticParams`/`generateMetadata`;
 * - this component is synchronous and pure, so the in-process suite can render
 *   it in `en`, `fr` and `ar` and assert the document attributes directly.
 *
 * `lang` and `dir` come from `LOCALE_METADATA` and are the **only** place the
 * writing direction is declared (D-I18N-13, §8). No component below this one
 * sets `dir`: a component must work under whatever direction its document
 * declares, and a second declaration somewhere in the tree is a second thing that
 * can disagree with the first. Everything visual is therefore expressed with
 * logical properties and logical utilities, which resolve against this one
 * attribute.
 *
 * The global stylesheet is imported by the layout that renders this component,
 * not here. Keeping the CSS out of the component is deliberate: a component that
 * imports a stylesheet cannot be mounted by vitest without a CSS pipeline, and
 * the stylesheet is a property of the route tree, not of the markup.
 */
export function LocaleDocument({
  locale,
  children,
}: Readonly<{ locale: Locale; children: ReactNode }>) {
  const metadata = LOCALE_METADATA[locale];

  return (
    <html lang={metadata.lang} dir={metadata.dir}>
      <body>
        <AppShell locale={locale}>{children}</AppShell>
      </body>
    </html>
  );
}