# scholar-rag-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-rag-kit`). Scope: `tools/scholar-rag-kit/src/scholar_rag/` (21 modules, 14,431 lines) and `tools/scholar-rag-kit/tests/` (19 files, 14,613 lines, 592 test functions), plus the harness call sites that use the kit (`src/scholar_harness/pipeline/{synthesis,matrix,indexing}.py`, `orchestrator.py`, `console/runtimes/actions.py`). Method: I read every research-facing module in full: `synthesis.py`, `consensus.py`, `matrix.py`, `retriever.py`, `indexer.py`, `chunker.py`, `embedder.py`, `models.py`, `extractor.py`, `redactor.py`, `backends.py`, `index_models.py`, and the `query/synthesize/consensus/matrix/stats/extract` part of `cli.py`. I only skimmed the index-governance modules (`index_service`, `index_manifest`, `index_verifier`, `replacement`, `recovery`; about 9.4k lines). I ran the kit's research-path tests (`uv run pytest tools/scholar-rag-kit/tests/test_{synthesis,consensus,matrix,retriever,chunker,extractor}.py -q`: 92 passed in 234 s) and three offline reproduction scripts. Those scripts used the `mock` embedder, stub LLM callables, and for the entailment test the real default embedder `all-MiniLM-L6-v2` loaded from the local HF cache with `HF_HUB_OFFLINE=1`. No network calls were made.

Reproduction scripts (scratch, not committed): `repro_rag.py`, `repro_entail.py`, `repro_misc.py` in the session scratchpad. Each finding below quotes the command shape and the observed output.

## 1. Verdict

The kit has two layers of very different quality. The index-identity and governance layer (content-addressed `CHK-` ids, a closed chunker configuration, manifest, replacement protocol) is over-engineered but disciplined, and its tests are heavy: about 490 of the 592 tests. The research layer is a set of thin heuristics, about 1.4k lines with 34 tests. That layer is the part that turns papers into claims, consensus verdicts and extraction matrices, and it presents those heuristics under strong methodological names. I reproduced each of the following:

- **Entailment check.** The "entailment verifier" is embedding cosine similarity. It marks a claim that directly contradicts its source as `VERIFIED` (0.93).
- **Uncited text.** LLM text without citations is never checked. Output with zero citations scores a 100% entailment rate.
- **Study attribution.** Every claim in a workspace is attributed to the workspace rather than to its study, so consensus can never see more than one study.
- **Methodology matrix.** The legacy matrix fills empty cells with invented values such as "Standard Corpus" and "Accuracy / F1".
- **Protocol matrix.** The protocol matrix truncates "92.5%" to "92". This is the path the harness ships, because the harness never passes an LLM.

As shipped, this kit must not be used to produce synthesis, consensus or extraction output for a systematic review without full human re-extraction. Retrieval and indexing are usable as a search aid.

| Lens | Rating | Reason |
| :--- | :--- | :--- |
| Code quality & architecture | Weak | Rigorous index governance, but the research layer has no LLM/provider abstraction, dead backends, journal-discovery logic copied four times with silent `except: pass`, and three git-pinned kit dependencies that are never imported. |
| Correctness & bugs | Weak | 14 reproduced defects in synthesis, matrix, consensus, chunker, indexer, redactor and retriever. Several produce silently wrong values rather than errors. |
| Research-method fitness | Failing | No real entailment, no per-cell provenance check, no not-found vs not-reported distinction, no dual extraction, a top-5 recall cap, a lexicon-based "consensus", and no reproducibility record. |

## 2. Architecture and code quality

**RAG-16 — Effort and tests are concentrated on index identity, not on research logic (Medium).** `index_service.py` (2,131 lines), `index_manifest.py` (2,086), `index_verifier.py` (1,190), `replacement.py` (2,741) and `recovery.py` (1,250) make up 9,398 of the 14,431 source lines. The research modules `synthesis.py` (415), `consensus.py` (400), `matrix.py` (349) and `retriever.py` (281) total 1,445. Test functions follow the same split: `test_index_*` and `test_canonical.py` hold 490 tests, while `test_synthesis.py` has 2, `test_retriever.py` 3, `test_matrix.py` 8 and `test_consensus.py` 21. The one synthesis status assertion is a tautology: `tests/test_synthesis.py:68` asserts that the status is one of all three possible values. None of the defects in §3 is caught by the suite.

