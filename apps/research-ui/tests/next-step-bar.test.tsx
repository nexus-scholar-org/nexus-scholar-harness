import { readFileSync } from "node:fs";
import { join } from "node:path";

import { act, cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { NextStepBar } from "@/components/next-step-bar";
import { AppShell } from "@/components/app-shell";
import { REVIEW_CHANGED_EVENT } from "@/components/review-bus";
import { ACTION_KEYS, NEXT_STATES, NEXT_STEP_COPY, WAITING_STAGES, type NextStepCopyKey } from "@/lib/next-step-copy";
import { SCREEN_ROUTES, type NextStep } from "@/lib/next-step";

/**
 * The next-step bar (`docs/ux/shared/final/04-next-step.md` "Acceptance tests", M10b Part C).
 * The engine's answer is served at the fetch boundary; the bar must print it, never derive it.
 */

let currentPath = "/en/discovery/handoff";
vi.mock("next/navigation", () => ({ usePathname: () => currentPath }));

const JOB = "djob_ab12cd34ef56ab12";

function answer(over: Partial<NextStep> = {}): NextStep {
  return {
    shape: "review.next-step-v1",
    scope: "workspace",
    phase: "discovery",
    round: 1,
    state: "READY_TO_SEARCH",
    params: {},
    waiting: null,
    action: { key: "goToHarvest", to: { screen: "discovery.harvest", query: {} } },
    also: [],
    unknown: [],
    protocol_fingerprint: null,
    computed_at: "2026-11-13T09:52:41+00:00",
    ...over,
  };
}

/** The spec's example: a harvest finished, verification running (table 2 row D). */
const VERIFYING = answer({
  state: "CORPUS_PENDING",
  params: { run: "run_003", records: 1074, works: 1050, databases: 5, answered: 5 },
  waiting: { kind: "running", stage: "verifying", job: { job_id: JOB, kind: "run", state: "running", started_at: "2026-11-13T09:40:12+00:00" }, reason: null, since: "2026-11-13T09:52:30+00:00" },
  action: { key: "followSearch", to: { screen: "discovery.harvest", query: { job: JOB } } },
});

const INTERRUPTED = answer({
  state: "CORPUS_PENDING",
  params: { run: "run_003", records: 1074, works: 1050, databases: 5, stage: "verifying" },
  waiting: { kind: "interrupted", stage: "verifying", job: null, reason: { code: "INTERRUPTED", message: null }, since: "2026-11-13T09:52:30+00:00", details: { stage_known: true } },
  action: { key: "finishPreparing", to: { screen: "discovery.harvest", query: { run: "run_003" } } },
  also: [{ key: "searchAgain", to: { screen: "discovery.harvest", query: {} } }],
});

type Reply = NextStep | { status: number; code: string } | "unreachable";
type Call = { url: string; init?: RequestInit };

function respond(reply: Reply): Response {
  if (reply === "unreachable") throw new TypeError("fetch failed");
  if ("status" in reply && "code" in reply) {
    return new Response(JSON.stringify({ detail: { code: reply.code, message: reply.code.toLowerCase() } }), { status: reply.status, headers: { "content-type": "application/json" } });
  }
  return new Response(JSON.stringify(reply), { status: 200, headers: { "content-type": "application/json" } });
}

/** Each call answers the next reply (the last one repeats). */
function engine(...replies: Reply[]) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return respond(replies[Math.min(calls.length - 1, replies.length - 1)]);
    }),
  );
  return calls;
}

function at(path: string, search = "") {
  currentPath = path;
  window.history.replaceState({}, "", `${path}${search}`);
}

const bar = () => document.querySelector("[data-next-step]") as HTMLElement | null;
const sentence = () => document.querySelector("[data-next-sentence]")?.textContent ?? "";

async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

