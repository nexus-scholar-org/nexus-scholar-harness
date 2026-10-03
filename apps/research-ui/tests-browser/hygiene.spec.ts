import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";

import { expect, APP_ROOT, report, test } from "./helpers";

/**
 * Supply-chain and privacy hygiene for the browser suite.
 *
 * The `page` fixture in `helpers.ts` already fails any test in which the
 * running app requests a non-localhost origin, which is the substantive check.
 * These two close the ways that guard can be bypassed: a URL baked into the
 * served markup that is never fetched, and an analytics global that is loaded
 * from the same origin.
 */

const PLAYWRIGHT_CONFIG = join(APP_ROOT, "playwright.config.ts");

/**
 * Tailwind's built-in colour families. None of them is a UI-01c role, so any
 * occurrence of one in our own source or in the shipped stylesheet is by
 * definition the retired palette leaking back in.
 */
const RAW_PALETTE_FAMILIES = [
  "slate", "gray", "zinc", "neutral", "stone",
  "red", "orange", "amber", "yellow", "lime", "green", "emerald", "teal",
  "cyan", "sky", "blue", "indigo", "violet", "purple", "fuchsia", "pink", "rose",
];

/** Utility prefixes that take a colour argument. */
const COLOUR_UTILITY_PREFIXES = [
  "text", "bg", "border", "ring", "outline", "decoration", "divide",
  "placeholder", "caret", "accent", "fill", "stroke",
  "from", "via", "to", "shadow", "inset",
];

/**
 * Matches a raw-palette utility **as written in source**: `text-slate-500`,
 * `bg-slate-900/30`, `hover:text-blue-700`.
 *
 * A1 forbids a raw hex as well as a raw palette utility, and a palette-name regex
 * cannot see either of the two ways a hex gets into a class:
 * `text-[#62748e]` and `bg-[oklch(...)]`. Both are matched here as alternatives
 * on the same colour-utility prefixes, so they cannot be reached around A1.
 *
 * The alternatives were checked against every arbitrary value this application
 * actually uses before being added — `grid-cols-[1.5rem_minmax(0,1fr)]`,
 * `text-[0.6875rem]`, `tracking-[0.12em]`, `aria-[current]`. None matches: the
 * hex branch needs `#`, the colour-function branch needs a function call, and
 * `text-[0.6875rem]` — a font size on a colour-named prefix — is precisely the
 * case a naive "reject anything after `text-`" rule would get wrong. There is no
 * `var(--…)` inside an arbitrary value anywhere in the tree, so there is no
 * legitimate token reference for these branches to collide with.
 */
const RAW_PALETTE_UTILITY_IN_SOURCE = new RegExp(
  String.raw`\b(?:(?:${COLOUR_UTILITY_PREFIXES.join("|")})-(?:${RAW_PALETTE_FAMILIES.join("|")})(?:-\d{2,3})?(?:/\d{1,3})?\b|(?:${COLOUR_UTILITY_PREFIXES.join("|")})-\[#[0-9a-fA-F]{3,8}\]|(?:${COLOUR_UTILITY_PREFIXES.join("|")})-\[(?:oklch|oklab|rgba?|hsla?|lab|lch|color)\()`,
  "g",
);

/**
 * The same thing **as it appears in a shipped stylesheet**, where the class is a
 * `.`-prefixed selector and the opacity slash may be escaped (`.bg-slate-900\/30`).
 *
 * The two arbitrary-value branches are included here as well as in the source
 * regex. If a hex ever reached the build by being *described* in prose, assertion
 * 2 would never see it — that is the whole failure mode this guard exists for —
 * so the shipped-bytes gate closes the same door.
 */
const RAW_PALETTE_UTILITY_IN_CSS = new RegExp(
  // Tailwind ships an arbitrary value escaped, e.g. `.text-\[\#62748e\]`. So the
  // bracket must be matched as a *backslash followed by* `[` (`\\\[`), not as a
  // bare `\[`, which would match the unescaped source spelling and therefore
  // nothing at all in the stylesheet. The backslash before `#` is optional so
  // either spelling is caught.
  String.raw`\.(?:(?:${COLOUR_UTILITY_PREFIXES.join("|")})-(?:${RAW_PALETTE_FAMILIES.join("|")})(?:-\d{2,3})?(?:\\?/\d{1,3})?(?![\w-])|(?:${COLOUR_UTILITY_PREFIXES.join("|")})-\\\[\\?#[0-9a-fA-F]{3,8}\\\]?|(?:${COLOUR_UTILITY_PREFIXES.join("|")})-\\\[(?:oklch|oklab|rgba?|hsla?|lab|lch|color))`,
  "g",
);

