# M12c Agent-proposed cells: for your review

Date: 2026-11-21 · Status: **draft, a plan only, waiting for your answers; nothing is approved to build and nothing will be spent without your approval** · Full record: [`M12c-agent-cells.md`](M12c-agent-cells.md) · Decisions: `docs/decisions.md`, "2026-11-21 — M12c agent-proposed cells" (PROPOSED)

## What you would be able to do

After charting your first 20 or so studies by hand, you run a measurement: the agent charts the same studies without seeing your values, and a report shows, column by column, how often it agreed with you, where it said "not reported" when you found a value, and what it cost. You open the agent only to the columns whose numbers you accept. On the remaining studies, each proposal appears beside its empty cell with the passage it relies on, highlighted on its page in the full text. You adopt it with one key, edit it or reject it; an agent's "not reported" you always type yourself. The export and the methods text say which cells came from the agent and how many you changed.

## Before any of it, in order

1. **M12b-read**: the PDFs you attached or confirmed (M12a Parts A and F) read into text page by page, with a failed parse shown as a failure (today it passes as success) and scanned papers marked "needs OCR".
2. A check that every quote is really in that text, on the page it names.
3. The highlighter from M8b, on the full text.
4. The measurement on your rows, with a spend you approve.
5. The contract decision (question 1).

## Questions (the first two touch the contract or an accepted decision)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| 1 | **Contract v1.** You decided that charting stays outside the contract "for now", with a contract decision before an agent proposes cells. Make proposals and cells typed Contract v1 records as the first part of M12c? | **Yes**, a part of its own (M12c-0) before any proposal is adopted. | One RELEASE PR: models, schemas, golden fixtures, a negative test, an independent review. |
| 2 | **Provenance.** Record an adopted value as `AGENT_ADOPTED` with the agent as its author and the proposal named, as the ladder decision of 2026-11-10 (item 1) does for screening, and an edited value as yours, naming the proposal it replaced? | **Yes.** | Nothing beyond M12c-2. |
| 3 | **How the agent runs.** From the app with your API key, the cost ceiling and the batches that screening uses; or through your own AI client over MCP (the M10c path, not yet tried with a real client), where the app checks the quotes but does not see the cost; or both? | **From the app first**: the measurement must be repeatable and its cost measured. MCP later. | The app path needs a key you create and a spend you approve. |
| 4 | **What may be sent to a provider.** Full texts are copyrighted unless openly licensed. Send every confirmed full text after a consent that names the provider and lists each study's licence; or only openly licensed texts (the licence the M12a fetch records); or ask per run? | **Every confirmed full text after a per-provider consent that lists the licences**, with the openly licensed-only choice offered on the run screen. Your institution's rules decide. | The consent screen and the licence column. |
| 5 | **When a proposal is shown.** Beside the empty cell as soon as you open the study; or hidden until you have typed your own value (no anchoring, but no time saved)? | **Beside the cell, never in it**, after the measurement; hidden during the measurement. | Anchoring risk, reported in the methods text as the share adopted unchanged. |
| 6 | **Which columns.** Each column opened to the agent by you, off by default, only after its measurement? | **Yes.** For your review the agent may help with cameras and data split, less with "sensor problems addressed". | Nothing. |
| 7 | **The measurement.** On at least 20 of your charted studies (the pilot and the next ones), each threshold set by you after reading the numbers (as for screening, where the thresholds are still open)? | **Yes, 20 at least.** | One measurement run, at a spend you approve; you chart 20 studies by hand first, which you would do anyway. |
| 8 | **An agent's "not reported".** Never adoptable with one key; you type it yourself? | **Yes.** An absence cannot be checked by quote. | A keystroke per such cell. |
| 9 | **Order.** M12b-read (reading full texts) first, then M12c-0 contract, M12c-1 measure, M12c-2 propose and adopt; all after M12a is built and you have charted by hand. Where does this sit against M9b to M9d and M10e in plan §6? | **After M12a and your first charted rows; before M9b to M9d**, since charting is where your time goes. | A planning decision for the main session. |

Nothing in this page asks to build or spend now. The rough cost in the record (one pass over 150 full texts at about three times one model's share of the M9a screening run) is a guess to be replaced by the estimate before any run.