beforeEach(() => at("/en/discovery/handoff"));
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("next-step.i18n", () => {
  const en = NEXT_STEP_COPY.en as Record<string, string>;
  const holes = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

  it("maps every state, waiting stage and action key to a key in en, fr and ar, with the same holes", () => {
    const keys = [
      ...NEXT_STATES.map((s) => `next.state.${s}`),
      ...WAITING_STAGES.map((s) => `next.waiting.${s}`),
      ...ACTION_KEYS.map((k) => `next.action.${k}`),
      "next.stopped.searching", "next.stopped.stage", "next.failed.searching", "next.failed.stage", "next.interrupted",
      "next.reason.STOPPED_BY_RESEARCHER", "next.reason.INTERRUPTED", "next.inRound",
      "next.state.SETUP_NEEDED.what.email", "next.state.SETUP_NEEDED.what.key", "next.state.SETUP_NEEDED.what.both",
      "next.stage.deduplicating", "next.stage.adding_abstracts", "next.stage.verifying",
      "next.region", "next.details", "next.asOf", "next.unknown", "next.here", "next.offline", "next.offline.last",
      "next.word.running", "next.word.stopped", "next.word.failed", "next.word.interrupted",
    ];
    for (const key of keys) expect(en, key).toHaveProperty([key]);
    for (const [key, text] of Object.entries(en)) {
      for (const locale of ["fr", "ar"] as const) {
        const other = NEXT_STEP_COPY[locale][key as NextStepCopyKey];
        expect(other, `${locale} ${key}`).toBeTruthy();
        expect(holes(other), `${locale} ${key}`).toEqual(holes(text));
      }
    }
    expect(en["next.state.PUBLISHED_STALE"]).toBe("The screening changed since you published.");
  });

  it("routes every screen the engine names, and the bar's source carries no literal accessible name (N9)", () => {
    for (const screen of ["workspaces", "inception.list", "inception.scope", "inception.explore", "inception.direction", "inception.shape", "inception.criteria", "inception.review", "inception.done", "discovery.plan", "discovery.harvest", "discovery.handoff", "discovery.chase", "screening.home", "screening.triage", "screening.publish"]) {
      expect(SCREEN_ROUTES, screen).toHaveProperty([screen]);
    }
    for (const file of ["components/next-step-bar.tsx", "components/review-bus.ts", "lib/next-step.ts", "lib/next-step-copy.ts"]) {
      const text = readFileSync(join(process.cwd(), file), "utf8");
      expect(text.match(/(aria-label|title|alt|placeholder)="/g), file).toBeNull();
    }
  });
});

describe("next-step.print", () => {
  it("prints the params as sent: a fixture with 1050 works prints 1,050, different works and records print both", async () => {
    engine(answer({ state: "CORPUS_READY", params: { run: "run_003", works: 1050, records: 1074 }, action: { key: "reviewCorpus", to: { screen: "discovery.handoff", query: {} } } }));
    at("/en/discovery/harvest");
    render(<NextStepBar locale="en" pathname="/en/discovery/harvest" />);
    await screen.findByText(/Your corpus is ready/);
    expect(sentence()).toBe("Your corpus is ready: 1,050 works from 1,074 records. Accept it to start screening.");
    expect(document.querySelector('[data-slot="works"]')).toHaveAttribute("dir", "ltr");
  });

  it("the harvest-finished, verification-pending answer follows the search to Harvest with the job id, and says no Accept", async () => {
    const calls = engine(VERIFYING);
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    await screen.findByText(/Checking/);
    expect(sentence()).toContain("Checking 1,050 works against the databases. The hand-off opens when this ends.");
    expect(document.querySelector('[data-next-word="running"]')).toHaveTextContent("Running");
    const link = screen.getByRole("link", { name: "Follow the search" });
    expect(link).toHaveAttribute("href", `/en/discovery/harvest/?job=${JOB}`);
    expect(bar()?.textContent).not.toMatch(/Accept/);
    expect(calls[0].url).toBe("/api/console/api/v1/review/next-step");
  });

  it("interrupted with can_finish: the sentence, Finish preparing with Search again, the reason under Details", async () => {
    engine(INTERRUPTED);
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    await screen.findByText(/The console may have been closed/);
    expect(screen.getByRole("link", { name: "Finish preparing this corpus" })).toHaveAttribute("href", "/en/discovery/harvest/?run=run_003");
    expect(screen.getByRole("link", { name: "Search again" })).toHaveAttribute("href", "/en/discovery/harvest/");
    const details = document.querySelector("[data-next-details]") as HTMLElement;
    expect(within(details).getByText("INTERRUPTED")).toBeInTheDocument();
    expect(details).toHaveTextContent("The search ended before the corpus was written. The cause is not recorded.");
    expect(details.querySelector("[data-next-detail-stage-named]")).toHaveTextContent("checking the works");
    expect(document.querySelector('[data-next-word="interrupted"]')).toHaveTextContent("Interrupted");
  });

  const variants: [string, NextStep, string, string][] = [
    [
      "A",
      answer({ state: "SEARCH_UNFINISHED", params: { answered: 2, databases: 5 }, waiting: { kind: "running", stage: "searching", job: { job_id: JOB }, reason: null, since: null }, action: { key: "followSearch", to: { screen: "discovery.harvest", query: { job: JOB } } } }),
      "The search is running. 2 of 5 databases have answered.",
      "Follow the search",
    ],
    [
      "G(a)",
      answer({ state: "SEARCH_UNFINISHED", params: { run: "run_002" }, waiting: { kind: "stopped", stage: "searching", job: null, reason: { code: "STOPPED_BY_RESEARCHER", message: null }, since: null }, action: { key: "searchAgain", to: { screen: "discovery.harvest", query: {} } } }),
      "You stopped the search. What was fetched is kept, but no corpus was made.",
      "Search again",
    ],
    [
      "H",
      answer({ state: "SEARCH_UNFINISHED", params: { run: "run_002" }, waiting: { kind: "failed", stage: "searching", job: null, reason: { code: "PROVIDERS_FAILED", message: null }, since: null }, action: { key: "searchAgain", to: { screen: "discovery.harvest", query: {} } } }),
      "No database answered, so nothing was kept.",
      "Search again",
    ],
  ];
  for (const [name, reply, text, label] of variants) {
    it(`SEARCH_UNFINISHED variant ${name}: the sentence and its button`, async () => {
      engine(reply);
      render(<NextStepBar locale="en" pathname="/en/discovery/plan" />);
      await screen.findByRole("link", { name: label });
      expect(sentence()).toContain(text);
    });
  }

  it("a failed preparation names the stage and prints the engine's message; a registered reason code reads its card title", async () => {
    engine(answer({
      state: "CORPUS_PENDING",
      params: { run: "run_003", stage: "verifying" },
      waiting: { kind: "failed", stage: "verifying", job: null, reason: { code: "DISCOVERY_FAILED", message: "RuntimeError: verifier down" }, since: null },
      action: { key: "finishPreparing", to: { screen: "discovery.harvest", query: { run: "run_003" } } },
    }));
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    await screen.findByText(/preparing the corpus failed/);
    expect(sentence()).toContain("The search finished, but preparing the corpus failed at checking the works. RuntimeError: verifier down");
    expect(document.querySelector("[data-next-detail-reason]")).toHaveTextContent("The search failed");
  });

  it("labels the draft's missing fields with the inception labels, the step with its name, and adds the round", async () => {
    engine(answer({ scope: "draft", state: "DRAFT_INCOMPLETE", params: { fields: ["paradigm", "rqs", "criteria_decisions"], step: "shape" }, action: { key: "goToStep", to: { screen: "inception.shape", query: { draft: "rec_1" } } } }));
    at("/en/inception/review/", "?draft=rec_1");
    render(<NextStepBar locale="en" pathname="/en/inception/review/" />);
    await screen.findByRole("link", { name: "Go to Shape" });
    expect(sentence()).toBe("Your draft still needs Paradigm, Research questions, and decisions on the criteria.");
    expect(screen.getByRole("link", { name: "Go to Shape" })).toHaveAttribute("href", "/en/inception/shape/?draft=rec_1");
    cleanup();
    engine(answer({ state: "SCREENING", params: { needs_you: 3, total: 10, round: 2 }, action: { key: "openTriage", to: { screen: "screening.triage", query: {} } } }));
    at("/en/screening/home");
    render(<NextStepBar locale="en" pathname="/en/screening/home" />);
    await screen.findByRole("link", { name: "Open triage" });
    expect(sentence()).toBe("3 of 10 records still need you in round 2.");
  });
});

describe("next-step.layout", () => {
  it("names the screen's own button when the destination is this screen, with no link", async () => {
    engine(answer({ state: "STAGED_EXPORTS", params: { n: 2 }, action: { key: "reviewExports", to: { screen: "discovery.handoff", query: {} } } }));
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    expect(await screen.findByText("Next: Review and accept the exports. The button is on this page.")).toBeInTheDocument();
    expect(within(bar()!).queryByRole("link")).toBeNull();
  });

  it("on a gate the bar is in the naming form even when the action points elsewhere", async () => {
    engine(answer({ phase: "published", state: "PUBLISHED", action: { key: "goToChase", to: { screen: "discovery.chase", query: {} } } }));
    at("/en/screening/publish");
    render(<NextStepBar locale="en" pathname="/en/screening/publish" />);
    expect(await screen.findByText("Next: Go to Chase. The button is on this page.")).toBeInTheDocument();
    expect(within(bar()!).queryByRole("link")).toBeNull();
    cleanup();
    engine(answer({ state: "CORPUS_READY", params: { works: 1, records: 2 }, action: { key: "reviewCorpus", to: { screen: "discovery.handoff", query: {} } } }));
    at("/en/discovery/handoff");
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    expect(await screen.findByText("Next: Review and accept the corpus. The button is on this page.")).toBeInTheDocument();
  });

  it("the button is secondary and the page keeps exactly one brand button", async () => {
    engine(VERIFYING);
    at("/en/discovery/handoff");
    render(
      <AppShell locale="en">
        <button type="button" className="bg-brand text-on-brand">
          Page action
        </button>
      </AppShell>,
    );
    const link = await screen.findByRole("link", { name: "Follow the search" });
    const classes = link.className.split(/\s+/);
    expect(classes).not.toContain("bg-brand");
    expect(classes).toContain("border-brand");
    expect(document.querySelectorAll(".bg-brand")).toHaveLength(1);
  });
});

describe("next-step.states", () => {
  it("loading shows the skeleton with aria-busy and no sentence", async () => {
    let release: (r: Response) => void = () => undefined;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => (release = resolve))));
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    expect(bar()).toHaveAttribute("aria-busy", "true");
    expect(document.querySelector("[data-next-skeleton]")).not.toBeNull();
    expect(document.querySelector("[data-next-sentence]")).toBeNull();
    await act(async () => release(respond(VERIFYING)));
    await screen.findByText(/Checking/);
    expect(bar()).not.toHaveAttribute("aria-busy");
  });

  it("ENGINE_UNREACHABLE keeps the last sentence as of its time, with no button", async () => {
    engine(VERIFYING, { status: 502, code: "CONSOLE_UNREACHABLE" });
    render(<NextStepBar locale="en" pathname="/en/discovery/handoff" />);
    await screen.findByRole("link", { name: "Follow the search" });
    act(() => window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT)));
    const offline = await screen.findByText(/The page cannot reach the engine/);
    expect(offline).toHaveTextContent("Last answer: Checking 1,050 works against the databases.");
    expect(offline).toHaveTextContent("As of 2026-11-13 09:52");
    expect(within(bar()!).queryByRole("link")).toBeNull();
  });

  for (const [code, status] of [["TOKEN_SCOPE_REFUSED", 403], ["HOST_REFUSED", 400], ["TOKEN_REQUIRED", 401]] as const) {
    it(`${code} renders nothing`, async () => {
      const calls = engine({ status, code });
      render(<NextStepBar locale="en" pathname="/en/screening/home" />);
      await flush();
      await flush();
      expect(calls).toHaveLength(1);
      expect(bar()).toBeNull();
    });
  }

  it("a draft refusal renders nothing, and the draft route is read with the draft id", async () => {
    const calls = engine({ status: 404, code: "DRAFT_NOT_FOUND" });
    at("/en/inception/shape/", "?draft=rec_missing");
    render(<NextStepBar locale="en" pathname="/en/inception/shape/" />);
    await flush();
    await flush();
    expect(calls[0].url).toBe("/api/console/api/v1/inception/drafts/rec_missing/next-step");
    expect(bar()).toBeNull();
  });

  it("the unknown line sits behind Details", async () => {
    engine(answer({ unknown: ["jobs"] }));
    render(<NextStepBar locale="en" pathname="/en/discovery/plan" />);
    await screen.findByRole("link", { name: "Go to Harvest" });
    expect(document.querySelector("[data-next-details] [data-next-unknown]")).toHaveTextContent("Some information could not be read.");
  });
});

