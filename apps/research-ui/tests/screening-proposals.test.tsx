import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { CHEAPEST_ANTHROPIC_MODEL, LISTED_ANTHROPIC_MODELS, PROPOSALS_COPY, ScreeningProposals } from "@/components/screening-proposals";
import { SUPPORTED_LOCALES } from "@/i18n";

/**
 * Agent proposals run (spec 06) in jsdom. The engine is stubbed at `fetch` with
 * the response shapes of `GET /proposals/setup`, `POST /proposals/runs` and
 * `GET /proposals/runs/{id}`; every gate (consent, key, lock, ceiling) is the
 * engine's, so the tests check what the screen sends and how it shows the result.
 */

const ESTIMATE = {
  records: 3,
  tokens: { input_tokens: 2400, cache_read_tokens: 1200, cache_write_tokens: 600, output_tokens: 1800 },
  assumptions: { chars_per_token: 4, output_tokens_per_record: 600 },
  cost_usd: 0.0512,
  batch: false,
  prices_as_of: "2026-11-05",
  priced: true,
};

function setup(options: { key?: "keychain" | "none"; consent?: boolean; latest?: unknown } = {}) {
  return {
    task: { task_version: "screen-v1", prompt_sha256: "sha256:abc", model: "claude-opus-5-5", effort: "low" },
    providers: [
      { provider: "anthropic", key: options.key ?? "keychain", consent: options.consent ? { accepted_at: "2026-11-05T09:00:00Z", model: "claude-opus-5-5", prompt_sha256: "sha256:abc" } : null },
      { provider: "openai_compatible", key: "none", consent: null },
      { provider: "gemini", key: "none", consent: null },
    ],
    data_flow: "titles, abstracts and publication years of every record in the run, and the screening criteria",
    active_run: null,
    latest_run: options.latest ?? null,
  };
}

function view(overrides: Record<string, unknown> = {}) {
  return {
    run_id: "RUN-1", kind: "proposals", state: "completed", code: null, provider: "anthropic", model: "claude-opus-5-5", effort: "low",
    records: 3, done: 3, failed: 0, refused: 0, truncated: 0, invalid: 0, check_failures: 0, cost_so_far: 0.05, cost_ceiling_usd: null,
    started_at: "2026-11-05T10:00:00Z", finished_at: "2026-11-05T10:01:00Z", ...overrides,
  };
}

function engine(options: { setup?: unknown; start?: (body: Record<string, unknown>) => Response; run?: unknown; decided?: string[]; cancel?: unknown } = {}) {
  const log: { method: string; path: string; body: Record<string, unknown> | null }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      const method = (init?.method ?? "GET").toUpperCase();
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      log.push({ method, path, body });
      const ok = (b: unknown) => new Response(JSON.stringify(b), { status: 200, headers: { "content-type": "application/json" } });
      if (path === "/proposals/setup") return ok(options.setup ?? setup());
      if (path === "/queue") return ok({ items: (options.decided ?? []).map((s) => ({ study_id: s, title: "t", batch_id: "b", has_proposal: false, decided: true, flags: [] })), next_cursor: null });
      if (path === "/proposals/runs" && body?.estimate_only) return ok({ run_id: null, estimate: ESTIMATE });
      if (path === "/proposals/runs") return options.start ? options.start(body ?? {}) : ok({ run_id: "RUN-1", estimate: ESTIMATE });
      if (path === "/proposals/runs/RUN-1/cancel") return ok(options.cancel ?? { run_id: "RUN-1", state: "running", cancel_requested: true });
      if (path === "/proposals/runs/RUN-1") return ok(options.run ?? view());
      return new Response(JSON.stringify({ detail: { code: "NOT_FOUND" } }), { status: 404 });
    }),
  );
  return log;
}

afterEach(() => vi.unstubAllGlobals());

const startButton = () => screen.findByRole("button", { name: "Start agent proposals · 3 records" });

/**
 * The first render in this file is cold (module graph, first role and accessible-name
 * queries over the whole screen) and cost more than Testing Library's one-second wait
 * for the Start button, so the first test failed with "Unable to find role=button"
 * on an idle machine and the others did whenever the machine was busy. The button is
 * not late because of the screen's logic: it appears once the setup and the estimate
 * have answered. One throw-away render pays the cold cost outside any test's wait.
 */
beforeAll(async () => {
  engine();
  const warm = render(<ScreeningProposals locale="en" />);
  await screen.findByRole("button", { name: "Start agent proposals · 3 records" }, { timeout: 20_000 });
  warm.unmount();
  vi.unstubAllGlobals();
}, 30_000);

