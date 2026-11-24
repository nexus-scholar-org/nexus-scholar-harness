/**
 * The copy and source rules of the research UI: `npm run lint:ui` (vitest.lint.config.ts).
 *
 * H-test-diet (2026-11-23): the researcher cut the vitest suite to tests of one component or one screen state.
 * The checks below read files (the en/fr/ar catalogues, component source, the stylesheet, the theme, the price
 * table) instead of rendering anything, so they left the suite; the ones that guard a rule the project decided
 * are kept here, in one file, with their logic unchanged. Each `describe` names the test file it came from.
 * The ones dropped are listed in docs/roadmap/milestones/H-test-diet.md.
 *
 * Paths are read from the app root (`apps/research-ui`), which is where `npm run lint:ui` and
 * `npm --prefix apps/research-ui run lint:ui` run it.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { describe, expect, it } from "vitest";
import { AGREEMENT_COPY } from "@/components/screening-agreement";
import { EXPORT_COPY } from "@/components/screening-export";
import { HOME_COPY } from "@/components/screening-home";
import { IMPORT_COPY } from "@/components/screening-import";
import { PILOT_CARD_COPY } from "@/components/screening-pilot-card";
import { PILOT_COPY } from "@/components/screening-pilot-copy";
import { PREPARE_COPY } from "@/components/screening-prepare";
import { CHEAPEST_ANTHROPIC_MODEL, LISTED_ANTHROPIC_MODELS, PROPOSALS_COPY as SCREENING_PROPOSALS_COPY } from "@/components/screening-proposals";
import { PUBLISH_COPY } from "@/components/screening-publish";
import { currentNavId } from "@/components/site-header";
import { WORKSPACES_COPY } from "@/components/workspaces-screen";
import { type Locale, placeholdersOf, SUPPORTED_LOCALES } from "@/i18n";
import { ADOPTION_COPY, adoptionText } from "@/lib/adoption-copy";
import { cc, CHARTING_COPY, CHARTING_REFUSAL_CODES, type ChartingCopyKey, refusalWords } from "@/lib/charting-copy";
import { CHECK_IDS, CHECKS_COPY } from "@/lib/checks-copy";
import { DISCOVERY_COPY, type DiscoveryCopyKey } from "@/lib/discovery-copy";
import { GUIDANCE_COPY } from "@/lib/guidance-copy";
import { INCEPTION_COPY } from "@/lib/inception-copy";
import { SCREEN_ROUTES } from "@/lib/next-step";
import { ACTION_KEYS, NEXT_STATES, NEXT_STEP_COPY, type NextStepCopyKey, WAITING_STAGES } from "@/lib/next-step-copy";
import { PLURALS } from "@/lib/plural";
import { PROPOSALS_COPY } from "@/lib/proposals-copy";
import { inceptionStateKey, stateCopy, STATES } from "@/lib/screening-states";
import { tc, TRIAGE_COPY } from "@/lib/triage-copy";
import { WORKBENCH_COPY } from "@/lib/workbench-copy";
import { CATALOGS } from "@/messages";
import en, { type MessageKey } from "@/messages/en";
import { auditRows, DISCOVERY_KEYS, INCEPTION_KEYS, WORKBENCH_KEYS } from "../tests/fixtures/guidance-audit";

const APP = resolve(import.meta.dirname, "..");
if (resolve(process.cwd()) !== APP) {
  throw new Error(`lint:ui reads files from the app root; run it with npm from apps/research-ui (cwd is ${process.cwd()})`);
}

// ---- from the vitest suite, group 1 ----
// Scans moved out of the unit suite. Paths are read from process.cwd(), which is apps/research-ui.

describe("charting-study.i18n.test.ts", () => {
  it("carries every Part B key in fr and ar, translated where English is not a name", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of Object.keys(CHARTING_COPY.en).filter((k) => k.startsWith("charting.study.") || k.startsWith("charting.form.") || k.startsWith("charting.cell.") || k.startsWith("charting.pilot."))) {
        expect((CHARTING_COPY[locale] as Record<string, string>)[key]?.trim(), `${locale} ${key}`).toBeTruthy();
      }
    }
    expect(cc("fr", "charting.study.position", { k: 1, total: 3 })).toBe("Étude 1 sur 3");
    expect(cc("ar", "charting.study.position", { k: 1, total: 3 })).toBe("الدراسة 1 من 3");
    expect(cc("ar", "charting.cell.notReported")).not.toBe(cc("en", "charting.cell.notReported"));
  });

  it("writes no literal aria-label, title, alt or placeholder in the Part B files (N9)", () => {
    for (const file of [
      "components/charting-study.tsx",
      "components/charting-cells.tsx",
      "components/charting-form-panel.tsx",
      "app/[locale]/charting/study/page.tsx",
    ]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });

});

describe("charting.fetch-i18n.test.ts", () => {
const fetchHoles = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
const FETCH_KEYS = Object.keys(CHARTING_COPY.en).filter((k) => k.startsWith("charting.fetch."));
  it("carries every charting.fetch key in en, fr and ar, non-empty, with the same holes", () => {
    expect(FETCH_KEYS.length).toBeGreaterThan(150);
    const en = CHARTING_COPY.en as Record<string, string>;
    for (const locale of SUPPORTED_LOCALES) {
      const other = CHARTING_COPY[locale] as Record<string, string>;
      for (const key of [...FETCH_KEYS, "charting.table.show.toConfirm", "charting.help.bodyFetch"]) {
        expect(other[key]?.trim(), `${locale} ${key}`).toBeTruthy();
        expect(fetchHoles(other[key]), `${locale} ${key}`).toEqual(fetchHoles(en[key]));
      }
    }
  });

  it("writes no literal aria-label, title, alt or placeholder in the Part F files (N9), and no browser storage (N12)", () => {
    for (const file of ["components/charting-fetch.tsx", "components/charting-page.tsx", "components/charting-study.tsx", "lib/charting-fetch.ts"]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
      expect(source.match(/localStorage|sessionStorage/g), file).toBeNull();
    }
  });

});

describe("charting.i18n.test.ts", () => {
const chartingHoles = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  it("carries every key in en, fr and ar, non-empty, with the same holes", () => {
    const en = CHARTING_COPY.en as Record<string, string>;
    for (const locale of SUPPORTED_LOCALES) {
      const other = CHARTING_COPY[locale] as Record<string, string>;
      expect(Object.keys(other).sort(), locale).toEqual(Object.keys(en).sort());
      for (const [key, text] of Object.entries(en)) {
        expect(other[key]?.trim(), `${locale} ${key}`).toBeTruthy();
        expect(chartingHoles(other[key]), `${locale} ${key}`).toEqual(chartingHoles(text));
      }
    }
  });

  it("writes no literal aria-label, title, alt or placeholder (N9)", () => {
    for (const file of ["components/charting-page.tsx", "app/[locale]/charting/page.tsx", "lib/charting-copy.ts", "lib/charting-api.ts", "lib/charting-logic.ts"]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});

describe("charting.report.i18n.test.tsx", () => {
const reportHoles = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
const REPORT_NEW_EXPORT_KEYS = ["charting.export.xlsx", "charting.export.done", "charting.export.requiredOpen", "charting.export.fileHad", "charting.export.format.csv", "charting.export.format.xlsx"];
  it("carries every report key and every new export key in en, fr and ar, non-empty, with the same holes", () => {
    const en = CHARTING_COPY.en as Record<string, string>;
    const keys = [...Object.keys(en).filter((k) => k.startsWith("charting.report.")), ...REPORT_NEW_EXPORT_KEYS];
    expect(keys.length).toBeGreaterThan(50);
    for (const locale of SUPPORTED_LOCALES) {
      const other = CHARTING_COPY[locale] as Record<string, string>;
      for (const key of keys) {
        expect(other[key]?.trim(), `${locale} ${key}`).toBeTruthy();
        expect(reportHoles(other[key]), `${locale} ${key}`).toEqual(reportHoles(en[key]));
      }
    }
  });

  it("writes no literal aria-label, title, alt or placeholder in the Part C files (N9)", () => {
    for (const file of ["components/charting-report.tsx", "components/charting-export-lines.tsx", "app/[locale]/charting/report/page.tsx"]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });

  it("reaches for no browser storage in the Part C files (N12)", () => {
    for (const file of ["components/charting-report.tsx", "components/charting-export-lines.tsx"]) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source, file).not.toMatch(/localStorage|sessionStorage|indexedDB/);
    }
  });
});

describe("charting.report.states.test.tsx", () => {
  it("every refusal this page can show has words of its own in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const unknown = CHARTING_COPY[locale]["charting.refusal.unknown"];
      for (const code of ["SCREENING_NOT_PUBLISHED", "CHARTING_EXPORT_FORMAT_INVALID", "CHARTING_PROTOCOL_REPLACED", "GENERATION_STALE", "BODY_INVALID"]) {
        expect(refusalWords(locale, code), `${locale} ${code}`).not.toBe(unknown);
      }
      for (const key of ["charting.report.failed", "charting.report.refused", "charting.offlineNoChange", "charting.report.phone.desktopOnly"] as const) {
        expect(CHARTING_COPY[locale][key].trim(), `${locale} ${key}`).not.toBe("");
      }
    }
  });
});

describe("charting.states.test.tsx", () => {
  it("every refusal code maps to its own key in en, fr and ar", () => {
    for (const code of CHARTING_REFUSAL_CODES) {
      const key = `charting.refusal.${code}` as ChartingCopyKey;
      for (const locale of SUPPORTED_LOCALES) {
        expect(CHARTING_COPY[locale][key], `${locale} ${code}`).toBeTruthy();
        expect(refusalWords(locale, code)).toBe(CHARTING_COPY[locale][key]);
      }
    }
    expect(refusalWords("en", "SOMETHING_NEW")).toBe("The console refused the change.");
    expect(CHARTING_COPY.en["charting.refusal.FULLTEXT_REASON_REQUIRED"]).toBe("Choose one reason first.");
  });
});

describe("checks-panel.test.tsx", () => {
  it("copy: every checks.* key and every checks.<ID>.* key exists in en; fr and ar fall back; no literal aria-label (N9 guard)", () => {
    const checksHoles = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    expect(CHECK_IDS).toHaveLength(59);
    for (const id of CHECK_IDS) {
      for (const part of ["sentence", "why", "action"]) expect(CHECKS_COPY.en, `${id}.${part}`).toHaveProperty([`checks.${id}.${part}`]);
    }
    for (const key of ["checks.HARVEST_ABOVE_TARGET_general.sentence", "checks.HARVEST_ABOVE_TARGET_general.why", "checks.SEEDS_CANNOT_TEST_all.sentence", "checks.SEEDS_CANNOT_TEST_concept.why", "checks.SEEDS_CANNOT_TEST_few.sentence", "checks.METHOD_RULE_UNCHOSEN_older.sentence", "checks.METHOD_RULE_UNCHOSEN_older.why", "checks.counts", "checks.ready.blocked", "checks.dismiss.label", "checks.earlier"]) {
      expect(CHECKS_COPY.en).toHaveProperty([key]);
    }
    for (const [key, en] of Object.entries(CHECKS_COPY.en)) {
      for (const locale of ["fr", "ar"] as const) {
        const text = CHECKS_COPY[locale][key as keyof typeof CHECKS_COPY.en];
        expect(text, `${locale} ${key}`).toBeTruthy();
        expect(checksHoles(text), `${locale} ${key}`).toEqual(checksHoles(en));
      }
    }
    for (const file of ["components/checks-panel.tsx", "components/discovery-checks.tsx", "components/inception-assist.tsx", "components/checks-bus.ts"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});

// ---- from the vitest suite, group 2 ----
describe("details-rule.test.ts", () => {
  const detailsRule_COMPONENTS = resolve(process.cwd(), "components");

    it("gives every summary a 44 px target and a focus ring", () => {
      const offenders: string[] = [];
      let seen = 0;
      for (const name of readdirSync(detailsRule_COMPONENTS).filter((f) => f.endsWith(".tsx"))) {
        const text = readFileSync(join(detailsRule_COMPONENTS, name), "utf-8");
        for (const match of text.matchAll(/<summary className="([^"]*)"/g)) {
          seen += 1;
          const classes = match[1].split(/\s+/);
          if (!classes.includes("min-h-11") || !classes.some((c) => c.startsWith("focus-visible:outline"))) offenders.push(`${name}: ${match[1]}`);
        }
        for (const bare of text.matchAll(/<summary(?! className)/g)) offenders.push(`${name}: summary without classes at ${bare.index}`);
      }
      expect(seen).toBeGreaterThan(10); // anti-vacuity: the screens use Details
      expect(offenders).toEqual([]);
    });

    it("gives the folded section's summary (03-guidance rule 4, M10d) the same 44 px target and focus ring", () => {
      const text = readFileSync(join(detailsRule_COMPONENTS, "ui", "guidance.tsx"), "utf-8");
      const summary = text.match(/const SUMMARY = `([^`]*)`/)?.[1] ?? "";
      expect(summary.split(/\s+/)).toContain("min-h-11");
      expect(text).toMatch(/const FOCUS = "[^"]*focus-visible:outline-2/);
      expect(summary).toContain("${FOCUS}");
      expect(text).toMatch(/<summary className=\{SUMMARY\}>/);
    });
});

describe("discovery-chase.test.tsx", () => {
    it("gives every chase refusal a known card in every locale", () => {
      for (const locale of SUPPORTED_LOCALES) {
        for (const code of ["SCREENING_NOT_PUBLISHED", "CHASE_NOT_RUN", "CHASE_NOTHING_NEW", "CHASE_ALREADY_ACCEPTED", "CHASE_STALE", "CHASE_DIRECTION_INVALID", "CHASE_SEEDS_INVALID", "PROTOCOL_CHANGED_SINCE_PUBLISH"]) {
          const card = stateCopy(locale, code);
          expect(card.known, `${locale} ${code}`).toBe(true);
          expect(card.title && card.body, `${locale} ${code}`).toBeTruthy();
        }
        expect(DISCOVERY_COPY[locale]["steps.chase"].startsWith("8 ")).toBe(true);
      }
    });
});

describe("discovery-copy.test.ts", () => {
  const discoveryCopy_placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

  const discoveryCopy_CODES = [
    "PROTOCOL_MISSING", "PROTOCOL_INVALID", "PROTOCOL_CHANGED_SINCE_RUN", "PROTOCOL_CHANGED_SINCE_SNAPSHOT", "MAILTO_NOT_SET", "OPENALEX_KEY_NOT_SET",
    "DISCOVERY_JOB_ACTIVE", "DISCOVERY_JOB_NOT_FOUND", "RUN_NOT_FOUND", "RECALL_NOT_RUN", "DEDUP_NOT_RUN", "SEEDS_INVALID",
    "CAP_INVALID", "PACE_INVALID", "PROVIDER_UNKNOWN", "STAGED_IMPORT_PENDING", "BATCHES_INCOMPLETE", "PROVIDERS_FAILED", "DISCOVERY_FAILED", "BODY_INVALID",
    "ACCEPT_CORPUS_REFUSED", "VERIFIED_EXISTS", "CORPUS_ALREADY_ACCEPTED", "NOTHING_STAGED",
  ];

    it("carries every English key in French and Arabic, with the same placeholders", () => {
      const keys = Object.keys(DISCOVERY_COPY.en).sort();
      for (const locale of SUPPORTED_LOCALES) {
        expect(Object.keys(DISCOVERY_COPY[locale]).sort(), locale).toEqual(keys);
        for (const [key, en] of Object.entries(DISCOVERY_COPY.en)) {
          const text = DISCOVERY_COPY[locale][key as DiscoveryCopyKey];
          expect(text, `${locale}.${key}`).toBeTruthy();
          expect(discoveryCopy_placeholders(text), `${locale}.${key}`).toEqual(discoveryCopy_placeholders(en));
        }
      }
    });

    it("gives every discovery refusal code a known card in every locale, with a title and a body", () => {
      for (const locale of SUPPORTED_LOCALES) {
        for (const code of discoveryCopy_CODES) {
          const card = stateCopy(locale, code);
          expect(card.known, `${locale} ${code}`).toBe(true);
          expect(card.title, `${locale} ${code}`).toBeTruthy();
          expect(card.body, `${locale} ${code}`).toBeTruthy();
        }
      }
    });

    it("prints the SCHOLAR_MAILTO line with the variable name untranslated in every locale", () => {
      expect(DISCOVERY_COPY.en["mailto.line"]).toBe("SCHOLAR_MAILTO=<your email>");
      for (const locale of SUPPORTED_LOCALES) {
        expect(DISCOVERY_COPY[locale]["mailto.line"].startsWith("SCHOLAR_MAILTO=")).toBe(true);
        expect(stateCopy(locale, "MAILTO_NOT_SET").command).toBe("SCHOLAR_MAILTO=<your email>");
      }
    });

    it("prints the SCHOLAR_OPENALEX_KEY line with the variable name untranslated in every locale (F12)", () => {
      for (const locale of SUPPORTED_LOCALES) {
        expect(DISCOVERY_COPY[locale]["openalexKey.line"]).toBe("SCHOLAR_OPENALEX_KEY=<your key>");
        expect(stateCopy(locale, "OPENALEX_KEY_NOT_SET").command).toBe("SCHOLAR_OPENALEX_KEY=<your key>");
      }
    });
});

describe("discovery-preparation.test.tsx", () => {
    it.each(["en", "fr", "ar"] as const)("in %s", (locale) => {
      for (const code of ["PREPARATION_UNFINISHED", "PREPARATION_NOT_AVAILABLE"]) {
        const copy = stateCopy(locale, code);
        expect(copy.known).toBe(true);
        expect(copy.title.length).toBeGreaterThan(5);
        expect(copy.actionLabel.length).toBeGreaterThan(2);
      }
    });
});

describe("guidance-copy.test.ts", () => {
  const guidanceCopy_holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

    it("has every key in en, fr and ar, with the same placeholders, none empty", () => {
      const keys = Object.keys(GUIDANCE_COPY.en);
      expect(keys).toContain("guidance.hint.open");
      expect(keys).toContain("guidance.recommended");
      for (const locale of ["fr", "ar"] as const) {
        expect(Object.keys(GUIDANCE_COPY[locale]).sort()).toEqual([...keys].sort());
        for (const key of keys) {
          const en = GUIDANCE_COPY.en[key as keyof typeof GUIDANCE_COPY.en];
          const other = GUIDANCE_COPY[locale][key as keyof typeof GUIDANCE_COPY.en];
          expect(other.trim(), `${locale} ${key}`).not.toBe("");
          expect(guidanceCopy_holes(other), `${locale} ${key}`).toEqual(guidanceCopy_holes(en));
        }
      }
    });

    it("writes no literal accessible name in the guidance components (N9)", () => {
      const source = readFileSync(resolve(process.cwd(), "components/ui/guidance.tsx"), "utf-8");
      expect(source).not.toMatch(/(aria-label|title|alt|placeholder)="/);
      expect(source).not.toMatch(/\bAI\b/);
    });
});

describe("guidance.audit.test.tsx", () => {
  const guidanceAudit_ROWS = auditRows();

    it("has a row for every key of the inception and discovery catalogs (a new key fails until it is audited)", () => {
      const covered = (prefix: string) => new Set(guidanceAudit_ROWS.filter((r) => r.id.startsWith(prefix)).flatMap((r) => r.keys));
      const inception = covered("I-");
      const discovery = covered("D-");
      const workbench = covered("W-");
      expect(INCEPTION_KEYS.filter((k) => !inception.has(k))).toEqual([]);
      expect(DISCOVERY_KEYS.filter((k) => !discovery.has(k))).toEqual([]);
      expect(WORKBENCH_KEYS.filter((k) => !workbench.has(k))).toEqual([]);
    });
});

describe("guidance.never-hidden.test.tsx", () => {
    it("passes no V1, V2, V3, V5 or V6 key, and no screening-state key, as a hint's text", () => {
      const rows = auditRows();
      // The keys the audit keeps visible as a refusal, warning, check result, provenance or gate text.
      const forbidden = new Set(rows.filter((r) => r.decision === "STAYS" && /\bV[12356]\b/.test(r.reason)).flatMap((r) => r.keys));
      const hintRows = new Set(rows.filter((r) => r.decision === "HINT").flatMap((r) => r.keys));
      const states = readFileSync(join(process.cwd(), "lib", "screening-states.ts"), "utf-8");
      const stateKeys = new Set([...states.matchAll(/^\s+"?([A-Za-z_.]+)"?:\s*"/gm)].map((m) => m[1]));
      const dir = join(process.cwd(), "components");
      const used: string[] = [];
      for (const name of readdirSync(dir).filter((f) => f.endsWith(".tsx"))) {
        const text = readFileSync(join(dir, name), "utf-8");
        for (const m of text.matchAll(/textKey="([^"]+)"/g)) used.push(`${name}:${m[1]}`);
        for (const m of text.matchAll(/whyKey="([^"]+)"/g)) used.push(`${name}:${m[1]}`);
      }
      expect(used.length).toBeGreaterThan(60); // anti-vacuity: the screens use hints
      // Every key a hint holds is a HINT row, never a key kept visible as V1/V2/V3/V5/V6, never a state key.
      const bad = used.filter((u) => {
        const key = u.split(":")[1];
        return !hintRows.has(key) || (forbidden.has(key) && !hintRows.has(key)) || stateKeys.has(key);
      });
      expect(bad).toEqual([]);
      expect(forbidden.size).toBeGreaterThan(100);
      expect(used.map((u) => u.split(":")[1]).filter((k) => forbidden.has(k) && !hintRows.has(k))).toEqual([]);
    });
});

describe("i18n-catalog.test.ts", () => {
    it("ships exactly the keys the packets inventory, in every locale", () => {
      // 150 keys until M5-slim; the demonstration screens and their 128 keys
      // were removed on 2026-11-05, and the new header and footer added 6
      // (`nav.workspaces`, `shell.descriptor`, `footer.*`): 22, the shell
      // chrome only; M3c-screens added `nav.discovery` (23), M12a `nav.charting` (24), M13 Part B `nav.settings` (25). `messages/en.ts`'s header states the same figure.
      const expected = Object.keys(en).sort();

      expect(expected).toHaveLength(25);
      for (const locale of SUPPORTED_LOCALES) {
        expect(Object.keys(CATALOGS[locale]).sort()).toEqual(expected);
      }
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
});

describe("i18n-direction-source.test.ts", () => {
  function dirSrc_resolveAppRoot(): string {
    const candidates = [process.cwd(), join(process.cwd(), "apps", "research-ui")];
    for (const candidate of candidates) {
      try {
        statSync(join(candidate, "app", "globals.css"));
        statSync(join(candidate, "components"));
        return candidate;
      } catch {
        continue;
      }
    }
    throw new Error(
      `no application root among ${JSON.stringify(candidates)}: expected app/globals.css and components/`,
    );
  }

  const dirSrc_APP_ROOT = dirSrc_resolveAppRoot();

  function dirSrc_sourceFiles(dir: string): string[] {
    const absolute = join(dirSrc_APP_ROOT, dir);
    const found: string[] = [];
    const walk = (current: string): void => {
      for (const entry of readdirSync(current)) {
        const path = join(current, entry);
        if (statSync(path).isDirectory()) {
          walk(path);
        } else if (/\.(ts|tsx)$/.test(entry)) {
          found.push(relative(dirSrc_APP_ROOT, path).split(sep).join("/"));
        }
      }
    };
    walk(absolute);
    return found.sort();
  }

  const dirSrc_LINES_CACHE = new Map<string, Array<{ file: string; line: number; text: string }>>();
  function dirSrc_lines(file: string): Array<{ file: string; line: number; text: string }> {
    let cached = dirSrc_LINES_CACHE.get(file);
    if (cached === undefined) {
      cached = readFileSync(join(dirSrc_APP_ROOT, file), "utf8")
        .split(/\r?\n/)
        .map((text, index) => ({ file, line: index + 1, text }));
      dirSrc_LINES_CACHE.set(file, cached);
    }
    return cached;
  }

  function dirSrc_hits(files: string[], pattern: RegExp): string[] {
    const found: string[] = [];
    for (const file of files) {
      for (const { line, text } of dirSrc_lines(file)) {
        const match = text.match(pattern);
        if (match) {
          found.push(`${file}:${line}: ${match[0]}`);
        }
      }
    }
    return found;
  }

  const dirSrc_UI_SOURCE = [
    ...dirSrc_sourceFiles("app").filter((file) => !file.startsWith("app/api/")),
    ...dirSrc_sourceFiles("components"),
  ];

    it("reads the UI source it is meant to guard", () => {
      // Anti-vacuity: a scan root that silently resolved to nothing would make
      // every assertion below pass for the wrong reason.
      expect(dirSrc_UI_SOURCE.length).toBeGreaterThan(5);
      expect(dirSrc_UI_SOURCE.some((file) => file.startsWith("app/"))).toBe(true);
      expect(dirSrc_UI_SOURCE.some((file) => file.startsWith("components/"))).toBe(true);
      expect(dirSrc_UI_SOURCE.some((file) => file.endsWith(".tsx"))).toBe(true);
    });

    it("carries no literal accessible name (N9)", () => {
      // `aria-label="…"`, `title="…"`, `alt="…"` and `placeholder="…"` are user-visible
      // strings that bypass the catalogs by construction. A translated label is a
      // catalog lookup written as an expression, so these four attributes with a
      // string literal have no legitimate spelling left in this application.
      const found = dirSrc_hits(dirSrc_UI_SOURCE, /(aria-label|title|alt|placeholder)="/);
      expect(found).toEqual([]);
    });

    it("uses no physical layout property where a logical one belongs (N10)", () => {
      // Each pattern is the physical-direction spelling of a utility that has a
      // logical equivalent (`border-s`, `ps-*`, `ms-*`, `text-end`, ...). The
      // optional `-<width>` suffix is what makes the border and corner patterns
      // match `border-l-2` and `rounded-r-lg` as well as the bare names.
      const patterns: Array<[string, RegExp]> = [
        ["border-left", /border-l(?:-[0-9]+)?(?![\w-])/],
        ["border-right", /border-r(?:-[0-9]+)?(?![\w-])/],
        ["rounded-left", /rounded-l(?:-[0-9]+)?(?![\w-])/],
        ["rounded-right", /rounded-r(?:-[0-9]+)?(?![\w-])/],
        ["text-align", /text-left|text-right(?![\w-])/],
        ["margin-left", /ml-\d/],
        ["margin-right", /mr-\d/],
        ["padding-left", /pl-\d/],
        ["padding-right", /pr-\d/],
        ["inset-left", /left-\d/],
        ["inset-right", /right-\d/],
        ["reversed flow", /space-x-reverse|divide-x-reverse/],
        ["transform origin", /origin-left|origin-right/],
        ["float", /float-left|float-right/],
      ];

      for (const [label, pattern] of patterns) {
        expect(dirSrc_hits(dirSrc_UI_SOURCE, pattern), label).toEqual([]);
      }
    });

    it("declares no physical layout property in the stylesheet (N10)", () => {
      // The class scan above cannot see a declaration in CSS, and the one physical
      // property this stylesheet still needs is the focus-ring offset — which is
      // physical by definition, because a ring is drawn outward from the element
      // and `outline-offset` has no logical spelling. What must not come back is a
      // directional property.
      const css = readFileSync(join(dirSrc_APP_ROOT, "app/globals.css"), "utf8");
      const declarations = css
        .split(/\r?\n/)
        .map((text, index) => ({ line: index + 1, text }))
        .filter(({ text }) =>
          /(^|[;\s])(left|right|margin-left|margin-right|padding-left|padding-right|border-left|border-right)\s*:/.test(
            text,
          ),
        )
        .map(({ line, text }) => `app/globals.css:${line}: ${text.trim()}`);
      expect(declarations).toEqual([]);
    });

    it("mirrors no icon (N11)", () => {
      // The header's icons (menu, close, language, a down chevron, a check) read
      // the same in both directions, so flipping them would be a false signal. If
      // a directional icon is ever added, this is where it has to be declared
      // deliberately rather than inherited from a class name.
      const header = readFileSync(join(dirSrc_APP_ROOT, "components/site-header.tsx"), "utf8");
      expect(header).not.toMatch(/scale-x-\[-1\]/);
      expect(header).not.toMatch(/rtl:scale-x/);
    });

    it("reaches for no browser state and no network at render time (N12)", () => {
      // The locale is a URL segment. Reading it from `navigator.language`, from
      // storage, or from a request would make the document's language depend on
      // state the URL does not contain, and the same URL would then render two
      // different languages.
      const scope = [...dirSrc_UI_SOURCE, ...dirSrc_sourceFiles("i18n"), ...dirSrc_sourceFiles("messages")];
      expect(dirSrc_hits(scope, /\bfetch\(/)).toEqual([]);
      expect(dirSrc_hits(scope, /XMLHttpRequest/)).toEqual([]);
      // One exemption, by file: the theme selector remembers light/dark/system in
      // `localStorage` (production plan §3, M0). A theme is not a locale and
      // changes no text, and it is read after render (an effect, and the boot
      // script that sets `data-theme` before paint), never during it. No other
      // file in this scope (`app/`, `components/`) may touch storage, and the theme
      // files may not read the locale. The boot script and its storage key live in
      // `lib/theme-boot.ts`, a module the server can inline (H-hydration-418); `lib/`
      // is outside the storage scope, so only the locale check applies to it.
      const THEME_FILES = ["components/theme-toggle.tsx", "lib/theme-boot.ts"];
      expect(dirSrc_hits(scope.filter((file) => !THEME_FILES.includes(file)), /localStorage/)).toEqual([]);
      expect(dirSrc_hits(THEME_FILES, /navigator\.|locale/i)).toEqual([]);
      expect(dirSrc_hits(scope, /navigator\.language/)).toEqual([]);
    });
});

describe("inception-copy.test.ts", () => {
  const inceptionCopy_placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

    it("carries every English key in French and Arabic, with the same placeholders", () => {
      for (const locale of SUPPORTED_LOCALES) {
        for (const [key, en] of Object.entries(INCEPTION_COPY.en)) {
          const text = INCEPTION_COPY[locale][key as keyof (typeof INCEPTION_COPY)["en"]];
          expect(text, `${locale}.${key}`).toBeTruthy();
          expect(inceptionCopy_placeholders(text), `${locale}.${key}`).toEqual(inceptionCopy_placeholders(en));
        }
      }
    });

    it("gives every inception refusal code a known card in every locale", () => {
      const codes = [
        "DRAFT_ID_INVALID", "DRAFT_NOT_FOUND", "DRAFT_UNREADABLE", "DRAFT_EXISTS", "DRAFT_CONFLICT", "DRAFT_EMITTED", "DRAFT_INVALID",
        "DRAFT_INCOMPLETE", "STEP_UNKNOWN", "CRITERIA_UNDECIDED", "CRITERIA_MISSING", "INTENT_INVALID", "SCREENING_BOUND",
        "CONFIRMATION_MISMATCH", "WORKSPACE_EXISTS", "WORKSPACE_ROOT_UNAVAILABLE", "WORKSPACE_TITLE_INVALID", "WORKSPACE_PATH_REFUSED",
        "WORKSPACE_JOB_ACTIVE", "ARCHIVE_INCOMPLETE",
        // H-input-limits: a draft over its size limits (F6) and a body pydantic refuses (F5).
        "DRAFT_TOO_LARGE", "BODY_INVALID",
        // M10b (spec 09): starting a draft from an earlier protocol.
        "IMPORT_SOURCE_NOT_FOUND", "IMPORT_SOURCE_UNREADABLE", "IMPORT_SOURCE_TOO_LARGE", "IMPORT_NOT_A_PROTOCOL",
        "IMPORT_PROTOCOL_VERSION_UNSUPPORTED", "IMPORT_SOURCE_CHANGED", "inception.PROTOCOL_INVALID",
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

    it("names the two decisions with the words on the buttons, in every locale", async () => {
      const { CHECKS_COPY } = await import("@/lib/checks-copy");
      for (const locale of SUPPORTED_LOCALES) {
        const sentence = CHECKS_COPY[locale]["checks.CRITERIA_UNDECIDED.sentence"];
        expect(sentence, locale).toContain(INCEPTION_COPY[locale]["criteria.accept"]);
        expect(sentence, locale).toContain(INCEPTION_COPY[locale]["criteria.reject"]);
      }
    });
});

describe("inception-criteria-block.test.tsx", () => {
    it("has the five wording checks, the not-checked note and the blocker in every locale", () => {
      for (const id of ["CRITERIA_DUPLICATE", "CRITERIA_CONTRADICT", "CRITERIA_MIRRORED", "CRITERIA_LUMPED", "CRITERIA_NEEDS_FULL_TEXT", "CRITERIA_WORDING_NOT_CHECKED", "METHOD_RULE_UNCHOSEN"]) {
        for (const locale of ["en", "fr", "ar"] as const) {
          for (const part of ["sentence", "why", "action"]) expect(CHECKS_COPY[locale], `${locale} ${id}.${part}`).toHaveProperty([`checks.${id}.${part}`]);
        }
      }
      expect(CHECKS_COPY.en["checks.METHOD_RULE_UNCHOSEN_older.sentence" as keyof (typeof CHECKS_COPY)["en"]]).toContain("This draft was started before this question existed.");
    });
});


// ---- from the vitest suite, group 3 ----
// Group 3 lint fragment: scans moved out of tests/*.test.tsx (they read catalogues and source files, no DOM needed).
// Paths read from disk resolve from the app root (apps/research-ui) through process.cwd(), as before.



describe("inception-sample.test", () => {
  it("carries every sample key in en, fr and ar, and the two refusal cards", () => {
    const keys = Object.keys(INCEPTION_COPY.en).filter((k) => k.startsWith("sample."));
    expect(keys).toEqual(expect.arrayContaining(["sample.mark", "sample.mark.label", "sample.put.label", "sample.putAll", "sample.undo", "sample.toast", "sample.moved", "sample.left.title", "sample.empty", "sample.noReserve", "sample.warnBound.title", "sample.warnSeed.go", "sample.stale.body"]));
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of keys) expect(INCEPTION_COPY[locale][key as keyof (typeof INCEPTION_COPY)["en"]], `${locale} ${key}`).toBeTruthy();
      for (const code of ["PAPER_UNKNOWN", "SAMPLE_EXCLUSIONS_FULL"]) expect(stateCopy(locale, code).known, `${locale} ${code}`).toBe(true);
    }
    expect(stateCopy("en", "PAPER_UNKNOWN").actionLabel).toBe("Reload the papers");
    expect(stateCopy("en", "SAMPLE_EXCLUSIONS_FULL").actionLabel).toBe("Change scope");
  });

  it("writes no literal accessible name (N9) and ships no fixture (live only)", () => {
    for (const file of ["components/inception-sample.tsx", "components/inception-explore.tsx"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
      expect(text, file).not.toMatch(/from "[^"]*(tests|fixtures)\//);
    }
  });
});

describe("inception-workbench.test", () => {
  it("has every key in en, fr and ar with the same placeholders, and no literal labels in the component (N9)", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const [key, en] of Object.entries(WORKBENCH_COPY.en)) {
      for (const locale of ["fr", "ar"] as const) {
        const text = WORKBENCH_COPY[locale][key as keyof typeof WORKBENCH_COPY.en];
        expect(text, `${locale} ${key}`).toBeTruthy();
        expect(holes(text), `${locale} ${key}`).toEqual(holes(en));
      }
    }
    const component = readFileSync(join(process.cwd(), "components", "query-workbench.tsx"), "utf8");
    expect(component.match(/(aria-label|title|alt|placeholder)="/g)).toBeNull();
  });
});

describe("next-step-bar.test", () => {
  const en = NEXT_STEP_COPY.en as Record<string, string>;
  const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

  it("maps every state, waiting stage and action key to a key in en, fr and ar, with the same holes", () => {
    const keys = [
      ...NEXT_STATES.map((s) => `next.state.${s}`),
      ...WAITING_STAGES.map((s) => `next.waiting.${s}`),
      ...ACTION_KEYS.map((k) => `next.action.${k}`),
      "next.stopped.searching", "next.stopped.stage", "next.failed.searching", "next.failed.stage", "next.interrupted",
      "next.reason.STOPPED_BY_RESEARCHER", "next.reason.INTERRUPTED", "next.inRound",
      "next.state.SETUP_NEEDED.what.email", "next.state.SETUP_NEEDED.what.key", "next.state.SETUP_NEEDED.what.both",
      "next.stage.deduplicating", "next.stage.adding_abstracts", "next.stage.verifying",
      "next.region", "next.details", "next.asOf", "next.unknown", "next.here", "next.offline", "next.offline.last",
      "next.word.running", "next.word.stopped", "next.word.failed", "next.word.interrupted",
    ];
    for (const key of keys) expect(en, key).toHaveProperty([key]);
    for (const [key, text] of Object.entries(en)) {
      for (const locale of ["fr", "ar"] as const) {
        const other = NEXT_STEP_COPY[locale][key as NextStepCopyKey];
        expect(other, `${locale} ${key}`).toBeTruthy();
        expect(holes(other), `${locale} ${key}`).toEqual(holes(text));
      }
    }
    expect(en["next.state.PUBLISHED_STALE"]).toBe("The screening changed since you published.");
  });

  it("routes every screen the engine names, and the bar's source carries no literal accessible name (N9)", () => {
    for (const screen of ["workspaces", "inception.list", "inception.scope", "inception.explore", "inception.direction", "inception.shape", "inception.criteria", "inception.review", "inception.done", "discovery.plan", "discovery.harvest", "discovery.handoff", "discovery.chase", "screening.home", "screening.triage", "screening.publish", "charting"]) {
      expect(SCREEN_ROUTES, screen).toHaveProperty([screen]);
    }
    for (const file of ["components/next-step-bar.tsx", "components/review-bus.ts", "lib/next-step.ts", "lib/next-step-copy.ts"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});

describe("plural.test", () => {
  const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).filter((h) => h !== "n").sort();
  const catalogs = { ...INCEPTION_COPY, } as Record<Locale, Record<string, string>>;
  const general = (locale: Locale, key: string): string =>
    (CHECKS_COPY[locale] as Record<string, string>)[key] ?? (PROPOSALS_COPY[locale] as Record<string, string>)[key] ?? catalogs[locale][key] ?? (DISCOVERY_COPY[locale] as Record<string, string>)[key] ?? (TRIAGE_COPY[locale] as Record<string, string>)[key] ?? (CHARTING_COPY[locale] as Record<string, string>)[key];

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

describe("proposals.test", () => {
  it("copy: every proposals.* key exists in en and fr/ar fall back", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const [key, en] of Object.entries(PROPOSALS_COPY.en)) {
      for (const locale of ["fr", "ar"] as const) {
        const text = PROPOSALS_COPY[locale][key as keyof typeof PROPOSALS_COPY.en];
        expect(text, `${locale} ${key}`).toBeTruthy();
        expect(holes(text), `${locale} ${key}`).toEqual(holes(en));
      }
    }
    for (const key of ["proposals.title", "proposals.what.add", "proposals.stale.was", "proposals.notRecorded", "proposals.source.engine.anchor_seed"]) {
      expect(PROPOSALS_COPY.en).toHaveProperty([key]);
    }
    // The N9 guard on the new components: no literal accessible name.
    for (const file of ["components/inception-assist.tsx", "components/assist-anchor.tsx", "components/assist-context.tsx"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});

describe("screening-agreement.test", () => {
  it("has every key in every locale", () => {
    const keys = Object.keys(AGREEMENT_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(AGREEMENT_COPY[locale]).sort()).toEqual(keys);
  });
});

describe("screening-export.test", () => {
  it("has a card for every export refusal code, in every locale", () => {
    for (const code of ["EXPORT_NOT_PUBLISHED", "GENERATION_STALE", "GENERATION_SUPERSEDED", "EXPORT_FORMAT_INVALID", "EXPORT_SOURCE_MISMATCH", "METHODS_SOURCE_MISSING"]) {
      for (const locale of SUPPORTED_LOCALES) expect(stateCopy(locale, code).known, `${code}/${locale}`).toBe(true);
    }
  });

  it("has every key in every locale", () => {
    const keys = Object.keys(EXPORT_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(EXPORT_COPY[locale]).sort(), locale).toEqual(keys);
    for (const locale of SUPPORTED_LOCALES) expect(HOME_COPY[locale].exportLink.trim(), locale).not.toBe("");
  });

  it("writes no literal aria-label, title, alt or placeholder (N9)", () => {
    const source = readFileSync(resolve(process.cwd(), "components/screening-export.tsx"), "utf-8");
    expect(source).not.toMatch(/(aria-label|alt|placeholder)="[^"{]/);
    expect(source).not.toMatch(/\stitle="[^"{]/);
  });
});

describe("screening-home.test", () => {
  it("has a title, body, affects and action for every code in every locale", () => {
    for (const [code, entry] of Object.entries(STATES)) {
      for (const locale of SUPPORTED_LOCALES) {
        for (const field of ["title", "body", "affects", "action"] as const) {
          expect(entry.copy[locale][field].trim(), `${code}/${locale}/${field}`).not.toBe("");
        }
      }
    }
  });

  it("home copy has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(HOME_COPY[locale]).sort()).toEqual(Object.keys(HOME_COPY.en).sort());
      for (const [key, value] of Object.entries(HOME_COPY[locale])) {
        expect(holes(value), `${locale}/${key}`).toEqual(holes(HOME_COPY.en[key as keyof typeof HOME_COPY.en]));
      }
    }
  });
});

describe("screening-import.test", () => {
  it("has the same keys in every locale", () => {
    const keys = Object.keys(IMPORT_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(IMPORT_COPY[locale]).sort()).toEqual(keys);
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of ["importCta", "imported", "importedLink"] as const) expect(HOME_COPY[locale][key]).toBeTruthy();
    }
  });
});

describe("screening-pilot-card.test", () => {
  it("every locale has every key with the same holes", () => {
    const keys = Object.keys(PILOT_CARD_COPY.en).sort();
    const holes = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort().join(",");
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PILOT_CARD_COPY[locale]).sort()).toEqual(keys);
      for (const key of keys) {
        const value = PILOT_CARD_COPY[locale][key as keyof (typeof PILOT_CARD_COPY)["en"]];
        expect(value.length, `${locale}.${key}`).toBeGreaterThan(0);
        expect(holes(value), `${locale}.${key}`).toBe(holes(PILOT_CARD_COPY.en[key as keyof (typeof PILOT_CARD_COPY)["en"]]));
      }
    }
  });
});

describe("screening-pilot.test", () => {
  it("every locale has every key with the same holes, none empty", () => {
    const keys = Object.keys(PILOT_COPY.en).sort();
    const holes = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort().join(",");
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PILOT_COPY[locale]).sort()).toEqual(keys);
      for (const key of keys) {
        const value = PILOT_COPY[locale][key as keyof (typeof PILOT_COPY)["en"]];
        expect(value.length, `${locale}.${key}`).toBeGreaterThan(0);
        expect(holes(value), `${locale}.${key}`).toBe(holes(PILOT_COPY.en[key as keyof (typeof PILOT_COPY)["en"]]));
      }
    }
  });
});



// ---- from the vitest suite, group 4 ----
// Base for every path read from disk: the app root (apps/research-ui). The original tests used
// resolve(import.meta.dirname, "..") from tests/; lint/ is at the same depth, so it is unchanged.
// The component imports above pull in React modules; they only need to load, not render, so no DOM is required.

describe("screening-prepare.test.tsx", () => {
  it("prepare copy: has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PREPARE_COPY[locale]).sort()).toEqual(Object.keys(PREPARE_COPY.en).sort());
      for (const [key, value] of Object.entries(PREPARE_COPY[locale])) {
        expect(holes(value), `${locale}/${key}`).toEqual(holes(PREPARE_COPY.en[key as keyof typeof PREPARE_COPY.en]));
      }
    }
  });
});

describe("screening-proposals.test.tsx", () => {
  it("proposals copy: has every key in every locale", () => {
    const keys = Object.keys(SCREENING_PROPOSALS_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(SCREENING_PROPOSALS_COPY[locale]).sort()).toEqual(keys);
  });

  it("is the listed model with the lowest input and output prices in the engine's price table", () => {
    const toml = readFileSync(resolve(APP, "../../src/scholar_agent/tasks/screening/prices.toml"), "utf-8");
    const price = (model: string, field: "input" | "output") => {
      const block = toml.split(`[anthropic."${model}"]`)[1].split(/\r?\n\[/)[0];
      return Number(new RegExp(`^${field} = ([0-9.]+)`, "m").exec(block)![1]);
    };
    const total = (model: string) => price(model, "input") + price(model, "output");
    const cheapest = [...LISTED_ANTHROPIC_MODELS].sort((a, b) => total(a) - total(b))[0];
    expect(CHEAPEST_ANTHROPIC_MODEL).toBe(cheapest);
  });
});

describe("screening-publish.test.tsx", () => {
  it("publish copy: has the same keys and holes in every locale", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(PUBLISH_COPY[locale]).sort()).toEqual(Object.keys(PUBLISH_COPY.en).sort());
      for (const [key, value] of Object.entries(PUBLISH_COPY[locale])) {
        expect(value.trim()).not.toBe("");
        expect(holes(value), `${locale}/${key}`).toEqual(holes(PUBLISH_COPY.en[key as keyof typeof PUBLISH_COPY.en]));
      }
    }
  });

  it("publish copy: has the three variants in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      for (const key of ["prisma", "prismaScr", "prismaNone", "publishBodyNone"] as const) expect(PUBLISH_COPY[locale][key]).toBeTruthy();
      // M12a DoD 9: Publish no longer says it writes a full-text list.
      for (const key of ["publishBody", "publishBodyNone"] as const) expect(PUBLISH_COPY[locale][key]).not.toMatch(/full-text lists|texte intégral ainsi|والنص الكامل وتقرير/);
    }
  });
});

describe("server-client-boundary.test.ts", () => {
  const ROOTS = ["app", "components", "lib", "i18n"];

  function boundarySourceFiles(dir: string): string[] {
    const out: string[] = [];
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      if (statSync(path).isDirectory()) out.push(...boundarySourceFiles(path));
      else if (/\.(ts|tsx)$/.test(name) && !name.endsWith(".d.ts")) out.push(path);
    }
    return out;
  }

  const DIRECTIVE = /^\s*(?:\/\/[^\n]*\n\s*|\/\*[\s\S]*?\*\/\s*)*["']use client["']/;
  const boundaryIsClient = (file: string) => DIRECTIVE.test(readFileSync(file, "utf8"));

  function boundaryResolveLocal(from: string, spec: string): string | null {
    const base = spec.startsWith("@/") ? resolve(APP, spec.slice(2)) : spec.startsWith(".") ? resolve(dirname(from), spec) : null;
    if (!base) return null;
    for (const candidate of [base, `${base}.ts`, `${base}.tsx`, join(base, "index.ts"), join(base, "index.tsx")]) {
      if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
    }
    return null;
  }

  /** The value names a module imports from each local specifier (type-only imports and names left out). */
  function boundaryValueImports(source: string): { spec: string; names: string[] }[] {
    const found: { spec: string; names: string[] }[] = [];
    const IMPORT = /import\s+(type\s+)?([\s\S]*?)\s+from\s+["']([^"']+)["']/g;
    for (const match of source.matchAll(IMPORT)) {
      if (match[1]) continue;
      const clause = match[2];
      const names: string[] = [];
      const braces = clause.match(/\{([\s\S]*)\}/);
      if (braces) {
        for (const part of braces[1].split(",")) {
          const item = part.trim();
          if (!item || item.startsWith("type ")) continue;
          names.push(item.split(/\s+as\s+/)[0].trim());
        }
      }
      const head = clause.replace(/\{[\s\S]*\}/, "").replace(/,/g, " ").trim();
      if (head.startsWith("* as ")) names.push("*");
      else if (head) names.push("default");
      found.push({ spec: match[3], names });
    }
    return found;
  }

  /** `AppShell` is a component; `THEME_BOOT_SCRIPT` (all capitals) and `consoleOrigin` are values. A default export here is always a component. */
  function boundaryIsComponentName(name: string): boolean {
    return /^[A-Z]/.test(name) && !/^[A-Z0-9_]+$/.test(name);
  }

  function boundaryViolations(): string[] {
    const files = ROOTS.flatMap((root) => boundarySourceFiles(join(APP, root)));
    const violations: string[] = [];
    for (const file of files) {
      if (boundaryIsClient(file)) continue;
      for (const { spec, names } of boundaryValueImports(readFileSync(file, "utf8"))) {
        const target = boundaryResolveLocal(file, spec);
        if (!target || !boundaryIsClient(target)) continue;
        for (const name of names) {
          if (name === "default" || boundaryIsComponentName(name)) continue;
          violations.push(`${relative(APP, file)} imports ${name} from client module ${relative(APP, target)}`.replace(/\\/g, "/"));
        }
      }
    }
    return violations;
  }

  it("a server module takes only components from a client module", () => {
    expect(boundaryViolations()).toEqual([]);
  });

  // Restored by the lead (H-test-diet): the guard for React #418 (H-hydration-418). The browser test that
  // caught it is gone, so this is the only check left that the document's boot script is inlined.
  it("the document renders the theme boot script from a module the server inlines", () => {
    const document = readFileSync(join(APP, "components", "locale-document.tsx"), "utf8");
    const source = boundaryValueImports(document).find(({ names }) => names.includes("THEME_BOOT_SCRIPT"));
    expect(source, "LocaleDocument imports THEME_BOOT_SCRIPT").toBeDefined();
    const target = boundaryResolveLocal(join(APP, "components", "locale-document.tsx"), source!.spec);
    expect(target).not.toBeNull();
    expect(boundaryIsClient(target!)).toBe(false);
  });

  it("the check sees a value taken from a client module", () => {
    // Guard on the guard: the parser must report the shape that caused #418.
    const parsed = boundaryValueImports(`import { THEME_BOOT_SCRIPT, ThemeToggle } from "./theme-toggle";
import type { Locale } from "@/i18n";`);
    expect(parsed).toEqual([{ spec: "./theme-toggle", names: ["THEME_BOOT_SCRIPT", "ThemeToggle"] }]);
    expect(parsed[0].names.filter((name) => !boundaryIsComponentName(name))).toEqual(["THEME_BOOT_SCRIPT"]);
    expect(DIRECTIVE.test(`"use client";
`)).toBe(true);
    expect(DIRECTIVE.test(`// note
"use client";
`)).toBe(true);
    expect(DIRECTIVE.test(`import x from "y";
"use client";
`)).toBe(false);
  });
});

