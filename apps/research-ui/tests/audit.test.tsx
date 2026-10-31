import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuditPage } from "@/components/audit-page";
import { SUPPORTED_LOCALES } from "@/i18n";
import { demoAuditEvents } from "@/lib/mock-audit";
import { CATALOGS } from "@/messages";

/**
 * The audit screen, in process (packet UI-06).
 *
 * What these tests hold down:
 *
 * 1. the default is the demonstration feed and it sends no request;
 * 2. the stored order is printed as received — the page never sorts, merges or
 *    retimes, so an out-of-order input renders out of order;
 * 3. the stored timestamp is printed verbatim, never reformatted;
 * 4. a missing agent, description or status says so instead of being filled in;
 * 5. `?source=live` reads the console feed through the same-origin proxy, and a
 *    refused read shows the server code rather than an empty journal;
 * 6. live mode also subscribes to `/events/tick` through the proxy and re-reads
 *    the feed on a tick, while the demonstration mode opens no stream.
 *
 * The rendered-DOM claims are jsdom's. Chromium capture stays in
 * `tests-browser/`.
 */

const LIVE_FEED = {
  shape: "ui07.audit-feed-v1",
  total: 3,
  offset: 0,
  limit: 25,
  items: [
    {
      timestamp: "2026-02-02T10:00:00.000000+00:00",
      event_id: "EVT-LIVE-3",
      action: "SCREENING_PUBLISHED",
      agent_or_tool: "screening worker",
      description: "latest first",
      status: "SUCCESS",
    },
    {
      timestamp: "2026-02-01T10:00:00.000000+00:00",
      event_id: null,
      action: "SCREENING_FINALIZED",
      agent_or_tool: null,
      description: null,
      status: null,
    },
    {
      timestamp: "2026-01-31T10:00:00.000000+00:00",
      event_id: "EVT-LIVE-1",
      action: "SCREENING_STARTED",
      agent_or_tool: "screening worker",
      description: "earliest",
      status: "FAILED",
    },
  ],
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function setQuery(query: string) {
  window.history.replaceState({}, "", `/en/audit${query}`);
}

afterEach(() => {
  cleanup();
  FakeEventSource.instances = [];
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/en/audit");
});

describe("audit screen — demonstration feed", () => {
  it("renders the fixture and sends no request", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    render(<AuditPage locale="en" />);

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(screen.getByText(CATALOGS.en["audit.fixtureLede"])).toBeInTheDocument();
    const countLine = screen.getByText(
      (_content, element) =>
        element?.tagName === "P" &&
        (element.textContent ?? "").startsWith(CATALOGS.en["audit.countLabel"]),
    );
    expect(countLine).toHaveTextContent(String(demoAuditEvents.length));
  });

  it("prints the stored timestamps verbatim and in the stored order", () => {
    render(<AuditPage locale="en" />);

    const rendered = screen
      .getAllByRole("listitem")
      .map((row) => within(row).getAllByRole("definition")[0].textContent);

    expect(rendered).toEqual(demoAuditEvents.map((event) => event.timestamp));
  });

  it("shows a non-success outcome without rewriting it", () => {
    render(<AuditPage locale="en" />);

    const failed = demoAuditEvents.find((event) => event.status === "FAILED");
    expect(failed).toBeDefined();
    expect(screen.getByText("FAILED")).toBeInTheDocument();
  });

  it("says a missing event id is not recorded instead of inventing one", () => {
    render(<AuditPage locale="en" />);

    expect(screen.getAllByText(CATALOGS.en["audit.notRecorded"]).length).toBe(
      demoAuditEvents.length,
    );
  });

  for (const locale of SUPPORTED_LOCALES) {
    it(`renders in ${locale} from the catalog, not the English pin`, () => {
      render(<AuditPage locale={locale} />);

      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        CATALOGS[locale]["audit.heading"],
      );
      expect(screen.getByText(CATALOGS[locale]["audit.feedHeading"])).toBeInTheDocument();
    });
  }
});

const LIVE_FEED_V2 = {
  shape: "ui07.audit-feed-v1",
  total: 4,
  offset: 0,
  limit: 25,
  items: [
    {
      timestamp: "2026-02-03T10:00:00.000000+00:00",
      event_id: "EVT-LIVE-4",
      action: "SCREENING_COLLECTED",
      agent_or_tool: "screening worker",
      description: "refreshed latest",
      status: "SUCCESS",
    },
    ...LIVE_FEED.items,
  ],
};

type TickListener = (event: MessageEvent) => void;

/** jsdom has no EventSource; this is the smallest one the screen can use. */
class FakeEventSource {
  static instances: FakeEventSource[] = [];

  readonly url: string;
  closed = false;
  private readonly listeners = new Map<string, Set<TickListener>>();

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: TickListener): void {
    const set = this.listeners.get(type) ?? new Set<TickListener>();
    set.add(listener);
    this.listeners.set(type, set);
  }

  removeEventListener(type: string, listener: TickListener): void {
    this.listeners.get(type)?.delete(listener);
  }

  close(): void {
    this.closed = true;
  }

  emit(type: string): void {
    for (const listener of this.listeners.get(type) ?? []) {
      listener(new MessageEvent(type));
    }
  }
}

