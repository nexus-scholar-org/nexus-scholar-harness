# Inception and recon scientific review

Date: 2026-10-09. Status: recorded review and proposed follow-ups, not an implementation packet or authorization to change runtime behavior.

## Conclusion and scope

Inception and recon are useful provenance-aware exploratory scoping assistants. Their deterministic processing, recorded pools, extensible lexicons, and human choices are valuable. They are not validated judges of novelty, research gaps, epistemological correctness, or review quality.

The review inspected `src/scholar_harness/inception/` and `src/scholar_harness/recon/` at local HEAD `38c89bc4a54014bdea004831a243a81ab39f0200`; these directories had no delta against the then-fetched `origin/main`. Small offline counterexamples were executed against the inspected source. No provider search, research workspace mutation, runtime repair, or cross-domain effectiveness evaluation was performed. Findings must be rechecked if these modules change.

## Findings and evidence

### Methodology concerns

1. **Paradigm and review design are conflated.** `inception/intent.py:36` maps Positivist to PRISMA SLR and Interpretivist to Scoping Review. `detect_leanings` at `:116` scores keyword substrings; a zero-score topic such as `soil salinity` ranks Positivist first through tie ordering, and `wizard.py` uses the first rank as its recommendation. A philosophical stance does not determine the appropriate review design. Recommend an undetermined state and a separate purpose/question-based design interview.
2. **Templates prejudge outcomes and can become eligibility rules.** `intent.py:71/:94/:105` presupposes statistical significance, artifact novelty, or improvement. `make_intent` at `:250` turns profile negative exclusions into actual exclusion criteria when none were supplied. Computational benchmark/latency examples also narrow the representation of Design Science. Recommend neutral questions, domain-appropriate evidence examples, and explicit approval of substantive inclusion/exclusion rules.
3. **Concentration is labelled coherence.** `recon/gates.py::compute_topic_purity` computes top-three topic counts divided by all topic counts; it does not measure semantic relatedness. Three unrelated topics (oncology, astronomy, economics; each n=1) return `coherent`, purity `1.0`. Recommend the literal name topic concentration, explicit topic coverage, and a separate relevance assessment.
4. **Retrieval volume is labelled saturation or gap evidence.** `recon/engine.py:36/:37/:179` defines fixed count bands below 50, 50–500, and above 500. `corpus_count` uses an OpenAlex term search with date filters. These are query-conditioned volume bands, not proof of a research gap or methodological saturation. The inception-agent skill's claim that scant/sparse counts support a defensible gap is too strong. Use: “Low retrieval volume for this query; candidate gap requiring verification.” Dense fields can still contain unresolved questions.
5. **Field neutrality and anchor strength are overstated.** `recon/lexicon.py` provides useful but ML/computing-weighted defaults. Regex “schools” are keyword groups, not demonstrated intellectual schools. `distiller.py:29` uses ASCII-oriented tokenization and English stopwords; `:77/:212` excludes records without DOIs from the taxonomy/topic evidence. An anchor records term occurrence in title/abstract, not substantive support for a research direction. Recommend optional versioned domain/language profiles, other persistent identifiers, and separate mention/relevance/support labels. QEI is lexical overlap, not a validated novelty or research-quality score; thresholds remain exploratory heuristics.

### Reproduced behavioral issues

