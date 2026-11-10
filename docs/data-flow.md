# What leaves your computer

Nexus Scholar runs on your computer. Your workspaces are folders on your disk,
the app and its engine run as one process that listens only on this computer
(`127.0.0.1`), and nothing is sent anywhere unless you start one of the actions
below. There is no account, no telemetry, no analytics and no automatic update
check. The app's pages load nothing from the internet; fonts and scripts are
bundled (`apps/research-ui/tests-browser/hygiene.spec.ts` fails the build if a
page reaches any host other than this computer).

This page lists every place where data leaves the machine, what is sent, and to
whom. It was written for M5-slim (2026-11-05) and checked again on 2026-11-10
against the beta 1.1.0b6.

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

## Searching and checking the literature (optional, app or command line)

These run only when you start them, and send **your search terms or the
identifiers of your records** (DOIs, titles), never your decisions:

| Action | Where you start it | Sent to |
| :-- | :-- | :-- |
| Search (a harvest) | Discovery, **Start the harvest** (1.1.0b6); `nexus-scholar run`; `scholar-search`; MCP `nexus_discover` | The databases your protocol selects among OpenAlex, Semantic Scholar, Crossref, arXiv and PubMed (NCBI E-utilities); bioRxiv only when the protocol names it |
| Plan (dry run) | Discovery, **Plan** | Nothing: the strings are translated on your computer |
| Recall check | Discovery, **Recall** (on `main`) | The protocol query, to the protocol's databases; then each seed's identifier to Crossref and OpenAlex for a title check (`scholar_search/recall.py`) |
| Abstract hydration and DOI verification, after a harvest | Part of the same run | Record DOIs (and arXiv ids) to Semantic Scholar, OpenAlex and Crossref (`scholar_search/enrichment.py`, `scholar_search/verifier.py`) |
| Inception reconnaissance (a first pool of up to 25 papers) | CLI wizard, MCP `recon_*` tools, and the console's recon routes (1.1.0b5; the Explore screen is not built) | Your topic as a query, to OpenAlex, Semantic Scholar, Crossref and arXiv |
| Full-text discovery and download (parked, not production) | CLI | Unpaywall, `doi.org` and the publisher sites it points to |
| Citation graph (parked) | CLI, MCP | OpenAlex |
| Verification: retractions and related checks (parked) | CLI, MCP | Crossref, OpenAlex |

With every search request the engine also sends who is asking:

- **Your contact email** (`SCHOLAR_MAILTO`): in the User-Agent header to every
  provider (`scholar-search-kit/0.1.0 (mailto:<address>)`, a stale version
  string), as `mailto` to OpenAlex, which no longer uses it, and as `email` (with
  `tool=nexus-scholar`) to PubMed. A live search refuses to start without it.
- **Your OpenAlex key** (`SCHOLAR_OPENALEX_KEY`), to OpenAlex only, when set.
  OpenAlex has required a key since 2026-02-13; without one, your requests share
  a small daily budget with everyone on your network address.
- **Your Semantic Scholar key** (`SCHOLAR_S2_KEY`), to Semantic Scholar only,
  when set.

Responses are cached on your disk under `.cache/` unless `SCHOLAR_HTTP_CACHE`
is off. Provider details: [`kits/search/PROVIDERS_2026-11.md`](kits/search/PROVIDERS_2026-11.md).

The import path that screening starts from (the Import screen, or
`nexus-scholar accept-corpus` on a file you exported) sends nothing.

## Phones (not yet)

Screening from a phone on your local network arrives with milestone M2. When it
does, it will stay on your network and this page will say what it serves.

## Where to check

- `src/scholar_harness/screening/agent_runs.py` (`DATA_FLOW`, consent, runs)
- `src/scholar_agent/drivers/` (the three providers) and `src/scholar_agent/keys.py`
- `src/scholar_search/providers/` (the search services)
- `src/scholar_harness/console/serve.py` (loopback only)
