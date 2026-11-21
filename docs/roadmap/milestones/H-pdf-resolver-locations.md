# H-pdf-resolver-locations The open-access resolver reads every listed location

Branch: `dev/h/pdf-resolver-locations` (from `origin/main` `46371f45`; `origin/main` `64fd8212` merged in at `e9d492c1`) · Lane: **RELEASE** (a production command's network behaviour changes) · Status: **IN REVIEW** · Started: 2026-11-21

A defect found by the live check after M12a K0 (PR 274). The researcher asked on 2026-11-21 for it to be fixed now, as a small PR of its own, ahead of M12a Part K. Choices the brief left open: `docs/decisions.md`, top entry (2026-11-21, H-pdf-resolver-locations). The researcher answered items 1 to 12 on 2026-11-21 in the main session, which passed the answers to this build: item 4 changed to "Always ask both services", item 3 "Three addresses", the other ten accepted as built, subject to the review. Item 13 follows from the changed item 4 and is PROPOSED.

## The defect

**Observed (2026-11-21, main session, with the researcher's approval).** `scholar-pdf download --doi 10.7717/peerj.4375`, a gold open-access PeerJ paper. The OpenAlex and the Unpaywall lookups both answered 200. The command reported "No legal open-access PDF URL was resolved from OpenAlex/Unpaywall", exit code 1, no file, no PDF request.

**Cause.** `AsyncPDFDownloader.process_doi` (`src/scholar_pdf/downloader.py`) read only `best_oa_location` and `primary_location`. In both answers that location is the publisher's, with a landing page and no PDF address. The direct addresses are in the full lists: OpenAlex `locations` has 12 entries, two with a `pdf_url` (PubMed Central, `publishedVersion`, cc-by; the Université de Montréal repository, `submittedVersion`, cc-by); Unpaywall `oa_locations` has 9, the same two with a `url_for_pdf` (Unpaywall has no `primary_location`). Second defect: a failed lookup was one `logger.debug` line, so "both services failed" and "no open copy listed" gave the same message.

The two answers of that check are the test fixtures `tests/kits/pdf/fixtures/openalex_peerj4375.json` and `unpaywall_peerj4375.json`, as received. They hold no e-mail address.

## What changed

- **`src/scholar_pdf/open_copies.py` (new, makes no request).** `open_copies(openalex, unpaywall)` reads every listed location: OpenAlex `best_oa_location`, `primary_location` and `locations`; Unpaywall `best_oa_location` and `oa_locations`. A location counts only if its provider marks it open (`is_oa: true` in an OpenAlex answer; listed in an Unpaywall answer and not saying `is_oa: false`) and it carries a direct PDF address (`pdf_url`, `url_for_pdf`) that is an `http` or `https` address. A landing page is never turned into an address and none is built. The copies are ranked across both lists: published version, accepted manuscript, submitted version or preprint, then a copy with no version label (M12a answer F3); within one version OpenAlex's before Unpaywall's; the same address is kept once.
- **Both services are asked for every DOI, once each** (decision item 4 as answered, "Always ask both services"). Before, and in this build's first version, Unpaywall was asked only when OpenAlex listed no address.
- **`process_doi`** tries the ranked copies in order, at most three (item 3), and stops at the first that gives a valid PDF. The result keeps the copy taken (`open_copy`: address, version, licence, host type, source name, provider), how many were listed and tried, and what each service answered (`lookups`).
- **A lookup keeps what happened** (`_lookup`): answered; not known (HTTP 404); or failed, with the HTTP status or the error's class name. The error's text is never kept, because it can hold the request address and so the contact e-mail.
- **Three outcomes when no address is found**, each with its own `outcome`, message and exit code: `LOOKUP_FAILED` (3), `OPEN_NO_DIRECT_PDF` (4), `NO_OPEN_COPY_LISTED` (5). `PDF_NOT_FETCHED` (an address was listed, none gave a PDF) keeps exit code 1. `status` keeps its three values (`ACQUIRED`, `UNRESOLVED`, `FAILED`).
- **`download`** shows the outcome in its table, names the copy taken on a success row, and exits with the code above. **`ingest`** prints one line when a metadata lookup failed; it still stores the file and exits 0.

**What the command sends now.**
- Lookups: two per DOI, always (OpenAlex once, Unpaywall once). Before the fix it was one when OpenAlex's "best" location carried an address and two otherwise. For 443 records that is 886 lookups. The e-mail rule and the user agent are unchanged; no key and no retry is added.
- PDF requests: one address at a time, at most three addresses per DOI (before: one address).
- `ingest` is unchanged: OpenAlex, then Unpaywall only when OpenAlex gave no answer.

**What item 4 does to item 7** (one lookup failed, the other lists something). Because both services are asked every time, one failing while the other lists a copy can now happen for any DOI. It never stops the download: the best copy the answering service lists is taken, and the failure stays on the result (`lookups`). If no address is listed by the service that answered, the outcome is the failed lookup (exit 3), as item 7 says. If an address was listed and gave no PDF, the outcome is `PDF_NOT_FETCHED` (exit 1) and the message names the service that failed, "so its list was not read" (item 13, PROPOSED).

**One behaviour that narrows.** A location that OpenAlex does not mark open is no longer requested even when it carries a `pdf_url`. Before, `best_oa_location` and `primary_location` were read without looking at `is_oa`. This is the location half of Part K item 7 (PDF-12), done here because the brief's rule requires it (decision item 5). Five older test mocks gained the `is_oa: true` field that real answers carry; none of their assertions changed.

## Definition of done

Each item names its test in `tests/kits/pdf/test_open_copy_resolver.py` (34 tests). Seen failing first: the 29 tests of the first commit on `origin/main`'s code (`7d299aaa`: junit 29 tests, 29 failures); the item 4 tests on the first version of the fix (`6cd34546`: junit 34 tests, 7 failures).

- [x] 1. With the two real answers, the resolver chooses the PubMed Central published-version address and records `publishedVersion`, `cc-by`, the repository host and the provider. `test_the_resolver_ranks_the_real_answers_pubmed_central_first`, `test_the_real_answers_download_the_pubmed_central_published_version`, `test_the_resolver_reads_unpaywalls_list_when_it_is_the_only_answer`, `test_unpaywalls_list_is_used_when_openalex_fails`.
- [x] 2. With only the submitted-version location carrying an address, it is taken and labelled. `test_only_a_submitted_version_with_an_address_is_taken_and_labelled`.
- [x] 3. A location that is not open, or has only a landing page, is never requested. `test_a_closed_location_or_a_landing_page_is_never_requested` (also: no `is_oa` field, an `ftp` address, Unpaywall's embargoed list), `test_the_real_answers_never_ask_a_landing_page_or_a_closed_location`.
- [x] 4. The ranking, with a stated order within a version. `test_copies_are_ranked_published_then_accepted_then_submitted_then_unlabelled`, `test_a_publishers_own_copy_is_labelled_as_the_publishers`.
- [x] 5. The first address failing leads to the second; at most three are tried. `test_the_first_address_failing_leads_to_the_second` (an HTML page), `test_a_refused_first_address_leads_to_the_second` (HTTP 403), `test_at_most_three_listed_addresses_are_tried`.
- [x] 6. A failed lookup, "open but no direct PDF" and "no open copy listed" each have their own message and outcome, including one lookup failing while the other answers. `test_both_lookups_failing_is_a_failed_lookup_not_a_missing_copy`, `test_one_lookup_failing_while_the_other_lists_nothing_is_a_failed_lookup`, `test_open_without_a_direct_address_says_so_and_names_the_landing_page`, `test_no_open_copy_listed_says_so`, `test_a_doi_the_services_do_not_know_is_an_answer_not_a_failure`, `test_the_three_outcomes_have_three_different_messages`, `test_an_answer_that_is_not_a_json_object_is_a_failed_lookup`, `test_a_lookup_failing_does_not_stop_a_copy_the_other_lists`, `test_a_failed_lookup_is_named_when_the_listed_addresses_give_no_pdf`.
- [x] 7. The command's words and exit code say which. `test_the_command_says_which_outcome_in_words_and_in_its_exit_code` (four outcomes), `test_the_commands_exit_code_for_several_dois_names_the_most_urgent_outcome`, `test_the_command_downloads_the_real_answers_offline_and_labels_the_copy`, `test_the_command_reports_a_failed_lookup_offline_with_exit_code_3`.
- [x] 8. No request goes to a host other than the two services and the chosen address; each service is asked once per DOI. Asserted on the fakes in items 1, 3 and 5, and `test_both_services_are_asked_once_for_every_doi` (the two request addresses, one each, with and without an address listed).
- [x] 9. Item 4 as answered: the best copy across both lists. `test_a_published_version_only_unpaywall_lists_is_taken_over_openalexs_submitted_one`, `test_an_address_only_unpaywall_lists_is_tried_after_openalexs_fail` (OpenAlex's two fail, Unpaywall's third is taken, the fourth is never asked).
- [x] 10. The contact address never reaches a message or a stored lookup. `test_a_failed_lookup_never_puts_the_contact_address_in_a_message`.
- [x] 11. `ingest` keeps a failed lookup on its result and says so. `test_ingest_keeps_a_failed_lookup_on_its_result`, `test_the_ingest_command_says_when_the_lookup_failed`.
- [x] 12. The words that describe `download` are true: `docs/nexus_scholar_user_guide.md`, `docs/kits_surface_matrix.md`, `.agents/skills/scholar-pdf-kit/SKILL.md` and its `references/resolution_and_download.md`, with the bundled copies under `.agents/plugins/nexus-scholar/skills/` kept identical; one line in `M12a-charting-table.md` (d3).
- [x] 13. No test uses the network: the lookups and the PDF hosts are in-memory fakes, and the suite's guard fails any real connection. No live request was sent while building this.

## Checked and reported, not changed (brief, point 4)

- **No lookup is made twice.** Each service is asked once per DOI. The first version of this fix kept the earlier order (Unpaywall only when OpenAlex listed no address), which wasted nothing; item 4 as answered adds the second lookup on purpose.
- **A PDF address that answers 403, 404 or 410 is still requested three times** (the retry rule on `download_pdf`; PDF-06, Part K item 6). With three addresses that is nine PDF requests for one DOI at worst, each after a wait of 2 to 10 seconds.
- **The lookup client retries 429 and 5xx** up to three times and may answer from its local cache (`scholar_search.http_client`), as before.
- **OpenAlex is still asked without its key** (Part K item 4): a spent keyless budget now reads "OpenAlex failed (HTTP 409)" or "(HTTP 429)", and the copy is taken from Unpaywall's list.
- **`access_status` is not repaired** (PDF-12, Part K item 7; decision item 12): it can still read `VERIFIED_OPEN_ACCESS` for a paper whose only `pdf_url` sits on a closed "best" or "primary" location, while `outcome` now reads `NO_OPEN_COPY_LISTED` for it. The one addition: a file that came from a location its provider marks open reads `VERIFIED_OPEN_ACCESS`.
- **`ingest` and `download --input <missing>` still exit 0 on failure** (PDF-15, Part K item 10).
- **`docs/kits/pdf/README.md` and `api_reference.md`** still describe the kit before K0 (Part K item 12); not touched.
- **`scholar_pdf/models.py`** (`OAResult.best_pdf_url`) already walks `oa_locations`, but nothing calls it and it would refuse real answers that lack a field; not used, left for Part K item 10 (PDF-05).
- **The parked gateway code** (a caller passing a gateway explicitly) now adds its rewritten address after each copy rather than after the single one; the commands still refuse a proxy.

## Evidence

| Stage | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| contract (before) | `46371f45` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" |
| red | `7d299aaa` (tests and fixtures only) | `uv run pytest tests/kits/pdf/test_open_copy_resolver.py --junitxml …` | junit: 29 tests, **29 failures**, 0 errors |
| green, kit | `ab0c3860` | `uv run pytest tests/kits/pdf tests/test_parked_labels.py -n 4 --junitxml …` | junit: 256 tests, 0 failures, 0 errors, 7 skipped (the Windows symlink tests) |
| merge of `origin/main` | `e9d492c1` (merges `64fd8212`, PR 276; only `docs/decisions.md` conflicted, both entries kept) | `git diff --name-only fba1d4a3 e9d492c1 -- src/scholar_pdf tests/kits/pdf` | empty: the merge changes no file of the PDF kit |
| red, item 4 | `6cd34546` (tests only) | `uv run pytest tests/kits/pdf/test_open_copy_resolver.py --junitxml …` | junit: 34 tests, **7 failures**, 0 errors |
| green, kit, item 4 | `c3616899` | `uv run pytest tests/kits/pdf tests/test_parked_labels.py -n 4 --junitxml …` | junit: 260 tests, 0 failures, 0 errors, 7 skipped |
| pr gate | `f42b6b00` (the final code commit `c3616899` plus documents) | `uv run pytest -q -n 4 -p no:cacheprovider --junitxml …` (full suite, 4 workers, from the build worktree) | junit: **6241 tests, 0 failures, 0 errors, 15 skipped** (623 s); exit code 0 |
| | `f42b6b00` | `uv run ruff check scripts/`; `uv run ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | "All checks passed!" twice |
| | `f42b6b00` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" |
| | `f42b6b00` | `git diff --name-only origin/main...HEAD -- apps/`; `git diff --check origin/main...HEAD` | empty (no UI file); clean |

No UI file changes, so typecheck, vitest, build and Playwright do not apply.

## Review rounds

REVIEW_ROUNDS

## Not verified

- **No live request was sent.** The PubMed Central address was not fetched. PubMed Central may answer a client that is not a browser with an HTML page or a refusal instead of the PDF; the code then tries the repository's submitted version and labels the file as that. Which copy a live run takes is therefore not known until the main session runs it.
- The live check is more than one request: one OpenAlex lookup, one Unpaywall lookup, then one PDF request per address tried, up to three attempts each if a host answers with an error status. For this DOI: 3 requests if PubMed Central gives the PDF, at most 8 if both hosts refuse.
- Only one paper's real answers are fixtures. Other shapes (a paper with only an accepted manuscript; an answer with a version label in other words; the two services listing different copies) are covered by hand-written payloads, not recorded ones.
- How often Unpaywall lists a better copy than OpenAlex was not measured; in the two recorded answers the lists agree.
- The 443-record run of Part F was not simulated; concurrency and pacing are unchanged from K0, with one more lookup per DOI.
- CI matrix (Linux, macOS, Python 3.11) not run; the gate ran on Windows, Python 3.12, only.

## The live check for the main session (after the merge; approved by the researcher on 2026-11-21 on condition of a clean gate and the reviewer's APPROVE)

```powershell
uv run scholar-pdf download --doi 10.7717/peerj.4375 --output "$env:TEMP\pdfres-live"
```

Expected: exit code 0, one `DOC-….pdf` in that folder, and a row that names the copy, either "publishedVersion, cc-by, PubMed Central, listed by OpenAlex" or, if PubMed Central does not give the PDF, "submittedVersion, cc-by, Papyrus : Institutional Repository (Université de Montréal), listed by OpenAlex; address 2 of 2 listed". If OpenAlex's keyless budget is spent the row is still a success, taken from Unpaywall's list ("listed by Unpaywall"). Exit code 3 means both lookups failed; 1 means both addresses refused.
