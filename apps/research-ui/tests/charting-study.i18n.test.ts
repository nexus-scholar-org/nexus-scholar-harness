import { describe, expect, it } from "vitest";

import { cc } from "@/lib/charting-copy";

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
});
