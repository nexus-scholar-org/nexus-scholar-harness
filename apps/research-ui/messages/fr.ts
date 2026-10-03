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
 *    seeing both would be looking at untranslated chrome. That rule is why
 *    `nav.audit` is "Registre" rather than the very common "Audit", and why
 *    `evidenceKind.document` is "article": both would otherwise read as
 *    untranslated English to a normalised comparison and in a screenshot.
 * 4. Latin script throughout, so the direction-neutral markup and the
 *    long-string filler need no special case for this locale.
 */
const fr: Record<MessageKey, string> = {
  "app.meta.description":
    "Des méthodes de revue systématique traçables pour les équipes de recherche.",
  "overview.eyebrow": "Vue d'ensemble du projet",
  "overview.lastEvent": "Dernière étape : {event}",
  "overview.workflowHeading": "Méthode",
  "overview.workflowLede":
    "Chaque étape expose ses décisions, ses preuves et ses refus.",
  "overview.traceHeading": "De la revue à la source",
  "overview.traceLede":
    "Suivez une affirmation jusqu'à la décision qui la rattache au protocole.",
  "overview.asideEyebrow": "Pourquoi c'est important",
  "overview.asideHeading":
    "Une synthèse n'est pas crédible simplement parce qu'elle sonne convaincante.",
  "overview.asideBody":
    "Nexus Scholar rend le chemin des preuves inspectable et refuse les artefacts qui ne respectent pas la filiation déclarée.",
  "a11y.skipToMain": "Aller au contenu principal",
  "shell.tagline": "Une intégrité de la recherche que vous pouvez vérifier",
  "safety.demoDataLabel": "Données de démonstration",
  "shell.authorityStatement":
    "Démonstrateur en lecture seule. Le harnais Python reste l'autorité pour les contrats, l'identité, l'acceptation, l'exécution des outils et les événements d'audit.",
  "nav.overview": "Vue d'ensemble",
  "nav.screening": "Sélection",
  "nav.evidence": "Preuves",
  "nav.audit": "Registre",
  "nav.unavailable": "Pas encore disponible",
  "nav.landmark.primary": "Principal",
  "a11y.openMainNavigation": "Ouvrir la navigation principale",
  "a11y.closeMainNavigation": "Fermer la navigation principale",
  "nav.landmark.primaryMobile": "Principal (menu mobile)",
  "nav.mobileDialogTitle": "Menu principal",
  "workflow.listLabel": "Méthode de la revue",
  "workflow.stageOrdinal": "Étape {number}",
  "workflow.stageOrdinal.prefix": "Étape ",
  "state.complete": "terminée",
  "state.active": "en cours",
  "state.waiting": "en attente",
  "state.refused": "refusée",
  "evidenceKind.claim": "affirmation",
  "evidenceKind.chunk": "extrait",
  "evidenceKind.document": "article",
  "evidenceKind.study": "étude",
  "evidenceKind.decision": "décision",
  "locale.selectorLabel": "Langue",
  "notFound.heading": "Page introuvable",
  "notFound.body":
    "Cette démonstration n'a pas de page à cette adresse. Utilisez l'un des liens de langue ci-dessous, ou revenez à la vue d'ensemble.",
  "notFound.unsupportedLocale":
    'La locale « {requested} » n\'est pas disponible. Locales disponibles : {available}.',
  "notFound.backToDefault": "Revenir à la vue d'ensemble en anglais",
  "brand.productName": "Nexus Scholar",
};

export default fr;