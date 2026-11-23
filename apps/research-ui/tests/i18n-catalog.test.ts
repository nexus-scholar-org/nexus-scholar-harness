import { describe, expect, it } from "vitest";

import {
  DEFAULT_LOCALE,
  LOCALE_METADATA,
  SUPPORTED_LOCALES,
  isSupportedLocale,
  resolveLocale,
  swapLocale,
  translate,
  MissingMessageError,
  UnmappedTokenError,
  navKey,
  translateParts,
} from "@/i18n";
import en, { type MessageKey } from "@/messages/en";
import { CATALOGS } from "@/messages";

describe("locale resolution", () => {
  it("accepts only the exact, case-sensitive locale codes it ships", () => {
    for (const locale of SUPPORTED_LOCALES) {
      expect(isSupportedLocale(locale)).toBe(true);
    }
    for (const value of ["EN", "Fr", "en-US", "fr-FR", "ar-EG", "en_US", "", " en", "en "]) {
      expect(isSupportedLocale(value), value).toBe(false);
    }
  });

  it("falls back to the default locale for unsupported base locales; case/region variants of supported bases resolve to their base", () => {
    // D-I18N-13B: locale resolution is case-insensitive and falls back to the
    // base language subtag. Supported bases resolve; unsupported bases fall back.
    // Case/region variants of supported bases:
    expect(resolveLocale("EN")).toBe("en");
    expect(resolveLocale("en-US")).toBe("en");
    expect(resolveLocale("ar-EG")).toBe("ar");
    expect(resolveLocale("fr-FR")).toBe("fr");
    // Unsupported bases fall back to default:
    for (const value of ["de", "france", "..", "%2F"]) {
      expect(resolveLocale(value), value).toBe(DEFAULT_LOCALE);
    }
    expect(DEFAULT_LOCALE).toBe("en");
  });

  it("declares the direction and tag per locale, and never a right-to-left one for Latin", () => {
    expect(LOCALE_METADATA.en.dir).toBe("ltr");
    expect(LOCALE_METADATA.fr.dir).toBe("ltr");
    expect(LOCALE_METADATA.ar.dir).toBe("rtl");
    expect(LOCALE_METADATA.ar.tag).toBe("ar-EG");
    // `lang` is the route segment itself, never the BCP-47 tag: `<html lang>` and
    // the URL have to agree.
    for (const locale of SUPPORTED_LOCALES) {
      expect(LOCALE_METADATA[locale].lang).toBe(locale);
      expect(LOCALE_METADATA[locale].tag.startsWith(`${locale}-`)).toBe(true);
    }
  });

  it("gives every locale a non-empty endonym and no locale a translated one", () => {
    for (const locale of SUPPORTED_LOCALES) {
      expect(LOCALE_METADATA[locale].endonym.trim()).not.toBe("");
    }
    // D-I18N-06: the three endonyms are three different strings. If two were
    // equal the selector would show the same word twice in a row.
    const endonyms = SUPPORTED_LOCALES.map((locale) => LOCALE_METADATA[locale].endonym);
    expect(new Set(endonyms).size).toBe(endonyms.length);
  });
});

