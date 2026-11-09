// @vitest-environment node

import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET, HEAD, POST, PUT } from "@/app/api/console/[...path]/route";

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
  // A browser always sends its own Origin on a fetch POST; the proxy requires it.
  if (init?.method === "POST" || init?.method === "PUT") {
    const headers = new Headers(init.headers);
    if (!headers.has("origin")) headers.set("origin", "http://localhost:3000");
    init = { ...init, headers };
  }
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
      // The run routes are exact: no other proposals write is reachable.
      ["api", "v1", "screening", "proposals"],
      ["api", "v1", "screening", "proposals", "runs", "RUN-abc"],
      ["api", "v1", "screening", "proposals", "setup"],
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

  // The console serves POST /actions/pairing/redeem, /actions/defer and
  // /actions/publish (console/api/screening.py).
  it.each(["pairing/begin", "pairing/redeem", "defer", "publish"])("forwards the screening %s action", async (action) => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ shape: "x" })));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await POST(
      request(`api/v1/screening/actions/${action}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{}",
      }),
      context("api", "v1", "screening", "actions", ...action.split("/")),
    );

    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/screening/actions/${action}`);
  });

  // M1b-1: the screening API write routes (contract §4).
  it.each([
    ["decisions/events", ["decisions", "events"]],
    ["decisions/conflicts/STU-abc/resolve", ["decisions", "conflicts", "STU-abc", "resolve"]],
    ["prepare", ["prepare"]],
    // M1b-2: agent runs and calibrations.
    ["proposals/runs", ["proposals", "runs"]],
    ["proposals/runs/RUN-abc/cancel", ["proposals", "runs", "RUN-abc", "cancel"]],
    ["proposals/calibrations", ["proposals", "calibrations"]],
  ])("forwards the screening %s POST", async (route, segments) => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ results: [] })));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await POST(
      request(`api/v1/screening/${route}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{}",
      }),
      context("api", "v1", "screening", ...segments),
    );

    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/screening/${route}`);
  });

  // M5-slim: the workspaces routes (workspaces API §3).
  it.each([
    ["workspaces", ["workspaces"]],
    ["workspaces/open", ["workspaces", "open"]],
  ])("forwards the %s POST", async (route, segments) => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ slug: "s" })));
    vi.stubGlobal("fetch", fetchSpy);
    const response = await POST(
      request(`api/v1/${route}`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }),
      context("api", "v1", ...segments),
    );
    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/${route}`);
  });

  it("refuses a POST to another workspaces path", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const response = await POST(
      request("api/v1/workspaces/delete", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }),
      context("api", "v1", "workspaces", "delete"),
    );
    expect(response.status).toBe(405);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  // M4b: the inception routes (inception API). Discarding a draft is not carried.
  it.each([
    ["inception/drafts"],
    ["inception/preview"],
    ["inception/steps/scope"],
    ["inception/steps/shape"],
    ["inception/steps/criteria"],
    ["inception/steps/matrix"],
    ["inception/drafts/rec_0123456789abcdef0123456789abcdef/genesis"],
    // M4c: recon over HTTP.
    ["inception/drafts/rec_0123456789abcdef0123456789abcdef/recon/probe"],
    ["inception/drafts/rec_0123456789abcdef0123456789abcdef/recon/delta"],
    ["inception/drafts/rec_0123456789abcdef0123456789abcdef/recon/distill"],
    ["inception/drafts/rec_0123456789abcdef0123456789abcdef/recon/bind"],
  ])("forwards the %s POST", async (route) => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ ok: true })));
    vi.stubGlobal("fetch", fetchSpy);
    const response = await POST(
      request(`api/v1/${route}`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }),
      context("api", "v1", ...route.split("/")),
    );
    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/${route}`);
  });

  it.each([
    ["inception/steps/emit"],
    ["inception/genesis"],
    ["inception/drafts/rec_1/emitted"],
    ["inception/drafts/rec_1/recon/directions"],
    ["inception/drafts/rec_1/recon/jobs/rjob_1/cancel"],
    ["inception/drafts/rec_1/recon"],
  ])(
    "refuses the %s POST",
    async (route) => {
      vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
      const fetchSpy = vi.fn();
      vi.stubGlobal("fetch", fetchSpy);
      const response = await POST(
        request(`api/v1/${route}`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }),
        context("api", "v1", ...route.split("/")),
      );
      expect(response.status).toBe(405);
      expect(fetchSpy).not.toHaveBeenCalled();
    },
  );

  it("forwards PUT to save an inception draft, and only the draft itself", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ session_id: "rec_1" })));
    vi.stubGlobal("fetch", fetchSpy);
    const body = JSON.stringify({ draft: {}, base_updated_at: "2026-11-09T00:00:00+00:00" });
    const ok = await PUT(
      request("api/v1/inception/drafts/rec_1", { method: "PUT", headers: { "content-type": "application/json" }, body }),
      context("api", "v1", "inception", "drafts", "rec_1"),
    );
    expect(ok.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect(String(call[0])).toBe(`${CONSOLE}/api/v1/inception/drafts/rec_1`);
    expect(call[1]?.body).toBe(body);

    const refused = await PUT(
      request("api/v1/inception/drafts/rec_1/genesis", { method: "PUT", body: "{}" }),
      context("api", "v1", "inception", "drafts", "rec_1", "genesis"),
    );
    expect(refused.status).toBe(405);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("forwards PUT for the screening settings and nothing else", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ blinding: "show" })));
    vi.stubGlobal("fetch", fetchSpy);
    const body = JSON.stringify({ blinding: "show" });

    const ok = await PUT(
      request("api/v1/screening/settings", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body,
      }),
      context("api", "v1", "screening", "settings"),
    );
    expect(ok.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect(call[1]?.method).toBe("PUT");
    expect(call[1]?.body).toBe(body);

    const refused = await PUT(
      request("api/v1/workspace/status", { method: "PUT", body: "{}" }),
      context("api", "v1", "workspace", "status"),
    );
    expect(refused.status).toBe(405);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("refuses a PUT from another origin", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const response = await PUT(
      request("api/v1/screening/settings", {
        method: "PUT",
        headers: { origin: "http://evil.example" },
        body: "{}",
      }),
      context("api", "v1", "screening", "settings"),
    );

    expect(response.status).toBe(403);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("refuses a cross-site draft read, which would record a reveal", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ proposal: null })));
    vi.stubGlobal("fetch", fetchSpy);
    const path = ["api", "v1", "screening", "records", "STU-abc", "proposal"];

    const crossSite = await GET(request(path.join("/"), { headers: { "sec-fetch-site": "cross-site" } }), context(...path));
    expect(crossSite.status).toBe(403);
    expect(fetchSpy).not.toHaveBeenCalled();

    const own = await GET(request(path.join("/"), { headers: { "sec-fetch-site": "same-origin" } }), context(...path));
    expect(own.status).toBe(200);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("refuses the non-existent bare redeem action", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({ shape: "x" })));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await POST(
      request("api/v1/screening/actions/redeem", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{}",
      }),
      context("api", "v1", "screening", "actions", "redeem"),
    );

    expect(response.status).toBe(405);
    expect(fetchSpy).not.toHaveBeenCalled();
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

  it("treats a recon job's events as a stream: the caller's signal, not the read timeout (M4c)", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() =>
      Promise.resolve(new Response(": keepalive\n\n", {
        headers: { "content-type": "text/event-stream" },
      })),
    );
    vi.stubGlobal("fetch", fetchSpy);
    const route = "api/v1/inception/drafts/rec_0123456789abcdef/recon/jobs/rjob_0123456789abcdef/events";
    const aborter = new AbortController();
    const response = await GET(
      request(route, { headers: { accept: "text/event-stream" }, signal: aborter.signal }),
      context(...route.split("/")),
    );
    expect(response.status).toBe(200);
    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    const signal = call[1]?.signal as AbortSignal | undefined;
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

