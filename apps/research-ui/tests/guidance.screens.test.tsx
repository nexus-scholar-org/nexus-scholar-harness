import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionReview } from "@/components/inception-review";
import { completeDraft, proofId } from "./fixtures/inception-engine";
import { setUp as inceptionSetUp } from "./inception-helpers";
import { SCREENS } from "./guidance-screens";
import { visibleWords } from "./guidance-words";

/**
 * M10d, the per-screen definition of done (`docs/roadmap/milestones/M10d-lighter-screens.md`):
 * for each screen, the texts moved behind a hint (`data-hint-body`, closed), the
 * sentences removed, the one primary button, the Recommended mark and the folds.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const mount = async (name: string) => {
  const s = SCREENS.find((x) => x.name === name);
  if (!s) throw new Error(`no screen ${name}`);
  await s.mount();
};

/** The keys behind a closed hint on the page. */
const hinted = () => new Set([...document.querySelectorAll<HTMLElement>("[data-hint-body]")].map((el) => (el.hidden ? el.dataset.hintBody : `OPEN:${el.dataset.hintBody}`)));
const visible = () => visibleWords().join(" ");
const primaries = () => [...document.querySelectorAll<HTMLElement>('button[data-variant="primary"], a[data-variant="primary"]')];
const folds = () => [...document.querySelectorAll<HTMLDetailsElement>("details[data-fold]")];
const foldTitles = () => folds().map((d) => d.querySelector("summary h2")?.textContent?.trim());

function expectHints(keys: string[]) {
  const on = hinted();
  for (const key of keys) expect(on, key).toContain(key);
}

function expectGone(sentences: string[]) {
  const all = document.body.textContent ?? "";
  for (const sentence of sentences) expect(all, sentence).not.toContain(sentence);
}

