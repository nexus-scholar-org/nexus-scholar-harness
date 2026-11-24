# M13 Part B: settings and first-run setup

Status: **BUILDING on `dev/m13/part-b-settings` (from `main` `f2a7407e`), not pushed. Lane RELEASE.** The researcher gave the go on 2026-11-24 ("Start Part B"), relayed by the coordinator session "Nexus Scholar parent work". Specification: `docs/roadmap/milestones/M13-installers.md` §4.3 and §5.2 Part B, and Q7 (settings in a file, keys in the system keychain). Decisions: `docs/decisions.md`, entry "2026-11-24 — M13 Part B". Screen specification: `docs/ux/shared/final/05-settings.md`.

## Questions answered by the researcher (2026-11-24)

Asked before the build and answered one by one in the coordinator session, each as recommended.

| # | Question | Answer | Not chosen |
| :-- | :-- | :-- | :-- |
| 1 | Scope of the screen | **E-mail, keys and the reviews folder**, plus a Settings link on Workspaces and a Settings button in the control window. Connect (Part C) and the update notice (Part D) come later, with no placeholder now | Connect Claude Desktop in this part |
| 2 | Which value wins when one is set in several places | **The environment, then `.env` in the current folder, then the screen** (the settings file and the keychain). When a value comes from the environment or `.env`, the screen says so and does not offer to change it | The screen's value beats `.env` |
| 3 | When setup opens by itself | **Only on the installed start with no settings file yet.** `nexus-scholar ui` from a terminal lands where it does today; both starts get the Settings link | Both starts open setup at first run |
| 4 | "Later" | **Remembered** in the settings file, so setup does not reopen at every start; a search still stops and asks for the contact e-mail, pointing to Settings | Setup reopens at each start until an e-mail is saved |
| 5 | AI provider keys | **Three optional rows**: Anthropic, OpenAI-compatible, Google Gemini; set, replace or remove only, never shown; no base-URL setting | Anthropic only |
| 6 | No system keychain | **A file only this user can read, after a confirmation, wherever the keychain fails**; the screen says where the file is | Linux only; elsewhere keys cannot be stored |

## What Part B replaces from Part A

- The installed app's words that send a tester to a `.env` file in the settings folder: the contact e-mail and OpenAlex key cards, the look-up's e-mail refusal (Part A second pull request, decision item 1).
- "Not available in this version" for provider keys in the installed app (item 2).
- "Open the settings folder" standing in for a Settings button in the control window (item 4).
