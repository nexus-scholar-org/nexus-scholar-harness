import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningAdopted } from "@/components/screening-adopted";
import { ScreeningAgreement } from "@/components/screening-agreement";
import { ScreeningExport } from "@/components/screening-export";
import { PUBLISH_COPY, ScreeningPublish } from "@/components/screening-publish";
import { formatNumber, SUPPORTED_LOCALES } from "@/i18n";
import { ADOPTION_COPY, adoptionText } from "@/lib/adoption-copy";
import { CHARTING_COPY } from "@/lib/charting-copy";

/**
 * H-adopted-decisions-disclosure (decision 2026-11-22) in jsdom: the declaration screen
 * offers the engine's candidates and sends nothing until the reviewer confirms; Agreement,
 * Publish, Export and charting state the declared decisions in en, fr and ar with the
 * decided phrase, and "You saw every record" is never shown once a declaration exists.
 */

const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;
const PREVIEW = JSON.parse(readFileSync(`${FIXTURES}prisma_preview.json`, "utf-8")).response.body;

const json = (b: unknown, code = 200) => new Response(JSON.stringify(b), { status: code, headers: { "content-type": "application/json" } });
const OUTCOMES0 = { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 };

function adoption(extra: Record<string, unknown> = {}) {
  return {
    phrase: "stored from the agent's draft without being read one by one",
    declared: 0,
    declared_by_outcome: OUTCOMES0,
    candidates: 0,
    undeclared_candidates: 0,
    undeclared_by_outcome: OUTCOMES0,
    declarations: [],
    samples: [],
    sample_owed: false,
    sample_owed_size: null,
    no_sample_drawn: false,
    integrity: { removed: [], unconfirmed: [] },
    ...extra,
  };
}

const CANDIDATES = [
  { event_id: "e-1", study_id: "STU-1", outcome: "EXCLUDE", note: "Adopted in bulk from the agent's draft", declared: false },
  { event_id: "e-2", study_id: "STU-2", outcome: "EXCLUDE", note: "Adopted in bulk from the agent's draft", declared: false },
  { event_id: "e-3", study_id: "STU-3", outcome: "INCLUDE", note: "Adopted in bulk from the agent's draft", declared: false },
];
const OFFERED = adoption({ candidates: 3, undeclared_candidates: 3, undeclared_by_outcome: { INCLUDE: 1, EXCLUDE: 2, MAYBE: 0 }, candidate_list: CANDIDATES, declared_study_ids: [] });
const DECLARED = adoption({
  declared: 996,
  declared_by_outcome: { INCLUDE: 86, EXCLUDE: 586, MAYBE: 324 },
  declarations: [
    { declaration_id: "ADD-1", declared_by: "researcher:local", declared_at: "2026-11-23T10:00:00Z", note: null, counts: { INCLUDE: 86, EXCLUDE: 586, MAYBE: 324 }, sample: { size: 50, seed: 20261120, study_ids: ["STU-9"], how: "given" } },
  ],
  samples: [{ declaration_id: "ADD-1", size: 50, seed: 20261120, study_ids: ["STU-9"], read: false, changed: null, recorded_at: null }],
  sample_owed: true,
  sample_owed_size: 50,
});

type Call = { method: string; path: string; body: unknown };

function engine(routes: Record<string, unknown>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname.replace("/api/console", "");
      const method = (init?.method ?? "GET").toUpperCase();
      calls.push({ method, path, body: init?.body ? JSON.parse(String(init.body)) : null });
      const answer = routes[`${method} ${path}`] ?? routes[path];
      if (answer instanceof Response) return answer;
      if (typeof answer === "function") return json((answer as () => unknown)());
      return answer === undefined ? json({ detail: { code: "NOT_FOUND", message: path } }, 404) : json(answer);
    }),
  );
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const S = "/api/v1/screening";

// --- the copy: one phrase, three languages --------------------------------------------