**RAG-17 — No LLM or provider abstraction; several half-built providers (Medium).**
- Synthesis takes a bare `Callable[[str], str]` (`synthesis.py:279`), and the matrix takes a different `Callable[[str], dict]` (`matrix.py:151`). Neither records a model, temperature, or retry/timeout policy.
- `LLMExtractor` hard-codes the Gemini REST URL and defaults to `model="gemini-pro"` (`extractor.py:50,99`).
- `get_embedder("gemini")` returns a `GeminiEmbedding` with no `__call__` (`embedder.py:126-168`). Reproduced: `callable(GeminiEmbedding(api_key="x"))` gives `False`, so Chroma cannot use it.
- `VectorBackend`/`NumpyBackend` (`backends.py:7-142`) are exported but used by nothing in `src` (grep finds only `__init__.py`). `NumpyBackend.query` ignores `where` (`backends.py:82-119`). Reproduced: with `where={"study_id":"B"}` it returned the metadata of both study A and study B.

**RAG-18 — Audit-journal discovery is copied four times with different semantics and swallowed errors (Medium).**
- Copies: `indexer.py:177-193`, `retriever.py:133-143`, `synthesis.py:227-243` and `matrix.py:57-73`.
- Three copies walk up to 5 parent directories from the process CWD and *create* an `audit/` directory wherever they find a `protocol.json`, `project.json` or `audit/`. The retriever copy only logs if the journal already exists.
- Every write is `except Exception: pass` (`synthesis.py:268`, `matrix.py:101`, `retriever.py:164`, `indexer.py:214`).
- Events are hand-built with `json.dumps` and bypass the workspace-manager `log_event.py` path. AGENTS.md calls that logger a hard convention.
- The CWD is searched before `db_path` (`synthesis.py:229-232`), so running from workspace A against workspace B's database logs into A.

**RAG-19 — Dead retry in matrix extraction (Low).** `matrix.py:197-204` re-issues exactly the same query when the first returns nothing. The comment says it deliberately avoids a global fallback, so the second call can never return a different result.

**RAG-20 — Clustering is order-dependent and compares only against the first member (Low).** `consensus.py:210-226` greedily attaches each claim to the cluster whose *first* claim is most similar. Permuting the input can change the clusters and therefore the verdicts. `analyze` also mutates the caller's claim objects in place (`consensus.py:299-303`).

**RAG-21 — Declared dependencies that are never imported (Low).** `pyproject.toml:34-36` pins `scholar-graph-kit`, `scholar-bib-kit` and `scholar-search-kit` to git SHAs. A grep for `scholar_graph|scholar_bib|scholar_search` in `src` returns nothing. These add install weight and pin churn for no runtime use.

Strength worth keeping: chunk identity (`chunker.py:121-164`, `_resolve_identity` at `chunker.py:593-606`) fails closed on missing identity limbs and has no fallback chain. The closed chunker configuration (`chunker.py:83-91`, `246-284`) is validated in one place. This is the right way to build identity.

## 3. Correctness and bugs

**RAG-01 — Critical — Reproduced — The "entailment" check marks contradicted claims VERIFIED.** `synthesis.py:112-148` embeds the claim and the cited chunks, takes the maximum cosine, rescales it to `(cos+1)/2`, and maps ≥0.85 to `VERIFIED`. Cosine similarity ignores negation, direction and magnitude. With the default embedder (`repro_entail.py`, MiniLM, offline) and the chunk *"UAV-based spraying reduced pesticide use by 32% … (n=120)"*:

```
(0.9843, 'VERIFIED') <- ...reduced pesticide use by 32% compared with manual spraying.
(0.9284, 'VERIFIED') <- ...did not reduce pesticide use compared with manual spraying.
(0.9765, 'VERIFIED') <- ...increased pesticide use by 32% compared with manual spraying.
(0.9543, 'VERIFIED') <- ...reduced pesticide use by 90% across all farms worldwide.
(0.4344, 'UNSUPPORTED') <- The capital of France is Paris.
```

Because of the `(cos+1)/2` rescale, an orthogonal (unrelated) embedding scores 0.5 and lands in `AMBIGUOUS`. Reproduced with a stub orthogonal embedder: `(0.5, 'AMBIGUOUS')`. `UNSUPPORTED` needs a *negative* cosine. The exception fallback (`synthesis.py:149-161`) switches to word overlap with *different* thresholds (0.6/0.3), so the same status word means different things depending on whether the embedder raised. Impact: `verified_claims_count` and `entailment_rate`, which the harness copies into `results["stages"]["synthesis"]` (`src/scholar_harness/pipeline/synthesis.py:117-122`), measure topical similarity, not support.

