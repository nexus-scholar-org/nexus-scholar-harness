# H-workspace-format-version

Status: **SPECIFICATION, 2026-11-23; six questions for the researcher (Â§7); nothing built.** Branch `dev/h/workspace-format-version`, cut from `origin/main` `cc0e8fa1` (the merge of release `1.1.0b7`, PR #307). Lane for the build: **RELEASE** (a new persisted file in every workspace and a change to how every workspace is opened).

Source: the project review of 2026-11-23, finding 9 and recommendation 8 ("A format version on the workspace and a copy made before a newer build first opens it"; on local branch `dev/docs/project-review-2026-11-23`), and the researcher's answer to question 11 of `docs/roadmap/milestones/M13-installers.md` (build it as its own piece of work, before installers go to outside testers). The instruction to start, in the coordinator's brief: "Start Part A and the workspace format version". Part A of M13 (the launcher) is built in parallel by another session; this work needs no change to `console/launcher.py`, `console/code_window.py` or the start-up path of `nexus-scholar ui` (Â§3.2).

Written from the code at `cc0e8fa1`. The comparison with `v1.1.0b6` in Â§1.4 was made by reading the tag's code (`git show v1.1.0b6:â€¦`), partly by a read-only subagent; its two strongest claims were opened again by this session (marked).

---

## 1. What the code does today

### 1.1 Where a workspace is created

| Door | Code | What it writes |
| :-- | :-- | :-- |
| `nexus-scholar init <title>` (with or without `--scaffold-only`) | `cli.py:142`; `inception/genesis.py:735` `scaffold_placeholder_workspace` | through `emit_workspace` (below), then the support files `genesis.py:590` (`.agents/skills/`, `.env.example`, `.mcp.json`, `.gitignore`) |
| The Workspaces screen, **New** | `console/api/workspaces.py:49` â†’ `workspace/catalog.py:220` `create` â†’ `scaffold_placeholder_workspace` | the same as `init --scaffold-only` (agent `nexus-scholar/ui`) |
| Inception genesis (wizard, browser inception, the bridge) | `inception/emit.py:315` `emit_workspace`, the one gated genesis path | a new folder: `scaffold_raw_project` (`genesis.py:252`, writes `project.json` at `:295` and the `PROJECT_INITIALIZED` row) or, in the monorepo layout, `scaffold_project` (`genesis.py:210`), which runs the workspace-manager script `.agents/skills/workspace-manager/scripts/init_project.py` as a subprocess; then `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md` (`genesis.py:192`), `protocol_origin` into `project.json` (`emit.py:289`), the `GENESIS` row. The file list shown at the write gate is `NEW_WORKSPACE_FILES` (`emit.py:86`), kept exact by a test |
| Protocol replacement (`--replace`) | `emit.py:377-404` | backs the protocol files up to `audit/replaced/<UTC stamp>/` (`emit.py:271`), **moves** the old corpus there (`ARCHIVED_ON_REPLACE`, `emit.py:49`: `literature/`, `pdfs/`, `extracted/`, `charting/`, â€¦), rewrites `project.json` keeping its other fields (`emit.py:300`) |
| The placeholder workspaces | the same two placeholder doors above (`catalog.create`, `init --scaffold-only`) | a deterministic placeholder protocol (`genesis.py:680`) |

### 1.2 Where a workspace is opened

There is **no single open path**. Every door takes a folder and reads or writes it directly.

| Door | Code | Reads or writes |
| :-- | :-- | :-- |
| `nexus-scholar ui` start | `cli.py:1619-1661` | **opens the most recent workspace automatically** when `--workspace` is not given (`cli.py:1651`, `catalog.most_recent`, `catalog.py:139`). So the first start of a new build opens the researcher's latest review for writing with no click. |
| The launcher's restart (Open on the Workspaces screen) | `console/api/workspaces.py:63-81` â†’ `catalog.check_open` (`catalog.py:257`) â†’ `app.state.on_open` â†’ `launcher.py:105` `request_open` â†’ `launcher.py:119-137` builds a new app | the open route answers 202 and the restart happens after (`workspaces.py:80`) |
| `scholar-harness serve --workspace` | `cli.py:1557-1616` | |
| All three above build the server with | `console/serve.py:136` `create_app(workspace, â€¦)` (`launcher.py:87-103` calls it) | the **one common point** of the browser app; `ws=None` means "no workspace open" (`serve.py:172-176`, `:274-275`, `_no_workspace` `:110`) |
| Command-line commands that take `--workspace` or a path | `cli.py`: `status` `:79`, `setup-mcp` `:169`, `doctor` `:198`, `log event/batch/sync-index` `:242-311`, `gate *` `:455-591`, `extract status/publish` `:718-748`, `supervise` `:785`, `sync` `:891`, `run` `:1143`, `export` `:1241`, `accept-corpus` `:1369`, `chase run/status/accept` `:1428-1526` | each reads or writes the folder directly |
| The screening hand-off script | `src/scholar_harness/agent_screen.py prepare|<status>|collect <workspace>` (AGENTS.md) | writes batches and collected files |
| The MCP server (`uv run scholar-agent`) | `src/scholar_agent/server.py`: paths anchored to `NEXUS_MCP_WORKSPACE` (`:173-176`), journal rows through `scholar_harness.workspace.audit.append_event` (`:272-310`), workspace tools such as `nexus_pipeline_run` (`:581`), the screening tools (`:1430` onward) | writes per tool call |
| Skill scripts run by an agent | `.agents/skills/workspace-manager/scripts/log_event.py`, `batch_log.py`, `init_project.py`; vendored into each workspace (`genesis.py:590`), possibly an old copy | append to the journal, rewrite `project.json` and `INDEX.md` |
| The journal writer every in-package door uses | `workspace/audit.py:146-212` `append_event` (legacy append `:231`) (and the legacy append below it) | appends one line, then rewrites `project.json` (`updated_at`, `workspace/manifest.py` `update_manifest_for_event`) and `INDEX.md` |

### 1.3 How a workspace is judged valid

`workspace/catalog.py:50` `validity`: a folder is a workspace when it holds the three `MARKERS` (`catalog.py:26`: `protocol.json`, `project.json`, `audit/journal.jsonl`). Nothing else is read. The Workspaces list skips dot-folders and symlinks out of the root (`catalog.py:163-175`). `doctor.py:254` has its own, wider marker list. `genesis.py:65` `INIT_MARKERS` decides that `init` refuses a folder.

### 1.4 Version-like fields today

- **No workspace-wide format version** anywhere (the review's E22, confirmed: no `format_version` or `schema_version` in `workspace/`, `catalog.py`, `serve.py`, `doctor.py`; no migration code).
- `project.json` `"$schema"` is the JSON Schema draft URI (`genesis.py:277`), not a format. `protocol.json` `"$schema"` names `schemas/v1/protocol.schema.json` (`inception/importer.py:35`), the protocol's contract schema.
- Single files carry their own schema strings, and several readers refuse a value they do not know: the screening generation (`authority/generations.py:72`, checked at `:238`), the pairing (`authority/pairing.py:63`, `:401`), the charting form (`charting/form.py:38`, `:111-114`, "not a charting form this version reads; it is kept as it is"), verification checks (`pipeline/verification.py:105`, `:127`), adoption declarations (`screening/adoption.py:50`, `:147`), screening rounds (`screening/rounds.py:34`, `:85`), the corpus import manifest (`corpus_accept.py:667`, `:643`), the combined corpus (`corpus_accept.py:958`). Decision and batch files carry `"schema_version": "1.0.0"` (`screening/batcher.py:327`, `screening/collector.py:703`); Contract v1 artifacts carry `contract_version` `1.0.0` (`contracts/models.py:16`). `charting/form.json` has a `version` that counts form amendments (`charting/form.py:139`, `:336`), not a format. `charting.table-v1` (`charting/table.py:33`), `review.next-step-v1` and the other `shape` strings are API answer shapes, not files.
- The journal rows (`audit/journal.jsonl`) have no version; `append_event` accepts any action name (`workspace/audit.py:183-194`), and the b6 readers skip actions they do not know (subagent, `generations.py:1124`, `export.py:397` at b6).

These per-file strings protect single readers. None of them tells a build, before it writes anything, that the workspace as a whole was written by a newer build.

### 1.5 What changed in workspace files since `v1.1.0b6` (2026-11-10), and what b6 would do with it

614 commits; 143 source files changed. What a b6 build does with a workspace written by `main`:

| File or path | Change | What b6 does |
| :-- | :-- | :-- |
| `protocol.json` `method.not_reported = "decisive_first"` (M11b part D) | the value is new | **refuses**: b6 `MethodConfig` allows only `unclear`/`exclude` (`git show v1.1.0b6:src/scholar_protocol/models.py`; main `models.py:342`) under `extra="forbid"`, so every protocol read fails. *Opened by this session.* |
| `audit/method_amendments.jsonl` (H-screening-drafts; main `screening/method.py:135`) | new | **misreads**: b6 uses the signed method; the not-reported rule, the reveal and the methods text are wrong. *File constant opened by this session; b6 behaviour from the subagent.* |
| `audit/criteria_amendments.jsonl`, `audit/amended/` (M11b part A, `screening/criteria.py:44-47`) | new; rewrites `SCREENING_CRITERIA.md` and the batch decision files, not `protocol.json` | **misreads and overwrites**: b6 knows only the protocol's criteria ids, refuses amended ids, and re-projects the decision files on its next intake, putting back records that were "shown again" |
| `audit/adoption_declarations.jsonl` (H-adopted-decisions-disclosure) | new | ignores it; its **methods text overstates human reading** |
| combined corpus manifest `nexus.corpus-combined.v1` (M3f) | new | treats it as a plain harvest; its methods text names only the imported databases |
| `literature/screening_rounds/` (M3g) | new | **misreads**: counts round-1 batches above round 2's count as current |
| `charting/` (M12a), `literature/citation_chase/`, `audit/query_development/` (M11a), `literature/screening/pilot/` (M11b), harvest marker, verification checks | new | ignores them (several "not opened" by the subagent) |
| `pdfs/<study>.pdf` attached by the researcher, `pdfs/replaced/`, `pdfs/fetched/` (M12a) | new | counts and extracts the attached files (mild) |
| `project.json` `protocol_origin`, `audit/proposals.jsonl`, `audit/check_dismissals.jsonl` (M10b) | new | ignores; `project.json` writers on both sides merge, so the field survives (`workspace/manifest.py` unchanged; b6 `orchestrator.sync_state` merges) |
| inception replacement | main archives the corpus (`emit.py:49`); b6 backs up only the three protocol files | b6 **leaves** `literature/`, `charting/`, `pdfs/` under a new protocol |

So within thirteen days, at least five changes would make an older build refuse, misread or overwrite a newer workspace. Today nothing stops it.

### 1.6 How large a workspace is, and what is re-creatable

Measured on the development workspaces in the main checkout (`workspaces/`, not the researcher's reviews, which were not opened):

| Workspace | Total | Largest parts |
| :-- | --: | :-- |
| `uav-crop-weed-v03` (about 14,000 screened records) | 434 MB | `calibration_v03/` 341 MB (a legacy folder of raw harvests), `literature/` 91 MB (`screening/` 60 MB, `excluded.json` 29 MB, `included.json` 1.6 MB), `extracted/` 0.4 MB, `audit/` 0.2 MB (journal 0.18 MB), `charting/` 0.14 MB; `pdfs/` empty here (git-ignored) |
| `golden-uav-30-run-2026-11-06` | 0.6 MB | `literature/` 0.45 MB |

A real review holds `pdfs/` of hundreds of megabytes (the brief; not measured here). The parts:

- **Not re-creatable** (the review itself): `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md`, `project.json`, `audit/` (journal, registry, amendments, declarations, proposals), `artifacts/`, `literature/` (search runs hold provider answers that change over time; batches, decision events, publications, rounds), `charting/`, `synthesis/literature_review.md` (the researcher's notes), the root's other hand-made files.
- **Re-creatable or derived**: `extracted/` (from the PDFs), `.cache/`, `chroma_db/`, `rag/` (removed features), `exports/` (made again by Export), `.agents/skills/` and `.mcp.json` (vendored by `install_workspace_support_files`), `.harness-console/` (the console's job records).
- **Partly re-creatable**: `pdfs/`. Fetched open-access files can be fetched again while their links live (`charting/fetch_manifest.jsonl`); files the researcher **attached by hand** (`charting/attachments.py:1-12`) are re-creatable only from the researcher's own copy.
- **Secret**: `.env` (keys). Never copied.

---

## 2. The format version

**Where it lives.** One small file at the workspace root, `workspace_format.json`, written atomically (temporary file and replace) by one owner, `scholar_harness/workspace/format.py`:

```json
{
  "schema": "nexus.workspace-format.v1",
  "format": 1,
  "written_by": "1.1.0b8",
  "updated_at": "2026-11-30T10:00:00+00:00"
}
```

- `format` is **one number for the whole workspace**: the newest layout its files follow. It goes up by one whenever a change would make an older build refuse, misread or overwrite something (the kinds of change in Â§1.5).
- `written_by` is the newest build that opened the workspace for writing (the installed package version). It is used by question 1 (a copy before each newer build) and by the newer-format message.
- Not a field in `project.json`, because `project.json` is rewritten by at least five writers, some outside the package (`workspace/manifest.py`, `orchestrator.sync_state`, `emit.py:289` and `:300`, the vendored `log_event.py`), each reading and writing it back; a race between two of them can drop a field, and then the next open would copy and stamp again. A file only one module writes avoids that, older builds never touch it, and its absence is unambiguous.
- `validity` (`catalog.py:50`) is unchanged: the file is not a marker, so every existing workspace stays valid.

**Who writes it, and when.**

1. **At birth**: every genesis door writes it with the current format and build (`scaffold_raw_project`, `genesis.py:252`; the workspace-manager script `init_project.py`, so the monorepo layout is stamped too). `NEW_WORKSPACE_FILES` (`emit.py:86`) gains it, so the write gate shows it. A protocol replacement keeps it (a root file, not in `ARCHIVED_ON_REPLACE`).
2. **At the first open for writing** by a build (Â§3): after the copy, by the migration steps.
3. **Never on a read.** The Workspaces list (`catalog.listing`, `describe`), `most_recent`, `status`, `doctor` and every display route read the file and never create or change it. The catalog's own rule ("It reads files only; it never holds a workspace open", `catalog.py:6`) stays true. Opening a workspace in the browser app counts as opening for writing, because the server may write on any request.

**A workspace without the file** (every existing workspace) is read as **format 0**: "written before format versions existed". It is opened like any older format (Â§3): copied, then stamped as 1 by the first migration step, which rewrites no file.

---

## 3. Opening a workspace

### 3.1 The one check, `prepare_for_writing(ws)`

One function in `workspace/format.py`, called by every door that may write (Â§3.2). It reads one small file, so it is cheap; after a success it is remembered for that folder for the life of the process.

1. Read `workspace_format.json`. Missing: format 0. Unreadable, not JSON, a `format` that is not a whole number, or a `schema` it does not know: refuse `WORKSPACE_FORMAT_UNREADABLE` (it never guesses).
2. `format` newer than this build's `CURRENT_FORMAT`: refuse `WORKSPACE_FORMAT_NEWER` (Â§3.4). Nothing is written.
3. Decide whether a copy is needed: the format is older, or (question 1, recommended) `written_by` is older than this build. Same format and same build: return at once; nothing is written.
4. Take the workspace's format lock (`audit/.format.lock`, created exclusively; one holder at a time, so two windows opening one review at once make one copy).
5. Make the copy (Â§3.3). If it fails: delete the partial file, release the lock, refuse `WORKSPACE_COPY_FAILED`. The workspace has not been written.
6. For each step from the workspace's format up to `CURRENT_FORMAT` (Â§4): one journal row naming the step, the copy and what it changes, then the step, then `workspace_format.json` with the step's `format`. A crash between the row and the stamp re-runs the step on the next open (steps are idempotent) and makes a second copy; the normal path makes one.
7. Same format but an older `written_by`: one journal row `WORKSPACE_OPENED_BY_NEWER_BUILD` naming the copy, then `written_by` updated.
8. Remove this workspace's older copies beyond the number kept (question 3), only after the new one is verified, and only copies this mechanism made.

The journal rows use `append_event` with `refresh_index=False`. So the stamp changes exactly three things: the new or rewritten `workspace_format.json`, one or more appended journal lines, and `project.json`'s `updated_at` (the standard projection, `workspace/manifest.py`). Every other file is byte-identical.

### 3.2 Which doors call it

| Door | Where the call goes | Why there |
| :-- | :-- | :-- |
| The browser app at start (`ui`, `serve`) and after every restart | `create_app` (`serve.py:136`), before the job runner is made (`serve.py:190`) | the one point all three paths share (Â§1.2); no edit to the launcher. On a refusal the app starts with **no workspace open** and remembers the refusal: every workspace route answers it (409, its code and message) instead of `WORKSPACE_NOT_VALID`, and the Workspaces list shows it on the row. Since `ui` without `--workspace` lands on the Workspaces screen (`launcher.py:113`, `cli.py:1655`), the researcher sees the row and the reason. |
| Open on the Workspaces screen | `catalog.check_open` (`catalog.py:257`), before the 202 | a failure is answered on the screen (409) while the current workspace stays open; `on_open` is not called. `create_app` then finds the work done. |
| The command line | each command that writes: `init` (stamps at birth), `setup-mcp`, `log event/batch/sync-index`, `extract publish`, `supervise`, `inception` (on an existing workspace), `sync`, `run`, `export`, `accept-corpus`, `chase run/accept`, `gate import`, `serve`, `ui` (through `create_app`); not `status`, `doctor`, `chase status`, `extract status`, `gate estimate/measure` (reads; to be confirmed per command in the build) | before the command's first write; a refusal prints the message and exits non-zero |
| `agent_screen.py prepare|collect` | at the start | |
| The MCP server | each workspace-writing tool, through one helper next to `_screening_workspace` (`server.py:1430`) and the pipeline tool (`server.py:581`) | |
| **Backstop**: `append_event` and the legacy append (`workspace/audit.py`) | refuse `WORKSPACE_FORMAT_NEWER` before the append | every journalled write of the package, including a door the build forgets. It does not copy (a copy there would come after the operation's first writes). |
| The vendored `log_event.py` / `batch_log.py` | the same newer-format refusal, written inline (the script may not import the package) | a script copy vendored before this build has no check; that cannot be fixed from here (Â§8) |

Coordination with M13 Part A: none needed. If Part A adds its own start-up step before `Launcher(...)`, it may call `prepare_for_writing` there to print the refusal to the log file as well; `create_app` stays the guarantee.

### 3.3 The copy

- **What is copied** (question 2, recommended): every file of the workspace **except** `pdfs/`, `extracted/`, `.cache/`, `chroma_db/`, `rag/`, `exports/`, `.agents/`, `.harness-console/`, `.env`, and the same folders inside `audit/replaced/<stamp>/` (an archived corpus holds its own `pdfs/`). The workspace's own lock files are skipped.
- **Form**: one zip file (deflate), written as `<name>.zip.partial`, then checked (every member's CRC by `ZipFile.testzip`, the member count and sizes against the list that was copied), then renamed. A zip keeps paths short (the Windows 260-character limit has already failed a gate, review section 3) and compresses JSON several times (not measured on a real review).
- **Where**: `<the workspace's parent folder>/.nexus-copies/<slug>/`, which for a listed workspace is the workspaces folder (question 3). The dot keeps it out of the Workspaces list (`catalog.py:168`). For a repository checkout, `workspaces/.nexus-copies/` is added to `.gitignore`.
- **Name**: `<slug>-<UTC yyyymmddTHHMMSSZ>-format<from>-to<to>-<built by>-to-<this build>.zip`, for example `sensor-stress-20261130T100000Z-format0-to1-1.1.0b7-to-1.1.0b8.zip`. A `README.txt` beside the copies says what they are and how to restore one.
- **How many**: the five newest per workspace (question 3); older ones made by this mechanism are deleted after a new copy is verified. Nothing else in the folder is touched.
- **Restore** (in the user guide, by hand; a restore command is a later, separate item):
  1. Close Nexus Scholar.
  2. Rename the workspace folder aside (for example `sensor-stress-newer`).
  3. Unzip the copy into a new folder with the workspace's name.
  4. Move `pdfs/` (and `extracted/` if wanted) from the renamed folder into it. **No migration step ever writes these folders** (rule in Â§4), so they are still right; PDFs added after the copy simply stay.
  5. Open it with the older build (a newer one would copy and stamp it again).
  Without the old folder's `pdfs/`, the restored review is complete except its PDFs: fetched ones can be fetched again; attached ones come from the researcher's own files.
- **The copy is not a backup.** It guards against a newer build's change, not against the loss of the disk or the folder (it sits beside the workspace). The guide says so.

**What the user sees.**

- Browser: once, on the first screen after the copy, a notice: "Before opening this review, Nexus Scholar 1.1.0b8 saved a copy of it (without the PDFs) in `<folder>`. You do not need to do anything." The row on the Workspaces screen names the last copy (question 5).
- Command line: one line with the same words and the zip's path.
- Journal: the rows of Â§3.1 (so the review's own history records the copy).

**If the copy fails** (disk full, no permission, path too long, a file that cannot be read): the workspace is **not opened for writing**. Browser, `WORKSPACE_COPY_FAILED` (409):

> **This review was not opened.** Nexus Scholar saves a copy of a review before a newer version opens it, and the copy could not be saved: *{reason}*. Nothing in the review was changed. Free some disk space or check that the folder `{copies folder}` can be written, then try again.

There is no override in the app; a failed copy stays a refusal.

### 3.4 A workspace written by a newer build

Recommended (question 4): **refuse to open it**. Nothing is written; the Workspaces list still lists it (a read) with a badge; `status` still reads it; every writing door refuses; the journal backstop refuses. Browser, `WORKSPACE_FORMAT_NEWER` (409):

> **Made with a newer version of Nexus Scholar.** This review was last opened with Nexus Scholar {written_by}, which stores reviews in a way this version ({this build}) cannot read safely. To keep it intact, this version does not open it. Install Nexus Scholar {written_by} or later to continue.

Only builds with this work protect anything: `1.1.0b7` and earlier have no check and will open any workspace (Â§8).

---

## 4. Migrations

- **The registry**: `workspace/format.py` holds `CURRENT_FORMAT` and one step per number, `STEPS[n]` from `n` to `n + 1`, each with a name, a one-line description, and `apply(ws) -> list[str]` (the files it changed).
- **Rules for every step**: it is **idempotent** (applying it to its own output changes nothing); it is **journalled** (one row `WORKSPACE_FORMAT_MIGRATED` with `from`, `to`, `step`, the changed files and the copy); it writes only files that the copy contains, never `pdfs/`, `extracted/` or the other excluded folders (so the restore of Â§3.3 is complete); it never changes `protocol.json`, a Contract v1 artifact, a fingerprint or a published generation unless a contract decision says so (then the step is part of that decision).
- **The first step, 0 to 1, `stamp-today`**: rewrites no file. It records that the workspace follows the layout of `main` at `cc0e8fa1` (`1.1.0b7`). Journal row `WORKSPACE_FORMAT_STAMPED`. (A workspace written by b6 or earlier is read by today's code as it is; that is how `1.1.0b7` opens it today. Not tested for every older layout, Â§8.)
- **The rule for later work** (into `DEVELOPER_COMPASS.md` and `AGENTS.md`): a change that an older build would refuse, misread or overwrite (Â§1.5 is the catalogue of kinds) raises `CURRENT_FORMAT` by one and adds a step, even an empty one, with its test. The review of a milestone checks it.

---

## 5. What does not change

- **No Contract v1 file**, no schema, no golden fixture; `generate_contract_baseline.py --check` stays current (run at `cc0e8fa1`: "Contract baseline current").
- **No fingerprint or digest.** The protocol fingerprint is computed from `protocol.json` alone (`authority/generations.py:971` `_protocol_fingerprint`); the registered workspace id is read from `project.json` (`generations.py:959`), whose content changes only in `updated_at`; a publication binds the batch files, the published outputs, the approval and the protocol (`screening/currentness.py:1-9`), none of which the stamp touches. A search for a digest over `audit/journal.jsonl`, `project.json` or `INDEX.md` found none. So the stamp changes no fingerprint, no corpus snapshot and no generation's currentness.
- **What the stamp does change that a user can see**: the journal row becomes the workspace's last event, so the Workspaces list shows it as the last activity (`catalog.py:59-70`) and the stamped workspace becomes "most recent" (`catalog.py:139-144`, the one `ui` opens next). The build shows the copy's row with readable words, or ranks by the last row that is not a format row (a choice for the build, Â§6 test 6).
- No published generation is re-made; no decision, batch or export is rewritten.

---

## 6. Definition of done

Lane **RELEASE**. Each test below fails on `cc0e8fa1` (there is no `workspace/format.py`, no copy and no refusal today).

1. **Unstamped workspace, first open for writing.** A fixture workspace with no `workspace_format.json` (a genesis output with the file removed, and a second fixture whose layout was written by `v1.1.0b6`, see 13). `create_app(ws)`: one zip in `.nexus-copies/<slug>/`; `workspace_format.json` says `format: 1` and this build; the journal is the old journal plus the new rows; `project.json` differs only in `updated_at`; **every other file is byte-identical** (SHA-256 of every file before and after).
2. **Second open makes no second copy**: a second `create_app` and a `check_open`: no new zip, no new row, no byte changed.
3. **Failed copy**: the copies folder unwritable, and separately the zip writer made to raise `OSError` midway: `WORKSPACE_COPY_FAILED`; no `.partial` left; the workspace byte-identical; `create_app` answers 409 with that code on a workspace route (a GET and a POST); `POST /workspaces/open` answers 409 and `on_open` is not called.
4. **Newer format** (`format: 2`): `create_app` routes answer `WORKSPACE_FORMAT_NEWER`; `append_event` raises before appending; each command-line write door in the list of Â§3.2 exits non-zero with the message (table-driven); the MCP writing helper refuses; the workspace is byte-identical after all of them. The Workspaces list still lists it, with the badge.
5. **What the copy holds**: a workspace with `pdfs/`, `extracted/`, `.cache/`, `.env`, `exports/`, `.agents/` and `audit/replaced/<stamp>/pdfs/`: none of them in the zip; every other file is. **Restore**: unzip, move the live `pdfs/` in: the tree is byte-identical to the workspace before the open; `validity` is true; the screening summary route answers the same counts as before the open.
6. **Reads never write**: `listing`, `describe`, `most_recent`, `status` and a display route on an unstamped workspace: no copy, no stamp, no byte changed; the list reports the format as not yet recorded. The last-activity column after a stamp shows the decided wording.
7. **Birth**: `catalog.create`, `init --scaffold-only` and `emit_workspace` (both layouts, including the `init_project.py` script) write `workspace_format.json` with the current format; their first open makes no copy; `NEW_WORKSPACE_FILES` names the file and its test passes.
8. **Registry**: every `n < CURRENT_FORMAT` has a step to `n + 1`; each step applied twice equals once; step 0 to 1 changes no file.
9. **Crash mid-way**: an exception after the copy and before the stamp: the next open completes; nothing outside the format file and the journal changed.
10. **Newer build, same format** (if question 1 is answered as recommended): an older `written_by`: a copy and `WORKSPACE_OPENED_BY_NEWER_BUILD`; the same build: nothing.
11. **Pruning**: six opens by six builds keep the five newest copies; a file in `.nexus-copies/<slug>/` not made by this mechanism is never deleted.
12. **Unreadable format file**: `WORKSPACE_FORMAT_UNREADABLE`, nothing written.
13. **The real older layout**: a workspace made by the `v1.1.0b6` tag's code (`git worktree add <temp> v1.1.0b6`, then `uv run --project <temp> nexus-scholar init "Old layout" --scaffold-only --dir <temp root>/old-layout`, plus a small screened corpus if the b6 code can make one offline from the golden cassette), opened by the new build through `nexus-scholar ui --root <temp root> --no-browser` on a free port (never 8792): copy, stamp, the app's screens answer. Recorded in the evidence with the commands.
- The checks of `AGENTS.md`: both ruff runs, `generate_contract_baseline.py --check`, the selector's `pr` gate for the touched areas, `select_test_gate.py --check`; `uv build --wheel` and both entry points' `--help` on a base install.
- The user guide: a section "The copy made before an update" with the restore steps of Â§3.3; `DEVELOPER_COMPASS.md` and `AGENTS.md`: the rule of Â§4; `.gitignore`: `workspaces/.nexus-copies/`.
- The web app: the notice, the row's copy line and the two refusals, in English, French and Arabic, with their component tests.
- Independent review (`milestone-reviewer`) APPROVE; the record's evidence table; a decisions entry with "for the researcher to decide" kept apart from "choices made in the build".

---

## 7. Questions for the researcher

1. **When is a copy made?** *Recommended:* **when the workspace's format is older than the build's, and also when the build is newer than the one that last wrote it** (your words in M13 question 11: "a copy made before a newer build first opens it"). *Not chosen:* only when the format number changes (fewer copies, but it relies on every developer raising the number; in the thirteen days after b6 at least five changes needed it, Â§1.5); a copy at every open (many identical copies). *Known cost:* one copy per review per release, made at its first open (about 90 MB of `literature/` in a 14,000-record review before compression; the zip's size and time are not measured).
2. **What is copied?** *Recommended:* **everything except the PDFs, the extracted text, caches, exports, the vendored skills and the key file** (`pdfs/`, `extracted/`, `.cache/`, `chroma_db/`, `rag/`, `exports/`, `.agents/`, `.harness-console/`, `.env`, and those folders inside `audit/replaced/`). *Not chosen:* everything including PDFs (hundreds of megabytes per release and a slow first open); only the authoritative files (protocol, `audit/`, `literature/`), which misses `charting/` and the review notes. *Known cost:* PDFs you attached by hand are not in the copy; a restore takes the current `pdfs/` folder (no migration writes it), and if the workspace folder itself is lost, the copy does not bring the PDFs back.
3. **Where are copies kept, and how many?** *Recommended:* **one zip per copy in `.nexus-copies/<review>/` inside the workspaces folder, the five newest per review**; the app deletes only its own older copies, after a new one is checked. *Not chosen:* inside the review's folder (it grows the review, is lost with it, and is tracked by git in the repository); a per-user application folder (survives the deletion of the reviews folder but is hard to find and not synced); keep every copy (grows without limit); a plain folder instead of a zip (no compression; long Windows paths). *Known cost:* deleting the workspaces folder deletes the copies; five copies of a large review take space (not measured).
4. **A review written by a newer version.** *Recommended:* **refuse to open it, with the message of Â§3.4**; it stays in the list with a badge. *Not chosen:* open it read-only (every screen would need a read-only state, and not every display route has been shown to write nothing); open it with a warning (the risk this work exists to stop). *Known cost:* after going back to an older version you cannot look at that review in it until you update again.
5. **What the Workspaces screen shows.** *Recommended:* **no format column; a badge only when a review is made by a newer version or its copy failed; the row's details name the last copy (date and folder); a one-time notice after a copy.** *Not chosen:* a format number on every row (means nothing to a researcher); nothing on screen (no one would know a copy exists to restore). *Known cost:* a field in the workspaces API and screen text in three languages.
6. **Ask before copying?** *Recommended:* **no question: copy, then say so** (on the first screen and in the command line). *Not chosen:* ask each time (a decision at every update, and "No" must leave the review unopened); a setting to turn copies off (easily left off and forgotten). *Known cost:* disk space used without asking, bounded by question 3.

---

## 8. Not verified

- **The researcher's real reviews** were not opened: their size, the size of their `pdfs/`, the zip's size and the time a copy takes are estimates. The figures in Â§1.6 are the repository's development workspaces.
- **The b6 comparison (Â§1.5)** is a reading of code. The `decisive_first` refusal and the `method_amendments.jsonl` file were opened by this session; the rest is a subagent's reading, some marked "not opened" by it (pilot, harvest marker, verification checks, PDF manifest, citation chase, query workbench, b6 `doctor`). No b6 build was run.
- **That today's code reads every older layout correctly** (the premise of step 0 to 1): `1.1.0b7` opens them today, but no test opens a b1 to b6 workspace of each kind.
- **Which command-line commands write**: the list in Â§3.2 is from the command names and help text; each must be confirmed in the build.
- **That every display route writes nothing**: not checked; it is why question 4 recommends refusing rather than a read-only view.
- **Concurrency**: no general lock exists between a command-line run, the MCP server and the browser app on one workspace (review, scout finding). The format lock covers two opens racing; a command writing while the copy is made could put a half-written file in the zip. Not handled beyond the lock.
- **Builds without this check** (`1.1.0b7` and earlier, and skill scripts vendored into a workspace before this build) will still open and write a newer workspace. Nothing can stop that from here.
- **The web app's handling** of the new refusal codes on screens other than Workspaces (where the app goes when a workspace route answers 409 with a new code) was not read.
- **Windows specifics**: a zip of a 90 MB `literature/` on a OneDrive-synced folder, file locks while syncing, and long paths in `audit/replaced/` were not tried.
