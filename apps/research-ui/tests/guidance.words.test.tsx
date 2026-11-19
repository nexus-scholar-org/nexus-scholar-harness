import { writeFileSync } from "node:fs";

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, describe, expect, it, vi } from "vitest";

import { SCREENS } from "./guidance-screens";
import { visibleWords } from "./guidance-words";

/**
 * M10d measurement (record `docs/roadmap/milestones/M10d-lighter-screens.md`,
 * "Measurement"): the visible words of each audited screen in one fixture state.
 * Set `GUIDANCE_WORDS_OUT` to a file path to write the counts as JSON.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const counts: Record<string, number> = {};

afterAll(() => {
  const out = process.env.GUIDANCE_WORDS_OUT;
  if (out) writeFileSync(out, JSON.stringify(counts, null, 2));
});

describe("guidance.words", () => {
  for (const s of SCREENS.filter((x) => x.measure !== false)) {
    it(`counts the visible words of ${s.name} (${s.state})`, async () => {
      await s.mount();
      counts[s.name] = visibleWords().length;
      expect(counts[s.name]).toBeGreaterThan(5);
    }, 20000);
  }
});