/** A raw-palette *theme variable* in the shipped CSS, e.g. `--color-slate-500`. */
const RAW_PALETTE_VARIABLE_IN_CSS = new RegExp(
  `--color-(?:${RAW_PALETTE_FAMILIES.join("|")})(?:-[\\w-]+)?(?=\\s*[:,])`,
  "g",
);

/**
 * The three UI-01 tokens and three UI-01 raw hexes retired by UI-01c. Gate 20
 * checks these by name; this test checks them in the bytes the browser receives,
 * which is a stronger statement than "the build output says so".
 */
const RETIRED_TOKENS = ["--color-surface", "--color-raised", "--color-accent"];
const RETIRED_HEXES = ["#f8fafc", "#172033", "#1d4ed8"];

/**
 * Application source we are allowed to scan for colour decisions.
 *
 * The walk is **recursive**, and that is not tidiness. It used to read only the
 * top level of `app/` and `components/`, which was complete while the routes
 * lived directly in `app/`. UI-01d moved them to `app/[locale]/`, and the effect
 * of the non-recursive walk was that the new route files became invisible to this
 * guard: a raw palette utility in `app/[locale]/page.tsx` would have been reported
 * as clean, and a utility used only there (`leading-7`, in `not-found.tsx`) was
 * reported as an emitted utility that no product source referenced — which is the
 * same class of defect as a disabled check, reached by the other direction.
 */
async function sourceFiles(): Promise<string[]> {
  const found: string[] = [];
  const walk = async (dir: string): Promise<void> => {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(path);
        continue;
      }
      if (!entry.isFile()) continue;
      if (!/\.(tsx|css)$/.test(entry.name)) continue;
      found.push(path);
    }
  };
  for (const dir of ["app", "components"]) {
    await walk(join(APP_ROOT, dir));
  }
  return found.sort();
}

/**
 * Strip `/* … *​/` comments from a stylesheet before scanning it.
 *
 * Not cosmetic: Tailwind strips them too. `app/globals.css` documents the
 * retired palette *by name* in prose — as it must, or this guard could not be
 * maintained — and that prose does **not** put `.text-slate-500` in the shipped
 * CSS, because the scanner never sees a comment. Verified on Tailwind 4.3.3.
 *
 * Without this, the guard would report this application's own documentation as a
 * palette defect, and a detector that cries wolf is a disabled detector (the same
 * argument as the `needle` line in the first test below).
 */
function stripCssComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, " ");
}

/**
 * Every class selector the stylesheet actually emits, with variant prefixes
 * stripped (`hover:bg-paper` -> `bg-paper`).
 *
 * Written against selector **preludes** rather than by scanning for dots, because
 * a dot also appears inside `calc()`, `minmax()` and decimal values, and a
 * scanner that picks those up reports nonsense as leaked utilities. Escapes are
 * consumed pairwise so that an escaped `\[` inside a class name is not mistaken
 * for an attribute selector, and commas are split only at bracket depth zero so
 * that `grid-cols-[repeat(auto-fit,minmax(0,1fr))]` stays one selector.
 */
