import type { Locale } from "@/i18n";
import type { ImportLoss } from "@/lib/inception-api";
import { inceptionT } from "@/lib/inception-copy";

/**
 * The import report's lines as sentences (M10b, `09-start-from-protocol`). The
 * engine decides every line and its values; this only picks the catalogued
 * sentence for each `what`. An unknown kind is shown by its name, never dropped.
 */
export function importLossLines(locale: Locale, lost: ImportLoss[], needsYou: string[]): string[] {
  const t = inceptionT(locale);
  const s = (value: unknown) => (value == null ? "" : String(value));
  const lines = lost.map((loss) => {
    switch (loss.what) {
      case "facets":
        return t("import.lost.facets");
      case "matrix_id":
        return t("import.lost.matrixId", { name: s(loss.name), id: s(loss.id), new: s(loss.new) });
      case "matrix_default":
        return t("import.lost.matrixDefault", { name: s(loss.name) });
      case "reason_code":
        return t("import.lost.reasonCode", { id: s(loss.id), original: s(loss.original), code: s(loss.code) });
      case "operator":
        return t("import.lost.operator", { concept: s(loss.concept), operator: s(loss.operator) });
      case "maps":
        return t("import.lost.maps", { id: s(loss.id), rqs: Array.isArray(loss.rqs) ? loss.rqs.join(", ") : s(loss.rqs) });
      case "category":
        return t("import.lost.category", { id: s(loss.id) });
      case "threshold":
        return t("import.lost.threshold", { n: s(loss.value) });
      case "rationale":
        return t("import.lost.rationale");
      case "preset":
        return t("import.lost.preset");
      case "method":
        return t("import.lost.method");
      case "seeds":
        return t("import.lost.seeds", { n: s(loss.count) });
      case "grounding":
        return t("import.lost.grounding");
      default:
        return loss.what;
    }
  });
  const needs = needsYou.map((field) => {
    switch (field) {
      case "topic":
        return t("import.needs.topic");
      case "proof":
        return t("import.needs.proof");
      case "paradigm":
        return t("import.needs.paradigm");
      case "unit":
        return t("import.needs.unit");
      default:
        return field;
    }
  });
  return [...lines, ...needs.map((need) => t("import.needs.line", { need }))];
}
