import { act, render, screen, waitFor } from "@testing-library/react";
import { expect, vi } from "vitest";

import { InceptionScope } from "@/components/inception-scope";
import { InceptionExplore } from "@/components/inception-explore";
import { InceptionDirection } from "@/components/inception-direction";
import { InceptionShape } from "@/components/inception-shape";
import { InceptionCriteria } from "@/components/inception-criteria";
import { InceptionReview } from "@/components/inception-review";
import { InceptionDone } from "@/components/inception-done";
import { DiscoveryOverview } from "@/components/discovery-overview";
import { DiscoveryPlan } from "@/components/discovery-plan";
import { DiscoveryRecall } from "@/components/discovery-recall";
import { DiscoveryHarvest } from "@/components/discovery-harvest";
import { DiscoveryDedup } from "@/components/discovery-dedup";
import { DiscoveryReport } from "@/components/discovery-report";
import { DiscoveryHandoff } from "@/components/discovery-handoff";
import { DiscoveryChase } from "@/components/discovery-chase";
import { ScreeningImport } from "@/components/screening-import";
import type { Locale } from "@/i18n";

import { completeDraft, outOfScopeId, proofId, ROOT, SESSION } from "./fixtures/inception-engine";
import type { ReconOptions } from "./fixtures/recon-engine";
import { setUp as inceptionSetUp } from "./inception-helpers";
import { setUp as discoverySetUp } from "./discovery-helpers";
import { visibleWords } from "./guidance-words";

/**
 * M10d (03-guidance): each audited screen in the state its acceptance tests
 * name, over the vitest fake engines. Shared by the word count, the audit, the
 * never-hidden check and the density budget, so all four read the same DOM.
 */

const RECON = `/api/v1/inception/drafts/${SESSION}/recon`;

function probed(recon: ReconOptions = {}, draft: Record<string, unknown> = completeDraft()) {
  const set = inceptionSetUp({ draft, recon });
  set.engine.handle("POST", `${RECON}/probe`, { refresh: false, semantic: false });
  return set;
}

const decided = () => completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId()]: true } });

const emitted = () => ({
  slug: "weed-review",
  workspace_dir: `${ROOT}\\weed-review`,
  protocol_fingerprint: "sha256:" + "ab".repeat(32),
  emitted_at: "2026-11-09T10:00:00Z",
  replaced: false,
  previous_fingerprint: null,
  backup_dir: null,
});

function importFake() {
  const corpus = {
    shape: "screening.corpus-v1",
    state: "EMPTY",
    sources: [],
    databases: [],
    preview: { identified: 0, duplicates: 0, unique_studies: 0 },
    accepted: null,
    from_discovery: false,
    limits: { max_source_bytes: 50 * 1024 * 1024, label_max_length: 40 },
    staging_refused: null,
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://ui.test").pathname.replace(/^\/api\/console/, "");
      const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
      if ((init?.method ?? "GET") === "GET" && path === "/api/v1/screening/corpus") return json(corpus);
      return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
    }),
  );
  vi.stubGlobal("location", { ...window.location, search: "?return=discovery", assign: vi.fn(), reload: vi.fn() });
}

export type GuidanceScreen = {
  /** The screen's name in the M10d record. */
  name: string;
  /** The state, in the record's words. */
  state: string;
  /** False for a state added after the before/after word count (it has no before). */
  measure?: boolean;
  mount: (locale?: Locale) => Promise<void>;
};

/**
 * Waits until the page has drawn what the fake engine answered. Every mount first waits for a text
 * that only the engine's answer draws; the fakes answer at once, so what is left are promise
 * callbacks and the renders they cause. Each turn flushes them inside `act` with a zero-delay timer;
 * the page is settled when three turns in a row leave the word count unchanged. No wall-clock wait
 * (H-test-diet replaced the former 150 ms loop, which cost up to 3 s per state under load).
 */
async function settle() {
  let last = -1;
  let unchanged = 0;
  for (let turn = 0; turn < 200 && unchanged < 3; turn++) {
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    const now = visibleWords().length;
    unchanged = now === last ? unchanged + 1 : 0;
    last = now;
  }
}

const text = async (value: string | RegExp) => {
  await screen.findAllByText(value, {}, { timeout: 5000 });
  await settle();
};

