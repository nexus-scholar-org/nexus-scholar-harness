import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionImport } from "@/components/inception-import";
import { InceptionScope } from "@/components/inception-scope";
import { InceptionShape } from "@/components/inception-shape";
import { InceptionStart } from "@/components/inception-start";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import { sent, setUp } from "./inception-helpers";

/**
 * Spec 09 (M10b): start from an existing review. The engine reads the source and
 * answers the report; the screen creates nothing before its one brand button,
 * and the draft it opens carries a banner and a mark per imported step.
 */

afterEach(() => vi.unstubAllGlobals());

const PROTOCOL = {
  playbook_type: "SCOPING_REVIEW",
  metadata: { title: "UAV crop-weed mapping", lead_researcher: "M" },
  epistemology: { primary_paradigm: "Pragmatist / Mixed Methods" },
  research_questions: [{ id: "RQ1", text: "How reliable is UAV weed mapping?" }],
  search_strategy: {},
  screening_criteria: {
    inclusion: [{ id: "INC-01", criterion: "Field trials" }],
    exclusion: [{ id: "EXC-01", criterion: "Satellite only", reason_category: "WRONG_PLATFORM" }],
  },
};
const WORKSPACES = [{ slug: "uav-crop-weed-v03", title: "UAV review v0.3", protocol: PROTOCOL }];

const posts = (engine: ReturnType<typeof setUp>["engine"]) => engine.calls.filter((c) => c.method === "POST" && c.path.endsWith("/drafts/import"));

describe("inception.import", () => {
  it("lists the workspaces, offers a file, says text needs the assistant, and has no brand button yet", async () => {
    setUp({ noDraft: true, workspaces: WORKSPACES, search: "" });
    render(<InceptionImport locale="en" />);
    expect(await screen.findByText("UAV review v0.3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Choose a file" })).toBeInTheDocument();
    expect(screen.getByText(/Reading text needs the assistant/)).toBeInTheDocument();
    expect(document.querySelectorAll("button.bg-brand")).toHaveLength(0);
  });

  it("reads a workspace with a dry run, shows the three groups, then creates and opens Scope", async () => {
    const { engine, assign } = setUp({ noDraft: true, workspaces: WORKSPACES, search: "" });
    render(<InceptionImport locale="en" />);
    fireEvent.click(await screen.findByRole("radio", { name: /UAV review v0.3/ }));
    const report = (await screen.findByText("Comes across as you wrote it")).closest("[data-report]") as HTMLElement;
    expect(posts(engine).map((c) => c.body)).toEqual([{ source: { kind: "workspace", slug: "uav-crop-weed-v03" }, dry_run: true }]);
    expect(within(report).getByText(/1 research questions, 2 criteria/)).toBeInTheDocument();
    expect(within(report).getByText("Each question's evidence type and synthesis type are replaced by the lens's defaults.")).toBeInTheDocument();
    expect(within(report).getByText("You write your question (a protocol does not store it).")).toBeInTheDocument();
    expect(sent(engine).some((c) => c === "POST /api/v1/inception/drafts")).toBe(false);
    expect(document.querySelectorAll("button.bg-brand")).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Create the draft from this review" }));
    await waitFor(() => expect(assign).toHaveBeenCalled());
    expect(posts(engine).at(-1)?.body).toMatchObject({ dry_run: false, expect_fingerprint: "sha256:" + "ef".repeat(32) });
    expect(assign.mock.calls[0][0]).toMatch(/^\/en\/inception\/scope\/\?draft=rec_/);
  });

  it("sends a picked file's exact bytes, base64", async () => {
    const { engine } = setUp({ noDraft: true, workspaces: [], search: "" });
    render(<InceptionImport locale="en" />);
    await screen.findByText(/No workspace with a protocol is under/);
    const text = JSON.stringify(PROTOCOL);
    const file = new File([text], "protocol.json", { type: "application/json" });
    fireEvent.change(document.querySelector("[data-file-input]") as HTMLInputElement, { target: { files: [file] } });
    await screen.findByText("Comes across as you wrote it");
    const body = posts(engine)[0].body as { source: { kind: string; file_name: string; content_base64: string } };
    expect(body.source.kind).toBe("file");
    expect(body.source.file_name).toBe("protocol.json");
    expect(Buffer.from(body.source.content_base64, "base64").toString("utf-8")).toBe(text);
  });

  it("shows a refusal with its code and clears the source", async () => {
    setUp({ noDraft: true, workspaces: [], search: "" });
    render(<InceptionImport locale="en" />);
    const file = new File(['{"title": "x"}'], "notes.json", { type: "application/json" });
    fireEvent.change(document.querySelector("[data-file-input]") as HTMLInputElement, { target: { files: [file] } });
    expect(await screen.findByRole("heading", { name: "That is not a protocol" })).toBeInTheDocument();
    expect(document.querySelector("[data-import-refusal='IMPORT_NOT_A_PROTOCOL']")).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Create the draft from this review" })).toBeNull();
  });

});

