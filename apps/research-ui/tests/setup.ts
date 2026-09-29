import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// `globals` is disabled in vitest.config.ts, so Testing Library cannot find a
// global `afterEach` to auto-register its unmount hook. Register it explicitly,
// otherwise rendered trees leak between test cases and assertions can pass
// against output from an earlier render.
afterEach(() => {
  cleanup();
});
