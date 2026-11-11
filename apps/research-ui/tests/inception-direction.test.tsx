import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionDirection } from "@/components/inception-direction";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import type { ReconOptions } from "./fixtures/recon-engine";
import { setUp } from "./inception-helpers";

/** Spec 03 Direction (M4d) over the stateful fake of the recon routes. */

afterEach(() => vi.unstubAllGlobals());

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;
type Engine = ReturnType<typeof setUp>["engine"];

function prepare(recon: ReconOptions = {}, draft: Record<string, unknown> = completeDraft(), probe = true) {
  const set = setUp({ draft, recon });
  if (probe) set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  return set;
}

function bind(engine: Engine, body: Record<string, unknown>) {
  const record = engine.drafts.get(SESSION)!;
  return engine.handle("POST", `${RECON}/bind`, { accept_thin_pool: false, ...body, base_updated_at: record.updated_at });
}

const sentTo = (engine: Engine, method: string, suffix: string) => engine.calls.filter((c) => c.method === method && c.path === `${RECON}${suffix}`);

async function cards() {
  return within(await screen.findByRole("radiogroup")).getAllByRole("radio");
}

describe("inception.direction", () => {
  it("checks no card on load, lists the engine's order and keeps Pursue disabled with its reason", async () => {
    prepare();
    render(<InceptionDirection locale="en" />);
    const radios = await cards();
    expect(radios.map((r) => r.closest("[data-direction]")?.getAttribute("data-direction"))).toEqual(["weed detection", "weed segmentation", "embedded hardware"]);
    expect(radios.every((r) => !(r as HTMLInputElement).checked)).toBe(true);
    const pursue = screen.getByRole("button", { name: "Pursue a direction" });
    expect(pursue).toBeDisabled();
    expect(pursue).toHaveAttribute("aria-describedby", "pursue-choose");
    expect(screen.getByText("Choose a direction, or write your own.")).toBeInTheDocument();
    expect(screen.getByText(/which is evidence, not a recommendation/)).toBeInTheDocument();
    expect(document.querySelector("[data-seeds]")).toBeNull();
  });

  it("states the occurrence from observed_in and n_docs, never the evidence hits", async () => {
    prepare();
    render(<InceptionDirection locale="en" />);
    await cards();
    const card = document.querySelector("[data-direction='weed detection']") as HTMLElement;
    expect(within(card).getByText("Term occurs in 8 of 14 titles or abstracts")).toBeInTheDocument();
    expect(within(card).getByText("Pool term observed in 8 papers")).toBeInTheDocument();
    expect(within(card).getByText("8 anchor papers")).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Show all 8 DOIs" })).toBeInTheDocument();
  });

  it("binds the chosen card with exactly direction, accept_thin_pool and base_updated_at", async () => {
    const { engine } = prepare();
    render(<InceptionDirection locale="en" />);
    const [first] = await cards();
    fireEvent.click(first);
    const base = engine.drafts.get(SESSION)!.updated_at;
    fireEvent.click(screen.getByRole("button", { name: "Pursue weed detection" }));
    // While the bind is in flight the cards and Pursue are disabled.
    expect(first).toBeDisabled();
    expect(await screen.findByRole("heading", { name: "Your direction: weed detection" })).toBeInTheDocument();
    expect(sentTo(engine, "POST", "/bind").map((c) => c.body)).toEqual([{ direction: "weed detection", accept_thin_pool: false, base_updated_at: base }]);
    expect(screen.getByRole("button", { name: "Continue to Shape" })).toBeEnabled();
    expect(screen.getByRole("heading", { name: "Papers to check discovery against" })).toBeInTheDocument();
  });

  it("needs the small-pool box for a thin pool and sends accept_thin_pool true", async () => {
    const { engine } = prepare({ outcomes: ["thin"] });
    render(<InceptionDirection locale="en" />);
    const [first] = await cards();
    fireEvent.click(first);
    const pursue = screen.getByRole("button", { name: "Pursue weed detection" });
    expect(pursue).toBeDisabled();
    expect(screen.getByText("Tick that you accept a pool this small.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "I accept a pool this small" }));
    fireEvent.click(pursue);
    await screen.findByRole("heading", { name: "Your direction: weed detection" });
    expect(sentTo(engine, "POST", "/bind")[0].body).toMatchObject({ direction: "weed detection", accept_thin_pool: true });
  });

  it("shows POOL_TOO_SMALL with the engine's count and floor", async () => {
    const { engine } = prepare();
    engine.refuseNext(`POST ${RECON}/bind`, { status: 409, body: { detail: { code: "POOL_TOO_SMALL", message: "small", details: { n_docs: 9, floor: 12 } } } });
    render(<InceptionDirection locale="en" />);
    fireEvent.click((await cards())[0]);
    fireEvent.click(screen.getByRole("button", { name: "Pursue weed detection" }));
    expect(await screen.findByRole("heading", { name: "The pool is under the floor for a direction" })).toBeInTheDocument();
    expect(screen.getByText("The engine counted 9; its floor is 12.")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "I accept a pool this small" })).toBeInTheDocument();
  });

  it("binds your own phrase with own only and says when it is not grounded", async () => {
    const { engine } = prepare();
    render(<InceptionDirection locale="en" />);
    await cards();
    fireEvent.click(screen.getByRole("button", { name: "Write my own direction" }));
    fireEvent.change(screen.getByLabelText("Your direction"), { target: { value: "quantum sensing" } });
    fireEvent.click(screen.getByRole("button", { name: "Pursue quantum sensing" }));
    expect(await screen.findByText("Your direction is recorded as not grounded: it occurs in 0 of 14 titles or abstracts, and a direction needs two.")).toBeInTheDocument();
    const body = sentTo(engine, "POST", "/bind")[0].body as Record<string, unknown>;
    expect(body.own).toBe("quantum sensing");
    expect("direction" in body).toBe(false);
  });

  it("checks a phrase once per press, URL-encoded, and leaves Pursue as it was", async () => {
    const { engine } = prepare();
    render(<InceptionDirection locale="en" />);
    await cards();
    fireEvent.click(screen.getByRole("button", { name: "Write my own direction" }));
    fireEvent.change(screen.getByLabelText("Your direction"), { target: { value: "weed detection & more" } });
    const pursue = screen.getByRole("button", { name: "Pursue weed detection & more" });
    const enabled = !(pursue as HTMLButtonElement).disabled;
    fireEvent.click(screen.getByRole("button", { name: "Check my phrase" }));
    expect(await screen.findByText(/This phrase occurs in 0 of 14 titles or abstracts/)).toBeInTheDocument();
    const checks = engine.calls.filter((c) => c.path === `${RECON}/evidence`);
    expect(checks).toHaveLength(1);
    expect(checks[0].search).toBe("term=weed%20detection%20%26%20more");
    expect(!(pursue as HTMLButtonElement).disabled).toBe(enabled);
    fireEvent.change(screen.getByLabelText("Your direction"), { target: { value: "weed detection" } });
    fireEvent.click(screen.getByRole("button", { name: "Check my phrase" }));
    expect(await screen.findByText("This phrase occurs in 8 of 14 titles or abstracts. It will be recorded as grounded.")).toBeInTheDocument();
    expect(document.querySelectorAll("[data-evidence] [data-doi]")).toHaveLength(8);
  });

  it("binds the skip with exactly skip and base_updated_at, then goes to Shape", async () => {
    const { engine, assign } = prepare();
    render(<InceptionDirection locale="en" />);
    await cards();
    const base = engine.drafts.get(SESSION)!.updated_at;
    fireEvent.click(screen.getByRole("button", { name: "Continue without a direction" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith(`/en/inception/shape/?draft=${SESSION}`));
    expect(sentTo(engine, "POST", "/bind").map((c) => c.body)).toEqual([{ skip: true, base_updated_at: base }]);
  });

  it("stays and shows the card when the skip is refused", async () => {
    const { engine, assign } = prepare();
    engine.refuseNext(`POST ${RECON}/bind`, { status: 422, body: { detail: { code: "NO_DIRECTION", message: "choose one" } } });
    render(<InceptionDirection locale="en" />);
    await cards();
    fireEvent.click(screen.getByRole("button", { name: "Continue without a direction" }));
    expect(await screen.findByRole("heading", { name: "Choose one direction, write your own, or go on without one" })).toBeInTheDocument();
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows a recorded skip as Not grounded with the seeds card", async () => {
    const { engine } = prepare();
    bind(engine, { skip: true });
    render(<InceptionDirection locale="en" />);
    expect(await screen.findByRole("heading", { name: "No direction chosen" })).toBeInTheDocument();
    expect(screen.getByText("Not grounded")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Papers to check discovery against" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue to Shape" })).toBeInTheDocument();
  });

  it("maps DIRECTION_UNKNOWN to its card", async () => {
    const { engine } = prepare();
    engine.refuseNext(`POST ${RECON}/bind`, { status: 422, body: { detail: { code: "DIRECTION_UNKNOWN", message: "no", details: { directions: [] } } } });
    render(<InceptionDirection locale="en" />);
    fireEvent.click((await cards())[0]);
    fireEvent.click(screen.getByRole("button", { name: "Pursue weed detection" }));
    expect(await screen.findByRole("heading", { name: "That is not a direction of the current pool" })).toBeInTheDocument();
  });

  it("runs the one narrower search on the chosen card, recomputes the cards and offers the first search back", async () => {
    const { engine } = prepare();
    render(<InceptionDirection locale="en" />);
    await cards();
    const narrower = screen.getByRole("button", { name: "Search again, narrower · 1 left" });
    expect(narrower).toBeDisabled();
    fireEvent.click((await cards())[1]);
    fireEvent.click(narrower);
    expect(await screen.findByText("These directions come from the narrower search on “weed segmentation”.")).toBeInTheDocument();
    expect(sentTo(engine, "POST", "/probe").at(-1)?.body).toEqual({ narrower: "weed segmentation" });
    await waitFor(() => expect(document.querySelector("[data-direction='embedded weed detection']")).not.toBeNull());
    expect(screen.getByRole("button", { name: "Narrower search used" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Go back to the first search" })).toBeInTheDocument();
  });

  it("keeps the original cards when the narrower search finds nothing", async () => {
    prepare({ outcomes: ["ok", "empty"] });
    render(<InceptionDirection locale="en" />);
    fireEvent.click((await cards())[0]);
    fireEvent.click(screen.getByRole("button", { name: "Search again, narrower · 1 left" }));
    expect(await screen.findByRole("heading", { name: "The search found no papers" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Narrower search used" })).toBeInTheDocument());
    expect(document.querySelector("[data-direction='weed detection']")).not.toBeNull();
  });

  it("shows NARROW_BUDGET_SPENT as its card", async () => {
    const { engine } = prepare();
    engine.refuseNext(`POST ${RECON}/probe`, { status: 409, body: { detail: { code: "NARROW_BUDGET_SPENT", message: "used" } } });
    render(<InceptionDirection locale="en" />);
    fireEvent.click((await cards())[0]);
    fireEvent.click(screen.getByRole("button", { name: "Search again, narrower · 1 left" }));
    expect(await screen.findByRole("heading", { name: "The one narrower search of this draft is used" })).toBeInTheDocument();
  });

  it("warns before a narrower search when a direction is bound, and sends nothing until confirmed", async () => {
    const { engine } = prepare();
    bind(engine, { direction: "weed detection" });
    render(<InceptionDirection locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Choose a different direction" }));
    fireEvent.click((await cards())[1]);
    fireEvent.click(screen.getByRole("button", { name: "Search again, narrower · 1 left" }));
    const dialog = await screen.findByRole("alertdialog");
    expect(sentTo(engine, "POST", "/probe")).toHaveLength(1);
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(sentTo(engine, "POST", "/probe")).toHaveLength(1);
    expect(engine.calls.some((c) => c.path.endsWith("/delta"))).toBe(false);
  });

  it("shows a binding made stale by a scope change, names the parts, keeps the cards live and offers no Continue", async () => {
    const { engine } = prepare();
    bind(engine, { direction: "weed detection" });
    const record = engine.drafts.get(SESSION)!;
    engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), end_year: 2025 }, base_updated_at: record.updated_at });
    render(<InceptionDirection locale="en" />);
    expect(await screen.findByRole("heading", { name: /The direction you chose was based on an earlier pool/ })).toBeInTheDocument();
    expect(screen.getByText("Changed: years")).toBeInTheDocument();
    const radios = await cards();
    expect(radios.every((r) => !(r as HTMLInputElement).disabled)).toBe(true);
    expect(screen.getByText("chosen on the earlier pool")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Continue to Shape" })).toBeNull();
  });

  it("lists seed candidates unticked in the engine's order and saves the ticks as golden_seeds", async () => {
    const { engine } = prepare();
    bind(engine, { direction: "weed detection" });
    render(<InceptionDirection locale="en" />);
    await screen.findByRole("heading", { name: "Papers to check discovery against" });
    await waitFor(() => expect(document.querySelectorAll("[data-seed]").length).toBeGreaterThan(2));
    const rows = [...document.querySelectorAll("[data-seed]")];
    expect(rows.every((r) => r.getAttribute("data-ticked") === "false")).toBe(true);
    const order = rows.map((r) => r.getAttribute("data-seed"));
    fireEvent.click(within(rows[0] as HTMLElement).getByRole("checkbox"));
    fireEvent.click(within(rows[1] as HTMLElement).getByRole("checkbox"));
    expect(screen.getByText("2 of 25 ticked")).toBeInTheDocument();
    const before = engine.drafts.get(SESSION)!.draft as Record<string, unknown>;
    fireEvent.click(screen.getByRole("button", { name: "Save seeds" }));
    await screen.findByText("Seeds saved");
    const put = engine.calls.filter((c) => c.method === "PUT").at(-1)!;
    expect(put.body).toMatchObject({ draft: { ...before, golden_seeds: [order[0], order[1]] } });
  });

  it("keeps saved seeds that are not in this pool ticked, and refuses a 26th", async () => {
    const saved = Array.from({ length: 25 }, (_, i) => `10.9/old${i}`);
    const { engine } = prepare({}, completeDraft({ golden_seeds: saved }));
    bind(engine, { direction: "weed detection" });
    render(<InceptionDirection locale="en" />);
    await screen.findByText("25 of 25 ticked");
    expect(document.querySelectorAll("[data-seed-saved-only]")).toHaveLength(25);
    expect(screen.getByText("At most 25 seeds.")).toBeInTheDocument();
    await waitFor(() => expect(document.querySelector("[data-seed='10.1/w000']")).not.toBeNull());
    const fresh = within(document.querySelector("[data-seed='10.1/w000']") as HTMLElement).getByRole("checkbox");
    expect(fresh).toBeDisabled();
    expect(fresh).toHaveAttribute("aria-describedby", "seeds-max");
  });

  it("says so when no paper with a DOI anchors anything", async () => {
    const { engine } = prepare({ outcomes: ["noDirections"] }, completeDraft({ concepts: [{ concept: "quantum" }] }));
    bind(engine, { skip: true });
    render(<InceptionDirection locale="en" />);
    expect(await screen.findByText(/No paper of this pool with a DOI anchors a direction or a concept/)).toBeInTheDocument();
  });

  it("shows the no-direction state with its four ways on and no code", async () => {
    prepare({ outcomes: ["noDirections"] });
    render(<InceptionDirection locale="en" />);
    expect(await screen.findByRole("heading", { name: "No phrase occurs in two or more titles or abstracts" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Change scope" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh pool with semantic search" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Write my own direction" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue without a direction" })).toBeInTheDocument();
    expect(document.querySelector("[data-state]")).toBeNull();
  });

  it("shows the no-pool state before any search, and reads no directions", async () => {
    const { engine } = prepare({}, completeDraft(), false);
    render(<InceptionDirection locale="en" />);
    expect(await screen.findByRole("heading", { name: "There is no pool to draw directions from" })).toBeInTheDocument();
    expect(engine.calls.some((c) => c.path.endsWith("/directions") || c.path.endsWith("/seeds"))).toBe(false);
  });

  it("disables the narrower search when the console has no contact address", async () => {
    const recon: ReconOptions = {};
    const set = prepare(recon);
    recon.mailto = false;
    render(<InceptionDirection locale="en" />);
    fireEvent.click((await cards())[0]);
    expect(screen.getByRole("heading", { name: "This console has no contact email for the literature databases" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search again, narrower · 1 left" })).toBeDisabled();
    expect(sentTo(set.engine, "POST", "/probe")).toHaveLength(1);
  });

  it("makes the page read-only on DRAFT_CONFLICT and offers the reload", async () => {
    const { engine } = prepare();
    render(<InceptionDirection locale="en" />);
    const [first] = await cards();
    const record = engine.drafts.get(SESSION)!;
    engine.handle("PUT", `/api/v1/inception/drafts/${SESSION}`, { draft: { ...(record.draft as object), topic: "other tab" }, base_updated_at: record.updated_at });
    fireEvent.click(first);
    fireEvent.click(screen.getByRole("button", { name: "Pursue weed detection" }));
    const card = await screen.findByRole("heading", { name: "This draft was saved somewhere else" });
    expect(card.closest("section")?.querySelector("details")?.textContent).toContain("DRAFT_CONFLICT");
    expect(first).toBeDisabled();
    expect(screen.getByRole("button", { name: "Continue without a direction" })).toBeDisabled();
  });
});
