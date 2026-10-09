# MCP availability and boundaries

Pinned agent kit (`capabilities.py`, `server.py`). Indexing is owned by
`nexus-scholar-org/scholar-rag-kit`; the MCP server only declares it.

## Availability (do not generalize across rows)

| Tool | Status | Signature / notes |
|---|---|---|
| `nexus_rag_index` | **DECLARED UNSUPPORTED** | `nexus_rag_index(docs_dir, db_path="./chroma_db", bib_file=None, workspace_id=None)` (`server.py:826`) — refuses unconditionally; args accepted for discoverability only, never validated, interpreted, or echoed |
| `nexus_rag_query` | supported | `nexus_rag_query(query, db_path="./chroma_db", section=None, section_category=None, paradigm=None, boost_doi=None, n_results=5, graph_source=None, alpha=0.25, beta=0.15)` (`server.py:876`); single-`boost_doi` seed boost; store default is CWD-relative — pass absolute paths |
| `nexus_rag_synthesize` | supported | `nexus_rag_synthesize(query, rq_id="RQ1", db_path="./chroma_db", section_category=None, paradigm=None, n_chunks=5)` (`server.py:932`); deterministic bullets when no LLM; pass `rq_id` explicitly; no boost/LLM override |
| `nexus_matrix_extract` | supported | `nexus_matrix_extract(workspace_dir=".", protocol_path=None, output_dir="./literature")`; db pinned to `<workspace_dir>/chroma_db` — align by indexing with explicit `db_path=<ws>/chroma_db` |

## The refusal envelope (exact)

Capability `rag_indexing`, `mcp_supported=false`
(`capabilities.py:56`, declaration `capabilities.py:414-429`, message
`capabilities.py:304-318`). Every call returns:

- `operation="rag_index"`, `status="FAILED"`, `artifacts=[]`, `warnings=[]`,
  exactly one non-retryable error with `code="UNSUPPORTED_CAPABILITY"`;
- zero I/O: no store opened, no directory read, no index built, no
  filesystem or audit write (pure builders over the immutable declaration).

It is not a soft "not found" and not a parity claim. Alternatives (the only
supported E3 surfaces, both calling the same T-90 shared service): the
`` `scholar-rag index` `` CLI and the `` `scholar_rag.index_service` ``
Python API (`index_workspace(IndexServiceRequest) -> IndexServiceResult`).

Why declared rather than served: the retired tool hard-coded a
working-directory-relative `db_path`, silently substituted workspace
identity from `project.json` when `workspace_id` was omitted, could not
carry an accepted parent, an embedder identity, or a `PARTIAL` result, and
returned free text (`capabilities.py:67-90`; `server.py:843-851`). Lifting
the boundary is a Packet E3 §9.1 change, not a local tweak.

## Audit events (distinct ledgers)

- Kit run report: `RAG_INDEX_RUN_BUILT` / `RAG_INDEX_RUN_REJECTED`
  (`index_service.py:209`) → the **explicit** journal destination only.
- Legacy paths: `RAG_QUERY_RETRIEVED` (retriever), `SYNTHESIS_GENERATED`
  (synthesis), `MATRIX_EXTRACTED` (matrix runs).
- Harness continuity / §6.6 accepted-record events are **not** this kit's
  to emit (the accepted-record event belongs to the future
  `index-acceptance-v1` adapter).

## Legacy vs current (say exactly this)

- Current typed path: `scholar_rag.index_service.index_workspace`
  (`index_service.py:752`) — explicit request limbs, accepted `parent_view`,
  embedder identity, explicit journal/docs destinations.
- Superseded: `ScholarIndexer.index_markdown/index_directory` upsert
  (`indexer.py:84,280`, `collection.upsert` at `indexer.py:126`) — Stage 6
  no longer uses it (harness keeps only a monkeypatch stub,
  `src/scholar_harness/orchestrator.py:58`; Stage 6 calls
  `index_workspace`, `orchestrator.py:1425`). Do not route new indexing
  through it, and do not present `matrix`'s no-`--protocol` fallback or
  `stats` (which still read through it) as publication.

## Identity rules (every surface)

Recorded-artifact-only: nothing is inferred from `project.json`, a title,
the CWD, a DOI, a filename, or a document's own frontmatter
(`indexer.py:294`, `chunker.py:18-28`). The legacy MCP indexer's silent
`project.json` substitution is exactly what the declaration removes — never
reintroduce it by hand.
