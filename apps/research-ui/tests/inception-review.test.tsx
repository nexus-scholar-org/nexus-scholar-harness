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

const decided = (extra: Record<string, unknown> = {}) => completeDraft({ criteria_decisions: { [proofId()]: true }, ...extra });
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

  it("lists what a replacement archives beside the old protocol (M4d, F1)", async () => {
    setUp({ draft: decided(), existing: "workspace" });
    render(<InceptionReview locale="en" />);
    await screen.findByText("A workspace exists in this folder");
    fireEvent.click(screen.getByRole("button", { name: "Create the workspace" }));
    const confirm = (await screen.findByRole("heading", { name: "Replace the protocol of the existing workspace?" })).closest("section") as HTMLElement;
    const archive = confirm.querySelector("[data-archive]") as HTMLElement;
    expect(within(archive).getByText("literature/")).toBeInTheDocument();
    expect(within(archive).getByText("artifacts/")).toBeInTheDocument();
    expect(archive.textContent).toContain("The new protocol starts with no corpus.");
  });

  it("states a draft that never used Direction, and a skip, without blocking Create (M4d)", async () => {
    const { engine } = setUp({ draft: decided() });
    render(<InceptionReview locale="en" />);
    expect(await screen.findByText("No direction recorded · step 3 was not used")).toBeInTheDocument();
    expect(screen.getByText("No recall seeds kept. The discovery Recall check will start with an empty form.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create the workspace" })).toBeEnabled();
    expect(engine.calls.find((c) => c.path === "/api/v1/inception/preview")?.body).toMatchObject({ session_id: SESSION });
  });

  it("shows the explicit skip as not grounded and the kept seeds under Details (M4d)", async () => {
    const { engine } = setUp({ draft: decided({ golden_seeds: ["10.1/w000", "10.1/w001"] }) });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    const record = engine.drafts.get(SESSION)!;
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/bind`, { skip: true, base_updated_at: record.updated_at });
    render(<InceptionReview locale="en" />);
    expect(await screen.findByText("No direction chosen · Not grounded")).toBeInTheDocument();
    expect(screen.getByText("Recall seeds kept: 2")).toBeInTheDocument();
    const seeds = document.querySelector("[data-review-seeds='2'] details") as HTMLElement;
    expect([...seeds.querySelectorAll("a")].map((a) => a.getAttribute("href"))).toEqual(["https://doi.org/10.1/w000", "https://doi.org/10.1/w001"]);
    expect(screen.getByRole("button", { name: "Create the workspace" })).toBeEnabled();
  });

  it("shows a pool direction and your own one with their grounded badge (M4d)", async () => {
    const { engine } = setUp({ draft: decided() });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    const record = engine.drafts.get(SESSION)!;
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/bind`, { own: "quantum sensing", base_updated_at: record.updated_at });
    render(<InceptionReview locale="en" />);
    const line = (await screen.findByText("Direction: quantum sensing (your own)")).closest("[data-direction-line]") as HTMLElement;
    expect(within(line).getByText("Not grounded")).toBeInTheDocument();
    expect(within(line).getByText("occurs in 0 of 14 titles or abstracts")).toBeInTheDocument();
  });

  it("shows STALE_BINDING from the preview with a link to Direction and no Create (M4d)", async () => {
    const { engine } = setUp({ draft: decided() });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    let record = engine.drafts.get(SESSION)!;
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/bind`, { direction: "weed detection", base_updated_at: record.updated_at });
    record = engine.drafts.get(SESSION)!;
    engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2024 }, base_updated_at: record.updated_at });
    render(<InceptionReview locale="en" />);
    const card = await screen.findByRole("heading", { name: "The direction was chosen on a pool or a scope that no longer matches" });
    const section = card.closest("section") as HTMLElement;
    expect(section.querySelector("details")?.textContent).toContain("STALE_BINDING");
    expect(within(section).getByRole("link", { name: "Choose the direction again" })).toHaveAttribute("href", `/en/inception/direction/?draft=${SESSION}`);
    expect(screen.queryByRole("button", { name: "Create the workspace" })).toBeNull();
  });

  it("shows WORKSPACE_JOB_ACTIVE from a replace with the running job and the code under Details (M4d, F1)", async () => {
    const { engine, assign } = setUp({ draft: decided(), existing: "workspace" });
    render(<InceptionReview locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Create the workspace" }));
    await screen.findByRole("heading", { name: "Replace the protocol of the existing workspace?" });
    engine.refuseNext(`POST /api/v1/inception/drafts/${SESSION}/genesis`, {
      status: 409,
      body: { detail: { code: "WORKSPACE_JOB_ACTIVE", message: "a job is running", details: { job: { job_id: "job-7", kind: "discovery", state: "running" } } } },
    });
    fireEvent.click(screen.getByRole("button", { name: "Replace and back up" }));
    const card = (await screen.findByRole("heading", { name: "A job is still running in this workspace" })).closest("section") as HTMLElement;
    const details = card.querySelector("[data-state-details]") as HTMLElement;
    expect(within(details).getByText("WORKSPACE_JOB_ACTIVE")).toBeInTheDocument();
    expect(details.querySelector("[data-refusal-job]")?.textContent).toContain("discovery · job-7 · running");
    expect(card.textContent).toContain("Wait for the job to end or stop it, then create again");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows ARCHIVE_INCOMPLETE with the backup folder and both file lists under Details (M4d, F1)", async () => {
    const { engine, assign } = setUp({ draft: decided(), existing: "workspace" });
    render(<InceptionReview locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Create the workspace" }));
    await screen.findByRole("heading", { name: "Replace the protocol of the existing workspace?" });
    engine.refuseNext(`POST /api/v1/inception/drafts/${SESSION}/genesis`, {
      status: 409,
      body: {
        detail: {
          code: "ARCHIVE_INCOMPLETE",
          message: "archive stopped",
          details: { backup_dir: "audit/replaced/20261111T120000Z", moved: ["literature/"], not_moved: ["artifacts/"] },
        },
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Replace and back up" }));
    const card = (await screen.findByRole("heading", { name: "Archiving the old corpus stopped part way" })).closest("section") as HTMLElement;
    const details = card.querySelector("[data-state-details]") as HTMLElement;
    expect(within(details).getByText("ARCHIVE_INCOMPLETE")).toBeInTheDocument();
    expect(within(details.querySelector("[data-backup-dir]") as HTMLElement).getByText("audit/replaced/20261111T120000Z")).toBeInTheDocument();
    expect(within(details.querySelector("[data-moved]") as HTMLElement).getByText("literature/")).toBeInTheDocument();
    expect(within(details.querySelector("[data-not-moved]") as HTMLElement).getByText("artifacts/")).toBeInTheDocument();
    expect(card.textContent).toContain("Close the program holding the file, then try again");
    expect(assign).not.toHaveBeenCalled();
  });
});
