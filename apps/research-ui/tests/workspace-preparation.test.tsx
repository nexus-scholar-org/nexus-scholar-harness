import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PREPARATION_COPY, WorkspacePreparationGate } from "@/components/workspace-preparation";
import { stateCopy } from "@/lib/screening-states";

/**
 * H-workspace-format-version: while the engine saves a copy of the review before
 * a newer version opens it, the page says which review and how far; after it,
 * a one-time notice names the folder. The engine is stubbed at `fetch` with the
 * shape of `GET /api/v1/workspaces/preparation`.
 */

const FOLDER = "C:\\Users\\r\\Documents\\Nexus Scholar\\workspaces\\.nexus-copies\\sensor-stress";

function prep(state: string, overrides: Record<string, unknown> = {}) {
  return {
    state, slug: "sensor-stress", title: "Sensor stress review", reason: "build",
    done_bytes: 150_000_000, total_bytes: 600_000_000, ...overrides,
  };
}

function engine(answers: unknown[]) {
  let i = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console", "");
      if (path !== "/api/v1/workspaces/preparation") return new Response("{}", { status: 404 });
      const answer = answers[Math.min(i++, answers.length - 1)];
      return new Response(JSON.stringify({ preparation: answer }), { status: 200, headers: { "content-type": "application/json" } });
    }),
  );
}

const page = <p data-page>the screening home</p>;

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("WorkspacePreparationGate", () => {
  it("shows which review is being copied and how far, then opens the page by itself", async () => {
    engine([prep("preparing"), prep("ready", { done_bytes: 600_000_000, result: { copied: true, copy: { name: "c.zip", folder: FOLDER } } })]);
    render(<WorkspacePreparationGate locale="en" pathname="/en/screening/home/">{page}</WorkspacePreparationGate>);

    const title = await screen.findByRole("heading", { level: 1 });
    expect(title.textContent).toBe("Saving a copy of Sensor stress review before opening it");
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("25");
    expect(screen.getByText("150 of 600 MB")).toBeTruthy();
    expect(screen.getByText(PREPARATION_COPY.en["panel.reason.build"])).toBeTruthy();
    expect(screen.queryByText("the screening home")).toBeNull();

    await waitFor(() => expect(screen.getByText("the screening home")).toBeTruthy(), { timeout: 3000 });
    expect(screen.queryByRole("progressbar")).toBeNull();
  });

  it("never replaces the Workspaces screen, from where another review can be opened", async () => {
    engine([prep("preparing")]);
    render(<WorkspacePreparationGate locale="en" pathname="/en/workspaces/">{page}</WorkspacePreparationGate>);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
    expect(screen.getByText("the screening home")).toBeTruthy();
    expect(screen.queryByRole("progressbar")).toBeNull();
  });

  it("names the folder of the copy once, and not again after it is dismissed", async () => {
    engine([prep("ready", { result: { copied: true, copy: { name: "c.zip", folder: FOLDER } } })]);
    const { unmount } = render(<WorkspacePreparationGate locale="en" pathname="/en/screening/home/">{page}</WorkspacePreparationGate>);
    const notice = await screen.findByText(FOLDER);
    expect(notice.closest("[data-copy-notice]")?.textContent).toContain("Before opening this review, Nexus Scholar saved a copy of it in");
    expect(screen.getByText("the screening home")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(screen.queryByText(FOLDER)).toBeNull();
    unmount();

    render(<WorkspacePreparationGate locale="en" pathname="/en/screening/home/">{page}</WorkspacePreparationGate>);
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(FOLDER)).toBeNull();
  });

  it("shows a refusal's state card and a way back to the workspaces", async () => {
    engine([prep("refused", { refusal: { code: "WORKSPACE_FORMAT_NEWER", message: "Made with a newer version of Nexus Scholar." } })]);
    render(<WorkspacePreparationGate locale="fr" pathname="/fr/screening/home/">{page}</WorkspacePreparationGate>);
    const card = await screen.findByText(stateCopy("fr", "WORKSPACE_FORMAT_NEWER").title);
    expect(card).toBeTruthy();
    expect(screen.getByRole("link", { name: PREPARATION_COPY.fr["refused.workspaces"] }).getAttribute("href")).toBe("/fr/workspaces/");
    expect(screen.queryByText("the screening home")).toBeNull();
  });

  it("tries a failed copy again by opening the same review, then reloads", async () => {
    const calls: string[] = [];
    let opened = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        const path = new URL(url, "http://localhost").pathname.replace("/api/console", "");
        calls.push(`${init?.method ?? "GET"} ${path}`);
        const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
        if (path === "/api/v1/workspaces/open") {
          opened = true;
          return json({ slug: "sensor-stress", path: "x", restarting: true }, 202);
        }
        const refused = prep("refused", { refusal: { code: "WORKSPACE_COPY_FAILED", message: "disk full" } });
        return json({ preparation: opened ? prep("preparing") : refused });
      }),
    );
    const reload = vi.fn();
    vi.stubGlobal("location", { ...window.location, reload, search: "" });
    render(<WorkspacePreparationGate locale="en" pathname="/en/screening/home/">{page}</WorkspacePreparationGate>);
    fireEvent.click(await screen.findByRole("button", { name: stateCopy("en", "WORKSPACE_COPY_FAILED").actionLabel }));
    await waitFor(() => expect(reload).toHaveBeenCalled(), { timeout: 3000 });
    expect(calls).toContain("POST /api/v1/workspaces/open");
  });

  it("announces the copy once, not every second", async () => {
    engine([prep("preparing")]);
    render(<WorkspacePreparationGate locale="en" pathname="/en/screening/home/">{page}</WorkspacePreparationGate>);
    await screen.findByRole("progressbar");
    const live = document.querySelectorAll("[role=status], [aria-live]");
    expect(live).toHaveLength(1);
    expect(live[0].textContent).toBe("Saving a copy of Sensor stress review before opening it");
  });

  it("leaves the page alone when the engine has no such route", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 404 })));
    render(<WorkspacePreparationGate locale="ar" pathname="/ar/screening/home/">{page}</WorkspacePreparationGate>);
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalled());
    expect(screen.getByText("the screening home")).toBeTruthy();
  });

  it("has the same keys in the three languages, and each new refusal has a card in each", () => {
    expect(Object.keys(PREPARATION_COPY.fr).sort()).toEqual(Object.keys(PREPARATION_COPY.en).sort());
    expect(Object.keys(PREPARATION_COPY.ar).sort()).toEqual(Object.keys(PREPARATION_COPY.en).sort());
    for (const code of ["WORKSPACE_FORMAT_NEWER", "WORKSPACE_FORMAT_UNREADABLE", "WORKSPACE_COPY_FAILED", "WORKSPACE_PREPARING"]) {
      for (const locale of ["en", "fr", "ar"] as const) {
        expect(stateCopy(locale, code).known).toBe(true);
      }
    }
  });
});
