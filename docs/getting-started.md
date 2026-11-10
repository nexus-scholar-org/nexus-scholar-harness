# Getting started: install Nexus Scholar and screen your first review

This guide takes you from nothing to a published screening with an exported
reference list. It takes about 15 minutes, plus the time you spend screening.
Everything runs on your computer. No account or API key is needed to screen (the AI
agent is optional and not covered here).

The commands are the same on Windows (PowerShell), macOS and Linux unless a
step says otherwise. This guide is for the beta, version **1.1.0b6**. To check
the version you have, run `nexus-scholar --version`.

## 1. Install uv (once)

[uv](https://docs.astral.sh/uv/getting-started/installation/) installs and runs
Python for you, including Python itself. Install it, close and reopen your
terminal, then check it:

```bash
uv --version
```

## 2. Install Nexus Scholar

```bash
uv tool install "nexus-scholar>=1.1.0b6"
```

The version in the command is needed while Nexus Scholar is in beta: it lets uv take a beta of Nexus Scholar without taking betas of anything else. Do not use `--prerelease allow`: it also takes development releases of other packages, and one of them stops the app from starting. The command installs the `nexus-scholar` command for your user. Check it:

```bash
nexus-scholar --version
```

It should print `nexus-scholar 1.1.0b6`. You can now run `nexus-scholar` from any
folder, and you do not need to activate anything. If you use pip instead of uv:
`pip install "nexus-scholar>=1.1.0b6"`.

## 3. Start the app and create a workspace

```bash
nexus-scholar ui
```

Your browser opens on **Workspaces**. Each review is one folder; by default
they live in `Documents/Nexus Scholar/workspaces` (choose another folder with
`nexus-scholar ui --root <folder>`). Keep the terminal open: the app runs there,
and it is where approval codes appear later. Stop the app with **Ctrl+C**.

Click **New workspace**, type your review's title, and create it. Then open it.

> **About the protocol.** A workspace made this way has a placeholder protocol
> (shown as a draft). It is enough to try the app. For a real review, write your
> question and your inclusion and exclusion criteria first, with **New review**
> (below) or with the guided interview in the terminal:
> `nexus-scholar init "Your review title" --dir "<your workspaces folder>/<review-name>"`
> (beta). The folder you give becomes the workspace, so give a new folder inside
> your workspaces folder, then open it in the app.

### Write the protocol in the app (Inception)

On **Workspaces**, click **New review**. It opens your drafts; start a new one
or resume one. The steps are:

1. **Scope.** What is the review about: the topic, the years and the languages.
2. **Shape.** The lens (paradigm) and playbook, the unit of analysis, what
   proof a reviewer would accept, what is out of scope, and the research
   questions. The lens the engine leans to and its draft question are shown as
   drafts; nothing is used until you choose it.
3. **Concepts and criteria.** The concepts the search uses and the screening
   criteria, each shown word for word with where it came from. A criterion the
   engine wrote needs your **Accept**; one you typed is accepted by default. A
   rejected criterion is not used.
4. **Review and create.** Nothing is written until you press **Create the
   workspace**. If the folder already holds a workspace, the screen offers to
   replace it and keep a backup; if it has screening decisions, you type the
   workspace's name to confirm.
5. **Done.** The folder and the protocol's fingerprint, and a link to open the
   workspace.

The step bar also shows **Explore** and **Direction** (the grounded search of
a first pool of papers). They have no screen yet; the CLI wizard
(`nexus-scholar inception`) and the MCP tools still have them. Every save is
checked against the draft's last update, so a second tab cannot overwrite your
work without telling you.

## 4. Import your search results

Export your search results as **RIS** from each database you searched (Scopus,
Web of Science, IEEE Xplore, or a reference manager such as Zotero). From
**PubMed**, use *Send to → Citation manager*: the `.nbib` file it downloads is
imported as it is. Then open the **Import** step in the app (it is in the steps
bar until the corpus is accepted, and on the screening home):

1. **Add a database file.** Choose the RIS or `.nbib` file and type the
   database's name.
   Under **Search details** you can add the date you searched and the exact
   search string. Both are optional, and both are what PRISMA asks you to
   report. A database you exported in parts: add each part under the same name,
   and the parts are added up.
2. **Check the counts.** The app shows the records found in each database, the
   duplicates it will remove (same DOI, or the same title, first author and year
   one year either way) and the studies left to screen. These are the numbers
   for your PRISMA flow diagram.
3. **Accept and freeze the corpus.** Screening starts from it, so after this no
   database can be added or removed.

Each file is copied unchanged into the workspace (`literature/raw/ris/`), and
every step is recorded in its audit journal. Prefer the terminal? The same
import is one command:
`nexus-scholar accept-corpus --workspace "<workspace folder>" --ris "Scopus=<scopus>.ris" --ris "Web of Science=<wos>.ris"`.

### Or search the free databases from the app (Discovery)

> **New in 1.1.0b6.** The Discovery screens have not been tried by a second
> person yet ([release notes](releases/1.1.0b6.md)). Before 1.1.0b6 the same
> search ran from the terminal: `nexus-scholar run`, which still works.

Discovery searches the free databases your protocol selects (among OpenAlex,
Semantic Scholar, Crossref, arXiv and PubMed) with
the query your protocol compiles, and records what each database was asked and
what came back. Two settings are needed before you start the app:

- **`SCHOLAR_MAILTO`**, your contact email. A search refuses to start without
  it (`MAILTO_NOT_SET`), and the Plan screen prints the line to set.
- **`SCHOLAR_OPENALEX_KEY`**, a free OpenAlex API key. OpenAlex has required a
  key since 2026-02-13. A search that includes OpenAlex refuses to start without
  it (`OPENALEX_KEY_NOT_SET`), and the Plan screen prints the line to set. To
  search without OpenAlex, leave it out of the protocol's databases.

Set both in the terminal before `nexus-scholar ui`, or put them in a `.env`
file in the folder you start the app from (`SCHOLAR_MAILTO=you@university.edu`).
Then open **Discovery** in the header. The entry page says where the search
stands, and the steps are:

1. **Plan.** The exact string each database will receive, and what it cannot
   express. Nothing is sent.
2. **Recall** (optional). Give papers you already know are relevant; the check
   says which databases find them. It never changes the query.
3. **Harvest.** **Start the harvest**. Each database appears as it finishes,
   with the total it reported and how many records it returned. A database that
   stops at the cap reads "at least N".
4. **Import.** The import screen above. For now a corpus is either a harvest or
   imported exports, not both: add exports before the first harvest, or harvest
   and skip this step.
5. **Duplicates.** How many records were merged, by rule (identifier, exact
   title, close title). Pair-by-pair review is not built.
6. **Report.** The PRISMA-S identification per database and a methods
   paragraph you mark as reviewed.
7. **Hand-off.** **Accept this corpus** freezes it, and screening starts from it.

A harvest does not freeze anything by itself; only the Hand-off accept does.
What the search sends, and to whom, is in [data-flow.md](data-flow.md).

## 5. Screen

Go to **Screening**. The steps are across the top:

1. **Prepare.** Check the settings, then **Prepare batches** → **Prepare now**.
   The settings are:
   - the batch size (5 to 100 records);
   - whether an agent's drafts are hidden until you decide;
   - what happens after you decide (show the draft, or move on at once);
   - whether you see every record.

   After a few seconds it says "Batches prepared".
2. **Agent proposals** (optional). Skip it to screen on your own.
3. **Triage.** Read each record and answer the criteria until the decision is
   clear (keys **1** yes, **2** no, **3** not reported). Exclude is ready as soon
   as one criterion fails, and its reason is taken from that criterion, so
   **E** then **Enter** excludes. Include is ready when every inclusion criterion
   is yes. Unclear (goes to full text) is always possible. Your decisions are
   saved as you go. With no agent draft, the next record opens by itself; with a
   draft, it shows after your decision and **N** moves on (or choose "move on at
   once" on Prepare). Identifiers and record
   details are under **Details**.
4. **Agreement.** Only meaningful if an agent proposed drafts.
5. **Publish.**
   1. Type your name under **Approver** and **Save name**. Approvals are recorded
      under it; it is a name typed on this computer, not a verified sign-in.
   2. For each batch, click **Show a code in the terminal**, read the code in the
      terminal where the app runs, type it, and approve.
   3. When every check passes, **Publish the screening**.

   A decision changed after publishing makes the screening read "Published,
   decisions since": publish again so the exports match.

## 6. Export and write your methods

After publishing, **Export and methods** appears on the screening home and on
Publish.

- **Download** a RIS file (included and unclear records) to import into Zotero,
  EndNote or Mendeley, or a CSV with every record, its decision and its reason.
- **Copy paragraph** gives a methods paragraph with your PRISMA counts, the
  databases and dates you searched, and how AI drafts were used. It is a draft
  written from your workspace files: check every number before you use it.

## Where your work lives

Everything is in the workspace folder:
- your records;
- your decisions;
- the published lists and the PRISMA report;
- `audit/journal.jsonl`, the append-only record of every step.

Back it up like any other research data. What leaves your computer, and when, is
listed in [data-flow.md](data-flow.md).

## Updating

```bash
uv tool install --force "nexus-scholar>=1.1.0b6"
```

Then check `nexus-scholar --version`. During the beta, finish a screening on the
version you started it with when you can; reading a workspace across versions
is not yet tested.

## Troubleshooting

| What you see | What to do |
| :-- | :-- |
| `nexus-scholar` is not found | Run `uv tool update-shell`, then open a new terminal. |
| `uv tool install` says no version matches, or installs 1.0.0 | Keep the version in the command: `"nexus-scholar>=1.1.0b6"` (the beta is a pre-release). |
| The app stops at start with `No module named 'httpcore'` | It was installed with `--prerelease allow`. Reinstall: `uv tool install --force "nexus-scholar>=1.1.0b6"`. |
| "No accepted corpus" (`SNAPSHOT_NOT_ACCEPTED`) | Import and accept your search results (step 4). |
| `MAILTO_NOT_SET` before a search | Set `SCHOLAR_MAILTO` (and `SCHOLAR_OPENALEX_KEY`) as in step 4, Discovery, then start the app again. |
| `OPENALEX_KEY_NOT_SET` before a search | Set `SCHOLAR_OPENALEX_KEY` as in step 4, Discovery, then start the app again, or leave OpenAlex out of the run. |
| `VERIFIED_EXISTS` when adding an export | A search already ran in this workspace. For now a corpus is a harvest or imported exports, not both. |
| "No records in this file" (`SOURCE_NOT_RIS`) | Export the results as RIS (`.ris` or `.txt`) from the database, or as `.nbib` from PubMed (Send to → Citation manager), not as CSV or BibTeX. |
| "File too large" (`SOURCE_TOO_LARGE`) | Export in parts of under 50 MB and add each part under the same database name. |
| `OPERATOR_CONTEXT_MISSING` when approving | Save your name under **Approver** on the Publish screen, then ask for a new code. |
| `APPROVAL_CONTENT_CHANGED` when publishing | A decision changed after the last approval. Approve the last batch again (a new code), then publish. |
| A card with a code in capitals | The card says what happened and the next step; the code is what to quote if you ask for help. |
| You are not sure which workspace is open | The terminal prints its folder when it starts or switches. To list only one folder's workspaces, start with `nexus-scholar ui --root <folder>`. |
| The browser did not open | Start with `nexus-scholar ui --no-browser` and open the one-time link it prints. |

For the command line, configuration and the AI agent, see the
[user guide](nexus_scholar_user_guide.md). Beta testers: see [the beta page](beta/README.md).

## Appendix: install from the source code (developers)

You need Git, uv and Node.js 22. Then:

```bash
git clone https://github.com/nexus-scholar-org/nexus-scholar-harness.git
cd nexus-scholar-harness
npm --prefix apps/research-ui ci
npm --prefix apps/research-ui run build:export
uv build --wheel
uv tool install --force dist/nexus_scholar-1.1.0b6-py3-none-any.whl
```

The wheel's file name carries the version in `pyproject.toml`. If the app opens
with an old look or says it has no app bundle, `build:export` did not finish:
run it again, check that no line says `Failed`, then repeat the last two
commands.
