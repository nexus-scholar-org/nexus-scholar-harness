import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionCriteria } from "@/components/inception-criteria";
import { PROPOSALS_COPY } from "@/lib/proposals-copy";
import { completeDraft, proofId, SESSION } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/**
 * `docs/ux/shared/final/01-proposals.md` "Acceptance tests / Vitest" (M10b B1):
 * the proposal card and the per-step list on Concepts and criteria, against the
 * stateful fake. The engine decides; the card sends one POST per click.
 */

afterEach(() => vi.unstubAllGlobals());

const PROPOSALS = `/api/v1/inception/drafts/${SESSION}/proposals`;
const decided = (extra: Record<string, unknown> = {}) => completeDraft({ criteria_decisions: { [proofId()]: true }, title: "UAV weed detection", ...extra });
const UAV = { field: "concepts", value: { concept: "UAV", synonyms: [] }, why: "Your title and questions use UAV, but no concept or synonym does.", evidence: [{ kind: "check", check_id: "CONCEPT_TERM_MISSING" }, { kind: "doi", doi: "10.1234/uav.1" }] };

const posts = (engine: ReturnType<typeof setUp>["engine"]) => engine.calls.filter((c) => c.method === "POST" && c.path.startsWith(`${PROPOSALS}/`));
const card = async (id: string) => (await screen.findByText((_, el) => el?.getAttribute("data-proposal") === id && el.tagName === "LI")) as HTMLElement;
const list = () => document.querySelector("[data-proposals='criteria']") as HTMLElement;
const actions = () => list().querySelectorAll("[data-apply],[data-edit],[data-reject],[data-restore],[data-apply-edit]");