describe("swapLocale", () => {
  it("replaces the leading locale segment", () => {
    expect(swapLocale("/fr", "ar")).toBe("/ar");
    expect(swapLocale("/fr/evidence", "ar")).toBe("/ar/evidence");
  });

  it("inserts the locale when the path has none", () => {
    expect(swapLocale("/", "ar")).toBe("/ar");
    expect(swapLocale("", "fr")).toBe("/fr");
    expect(swapLocale("/evidence", "fr")).toBe("/fr/evidence");
  });

  it("preserves the query, the fragment and a trailing slash", () => {
    // §5 item 5. These are the exact cases the packet names, plus the trailing
    // slash, which is a *path* suffix and has to survive ahead of the query.
    expect(swapLocale("/fr/evidence?x=1", "ar")).toBe("/ar/evidence?x=1");
    expect(swapLocale("/fr/evidence#chain", "ar")).toBe("/ar/evidence#chain");
    expect(swapLocale("/fr/", "ar")).toBe("/ar/");
    expect(swapLocale("/fr/evidence/?x=1", "ar")).toBe("/ar/evidence/?x=1");
  });

  it("produces a supported locale as the first segment for every input", () => {
    for (const input of ["/", "", "/en", "/fr/a/b", "/de/x", "/en?x=1"]) {
      for (const target of SUPPORTED_LOCALES) {
        const first = swapLocale(input, target).split(/[/?#]/)[1] ?? "";
        expect(isSupportedLocale(first), `${input} -> ${target}`).toBe(true);
      }
    }
  });
});

describe("translate", () => {
  it("returns the catalog value, with no key and no leftover placeholder", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of Object.keys(en) as MessageKey[]) {
        const rendered = translate(locale, key, { requested: "de", available: "a" });
        expect(rendered, `${locale} / ${key}`).not.toContain(key);
        expect(rendered, `${locale} / ${key}`).not.toMatch(/\{[a-zA-Z]/);
        expect(rendered.trim(), `${locale} / ${key}`).not.toBe("");
      }
    }
  });

  it("substitutes a hole in every locale, wherever the translator put it", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const rendered = translate(locale, "notFound.unsupportedLocale", {
        requested: "de",
        available: "en, fr, ar",
      });
      expect(rendered).toContain("de");
      expect(rendered).toContain("en, fr, ar");
      expect(rendered).not.toContain("{requested}");
      expect(rendered).not.toContain("{available}");
    }
  });

  it("renders the long-string probe messages unchanged when expansion is off", () => {
    // The default in `npm test` and in every production build. If this fails,
    // something has made the test-only transform unconditional.
    expect(translate("en", "footer.local")).toBe(en["footer.local"]);
    expect(translate("fr", "notFound.body")).toBe(CATALOGS.fr["notFound.body"]);
  });

  it("throws rather than rendering a key, an empty string, or another language", () => {
    // N3. Each of these is a state where a fallback would look fine on screen and
    // ship a wrong document.
    for (const locale of SUPPORTED_LOCALES) {
      expect(() => translate(locale, "not.a.key" as MessageKey), locale).toThrow(MissingMessageError);
      expect(() => translate(locale, "a11y.skipToMain", { name: "" }), locale).toThrow(
        MissingMessageError,
      );
      expect(() => translate(locale, "notFound.unsupportedLocale", {}), locale).toThrow(
        MissingMessageError,
      );
      expect(
        () => translate(locale, "notFound.unsupportedLocale", { requested: "   ", available: "en" }),
        locale,
      ).toThrow(MissingMessageError);
    }
  });

  it("names the key and the locale in the failure, so the red test says which one", () => {
    try {
      translate("fr", "not.a.key" as MessageKey);
      expect.unreachable("translate must throw for an unknown key");
    } catch (error) {
      expect(error).toBeInstanceOf(MissingMessageError);
      const failure = error as MissingMessageError;
      expect(failure.key).toBe("not.a.key");
      expect(failure.locale).toBe("fr");
      expect(failure.message).toContain("not.a.key");
      expect(failure.message).toContain("fr");
    }
  });
});

describe("navigation keys", () => {

  it("throws UnmappedTokenError for a nav id nobody declared", () => {
    expect(() => navKey("overview")).toThrow(UnmappedTokenError);
  });
});

describe("translateParts", () => {
  it("keeps the substituted value byte-identical to what it was given", () => {
    // D-I18N-02: the reader's own text is never rewritten, and this holds even
    // if the long-string transform is on.
    const requested = "de-AT_x";
    for (const locale of SUPPORTED_LOCALES) {
      const parts = translateParts(locale, "notFound.unsupportedLocale", { requested, available: "en" });
      expect(parts.filter((part) => part.kind === "isolated").map((part) => part.value)).toEqual([requested, "en"]);
    }
  });

  it("keeps the template's own order, without moving either hole", () => {
    // The reason parts come from the template rather than from a search over the
    // rendered string: the interleaving of literals and holes is the
    // translator's sentence structure. The expected literals are derived from
    // the catalog template itself, so this test asserts "no reordering, no lost
    // or duplicated text" rather than any particular language's word order.
    for (const locale of SUPPORTED_LOCALES) {
      const template = CATALOGS[locale]["notFound.unsupportedLocale"];
      const parts = translateParts(locale, "notFound.unsupportedLocale", {
        requested: "de",
        available: "en, fr, ar",
      });

      expect(parts.map((part) => part.kind), locale).toEqual([
        "text",
        "isolated",
        "text",
        "isolated",
        "text",
      ]);
      expect(
        parts
          .filter((part) => part.kind === "text")
          .map((part) => part.value)
          .join("|"),
        locale,
      ).toBe(
        template
          .split(/\{requested\}|\{available\}/)
          .filter((piece) => piece !== "")
          .join("|"),
      );
    }
  });

  it("throws on an unfilled hole rather than rendering a blank", () => {
    expect(() => translateParts("fr", "notFound.unsupportedLocale", {})).toThrow(MissingMessageError);
  });
});