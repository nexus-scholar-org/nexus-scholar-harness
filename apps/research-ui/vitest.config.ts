import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

/**
 * In-process component/unit test runner for the Research UI.
 *
 * There is deliberately no browser here: no Playwright, no `webServer`, no
 * headless browser download. Everything below runs in a single Node process
 * against jsdom. Anything that requires a real rendering engine is tracked as
 * unverified in `GATES.md` and deferred to packet UI-00b.
 */

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
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    // Refuse to pass a suite that has nothing in it.
    passWithNoTests: false,
  },
});
