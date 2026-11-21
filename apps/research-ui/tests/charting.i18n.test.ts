import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { CHARTING_COPY, cc } from "@/lib/charting-copy";

/** Spec 01 "Copy" and DoD 8: every key in en, fr and ar with the same holes; no literal accessible name (N9). */

const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

describe("charting.i18n", () => {
  it("carries every key in en, fr and ar, non-empty, with the same holes", () => {
    const en = CHARTING_COPY.en as Record<string, string>;
    for (const locale of SUPPORTED_LOCALES) {
      const other = CHARTING_COPY[locale] as Record<string, string>;
      expect(Object.keys(other).sort(), locale).toEqual(Object.keys(en).sort());
      for (const [key, text] of Object.entries(en)) {
        expect(other[key]?.trim(), `${locale} ${key}`).toBeTruthy();
        expect(holes(other[key]), `${locale} ${key}`).toEqual(holes(text));
      }
    }
  });

  it("keeps the spec's English words for the Full text view", () => {
    expect(cc("en", "charting.table.title")).toBe("Charting");
    expect(cc("en", "charting.table.link")).toBe("Chart the included studies");
    expect(cc("en", "charting.bulk.confirm", { n: 23, status: "Retrieved" })).toBe("Mark 23 records as Retrieved? Enter to confirm · Esc to cancel");
    expect(cc("en", "charting.offline", { time: "14:32" })).toBe("The console is not answering. Nothing is lost; last change saved at 14:32.");
    expect(cc("en", "charting.notRetrieved.noAccess")).toBe("No access or paywalled");
    expect(cc("en", "charting.noLongerKept")).toBe("No longer kept at title and abstract");
    expect(() => cc("en", "charting.new")).toThrow(/needs \{date\}/);
  });

  it("writes no literal aria-label, title, alt or placeholder (N9)", () => {
    for (const file of ["components/charting-page.tsx", "app/[locale]/charting/page.tsx", "lib/charting-copy.ts", "lib/charting-api.ts", "lib/charting-logic.ts"]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});
