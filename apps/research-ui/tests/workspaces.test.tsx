import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WORKSPACES_COPY, WorkspacesScreen } from "@/components/workspaces-screen";
import { SUPPORTED_LOCALES } from "@/i18n";
import { currentNavId } from "@/components/site-header";
import { stateCopy } from "@/lib/screening-states";
import { previewSlug } from "@/lib/workspaces";

/**
 * The workspace screen (spec 00) in jsdom. The engine is stubbed at `fetch`
 * with the shapes of `GET/POST /workspaces` and `POST /workspaces/open`; every
 * check is the engine's, so the tests pin what the screen sends and shows.
 */

const ROOT = "C:\\Users\\r\\Documents\\Nexus Scholar\\workspaces";

function item(slug: string, overrides: Record<string, unknown> = {}) {
  return {
    slug, title: slug.replace(/-/g, " "), path: `${ROOT}\\${slug}`, valid: true, has_corpus: false, screening_started: false,
    last_event: { at: "2026-11-05T10:00:00+00:00", action: "GENESIS" }, is_current: false, ...overrides,
  };
}

function listing(overrides: Record<string, unknown> = {}) {
  return {
    root: ROOT, root_source: "default", writable: true, current: { slug: "uav-review", path: `${ROOT}\\uav-review` },
    busy: { run_active: false, pairing_open: false }, skipped_count: 0,
    items: [item("uav-review", { is_current: true, has_corpus: true, screening_started: true }), item("crop-review", { has_corpus: true })],
    ...overrides,
  };
}

type Call = { method: string; path: string; body: Record<string, unknown> | null };

function engine(options: { list?: (invalid: boolean) => unknown; create?: (body: Record<string, unknown>) => Response; open?: Response; meta?: () => unknown } = {}) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const parsed = new URL(url, "http://localhost");
      const path = parsed.pathname.replace("/api/console", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      calls.push({ method, path: path + parsed.search, body });
      const ok = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "content-type": "application/json" } });
      if (path === "/api/v1/workspaces" && method === "GET") return ok(options.list ? options.list(parsed.searchParams.get("include_invalid") === "true") : listing());
      if (path === "/api/v1/workspaces" && method === "POST") return options.create ? options.create(body ?? {}) : ok({ slug: "weed-mapping", path: `${ROOT}\\weed-mapping`, protocol_fingerprint: "sha256:x" }, 201);
      if (path === "/api/v1/workspaces/open") return options.open ?? ok({ slug: "crop-review", path: `${ROOT}\\crop-review`, restarting: true }, 202);
      if (path === "/api/v1/workspace/meta") return ok(options.meta ? options.meta() : { workspace: `${ROOT}\\crop-review` });
      return new Response(JSON.stringify({ detail: { code: "NOT_FOUND" } }), { status: 404 });
    }),
  );
  return calls;
}

const refuse = (status: number, code: string, details?: unknown) =>
  new Response(JSON.stringify({ detail: { code, message: code.toLowerCase(), ...(details ? { details } : {}) } }), { status, headers: { "content-type": "application/json" } });

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("workspaces.list", () => {
  it("lists the workspaces with their status and marks the open one", async () => {
    engine();
    render(<WorkspacesScreen locale="en" />);
    const current = await screen.findByText("uav review");
    const row = current.closest("tr")!;
    expect(row).toHaveAttribute("aria-current", "true");
    expect(within(row).getByText("Open now")).toBeInTheDocument();
    expect(within(row).getByText("Screening in progress")).toBeInTheDocument();
    expect(within(row).queryByRole("button", { name: "Open" })).toBeNull();
    const other = screen.getByText("crop review").closest("tr")!;
    expect(within(other).getByText("Corpus accepted")).toBeInTheDocument();
    expect(within(other).getByRole("button", { name: "Open" })).toBeEnabled();
    expect(document.body.textContent).toContain(ROOT);
  });

  it("links New review to the inception drafts, as a secondary action beside the one brand button (M4b)", async () => {
    engine();
    render(<WorkspacesScreen locale="en" />);
    const link = await screen.findByRole("link", { name: "New review" });
    expect(link).toHaveAttribute("href", "/en/inception/");
    expect(link.className).not.toContain("bg-brand");
    expect(document.querySelectorAll(".bg-brand")).toHaveLength(1);
  });

  it("shows the engine's status: published reads published, not in progress (M6-beta, U-3)", async () => {
    engine({
      list: () =>
        listing({
          items: [
            item("done-review", { has_corpus: true, screening_started: true, status: "PUBLISHED" }),
            item("changed-review", { has_corpus: true, screening_started: true, status: "PUBLISHED_CHANGED" }),
          ],
        }),
    });
    render(<WorkspacesScreen locale="en" />);
    const done = (await screen.findByText("done review")).closest("tr")!;
    expect(within(done).getByText("Published")).toBeInTheDocument();
    expect(within(done).queryByText("Screening in progress")).toBeNull();
    const changed = screen.getByText("changed review").closest("tr")!;
    expect(within(changed).getByText("Published, decisions since")).toBeInTheDocument();
  });

  it("hides invalid folders behind a count and shows them greyed with the reason and no Open", async () => {
    const calls = engine({
      list: (invalid) => listing({ skipped_count: 1, items: [...listing().items, ...(invalid ? [{ slug: "notes", title: null, path: `${ROOT}\\notes`, valid: false, invalid_reason: "missing protocol.json, project.json", is_current: false }] : [])] }),
    });
    render(<WorkspacesScreen locale="en" />);
    expect(await screen.findByText(/1 folders skipped/)).toBeInTheDocument();
    expect(document.querySelector('[data-invalid="notes"]')).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show them" }));
    const row = await waitFor(() => {
      const found = document.querySelector('[data-invalid="notes"]');
      if (!found) throw new Error("not yet");
      return found;
    });
    expect(row).toHaveAttribute("aria-disabled", "true");
    expect(row).toHaveTextContent("Not a workspace: no project.json, no protocol.json");
    expect(within(row as HTMLElement).queryByRole("button")).toBeNull();
    expect(calls.some((c) => c.path === "/api/v1/workspaces?include_invalid=true")).toBe(true);
  });

  it("shows the empty state, and disables Open while a run is active", async () => {
    engine({ list: () => listing({ items: [], current: null }) });
    const { unmount } = render(<WorkspacesScreen locale="en" />);
    expect(await screen.findByText("No workspaces yet")).toBeInTheDocument();
    unmount();
    vi.unstubAllGlobals();
    engine({ list: () => listing({ busy: { run_active: true, pairing_open: false } }) });
    render(<WorkspacesScreen locale="en" />);
    const open = await screen.findByRole("button", { name: "Open" });
    expect(open).toBeDisabled();
    expect(document.querySelector("[data-busy]")).toHaveTextContent("An agent run is active");
  });
});

