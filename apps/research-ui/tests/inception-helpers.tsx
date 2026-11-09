import { vi } from "vitest";

import { inceptionEngine, SESSION, stubFetch, type FakeOptions } from "./fixtures/inception-engine";

/**
 * Shared set-up for the inception screen tests: a stateful fake engine at
 * `fetch`, a `?draft=` in the address, and a recorded `location.assign`.
 */
export function setUp(options: FakeOptions & { draft?: Record<string, unknown>; emitted?: Record<string, unknown> | null; noDraft?: boolean; search?: string } = {}) {
  const engine = inceptionEngine(options);
  if (!options.noDraft) engine.seed(options.draft ?? {}, options.emitted ?? null);
  stubFetch(engine, (fn) => vi.stubGlobal("fetch", vi.fn(fn)));
  const assign = vi.fn();
  vi.stubGlobal("location", { ...window.location, assign, search: options.search ?? `?draft=${SESSION}`, reload: vi.fn() });
  return { engine, assign };
}

/** The calls the screen sent, as `METHOD path`. */
export function sent(engine: ReturnType<typeof inceptionEngine>): string[] {
  return engine.calls.map((c) => `${c.method} ${c.path}`);
}