**RAG-02 — Critical — Reproduced — Uncited text is never checked, and zero claims means 100% verified.** `_extract_claims_and_citations` skips any unit without a token (`synthesis.py:175-177`). When the text contains any `- ` bullet, `_claim_units` keeps only bullets and drops every other sentence (`synthesis.py:56-58`). `entailment_rate` is `1.0` when there are no claims (`synthesis.py:318`). Using `repro_rag.py` R4 with a stub LLM:

```
LLM returns "Drones eliminate all crop losses. Studies unanimously agree on a 300% yield gain."
-> claims: 0 verified: 0 entailment_rate: 1.0
LLM returns that sentence + one cited bullet
-> claims: 1 ... fabricated sentence present in markdown: True
```

The fabricated sentence is written into `synthesis_markdown` and then into `literature_review.md` with no flag attached.

**RAG-03 — Critical — Reproduced — Study attribution is the workspace, so all claims collapse into one "study".** Three places pick a study id with `workspace_id` first: claim attribution `meta.get("workspace_id") or meta.get("paper_id") or …` (`synthesis.py:203`), citation tokens (`retriever.py:128`) and the methodology matrix key (`synthesis.py:358-360`). Since T-20, `workspace_id` is a *required* limb on every chunk (`chunker.py:65-72`), so it is always present and always identical across the studies in a review. The typed `study_id` limb that is stored on every chunk (`models.py:162-163`) is ignored by all three. Using `repro_rag.py` R1/R2 with three studies (`STU-a…`, `STU-b…`, `STU-c…`) in workspace `WS-uav-review`:

```
study_id= WS-uav-review | token= [WS-uav-review#results#CHK-0427...   (x6, all claims)
provisional: studies=['WS-uav-review'] claims=3 dist={'POSITIVE': 1, ...}   (every cluster)
```

`ConsensusCartographer` can therefore never reach `HIGH_CONSENSUS` or `ACTIVE_DEBATE`: `support_count < 2` gives `PROVISIONAL` (`consensus.py:275`). The citation token no longer identifies the paper, only the workspace plus an opaque chunk hash. A claim that cites several studies is also attributed only to the first one (`synthesis.py:206`).

**RAG-04 — Critical — Reproduced — The methodology matrix invents values and merges all studies into one row.** `generate_methodology_matrix` (`synthesis.py:362-374`, `384-389`) fills missing fields with literals: `"Design Science / Empirical"`, `"Evaluation Benchmark"`, `"Standard Corpus"`, `"Accuracy / F1"`, `"Proposed System"`, `"Evaluated via Accuracy / F1"`, `"Domain bounded"`. It also keys rows by `workspace_id` (see RAG-03). Using `repro_rag.py` R3 with three studies:

```
rows: 1
{'study_id': 'WS-uav-review', 'authors_year': 'Unknown',
 'epistemological_design': 'Evaluation Benchmark (Design Science / Empirical)',
 'population_dataset_sample': 'Standard Corpus', 'key_intervention_model': 'Paper a',
 'primary_metrics_results': 'Detection accuracy was 92.5% ... of study A only',
 'declared_limitations': 'Domain bounded'}
```

The default `scholar-rag matrix` command without `--protocol` reaches this function (`cli.py:860-877`).

**RAG-05 — Critical — Reproduced — The heuristic matrix cell truncates numbers at the first period.** Without an LLM, the cell value is `top_chunk.text.split(".")[0]` (`matrix.py:213-215`). The harness Stage 7 calls `extract_all` without `llm_callable` (`src/scholar_harness/pipeline/matrix.py:103-104`), so this is the shipped behaviour. Using `repro_rag.py` R7:

```
'primary_result': 'Detection accuracy was 92'     (source: "...was 92.5% with the proposed model")
'primary_result': 'Detection accuracy was 71'     (source: "...was 71.3% and the model does not improve...")
```

Any decimal, "et al.", "e.g.", "Fig. 2" or "p < .05" cuts the value. The truncated value is written to `synthesis_matrix.{json,csv,md}` with a citation token, so it looks sourced.

