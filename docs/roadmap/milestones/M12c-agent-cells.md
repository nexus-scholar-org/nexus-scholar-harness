# M12c Agent-proposed cells

Branch: `dev/m12a/charting-table-spec` (written beside the M12a specification) · Lane: declared per part (below; each **RELEASE**) · Status: **SPECIFICATION; the nine questions answered by the researcher on 2026-11-21** (six as recommended; question 3 changed: the app and MCP from the start; question 6 changed: all columns at once; question 7 changed: no measurement, the counts come from the researcher's own actions). The two questions where the answers met accepted decisions were answered the same day, both as recommended: N1 "Small eval set", N2 "AGENT_ADOPTED, stated plainly". **A plan only: nothing is approved to build, and any AI spend needs the researcher's own approval.** · Asked for by the researcher on 2026-11-21 (M12a question 9, "Plan it now")

Short page for the researcher: [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md). Decisions: `docs/decisions.md`, "2026-11-21 — M12c agent-proposed cells". Built on [`M12a-charting-table.md`](M12a-charting-table.md) section (g), its list of prerequisites.

Sources: M12a (g); `docs/architecture/agent_autonomy_ladder.md` (§3 rungs, §4 calibration, §5 provenance, §9 decisions, lesson 54 on what the agent is never shown); `docs/decisions.md` 2026-11-03 "Agent system: proposals only, least autonomy per job", 2026-11-10 and 2026-11-11 (the ladder), 2026-11-19 (M9a, accepted 2026-11-20), 2026-11-19 (M10c, assistant over MCP); `docs/roadmap/milestones/M9a-measure.md`; the screening proposal engine (`src/scholar_harness/screening/proposals.py`, `agent_runs.py`) and its MCP tools (`nexus_screening_record`, `nexus_submit_proposal`, `scholar_agent/server.py:2095-2137`); the Phase 3 findings X2 to X4 (`docs/ux/phase3-extraction/README.md`); the PDF assessment (`docs/assessment/kit-pdf.md`, PDF-07, PDF-08). Code read at `1f218054`.

## The researcher's answers (2026-11-21), quoted as chosen

1 Contract v1: "Yes, contract first". 2 Provenance: "Yes". 3 How the agent runs: **"Both from the start"** (not as recommended, which was "From the app first"). 4 What may be sent: "All, after consent". 5 When a proposal is shown: "Beside the cell, never in it". 6 Which columns: **"All columns at once"** (not as recommended, which was each column opened one by one after its measurement). 7 The measurement: **"no time to chart by hand just do it without measuring"** (the researcher's own words, not as recommended); asked then whether the app should still count, at no extra work, how many proposals they adopted unchanged, edited or rejected per column and put that in the methods text: "Count as I work". 8 An agent's "not reported": "Yes, I type it". 9 Order: "After M12a, before M9b–M9d"; with answer 7 the measurement part is dropped.

## Amendment 2026-11-22: a blind second reading

The researcher answered on 2026-11-22: **"Yes, add it to the spec."** Each paper is read twice by the agent, the two readings independent of each other (neither is shown the other's output); the researcher still decides every cell; a cell on which the two readings disagree is flagged for a closer look. The cost named when asked: about twice the AI spend per paper. Decision: `docs/decisions.md`, "2026-11-22 — M12c agent-proposed cells: a blind second reading".

What this changes below, to be written out before M12c-2 is built (the sections are not yet rewritten):
- "What the agent is asked, and what it is shown", "What the researcher sees", "What the counts show": two readings and a disagreement flag. Agreement between the readings is not accuracy, and answer 7 ("No measurement") stands.
- "Runs, consent and spend": the estimate and both ceilings cover two readings.
- "The methods text": it says each paper was read twice and what a disagreement led to.
- Risk 1 (anchoring) is unchanged: every value is still shown before the researcher's reading.

Still open (decision items 2 to 5 of that entry): what counts as a disagreement per column type; what is shown; the same model and prompt or not; the MCP path, where the app cannot make a client read twice.

## Goal

When the researcher charts, an agent may propose a value for every column of the charting form (one switch for the whole form), each value with a quote from the study's full text that the app has checked is really there, on the page it names. The proposal is shown beside its empty cell; the researcher adopts, edits or rejects it, one cell at a time; nothing becomes a cell without them, and every adopted cell says it came from the agent. The agent is **not measured** before use (answer 7): the app counts, as the researcher works, how many proposals were adopted unchanged, edited or rejected per column, and the methods text reports those counts and says that accuracy was not measured. Proposals come from the app's own run (the researcher's API key) and from the researcher's own AI client over MCP, both from the first release (answer 3).

## What exists today, and what is missing

| Needed | Today (at `1f218054`) | Missing |
| :-- | :-- | :-- |
| The full text as text | The legacy parser walks pages (`scholar_pdf/extract.py:56-58`) and writes Markdown with no page marker or offset; on failure it writes "Extracted content from <name>" as a success (PDF-08). A missing PDF becomes an abstract-only file counted as extracted (X2). Everything is parked. | Text per page with offsets, a text-quality flag per study, no abstract-only file passing as a full text |
| Which PDF belongs to which study | PDF-07: the kit's files carry no study mapping. M12a Part A (attach) and Part F (fetch, manifest, confirmation) give each study one confirmed file. | Nothing more, once M12a A and F are built |
| A quote check | Screening's `quote_in_source` (`proposals.py:99-135`): the quote must equal `text[start:end]` of the title and abstract | The same rule over the full text, plus the page |
| Showing the quote | The triage page's abstract highlighter (`components/triage-page.tsx:106-120`); a reusable component in M8b-triage-highlights (not merged) | The component on full text, page by page |
| Proposals that are never decisions | Screening: append-only `proposals.jsonl`, plain-code validators, a failed check is Unclear (`proposals.py:1-38`) | The charting version, per study and column |
| Runs from the app | `agent_runs.py`: consent per provider (`CONSENT_REQUIRED`), keys, one run per workspace, a hard cost ceiling (`COST_CEILING_REACHED`), Message Batches, three drivers, a dated price table | A charting task and its consent (full texts are sent) |
| Runs through an AI client | Screening's MCP tools: the client reads one record (`nexus_screening_record`) and submits a proposal (`nexus_submit_proposal`), checked by the same validators; M10c's assistant tools on drafts. Neither has been tried with a real AI client (plan §6, M10c) | Two charting tools on the same intake, a consent before a full text is handed out |
| Provenance | Screening decision events are human only (`events.py:344`: "decision events are human decisions; agents submit proposals"). Ladder §5 and decision 2026-11-10 item 1 define `AGENT_ADOPTED` for the screening autonomy modes, with the mode and the calibration run | Its shape for a cell adopted by hand with no calibration (question N2) |
| A typed contract | Contract v1 has no full-text decision or cell (M12a answer 1, "Outside for now") | The decision of M12c-0 (answer 1) |

## The prerequisites, in order

1. **M12b-read: the full text as text with page anchors.** (M12a G1, answered 2026-11-21: "Reading waits for M12b-read", so reading PDFs is this step, not M12a's.) One confirmed PDF per study parsed into text per page with offsets, PDF-08 fixed, X2 fixed, a text-quality flag per study (parsed, partial, mostly table or image, needs OCR, failed). Without OCR a scanned paper is "needs OCR" and gets no proposals. M12b-read also shows the full text beside the form and applies the M8b highlighter to it. Its own specification, not written yet.
2. **The contract decision** for proposals and cells (answer 1, M12c-0), with the provenance shape (answer 2, question N2).
3. **A quote check over the full text:** a proposal's quote must equal the text at its offsets on the page it names; a proposal without a checkable quote cannot be adopted.
4. **Adoption with agent provenance**, never `HUMAN`.

The measurement that the draft placed here is **dropped** (answer 7).

## Design

### What the agent is asked, and what it is shown

- **One request per study, for every column of the form** (answer 6, "All columns at once"): one switch for the whole form, off by default, turned on by the researcher and journaled. For each column: its name, definition and type, and for a list column its options, from the charting form at its current version. Nothing else: no other study's values, no count, no statistic, no earlier proposal, no title-and-abstract decision (lesson 54). The study's text is its full text, page by page.
- **The answer per column** is a value that fits the column with one or more quotes (page, start, end, text); or `not_reported` with a short statement of where the agent looked; or `cannot_decide`.
- **The model never writes a cell.** The answer is a proposal in `charting/proposals/proposals.jsonl`, append-only, bound to the form version, the protocol fingerprint, the full-text file's SHA-256 and the text version, and to the path it came by (`app` with the run id, or `mcp` with the model the client declared).

### Plain-code checks on every proposal, whichever path it came by

`schema`; `one_answer_per_column`; `fits_column`; `quote_in_source` (the quote equals the text at its offsets, on its page; over MCP the client sends the quote and the page, and the engine finds and checks the offsets, as `nexus_submit_proposal` asks for a verbatim quote today); `text_quality`. A proposal that fails a check is kept, shown as "failed check: <name>", and cannot be adopted with one key.

### What the researcher sees

- **Beside the cell, never in it** (answer 5): the proposal next to its empty cell with its quote and "show in text", which opens the page with the quote highlighted. Proposals are visible from the start; nothing is hidden, since there is no measurement to protect (answer 7). The plan's "Decided, blinding" line (§2, "Phase 2 Screening") is screening's default for screening proposals; it is not read as covering charting, where answer 5 decides.
- **Adopt** (one key; the engine mints the cell event, question N2), **Edit** (a `HUMAN` cell event naming the proposal it replaced), **Reject** (optional reason). All undoable.
- **An agent's "not reported"** is never adopted with one key (answer 8): the researcher types Not reported (Alt+N) or the value they find.
- **No bulk adoption.** One cell at a time (M12a risk 3).
- **The counts, as the researcher works** ("Count as I work"): a small panel per column with the figures below, updated from the cell events.

### What the counts show, and what they do not

Per column, from the researcher's own actions, at no extra work:
- proposals made; proposals that failed a check;
- adopted unchanged; adopted then edited, or edited instead of adopted; rejected;
- the agent said "not reported" and the researcher typed Not reported; the agent said "not reported" and the researcher typed a value (**a value the agent missed, found by the researcher**); the agent could not decide;
- cells the researcher filled with no proposal.

**What they show:** how much of the table came from the agent, and how much the researcher changed, column by column.

**What they do not show, and what is therefore not known:**
- **The agent's accuracy per column.** An adopted-unchanged value is the researcher's agreement after seeing the agent's value and its quote, not an independent check: a wrong value that looked right is counted as adopted. Nobody charted those studies without the agent, so there is no reference to measure against.
- **Missed values are caught only where the researcher looks.** An agent's "not reported" cannot be adopted with one key, so the researcher types each one; a value the agent missed is caught only if the researcher looks for it in the paper while typing. If they type Not reported on the agent's word, the miss is invisible and counted as agreement.
- **Anchoring.** Every value was shown before the researcher's own reading, so the counts measure acceptance under anchoring, not agreement.
- **Comparison with other reviews or tools.** None; the counts are this review's, this form version's and this model's.

### Runs, consent and spend: the two paths (answer 3, "Both from the start")

| | From the app (the researcher's API key) | Through the researcher's AI client over MCP |
| :-- | :-- | :-- |
| How | `agent_runs` with a charting task: one run per workspace, Message Batches for Anthropic, cancel | Two tools: one hands out a study's columns and full text, one stores a proposal (as screening's `nexus_screening_record` and `nexus_submit_proposal`) |
| Consent (answer 4) | Per provider, naming what is sent (the full texts of the chosen studies) and listing each study's licence from the M12a fetch manifest; an "openly licensed only" choice on the run screen | The same consent, given in the app for "your AI client", before the tool hands out any full text (`CONSENT_REQUIRED` in the tool's answer); the provider behind the client is whatever the client uses, which the app cannot see |
| Model | Known (the driver's model id) | **As declared by the client** (`agent:<model>`, recorded as declared, M10c item 2); it cannot be verified |
| Cost | **Known**: an estimate from the dated price table before any call, refusal when the typed ceiling is below it, a hard ceiling during the run, tokens and cost recorded per run | **Not known to the app**: it sees no tokens and no price; the cost is on the researcher's client account or subscription; no ceiling can be enforced; the proposals are counted, not priced |
| What the agent is shown | Exactly the request above | The tool returns exactly the request above; what else is in the client's conversation (earlier studies, the researcher's own words) is outside the app's control, so lesson 54 holds for what the app sends, not for the client's context |
| Spend approval | Every run needs the researcher's own approval with a ceiling they type | Nothing for the app to approve; the researcher decides in their client |

**What "both from the start" adds to build and test.** A second entry to the same proposal intake: two MCP tools, their consent check, the declared-model field, and refusals in the tool's answers; the counts and the methods text split by path. Tests: the tool functions called directly, as the existing MCP tests do (`tests/mcp/test_mcp_screening_proposals.py`, `tests/kits/agent/test_mcp_assistant.py`; no test drives the server through a real MCP client today), each refusal, a proposal from each path through the same checks, and a test that the tool hands out nothing before consent. About M on its own, a part of its own (M12c-3).

**What stays untested until a real AI client is used.** Whether a real client follows the tool's schema over a long full text; how often its quotes fail the check; whether the declared model is the one that answered; how the client's own tool-approval prompts behave on Windows; the time per study; and the cost on the researcher's account. M10c's assistant tools have the same gap (not yet tried with a real client); trying one of them first would show the client's behaviour before M12c-3 is used.

**A rough cost for the app path**, to be replaced by the estimate before any run: a full paper is roughly 30 times an abstract, so one pass over 150 studies is roughly the input of 4,500 abstracts, about three times one model's share of the M9a run ($12.63 for three models over 1,644 abstracts). All columns in one request per study (answer 6) costs about the same as one column, since the full text dominates. A guess, not a quote.

### Contract and provenance (answers 1 and 2)

Proposals and adopted cells become typed artifacts before the first adoption (M12c-0): a proposal record (with its path, `app` or `mcp`), a cell event with `method` in {`HUMAN`, `AGENT_ADOPTED`}, the bindings, a negative regression test (an `AGENT_ADOPTED` cell without a `proposal_id` is refused, and one posted by a client is refused: the engine mints it when the researcher presses Adopt), schemas and golden fixtures, an independent review. What the `AGENT_ADOPTED` cell carries (N2, "AGENT_ADOPTED, stated plainly"): the proposal, the researcher as the adopter, "adopted one at a time" where the ladder's screening event carries a mode, and "none" where it carries a calibration run; the engine writes it on Adopt; screening's rule is unchanged.

### The methods text (proposed)

"Values for all charting items were proposed by a large language model (<model and version>, run by the review software; or <model as declared>, through the reviewer's own AI client) from the full text of each report. One reviewer checked each proposal against its quoted passage and adopted, edited or rejected it, one item at a time; where the model stated that an item was not reported, the reviewer recorded the item themselves. Per item, of N proposals, A were adopted unchanged, E edited and R rejected; in K cases the model reported an item as not reported where the reviewer found it. The model's accuracy was not measured against independent charting, and the reviewer saw each proposal before recording a value." Every number from the events, split by path when both were used.

## Parts (a plan; none is approved)

| Part | Content | Lane | Size | Depends on |
| :-- | :-- | :-- | :-- | :-- |
| **M12b-read** | Text per page with offsets from the confirmed PDF, PDF-08 and X2 fixed, a quality flag, the full text beside the form, the M8b highlighter on it | RELEASE | L | M12a A, B and F; M8b merged |
| **M12c-0 contract** | The contract decision, typed proposal and cell records, the provenance shape (N2), schemas, fixtures, negative tests | RELEASE | M | Answers 1 and 2; N2 |
| ~~M12c-1 measure~~ | **Dropped** (answer 7) | — | — | — |
| **M12c-eval, the task's eval set** (N1, "Small eval set") | About five open-access papers outside the review, values written by the developer for a two-column test form, run once per task version: answers parse, quotes pass, values fit; it shows the task works, not that it is right on the review | STANDARD | S, plus a run whose spend the researcher approves separately | M12b-read (the text the task reads) |
| **M12c-2 propose and adopt, from the app** | The charting task, the checks, the consent, app runs with estimate and ceiling, the all-columns switch, adopt/edit/reject, the counts as the researcher works, the methods text, the screens | RELEASE | L | M12b-read, M12c-0, M12c-eval |
| **M12c-3 the MCP path** | The two tools on the same intake, the consent before a full text is handed out, the declared model, the counts and the methods text by path, tests calling the tools | RELEASE | M | M12c-2's intake |

Order: **M12b-read, M12c-0, M12c-eval, M12c-2, M12c-3**, after M12a and before M9b to M9d (answer 9). With answer 3 the first use waits for M12c-3, so the agent is offered on both paths at once. Four RELEASE PRs and one small STANDARD part (the eval set, N1).

## Where the answers meet accepted decisions (checked 2026-11-21)

- **Answer 7 and the 2026-11-03 decision "Agent system: proposals only, least autonomy per job"**, which reads: "The AI behind Phases 0–2 is built as versioned *tasks*: a prompt, an output schema, a model and effort setting, and an eval set." and "Changing a prompt, model or effort setting needs a new task version and an eval re-run, mirroring the contract-baseline gate." Charting is Phase 3, so the text does not name it, but M12c reuses those tasks and drivers. With no measurement, the charting task has no eval set. **Question N1, answered "Small eval set".**
- **Answers 2 and 7 and the ladder's provenance decision** (2026-11-10, item 1; `agent_autonomy_ladder.md` §9.1), which reads: "One `AGENT_ADOPTED` event per record, minted by the engine only, carrying the proposal, the mode, the calibration run and the human who set the mode. A client can never post one." A cell adopted by hand has no mode in the ladder's sense and, with answer 7, no calibration run. **Question N2, answered "AGENT_ADOPTED, stated plainly".**
- **Answer 6 ("All columns at once")** conflicts with no accepted decision. The ladder's rungs and gates are about screening decisions that stand without the researcher; every cell here is still adopted by the researcher one at a time, which is the ladder's L0 ("The agent proposes"), always available. The 2026-11-03 "least autonomy per job" holds: the agent proposes only.
- **Answer 7 and the ladder's calibration gates** (2026-11-11, L1 and L2) and **the M9a decision** (2026-11-19, accepted 2026-11-20): no conflict. Those gates unlock rungs where agent decisions stand; M12c unlocks no rung. M9a is a warning, not a rule: on abstracts the screening agent left 67% to 77% of records Unclear, mostly because the abstract did not report what a criterion asked; a charting agent answering "not reported" often is likely, which is why answer 8 matters.
- **Answer 5 and the plan's screening blinding line** (§2, "Decided, blinding: the agent proposal is hidden until you decide"): read as screening's, not a conflict (above).
- **Plan §6 and §8:** §6 does not list M12b-read or M12c yet; §8's parked "matrix" is the automatic extractor (`scholar_rag`, `nexus_matrix_extract`), which stays parked; M12c is a new proposal task, not that extractor. Nothing in §8 forbids it.

## Risks

1. **Anchoring, unmeasured.** Every value is shown before the researcher's reading, and nothing measures what that does (answer 7). The methods text says so.
2. **Absence claims.** "Not reported" cannot be checked by quote; the researcher types each one, and a miss is caught only if they look (above).
3. **Tables and figures.** Camera models and data splits often sit in tables, which parsers break; a quote may be found but mean little out of its table. The quality flag and "show in text" are the defence; nothing measures how often this misleads.
4. **All columns at once.** Judgement columns (for this review, "sensor problems addressed") are offered with the factual ones; their proposals are likely to be "not reported" or arguable. The counts per column will show how often the researcher rejects them, after the fact.
5. **Licences.** Sending a publisher's text to a provider, or to a client's provider the app cannot see, may not be allowed by its licence or the researcher's institution (answer 4 puts this in the consent).
6. **Cost over MCP is invisible to the app**, and a re-run after each form amendment costs again on both paths. Proposals are bound to the form version; an amendment marks them stale rather than re-running.
7. **A parallel build.** M12c is written while M12a is built; any M12a change to the events or the form is reflected here before M12c starts.

## What cannot be verified on paper

How well text comes out of this review's PDFs; how often the agent's values are right (not measured, by answer 7); how long a proposal saves against typing; the real cost on the app path; and everything listed under "What stays untested until a real AI client is used".

## What the main session must change in plan §6 and §8 (not edited here)

- **§6, "After the acceptance run":** add M12b-read and M12c (parts M12c-0, M12c-2, M12c-3, each RELEASE; no measurement part) after M12a and before M9b to M9d (answer 9); the "Waiting" line that names M9b and M9c first moves them after M12c.
- **§6, M10c row:** note that M12c-3 is a second MCP path that, like M10c, has not been tried with a real client.
- **§8:** no change for M12c itself (the automatic matrix stays parked); M12b-read, when built, takes reading PDFs out of §8's parked `scholar_pdf` lines (M12a G1).
- **§6, the M12c row:** includes M12c-eval (STANDARD, S, a spend the researcher approves separately) before M12c-2.

## Open questions

None (N1 and N2 answered 2026-11-21). The page: [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md).