function emittedClassSelectors(css: string): string[] {
  const found = new Set<string>();
  for (const match of css.matchAll(/([^{}]+)\{/g)) {
    const prelude = match[1];
    if (/^\s*@/.test(prelude)) continue; // at-rule, not a selector
    const parts: string[] = [];
    let depth = 0;
    let part = "";
    for (let i = 0; i < prelude.length; i += 1) {
      const ch = prelude[i];
      if (ch === "\\") {
        part += ch + (prelude[i + 1] ?? "");
        i += 1;
        continue;
      }
      if (ch === "[" || ch === "(") depth += 1;
      else if (ch === "]" || ch === ")") depth -= 1;
      if (ch === "," && depth === 0) {
        parts.push(part);
        part = "";
      } else {
        part += ch;
      }
    }
    parts.push(part);
    for (const one of parts) {
      for (const cls of one.matchAll(/\.((?:\\.|[^\\\s:>+~,[)])+)/g)) {
        const name = cls[1].replace(/\\(.)/g, "$1").split(":").pop();
        if (name) found.add(name);
      }
    }
  }
  return [...found].sort();
}

/**
 * The parts of a stylesheet that can legitimately *name* a class: selector
 * preludes and `@apply` arguments. Declaration **values** are deliberately
 * excluded.
 *
 * This exists because of `overflow: visible` in `globals.css`. Feeding a whole
 * stylesheet to {@link hasClassToken} made `visible` look like a live utility, so
 * the prose collision in a comment — which really does emit `.visible` — was
 * scored as "used", and its allow-list entry was reported as stale. The guard was
 * masking one of the exact leaks it exists to catch. A declaration value is not a
 * class usage, so it must not be allowed to count as one.
 */
function cssClassUsages(css: string): string {
  const withoutComments = stripCssComments(css);
  const chunks: string[] = [];
  // A prelude is the run of text before an opening brace, so it cannot contain a
  // declaration: `overflow: visible;` is followed by `}` or `;`, never `{`.
  for (const match of withoutComments.matchAll(/([^{}]+)\{/g)) chunks.push(match[1]);
  for (const match of withoutComments.matchAll(/@apply\s+([^;}]+)/g)) chunks.push(match[1]);
  return chunks.join("\n");
}

/**
 * Does `cls` occur in `source` as a complete class token?
 *
 * The optional variant chain in the middle is load-bearing twice over. An earlier
 * pass that tested for a bare substring lost thirteen used utilities to false
 * "apparent loss" verdicts, because `hidden` is emitted as `.lg\:hidden` and the
 * naive test never matched it. The chain then has to admit **bracketed** variants
 * as well as bare ones: `aria-[current]:decoration-evidence` is real usage in
 * `primary-nav.tsx`, and a `[\w-]+:` chain silently missed it, reporting a
 * genuinely-used utility as an unexplained leak.
 *
 * Requiring a boundary *after* the name is equally load-bearing: it is what stops
 * `rounded` from matching inside `rounded-md`, which is the difference between
 * "collateral" and "leak" below.
 */
function hasClassToken(source: string, cls: string): boolean {
  const escaped = cls.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // Each variant segment requires at least one character before its colon, so the
  // group can never match the empty string and cannot backtrack catastrophically.
  const variantChain = "(?:[\\w\\[\\]=%.-]+:)*";
  return new RegExp(
    `(?:^|[\\s"'\`({\\[])(${variantChain})${escaped}(?![\\w-])`,
    "m",
  ).test(source);
}

/**
 * Emitted utilities that are **comment-harvested prose collisions**, not leaks.
 *
 * Every one of these is an ordinary English word that Tailwind also happens to
 * ship as a utility. Tailwind's scanner reads `.tsx` as plain text and strips no
 * comments, so a word in prose becomes a real rule in the stylesheet: "the
 * columns collapse", "a contents page", "a marginal ordinal", "a single ruled
 * table", "rounded", "drop shadow", "visible".
 *
 * They are allow-listed rather than de-tokenised because de-tokenising ordinary
 * English would damage the very prose that explains this screen's visual
 * decisions — there is no honest way to describe a ruled table without the word
 * "table". Contrast the three real leaks, which *were* class-shaped tokens in
 * backticks and are now de-tokenised, per R-N1.
 *
 * Established empirically, not assumed. The reviewer's note attributed these six
 * names to "Tailwind group collateral emitted alongside genuinely-used members".
 * A build with every `.tsx` comment stripped settles the question: all seven
 * selectors disappear, so they are prose harvests, not group collateral. That
 * same measurement is what produced the seventh name, `collapse`, which the
 * reviewer's list of six missed. `rounded` is on this list on its own evidence —
 * it vanishes with the comments, so it is not a bare member dragged in by
 * `rounded-full`.
 *
 * This is deliberately not the gate-19 mistake. Gate 19 enumerated twelve *tokens*
 * and let a thirteenth arrive silently; this fails closed on anything
 * unrecognised, reports the entire unused-emitted set on every run, and asserts
 * that this list is not stale. A name not listed here is treated as a leak.
 */
const COLLATERAL_EMITTED = new Set([
  "collapse", // "the columns collapse" — workflow-timeline.tsx
  "contents", // "a contents page" — primary-nav.tsx
  "ordinal", // "a marginal ordinal" — evidence-chain / workflow-timeline
  "rounded", // "rounded" in the shape prose; not a group member of rounded-full
  "shadow", // "shadowed" / "drop shadow" in the shape prose
  "table", // "a single ruled table" — page.tsx / workflow-timeline
  "visible", // prose "visible"; deliberately NOT scored via `overflow: visible`
]);

test.describe("browser-suite hygiene", () => {
  test("the served HTML references no absolute non-localhost URL", async ({ request }) => {
    const response = await request.get("/");
    expect(response.status()).toBe(200);
    const html = await response.text();

    const absolute = Array.from(
      html.matchAll(/(?:src|href|action|data-src)\s*=\s*["'](https?:\/\/[^"']+)["']/gi),
    ).map((match) => match[1]);
    report(`absolute URLs in served HTML: ${JSON.stringify(absolute)}`);
    expect(
      absolute.filter((url) => new URL(url).hostname !== "localhost"),
      "the served document must not point at anything but localhost",
    ).toEqual([]);

    // No analytics or tag-manager payload is inlined into the document. The
    // needles are deliberately specific: an earlier pass used the bare string
    // "G-", which matched `ring-1` in a Tailwind class and failed the run for
    // no reason. A detector that cries wolf is a disabled detector.
    const payloads = [
      "googletagmanager.com",
      "google-analytics.com",
      "gtag/js",
      "plausible.io",
      "segment.io",
      "hotjar.com",
      /gtag\(/i,
      /\bG-[A-Z0-9]{6,}\b/,
    ];
    const found = payloads.filter((needle) =>
      typeof needle === "string"
        ? html.toLowerCase().includes(needle.toLowerCase())
        : needle.test(html),
    );
    report(`analytics payloads in served HTML: ${JSON.stringify(found.map(String))}`);
    expect(found.map(String)).toEqual([]);
  });

  test("the running page exposes no analytics globals", async ({ page }) => {
    await page.goto("/en");
    const globals = await page.evaluate(() =>
      ["gtag", "ga", "analytics", "_paq", "plausible", "segment", "intercom", "hotjar"]
        .filter((name) => (window as unknown as Record<string, unknown>)[name] !== undefined)
        .map((name) => name),
    );
    report(`analytics globals on window: ${JSON.stringify(globals)}`);
    expect(globals).toEqual([]);
  });

  test("the Playwright config carries no credential-shaped literal", async () => {
    const source = await readFile(PLAYWRIGHT_CONFIG, "utf8");
    // A crude but honest sweep: nothing that looks like a bearer token, an
    // API key assignment, or a hard-coded auth header.
    const suspicious = source.match(
      /(bearer\s+[a-z0-9._-]{16,}|sk-[a-z0-9]{16,}|(?:api[_-]?key|token|password|secret|authorization)\s*[:=]\s*["'][^"']{6,}["'])/gi,
    );
    report(`credential-shaped literals in playwright.config.ts: ${JSON.stringify(suspicious ?? [])}`);
    expect(suspicious ?? []).toEqual([]);
  });

  /**
   * The token-discipline guard (packet UI-01c repair pass, finding R1).
   *
   * Gate 19 was a **drift detector**; gate 20 is an **enumeration** of the twelve
   * tokens that exist today. Trading the first for the second lost two general
   * properties, and this test is where they come back. The human ratified the
   * palette change on exactly this condition — recorded on gate 19's row in
   * `GATES.md` §1.
   *
   * 1. **No dangling token reference.** Every `var(--token)` written under `app/`
   *    or `components/` is declared in `app/globals.css`, *and* actually reaches
   *    the browser. CSS custom properties fail **silently**: `var(--color-raised)`
   *    on a deleted token resolves to nothing, the element renders unstyled, and
   *    `next build` reports success. Nothing but an explicit check catches it.
   * 2. **No raw palette utility in source.** A1 was a source convention with zero
   *    enforcement. This is the enforcement.
   * 3. **No retired palette in the shipped stylesheet**, read over HTTP from the
   *    running server rather than read off `.next/`, so the evidence is about the
   *    product and not about a build directory.
   *
   * (3) is also what protects the `@source not` directives in `app/globals.css`.
   * Tailwind harvests class names out of Markdown prose, so this comment and
   * `GATES.md` would otherwise be enough to bring `.text-slate-500` back with
   * UI-00b's `#62748e` — which passes axe and fails nothing.
   *
   * Two traps, both hit while writing this test, both of which fail *silently*:
   *
   * - **This file was itself a source.** It is a `.ts` file, Tailwind reads it as
   *   a class-name source, and Tailwind does not strip comments from `.ts`. The
   *   JSDoc above names the retired palette, so excluding only `*.md` left the
   *   defect in place — the guard was regenerating what it guards. The
   *   `@source not` directives therefore exclude `../tests/**` and
   *   `../tests-browser/**` too.
   * - **`@source` paths are relative to `globals.css`, i.e. to `app/`, not to the
   *   app root.** `./tests-browser/**` resolves to a directory that does not
   *   exist, excludes nothing, and builds cleanly.
   *
   * (3) is what catches either mistake, on a clean tree, with a message naming
   * the selectors. That is how the first one was found.
   */
  test("no dangling token, no raw palette utility, and no retired palette in the shipped CSS", async ({ page, request }) => {
    const globals = await readFile(join(APP_ROOT, "app", "globals.css"), "utf8");

    // --- 1a. every referenced var() token is declared -----------------------
    const declared = new Set(
      Array.from(stripCssComments(globals).matchAll(/^\s*(--[a-z0-9-]+)\s*:/gm), (m) => m[1]),
    );
    const dangling: string[] = [];
    const referenced = new Set<string>();
    for (const file of await sourceFiles()) {
      const raw = await readFile(file, "utf8");
      const source = file.endsWith(".css") ? stripCssComments(raw) : raw;
      for (const match of source.matchAll(/var\(\s*(--[a-z0-9-]+)/g)) {
        referenced.add(match[1]);
        if (!declared.has(match[1])) {
          dangling.push(`${file.slice(APP_ROOT.length)} references undeclared ${match[1]}`);
        }
      }
    }
    report(`tokens declared in globals.css: ${declared.size}; referenced in app/+components/: ${referenced.size}`);
    expect(
      dangling,
      "every var(--token) in app/ or components/ must be declared in app/globals.css, " +
        "or it resolves to nothing at runtime and no build error is raised",
    ).toEqual([]);

    // --- 1b/2. no raw palette utility in component/page markup --------------
    // Scoped to `.tsx`, which is where A1 applies. `globals.css` is excluded
    // because Tailwind ignores its comments, so a utility named there in prose
    // is documentation, not a decision — and (3) below is the real backstop.
    const rawInSource: string[] = [];
    for (const file of (await sourceFiles()).filter((path) => path.endsWith(".tsx"))) {
      const source = await readFile(file, "utf8");
      for (const match of source.matchAll(RAW_PALETTE_UTILITY_IN_SOURCE)) {
        rawInSource.push(`${file.slice(APP_ROOT.length)}: ${match[0]}`);
      }
    }
    report(`raw-palette utilities in app/+components source: ${JSON.stringify(rawInSource)}`);
    expect(
      rawInSource,
      "A1: components and pages must use semantic colour roles (bg-paper, text-ink-muted, " +
        "border-rule, ...), never a raw Tailwind palette utility. Declared roles are in app/globals.css.",
    ).toEqual([]);

    // --- 3. the bytes the browser actually receives -------------------------
    await page.goto("/en");
    const hrefs = await page.evaluate(() =>
      Array.from(document.querySelectorAll<HTMLLinkElement>('link[rel~="stylesheet"]')).map(
        (link) => link.href,
      ),
    );
    expect(hrefs.length, "the page must serve at least one stylesheet for this guard to mean anything").toBeGreaterThan(0);
    const sheets: string[] = [];
    for (const href of hrefs) {
      const response = await request.get(href);
      expect(response.status(), `stylesheet ${href} must be served`).toBe(200);
      sheets.push(await response.text());
    }
    const css = sheets.join("\n");
    report(`shipped CSS: ${hrefs.length} stylesheet(s), ${css.length} bytes, from ${hrefs.join(", ")}`);

    const rawInCss = Array.from(css.matchAll(RAW_PALETTE_UTILITY_IN_CSS), (m) => m[0]);
    const rawVars = Array.from(css.matchAll(RAW_PALETTE_VARIABLE_IN_CSS), (m) => m[0]);
    const retired = [
      ...RETIRED_TOKENS.filter((token) => css.includes(token)),
      ...RETIRED_HEXES.filter((hex) => css.includes(hex)),
    ];
    report(`shipped CSS raw-palette utilities: ${JSON.stringify(rawInCss)}`);
    report(`shipped CSS raw-palette variables: ${JSON.stringify(rawVars)}`);
    report(`shipped CSS retired tokens/hexes: ${JSON.stringify(retired)}`);
    expect(
      [...rawInCss, ...rawVars],
      "the shipped stylesheet must emit no Tailwind palette utility or variable. " +
        "These are almost certainly being harvested from Markdown prose: check the " +
        "@source not directives at the top of app/globals.css are still present.",
    ).toEqual([]);
    expect(
      retired,
      "the shipped stylesheet must not carry any UI-01 token or raw hex retired by UI-01c",
    ).toEqual([]);

    // --- 1c. every referenced token actually reaches the browser ------------
    const notShipped = Array.from(referenced).filter((token) => !css.includes(`${token}:`));
    report(`referenced tokens absent from shipped CSS: ${JSON.stringify(notShipped)}`);
    expect(
      notShipped,
      "a token can be declared in globals.css and still never be shipped if Tailwind " +
        "does not scan the file it lives in. Declare it somewhere that is scanned.",
    ).toEqual([]);

    // --- 4. no emitted utility may lack a non-comment source -----------------
    // The invariant `globals.css` states at the top of the file. It cannot be
    // checked in source alone, because the defect is by definition a utility that
    // source does *not* use, so this runs emitted-vs-used over the served bytes.
    const live: string[] = [];
    let rawAll = "";
    for (const file of await sourceFiles()) {
      const text = await readFile(file, "utf8");
      rawAll += `\n${text}`;
      // Block and line comments both go: Tailwind's scanner reads .ts/.tsx as
      // plain text and strips neither, so a name in a `//` comment is harvested
      // exactly like one in a `/* */` comment. Anchored to line starts so that a
      // `//` inside a string is not treated as a comment.
      const withoutComments = stripCssComments(text).replace(/^\s*\/\/.*$/gm, " ");
      // A stylesheet counts as a *usage* only where it can legitimately name a
      // class — selectors and `@apply`. Otherwise a declaration value like
      // `overflow: visible` scores as a live `visible`, which hides the fact that
      // the only real `visible` in this app is a word in a comment.
      live.push(file.endsWith(".css") ? cssClassUsages(text) : withoutComments);
    }
    const liveAll = live.join("\n");

    const emitted = emittedClassSelectors(css);
    const unused = emitted.filter((cls) => !hasClassToken(liveAll, cls));
    const collateral = unused.filter((cls) => COLLATERAL_EMITTED.has(cls));
    const commentOnly = unused.filter(
      (cls) => !COLLATERAL_EMITTED.has(cls) && hasClassToken(rawAll, cls),
    );
    const unexplained = unused.filter(
      (cls) => !COLLATERAL_EMITTED.has(cls) && !hasClassToken(rawAll, cls),
    );
    const staleEntries = [...COLLATERAL_EMITTED].filter((cls) => !unused.includes(cls));

    report(`emitted class selectors: ${emitted.length}, used: ${emitted.length - unused.length}`);
    report(`collateral (allow-listed): ${JSON.stringify(collateral)}`);
    report(`allow-listed but no longer emitted: ${JSON.stringify(staleEntries)}`);
    report(`emitted with no source anywhere: ${JSON.stringify(unexplained)}`);
    report(`emitted from a comment only: ${JSON.stringify(commentOnly)}`);

    expect(
      unexplained,
      "an emitted utility that appears in no product source at all is either a " +
        "comment-harvested collision listed in COLLATERAL_EMITTED, or a gap in this " +
        "test's selector parser. If it really is unavoidable prose, add it to " +
        "COLLATERAL_EMITTED with the reason, so the decision is recorded rather than assumed.",
    ).toEqual([]);
    expect(
      commentOnly,
      "every emitted utility needs a source in product code, not in a comment. Tailwind does not " +
        "strip comments from .ts/.tsx, so a comment naming a utility compiles it — including the " +
        "elevation and corner-radius classes UI-01c removed. Break the token in the prose " +
        "(for example `rounded-*`) or use a semantic role. See GATES.md 3.7.9.",
    ).toEqual([]);
    expect(
      staleEntries,
      "COLLATERAL_EMITTED names utilities this build no longer emits. Remove the stale entries so " +
        "the allow-list stays exactly as large as the evidence requires.",
    ).toEqual([]);
  });
});
