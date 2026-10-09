# Retrieval, synthesis, consensus, matrix, stats

Querying and synthesis read an existing store; only the typed index path
writes one. Pinned kit `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad`.

## `query` — hybrid graph-boosted retrieval (`cli.py:529`)

```
Score(d) = CosineSim(q, d) + α·PageRank(d) + β·I_seed(d)   (retriever.py:167-187)
```

- Defaults `α = 0.25`, `β = 0.15` (`retriever.py:180-181`); with boosting the
  store is over-fetched ×4 then re-ranked (`retriever.py:204`).
- `CosineSim` is Chroma cosine distance mapped from [0,2] to [0,1].
- PageRank source: `--graph <graph.json>` (node-link with `pagerank` key, or a
  graph recomputed via `nx.pagerank α=0.85`, normalized to max 1.0,
  lowercased keys). MCP takes the same as `graph_source`.
- Seed boost: repeatable `--boost-doi/-d` on the CLI (list `boost_dois` in
  Python); single `boost_doi` on MCP.

Flags: positional `query_text`; `--db-path` (default `./chroma_db` — pass an
absolute path), `--collection`, `--embedder` (help text lists
`sentence-transformers, openai, or mock`; all route to `get_embedder`, which
also supports `gemini`), `--section/-s` (exact section name),
`--section-category/-c` (`abstract_intro | methodology | results_empirical |
discussion_limitations`), `--paradigm/-p`, `--study-design`, `--workspace-id/-w`
(filter only — not identity), `--boost-doi/-d` (repeatable), `--graph/-g`,
`--alpha`, `--beta`, `--limit/-n` (default 5), `--format/-f`
(`rich | json | table`).

Section categories come from keyword classification (`models.py:22-88`).

## Citation tokens and chunk identity

Tokens render as `[<workspace_id|paper_id|doi|filename>#<sec10>#<chunk_id>]`
(`retriever.py:123`). The `CHK-` chunk id is content-derived
(`chunker.py:121`); sections are `#`/`##`/`###` AST splits. Never infer
identity from a token's first field — read the stored typed limbs.

## `synthesize` — grounded synthesis (`cli.py:641`)

Deterministic bullets when no `llm_callable` (one per cited chunk);
`--output` writes the Markdown review, `--output-claims` writes the claim
ledger for consensus. Flags: positional `query_text`; `--rq-id/-r`
(optional — pass explicitly), `--output/-o`, `--output-claims`, `--db-path`,
`--collection`, `--embedder`, `--section-category/-c`, `--paradigm/-p`,
`--limit/-n` (default 5).

**Similarity is not entailment.** `verify_claim_entailment`
(`synthesis.py:112`) scores embedding cosine scaled to [0,1] (lexical-overlap
fallback on embedder errors) and labels `VERIFIED (≥0.85)` / `AMBIGUOUS
(≥0.50)` / `UNSUPPORTED` (`models.py:207-213`). These are kit-observed
similarity words — no claim verifies semantic entailment. Claims whose
citation tokens match no retrieved chunk are still scored against an empty
set (`0.0`, `UNSUPPORTED`).

**claims.json ≠ verify input.** `SynthesisClaim` carries
`claim_text`/`citation_tokens`/`entailment_status` with **no
`evidence_quote`/`claim_id`**, so the verbatim verifier cannot pair them
field-for-field (its verdicts are a different, verbatim-match notion).
Surface the RAG `entailment_status` alongside verbatim verdicts; never
conflate the two.

## `consensus` — Consensus Cartographer (`cli.py:721`)

Jaccard greedy clustering (default threshold `0.30`,
`ConsensusCartographer.DEFAULT_THRESHOLD`, `consensus.py:203`), deterministic
polarity-lexicon stance (`POSITIVE`/`NEGATIVE`/`NEUTRAL`, auto-derived unless
pre-set), per-study majority-stance dedup, then study-count verdicts
`HIGH_CONSENSUS` / `ACTIVE_DEBATE` / `UNRESOLVED` / `PROVISIONAL`
(`models.py:251-257`).

For paraphrase-heavy corpora prefer embedding-cosine similarity
(`--similarity sentence-transformers --threshold 0.40`; `--similarity` is a
provider name passed to `get_embedder`, falling back to lexical on embedder
errors). Filter non-claim fragments (headers, watermarks, captions,
in-text reference lines) from the claim pool first.

Flags: positional `claims_file` (JSON array, or JSONL); `--rq-id/-r`,
`--threshold/-t`, `--similarity` (default `lexical`), `--model-name`,
`--output-json`, `--output-md`.

## `matrix` and `stats`

- `matrix` (`cli.py:827`): with an existing `--protocol/-P` →
  `MatrixExtractor` dynamic dimensions via `build_extraction_model`, writing
  `synthesis_matrix.{json,csv,md}` under `--output-dir/-o` (default
  `literature`). Without `--protocol` → 7-dimension methodology matrix
  (`study_id | authors_year | epistemological_design |
  population_dataset_sample | key_intervention_model |
  primary_metrics_results | declared_limitations`) written to
  `--output-md`/`--output-json` (default `<output-dir>/matrix.md|json`).
  The fallback path drives the legacy `ScholarIndexer` (`cli.py:859`) —
  a command-local reader, not the typed publication path.
- `stats` (`cli.py:880`): store summary (`--db-path`, `--collection`,
  `--embedder`); also drives the legacy indexer as a reader.

## Auxiliary extraction (not the publication path)

`scholar-rag extract <input.md> [--schema paper] [--output out.json]
[--api-key KEY]` (`cli.py:896`): `LLMExtractor` (default model `gemini-pro`,
`extractor.py:47-58`) with heuristic fallback (`_heuristic_extract`) and
`PIIRedactor` redaction (`redactor.py:9`). Only `paper` is registered in the
schema map. This never publishes a manifest and carries no parent lineage.