describe("adoption.copy", () => {
  it("has every key in en, fr and ar, and the decided phrase in English", () => {
    const keys = Object.keys(ADOPTION_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(ADOPTION_COPY[locale]).sort()).toEqual(keys);
    expect(ADOPTION_COPY.en.phraseOne).toBe("Stored from the agent's draft without being read one by one");
    expect(ADOPTION_COPY.en.notCounted).toContain("stored from the agent's draft without being read one by one");
    expect(CHARTING_COPY.en["charting.study.taAdopted"]).toBe("Stored from the agent's draft without being read one by one");
    expect(PUBLISH_COPY.en["check.human_provenance"]).toBe("Every decision is recorded as the reviewer's");
    expect(PUBLISH_COPY.en["check.adopted_decisions_declared"]).toBe("Decisions stored from drafts are declared");
    for (const locale of SUPPORTED_LOCALES) {
      expect(CHARTING_COPY[locale]["charting.study.taAdopted"]).toBeTruthy();
      expect(PUBLISH_COPY[locale].look).toBeTruthy();
    }
  });

  it("pins the fr and ar wording of the phrase", () => {
    expect(ADOPTION_COPY.fr.phraseOne).toBe("Enregistrée depuis le brouillon de l'agent sans être lue une à une");
    expect(ADOPTION_COPY.ar.phraseOne).toBe("حُفظ من مسودة الوكيل دون قراءته واحدًا واحدًا");
    expect(adoptionText("fr", "sampleOwed", { k: 50 })).toBe("Un échantillon de 50 exclusions adoptées est dû.");
    expect(adoptionText("ar", "sampleOwed", { k: 50 })).toBe("عيّنة من 50 استبعادًا معتمَدًا مستحقة.");
  });
});

// --- the declaration screen ------------------------------------------------------------

