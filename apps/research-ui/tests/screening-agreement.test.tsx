import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AGREEMENT_COPY, ScreeningAgreement } from "@/components/screening-agreement";
import { SUPPORTED_LOCALES } from "@/i18n";

/**
 * Agreement with the agent (spec 07) in jsdom. Every number is the engine's
 * `GET /agreement`; the screen prints it and never asks for a draft.
 */

const AGREEMENT = {
  decided_with_proposal: 49,
  decided_after_seeing_the_draft: 2,
  agreement_pct: 95.9,
  table_2x2: { both_include: 10, you_include_agent_exclude: 1, you_exclude_agent_include: 1, both_exclude: 37 },
  splits_by_criterion: [{ criterion_id: "INC-03", n: 2 }],
  unclear_either_side: 0,
  kappa: null,
  kappa_note: "needs a second human screener",
};
const SUMMARY = { total: 60, decided: 51, by_outcome: { INCLUDE: 11, EXCLUDE: 40, MAYBE: 0 }, agent_proposed: 60, needs_you: 9, conflicts: 0, lanes: { agent: 60, you: 51, second_screener: "PARKED" } };
const SETTINGS = { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" };

function engine(options: { summary?: unknown; settings?: unknown } = {}) {
  const paths: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console/api/v1/screening", "");
      paths.push(path);
      const ok = (b: unknown) => new Response(JSON.stringify(b), { status: 200, headers: { "content-type": "application/json" } });
      if (path === "/agreement") return ok(AGREEMENT);
      if (path === "/summary") return ok(options.summary ?? SUMMARY);
      if (path === "/settings") return ok(options.settings ?? SETTINGS);
      return new Response(JSON.stringify({ detail: { code: "NOT_FOUND" } }), { status: 404 });
    }),
  );
  return paths;
}

afterEach(() => vi.unstubAllGlobals());

describe("agreement.no-kappa-value", () => {
  it("prints the server's numbers and a greyed kappa with no value", async () => {
    engine();
    render(<ScreeningAgreement locale="en" />);
    await screen.findByText("You and the agent agreed on 95.9% of records; it would have dropped 1 of your includes.");
    const kappa = document.querySelector("[data-kappa]")!;
    expect(kappa).toHaveAttribute("aria-disabled", "true");
    expect(kappa).toHaveTextContent("needs a second human screener · not production");
    expect(kappa.textContent).not.toMatch(/\d/);
    expect(document.querySelector('[data-cell="both_exclude"]')).toHaveTextContent("37");
    expect(screen.getAllByText("of 51 decided so far")).toHaveLength(4);
    expect(screen.getByText(/2 records were decided with the draft already in view/)).toBeInTheDocument();
  });
});

describe("agreement.sample-only-with-optin", () => {
  it("needs no sample when you saw every record", async () => {
    engine();
    render(<ScreeningAgreement locale="en" />);
    expect(await screen.findByText("You saw every record. No sample needed.")).toBeInTheDocument();
  });

  it("asks for the sample check when AI-agreed exclusion is on", async () => {
    engine({ settings: { ...SETTINGS, mode: "ai_agreed_exclusion", sample_audit_size: 60 } });
    render(<ScreeningAgreement locale="en" />);
    expect(await screen.findByText(/AI-agreed exclusion is on/)).toBeInTheDocument();
    expect(document.querySelector('[data-sample="ai_agreed_exclusion"]')).toHaveTextContent("60");
  });
});

describe("agreement.no-undecided-leak", () => {
  it("never reads a draft, and shows the empty state before any decision", async () => {
    const paths = engine({ summary: { ...SUMMARY, decided: 0 } });
    render(<ScreeningAgreement locale="en" />);
    expect(await screen.findByText("Decide some records first.")).toBeInTheDocument();
    expect(paths.some((p) => /\/proposal$/.test(p))).toBe(false);
    expect(document.querySelector('[data-cell="both_include"]')).toBeNull();
  });

  it("points to the run screen when there are no proposals", async () => {
    engine({ summary: { ...SUMMARY, agent_proposed: 0 } });
    render(<ScreeningAgreement locale="en" />);
    expect(await screen.findByRole("link", { name: "Run agent proposals" })).toHaveAttribute("href", "/en/screening/proposals");
  });
});

describe("agreement copy", () => {
  it("has every key in every locale", () => {
    const keys = Object.keys(AGREEMENT_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(AGREEMENT_COPY[locale]).sort()).toEqual(keys);
  });
});
