// @vitest-environment node

import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET, HEAD, POST } from "@/app/api/console/[...path]/route";

/**
 * The same-origin console proxy (packet UI-09).
 *
 * The browser never holds the console's port and the console's reviewed
 * GET-only CORS policy is never widened, so everything the Research UI reads
 * or posts passes through this handler. Its job is small and therefore pinned
 * exactly here:
 *
 * 1. one upstream, from `NEXUS_CONSOLE_URL`, and it must be loopback;
 * 2. only `/api/v1/...` paths with plain segments are forwarded;
 * 3. GET/HEAD anywhere under that prefix, POST only for the screening action
 *    surface and the draft writer;
 * 4. the browser-only `console` parameter is stripped, never forwarded;
 * 5. upstream failures surface as typed 502/504, not as a hung request;
 * 6. SSE bodies are handed through as a stream, never read to completion.
 */

const CONSOLE = "http://127.0.0.1:8765";

function context(...path: string[]) {
  return { params: Promise.resolve({ path }) };
}

function request(
  path: string,
  init?: ConstructorParameters<typeof NextRequest>[1],
): NextRequest {
  return new NextRequest(`http://localhost:3000/api/console/${path}`, init);
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("console proxy — reads", () => {
  it("forwards GET to the configured loopback console", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ shape: "ui07.project-summary-v1" })));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await GET(
      request("api/v1/ui/project-summary?limit=5"),
      context("api", "v1", "ui", "project-summary"),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(await response.json()).toEqual({ shape: "ui07.project-summary-v1" });

    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/ui/project-summary?limit=5`);
    expect(call[1]?.method).toBe("GET");
    expect(call[1]?.redirect).toBe("manual");
  });

  it("strips the browser-only console override instead of forwarding it", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({})));
    vi.stubGlobal("fetch", fetchSpy);

    await GET(
      request("api/v1/workspace/status?console=http://127.0.0.1:9999&x=1"),
      context("api", "v1", "workspace", "status"),
    );

    const call = fetchSpy.mock.calls[0] as unknown as [unknown];
    const url = new URL(String(call[0]));
    expect(url.searchParams.has("console")).toBe(false);
    expect(url.searchParams.get("x")).toBe("1");
    expect(url.origin).toBe(CONSOLE);
  });

  it("forwards HEAD", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(new Response(null, { status: 204 })));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await HEAD(
      request("api/v1/screening/ui/batches", { method: "HEAD" }),
      context("api", "v1", "screening", "ui", "batches"),
    );

    expect(response.status).toBe(204);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect(call[1]?.method).toBe("HEAD");
  });
});

describe("console proxy — refusals", () => {
  it("refuses a path outside /api/v1", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const response = await GET(
      request("health"),
      context("health"),
    );

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      detail: { code: "CONSOLE_PATH_REFUSED", message: "only /api/v1/... paths are proxied" },
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("refuses a path segment that is not a plain token", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    vi.stubGlobal("fetch", vi.fn());

    const response = await GET(
      request("api/v1/..%2F..%2Fetc/passwd"),
      context("api", "v1", "..", "etc", "passwd"),
    );

    expect(response.status).toBe(400);
  });

  it("refuses a non-loopback upstream", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", "http://console.example.com:8765");
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const response = await GET(
      request("api/v1/workspace/status"),
      context("api", "v1", "workspace", "status"),
    );

    expect(response.status).toBe(500);
    expect(await response.json()).toEqual({
      detail: {
        code: "CONSOLE_ORIGIN_INVALID",
        message: "NEXUS_CONSOLE_URL must be a plain loopback http(s) origin",
      },
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("refuses a malformed upstream URL", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", "not a url");
    vi.stubGlobal("fetch", vi.fn());

    const response = await GET(
      request("api/v1/workspace/status"),
      context("api", "v1", "workspace", "status"),
    );

    expect(response.status).toBe(500);
  });

  it("refuses POST outside the screening action surface", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    for (const path of [
      ["api", "v1", "jobs", "start"],
      ["api", "v1", "pipelines"],
      ["api", "v1", "audit", "events"],
    ]) {
      const response = await POST(
        request(path.join("/"), {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: "{}",
        }),
        context(...path),
      );
      expect(response.status).toBe(405);
    }
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("refuses a method the console proxy does not carry", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    vi.stubGlobal("fetch", vi.fn());

    const response = await GET(
      request("api/v1/workspace/status", { method: "DELETE" }),
      context("api", "v1", "workspace", "status"),
    );

    expect(response.status).toBe(405);
  });
});

describe("console proxy — writes", () => {
  it("forwards an allowlisted draft-decisions POST with its body and content type", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() =>
      Promise.resolve(jsonResponse({ batch: 1, decisions_written: 1, decisions_file: "x" })),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const response = await POST(
      request("api/v1/screening/batch/1/decisions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ study_id: "SCI-001", decision: "INCLUDE" }),
      }),
      context("api", "v1", "screening", "batch", "1", "decisions"),
    );

    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/screening/batch/1/decisions`);
    expect(call[1]?.method).toBe("POST");
    expect(call[1]?.body).toBe(JSON.stringify({ study_id: "SCI-001", decision: "INCLUDE" }));
    expect((call[1]?.headers as Record<string, string>)["content-type"]).toBe("application/json");
  });

  it.each(["redeem", "defer", "publish"])("forwards the screening %s action", async (action) => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ shape: "x" })));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await POST(
      request(`api/v1/screening/actions/${action}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{}",
      }),
      context("api", "v1", "screening", "actions", action),
    );

    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/screening/actions/${action}`);
  });
});

