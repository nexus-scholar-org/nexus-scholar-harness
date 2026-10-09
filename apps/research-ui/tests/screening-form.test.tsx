import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningForm } from "@/components/screening-form";
import { ScreeningPage } from "@/components/screening-page";
import { SUPPORTED_LOCALES, formatNumber, translate, type Locale } from "@/i18n";
import { demoScreeningRecord } from "@/lib/mock-screening";
import { CATALOGS } from "@/messages";

/**
 * The screening workspace, in process (packet UI-04).
 *
 * Three groups of claims, in the order the packet states them:
 *
 * 1. The **fixture** carries no verdict and no identifier — checked
 *    mechanically here because `lib/mock-screening.ts` promises exactly that,
 *    and a promise only a reader can check is a promise nobody checks.
 * 2. The **form** offers three distinguishable choices, preselects none,
 *    requires a reason for exclusion with a non-live message, and submits
 *    nowhere: disabled in every state, with the explanation as real text.
 * 3. The **screen** keeps the shell's landmarks and the translation boundary:
 *    h1 → h2 only, no `main` of its own, fixture prose byte for byte inside
 *    `<bdi>`, criteria ordinals in the locale's own numerals.
 *
 * These are jsdom assertions. They prove structure, attributes and text — not
 * that a browser lays the form out correctly, which `tests-browser/` covers.
 */
const DECISION_KEYS = [
  "screening.decision.include",
  "screening.decision.exclude",
  "screening.decision.unclear",
] as const;

