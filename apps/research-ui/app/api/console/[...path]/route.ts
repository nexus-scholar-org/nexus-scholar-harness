import type { NextRequest } from "next/server";

/**
 * Same-origin proxy to the local Harness Console (packet UI-09).
 *
 * The Research UI is the product surface; the console is its backend. The
 * browser must not learn the console's port, and the console's CORS policy
 * stays exactly as reviewed (`allow_methods=["GET"]`), so every read the app
 * makes is issued to this route on the app's own origin and resolved here,
 * server-side.
 *
 * Three rules this handler enforces, each pinned by `tests/console-proxy.test.ts`:
 *
 * 1. **One upstream, from configuration.** `NEXUS_CONSOLE_URL` (default
 *    `http://127.0.0.1:8765`) must be a loopback `http(s)` origin. A caller
 *    cannot name a host, a port, or a scheme.
 * 2. **A path allowlist, not free forwarding.** Only `/api/v1/...` reaches the
 *    console, and every path segment must be a plain token. Nothing else is
 *    forwarded, so the proxy is not a general-purpose pass-through.
 * 3. **Reads plus the action routes, nothing else.** GET/HEAD are forwarded.
 *    POST is forwarded only for the screening action surface and the draft
 *    writer, whose own gates (pairing code, exact coverage, approval,
 *    generation) still run inside the console. The audit-journal writer, job
 *    start and pipeline creation are deliberately **not** reachable through
 *    the browser.
 * 4. **Event streams stay streams.** The console's two SSE routes
 *    (`/jobs/{id}/stream`, `/events/tick`) are returned as the upstream body, not
 *    read to completion. Buffering them (the old `upstream.text()`) meant a
 *    streamed job never reached the browser: the handler waited for a
 *    connection that only ends when the job does. Those routes also carry no
 *    120 s timeout — they are long-lived by design — and abort with the
 *    caller's request signal instead.
 */

const DEFAULT_CONSOLE_URL = "http://127.0.0.1:8765";
const LOOPBACK = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);
const SEGMENT = /^[A-Za-z0-9_-]+$/;
const READ_METHODS = new Set(["GET", "HEAD"]);

/** POST targets the browser may reach: screening actions and draft capture. */
const POST_PATHS: ReadonlyArray<RegExp> = [
  /^api\/v1\/screening\/batch\/\d+\/decisions$/,
  /^api\/v1\/screening\/actions\/(redeem|defer|publish)$/,
];

/**
 * The console's long-lived SSE routes. They are GET-only (no allowlist
 * widening) but must not be read to completion or raced against a timeout.
 */
const STREAM_PATHS: ReadonlyArray<RegExp> = [
  /^api\/v1\/jobs\/[A-Za-z0-9_-]+\/stream$/,
  /^api\/v1\/events(\/tick)?$/,
];

function isStreamPath(path: string): boolean {
  return STREAM_PATHS.some((pattern) => pattern.test(path));
}

function isEventStream(upstream: Response): boolean {
  return (upstream.headers.get("content-type") ?? "").toLowerCase().includes("text/event-stream");
}

function typedError(status: number, code: string, message: string): Response {
  return Response.json({ detail: { code, message } }, { status });
}

function consoleBase(): string | null {
  const raw = (process.env.NEXUS_CONSOLE_URL ?? DEFAULT_CONSOLE_URL).trim();
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return null;
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return null;
  if (!LOOPBACK.has(url.hostname)) return null;
  if (url.username || url.password || url.search || url.hash) return null;
  return url.origin;
}

function joinedPath(segments: string[] | undefined): string | null {
  if (!segments || segments.length < 2) return null;
  if (segments.some((segment) => !SEGMENT.test(segment))) return null;
  if (segments[0] !== "api" || segments[1] !== "v1") return null;
  return segments.join("/");
}

function proxyResponse(upstream: Response): Promise<Response> {
  const contentType = upstream.headers.get("content-type") ?? "application/json";
  return upstream.text().then(
    (body) =>
      new Response(
        // 204/205/304 must not carry a body; the console uses 204 for HEAD.
        body === "" && [204, 205, 304].includes(upstream.status) ? null : body,
        {
          status: upstream.status,
          headers: {
            "content-type": contentType,
            "cache-control": "no-store",
          },
        },
      ),
  );
}

/**
 * Hand the upstream body straight through.
 *
 * `upstream.text()` waits for the stream to end; for an SSE job stream that is
 * "when the job finishes", so the browser saw nothing until the work was over.
 * Returning the ReadableStream is what makes the events arrive as they are
 * produced. `x-accel-buffering: no` is for any buffering reverse proxy in
 * front of the app; the console itself is loopback-only.
 */
function streamResponse(upstream: Response): Response {
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "text/event-stream",
      "cache-control": "no-store",
      "x-accel-buffering": "no",
    },
  });
}

async function forward(request: NextRequest, segments: string[] | undefined): Promise<Response> {
  const base = consoleBase();
  if (base === null) {
    return typedError(
      500,
      "CONSOLE_ORIGIN_INVALID",
      "NEXUS_CONSOLE_URL must be a plain loopback http(s) origin",
    );
  }
  const path = joinedPath(segments);
  if (path === null) {
    return typedError(400, "CONSOLE_PATH_REFUSED", "only /api/v1/... paths are proxied");
  }

  const method = request.method.toUpperCase();
  if (!READ_METHODS.has(method) && method !== "POST") {
    return typedError(405, "CONSOLE_METHOD_REFUSED", "the console proxy accepts GET, HEAD and POST");
  }
  if (method === "POST" && !POST_PATHS.some((pattern) => pattern.test(path))) {
    return typedError(
      405,
      "CONSOLE_METHOD_REFUSED",
      "POST is proxied only for screening actions and draft decisions",
    );
  }

  const incoming = new URL(request.url);
  const query = new URLSearchParams(incoming.searchParams);
  // `console` is the opt-in override read by the client during tests; it is
  // never an upstream parameter.
  query.delete("console");
  const target = `${base}/${path}${query.size > 0 ? `?${query.toString()}` : ""}`;

  const stream = isStreamPath(path);
  const init: RequestInit = {
    method,
    headers: {
      // `EventSource` sends `text/event-stream`; everything else is JSON.
      accept: request.headers.get("accept") ?? (stream ? "text/event-stream" : "application/json"),
    },
    redirect: "manual",
    cache: "no-store",
    // A stream lives as long as the job does, and the caller's own signal is
    // what ends it; only bounded reads get the 120 s ceiling.
    signal: stream ? request.signal : AbortSignal.timeout(120_000),
  };
  if (method === "POST") {
    const contentType = request.headers.get("content-type");
    if (contentType) init.headers = { ...init.headers, "content-type": contentType };
    init.body = await request.text();
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch (error: unknown) {
    const timedOut = error instanceof Error && error.name === "TimeoutError";
    return typedError(
      timedOut ? 504 : 502,
      timedOut ? "CONSOLE_TIMEOUT" : "CONSOLE_UNREACHABLE",
      error instanceof Error ? error.message : "the console could not be reached",
    );
  }
  if (stream || isEventStream(upstream)) return streamResponse(upstream);
  return proxyResponse(upstream);
}

type Context = { params: Promise<{ path?: string[] }> };

export async function GET(request: NextRequest, context: Context): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export async function HEAD(request: NextRequest, context: Context): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export async function POST(request: NextRequest, context: Context): Promise<Response> {
  const { path } = await context.params;
  return forward(request, path);
}

export const dynamic = "force-dynamic";