**RAG-06 — High — Reproduced — Matrix cells have no real provenance, and failures are silent.** Using `repro_rag.py` R7:
- **Citation does not match the value.** `citation_token` is always the *top* retrieved chunk (`matrix.py:210-211`), but the LLM sees all three chunks (`matrix.py:220`). Its answer is accepted without checking that it appears in the cited text (`matrix.py:227-228`). A stub LLM answering `"71.3%"` for study A, a value from study B, is stored as `71.3%` with study A's citation.
- **LLM failure is hidden.** `except Exception: pass` (`matrix.py:229-230`) keeps the heuristic value. Reproduced: an LLM raising `RuntimeError("rate limited")` produced `primary_result='Detection accuracy was 92'`, and the row has no error or status field.
- **Not found and not reported look the same.** An unretrieved study gets the protocol `fallback_value`, which defaults to `"Not Reported"`. Reproduced for an unindexed study: `{'sample_size': 'Not Reported', 'primary_result': 'Not Reported', 'outcomes': 'Not Reported'}`. "Not indexed", "not retrieved" and "the paper does not report it" are indistinguishable.
- **Schema validation is silent.** Validation failures are swallowed (`matrix.py:236-241`). A `data_type: list, required: True` dimension was emitted as the string `'Detection accuracy was 92'`. `MatrixDimension.required`, whose own description says the extractor "flags papers that omit this dimension" (`tools/scholar-protocol-kit/src/scholar_protocol/models.py:223-226`), is never read by `matrix.py`.

**RAG-07 — High — Static (+R1) — The top-k cap silently limits which studies enter the synthesis.** `synthesize(n_chunks=5)` (`synthesis.py:275`) retrieves 5 chunks for the whole corpus. The harness uses that default for the first research question only, restricted to `results_empirical` (`src/scholar_harness/pipeline/synthesis.py:111-115`). A 40-study review therefore produces a "literature_review.md" built from at most 5 chunks, so at most 5 studies. `SynthesisResult` records only `retrieved_chunks_count` (`models.py:219-228`). It does not record which chunks or studies were retrieved, or which included studies were never consulted, so the gap cannot be seen from the output.

**RAG-08 — High — Reproduced — The stance lexicon gets polarity wrong.** `classify_stance` (`consensus.py:144-159`) counts space-delimited lexicon hits. Punctuation next to a word defeats the match. Contrast words ("but", "however", "although", "despite") count as negative. Direction words are not tied to outcome desirability. Using `repro_rag.py` R6:

```
NEUTRAL  <- Accuracy improved.                       ("improved." not matched)
NEUTRAL  <- Mortality was reduced by 30%.            ("reduced" not in lexicon)
NEGATIVE <- Error rates were lower with the new controller.   (a benefit)
NEGATIVE <- The intervention did not reduce mortality.
NEUTRAL  <- Although costly, the method improves yield.
```

Consensus verdicts are computed from these labels (`consensus.py:236-281`).

**RAG-09 — High — Static — Synthesis and matrix runs cannot be reproduced or audited.** No model id, temperature, prompt text or hash, prompt version, embedder identity, or retrieved chunk ids are recorded in `SynthesisResult` (`models.py:219-228`) or in the `SYNTHESIS_GENERATED` / `MATRIX_EXTRACTED` events (`synthesis.py:253-264`, `matrix.py:83-97`). The synthesis event hard-codes `"synthesis_file": "literature/literature_review.md"` (`synthesis.py:262`), while the harness writes `synthesis/literature_review.md` and the CLI writes to `--output`. The ledger therefore names a file that was not written. `build_synthesis_prompt` ignores its `rq_id` argument (`synthesis.py:84`).

**RAG-10 — High — Reproduced — `index_directory` gives every file the same study identity and silently overwrites colliding chunks.** One resolved request supplies the six identity limbs to every `*.md` file in the directory (`indexer.py:304-306`, `363`). Chunks with identical text under the same heading and ordinal in two files mint the same id, and `upsert` overwrites the earlier one (`indexer.py:126`). Using `repro_misc.py` M5 with two papers that both contain `# Funding / None declared.`:

```
result: {'indexed_files': 2, 'total_chunks': 4, 'collection_count': 3}
distinct study_id: {'STU-111...'} | filenames: ['paper1.md', 'paper2.md', 'paper2.md']
```

