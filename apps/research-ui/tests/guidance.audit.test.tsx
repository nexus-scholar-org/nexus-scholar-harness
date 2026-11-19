import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DISCOVERY_COPY } from "@/lib/discovery-copy";
import { INCEPTION_COPY } from "@/lib/inception-copy";

import { auditRows, DISCOVERY_KEYS, INCEPTION_KEYS, type AuditRow } from "./fixtures/guidance-audit";
import { SCREENS } from "./guidance-screens";
import { visibleWords } from "./guidance-words";

/**
 * 03-guidance "Acceptance tests", `guidance.audit.test.tsx` (M10d): the Audit
 * table (read from the spec, `fixtures/guidance-audit.ts`) against the catalogs
 * and the rendered screens.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const ROWS = auditRows();
const EN: Record<string, string> = { ...(INCEPTION_COPY.en as Record<string, string>), ...(DISCOVERY_COPY.en as Record<string, string>) };
const keysOf = (decision: AuditRow["decision"]) => new Set(ROWS.filter((r) => r.decision === decision).flatMap((r) => r.keys));
const HINT = keysOf("HINT");
const STAYS = keysOf("STAYS");
/**
 * A HINT key whose whole text is hidden: not a key that also has a STAYS sentence,
 * and not a sentence another screen keeps visible inside a STAYS text (the chase's
 * gate record is a hint; the hand-off gate body says the same and stays).
 */
const STAYS_TEXT = [...STAYS].map((k) => (INCEPTION_COPY.en as Record<string, string>)[k] ?? (DISCOVERY_COPY.en as Record<string, string>)[k] ?? "");
const HINT_ONLY = [...HINT].filter((k) => !STAYS.has(k));

const norm = (s: string) => s.replace(/\s+/g, " ").trim();
/** The fixed words of a template: up to its first placeholder. */
const fixedPart = (template: string) => norm(template.split("{")[0]);
/** A REMOVED row's sentence as the spec quotes it, up to an ellipsis or a placeholder. */
const removedText = (row: AuditRow) => norm((row.text.match(/"([^"]+)"/)?.[1] ?? "").split(/\.\.\.|…|\{/)[0]);

describe("guidance.audit", () => {
  it("reads every row of the spec's Audit, each id once, each key cell resolved", () => {
    expect(ROWS.length).toBeGreaterThan(280);
    const ids = ROWS.map((r) => r.id);
    expect(ids.filter((id, i) => ids.indexOf(id) !== i)).toEqual([]);
    expect(ROWS.filter((r) => r.unresolved.length).map((r) => `${r.id}: ${r.unresolved.join(", ")}`)).toEqual([]);
  });

  it("has a row for every key of the inception and discovery catalogs (a new key fails until it is audited)", () => {
    const covered = (prefix: string) => new Set(ROWS.filter((r) => r.id.startsWith(prefix)).flatMap((r) => r.keys));
    const inception = covered("I-");
    const discovery = covered("D-");
    expect(INCEPTION_KEYS.filter((k) => !inception.has(k))).toEqual([]);
    expect(DISCOVERY_KEYS.filter((k) => !discovery.has(k))).toEqual([]);
  });

  it("states the same counts per decision as the spec's table", () => {
    const spec = readFileSync(join(process.cwd(), "..", "..", "docs", "ux", "shared", "final", "03-guidance.md"), "utf-8");
    const count = (prefix: string, d: string) => ROWS.filter((r) => r.id.startsWith(prefix) && r.decision === d).length;
    for (const [label, prefix] of [
      ["Inception 01 to 07", "I-"],
      ["Discovery 01 to 09", "D-"],
    ] as const) {
      const line = spec.split(/\r?\n/).find((l) => l.startsWith(`| ${label}`));
      const numbers = (line ?? "").split("|").slice(2, 6).map((c) => Number(c.trim()));
      expect(numbers, label).toEqual([count(prefix, "STAYS"), count(prefix, "HINT"), count(prefix, "REMOVED"), ROWS.filter((r) => r.id.startsWith(prefix)).length]);
    }
  });

  for (const s of SCREENS) {
    it(`${s.name}: every hint holds a HINT key, no HINT text is in the visible flow, no REMOVED sentence is in the page`, async () => {
      await s.mount();
      const hinted = [...document.querySelectorAll<HTMLElement>("[data-hint-body]")].map((el) => el.dataset.hintBody ?? "");
      expect(hinted.filter((k) => !HINT.has(k)), "hint bodies that are not HINT rows").toEqual([]);
      const visible = norm(visibleWords().join(" "));
      for (const key of HINT_ONLY) {
        const fixed = fixedPart(EN[key] ?? "");
        if (fixed.split(" ").length < 4) continue; // too short to identify a sentence
        if (STAYS_TEXT.some((t) => norm(t).includes(fixed))) continue;
        expect(visible.includes(fixed), `${key} is visible: "${fixed}"`).toBe(false);
      }
      const all = norm(document.body.textContent ?? "");
      for (const row of ROWS.filter((r) => r.decision === "REMOVED")) {
        const text = removedText(row);
        if (text.split(" ").length < 4) continue;
        expect(all.includes(text), `${row.id} still in the page: "${text}"`).toBe(false);
      }
      expect(hinted.length, "the screen has at least one hint").toBeGreaterThan(0);
    }, 20000);
  }
});
