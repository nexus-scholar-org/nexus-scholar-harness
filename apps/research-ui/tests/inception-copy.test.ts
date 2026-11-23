import { describe, expect, it } from "vitest";

import { sourceText } from "@/lib/inception-copy";

/** The inception copy (M4b): an unknown source falls back to the engine's label. */

describe("inception.copy", () => {

  it("falls back to the engine's label for a source it does not know", () => {
    expect(sourceText("fr", "manual", "", "typed by you")).toBe("Saisi par vous");
    expect(sourceText("fr", "something_new", "", "engine words")).toBe("engine words");
  });
});
