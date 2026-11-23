
import { cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SCREENS } from "./guidance-screens";

/**
 * 03-guidance "Acceptance tests", `guidance.never-hidden.test.tsx` (M10d): a
 * warning is never inside a hint. Rendered: no alert, state card, blocked or
 * unclear badge, check, provenance or gate element sits in a hint panel. Source:
 * no key the audit keeps visible as a refusal, warning, check result,
 * provenance or gate text (V1, V2, V3, V5, V6), and no screening-state key, is
 * passed as a hint's `textKey`.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const NEVER = '[role="alert"], [data-state], [data-role="blocked"], [data-role="unclear"], [data-check], [data-provenance], [data-gate]';

describe("guidance.never-hidden", () => {
  for (const s of SCREENS) {
    it(`${s.name}: no warning, check or gate element is inside a hint`, async () => {
      await s.mount();
      const inside = [...document.querySelectorAll(NEVER)].filter((el) => el.closest("[data-hint-body]"));
      expect(inside.map((el) => el.outerHTML.slice(0, 120))).toEqual([]);
      // A hint panel holds text only: no element of any kind.
      for (const body of document.querySelectorAll("[data-hint-body]")) expect(body.children.length).toBe(0);
      // Rule 1.7: each hint has a name of its own on the screen, and no group, radio group or
      // fieldset takes a hint's "About …" into its name (review M10d round 2, finding 3).
      const names = [...document.querySelectorAll("[data-hint-button]")].map((b) => b.getAttribute("aria-label") ?? "");
      expect(names.filter((n, i) => names.indexOf(n) !== i), "two hints with one name").toEqual([]);
      for (const group of document.querySelectorAll('fieldset, [role="group"], [role="radiogroup"]')) {
        const ids = (group.getAttribute("aria-labelledby") ?? "").split(/\s+/).filter(Boolean);
        const name = ids.length
          ? ids.map((id) => document.getElementById(id)?.textContent ?? "").join(" ")
          : group.getAttribute("aria-label") ?? [...group.children].filter((c) => c.tagName === "LEGEND").map((l) => [l.textContent ?? "", ...[...l.querySelectorAll("[aria-label]")].map((e) => e.getAttribute("aria-label"))].join(" ")).join(" ");
        expect(name, `a group named by a hint: ${name}`).not.toMatch(/About /);
      }
      // A closed fold holds no alert or state card, and a blocked or unclear item inside it is
      // named in its summary by a badge of the same role (rule 4; review M10d, finding 2).
      const closed = [...document.querySelectorAll<HTMLDetailsElement>("details[data-fold]")].filter((d) => !d.open);
      for (const fold of closed) {
        const body = [...fold.children].filter((c) => c.tagName !== "SUMMARY");
        const inBody = (sel: string) => body.flatMap((c) => [...c.querySelectorAll(sel)]);
        expect(inBody('[role="alert"], [data-state]').length, "an alert inside a closed fold").toBe(0);
        for (const role of ["blocked", "unclear"]) {
          if (inBody(`[data-role="${role}"]`).length) expect(fold.querySelector(`summary [data-role="${role}"]`), `${role} item hidden in a fold without a summary badge`).not.toBeNull();
        }
      }
    }, 20000);
  }
});