describe("proposals.consent-required", () => {
  it("keeps Start disabled until consent is ticked, and sends the consent with the run", async () => {
    const log = engine();
    render(<ScreeningProposals locale="en" />);
    const start = await startButton();
    expect(start).toBeDisabled();
    expect(log.filter((c) => c.path === "/proposals/runs").every((c) => c.body?.estimate_only === true)).toBe(true);
    fireEvent.click(screen.getByRole("checkbox", { name: /I consent to send the records above to Anthropic/ }));
    expect(start).toBeEnabled();
    fireEvent.click(start);
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("What leaves this machine: titles, abstracts and publication years");
    fireEvent.click(screen.getByRole("button", { name: "Start the run" }));
    await waitFor(() => expect(log.some((c) => c.path === "/proposals/runs" && !c.body?.estimate_only)).toBe(true));
    const sent = log.find((c) => c.path === "/proposals/runs" && !c.body?.estimate_only)!.body!;
    expect(sent.consent).toMatchObject({ provider: "anthropic" });
    expect(sent.scope).toEqual({ view: "no_proposal" });
    await screen.findByText("3 of 3 proposed");
  });

  it("shows the engine's CONSENT_REQUIRED card when the engine refuses", async () => {
    engine({
      setup: setup({ consent: true }),
      start: () => new Response(JSON.stringify({ detail: { code: "CONSENT_REQUIRED", message: "no consent" } }), { status: 409 }),
    });
    render(<ScreeningProposals locale="en" />);
    fireEvent.click(await startButton());
    fireEvent.click(await screen.findByRole("button", { name: "Start the run" }));
    expect(await screen.findByRole("heading", { name: "Consent needed" })).toBeInTheDocument();
    expect(document.querySelector('[data-state="CONSENT_REQUIRED"]')).toHaveTextContent("CONSENT_REQUIRED");
  });

  it("without a key, names the terminal command and never offers a key field", async () => {
    engine({ setup: setup({ key: "none" }) });
    render(<ScreeningProposals locale="en" />);
    await startButton();
    const card = document.querySelector('[data-state="PROVIDER_KEY_MISSING"]');
    expect(card).toHaveTextContent("uv run nexus-scholar keys set anthropic");
    expect(document.querySelector('input[type="password"]')).toBeNull();
    expect(screen.getByRole("button", { name: "Start agent proposals · 3 records" })).toBeDisabled();
  });
});

describe("proposals.cost-ceiling-hard-stop", () => {
  it("sends the ceiling, states it before the run, and shows a stopped run as partial with a resume", async () => {
    const log = engine({ setup: setup({ consent: true }), run: view({ state: "stopped", code: "COST_CEILING_REACHED", done: 1, cost_so_far: 0.02, cost_ceiling_usd: 0.02 }) });
    render(<ScreeningProposals locale="en" />);
    await screen.findByText(/prices as of 2026-11-05/);
    fireEvent.change(screen.getByLabelText("Cost ceiling (USD)"), { target: { value: "0.02" } });
    fireEvent.click(await startButton());
    expect(await screen.findByRole("dialog")).toHaveTextContent("The run stops at $0.02");
    fireEvent.click(screen.getByRole("button", { name: "Start the run" }));
    await screen.findByText(/stopped at 1 of 3\. 2 records have no draft/);
    expect(log.find((c) => c.path === "/proposals/runs" && !c.body?.estimate_only)!.body!.cost_ceiling_usd).toBe(0.02);
    expect(document.querySelector('[data-state="COST_CEILING_REACHED"]')).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resume over the records without a draft" })).toBeInTheDocument();
  });
});

describe("proposals.unpriced-model", () => {
  it("disables the ceiling, sends none, and shows the cost as not measured", async () => {
    const log: Record<string, unknown>[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
        const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
        const ok = (b: unknown) => new Response(JSON.stringify(b), { status: 200, headers: { "content-type": "application/json" } });
        if (path === "/proposals/setup") return ok(setup({ consent: true }));
        if (path === "/queue") return ok({ items: [], next_cursor: null });
        if (path === "/proposals/runs" && body?.estimate_only) return ok({ run_id: null, estimate: { ...ESTIMATE, cost_usd: null, priced: false } });
        if (path === "/proposals/runs") {
          log.push(body ?? {});
          return ok({ run_id: "RUN-1", estimate: ESTIMATE });
        }
        if (path === "/proposals/runs/RUN-1") return ok(view({ cost_so_far: null }));
        return new Response(JSON.stringify({ detail: { code: "NOT_FOUND" } }), { status: 404 });
      }),
    );
    render(<ScreeningProposals locale="en" />);
    await screen.findByText(/No price on file for this model, so its cost cannot be measured/);
    const ceiling = screen.getByLabelText("Cost ceiling (USD)");
    expect(ceiling).toBeDisabled();
    fireEvent.click(await startButton());
    fireEvent.click(await screen.findByRole("button", { name: "Start the run" }));
    await screen.findByText("Cost so far: not measured (no price on file for this model)");
    expect(log[0].cost_ceiling_usd).toBeNull();
  });
});

