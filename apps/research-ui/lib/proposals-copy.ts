import type { Locale } from "@/i18n";
import { fillCopy } from "@/lib/inception-copy";
import { pluralTemplate } from "@/lib/plural";

/**
 * Copy of the proposal card and list (`docs/ux/shared/final/01-proposals.md`
 * "Copy", M10b). English is the master; French and Arabic carry every key (a
 * missing key fails the type check). Engine text (a proposal's `why`, values,
 * the "was" and "now" texts) is shown as the engine wrote it, never translated.
 */

const EN = {
  // List
  "proposals.title": "Suggestions for this step · {n}",
  "proposals.outOfDate": "{n} out of date",
  "proposals.none": "No suggestions are waiting.",
  "proposals.decided": "Decided ({n})",
  "proposals.badge": "{n} suggestions",
  "proposals.loading": "Reading the suggestions…",

  // Card
  "proposals.draftLabel": "Suggestion · not yet yours",
  "proposals.what.add": "Add {value} to {field}",
  "proposals.what.remove": "Remove {value} from {field}",
  "proposals.what.replace": "Replace {now} with {value}",
  "proposals.why": "Why",
  "proposals.evidence": "Evidence ({n})",
  "proposals.evidence.doi": "Paper {doi}",
  "proposals.evidence.check": "Check {id}",
  "proposals.evidence.count": "{value} {unit}",
  "proposals.evidence.file": "File {path}",
  "proposals.field.synonyms": "Synonyms of {concept}",
  "proposals.edit.concept": "Concept name",
  "proposals.edit.synonym": "Synonym",
  "proposals.edit.value": "Value",

  // Source labels
  "proposals.source.check": "Suggested by a check: {name}",
  "proposals.source.import": "From the protocol {name}",
  "proposals.source.agent": "Suggested by an assistant",
  "proposals.source.generic": "Suggested by the engine",
  "proposals.source.engine.wizard_criterion": "Written by the wizard from your answers",
  "proposals.source.engine.pool_synonym": "A term from the sampled papers",
  "proposals.source.engine.suggested_concept": "A concept suggested from your topic",
  "proposals.source.engine.matrix_column": "A column suggested for this playbook",
  "proposals.source.engine.direction": "A direction proposed from the sampled papers",
  "proposals.source.engine.anchor_seed": "A paper from the sample kept as a known paper",

  // Actions
  "proposals.act.apply": "Apply",
  "proposals.act.edit": "Edit",
  "proposals.act.applyEdit": "Apply my edit",
  "proposals.act.cancel": "Cancel",
  "proposals.act.reject": "Reject",
  "proposals.act.dismiss": "Dismiss",
  "proposals.act.restore": "Restore",
  "proposals.act.announceApplied": "Applied: {field}",
  "proposals.act.announceRejected": "Rejected: {field}",
  "proposals.act.announceStale": "Out of date: {field}",
  "proposals.act.announceRestored": "Restored: {field}",
  "proposals.act.toast": "Applied · {field}",

  // Status
  "proposals.status.applied": "Applied by you",
  "proposals.status.appliedEdited": "Applied after your edit",
  "proposals.status.rejected": "Rejected",
  "proposals.status.stale": "Out of date",
  "proposals.status.open": "Open",

  // Stale
  "proposals.stale.was": "Was: {shown}",
  "proposals.stale.now": "Now: {shown}",
  "proposals.stale.line": "This field changed after the suggestion was made, so it is not applied.",
  "proposals.stale.protocol": "The protocol changed after the suggestion was made.",

  // Errors in the card
  "proposals.err.invalid": "The draft cannot take this value: {error}",
  "proposals.err.gone": "That suggestion is no longer there.",
  "proposals.err.already": "Already {status}.",
  "proposals.word.applied": "applied",
  "proposals.word.rejected": "rejected",
  "proposals.err.other": "The engine refused this decision.",
  "proposals.readOnly": "This draft cannot be changed from this page, so the suggestions are read-only.",

  // Offline and the saved-source line
  "proposals.offline": "needs the engine on this computer",
  "proposals.asOf": "As of {time}",
  "proposals.notRecorded": "This choice was saved; its source could not be recorded.",
} as const;

export type ProposalsCopyKey = keyof typeof EN;

