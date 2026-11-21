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
const posts = (engine: ReturnType<typeof setUp>["engine"], path: string) => engine.calls.filter((c) => c.method === "POST" && c.path === path);

async function openSearch() {
  const button = await screen.findByRole("button", { name: "Change the search" });
  expect(button).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(button);
  await waitFor(() => expect(document.querySelector("[data-workbench]")).not.toBeNull());
}

describe("discovery.plan change the search", () => {
  it("is closed until asked; then opens the workbench on the protocol's query, counts nothing on open, and keeps the protocol read only", async () => {
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"] });
    render(<DiscoveryPlan locale="en" />);
    expect(await screen.findByRole("button", { name: "Change the search" })).toBeInTheDocument();
    expect(document.querySelector("[data-workbench]")).toBeNull();
    await openSearch();
    const protocol = document.querySelector("[data-in-protocol]") as HTMLElement;
    expect(within(protocol).getByText("In the protocol")).toBeInTheDocument();
    expect(protocol.textContent).toContain("weed detection OR weed segmentation");
    expect((screen.getByLabelText("Concept 1") as HTMLInputElement).value).toBe("weed detection");
    expect(screen.getByText("Search: main")).toBeInTheDocument();
    expect(posts(engine, "/api/v1/discovery/workbench/counts").filter((c) => !(c.body as { dry_run?: boolean }).dry_run)).toHaveLength(0);
    expect(screen.queryByRole("button", { name: "Use this version" })).toBeNull();
  });

  it("Record this amendment waits for a change, asks one sentence, lists what it changes, and sends concepts, reason and the fingerprint read", async () => {
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"] });
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    const open = screen.getByRole("button", { name: "Record this amendment" });
    expect(open).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: "Select weed detection to merge" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select edge device to merge" }));
    fireEvent.click(screen.getByRole("button", { name: "Merge into one" }));
    fireEvent.click(screen.getByRole("button", { name: "Merge" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Record this amendment" })).not.toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: "Record this amendment" }));
    const form = (await screen.findByText("What this amendment changes")).closest("form") as HTMLElement;
    await waitFor(() => expect(form.querySelector("[data-consequences]")).not.toBeNull());
    expect(within(form).getByText("Before: OpenAlex 166, Semantic Scholar not counted")).toBeInTheDocument();
    // The one brand button while the confirmation is open.
    expect(document.querySelectorAll("[data-plan-search] button[data-variant='primary']")).toHaveLength(1);
    fireEvent.click(within(form).getByRole("button", { name: "Record this amendment" }));
    expect(await within(form).findByText("Write one sentence.")).toBeInTheDocument();
    expect(posts(engine, AMEND).filter((c) => !(c.body as { dry_run?: boolean }).dry_run)).toHaveLength(0);
    fireEvent.change(within(form).getByLabelText("Why are you changing the search?"), { target: { value: "Edge devices and weed detection are one idea here." } });
    fireEvent.click(within(form).getByRole("button", { name: "Record this amendment" }));
    expect(await screen.findByText(/Amendment recorded\. The search in the protocol has changed\./)).toBeInTheDocument();
    const real = posts(engine, AMEND).filter((c) => !(c.body as { dry_run?: boolean }).dry_run);
    expect(real).toHaveLength(1);
    const body = real[0].body as Record<string, unknown>;
    expect(Object.keys(body).sort()).toEqual(["concepts", "dry_run", "protocol_fingerprint", "query_key", "reason"]);
    expect(body.reason).toBe("Edge devices and weed detection are one idea here.");
    expect(body.concepts).toEqual([{ concept: "weed detection", synonyms: ["weed segmentation", "edge device", "embedded"] }]);
    expect(engine.amendments).toHaveLength(1);
    // Plan is read again: the new fingerprint is shown.
    await waitFor(() => expect(document.querySelector("[data-plan-strings]")?.textContent).toContain("sha256:01"));
  });

  it("names each earlier run, each staged export and the recall check in the engine's words", async () => {
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"], staged: true });
    expect(engine.handle("POST", "/api/v1/discovery/recall", { seeds: [{ id: "10.1234/a", kind: "doi", source: "you" }] }).status).toBe(202);
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    fireEvent.click(screen.getAllByRole("button", { name: "Remove concept" })[1]);
    fireEvent.click(await screen.findByRole("button", { name: "Record this amendment" }));
    const list = await waitFor(() => {
      const el = document.querySelector("[data-consequences]") as HTMLElement | null;
      if (!el) throw new Error("no list yet");
      return el;
    });
    expect(list.querySelector("[data-conseq='export']")?.textContent).toBe(
      "Scopus, 120 records, staged 2026-11-01. Searched there with a string you did not state. It stays as it is. If you change that search too, export again and replace the file.",
    );
    expect(list.querySelector("[data-conseq='recall'] bdi[dir='ltr']")?.textContent).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/);
  });

  it("prints the string the researcher stated for an export, isolated as code, in the spec's order", async () => {
    setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"], staged: true, stagedQuery: "TITLE-ABS-KEY(uav AND weed)" });
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
    // The date and the stated string are isolated left to right (I18N.md); the sentence is not.
    expect([...line.querySelectorAll("bdi[dir='ltr']")].map((x) => x.textContent)).toEqual(["2026-11-01", "TITLE-ABS-KEY(uav AND weed)"]);
    expect(line.textContent).toBe("Scopus، ١٢٠ سجلات، أُودع في 2026-11-01. بُحث هناك بـ: TITLE-ABS-KEY(uav AND weed). يبقى كما هو. إن غيّرت ذلك البحث أيضًا فصدّر من جديد واستبدل الملف.");
    // The databases in the counts summary are joined with the language's own separator.
    expect(document.querySelector("[data-amend-counts]")?.textContent).toContain("OpenAlex ١٦٦، Semantic Scholar");
  });

  it("refuses with the engine's words when a job runs or the protocol changed elsewhere, and writes nothing", async () => {
    const { engine } = setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"] });
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    fireEvent.click(screen.getAllByRole("button", { name: "Remove concept" })[1]);
    fireEvent.click(await screen.findByRole("button", { name: "Record this amendment" }));
    const form = (await screen.findByText("What this amendment changes")).closest("form") as HTMLElement;
    await waitFor(() => expect(form.querySelector("[data-consequences]")).not.toBeNull());
    fireEvent.change(within(form).getByLabelText("Why are you changing the search?"), { target: { value: "One concept is enough." } });
    // The page's fingerprint no longer matches: another tab amended the protocol.
    const plan = engine.handle("GET", "/api/v1/discovery/plan", null).body as { protocol_fingerprint: string; search: { concepts: unknown[] } };
    engine.handle("POST", AMEND, { query_key: "main", concepts: [{ concept: "weed", synonyms: [] }], reason: "elsewhere", protocol_fingerprint: plan.protocol_fingerprint, dry_run: false });
    fireEvent.click(within(form).getByRole("button", { name: "Record this amendment" }));
    expect(await screen.findByText("The protocol changed since this page was read.")).toBeInTheDocument();
    expect(document.querySelector("[data-amend-refusal='WORKBENCH_PROTOCOL_CHANGED']")).not.toBeNull();
    expect(engine.amendments).toHaveLength(1); // only the other tab's
  });

  it("after the corpus is accepted: the workbench still opens and counts, Record is absent, and the way on is a new workspace", async () => {
    setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"], accepted: true });
    render(<DiscoveryPlan locale="en" />);
    await openSearch();
    expect(screen.queryByRole("button", { name: "Record this amendment" })).toBeNull();
    expect(screen.getByText(/The corpus is accepted, so the search is not amended here\./)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a new workspace from this protocol" })).toHaveAttribute("href", "/en/inception/import/");
    expect(screen.getByRole("button", { name: "Count" })).not.toBeDisabled();
  });

  it("offers the harvest measure for a comparison on Plan", async () => {
    setUp({ protocolProviders: ["openalex", "semanticscholar", "arxiv"] });
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
