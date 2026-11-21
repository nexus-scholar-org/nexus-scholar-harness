# M11b Criteria pilot: for your review

Date: 2026-11-21 · Status: **your ten answers recorded (2026-11-21); two new questions open; nothing built, build start not approved** · Full record: [`M11b-criteria-pilot.md`](M11b-criteria-pilot.md) · Screens (drafts): `docs/ux/phase2-screening/final/13-criteria-pilot.md`, `docs/ux/phase0-inception/final/11-criteria-block.md`

## What you will be able to do

**At Inception's step 5**, the app warns when two criteria say the same thing, or the opposite of each other in the same words, when one criterion holds several tests, and when one needs the full text. It also asks two things it decides silently today. The first is when you want to see the agent's draft ("after you decide the record" is pre-selected; this is still a proposal). The second is what a draft does when an abstract does not report a criterion: **no answer is pre-selected, and you cannot pass step 5 until you pick one.**

**After the corpus is accepted and batches are prepared**, Prepare offers "Pilot your criteria first". The app draws 50 records at random (the seed is recorded) and you screen them in Triage as usual, with the checklist closed as today. **These pilot decisions are kept apart and do not count:** the 50 records come back in the main screening, where you screen them again without seeing your pilot decision. Then one screen shows:
- how many records you included, excluded and left Unclear;
- which criteria were the reason for your exclusions, and which were never one;
- if you let the agent check the 50 records: which criteria it could not judge from the abstract, which ones look like mirrors, and where it read a criterion differently from you.

You can then revise a criterion (reword, split, merge, remove, add) with a one-sentence reason. A revision made after the pilot and before the main screening changes no counted decision. The methods paragraph says the criteria were piloted on 50 records that were not counted and screened again, and lists each revision.

## Your review, replayed (illustration: the criteria are paraphrased and every pilot number is invented)

Your review has four inclusion and five exclusion criteria and 1,062 records. At step 5 the wording checks raise little: "RGB only" (EXC-02) and "multispectral imagery from a UAV" (INC-02) share no word, so the word rules cannot see that they are mirrors. You pick a not-reported rule; nothing is chosen for you.

You draw a pilot of 50 and screen them in about 25 minutes: 30 Exclude, 8 Include, 12 Unclear. With nothing else, the result says:

- **EXC-05 was the reason for none of the 30 exclusions.** "It may be rare, or covered by another criterion."
- **12 of 50 Unclear (24%)**: under the 30% line, so no reading.
- Four readings need answers per criterion. The screen names them and offers the agent check.

You let the agent check these 50 records (Haiku, about $0.01). The result adds:

- The agent answered EXC-02 "yes" exactly when it answered INC-02 "no", in 46 of 48 records. **"EXC-02 and INC-02 look like mirrors: a record that fails INC-02 is already excluded."**
- The agent answered INC-03 ("uses a learned model") "not reported" in 27 of 50 records, mostly dataset papers. **"INC-03 is hard to judge from the abstract."**

You remove EXC-02 (reason: "mirror of INC-02") and reword INC-03 to "uses a learned model, or publishes a dataset meant for training one". The dialog says **no record will be shown again**, because no counted decision exists yet. You pilot 50 more, see nothing new, and start the main screening of all 1,062 records, the 100 pilot records among them. That costs about 50 minutes more than counting the pilot. EXC-02 is retired and never reused; the next new exclusion would be EXC-06. Your methods paragraph reads: "The screening criteria were piloted on 100 records drawn at random from the 1,062 records of the corpus (seed …). The pilot decisions were not counted; these records were screened again with the rest of the corpus. On 22 November 2026, EXC-02 was removed. Reason: mirror of INC-02. It was made after the pilot and before the main screening. …"

## Your answers (2026-11-21)

| # | Question | Your answer | |
| :-- | :-- | :-- | :-- |
| 1 | How a revised criterion is recorded | Amendment beside the protocol | as recommended |
| 2 | Decisions already made | Kept; affected ones return. Since answer 5 this applies only to decisions of the main screening | as recommended |
| 3 | Criterion numbers | Reworded keeps it; others retire; never reused | as recommended |
| 4 | Until when | Until the first batch is approved | as recommended |
| 5 | The pilot sample | **Pilot decisions not counted**: screened again in the main screening. 50 (20 to 100), random, seed recorded | **against the recommendation** |
| 6 | The checklist during the pilot | **Closed as today** | **against the recommendation** |
| 7 | Warnings without a model | Rules only | as recommended |
| 8 | The method defaults at step 5 | **No default; I must choose** the not-reported rule. Draft visibility "after you decide" stays pre-selected, as a proposal | **against the recommendation** |
| 9 | Check the agent on the pilot | Yes | as recommended |
| 10 | Build order | A, B, C, then D (D after M11a part C is merged) | as recommended; the order still holds |

**What your three choices change** (details in the record):
- **5:** pilot decisions go to their own file, never to the decision log, so nothing that counts can read them. While the pilot is open, its records cannot be decided in the main screening. After it, they are ordinary records again. Part B grows: a second place to record decisions.
- **6:** without per-criterion answers, three readings come from your decisions alone (many Unclear, does most of the work, never used). Four need the agent check: hard to judge, fire together, mirrors, read differently. The mirror in your review is caught only with the agent check.
- **8:** step 5 has a new blocker until you choose. Drafts started before the change meet it too, and so does an imported protocol without a method block. Existing reviews are not touched. One fix found while reworking: the choice must be kept in `intent.json`, or a later search change on a review that chose a non-default rule would be refused.

## Two new questions

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| 11 | **Can the pilot result show the agent's draft for one record?** Your pilot records come back in the main screening. If you saw the agent's draft for a record during the pilot, your later decision on it is not blind. Yet the screening contract of 4 November records it as blind: `proposal_shown` "is always `null` at decision time" with blinding on, and a reveal is only "the first time `GET /records/{id}/proposal` returns a proposal". | **Counts only:** the pilot result shows the agent per criterion, never per record, and the main screening shows nothing of your pilot decision. The contract is unchanged. | You cannot see which records the agent read differently. The alternatives each amend the contract's reveal rules: show a draft on request and record it as a reveal (up to 50 records leave the blind comparison), or report pilot records as decided with the draft visible. |
| 12 | **Does "I must choose" also apply to the terminal wizard** (`scholar-harness inception`)? It writes `unclear` without asking today (H-screening-drafts item 1: "`unclear` stays the default and the value genesis writes"). | **Yes:** the wizard asks with no default, and a scripted run needs `--not-reported <rule>`. | A small CLI change in part D. If you say no, a review made in the terminal still gets `unclear` silently. |