describe("inception proposals (01-proposals)", () => {
  it("a proposal card is never pre-ticked or pre-applied", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    expect(li).toHaveAttribute("data-status", "open");
    expect(within(li).queryByText("Applied by you")).toBeNull();
    expect(within(li).queryAllByRole("checkbox")).toHaveLength(0);
    expect(within(li).getByText("Suggestion · not yet yours", { exact: false })).toBeInTheDocument();
    expect(document.activeElement && li.contains(document.activeElement)).toBe(false);
    expect(posts(engine)).toEqual([]);
    expect(engine.calls.filter((c) => c.method === "PUT")).toEqual([]);
  });

  it("Apply sends one POST and shows the new value", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    expect(li.querySelector("[data-what]")?.textContent).toBe("Add UAV to Concepts");
    fireEvent.click(within(li).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(posts(engine)).toHaveLength(1));
    const [apply] = posts(engine);
    expect(apply.path).toBe(`${PROPOSALS}/${made.proposal_id}/apply`);
    expect(Object.keys(apply.body ?? {})).toEqual(["base_updated_at"]);
    // The field shows the value; the card is the decided row.
    await waitFor(() => expect(screen.getByDisplayValue("UAV")).toBeInTheDocument());
    const row = list().querySelector(`[data-proposal='${made.proposal_id}']`) as HTMLElement;
    expect(row).toHaveAttribute("data-status", "applied");
    expect(within(row).getByText("Applied by you")).toBeInTheDocument();
    expect(screen.getByText("Applied: Concepts")).toBeInTheDocument();
  });

  it("Edit then Apply sends the researcher's value as apply-edited", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    fireEvent.click(within(li).getByRole("button", { name: "Edit" }));
    const editor = within(li).getByLabelText("Concept name");
    await waitFor(() => expect(editor).toHaveFocus());
    fireEvent.change(editor, { target: { value: "unmanned aerial vehicle" } });
    fireEvent.click(within(li).getByRole("button", { name: "Apply my edit" }));
    await waitFor(() => expect(posts(engine)).toHaveLength(1));
    expect(posts(engine)[0].path).toBe(`${PROPOSALS}/${made.proposal_id}/apply-edited`);
    expect(posts(engine)[0].body).toMatchObject({ value: { concept: "unmanned aerial vehicle", synonyms: [] } });
    await waitFor(() => expect(list().querySelector(`[data-proposal='${made.proposal_id}']`)).toHaveAttribute("data-status", "applied_edited"));
    expect(within(list()).getByText("Applied after your edit")).toBeInTheDocument();
  });

  it("Reject changes no field; Restore returns it to open", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    const before = JSON.stringify(engine.drafts.get(SESSION)!.draft);
    const at = engine.drafts.get(SESSION)!.updated_at;
    render(<InceptionCriteria locale="en" />);
    fireEvent.click(within(await card(String(made.proposal_id))).getByRole("button", { name: "Reject" }));
    await waitFor(() => expect(list().querySelector(`[data-proposal='${made.proposal_id}']`)).toHaveAttribute("data-status", "rejected"));
    expect(JSON.stringify(engine.drafts.get(SESSION)!.draft)).toBe(before);
    expect(engine.drafts.get(SESSION)!.updated_at).toBe(at);
    expect(screen.queryByDisplayValue("UAV")).toBeNull();
    const row = list().querySelector(`[data-proposal='${made.proposal_id}']`) as HTMLElement;
    expect(within(row).getByText("Rejected")).toBeInTheDocument();
    fireEvent.click(within(row).getByRole("button", { name: "Restore" }));
    await waitFor(() => expect(list().querySelector(`[data-proposal='${made.proposal_id}']`)).toHaveAttribute("data-status", "open"));
    expect(posts(engine).map((c) => c.path.split("/").at(-1))).toEqual(["reject", "restore"]);
  });

  it("a stale proposal shows Was and Now, no Apply and no Edit", async () => {
    // Derived by the engine: the target changed since the proposal was made.
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal({ ...UAV, field: "concepts", baseValue: [{ concept: "weeds", synonyms: [] }] });
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    expect(li).toHaveAttribute("data-status", "stale");
    expect(within(li).getByText("Out of date")).toBeInTheDocument();
    expect(li.querySelector("[data-was]")?.textContent).toBe("Was: weeds");
    expect(li.querySelector("[data-now]")?.textContent).toBe("Now: weed detection");
    expect(within(li).getByText("This field changed after the suggestion was made, so it is not applied.")).toBeInTheDocument();
    expect(within(li).queryByRole("button", { name: "Apply" })).toBeNull();
    expect(within(li).queryByRole("button", { name: "Edit" })).toBeNull();
    expect(within(li).getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    expect(document.querySelector("[data-out-of-date]")?.textContent).toContain("1 out of date");

    // Answered by the engine on Apply: the card re-reads and becomes stale.
    vi.unstubAllGlobals();
    const second = setUp({ draft: decided() });
    const open = second.engine.addProposal(UAV);
    cleanup();
    render(<InceptionCriteria locale="en" />);
    const li2 = await card(String(open.proposal_id));
    // Another tab changes the concepts before the click.
    const record = second.engine.drafts.get(SESSION)!;
    record.draft = { ...(record.draft as object), concepts: [{ concept: "crop rows", synonyms: [] }] };
    second.engine.refuseNext(`POST ${PROPOSALS}/${open.proposal_id}/apply`, { status: 409, body: { detail: { code: "PROPOSAL_STALE", message: "changed", details: { base: "weed detection", current: "crop rows" } } } });
    fireEvent.click(within(li2).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(list().querySelector(`[data-proposal='${open.proposal_id}']`)).toHaveAttribute("data-status", "stale"));
    expect(within(list()).queryByRole("button", { name: "Apply" })).toBeNull();
    expect(screen.getByText("Out of date: Concepts")).toBeInTheDocument();
  });

  it("PROPOSAL_NOT_OPEN re-reads the card and does not alarm", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    // Rejected meanwhile in another tab.
    (engine.drafts.get(SESSION)!.proposals as Record<string, unknown>[])[0].status = "rejected";
    fireEvent.click(within(li).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(list().querySelector(`[data-proposal='${made.proposal_id}']`)).toHaveAttribute("data-status", "rejected"));
    expect(screen.getByText("Already rejected.")).toBeInTheDocument();
    expect(within(list()).queryByRole("alert")).toBeNull();
  });

  it("DRAFT_INVALID on Apply keeps the card open with the first error", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    engine.refuseNext(`POST ${PROPOSALS}/${made.proposal_id}/apply`, { status: 422, body: { detail: { code: "DRAFT_INVALID", message: "invalid", details: { errors: ["concepts: at most 12 concepts", "concepts.13: too long"] } } } });
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    fireEvent.click(within(li).getByRole("button", { name: "Apply" }));
    expect(await within(li).findByRole("alert")).toHaveTextContent("The draft cannot take this value: concepts: at most 12 concepts");
    expect(li).toHaveAttribute("data-status", "open");
    expect(within(li).getByRole("button", { name: "Edit" })).toBeEnabled();
    expect(within(li).getByText("concepts.13: too long")).toBeInTheDocument();
  });

  it("DRAFT_CONFLICT and DRAFT_EMITTED make the list read-only", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    engine.refuseNext(`POST ${PROPOSALS}/${made.proposal_id}/apply`, { status: 409, body: { detail: { code: "DRAFT_CONFLICT", message: "the draft changed since it was read" } } });
    render(<InceptionCriteria locale="en" />);
    fireEvent.click(within(await card(String(made.proposal_id))).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(actions()).toHaveLength(0));
    expect(within(list()).getByText("This draft cannot be changed from this page, so the suggestions are read-only.")).toBeInTheDocument();

    // An emitted draft is read-only from the start: decisions shown, no button.
    vi.unstubAllGlobals();
    cleanup();
    const emitted = setUp({ draft: decided(), emitted: { slug: "uav", path: "C:\\w\\uav", protocol_fingerprint: "sha256:" + "ab".repeat(32), replaced: false } });
    const applied = emitted.engine.addProposal({ ...UAV, status: "applied" });
    emitted.engine.addProposal({ ...UAV, value: { concept: "drone", synonyms: [] } });
    render(<InceptionCriteria locale="en" />);
    await waitFor(() => expect(document.querySelector(`[data-proposal='${applied.proposal_id}']`)).not.toBeNull());
    expect(actions()).toHaveLength(0);
  });

  it("the stepper badge and the list heading show the engine's count, never one the browser derived", async () => {
    const { engine } = setUp({ draft: decided() });
    engine.addProposal(UAV);
    // The engine's counts disagree with the one card on purpose.
    const real = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        const response = await real(url, init);
        if (!String(url).includes("/proposals") || (init?.method ?? "GET") !== "GET") return response;
        const body = await response.json();
        body.by_step.criteria = { open: 7, stale: 2 };
        return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
      }),
    );
    render(<InceptionCriteria locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-proposals-heading]")?.textContent).toContain("Suggestions for this step · 7"));
    expect(document.querySelector("[data-out-of-date]")?.textContent).toContain("2 out of date");
    await waitFor(() => expect(document.querySelector("[data-step-suggestions='criteria']")?.textContent).toContain("7 suggestions"));
    expect(document.querySelectorAll("[data-proposals='criteria'] li[data-proposal]")).toHaveLength(1);
  });

  it('no card is rendered for an empty step, and the "Decided" disclosure lists decided ones', async () => {
    const { engine } = setUp({ draft: decided() });
    render(<InceptionCriteria locale="en" />);
    await waitFor(() => expect(engine.calls.some((c) => c.method === "GET" && c.path === PROPOSALS && c.search === "step=criteria")).toBe(true));
    await screen.findAllByRole("button", { name: "Accept" });
    expect(document.querySelector("[data-proposals]")).toBeNull();
    expect(screen.queryByText("No suggestions are waiting.")).toBeNull();

    vi.unstubAllGlobals();
    cleanup();
    const second = setUp({ draft: decided() });
    const applied = second.engine.addProposal({ ...UAV, status: "applied" });
    second.engine.addProposal({ source: "engine:pool_synonym", field: "concepts[weed detection].synonyms", value: "weeding", status: "applied" });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("No suggestions are waiting.")).toBeInTheDocument();
    const disclosure = document.querySelector("[data-decided]") as HTMLDetailsElement;
    expect(disclosure.open).toBe(false);
    expect(disclosure.querySelector("summary")?.textContent).toBe("Decided (2)");
    expect(within(disclosure).getByText("A term from the sampled papers")).toBeInTheDocument();
    expect(disclosure.querySelector(`[data-proposal='${applied.proposal_id}']`)).not.toBeNull();
  });

  it("offline disables every button and keeps the cards", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    engine.addProposal({ ...UAV, value: { concept: "drone", synonyms: [] } });
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    const real = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (String(url).includes("/proposals/")) throw new TypeError("Failed to fetch");
        return real(url, init);
      }),
    );
    fireEvent.click(within(li).getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(document.querySelector("[data-proposals-offline]")).not.toBeNull());
    expect(document.querySelector("[data-proposals-offline]")?.textContent).toContain("needs the engine on this computer");
    expect(document.querySelector("[data-proposals-offline]")?.textContent).toMatch(/As of \d{4}-\d{2}-\d{2}/);
    const buttons = [...actions()];
    expect(buttons.length).toBe(6);
    expect(buttons.every((b) => (b as HTMLButtonElement).disabled)).toBe(true);
    expect(list().querySelectorAll("li[data-proposal]")).toHaveLength(2);
  });

  it("RTL: values are dir=auto and DOIs and ids are dir=ltr", async () => {
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal(UAV);
    render(<InceptionCriteria locale="ar" />);
    const li = await card(String(made.proposal_id));
    expect(li.querySelector("[data-value]")).toHaveAttribute("dir", "auto");
    expect(within(li).getByText("CONCEPT_TERM_MISSING", { selector: "[data-proposal-source] bdi" })).toHaveAttribute("dir", "ltr");
    fireEvent.click(li.querySelector("[data-evidence-toggle]") as HTMLElement);
    expect(within(li).getByText("10.1234/uav.1")).toHaveAttribute("dir", "ltr");
    expect(within(li).getByRole("button", { name: "طبّق" })).toBeInTheDocument();
  });

  it("copy: every proposals.* key exists in en and fr/ar fall back", () => {
    const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const [key, en] of Object.entries(PROPOSALS_COPY.en)) {
      for (const locale of ["fr", "ar"] as const) {
        const text = PROPOSALS_COPY[locale][key as keyof typeof PROPOSALS_COPY.en];
        expect(text, `${locale} ${key}`).toBeTruthy();
        expect(holes(text), `${locale} ${key}`).toEqual(holes(en));
      }
    }
    for (const key of ["proposals.title", "proposals.what.add", "proposals.stale.was", "proposals.notRecorded", "proposals.source.engine.anchor_seed"]) {
      expect(PROPOSALS_COPY.en).toHaveProperty([key]);
    }
    // The N9 guard on the new components: no literal accessible name.
    for (const file of ["components/inception-assist.tsx", "components/assist-anchor.tsx", "components/assist-context.tsx"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });

  it("ticking a pool synonym sends accepted_from with the save", async () => {
    const { engine } = setUp({ draft: decided({ concepts: [{ concept: "weed detection", synonyms: [] }] }), offered: (entry) => entry.value !== "real-time" });
    engine.handle("POST", `/api/v1/inception/drafts/${SESSION}/recon/probe`, { refresh: false, semantic: false });
    render(<InceptionCriteria locale="en" />);
    const group = await screen.findByRole("group", { name: "Terms from your first search for weed detection" });
    fireEvent.click(within(group).getByRole("checkbox", { name: "embedded hardware · 8 papers" }));
    fireEvent.click(within(group).getByRole("checkbox", { name: "real-time · 8 papers" }));
    const before = engine.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    await waitFor(() => expect(engine.calls.some((c) => c.method === "PUT")).toBe(true));
    const put = engine.calls.find((c) => c.method === "PUT")!;
    expect(put.body?.accepted_from).toEqual([
      { mechanism: "pool_synonym", field: "concepts[weed detection].synonyms", value: "embedded hardware" },
      { mechanism: "pool_synonym", field: "concepts[weed detection].synonyms", value: "real-time" },
    ]);
    expect(put.body).toHaveProperty("draft");
    // No other request carries the record.
    expect(engine.calls.slice(before).filter((c) => c.method === "POST" && c.path.includes("/proposals"))).toEqual([]);
    // `real-time` was not offered: the quiet line, and the field stays saved.
    expect(await screen.findByText("This choice was saved; its source could not be recorded.")).toBeInTheDocument();
    const saved = engine.drafts.get(SESSION)!.draft as { concepts: { synonyms: string[] }[] };
    expect(saved.concepts[0].synonyms).toEqual(["embedded hardware", "real-time"]);
  });

  it("agent source is not rendered in M10b", async () => {
    // The engine refuses `agent:*` as a proposal source (PROPOSAL_SOURCE_REFUSED) until M10c; a stub
    // that sends one anyway gets the generic label, never an assistant's.
    const { engine } = setUp({ draft: decided() });
    const made = engine.addProposal({ ...UAV, source: "agent:claude" });
    render(<InceptionCriteria locale="en" />);
    const li = await card(String(made.proposal_id));
    expect(within(li).getByText("Suggested by the engine")).toBeInTheDocument();
    expect(within(li).queryByText("Suggested by an assistant")).toBeNull();
  });
});
