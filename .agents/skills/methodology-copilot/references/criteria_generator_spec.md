# Inclusion & Exclusion Criteria Specification (`criteria.md`)

When transitioning from the methodology interview to the literature screening phase, the Copilot produces a `criteria.md` file inside `workspaces/<project-slug>/literature/criteria.md`.

---

## 1. Structure of `criteria.md`

The file must follow standard systematic review reporting rules (compatible with PRISMA):

```markdown
# Systematic Literature Screening Criteria

## Project Context
- **Project ID**: `transformer-linear-attention`
- **Paradigm**: Design Science & Quantitative Benchmark
- **Primary Objective**: Investigate sub-quadratic attention formulations and hardware efficiency.

---

## Inclusion Criteria (Must satisfy ALL to be included)
1. **Domain Focus**: Peer-reviewed or reputable preprint studies proposing or benchmarking transformer architectures with sub-quadratic ($O(N \sqrt{N})$ or $O(N)$) attention mechanisms.
2. **Empirical Evaluation**: Must report concrete empirical measurements (e.g. throughput, memory footprint, perplexity, downstream task accuracy).
3. **Publication Window**: Published between January 2018 and present.
4. **Language**: English full-text available.

---

## Exclusion Criteria (Exclude if ANY condition is met)
1. **Pure Application without Architectural Modification**: Studies that only apply standard dense softmax attention to a new domain without modifying or evaluating the attention mechanism itself.
2. **Review / Opinion Articles**: Secondary literature, position papers, non-peer-reviewed blog posts without algorithmic contributions.
3. **Non-English Literature**: Papers without an English translation.
4. **Incomplete Technical Specification**: Papers lacking algorithmic formulation or baseline comparisons.

---

## Target Search Queries (for `scholar-search-kit`)
- Primary: `"linear attention" OR "sparse attention" OR "efficient transformers"`
- Secondary: `("sub-quadratic attention" OR "kernelized attention") AND benchmark`
```