describe("proposals.no-content-before-decision", () => {
  it("never reads a draft and shows only counts", async () => {
    const log = engine({ setup: setup({ consent: true, latest: view({ refused: 1, done: 3 }) }) });
    render(<ScreeningProposals locale="en" />);
    await screen.findByText("3 of 3 proposed");
    expect(screen.getByText(/1 refused/)).toBeInTheDocument();
    expect(log.some((c) => /\/records\/.+\/proposal$/.test(c.path))).toBe(false);
    for (const word of ["INCLUDE", "EXCLUDE", "MAYBE"]) expect(document.body.textContent).not.toContain(word);
  });
});

describe("proposals copy", () => {
  it("has every key in every locale", () => {
    const keys = Object.keys(PROPOSALS_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(PROPOSALS_COPY[locale]).sort()).toEqual(keys);
  });
});

// H-screening-drafts (acceptance run 2026-11-20): one click cost $7.59 where $0.22
// was meant, because the model went back to Opus on every reload and the dialog
// named neither the model nor the estimate; a Batch run looked stuck for minutes.
describe("proposals.model-remembered (H-screening-drafts)", () => {
  it("defaults to the cheapest listed model when the workspace has no run", async () => {
    engine({ setup: setup({ consent: true }) });
    render(<ScreeningProposals locale="en" />);
    await startButton();
    expect(screen.getByLabelText("Model")).toHaveValue("claude-haiku-5-5");
  });

  it("starts from the last model used in this workspace, after every reload", async () => {
    const remembered = { ...setup({ consent: true }), last_model: { provider: "anthropic", model: "claude-sonnet-5-5" } };
    const log = engine({ setup: remembered });
    const first = render(<ScreeningProposals locale="en" />);
    await startButton();
    expect(screen.getByLabelText("Model")).toHaveValue("claude-sonnet-5-5");
    first.unmount();
    render(<ScreeningProposals locale="en" />);
    await startButton();
    expect(screen.getByLabelText("Model")).toHaveValue("claude-sonnet-5-5");
    await waitFor(() => expect(log.filter((c) => c.body?.estimate_only).every((c) => c.body?.model === "claude-sonnet-5-5")).toBe(true));
  });

  it("names the model, the record count and the estimate in the confirmation", async () => {
    engine({ setup: setup({ consent: true }) });
    render(<ScreeningProposals locale="en" />);
    await screen.findByText(/prices as of 2026-11-05/);
    fireEvent.click(await startButton());
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("Send 3 records to Anthropic with claude-haiku-5-5?");
    expect(dialog).toHaveTextContent("Estimated cost: $0.0512 (prices as of 2026-11-05).");
  });
});

describe("proposals.run-starting (H-screening-drafts)", () => {
  it("shows the run as starting as soon as Start the run is pressed", async () => {
    let release: (r: Response) => void = () => {};
    engine({ setup: setup({ consent: true }), start: () => new Promise<Response>((resolve) => (release = resolve)) as unknown as Response });
    render(<ScreeningProposals locale="en" />);
    fireEvent.click(await startButton());
    fireEvent.click(await screen.findByRole("button", { name: "Start the run" }));
    expect(await screen.findByText("Starting the run…")).toBeInTheDocument();
    expect(screen.queryByText("No run yet.")).toBeNull();
    release(new Response(JSON.stringify({ run_id: "RUN-1", estimate: ESTIMATE }), { status: 200, headers: { "content-type": "application/json" } }));
    await screen.findByText("3 of 3 proposed");
  });
});

