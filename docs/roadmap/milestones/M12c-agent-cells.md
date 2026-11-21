# M12c Agent-proposed cells

Branch: `dev/m12a/charting-table-spec` (written beside the M12a specification) · Lane: declared per part (proposed below) · Status: **SPECIFICATION DRAFT, a plan only; nothing in it is approved to build, and any AI spend needs the researcher's approval** · Asked for by the researcher on 2026-11-21 (M12a question 9, answer "Plan it now": write this specification next, in parallel with the M12a build)

Short page for the researcher: [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md). Decisions: `docs/decisions.md`, "2026-11-21 — M12c agent-proposed cells: the specification's choices" (PROPOSED). Built on [`M12a-charting-table.md`](M12a-charting-table.md) section (g), its list of prerequisites.

Sources: M12a (g); `docs/architecture/agent_autonomy_ladder.md` (§3 rungs, §4 calibration, §5 provenance, lesson 54 on what the agent is never shown); `docs/roadmap/milestones/M9a-measure.md` (the measurement on the researcher's screening decisions, 2026-11-19); the screening proposal engine (`src/scholar_harness/screening/proposals.py`, `agent_runs.py`); the Phase 3 findings X2 to X4 (`docs/ux/phase3-extraction/README.md`); the PDF assessment (`docs/assessment/kit-pdf.md`, PDF-07, PDF-08). Code read at `1f218054`.

## Goal

When the researcher has charted their review's first studies by hand, an agent may propose a value for chosen columns of the remaining studies, each value with a quote from the study's full text that the app has checked is really there, on the page it names. The researcher sees the quote highlighted, and adopts, edits or rejects each proposal; nothing becomes a cell without them, and every adopted cell says it came from the agent. Before any proposal is offered, the agent is measured on the researcher's own charted rows, column by column, and only columns that pass are offered.

## What exists today, and what is missing

| Needed | Today (at `1f218054`) | Missing |
| :-- | :-- | :-- |
| The full text as text | The legacy parser walks pages (`scholar_pdf/extract.py:56-58`) and writes Markdown with no page marker or offset; on failure it writes "Extracted content from <name>" as a success (PDF-08, `extract.py:98-100`). A missing PDF becomes an abstract-only file counted as extracted (X2). The E2 engines (`scholar_pdf/extraction_engines.py`) were not checked for page offsets. Everything is parked. | Text per page with offsets, a text-quality flag per study (parsed, partial, needs OCR, failed), and no abstract-only file passing as a full text |
| Which PDF belongs to which study | PDF-07: the kit's files carry no study mapping. M12a Part A (attach) and Part F (fetch, manifest, confirmation) give each study one confirmed file. | Nothing more, once M12a A and F are built |
| A quote check | Screening's `quote_in_source` (`proposals.py:99-135`): the quote must equal `text[start:end]` of the title and abstract | The same rule over the full text, plus the page |
| Showing the quote | The triage page's inner abstract highlighter (`components/triage-page.tsx:106-120`); a reusable component is built in M8b-triage-highlights (branch `dev/m8b/triage-highlights`, not merged) | The component applied to full text, page by page |
| Proposals that are never decisions | Screening: append-only `proposals.jsonl`, the model never chooses the outcome, plain-code validators, a failed check is Unclear (`proposals.py:1-38`) | The charting version, per study and column |
| Runs, keys, consent, cost | `agent_runs.py:1-30`: consent per provider (`agent_consent.json`, `CONSENT_REQUIRED`), keys from the keychain or environment, one run per workspace, a hard cost ceiling (`COST_CEILING_REACHED`), chunks of 200 in Message Batches; three drivers (`scholar_agent/drivers/`: Anthropic, OpenAI-compatible, Gemini); a dated price table | A charting task and its consent (full texts, not abstracts, are sent) |
| A measurement | M9a: one command over the researcher's decisions, blind (nothing but the record's text is sent), a report of agreement, failures, tokens and cost | The same per column, against the researcher's charted cells |
| Provenance | Ladder §5: an adopted proposal is an `AGENT_ADOPTED` event with `screener_id` `agent:<model>` and a `proposal_id`, never `HUMAN` (decision 2026-11-10, item 1) | The same for cells; M12a's cell events already carry `method` and `screener_id` |
| A typed contract | Contract v1 has no full-text decision or cell (M12a item 1, accepted outside the contract "for now"; a contract decision comes before an agent proposes cells) | That decision |

