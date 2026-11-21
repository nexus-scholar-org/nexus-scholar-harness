import { readFileSync } from "node:fs";
import { join } from "node:path";

import { DISCOVERY_COPY } from "@/lib/discovery-copy";
import { INCEPTION_COPY } from "@/lib/inception-copy";
import { WORKBENCH_COPY } from "@/lib/workbench-copy";

/**
 * The Audit of `docs/ux/shared/final/03-guidance.md` (M10d), read from the spec
 * itself so the spec stays the one list: each row's id, its decision (STAYS,
 * HINT, REMOVED) and the catalog keys its "Copy key" cell names.
 *
 * A cell names keys the way the spec writes them: a full key
 * (`explore.pool.title`), a key relative to the row's first key (`pool.meta`
 * after `explore.pool.title`), or a group (`harvest.col.*`). Inception rows
 * (`I-`) name `inception-copy` keys, discovery rows (`D-`) `discovery-copy` keys.
 */

export type Decision = "STAYS" | "HINT" | "REMOVED";
export type AuditRow = { id: string; decision: Decision; tokens: string[]; keys: string[]; unresolved: string[]; text: string; reason: string };

function specPath(): string {
  for (const root of [process.cwd(), join(process.cwd(), "..", "..")]) {
    const path = join(root, "docs", "ux", "shared", "final", "03-guidance.md");
    try {
      readFileSync(path);
      return path;
    } catch {
      continue;
    }
  }
  return join(process.cwd(), "..", "..", "docs", "ux", "shared", "final", "03-guidance.md");
}

export const INCEPTION_KEYS = Object.keys(INCEPTION_COPY.en);
export const DISCOVERY_KEYS = Object.keys(DISCOVERY_COPY.en);
/** M11a: the query workbench's catalog (`W-` rows). */
export const WORKBENCH_KEYS = Object.keys(WORKBENCH_COPY.en);

/** A token as written, then relative to each leading part of the row's first key (`size.ok` after `explore.tile.size.title`). */
function resolve(token: string, first: string, catalog: string[]): string[] {
  const parts = first.split(".");
  const prefixes = parts.slice(0, -1).map((_, i) => parts.slice(0, i + 1).join("."));
  // Relative first (the longest leading part wins), then as written: `direction.own` after
  // `review.direction.title` is `review.direction.own`, not Direction's `direction.own.*`.
  const forms = [...prefixes.reverse().map((p) => `${p}.${token}`), token];
  for (const form of forms) {
    if (form.endsWith("*")) {
      const prefix = form.endsWith(".*") ? form.slice(0, -1) : form.slice(0, -1);
      const hits = catalog.filter((k) => k.startsWith(prefix));
      if (hits.length) return hits;
    } else {
      const hits = catalog.filter((k) => k === form || k.startsWith(`${form}.`));
      if (hits.length) return hits;
    }
  }
  return [];
}

export function auditRows(): AuditRow[] {
  const text = readFileSync(specPath(), "utf-8");
  const rows: AuditRow[] = [];
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(/^\| ((?:I|D|W)-[A-Z]*\d+) \| (.*?) \| (.*?) \| (STAYS|HINT|REMOVED) \| (.*) \|$/);
    if (!m) continue;
    const [, id, keyCell, textCell, decision, reason] = m;
    const tokens = [...keyCell.matchAll(/`([^`]+)`/g)].map((t) => t[1]);
    const catalog = id.startsWith("I-") ? INCEPTION_KEYS : id.startsWith("W-") ? WORKBENCH_KEYS : DISCOVERY_KEYS;
    const first = tokens[0] ?? "";
    const keys = new Set<string>();
    const unresolved: string[] = [];
    for (const token of tokens) {
      const hits = resolve(token, first, catalog);
      if (hits.length) hits.forEach((k) => keys.add(k));
      else unresolved.push(token);
    }
    rows.push({ id, decision: decision as Decision, tokens, keys: [...keys], unresolved, text: textCell, reason });
  }
  return rows;
}
