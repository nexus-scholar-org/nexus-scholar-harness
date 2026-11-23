import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

/**
 * In-process component/unit test runner for the Research UI.
 *
 * There is deliberately no browser here: no Playwright, no `webServer`, no
 * headless browser download. Everything below runs in Node against jsdom.
 * There is no browser suite either since 2026-11-23 (H-test-diet): anything
 * that requires a real rendering engine is unchecked; `GATES.md` lists it.
 */

// The screens print engine instants on the machine's clock (H-ui-findings F6); the tests read them in UTC
// so a run does not depend on the developer's zone. Tests of the conversion set `TZ` themselves.
process.env.TZ = "UTC";

const appRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Application components import through the `@/*` alias declared in
    // tsconfig.json (`"@/*": ["./*"]`). Tests import the very same components,
    // so this alias MUST be resolved here too. Without it every component
    // import (`@/lib/contracts`, `@/components/...`) fails to resolve and the
    // whole suite errors out before a single assertion runs.
    alias: {
      "@": appRoot,
    },
  },
  test: {
    environment: "jsdom",
    // Globals stay off so that test helpers must be imported explicitly and
    // cannot silently resolve to another framework's globals.
    globals: false,
    setupFiles: ["./tests/setup.ts"],
    // A test may now wait up to 3 s at each step (tests/setup.ts); the default 5 s per test would cut
    // short one with two slow steps.
    testTimeout: 15000,
    // At most four workers (H-test-diet): the default is one per core, eight Node processes rendering
    // pages beside the other suites sessions run on the same PC, which made waits time out under load.
    maxWorkers: 4,
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    // Refuse to pass a suite that has nothing in it.
    passWithNoTests: false,
  },
});
