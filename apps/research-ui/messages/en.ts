/**
 * The English catalog — structural source of truth (D-I18N-03).
 *
 * This file defines the 74 keys that `fr.ts` and `ar.ts` must mirror exactly
 * (compile-time via `Record<MessageKey, string>` and runtime via
 * `tests/i18n-catalog.test.ts`). A key added, removed, or misspelled here
 * cascades as a `tsc` error in the translations and a test failure in the
 * parity suite. Do not edit the key set without updating all three catalogs
 * and the packet's §4 inventory.
 *
 * 42 of those keys predate packet UI-02; UI-02 added the 32 marked below
 * (current stage, record arrival, nine phases with descriptions, and the corpus
 * statistics). The count is asserted, not trusted: the parity test fails on any
 * drift, and its expected number is the number this comment claims.
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

  // ---- Project overview state model (packet UI-02): 32 keys ----
  // Current stage section
  "overview.stateHeading": "Current stage",
  "overview.stateLede":
    "Where this project stands now, and the statistics the record carries. A statistic the record does not carry is shown as unknown, not as zero.",

  // Record arrival: did the overview record arrive, independent of any phase
  "overview.recordLoadingLabel": "Loading",
  "overview.recordLoading":
    "The project record has not arrived yet. Nothing is inferred while it is pending.",
  "overview.recordErrorLabel": "Unavailable",
  "overview.recordError":
    "The overview record could not be loaded. This is a failed read, not a refused decision.",
  "overview.nextDestination": "Continue in {destination}.",

  // The nine workflow phases: stamp word, then one sentence of explanation
  "phase.empty": "No project",
  "phase.empty.description":
    "No project has been created yet, so there is no corpus, no decisions, and no evidence to show.",
  "phase.setup": "Setup",
  "phase.setup.description":
    "The protocol and its criteria are being written. The workflow starts when the protocol is sealed.",
  "phase.search": "Search",
  "phase.search.description":
    "Records are being discovered and deduplicated before anyone screens them.",
  "phase.screening": "Screening",
  "phase.screening.description":
    "Inclusion and exclusion decisions are waiting for a person to make them. Nothing is decided automatically.",
  "phase.extraction": "Extraction",
  "phase.extraction.description":
    "Included studies are being extracted, and every extracted passage keeps its path back to its source.",
  "phase.indexing": "Indexing",
  "phase.indexing.description":
    "Extracted passages are being indexed so a later synthesis can retrieve them with their lineage intact.",
  "phase.refusal": "Refused",
  "phase.refusal.description":
    "A step was refused by the authority that runs it, so no partial result stands in its place.",
  "phase.degraded": "Degraded",
  "phase.degraded.description":
    "Part of the record is unavailable. What the record does not carry is shown as unknown rather than guessed.",
  "phase.ready": "Ready",
  "phase.ready.description":
    "Screening, full text, and extraction have produced the included studies. The grounded report has not started.",

  // Corpus statistics: five labels, always rendered; absent value reads unknown
  "counts.heading": "Corpus statistics",
  "counts.recordsDiscovered": "Records discovered",
  "counts.studiesIncluded": "Studies included",
  "counts.decisionsPending": "Decisions awaiting a person",
  "counts.documentsExtracted": "Documents extracted",
  "counts.chunksIndexed": "Passages indexed",
  "counts.unknown": "unknown",

  // Brand (identical in all three catalogs — D-I18N-02, §4.2)
  "brand.productName": "Nexus Scholar",
} as const;

export type MessageKey = keyof typeof en;

export default en;