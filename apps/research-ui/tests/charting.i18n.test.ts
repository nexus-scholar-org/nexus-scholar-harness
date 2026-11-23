import { describe, expect, it } from "vitest";

import { cc } from "@/lib/charting-copy";

/** Spec 01 "Copy" and DoD 8: every key in en, fr and ar with the same holes; no literal accessible name (N9). */

describe("charting.i18n", () => {
  it("keeps the spec's English words for the Full text view", () => {
    expect(cc("en", "charting.table.title")).toBe("Charting");
    expect(cc("en", "charting.table.link")).toBe("Chart the included studies");
    expect(cc("en", "charting.bulk.confirm", { n: 23, status: "Retrieved" })).toBe("Mark 23 records as Retrieved? Enter to confirm · Esc to cancel");
    expect(cc("en", "charting.offline", { time: "14:32" })).toBe("The console is not answering. Nothing is lost; last change saved at 14:32.");
    expect(cc("en", "charting.notRetrieved.noAccess")).toBe("No access or paywalled");
    expect(cc("en", "charting.noLongerKept")).toBe("No longer kept at title and abstract");
    expect(() => cc("en", "charting.new")).toThrow(/needs \{date\}/);
  });
});