describe("proposals.run-starting-again (H-screening-drafts, review F2)", () => {
  it("shows the run as starting above an earlier run's panel", async () => {
    let release: (r: Response) => void = () => {};
    const earlier = view({ run_id: "RUN-0", state: "completed", done: 3 });
    engine({ setup: setup({ consent: true, latest: earlier }), start: () => new Promise<Response>((resolve) => (release = resolve)) as unknown as Response });
    render(<ScreeningProposals locale="en" />);
    await screen.findByText("3 of 3 proposed");
    fireEvent.click(await screen.findByRole("button", { name: /Start agent proposals|Resume/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Start the run" }));
    expect(await screen.findByText("Starting the run…")).toBeInTheDocument();
    release(new Response(JSON.stringify({ run_id: "RUN-1", estimate: ESTIMATE }), { status: 200, headers: { "content-type": "application/json" } }));
    await waitFor(() => expect(screen.queryByText("Starting the run…")).toBeNull());
  });
});

describe("proposals.batch-waiting (H-screening-drafts)", () => {
  it("says a Batch run is waiting on the batch service, with the time waited", async () => {
    const started = new Date(Date.now() - 125_000).toISOString();
    const running = view({ state: "running", done: 0, records: 450, batch: true, chunk_size: 200, started_at: started, finished_at: null, cost_so_far: 0 });
    engine({ setup: setup({ consent: true, latest: running }), run: running });
    render(<ScreeningProposals locale="en" />);
    const note = await screen.findByText(/Sent to the batch service; results arrive in chunks of 200, usually within minutes\./);
    expect(note).toHaveTextContent(/Waiting 2 min \d+ s\./);
  });

  it("says nothing of a batch for a direct run", async () => {
    const running = view({ state: "running", done: 0, batch: false, finished_at: null });
    engine({ setup: setup({ consent: true, latest: running }), run: running });
    render(<ScreeningProposals locale="en" />);
    await screen.findByText("0 of 3 proposed");
    expect(screen.queryByText(/batch service/)).toBeNull();
  });
});

describe("proposals.not-prepared (H-screening-drafts)", () => {
  it("says the batches are not prepared, never that the corpus is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
        if (path === "/proposals/setup") return new Response(JSON.stringify(setup()), { status: 200, headers: { "content-type": "application/json" } });
        return new Response(JSON.stringify({ detail: { code: "BATCHES_NOT_PREPARED", message: "the corpus is accepted; prepare the screening batches" } }), { status: 409 });
      }),
    );
    render(<ScreeningProposals locale="en" />);
    expect(await screen.findByRole("heading", { name: "Batches not prepared yet" })).toBeInTheDocument();
    expect(screen.queryByText("No accepted corpus")).toBeNull();
  });
});

describe("proposals.cheapest-model (H-screening-drafts)", () => {
  it("is the listed model with the lowest input and output prices in the engine's price table", () => {
    const toml = readFileSync(resolve(process.cwd(), "../../src/scholar_agent/tasks/screening/prices.toml"), "utf-8");
    const price = (model: string, field: "input" | "output") => {
      const block = toml.split(`[anthropic."${model}"]`)[1].split(/\r?\n\[/)[0];
      return Number(new RegExp(`^${field} = ([0-9.]+)`, "m").exec(block)![1]);
    };
    const total = (model: string) => price(model, "input") + price(model, "output");
    const cheapest = [...LISTED_ANTHROPIC_MODELS].sort((a, b) => total(a) - total(b))[0];
    expect(CHEAPEST_ANTHROPIC_MODEL).toBe(cheapest);
  });
});


describe("proposals cancel (H-run-small-fixes, finding 35)", () => {
  it("says the run is stopping until a poll reports it finished, and offers no Start meanwhile", async () => {
    const running = view({ state: "running", done: 1, finished_at: null });
    const log = engine({ setup: setup({ latest: running }), run: { ...running, cancel_requested: true } });
    render(<ScreeningProposals locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Cancel the run" }));
    await screen.findByText(/Stopping the run/);
    expect(screen.queryByRole("button", { name: "Cancel the run" })).toBeNull();
    expect(log.filter((c) => c.method === "POST" && c.path === "/proposals/runs" && !c.body?.estimate_only)).toHaveLength(0);
  });

  it("has the stopping sentence in every locale", () => {
    for (const locale of SUPPORTED_LOCALES) expect(PROPOSALS_COPY[locale].stopping, locale).toBeTruthy();
  });
});

describe("proposals.redraft (M11b part C, spec 13)", () => {
  it("offers to draft again the records whose draft predates a revision, scoped to them", async () => {
    const log = engine({ setup: { ...setup({ consent: true }), earlier_wording_drafts: { criteria_version: 1, count: 2, study_ids: ["STU-a", "STU-b"] } } });
    render(<ScreeningProposals locale="en" />);
    await startButton();
    fireEvent.click(screen.getByRole("button", { name: "Draft again the 2 records whose draft predates the revision" }));
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("Send 2 records to Anthropic");
    await waitFor(() => expect(log.some((c) => c.path === "/proposals/runs" && c.body?.estimate_only && (c.body.scope as { study_ids?: string[] })?.study_ids)).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: "Start the run" }));
    await waitFor(() => expect(log.some((c) => c.path === "/proposals/runs" && !c.body?.estimate_only)).toBe(true));
    const sent = log.find((c) => c.path === "/proposals/runs" && !c.body?.estimate_only)!.body!;
    expect(sent.scope).toEqual({ study_ids: ["STU-a", "STU-b"] });
  });

  it("says nothing of it when every draft is current", async () => {
    engine({ setup: { ...setup({ consent: true }), earlier_wording_drafts: { criteria_version: 2, count: 0, study_ids: [] } } });
    render(<ScreeningProposals locale="en" />);
    await startButton();
    expect(document.querySelector("[data-redraft]")).toBeNull();
  });
});
