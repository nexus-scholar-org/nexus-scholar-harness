# H-workspace-format-version

Status: **IN A PULL REQUEST 2026-11-24, pushed on the researcher's word ("Yes, both"), with M13 Part A's branch merged in.** Independent review: round 1 CHANGES on `dce1abee` (12 findings, all repaired), round 2 APPROVE on `7605edd8`. Questions answered by the researcher on 2026-11-24 (§7): five as recommended, question 2 changed to "Everything including PDFs". Specification written 2026-11-23.

Source: the project review of 2026-11-23, finding 9 and recommendation 8 ("A format version on the workspace and a copy made before a newer build first opens it"; on local branch `dev/docs/project-review-2026-11-23`), and the researcher's answer to question 11 of `docs/roadmap/milestones/M13-installers.md` (build it as its own piece of work, before installers go to outside testers). The instruction to start, in the coordinator's brief: "Start Part A and the workspace format version". Part A of M13 (the launcher) is built in parallel by another session; this work needs no change to `console/launcher.py`, `console/code_window.py` or the start-up path of `nexus-scholar ui` (§3.2).

Written from the code at `cc0e8fa1`. The comparison with `v1.1.0b6` in §1.4 was made by reading the tag's code (`git show v1.1.0b6:…`), partly by a read-only subagent; its two strongest claims were opened again by this session (marked).

---

## 1. What the code does today

### 1.1 Where a workspace is created

| Door | Code | What it writes |
| :-- | :-- | :-- |
| `nexus-scholar init <title>` (with or without `--scaffold-only`) | `cli.py:142`; `inception/genesis.py:735` `scaffold_placeholder_workspace` | through `emit_workspace` (below), then the support files `genesis.py:590` (`.agents/skills/`, `.env.example`, `.mcp.json`, `.gitignore`) |
| The Workspaces screen, **New** | `console/api/workspaces.py:49` → `workspace/catalog.py:220` `create` → `scaffold_placeholder_workspace` | the same as `init --scaffold-only` (agent `nexus-scholar/ui`) |
| Inception genesis (wizard, browser inception, the bridge) | `inception/emit.py:315` `emit_workspace`, the one gated genesis path | a new folder: `scaffold_raw_project` (`genesis.py:252`, writes `project.json` at `:295` and the `PROJECT_INITIALIZED` row) or, in the monorepo layout, `scaffold_project` (`genesis.py:210`), which runs the workspace-manager script `.agents/skills/workspace-manager/scripts/init_project.py` as a subprocess; then `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md` (`genesis.py:192`), `protocol_origin` into `project.json` (`emit.py:289`), the `GENESIS` row. The file list shown at the write gate is `NEW_WORKSPACE_FILES` (`emit.py:86`), kept exact by a test |
| Protocol replacement (`--replace`) | `emit.py:377-404` | backs the protocol files up to `audit/replaced/<UTC stamp>/` (`emit.py:271`), **moves** the old corpus there (`ARCHIVED_ON_REPLACE`, `emit.py:49`: `literature/`, `pdfs/`, `extracted/`, `charting/`, …), rewrites `project.json` keeping its other fields (`emit.py:300`) |
| The placeholder workspaces | the same two placeholder doors above (`catalog.create`, `init --scaffold-only`) | a deterministic placeholder protocol (`genesis.py:680`) |

### 1.2 Where a workspace is opened

There is **no single open path**. Every door takes a folder and reads or writes it directly.

| Door | Code | Reads or writes |
| :-- | :-- | :-- |
| `nexus-scholar ui` start | `cli.py:1619-1661` | **opens the most recent workspace automatically** when `--workspace` is not given (`cli.py:1651`, `catalog.most_recent`, `catalog.py:139`). So the first start of a new build opens the researcher's latest review for writing with no click. |
| The launcher's restart (Open on the Workspaces screen) | `console/api/workspaces.py:63-81` → `catalog.check_open` (`catalog.py:257`) → `app.state.on_open` → `launcher.py:105` `request_open` → `launcher.py:119-137` builds a new app | the open route answers 202 and the restart happens after (`workspaces.py:80`) |
| `scholar-harness serve --workspace` | `cli.py:1557-1616` | |
| All three above build the server with | `console/serve.py:136` `create_app(workspace, …)` (`launcher.py:87-103` calls it) | the **one common point** of the browser app; `ws=None` means "no workspace open" (`serve.py:172-176`, `:274-275`, `_no_workspace` `:110`) |
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

- `format` is **one number for the whole workspace**: the newest layout its files follow. It goes up by one whenever a change would make an older build refuse, misread or overwrite something (the kinds of change in §1.5).
- `written_by` is the newest build that opened the workspace for writing (the installed package version). It is used by question 1 (a copy before each newer build) and by the newer-format message.
- Not a field in `project.json`, because `project.json` is rewritten by at least five writers, some outside the package (`workspace/manifest.py`, `orchestrator.sync_state`, `emit.py:289` and `:300`, the vendored `log_event.py`), each reading and writing it back; a race between two of them can drop a field, and then the next open would copy and stamp again. A file only one module writes avoids that, older builds never touch it, and its absence is unambiguous.
- `validity` (`catalog.py:50`) is unchanged: the file is not a marker, so every existing workspace stays valid.

**Who writes it, and when.**

