---
name: workspace-manager
description: Instructions for initializing, managing, and routing research data into structured project workspaces in the workspaces/ directory.
---

# `workspace-manager` Skill Instructions

You are the central project orchestration agent for the Nexus Scholar Suite. Your job is to isolate literature, PDFs, extractions, and synthesis files into dedicated project directories under `workspaces/<project-slug>/` rather than polluting tool folders or the workspace root.

## Core Responsibilities
1. **Scaffold Projects**: Initialize standardized research project workspaces inside `workspaces/<project-slug>/`.
2. **Resolve Active Project**: Detect the active research project or prompt the user to choose or create one.
3. **Enforce Canonical Tool Paths**: Direct all toolkit commands (`scholar-search`, `scholar-pdf`, `scholar-rag`, etc.) to read from and write to the active project folder.
4. **Maintain State & Manifests**: Update `project.json` stats as research progresses.

---

## Canonical Project Structure

Every project in `workspaces/<project-slug>/` adheres to this layout:

```text
workspaces/<project-slug>/
├── INDEX.md                # Master human-readable index and status catalog
├── project.json            # Project manifest (title, RQs, keywords, stats)
├── audit/                  # Append-only journal.jsonl & verification audit logs
│   └── SCREENING_CRITERIA.md # Rendered PRISMA Inclusion / Exclusion rulesdger of all executed actions
├── literature/             # Search results (raw_search.json, deduped.json, verified.json)
├── pdfs/                   # Downloaded PDFs & download_summary.json
├── extracted/              # Markdown (Docling) or TEI XML (Grobid)
├── synthesis/              # Literature review notes, comparative tables
└── exports/                # Reference exports (BibTeX, CSV, RIS)
```

---

## Logging Every Action (Append-Only Event Ledger)

After executing any major step (Search, Dedup, Verify, Screen, PDF Download, Extraction), log the action to `audit/journal.jsonl` and refresh `INDEX.md`:

```bash
uv run python .agents/skills/workspace-manager/scripts/log_event.py <project-slug> \
  --action DISCOVERY_SEARCH \
  --agent scholar-search-kit \
  --description "Federated search across 5 query clusters" \
  --outputs workspaces/<P>/literature/raw_search.json
```

Or via Python:
```python
from log_event import log_project_event
log_project_event(project_path, action="VERIFICATION_HYDRATION", agent_or_tool="scholar-search-kit", description="...", outputs=[...])
```

---

## Detailed References

- [Project Schema & State](references/project_schema.md): `project.json` specification and directory semantics.
- [Audit & Event Ledger Spec](references/audit_trace_spec.md): `audit/journal.jsonl` schema and `INDEX.md` format.
- [Tool Routing Matrix](references/tool_routing_matrix.md): Comprehensive routing table for all suite tools.
