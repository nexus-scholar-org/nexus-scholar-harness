# Nexus Scholar beta (1.1.0b8)

Thank you for testing. This page says who the beta is for, how to install it,
what it cannot do yet, and how to tell us what happened.

## What is new in 1.1.0b8

1.1.0b8 adds a **Windows installer** (unsigned; no Python or terminal needed), a start with no terminal (`nexus-scholar-app`), a **Settings** screen for your contact e-mail, keys and reviews folder, and a format version on each review: before this build first writes to a review made with an older build it saves one copy of the whole review, PDFs included, under `.nexus-copies/` in your reviews folder. It also **removes** the citation graph (`scholar-graph`, two MCP tools). Upgrade with `uv tool install --force "nexus-scholar>=1.1.0b8"`, or run the installer from the [release page](https://github.com/nexus-scholar-org/nexus-scholar-harness/releases/tag/v1.1.0b8). Details: [release notes](../releases/1.1.0b8.md); the earlier [1.1.0b7](../releases/1.1.0b7.md) added Explore and Direction, the query workbench, citation chasing, the criteria pilot and the Charting step, mostly used only on test data.

## Who it is for

Researchers who screen titles and abstracts for a systematic or scoping review,
alone, on their own computer. You bring RIS exports from the databases you
searched (or PubMed `.nbib` exports). You leave with a published screening, its PRISMA counts and a draft
methods paragraph.

## Install (four commands)

On Windows you can skip these commands: run `NexusScholar-1.1.0b8-setup.exe` from the [release page](https://github.com/nexus-scholar-org/nexus-scholar-harness/releases/tag/v1.1.0b8) and start Nexus Scholar from the Start menu. The installer is not signed, so Windows may warn you first (see the [release notes](../releases/1.1.0b8.md)).

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal.
2. Install Nexus Scholar:

   ```bash
   uv tool install "nexus-scholar>=1.1.0b8"
   ```

3. Check the version (it should print `nexus-scholar 1.1.0b8`):

   ```bash
   nexus-scholar --version
   ```

4. Start the app (your browser opens on Workspaces):

   ```bash
   nexus-scholar ui
   ```

Then follow [Getting started](../getting-started.md) from step 3: create a
workspace, import your RIS or `.nbib` files, prepare, screen, publish and export.

## Known limits

- **One reviewer.** A second screener, and agreement between two people (kappa), are not in the beta.
- **Full text is handled by you, on the Charting step.** After publication, Charting lists the kept studies; you attach or fetch each PDF (the open-access look-up asks Unpaywall, arXiv and, with your key, OpenAlex), record a full-text decision and fill the charting columns by hand. The app extracts nothing from a PDF's text: the look-up only checks that the DOI or the title's words are on a fetched file's first two pages. There is no synthesis.
- **RIS and PubMed `.nbib` only.** CSV and BibTeX are not imported yet.
- **Approval uses a code shown on your computer:** in a small window, and also in the terminal when you started the app with `nexus-scholar ui`.
- **The approver is a typed name,** not a verified sign-in.
- **AI drafts are optional and not validated.** Do not report a recall or accuracy figure for them.
- **The Discovery, Explore and Charting screens have not been tried by a second person.** Search needs your contact e-mail (on the Settings screen, or `SCHOLAR_MAILTO`), and OpenAlex needs its key (Settings, or `SCHOLAR_OPENALEX_KEY`) (required by OpenAlex since 2026-02-13). See the release notes, "Known limits" ([1.1.0b8](../releases/1.1.0b8.md), [1.1.0b7](../releases/1.1.0b7.md)).

## Tell us what happened

The most useful thing you can send is **a screen recording, or a written note, of
your first 15 minutes**: where you hesitated, what you expected, what surprised
you. With it, send:

- the version (`nexus-scholar --version`);
- any code shown on a card (a word in capitals, for example `SOURCE_NOT_RIS`);
- if something went wrong in a workspace, two of its files: `audit/journal.jsonl`
  and `literature/screening/MANIFEST.json`.

Those two files hold the steps you took, your review's title and questions, and the
batch list, not your records' titles or abstracts. Nothing else leaves your
computer unless you send it (see
[data-flow.md](../data-flow.md)). Report by email to the person who invited you,
or as an issue at
<https://github.com/nexus-scholar-org/nexus-scholar-harness/issues>.
