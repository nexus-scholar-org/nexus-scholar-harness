import { defineConfig } from "@playwright/test";

/**
 * The 30 % expansion gate (packet UI-01d, §13.2, AC-9/AC-9P).
 *
 * This runner exists because the previous formulation of the gate was vacuous
 * (§13.2.1, finding B1): it set `NEXT_PUBLIC_I18N_EXPANSION_PERCENT=30` but served
 * the **already-built** `.next` tree from `playwright.config.ts`, and because
 * `NEXT_PUBLIC_*` is inlined at build time, that tree contained no expansion at
 * all. The gate measured a build with zero inflation and passed, which is the
 * worst possible failure for this gate: it looked green and proved nothing.
 *
 * Three properties of the block below are load-bearing, and each one exists to
 * close a specific way of repeating B1:
 *
 * 1. **The command runs `npm run build` itself.** It does not assume `.next`
 *    exists and does not attach to it, so the served bytes are produced by this
 *    configuration. `npm run build` is `next build` (`package.json`), unchanged —
 *    D-I18N-04 holds and `package.json` stays byte-frozen.
 * 2. **`NEXT_DIST_DIR=.next-longstrings` writes to a different directory**, so
 *    this build can neither read nor overwrite `.next`. A separate port already
 *    prevents serving collision and a separate `distDir` already prevents
 *    clobbering; both, because the failure being repaired was a build shared
 *    between two configurations.
 * 3. **`env` is on the `webServer`, so it applies to the build step too.** This
 *    is the detail B1 turned on: putting the variable on `next start` alone would
 *    leave the inlined constant at zero, because the value is baked in when the
 *    bundle is compiled.
 *
 * The gate's own precondition — that the served prose really is ≥30 % longer
 * than the catalog source — lives in `tests-long-strings/long-strings.spec.ts`,
 * not here. A runner cannot assert anything about the build it started.
 */

const PORT = 3121;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./tests-long-strings",
  // Nested inside the main suite's already-ignored `test-results/` rather than
  // given its own sibling directory. The repo root ignores
  // `apps/research-ui/test-results/` but not a second top-level `test-results-*`
  // tree, and packet §13.2.4 authorises exactly one line in the application's
  // `.gitignore` (`.next-longstrings/`), so a sibling output directory would have
  // required either an unauthorised second ignore rule or an untracked
  // `test-results-longstrings/` polluting every developer's `git status`. Nesting
  // keeps the artifacts isolated — Playwright clears only the directory it is
  // given — while staying inside a path the repository already ignores.
  outputDir: "./test-results/long-strings",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "off",
    video: "off",
    screenshot: "off",
    // Identical to `playwright.config.ts`, so a difference in the measurement is
    // attributable to the strings rather than to the environment.
    deviceScaleFactor: 1,
    colorScheme: "light",
    locale: "en-US",
    timezoneId: "UTC",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: {
    command: "npm run build && npx next start -p 3121",
    url: BASE_URL,
    reuseExistingServer: false,
    timeout: 300_000,
    env: {
      NEXT_PUBLIC_I18N_EXPANSION_PERCENT: "30",
      NEXT_DIST_DIR: ".next-longstrings",
    },
    stdout: "pipe",
    stderr: "pipe",
  },
});