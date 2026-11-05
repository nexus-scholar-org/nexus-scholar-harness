# Getting started: install Nexus Scholar and screen your first review

This guide takes you from nothing to a published screening with an exported
reference list. It takes about 20 minutes, plus the time you spend screening.
Everything runs on your computer. No account or API key is needed (the AI
agent is optional and not covered here).

The commands are the same on Windows (PowerShell), macOS and Linux unless a
step says otherwise.

## 1. Install the tools (once)

You need three free tools:

| Tool | What it is for | Get it |
| :-- | :-- | :-- |
| **Git** | download the source code | <https://git-scm.com/downloads> |
| **uv** | install and run Python; it also installs Python 3.12 for you | <https://docs.astral.sh/uv/getting-started/installation/> |
| **Node.js 22** | build the app's screens (only needed for this build step) | <https://nodejs.org/> (choose the 22 LTS release) |

Close and reopen your terminal after installing, then check each one:

```bash
git --version
uv --version
node --version
```

`node --version` should print `v22.x`.

## 2. Download the code

Pick a folder for the code (for example your Documents folder), then:

```bash
git clone https://github.com/nexus-scholar-org/nexus-scholar-harness.git
cd nexus-scholar-harness
```

## 3. Build the app

The app's screens are built once, then packed into the Python package.

```bash
npm --prefix apps/research-ui ci
npm --prefix apps/research-ui run build:export
uv build --wheel
```

- The first command downloads the screen libraries (a few minutes, once).
- The second builds the screens. It ends with a list of pages; any line saying
  `Failed` means the build did not work (see Troubleshooting).
- The third writes the package to `dist/nexus_scholar-1.0.0-py3-none-any.whl`.

## 4. Install it

```bash
uv tool install --force dist/nexus_scholar-1.0.0-py3-none-any.whl
```

This installs the `nexus-scholar` command for your user. Check it:

```bash
nexus-scholar --help
```

You can now run `nexus-scholar` from any folder. You do not need to be in the
code folder any more, and you do not need to activate anything.

## 5. Start the app and create a workspace

```bash
nexus-scholar ui
```

Your browser opens on **Workspaces**. Each review is one folder; by default
they live in `Documents/Nexus Scholar/workspaces` (choose another folder with
`nexus-scholar ui --root <folder>`). Keep the terminal open: the app runs there,
and it is where approval codes appear later. Stop the app with **Ctrl+C**.

1. Click **New workspace**, type your review's title, and create it.
2. The next-step card shows a command with the workspace's folder filled in.
   Copy it; you will use it in step 6.

> **About the protocol.** A workspace made this way has a placeholder protocol
> (shown as a draft). It is enough to try the app. For a real review, write your
> inclusion and exclusion criteria with the guided interview instead:
> `nexus-scholar init "Your review title" --dir "<your workspaces folder>/<review-name>"`
> (beta). The folder you give becomes the workspace, so give a new folder inside
> your workspaces folder, then open it in the app.

## 6. Bring in your records

Export your search results as **RIS** from Scopus, Web of Science, Zotero or
another reference manager. Then, in a second terminal (leave the app running):

```bash
nexus-scholar accept-corpus --workspace "<the workspace folder>" --ris "<your-file>.ris"
```

It reports how many records were accepted. The corpus is
fingerprinted, and the step is recorded in the workspace's audit journal.
Running it again on the same file changes nothing.

## 7. Screen

Back in the browser, open the workspace and go to **Screening**. The steps are
across the top:

1. **Prepare.** Check the settings (whether an agent's drafts are hidden until
   you decide, and whether you see every record), then **Prepare batches** →
   **Prepare now**. After a few seconds it says "Batches prepared".
2. **Agent proposals** (optional). Skip it to screen on your own.
3. **Triage.** Read each record and decide: include, exclude (with a reason
   code), or unclear (goes to full text). The keyboard keys are shown on the
   buttons. Your decisions are saved as you go.
4. **Agreement.** Only meaningful if an agent proposed drafts.
5. **Publish.** For each batch, click **Show a code in the terminal**, read the
   code in the terminal where the app runs, type it, and approve. When every
   check passes, **Publish the screening**.

## 8. Export and write your methods

After publishing, **Export and methods** appears on the screening home and on
Publish.

- **Download** a RIS file (included and unclear records) to import into Zotero,
  EndNote or Mendeley, or a CSV with every record, its decision and its reason.
- **Copy paragraph** gives a methods paragraph with your PRISMA counts. It is a
  draft written from your workspace files: check every number before you use it.

## Where your work lives

Everything is in the workspace folder: your records, your decisions, the
published lists and the PRISMA report, and `audit/journal.jsonl`, the
append-only record of every step. Back it up like any other research data. What
leaves your computer, and when, is listed in [data-flow.md](data-flow.md).

## Updating

From the code folder:

```bash
git pull
npm --prefix apps/research-ui run build:export
uv build --wheel
uv tool install --force dist/nexus_scholar-1.0.0-py3-none-any.whl
```

## Troubleshooting

| What you see | What to do |
| :-- | :-- |
| `nexus-scholar` is not found | Run `uv tool update-shell`, then open a new terminal. |
| The app opens with an old look, or says it has no app bundle | Step 3 did not finish. Run `build:export` again and check that it does not say `Failed`, then repeat `uv build --wheel` and step 4. |
| "No accepted corpus" (`SNAPSHOT_NOT_ACCEPTED`) | Run step 6 for that workspace. |
| A card with a code in capitals | The card says what happened and the next step; the code is what to quote if you ask for help. |
| You are not sure which workspace is open | The terminal prints its folder when it starts or switches. To list only one folder's workspaces, start with `nexus-scholar ui --root <folder>`. |
| The browser did not open | Start with `nexus-scholar ui --no-browser` and open the one-time link it prints. |

For the command line, configuration and the AI agent, see the
[user guide](nexus_scholar_user_guide.md).
