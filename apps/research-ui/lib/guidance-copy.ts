import type { Locale } from "@/i18n";

/**
 * Copy of the guidance components (`docs/ux/shared/final/03-guidance.md`
 * "Copy", M10d): the hint button's name, the Recommended mark and the folded
 * section's summary. English is the master; French and Arabic carry every key
 * (a missing key fails the type check). A hint's own text is never here: it is
 * the screen's existing key, moved, not rewritten.
 */

const EN = {
  "guidance.hint.open": "About {label}",
  "guidance.hint.close": "Close",
  "guidance.recommended": "Recommended",
  "guidance.recommended.by": "Recommended · {source}",
  "guidance.recommended.source.wordScan": "word scan of your topic",
  "guidance.recommended.source.poolHealth": "pool size check",
  "guidance.recommended.source.check": "check {id}",
  "guidance.recommended.source.import": "imported protocol",
  "guidance.recommended.source.estimate": "size estimate",
  "guidance.recommended.source.lens": "matches your lens",
  "guidance.section.count": "{title} · {n}",
  "guidance.section.failed": "{n} failed",
  "guidance.section.zero": "{n} found nothing",
  "guidance.notStored": "Not stored",
} as const;

export type GuidanceCopyKey = keyof typeof EN;

const FR: Record<GuidanceCopyKey, string> = {
  "guidance.hint.open": "À propos de « {label} »",
  "guidance.hint.close": "Fermer",
  "guidance.recommended": "Recommandé",
  "guidance.recommended.by": "Recommandé · {source}",
  "guidance.recommended.source.wordScan": "analyse des mots de votre sujet",
  "guidance.recommended.source.poolHealth": "vérification de la taille du corpus",
  "guidance.recommended.source.check": "vérification {id}",
  "guidance.recommended.source.import": "protocole importé",
  "guidance.recommended.source.estimate": "estimation de taille",
  "guidance.recommended.source.lens": "correspond à votre perspective",
  "guidance.section.count": "{title} · {n}",
  "guidance.section.failed": "{n} en échec",
  "guidance.section.zero": "{n} sans résultat",
  "guidance.notStored": "Non enregistré",
};

const AR: Record<GuidanceCopyKey, string> = {
  "guidance.hint.open": "حول «{label}»",
  "guidance.hint.close": "إغلاق",
  "guidance.recommended": "موصى به",
  "guidance.recommended.by": "موصى به · {source}",
  "guidance.recommended.source.wordScan": "فحص كلمات موضوعك",
  "guidance.recommended.source.poolHealth": "فحص حجم المجموعة",
  "guidance.recommended.source.check": "الفحص {id}",
  "guidance.recommended.source.import": "البروتوكول المستورد",
  "guidance.recommended.source.estimate": "تقدير الحجم",
  "guidance.recommended.source.lens": "يوافق منظورك",
  "guidance.section.count": "{title} · {n}",
  "guidance.section.failed": "فشل {n}",
  "guidance.section.zero": "{n} بلا نتائج",
  "guidance.notStored": "غير محفوظ",
};

export const GUIDANCE_COPY: Record<Locale, Record<GuidanceCopyKey, string>> = { en: EN, fr: FR, ar: AR };

export function guidanceT(locale: Locale) {
  return (key: GuidanceCopyKey, values: Record<string, string | number> = {}) =>
    GUIDANCE_COPY[locale][key].replace(/\{(\w+)\}/g, (_, k: string) => {
      if (!(k in values)) throw new Error(`guidance copy needs {${k}}`);
      return String(values[k]);
    });
}
