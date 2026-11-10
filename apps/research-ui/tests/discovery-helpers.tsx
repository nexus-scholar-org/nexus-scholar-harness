import { vi } from "vitest";

import { discoveryEngine, stubDiscoveryFetch, type DiscoveryFakeOptions } from "./fixtures/discovery-engine";

/**
 * Shared set-up for the discovery screen tests: the stateful fake engine at
 * `fetch`, an address query, a recorded `location.assign`, and a clipboard.
 */
export function setUp(options: DiscoveryFakeOptions & { search?: string } = {}) {
  const engine = discoveryEngine(options);
  stubDiscoveryFetch(engine, (fn) => vi.stubGlobal("fetch", vi.fn(fn)));
  const assign = vi.fn();
  vi.stubGlobal("location", { ...window.location, assign, search: options.search ?? "", reload: vi.fn() });
  const writeText = vi.fn(async () => undefined);
  Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
  return { engine, assign, writeText };
}

/** The calls the screen sent, as `METHOD path`. */
export function sent(engine: ReturnType<typeof discoveryEngine>): string[] {
  return engine.calls.map((c) => `${c.method} ${c.path}`);
}
