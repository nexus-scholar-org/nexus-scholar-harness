import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionScope } from "@/components/inception-scope";
import { localDate, localStamp } from "@/lib/local-time";
import { completeDraft } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/** H-ui-findings F6: engine instants are shown on the researcher's clock, with the ISO instant kept. */

const zone = process.env.TZ;
afterEach(() => {
  vi.unstubAllGlobals();
  if (zone === undefined) delete process.env.TZ;
  else process.env.TZ = zone;
});

describe("local time", () => {
  it("prints the instant in the browser's zone, across a date line", () => {
    process.env.TZ = "Asia/Tokyo";
    expect(localStamp("2026-11-19T06:17:00+00:00")).toBe("2026-11-19 15:17");
    expect(localStamp("2026-11-19T23:30:00Z")).toBe("2026-11-20 08:30");
    expect(localDate("2026-11-19T23:30:00Z")).toBe("2026-11-20");
    process.env.TZ = "Pacific/Honolulu";
    expect(localStamp("2026-11-19T06:17:00+00:00")).toBe("2026-11-18 20:17");
    process.env.TZ = "Europe/Paris";
    expect(localStamp("2026-11-19T06:17:00+00:00")).toBe("2026-11-19 07:17");
  });

  it("reads a timestamp with no zone as UTC, and shows an unreadable one as it came", () => {
    process.env.TZ = "Europe/Paris";
    expect(localStamp("2026-11-19T06:17:00")).toBe("2026-11-19 07:17");
    expect(localStamp("not a time")).toBe("not a time");
    expect(localStamp(null)).toBe("");
  });

  it("the draft header shows the local time and keeps the ISO instant in dateTime only", async () => {
    process.env.TZ = "Asia/Tokyo";
    setUp({ draft: completeDraft() });
    render(<InceptionScope locale="en" />);
    const saved = await waitFor(() => {
      const el = document.querySelector("[data-saved] time");
      expect(el).not.toBeNull();
      return el as HTMLTimeElement;
    });
    const iso = saved.getAttribute("datetime") ?? "";
    expect(iso).toMatch(/^2\d{3}-\d\d-\d\dT/);
    // H-run-small-fixes (finding 5): no title: readers announced the raw instant beside the local time.
    expect(saved).not.toHaveAttribute("title");
    expect(saved.textContent).toBe(localStamp(iso));
    expect(screen.getByText(/Draft saved/)).toBeInTheDocument();
  });
});
