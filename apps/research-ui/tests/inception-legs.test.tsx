import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LegsList } from "@/components/inception-recon";
import type { Locale } from "@/i18n";
import { inceptionT } from "@/lib/inception-copy";
import type { ReconLeg } from "@/lib/recon-api";

/** The databases asked (spec 02): a database that found nothing says so (M10a, OBS-1b), and shows the query it received. */

function leg(extra: Partial<ReconLeg> = {}): ReconLeg {
  return {
    provider: "openalex",
    status: "ok",
    reported_total: 0,
    fetched: 0,
    cap: 25,
    cap_hit: false,
    error: null,
    error_code: null,
    notes: [],
    ...extra,
  };
}

function row(locale: Locale, l: ReconLeg): HTMLElement {
  const { container } = render(<LegsList locale={locale} legs={[l]} />);
  return container.querySelector(`[data-leg="${l.provider}"]`) as HTMLElement;
}

describe("inception.legs", () => {
  for (const locale of ["en", "ar"] as const) {
    it(`says 0 results, never answered, for a database that found nothing (${locale})`, () => {
      const t = inceptionT(locale);
      const el = row(locale, leg());
      expect(el.textContent).not.toContain(t("explore.legs.ok"));
      expect(el.textContent).toContain(t("explore.legs.zero"));
      expect(el.querySelector('[data-role="include"]')).toBeNull();
      expect(el.querySelector('[data-role="unclear"]')?.textContent).toBe(t("explore.legs.zero"));
      expect(el.querySelector("[data-fetched]")?.textContent).toBe(t("explore.legs.fetchedOf", { fetched: "0", total: "0" }));
    });
  }

  it("keeps answered for a database that found records", () => {
    const t = inceptionT("en");
    const el = row("en", leg({ fetched: 6, reported_total: 18 }));
    expect(el.querySelector('[data-role="include"]')?.textContent).toBe(t("explore.legs.ok"));
    expect(el.textContent).not.toContain(t("explore.legs.zero"));
  });

  it("says 0 results when the database reported no total and nothing was fetched", () => {
    const t = inceptionT("en");
    const el = row("en", leg({ reported_total: null, fetched: 0 }));
    expect(el.querySelector('[data-role="unclear"]')?.textContent).toBe(t("explore.legs.zero"));
    expect(el.textContent).not.toContain(t("explore.legs.ok"));
  });

  it("keeps answered, with its counts, when the database reported a total but nothing was fetched", () => {
    const t = inceptionT("en");
    const el = row("en", leg({ reported_total: 40, fetched: 0 }));
    expect(el.querySelector('[data-role="include"]')?.textContent).toBe(t("explore.legs.ok"));
    expect(el.textContent).not.toContain(t("explore.legs.zero"));
    expect(el.querySelector("[data-fetched]")?.textContent).toBe(t("explore.legs.fetchedOf", { fetched: "0", total: "40" }));
  });

  it("still says failed, never 0 results, for a failed database", () => {
    const t = inceptionT("en");
    const el = row("en", leg({ status: "failed", reported_total: null, fetched: 0, error: "HTTPStatusError: 503", error_code: "PROVIDER_UNAVAILABLE" }));
    expect(el.querySelector('[data-role="blocked"]')?.textContent).toBe(t("explore.legs.failed"));
    expect(el.textContent).not.toContain(t("explore.legs.zero"));
  });

  it("shows the exact query the database received, left to right; nothing when absent", () => {
    const t = inceptionT("ar");
    const el = row("ar", leg({ provider: "arxiv", executed_query: "all:uav AND all:weed" }));
    const value = el.querySelector("[data-executed-query]") as HTMLElement;
    expect(value.querySelector('[dir="ltr"]')?.textContent).toBe("all:uav AND all:weed");
    // A DataCell: monospace, wrapping anywhere.
    expect(value.querySelector('[dir="ltr"]')?.className).toMatch(/font-mono/);
    expect(value.querySelector('[dir="ltr"]')?.className).toMatch(/overflow-wrap:anywhere/);
    expect(el.textContent).toContain(t("explore.legs.col.query"));

    const bare = row("ar", leg({ provider: "crossref", executed_query: null }));
    expect(bare.querySelector("[data-executed-query]")).toBeNull();
    expect(bare.textContent).not.toContain(t("explore.legs.col.query"));
  });
});