describe("console proxy — event streams", () => {
  it("hands an SSE body through without waiting for it to end", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    let upstreamController!: ReadableStreamDefaultController<Uint8Array>;
    const upstreamBody = new ReadableStream<Uint8Array>({
      start(controller) {
        upstreamController = controller;
      },
    });
    const fetchSpy = vi.fn(() =>
      Promise.resolve(
        new Response(upstreamBody, { headers: { "content-type": "text/event-stream" } }),
      ),
    );
    vi.stubGlobal("fetch", fetchSpy);

    // The stream is deliberately never closed. A buffering proxy would hang
    // here; the assertion below only resolves because the body is passed on.
    const response = await GET(
      request("api/v1/jobs/JOB-1/stream", { headers: { accept: "text/event-stream" } }),
      context("api", "v1", "jobs", "JOB-1", "stream"),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("text/event-stream");
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.get("x-accel-buffering")).toBe("no");

    const reader = response.body?.getReader();
    if (!reader) throw new Error("the proxied response has no body stream");
    upstreamController.enqueue(new TextEncoder().encode("event: snapshot\ndata: {}\n\n"));
    const snapshot = await reader.read();
    expect(new TextDecoder().decode(snapshot.value)).toContain("event: snapshot");

    upstreamController.enqueue(new TextEncoder().encode("event: update\ndata: {}\n\n"));
    const update = await reader.read();
    expect(new TextDecoder().decode(update.value)).toContain("event: update");

    // Cancelling the reader propagates back to the upstream source.
    await reader.cancel();
  });

  it("passes the caller's abort signal to a stream and skips the read timeout", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() =>
      Promise.resolve(new Response(": keepalive\n\n", {
        headers: { "content-type": "text/event-stream" },
      })),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const aborter = new AbortController();
    const incoming = request("api/v1/events", {
      headers: { accept: "text/event-stream" },
      signal: aborter.signal,
    });
    const response = await GET(incoming, context("api", "v1", "events"));

    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    const signal = call[1]?.signal as AbortSignal | undefined;
    expect(signal).toBeDefined();
    // A stream carries the caller's signal, not the 120 s read timeout.
    expect(signal?.aborted).toBe(false);

    aborter.abort();
    expect(signal?.aborted).toBe(true);
  });

  it("streams any upstream that answers text/event-stream, even off the stream paths", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode("event: tick\ndata: {}\n\n"));
        controller.close();
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(new Response(body, { headers: { "content-type": "text/event-stream" } })),
      ),
    );

    const response = await GET(
      request("api/v1/workspace/status"),
      context("api", "v1", "workspace", "status"),
    );

    expect(response.headers.get("content-type")).toBe("text/event-stream");
    expect(response.headers.get("x-accel-buffering")).toBe("no");
    expect(await response.text()).toContain("event: tick");
  });
});

describe("console proxy — upstream failure", () => {
  it("answers a typed 502 when the console is unreachable", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("connect ECONNREFUSED"))),
    );

    const response = await GET(
      request("api/v1/workspace/status"),
      context("api", "v1", "workspace", "status"),
    );

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({
      detail: { code: "CONSOLE_UNREACHABLE", message: "connect ECONNREFUSED" },
    });
  });

  it("answers a typed 504 on timeout", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const timeout = new Error("timed out");
    timeout.name = "TimeoutError";
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(timeout)),
    );

    const response = await GET(
      request("api/v1/workspace/status"),
      context("api", "v1", "workspace", "status"),
    );

    expect(response.status).toBe(504);
  });
});