describe("audit screen — live feed through the console proxy", () => {
  it("reads the same-origin proxy path and prints the feed as received", async () => {
    setQuery("?source=live");
    const fetchSpy = vi.fn(() => Promise.resolve(jsonResponse(LIVE_FEED)));
    vi.stubGlobal("fetch", fetchSpy);

    render(<AuditPage locale="en" />);

    await waitFor(() => {
      expect(screen.getByText(CATALOGS.en["audit.liveLede"])).toBeInTheDocument();
    });

    const call = fetchSpy.mock.calls[0] as unknown as [unknown, RequestInit | undefined];
    const url = new URL(String(call[0]), "http://localhost:3000");
    expect(url.pathname).toBe("/api/console/api/v1/screening/ui/audit-feed");
    expect(url.searchParams.get("limit")).toBe("25");
    expect(call[1]?.method ?? "GET").toBe("GET");

    await waitFor(() => {
      expect(screen.getAllByRole("listitem")).toHaveLength(LIVE_FEED.items.length);
    });

    const actions = screen
      .getAllByRole("listitem")
      .map((row) => row.querySelector("bdi")?.textContent);
    expect(actions).toEqual(LIVE_FEED.items.map((event) => event.action));

    // A missing status/agent/description is stated, never filled in.
    expect(screen.getByText(CATALOGS.en["audit.noStatus"])).toBeInTheDocument();
    expect(screen.getByText(CATALOGS.en["audit.noAgent"])).toBeInTheDocument();
    expect(screen.getByText(CATALOGS.en["audit.noDescription"])).toBeInTheDocument();
  });

  it("shows the typed server code when the feed is refused", async () => {
    setQuery("?source=live");
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          jsonResponse(
            { detail: { code: "CONSOLE_UNREACHABLE", message: "console down", details: {} } },
            502,
          ),
        ),
      ),
    );

    render(<AuditPage locale="en" />);

    await waitFor(() => {
      expect(screen.getByText(CATALOGS.en["audit.liveUnavailable"])).toBeInTheDocument();
    });
    expect(screen.getByText("CONSOLE_UNREACHABLE")).toBeInTheDocument();
    expect(screen.queryByRole("listitem")).toBeNull();
  });
});

describe("audit screen — live tick stream", () => {
  it("opens no stream for the demonstration feed", () => {
    vi.stubGlobal("EventSource", FakeEventSource);
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    render(<AuditPage locale="en" />);

    expect(FakeEventSource.instances).toHaveLength(0);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("subscribes through the proxy and re-reads the feed on a tick", async () => {
    setQuery("?source=live");
    const fetchSpy = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(LIVE_FEED))
      .mockResolvedValue(jsonResponse(LIVE_FEED_V2));
    vi.stubGlobal("fetch", fetchSpy);
    vi.stubGlobal("EventSource", FakeEventSource);

    render(<AuditPage locale="en" />);

    await waitFor(() => expect(screen.getAllByRole("listitem")).toHaveLength(3));
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(FakeEventSource.instances[0]?.url).toBe("/api/console/api/v1/events/tick");

    FakeEventSource.instances[0]?.emit("tick");

    await waitFor(() => expect(screen.getByText("refreshed latest")).toBeInTheDocument());
    expect(fetchSpy).toHaveBeenCalledTimes(2);
    const refresh = fetchSpy.mock.calls[1] as unknown as [unknown];
    expect(new URL(String(refresh[0]), "http://localhost:3000").pathname).toBe(
      "/api/console/api/v1/screening/ui/audit-feed",
    );

    // The refreshed feed is printed as received: newest first, no client sort.
    const actions = screen
      .getAllByRole("listitem")
      .map((row) => row.querySelector("bdi")?.textContent);
    expect(actions).toEqual(LIVE_FEED_V2.items.map((event) => event.action));
  });

  it("drops a tick that arrives while the first read is still in flight", async () => {
    setQuery("?source=live");
    const fetchSpy = vi.fn(() => new Promise<Response>(() => {}));
    vi.stubGlobal("fetch", fetchSpy);
    vi.stubGlobal("EventSource", FakeEventSource);

    render(<AuditPage locale="en" />);

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    FakeEventSource.instances[0]?.emit("tick");
    await Promise.resolve();

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("keeps the last successful feed when a tick's re-read fails", async () => {
    setQuery("?source=live");
    const fetchSpy = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(LIVE_FEED))
      .mockRejectedValue(new Error("console went away"));
    vi.stubGlobal("fetch", fetchSpy);
    vi.stubGlobal("EventSource", FakeEventSource);

    render(<AuditPage locale="en" />);

    await waitFor(() => expect(screen.getAllByRole("listitem")).toHaveLength(3));
    FakeEventSource.instances[0]?.emit("tick");

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
    expect(screen.getByText("latest first")).toBeInTheDocument();
    expect(screen.queryByText(CATALOGS.en["audit.liveUnavailable"])).toBeNull();
  });

  it("closes the stream when the screen unmounts", async () => {
    setQuery("?source=live");
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(jsonResponse(LIVE_FEED))));
    vi.stubGlobal("EventSource", FakeEventSource);

    const { unmount } = render(<AuditPage locale="en" />);
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    const stream = FakeEventSource.instances[0];
    expect(stream?.closed).toBe(false);

    unmount();

    expect(stream?.closed).toBe(true);
  });
});