describe("next-step.refresh", () => {
  it("re-reads on nexus:review-changed and on a route change; never sends If-None-Match", async () => {
    const calls = engine(answer(), answer({ state: "STAGED_EXPORTS", params: { n: 1 }, action: { key: "reviewExports", to: { screen: "discovery.handoff", query: {} } } }), answer({ state: "DONE", phase: "published", action: { key: "goToPublish", to: { screen: "screening.publish", query: {} } } }));
    at("/en/discovery/plan");
    const view = render(<NextStepBar locale="en" pathname="/en/discovery/plan" />);
    await screen.findByRole("link", { name: "Go to Harvest" });
    act(() => window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT)));
    await screen.findByRole("link", { name: "Review and accept the exports" });
    at("/en/discovery/harvest");
    view.rerender(<NextStepBar locale="en" pathname="/en/discovery/harvest" />);
    await screen.findByRole("link", { name: "Go to Publish" });
    expect(calls).toHaveLength(3);
    for (const call of calls) {
      const headers = new Headers(call.init?.headers);
      expect(headers.has("if-none-match")).toBe(false);
      expect(call.init?.method ?? "GET").toBe("GET");
    }
  });

  it("polls every 5 s only while waiting.kind is running", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const idle = answer({ state: "CORPUS_READY", params: { works: 1050, records: 1074 }, action: { key: "reviewCorpus", to: { screen: "discovery.handoff", query: {} } } });
    const calls = engine(VERIFYING, VERIFYING, idle);
    render(<NextStepBar locale="en" pathname="/en/discovery/harvest" />);
    await act(async () => vi.advanceTimersByTimeAsync(10));
    expect(calls).toHaveLength(1);
    await act(async () => vi.advanceTimersByTimeAsync(5_000));
    expect(calls).toHaveLength(2);
    await act(async () => vi.advanceTimersByTimeAsync(5_000));
    expect(calls).toHaveLength(3);
    expect(sentence()).toContain("Your corpus is ready");
    await act(async () => vi.advanceTimersByTimeAsync(20_000));
    expect(calls).toHaveLength(3);
  });

  it("never has two requests in flight; a refresh asked for meanwhile runs once afterwards", async () => {
    const pending: ((r: Response) => void)[] = [];
    let open = 0;
    let most = 0;
    const fetch = vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          open += 1;
          most = Math.max(most, open);
          pending.push((r) => {
            open -= 1;
            resolve(r);
          });
        }),
    );
    vi.stubGlobal("fetch", fetch);
    render(<NextStepBar locale="en" pathname="/en/discovery/plan" />);
    await flush();
    for (let i = 0; i < 3; i += 1) act(() => window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT)));
    await flush();
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => pending[0](respond(answer())));
    await flush();
    expect(fetch).toHaveBeenCalledTimes(2);
    await act(async () => pending[1](respond(answer())));
    await flush();
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(most).toBe(1);
  });

  it("drops an answer older than the one shown", async () => {
    const older = answer({ state: "DONE", phase: "published", computed_at: "2026-11-13T09:00:00+00:00", action: { key: "goToPublish", to: { screen: "screening.publish", query: {} } } });
    engine(answer(), older);
    render(<NextStepBar locale="en" pathname="/en/discovery/plan" />);
    await screen.findByRole("link", { name: "Go to Harvest" });
    act(() => window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT)));
    await flush();
    await flush();
    expect(screen.getByRole("link", { name: "Go to Harvest" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Go to Publish" })).toBeNull();
  });
});

