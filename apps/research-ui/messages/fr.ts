import type { MessageKey } from "./en";

/**
 * The French catalog.
 *
 * **Demonstration translation.** No fluent reviewer has approved this wording
 * (`README.md`'s i18n policy; packet UI-01d H1). It exists so the routing,
 * document-attribute, logical-CSS and long-string machinery can be exercised
 * in a second language, and it must be read as an unreviewed draft until a
 * fluent French reader signs it off. It is *not* a claim of professional
 * translation. See `I18N.md`.
 *
 * Rules this file obeys, and which `tests/i18n-catalog.test.ts` checks
 * mechanically:
 *
 * 1. Exactly the keys of `en.ts` — no more, no fewer (N5). The `Record` type
 *    makes an extra key a compile error and a missing one too.
 * 2. The same `{…}` placeholders in the same strings (N4). Placeholder *names*
 *    are part of the contract; their *positions* are this translator's
 *    decision, which is why a template is one entry and never two fragments.
 * 3. No French value may normalise to its English counterpart
 *    (whitespace-collapsed, case-folded, diacritic-stripped), because a reader
 *    seeing both would be looking at untranslated chrome.
 * 4. Latin script throughout, so the direction-neutral markup and the
 *    long-string filler need no special case for this locale.
 */
const fr: Record<MessageKey, string> = {
  "app.meta.description":
    "Des méthodes de revue systématique traçables pour les équipes de recherche.",
  "a11y.skipToMain": "Aller au contenu principal",
  "shell.descriptor": "Sélection pour revues systématiques",
  "footer.local":
    "Fonctionne sur cet ordinateur. Rien n'est envoyé ailleurs, sauf si vous lancez les propositions de l'agent.",
  "footer.journal":
    "Chaque décision est consignée dans le journal d'audit de l'espace de travail.",
  "nav.screening": "Sélection",
  "nav.workspaces": "Espaces de travail",
  "nav.landmark.primary": "Principal",
  "a11y.openMainNavigation": "Ouvrir la navigation principale",
  "a11y.closeMainNavigation": "Fermer la navigation principale",
  "nav.landmark.primaryMobile": "Principal (menu mobile)",
  "nav.mobileDialogTitle": "Menu principal",
  "locale.selectorLabel": "Langue",
  "theme.selectorLabel": "Thème",
  "theme.system": "Système",
  "theme.light": "Clair",
  "theme.dark": "Sombre",
  "notFound.heading": "Page introuvable",
  "notFound.body":
    "Il n'y a aucune page à cette adresse. Utilisez la navigation ci-dessus, ou revenez à vos espaces de travail.",
  "notFound.unsupportedLocale":
    'La locale « {requested} » n\'est pas disponible. Locales disponibles : {available}.',
  "notFound.backToDefault":
    "Revenir à vos espaces de travail",

  "brand.productName": "Nexus Scholar",
};

export default fr;