describe("theme.test.tsx", () => {
  const THEME = readFileSync(resolve(APP, "app", "theme.css"), "utf8").replace(/\r\n/g, "\n");
  const TOKENS = JSON.parse(
    readFileSync(resolve(APP, "..", "..", "docs", "ux", "brand", "tokens.json"), "utf8"),
  ) as { color: { tokens: { name: string; value: { light: string; dark: string } }[] } };

  it("is current with the brand tokens", () => {
    const out = execFileSync(process.execPath, [resolve(APP, "scripts", "build-tokens.mjs"), "--check"], {
      encoding: "utf8",
    });
    expect(out).toContain("app/theme.css is current.");
  });

  it("declares every brand colour for light and for dark", () => {
    const [light, rest] = THEME.split("@media (prefers-color-scheme: dark)");
    for (const { name, value } of TOKENS.color.tokens) {
      expect(light).toContain(`--ns-${name}: ${value.light};`);
      expect(rest).toContain(`--ns-${name}: ${value.dark};`);
    }
    expect(THEME).toContain(':root:not([data-theme="light"])');
    expect(THEME).toContain(':root[data-theme="dark"]');
  });

  it("routes every role through a brand variable and keeps retired names out", () => {
    for (const role of ["paper", "leaf", "ink", "ink-muted", "rule", "evidence", "focus", "include", "anchor"]) {
      expect(THEME).toMatch(new RegExp(`--color-${role}: var\\(--ns-[a-z-]+\\);`));
    }
    for (const retired of ["--color-surface", "--color-raised", "--color-accent"]) {
      expect(THEME).not.toContain(retired);
    }
  });
});

