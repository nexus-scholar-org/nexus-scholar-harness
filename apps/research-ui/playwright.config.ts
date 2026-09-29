import { defineConfig } from "@playwright/test";

/**
 * Browser verification runner for the Research UI (packet UI-00b).
 *
 * This is the *second* suite, not a replacement: `npm run test` still runs the
 * 53-test jsdom suite declared in `vitest.config.ts`, and the browser suite
 * lives in `tests-browser/` precisely so vitest's
 * `include: ["tests/**\/*.test.ts(x)"]` glob cannot pick it up. The 7 vitest
 * files and their fixtures are untouched by this packet.
 *
 * Everything here is local. The `webServer` block is the only thing that binds
 * a port, it is a plain `next start` against the production build, and
 * Playwright tears it down automatically — including when a test fails.
 *
 * No secrets, no analytics, no external origins. `RESEARCH_UI_PORT` exists so
 * the port is declared once instead of being repeated in three places.
 */

const PORT = Number(process.env.RESEARCH_UI_PORT ?? 3117);
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./tests-browser",
  // Default is already `test-results`; named explicitly because the root
  // `.gitignore` lists it by path, and a silent default change would leave
  // untracked artifacts in the tree.
  outputDir: "./test-results",
  // Serial and single-worker: these assertions are about *one* running
  // instance, and a parallel run would multiply server hits for no gain.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: BASE_URL,
    trace: "off",
    video: "off",
    screenshot: "off",
    // Determinism for the committed screenshots in `screenshots/`.
    deviceScaleFactor: 1,
    colorScheme: "light",
    locale: "en-US",
    timezoneId: "UTC",
  },
  projects: [
    {
      name: "chromium",
      // No `channel`, so this uses the Chromium build installed by
      // `npx playwright install chromium` and not a system Chrome.
      use: { browserName: "chromium" },
    },
  ],
  webServer: {
    // `next start` serves the production bundle, so the screenshots and the
    // rendered-CSS axe run describe what a user would actually get, not a dev
    // overlay. The build is produced immediately before the server so a clean
    // checkout cannot fail with a confusing "no build found".
    command: `npm run build && npx next start -p ${PORT}`,
    url: BASE_URL,
    // Never attach to a process that was already listening: a stale server on
    // 3117 would silently invalidate every measurement below.
    reuseExistingServer: false,
    timeout: 300_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