1. **At birth**: every genesis door writes it with the current format and build (`scaffold_raw_project`, `genesis.py:252`; the workspace-manager script `init_project.py`, so the monorepo layout is stamped too). `NEW_WORKSPACE_FILES` (`emit.py:86`) gains it, so the write gate shows it. A protocol replacement keeps it (a root file, not in `ARCHIVED_ON_REPLACE`).
2. **At the first open for writing** by a build (§3): after the copy, by the migration steps.
3. **Never on a read.** The Workspaces list (`catalog.listing`, `describe`), `most_recent`, `status`, `doctor` and every display route read the file and never create or change it. The catalog's own rule ("It reads files only; it never holds a workspace open", `catalog.py:6`) stays true. Opening a workspace in the browser app counts as opening for writing, because the server may write on any request.

**A workspace without the file** (every existing workspace) is read as **format 0**: "written before format versions existed". It is opened like any older format (§3): copied, then stamped as 1 by the first migration step, which rewrites no file.

---

## 3. Opening a workspace

### 3.1 The one check, `prepare_for_writing(ws)`

One function in `workspace/format.py`, called by every door that may write (§3.2). It reads one small file, so it is cheap; after a success it is remembered for that folder for the life of the process.

1. Read `workspace_format.json`. Missing: format 0. Unreadable, not JSON, a `format` that is not a whole number, or a `schema` it does not know: refuse `WORKSPACE_FORMAT_UNREADABLE` (it never guesses).
2. `format` newer than this build's `CURRENT_FORMAT`: refuse `WORKSPACE_FORMAT_NEWER` (§3.4). Nothing is written.
3. Decide whether a copy is needed: the format is older, or (question 1, recommended) `written_by` is older than this build. Same format and same build: return at once; nothing is written.
4. Take the copy lock: an operating-system lock on `.nexus-copies/<slug>/.copy.lock` (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere), beside the copies and so outside the review. One holder at a time, so two windows opening one review make one copy; the lock ends with the process that holds it, so a crash or a closed window leaves nothing that blocks the next open (review finding 2). An open waits up to ten minutes for another running copy of the same review, then refuses.
5. Make the copy (§3.3). If it fails: delete the partial file, release the lock, refuse `WORKSPACE_COPY_FAILED`. The workspace has not been written.
6. For each step from the workspace's format up to `CURRENT_FORMAT` (§4): one journal row naming the step, the copy and what it changes, then the step, then `workspace_format.json` with the step's `format`. A crash between the row and the stamp re-runs the step on the next open (steps are idempotent) and makes a second copy; the normal path makes one.
7. Same format but an older `written_by`: one journal row `WORKSPACE_OPENED_BY_NEWER_BUILD` naming the copy, then `written_by` updated.
8. Remove this workspace's older copies beyond the number kept (question 3), only after the new one is verified, and only copies this mechanism made.

The journal rows use `append_event` with `refresh_index=False`. So the stamp changes exactly three things: the new or rewritten `workspace_format.json`, one or more appended journal lines, and `project.json`'s `updated_at` (the standard projection, `workspace/manifest.py`). Every other file is byte-identical.

### 3.2 Which doors call it

