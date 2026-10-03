/**
 * The English catalog — structural source of truth (D-I18N-03).
 *
 * This file defines the 41 keys that `fr.ts` and `ar.ts` must mirror exactly
 * (compile-time via `Record<MessageKey, string>` and runtime via
 * `tests/i18n-catalog.test.ts`). A key added, removed, or misspelled here
 * cascades as a `tsc` error in the translations and a test failure in the
 * parity suite. Do not edit the key set without updating all three catalogs
 * and the packet's §4 inventory.
 *
 * Values are the product's chrome wording — no authoritative content, no
 * fixture data, no interpolated values. The only identical string across all
 * three catalogs is `brand.productName` (B01).
 */

export const en = {
  // Metadata / SEO
  "app.meta.description":
    "Traceable systematic-review workflows for research teams.",

  // Overview page chrome
  "overview.eyebrow": "Project overview",
  "overview.lastEvent": "Latest: {event}",
  "overview.workflowHeading": "Workflow",
  "overview.workflowLede":
    "Every stage exposes its decisions, evidence, and refusals.",
  "overview.traceHeading": "Claim-to-source trace",
  "overview.traceLede":
    "Follow a research claim back to its protocol-bound decision.",
  "overview.asideEyebrow": "Why this matters",
  "overview.asideHeading":
    "A synthesis is not trusted because it sounds convincing.",
  "overview.asideBody":
    "Nexus Scholar makes the evidence path inspectable and refuses artifacts that do not satisfy the declared lineage.",

  // Shell chrome
  "a11y.skipToMain": "Skip to main content",
  "shell.tagline": "Research integrity you can inspect",
  "safety.demoDataLabel": "Demonstration data",
  "shell.authorityStatement":
    "Read-only demonstrator. The Python harness remains authoritative for contracts, identity, acceptance, toolkit execution and audit events.",

  // Navigation
  "nav.overview": "Overview",
  "nav.screening": "Screening",
  "nav.evidence": "Evidence",
  "nav.audit": "Audit",
  "nav.unavailable": "Not yet available",
  "nav.landmark.primary": "Primary",

  // Mobile navigation
  "a11y.openMainNavigation": "Open main navigation",
  "a11y.closeMainNavigation": "Close main navigation",
  "nav.landmark.primaryMobile": "Primary (mobile menu)",
  "nav.mobileDialogTitle": "Main menu",

  // Workflow timeline
  "workflow.listLabel": "Research workflow",
  "workflow.stageOrdinal": "Stage {number}",
  "workflow.stageOrdinal.prefix": "Stage ",

  // State stamps
  "state.complete": "complete",
  "state.active": "active",
  "state.waiting": "waiting",
  "state.refused": "refused",

  // Evidence kinds
  "evidenceKind.claim": "claim",
  "evidenceKind.chunk": "chunk",
  "evidenceKind.document": "document",
  "evidenceKind.study": "study",
  "evidenceKind.decision": "decision",

  // Locale selector
  "locale.selectorLabel": "Language",

  // Not found page
  "notFound.heading": "Page not found",
  "notFound.body":
    "This demonstration has no page at this address. Use one of the language links below, or return to the overview.",
  "notFound.unsupportedLocale":
    'The locale "{requested}" is not available. Available locales: {available}.',
  "notFound.backToDefault": "Return to the English overview",

  // Brand (identical in all three catalogs — D-I18N-02, §4.2)
  "brand.productName": "Nexus Scholar",
} as const;

export type MessageKey = keyof typeof en;

export default en;