const FR: Record<ProposalsCopyKey, string> = {
  "proposals.title": "Suggestions pour cette étape · {n}",
  "proposals.outOfDate": "{n} périmées",
  "proposals.none": "Aucune suggestion en attente.",
  "proposals.decided": "Décidées ({n})",
  "proposals.badge": "{n} suggestions",
  "proposals.loading": "Lecture des suggestions…",

  "proposals.draftLabel": "Suggestion · pas encore la vôtre",
  "proposals.what.add": "Ajouter {value} à {field}",
  "proposals.what.remove": "Retirer {value} de {field}",
  "proposals.what.replace": "Remplacer {now} par {value}",
  "proposals.why": "Pourquoi",
  "proposals.evidence": "Éléments ({n})",
  "proposals.evidence.doi": "Article {doi}",
  "proposals.evidence.check": "Vérification {id}",
  "proposals.evidence.count": "{value} {unit}",
  "proposals.evidence.file": "Fichier {path}",
  "proposals.field.synonyms": "Synonymes de {concept}",
  "proposals.edit.concept": "Nom du concept",
  "proposals.edit.synonym": "Synonyme",
  "proposals.edit.value": "Valeur",

  "proposals.source.check": "Suggéré par une vérification : {name}",
  "proposals.source.import": "Issu du protocole {name}",
  "proposals.source.agent": "Suggéré par un assistant",
  "proposals.source.generic": "Suggéré par le moteur",
  "proposals.source.engine.wizard_criterion": "Rédigé par l'assistant à partir de vos réponses",
  "proposals.source.engine.pool_synonym": "Un terme tiré des articles de l'échantillon",
  "proposals.source.engine.suggested_concept": "Un concept suggéré à partir de votre sujet",
  "proposals.source.engine.matrix_column": "Une colonne suggérée pour ce type de revue",
  "proposals.source.engine.direction": "Une direction proposée à partir des articles de l'échantillon",
  "proposals.source.engine.anchor_seed": "Un article de l'échantillon gardé comme article connu",

  "proposals.act.apply": "Appliquer",
  "proposals.act.edit": "Modifier",
  "proposals.act.applyEdit": "Appliquer ma modification",
  "proposals.act.cancel": "Annuler",
  "proposals.act.reject": "Rejeter",
  "proposals.act.dismiss": "Écarter",
  "proposals.act.restore": "Rétablir",
  "proposals.act.announceApplied": "Appliqué : {field}",
  "proposals.act.announceRejected": "Rejeté : {field}",
  "proposals.act.announceStale": "Périmé : {field}",
  "proposals.act.announceRestored": "Rétabli : {field}",
  "proposals.act.toast": "Appliqué · {field}",

  "proposals.status.applied": "Appliqué par vous",
  "proposals.status.appliedEdited": "Appliqué après votre modification",
  "proposals.status.rejected": "Rejeté",
  "proposals.status.stale": "Périmé",
  "proposals.status.open": "Ouverte",

  "proposals.stale.was": "Avant : {shown}",
  "proposals.stale.now": "Maintenant : {shown}",
  "proposals.stale.line": "Ce champ a changé après la suggestion ; elle n'est donc pas appliquée.",
  "proposals.stale.protocol": "Le protocole a changé après la suggestion.",

  "proposals.err.invalid": "Le brouillon ne peut pas prendre cette valeur : {error}",
  "proposals.err.gone": "Cette suggestion n'existe plus.",
  "proposals.err.already": "Déjà {status}.",
  "proposals.word.applied": "appliquée",
  "proposals.word.rejected": "rejetée",
  "proposals.err.other": "Le moteur a refusé cette décision.",
  "proposals.readOnly": "Ce brouillon ne peut pas être modifié depuis cette page ; les suggestions sont en lecture seule.",

  "proposals.offline": "nécessite le moteur sur cet ordinateur",
  "proposals.asOf": "Au {time}",
  "proposals.notRecorded": "Ce choix est enregistré ; sa source n'a pas pu être consignée.",
};

