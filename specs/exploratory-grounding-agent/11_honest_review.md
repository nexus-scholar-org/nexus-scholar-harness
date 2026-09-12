# 11 — Honest Engineering Review

> **Status:** Post-implementation, post-M0.1…M0.5 retrospective. Written 2026-09-13 after a live end-to-end smoke on a real topic.
> **Author standpoint:** the same agent that designed, built, and reviewed the feature. That is a conflict of interest — read every compliment with suspicion and every complaint as the statement most likely to survive scrutiny.
> **How to read:** this is a *review for the human*, not an acceptance gate. Milestones M0.1–M0.5 already passed coder/tester/reviewer DoD. This document judges whether those DoDs tested the *right* things.

---

## 1. Verdict in one paragraph

The feature is **real, deterministic, auditable, and works end-to-end** — the live probe→distill→delta chain returned a 25-doc pool with anchored schools, metrics, datasets, auto-triggered gap probes, and capped merges, all through the running MCP server. It is also **more brittle than the green test suite suggests**: the "taxonomy" is a keyword-co-occurrence model dressed up as field-agnostic science, the gap-signal metrics degrade to pool-relative noise on real pools, and the cross-field claim (T4.5) is really "configurable," not adaptive. None of this blocks shipping; all of it should be read before trust is placed in the direction proposals.

---

## 2. What is genuinely strong

| # | Claim | Why it holds |
|---|-------|--------------|
| 1 | **Hermetic determinism** | `distill_pool` and `plan_followups` are byte-deterministic; the injection seam (`search_fn` / `RECON_SEARCH_FN`) makes the entire network surface a pure dependency. This is rare and valuable. |
| 2 | **No heavy deps** | Stdlib + regex. Zero new packages. The "no sklearn/keybert/LLM" rule (M0.1.3) kept the deployable tiny and the logic inspectable. |
| 3 | **Literal anchor discipline** | M0.3's DoD-3 got enforced hard (concepts ship only if anchored; synonyms drop; empty pool aborts). After the reviewer BLOCKED, the fix was real, not cosmetic. |
| 4 | **Lineage by construction** | `cache_key` on every artifact and result; content-addressed pool/terms files; session state on disk surviving across turns. This is the FAIR part of M0.5 and it is genuinely FAIR. |
| 5 | **Workspace purity** | Refusal of any `workspaces/`-rooted path, case-insensitively. This repo's #1 footgun, closed in three separate places. |

The three-person loop (coder/tester/reviewer) caught real bugs that zero of us would have caught solo: a case-insensitive guard bypass, the unanchored-terms blocker, and the distiller's legacy-format conflict. That process is the strongest artifact of this session.

---

## 3. What I do not trust as much as the tests suggest

### 3.1 The micro-taxonomy is query-term-noise dominated

Live run, topic *"grape disease detection deep learning edge deployment"*:

```
deep 20 · learning 19 · deep learning 18 · detection 18 · disease 14
```

The entire top of the taxonomy is a restatement of the query. Pure term frequency on a pool *seeded by the query* cannot separate "what the field talks about" from "what my query forced into the pool." Symptoms:

- the real domain texture lives **only** in the schools/metrics/datasets layers, which are keyword tables, not learned structure;
- `remove_unanchored` filters by pool membership, which is exactly the thing the pool *guarantees* for queried terms — it filters nothing meaningful at the top;
- there is no idf/relevance normalization and no stopword treatment for topic terms.

**Fixing this is the highest-value next step.** A relative-frequency or tf-idf-vs-pool term in `micro_taxonomy` would make direction-ranking actually informative. It stays stdlib (a `Counter` + a baseline corpus) and would not violate the determinism/purity constraints.

### 3.2 "Cross-field" (T4.5) is configuration, not generalization

The `DomainLexicon` move was correct and honest — tables are now pluggable, `merge_lexicons` is well-behaved, and the bidirectional isolation tests pass. But the honest framing is: *we relocated the hard-coding, we did not remove it.* A new field (oncology, education, robotics) must still hand-author metric/dataset/school regex patterns. The pipeline will never *discover* that "TCGA" is a dataset on its own.

That is fine as a v1 contract, but the spec language "work across any research field" is only true when a human supplies a lexicon. Recommended framing in docs: **domain-agnostic by default, domain-confident by registration** — and ship 1-2 example lexicons so the registration ceremony is copy-pasteable.

### 3.3 The gap signal ("1 direct hits, 20 adjacent") is pool-relative noise

The reason string is well-formed, deterministic, and honest to its formula — but the formula's *adjacent* term counts any pool doc sharing a micro-taxonomy token with the school's anchors. On a 25-doc pool where 18-20 docs all contain "deep/learning/detection", "20 adjacent" carries no information — it is pool-saturation, not evidence-of-adjacency. The live smoke exposed this immediately; the hermetic fixtures never did because their pools were engineered for shape, not realism.

