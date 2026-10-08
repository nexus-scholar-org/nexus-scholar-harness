import { describe, expect, it } from "vitest";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  DEFAULT_LOCALE,
  LOCALE_METADATA,
  SUPPORTED_LOCALES,
  isSupportedLocale,
  placeholdersOf,
  resolveLocale,
  swapLocale,
  translate,
  MissingMessageError,
  UnmappedTokenError,
  evidenceKindKey,
  navKey,
  stateKey,
  countKey,
  phaseKey,
  phaseDescriptionKey,
  translateParts,
} from "@/i18n";
import en, { type MessageKey } from "@/messages/en";
import { CATALOGS } from "@/messages";
import type { EvidenceNode, WorkflowState } from "@/lib/contracts";
import type { OverviewCountField, ProjectOverviewPhase } from "@/lib/project-state";

/**
 * Catalog integrity (packet UI-01d, N1-N8).
 *
 * These are the mechanical checks that keep three catalogs describing one
 * product: identical key sets, identical holes, no empty string, no raw token
 * leaking into a translated catalog, and one deliberately language-independent
 * brand string. None of them can tell you whether a French sentence reads well -
 * that is H1/H2 in `GATES.md`, and a human gate - but every one of them catches
 * the failure that a build should never ship.
 */
describe("catalog parity", () => {
  it("ships exactly the keys the packets inventory, in every locale", () => {
    // 42 keys at UI-01d, +32 in packet UI-02's state model = 74. The number is
    // asserted rather than trusted; `messages/en.ts`'s header states the same
    // figure, and `docs/I18N.md` §3 repeats it.
    const expected = Object.keys(en).sort();

    expect(expected).toHaveLength(74);
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(CATALOGS[locale]).sort()).toEqual(expected);
    }
  });

  it("declares the key set once, in the catalog index", () => {
    // `MESSAGE_KEYS` is what `translate` accepts, so it must be exactly the
    // English key set: a key that exists only in a translation would be
    // unreachable, and one that exists only in English would be renderable in no
    // locale at all.
    const keys = Object.keys(en) as MessageKey[];
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("gives every key a non-empty value in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const [key, value] of Object.entries(CATALOGS[locale])) {
        expect(typeof value, `${locale} / ${key}`).toBe("string");
        expect(value.trim(), `${locale} / ${key}`).not.toBe("");
      }
    }
  });

  it("uses the same holes in every locale, in every message that has any", () => {
    // N4. A translation that dropped `{available}` would render
    // `Available locales: .` - valid JSX, wrong sentence, no error anywhere.
    for (const key of Object.keys(en) as MessageKey[]) {
      const english = placeholdersOf(en[key]);
      for (const locale of SUPPORTED_LOCALES) {
        expect(
          placeholdersOf(CATALOGS[locale][key]),
          `${locale} / ${key} must use the same holes as English`,
        ).toEqual(english);
      }
    }
  });

  it("has no hole that English does not have, in any translation", () => {
    // The other direction: an extra `{typo}` in a translation would render as
    // literal `{typo}` text on screen, forever, because nothing looks up a hole
    // that no template declares.
    const englishHoles = new Set(Object.values(en).flatMap(placeholdersOf));
    for (const locale of SUPPORTED_LOCALES) {
      for (const [key, value] of Object.entries(CATALOGS[locale])) {
        for (const hole of placeholdersOf(value)) {
          expect(englishHoles.has(hole), `${locale} / ${key} invented {${hole}}`).toBe(true);
        }
      }
    }
  });

  it("uses no positional or brace-style placeholder other than {name}", () => {
    // §4.5: no `{0}`, no `%s`, no `{{interpolation}}`, no ICU blocks. A template
    // using any of those renders as literal text here, because `translate`
    // substitutes only `{name}`.
    for (const locale of SUPPORTED_LOCALES) {
      for (const [key, value] of Object.entries(CATALOGS[locale])) {
        expect(value, `${locale} / ${key}`).not.toMatch(/\{\{|\}\}|\{\d|%s|\bnplural\b/);
        expect(value, `${locale} / ${key}`).not.toMatch(/\{(?![a-zA-Z][a-zA-Z0-9_]*\})[^}]*\}/);
      }
    }
  });

  it("keeps the brand identical and untranslated in every catalog", () => {
    // §4.2 B01: the wordmark is not chrome to translate. It is asserted per
    // locale rather than globally, so a translator who changes one catalog sees
    // exactly which one drifted.
    for (const locale of SUPPORTED_LOCALES) {
      expect(CATALOGS[locale]["brand.productName"], locale).toBe("Nexus Scholar");
    }
  });

  it("does not render an English sentence in a non-English catalog", () => {
    // A coarse but real signal: every message is either the brand or differs
    // from its English source, and the number of identical strings is bounded so
    // a wholesale "paste English into fr.ts" fails here instead of shipping.
    for (const locale of SUPPORTED_LOCALES.filter((code) => code !== "en")) {
      const identical = Object.keys(en).filter(
        (key) => CATALOGS[locale][key as MessageKey] === en[key as MessageKey],
      );
      expect(identical, `${locale} still holds ${identical.length} English strings`).toEqual([
        "brand.productName",
      ]);
    }
  });

  it("keeps the translated state and evidence-kind labels distinct from each other", () => {
    // The status badge and the evidence stamp are told apart by text alone (no
    // colour-only signal). If two states or two kinds collapsed to one word in a
    // translation, the four distinct badge styles in
    // `tests/status-badge.test.tsx` would stop being distinguishable.
    for (const locale of SUPPORTED_LOCALES) {
      const states = Object.keys(en)
        .filter((key) => key.startsWith("state."))
        .map((key) => CATALOGS[locale][key as MessageKey]);
      expect(new Set(states).size, locale).toBe(states.length);

      const kinds = Object.keys(en)
        .filter((key) => key.startsWith("evidenceKind."))
        .map((key) => CATALOGS[locale][key as MessageKey]);
      expect(new Set(kinds).size, locale).toBe(kinds.length);
    }
  });
});

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
        const rendered = translate(locale, key, { event: "x", number: "1", requested: "de", available: "a", destination: "Screening" });
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
    expect(translate("en", "overview.traceLede")).toBe(en["overview.traceLede"]);
    expect(translate("fr", "overview.asideBody")).toBe(CATALOGS.fr["overview.asideBody"]);
  });

  it("throws rather than rendering a key, an empty string, or another language", () => {
    // N3. Each of these is a state where a fallback would look fine on screen and
    // ship a wrong document.
    for (const locale of SUPPORTED_LOCALES) {
      expect(() => translate(locale, "not.a.key" as MessageKey), locale).toThrow(MissingMessageError);
      expect(() => translate(locale, "a11y.skipToMain", { name: "" }), locale).toThrow(
        MissingMessageError,
      );
      expect(() => translate(locale, "workflow.stageOrdinal", {}), locale).toThrow(
        MissingMessageError,
      );
      expect(() => translate(locale, "overview.lastEvent", { event: "   " }), locale).toThrow(
        MissingMessageError,
      );
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

describe("controlled vocabulary keys", () => {
  it("maps every canonical token to a key that exists in every catalog", () => {
    const states: WorkflowState[] = ["complete", "active", "waiting", "refused"];
    const kinds: EvidenceNode["kind"][] = ["claim", "chunk", "document", "study", "decision"];

    for (const locale of SUPPORTED_LOCALES) {
      for (const state of states) {
        expect(CATALOGS[locale][stateKey(state)]).toBeTruthy();
      }
      for (const kind of kinds) {
        expect(CATALOGS[locale][evidenceKindKey(kind)]).toBeTruthy();
      }
      for (const id of ["overview", "screening", "evidence", "audit"]) {
        expect(CATALOGS[locale][navKey(id)]).toBeTruthy();
      }
    }
  });

  it("throws UnmappedTokenError for a token nobody decided on", () => {
    // The canonical token sets are frozen by packet UI-01c, so a token with no
    // label is a decision nobody made - a different failure from a lost string,
    // and it must not render as one.
    expect(() => stateKey("done" as WorkflowState)).toThrow(UnmappedTokenError);
    expect(() => evidenceKindKey("quote" as EvidenceNode["kind"])).toThrow(UnmappedTokenError);
    expect(() => navKey("reports")).toThrow(UnmappedTokenError);
  });

  it("maps a token to the same key in every locale, because the token is the data", () => {
    // The token set is canonical; the *label* is translated. A locale whose token
    // resolved to a different key would mean the data itself had been translated.
    for (const state of ["complete", "active", "waiting", "refused"] as WorkflowState[]) {
      const key = stateKey(state);
      expect(CATALOGS.en[key]).toBe(state);
    }
  });
});

describe("state-model vocabulary (packet UI-02)", () => {
  const PHASES: ProjectOverviewPhase[] = [
    "empty",
    "setup",
    "search",
    "screening",
    "extraction",
    "indexing",
    "refusal",
    "degraded",
    "ready",
  ];
  const COUNTS: OverviewCountField[] = [
    "recordsDiscovered",
    "studiesIncluded",
    "decisionsPending",
    "documentsExtracted",
    "chunksIndexed",
  ];
  const ARRIVAL_LABELS = ["overview.recordLoadingLabel", "overview.recordErrorLabel"] as const;

  it("maps every phase and every statistic to a key that exists in every catalog", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const phase of PHASES) {
        expect(CATALOGS[locale][phaseKey(phase)], `${locale} / ${phase}`).toBeTruthy();
        expect(
          CATALOGS[locale][phaseDescriptionKey(phase)],
          `${locale} / ${phase} description`,
        ).toBeTruthy();
      }
      for (const field of COUNTS) {
        expect(CATALOGS[locale][countKey(field)], `${locale} / ${field}`).toBeTruthy();
      }
    }
  });

  it("throws UnmappedTokenError for a phase or a statistic nobody declared", () => {
    // The phase token set is the presentation contract of `lib/project-state.ts`;
    // a token with no label is a decision nobody made, and it must not render as
    // a raw token on screen.
    expect(() => phaseKey("declined")).toThrow(UnmappedTokenError);
    expect(() => phaseDescriptionKey("paused")).toThrow(UnmappedTokenError);
    expect(() => countKey("recordsRead")).toThrow(UnmappedTokenError);
  });

  it("keeps all nine phase words distinct in every locale, and apart from the arrival words", () => {
    // The stamp is text first (GATES §3.7): two phases sharing a word, or a
    // phase colliding with the record-arrival stamps, would make the
    // "distinguishable without colour" claim in
    // `components/project-state-record.tsx` false rather than merely weak.
    for (const locale of SUPPORTED_LOCALES) {
      const phases = PHASES.map((phase) => CATALOGS[locale][phaseKey(phase)]);
      expect(new Set(phases).size, locale).toBe(PHASES.length);

      const arrivals = ARRIVAL_LABELS.map((key) => CATALOGS[locale][key]);
      expect(new Set(arrivals).size, locale).toBe(arrivals.length);
      for (const arrival of arrivals) {
        expect(phases, `${locale} / ${arrival}`).not.toContain(arrival);
      }
    }
  });

  it("keeps the five statistic labels distinct in every locale, and apart from 'unknown'", () => {
    // The value column is read against its row label; two rows claiming the
    // same statistic would make the unknown-versus-zero cell ambiguous, and a
    // label equal to the unknown word would defeat the negative case itself.
    for (const locale of SUPPORTED_LOCALES) {
      const labels = COUNTS.map((field) => CATALOGS[locale][countKey(field)]);
      expect(new Set(labels).size, locale).toBe(COUNTS.length);
      expect(labels, locale).not.toContain(CATALOGS[locale]["counts.unknown"]);
    }
  });
});