const AR: Record<ProposalsCopyKey, string> = {
  "proposals.title": "اقتراحات لهذه الخطوة · {n}",
  "proposals.outOfDate": "{n} لم تعد مطابقة",
  "proposals.none": "لا توجد اقتراحات بانتظارك.",
  "proposals.decided": "ما تقرّر ({n})",
  "proposals.badge": "{n} اقتراحات",
  "proposals.loading": "جارٍ قراءة الاقتراحات…",

  "proposals.draftLabel": "اقتراح · ليس قرارك بعد",
  "proposals.what.add": "أضف {value} إلى {field}",
  "proposals.what.remove": "احذف {value} من {field}",
  "proposals.what.replace": "استبدل {now} بـ {value}",
  "proposals.why": "لماذا",
  "proposals.evidence": "الأدلة ({n})",
  "proposals.evidence.doi": "الورقة {doi}",
  "proposals.evidence.check": "الفحص {id}",
  "proposals.evidence.count": "{value} {unit}",
  "proposals.evidence.file": "الملف {path}",
  "proposals.field.synonyms": "مرادفات {concept}",
  "proposals.edit.concept": "اسم المفهوم",
  "proposals.edit.synonym": "المرادف",
  "proposals.edit.value": "القيمة",

  "proposals.source.check": "اقترحه فحص: {name}",
  "proposals.source.import": "من البروتوكول {name}",
  "proposals.source.agent": "اقترحه مساعد",
  "proposals.source.generic": "اقترحه المحرك",
  "proposals.source.engine.wizard_criterion": "كتبه المعالج من إجاباتك",
  "proposals.source.engine.pool_synonym": "مصطلح من أوراق العينة",
  "proposals.source.engine.suggested_concept": "مفهوم مقترح من موضوعك",
  "proposals.source.engine.matrix_column": "عمود مقترح لهذا النوع من المراجعات",
  "proposals.source.engine.direction": "اتجاه مقترح من أوراق العينة",
  "proposals.source.engine.anchor_seed": "ورقة من العينة احتُفظ بها ورقةً معروفة",

  "proposals.act.apply": "طبّق",
  "proposals.act.edit": "عدّل",
  "proposals.act.applyEdit": "طبّق تعديلي",
  "proposals.act.cancel": "إلغاء",
  "proposals.act.reject": "ارفض",
  "proposals.act.dismiss": "تجاهل",
  "proposals.act.restore": "استعد",
  "proposals.act.announceApplied": "طُبّق: {field}",
  "proposals.act.announceRejected": "رُفض: {field}",
  "proposals.act.announceStale": "لم يعد مطابقًا: {field}",
  "proposals.act.announceRestored": "استُعيد: {field}",
  "proposals.act.toast": "طُبّق · {field}",

  "proposals.status.applied": "طبّقته أنت",
  "proposals.status.appliedEdited": "طُبّق بعد تعديلك",
  "proposals.status.rejected": "مرفوض",
  "proposals.status.stale": "لم يعد مطابقًا",
  "proposals.status.open": "مفتوح",

  "proposals.stale.was": "كان: {shown}",
  "proposals.stale.now": "الآن: {shown}",
  "proposals.stale.line": "تغيّر هذا الحقل بعد تقديم الاقتراح، لذا لا يُطبَّق.",
  "proposals.stale.protocol": "تغيّر البروتوكول بعد تقديم الاقتراح.",

  "proposals.err.invalid": "لا تقبل المسودة هذه القيمة: {error}",
  "proposals.err.gone": "لم يعد ذلك الاقتراح موجودًا.",
  "proposals.err.already": "سبق أن {status}.",
  "proposals.word.applied": "طُبّق",
  "proposals.word.rejected": "رُفض",
  "proposals.err.other": "رفض المحرك هذا القرار.",
  "proposals.readOnly": "لا يمكن تغيير هذه المسودة من هذه الصفحة، لذا الاقتراحات للقراءة فقط.",

  "proposals.offline": "يحتاج إلى المحرك على هذا الحاسوب",
  "proposals.asOf": "حتى {time}",
  "proposals.notRecorded": "حُفظ هذا الاختيار؛ تعذّر تسجيل مصدره.",
};

export const PROPOSALS_COPY: Record<Locale, Record<ProposalsCopyKey, string>> = { en: EN, fr: FR, ar: AR };

/** The template of a key for a count (H-ui-findings F4). */
export function proposalsCountTemplate(locale: Locale, key: ProposalsCopyKey, count: number): string {
  return pluralTemplate(locale, key, count, PROPOSALS_COPY[locale][key]);
}

export function proposalsT(locale: Locale) {
  return (key: ProposalsCopyKey, values?: Record<string, string | number>) => fillCopy(PROPOSALS_COPY[locale][key], values);
}

/** Whether a key exists (a source label for an engine mechanism the copy does not know falls back). */
export function hasProposalsKey(key: string): key is ProposalsCopyKey {
  return key in EN;
}
