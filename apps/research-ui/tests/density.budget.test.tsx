import { cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DISCOVERY_COPY } from "@/lib/discovery-copy";
import { INCEPTION_COPY } from "@/lib/inception-copy";

import { auditRows } from "./fixtures/guidance-audit";
import { SCREENS } from "./guidance-screens";

/**
 * 03-guidance rule 5, `density.budget.test.tsx` (M10d): each audited screen in
 * its fixture state, hints closed, folds closed.
 *
 * - B1: at most one lede (`data-copy="lede"`), one sentence, at most 130
 *   characters, except where the per-screen header table of 03-guidance fixes a
 *   longer sentence (`LONG_LEDE`).
 * - B2: at most 4 cards outside the folds, counted by the distinct `data-card`
 *   names the screens give their cards (so a card the build did not name is not
 *   counted); only on Explore and Review (question 3: the other screens are
 *   folded after the researcher has looked at these two).
 * - B4: at most 6 hint buttons reachable without opening a fold.
 * - B5: exactly one primary action (`data-variant="primary"`, button or link) and
 *   at most one gate.
 * - B6: no sentence the audit moved behind a hint (a HINT row's text) is in the
 *   page flow. Help text the audit never covered is not detected here.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/** Ledes the per-screen table of 03-guidance fixes at more than 130 characters (rule 2 says "about 130"). */
const LONG_LEDE: Record<string, number> = { "04 Shape": 170 };
/**
 * Over the B4 budget of 6, as built, waiting for the researcher (decision 2026-11-19 M10d, item 3):
 * Explore's pool state repeats the search controls (mode, query, order) for a new search, and
 * Plan's Limits card has one hint per key line. Each number here is the screen's count today; it
 * may only go down.
 */
const HINT_BUDGET: Record<string, number> = { "02 Explore (pool)": 9, "02 Explore (thin pool)": 9, "01 Plan": 7 };
const EN: Record<string, string> = { ...(INCEPTION_COPY.en as Record<string, string>), ...(DISCOVERY_COPY.en as Record<string, string>) };
const ROWS = auditRows();
const STAYS = new Set(ROWS.filter((r) => r.decision === "STAYS").flatMap((r) => r.keys));
const HINT_TEXT = new Set(
  ROWS.filter((r) => r.decision === "HINT")
    .flatMap((r) => r.keys)
    .filter((k) => !STAYS.has(k))
    .map((k) => (EN[k] ?? "").split("{")[0].replace(/\s+/g, " ").trim())
    .filter((t) => t.split(" ").length >= 4),
);
const FOLDED_FIRST = new Set(["02 Explore (first search)", "02 Explore (pool)", "02 Explore (thin pool)", "06 Review"]);

const open = (el: Element) => !el.closest("details:not([open])") || el.closest("details:not([open]) > summary") !== null;

describe("density.budget", () => {
  for (const s of SCREENS) {
    it(`${s.name}: one lede sentence, the card, hint and primary budgets, no inline help`, async () => {
      await s.mount();
      const ledes = [...document.querySelectorAll<HTMLElement>('[data-copy="lede"]')];
      expect(ledes.length).toBeLessThanOrEqual(1);
      for (const lede of ledes) {
        // The lede's own text, without the name of a hint button inside it.
        const clone = lede.cloneNode(true) as HTMLElement;
        clone.querySelectorAll("[data-hint]").forEach((h) => h.remove());
        const text = (clone.textContent ?? "").replace(/\s+/g, " ").trim();
        expect(text.split(/(?<=[.!?؟])\s+/).length, `lede "${text}"`).toBe(1);
        expect(text.length, `lede "${text}"`).toBeLessThanOrEqual(LONG_LEDE[s.name] ?? 130);
      }
      if (FOLDED_FIRST.has(s.name)) {
        const cards = new Set([...document.querySelectorAll<HTMLElement>("[data-card]")].filter(open).map((el) => el.dataset.card));
        expect([...cards].length, [...cards].join(", ")).toBeLessThanOrEqual(4);
      }
      const hints = [...document.querySelectorAll("[data-hint-button]")].filter(open);
      expect(hints.length).toBeLessThanOrEqual(HINT_BUDGET[s.name] ?? 6);
      const primaries = [...document.querySelectorAll('[data-variant="primary"]')];
      expect(primaries.map((p) => p.textContent)).toHaveLength(1);
      expect(document.querySelectorAll("section.border-dashed.border-brand").length).toBeLessThanOrEqual(1);
      // B6: no paragraph in the page flow says what the audit moved behind a hint (a disabled
      // action's reason, an error or a status is not help and stays).
      const inline = [...document.querySelectorAll("p, dd, span")]
        .filter((el) => !el.closest("[data-hint-body]") && el.children.length === 0)
        .map((el) => (el.textContent ?? "").replace(/\s+/g, " ").trim())
        .filter((text) => [...HINT_TEXT].some((h) => text.startsWith(h)));
      expect(inline).toEqual([]);
    }, 20000);
  }
});
