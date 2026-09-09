# Conflict-of-Interest Audit

**Corpus**: 47 studies (post-audit); **run**: 2026-09-08T09:51:47.352491+01:00
**Method**: independent analyst read of extraction fulltext (parallel subagents); funding/acknowledgments/COI statements captured verbatim; industry entities tagged (`funding` / `affiliation` / `donated-equipment` / `tooling`); single severity-ordered label per study.

## Summary

| Label | Count |
|---|---|
| no-statement | 37 |
| academic-or-public | 1 |
| industry-money | 0 |
| industry-affiliation-or-equipment | 5 |
| declared-no-conflict | 4 |
| **Studies with any industry tie (money OR affiliation/equipment)** | **5** |
| — of which industry money | 0 |
| — of which industry affiliation / donated equipment | 5 |
| Analyst-label adjustments (no-statement -> relabel) | 0 |

Labels are severity-ordered: `industry-money` > `industry-affiliation-or-equipment` > `declared-no-conflict` > `academic-or-public` > `no-statement`. Vendor products merely used in methods are `tooling` and do NOT raise the label.

## Industry affiliation / donated-equipment studies

SCI-000003, SCI-000005, SCI-000034, SCI-000172, SCI-000041

## Top tagged industry entities (non-tooling)

| Entity | Kind | Studies |
|---|---|---|
| Meta | affiliation | 2 |
| Google | affiliation | 1 |
| Anthropic | affiliation | 1 |
| OpenAI | affiliation | 1 |
| Meta | donated-equipment | 1 |

## Per-study detail (studies with tagged entities)

| ID | Year | Label | Entities |
|---|---|---|---|
| SCI-000003 | 2024 | industry-affiliation-or-equipment | Meta (affiliation) |
| SCI-000005 | 2024 | industry-affiliation-or-equipment | Google (affiliation) |
| SCI-000034 | 2024 | industry-affiliation-or-equipment | Meta (affiliation); Anthropic (affiliation) |
| SCI-000172 | 2026 | industry-affiliation-or-equipment | OpenAI (affiliation) |
| SCI-000041 | 2024 | industry-affiliation-or-equipment | Meta (donated-equipment) |

## Studies with no statement available

SCI-000001, SCI-000002, SCI-000156, SCI-000154, SCI-000104, SCI-000105, SCI-000009, SCI-000120, SCI-000158, SCI-000108, SCI-000013, SCI-000014, SCI-000101, SCI-000184, SCI-000017, SCI-000161, SCI-000181, SCI-000020, SCI-000145, SCI-000106, SCI-000125, SCI-000025, SCI-000027, SCI-000171, SCI-000167, SCI-000083, SCI-000032, SCI-000033, SCI-000138, SCI-000038, SCI-000134, SCI-000042, SCI-000043, SCI-000045, SCI-000046, SCI-000136, SCI-000144

## Methodological note

- Government/academic/university grants are NOT industry entities; they map to `academic-or-public` or `declared-no-conflict` when an explicit declaration exists.
- `industry-money` = any funding/salary/equity from a private-sector company (incl. corporate foundations); `industry-affiliation-or-equipment` = author employed by industry or equipment/data donated by industry without cash.
- Seed/variety donations from agrochemical companies (e.g. BASF, Bayer) are tagged `donated-equipment`.
- Verbatim statements and evidence are recorded per study in the JSON output for independent verification.
- Regenerate with `scholar-verify coi --workspace <dir>`; relabel rule: no-statement with a COI statement -> declared-no-conflict; no-statement with only funding -> academic-or-public; non-tooling entities upgrade to the matching industry label; adjustments recorded on each row.
