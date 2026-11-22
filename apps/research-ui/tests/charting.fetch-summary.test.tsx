import { act, fireEvent, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POLL_MS } from "@/components/charting-fetch";

import { flush, installEngine, lastLookup, makeRow, makeTable, press, renderCharting, runView, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "End summary" (M12a Part F): `role="status"`, every count with its
 * number, the errors by class in words, "OpenAlex was not asked", "Show the n
 * to confirm" (the filter), "Select the n to try later" (selects, and starts
 * nothing), "Dismiss"; shown again on a reload as "Last look-up".
 */

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const summary = () => desktop().querySelector("[data-fetch-summary]") as HTMLElement | null;
const rowOf = (id: string) => desktop().querySelector(`[data-study-row="${id}"]`) as HTMLElement;

const finished = runView({
  run_id: "FR-000000000000000000000001",
  state: "finished",
  total: 214,
  reached: 214,
  found: 120,
  downloaded: 96,
  failed_checks: 4,
  errors: { "HTTP 403": 3, "HTTP 404": 2, "timed out": 1, "HTTP 503": 1, "lookup failed": 1, "too many redirects": 1, "network error (ClientConnectorCertificateError)": 1 },
  no_open_copy: 60,
  no_direct_pdf: 12,
  try_later: 8,
  skipped_no_id: 6,
  not_reached: 0,
  providers: ["unpaywall"],
  openalex_key_set: false,
  started_at: "2026-11-22T14:00:00Z",
  finished_at: "2026-11-22T14:32:00Z",
});

function tableWithTryLater() {
  return makeTable([
    waitingRow(1),
    waitingRow(2),
    makeRow(3, { fulltext: { ...makeRow(3).fulltext, last_lookup: lastLookup({ outcome: "LOOKUP_FAILED", try_later: true }) } }),
    makeRow(4, { fulltext: { ...makeRow(4).fulltext, last_lookup: lastLookup({ outcome: "PDF_NOT_FETCHED", try_later: true }) } }),
    makeRow(5, { fulltext: { ...makeRow(5).fulltext, last_lookup: lastLookup({ outcome: "NO_OPEN_COPY_LISTED" }) } }),
  ]);
}

