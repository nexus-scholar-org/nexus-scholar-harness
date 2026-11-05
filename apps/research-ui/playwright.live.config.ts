import { tmpdir } from "node:os";
import { join } from "node:path";

import { defineConfig } from "@playwright/test";

/**
 * The live screening gate (M1b-1 DoD "Playwright, live").
 *
 * Unlike `playwright.config.ts`, whose screens are fed shape-conformant
 * payloads at the network boundary, this run drives the real stack: a prepared
 * copy of `workspaces/golden-uav-30` served by the Harness Console
 * (`scripts/golden_screening_sandbox.py`, built outside `workspaces/`), and the
 * research UI's own build talking to it through the same-origin proxy.
 *
 * - The console prints the approval code only to its terminal (decision
 *   2026-11-04); the sandbox copies that terminal output to `LIVE_TERMINAL_LOG`,
 *   which the spec reads exactly as a researcher reads the terminal.
 * - Three sandbox drafts (driver `sandbox`, model `sandbox-fixture`) exist so a
 *   reveal can happen. They are test data, not an agent run.
 * - The UI builds into `.next-live` and the ports differ from the defaults, so
 *   this run can neither serve nor overwrite a developer's running instance.
 */

const UI_PORT = 3127;
const CONSOLE_PORT = 8775;
const TOKEN = "live-gate-token";
export const LIVE_SANDBOX = join(tmpdir(), "nexus-live-sandbox");
export const LIVE_TERMINAL_LOG = join(tmpdir(), "nexus-live-terminal.log");

process.env.LIVE_TERMINAL_LOG = LIVE_TERMINAL_LOG;
process.env.LIVE_SANDBOX = LIVE_SANDBOX;

export default defineConfig({
  testDir: "./tests-live",
  outputDir: "./test-results/live",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  // One test decides 30 records by keyboard against a real engine (~4-5 min).
  timeout: 900_000,
  expect: { timeout: 15_000 },
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${UI_PORT}`,
    trace: "retain-on-failure",
    video: "off",
    screenshot: "only-on-failure",
    viewport: { width: 1440, height: 900 },
    colorScheme: "light",
    locale: "en-US",
    timezoneId: "UTC",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: [
    {
      command: `uv run python ../../scripts/golden_screening_sandbox.py --dest "${LIVE_SANDBOX}" --port ${CONSOLE_PORT} --with-drafts 3 --terminal-log "${LIVE_TERMINAL_LOG}"`,
      url: `http://127.0.0.1:${CONSOLE_PORT}/healthz`,
      reuseExistingServer: false,
      timeout: 180_000,
      env: { NEXUS_CONSOLE_TOKEN: TOKEN },
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: `npm run build && npx next start -p ${UI_PORT}`,
      url: `http://localhost:${UI_PORT}`,
      reuseExistingServer: false,
      timeout: 300_000,
      env: {
        NEXT_DIST_DIR: ".next-live",
        NEXUS_CONSOLE_URL: `http://127.0.0.1:${CONSOLE_PORT}`,
        NEXUS_CONSOLE_TOKEN: TOKEN,
      },
      stdout: "pipe",
      stderr: "pipe",
    },
  ],
});