The reported `total_chunks` (4) overstates what was stored (3). Mitigation: harness Stage 6 uses the typed `index_service.index_workspace` path, which carries per-document requests (`index_service.py:1154-1211`). `index_directory` is still public, exported and documented in the README.

**RAG-11 — Medium — Reproduced/Static — The retriever silently creates empty collections and may query with the wrong embedding function.** Any non-`ValueError` from `get_collection` falls into `get_or_create_collection` (`retriever.py:48-51`). Reproduced (M4): `ScholarRetriever(collection_name="dosc")` created a new `dosc` collection and returned `[]`, which `synthesize` reports as "No relevant evidence found in indexed corpus." (`synthesis.py:296`). Static: on "Embedding function conflict" both the indexer and the retriever re-open the collection *without* an embedding function (`indexer.py:55-57`, `retriever.py:43-45`). Depending on the Chroma version, `query_texts` may then be embedded by Chroma's default function rather than the one that built the index. I did not reproduce this because it needs a second real provider.

**RAG-12 — Medium — Reproduced — Section classification misroutes evidence-bearing sections.** `classify_section` (`models.py:22-88`) matches keyword substrings in a fixed order. Reproduced: `'2.4 Statistical analysis' -> results_empirical`, `'Data analysis' -> results_empirical`, `'Limitations of existing methods' -> methodology`, `'Supplementary material' -> methodology` ("material"), `'Participants' -> other`, `'Outcomes' -> other`. The harness synthesis filters on `results_empirical`, and matrix dimensions filter on `target_section_category`. Evidence in a mislabelled section is therefore excluded without notice: the filter is a hard Chroma `where`, not a ranking boost.

**RAG-13 — Medium — Reproduced — The chunker breaks its size guard, does not keep text verbatim, and records no source location.** Using `repro_misc.py` M6 with `max_chunk_chars=200`, chunk lengths were `[400, 39]`. A sentence longer than the maximum is emitted whole (`chunker.py:500-512`). Sentence-split pieces are re-joined with single spaces (`chunker.py:502,514`), so a chunk is not always a verbatim substring of the extracted text. A `# comment` inside a fenced code block becomes a section heading (M6: sections `['Methods', 'compute stats']`), because `_header_pattern` is applied line by line without tracking fences (`chunker.py:690-711`). `ChunkMetadata` has no character offset, page or PDF locator (`models.py:122-146`), so a citation token cannot be resolved to a checkable location in the source PDF.

**RAG-14 — Medium — Reproduced — The PII redactor wipes DOIs and every number.** `PHONE_PATTERN` (`redactor.py:16`) matches any 1–4 digit run. Using `repro_misc.py` M1:

```
{'doi': '[PHONE REDACTED]/s[PHONE REDACTED]-[PHONE REDACTED]',
 'abstract': 'Accuracy rose from [PHONE REDACTED]% to [PHONE REDACTED]% in [PHONE REDACTED] (n = [PHONE REDACTED]).'}
```

This is applied to every `scholar-rag extract` result (`extractor.py:77`).

**RAG-15 — Low — Static — `LLMExtractor` has several defects.**
- The API key is sent as a URL query parameter (`extractor.py:107`).
- Any failure, including HTTP errors and a missing key, falls back silently to regex heuristics (`extractor.py:69-74`). The heuristic `year` is the first 19xx/20xx anywhere in the text, which can be a reference year (`extractor.py:146-149`).
- The `schema` argument is accepted and ignored (`extractor.py:60-80`).
- `confidence` is a field-presence weight, not a measure of accuracy (`extractor.py:158-165`).

## 4. Research-method fitness

**Is "grounded synthesis" grounded?** No.
- **Without an LLM** (the CLI and the harness both call it this way: `cli.py:672-674`, `src/scholar_harness/pipeline/synthesis.py:111-115`), the "synthesis" is the first line of each of the top 5 chunks, cut to 160 characters, as bullets (`synthesis.py:308-314`). Each bullet is then "verified" against the chunk it was copied from. That check is self-confirming and says nothing about synthesis quality. The output file is still named `literature_review.md`.
- **With an LLM**, uncited sentences are invisible to verification (RAG-02), and "verification" is topical similarity that accepts reversed findings (RAG-01). Citation tokens point to a workspace plus a hash (RAG-03), with no quote or offset (RAG-13).
- There is no `evidence_quote` field on `SynthesisClaim` (`models.py:207-216`). The only quote-level check in the system is in scholar-verify-kit, which per the surface matrix falls back to using `claim_text` itself as the quote. I did not verify that claim here.

