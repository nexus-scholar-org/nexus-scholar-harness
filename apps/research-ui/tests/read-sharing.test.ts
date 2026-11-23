import { afterEach, describe, expect, it, vi } from "vitest";

import { readJson, ScreeningApiError } from "@/lib/screening-api";

/**
 * H-screening-read-performance: readers of the same GET at the same time share
 * one request; each gets its own copy, its own refusal and its own abort, and
 * nothing is kept once the answer arrived.
 */

afterEach(() => vi.unstubAllGlobals());

function deferredEngine() {
  const pending: Array<{ url: string; signal?: AbortSignal; answer: (status: number, body: unknown) => void }> = [];
  const fetchMock = vi.fn((url: string, init?: RequestInit) =>
    new Promise<Response>((resolve, reject) => {
      if (init?.signal?.aborted) return reject(new DOMException("This operation was aborted", "AbortError"));
      init?.signal?.addEventListener("abort", () => reject(new DOMException("This operation was aborted", "AbortError")));
      pending.push({
        url,
        signal: init?.signal ?? undefined,
        answer: (status, body) => resolve(new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } })),
      });
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return { fetchMock, pending };
}

describe("read-sharing", () => {
  it("two readers of one address at once send one request and get their own copies", async () => {
    const { fetchMock, pending } = deferredEngine();
    const a = readJson<{ n: number[] }>("/api/v1/screening/corpus", "/api/console");
    const b = readJson<{ n: number[] }>("/api/v1/screening/corpus", "/api/console");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    pending[0].answer(200, { n: [1, 2] });
    const [first, second] = await Promise.all([a, b]);
    expect(first).toEqual({ n: [1, 2] });
    expect(second).toEqual({ n: [1, 2] });
    first.n.push(3);
    expect(second.n).toEqual([1, 2]);
  });

  it("another address, or a read after the answer, is its own request", async () => {
    const { fetchMock, pending } = deferredEngine();
    const a = readJson("/api/v1/screening/corpus", "/api/console");
    const b = readJson("/api/v1/screening/summary", "/api/console");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    pending[0].answer(200, {});
    pending[1].answer(200, {});
    await Promise.all([a, b]);
    const c = readJson("/api/v1/screening/corpus", "/api/console");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    pending[2].answer(200, { again: true });
    expect(await c).toEqual({ again: true });
  });

  it("a refusal reaches every reader as the typed error", async () => {
    const { pending } = deferredEngine();
    const a = readJson("/api/v1/screening/corpus", "/api/console");
    const b = readJson("/api/v1/screening/corpus", "/api/console");
    pending[0].answer(409, { detail: { code: "PROTOCOL_METHOD_INVALID", message: "m" } });
    for (const read of [a, b]) {
      await expect(read).rejects.toBeInstanceOf(ScreeningApiError);
      await expect(read).rejects.toMatchObject({ code: "PROTOCOL_METHOD_INVALID", status: 409 });
    }
  });

  it("one reader leaving does not stop the other; the last one leaving stops the request", async () => {
    const { fetchMock, pending } = deferredEngine();
    const leaving = new AbortController();
    const a = readJson("/api/v1/screening/corpus", "/api/console", leaving.signal);
    const staying = new AbortController();
    const b = readJson("/api/v1/screening/corpus", "/api/console", staying.signal);
    leaving.abort();
    await expect(a).rejects.toMatchObject({ code: "CONSOLE_UNREACHABLE" });
    expect(pending[0].signal?.aborted).toBe(false);
    pending[0].answer(200, { ok: 1 });
    expect(await b).toEqual({ ok: 1 });

    const alone = new AbortController();
    const c = readJson("/api/v1/screening/corpus", "/api/console", alone.signal);
    alone.abort();
    await expect(c).rejects.toMatchObject({ code: "CONSOLE_UNREACHABLE" });
    expect(pending[1].signal?.aborted).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("a reader whose signal is already aborted fails as before, alone", async () => {
    const { fetchMock } = deferredEngine();
    const done = new AbortController();
    done.abort();
    await expect(readJson("/api/v1/screening/corpus", "/api/console", done.signal)).rejects.toMatchObject({ code: "CONSOLE_UNREACHABLE" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("a read made with another fetch (a new test's) never joins an earlier one", async () => {
    const first = deferredEngine();
    void readJson("/api/v1/screening/corpus", "/api/console").catch(() => undefined);
    const second = deferredEngine();
    const read = readJson("/api/v1/screening/corpus", "/api/console");
    expect(first.fetchMock).toHaveBeenCalledTimes(1);
    expect(second.fetchMock).toHaveBeenCalledTimes(1);
    second.pending[0].answer(200, { fresh: true });
    expect(await read).toEqual({ fresh: true });
  });

  it("review finding 1: a read after a write never joins a read made before it", async () => {
    const { fetchMock, pending } = deferredEngine();
    const before = readJson("/api/v1/charting", "/api/console");
    await Promise.resolve(); // the write's await: a later task, as after a POST
    await new Promise((r) => setTimeout(r, 0));
    const after = readJson("/api/v1/charting", "/api/console");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    pending[0].answer(200, { version: 1 });
    pending[1].answer(200, { version: 2 });
    expect(await before).toEqual({ version: 1 });
    expect(await after).toEqual({ version: 2 });
  });

  it("a read one microtask later is already its own request", async () => {
    const { fetchMock } = deferredEngine();
    void readJson("/api/v1/screening/summary", "/api/console").catch(() => undefined);
    await Promise.resolve();
    void readJson("/api/v1/screening/summary", "/api/console").catch(() => undefined);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
