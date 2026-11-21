# M12c Agent-proposed cells: for your review

Date: 2026-11-21 · Status: **your nine answers recorded (2026-11-21); two new questions where they meet decisions already taken; a plan only, nothing is approved to build and nothing will be spent without your approval** · Full record: [`M12c-agent-cells.md`](M12c-agent-cells.md) · Decisions: `docs/decisions.md`, "2026-11-21 — M12c agent-proposed cells"

## What you would be able to do

When you chart, you turn the agent on for the whole form with one switch. On each study, every column gets a proposal beside its empty cell, with the passage it relies on highlighted on its page in the full text. You adopt it with one key, edit it or reject it; an agent's "not reported" you always type yourself. Proposals come from the app with your API key (with an estimate and a ceiling you type before any spend), or from your own AI client over MCP, from the first release. As you work, the app counts per column how many proposals you adopted unchanged, edited or rejected, and how often the agent said "not reported" where you found a value. The export and the methods text say which cells came from the agent, those counts, and that the agent's accuracy was not measured.

## Your answers (2026-11-21)

| # | Question | Your answer |
| :-- | :-- | :-- |
| 1 | Contract v1 | "Yes, contract first" (as recommended) |
| 2 | Provenance | "Yes" (as recommended); see N2 |
| 3 | How the agent runs | **"Both from the start"** (recommended: the app first). Adds a part of its own for the MCP path (size M). Over MCP the app does not see the cost or the model behind your client; it records the model your client declares. |
| 4 | What may be sent | "All, after consent" (as recommended) |
| 5 | When a proposal is shown | "Beside the cell, never in it" (as recommended) |
| 6 | Which columns | **"All columns at once"** (recommended: one by one after measuring). One switch for the whole form. No decision taken earlier is affected. |
| 7 | The measurement | **"no time to chart by hand just do it without measuring"** (recommended: 20 studies first), then "Count as I work". The measurement part is dropped. See below for what this leaves unknown, and N1. |
| 8 | An agent's "not reported" | "Yes, I type it" (as recommended) |
| 9 | Order | "After M12a, before M9b–M9d" (as recommended) |

## What "count as I work" tells you, and what it does not

It tells you how much of your table came from the agent and how much you changed, per column. It does **not** tell you how often the agent is right: a value you adopted after seeing it and its quote counts as adopted even if it was wrong and looked right, and nobody charted those studies without the agent to compare. A value the agent missed is caught only if you look for it while typing its "not reported"; if you type Not reported on the agent's word, the miss stays invisible. The methods text will say: "The model's accuracy was not measured against independent charting, and the reviewer saw each proposal before recording a value."

## The plan now

**M12b-read** (reading the PDFs as text, page by page; large), then **M12c-0** (the contract; medium), then **M12c-2** (proposals from the app, adopt/edit/reject, the counts, the screens; large), then **M12c-3** (the MCP path; medium). All four are reviewed in the RELEASE lane. They come after M12a and before the screening ladder work (M9b to M9d). The agent is offered once M12c-3 is in, so both paths start together.

## New questions (each meets a decision already taken)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| N1 | **An eval set for the charting task.** Your decision of 2026-11-03 says each AI task has "a prompt, an output schema, a model and effort setting, and an eval set", and that a change "needs a new task version and an eval re-run". It names Phases 0–2; charting is Phase 3. With no measurement, the charting task has no eval set. (a) Give it a small one that needs none of your charting: about five open-access papers outside your review, their values written by the developer for a two-column test form, run once per task version, checking that answers parse, quotes pass and values fit; it shows the task works, not that it is right on your review. Or (b) no eval set for this task, the counts standing in, with a note on the 2026-11-03 decision. | **(a).** It is the only check before the agent touches your review, and it costs none of your time. | (a) A small STANDARD part and a run of a few dollars, which you approve. (b) Nothing. |
| N2 | **How an adopted cell is recorded.** You said yes to `AGENT_ADOPTED` with the agent as author. The ladder decision of 2026-11-10 says such an event is "minted by the engine only, carrying the proposal, the mode, the calibration run and the human who set the mode. A client can never post one." Here there is no autonomy mode and, with answer 7, no calibration run. (a) Keep `AGENT_ADOPTED` for cells: the engine mints it when you press Adopt (you never post it), and it carries the proposal, you as the adopter, "adopted one at a time" in place of a mode, and "none" in place of a calibration run; screening's rule stays as it is. Or (b) record an adopted cell as yours (`HUMAN`) naming the proposal, as a screening decision taken after seeing a draft is recorded today. | **(a).** It keeps what you chose in answer 2, says plainly that nothing was calibrated, and changes nothing in screening. | (a) Part of M12c-0, no extra size. |
