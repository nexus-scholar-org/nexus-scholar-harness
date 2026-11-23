
import { describe, expect, it } from "vitest";

import { guidanceT } from "@/lib/guidance-copy";

/** 03-guidance "Copy" (M10d): a missing value fails loudly. */


describe("guidance-copy", () => {

  it("fails loudly on a missing value", () => {
    expect(() => guidanceT("en")("guidance.hint.open")).toThrow(/needs \{label\}/);
    expect(guidanceT("en")("guidance.recommended.by", { source: "check X" })).toBe("Recommended · check X");
  });
});