**Is "consensus" a real measure?** No. It is a share of studies by majority lexicon label within a greedy Jaccard cluster (`consensus.py:236-281`):
- It has no effect sizes, no direction relative to a defined outcome, and no weighting by sample size, design or risk of bias.
- No heterogeneity statistic is computed.
- Two studies whose sentences both contain "improves" yield `HIGH_CONSENSUS` with `consensus_score = 1.0`.
- In current workspaces it cannot fire at all, because of RAG-03.

The word "consensus" in a review built on this output would be unjustified. At best the output can serve as a reading-order hint for the human reviewer.

**Does matrix extraction meet SLR data-extraction standards?** No.
- Per-cell provenance is one citation token that is not tied to the value (RAG-06), with no quote, page or confidence.
- Missing, not-retrieved and not-reported share one sentinel (RAG-06).
- There is no reviewer field, no second extraction, no agreement measure and no adjudication record. Rows are overwritten on each `extract_all` run (`matrix.py:312-346`).
- The shipped harness path is the period-split heuristic (RAG-05). Section filtering can exclude the sections that matter for population and outcome data (RAG-12).

For a sole-reviewer review, the minimum acceptable use is to treat every cell as a *pointer to a chunk to read*, never as extracted data.

**Recall limits.** Retrieval is pure top-k with hard metadata filters:
- Synthesis uses 5 chunks (RAG-07).
- The matrix uses 3 chunks per dimension per study (`matrix.py:189`). This is scoped per study, which is correct.
- Graph boosting only re-ranks inside 4×k candidates (`retriever.py:204-208`).
- Nothing reports which included studies were not represented, so silent omission is the default failure mode.
- The "CosineSim" in the reported hybrid score is actually `(1+cos)/2` (`retriever.py:232`). That is harmless for ranking but misleading when someone reads the number.

**Reproducibility.** No temperature, model id, prompt version or retrieved set is recorded (RAG-09). The embedder default `all-MiniLM-L6-v2` is not pinned to a revision in the synthesis or retrieval path (`embedder.py:103-106`). Only the typed index path records embedder identity.

## 5. Doc drift

- `tools/scholar-rag-kit/README.md:16` says chunk ids are `chk-<doc_id>-<sec_slug>-<index:02d>`. False: ids are canonical content-addressed `CHK-…` (`chunker.py:121-164`).
- `README.md:19` says the indexer "integrates with … `project.json`". False: identity and metadata are never read from `project.json` (`indexer.py:294-297`).
- `README.md:29-31` and the `synthesis.py:65` docstring promise "automated entailment verification". The check is cosine similarity and accepts contradictions (RAG-01).
- `README.md:33-34` says the kit "extracts 7 standard dimensions". Missing dimensions are filled with hard-coded literals (RAG-04).
- `cli.py:880-893`: the `stats` docstring promises a "section distribution". It prints only the chunk count.
- `models.py:268` documents `consensus_score` as agreed/(agreed+opposing). The code divides by all studies, including neutral ones (`consensus.py:266-281`).
- `docs/kits_surface_matrix.md:489` labels the scholar-protocol-kit dependency "UNDECLARED". It is now declared (`pyproject.toml:33`). The same diagram's "scholar-bib-kit (rag declares, unused in code)" is accurate, and graph-kit and search-kit are unused as well (RAG-21).
- `tools/scholar-protocol-kit/.../models.py:223-226`: `required` "flags papers that omit this dimension". No consumer in scholar-rag-kit implements this (RAG-06).

## 6. Prioritized recommendations

All source fixes belong in the kit's own repository, `nexus-scholar-org/scholar-rag-kit`. Then bump `default_rev` in `.agents/plugins/nexus-scholar/plugins.json` to the new full SHA and re-sync the vendored tree (AGENTS.md hard rule). Harness-side changes (`src/scholar_harness/pipeline/*`) belong in this repository.

