import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { GUIDANCE_COPY, guidanceT } from "@/lib/guidance-copy";

/** 03-guidance "Copy" (M10d): keys and placeholders in en, fr and ar; no literal accessible name. */

const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

describe("guidance-copy", () => {
  it("has every key in en, fr and ar, with the same placeholders, none empty", () => {
    const keys = Object.keys(GUIDANCE_COPY.en);
    expect(keys).toContain("guidance.hint.open");
    expect(keys).toContain("guidance.recommended");
    for (const locale of ["fr", "ar"] as const) {
      expect(Object.keys(GUIDANCE_COPY[locale]).sort()).toEqual([...keys].sort());
      for (const key of keys) {
        const en = GUIDANCE_COPY.en[key as keyof typeof GUIDANCE_COPY.en];
        const other = GUIDANCE_COPY[locale][key as keyof typeof GUIDANCE_COPY.en];
        expect(other.trim(), `${locale} ${key}`).not.toBe("");
        expect(holes(other), `${locale} ${key}`).toEqual(holes(en));
      }
    }
  });

  it("fails loudly on a missing value", () => {
    expect(() => guidanceT("en")("guidance.hint.open")).toThrow(/needs \{label\}/);
    expect(guidanceT("en")("guidance.recommended.by", { source: "check X" })).toBe("Recommended · check X");
  });

  it("writes no literal accessible name in the guidance components (N9)", () => {
    const source = readFileSync(resolve(process.cwd(), "components/ui/guidance.tsx"), "utf-8");
    expect(source).not.toMatch(/(aria-label|title|alt|placeholder)="/);
    expect(source).not.toMatch(/\bAI\b/);
  });
});