describe("console proxy — INC-01 guards", () => {
  it("adds the console token from NEXUS_CONSOLE_TOKEN, server-side", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    vi.stubEnv("NEXUS_CONSOLE_TOKEN", "launch-token");
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({})));
    vi.stubGlobal("fetch", fetchSpy);

    await GET(request("api/v1/jobs"), context("api", "v1", "jobs"));

    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect((call[1]?.headers as Record<string, string>).authorization).toBe("Bearer launch-token");
  });

  it("sends no authorization header when no token is configured", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    vi.stubEnv("NEXUS_CONSOLE_TOKEN", "");
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({})));
    vi.stubGlobal("fetch", fetchSpy);

    await GET(request("api/v1/jobs"), context("api", "v1", "jobs"));

    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    expect((call[1]?.headers as Record<string, string>).authorization).toBeUndefined();
  });

  it("refuses a request addressed to a foreign host (DNS rebinding)", async () => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({})));
    vi.stubGlobal("fetch", fetchSpy);

    const response = await GET(
      new NextRequest("http://evil.example:3000/api/console/api/v1/jobs"),
      context("api", "v1", "jobs"),
    );

    expect(response.status).toBe(400);
    expect((await response.json()).detail.code).toBe("CONSOLE_HOST_REFUSED");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it.each([
    ["a foreign origin", "https://evil.example"],
    ["another loopback port", "http://localhost:4000"],
    ["no origin", null],
  ])("refuses a POST from %s", async (_label, origin) => {
    vi.stubEnv("NEXUS_CONSOLE_URL", CONSOLE);
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse({})));
    vi.stubGlobal("fetch", fetchSpy);
    const headers: Record<string, string> = { "content-type": "application/json" };
    if (origin !== null) headers.origin = origin;

    const response = await POST(
      new NextRequest("http://localhost:3000/api/console/api/v1/screening/actions/publish", {
        method: "POST",
        headers,
        body: "{}",
      }),
      context("api", "v1", "screening", "actions", "publish"),
    );

    expect(response.status).toBe(403);
    expect((await response.json()).detail.code).toBe("CONSOLE_ORIGIN_REFUSED");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
