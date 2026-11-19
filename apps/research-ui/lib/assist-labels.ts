import type { Locale } from "@/i18n";
import { INCEPTION_COPY, fillCopy, type InceptionCopyKey } from "@/lib/inception-copy";
import { PROPOSALS_COPY } from "@/lib/proposals-copy";

/**
 * The names the proposal cards and the check sentences give a draft field or a
 * step: the screen's own label for the field (01-proposals "What"), the
 * stepper's name for the step. A field the screens do not label is shown as
 * the engine named it.
 */

const FIELD_KEY: Record<string, InceptionCopyKey> = {
  topic: "field.topic",
  paradigm: "field.paradigm",
  playbook: "field.playbook",
  unit_of_analysis: "field.unit_of_analysis",
  proof: "field.proof",
  rqs: "field.rqs",
  concepts: "field.concepts",
  title: "field.title",
  lead_researcher: "field.lead_researcher",
  start_year: "scope.fromYear",
  end_year: "scope.toYear",
  languages: "scope.languages",
  out_of_scope: "shape.outOfScope",
  extra_inclusions: "criteria.inclusion",
  extra_exclusions: "criteria.exclusion",
  matrix_columns: "criteria.matrix",
  golden_seeds: "direction.seeds.title",
  venue: "review.venue",
};

const SYNONYMS = /^concepts\[(.+)\]\.synonyms$/;

/** The concept a `concepts[<name>].synonyms` target names, or `null`. */
export function synonymConcept(field: string): string | null {
  return field.match(SYNONYMS)?.[1] ?? null;
}

export function fieldLabel(locale: Locale, field: string): string {
  const concept = synonymConcept(field);
  if (concept !== null) return fillCopy(PROPOSALS_COPY[locale]["proposals.field.synonyms"], { concept });
  const key = FIELD_KEY[field];
  return key ? INCEPTION_COPY[locale][key] : field;
}

const STEP_KEY: Record<string, InceptionCopyKey> = {
  scope: "step.scope",
  explore: "step.explore",
  direction: "step.direction",
  shape: "step.shape",
  criteria: "step.criteria",
  review: "step.review",
};

/** The inception step's number on the stepper (06's "Step {n}" chips). */
export const STEP_NUMBER: Record<string, number> = { scope: 1, explore: 2, direction: 3, shape: 4, criteria: 5, review: 6 };

export function stepLabel(locale: Locale, step: string): string {
  const key = STEP_KEY[step];
  return key ? INCEPTION_COPY[locale][key] : step;
}
