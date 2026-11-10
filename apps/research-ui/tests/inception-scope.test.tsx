import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionScope, parseYear } from "@/components/inception-scope";
import { SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/** Spec 01 (M4b): topic, years, languages; save with `base_updated_at`; the conflict as a sentence. */

afterEach(() => vi.unstubAllGlobals());

describe("inception.scope", () => {
  it("shows the stepper with Explore and Direction marked not built yet, not as links", async () => {
    setUp();
    render(<InceptionScope locale="en" />);
    await screen.findByLabelText("Research topic, in one or two sentences");
    const nav = screen.getByRole("navigation", { name: "Inception steps" });
    expect(within(nav).getByText("2 Explore · not built yet").closest("a")).toBeNull();
    expect(within(nav).getByText("3 Direction · not built yet").closest("a")).toBeNull();
    expect(within(nav).getByRole("link", { name: "1 Scope" })).toHaveAttribute("aria-current", "step");
    expect(screen.getByText(SESSION)).toBeInTheDocument();
  });

  it("needs a topic, then saves the answers with the version it read and goes to Shape", async () => {
    const { engine, assign } = setUp();
    render(<InceptionScope locale="en" />);
    const topic = await screen.findByLabelText("Research topic, in one or two sentences");
    const next = screen.getByRole("button", { name: "Continue to Shape" });
    expect(next).toBeDisabled();
    expect(screen.getByText("Write your topic first.")).toBeInTheDocument();
    fireEvent.change(topic, { target: { value: "weed detection on drones" } });
    fireEvent.change(screen.getByLabelText("From year"), { target: { value: "2020" } });
    fireEvent.change(screen.getByLabelText("Languages"), { target: { value: "en, fr" } });
    fireEvent.click(next);
    await waitFor(() => expect(assign).toHaveBeenCalledWith(`/en/inception/shape/?draft=${SESSION}`));
    const put = engine.calls.find((c) => c.method === "PUT")!;
    expect(put.body).toMatchObject({ base_updated_at: "2026-11-09T10:00:00+00:00", draft: { topic: "weed detection on drones", start_year: 2020, end_year: null, languages: ["en", "fr"] } });
  });

  it("refuses a malformed year before saving", async () => {
    const { engine } = setUp({ draft: { topic: "x" } });
    render(<InceptionScope locale="en" />);
    fireEvent.change(await screen.findByLabelText("To year"), { target: { value: "20x4" } });
    expect(screen.getByRole("alert")).toHaveTextContent("Write a year as four digits, or leave it empty.");
    expect(screen.getByRole("button", { name: "Continue to Shape" })).toBeDisabled();
    expect(engine.calls.some((c) => c.method === "PUT")).toBe(false);
    expect(parseYear("")).toBeNull();
  });

  it("shows DRAFT_CONFLICT as a sentence and overwrites nothing", async () => {
    const { engine, assign } = setUp({ draft: { topic: "x" } });
    render(<InceptionScope locale="en" />);
    await screen.findByLabelText("Research topic, in one or two sentences");
    // Another tab saves first.
    engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { topic: "other tab" } });
    fireEvent.click(screen.getByRole("button", { name: "Continue to Shape" }));
    const card = await screen.findByRole("heading", { name: "This draft was saved somewhere else" });
    expect(card.closest("section")?.querySelector("details")?.textContent).toContain("DRAFT_CONFLICT");
    expect(assign).not.toHaveBeenCalled();
    expect((engine.drafts.get(SESSION)!.draft as { topic: string }).topic).toBe("other tab");
  });

  it("says in words that the address names no draft, and asks the engine nothing", async () => {
    const { engine } = setUp({ search: "" });
    render(<InceptionScope locale="en" />);
    expect(await screen.findByRole("heading", { name: "No draft is named in this address. Open one from the list of drafts." })).toBeInTheDocument();
    expect(engine.calls).toEqual([]);
  });

  it("shows a missing draft as the page's refusal", async () => {
    setUp({ noDraft: true });
    render(<InceptionScope locale="en" />);
    expect(await screen.findByRole("heading", { name: "This draft is not here" })).toBeInTheDocument();
  });
});
