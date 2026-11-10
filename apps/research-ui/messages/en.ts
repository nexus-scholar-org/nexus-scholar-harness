/**
 * The English catalog — structural source of truth (D-I18N-03).
 *
 * This file defines the 23 keys that `fr.ts` and `ar.ts` must mirror exactly
 * (compile-time via `Record<MessageKey, string>` and runtime via
 * `tests/i18n-catalog.test.ts`). A key added, removed, or misspelled here
 * cascades as a `tsc` error in the translations and a test failure in the
 * parity suite.
 *
 * The catalog holds the shell chrome only: the skip link, the header, the
 * footer, the navigation, the language and theme selectors and the not-found
 * page. The screening screens keep their wording beside them, per locale.
 * The demonstration screens (overview, the single-record screening page,
 * corpus, lineage and audit) and their 128 keys were removed on 2026-11-05.
 *
 * Values are the product's chrome wording — no authoritative content, no
 * fixture data, no interpolated values. The only identical string across all
 * three catalogs is `brand.productName` (B01).
 */

export const en = {
  // Metadata / SEO
  "app.meta.description":
    "Traceable systematic-review workflows for research teams.",

  // Shell chrome
  "a11y.skipToMain": "Skip to main content",
  "shell.descriptor": "Systematic review screening",
  "footer.local":
    "Runs on this computer. Nothing is sent anywhere unless you start agent proposals.",
  "footer.journal":
    "Every decision is recorded in the workspace's audit journal.",

  "nav.discovery": "Discovery",
  "nav.screening": "Screening",
  "nav.workspaces": "Workspaces",
  "nav.landmark.primary": "Primary",

  // Mobile navigation
  "a11y.openMainNavigation": "Open main navigation",
  "a11y.closeMainNavigation": "Close main navigation",
  "nav.landmark.primaryMobile": "Primary (mobile menu)",
  "nav.mobileDialogTitle": "Main menu",

  // Locale selector
  "locale.selectorLabel": "Language",

  // Theme selector
  "theme.selectorLabel": "Theme",
  "theme.system": "System",
  "theme.light": "Light",
  "theme.dark": "Dark",

  // Not found page
  "notFound.heading": "Page not found",
  "notFound.body":
    "There is no page at this address. Use the navigation above, or go to your workspaces.",
  "notFound.unsupportedLocale":
    'The locale "{requested}" is not available. Available locales: {available}.',
  "notFound.backToDefault":
    "Go to your workspaces",

  // Brand (identical in all three catalogs — D-I18N-02, §4.2)
  "brand.productName": "Nexus Scholar",
} as const;

export type MessageKey = keyof typeof en;

export default en;