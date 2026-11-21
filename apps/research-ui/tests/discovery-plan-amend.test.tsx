import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DiscoveryPlan } from "@/components/discovery-plan";

import { setUp } from "./discovery-helpers";

/**
 * "Change the search" on Plan (M11a part D; spec
 * `docs/ux/phase1-discovery/final/10-plan-amend-search.md`, "Acceptance tests").
 * The fake engine answers the plan, the workbench routes and the amendment;
 * the engine's own path is pinned by `tests/console/test_workbench_amend_api.py`.
 */

afterEach(() => vi.unstubAllGlobals());

const AMEND = "/api/v1/discovery/workbench/amend";
const PROVIDERS = { protocolProviders: ["openalex", "semanticscholar", "arxiv"] };
type Engine = ReturnType<typeof setUp>["engine"];
const posts = (engine: Engine, path: string) => engine.calls.filter((c) => c.method === "POST" && c.path === path);
const real = (engine: Engine) => posts(engine, AMEND).filter((c) => !(c.body as { dry_run?: boolean }).dry_run);
const confirmation = () => document.querySelector("[data-amend-confirm]") as HTMLElement | null;
/** Every brand button and brand link on the screen (03-guidance rule 2). */
const brand = () => [...document.querySelectorAll<HTMLElement>("button[data-variant='primary'], a[data-variant='primary']")].map((b) => b.textContent?.trim());

async function openSearch() {
  const button = await screen.findByRole("button", { name: "Change the search" });
  expect(button).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(button);
  await waitFor(() => expect(document.querySelector("[data-workbench]")).not.toBeNull());
}

/** Remove the second concept and open the confirmation; resolves once the engine's list is on screen. */
async function openConfirmation() {
  fireEvent.click(screen.getAllByRole("button", { name: "Remove concept" })[1]);
  fireEvent.click(await screen.findByRole("button", { name: "Record this amendment" }));
  await waitFor(() => expect(confirmation()?.querySelector("[data-consequences]")).not.toBeNull());
  return confirmation() as HTMLElement;
}