describe("next-step.a11y", () => {
  it("announces a state change once, 2 s after it settles, and not an unchanged poll; focus stays on the button", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const later = (over: Partial<NextStep>, minute: number) => answer({ ...over, computed_at: `2026-11-13T10:${String(minute).padStart(2, "0")}:00+00:00` });
    const staged = { state: "STAGED_EXPORTS", params: { n: 1 }, action: { key: "reviewExports", to: { screen: "discovery.handoff", query: {} } } } as const;
    engine(later({}, 1), later({ ...staged }, 2), later({ ...staged, params: { n: 2 } }, 3));
    render(<NextStepBar locale="en" pathname="/en/discovery/plan" />);
    await act(async () => vi.advanceTimersByTimeAsync(10));
    const live = document.querySelector("[data-next-live]") as HTMLElement;
    expect(live).toHaveAttribute("aria-live", "polite");
    expect(live).toHaveAttribute("role", "status");
    await act(async () => vi.advanceTimersByTimeAsync(3_000));
    expect(live.textContent).toBe("");

    const link = screen.getByRole("link", { name: "Go to Harvest" });
    link.focus();
    await act(async () => {
      window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT));
      await vi.advanceTimersByTimeAsync(10);
    });
    expect(document.activeElement).toBe(link);
    expect(link).toHaveTextContent("Review and accept the exports");
    expect(live.textContent).toBe("");
    await act(async () => vi.advanceTimersByTimeAsync(2_000));
    expect(live.textContent).toBe("1 database exports are staged. Accept them to start screening.");

    await act(async () => {
      window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT));
      await vi.advanceTimersByTimeAsync(3_000);
    });
    expect(sentence()).toContain("2 database exports");
    expect(live.textContent).toBe("1 database exports are staged. Accept them to start screening.");
  });

  it("is a region labelled What comes next; in Arabic ids and counts are LTR and the arrow mirrors", async () => {
    engine(VERIFYING);
    at("/ar/discovery/handoff");
    render(<NextStepBar locale="ar" pathname="/ar/discovery/handoff" />);
    const region = await screen.findByRole("region", { name: "ما التالي" });
    await within(region).findByRole("link", { name: "تابع البحث" });
    expect(region.querySelector('[data-slot="works"]')).toHaveAttribute("dir", "ltr");
    expect(region.querySelector('[data-slot="works"]')).toHaveTextContent("1,050");
    expect(region.querySelector("[data-next-action] svg")?.getAttribute("class")).toContain("rtl:-scale-x-100");
    expect(region.querySelector("[aria-label]")).toBeNull();
  });
});

