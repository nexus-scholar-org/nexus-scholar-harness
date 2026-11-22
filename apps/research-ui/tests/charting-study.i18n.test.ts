import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { CHARTING_COPY, cc } from "@/lib/charting-copy";

/**
 * Spec 02 "Copy" and spec 01's Part B keys (M12a Part B): the spec's English
 * words, every key in fr and ar, and no literal accessible name in the new files (N9).
 */

describe("charting-study.i18n", () => {
  it("keeps the spec's English words for the one-study view and the Charting view", () => {
    const en = (key: Parameters<typeof cc>[1], values?: Record<string, string | number>) => cc("en", key, values);
    expect(en("charting.study.position", { k: 12, total: 74 })).toBe("Study 12 of 74");
    expect(en("charting.study.back")).toBe("Back to the table");
    expect(en("charting.study.next")).toBe("Next study");
    expect(en("charting.study.fromAbstract")).toBe("Charting from the abstract. This row is counted as having no full text.");
    expect(en("charting.study.excluded", { reason: "EXC-01" })).toBe("Excluded at full text: EXC-01. Change the decision to chart it.");
    expect(en("charting.study.noLongerKept")).toBe("No longer kept at title and abstract. Its values are kept and left out of exports.");
    expect(en("charting.study.archived")).toBe("This study's table belongs to the old protocol.");
    expect(en("charting.study.announce.moved", { k: 13, total: 74 })).toBe("Study 13 of 74. Saved.");
    expect(en("charting.study.tip.notReported")).toBe("Use this when the study does not say. It is a finding, not a blank.");
    expect(en("charting.pilot.suggest")).toBe("Try the form on about five studies, then revise it.");
    expect(en("charting.form.reasonLabel")).toBe("Why does the form change? One sentence.");
    expect(en("charting.form.record")).toBe("Record the amendment");
    expect(en("charting.form.amended", { date: "2026-11-21", who: "researcher:local", change: "renamed", from: "A", to: "B" })).toBe("Amended on 2026-11-21 by researcher:local: renamed, from “A” to “B”.");
    expect(en("charting.next")).toBe("Chart the next study");
    expect(en("charting.cell.whereFrom")).toBe("Where from (page or quote)");
    expect(["text", "one", "several", "yesNo", "number"].map((k) => en(`charting.type.${k}` as Parameters<typeof cc>[1]))).toEqual(["Text", "One of a list", "Several of a list", "Yes or No", "Number"]);
  });

  it("carries every Part B key in fr and ar, translated where English is not a name", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of Object.keys(CHARTING_COPY.en).filter((k) => k.startsWith("charting.study.") || k.startsWith("charting.form.") || k.startsWith("charting.cell.") || k.startsWith("charting.pilot."))) {
        expect((CHARTING_COPY[locale] as Record<string, string>)[key]?.trim(), `${locale} ${key}`).toBeTruthy();
      }
    }
    expect(cc("fr", "charting.study.position", { k: 1, total: 3 })).toBe("Étude 1 sur 3");
    expect(cc("ar", "charting.study.position", { k: 1, total: 3 })).toBe("الدراسة 1 من 3");
    expect(cc("ar", "charting.cell.notReported")).not.toBe(cc("en", "charting.cell.notReported"));
  });

  it("writes no literal aria-label, title, alt or placeholder in the Part B files (N9)", () => {
    for (const file of [
      "components/charting-study.tsx",
      "components/charting-cells.tsx",
      "components/charting-form-panel.tsx",
      "app/[locale]/charting/study/page.tsx",
    ]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});
