# 09 Start from an existing review    Status: FINAL, not built (questions closed by the researcher 2026-11-15) | Phase 0 Inception | Route `/[locale]/inception/import` (desktop only; reached from the start screen 08) | Milestone M10b (import, no language model)

Boards: none. The canvas has no import flow; this screen is new and composes the start screen (08), the step header and the `StateCard` of 01 and 08. Contract: `docs/architecture/inception-api.md` (Draft, Routes). Code read for this spec: `src/scholar_harness/inception/steps.py` (`Draft` `:149`, `parse_draft` `:197`, `_survey` `:226`, `criteria_with_decisions` `:285`, `build_intent` `:335`, `preview` `:361`, `genesis` `:433`), `inception/drafts.py` (`DraftStore` `:45`, `create` `:65`, `save` `:81`, `listing` `:118`), `inception/intent.py` (`CRITERION_SOURCES` `:243`, `draft_criteria` `:287`, `make_intent` `:304`), `inception/genesis.py` (`compile_intent` `:143`, `_default_matrix_dimensions` `:373`), `inception/emit.py` (`emit_workspace` `:285`), `console/api/inception.py`, `console/browser.py` (`POST_PATHS` `:40`), `console/refusals.py:80-109`, `workspace/catalog.py` (`listing` `:178`, `_target` `:207`), `scholar_protocol/models.py` (`ResearchProtocol` `:376`) and `scholar_protocol/intent.py` (`IntentPacket` `:126`), `scholar_protocol/presets.py`, `workspaces/uav-crop-weed-v03/{protocol,intent}.json`. Shared draft rules: `01-scope.md` "Shared by 01, 04, 05, 06 and 07". The proposal object (`docs/ux/shared/final/01-proposals.md`) is being drafted by another writer and is read here only for the alternative in "How imported values arrive".