describe("charting.fetch-summary", () => {
  it("on a reload: 'Last look-up', role status, every count, the errors in words and OpenAlex not asked", async () => {
    installEngine(tableWithTryLater(), { fetch: { runs: [finished] } });
    await renderCharting();
    const card = summary()!;
    expect(card).toHaveAttribute("role", "status");
    expect(within(card).getByRole("heading").textContent).toMatch(/^Last look-up, 2026-11-2\d \d\d:\d\d$/);
    const lines = [...card.querySelectorAll<HTMLElement>("[data-summary-line]")].map((l) => [l.dataset.summaryLine, l.firstChild?.textContent]);
    expect(lines).toEqual([
      ["asked", "214 records asked"],
      ["found", "Open copy found for 120"],
      ["downloaded", "96 downloaded, waiting for you"],
      ["failedChecks", "4 failed the file checks"],
      ["errors", "10 errors"],
      ["noPdf", "12 open access but no direct PDF address"],
      ["noCopy", "60 with no open copy listed"],
      ["skipped", "6 skipped: no DOI or arXiv id"],
      ["notReached", "0 not reached"],
      ["tryLater", "8 to try later"],
    ]);
    expect([...card.querySelectorAll("[data-summary-errors] li")].map((li) => li.textContent)).toEqual([
      "3 × the host refused (HTTP 403)",
      "2 × not found (HTTP 404)",
      "1 × the host did not answer in time",
      "1 × the host had an error (HTTP 503)",
      "1 × a lookup failed",
      "1 × too many redirects",
      "1 × the host's certificate was refused",
    ]);
    expect(card.querySelector("[data-summary-openalex]")).toHaveTextContent("OpenAlex was not asked.");
    // The try-later hint holds the sentence behind its button.
    expect(card.querySelector("[data-hint-body='charting.fetch.tip.tryLater']")).toHaveTextContent(
      "Try later means the service or the host asked the app to wait, or did not answer. It is not an answer about the paper.",
    );
  });

  it("names the failed checks in the spec's words and the failed look-ups by service and status", async () => {
    const named = runView({
      ...finished,
      failed_checks: 5,
      check_failures: { pdf_header: 2, size_floor: 1, size_limit: 1, pdf_trailer: 1, structure: 1 },
      errors: { "HTTP 403": 1, "lookup failed": 3 },
      lookup_failures: [
        { service: "unpaywall", http_status: 503, error_kind: null, n: 2 },
        { service: "openalex", http_status: null, error_kind: "ClientConnectorError", n: 1 },
        { service: "arxiv", http_status: null, error_kind: "TimeoutError", n: 1 },
      ],
    });
    installEngine(tableWithTryLater(), { fetch: { runs: [named] } });
    await renderCharting();
    const card = summary()!;
    expect([...card.querySelectorAll("[data-summary-checks] li")].map((li) => li.textContent)).toEqual([
      "2 × not a PDF (an HTML page, for example)",
      // The trailer and the structure share the words "the PDF structure is not valid".
      "2 × the PDF structure is not valid",
      "1 × too small to be a paper",
      "1 × over 100 MB",
    ]);
    expect([...card.querySelectorAll("[data-summary-errors] li")].map((li) => li.textContent)).toEqual([
      "1 × the host refused (HTTP 403)",
      "2 × the lookup failed: Unpaywall answered HTTP 503",
      "1 × the connection failed",
      "1 × the host did not answer in time",
    ]);
    expect(card.querySelector("[data-summary-line=errors]")!.firstChild!.textContent).toBe("4 errors");
  });

  it("says how many rows were left because the researcher changed them during the run (review round 2)", async () => {
    installEngine(tableWithTryLater(), { fetch: { runs: [runView({ ...finished, left_out: { changed_during_run: 2 } })] } });
    await renderCharting();
    expect(summary()!.querySelector("[data-summary-line=changed]")).toHaveTextContent("2 changed by you during the look-up and not asked");
  });

  it("an older run file with no names keeps the counts and the bare 'a lookup failed' line", async () => {
    const older = { ...finished };
    delete older.check_failures;
    delete older.lookup_failures;
    installEngine(tableWithTryLater(), { fetch: { runs: [older] } });
    await renderCharting();
    expect(summary()!.querySelector("[data-summary-checks]")).toBeNull();
    expect([...summary()!.querySelectorAll("[data-summary-errors] li")].map((li) => li.textContent)).toContain("1 × a lookup failed");
  });

  it("'Show the n to confirm' sets the filter", async () => {
    installEngine(tableWithTryLater(), { fetch: { runs: [finished] } });
    await renderCharting();
    fireEvent.click(within(summary()!).getByRole("button", { name: "Show the 2 to confirm" }));
    await flush();
    expect((within(desktop()).getByRole("combobox", { name: "Show" }) as HTMLSelectElement).value).toBe("toConfirm");
    expect([...desktop().querySelectorAll<HTMLElement>("[data-study-row]")].map((r) => r.dataset.studyRow)).toEqual(["STU-001", "STU-002"]);
  });

  it("'Select the n to try later' selects those rows and starts nothing; L then asks with their count", async () => {
    const engine = installEngine(tableWithTryLater(), { fetch: { runs: [finished] } });
    await renderCharting();
    fireEvent.click(within(summary()!).getByRole("button", { name: "Select the 2 to try later" }));
    await flush();
    expect(rowOf("STU-003")).toHaveAttribute("aria-selected", "true");
    expect(rowOf("STU-004")).toHaveAttribute("aria-selected", "true");
    expect(rowOf("STU-005")).toHaveAttribute("aria-selected", "false");
    expect(engine.calls.filter((c) => c.method === "POST")).toHaveLength(0);
    await press("l");
    expect(engine.calls.find((c) => c.path.startsWith("/api/v1/charting/fetch/plan"))!.path).toBe("/api/v1/charting/fetch/plan?ids=STU-003%2CSTU-004");
    expect(desktop().querySelector("[data-fetch-plan]")).toHaveTextContent("Look up open-access copies of 2 records?");
    expect(engine.fetch.starts).toHaveLength(0);
  });

  it("Dismiss hides it for this page load; a cancelled run says so with what was not reached", async () => {
    installEngine(makeTable([makeRow(1)]), { fetch: { runs: [finished] } });
    await renderCharting();
    fireEvent.click(within(summary()!).getByRole("button", { name: "Dismiss" }));
    await flush();
    expect(summary()).toBeNull();
  });

  it("a run watched to its end reads 'Look-up cancelled' with the records not reached", async () => {
    installEngine(makeTable([makeRow(1), makeRow(2)]), {
      fetch: { started: runView({ total: 2 }), afterStart: [runView({ state: "cancelled", total: 2, reached: 1, not_reached: 1, finished_at: "2026-11-22T14:40:00Z" })] },
    });
    await renderCharting();
    fireEvent.focus(rowOf("STU-001"));
    rowOf("STU-001").focus();
    await press("l");
    await press("Enter");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_MS);
    });
    await flush();
    expect(within(summary()!).getByRole("heading").textContent).toMatch(/^Look-up cancelled /);
    expect(summary()!.querySelector("[data-summary-line=notReached]")).toHaveTextContent("1 not reached");
  });
});