| Door | Where the call goes | Why there |
| :-- | :-- | :-- |
| The browser app at start (`ui`, `serve`) and after every restart | `create_app` (`serve.py:136`) | the one point all three paths share (§1.2); no edit to the launcher. The quick checks (newer format, unreadable file) run at once. When a copy is needed, `create_app` starts it on a background thread and the server starts serving; until the copy and the stamp are done, every workspace route answers 503 `WORKSPACE_PREPARING` with the progress, and `GET /api/v1/workspaces/preparation` (workspace-free) reports it, so the browser shows the "Saving a copy" panel (§3.3). Nothing in the app writes before that: the lifespan only stops jobs at shutdown (`discovery.py:182-187`) and the job runner's constructor writes nothing (`job_runner.py:95-101`). On a refusal (newer, unreadable, copy failed) every workspace route answers the refusal's code (409) and the Workspaces list shows it on the row. A shutdown during the copy (the launcher's restart onto another workspace) cancels it: the partial zip is removed and nothing is stamped. |
| Open on the Workspaces screen | `catalog.check_open` (`catalog.py:257`), before the 202 | the quick checks only: a newer or unreadable workspace is refused on the screen (409) while the current workspace stays open, and `on_open` is not called. The copy itself runs in the new server, with the panel, because a long copy must not hold the HTTP request. A failed copy then shows on the screen the app lands on, and the Workspaces row carries the badge. |
| The command line | each command that writes, checked one by one in the build: `setup-mcp` (not with `--dry-run`), `log event`, `log batch`, `log sync-index` (a slug is resolved first), `extract publish`, `supervise`, `sync`, `run`, `export`, `accept-corpus`, `chase run`, `chase accept`; `init` stamps at birth; `inception --replace` goes through `emit_workspace` (below); `serve` and `ui` through `create_app`. Not: `status`, `doctor`, `chase status`, `extract status`, and the `prompt-gate` commands, which only read the workspace and write their reports elsewhere (`pg.RESULTS_DIR`, `cli.py` `gate_run`) | `_open_for_writing` in `cli.py`, before the command's first write; a refusal prints the message and exits 1; an older workspace prints "Saving a copy of …" and then the zip's path |
| Inception genesis that replaces a protocol | `emit_workspace` (`inception/emit.py`), before the backup and the archive | the browser's genesis route, the wizard and `inception --replace` all reach it; a refusal becomes `GenesisRefused` with the same code |
| `agent_screen.py prepare|collect` | at the start | |
| The MCP server | each workspace-writing tool, through one helper next to `_screening_workspace` (`server.py:1430`) and the pipeline tool (`server.py:581`) | |
| **Backstop**: `append_event` and the legacy append (`workspace/audit.py`) | refuse `WORKSPACE_FORMAT_NEWER` before the append | every journalled write of the package, including a door the build forgets. It does not copy (a copy there would come after the operation's first writes). |
| The vendored `log_event.py` / `batch_log.py` | the same newer-format refusal, written inline (the script may not import the package) | a script copy vendored before this build has no check; that cannot be fixed from here (§8) |

Coordination with M13 Part A: none needed. If Part A adds its own start-up step before `Launcher(...)`, it may call `prepare_for_writing` there to print the refusal to the log file as well; `create_app` stays the guarantee.

### 3.3 The copy

- **What is copied** (question 2, answered "Everything including PDFs"): the whole review, **including `pdfs/` and `extracted/`**, so a copy restores by itself. Left out, each because a restore works without it:
  - `.env`: the key file; a copy never holds keys.
  - `.agents/`: the vendored skills, written again by `install_workspace_support_files` (`genesis.py:590`); nothing in the review points into it.
  - `.cache/`: caches.
  - `exports/`: files Export writes for the researcher; nothing registers them, and Export makes them again.
  - `chroma_db/`, `rag/`: indexes of the removed retrieval feature; no build from `1.1.0b7` on reads them.
  - The same five folders inside `audit/replaced/<stamp>/` (a replaced protocol's archived corpus).
  Kept on purpose, although they looked re-creatable in the specification: `extracted/` (a published document manifest names `extracted/<stem>.md` with its checksum, `extraction_producer.py:5`, `:48`, so a restore without it would break the registry), `.harness-console/` (it holds the researcher's saved pipelines, `cli.py:1339`), `.mcp.json` (small). Any other folder the researcher keeps in the review, such as `.git/`, is copied.
- **Form**: one zip file. PDFs and other already-compressed files (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.zip`, `.gz`, `.xlsx`, `.docx`) are **stored**, everything else is deflated. Written as `<name>.zip.partial`, then checked (every member's CRC by `ZipFile.testzip`, the member count and sizes against the list that was copied), then renamed. A zip keeps paths short (the Windows 260-character limit has already failed a gate, review section 3).
- **Measured** (2026-11-24, this PC, a synthetic workspace in the scratchpad: 300 PDF-sized files of random bytes, 417 MB, and 41.5 MB of JSON shaped like batches and `excluded.json`; files read from a warm cache):

  | Mode | Write | Check | Zip size |
  | :-- | --: | --: | --: |
  | everything deflated | 22.2 s | 1.1 s | 417.4 MB |
  | PDFs stored, the rest deflated (chosen) | 0.9 s | 0.3 s | 417.3 MB |
  | everything stored | 0.8 s | 0.3 s | 458.6 MB |

  Compressing PDFs gains nothing (their content is already compressed) and costs most of the time. The synthetic JSON is more repetitive than real records, so it compresses better than a real review's will; a cold disk is slower than these figures.
- **Where**: `<the workspace's parent folder>/.nexus-copies/<slug>/`, which for a listed workspace is the workspaces folder (question 3). The dot keeps it out of the Workspaces list (`catalog.py:168`). For a repository checkout, `workspaces/.nexus-copies/` is added to `.gitignore`.
- **Name**: `<UTC yyyymmddTHHMMSSZ>-format<from>-to<to>-<built by>-to-<this build>.zip` inside the review's own folder, for example `.nexus-copies/sensor-stress/20261130T100000Z-format0-to1-1.1.0b7-to-1.1.0b8.zip`. The file name does not repeat the review's name: with it, a review name over about 66 characters under the default Windows root passed the 260-character path limit and the review could not be opened (review finding 1). A `README.txt` beside the copies says what they are and how to restore one.
- **How many**: the five newest per workspace (question 3); older ones made by this mechanism are deleted after a new copy is verified. Nothing else in the folder is touched.
- **Restore** (in the user guide, by hand; a restore command is a later, separate item):
  1. Close Nexus Scholar.
  2. Rename the workspace folder aside (for example `sensor-stress-newer`).
  3. Unzip the copy into a new folder with the workspace's name.
  4. Copy your `.env` back if the review had one (the copy never holds keys).
  5. Open it with the older build (a newer one would copy and stamp it again).
  The restored review is the review as it was before the newer build opened it, PDFs included.
- **The copy is not a backup against the loss of the disk.** It sits beside the workspace in the same workspaces folder; deleting that folder deletes the copies. The guide says so.

**What the user sees.**

- **While the copy is made** (the researcher's answer to question 6: with PDFs in the copy, opening can take noticeably long, and the user must see that a copy is being made, and of which review, not a frozen screen). The browser app starts at once and makes the copy in the background (§3.2): every screen shows a full-page panel "Saving a copy of *{review title}* before opening it", with the megabytes done of the total and a short reason; when the copy is done the screen opens by itself. This holds on the start-up path (`ui` opening the most recent review with no click), after Open on the Workspaces screen, and with `serve`. The terminal prints the same line once.
- **After the copy**: once, on the first screen, a notice: "Before opening this review, Nexus Scholar saved a copy of it in `<folder>`. You do not need to do anything." The row on the Workspaces screen names the last copy (question 5).
- Command line: the same "Saving a copy…" line, then one line with the zip's path.
- Journal: the rows of §3.1 (so the review's own history records the copy).

**If the copy fails** (disk full, no permission, path too long, a file that cannot be read): the workspace is **not opened for writing**. Browser, `WORKSPACE_COPY_FAILED` (409):

> **This review was not opened.** Nexus Scholar saves a copy of a review before a newer version opens it, and the copy could not be saved: *{reason}*. Nothing in the review was changed. Free some disk space or check that the folder `{copies folder}` can be written, then try again.

There is no override in the app; a failed copy stays a refusal.

### 3.4 A workspace written by a newer build

Recommended (question 4): **refuse to open it**. Nothing is written; the Workspaces list still lists it (a read) with a badge; `status` still reads it; every writing door refuses; the journal backstop refuses. Browser, `WORKSPACE_FORMAT_NEWER` (409):

> **Made with a newer version of Nexus Scholar.** This review was last opened with Nexus Scholar {written_by}, which stores reviews in a way this version ({this build}) cannot read safely. To keep it intact, this version does not open it. Install Nexus Scholar {written_by} or later to continue.

Only builds with this work protect anything: `1.1.0b7` and earlier have no check and will open any workspace (§8).

---

## 4. Migrations

- **The registry**: `workspace/format.py` holds `CURRENT_FORMAT` and one step per number, `STEPS[n]` from `n` to `n + 1`, each with a name, a one-line description, and `apply(ws) -> list[str]` (the files it changed).
- **Rules for every step**: it is **idempotent** (applying it to its own output changes nothing); it is **journalled** (one row `WORKSPACE_FORMAT_MIGRATED` with `from`, `to`, `step`, the changed files and the copy); it writes only files that the copy contains, never `pdfs/`, `extracted/` or the other excluded folders (so the restore of §3.3 is complete); it never changes `protocol.json`, a Contract v1 artifact, a fingerprint or a published generation unless a contract decision says so (then the step is part of that decision).
- **The first step, 0 to 1, `stamp-today`**: rewrites no file. It records that the workspace follows the layout of `main` at `cc0e8fa1` (`1.1.0b7`). Journal row `WORKSPACE_FORMAT_STAMPED`. (A workspace written by b6 or earlier is read by today's code as it is; that is how `1.1.0b7` opens it today. Not tested for every older layout, §8.)
- **The rule for later work** (into `DEVELOPER_COMPASS.md` and `AGENTS.md`): a change that an older build would refuse, misread or overwrite (§1.5 is the catalogue of kinds) raises `CURRENT_FORMAT` by one and adds a step, even an empty one, with its test. The review of a milestone checks it.

---

## 5. What does not change

- **No Contract v1 file**, no schema, no golden fixture; `generate_contract_baseline.py --check` stays current (run at `cc0e8fa1`: "Contract baseline current").
- **No fingerprint or digest.** The protocol fingerprint is computed from `protocol.json` alone (`authority/generations.py:971` `_protocol_fingerprint`); the registered workspace id is read from `project.json` (`generations.py:959`), whose content changes only in `updated_at`; a publication binds the batch files, the published outputs, the approval and the protocol (`screening/currentness.py:1-9`), none of which the stamp touches. A search for a digest over `audit/journal.jsonl`, `project.json` or `INDEX.md` found none. So the stamp changes no fingerprint, no corpus snapshot and no generation's currentness.
- **What the stamp would change that a user can see, and does not**: a format row is not the researcher's activity, so the Workspaces list's last activity and `most_recent` (the review `ui` opens next) skip the rows `WORKSPACE_FORMAT_STAMPED`, `WORKSPACE_FORMAT_MIGRATED` and `WORKSPACE_OPENED_BY_NEWER_BUILD` (`catalog._last_event`; review finding 5). The copy itself shows on the row as "Copy saved before an update".
- No published generation is re-made; no decision, batch or export is rewritten.

---

## 6. Definition of done

Lane **RELEASE**. Each test below fails on `cc0e8fa1` (there is no `workspace/format.py`, no copy and no refusal today).

1. **Unstamped workspace, first open for writing.** A fixture workspace with no `workspace_format.json` (a genesis output with the file removed, and a second fixture whose layout was written by `v1.1.0b6`, see 13). `create_app(ws)`: one zip in `.nexus-copies/<slug>/`; `workspace_format.json` says `format: 1` and this build; the journal is the old journal plus the new rows; `project.json` differs only in `updated_at`; **every other file is byte-identical** (SHA-256 of every file before and after).
2. **Second open makes no second copy**: a second `create_app` and a `check_open`: no new zip, no new row, no byte changed.
3. **Failed copy**: the copies folder unwritable, and separately the zip writer made to raise `OSError` midway: `WORKSPACE_COPY_FAILED`; no `.partial` left; the workspace byte-identical; `create_app` answers 409 with that code on a workspace route (a GET and a POST); the list's `preparation` says refused. `POST /workspaces/open` answers 409 and does not call `on_open` for a newer or unreadable workspace (the copy itself runs in the new server, §3.2).
4. **Newer format** (`format: 2`): `create_app` routes answer `WORKSPACE_FORMAT_NEWER`; `append_event` raises before appending; each command-line write door in the list of §3.2 exits non-zero with the message (table-driven); the MCP writing helper refuses; the workspace is byte-identical after all of them. The Workspaces list still lists it, with the badge.
5. **What the copy holds**: a workspace with `pdfs/`, `extracted/`, `.harness-console/`, `.cache/`, `.env`, `exports/`, `.agents/`, `rag/`, `chroma_db/` and `audit/replaced/<stamp>/.cache/`: `.env`, `.agents/`, `.cache/`, `exports/`, `rag/`, `chroma_db/` (also under `audit/replaced/`) are not in the zip; every other file is, PDFs stored and text deflated. **Restore**: unzip into a new folder: every file of the workspace before the open, except the left-out ones, is byte-identical; `validity` is true; the screening summary route answers the same counts as before the open.
5b. **The copy is visible**: while the background copy runs, a workspace route answers 503 `WORKSPACE_PREPARING` and the preparation route reports the review's title and progress; on the `ui` start-up path (the launcher building the app for the most recent workspace, no click) the same, tested through `Launcher` with a fake server. The web app shows the panel (component test) and opens the screen when the copy is done.
6. **Reads never write**: `listing`, `describe`, `most_recent`, `status` and a display route on an unstamped workspace: no copy, no stamp, no byte changed; the list reports the format as not yet recorded. The last-activity column after a stamp shows the decided wording.
7. **Birth**: `catalog.create`, `init --scaffold-only` and `emit_workspace` (both layouts, including the `init_project.py` script) write `workspace_format.json` with the current format; their first open makes no copy; `NEW_WORKSPACE_FILES` names the file and its test passes.
8. **Registry**: every `n < CURRENT_FORMAT` has a step to `n + 1`; each step applied twice equals once; step 0 to 1 changes no file.
9. **Crash mid-way**: an exception after the copy and before the stamp: the next open completes; nothing outside the format file and the journal changed.
10. **Newer build, same format** (if question 1 is answered as recommended): an older `written_by`: a copy and `WORKSPACE_OPENED_BY_NEWER_BUILD`; the same build: nothing.
11. **Pruning**: six opens by six builds keep the five newest copies; a file in `.nexus-copies/<slug>/` not made by this mechanism is never deleted.
12. **Unreadable format file**: `WORKSPACE_FORMAT_UNREADABLE`, nothing written.
13. **The real older layout**: a workspace made by the `v1.1.0b6` tag's code (`git worktree add <temp> v1.1.0b6`, then `uv run --project <temp> nexus-scholar init "Old layout" --scaffold-only --dir <temp root>/old-layout`, plus a small screened corpus if the b6 code can make one offline from the golden cassette), opened by the new build through `nexus-scholar ui --root <temp root> --no-browser` on a free port (never 8792): copy, stamp, the app's screens answer. Recorded in the evidence with the commands.
- The checks of `AGENTS.md`: both ruff runs, `generate_contract_baseline.py --check`, the selector's `pr` gate for the touched areas, `select_test_gate.py --check`; `uv build --wheel` and both entry points' `--help` on a base install.
- The user guide: a section "The copy made before an update" with the restore steps of §3.3; `DEVELOPER_COMPASS.md` and `AGENTS.md`: the rule of §4; `.gitignore`: `workspaces/.nexus-copies/`.
- The web app: the notice, the row's copy line and the two refusals, in English, French and Arabic, with their component tests.
- Independent review (`milestone-reviewer`) APPROVE; the record's evidence table; a decisions entry with "for the researcher to decide" kept apart from "choices made in the build".

---

## 7. Questions closed (2026-11-24)

The researcher answered in the coordinator session on 2026-11-24, one by one (relayed by the coordinator).

1. **When a copy is made.** *Answer (as recommended):* when the format is older, and also the first time a build newer than the one that last wrote the workspace opens it for writing. *Not chosen:* only on a format change; at every open.
2. **What is copied.** *Answer (changed):* **"Everything including PDFs".** The copy restores by itself; left out are only `.env`, `.agents/`, `.cache/`, `exports/`, `chroma_db/` and `rag/` (§3.3 gives why each, and why `extracted/` and `.harness-console/` are kept). *Not chosen:* the recommendation without PDFs; only the authoritative files. *Known cost:* with answers 1 and 3, **a review with a large `pdfs/` folder is copied in full after every update, and up to five full copies are kept**: up to five times the review's size on disk beside it (the researcher's current review holds 107 PDFs; its size was not measured). The first open after an update waits for the copy: on this PC about one second per 400 MB from a warm cache (§3.3), slower from a cold disk.
3. **Where and how many.** *Answer (as recommended):* one zip per copy in `.nexus-copies/<review>/` inside the workspaces folder, the five newest kept. *Not chosen:* inside the review; a per-user application folder; keep every copy; a plain folder. *Known cost:* deleting the workspaces folder deletes the copies.
4. **A newer-format review.** *Answer (as recommended):* refused with a plain message; the list still shows it with a badge. *Not chosen:* read-only; open with a warning. *Known cost:* an older version cannot look at it until updated.
5. **The Workspaces screen.** *Answer (as recommended):* no format column; a badge only for "made by a newer version" or "copy failed"; the row's details name the last copy; a one-time notice after a copy. *Not chosen:* a format number on every row; nothing on screen.
6. **Asking first.** *Answer (as recommended):* copy, then tell; and, because PDFs make the copy longer, **the user sees that a copy is being made, and of which review, while it runs** (§3.3, "While the copy is made"). *Not chosen:* ask each time; a setting to turn copies off. *Known cost:* disk space used without asking, bounded by answer 3.

## 7a. The questions as they were put (2026-11-23)

1. **When is a copy made?** *Recommended:* **when the workspace's format is older than the build's, and also when the build is newer than the one that last wrote it** (your words in M13 question 11: "a copy made before a newer build first opens it"). *Not chosen:* only when the format number changes (fewer copies, but it relies on every developer raising the number; in the thirteen days after b6 at least five changes needed it, §1.5); a copy at every open (many identical copies). *Known cost:* one copy per review per release, made at its first open (about 90 MB of `literature/` in a 14,000-record review before compression; the zip's size and time are not measured).
2. **What is copied?** *Recommended:* **everything except the PDFs, the extracted text, caches, exports, the vendored skills and the key file** (`pdfs/`, `extracted/`, `.cache/`, `chroma_db/`, `rag/`, `exports/`, `.agents/`, `.harness-console/`, `.env`, and those folders inside `audit/replaced/`). *Not chosen:* everything including PDFs (hundreds of megabytes per release and a slow first open); only the authoritative files (protocol, `audit/`, `literature/`), which misses `charting/` and the review notes. *Known cost:* PDFs you attached by hand are not in the copy; a restore takes the current `pdfs/` folder (no migration writes it), and if the workspace folder itself is lost, the copy does not bring the PDFs back.
3. **Where are copies kept, and how many?** *Recommended:* **one zip per copy in `.nexus-copies/<review>/` inside the workspaces folder, the five newest per review**; the app deletes only its own older copies, after a new one is checked. *Not chosen:* inside the review's folder (it grows the review, is lost with it, and is tracked by git in the repository); a per-user application folder (survives the deletion of the reviews folder but is hard to find and not synced); keep every copy (grows without limit); a plain folder instead of a zip (no compression; long Windows paths). *Known cost:* deleting the workspaces folder deletes the copies; five copies of a large review take space (not measured).
4. **A review written by a newer version.** *Recommended:* **refuse to open it, with the message of §3.4**; it stays in the list with a badge. *Not chosen:* open it read-only (every screen would need a read-only state, and not every display route has been shown to write nothing); open it with a warning (the risk this work exists to stop). *Known cost:* after going back to an older version you cannot look at that review in it until you update again.
5. **What the Workspaces screen shows.** *Recommended:* **no format column; a badge only when a review is made by a newer version or its copy failed; the row's details name the last copy (date and folder); a one-time notice after a copy.** *Not chosen:* a format number on every row (means nothing to a researcher); nothing on screen (no one would know a copy exists to restore). *Known cost:* a field in the workspaces API and screen text in three languages.
6. **Ask before copying?** *Recommended:* **no question: copy, then say so** (on the first screen and in the command line). *Not chosen:* ask each time (a decision at every update, and "No" must leave the review unopened); a setting to turn copies off (easily left off and forgotten). *Known cost:* disk space used without asking, bounded by question 3.

---

## 8. What was built (2026-11-24)

Branch `dev/h/workspace-format-version`; `origin/main` `0bcefdd3` (PR 308, H-remove-graph) merged in at `0df8161b`. Commits after the specification: `3c2ac370` (engine), `19c97793` (web app, codes, guides), `f9b9577e` (notices on standard error; `agent_screen.py review` reads only), `a669d91a` (`workspace/meta` answers during the copy).

- **Engine.** `src/scholar_harness/workspace/format.py` (new): the format file, `plan`, `prepare_for_writing`, the verified zip (`make_copy`), pruning, `last_copy`, the step registry (`STEPS`, step 0 to 1 `stamp-today`), version comparison, and `OpenGate` (the browser app's gate: foreground up to 64 MB, background above, progress, cancel on shutdown).
- **Doors.** `console/serve.py` `create_app` (the gate; `_format_blocked` in the middleware; a lifespan that cancels a running copy); `workspace/catalog.py` (`check_open` quick checks; each row's `format` and `last_copy`, reads only); `console/api/workspaces.py` (`GET /api/v1/workspaces/preparation`, `preparation` in the list); `cli.py` (`_open_for_writing` in eleven writing commands, notices on standard error); `agent_screen.py` (every subcommand but `status` and `review`); `scholar_agent/server.py` (the journalled tools, `nexus_screen`'s proposals, `nexus_pipeline_run`, `nexus_submit_proposal`, the assistant's two writing tools); `inception/emit.py` (a replacement); `workspace/audit.py` (newer-format backstop in both journal writers); the workspace-manager `init_project.py` and `log_event.py` (canonical and bundle copies).
- **Birth.** `genesis.scaffold_raw_project` and `init_project.py` stamp; `NEW_WORKSPACE_FILES` names `workspace_format.json`.
- **Web app.** `components/workspace-preparation.tsx` (new, inside the shell's `main`): the "Saving a copy of {title} before opening it" panel with a progress bar, the one-time notice, the refusal card; `lib/copy-notice.ts`; the Workspaces rows' badges ("Made with a newer version", "Copy failed") and last-copy line; four state cards in English, French and Arabic.
- **Codes.** `WORKSPACE_FORMAT_NEWER`, `WORKSPACE_FORMAT_UNREADABLE`, `WORKSPACE_COPY_FAILED`, `WORKSPACE_PREPARING` in `console/refusals.py`, `screening-api-contract.md` §7 and `workspaces-api.md` §5 (console codes, not Contract v1).
- **Docs.** User guide ("The copy made before an update", restore steps); `DEVELOPER_COMPASS.md` (the rule for raising the format); `AGENTS.md`; `.gitignore` (`workspaces/.nexus-copies/`).
- **Tests.** `tests/unit/test_workspace_format.py` (33 tests, each item of §6); `apps/research-ui/tests/workspace-preparation.test.tsx` (6) and one more in `workspaces.test.tsx`; three shared fixtures that model today's layout now call `stamp_new` (`tests/test_screening_events.py`, `tests/console/test_console_serve.py`, `tests/console/test_corpus_import_api.py`); `next-step-bar.test.tsx` counts the bar's own reads only.

## 9. Evidence

| Check | Commit | Result |
| :-- | :-- | :-- |
| `generate_contract_baseline.py --check` | `0df8161b`, `a669d91a` | current |
| `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | `0df8161b`, `a669d91a` | pass |
| `select_test_gate.py --check`; `sync_skills_bundle.py --check`; `git diff --check` | `0df8161b`, `a669d91a` | pass |
| Selector `pr` gate, areas screening, console, inception, workspace-audit, harness-cli, agent-mcp, research-ui: web app `typecheck`, `lint:ui` (76), `npm test` (118 files, 1,354 tests) | `0df8161b` | pass |
| The same gate: full Python suite, `-n 4` through `suite_lock.py` | `0df8161b` | 3 failures, all caused by this work and repaired in `f9b9577e`: `test_review_is_read_only` (`agent_screen.py review` opened for writing) and two `extract publish --json` tests (a notice on standard output) |
| The full gate again: every check above, the web app (118 files, 1,354 tests) and the full Python suite (`-n 4`, `suite_lock.py`, exit 0) | `a669d91a` | pass |
| `tests/unit/test_workspace_format.py` | `a669d91a` | 33 pass |
| Review round 1 repairs: the full gate again (every check above; web app 118 files, 1,356 tests; full Python suite `-n 4` through `suite_lock.py`) | `7605edd8` | all pass except one test: `test_a_long_review_name_keeps_the_copy_path_short`, whose own 89-character folder under pytest's parallel temporary folder (`popen-gw3`) passed 260 characters; the test's name was shortened to 71 characters (still above the 66 the review found) in the next commit, and the file then passed under `-n 4` |
| Independent review round 2 (`milestone-reviewer`) | `7605edd8` | APPROVE; ran 60 Python tests, four API and launcher files, 54 web app tests |
| `uv build --wheel`; fresh Python 3.12 base install; `nexus-scholar --help`, `scholar-agent --help`; `init --scaffold-only` from the wheel writes `workspace_format.json` (format 1) | `a669d91a` | pass; wheel 4.25 MB; `format.py`, the UI bundle and the bundled `log_event.py` with its check are in it |

**Verification with a workspace written by `v1.1.0b6`** (2026-11-24, scratch folders, port 8771; the researcher's workspaces were not touched):

1. `git worktree add --detach <scratch>/b6 v1.1.0b6`; in it `uv sync`; `uv run nexus-scholar --version` gave `1.1.0b6`.
2. With that b6 code: `nexus-scholar init "Old layout review" --scaffold-only --dir <scratch>/b6root/old-layout-review`; `nexus-scholar accept-corpus --workspace … --ris Scopus=<5 records>.ris` (5 studies accepted); `python src/scholar_harness/agent_screen.py prepare …` (`batch_001.json`). Then 300 PDF-sized files (417 MB) copied into `pdfs/`, and the SHA-256 of all 358 files recorded. No `workspace_format.json`.
3. This build: `uv run nexus-scholar ui --no-browser --port 8771 --root <scratch>/b6root` (no `--workspace`). The terminal printed "Saving a copy of Old layout review before this version of Nexus Scholar opens it (417 MB)…" before the server line, then "Saved a copy …": the start-up path opened the most recent review and copied it with no click.
4. In the browser: the screening home showed the one-time notice naming `<root>\.nexus-copies\old-layout-review` and read the b6 corpus correctly ("5 records from Scopus", batch 1, nothing decided). The Workspaces row showed "Copy saved before an update" with its date.
5. On disk: only `workspace_format.json` (format 1), `audit/journal.jsonl` (one `WORKSPACE_FORMAT_STAMPED` row naming the copy) and `project.json` (`updated_at`) differed from b6's files. The zip: 417.1 MB, 319 members, the 300 PDFs stored; it unzipped in 0.6 s to files byte-identical to b6's, less `.agents/` (left out by design).
6. The panel: a second b6 workspace with 40,000 small text files (109 MB) was the most recent at the next start; the screening home showed "Saving a copy of Third old review before opening it", "30 of 109 MB", then "60 of 109 MB", and opened by itself with the notice when the copy was done (screenshot `h-workspace-format-version-copy-panel.jpg` in the coordinator's notes folder).
7. Open on the Workspaces screen did **not** restart the server in the app's browser pane, for a review that needed a copy, for one already stamped, and also on `cc0e8fa1` (main before this branch, same UI export): a **pre-existing** fault in this environment, not caused by this work. The same restart driven by a script against the real uvicorn server restarts and copies correctly (stamped and unstamped target). See §10.

### Independent review, round 1 (`dce1abee`): CHANGES

`milestone-reviewer` found one P1, four P2 and seven P3; each was repaired, with a test, in the commit after `dce1abee`:

1. P1, a long review name made the copy path pass 260 characters on Windows and the review could not be opened (reproduced with a 52-character slug in a deep folder): the file name no longer repeats the review's name.
2. P2, a lock left by a killed process blocked the review for up to six hours: an operating-system lock now, released when its process ends.
3. P2, no retry inside the app after a failed copy: Open on the current review restarts on it (`workspaces.py`), and the card's "Try again" does that; decisions item 10 corrected (the app starts with the review bound but refused, not with none open).
4. P2, `create_app` copied and stamped a folder that is not a workspace (`serve` defaults to `.`): the gate runs only where a workspace marker exists.
5. P2, the last activity showed the raw stamp row and `most_recent` ranked by it: format rows are skipped.
6. P3, `sync --dry-run` copied and stamped: skipped on a dry run.
7. P3, a cancel during the zip's check could still stamp: checked again before the rename and before the journal.
8. P3, the cancel test bypassed the lifespan: it now leaves a `TestClient` block.
9. P3, one failed progress read froze the panel, and the next-step bar was not refreshed: reads retry with back-off; the page's remount sends the review-changed event.
10. P3, the whole panel was a live region re-announced every second: one status line, announced once.
11. P3, doors not named: the kit command lines that write into a workspace through a path (`scholar-pdf` acquire and extract-run with `workspace_root`, `scholar-search` output paths) have no check; named in §10.
12. P3, `prune` could fail on a copy removed meanwhile: it skips it.

Also from the review: Open on an unreadable review and `log batch` are now tested; the refusal card's link keeps `?console=`.

Round 2 (`7605edd8`): **APPROVE**, no new findings. Its two follow-ups, not built: a line in `.nexus-copies/README.txt` about the `.copy.lock` file that now stays there; a test with a real second process holding the lock (for the `fcntl` path, which only CI runs).

## 10. Not verified

- **The researcher's real reviews** were not opened: their size, the size of their `pdfs/`, the zip's size and the time a copy takes are estimates. The figures in §1.6 are the repository's development workspaces.
- **The b6 comparison (§1.5)** is a reading of code. The `decisive_first` refusal and the `method_amendments.jsonl` file were opened by this session; the rest is a subagent's reading, some marked "not opened" by it (pilot, harvest marker, verification checks, PDF manifest, citation chase, query workbench, b6 `doctor`). No b6 build was run.
- **That today's code reads every older layout correctly** (the premise of step 0 to 1): `1.1.0b7` opens them today, but no test opens a b1 to b6 workspace of each kind.
- **Which command-line commands write**: confirmed by reading each command's body in the build (§3.2), not by tracing every function they call.
- **That every display route writes nothing**: not checked; it is why question 4 recommends refusing rather than a read-only view.
- **Concurrency**: no general lock exists between a command-line run, the MCP server and the browser app on one workspace (review, scout finding). The format lock covers two opens racing; a command writing while the copy is made could put a half-written file in the zip. Not handled beyond the lock.
- **Builds without this check** (`1.1.0b7` and earlier, and skill scripts vendored into a workspace before this build) will still open and write a newer workspace. Nothing can stop that from here.
- **Screens' own handling of the new codes**: the shell replaces every page but Workspaces while a copy runs or after a refusal, so pages do not see the codes in normal use; a page that is already open when a workspace becomes refused (not possible today: the gate decides at start) was not tried.
- **Windows specifics**: a zip of a 90 MB `literature/` on a OneDrive-synced folder, file locks while syncing, and long paths in `audit/replaced/` were not tried.
- **Open from the Workspaces screen in the app's browser pane**: the server does not restart, on this branch and on `cc0e8fa1` alike (§9 item 7); whether the same happens in an ordinary browser was not tried. It may be the "workspace-open hang" noted before release `1.1.0b7`.
- **`written_by` reads `1.1.0b7`** on this branch, the version in `pyproject.toml`: a workspace opened by this build and later by the released `1.1.0b8` gets one more copy then (answer 1).
- **The copy's time on a real review and on a cold disk**: measured on synthetic files from a warm cache only (§3.3).
- **macOS and Linux**: the tests ran on Windows; CI runs them on Ubuntu (the `fcntl` lock path runs only there).
- **The kit command lines** (`scholar-pdf acquire` / `extract-run` with `workspace_root`, `scholar-search` with an output path inside a workspace) write without the check (review finding 11); the harness commands, the app and the MCP server's writing tools are covered.
- **A future change of the format file's `schema` string** would make this build report the file as damaged rather than newer: the string stays `nexus.workspace-format.v1` and only `format` rises (compass rule).
- **Windows path length**: the copy path is now the review's path plus about 100 characters; a review folder already within about 100 characters of the limit can still fail to copy (the message names the possible cause).
