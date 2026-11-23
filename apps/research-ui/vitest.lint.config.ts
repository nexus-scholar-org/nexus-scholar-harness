import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

/**
 * `npm run lint:ui`: the rules the web app's copy and source must keep (H-test-diet, 2026-11-23).
 *
 * These checks read files (the en/fr/ar catalogues, component source, the stylesheet, the theme) rather than
 * render a screen, so they are not tests of behaviour and are not in `npm test`. They were moved here, one file,
 * from the vitest suite; vitest is only the runner, because it loads the TypeScript catalogues through the `@/`
 * alias. Node environment, no DOM. CI and the local gate run it.
 */

process.env.TZ = "UTC";

const appRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  resolve: { alias: { "@": appRoot } },
  test: {
    environment: "node",
    globals: false,
    include: ["lint/ui-rules.lint.ts"],
    maxWorkers: 1,
    passWithNoTests: false,
  },
});
