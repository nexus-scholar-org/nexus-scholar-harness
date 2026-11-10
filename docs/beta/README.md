# Nexus Scholar beta (1.1.0b5)

Thank you for testing. This page says who the beta is for, how to install it,
what it cannot do yet, and how to tell us what happened.

## What is new in 1.1.0b5

1.1.0b5 adds creating a workspace from the browser (inception screens), PubMed `.nbib` import, a one-screen triage focus view with an optional checklist, and a more honest search engine on the command line. Already on 1.1.0b4 or earlier? Upgrade with `uv tool install --force "nexus-scholar>=1.1.0b5"`. Details, including changes to the local API: [release notes](../releases/1.1.0b5.md).

## Who it is for

Researchers who screen titles and abstracts for a systematic or scoping review,
alone, on their own computer. You bring RIS exports from the databases you
searched (or PubMed `.nbib` exports). You leave with a published screening, its PRISMA counts and a draft
methods paragraph.

## Install (four commands)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal.
2. Install Nexus Scholar:

   ```bash
   uv tool install "nexus-scholar>=1.1.0b5"
   ```

3. Check the version (it should print `nexus-scholar 1.1.0b5`):

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
- **Title and abstract only.** No full-text screening, data extraction or synthesis. Unclear records are listed for full text.
- **RIS and PubMed `.nbib` only.** CSV and BibTeX are not imported yet.
- **Approval uses a code shown in the terminal.** Keep the terminal where the app runs in view.
- **The approver is a typed name,** not a verified sign-in.
- **AI drafts are optional and not validated.** Do not report a recall or accuracy figure for them.
- **No search from the browser in 1.1.0b5.** The Discovery screens (Plan to Hand-off) are on `main` and come with 1.1.0b6 ([draft notes](../releases/1.1.0b6.md)). A command-line search (`nexus-scholar run`) needs `SCHOLAR_MAILTO`, and OpenAlex needs `SCHOLAR_OPENALEX_KEY` (required by OpenAlex since 2026-02-13).
- **Inception has no Explore or Direction screen.** The browser flow goes Scope, Shape, Concepts and criteria, Review, Done.

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
