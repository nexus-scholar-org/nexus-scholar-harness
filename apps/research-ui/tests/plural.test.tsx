import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CheckSentence } from "@/components/checks-panel";
import { InceptionCriteria } from "@/components/inception-criteria";
import { InceptionScope } from "@/components/inception-scope";
import { SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CHECKS_COPY } from "@/lib/checks-copy";
import { DISCOVERY_COPY } from "@/lib/discovery-copy";
import { INCEPTION_COPY } from "@/lib/inception-copy";
import { PLURALS, pluralForm, pluralTemplate } from "@/lib/plural";
import { PROPOSALS_COPY } from "@/lib/proposals-copy";
import { checkRow } from "./fixtures/checks-engine";
import { completeDraft, outOfScopeId, proofId } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/** H-ui-findings F4: a count of one reads "1 suggestion", not "1 suggestions"; Arabic has six forms. */

afterEach(() => vi.unstubAllGlobals());

const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).filter((h) => h !== "n").sort();
const catalogs = { ...INCEPTION_COPY, } as Record<Locale, Record<string, string>>;
const general = (locale: Locale, key: string): string =>
  (CHECKS_COPY[locale] as Record<string, string>)[key] ?? (PROPOSALS_COPY[locale] as Record<string, string>)[key] ?? catalogs[locale][key] ?? (DISCOVERY_COPY[locale] as Record<string, string>)[key];

describe("plural forms", () => {
  it("picks the CLDR form of a count in each language", () => {
    expect([0, 1, 2, 5].map((n) => pluralForm("en", n))).toEqual(["other", "one", "other", "other"]);
    expect([0, 1, 2].map((n) => pluralForm("fr", n))).toEqual(["one", "one", "other"]);
    expect([0, 1, 2, 3, 10, 11, 99, 100].map((n) => pluralForm("ar", n))).toEqual(["zero", "one", "two", "few", "few", "many", "many", "other"]);
  });

  it("falls back to the catalog's own string when the table has no form or no count", () => {
    expect(pluralTemplate("en", "proposals.badge", 5, "{n} suggestions")).toBe("{n} suggestions");
    expect(pluralTemplate("en", "proposals.badge", undefined, "{n} suggestions")).toBe("{n} suggestions");
    expect(pluralTemplate("en", "proposals.badge", 1, "{n} suggestions")).toBe("{n} suggestion");
    expect(pluralTemplate("en", "no.such.key", 1, "general")).toBe("general");
  });

  it("lists only keys that exist, with the holes of the general string (n may be spelled out)", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const [key, forms] of Object.entries(PLURALS[locale])) {
        const base = general(locale, key);
        expect(base, `${locale} / ${key} has no catalog string`).toBeTruthy();
        for (const [form, text] of Object.entries(forms)) {
          expect(holes(text), `${locale} / ${key} / ${form}`).toEqual(holes(base));
        }
      }
    }
  });

  it("gives Arabic every count form for the criteria check", () => {
    const forms = PLURALS.ar["checks.CRITERIA_UNDECIDED.sentence"];
    for (const form of ["one", "two", "few", "many", "other"] as const) expect(forms[form], form).toBeTruthy();
    for (const text of Object.values(forms)) {
      expect(text).toContain(INCEPTION_COPY.ar["criteria.accept"]);
      expect(text).toContain(INCEPTION_COPY.ar["criteria.reject"]);
    }
  });
});

describe("plural wording on screen", () => {
  const sentence = (locale: Locale, n: number) => {
    const check = checkRow({ check_id: "CRITERIA_UNDECIDED", step: "criteria", level: "blocker", params: { n }, action: { kind: "step", step: "criteria" } }) as never;
    const { container, unmount } = render(<CheckSentence locale={locale} check={check} />);
    // The sentence slots format numbers for the locale (Arabic-Indic digits in Arabic); compare in Latin digits.
    const text = (container.textContent ?? "").replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660));
    unmount();
    return text;
  };

  it("the criteria check agrees with its count in English, French and Arabic", () => {
    expect(sentence("en", 1)).toBe("1 criterion still needs your decision: Accept or Reject.");
    expect(sentence("en", 3)).toBe("3 criteria still need your decision: Accept or Reject.");
    expect(sentence("fr", 1)).toBe("1 critère attend encore votre décision : Accepter ou Rejeter.");
    expect(sentence("fr", 3)).toBe("3 critères attendent encore votre décision : Accepter ou Rejeter.");
    expect(sentence("ar", 1)).toBe("معيار واحد ما زال ينتظر قرارك: قبول أو رفض.");
    expect(sentence("ar", 2)).toBe("معياران ما زالا ينتظران قرارك: قبول أو رفض.");
    expect(sentence("ar", 5)).toBe("5 معايير ما زالت تنتظر قرارك: قبول أو رفض.");
    expect(sentence("ar", 12)).toBe("12 معيارًا ما زالت تنتظر قرارك: قبول أو رفض.");
    expect(sentence("ar", 100)).toBe("100 معيار ما زالت تنتظر قرارك: قبول أو رفض.");
  });

  it("the step bar says '1 suggestion', and the checks panel '1 check is waiting'", async () => {
    const { engine } = setUp({
      draft: completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } }),
      checks: () => [],
      checksAnswer: (step) => ({
        shape: "checks-v1", scope: { kind: "draft", id: "x", updated_at: "x" }, computed_at: "2026-11-18T10:00:00+00:00", sources: ["check"],
        checks: [], waiting: [{ check_id: "PLAN_NO_CAP", step: "scope", needs: "pool" }], counts: { blocker: 0, warning: 0, note: 0, dismissed: 0 }, partial: [],
        ...(step ? {} : { by_step: { scope: { blocker: 0, warning: 0, note: 0 } } }), ready: true,
      }),
    });
    const real = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        const response = await real(url, init);
        if (!String(url).includes("/proposals") || (init?.method ?? "GET") !== "GET") return response;
        const body = await response.json();
        body.by_step.scope = { open: 1, stale: 0 };
        return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
      }),
    );
    void engine;
    render(<InceptionScope locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-step-suggestions='scope']")?.textContent).toContain("1 suggestion"));
    expect(document.querySelector("[data-step-suggestions='scope']")?.textContent).not.toContain("1 suggestions");
    await waitFor(() => expect(document.querySelector("[data-waiting='pool']")?.textContent).toBe("1 check is waiting for your first search"));
  });

  it("the criteria screen says how many still need you with the right form", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    const line = await screen.findByText(/still needs? you\./);
    const count = Number(/^[0-9]+/.exec(line.textContent ?? "")?.[0]);
    expect(line.textContent).toBe(count === 1 ? "1 still needs you." : `${count} still need you.`);
  });
});