describe("inception.import on the steps", () => {
  const origin = (checked: Record<string, boolean>) => ({
    kind: "import",
    source: { kind: "workspace", label: "uav-crop-weed-v03", read: "protocol", protocol_created_at: "2026-10-12T00:00:00+00:00", protocol_fingerprint: "sha256:" + "ef".repeat(32), target_slug: "x", collides_with_source: false },
    imported_at: "2026-11-18T09:00:00+00:00",
    checked,
    report: { carried: [], lost: [{ what: "rationale" }], needs_you: ["topic"] },
    earlier_pool: { min: 0, max: 1000 },
  });

  it("shows the banner and the marks, and clears the current step's mark once it is opened", async () => {
    const { engine } = setUp({ draft: completeDraft({ topic: "", rqs: ["How reliable is UAV weed mapping?"] }) });
    engine.seed(completeDraft({ topic: "", rqs: ["How reliable is UAV weed mapping?"] }), null, SESSION, { origin: origin({ scope: false, direction: false, shape: false, criteria: false, review: false }) });
    render(<InceptionScope locale="en" />);
    expect(await screen.findByText(/Started from uav-crop-weed-v03/)).toBeInTheDocument();
    expect(screen.getByText("What was not carried (2)")).toBeInTheDocument();
    expect(document.querySelector("[data-imported-mark='shape']")).not.toBeNull();
    await waitFor(() => expect(document.querySelector("[data-imported-mark='scope']")).toBeNull());
    expect(engine.calls.some((c) => c.method === "POST" && c.path.endsWith("/origin/checked") && (c.body as { step: string }).step === "scope")).toBe(true);
    // The topic is not stored by a protocol: the first question is offered, never copied unasked.
    expect(screen.getByLabelText(/topic/i, { selector: "textarea" })).toHaveValue("");
    fireEvent.click(screen.getByRole("button", { name: "Use research question 1" }));
    expect(screen.getByLabelText(/topic/i, { selector: "textarea" })).toHaveValue("How reliable is UAV weed mapping?");
  });

  it("offers the earlier range on Shape, filled only when pressed", async () => {
    const { engine } = setUp({ draft: completeDraft() });
    engine.seed(completeDraft(), null, SESSION, { origin: origin({ scope: true, direction: true, shape: false, criteria: false, review: false }) });
    render(<InceptionShape locale="en" />);
    const button = await screen.findByRole("button", { name: "Use the earlier range (0 to 1000)" }, { timeout: 5000 });
    expect(screen.getByLabelText("up to")).toHaveValue(null);
    fireEvent.click(button);
    expect(screen.getByLabelText("up to")).toHaveValue(1000);
  });

  it("the start screen links to the import and names an imported draft's source", async () => {
    const { engine } = setUp({ noDraft: true, search: "" });
    engine.seed({ title: "Second review" }, null, SESSION, { origin: origin({}) });
    render(<InceptionStart locale="en" />);
    expect(await screen.findByText("Started from uav-crop-weed-v03")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start from an existing review" })).toHaveAttribute("href", "/en/inception/import/");
  });
});