/** The fixture's prose, joined, for the mechanical negative checks. */
function fixtureProse(): string {
  return [
    demoScreeningRecord.citation,
    demoScreeningRecord.abstract,
    ...demoScreeningRecord.criteria,
  ].join("\n");
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("the demonstration record carries no verdict and no identifier", () => {
  it("declares exactly the three screening fields, none of them an outcome", () => {
    // A fourth key named `decision`, `verdict` or `included` would be the
    // failure mode: a fixture that answers the question the reader is supposed
    // to answer. The record states what the study is, never what was decided.
    expect(Object.keys(demoScreeningRecord).sort()).toEqual(["abstract", "citation", "criteria"]);
  });

  it("contains no identifier-shaped string anywhere in the record", () => {
    // No DOI (`10.xxxx/...`), no PMID/PMC id, no ISSN, no ISBN. The citation
    // deliberately stops at the journal and year, because an identifier here
    // could be mistaken for a canonical identity the harness never minted.
    expect(fixtureProse()).not.toMatch(/\bdoi\b|10\.\d{4,}\//i);
    expect(fixtureProse()).not.toMatch(/\bPMID\b|\bPMC\d{5,}\b/i);
    expect(fixtureProse()).not.toMatch(/\bISSN[:\s]|\bISBN\b/i);
  });

  it("never states an inclusion outcome in the fixture prose", () => {
    // The negative case for automatic inclusion: no word of the record says a
    // decision was made. (The form's own labels are chrome and live in the
    // catalog, not here.)
    expect(fixtureProse()).not.toMatch(/\bincluded\b|\bexcluded\b|\baccepted\b|\brejected\b/i);
    expect(demoScreeningRecord.criteria).toHaveLength(3);
  });
});

describe("the decision form", () => {
  for (const locale of SUPPORTED_LOCALES) {
    it(`offers three distinguishable choices, none preselected (${locale})`, () => {
      render(<ScreeningForm locale={locale} />);

      const group = screen.getByRole("group", {
        name: CATALOGS[locale]["screening.decisionLegend"],
      });
      const radios = within(group).getAllByRole("radio");
      expect(radios).toHaveLength(3);

      // No decision is made for the reader: every radio starts unchecked, so a
      // screenshot of the initial state shows a question, not an answer.
      for (const radio of radios) {
        expect(radio).not.toBeChecked();
      }

      // Three distinct accessible names — the negative case where a translation
      // collapses "Include" and "Exclude" into one word. Two equal labels would
      // both fail the set-size check and make the name query below ambiguous.
      const names = DECISION_KEYS.map((key) => CATALOGS[locale][key]);
      expect(new Set(names).size).toBe(3);
      for (const name of names) {
        expect(screen.getByRole("radio", { name })).toBeInTheDocument();
      }
    });
  }

  it("links the reason field to its hint, and to the requirement only when it applies", async () => {
    const user = userEvent.setup();
    render(<ScreeningForm locale="en" />);
    const reason = screen.getByLabelText(CATALOGS.en["screening.reasonLabel"]);

    // The hint applies whenever the field exists...
    expect(reason).toHaveAttribute("aria-describedby", "screening-reason-hint");
    expect(screen.getByText(CATALOGS.en["screening.reasonHint"])).toBeInTheDocument();
    // ...the requirement does not: nothing is required of an include or unclear
    // decision, and the message must not be present only to be dismissed later.
    expect(screen.queryByText(CATALOGS.en["screening.reasonRequired"])).toBeNull();

    // Choosing "Exclude" raises the requirement, wired into the field's
    // description so a screen reader meets it on focus.
    await user.click(screen.getByLabelText(CATALOGS.en["screening.decision.exclude"]));
    const message = screen.getByText(CATALOGS.en["screening.reasonRequired"]);
    expect(reason).toHaveAttribute(
      "aria-describedby",
      "screening-reason-hint screening-reason-required",
    );

    // The message is visible text, and it is NOT announced: no live region, no
    // role, no atomic politeness. It appears beside a choice the reader just
    // made, and interrupting them to repeat it would be noise.
    expect(message).toBeInTheDocument();
    expect(message).not.toHaveAttribute("aria-live");
    expect(message).not.toHaveAttribute("aria-atomic");
    expect(message).not.toHaveAttribute("role");

    // Filling the reason satisfies it; emptying it raises it again.
    await user.type(reason, "No comparator arm.");
    expect(screen.queryByText(CATALOGS.en["screening.reasonRequired"])).toBeNull();
    await user.clear(reason);
    expect(screen.getByText(CATALOGS.en["screening.reasonRequired"])).toBeInTheDocument();

    // Another decision withdraws the requirement entirely.
    await user.click(screen.getByLabelText(CATALOGS.en["screening.decision.include"]));
    expect(screen.queryByText(CATALOGS.en["screening.reasonRequired"])).toBeNull();
  });

  it("never submits, never persists, and says so in visible text", async () => {
    const fetchSpy = vi.fn();
    const storageSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(storageSpy);

    render(<ScreeningForm locale="en" />);
    const submit = screen.getByRole("button", { name: CATALOGS.en["screening.submit"] });
    const form = screen.getByRole("form", { name: CATALOGS.en["screening.decisionLegend"] });

    // Disabled in the initial state...
    expect(submit).toBeDisabled();
    expect(submit).toHaveAttribute("aria-describedby", "screening-submit-disabled");

    // ...and still disabled after the reader has done everything the form asks:
    // a choice, a reason. There is no state in which an API would exist.
    await userEvent.click(screen.getByLabelText(CATALOGS.en["screening.decision.exclude"]));
    await userEvent.type(
      screen.getByLabelText(CATALOGS.en["screening.reasonLabel"]),
      "No comparator arm.",
    );
    expect(submit).toBeDisabled();

    // The explanation is real text tied to the button, plus the no-persistence
    // statement beside it — not a title attribute, not a comment, not something
    // a click has to reveal.
    expect(
      screen.getByText(CATALOGS.en["screening.submitDisabledExplanation"]),
    ).toBeInTheDocument();
    expect(screen.getByText(CATALOGS.en["screening.noPersistence"])).toBeInTheDocument();

    // And even a forced submit goes nowhere: no request, no storage write. The
    // disabled attribute is a promise; this is the check that keeps it true.
    fireEvent.submit(form);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(storageSpy).not.toHaveBeenCalled();
  });
});

describe("the workspace screen", () => {
  it("runs h1 → h2 with no skipped level and no main of its own", () => {
    // The shell owns `<main>`; a second one would break the skip link's
    // contract the moment a reader tabs past the navigation.
    const { container } = render(<ScreeningPage locale="en" />);

    expect(container.querySelector("main")).toBeNull();

    const headings = screen.getAllByRole("heading");
    expect(headings.map((heading) => heading.tagName)).toEqual(["H1", "H2", "H2", "H2"]);
    expect(headings[0]).toHaveTextContent(CATALOGS.en["screening.heading"]);
    expect(headings[1]).toHaveTextContent(CATALOGS.en["screening.recordHeading"]);
    expect(headings[2]).toHaveTextContent(CATALOGS.en["screening.criteriaHeading"]);
    expect(headings[3]).toHaveTextContent(CATALOGS.en["screening.decisionHeading"]);
  });

  it("renders the decision form as part of the screen", () => {
    render(<ScreeningPage locale="en" />);
    expect(screen.getAllByRole("radio")).toHaveLength(3);
    expect(screen.getByRole("button", { name: CATALOGS.en["screening.submit"] })).toBeDisabled();
  });

  for (const locale of SUPPORTED_LOCALES) {
    it(`keeps the fixture byte for byte inside bdi, with translated labels (${locale})`, () => {
      const { container } = render(<ScreeningPage locale={locale} />);

      // The two kinds of text, one page at a time: the labels are catalog
      // chrome...
      expect(screen.getByText(CATALOGS[locale]["screening.citationLabel"])).toBeInTheDocument();
      expect(screen.getByText(CATALOGS[locale]["screening.abstractLabel"])).toBeInTheDocument();

      // ...and the fixture is isolated, untranslated, byte identical. The
      // comparison is exact `textContent` equality on every `<bdi>` the page
      // renders — deliberately NOT `getByText(fixture, { selector: "bdi" })`,
      // whose normalizer folds whitespace and would let a whitespace-only
      // rewrite pass while this test's name claims byte equality (repair
      // cycle 1, F4). No trim, no normalization is applied to either side.
      // The inventory length is the non-vacuity guard: it states exactly what
      // "every fixture string" means, so a dropped `<bdi>` fails as a count
      // mismatch rather than as an index error.
      const rendered = Array.from(container.querySelectorAll("bdi"));
      expect(rendered).toHaveLength(2 + demoScreeningRecord.criteria.length);
      expect(rendered[0]?.textContent).toBe(demoScreeningRecord.citation);
      expect(rendered[1]?.textContent).toBe(demoScreeningRecord.abstract);
      for (const [index, criterion] of demoScreeningRecord.criteria.entries()) {
        expect(rendered[index + 2]?.textContent).toBe(criterion);
      }
    });

    it(`numbers the criteria in this locale's own numerals (${locale})`, () => {
      const { container } = render(<ScreeningPage locale={locale} />);

      // Scoped to the criteria `<ol>` rather than any list role on the page, so
      // the assertion names its own target instead of hoping it is unique.
      const list = container.querySelector("ol");
      expect(list).not.toBeNull();
      const items = Array.from(list?.querySelectorAll(":scope > li") ?? []);
      expect(items).toHaveLength(demoScreeningRecord.criteria.length);

      // The marginal ordinal is a real element holding `Intl` output — `ar`
      // gets its own digits, and a bare "1" would fail here.
      items.forEach((item, index) => {
        const ordinal = item.firstElementChild;
        expect(ordinal?.textContent).toBe(formatNumber(locale, index + 1));
      });
    });
  }

  it("keeps the record in a definition list labelled in this locale", () => {
    const { container } = render(<ScreeningPage locale="fr" />);

    const terms = container.querySelectorAll("dl dt");
    expect(terms).toHaveLength(2);
    expect(terms[0]).toHaveTextContent(CATALOGS.fr["screening.citationLabel"]);
    expect(terms[1]).toHaveTextContent(CATALOGS.fr["screening.abstractLabel"]);
  });

  it("renders the lede from the catalog, in every requested locale", () => {
    for (const locale of SUPPORTED_LOCALES) {
      render(<ScreeningPage locale={locale} />);
      expect(screen.getByText(translate(locale, "screening.lede"))).toBeInTheDocument();
      cleanup();
    }
  });
});
