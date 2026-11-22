import "@testing-library/jest-dom/vitest";

import { cleanup, configure } from "@testing-library/react";
import { afterEach } from "vitest";

// `globals` is disabled in vitest.config.ts, so Testing Library cannot find a
// global `afterEach` to auto-register its unmount hook. Register it explicitly,
// otherwise rendered trees leak between test cases and assertions can pass
// against output from an earlier render.
afterEach(() => {
  cleanup();
});

// `findBy…` and `waitFor` give up after 1 s by default. Under the full suite, or on a busy CI machine,
// a first render sometimes takes longer, and a different file failed on each run (H-test-waits). The
// limit is how long a test waits before failing, not how long a passing test takes; these tests check
// behaviour, and speed is measured elsewhere.
configure({ asyncUtilTimeout: 3000 });
