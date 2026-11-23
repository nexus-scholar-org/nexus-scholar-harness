
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionExplore } from "@/components/inception-explore";
import { completeDraft, SESSION } from "./fixtures/inception-engine";
import type { ReconOptions } from "./fixtures/recon-engine";
import { setUp } from "./inception-helpers";

/**
 * Sample curation on Explore (M10b Part C, 02-explore "Sample curation") over
 * the stateful fake of the recon routes; the engine's answers are pinned by
 * `tests/console/test_recon_sample_api.py`.
 */

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;
const FIRST = "Real-time weed detection on embedded hardware 0";
const SECOND = "Real-time weed detection on embedded hardware 1";

type Engine = ReturnType<typeof setUp>["engine"];

function start(recon: ReconOptions = {}, draft: Record<string, unknown> = completeDraft(), more: Parameters<typeof setUp>[0] = {}) {
  const set = setUp({ draft, recon, ...more });
  set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  return set;
}

const mount = async () => {
  render(<InceptionExplore locale="en" />);
  // The first render of the screen is slow when the whole suite runs in parallel: wait up to 5 s.
  await screen.findByRole("heading", { name: /^Pool ·/ }, { timeout: 5000 });
  return screen.findByRole("button", { name: `Not relevant: ${FIRST}` }, { timeout: 5000 });
};

const reconCalls = (engine: Engine, from = 0) =>
  engine.calls.slice(from).filter((c) => c.path.startsWith(RECON)).map((c) => `${c.method} ${c.path.slice(RECON.length)}`);
const samplePosts = (engine: Engine) => engine.calls.filter((c) => c.method === "POST" && c.path === `${RECON}/sample`);
const record = (engine: Engine) => engine.drafts.get(SESSION)!;
const row = (title: string) => screen.queryByRole("button", { name: `Not relevant: ${title}` });
const openLeftOut = () => fireEvent.click(screen.getByRole("button", { name: /^Left out · / }));
const moved = () => document.querySelector("[data-sample-moved]")?.textContent ?? "";

/** Put papers on the draft record as left out, as earlier marks would have. */
function leaveOut(engine: Engine, items: { key: string; title: string }[]) {
  record(engine).sample_exclusions = {
    items: items.map((i) => ({ ...i, doi: i.key.startsWith("10.") ? i.key : null, year: 2021, provider: "openalex", reason: "NOT_RELEVANT", excluded_at: "2026-11-19T08:00:00+00:00", pool_fingerprint: "sha256:x" })),
  };
}

/** Wrap the fake: `hold` answers a matching call only when released; `fail` rejects it as a lost connection. */
function intercept(match: (method: string, path: string) => "hold" | "fail" | null) {
  const inner = globalThis.fetch;
  const held: (() => void)[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const path = new URL(url, "http://localhost").pathname.replace("/api/console", "");
      const what = match((init?.method ?? "GET").toUpperCase(), path);
      if (what === "fail") throw new TypeError("Failed to fetch");
      if (what === "hold") await new Promise<void>((resolve) => held.push(resolve));
      return inner(input, init);
    }),
  );
  return { release: () => held.splice(0).forEach((r) => r()), held };
}

