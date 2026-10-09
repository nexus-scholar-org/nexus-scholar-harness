# Toolkit Path Routing Matrix

When operating on an active project (e.g. `workspaces/<P>/`), all Nexus Scholar tools MUST strictly route their inputs and outputs inside `workspaces/<P>/`.

This matrix states **workspace-relative paths only**. Exact kit CLI flags live
in the owning `scholar-*-kit` skills and are not duplicated here (no volatile
duplication); verify flags there before running.

---

## Tool Execution Reference

| Pipeline Stage | Tool / CLI | Canonical Input | Canonical Output | Command Example |
| :--- | :--- | :--- | :--- | :--- |
| **1. Discovery & Search** | `scholar-search-kit` | User Query / Query Tokens | `workspaces/<P>/literature/raw_search.json` | `uv run scholar-search search "<query>" --limit 50 --output workspaces/<P>/literature/raw_search.json` |
| **2. Deduplication** | `scholar-search-kit` | `workspaces/<P>/literature/raw_search.json` | `workspaces/<P>/literature/deduped.json` | `uv run scholar-search dedup workspaces/<P>/literature/raw_search.json --output workspaces/<P>/literature/deduped.json` |
| **3. Verification & Hydration** | `scholar-search-kit` | `workspaces/<P>/literature/deduped.json` | `workspaces/<P>/literature/verified.json` | `uv run scholar-search import workspaces/<P>/literature/deduped.json --verify --enrich --output workspaces/<P>/literature/verified.json` |
| **4. Citation Snowballing** | `scholar-search-kit` | Seed Paper ID (e.g. `W...`) | `workspaces/<P>/literature/snowball_citing.json` | `uv run scholar-search snowball <seed_id> --direction forward --output workspaces/<P>/literature/snowball_citing.json` |
| **5. PDF Download** | `scholar-pdf-kit` | `workspaces/<P>/literature/verified.json` | `workspaces/<P>/pdfs/*.pdf` | `uv run scholar-pdf download --input workspaces/<P>/literature/verified.json --output workspaces/<P>/pdfs/ --smart-names --export json` |
| **6. Manual PDF Ingest** | `scholar-pdf-kit` | Local PDF + DOI | `workspaces/<P>/pdfs/*.pdf` | `uv run scholar-pdf ingest <file.pdf> --doi <doi> --output workspaces/<P>/pdfs/ --smart-names` |
| **7. Fulltext Extraction** | `scholar-pdf-kit` | `workspaces/<P>/pdfs/` | `workspaces/<P>/extracted/*.md` | `uv run scholar-pdf extract workspaces/<P>/pdfs/ --output workspaces/<P>/extracted/ --engine docling` |
| **8. Bibliographic Export** | `scholar-search-kit` | `workspaces/<P>/literature/verified.json` | `workspaces/<P>/exports/` (e.g. `references.csv`) | `scholar-search export` → `workspaces/<P>/exports/` (flags: see scholar-search-kit skill) |
| **9. Graph & RAG Indexing** | `scholar-rag-kit` | `workspaces/<P>/extracted/` | index under `workspaces/<P>/` (see scholar-rag-kit skill) | `scholar-rag index` → workspace index (flags: see scholar-rag-kit skill; RAG indexing is not available via MCP) |

---

## Agent Enforcement Rules

1. **Never write outside `workspaces/<P>/`**: Do not write temporary data into `tools/`, the workspace root, or home directory.
2. **Deterministic File Handoffs**: Always verify that the predecessor output file exists before invoking the next tool in the pipeline.
3. **Manifest Upkeep**: After executing bulk operations, update `project.json` stats (`discovered_papers`, `downloaded_pdfs`, etc.).