6. **Full pools absorb no new follow-up evidence.** `adaptive.py:195/:225` merges original records first and caps at 25. An original 25-record pool plus a new follow-up DOI excludes the new record; re-distillation may therefore remain unchanged. Preserve separate probe pools and define an explicit balanced selection policy rather than silently privileging the original pool.
7. **Cache identity omits the requested sample size.** `engine.py:290` calls `cache_key` without `max_results`; `:294` returns an existing pool regardless of the new limit. Raising the limit can reuse a smaller sample. Repair with a versioned sampling-aware cache identity or explicit refresh/expansion semantics, not an undocumented cache overwrite.
8. **Noise filtering rejects legitimate topics.** `inception/grounded.py:80` checks venue tokens as substrings. Offline results: `science journalism`, `volume rendering`, and `workshop pedagogy` all return junk=True. Replace substring bans with context-sensitive filtering and regression examples from affected fields.
9. **Fallback direction anchors do not necessarily support the selected concept twice.** `grounded.py:171–181` combines anchors across separate terms and chooses the first term as concept. Two terms occurring in one paper each yield a two-anchor direction although its selected concept occurs in only one paper. Preserve concept-specific anchor checks or label the result explicitly as a mixed vocabulary bundle, not a two-paper-supported concept.

## Scientific boundaries

Provenance establishes where a suggestion came from, not whether the suggestion is scientifically valid. Human confirmation is necessary but does not transform an unvalidated score into a valid measurement.

PRISMA is a reporting guideline, not a quality certificate or a substitute for a methodology. Its statement explicitly says it should not assess review conduct or methodological quality. Review-design choice should follow the question and purpose.

- [PRISMA 2020 statement](https://www.bmj.com/content/372/bmj.n71)
- [JBI scoping review methodology guidance](https://jbi.global/news/jbi-updates-its-scoping-review-methodology)

## Follow-up order and HCM separation

All items below are proposed, not started by this review.

1. **Skill honesty repair:** adjust gap/saturation/coherence/anchor wording in inception-stack skills and mirrors; documentation only, separately from toolkit refresh.
2. **Bounded behavioral repair:** reproduce findings 6–9 as regression tests, specify intended behavior, then repair in separate focused packets. Include sampling/cache compatibility and explicit provenance; never silently change stored meaning.
3. **Methodology decision:** review paradigm/design separation, neutral question templates, eligibility confirmation, and versioned profiles with domain experts. This is a behavior/methodology decision, not a mechanical HCM move.
4. **Empirical validation:** use expert-reviewed cases across computing, health, social sciences, agriculture, and humanities, including non-English and non-DOI literature. Assess relevance, false gap suggestions, profile sensitivity, query sensitivity, and suggestion usefulness. Compare with a simple search-plus-human-scoping baseline. Software tests alone cannot establish scientific correctness.

HCM characterization should record current behavior, including questionable defaults, without endorsing it. HCM-02/HCM-05 should preserve behavior unless a separate approved decision changes it. Domain configuration should eventually sit behind explicit, versioned interfaces; avoid turning a structural refactor into a scientific-policy rewrite.

## UI recommendation

Inception belongs near the beginning of a new-project journey: idea → exploratory literature scan → refine question and scope → draft protocol → researcher confirmation → recorded workspace/protocol. It is optional, not a mandatory gateway: experienced researchers may bring an existing question or protocol and must be able to skip exploration.

Two surfaces serve different audiences:

- **Researcher-facing “Explore and scope”:** topic, scope/date/language choices, observed sources, editable candidate directions, limitations, then a draft-protocol preview. Never show “novel gap confirmed”, “scientifically coherent”, or automatic methodological approval. Source links and explicit user choices must remain visible.
- **Developer diagnostic view:** raw probe inputs, provider outcomes, cache identity, sampling limits, active lexicon/profile version, observed versus dropped records, and raw heuristic scores with literal definitions. It is a test instrument, not scientific validation.

Build a small fixture-backed/read-only interaction prototype now if useful, clearly labelled demonstration data. Live execution needs a separate packet covering recon/cache mutations, errors, provenance, and HCM interfaces. Workspace/protocol emission requires a separately specified confirmed write path. Do not duplicate wizard or recon logic in the browser and do not make the first UI depend on unfinished HCM internals.

Success for the first screen is that a researcher can explain what was searched, inspect source evidence, revise the question, reject a suggestion, and distinguish an exploratory hypothesis from an accepted protocol—not merely obtain a green score.
