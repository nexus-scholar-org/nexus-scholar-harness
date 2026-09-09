# Supplementary: Reference Provenance Map and Preprint Version Table (Review 1.0)

*Version stamp:* Review 1.0, corpus finalized 2026-09-09. Relation of this file to the
manuscript: full reference ↔ workspace record mapping for `manuscript_draft.md` and the
preprint→published supersession table used by the §3.8 living-review protocol.

## 1. Reference numbering ↔ workspace record map

The manuscript reference list ([1]–[36]) was regenerated deterministically by
`scripts/restyle_references_vancouver.py` from `synthesis/_manuscript_authors_cache.json`
(first 6 authors then "et al.", ICMJE/Vancouver venue- and date-format). Each reference
maps to a workspace screening record by stable internal ID:

| Ref | SCI ID | Workspace record |
| :-- | :----- | :--------------- |
| [1] | SCI-000182 | Tampere repository thesis (Islam) |
| [2] | SCI-000181 | World Journal of Advanced Research and Reviews (Paulraj) |
| [3] | SCI-000088 | Journal of Evidence-Based Medicine (Xie et al.) |
| [4] | SCI-000144 | arXiv:2603.07287 (Zhao, Tang, Qian) |
| [5] | SCI-000154 | Nature 2026, DOI 10.1038/s41586-025-10072-4 (Asai et al., OpenScholar published version) |
| [6] | SCI-000159 | arXiv:2411.14199 (Asai et al., OpenScholar preprint — preprint version of [5]) |
| [7] | SCI-000126 | arXiv:2605.05985 (BioResearcher) |
| [8] | SCI-000137 | arXiv:2608.26885 (Figalová et al.) |
| [9] | SCI-000106 | arXiv:2509.00038 (Susnjak) |
| [10] | SCI-000099 | arXiv:2510.05335 (Wysocki et al.) |
| [11] | SCI-000102 | arXiv:2604.15456 (DeepER-Med) |
| [12] | SCI-000118 | arXiv:2606.28362 (LUMEN) |
| [13] | SCI-000135 | arXiv:2607.15247 (AutoSynthesis) |
| [14] | SCI-000109 | npj Digital Medicine 2025, DOI 10.1038/s41746-025-01840-7 |
| [15] | SCI-000142 | arXiv:2606.28363 (meta-pipe) |
| [16] | SCI-000096 | arXiv:2501.05468 (LatteReview) |
| [17] | SCI-000127 | MedMeta (Ha, Favre, Portet) |
| [18] | SCI-000100 | arXiv:2508.05666 (HySemRAG) |
| [19] | SCI-000138 | arXiv:2601.11825 (Rahgozar & Mortezaagha proof of concept) |
| [20] | SCI-000110 | arXiv:2501.17181 (Rahgozar et al. live reviews) |
| [21] | SCI-000179 | Journal of Computer Science 2026, DOI 10.3844/jcssp.2026.2082.2091 |
| [22] | SCI-000140 | arXiv:2608.19902 (Brain Researcher) |
| [23] | SCI-000108 | arXiv:2405.14445 (Schmidt et al.) |
| [24] | SCI-000164 | ACL 2025 Findings, DOI 10.18653/v1/2025.findings-acl.412 |
| [25] | SCI-000090 | Cureus 2026, DOI 10.7759/cureus.111193 |
| [26] | SCI-000151 | arXiv:2407.13993 (LLAssist) |
| [27] | SCI-000111 | arXiv:2308.06610 (Bio-SIEVE) |
| [28] | SCI-000141 | arXiv:2512.16447 (TIB AIssistant) |
| [29] | SCI-000082 | bioRxiv 2026, DOI 10.64898/2026.07.08.737358 (EcoXAI) |
| [30] | SCI-000124 | JAMIA 2026, DOI 10.1093/jamia/ocag108 (Zhang et al.) |
| [31] | SCI-000115 | arXiv:2608.12741 (Shafqat et al.) |
| [32] | SCI-000152 | IEEE CINTI 2025, DOI 10.1109/cinti67731.2025.11311831 |
| [33] | SCI-000172 | ICEBE 2026, DOI 10.2478/picbe-2026-0107 (Moţăţăianu & Păvăloiu) |
| [34] | SCI-000129 | IEEE/ACM 2026 Workshop, DOI 10.1145/3786149.3788298 |
| [35] | SCI-000125 | EMNLP 2025, DOI 10.18653/v1/2025.emnlp-main.83 |
| [36] | SCI-000117 | arXiv:2608.18988 (DeepWeaver) |

