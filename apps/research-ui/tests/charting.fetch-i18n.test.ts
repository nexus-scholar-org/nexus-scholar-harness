import { describe, expect, it } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { CHARTING_REFUSAL_CODES, cc, refusalWords } from "@/lib/charting-copy";

/**
 * Spec 03 "Copy" (M12a Part F): every `charting.fetch.*` key in en, fr and ar
 * with the same holes; the five refusal keys and their codes; the spec's English
 * words; the names of settings and hosts kept as they are; no literal
 * accessible name (N9).
 */

const CODES = ["MAILTO_NOT_SET", "FETCH_ALREADY_ACTIVE", "FETCH_NOT_PENDING", "DISCARD_REASON_REQUIRED", "FETCH_FILE_WAITING"] as const;

describe("charting.fetch-i18n", () => {
  it("has the five refusal codes, each with its own words in every language", () => {
    for (const code of CODES) {
      expect(CHARTING_REFUSAL_CODES).toContain(code);
      for (const locale of SUPPORTED_LOCALES) {
        expect(refusalWords(locale, code), `${locale} ${code}`).not.toBe(refusalWords(locale, "NOT_A_CODE"));
      }
    }
    expect(refusalWords("en", "MAILTO_NOT_SET")).toBe(
      "A look-up needs a contact e-mail: the open-access services ask for it on every request. Set SCHOLAR_MAILTO for the console (environment or .env) and start it again. Nothing was sent.",
    );
    expect(refusalWords("en", "FETCH_ALREADY_ACTIVE")).toBe("A look-up is already running for this workspace. Wait for it to finish, or cancel it.");
    expect(refusalWords("en", "FETCH_NOT_PENDING")).toBe("That file is not waiting for you any more. Reload the table.");
    expect(refusalWords("en", "DISCARD_REASON_REQUIRED")).toBe("Choose one reason first, then discard.");
    expect(refusalWords("en", "FETCH_FILE_WAITING")).toBe("A fetched file is waiting on this row. Confirm it or discard it first.");
  });

  it("keeps the spec's English words", () => {
    expect(cc("en", "charting.table.show.toConfirm")).toBe("Fetched, to confirm");
    expect(cc("en", "charting.help.bodyFetch")).toBe("L look up open-access copies · C confirm the fetched file · D discard it, then a number · O open it");
    expect(cc("en", "charting.fetch.plan.title", { n: 214 })).toBe("Look up open-access copies of 214 records?");
    expect(cc("en", "charting.fetch.plan.unpaywall", { email: "you@example.org", n: 177 })).toBe("Asks Unpaywall with your contact e-mail you@example.org, for the 177 records with a DOI.");
    expect(cc("en", "charting.fetch.run.counts", { found: 12, downloaded: 9, failed: 2, errors: 3 })).toBe("12 found · 9 downloaded · 2 failed checks · 3 errors");
    expect(cc("en", "charting.fetch.run.interrupted", { reached: 88, total: 214 })).toBe(
      "The last look-up stopped after 88 of 214 records, probably because the console was closed. What it reached is kept. Look up the rest with L.",
    );
    expect(cc("en", "charting.fetch.error.lookupFailed", { n: 1, service: "Unpaywall", status: 429 })).toBe("1 × the lookup failed: Unpaywall answered HTTP 429");
    expect(cc("en", "charting.fetch.tried.notPaywall")).toBe("This is not a paywall determination.");
    expect(cc("en", "charting.fetch.tip.identity")).toBe(
      "The check looks for the DOI or the title words on the first two pages. It cannot tell you the paper is the right one. Open the file to be sure.",
    );
    expect(() => cc("en", "charting.fetch.plan.title")).toThrow(/needs \{n\}/);
  });

  it("never translates the names of settings, services and versions", () => {
    for (const locale of SUPPORTED_LOCALES) {
      expect(cc(locale, "charting.fetch.plan.openalexNot")).toContain("SCHOLAR_OPENALEX_KEY");
      expect(cc(locale, "charting.refusal.MAILTO_NOT_SET")).toContain("SCHOLAR_MAILTO");
      expect(cc(locale, "charting.fetch.service.unpaywall")).toBe("Unpaywall");
      expect(cc(locale, "charting.fetch.service.openalex")).toBe("OpenAlex");
      expect(cc(locale, "charting.fetch.service.arxiv")).toBe("arXiv");
      expect(cc(locale, "charting.fetch.version.arxiv", { n: 2 })).toContain("arXiv v2");
    }
  });
});
