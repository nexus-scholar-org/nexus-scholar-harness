import { describe, expect, it } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { stateCopy } from "@/lib/screening-states";

/** The discovery copy (M3c-screens): an unknown refusal code renders as itself. */

describe("discovery.copy", () => {
  it("renders an unknown code as itself, never as another card", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const card = stateCopy(locale, "SOMETHING_NEW_FROM_THE_ENGINE");
      expect(card.known).toBe(false);
      expect(card.code).toBe("SOMETHING_NEW_FROM_THE_ENGINE");
    }
  });
});
