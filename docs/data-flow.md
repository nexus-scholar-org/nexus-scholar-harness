# What leaves your computer

Nexus Scholar runs on your computer. Your workspaces are folders on your disk,
the app and its engine run as one process that listens only on this computer
(`127.0.0.1`), and nothing is sent anywhere unless you start one of the actions
below. There is no account, no telemetry, no analytics and no automatic update
check. The app's pages load nothing from the internet; fonts and scripts are
bundled (`apps/research-ui/tests-browser/hygiene.spec.ts` fails the build if a
page reaches any host other than this computer).

This page lists every place where data leaves the machine, what is sent, and to
whom. It describes version 1.0.0 as of 2026-11-05 (M5-slim).

## Screening with an AI model (optional)

Screening never needs an AI model. If you run **agent proposals** (screen 06),
the engine sends, for each record in the run:

- the record's **title, abstract and publication year**, and
- your protocol's **screening criteria**,

to the provider you chose, and stores the model's draft in the workspace. Your
decisions, notes, names and the rest of the workspace are not sent.

| Provider | Where it goes | Key |
| :-- | :-- | :-- |
| Anthropic | `api.anthropic.com`, or the host in `ANTHROPIC_BASE_URL` if you set it | your own, from `nexus-scholar keys set anthropic` |
| OpenAI-compatible | the base URL you type on screen 06 (it can be a model on your own computer) | your own, if the endpoint needs one |
| Google Gemini | `generativelanguage.googleapis.com` | your own, from `nexus-scholar keys set gemini` |

- Nothing is sent until you tick **consent** for that provider on screen 06. The
  consent (provider, model, prompt fingerprint, date and the sentence above) is
  written to `literature/screening/agent_consent.json` and to the audit journal.
- **Keys** stay in your operating system's keychain, or in your environment if you
  put them there. They are never written to a workspace, a config file, the
  journal or the browser.
- What the provider does with the data is governed by **your** agreement with it
  (for example, whether it keeps or trains on API inputs). Check those terms
  before you consent, especially for unpublished or confidential records.
- A **cost ceiling** you set stops the run; the estimate comes from a dated price
  table, not from the provider.

## Screening with your own Claude (MCP, optional)

If you connect Claude Desktop or Claude Code to the `scholar-agent` MCP server,
your Claude reads records from the workspace through the server's tools
(`nexus_screening_queue`, `nexus_screening_record`) and submits drafts with
`nexus_submit_proposal`. The record text then goes to Anthropic **through your
Claude app, under your Claude account's terms**, not through Nexus Scholar.
The MCP server itself runs on your computer and holds no key.

## Searching and checking the literature (optional, command line)

These run only when you start them, and send **your search terms or the
identifiers of your records** (DOIs, titles), never your decisions:

| Action | Sent to |
| :-- | :-- |
| Search (`scholar-search`, discovery, inception reconnaissance) | OpenAlex, Crossref, PubMed (NCBI E-utilities), arXiv, bioRxiv, Semantic Scholar |
| Full-text discovery and download (parked, not production) | Unpaywall, `doi.org` and the publisher sites it points to |
| Citation graph (parked) | OpenAlex |
| Verification: retractions and related checks (parked) | Crossref, OpenAlex |

The import path that screening starts from (`nexus-scholar accept-corpus` on a
file you exported) sends nothing.

## Phones (not yet)

Screening from a phone on your local network arrives with milestone M2. When it
does, it will stay on your network and this page will say what it serves.

## Where to check

- `src/scholar_harness/screening/agent_runs.py` (`DATA_FLOW`, consent, runs)
- `src/scholar_agent/drivers/` (the three providers) and `src/scholar_agent/keys.py`
- `src/scholar_search/providers/` (the search services)
- `src/scholar_harness/console/serve.py` (loopback only)
