import { describe, expect, it } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { DISCOVERY_COPY, type DiscoveryCopyKey } from "@/lib/discovery-copy";
import { stateCopy } from "@/lib/screening-states";

/** The discovery copy (M3c-screens): every key in every locale, the same placeholders, every refusal a known card. */

const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

const CODES = [
  "PROTOCOL_MISSING", "PROTOCOL_INVALID", "PROTOCOL_CHANGED_SINCE_RUN", "PROTOCOL_CHANGED_SINCE_SNAPSHOT", "MAILTO_NOT_SET",
  "DISCOVERY_JOB_ACTIVE", "DISCOVERY_JOB_NOT_FOUND", "RUN_NOT_FOUND", "RECALL_NOT_RUN", "DEDUP_NOT_RUN", "SEEDS_INVALID",
  "CAP_INVALID", "PROVIDER_UNKNOWN", "STAGED_IMPORT_PENDING", "BATCHES_INCOMPLETE", "PROVIDERS_FAILED", "DISCOVERY_FAILED",
  "ACCEPT_CORPUS_REFUSED", "VERIFIED_EXISTS", "CORPUS_ALREADY_ACCEPTED", "NOTHING_STAGED",
];

describe("discovery.copy", () => {
  it("carries every English key in French and Arabic, with the same placeholders", () => {
    const keys = Object.keys(DISCOVERY_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(DISCOVERY_COPY[locale]).sort(), locale).toEqual(keys);
      for (const [key, en] of Object.entries(DISCOVERY_COPY.en)) {
        const text = DISCOVERY_COPY[locale][key as DiscoveryCopyKey];
        expect(text, `${locale}.${key}`).toBeTruthy();
        expect(placeholders(text), `${locale}.${key}`).toEqual(placeholders(en));
      }
    }
  });

  it("gives every discovery refusal code a known card in every locale, with a title and a body", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const code of CODES) {
        const card = stateCopy(locale, code);
        expect(card.known, `${locale} ${code}`).toBe(true);
        expect(card.title, `${locale} ${code}`).toBeTruthy();
        expect(card.body, `${locale} ${code}`).toBeTruthy();
      }
    }
  });

  it("renders an unknown code as itself, never as another card", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const card = stateCopy(locale, "SOMETHING_NEW_FROM_THE_ENGINE");
      expect(card.known).toBe(false);
      expect(card.code).toBe("SOMETHING_NEW_FROM_THE_ENGINE");
    }
  });

  it("prints the SCHOLAR_MAILTO line with the variable name untranslated in every locale", () => {
    expect(DISCOVERY_COPY.en["mailto.line"]).toBe("SCHOLAR_MAILTO=<your email>");
    for (const locale of SUPPORTED_LOCALES) {
      expect(DISCOVERY_COPY[locale]["mailto.line"].startsWith("SCHOLAR_MAILTO=")).toBe(true);
      expect(stateCopy(locale, "MAILTO_NOT_SET").command).toBe("SCHOLAR_MAILTO=<your email>");
    }
  });
});
