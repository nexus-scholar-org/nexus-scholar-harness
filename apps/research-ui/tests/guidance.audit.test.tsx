
import { cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DISCOVERY_COPY } from "@/lib/discovery-copy";
import { INCEPTION_COPY } from "@/lib/inception-copy";
import { WORKBENCH_COPY } from "@/lib/workbench-copy";

import { auditRows, type AuditRow } from "./fixtures/guidance-audit";
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
const EN: Record<string, string> = { ...(INCEPTION_COPY.en as Record<string, string>), ...(DISCOVERY_COPY.en as Record<string, string>), ...(WORKBENCH_COPY.en as Record<string, string>) };
const keysOf = (decision: AuditRow["decision"]) => new Set(ROWS.filter((r) => r.decision === decision).flatMap((r) => r.keys));
const HINT = keysOf("HINT");
const STAYS = keysOf("STAYS");
/**
 * A HINT key whose whole text is hidden: not a key that also has a STAYS sentence,
 * and not a sentence another screen keeps visible inside a STAYS text (the chase's
 * gate record is a hint; the hand-off gate body says the same and stays).
 */
const STAYS_TEXT = [...STAYS].map((k) => EN[k] ?? "");
const HINT_ONLY = [...HINT].filter((k) => !STAYS.has(k));

const norm = (s: string) => s.replace(/\s+/g, " ").trim();
/** The fixed words of a template: up to its first placeholder. */
const fixedPart = (template: string) => norm(template.split("{")[0]);
/** A REMOVED row's sentence as the spec quotes it, up to an ellipsis or a placeholder. */
const removedText = (row: AuditRow) => norm((row.text.match(/"([^"]+)"/)?.[1] ?? "").split(/\.\.\.|…|\{/)[0]);

describe("guidance.audit", () => {

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