describe("translateParts", () => {
  it("separates the translator's words from the fixture value, in template order", () => {
    // `overview.lastEvent` is the only message today whose substituted value must
    // sit in its own element, so this is what the `<bdi>` split depends on.
    for (const locale of SUPPORTED_LOCALES) {
      const parts = translateParts(locale, "overview.lastEvent", { event: "Protocol sealed" });
      expect(parts.map((part) => part.kind)).toEqual(["text", "isolated"]);
      expect(parts[0]?.value).toBe(CATALOGS[locale]["overview.lastEvent"].replace("{event}", ""));
      expect(parts[1]?.value).toBe("Protocol sealed");
    }
  });

  it("keeps the substituted value byte-identical to what it was given", () => {
    // D-I18N-02: the record's own text is never rewritten, and this holds even
    // if the long-string transform is on.
    const fixture = "142 records screened - 14 excluded";
    for (const locale of SUPPORTED_LOCALES) {
      const parts = translateParts(locale, "overview.lastEvent", { event: fixture });
      expect(parts.find((part) => part.kind === "isolated")?.value).toBe(fixture);
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
    expect(() => translateParts("fr", "overview.lastEvent", {})).toThrow(MissingMessageError);
  });
});

describe("byte pins", () => {
  const FILES = [
    {
      path: "lib/mock-project.ts",
      sha256: "af33ce0e6e9372ff4aa5c2d35689580ae8a78402edc521d40e7db0e314f72f2c",
    },
    {
      path: "lib/contracts.ts",
      sha256: "57b3d551a1ae0be4c0aa9cee7d05df47aef973c647f686699301dcbddaa624a2",
    },
    {
      path: "package.json",
      sha256: "5687ea5bda1a92ab38d81d62263aff3f4f93082f7b4cc27ad8cebd847fb3f449",
    },
    {
      path: "package-lock.json",
      sha256: "bcdd05a0a17254fd70f58e3ff45b7419373e9cd072968536c7374387826536e7",
    },
  ] as const;

  for (const { path, sha256 } of FILES) {
    it(`matches SHA-256 for ${path}`, () => {
      const root = resolve(import.meta.dirname, "..");
      const b = readFileSync(resolve(root, path));
      const d = createHash("sha256").update(b).digest("hex");
      expect(d).toBe(sha256);
    });
  }
});