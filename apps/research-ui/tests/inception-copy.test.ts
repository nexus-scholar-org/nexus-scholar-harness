import { describe, expect, it } from "vitest";

import { SUPPORTED_LOCALES } from "@/i18n";
import { INCEPTION_COPY, sourceText } from "@/lib/inception-copy";
import { inceptionStateKey, stateCopy } from "@/lib/screening-states";

/** The inception copy (M4b): every key in every locale, the same placeholders, every refusal a sentence. */

const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

describe("inception.copy", () => {
  it("carries every English key in French and Arabic, with the same placeholders", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const [key, en] of Object.entries(INCEPTION_COPY.en)) {
        const text = INCEPTION_COPY[locale][key as keyof (typeof INCEPTION_COPY)["en"]];
        expect(text, `${locale}.${key}`).toBeTruthy();
        expect(placeholders(text), `${locale}.${key}`).toEqual(placeholders(en));
      }
    }
  });

  it("gives every inception refusal code a known card in every locale", () => {
    const codes = [
      "DRAFT_ID_INVALID", "DRAFT_NOT_FOUND", "DRAFT_UNREADABLE", "DRAFT_EXISTS", "DRAFT_CONFLICT", "DRAFT_EMITTED", "DRAFT_INVALID",
      "DRAFT_INCOMPLETE", "STEP_UNKNOWN", "CRITERIA_UNDECIDED", "CRITERIA_MISSING", "INTENT_INVALID", "SCREENING_BOUND",
      "CONFIRMATION_MISMATCH", "WORKSPACE_EXISTS", "WORKSPACE_ROOT_UNAVAILABLE", "WORKSPACE_TITLE_INVALID", "WORKSPACE_PATH_REFUSED",
      "WORKSPACE_JOB_ACTIVE", "ARCHIVE_INCOMPLETE",
    ];
    for (const locale of SUPPORTED_LOCALES) {
      for (const code of codes) expect(stateCopy(locale, code).known, `${locale} ${code}`).toBe(true);
    }
  });

  it("gives every recon refusal of Explore and Direction its inception card in every locale (M4d)", () => {
    const codes = [
      "MAILTO_NOT_SET", "RECON_JOB_ACTIVE", "POOL_EMPTY", "PROVIDERS_FAILED", "RECON_FAILED", "RECON_NO_POOL", "RECON_SESSION_NOT_FOUND",
      "RECON_SESSION_INVALID", "RECON_JOB_NOT_FOUND", "POOL_TOO_SMALL", "NO_DIRECTION", "DIRECTION_UNKNOWN", "NARROW_BUDGET_SPENT",
      "STALE_BINDING", "TERM_EMPTY",
    ];
    for (const locale of SUPPORTED_LOCALES) {
      for (const code of codes) expect(stateCopy(locale, inceptionStateKey(code)).known, `${locale} ${code}`).toBe(true);
    }
    // The three codes discovery and screening also use keep their own cards there.
    expect(stateCopy("en", "STALE_BINDING").title).toBe("Protocol changed");
    expect(stateCopy("en", inceptionStateKey("STALE_BINDING")).title).toBe("The direction was chosen on a pool or a scope that no longer matches");
    expect(stateCopy("en", "MAILTO_NOT_SET").title).not.toBe(stateCopy("en", inceptionStateKey("MAILTO_NOT_SET")).title);
  });

  it("retires the not-built step tag and the recon note (M4d)", () => {
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(INCEPTION_COPY[locale])).not.toContain("step.comingWithRecon");
      expect(Object.keys(INCEPTION_COPY[locale])).not.toContain("recon.note");
    }
  });

  it("falls back to the engine's label for a source it does not know", () => {
    expect(sourceText("fr", "manual", "", "typed by you")).toBe("Saisi par vous");
    expect(sourceText("fr", "something_new", "", "engine words")).toBe("engine words");
  });
});