export const SCREENS: GuidanceScreen[] = [
  {
    name: "01 Scope",
    state: "a complete draft",
    mount: async (locale = "en") => {
      inceptionSetUp({ draft: completeDraft() });
      render(<InceptionScope locale={locale} />);
      await settle();
      await screen.findAllByRole("textbox");
      await settle();
    },
  },
  {
    name: "02 Explore (first search)",
    state: "a complete draft, never searched",
    mount: async (locale = "en") => {
      inceptionSetUp({ draft: completeDraft() });
      render(<InceptionExplore locale={locale} />);
      await screen.findAllByRole("heading", {}, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "02 Explore (pool)",
    state: "after the first search, 14 papers",
    mount: async (locale = "en") => {
      probed();
      render(<InceptionExplore locale={locale} />);
      await screen.findAllByRole("table", {}, { timeout: 5000 }).catch(() => undefined);
      await settle();
    },
  },
  {
    name: "02 Explore (thin pool)",
    state: "after a first search that found 7 papers",
    mount: async (locale = "en") => {
      probed({ outcomes: ["thin"] });
      render(<InceptionExplore locale={locale} />);
      await screen.findAllByRole("table", {}, { timeout: 5000 }).catch(() => undefined);
      await settle();
    },
  },
  {
    name: "02 Explore (one database found nothing)",
    state: "after a first search where arXiv answered with nothing",
    measure: false,
    mount: async (locale = "en") => {
      probed({ outcomes: ["someEmpty"] });
      render(<InceptionExplore locale={locale} />);
      await screen.findAllByRole("table", {}, { timeout: 5000 }).catch(() => undefined);
      await settle();
    },
  },
  {
    name: "03 Direction",
    state: "after the first search, three directions",
    mount: async (locale = "en") => {
      probed();
      render(<InceptionDirection locale={locale} />);
      await screen.findByRole("radiogroup", {}, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "04 Shape",
    state: "a draft with a topic only",
    mount: async (locale = "en") => {
      inceptionSetUp({ draft: { topic: "weed detection" } });
      render(<InceptionShape locale={locale} />);
      await screen.findAllByRole("radio", {}, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "05 Criteria",
    state: "a complete draft, nothing decided",
    mount: async (locale = "en") => {
      inceptionSetUp({ draft: completeDraft() });
      render(<InceptionCriteria locale={locale} />);
      await screen.findAllByRole("listitem", {}, { timeout: 5000 });
      // The page asks the engine for its criteria 200 ms after the draft is read; the block is drawn from that answer.
      await waitFor(() => expect(document.querySelector("[data-criteria-block]")).not.toBeNull(), { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "05 Criteria (pool)",
    state: "a complete draft with two concepts, after the first search",
    measure: false,
    mount: async (locale = "en") => {
      probed({}, completeDraft({ concepts: [{ concept: "weed detection", synonyms: [] }, { concept: "edge device", synonyms: [] }] }));
      render(<InceptionCriteria locale={locale} />);
      await screen.findAllByRole("listitem", {}, { timeout: 5000 });
      // The page asks the engine for its criteria 200 ms after the draft is read; the block is drawn from that answer.
      await waitFor(() => expect(document.querySelector("[data-criteria-block]")).not.toBeNull(), { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "06 Review",
    state: "a complete draft, every criterion decided",
    mount: async (locale = "en") => {
      inceptionSetUp({ draft: decided() });
      render(<InceptionReview locale={locale} />);
      await screen.findAllByRole("listitem", {}, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "07 Done",
    state: "the workspace created",
    mount: async (locale = "en") => {
      inceptionSetUp({ draft: { title: "Weed review" }, emitted: emitted() });
      render(<InceptionDone locale={locale} />);
      await screen.findAllByRole("heading", {}, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "discovery entry",
    state: "one finished run",
    mount: async (locale = "en") => {
      discoverySetUp({ runs: 1 });
      render(<DiscoveryOverview locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "01 Plan",
    state: "the protocol's plan",
    mount: async (locale = "en") => {
      discoverySetUp();
      render(<DiscoveryPlan locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "02 Recall",
    state: "no recall check yet",
    mount: async (locale = "en") => {
      discoverySetUp();
      render(<DiscoveryRecall locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "03 Harvest",
    state: "ready, no run yet",
    mount: async (locale = "en") => {
      discoverySetUp();
      render(<DiscoveryHarvest locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "04 Import",
    state: "the discovery visit, nothing staged",
    mount: async (locale = "en") => {
      importFake();
      render(<ScreeningImport locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "05 Duplicates",
    state: "one finished run",
    mount: async (locale = "en") => {
      discoverySetUp({ runs: 1 });
      render(<DiscoveryDedup locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "06 Report",
    state: "one finished run, a rate-limited database",
    mount: async (locale = "en") => {
      discoverySetUp({ runs: 1, failedLeg: { provider: "pubmed", code: "PROVIDER_RATE_LIMITED", error: "HTTPStatusError: 429" } });
      render(<DiscoveryReport locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "08 Hand-off",
    state: "one finished run, not accepted",
    mount: async (locale = "en") => {
      discoverySetUp({ runs: 1 });
      render(<DiscoveryHandoff locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
  {
    name: "09 Chase",
    state: "screening published, no chase yet",
    mount: async (locale = "en") => {
      discoverySetUp({ runs: 1, accepted: true, published: true });
      render(<DiscoveryChase locale={locale} />);
      await screen.findAllByRole("heading", { level: 1 }, { timeout: 5000 });
      await settle();
    },
  },
];

export { text as waitForText };