describe("triage.test.tsx", () => {
  it("triage copy: has the same keys and holes in every locale, none empty", () => {
    const keys = Object.keys(TRIAGE_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) {
      expect(Object.keys(TRIAGE_COPY[locale]).sort()).toEqual(keys);
      for (const key of keys as (keyof typeof TRIAGE_COPY.en)[]) {
        const value = TRIAGE_COPY[locale][key];
        expect(value.trim(), `${locale}/${key}`).not.toBe("");
        const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
        expect(holes(value), `${locale}/${key}`).toEqual(holes(TRIAGE_COPY.en[key]));
      }
    }
    expect(() => tc("en", "refused")).toThrow(/needs \{code\}/);
  });
});

describe("workspaces.test.tsx", () => {
  it("has every key in every locale, and the header marks the screen current", () => {
    const keys = Object.keys(WORKSPACES_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(WORKSPACES_COPY[locale]).sort()).toEqual(keys);
    expect(currentNavId("/ar/workspaces/", "ar")).toBe("workspaces");
    for (const code of ["WORKSPACE_TITLE_INVALID", "WORKSPACE_EXISTS", "WORKSPACE_PATH_REFUSED", "WORKSPACE_ROOT_UNAVAILABLE", "WORKSPACE_NOT_VALID", "WORKSPACE_BUSY", "RESTART_UNSUPPORTED"]) {
      for (const locale of SUPPORTED_LOCALES) expect(stateCopy(locale, code).known).toBe(true);
    }
  });
});

