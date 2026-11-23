import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionCriteria } from "@/components/inception-criteria";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/**
 * Spec 05 (M4b; INC-22): every criterion verbatim with its source; a generated
 * one waits for an explicit Accept (default no); typed ones are accepted unless
 * rejected; decisions are saved in `criteria_decisions` by the engine's ids.
 */

afterEach(() => vi.unstubAllGlobals());

const PROOF = "Reports the gold-standard proof — mIoU and FPS on a public benchmark";

describe("inception.criteria", () => {
  it("shows each criterion verbatim with its source; the generated one waits for you", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    const proof = (await screen.findByText(PROOF)).closest("li")!;
    expect(proof).toHaveAttribute("data-status", "undecided");
    expect(within(proof).getByText("Written by the wizard from your proof answer")).toBeInTheDocument();
    expect(within(proof).getByText("Waiting for you")).toBeInTheDocument();
    // M10d (03-guidance I-C13): the per-row sentence is removed; the source and "Waiting for you" say it.
    expect(within(proof).queryByText("Written by the wizard: not in the protocol unless you accept it.")).toBeNull();
    expect(within(proof).getByRole("button", { name: "Accept" })).toHaveAttribute("aria-pressed", "false");
    // H-run-small-fixes (finding 2): an out-of-scope item waits for Accept too.
    const typed = screen.getByText("closed-source models", { selector: "[data-verbatim]" }).closest("li")!;
    expect(typed).toHaveAttribute("data-status", "undecided");
    expect(within(typed).getByText("Your out-of-scope answer")).toBeInTheDocument();
    expect(screen.getByText("2 still need you.")).toBeInTheDocument();
  });

  it("says the columns are filled on the Charting step, and labels the verification checks as parked", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("These columns are filled on the Charting step.")).toBeInTheDocument();
    expect(screen.queryByText(/Parked: the Matrix phase/)).toBeNull();
    expect(screen.getByText(/Advisory: Phase 4 checks are parked/)).toBeInTheDocument();
    expect(screen.getByText("Ticked columns are saved in the protocol. With none ticked, the protocol has no matrix columns.")).toBeInTheDocument();
  });

  it("offers the engine's suggested concepts as drafts", async () => {
    setUp({ draft: completeDraft({ concepts: [] }) });
    render(<InceptionCriteria locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Add weed" }));
    expect(screen.getByLabelText("Concept 1")).toHaveValue("weed");
  });

  it("shows source labels in Arabic, and keeps the criterion text as the engine wrote it", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="ar" />);
    const proof = (await screen.findByText(PROOF)).closest("li")!;
    expect(within(proof).getByText("كتبه المعالج من إجابتك عن الدليل")).toBeInTheDocument();
  });

  it("shows each term's count in the pool and adds a pool term only on Apply; Use this version saves it with its source (M4d, M11a D5)", async () => {
    const { engine } = setUp({ draft: completeDraft({ concepts: [{ concept: "weed detection", synonyms: ["quantum"] }] }) });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("in 8 of 14")).toBeInTheDocument();
    const quantum = document.querySelector("[data-chip='quantum']") as HTMLElement;
    expect(within(quantum).getByText("not in the pool")).toBeInTheDocument();
    const weed = document.querySelector("[data-chip='weed detection']") as HTMLElement;
    expect(within(weed).getByText("in 8 of 14")).toBeInTheDocument();
    const list = (await screen.findByText("Suggested by your first search · not yet yours")).closest("[data-suggestions]") as HTMLElement;
    expect([...list.querySelectorAll("[data-suggestion-row]")].map((r) => r.getAttribute("data-suggestion-row"))).toEqual(["embedded hardware", "real-time"]);
    const puts = () => engine.calls.filter((c) => c.method === "PUT");
    fireEvent.click(within(list).getAllByRole("button", { name: "Apply" })[0]);
    expect(puts()).toHaveLength(0);
    expect(document.querySelector("[data-chip='embedded hardware']")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Use this version" }));
    await waitFor(() => expect(puts()).toHaveLength(1));
    const put = puts()[0].body as { draft: { concepts: unknown }; accepted_from: unknown };
    expect(put.draft.concepts).toEqual([{ concept: "weed detection", synonyms: ["quantum", "embedded hardware"] }]);
    expect(put.accepted_from).toEqual([{ mechanism: "pool_synonym", field: "concepts[weed detection].synonyms", value: "embedded hardware" }]);
  });

  it("with no pool shows no counts, no suggestions, a link to Explore, and never reads the concepts (M4d)", async () => {
    const { engine } = setUp({ draft: completeDraft() });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByRole("link", { name: "Go to Explore" })).toHaveAttribute("href", `/en/inception/explore/?draft=${SESSION}`);
    expect(document.querySelector("[data-in-pool]")).toBeNull();
    expect(engine.calls.some((c) => c.path.endsWith("/recon/concepts"))).toBe(false);
  });

  it("notes an earlier scope when the engine reports one (M4d)", async () => {
    const { engine } = setUp({ draft: completeDraft() });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    const record = engine.drafts.get(SESSION)!;
    engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), start_year: 2015 }, base_updated_at: record.updated_at });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText(/The pool was searched for an earlier scope; counts may not match./)).toBeInTheDocument();
  });
});
