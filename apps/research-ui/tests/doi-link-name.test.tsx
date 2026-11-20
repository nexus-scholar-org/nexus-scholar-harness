import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DoiLink } from "@/components/inception-recon";

/** H-run-small-fixes, finding 6: a DOI link without a title was named ", DOI 10.…". */
describe("DoiLink name", () => {
  it.each(["en", "fr", "ar"] as const)("never starts with a separator when there is no title (%s)", (locale) => {
    render(<DoiLink locale={locale} doi="10.1/abc" />);
    const name = screen.getByRole("link").getAttribute("aria-label") ?? "";
    expect(name.startsWith("DOI 10.1/abc")).toBe(true);
  });

  it("keeps the title first when there is one", () => {
    render(<DoiLink locale="en" doi="10.1/abc" title="Weed maps" />);
    expect(screen.getByRole("link").getAttribute("aria-label")).toMatch(/^Weed maps, DOI 10\.1\/abc/);
  });
});
