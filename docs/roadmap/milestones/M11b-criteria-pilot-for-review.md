# M11b Criteria pilot: for your review

Date: 2026-11-21 · Status: **questions open, nothing decided, nothing built** · Full record: [`M11b-criteria-pilot.md`](M11b-criteria-pilot.md) · Screens (drafts): `docs/ux/phase2-screening/final/13-criteria-pilot.md`, `docs/ux/phase0-inception/final/11-criteria-block.md`

## What you will be able to do

**At Inception's step 5**, the app warns when two criteria say the same thing, or the opposite of each other in the same words, when one criterion holds several tests, and when one needs the full text. It also asks two things it decides silently today: when you want to see the agent's draft, and what a draft does when an abstract does not report a criterion.

**After the corpus is accepted and batches are prepared**, Prepare offers "Pilot your criteria first". The app draws 50 records at random (the seed is recorded) and you screen them as usual, with the checklist open. Then one screen shows:
- which criteria decided the exclusions;
- which decided nothing;
- where you or the agent answered "not reported";
- where the agent read a criterion differently from you.

You can then revise a criterion (reword, split, merge, remove, add) with a one-sentence reason. Nothing you decided is lost. The records the revision could change come back for a second look, and the methods paragraph says the criteria were piloted on 50 records and revised, and how.

## Your review, replayed (illustration: the criteria are paraphrased and every pilot number is invented)

Your review has four inclusion and five exclusion criteria and 1,062 records. At step 5 the wording checks raise little: "RGB only" (EXC-02) and "multispectral imagery from a UAV" (INC-02) share no word, so the word rules cannot see that they are mirrors. That limit is real and the screen says so.

You draw a pilot of 50 and screen them in about 25 minutes: 30 Exclude, 8 Include, 12 Unclear. You let the agent check these 50 (Haiku, about $0.01). The result screen says:

- EXC-02 decided 14 of the 30 exclusions. The agent answered EXC-02 "yes" exactly when it answered INC-02 "no", in 46 of 48 records. **"EXC-02 and INC-02 look like mirrors: a record that fails INC-02 is already excluded."**
- INC-03 ("uses a learned model") was "not reported" in your checklist for 9 of the 12 Unclear records. Most were dataset papers. **"INC-03 is hard to judge from the abstract."**
- EXC-05 decided nothing. **"It may be rare, or covered by another criterion."**

You remove EXC-02 (reason: "mirror of INC-02") and reword INC-03 to "uses a learned model, or publishes a dataset meant for training one". Before you confirm, the dialog says the two revisions will show again **34 of your 50 decisions**: 8 Include, 12 Unclear, and 14 Exclude that cited EXC-02 (none of the 30 exclusions cited INC-03). You recheck them (about 15 minutes), pilot 50 more, see nothing new, and screen the rest. EXC-02 is retired and never reused, and the next new exclusion would be EXC-06. Your methods paragraph reads: "The screening criteria were piloted on 100 records drawn at random from the 1,062 records of the corpus (seed …). On 22 November 2026, EXC-02 was removed. Reason: mirror of INC-02. 14 records already decided were screened again. …"

## Questions, in order (the first four decide whether this is small or large)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| 1 | **How is a revised criterion recorded?** Changing a criterion today changes the protocol's fingerprint, and then every decision, the batches and the corpus stop counting. | **As an amendment beside the signed protocol,** like the method amendments of 20 November. The protocol file stays as signed, and the app records a criteria version on every decision. | No contract change, but RELEASE testing. It extends your 20 November rule (the signed protocol plus amendments is what is in force) from the method to the criteria. A *new signed protocol version* instead would keep the fingerprint exact but needs a contract decision and new schemas: several times larger. |
| 2 | **What happens to decisions already made** when you revise? | Kept. Every Include, every Unclear, and every Exclude that cited the changed criterion come back for a second look. The earlier decision stays in the log. A batch with a record waiting cannot be approved. | Re-reading: in the illustration, 34 of 50. Excludes for an untouched criterion are not shown again. |
| 3 | **What happens to `EXC-03`** when it is reworded, split, merged or removed? | Reworded: it keeps `EXC-03`, and the history keeps the old wording. Split, merged or removed: it is retired, and the new criteria get new numbers. **A number is never reused.** A new decision cannot cite a retired number. | Small. The other choice (a new number on every rewording) splits a criterion's PRISMA count across two labels. |
| 4 | **Until when can criteria be revised?** | From the moment batches are prepared until the **first batch is approved**. After that, refused: a change then means a new screening, as today. | A late revision (after 300 decisions) is allowed and may show many records again; the dialog gives the number before you confirm. |
| 5 | **The pilot sample:** size, how drawn, where its records go | 50 by default (20 to 100), simple random from the accepted corpus with a recorded seed, only undecided records. The decisions are ordinary decisions that count in the review. A second pilot after a revision is allowed. | Nothing extra. Not stratified, because the app has no strata to draw by. |
| 6 | **The checklist opens by default during the pilot** (today it is closed and optional) | Yes, still optional. Without your answers per criterion, the result cannot show where you were unsure and why. | A few seconds a record, on 50 records. |
| 7 | **Warnings without an AI model?** | Yes, rules only. There are five word checks at step 5 and seven answer patterns after the pilot. The answer patterns catch your own mirror (from the agent's per-criterion answers); the word checks do not. | A model check at Inception would mean spend and its own measurement. Your AI client can already ask the critic over MCP (not yet tried with a real client). |
| 8 | **The two method questions at step 5: the defaults** | Draft visibility: "after you decide the record" (as today). Not-reported rule: "exclude only on a clear failure, otherwise Unclear" (`decisive_first`) pre-selected for new reviews. Existing protocols do not change. | On the measured 1,644-record set, the agent's include recall (lower bound) is 92.2% under this rule, against 96.8% under `unclear`. The excludes it catches rise from 2% to 79%. |
| 9 | **"Check the agent on these 50 records"** | It reuses the existing calibration on your pilot decisions. The dialog always names the model, the count and the estimate. Drafts made before a revision are labelled and not counted. "Draft again" is offered with its cost. | About $0.01 for 50 records on Haiku. The route's own default is Opus, so the screen must never rely on it. |
| 10 | **Build order** | A (criteria in force) → B (pilot) → C (screens), then D (step 5) after M11a part C is merged. The build starts only when you say, because at most two milestones run at once. | A, B and D are RELEASE, C is STANDARD. In size, about M10b. |