describe("screening-adopted.test.tsx", () => {
  // Moved with the merge of PR 298 (H-test-diet): key parity and the decided phrase of the adoption copy.
  it("has every key in en, fr and ar, and the decided phrase in English", () => {
    const keys = Object.keys(ADOPTION_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(ADOPTION_COPY[locale]).sort()).toEqual(keys);
    expect(ADOPTION_COPY.en.phraseOne).toBe("Stored from the agent's draft without being read one by one");
    expect(ADOPTION_COPY.en.notCounted).toContain("stored from the agent's draft without being read one by one");
    expect(CHARTING_COPY.en["charting.study.taAdopted"]).toBe("Stored from the agent's draft without being read one by one");
    expect(PUBLISH_COPY.en["check.human_provenance"]).toBe("Every decision is recorded as the reviewer's");
    expect(PUBLISH_COPY.en["check.adopted_decisions_declared"]).toBe("Decisions stored from drafts are declared");
    for (const locale of SUPPORTED_LOCALES) {
      expect(CHARTING_COPY[locale]["charting.study.taAdopted"]).toBeTruthy();
      expect(PUBLISH_COPY[locale].look).toBeTruthy();
    }
  });

  it("pins the fr and ar wording of the phrase", () => {
    expect(ADOPTION_COPY.fr.phraseOne).toBe("Enregistrée depuis le brouillon de l'agent sans être lue une à une");
    expect(ADOPTION_COPY.ar.phraseOne).toBe("حُفظ من مسودة الوكيل دون قراءته واحدًا واحدًا");
    expect(adoptionText("fr", "sampleOwed", { k: 50 })).toBe("Un échantillon de 50 exclusions adoptées est dû.");
    expect(adoptionText("ar", "sampleOwed", { k: 50 })).toBe("عيّنة من 50 استبعادًا معتمَدًا مستحقة.");
  });
});