## The prerequisites, in order (from M12a (g))

1. **M12b-read: the full text as text with page anchors.** One confirmed PDF per study (M12a A and F) parsed into text per page with offsets, PDF-08 fixed (a failed parse is a failure), X2 fixed (no abstract-only file counted as a full text), a text-quality flag per study, and the `pdf` extra's parser (PyMuPDF) or the E2 engine chosen by a measurement on the researcher's own PDFs. Tables in PDFs often come out as broken text; the flag must say when a page is mostly table or image. Without OCR a scanned paper is "needs OCR" and gets no proposals. M12b also shows the full text beside the form (the in-app viewer of M12a's "Out" list) and is where PDF-07's parked lookup in `pipeline/extraction.py` is retired or pointed at the M12a manifest. Not specified yet; it is its own specification.
2. **A quote check over the full text:** a proposal's quote must equal the text at its offsets on the page it names; a proposal without a checkable quote cannot be adopted (it is shown as "no evidence").
3. **The highlighter** (M8b) on that text, so the researcher sees the quote in its place.
4. **A measurement** on the researcher's own charted rows, per column, with an approved spend (below).
5. **The contract decision** for cells and proposals (question 1).
6. **Adoption with agent provenance**, never `HUMAN`.

## Design (each choice is PROPOSED; the questions are on the researcher's page)

### What the agent is asked, and what it is shown

- **One request per study**, covering the columns the researcher has opened to the agent (per column, off by default). For each column: its name, its definition and its type, and for a list column its options, all from the charting form at its current version. Nothing else: no other study's values, no count, no statistic, no earlier proposal, no title-and-abstract decision (lesson 54, M9a D4). The study's text is its full text, page by page.
- **The answer per column** is one of: a value that fits the column's type and options, each with one or more quotes (page, start, end, text); `not_reported` with a short statement of where the agent looked (it cannot be checked); or `cannot_decide`.
- **The model never writes a cell.** As in screening, the answer is a proposal stored in its own append-only file (`charting/proposals/proposals.jsonl`), bound to the form version, the protocol fingerprint, the study's full-text file (its SHA-256) and the text version.

### Plain-code checks on every proposal

`schema` (the answer parses); `one_answer_per_column`; `fits_column` (the value is of the column's type and in its options); `quote_in_source` (each quote equals the text at its offsets, on its page); `text_quality` (the page is parsed text, not "needs OCR"). A proposal that fails a check is kept and shown as "failed check: <name>", and cannot be adopted with one key.

### What the researcher sees (screen 02 and the Charting view; screens drafted later)

- **Shown beside the cell, never in it.** A proposal appears next to its cell with the quote and a "show in text" link that opens the page with the quote highlighted. The cell stays empty until the researcher acts.
- **Adopt** (one key) writes a cell event with `method: AGENT_ADOPTED`, `screener_id: agent:<model>`, the `proposal_id` and the researcher who adopted it. **Edit** writes a `HUMAN` cell event that names the proposal it replaced. **Reject** writes a rejection with an optional reason. All are undoable like any cell.
- **An agent's "not reported"** is never adopted with one key: the researcher types Not reported themselves (Alt+N), because an absence cannot be checked by quote.
- **No bulk adoption.** One cell at a time; the lesson of the bulk adoption of 2026-11-20 (M12a risk 3).
- **During a measurement the agent is blind to the researcher and the researcher to the agent:** proposals for studies the researcher has not charted yet are hidden until the measurement report exists.

### The measurement (the gate per column)

- **What:** the agent runs on studies the researcher has already charted (the pilot and the first charted rows, at least 20 studies, question 7), blind as above. Per column: exact agreement for Yes/No, One of and Number; overlap for Several of (each option counted); for Text, no automatic score: the report lists the pairs side by side and the researcher marks a sample "same meaning" or "different". Also: how often the agent says not reported where the researcher charted a value (a missed finding), the reverse, failed checks, tokens and cost.
- **Gate:** a column is offered to the agent only after its numbers are read and a threshold for it is accepted by the researcher. No threshold is proposed here (the M9a lesson: thresholds are set from the numbers, and the M9a thresholds are still open).
- **Reuse:** the M9a measure command's structure (blind check, report, ceiling) with a charting task; no second driver.

### Runs, consent and spend

- **Reuse of `agent_runs`:** keys, one run per workspace, Message Batches for Anthropic, the hard cost ceiling, an estimate from the dated price table before any call, refusal when the ceiling is below the estimate.
- **A consent of its own** per provider: sending full texts is not sending abstracts. The consent names what is sent (the full texts of the chosen studies), to which provider, and the licence of each text as the M12a fetch manifest records it (question 4).
- **Spend:** every run, including the measurement, needs the researcher's own approval with a ceiling they type. A rough order of size, to be replaced by the estimate command's figure: a full paper is roughly 30 times an abstract, so one pass over 150 studies is roughly the input of 4,500 abstracts, about three times one model's share of the M9a run ($12.63 for three models over 1,644 abstracts). Treat that as a guess, not a quote.

### Contract and provenance

The proposals and the adopted cells become typed artifacts before the first adoption (M12a item 1 says a contract decision comes before an agent proposes cells): a proposal record, a cell event with `method` in {`HUMAN`, `AGENT_ADOPTED`}, the bindings (form version, protocol fingerprint, full-text SHA-256, text version), a negative regression test (an `AGENT_ADOPTED` cell without a `proposal_id` is refused), schemas and golden fixtures, an independent review. M12a's events already carry what this needs, so nothing M12a writes would be migrated.

### The methods text

"Values for <columns> were proposed by <model, version> from the full text and checked by one reviewer against the quoted passage; of N proposals, A were adopted unchanged, E edited and R rejected. Before use, the agent was compared with the reviewer on S studies charted by hand: <agreement per column>." Every number from the events.

## Parts (a plan; none is approved)

| Part | Content | Lane | Depends on |
| :-- | :-- | :-- | :-- |
| **M12b-read** | Text per page with offsets from the confirmed PDF, PDF-08 and X2 fixed, a quality flag, the full text beside the form, the M8b highlighter on it | RELEASE | M12a A and F; M8b merged |
| **M12c-0 contract** | The contract decision and typed proposal and cell records | RELEASE | The researcher's answer to question 1 |
| **M12c-1 measure** | The charting task, the blind check, the measurement command and report | STANDARD (like M9a: a maintainer command, no route) | M12b-read; the researcher's charted rows; an approved spend |
| **M12c-2 propose and adopt** | Proposal runs from the app, checks, consent, adoption, the screens, the methods text | RELEASE | M12c-0, M12c-1 read and thresholds accepted |

## Risks

1. **Anchoring.** A value shown beside an empty cell pulls the reviewer towards it. Mitigation: the quote is the evidence, adoption is one cell at a time, and the methods text reports how many were adopted unchanged. Blinding until the researcher's own value would remove the time saved; that is question 5.
2. **Absence claims.** "Not reported" is a finding in a scoping review and cannot be checked by quote. Hence it is never one-key adoptable.
3. **Tables and figures.** Camera models and data splits often sit in tables, which parsers break; a quote may be found but mean little out of its table. The quality flag and the "show in text" view are the defence; the measurement shows how bad it is.
4. **Licences.** Sending a publisher's text to a provider may not be allowed by its licence or the researcher's institution (question 4).
5. **Cost** grows with full texts and with re-runs after each form amendment. Proposals are bound to the form version; an amendment marks the affected proposals stale rather than re-running.
6. **A parallel build.** M12c is written while M12a is built; any M12a change to the events or the form shape is reflected here before M12c starts.

## What cannot be verified on paper

How well text comes out of this review's PDFs (MDPI, IEEE, Elsevier, arXiv), how often the agent agrees with the researcher on their two columns, how long a proposal saves against typing, and the real cost. Each needs M12b on real PDFs and an approved measurement.

## Open questions

On the researcher's page: [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md).