| ID | Severity | Effort | Action |
| :--- | :--- | :--- | :--- |
| RAG-03 | Critical | S | Attribute claims, tokens and matrix rows by the stored `study_id` limb (fall back to legacy keys only when it is absent). Put `study_id` and `document_id` in the citation token. Add a multi-study regression test. |
| RAG-02 | Critical | S | Treat every sentence or unit of generated text as a claim. Uncited ones become `UNSUPPORTED`/`UNCITED` and count in the denominator. Set `entailment_rate` to 0 or `None` when no claims exist. |
| RAG-01 | Critical | M | Rename the status to `SIMILAR`/`DISSIMILAR` immediately. For real support, require a verbatim `evidence_quote` that appears in the cited chunk (string match), and optionally add an NLI model. Never emit `VERIFIED` from cosine alone. |
| RAG-04 | Critical | S | Delete the literal defaults in `generate_methodology_matrix` and emit an explicit `NOT_EXTRACTED`. Key rows by `study_id`. Consider removing the command. |
| RAG-05 | Critical | S | Remove the period-split heuristic. Without an LLM, emit `NOT_EXTRACTED` plus the chunk pointer, not a value. Make the harness Stage 7 output state that it contains pointers, not data. |
| RAG-06 | High | M | Store per-cell `{value, status ∈ extracted/not_reported/not_found/error, quote, chunk_id, model, prompt_sha}`. Verify that the quote is in the cited chunk. Surface LLM and validation failures. Honour `required`. Add `extractor_id` so a second reviewer's run can be compared. |
| RAG-07 | High | M | Add per-study coverage to synthesis: retrieve per included study, or report which included studies contributed no chunk. Record retrieved chunk ids in `SynthesisResult`. |
| RAG-09 | High | S | Record model id, temperature, prompt template version and hash, embedder identity and the retrieved chunk ids in results and journal events. Log the actual output path. |
| RAG-08 | High | M | Stop presenting lexicon stance as consensus. Either require a human or LLM stance per claim relative to a declared outcome direction, or rename the output to "topic clusters". Tokenize properly instead of matching space-padded words. |
| RAG-10 | High | S | Make `index_directory` refuse more than one file per identity, or require per-file requests. Report stored count deltas. Deprecate it in favour of `index_workspace`. |
| RAG-12 | Medium | S | Treat section category as a ranking boost, not a hard filter, or fall back to unfiltered retrieval within the same study. Fix keyword precedence (statistical/data analysis to methodology; participants/outcomes). |
| RAG-13 | Medium | M | Record character offsets (and page, when available) per chunk. Split overlong sentences. Track code fences. Keep chunk text verbatim. |
| RAG-11 | Medium | S | Use `get_collection` only on the read path and fail loudly on a missing collection or embedding-function conflict. |
| RAG-14 | Medium | S | Drop the phone regex, or anchor it to phone-like context. Never redact `doi`/`year` fields. |
| RAG-18 | Medium | S | One journal writer that takes an explicit path, routed through the workspace-manager event schema. No CWD walk, no implicit `mkdir`, no silent failure. |
| RAG-16 | Medium | M | Add method-level tests: contradiction, uncited text, multi-study attribution, decimal values, LIST dimensions. Replace the tautological `test_synthesis.py:68`. |
| RAG-17 | Medium | M | Introduce one `LLMClient` protocol (model, temperature, seed, call → text plus metadata). Fix or remove `GeminiEmbedding`, `NumpyBackend` and `VectorBackend`. |
| RAG-15, 19, 20, 21 | Low | S | Header-based API key; drop the dead retry; make clustering order-independent (compare to centroid or all members); remove the unused kit dependencies. |

## 7. Limits of this assessment

- I did not review the 9.4k-line index-governance layer (`index_service`, `index_manifest`, `index_verifier`, `replacement`, `recovery`) line by line. I judged it from its structure, docstrings and test volume. It may contain defects not listed here, and its rigour is inferred, not verified.
- I did not run the full kit suite: only the six research-path test files (92 passed). I did not test cross-platform behaviour.
- LLM behaviour was simulated with stub callables. Real LLM output may differ in how often it omits citations, but the code paths that mishandle uncited text are deterministic.
- RAG-01 used the real default embedder. Other embedders (OpenAI, Gemini) were not tested. Cosine similarity's blindness to negation is a general property, but the exact scores will differ.
- The Chroma embedding-function-conflict path in RAG-11 is a static reading. I did not reproduce it because it needs two real providers.
- Harness consumption was checked only in `src/scholar_harness/`. MCP tools in `tools/scholar-agent-kit` and the downstream scholar-verify-kit quote check were not examined; statements about them are cited as claims from `docs/kits_surface_matrix.md`.