describe("next-step.where", () => {
  function shell(path: string, search = "") {
    at(path, search);
    return render(
      <AppShell locale="en">
        <h1>Route</h1>
      </AppShell>,
    );
  }

  it("is absent on /workspaces and on triage, and reads nothing there", async () => {
    const calls = engine(VERIFYING);
    shell("/en/workspaces");
    await flush();
    expect(bar()).toBeNull();
    cleanup();
    shell("/en/screening/triage");
    await flush();
    expect(bar()).toBeNull();
    expect(calls).toHaveLength(0);
  });

  it("is absent with a phone-scoped token", async () => {
    engine({ status: 403, code: "TOKEN_SCOPE_REFUSED" });
    shell("/en/screening/home");
    await flush();
    await flush();
    expect(bar()).toBeNull();
  });

  for (const [path, search] of [["/en/inception/scope/", "?draft=rec_1"], ["/en/discovery/harvest", ""], ["/en/screening/home", ""]] as const) {
    it(`is present on ${path}, between the banner and main`, async () => {
      engine(answer());
      shell(path, search);
      const region = await screen.findByRole("region", { name: "What comes next" });
      const main = document.querySelector("main") as HTMLElement;
      expect(main.contains(region)).toBe(false);
      expect(region.compareDocumentPosition(main) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      expect(document.querySelector("header")!.compareDocumentPosition(region) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });
  }
});
