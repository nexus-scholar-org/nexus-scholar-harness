# Phase 5 — Harness Console UI Component Architecture

> **Source of Components:** Tailwind CSS Plus (Tailwind UI) Catalog  
> **Target File:** [`src/scholar_harness/console/static/index.html`](../../src/scholar_harness/console/static/index.html)  
> **Styling Framework:** Tailwind CSS v4 (Dark Theme Default)

---

## 1. Selected Components & Taxonomy Mapping

The table below catalogs the official Tailwind Plus components selected for each Phase 5 screen defined in [`SPECS.md`](./SPECS.md) §9:

| Screen / Area | Tailwind Plus Component | UUID / Slug | Catalog Category | Purpose in Harness Console |
| :-- | :-- | :-- | :-- | :-- |
| **Global App Shell** | `dark-sidebar-with-header` | `5548358cb34897c6b28551f2ad885eec` | Application Shells > Sidebar Layouts | Root layout with workspace badge, pipeline navigation, and status header |
| **Dashboard** | `simple-in-cards` | `b4c225b72dcb3b747e6d6ffcf44b1a9d` | Data Display > Stats | 4-card PRISMA funnel & evidence metrics (Candidates, Screened, PDFs, Trust) |
| **Literature Database** | `simple-in-card` | `4738eac883e67bf84a9f7db2446e838a` | Lists > Tables | Candidate & included studies list with search, DOI links, and status badges |
| **Screening Room** | `list-with-description` | `5a30657598f3154f9bc03a680cea7ff4` | Forms > Radio Groups | Inclusion / Exclusion / Uncertain human decision recorder with reason codes |
| **Trust Badges** | Catalyst `badge` | `catalyst/badge.jsx` | UI Kit > Catalyst | Trust level pill indicators (`STRONG`, `ADEQUATE`, `WEAK`, `UNVERIFIED`, `BLOCKED`) |
| **Action Cards** | `with-actions` | `59743e93ed6676a0284e9f2ab10ac8f6` | Feedback > Alerts | Action runner cards and notification states |
| **Agent Exchange** | `simple-table` | `4bf0d3a6dd46681182cd9e2d9bc2af66` | Lists > Tables | D6 parity mapping table showing exact `uv run` commands and MCP tools |
| **Audit Ledger** | `stacked-list` | `b54103077fe282f9cb98536080d9bcd0` | Lists > Stacked Lists | Timeline of append-only events from `audit/journal.jsonl` |
| **Inspection Modal** | `simple-with-dismiss-button`| `f89a7babb527a1909590ce2fa868a45d` | Overlays > Modal Dialogs | Paper abstract & raw JSON inspection drawer |

---

## 2. Key Architecture Decisions

1. **No-Build Standalone Console:**
   - Evaluated directly in any browser or served via FastAPI `scholar-harness serve` (M5.1).
   - Powered by the native `@tailwindcss/browser@4` runtime without needing a Node.js/Webpack build chain.

2. **D6 Agent-Agnostic Parity:**
   - The UI surfaces the exact `uv run <command>` and `nexus_*` MCP tools for every action button.
   - Any manual click can be reproduced 100% headlessly by opencode, Claude, or CI scripts.

3. **Grounded with Real Workspace Data:**
   - Styled against the real artifacts of `workspaces/uav-cv-precision-agriculture` (1,029 candidates, 94 included, 12 consensus clusters, 0 retractions).