describe("workspaces.create", () => {
  it("previews the folder, sends only the title, and shows the accept-corpus step", async () => {
    const calls = engine();
    render(<WorkspacesScreen locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "New workspace" }));
    const field = screen.getByLabelText("Title of the review");
    fireEvent.change(field, { target: { value: "Weed Mapping!" } });
    expect(document.querySelector("[data-folder]")).toHaveTextContent(`${ROOT}\\weed-mapping`);
    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    const heading = await screen.findByRole("heading", { name: "Workspace created" });
    await waitFor(() => expect(heading).toHaveFocus());
    expect(calls.find((c) => c.method === "POST")!.body).toEqual({ title: "Weed Mapping!" });
    const next = document.querySelector("[data-next-step]")!;
    expect(next).toHaveTextContent(`nexus-scholar accept-corpus --workspace "${ROOT}\\weed-mapping"`);
    expect(next.querySelector("[data-draft]")).toHaveTextContent("Placeholder protocol");
  });

  it.each([
    ["WORKSPACE_EXISTS", 409],
    ["WORKSPACE_TITLE_INVALID", 422],
    ["WORKSPACE_PATH_REFUSED", 422],
    ["WORKSPACE_ROOT_UNAVAILABLE", 409],
  ])("shows the engine's %s card", async (code, status) => {
    engine({ create: () => refuse(status, code) });
    render(<WorkspacesScreen locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "New workspace" }));
    fireEvent.change(screen.getByLabelText("Title of the review"), { target: { value: "Something" } });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    const card = await waitFor(() => {
      const found = document.querySelector(`[data-state="${code}"]`);
      if (!found) throw new Error("not yet");
      return found;
    });
    expect(card).toHaveTextContent(stateCopy("en", code).title);
    expect(card).toHaveTextContent(code);
  });

  it("closes the panel with Escape and returns focus to New workspace", async () => {
    engine();
    render(<WorkspacesScreen locale="en" />);
    const button = await screen.findByRole("button", { name: "New workspace" });
    fireEvent.click(button);
    fireEvent.keyDown(screen.getByLabelText("Title of the review"), { key: "Escape" });
    expect(screen.queryByLabelText("Title of the review")).toBeNull();
    expect(button).toHaveFocus();
  });
});

describe("workspaces.open", () => {
  it("asks the engine to restart and waits for it before loading screening", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign, search: "" });
    let meta = 0;
    const calls = engine({ meta: () => ({ workspace: meta++ < 1 ? `${ROOT}\\uav-review` : `${ROOT}\\crop-review` }) });
    render(<WorkspacesScreen locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Open" }));
    expect(await screen.findByText("Opening crop review…")).toBeInTheDocument();
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/screening/"), { timeout: 4000 });
    expect(calls.find((c) => c.path === "/api/v1/workspaces/open")!.body).toEqual({ slug: "crop-review" });
  });

  it("shows WORKSPACE_BUSY with the way to screening home", async () => {
    engine({ open: refuse(409, "WORKSPACE_BUSY", { run_active: true, pairing_open: false }) });
    render(<WorkspacesScreen locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Open" }));
    await screen.findByText(/An agent run is active/);
    expect(document.querySelector('[data-state="WORKSPACE_BUSY"]')).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /screening home/ })[0]).toHaveAttribute("href", expect.stringContaining("/en/screening/home"));
  });
});

describe("workspaces copy and shell", () => {
  it("has every key in every locale, and the header marks the screen current", () => {
    const keys = Object.keys(WORKSPACES_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(WORKSPACES_COPY[locale]).sort()).toEqual(keys);
    expect(currentNavId("/ar/workspaces/", "ar")).toBe("workspaces");
    for (const code of ["WORKSPACE_TITLE_INVALID", "WORKSPACE_EXISTS", "WORKSPACE_PATH_REFUSED", "WORKSPACE_ROOT_UNAVAILABLE", "WORKSPACE_NOT_VALID", "WORKSPACE_BUSY", "RESTART_UNSUPPORTED"]) {
      for (const locale of SUPPORTED_LOCALES) expect(stateCopy(locale, code).known).toBe(true);
    }
  });

  it("previews the folder name the way the engine derives it", () => {
    expect(previewSlug("  Weed Mapping with UAVs!  ")).toBe("weed-mapping-with-uavs");
    expect(previewSlug("Revue -- systématique")).toBe("revue-systématique");
    expect(previewSlug("!!!")).toBe("");
  });
});
