import { Fragment, type ReactNode } from "react";

/**
 * Small shared pieces of the M10b proposal and check lists: a copy template
 * filled with React nodes (so a slot can be a `bdi`), and the field anchors a
 * check's action link lands on. The anchors name where each draft field is
 * edited on its screen; they decide nothing.
 */

/** `{name}` slots filled with nodes; a slot the values do not name renders nothing. */
export function fillNodes(template: string, values: Record<string, ReactNode>): ReactNode {
  const parts = template.split(/(\{\w+\})/g);
  return parts.map((part, index) => {
    const match = part.match(/^\{(\w+)\}$/);
    return <Fragment key={index}>{match ? (values[match[1]] ?? null) : part}</Fragment>;
  });
}

/** The same template as plain text, for announcements. */
export function fillText(template: string, values: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => values[k] ?? "");
}

/** Where each draft field is edited, as a selector on its own screen. */
const FIELD_SELECTOR: Record<string, string> = {
  topic: "#scope-topic",
  start_year: "#scope-from",
  end_year: "#scope-to",
  languages: "#scope-languages",
  golden_seeds: "#seeds-title",
  paradigm: 'input[name="paradigm"]',
  playbook: 'input[name="playbook"]',
  unit_of_analysis: "#shape-unit",
  proof: "#shape-proof",
  rqs: "#shape-rq-0",
  out_of_scope: "#shape-out",
  pool_min: "#shape-planned-min",
  pool_max: "#shape-planned-max",
  concepts: "#criteria-concepts",
  criteria_decisions: "#criteria-inclusion",
  extra_inclusions: "#criteria-new-inclusion",
  extra_exclusions: "#criteria-new-exclusion",
  matrix_columns: "[data-matrix] legend",
  title: "#review-title",
  lead_researcher: "#review-lead",
  venue: "#review-venue",
};

/** The hash of a field link: `field-<name>`, or `field-criteria_decisions:<criterion id>` for one criterion. */
export function fieldHash(field: string, criterionId?: string): string {
  return criterionId ? `field-${field}:${criterionId}` : `field-${field}`;
}

export function proposalHash(proposalId: string): string {
  return `proposal-${proposalId}`;
}

function resolve(hash: string): HTMLElement | null {
  if (typeof document === "undefined") return null;
  if (hash.startsWith("proposal-")) {
    const card = document.getElementById(hash);
    return (card?.querySelector("button:not([disabled])") as HTMLElement | null) ?? card;
  }
  if (!hash.startsWith("field-")) return null;
  const [field, criterion] = hash.slice("field-".length).split(":");
  if (criterion) {
    const row = document.querySelector(`[data-criterion="${criterion.replace(/["\\]/g, "")}"] [data-accept]`) as HTMLElement | null;
    if (row) return row;
  }
  const selector = FIELD_SELECTOR[field];
  return selector ? (document.querySelector(selector) as HTMLElement | null) : null;
}

/** Focus the element a hash names when it is on this page now; answers whether it was. */
export function tryFocus(hash: string): boolean {
  const element = resolve(hash);
  if (!element) return false;
  if (element.tabIndex < 0 && !element.hasAttribute("tabindex")) element.setAttribute("tabindex", "-1");
  element.focus();
  return true;
}

/** Focus the element a hash names; the screen may draw it late, so try again a few times. Returns a cancel. */
export function focusAnchor(hash: string, tries = 1): () => void {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let left = tries;
  const attempt = () => {
    const element = resolve(hash);
    if (element) {
      if (element.tabIndex < 0 && !element.hasAttribute("tabindex")) element.setAttribute("tabindex", "-1");
      element.focus();
      return;
    }
    left -= 1;
    if (left > 0) timer = setTimeout(attempt, 200);
  };
  attempt();
  return () => {
    if (timer) clearTimeout(timer);
  };
}