describe("discovery.plan change the search", () => {
  it("is a button in the executed strings' header; opened, a region above the columns on the protocol's query, nothing counted on open", async () => {
    const { engine } = setUp(PROVIDERS);
    render(<DiscoveryPlan locale="en" />);
    const button = await screen.findByRole("button", { name: "Change the search" });
    expect(button.closest("[data-plan-strings]")).not.toBeNull();
    expect(document.querySelector("[data-workbench]")).toBeNull();
    await openSearch();
    const region = document.querySelector("[data-plan-search]") as HTMLElement;
    // Above the two columns: before the picker in document order, outside the main column.
    expect(region.compareDocumentPosition(document.querySelector("[data-plan-picker]")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(region.closest(".lg\\:col-span-2")).toBeNull();
    expect(button).toHaveAttribute("aria-controls", region.id);
    expect(document.activeElement).toBe(region);
    const protocol = document.querySelector("[data-in-protocol]") as HTMLElement;
    expect(within(protocol).getByText("In the protocol")).toBeInTheDocument();
    expect(protocol.textContent).toContain("weed detection OR weed segmentation");
    expect(within(document.querySelector("[data-this-version]") as HTMLElement).getByText("This version")).toBeInTheDocument();
    expect((screen.getByLabelText("Concept 1") as HTMLInputElement).value).toBe("weed detection");
    expect(posts(engine, "/api/v1/discovery/workbench/counts").filter((c) => !(c.body as { dry_run?: boolean }).dry_run)).toHaveLength(0);
    expect(screen.queryByRole("button", { name: "Use this version" })).toBeNull();
    // One brand button on the screen: Count; Continue to Recall is a plain link while the region is open.
    expect(brand()).toEqual(["Count"]);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(document.querySelector("[data-workbench]")).toBeNull();
    expect(document.activeElement).toBe(button);
    expect(brand()).toEqual(["Continue to Recall"]);
  });

  it("Record this amendment waits for a change, asks one sentence, lists what it changes, and sends concepts, reason and the fingerprint read", async () => {
    const { engine } = setUp(PROVIDERS);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    expect(screen.getByRole("button", { name: "Record this amendment" })).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: "Select weed detection to merge" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select edge device to merge" }));
    fireEvent.click(screen.getByRole("button", { name: "Merge into one" }));
    fireEvent.click(screen.getByRole("button", { name: "Merge" }));
    const opener = await screen.findByRole("button", { name: "Record this amendment" });
    await waitFor(() => expect(opener).not.toBeDisabled());
    // The version differs: the decision bar's one primary action is now "Record this amendment".
    expect(brand()).toEqual(["Record this amendment"]);
    fireEvent.click(opener);
    await waitFor(() => expect(confirmation()?.querySelector("[data-consequences]")).not.toBeNull());
    const box = confirmation() as HTMLElement;
    expect(document.activeElement).toBe(within(box).getByLabelText("Why are you changing the search?"));
    expect(box.querySelector("[data-amend-counts] p")?.textContent).toBe("Before: OpenAlex 166, Semantic Scholar not counted");
    // The one brand button on the screen while the confirmation is open.
    expect(brand()).toEqual(["Record this amendment"]);
    expect([...box.querySelectorAll("button")].map((b) => b.textContent)).toEqual(["Cancel", "Record this amendment"]);
    fireEvent.click(within(box).getByRole("button", { name: "Record this amendment" }));
    expect(await within(box).findByText("Write one sentence.")).toBeInTheDocument();
    expect(real(engine)).toHaveLength(0);
    fireEvent.change(within(box).getByLabelText("Why are you changing the search?"), { target: { value: "Edge devices and weed detection are one idea here." } });
    fireEvent.click(within(box).getByRole("button", { name: "Record this amendment" }));
    expect(await screen.findByText(/Amendment recorded\. The search in the protocol has changed\./)).toBeInTheDocument();
    expect(real(engine)).toHaveLength(1);
    const body = real(engine)[0].body as Record<string, unknown>;
    expect(Object.keys(body).sort()).toEqual(["concepts", "dry_run", "protocol_fingerprint", "query_key", "reason"]);
    expect(body.reason).toBe("Edge devices and weed detection are one idea here.");
    expect(body.concepts).toEqual([{ concept: "weed detection", synonyms: ["weed segmentation", "edge device", "embedded"] }]);
    expect(engine.amendments).toHaveLength(1);
    // Plan is read again with the new fingerprint; the researcher's own amendment is not "changed elsewhere"; focus on the h1.
    await waitFor(() => expect(document.querySelector("[data-plan-strings]")?.textContent).toContain("sha256:01"));
    expect(document.querySelector("[data-plan-changed]")).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole("heading", { level: 1 })));
  });

  it("an edit while the confirmation is open closes it, so the version recorded is always the one on screen", async () => {
    const { engine } = setUp(PROVIDERS);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    await openConfirmation();
    fireEvent.change(screen.getAllByLabelText("Add a term")[0], { target: { value: "weed mapping" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Add" })[0]);
    await waitFor(() => expect(confirmation()).toBeNull());
    // Discard too.
    await waitFor(() => expect(screen.getByRole("button", { name: "Record this amendment" })).not.toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: "Record this amendment" }));
    await waitFor(() => expect(confirmation()).not.toBeNull());
    fireEvent.click(screen.getByRole("button", { name: "Discard edits" }));
    await waitFor(() => expect(confirmation()).toBeNull());
    expect(real(engine)).toHaveLength(0);
  });

  it("Escape and Cancel close the confirmation and return focus to Record this amendment; Enter in the reason never records; Ctrl+Enter opens it", async () => {
    const { engine } = setUp(PROVIDERS);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const box = await openConfirmation();
    const field = within(box).getByLabelText("Why are you changing the search?");
    fireEvent.change(field, { target: { value: "One concept is enough." } });
    fireEvent.keyDown(field, { key: "Enter" });
    expect(real(engine)).toHaveLength(0);
    fireEvent.keyDown(field, { key: "Escape" });
    await waitFor(() => expect(confirmation()).toBeNull());
    const opener = screen.getByRole("button", { name: "Record this amendment" });
    await waitFor(() => expect(document.activeElement).toBe(opener));
    // Ctrl+Enter in the workbench opens the confirmation once the version differs (it never records).
    fireEvent.keyDown(screen.getByLabelText("Concept 1"), { key: "Enter", ctrlKey: true });
    await waitFor(() => expect(confirmation()).not.toBeNull());
    expect(posts(engine, "/api/v1/discovery/workbench/counts").filter((c) => !(c.body as { dry_run?: boolean }).dry_run)).toHaveLength(0);
    fireEvent.click(within(confirmation() as HTMLElement).getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole("button", { name: "Record this amendment" })));
    expect(real(engine)).toHaveLength(0);
  });

  it("names each earlier run, each staged export and the recall check in the engine's words, and the estimate only when the engine says", async () => {
    const { engine } = setUp({ ...PROVIDERS, staged: true });
    expect(engine.handle("POST", "/api/v1/discovery/recall", { seeds: [{ id: "10.1234/a", kind: "doi", source: "you" }] }).status).toBe(202);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const list = (await openConfirmation()).querySelector("[data-consequences]") as HTMLElement;
    expect(list.querySelector("[data-conseq='export']")?.textContent).toBe(
      "Scopus, 120 records, staged 2026-11-01. Searched there with a string you did not state. It stays as it is. If you change that search too, export again and replace the file.",
    );
    expect(list.querySelector("[data-conseq='recall'] bdi[dir='ltr']")?.textContent).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/);
    // No estimate was counted for this protocol: the engine sends false and no line is printed.
    expect(list.querySelector("[data-conseq='estimate']")).toBeNull();
  });

  it("prints the estimate line when an estimate was counted, even with no run and no recall check", async () => {
    const { engine } = setUp(PROVIDERS);
    expect(engine.handle("POST", "/api/v1/discovery/estimate", {}).status).toBe(200);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const list = (await openConfirmation()).querySelector("[data-consequences]") as HTMLElement;
    expect(list.querySelector("[data-conseq='estimate']")?.textContent).toBe("The size estimate no longer applies; count again.");
    expect(list.textContent).not.toContain("Nothing else depends on the earlier query.");
  });

  it("prints the string the researcher stated for an export, and isolates dates, names and strings left to right in Arabic", async () => {
    setUp({ ...PROVIDERS, staged: true, stagedQuery: "TITLE-ABS-KEY(uav AND weed)" });
    render(<DiscoveryPlan locale="ar" />);
    fireEvent.click(await screen.findByRole("button", { name: "غيّر البحث" }));
    await waitFor(() => expect(document.querySelector("[data-workbench]")).not.toBeNull());
    fireEvent.click(screen.getAllByRole("button", { name: "أزل المفهوم" })[1]);
    fireEvent.click(await screen.findByRole("button", { name: "سجّل هذا التعديل" }));
    const line = await waitFor(() => {
      const el = document.querySelector("[data-conseq='export']") as HTMLElement | null;
      if (!el) throw new Error("no line yet");
      return el;
    });
    expect([...line.querySelectorAll("bdi[dir='ltr']")].map((x) => x.textContent)).toEqual(["Scopus", "2026-11-01", "TITLE-ABS-KEY(uav AND weed)"]);
    expect(line.textContent).toBe("Scopus، ١٢٠ سجلات، أُودع في 2026-11-01. بُحث هناك بـ: TITLE-ABS-KEY(uav AND weed). يبقى كما هو. إن غيّرت ذلك البحث أيضًا فصدّر من جديد واستبدل الملف.");
    // The databases in the counts summary: the language's own separator, each name isolated.
    const counts = document.querySelector("[data-amend-counts]") as HTMLElement;
    expect(counts.textContent).toContain("OpenAlex ١٦٦، Semantic Scholar");
    expect([...counts.querySelectorAll("bdi[dir='ltr']")].map((x) => x.textContent)).toContain("Semantic Scholar");
  });

  it("refuses with the engine's words when the protocol changed elsewhere, reads Plan again and writes nothing", async () => {
    const { engine } = setUp(PROVIDERS);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const box = await openConfirmation();
    fireEvent.change(within(box).getByLabelText("Why are you changing the search?"), { target: { value: "One concept is enough." } });
    // Another tab amended the protocol.
    const plan = engine.handle("GET", "/api/v1/discovery/plan", null).body as { protocol_fingerprint: string };
    engine.handle("POST", AMEND, { query_key: "main", concepts: [{ concept: "weed", synonyms: [] }], reason: "elsewhere", protocol_fingerprint: plan.protocol_fingerprint, dry_run: false });
    fireEvent.click(within(box).getByRole("button", { name: "Record this amendment" }));
    const refusal = await waitFor(() => {
      const el = document.querySelector("[data-amend-refusal='WORKBENCH_PROTOCOL_CHANGED']") as HTMLElement | null;
      if (!el) throw new Error("no refusal yet");
      return el;
    });
    expect(refusal.textContent).toContain("The protocol changed since this page was read.");
    expect(confirmation()).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(refusal));
    // Plan reads the protocol again: its line and the new fingerprint.
    await waitFor(() => expect(document.querySelector("[data-plan-changed]")).not.toBeNull());
    await waitFor(() => expect(document.querySelector("[data-in-protocol]")?.textContent).toContain("sha256:01"));
    expect(engine.amendments).toHaveLength(1); // only the other tab's
  });

  it("a running job refuses Record with its words and the way to follow it; nothing is written", async () => {
    const { engine } = setUp({ ...PROVIDERS, activeJob: true });
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const box = await openConfirmation();
    fireEvent.change(within(box).getByLabelText("Why are you changing the search?"), { target: { value: "One concept is enough." } });
    fireEvent.click(within(box).getByRole("button", { name: "Record this amendment" }));
    const refusal = await within(box).findByText(/so the search cannot be amended now/);
    expect(refusal.closest("[data-amend-refusal]")).toHaveAttribute("data-amend-refusal", "DISCOVERY_JOB_ACTIVE");
    expect(within(box).getByRole("link", { name: "Follow the running job" })).toHaveAttribute("href", "/en/discovery/harvest/");
    await waitFor(() => expect(document.activeElement).toBe(within(box).getByRole("heading", { name: "What this amendment changes" })));
    expect(engine.amendments).toHaveLength(0);
  });

  it("a refused dry run shows the engine's words instead of reading forever, and Record stays disabled", async () => {
    setUp({
      ...PROVIDERS,
      refuseOnce: {
        [`POST ${AMEND}`]: { status: 422, body: { detail: { code: "PROTOCOL_AMENDMENT_REFUSED", message: "the change reaches eligibility", details: { reason: "outside_search" } } } },
      },
    });
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    fireEvent.click(screen.getAllByRole("button", { name: "Remove concept" })[1]);
    fireEvent.click(await screen.findByRole("button", { name: "Record this amendment" }));
    const box = await waitFor(() => {
      const el = confirmation();
      if (!el?.querySelector("[data-amend-refusal]")) throw new Error("no refusal yet");
      return el;
    });
    expect(box.textContent).toContain("The engine only amends the search here, and this change reaches something else. Nothing was changed.");
    expect(box.textContent).not.toContain("Reading what this amendment changes");
    expect(within(box).getByRole("button", { name: "Record this amendment" })).toBeDisabled();
  });

  it("a console that cannot be reached on Record says so and writes nothing", async () => {
    const { engine } = setUp(PROVIDERS);
    const reach = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) =>
      String(url).includes("/workbench/amend") && init?.body && !JSON.parse(String(init.body)).dry_run ? Promise.reject(new TypeError("Failed to fetch")) : reach(url, init),
    ));
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const box = await openConfirmation();
    fireEvent.change(within(box).getByLabelText("Why are you changing the search?"), { target: { value: "One concept is enough." } });
    fireEvent.click(within(box).getByRole("button", { name: "Record this amendment" }));
    await waitFor(() => expect(box.querySelector("[data-amend-refusal='CONSOLE_UNREACHABLE']")).not.toBeNull());
    expect(engine.amendments).toHaveLength(0);
  });

  it("after the corpus is accepted: the workbench still opens and counts, Record is absent, and the way on is a new workspace", async () => {
    setUp({ ...PROVIDERS, accepted: true, search: "?console=http%3A%2F%2F127.0.0.1%3A8765" });
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    expect(screen.queryByRole("button", { name: "Record this amendment" })).toBeNull();
    expect(screen.getByText(/The corpus is accepted, so the search is not amended here\./)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a new workspace from this protocol" }).getAttribute("href")).toBe(
      "/en/inception/import/?console=http%3A%2F%2F127.0.0.1%3A8765",
    );
    expect(screen.getByRole("button", { name: "Count" })).not.toBeDisabled();
  });

  it("the anchor other screens link to opens the section", async () => {
    setUp(PROVIDERS);
    vi.stubGlobal("location", { ...window.location, search: "", hash: "#change-search", assign: vi.fn() });
    render(<DiscoveryPlan locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-workbench]")).not.toBeNull());
    expect(screen.getByRole("button", { name: "Change the search" })).toHaveAttribute("aria-expanded", "true");
  });

  it("offers the harvest measure for a comparison on Plan", async () => {
    setUp(PROVIDERS);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    fireEvent.click(document.querySelector("[data-section='comparison'] summary") as HTMLElement);
    const ris = "TY  - JOUR\nTI  - Weed detection on edge devices\nDO  - 10.9/a\nER  - \n";
    const file = new File([ris], "scopus.ris");
    Object.defineProperty(file, "arrayBuffer", { value: async () => new TextEncoder().encode(ris).buffer });
    fireEvent.change(screen.getByLabelText("RIS or NBIB file"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Database it came from"), { target: { value: "Scopus" } });
    fireEvent.click(document.querySelector("[data-cmp-stage]") as HTMLElement);
    const select = (await screen.findByLabelText("Measure")) as HTMLSelectElement;
    expect([...select.options].map((o) => o.value)).toEqual(["words", "openalex", "harvest"]);
  });
});
