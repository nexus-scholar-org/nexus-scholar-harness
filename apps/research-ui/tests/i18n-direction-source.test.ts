import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

import { describe, expect, it } from "vitest";

/**
 * Direction and literal-string guards over the source itself (packet UI-01d,
 * N9-N12).
 *
 * These are the four checks that cannot be expressed by rendering something and
 * looking at it, because each one is about a *class of mistake* spread across the
 * tree rather than about one node: a hard-coded accessible name, a physical
 * property quietly reintroduced next to a logical one, a mirrored icon, or a
 * locale read out of the browser. A render test would only ever see the mistakes
 * that happen to sit on the one route that exists today.
 *
 * They are source scans, so they are also the checks most able to rot into a
 * tautology. Three things keep them honest:
 *
 * - every guard reports `file:line` for each hit, so a red run names the site;
 * - every guard asserts it actually read a non-trivial number of files, so an
 *   empty scan root cannot pass by finding nothing;
 * - the class patterns come from the packet with their width suffixes
 *   **optional**. That detail is measured, not stylistic: `border-l(?![\w-])`
 *   does not match `border-l-2`, so a suffixed border would slip past the
 *   intuitive spelling of the same guard. The optional suffix is what catches it.
 */

/**
 * The application root, resolved rather than assumed.
 *
 * `import.meta.url` is not a `file:` URL under Vitest's transform, so it cannot
 * be handed to `fileURLToPath`; and the suite may be started from the repository
 * root as well as from this application. Both candidates are therefore checked
 * against a file that must exist, and the check is an assertion rather than a
 * silent fallback — a root that resolved to the wrong directory would otherwise
 * turn every guard below into a scan of nothing.
 */
function resolveAppRoot(): string {
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

const APP_ROOT = resolveAppRoot();

/** Every `.ts`/`.tsx` file under `dir`, recursively, as POSIX-ish relative paths. */
function sourceFiles(dir: string): string[] {
  const absolute = join(APP_ROOT, dir);
  const found: string[] = [];
  const walk = (current: string): void => {
    for (const entry of readdirSync(current)) {
      const path = join(current, entry);
      if (statSync(path).isDirectory()) {
        walk(path);
      } else if (/\.(ts|tsx)$/.test(entry)) {
        found.push(relative(APP_ROOT, path).split(sep).join("/"));
      }
    }
  };
  walk(absolute);
  return found.sort();
}

/** `{ file, line, text }` for each line of `file`, 1-indexed. */
function lines(file: string): Array<{ file: string; line: number; text: string }> {
  return readFileSync(join(APP_ROOT, file), "utf8")
    .split(/\r?\n/)
    .map((text, index) => ({ file, line: index + 1, text }));
}

function hits(files: string[], pattern: RegExp): string[] {
  const found: string[] = [];
  for (const file of files) {
    for (const { line, text } of lines(file)) {
      const match = text.match(pattern);
      if (match) {
        found.push(`${file}:${line}: ${match[0]}`);
      }
    }
  }
  return found;
}

/** `app/**` + `components/**`: the JSX-bearing source the UI ships. */
const UI_SOURCE = [...sourceFiles("app"), ...sourceFiles("components")];

describe("direction and literal-string source guards", () => {
  it("reads the UI source it is meant to guard", () => {
    // Anti-vacuity: a scan root that silently resolved to nothing would make
    // every assertion below pass for the wrong reason.
    expect(UI_SOURCE.length).toBeGreaterThan(5);
    expect(UI_SOURCE.some((file) => file.startsWith("app/"))).toBe(true);
    expect(UI_SOURCE.some((file) => file.startsWith("components/"))).toBe(true);
    expect(UI_SOURCE.some((file) => file.endsWith(".tsx"))).toBe(true);
  });

  it("carries no literal accessible name (N9)", () => {
    // `aria-label="…"`, `title="…"`, `alt="…"` and `placeholder="…"` are user-visible
    // strings that bypass the catalogs by construction. A translated label is a
    // catalog lookup written as an expression, so these four attributes with a
    // string literal have no legitimate spelling left in this application.
    const found = hits(UI_SOURCE, /(aria-label|title|alt|placeholder)="/);
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
      expect(hits(UI_SOURCE, pattern), label).toEqual([]);
    }
  });

  it("declares no physical layout property in the stylesheet (N10)", () => {
    // The class scan above cannot see a declaration in CSS, and the one physical
    // property this stylesheet still needs is the focus-ring offset — which is
    // physical by definition, because a ring is drawn outward from the element
    // and `outline-offset` has no logical spelling. What must not come back is a
    // directional property.
    const css = readFileSync(join(APP_ROOT, "app/globals.css"), "utf8");
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
    // The disclosure affordance is a chevron, and a chevron is a shape that reads
    // the same in both directions, so flipping it would be a false signal. If a
    // directional icon is ever added, this is where it has to be declared
    // deliberately rather than inherited from a class name.
    const mobile = readFileSync(join(APP_ROOT, "components/mobile-nav.tsx"), "utf8");
    expect(mobile).not.toMatch(/scale-x-\[-1\]/);
    expect(mobile).not.toMatch(/rtl:scale-x/);
  });

  it("reaches for no browser state and no network at render time (N12)", () => {
    // The locale is a URL segment. Reading it from `navigator.language`, from
    // storage, or from a request would make the document's language depend on
    // state the URL does not contain, and the same URL would then render two
    // different languages.
    const scope = [...UI_SOURCE, ...sourceFiles("i18n"), ...sourceFiles("messages")];
    expect(hits(scope, /\bfetch\(/)).toEqual([]);
    expect(hits(scope, /XMLHttpRequest/)).toEqual([]);
    expect(hits(scope, /localStorage/)).toEqual([]);
    expect(hits(scope, /navigator\.language/)).toEqual([]);
  });
});