describe("guidance.screens", () => {
  describe("02 Explore", () => {
    it("first search: the mode and the query help are hints; one primary button", async () => {
      await mount("02 Explore (first search)");
      expectHints(["explore.mode.help", "explore.query.help", "explore.picker.orderHelp", "plan.limits.s2Key.help"]);
      expect(visible()).not.toContain("Semantic search matches meaning");
      expect(primaries().map((b) => b.textContent)).toEqual(["Search the literature"]);
      expectGone(["Pool health first, in plain words with the raw value underneath."]);
    });

    it("pool: the notes are hints, topics, papers and databases are folded and closed, one primary button", async () => {
      await mount("02 Explore (pool)");
      expectHints(["explore.mode.help", "explore.pool.refreshNote", "explore.tile.echo.body", "explore.concepts.note", "explore.legs.neverEmpty", "explore.papers.note"]);
      expect(visible()).not.toContain("A refresh runs the same search again");
      expect(foldTitles()).toEqual(expect.arrayContaining([expect.stringContaining("OpenAlex topics ·"), "Papers · 14", "Databases asked · 4"]));
      expect(folds().every((d) => !d.open)).toBe(true);
      // The pool's own numbers and draft label stay in the visible flow.
      expect(visible()).toContain("Heuristic reading not yet yours");
      expect(screen.getByRole("heading", { name: "Pool · 14 papers" })).toBeVisible();
      expect(primaries().map((b) => b.textContent)).toEqual(["See 3 directions"]);
      expect(document.querySelector("[data-recommended]")).toBeNull();
    });

    it("thin pool: semantic search is marked Recommended with its source, nothing is chosen for the researcher", async () => {
      await mount("02 Explore (thin pool)");
      const tile = document.querySelector('[data-tile="size"]') as HTMLElement;
      expect(within(tile).getByText("Recommended · pool size check")).toBeInTheDocument();
      expect(within(tile).getByRole("button", { name: "Search again with semantic search" })).toBeInTheDocument();
      expectGone(["Widening the years or using semantic search usually helps."]);
      expect(tile.textContent).toContain("are often fragments");
      const semantic = screen.getAllByRole("radio", { name: "Semantic" });
      expect(semantic.every((r) => !(r as HTMLInputElement).checked)).toBe(true);
      expect(document.activeElement).not.toBe(within(tile).getByRole("button", { name: "Search again with semantic search" }));
    });
  });

  describe("06 Review", () => {
    it("the title help, the seeds caption and the fingerprint note are hints; files and fingerprint are behind Details; one primary button", async () => {
      await mount("06 Review");
      expectHints(["review.reviewTitleHelp", "review.fingerprintNote"]);
      expect(screen.getByLabelText("Title of the review")).toHaveAccessibleDescription("The workspace folder is named after the title.");
      expectGone(["Nothing is written until you create the workspace."]);
      const files = document.querySelector("details[data-review-files]") as HTMLDetailsElement;
      expect(files.open).toBe(false);
      expect(files.querySelector("summary")?.textContent).toBe("Details · Files that will be written");
      expect(files.querySelector("[data-fingerprint]")).not.toBeNull();
      // The gate still states the folder in the visible flow.
      expect(document.querySelector("section.border-brand")?.textContent).toContain("weed");
      expect(primaries().map((b) => b.textContent)).toEqual(["Create the workspace"]);
    });

    it("marks the first open check's fix Recommended with its check id, and only that one", async () => {
      const rows = () => [
        { check_id: "REVIEW_TARGET_HAS_WORKSPACE", step: "review", level: "warning" as const, dismissible: true, action: { kind: "field", step: "review", field: "title" } },
        { check_id: "CRITERIA_FEW_INCLUSIONS", step: "criteria", level: "warning" as const, dismissible: true, action: { kind: "field", step: "criteria", field: "criteria_decisions" } },
      ];
      inceptionSetUp({ draft: completeDraft({ criteria_decisions: { [proofId()]: true } }), existing: "workspace", checks: rows });
      render(<InceptionReview locale="en" />);
      const first = await screen.findByText("Recommended · check REVIEW_TARGET_HAS_WORKSPACE", {}, { timeout: 5000 });
      expect(first.closest("[data-check]")?.getAttribute("data-check")).toBe("REVIEW_TARGET_HAS_WORKSPACE");
      expect(document.querySelectorAll("[data-recommended]")).toHaveLength(1);
      // Nothing is pressed or focused for the researcher; Create keeps its own rules.
      expect(document.activeElement?.closest("[data-check]")).toBeNull();
    });

    it("the skipped direction says it once", async () => {
      await mount("06 Review");
      expectGone(["The protocol will say it was not grounded in a direction."]);
    });
  });

  describe("inception frame", () => {
    it("how drafts work is a hint beside the saved status, on every step", async () => {
      for (const name of ["01 Scope", "04 Shape", "05 Criteria"]) {
        await mount(name);
        expectHints(["nothingWritten"]);
        expect(visible()).not.toContain("Nothing is written to a workspace before Review");
        cleanup();
        vi.unstubAllGlobals();
      }
    });
  });

  describe("01 Scope", () => {
    it("the three field helps are hints read with their fields; one lede sentence; one primary button", async () => {
      await mount("01 Scope");
      expectHints(["scope.topicHelp", "scope.toYearHelp", "scope.languagesHelp"]);
      expect(screen.getByLabelText("Languages", { selector: "input" })).toHaveAccessibleDescription("Language codes separated by commas, for example en, fr.");
      expectGone(["The engine reads the topic to suggest a lens on the next step."]);
      expect(primaries().map((b) => b.textContent)).toEqual(["Continue to Explore"]);
    });
  });

  describe("03 Direction", () => {
    it("the order, anchor, narrower, own-phrase and seeds notes are hints; the duplicate sentences are removed; nothing is marked", async () => {
      await mount("03 Direction");
      expectHints(["direction.lede.order", "direction.card.note"]);
      expectGone(["You can also write your own, or go on without one."]);
      expect(document.querySelector('[data-copy="lede"]')?.textContent).toContain("These directions come from phrases");
      expect(visible()).not.toContain("which is evidence, not a recommendation");
      // Nothing is preselected and nothing is Recommended on Direction (03-guidance rule 3).
      expect(screen.getAllByRole("radio").every((r) => !(r as HTMLInputElement).checked)).toBe(true);
      expect(document.querySelector("[data-recommended]")).toBeNull();
      // Before a choice the reason stays on the page.
      expect(visible()).toContain("Choose a direction first.");
      expect(primaries().map((b) => b.textContent)).toEqual([expect.stringMatching(/^Pursue/)]);
    });
  });

  describe("04 Shape", () => {
    it("marks the leaning lens Recommended with its source, the why on the legend's hint, nothing chosen; field helps are hints", async () => {
      await mount("04 Shape");
      const card = (await screen.findByText("Design Science")).closest("label")!;
      expect(within(card).getByText("Recommended · word scan of your topic")).toBeInTheDocument();
      expect(within(card).queryByRole("button")).toBeNull();
      expect(screen.getAllByRole("radio").every((r) => !(r as HTMLInputElement).checked)).toBe(true);
      expectHints(["shape.leaningNote", "shape.unitHelp", "shape.proofHelp", "shape.outOfScopeHelp", "shape.planned.hint"]);
      expectGone(["A word scan of your topic leans one way; that lens is marked."]);
      expect(screen.getByRole("button", { name: "Continue to concepts and criteria" })).toBeDisabled();
      expect(primaries().map((b) => b.textContent)).toEqual(["Continue to concepts and criteria"]);
      for (const b of document.querySelectorAll("[data-hint-button]")) expect(b.closest("label")).toBeNull();
    });
  });

  describe("05 Criteria", () => {
    it("one edit hint on each list heading, not one per criterion; the per-row sentence is removed; the parked notes stay", async () => {
      await mount("05 Criteria");
      expectHints(["criteria.editHint"]);
      expect(document.querySelectorAll('[data-hint-body="criteria.editHint"]').length).toBeLessThanOrEqual(2);
      expectGone(["Written by the wizard: not in the protocol unless you accept it.", "Every criterion is shown word for word with where it came from."]);
      expect(primaries().map((b) => b.textContent)).toEqual(["Continue to review"]);
    });
  });

  describe("07 Done", () => {
    it("one lede sentence, the next step; one primary action", async () => {
      await mount("07 Done");
      expectGone(["The protocol and the criteria are written, and GENESIS is in the audit journal."]);
      expect(visible()).toContain("Next, open the workspace and import your search results.");
    });
  });
});
