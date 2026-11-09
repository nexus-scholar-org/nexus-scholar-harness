import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionReview } from "@/components/inception-review";
import { completeDraft, proofId, SESSION } from "./fixtures/inception-engine";
import { sent, setUp } from "./inception-helpers";

/**
 * Spec 06 (M4b): the preview writes nothing; one gate, one brand button in every
 * state; `WORKSPACE_EXISTS` → replace with the backup explained; `SCREENING_BOUND`
 * → the researcher types the slug and the engine compares it.
 */

afterEach(() => vi.unstubAllGlobals());

const decided = () => completeDraft({ criteria_decisions: { [proofId()]: true } });
const brandButtons = () => document.querySelectorAll("button.bg-brand");

describe("inception.review", () => {
  it("previews the saved draft: criteria verbatim, files, fingerprint, folder, checks", async () => {
    const { engine } = setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    await screen.findByText("Reports the gold-standard proof — mIoU and FPS on a public benchmark");
    expect(screen.getByText("closed-source models")).toBeInTheDocument();
    expect(document.querySelector("[data-fingerprint]")?.textContent).toBe("sha256:" + "ab".repeat(32));
    expect(document.querySelector("[data-target-path]")?.textContent).toContain("on-device-weed-detection");
    expect(within(document.querySelector("[data-files]") as HTMLElement).getByText("protocol.json")).toBeInTheDocument();
    expect(screen.getByText("The folder is free")).toBeInTheDocument();
    expect(brandButtons()).toHaveLength(1);
    expect(sent(engine).filter((c) => c.startsWith("POST /api/v1/inception/drafts/"))).toEqual([]);
  });

  it("creates the workspace and goes to Done", async () => {
    const { engine, assign } = setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Create the workspace" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith(`/en/inception/done/?draft=${SESSION}`));
    expect(engine.calls.find((c) => c.path.endsWith("/genesis"))?.body).toEqual({});
  });

  it("shows an undecided criterion as a sentence and offers no gate", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionReview locale="en" />);
    const heading = await screen.findByRole("heading", { name: "Some criteria still wait for your decision" });
    expect(heading.closest("section")?.querySelector("details")?.textContent).toContain("CRITERIA_UNDECIDED");
    expect(screen.queryByRole("button", { name: "Create the workspace" })).toBeNull();
  });

  it("disables Create while a project edit is not checked", async () => {
    setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    const create = await screen.findByRole("button", { name: "Create the workspace" });
    fireEvent.change(screen.getByLabelText("Title of the review"), { target: { value: "Another title" } });
    expect(create).toBeDisabled();
    expect(screen.getAllByText("The preview is out of date. Check the protocol again to create the workspace.").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Check the protocol" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Create the workspace" })).toBeEnabled());
  });

  it("asks before replacing an existing workspace, then sends replace", async () => {
    const { engine, assign } = setUp({ draft: decided(), existing: "workspace" });
    render(<InceptionReview locale="en" />);
    expect(await screen.findByText("A workspace exists in this folder")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create the workspace" }));
    const confirm = await screen.findByRole("heading", { name: "Replace the protocol of the existing workspace?" });
    expect(confirm.closest("section")?.textContent).toContain("audit/replaced/");
    expect(brandButtons()).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Create the workspace" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Replace and back up" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(engine.calls.filter((c) => c.path.endsWith("/genesis")).map((c) => c.body)).toEqual([{}, { replace: true }]);
  });

  it("says the fingerprint is a preview that creating re-stamps", async () => {
    setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    expect(await screen.findByText(/Creating the workspace stamps the date into the protocol/)).toBeInTheDocument();
    expect(screen.getByText("Protocol fingerprint (preview)")).toBeInTheDocument();
  });

  it("does not offer Replace when the folder is not a workspace", async () => {
    setUp({ draft: decided(), existing: "folder" });
    render(<InceptionReview locale="en" />);
    expect(await screen.findByText("A folder with this name exists and is not a workspace")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Create the workspace" }));
    expect(await screen.findByRole("heading", { name: "A workspace for this title already exists" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Replace and back up" })).toBeNull();
  });

  it("needs the typed slug for a workspace with screening; the engine compares it", async () => {
    const { engine, assign } = setUp({ draft: decided(), existing: "bound" });
    render(<InceptionReview locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Create the workspace" }));
    fireEvent.click(await screen.findByRole("button", { name: "Replace and back up" }));
    const bound = await screen.findByRole("heading", { name: "Screening was done under the current protocol" });
    expect(bound.closest("section")?.textContent).toContain("4 screening decision events, 1 batch decision files");
    const confirmButton = screen.getByRole("button", { name: "Replace, and discard the screening link" });
    expect(confirmButton).toBeDisabled();
    expect(brandButtons()).toHaveLength(1);

    fireEvent.change(screen.getByLabelText(/To replace it anyway, type the workspace name/), { target: { value: "wrong" } });
    fireEvent.click(confirmButton);
    expect(await screen.findByRole("heading", { name: "The name does not match" })).toBeInTheDocument();
    expect(screen.getByLabelText(/To replace it anyway/)).toHaveValue("wrong");
    expect(assign).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText(/To replace it anyway/), { target: { value: "on-device-weed-detection" } });
    fireEvent.click(screen.getByRole("button", { name: "Replace, and discard the screening link" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(engine.calls.filter((c) => c.path.endsWith("/genesis")).at(-1)?.body).toEqual({ replace: true, confirm_discard_screening_binding: "on-device-weed-detection" });
  });

  it("Escape cancels a confirmation and writes nothing", async () => {
    const { engine } = setUp({ draft: decided(), existing: "workspace" });
    render(<InceptionReview locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Create the workspace" }));
    const heading = await screen.findByRole("heading", { name: "Replace the protocol of the existing workspace?" });
    fireEvent.keyDown(heading, { key: "Escape" });
    expect(await screen.findByRole("button", { name: "Create the workspace" })).toBeInTheDocument();
    expect(engine.calls.filter((c) => c.path.endsWith("/genesis"))).toHaveLength(1);
  });
});
