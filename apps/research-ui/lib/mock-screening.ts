/**
 * The single demonstration record the screening workspace renders (UI-04).
 *
 * **Demonstration data.** Like `lib/mock-project.ts` and
 * `lib/mock-project-states.ts`, these are presentation fixtures and nothing
 * more: no identifier, no fingerprint, no acceptance result, no refusal code is
 * minted here, nothing claims to be a live API response, and the shell's
 * visible `Demonstration data` marker covers them.
 *
 * Two rules this file obeys, and which `tests/screening-form.test.tsx` checks
 * mechanically:
 *
 * 1. **No verdicts.** The record carries a citation, an abstract and the
 *    criteria it is screened against — it never says whether it was included or
 *    excluded. Every include/exclude decision on the screen is a choice the
 *    reader makes in the form, and none is preselected (UI-04 negative case:
 *    no automatic inclusion presented as a human decision).
 * 2. **No identifiers.** No DOI, PMID, accession number, project slug or
 *    contract id appears anywhere in this file, so nothing here can be mistaken
 *    for a canonical identity. The prose is methodological demonstration
 *    fixture text and is rendered byte for byte inside `<bdi>`, per the
 *    translation boundary in `docs/I18N.md` §3.
 *
 * The strings are deliberately free of the bare word shapes Tailwind compiles
 * as utilities: this file sits under `lib/`, which the `@source not` list does
 * not exclude, so a utility-looking word here that no product component uses
 * would be emitted into the stylesheet with no source to justify it, and
 * `tests-browser/hygiene.spec.ts` reports that as unexplained.
 */
export const demoScreeningRecord = {
  /**
   * The record's citation as a bibliography entry would print it, minus any
   * locator a reader could mistake for an identifier.
   */
  citation:
    "Amara R, Okonkwo L, Chen M. Machine-assisted screening pipelines in systematic reviews: a replication study. Journal of Research Synthesis Methods; 2024.",

  /**
   * The abstract. Fixture prose: rendered as-is in every locale, never
   * translated, always isolated for direction.
   */
  abstract:
    "This replication examines how a machine-assisted screening pipeline behaves when reviewers screen the same records independently. It reports how disagreements arise, how they are resolved, and how much reading each decision costs, with the data and the analysis described so the reported steps can be repeated.",

  /**
   * The sealed criteria this record is screened against, as the protocol would
   * declare them. Presentation fixture only: the harness remains authoritative
   * for any real protocol.
   */
  criteria: [
    "Reports a review question that names the population, the intervention, and the outcome of interest.",
    "Compares a machine-assisted screening step against independent human screening.",
    "States how disagreements between reviewers were resolved.",
  ],
} as const;