## 2. Preprint→published supersession status at Version 1.0

Living-review protocol (§3.8) requires tracking preprint→published supersession via
Crossref `update-to` / OpenAlex status. **At Version 1.0 finalization these fields were empty
for the corpus** — the automated retraction stream covered 48 records with no update events,
and the OpenAlex provenance stream returned no `update-to` relations (`phase4/retraction_status_check.json`).
The single, manually-verified supersession is:

| Preprint | Published version | Evidence |
| :------- | :---------------- | :------- |
| [6] OpenScholar (arXiv:2411.14199, 2024, SCI-000159) | [5] *Nature* 2026, DOI 10.1038/s41586-025-10072-4 (SCI-000154) | Same author set and title; DOI resolved via Crossref |

## 3. Preprint-track identified identifiers (for future living-review sweeps)

32 of 58 included records are preprint-track. Identifiers recorded for the trailing-boundary
re-sweep (arXiv IDs are authoritative; arXiv-DataCite DOIs happen to be present for some):

| SCI ID | ID type | Value |
| :----- | :------ | :---- |
| SCI-000082 | bioRxiv DOI | 10.64898/2026.07.08.737358 |
| SCI-000096 | arXiv DOI | 10.48550/arxiv.2501.05468 |
| SCI-000099 | arXiv DOI | 10.48550/arxiv.2510.05335 |
| SCI-000100 | arXiv DOI | 10.48550/arxiv.2508.05666 |
| SCI-000102 | arXiv ID | 2604.15456 |
| SCI-000106 | arXiv ID | 2509.00038 |
| SCI-000107 | arXiv DOI | 10.48550/arxiv.2305.01145 |
| SCI-000108 | arXiv ID | 2405.14445 |
| SCI-000110 | arXiv DOI | 10.48550/arxiv.2501.17181 |
| SCI-000111 | arXiv DOI | 10.48550/arxiv.2308.06610 |
| SCI-000114 | arXiv DOI | 10.48550/arxiv.2408.13450 |
| SCI-000115 | arXiv ID | 2608.12741 |
| SCI-000117 | arXiv DOI | 10.48550/arxiv.2608.18988 |
| SCI-000118 | arXiv ID | 2606.28362 |
| SCI-000122 | arXiv ID | 2604.02678 |
| SCI-000126 | arXiv ID | 2605.05985 |
| SCI-000127 | arXiv ID | (URL-based; see included.json) |
| SCI-000128 | arXiv ID | 2606.20997 |
| SCI-000131 | arXiv ID | 2605.03042 |
| SCI-000135 | arXiv ID | 2607.15247 |
| SCI-000137 | arXiv ID | 2608.26885 |
| SCI-000138 | arXiv ID | 2601.11825 |
| SCI-000140 | arXiv ID | 2608.19902 |
| SCI-000141 | arXiv ID | 2512.16447 |
| SCI-000142 | arXiv ID | 2606.28363 |
| SCI-000144 | arXiv ID | 2603.07287 |
| SCI-000151 | arXiv DOI | 10.48550/arxiv.2407.13993 |
| SCI-000156 | arXiv DOI | 10.48550/arxiv.2411.18583 |
| SCI-000158 | arXiv DOI | 10.48550/arxiv.2403.08399 |
| SCI-000159 | arXiv DOI | 10.48550/arxiv.2411.14199 |
| SCI-000182 | (Tampere repository) | institutional thesis, no DOI |
| SCI-000186 | (arXiv, no DOI captured) | venue-only record |