Options, honest ranking:
1. **Tightest:** exclude pool-ubiquitous terms (top-K by frequency, or terms ≤ some doccoverage threshold) when scoring adjacency.
2. **Middle:** cap "20 adjacent" at the school's own anchor neighborhood plus non-query co-terms only.
3. **Softest:** accept it and document that adjacency is naive (current state). I would not ship this as-is into a research-facing direction proposal — "2 direct hits, 18 adjacent" reads like confidence the model does not have.

### 3.4 Schools are keyword syllabi, with all the false-positive risk acknowledged (and embraced)

`distiller._schools` warnings are profile-brutally accurate ("drone" → bee drones, "transformer" → power grids). For a *directional taxonomy* this is acceptable — but a downstream consumer must never read schools as ground truth. There is no citation-clustering or co-keyword graph here; a school is "docs whose text matches this regex," nothing more. The confidence contract (M0.4 T4.2) labels these gaps with near-certainty language; near-certainty is not warranted. Keep the strings, soften the marketing.

### 3.5 The MCP seam is a smell that works

The server imports harness `scholar_harness.recon` by walking up parents to find `src/scholar_harness/recon/__init__.py` and injecting it on `sys.path` (Option B). It is documented, robust (no CWD assumptions), env-overridable, and the only viable option short of installing the harness into the kit's venv. None of that changes that the *live* process resolved its cache root to `tools/scholar-agent-kit/.cache/inception_recon/…` (kit-relative CWD), while the pytest hermetic tests wrote kit-untouched `.cache` roots. Two sources of truth for where findings live is a self-inflicted footgun:

- **Recommendation:** set a canonical `NEXUS_RECON_ROOT` (defaulting to the harness root `.cache`) in `mcp_config.json`, and make `RECON_CACHE_ROOT` read it. One sentence in the schema spec; real cross-component consistency.

### 3.6 The wizard will surprise by hard-stopping

M0.3's contract is admirable (nothing unanchored ships) but the UX is a cliff: an unanchored concept raises `typer.Exit`, and an empty pool aborts the whole `--grounded` run with guidance. For a researcher, that is a dead end one keystroke away from a non-grounded run they did not ask for. Consider, in M0.6+: offer *"retry refined topic / continue ungrounded (documented)"* instead of a hard exit. Strict in the *data contract*, gentle in the *human path*.

---

## 4. Cross-cutting engineering notes

- **Unexpected cost center:** the encoding slip during checklist bookkeeping (PowerShell `Set-Content` double-encoded em-dashes). This produced the only "surprise" of the session that looked like a user-visible defect. Lesson recorded: use `Write`/`Edit`, never PowerShell text re-encodes, for tracked markdown.
- **Test philosophy tension:** hermetic tests give confidence in *shape*; the live smoke gave confidence in *reality* — and they disagreed (adjacency saturation). Going forward, treat "one live probe per milestone" as a mandatory reviewer step, not a QA afterthought.
- **Untracked-then-committed:** the `recon/` package was untracked until this commit; schema-table diffs are now auditable. Good. Note that this means the M0.2 "verbatim DEFAULT_LEXICON" claim was verified by parity tests, not by diff — the historical baseline commit `c873c48` is now the diff anchor.
- **PR-split (done):** scaffold → wizard → MCP → docs, four commits, each independently reviewable.

---

## 5. Prioritized recommendations

| P | Item | Where | Effort |
|---|------|-------|--------|
| P1 | Relative-frequency/coverage normalization in `micro_taxonomy` (kill query-term dominance) | `recon/distiller.py` | M |
| P1 | Adjacency scoring that excludes pool-ubiquitous terms | `recon/adaptive.py` | S |
| P1 | Canonical recon root (env in `mcp_config.json`) | `server.py` + `mcp_config.json` | S |
| P2 | Soften wizard hard-exit into "refine / continue ungrounded (documented)" | `inception.py` | S |
| P2 | Ship 1-2 example domain lexicons (education, oncology) | `recon/lexicon.py` | S |
| P2 | Reframe docs: "domain-agnostic by default, domain-confident by registration" | `09_mcp_integration.md` | XS |
| P3 | Co-keyword/citation clustering for schools (stay stdlib) | `recon/` | L |
| P3 | Confidence strings: add a `saturation` qualifier ("N of ≤25 pool") | `recon/adaptive.py` | S |

---

## 6. Final word

This is a **solid v1 of a deterministic grounding harness** — the kind of thing that will reliably and reproducibly tell a researcher what the literature surface *around a query* looks like, with every number traceable to a DOI-laden pool. It is not yet a *semantic* understanding of that surface: keywords-pattern taxonomy, configuration-not-generalization lexicons, and naive adjacency all understate the gap between what the pipeline says and what a domain expert would mean. The honest headline for the PR is:

> Deterministic, traceable literature grounding for inception, v1 — with the caveat that its "understanding" is keyword-co-occurrence until P1-P3 land.