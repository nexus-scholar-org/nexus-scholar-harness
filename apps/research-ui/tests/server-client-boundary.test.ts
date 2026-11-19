import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

import { describe, expect, it } from "vitest";

/**
 * What a server module may take from a client module (H-hydration-418).
 *
 * A file without `"use client"` is rendered on the server. When it imports from a
 * `"use client"` module, Next does not inline the import: it writes a client
 * reference into the page's payload, and the browser resolves it only once that
 * module's chunks have loaded. For a component that is the point. For a plain value
 * it is a hydration hazard: `LocaleDocument` took `THEME_BOOT_SCRIPT` (a string) from
 * `theme-toggle.tsx`, so `<head>` carried `__html: "$f"`, a reference to that module.
 * When the chunks arrived after hydration began, `<head>` suspended and was replayed,
 * React's hydration cursor was left on `<meta charset>`, and the whole document failed
 * to hydrate (React #418, twice per load, on every page).
 *
 * The rule: from a client module, a server module imports components only (names
 * that start with a capital letter) and types. Shared values live in a module with no
 * directive, which both sides can import.
 */

const APP = resolve(import.meta.dirname, "..");
const ROOTS = ["app", "components", "lib", "i18n"];

function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) out.push(...sourceFiles(path));
    else if (/\.(ts|tsx)$/.test(name) && !name.endsWith(".d.ts")) out.push(path);
  }
  return out;
}

const DIRECTIVE = /^\s*(?:\/\/[^\n]*\n\s*|\/\*[\s\S]*?\*\/\s*)*["']use client["']/;
const isClient = (file: string) => DIRECTIVE.test(readFileSync(file, "utf8"));

function resolveLocal(from: string, spec: string): string | null {
  const base = spec.startsWith("@/") ? resolve(APP, spec.slice(2)) : spec.startsWith(".") ? resolve(dirname(from), spec) : null;
  if (!base) return null;
  for (const candidate of [base, `${base}.ts`, `${base}.tsx`, join(base, "index.ts"), join(base, "index.tsx")]) {
    if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
  }
  return null;
}

/** The value names a module imports from each local specifier (type-only imports and names left out). */
function valueImports(source: string): { spec: string; names: string[] }[] {
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
function isComponentName(name: string): boolean {
  return /^[A-Z]/.test(name) && !/^[A-Z0-9_]+$/.test(name);
}

function boundaryViolations(): string[] {
  const files = ROOTS.flatMap((root) => sourceFiles(join(APP, root)));
  const violations: string[] = [];
  for (const file of files) {
    if (isClient(file)) continue;
    for (const { spec, names } of valueImports(readFileSync(file, "utf8"))) {
      const target = resolveLocal(file, spec);
      if (!target || !isClient(target)) continue;
      for (const name of names) {
        if (name === "default" || isComponentName(name)) continue;
        violations.push(`${relative(APP, file)} imports ${name} from client module ${relative(APP, target)}`.replace(/\\/g, "/"));
      }
    }
  }
  return violations;
}

describe("server and client modules", () => {
  it("a server module takes only components from a client module", () => {
    expect(boundaryViolations()).toEqual([]);
  });

  it("the document renders the theme boot script from a module the server inlines", () => {
    const document = readFileSync(join(APP, "components", "locale-document.tsx"), "utf8");
    const source = valueImports(document).find(({ names }) => names.includes("THEME_BOOT_SCRIPT"));
    expect(source, "LocaleDocument imports THEME_BOOT_SCRIPT").toBeDefined();
    const target = resolveLocal(join(APP, "components", "locale-document.tsx"), source!.spec);
    expect(target).not.toBeNull();
    expect(isClient(target!)).toBe(false);
  });

  it("the check sees a value taken from a client module", () => {
    // Guard on the guard: the parser must report the shape that caused #418.
    const parsed = valueImports(`import { THEME_BOOT_SCRIPT, ThemeToggle } from "./theme-toggle";\nimport type { Locale } from "@/i18n";`);
    expect(parsed).toEqual([{ spec: "./theme-toggle", names: ["THEME_BOOT_SCRIPT", "ThemeToggle"] }]);
    expect(parsed[0].names.filter((name) => !isComponentName(name))).toEqual(["THEME_BOOT_SCRIPT"]);
    expect(DIRECTIVE.test(`"use client";\n`)).toBe(true);
    expect(DIRECTIVE.test(`// note\n"use client";\n`)).toBe(true);
    expect(DIRECTIVE.test(`import x from "y";\n"use client";\n`)).toBe(false);
  });
});
