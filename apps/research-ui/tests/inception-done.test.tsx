import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionDone } from "@/components/inception-done";
import { ROOT } from "./fixtures/inception-engine";
import { sent, setUp } from "./inception-helpers";

/** Spec 07 (M4b): what genesis wrote, then `POST /workspaces/open` and screening Home. */

afterEach(() => vi.unstubAllGlobals());

const emitted = (extra: Record<string, unknown> = {}) => ({
  slug: "weed-review",
  path: `${ROOT}\\weed-review`,
  protocol_fingerprint: "sha256:" + "ab".repeat(32),
  replaced: false,
  ...extra,
});

describe("inception.done", () => {
  it("shows the folder and fingerprint, opens the workspace and lands on screening Home", async () => {
    const { engine, assign } = setUp({ draft: { title: "Weed review" }, emitted: emitted() });
    render(<InceptionDone locale="en" />);
    expect(await screen.findByRole("heading", { name: "The workspace is created" })).toHaveFocus();
    expect(document.querySelector("[data-done-path]")?.textContent).toBe(`${ROOT}\\weed-review`);
    fireEvent.click(screen.getByRole("button", { name: "Open the workspace" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/screening/home/"));
    expect(engine.calls.find((c) => c.path === "/api/v1/workspaces/open")?.body).toEqual({ slug: "weed-review" });
  });

  it("after a replacement, shows the backup and previous fingerprint the draft recorded", async () => {
    setUp({ emitted: emitted({ replaced: true, previous_fingerprint: "sha256:" + "cd".repeat(32), backup_dir: `${ROOT}\\weed-review\\audit\\replaced\\20261109T100000Z` }) });
    render(<InceptionDone locale="en" />);
    expect(await screen.findByRole("heading", { name: "The protocol is replaced" })).toBeInTheDocument();
    expect(document.querySelector("[data-backup]")?.textContent).toContain("audit\\replaced\\20261109T100000Z");
    expect(screen.getByText("sha256:" + "cd".repeat(32))).toBeInTheDocument();
  });

  it("names the terminal command when the app cannot switch workspaces", async () => {
    setUp({ emitted: emitted(), refuseOnce: { "POST /api/v1/workspaces/open": { status: 501, body: { detail: { code: "RESTART_UNSUPPORTED", message: "x" } } } } });
    render(<InceptionDone locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Open the workspace" }));
    expect(await screen.findByRole("heading", { name: "This app cannot switch workspaces" })).toBeInTheDocument();
    expect(screen.getByText(`nexus-scholar ui --workspace "${ROOT}\\weed-review"`)).toBeInTheDocument();
  });

  it("a draft that created nothing points back to Review", async () => {
    const { engine } = setUp({ draft: { title: "x" } });
    render(<InceptionDone locale="en" />);
    expect(await screen.findByRole("heading", { name: "This draft has not created a workspace yet." })).toBeInTheDocument();
    expect(sent(engine).some((c) => c.includes("/workspaces/open"))).toBe(false);
  });
});