**Purpose.** Begin a new review from a protocol the researcher already has (a workspace's, or a file), so its questions, criteria and concepts arrive as the researcher's own earlier text instead of being typed again, with a plain list of what could not come across.

**Why.** On 2026-11-13 the researcher had a finished protocol (`workspaces/uav-crop-weed-v03/protocol.json`: title, review type, four research questions, three inclusion and four exclusion criteria with reason categories such as `WRONG_PLATFORM`, thirteen matrix dimensions) and retyped all of it into the inception steps.

**Changed from the canvas.** The canvas has no such flow. What this spec adds and what it leaves out:
- **A second way to begin, beside "Start a new review" (08).** Not a mode of the six steps. The six steps and the stepper are unchanged; the draft they open is simply already filled in.
- **No pasted text.** A PROSPERO record or a draft protocol document needs reading and interpreting; that is the assistant of M10c. The screen says so (see Copy `import.text.*`) and offers no text box. Nothing here calls a language model.
- **No new draft fields except the one other specs add.** `Draft` is `extra="forbid"` (`steps.py:152`). This spec adds none. Matrix dimensions need the "researcher's own columns" field that M10b adds to `05-criteria`; until it exists they are listed as not carried (see the mapping table).
- **No edit of the source review.** Reading only. Not a journal event, not an `updated_at`, not a lock in the source.
- **Phone.** Not built. Inception routes are not phone routes (`01-scope.md`, Mobile layout).

## Entry / exit
- Entry: a secondary button "Start from an existing review" on the start screen 08, beside the brand button "Start a new review" (an addendum to 08, listed under "Screens touched at build"); a direct URL.
- Exit: "Create the draft from this review" (brand button, only in the report state) creates the draft and goes to Scope (01) of the new draft, with `?draft=` and `?console=` as on every inception link. "Back to your drafts" goes to 08. Nothing is created before that click.
- Gate: none that writes a workspace. The only write is one small draft file under `<workspaces root>/.drafts/<id>/draft.json`, as on 08. The brand button is disabled until a source has been read and the report shown.

## Data in
| Field | Source |
| :-- | :-- |
| the workspaces under the root a researcher can start from: `items[{slug, title, valid, status, last_event}]` (valid ones only; a valid workspace has `protocol.json`, `project.json` and `audit/journal.jsonl`, `catalog.MARKERS` `:26`) | `GET /api/v1/workspaces` ✓ `console/api/workspaces.py:33` (workspace-free, as the inception routes) |
| the report for the chosen source: `source{kind, label, slug?, file_name?, read, protocol_id, protocol_created_at, protocol_fingerprint, schema, target_slug, collides_with_source}`, `draft`, `carried[]`, `lost[]`, `needs_you[]` | `POST /api/v1/inception/drafts/import` with `dry_run: true` ✗ M10b |
| a picked file: its bytes, read in the browser (`FileReader`) and sent base64, as the corpus import does (`CorpusSourceBody.content_base64`, `screening_v1.py:556`) | the researcher's file; no path reaches the engine |

`read` is `protocol` or `intent`: which shape the source was. A workspace is always read as `protocol.json`; `intent.json` is read only when the researcher picks that file (it holds the same answers before compilation, with no ids and no `$schema`).

## Data out
- **Create the draft:** `POST /api/v1/inception/drafts/import` ✗ M10b with `dry_run: false` and `expect_fingerprint` (the one the report showed). Answers `201` with the draft record (`session_id`, `created_at`, `updated_at`, `draft`, `emitted: null`) plus `origin` and `report`. The engine stores `origin` beside `draft` in the same `draft.json` (the record is a plain dict and `save` rewrites it whole, so an extra key survives: `drafts.py:81-93`; `bind_grounding` already stores `grounding` this way, `:95`). No journal event: a draft is not a workspace (08).
- **Mark a step as visited:** `POST /api/v1/inception/drafts/{id}/origin/checked` ✗ M10b, `{step}`. Does not change `updated_at`, so another tab's `base_updated_at` stays valid (marks are not draft content).
- **At genesis (06):** the GENESIS event names the source ("started from {label}, protocol {fingerprint}, imported {date}"). `emit_workspace` already takes a `description` (`emit.py:294`, used at `:310`); the web genesis does not pass one (`steps.py:495-498`). ✗ M10b: pass it when the draft has an `origin`. This is how the methods text can say the review began from an earlier protocol.
- Writes nothing to the source, ever.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/workspaces` (the picker) | ✓ `console/api/workspaces.py:33`, `workspace/catalog.py:178` |
| `POST /api/v1/inception/drafts/import` (`dry_run` true: report; false: create) | ✗ M10b |
| `POST /api/v1/inception/drafts/{id}/origin/checked` | ✗ M10b |
| `POST /api/v1/inception/drafts` (not used by this flow; the import creates the draft itself so `origin` is stored with it) | ✓ M4a `console/api/inception.py:90` |
| browser allowlist: `api/v1/inception/drafts/import` and `api/v1/inception/drafts/[A-Za-z0-9_-]+/origin/checked` added to `POST_PATHS` (`browser.py:40-61`) and the proxy's list (`app/api/console/[...path]/route.ts`) | ✗ M10b (without it the browser answers `CONSOLE_PATH_REFUSED`) |
| `drafts.listing()` adds `origin.label` so 08 can say "Started from {label}" | ✗ M10b |
| genesis passes the source to the GENESIS event | ✗ M10b |

None is in `_PHONE_ROUTES` (`serve.py:55`). The POSTs sit under the loopback origin check, `HOST_REFUSED` and `TOKEN_REQUIRED` as the other inception writes. `/drafts/import` cannot be confused with a draft id: no POST exists on `/drafts/{id}`, and a GET or PUT on `import` answers `DRAFT_ID_INVALID` (it does not match `rec_<hex>`, `drafts.py:25`).

### `POST /api/v1/inception/drafts/import` (✗ M10b)
Request (`extra="forbid"`):
```
{ "source": { "kind": "workspace", "slug": "uav-crop-weed-v03" }
         | { "kind": "file", "file_name": "protocol.json", "content_base64": "<base64>" },
  "dry_run": true,
  "expect_fingerprint": null }
```
- `workspace`: the slug goes through `catalog._target(root, slug)` (`catalog.py:207`), so a name that leaves the workspaces folder is `WORKSPACE_PATH_REFUSED` (422), as elsewhere. The engine reads `<root>/<slug>/protocol.json`.
- `file`: at most **1 MiB** of decoded bytes (new limit; a real protocol is about 22 KB, the UAV one included). Mirrors the 50 MB RIS limit of the corpus import (`corpus_accept.py:62`) in kind, not in size.
- `expect_fingerprint`: only on the creating call; the fingerprint the report showed.

`200` (dry run; stores nothing):
```
{ "source": { "kind": "workspace", "label": "uav-crop-weed-v03", "slug": "uav-crop-weed-v03",
              "read": "protocol", "schema": "schemas/v1/protocol.schema.json",
              "protocol_id": "proto-20261012-uav-crop-weed-reliability",
              "protocol_created_at": "2026-10-12T14:12:24.953835+00:00",
              "protocol_fingerprint": "<sha256, null for an intent file>",
              "target_slug": "reliability-and-generalization-in-uav-crop-weed-mapping-a-scoping-review",
              "collides_with_source": false },
  "draft": { ...a Draft, already through parse_draft... },
  "carried": [ { "field": "rqs", "from": "research_questions[].text", "class": "exact" },
               { "field": "rqs", "from": "research_questions[].target_facet, synthesis_type, required_evidence_type",
                 "class": "lossy", "note": "replaced by the lens's values and \"Comparative Matrix\"" }, ... ],
  "lost":    [ { "what": "matrix_dimensions", "count": 13, "why": "..." }, ... ],
  "needs_you": ["topic"] }
```
`201` (creating): `{session_id, created_at, updated_at, draft, emitted: null, origin, report: {carried, lost, needs_you}}`. `origin` is `{kind: "import", source, imported_at, checked: {scope, direction, shape, criteria, review}, report}`, with each `checked` value `false` at creation.

The engine builds `draft` by the mapping table below and passes it through `steps.parse_draft`, so the draft limits and the draft shape apply to an import exactly as to a typed draft. `protocol_fingerprint` is computed with the same `canonical_fingerprint` the compiler uses (`genesis.py:152, :177`); I did not read how screening derives the fingerprint it binds for a hand-edited file, so the build must reuse that helper and a test must pin that the two agree.

Refusals (code, HTTP; all in the style of `_error`, `inception.py:41`, `{code, message, details?}`):
| Code | HTTP | When | `details` |
| :-- | :-- | :-- | :-- |
| `IMPORT_SOURCE_NOT_FOUND` ✗ | 404 | the workspace folder or its `protocol.json` does not exist | `{slug}` |
| `IMPORT_SOURCE_UNREADABLE` ✗ | 422 | the bytes cannot be read: not base64, not UTF-8, not JSON, not a JSON object, or the folder cannot be read | `{reason}` |
| `IMPORT_SOURCE_TOO_LARGE` ✗ | 413 | a file over 1 MiB decoded | `{max_bytes, got_bytes}` |
| `IMPORT_NOT_A_PROTOCOL` ✗ | 422 | a JSON object that is neither a protocol (no `epistemology`, `search_strategy` and `screening_criteria`) nor an intent (no `inclusion_criteria` and `research_questions`) | `{missing: [keys]}` |
| `IMPORT_PROTOCOL_VERSION_UNSUPPORTED` ✗ | 422 | `$schema` is present and is not `schemas/v1/protocol.schema.json` (the only value `ResearchProtocol` writes, `models.py:391-395`; an absent `$schema` is accepted because the model defaults it, and an intent has none) | `{found, supported: ["schemas/v1/protocol.schema.json"]}` |
| `PROTOCOL_INVALID` ✓ `refusals.py:80` | 422 | the shape is right but `ResearchProtocol` or `IntentPacket` validation fails | `{shape: "protocol" or "intent", errors}` (the validator's errors without echoing values) |
| `DRAFT_TOO_LARGE` ✓ `refusals.py:103` | 422 | a mapped value is over a draft limit (`DRAFT_LIMITS`, `steps.py:103`: free text 2 000 characters, names 200, 20 research questions, 50 concepts, 50 synonyms, 50 list items, 25 seeds, 20 languages). Nothing is shortened silently. | `{errors, limits}` as `parse_draft` sends it |
| `DRAFT_INVALID` ✓ `refusals.py:100` | 422 | `parse_draft` refuses a mapped value for a reason other than size and the engine cannot set it aside | `{errors}` |
| `IMPORT_SOURCE_CHANGED` ✗ | 409 | the creating call's source no longer has `expect_fingerprint` (the workspace's protocol was replaced between the report and the click) | `{expected, found}` |
| `WORKSPACE_PATH_REFUSED` ✓ `catalog.py:209` | 422 | the slug leaves the workspaces folder | none |
| guard codes | 403, 401 | `ACTION_ORIGIN_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `TOKEN_SCOPE_REFUSED` | as 01 |

The rule: a value that parses and fits is carried; a value that parses but is over a draft limit (more than 25 seeds, more than 20 languages, a 2 001-character criterion) is refused as `DRAFT_TOO_LARGE`, never cut; a value the draft has no field for, or one the draft's own validator would refuse (a seed that is not a DOI, `steps.py:180-183`), is listed in `lost` and not refused.

### `POST /api/v1/inception/drafts/{id}/origin/checked` (✗ M10b)
Request `{ "step": "scope" | "direction" | "shape" | "criteria" | "review" }`. Answers `200 {session_id, origin}` (`origin` is `null` when the draft was not imported; idempotent). Refusals: `DRAFT_ID_INVALID` 422, `DRAFT_NOT_FOUND` 404, `DRAFT_UNREADABLE` 500 (all ✓, `drafts.py:52-79`), `STEP_UNKNOWN` ✓ 404 for any other step name. On an emitted draft it changes nothing and answers 200.

## What maps to what (the mapping table)
Built by reading `Draft` (`steps.py:149-178`), `_survey` (`:226`), `build_intent` (`:335`), `make_intent` (`intent.py:304`) and the two source shapes (`models.py`, `scholar_protocol/intent.py`). "Exact" means the text or value written into the compiled protocol is the source's. "Lossy" says what is lost. The UAV column is checked against `workspaces/uav-crop-weed-v03/protocol.json` and `intent.json` as read.

| Draft field (`Draft`) | From `protocol.json` | From `intent.json` | Class | What is lost, or why it cannot come across |
| :-- | :-- | :-- | :-- | :-- |
| `title` | `metadata.title` | `title` | exact | |
| `lead_researcher` | `metadata.lead_researcher` | `lead_researcher` | exact | |
| `venue` | `metadata.target_venue_type` | `target_venue_type` | exact | |
| `timeline_weeks` | `metadata.timeline_weeks` (int) | `timeline_weeks` | exact | The model's default 4 (`models.py:417`) is imported as 4 when the field is absent. A value that is not a whole number is listed in `lost`. |
| `paradigm` | `epistemology.primary_paradigm` | `primary_paradigm` | exact | `null` in an intent: left empty, in `needs_you`. The enum has the same four values as `PARADIGM_PROFILE` (`models.py:46-58`, `intent.py:64`). |
| `secondary_paradigm` | `epistemology.secondary_paradigm` | `secondary_paradigm` | exact | |
| `playbook` | `playbook_type` | `playbook_type` | exact | Five values, same as `ALL_PLAYBOOKS`. |
| `unit_of_analysis` | `epistemology.unit_of_analysis` | `unit_of_analysis` | exact | |
| `languages` | `search_strategy.languages` | `languages` | exact | `null` in an intent: the draft default `["en"]`. |
| `start_year`, `end_year` | `search_strategy.date_range.{start_year,end_year}` | `start_year`, `end_year` | exact | |
| `rqs` (texts) | `research_questions[].text`, in order | same | exact | Ids are regenerated `RQ1..` from the order, so a source that numbered them differently is renumbered. |
| `concepts[].concept`, `.synonyms` | `search_strategy.core_concepts[]` | `core_concepts[]` | exact | |
| `extra_inclusions` | `screening_criteria.inclusion[].criterion`, in order | `inclusion_criteria[].criterion` | exact | All of them, as "typed by you" (`manual`, `intent.py:247`): accepted unless dropped. Their ids (`INC-01`..) are regenerated from the order. See the proof rule below. |
| `extra_exclusions[].criterion` and `.reason_category` | `screening_criteria.exclusion[]` | `exclusion_criteria[]` | exact | UAV: `WRONG_PLATFORM`, `WRONG_TASK`, `WRONG_REPORT_TYPE`, `OUTSIDE_DATE_LANGUAGE` carry over. |
| `golden_seeds` | `search_strategy.golden_seeds` | `golden_seeds` | exact | |
| `verification_checks` | `verification.minimum_trust_score_threshold` | `minimum_trust_score_threshold` | lossy | Draft keeps only on or off: a threshold above 0 becomes on and is compiled as 6.0 (`VERIFICATION_TRUST_THRESHOLD`, `intent.py:61`); 0 becomes off. Any other number (for example 4.5) is lost. UAV: 0.0 gives off, which compiles back to 0.0. |
| `rqs` (facet, synthesis, evidence) | `research_questions[].target_facet`, `.synthesis_type`, `.required_evidence_type` | same | lossy | The draft keeps only text. `_survey` (`steps.py:244`) gives every RQ the lens's facet and evidence and the synthesis "Comparative Matrix". UAV: `reliability_evaluation`, "Descriptive evidence map and narrative comparison" and "Primary empirical study or dataset/benchmark report with source-linked methods" become the Pragmatist profile's values. |
| exclusion `reason_category` that is `null` | `screening_criteria.exclusion[].reason_category` | same | lossy | A missing category becomes `OUT_OF_SCOPE` (`ExclusionIn` default, `steps.py:129`; `make_intent`, `intent.py:321`). The import lists each one. |
| concept `boolean_operator` | `core_concepts[].boolean_operator` | same | lossy | `ConceptIn` has no operator and `make_intent` writes `OR` (`intent.py:362`). An `AND` is listed. UAV: all `OR`. |
| criterion `maps_to_rqs` | `screening_criteria.*[].maps_to_rqs` | same | lossy | `make_intent` maps every criterion to every RQ (`intent.py:316`). A criterion that mapped to a subset is listed with its subset. UAV: all four, so nothing changes. |
| `matrix_columns` (default columns) | `matrix_dimensions[].name` where it equals a default's name | same | exact | Only for a column whose `name` is one of `_default_matrix_dimensions(playbook, unit)` (`genesis.py:373`); `build_intent` keeps only those (`steps.py:353-355`). |
| matrix columns that are the researcher's own | `matrix_dimensions[{id, name, description, data_type, required, fallback_value, target_section_category}]` | same | not recoverable today | `Draft` has no field for them, and `build_intent` drops a name that is not a default silently. UAV: 13 dimensions (`study_reports` .. `open_science`) and none is a default, so all 13 would go. They come across only with the "researcher's own matrix columns" field M10b adds to `05-criteria`; this spec then carries the whole dimension. Until that field is built they are listed as not carried, by name. |
| `topic` | not stored | not stored | not recoverable | No protocol or intent field holds the question the researcher first wrote (`make_intent` never reads `Survey.topic`, `intent.py:304-384`). `topic` is required (`build_intent`, `steps.py:337`; Continue on 01). In `needs_you`. |
| `proof` | not stored, with one exception | not stored, with the same exception | not recoverable | The wizard turned the proof answer into the first inclusion criterion "Reports the gold-standard proof — {proof}" (`intent.py:294`) and into the rationale sentence "Convincing evidence is {proof}" (`:331`). Exception, exact: if the first inclusion criterion starts with that prefix, the rest is the proof, and that criterion is not also imported as an extra inclusion (it would duplicate). Otherwise (UAV) `proof` is in `needs_you`, and see the proof rule below. `proof` is required today (`steps.py:337`); M10b makes it optional for a draft that already holds a typed or imported inclusion (decided 2026-11-15), so an imported draft with inclusions does not list it in `needs_you`. |
| `out_of_scope` | not stored as such | not stored as such | not recoverable (kept as exclusions) | The wizard turned each out-of-scope answer into an exclusion with `OUT_OF_SCOPE`, indistinguishable in the file from a typed one. They are imported as `extra_exclusions` with the same text and category, so the criteria are unchanged; only the provenance label ("your out-of-scope answer") becomes "typed by you". `out_of_scope` stays empty. |
| wizard default exclusion | an exclusion equal to the lens's `negative_exclusions` text | same | exact, no longer "wizard-written" | Imported as an `extra_exclusion`, so it counts as typed. Because the draft now has an exclusion, the lens default is not proposed again (`intent.py:298`). |
| `criteria_decisions` | none | none | not applicable | An import writes none. Typed criteria are accepted by default. A wizard-written proof inclusion exists only if the researcher later types a proof answer; it then waits for them (see the proof rule). |

Fields the compiled protocol has that the draft cannot hold. They are listed in `lost`, and a new compile fills them from the playbook preset or from constants, so they can differ from the source:
| Source field | What the new protocol gets |
| :-- | :-- |
| `epistemology.epistemological_rationale` | regenerated each compile from lens, playbook, unit, proof and the accepted out-of-scope items (`intent.py:328-333`); the original text is lost. UAV: the hand-written rationale is lost, and the new one says "Explicitly out of scope: none specified" because `out_of_scope` is empty. |
| `epistemology.trustworthiness_framework` | the playbook's framework (`TRUSTWORTHINESS_FRAMEWORK`, `intent.py:52`); a custom text is lost. UAV: the custom "Transparent scoping evidence map ..." sentence is lost, "JBI Scoping Review Framework" is written. |
| `epistemology.incompatible_concepts` | `[]` |
| `search_strategy.target_candidate_pool_size` | not carried into the draft's planned number of records (`pool_min`, `pool_max`, the field `04-shape` adds in M10b): a protocol does not say whether its range was chosen or is a playbook preset, so the import leaves the field empty and Shape offers the button "Use the earlier range ({min} to {max})", which fills it only when pressed. Left empty, the new protocol gets the playbook preset as today. |
| `search_strategy.target_databases`, `open_access_preferred` | the playbook preset (`make_intent` sends `None`, `intent.py:365, :369-371`). UAV: pool `{min: 0, max: 1000}` becomes the SCOPING_REVIEW preset's 200 to 1000 (`presets.py:92-93`); the database list is the preset's (the lists were not compared). |
| `screening_criteria.two_tier_screening`, `verification.*_required` flags | `True` (`intent.py:374, :376-378`). UAV: all true, no change. |
| `method` (dedup, blinding, retrieval cap, reporting) | the compile fills it with defaults for a new workspace (`genesis.py:165-172`). A source `method` block is lost. UAV: none present. |
| `protocol_id`, `created_at`, `project_slug`, `$schema` | new: id and time from the genesis moment, slug from the title (`slugify`), `$schema` current. |
| grounding: the direction, the pool, per-term anchoring (`audit/recon_context.json` of the source workspace) | not read. The new draft has no `grounding`, so 06 says "No direction recorded" and the Direction step is open. Recon evidence belongs to a recon session in the cache and a direction chosen against a pool; it is not a protocol field. |
| screening decisions, corpus, matrix charting of the source | never read. The import reads one file. |

**Is the original draft kept anywhere after genesis?** Not in the workspace. The draft stays at `<workspaces root>/.drafts/<session id>/draft.json`, with `emitted` set (`mark_emitted`, `drafts.py:112-116`); genesis does not move, copy or delete it (`emit.py` has no draft reference: a search for "draft" in it finds none), and the browser cannot delete it (no `DELETE`, `browser.py:117-122`). The workspace itself holds the compiled result: `intent.json`, `protocol.json`, `SCREENING_CRITERIA.md`, the GENESIS journal row, and `audit/recon_context.json` for a grounded draft (`genesis.py:335-362`). So the typed answers behind a generated criterion (the proof, which items were out-of-scope answers, the topic) exist only in the draft file beside the root, and not at all for a workspace made from the terminal wizard or an older version, or for one copied to another root. That is why the import can recover a proof only from the criterion prefix, and why `topic` is always lost. (Confirmed by reading `emit.py`, `drafts.py`, `steps.genesis`; I did not run a genesis to look at the folder.)

### The proof rule (a consequence of the table)
Today `draft_criteria` always writes a wizard criterion "Reports the gold-standard proof — {proof}" first (`intent.py:294`), source `proof`, which is *generated*, so it is `undecided` until the researcher accepts or drops it (`criteria_with_decisions`, `steps.py:285-299`) and `CRITERIA_UNDECIDED` blocks Create; and `proof` is required (`steps.py:305, :337`). For an imported draft the researcher's own inclusions are already in `extra_inclusions`, so that rule would make them type a sentence and then drop the criterion written from it.

**Decided 2026-11-15 (✗ M10b, engine; the rule is specified in `04-shape` "The proof answer may be empty (M10b)" and holds for every draft, imported or not):** `proof` may be empty when the draft holds at least one inclusion the researcher typed or imported and has not dropped. With an empty proof the wizard writes no proof criterion, offers no template research question, and leaves the "Convincing evidence is …" sentence out of the rationale. The import therefore asks for `proof` only when the source has no inclusion criterion at all. If the researcher does type a proof, the criteria step shows the wizard's inclusion waiting for them, as today. The import never sets `criteria_decisions` for it: the id is content-derived from the proof text (`intent.py:265-270`), and writing a decision for them would decide a wizard-written criterion on their behalf.

## How imported values arrive
**Recommended design (works for the fields above, with the gaps above).** Imported values prefill the new draft directly as the researcher's own earlier text. Criteria count as typed, so they are accepted unless dropped, exactly as `criteria_with_decisions` already treats `manual` criteria. Nothing is a proposal card: the researcher did not receive a suggestion, they brought their own text. Four rules make it honest:
1. **One banner on every draft screen**, under the stepper: "Started from {label}, protocol dated {date}. These are your earlier answers; nothing in that review was changed." with a disclosure "What was not carried ({n})" listing `lost` and `needs_you` in plain words. It cannot be dismissed (it is one line).
2. **A mark per step**: "Imported, not yet checked", in the `unclear` role as text with an icon, on the stepper item and at the top of the step. It clears when the researcher visits the step (the page loads for that draft and the step's heading is shown; the page calls `origin/checked`). Steps with imported values: Scope (years, languages), Direction (recall seeds), Shape (lens, secondary lens, playbook, unit, research questions), Concepts and criteria (concepts, criteria, verification, columns), Review (title, lead, venue, weeks). Explore carries nothing and has no mark.
3. **Anything unmappable is listed, not dropped silently**: on the report before creating, in the banner's disclosure afterwards, and on the step where the researcher would supply it (a line "This protocol does not store {topic}. Write it here.").
4. **Review still decides.** A step not yet opened shows as a `note` in the Review checks ("Not opened since the import: Shape, Criteria"); it never disables Create. The engine's refusals (`DRAFT_INCOMPLETE`, `CRITERIA_UNDECIDED`) remain the only blockers.

**Why the stated design holds, and where it needs help.** It works because `Draft` is already the researcher's typed text and every imported field is a typed-answer field (`extra_inclusions`, `extra_exclusions`, `rqs`, `concepts`). It does not by itself fill four things: `topic` (required, not in any protocol) and `proof` (not in any protocol; optional once the draft has an inclusion), the matrix columns (carried whole by the own-columns field of `05-criteria`, built in the same milestone), and the per-RQ facets and the rationale (the draft has no field). Those are listed rather than guessed. **A fallback via proposals** (`01-proposals.md`) is needed only if the researcher wants imported values to be *suggested* instead of *entered*, for example to avoid overwriting an existing draft's fields: the same mapping would be emitted as proposals with `source: "import:<label>"`, `op: "replace"`, `target` the draft field, `base` the empty value, and decided one by one. That costs one click per value (for the UAV protocol at least 4 questions, 7 criteria and 3 concepts, before any synonym) and is the wrong default for a person who is bringing their own work. Recommended: the direct prefill here, and proposals only for the later case of importing *into* a draft that already has answers (not in M10b).

## States
- **Default** (nothing chosen yet): eyebrow "Start from an existing review"; h1 "Which review are you starting from?"; lede "Its questions, criteria and concepts arrive as your own earlier text, for you to check. Nothing in that review is changed." Two source cards: **A workspace on this computer** (a list of the engine's workspaces: title, folder, last event; one radio per row) and **A protocol file** (a 44 px "Choose a file" button for `protocol.json` or `intent.json`, with the file's name once chosen). A card **Text, a PROSPERO record or a draft protocol document** says "Reading text needs the assistant, which is not built yet. Start a new review and write your question, or use a protocol file." and has no input. A secondary "Back to your drafts". No brand button yet.
- **Report** (a source was read with `dry_run: true`): the source line ("{label} · protocol dated {date} · read as {protocol|intent}"); three groups, each a list in plain words with the field names the researcher knows: **Comes across as you wrote it** (counts and a few examples: "4 research questions, 7 criteria, 3 concepts, years 2020 to 2026, language en"), **Comes across with a change** (each `lossy` line: for example "Each question's evidence type is replaced by the lens's default" and "Matrix columns: 13 not carried"), **You write it** (`needs_you`: "your question"; "the proof" only when the source has no inclusion criterion). If `collides_with_source`, a note: "The title of this review would create the folder {slug}, which is the review you started from. You can change the title on the last step." One brand button: "Create the draft from this review". Secondary: "Choose a different source".
- **Empty**: no workspace with a protocol under the root (`items` empty): the workspace card says "No workspace with a protocol is under {root}. Choose a protocol file instead." with the file button; not an error, no code.
- **Loading** (skeleton): the workspace list shows three row skeletons while `GET /workspaces` runs; after a pick or file choice the report area shows a skeleton and "Reading the protocol" (`aria-busy`); the source cards stay usable. Creating: the brand button reads "Creating the draft", disabled, `aria-live="polite"`; no optimistic navigation.
- **Error** (typed refusal, `StateCard`, texts below; the code under Details):
  - `IMPORT_SOURCE_NOT_FOUND`, `IMPORT_SOURCE_UNREADABLE`, `IMPORT_SOURCE_TOO_LARGE`, `IMPORT_NOT_A_PROTOCOL`, `IMPORT_PROTOCOL_VERSION_UNSUPPORTED`, `PROTOCOL_INVALID`, `DRAFT_TOO_LARGE`, `DRAFT_INVALID`: the card sits above the source cards, the chosen source is cleared, one next step each (choose another source). `DRAFT_TOO_LARGE` lists each item and its limit from `details` (`rqs[3] (over 2000 characters)`).
  - `IMPORT_SOURCE_CHANGED` (on create): the card says the protocol changed since it was read; the action "Read it again" re-runs the dry run and shows the new report.
  - `WORKSPACE_PATH_REFUSED`: the existing copy; the workspace list is reloaded.
  - Guard codes (`ACTION_ORIGIN_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `TOKEN_SCOPE_REFUSED`) and `ENGINE_UNREACHABLE`: the shared cards (08).
  - A file the browser cannot read (`FileReader` error): the client-side message `import.file.unreadable`, no engine code.
- **Partial**: a protocol that carries some fields and not others (an intent with `null` paradigm, an old protocol with no `method`): the report shows what it has and `needs_you` grows ("a lens"). The draft is created and the researcher fills the rest on the steps; this is the normal case, not an error.
- **Offline**: the engine is local; offline is "engine unreachable". The workspace list and any report stay with "As of {time}", and "Create the draft from this review" is disabled with "needs the engine on this computer". A create in flight when the engine drops is not retried: the screen reloads the draft list (08) and, if a new draft with `origin.source` equal to this source appeared, offers to open it; otherwise shows `ENGINE_UNREACHABLE`.
- **Stale / protocol changed**: three cases. (1) The source protocol changes between the report and the click: `IMPORT_SOURCE_CHANGED`. (2) The source is replaced *after* the draft exists: the draft is a copy and is unaffected; the banner keeps the original fingerprint and date. (3) A protocol from an unsupported version: `IMPORT_PROTOCOL_VERSION_UNSUPPORTED`; nothing is guessed from a layout the engine does not know.

## Desktop layout
Reduced from 08's start screen: the step header pattern of 01, `StateCard`, a radio list, and the existing `Button` (`apps/research-ui/components/ui/base`). Regions in order: shell; "Back to your drafts"; eyebrow, h1, lede; the two source cards side by side (workspace list; file), the text card full width beneath; the report card (after a read) with its three groups; the button row at the end (Choose a different source, then the brand button). The banner and step marks this flow leaves behind are new, composed from existing tokens: the banner is `surface` with a 1px `rule` border and `ink` text (the dashed border is reserved for machine drafts and the gate); the mark is `unclear` text with an icon.

## Mobile layout (<= 640 px)
Desktop-only on the engine (no route is in `_PHONE_ROUTES`; a phone token gets `TOKEN_SCOPE_REFUSED`), so a real phone shows `inception.common.phone.desktopOnly` and a 44 px link "Go to screening". A narrow desktop window gets one column: the two source cards stacked (workspace rows are 44 px; the file button full width), the report groups as three disclosures with counts, the button row stacked and full width (brand button first), all targets at least 44 px. The banner on later steps wraps to two lines with the disclosure below it.

## Keyboard
Focus order: skip link, shell, "Back to your drafts", h1, the workspace radio group (arrow keys move, `Space` selects; a selection reads the report), "Choose a file" (`Enter` or `Space` opens the system picker), the report's three groups (each a button with `aria-expanded`), "Choose a different source", "Create the draft from this review". After a read, focus moves to the report heading; after a refusal, to the card heading; after the create, to the h1 of Scope. `Escape` in the report returns focus to the source cards without clearing the source. No single-key shortcuts. On later steps the mark is not a tab stop; the banner's disclosure button is.

## Copy
Keys in `apps/research-ui/lib/inception-copy.ts`, flat like the existing `start.*` keys (en master; fr and ar by the implementer). No literal `aria-label`, `title`, `alt` or `placeholder` (N9 guard). Refusal cards are `STATES` entries in `lib/screening-states.ts` (as 08, "As built").

Screen (`import.*`):
- `import.open` "Start from an existing review"; `import.eyebrow` "Start from an existing review"; `import.title` "Which review are you starting from?"; `import.lede` "Its questions, criteria and concepts arrive as your own earlier text, for you to check. Nothing in that review is changed."
- `import.workspace.title` "A workspace on this computer"; `import.workspace.row` "{title} · {slug}"; `import.workspace.last` "Last activity {date}"; `import.workspace.empty` "No workspace with a protocol is under {root}. Choose a protocol file instead."
- `import.file.title` "A protocol file"; `import.file.help` "Choose protocol.json or intent.json. The file is read on this computer and not changed."; `import.file.choose` "Choose a file"; `import.file.chosen` "File: {name}"; `import.file.unreadable` "This browser could not read that file."
- `import.text.title` "Text, a PROSPERO record or a draft protocol document"; `import.text.note` "Reading text needs the assistant, which is not built yet. Start a new review and write your question, or use a protocol file."
- `import.reading` "Reading the protocol"; `import.source` "{label} · protocol dated {date} · read as {shape}"; `import.shape.protocol` "protocol"; `import.shape.intent` "intent".
- `import.report.exact` "Comes across as you wrote it"; `import.report.lossy` "Comes across with a change"; `import.report.needs` "You write it"; `import.report.counts` "{rqs} research questions, {criteria} criteria, {concepts} concepts, years {start} to {end}, {languages}"; `import.report.noYear` "no limit"; `import.report.collides` "The title of this review would create the folder {slug}, which is the review you started from. You can change the title on the last step."
- Loss lines: `import.lost.facets` "Each question's evidence type and synthesis type are replaced by the lens's defaults."; `import.lost.matrix` "Matrix columns: {n} not carried."; `import.lost.operator` "Concept {concept} joined its words with {operator}. The new protocol uses OR."; `import.lost.maps` "Criterion {id} applied to {rqs} only. The new protocol applies every criterion to every question."; `import.lost.category` "Exclusion {id} had no reason category. It is now OUT_OF_SCOPE."; `import.lost.threshold` "The verification threshold {n} becomes the standard 6.0."; `import.lost.rationale` "The rationale and the framework sentence are written again from your answers."; `import.lost.preset` "Databases and the candidate pool size come from the review type's defaults."; `import.lost.method` "The method settings in that protocol are not carried."; `import.lost.seeds` "{n} recall seeds are not DOIs and are not carried."; `import.lost.grounding` "The direction and the first-search evidence of that review are not carried. Step 3 is open."
- Needs you: `import.needs.topic` "your question (a protocol does not store it)"; `import.needs.proof` "what would count as convincing evidence (a protocol does not store it)"; `import.needs.paradigm` "a lens"; `import.needs.unit` "the unit of analysis".
- Buttons: `import.create` "Create the draft from this review"; `import.creating` "Creating the draft"; `import.change` "Choose a different source"; `import.back` "Back to your drafts".
- Banner and marks (shared, `inception.common.imported.*`): `banner` "Started from {label}, protocol dated {date}. These are your earlier answers; nothing in that review was changed."; `banner.more` "What was not carried ({n})"; `mark` "Imported, not yet checked"; `mark.step` "Imported from {label}. Read each answer before you rely on it."; `needs.line` "This protocol does not store {field}. Write it here."; `review.note` "Not opened since the import: {steps}".
- Refusals (title / body / affects / action), en:
  - `IMPORT_SOURCE_NOT_FOUND`: "That protocol is not there" / "The workspace folder or its protocol.json is not on this computer any more." / "Starting from it" / "Choose another source"
  - `IMPORT_SOURCE_UNREADABLE`: "That file cannot be read" / "It is not text in UTF-8, or not JSON, or not a JSON object. Details says which." / "Starting from it" / "Choose another file"
  - `IMPORT_SOURCE_TOO_LARGE`: "That file is too large for a protocol" / "A protocol file is a few kilobytes. This one is over 1 MB." / "Starting from it" / "Choose another file"
  - `IMPORT_NOT_A_PROTOCOL`: "That is not a protocol" / "It is JSON, but it has no research questions, criteria and search strategy. Details lists what is missing." / "Starting from it" / "Choose protocol.json or intent.json"
  - `IMPORT_PROTOCOL_VERSION_UNSUPPORTED`: "This protocol is from a version this app does not read" / "It says {found}. This app reads {supported}. Nothing was guessed." / "Starting from it" / "Choose another source"
  - `PROTOCOL_INVALID`: "This protocol does not pass the protocol check" / "It looks like a protocol, but a field has the wrong type or value. Details lists them." / "Starting from it" / "Choose another source"
  - `DRAFT_TOO_LARGE` (08's entry, extended): the import uses the existing copy and lists the items from `details`.
  - `IMPORT_SOURCE_CHANGED`: "That protocol changed while you were looking" / "Its fingerprint is not the one the report showed. No draft was created." / "Creating the draft" / "Read it again"

## Accessibility
- Contrast pairs from `tokens.json`: `ink` on `surface`; `unclear` role text on `surface` for the mark, always with an icon and the words "Imported, not yet checked", never colour alone; `blocked` is text colour only in refusal cards.
- The workspace list is a `radiogroup` with a visible group label; each row's accessible name is "{title}, folder {slug}". The file button's chosen name is announced through `aria-live="polite"`. The report groups are headed regions; counts are words.
- The stepper's per-step mark is text inside the item ("Imported, not yet checked") and part of its accessible name ("3 Direction, imported, not yet checked"); clearing it announces nothing (it is not an event the researcher asked for), and the banner count is updated silently.
- Refusals use `role="alert"`; creating announces "Creating the draft" with `aria-busy`.
- **RTL (ar):** layout, the stepper and the radio list mirror; the source folder, the file name, the protocol id, the fingerprint, DOIs and reason codes (`WRONG_PLATFORM`) are `dir="ltr"` inside a `<bdi>`; dates and numbers use Latin digits; imported texts (titles, questions, criteria, concepts) are `dir="auto"` because a protocol may be in any language. A source in a different direction from the interface never changes the interface's direction.
- Contrast and 44 px targets hold in light and dark.

## Screens touched at build (not edited by this spec)
Listed so each owner amends their own spec; this spec edits none of them.
- 08 start screen: the secondary button "Start from an existing review", the one-line caption, and a row line "Started from {label}" from `listing().origin.label`.
- 01, 03, 04, 05, 06 (steps Scope, Direction, Shape, Concepts and criteria, Review): the banner under the stepper, the step mark, the `needs.line` where a required field was not carried, and the call to `origin/checked` on load. The Direction step (03) and the `Draft` of 02 and 03 are not otherwise changed by this spec.
- 05: the own-matrix-columns field this spec depends on (written by the 05 amendment of M10b).
- 06: the `note` check "Not opened since the import" (catalogued in `docs/ux/shared/final/02-checks.md` when that spec exists), and the GENESIS description.

## Acceptance tests
Vitest `apps/research-ui/tests/inception-import.test.tsx` (fixtures are test files; a copy of the UAV protocol is a test fixture, not shipped data):
- the default state lists the workspaces from `GET /workspaces`, offers the file button, shows the text card without an input, and has no brand button; the empty state shows the file-only sentence;
- choosing a workspace sends `POST /drafts/import` with `{source: {kind: "workspace", slug}, dry_run: true}` and no other call; choosing a file sends `{kind: "file", file_name, content_base64}` of the file's exact bytes; neither writes a draft;
- the report renders the three groups from `carried`, `lost` and `needs_you`, every `lost` entry as a plain sentence and none dropped, and "Create the draft from this review" is the only brand button; `collides_with_source` shows the folder note;
- Create sends `dry_run: false` with `expect_fingerprint` from the report, disables itself while pending, and navigates to Scope with the new id and `?console=`;
- each refusal code in the table maps to copy and shows its code under Details; `DRAFT_TOO_LARGE` lists the items; `IMPORT_SOURCE_CHANGED` offers "Read it again" and re-runs the dry run; an unknown code renders as itself;
- the banner shows on Scope, Direction, Shape, Concepts and criteria, and Review for a draft with `origin`, and on none for a draft without; each step shows its mark until its page has loaded once and the `origin/checked` call has succeeded, then not; Explore shows none; the Review note lists unopened steps and never disables Create;
- the `needs.line` shows on Scope for `topic` and on Shape for `proof` when `needs_you` has them; a source with inclusions does not put `proof` in `needs_you`, and Shape's Continue is enabled without it;
- offline disables Create; i18n keys exist in en, fr, ar and the N9 guard holds; `inception.live-only` (no Demonstration marker).

**Rebuild the UAV draft** (vitest `inception-import.uav.test.tsx` against a stateful fake of the engine API that implements the real mapping rules from this spec, so it proves the UI, and Python below proves the engine): import the fixture copy of `workspaces/uav-crop-weed-v03/protocol.json`; write the two answers the report names (`topic`, `proof`) and drop the one wizard-written proof criterion; open Review; assert the compiled preview's `intent.research_questions[].text` equal the source's four texts in order, `intent.inclusion_criteria[].criterion` equal the source's three, `intent.exclusion_criteria[]` equal the source's four texts with `WRONG_PLATFORM`, `WRONG_TASK`, `WRONG_REPORT_TYPE`, `OUTSIDE_DATE_LANGUAGE` in order, `core_concepts` equal the three concepts with their synonyms, years 2020 to 2026, languages `["en"]`; and assert the report named exactly the expected differences (13 matrix columns not carried, four facets replaced, rationale, framework, pool minimum).

Python `tests/console/test_inception_import.py` (engine; the UAV folder is copied to `tmp_path` first and the real one is never opened for writing):
- `test_import_rebuilds_uav_draft`: `POST /drafts/import` on the copy; create; set `topic` only (no proof: the source has inclusions, and no wizard proof criterion appears in `steps/criteria`); `POST /preview`; assert the same equalities as above on `preview["protocol"]` (`research_questions[].text`, `screening_criteria.inclusion[].criterion`, `exclusion[].criterion` and `.reason_category`, `search_strategy.core_concepts`, `date_range`, `languages`), and that `report.lost` equals the expected set; the fingerprint is not compared (it differs by design);
- `test_import_never_touches_source`: hashes and modification times of every file in the source folder are equal before and after a dry run and a create;
- `test_import_wizard_protocol_recovers_proof`: a protocol made by genesis from a draft with a proof reads back the proof exactly and does not also import its inclusion criterion;
- `test_import_intent_file`: `intent.json` of the UAV copy reads as `read: "intent"` with the same draft as the protocol;
- one test per refusal: not found, unreadable (not base64, not UTF-8, not JSON, a JSON array), too large (1 MiB + 1 byte), not a protocol, version unsupported (`$schema` changed), invalid (an RQ with no `text`), `DRAFT_TOO_LARGE` (a criterion of 2 001 characters; `details.limits` equals `DRAFT_LIMITS`), `IMPORT_SOURCE_CHANGED`, `WORKSPACE_PATH_REFUSED` (`../x`);
- `test_import_lossy_lines`: `AND` operator, a criterion mapped to a subset, a null reason category, threshold 4.5, a non-DOI seed each produce their `lost` entry;
- `test_origin_checked_keeps_updated_at`: marking a step leaves `updated_at` unchanged, a later `PUT` with the old `base_updated_at` succeeds, and the mark is idempotent; `test_save_keeps_origin` (a `PUT /drafts/{id}` keeps `origin`);
- `test_genesis_names_origin`: the GENESIS journal row of a workspace made from an imported draft names the source label and fingerprint;
- `tests/console/test_console_refusals.py` is extended with the new codes, and the browser allowlist test with the two new paths.

Playwright `apps/research-ui/tests-browser/inception.spec.ts` (this screen's part, stateful fake): from 08 open the import screen; choose a workspace, read the report, create, land on Scope with the banner and the mark; open Scope and see its mark clear, Shape still marked; the report for a file with a null paradigm lists "a lens"; each of two refusals (`IMPORT_NOT_A_PROTOCOL`, `IMPORT_PROTOCOL_VERSION_UNSUPPORTED`) shows its card and keeps the source cards usable; keyboard-only completion; RTL (ar) pass with the folder and fingerprint LTR; axe in light and dark; no horizontal overflow at 375 and 1440 px; a phone-scoped token shows the desktop pointer card and no form.

## Open questions
None.

Closed by the researcher on 2026-11-15 (record: `docs/roadmap/milestones/M10b-proposals-checks.md`, R3 and R4 and "Adopted from the writers' recommendations"):
1. `proof` is never prefilled from a derived value. It becomes optional when the draft already holds a typed or imported inclusion (an engine change in M10b, for every draft), so an imported review with inclusions needs neither the sentence nor the Drop.
2. `topic` stays empty; Scope shows "This protocol does not store your question. Write it here." with the secondary button "Use research question 1", which copies the text only when pressed.
3. The own-columns field stores the whole dimension, so the thirteen UAV columns come across. The import and the own-columns field are built together; an import built without it would list the columns as not carried.
4. A mark clears when the researcher visits the step. The Review note "Not opened since the import" (`REVIEW_IMPORT_STEP_NOT_OPENED` in `02-checks`' catalogue) and the banner's "What was not carried" stay.
5. Per-question facet, synthesis type, evidence type and the rationale are not carried in M10b; the report and the banner say so. Whether the draft gains fields for them is decided with M10c.
6. The planned number of records is not carried silently; Shape offers "Use the earlier range" (R3).
