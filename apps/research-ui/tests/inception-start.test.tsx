import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionStart } from "@/components/inception-start";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import { sent, setUp } from "./inception-helpers";

/** Spec 08 (M4b): the drafts list, resume, a new review, and refusals as sentences. */

afterEach(() => vi.unstubAllGlobals());

describe("inception.start", () => {
  it("shows the empty state and starts a draft, then goes to Scope", async () => {
    const { engine, assign } = setUp({ noDraft: true, search: "" });
    render(<InceptionStart locale="en" />);
    expect(await screen.findByText("No drafts yet. A new review starts here.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start a new review" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(sent(engine)).toContain("POST /api/v1/inception/drafts");
    expect(String(assign.mock.calls[0][0])).toMatch(/^\/en\/inception\/scope\/\?draft=rec_\d{32}$/);
  });

  it("lists drafts: titled, empty, created; resume opens Scope and a created one opens Done", async () => {
    const { engine } = setUp({ draft: completeDraft(), search: "" });
    engine.seed({}, null, "rec_" + "1".repeat(32));
    engine.seed({ title: "Done review" }, { slug: "done-review", path: "C:\\w\\done-review", protocol_fingerprint: "sha256:x", replaced: false }, "rec_" + "2".repeat(32));
    render(<InceptionStart locale="en" />);
    const titled = (await screen.findByText("On-Device Weed Detection")).closest("li")!;
    expect(within(titled).getByRole("link", { name: "Resume" })).toHaveAttribute("href", `/en/inception/scope/?draft=${SESSION}`);
    expect(screen.getByText("Empty draft")).toBeInTheDocument();
    const done = screen.getByText("Done review").closest("li")!;
    expect(within(done).getByRole("link", { name: "See what was created" }).getAttribute("href")).toContain("/en/inception/done/");
    expect(within(done).getByText("done-review")).toBeInTheDocument();
  });

  it("shows a failed listing as a sentence with the code under Details", async () => {
    setUp({ noDraft: true, search: "", refuseOnce: { "GET /api/v1/inception/drafts": { status: 500, body: { detail: { code: "DRAFT_UNREADABLE", message: "x" } } } } });
    render(<InceptionStart locale="en" />);
    const card = await screen.findByRole("alert");
    expect(within(card).getByRole("heading", { name: "This draft cannot be read" })).toBeInTheDocument();
    expect(card.querySelector("details")?.textContent).toContain("DRAFT_UNREADABLE");
  });

  it("speaks French and Arabic", async () => {
    setUp({ noDraft: true, search: "" });
    const { unmount } = render(<InceptionStart locale="fr" />);
    expect(await screen.findByRole("button", { name: "Commencer une nouvelle revue" })).toBeInTheDocument();
    unmount();
    render(<InceptionStart locale="ar" />);
    expect(await screen.findByRole("button", { name: "بدء مراجعة جديدة" })).toBeInTheDocument();
  });
});
