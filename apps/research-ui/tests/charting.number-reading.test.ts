import { describe, expect, it } from "vitest";

import type { FormColumn } from "@/lib/charting-api";
import { valueOfDraft } from "@/lib/charting-logic";

/** M12a Part B, review finding 3: a number the screen cannot read for sure is asked again, never guessed. */
const NUMBER = { column_id: "n", name: "Images", definition: "", type: "number", options: [], required: false } as unknown as FormColumn;

describe("charting number reading", () => {
  it("reads plain numbers, a space as thousands and a decimal comma", () => {
    expect(valueOfDraft(NUMBER, "1260")).toEqual({ kind: "value", value: 1260 });
    expect(valueOfDraft(NUMBER, "1 260")).toEqual({ kind: "value", value: 1260 });
    expect(valueOfDraft(NUMBER, "2,5")).toEqual({ kind: "value", value: 2.5 });
    expect(valueOfDraft(NUMBER, "2.5")).toEqual({ kind: "value", value: 2.5 });
  });

  it("asks again for a comma before three digits, two commas, or a hexadecimal", () => {
    for (const text of ["1,260", "12,345", "1,260,000", "0x10"]) {
      expect(valueOfDraft(NUMBER, text), text).toEqual({ kind: "notANumber" });
    }
  });
});