describe("adoption.screen", () => {
  it("offers the candidates and sends nothing until the reviewer confirms", async () => {
    const calls = engine({ [`GET ${S}/adoption-declarations`]: OFFERED });
    render(<ScreeningAdopted locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Decisions stored from the agent's draft" });
    expect(screen.getByText(/3 decisions have a note that says they were adopted or stored in bulk/)).toBeInTheDocument();
    expect(calls.filter((c) => c.method === "POST")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Declare 3 decisions" }));
    const dialog = await screen.findByRole("alertdialog");
    const record = screen.getByRole("button", { name: "Record the declaration" });
    expect(record).toBeDisabled(); // not until "I did not read these records one by one" is ticked
    expect(dialog).toHaveTextContent("Declare 3 decisions as stored from the agent's draft without being read one by one?");
    expect(calls.filter((c) => c.method === "POST")).toHaveLength(0);
  });

  it("sends the selected events with confirm, and the sample when a size is given", async () => {
    let declared = false;
    const calls = engine({
      [`GET ${S}/adoption-declarations`]: () => (declared ? DECLARED : OFFERED),
      [`POST ${S}/adoption-declarations`]: () => {
        declared = true;
        return { declaration: DECLARED.declarations[0], state: DECLARED };
      },
    });
    render(<ScreeningAdopted locale="en" />);
    await screen.findByText(/3 decisions have a note/);
    // The reviewer unselects one record from the list.
    fireEvent.click(screen.getByText("List them"));
    const third = document.querySelector('[data-candidate="STU-3"] input[type="checkbox"]') as HTMLInputElement;
    fireEvent.click(third);
    expect(screen.getByText("2 selected")).toBeInTheDocument();
    fireEvent.change(document.querySelector("[data-sample-size]")!, { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Declare 2 decisions" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "I did not read these records one by one." }));
    fireEvent.click(screen.getByRole("button", { name: "Record the declaration" }));
    await screen.findByText("Recorded.");
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.path).toBe(`${S}/adoption-declarations`);
    const sent = post.body as { event_ids: string[]; confirm: boolean; sample: { size: number; seed: number } };
    expect(sent.event_ids).toEqual(["e-1", "e-2"]);
    expect(sent.confirm).toBe(true);
    expect(sent.sample.size).toBe(1);
    expect(Number.isInteger(sent.sample.seed)).toBe(true);
    await waitFor(() => expect(document.querySelector('[data-declaration="ADD-1"]')).not.toBeNull());
    expect(document.querySelector('[data-sample="owed"]')).toHaveTextContent("Sample of 50 (seed 20261120)");
  });

  it("refuses a sample larger than the selected exclusions before anything is sent", async () => {
    engine({ [`GET ${S}/adoption-declarations`]: OFFERED });
    render(<ScreeningAdopted locale="en" />);
    await screen.findByText(/3 decisions have a note/);
    fireEvent.change(document.querySelector("[data-sample-size]")!, { target: { value: "3" } });
    expect(screen.getByRole("button", { name: "Declare 3 decisions" })).toBeDisabled();
  });

  it.each(SUPPORTED_LOCALES)("renders in %s", async (locale) => {
    engine({ [`GET ${S}/adoption-declarations`]: OFFERED });
    render(<ScreeningAdopted locale={locale} />);
    await screen.findByRole("heading", { level: 1, name: ADOPTION_COPY[locale].title });
  });
});

// --- Agreement --------------------------------------------------------------------------

const AGREEMENT = {
  decided_with_proposal: 66,
  decided_after_seeing_the_draft: 0,
  agreement_pct: 97,
  table_2x2: { both_include: 1, you_include_agent_exclude: 1, you_exclude_agent_include: 0, both_exclude: 32 },
  splits_by_criterion: [],
  unclear_either_side: 32,
  kappa: null,
  kappa_note: "needs a second human screener",
};
const SUMMARY = { total: 1062, decided: 1062, by_outcome: { INCLUDE: 0, EXCLUDE: 0, MAYBE: 0 }, agent_proposed: 1062, needs_you: 0, conflicts: 0, lanes: { agent: 1062, you: 1062, second_screener: "PARKED" } };
const SETTINGS = { blinding: "reveal_after_decision", mode: "human_sees_every_record", sample_audit_size: null, screener_id: "researcher:local" };

describe("adoption.agreement", () => {
  it.each(SUPPORTED_LOCALES)("states the declared decisions and the owed sample, never 'You saw every record' (%s)", async (locale) => {
    engine({ [`${S}/agreement`]: { ...AGREEMENT, adoption: DECLARED }, [`${S}/summary`]: SUMMARY, [`${S}/settings`]: SETTINGS });
    render(<ScreeningAgreement locale={locale} />);
    await waitFor(() => expect(document.querySelector("[data-adoption-not-counted]")).not.toBeNull());
    expect(document.querySelector("[data-adoption-not-counted]")).toHaveTextContent(adoptionText(locale, "notCounted", { n: formatNumber(locale, 996) }));
    const box = document.querySelector('[data-sample="declared"]')!;
    expect(box).toHaveTextContent(adoptionText(locale, "sampleOwed", { k: formatNumber(locale, 50) }));
    expect(document.body.textContent).not.toContain("You saw every record");
    expect(document.body.textContent).not.toContain("Vous avez vu chaque notice");
    expect(document.body.textContent).not.toContain("رأيت كل سجل");
  });

  it("does not say 'You saw every record' while candidates are undeclared", async () => {
    engine({ [`${S}/agreement`]: { ...AGREEMENT, adoption: adoption({ candidates: 3, undeclared_candidates: 3 }) }, [`${S}/summary`]: SUMMARY, [`${S}/settings`]: SETTINGS });
    render(<ScreeningAgreement locale="en" />);
    await waitFor(() => expect(document.querySelector('[data-adoption-sample="undeclared"]')).not.toBeNull());
    expect(document.body.textContent).not.toContain("You saw every record");
  });

  it("says a sample is owed even when none was drawn", async () => {
    engine({
      [`${S}/agreement`]: { ...AGREEMENT, adoption: adoption({ declared: 2, declared_by_outcome: { INCLUDE: 1, EXCLUDE: 1, MAYBE: 0 }, sample_owed: true, no_sample_drawn: true }) },
      [`${S}/summary`]: SUMMARY,
      [`${S}/settings`]: SETTINGS,
    });
    render(<ScreeningAgreement locale="en" />);
    expect(await screen.findByText("A sample of the adopted exclusions is owed; none has been drawn yet.")).toBeInTheDocument();
    expect(screen.getByText(/2 decisions were stored from the agent's draft without being read one by one; they are not counted here./)).toBeInTheDocument();
  });

  it("states what a read sample found", async () => {
    engine({
      [`${S}/agreement`]: { ...AGREEMENT, adoption: { ...DECLARED, sample_owed: false, sample_owed_size: null, samples: [{ ...(DECLARED.samples as Record<string, unknown>[])[0], read: true, changed: 2 }] } },
      [`${S}/summary`]: SUMMARY,
      [`${S}/settings`]: SETTINGS,
    });
    render(<ScreeningAgreement locale="en" />);
    expect(await screen.findByText("A sample of 50 adopted exclusions was read: you changed 2.")).toBeInTheDocument();
  });
});

// --- Publish ----------------------------------------------------------------------------

const BATCHES = { shape: "ui07.screening-batches-v1", run_id: "RUN-1", count: 1, batches: [{ batch_index: 1, batch_file: "batch_001.json", items: 3, decisions_file: "batch_001_decisions.json", decisions_count: 3, collected: false, coverage: "COMPLETE", unresolved_rows: [] }], missing: [] };
const REVIEW = { shape: "ui07.review-state-v1", batch_index: 1, recommendation: { present: false }, resolution: { resolved: 3, total: 3, unresolved_rows: [] }, override: { superseded: false }, review: { present: true, approval_fingerprint: "sha256:x" }, deferral: { present: false }, missing: [] };

function publishEngine(preview: unknown) {
  return engine({
    [`${S}/prisma/preview`]: preview,
    [`${S}/settings`]: { blinding: "reveal_after_decision" },
    [`${S}/ui/batches`]: BATCHES,
    [`${S}/ui/batches/review`]: { shape: "ui07.batch-reviews-v1", count: 1, reviews: [REVIEW] },
    [`${S}/ui/batch/1/review`]: REVIEW,
    [`${S}/approver`]: { name: "Researcher", set_at: "2026-11-06T13:00:00Z", basis: "typed-name" },
  });
}

describe("adoption.publish", () => {
  const look = {
    ...PREVIEW,
    checks: [
      ...PREVIEW.checks.filter((c: { name: string }) => c.name !== "adopted_decisions_declared"),
      { name: "adopted_decisions_declared", ok: false, advisory: true, detail: "3 decisions have a note that says adopted or stored in bulk and are not declared" },
    ],
    adoption: adoption({ candidates: 3, undeclared_candidates: 3 }),
  };

  it("shows Look at this, does not block, and links to the declaration screen", async () => {
    publishEngine(look);
    render(<ScreeningPublish locale="en" />);
    const row = await waitFor(() => {
      const found = document.querySelector('[data-check="adopted_decisions_declared"]');
      expect(found).not.toBeNull();
      return found!;
    });
    expect(row).toHaveTextContent("Look at this");
    expect(row).toHaveTextContent("Decisions stored from drafts are declared");
    expect(document.querySelector('[data-check="human_provenance"]')).toHaveTextContent("Every decision is recorded as the reviewer's");
    // Not blocked: the title is the ready one, not the blocked one.
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(PUBLISH_COPY.en.title);
    expect(document.querySelector("[data-adoption-look]")).toHaveTextContent("Does not block publishing.");
    expect(screen.getByRole("link", { name: "Declare decisions stored from drafts" })).toHaveAttribute("href", "/en/screening/adopted");
  });

  it("states the owed sample once declared", async () => {
    publishEngine({ ...PREVIEW, adoption: DECLARED });
    render(<ScreeningPublish locale="fr" />);
    await waitFor(() => expect(document.querySelector("[data-adoption-declared]")).not.toBeNull());
    expect(document.querySelector("[data-adoption-declared]")).toHaveTextContent("la publication ne l'attend pas");
  });
});

// --- Export ----------------------------------------------------------------------------

describe("adoption.export", () => {
  const METHODS = {
    generation_id: "GEN-1",
    generation_fingerprint: "sha256:f",
    published_at: "2026-11-21T10:00:00Z",
    language: "en",
    paragraph: "One reviewer read 66 records one by one; 996 decisions were stored from the agent's draft without being read one by one (586 excluded, 86 included and 324 unclear).",
    figures: {
      identified: 1062, duplicates_removed: 0, screened: 1062, excluded: 586, unclear: 443, included: 33, exclusion_reasons: {},
      adoption: { read_one_by_one: 66, stored_from_drafts: 996, by_outcome: { EXCLUDE: 586, INCLUDE: 86, MAYBE: 324 }, samples: [{ size: 50, seed: 20261120, read: false, changed: null }], declared_on: ["2026-11-23"], declared_after_publication: true, phrase: "stored from the agent's draft without being read one by one" },
    },
    sources: [],
    caveats: [],
    not_stated: [],
  };

  it.each(SUPPORTED_LOCALES)("shows the declared figures with their labels and the after-publication note (%s)", async (locale) => {
    engine({
      "/api/v1/ui/publication-status": { shape: "ui07.publication-status-v1", status: "CURRENT", code: null, generation_id: "GEN-1", outputs: {}, message: "", details: {} },
      [`${S}/methods`]: METHODS,
      [`${S}/prisma/preview`]: PREVIEW,
    });
    render(<ScreeningExport locale={locale} />);
    await waitFor(() => expect(document.querySelector("[data-methods-adoption]")).not.toBeNull());
    const section = document.querySelector("[data-methods-adoption]")!;
    expect(section).toHaveTextContent(ADOPTION_COPY[locale].exportTitle);
    expect(section).toHaveTextContent(ADOPTION_COPY[locale].exportRead);
    expect(section).toHaveTextContent(ADOPTION_COPY[locale].exportStored);
    expect(section).toHaveTextContent(ADOPTION_COPY[locale].exportSampleUnread);
    expect(document.querySelector("[data-adoption-after]")).toHaveTextContent(ADOPTION_COPY[locale].exportAfter);
  });
});