describe("inception.sample", () => {
  it("names every row's button by its paper", async () => {
    start();
    await mount();
    fireEvent.click(screen.getByRole("button", { name: /^\+ 9 more/ }));
    const buttons = screen.getAllByRole("button", { name: /^Not relevant: / });
    expect(buttons).toHaveLength(14);
    for (const b of buttons) expect(b).toHaveTextContent("Not relevant");
    expect(screen.getByText("14 papers · none left out")).toBeInTheDocument();
  });

  it("sends one POST with the key and the base, then re-reads distill, directions and concepts once; the paper moves to Left out", async () => {
    const { engine } = start();
    const button = await mount();
    const base = record(engine).updated_at;
    const from = engine.calls.length;
    fireEvent.click(button);
    await waitFor(() => expect(row(FIRST)).toBeNull());
    expect(samplePosts(engine).map((c) => c.body)).toEqual([{ add: ["10.1/w000"], base_updated_at: base }]);
    await waitFor(() => expect(reconCalls(engine, from)).toEqual(["POST /sample", "POST /distill", "GET /directions", "GET /concepts"]));
    expect(screen.getByText("14 papers · 1 left out")).toBeInTheDocument();
    openLeftOut();
    const item = document.querySelector("[data-left-out-item='10.1/w000']") as HTMLElement;
    expect(within(item).getByText(FIRST)).toBeInTheDocument();
    expect(item.querySelector("[data-left-out-when]")?.textContent).toMatch(/^Left out \d{4}-\d{2}-\d{2} \d{2}:\d{2}$/);
    // The reserve paper the engine put in its place carries the badge.
    fireEvent.click(screen.getByRole("button", { name: /^\+ 9 more/ }));
    const added = document.querySelector("[data-added-for='10.1/w000']") as HTMLElement;
    expect(added.textContent).toBe("Added to replace a paper you left out");
    expect(added.closest("tr")?.textContent).toContain("Crop row following for field robots 0");
  });

  it("moves focus to the next row's button and says what moved, from the two reads", async () => {
    const { engine } = start();
    const button = await mount();
    button.focus();
    fireEvent.click(button);
    await waitFor(() => expect(row(SECOND)).toHaveFocus());
    await waitFor(() => expect(moved()).toBe(`Left out: ${FIRST}. Directions: 3 to 3. Papers: 14.`));
    expect(samplePosts(engine)).toHaveLength(1);
  });

  it("keeps the toast while it has focus and closes it after 8 seconds otherwise; Escape closes it without undoing", async () => {
    const { engine } = start();
    const button = await mount();
    fireEvent.click(button);
    const toast = (await screen.findByText(`Left out: ${FIRST}`)).closest("[data-sample-toast]") as HTMLElement;
    const undo = within(toast).getByRole("button", { name: "Undo" });
    act(() => undo.focus());
    fireEvent.focus(undo);
    await act(async () => new Promise((r) => setTimeout(r, 50)));
    expect(document.querySelector("[data-sample-toast]")).not.toBeNull();
    fireEvent.keyDown(toast, { key: "Escape" });
    expect(document.querySelector("[data-sample-toast]")).toBeNull();
    expect(samplePosts(engine)).toHaveLength(1);
  });

  it("times the toast out after 8 seconds", async () => {
    start();
    const button = await mount();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    fireEvent.click(button);
    await screen.findByText(`Left out: ${FIRST}`);
    // Focus has moved on to the next row; the toast is not focused.
    await waitFor(() => expect(row(SECOND)).toHaveFocus());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(8100);
    });
    await waitFor(() => expect(document.querySelector("[data-sample-toast]")).toBeNull());
  });

  it("addresses a paper without a DOI by its pool id", async () => {
    const { engine } = start({ noDoiPaper: true });
    await mount();
    fireEvent.click(screen.getByRole("button", { name: /^\+ 9 more/ }));
    fireEvent.click(screen.getByRole("button", { name: "Not relevant: A paper without a DOI" }));
    await waitFor(() => expect(samplePosts(engine)).toHaveLength(1));
    expect(samplePosts(engine)[0].body).toMatchObject({ add: ["openalex|Ws005"] });
  });

  it("asks before leaving out a saved seed; only the first button sends the change and a PUT without that seed", async () => {
    const draft = completeDraft({ golden_seeds: ["10.1/w000", "10.1/w001"] });
    const { engine } = start({}, draft);
    const button = await mount();
    fireEvent.click(button);
    const dialog = await screen.findByRole("alertdialog", { name: "This paper is one of your seeds" });
    expect(dialog).toHaveAccessibleDescription("This paper is one of the seeds discovery will look for. A paper you call not relevant is usually not a seed.");
    expect(within(dialog).getByRole("button", { name: "Keep it" })).toHaveFocus();
    fireEvent.click(within(dialog).getByRole("button", { name: "Keep it" }));
    expect(screen.queryByRole("alertdialog")).toBeNull();
    await waitFor(() => expect(button).toHaveFocus());
    expect(samplePosts(engine)).toHaveLength(0);

    fireEvent.click(button);
    fireEvent.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Leave it out and remove it from the seeds" }));
    await waitFor(() => expect(engine.calls.some((c) => c.method === "PUT")).toBe(true));
    const post = samplePosts(engine)[0];
    const put = engine.calls.find((c) => c.method === "PUT")!;
    expect(engine.calls.indexOf(post)).toBeLessThan(engine.calls.indexOf(put));
    expect(put.body).toEqual({ draft: { ...draft, golden_seeds: ["10.1/w001"] }, base_updated_at: expect.any(String) });
    expect((put.body as { base_updated_at: string }).base_updated_at).not.toBe((post.body as { base_updated_at: string }).base_updated_at);
    expect(record(engine).draft).toEqual({ ...draft, golden_seeds: ["10.1/w001"] });
  });

  it("draws no recommendation card of its own: EXPLORE_POOL_THIN is a checks-panel row and See directions stays enabled", async () => {
    const thinRow = () => [{ check_id: "EXPLORE_POOL_THIN", step: "explore", level: "warning" as const, params: { n: 7, floor: 12 }, action: { kind: "step", step: "scope" } }];
    start({ outcomes: ["thin"] }, completeDraft(), { checks: () => thinRow() });
    render(<InceptionExplore locale="en" />);
    await screen.findByRole("heading", { name: /^Pool ·/ });
    await waitFor(() => expect(document.body.textContent).toContain("The sample has only 7 papers. 12 or more gives steadier suggestions."));
    expect(screen.getByRole("button", { name: /^See .*direction/ })).toBeEnabled();
    expect(document.querySelector("[data-papers]")?.textContent).not.toMatch(/BELOW_FLOOR|steadier/);
  });

  it("re-reads the checks panel and announces the change to the next-step bar after each change", async () => {
    const { engine } = start({}, completeDraft(), { checks: () => [] });
    const button = await mount();
    const changed = vi.fn();
    window.addEventListener("nexus:review-changed", changed);
    await waitFor(() => expect(engine.calls.some((c) => c.path.endsWith("/checks"))).toBe(true));
    const before = engine.calls.filter((c) => c.path.endsWith("/checks")).length;
    fireEvent.click(button);
    await waitFor(() => expect(changed).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(engine.calls.filter((c) => c.path.endsWith("/checks")).length).toBeGreaterThan(before));
    window.removeEventListener("nexus:review-changed", changed);
  });

  it("shows the empty sample with Put back all, which puts every paper back", async () => {
    const set = setUp({ draft: completeDraft(), recon: { outcomes: ["thin"] } });
    set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
    const keys = Array.from({ length: 7 }, (_, i) => `10.1/t00${i}`);
    leaveOut(set.engine, keys.map((key, i) => ({ key, title: `Real-time weed detection on embedded hardware ${i}` })));
    render(<InceptionExplore locale="en" />);
    expect(await screen.findByText("Every paper has been left out. Put some back, or search again.")).toBeInTheDocument();
    expect(screen.getByText("0 papers · 7 left out")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Put back all" }));
    await waitFor(() => expect(samplePosts(set.engine)).toHaveLength(1));
    expect(samplePosts(set.engine)[0].body).toMatchObject({ remove: keys });
    expect(await screen.findByText("7 papers · none left out")).toBeInTheDocument();
  });

  it("lists a paper left out in an earlier search as Not in the current pool, and does not count it", async () => {
    const { engine } = start();
    leaveOut(engine, [{ key: "10.1/gone", title: "An earlier paper" }]);
    await mount();
    expect(screen.getByText("14 papers · none left out")).toBeInTheDocument();
    openLeftOut();
    const item = document.querySelector("[data-left-out-item='10.1/gone']") as HTMLElement;
    expect(within(item).getByText("Not in the current pool")).toBeInTheDocument();
    expect(screen.getByText("1 of these are not in the current pool.")).toBeInTheDocument();
  });

  it("says the pool was saved before replacements were kept when it has no reserve", async () => {
    start({ noReserve: true });
    await mount();
    expect(screen.getByText("This pool was saved before replacements were kept. Search again to be able to replace papers.")).toBeInTheDocument();
  });

  for (const [code, status, title, extra] of [
    ["PAPER_UNKNOWN", 422, "That paper is not in this sample", { keys: ["10.1/w000"] }],
    ["SAMPLE_EXCLUSIONS_FULL", 422, "You have left out as many papers as this draft can record", { limit: 200 }],
    ["DRAFT_CONFLICT", 409, "This draft was saved somewhere else", undefined],
    ["DRAFT_EMITTED", 409, "This draft already created a workspace", undefined],
  ] as const) {
    it(`maps ${code} to its card with the code under Details and leaves the table as it was`, async () => {
      const { engine } = start();
      const button = await mount();
      engine.refuseNext(`POST ${RECON}/sample`, { status, body: { detail: { code, message: code.toLowerCase(), ...(extra ? { details: extra } : {}) } } });
      fireEvent.click(button);
      const heading = await screen.findByRole("heading", { name: title });
      expect(heading.closest("section")?.querySelector("details")?.textContent).toContain(code);
      expect(row(FIRST)).not.toBeNull();
      expect(document.querySelector("[data-paper-key='10.1/w000'] [data-row-error]")?.textContent).toContain(code);
      expect(screen.getByText("14 papers · none left out")).toBeInTheDocument();
      if (code === "SAMPLE_EXCLUSIONS_FULL") expect(screen.getByText("The limit is 200.")).toBeInTheDocument();
      if (code === "DRAFT_CONFLICT" || code === "DRAFT_EMITTED") expect(row(FIRST)).toBeDisabled();
      if (code === "PAPER_UNKNOWN") {
        const from = engine.calls.length;
        fireEvent.click(within(heading.closest("section") as HTMLElement).getByRole("button", { name: "Reload the papers" }));
        await waitFor(() => expect(reconCalls(engine, from)).toEqual(expect.arrayContaining(["GET /sample", "POST /distill"])));
        await waitFor(() => expect(screen.queryByRole("heading", { name: title })).toBeNull());
      }
    });
  }

  it("offline: disables Not relevant and Put back, says why, and queues nothing", async () => {
    const { engine } = start();
    leaveOut(engine, [{ key: "10.1/s005", title: "Lightweight cnn weed segmentation 5" }]);
    const button = await mount();
    intercept((method, path) => (method === "POST" && path.endsWith("/recon/sample") ? "fail" : null));
    fireEvent.click(button);
    expect(await screen.findByRole("heading", { name: "Engine unreachable" })).toBeInTheDocument();
    await waitFor(() => expect(row(FIRST)).toBeDisabled());
    expect(row(SECOND)).toBeDisabled();
    expect(document.querySelector("[data-sample-offline]")?.textContent).toContain("needs the engine on this computer");
    openLeftOut();
    expect(screen.getByRole("button", { name: "Put back: Lightweight cnn weed segmentation 5" })).toBeDisabled();
    fireEvent.click(row(SECOND)!);
    expect(samplePosts(engine)).toHaveLength(0);
    expect(row(FIRST)).not.toBeNull();
  });

  it("ignores a second click during a request, queues another row, and drops a read a later change overtook", async () => {
    const { engine } = start();
    const button = await mount();
    let holdDistill = true;
    const gate = intercept((method, path) => {
      if (method === "POST" && path.endsWith("/recon/sample")) return "hold";
      if (method === "POST" && path.endsWith("/recon/distill") && holdDistill) {
        holdDistill = false;
        return "hold";
      }
      return null;
    });
    fireEvent.click(button);
    await waitFor(() => expect(gate.held).toHaveLength(1));
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    fireEvent.click(button);
    // Another row stays usable; its change waits behind the first.
    fireEvent.click(row(SECOND)!);
    gate.release();
    // The first change's answer, then its pool read is held; the second change goes and reads.
    await waitFor(() => expect(gate.held.length).toBeGreaterThan(0));
    gate.release();
    await waitFor(() => expect(samplePosts(engine)).toHaveLength(2));
    await waitFor(() => expect(gate.held.length).toBe(0));
    expect(samplePosts(engine).map((c) => (c.body as { add: string[] }).add)).toEqual([["10.1/w000"], ["10.1/w001"]]);
    await waitFor(() => expect(moved()).toContain(`Left out: ${SECOND}.`));
    await waitFor(() => expect(row(SECOND)).toBeNull());
    // Release the first change's overtaken read: the screen keeps the newer answer.
    gate.release();
    await act(async () => new Promise((r) => setTimeout(r, 20)));
    expect(row(FIRST)).toBeNull();
    expect(row(SECOND)).toBeNull();
    expect(moved()).toContain(`Left out: ${SECOND}.`);
  });

  it("shows no control to a phone-scoped token", async () => {
    setUp({
      draft: completeDraft(),
      refuseOnce: { [`GET /api/v1/inception/drafts/${SESSION}`]: { status: 403, body: { detail: { code: "TOKEN_SCOPE_REFUSED", message: "desktop only" } } } },
    });
    render(<InceptionExplore locale="en" />);
    expect(await screen.findByRole("heading", { name: "Not available on this device" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Not relevant/ })).toBeNull();
  });
});
