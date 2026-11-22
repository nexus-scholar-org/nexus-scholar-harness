import { fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { flush, installEngine, lastLookup, makeRow, makeTable, manifestRow, press, renderCharting } from "./charting-helpers";

/**
 * Spec 03 "Per-row failure and how the row reads afterwards" (M12a Part F): the
 * status badge does not change; one line says when it was looked up and what
 * came of it; "What was tried" opens an inline panel from the manifest: each
 * service and its answer, each address with its answer, the checks, PubMed
 * Central when it gave no PDF, and "This is not a paywall determination." The
 * words come from the outcome codes, never the kit's own text.
 */

afterEach(() => vi.unstubAllGlobals());

const desktop = () => document.querySelector("[data-desktop]") as HTMLElement;
const rowOf = (id: string) => desktop().querySelector(`[data-study-row="${id}"]`) as HTMLElement;
const panel = () => desktop().querySelector("[data-tried]") as HTMLElement | null;

function rowWith(i: number, last: Parameters<typeof lastLookup>[0]) {
  return makeRow(i, { fulltext: { ...makeRow(i).fulltext, last_lookup: lastLookup(last) } });
}

async function openTried(id: string) {
  fireEvent.click(within(rowOf(id)).getByRole("button", { name: "What was tried" }));
  await flush();
}

describe("charting.fetch-tried", () => {
  it("a row with no open copy stays To get, with one line and the panel of what was tried", async () => {
    const engine = installEngine(makeTable([rowWith(1, { outcome: "NO_OPEN_COPY_LISTED" })]), { fetch: { manifest: { "STU-001": [manifestRow()] } } });
    await renderCharting();
    expect(rowOf("STU-001").querySelector("[data-badge^=status]")).toHaveTextContent("To get");
    expect(rowOf("STU-001").querySelector("[data-last-lookup]")!.textContent).toMatch(/^Looked up 2026-11-2\d: no open copy listed$/);
    const button = within(rowOf("STU-001")).getByRole("button", { name: "What was tried" });
    expect(button).toHaveAttribute("aria-expanded", "false");
    await openTried("STU-001");
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(engine.calls.some((c) => c.method === "GET" && c.path === "/api/v1/charting/records/STU-001/fetch")).toBe(true);
    expect(panel()!.textContent).toMatch(/Looked up 2026-11-2\d \d\d:\d\d/);
    expect(within(panel()!).getByText("FR-000000000000000000000001")).toHaveAttribute("dir", "ltr");
    expect([...panel()!.querySelectorAll("[data-tried-services] li")].map((li) => li.textContent)).toEqual([
      "Unpaywall: no open copy listed",
      "OpenAlex: not asked (SCHOLAR_OPENALEX_KEY is not set)",
    ]);
    expect(panel()!.querySelector("[data-tried-not-paywall]")).toHaveTextContent("This is not a paywall determination.");
    // The kit's own words are never the screen's.
    expect(panel()!.textContent).not.toMatch(/OpenAlex was not asked \(/);
    await press("Escape");
    expect(panel()).toBeNull();
  });

  it("a failed download: each address and its answer, the checks, PubMed Central, from the manifest's codes", async () => {
    const pmc = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/pdf/a.pdf";
    const epmc = "https://europepmc.org/articles/PMC1/pdf/a.pdf";
    installEngine(
      makeTable([rowWith(1, { outcome: "PDF_NOT_FETCHED", message: "The listed address gave no PDF: not a PDF (no %PDF- header in the first 1024 bytes)" })]),
      {
        fetch: {
          manifest: {
            "STU-001": [
              manifestRow({
                outcome: "PDF_NOT_FETCHED",
                address: epmc,
                version: "publishedVersion",
                version_label: "publishedVersion",
                license: "cc-by",
                provider: "unpaywall",
                checks: { pdf_header: "fail", pdf_trailer: "pass", size_floor: "pass" },
                requests: [
                  { url: pmc, host: "www.ncbi.nlm.nih.gov", http_status: 403, error: "HTTP 403", redirects: [] },
                  { url: epmc, host: "europepmc.org", http_status: 200, error: "not a PDF (no %PDF- header in the first 1024 bytes)", redirects: ["https://europepmc.org/a", "https://europepmc.org/b"] },
                ],
              }),
            ],
          },
        },
      },
    );
    await renderCharting();
    expect(rowOf("STU-001").querySelector("[data-last-lookup]")!.textContent).toMatch(/: the file failed the checks: not a PDF \(an HTML page, for example\)$/);
    await openTried("STU-001");
    expect([...panel()!.querySelectorAll("[data-tried-addresses] li")].map((li) => li.textContent)).toEqual([
      "www.ncbi.nlm.nih.gov · HTTP 403: the host refused",
      "europepmc.org · Published version · Licence: cc-by · the file failed the checks: not a PDF (an HTML page, for example) · redirected 2 times",
    ]);
    expect(within(panel()!.querySelector("[data-tried-addresses]") as HTMLElement).getByText("www.ncbi.nlm.nih.gov")).toHaveAttribute("dir", "ltr");
    expect(panel()!.querySelector("[data-tried-checks]")).toHaveTextContent("Checks: not a PDF (an HTML page, for example)");
    expect(panel()!.querySelector("[data-tried-pmc]")).toHaveTextContent("PubMed Central did not give its PDF to this app.");
    expect([...panel()!.querySelectorAll("[data-tried-services] li")].map((li) => li.textContent)[0]).toBe("Unpaywall: open copy listed");
    expect(panel()!.textContent).not.toMatch(/no %PDF- header/);
  });

  it("the other outcomes, in words", async () => {
    installEngine(
      makeTable([
        rowWith(1, { outcome: "OPEN_NO_DIRECT_PDF" }),
        rowWith(2, { outcome: "LOOKUP_FAILED", try_later: true }),
        rowWith(3, { outcome: "SKIPPED_NO_ID" }),
        rowWith(4, { outcome: "FAILED" }),
        rowWith(5, { outcome: "ACQUIRED", same_as_discarded: true }),
      ]),
    );
    await renderCharting();
    const said = (i: number) => rowOf(`STU-00${i}`).querySelector("[data-last-lookup]")!.firstChild!.textContent!.replace(/^Looked up [0-9-]+: /, "");
    expect([1, 2, 3, 4, 5].map(said)).toEqual([
      "open access, but no direct PDF address",
      "the lookup failed, try later",
      "skipped: no DOI or arXiv id",
      "the download failed",
      "the same file as the one you discarded",
    ]);
    // "Try later" has its hint.
    expect(rowOf("STU-002").querySelector("[data-hint-button='charting.fetch.tip.tryLater']")).not.toBeNull();
  });

  it("arXiv's answer names its version; a lookup that failed names its status", async () => {
    installEngine(makeTable([rowWith(1, { outcome: "ACQUIRED" })]), {
      fetch: {
        manifest: {
          "STU-001": [
            manifestRow({
              outcome: "LOOKUP_FAILED",
              provider: "arxiv",
              arxiv_version: "v2",
              lookups: [
                { service: "arxiv", state: "ANSWERED", http_status: 200, error: null },
                { service: "unpaywall", state: "FAILED", http_status: 503, error: "Unpaywall failed (HTTP 503)" },
              ],
            }),
          ],
        },
      },
    });
    await renderCharting();
    await openTried("STU-001");
    expect([...panel()!.querySelectorAll("[data-tried-services] li")].map((li) => li.textContent)).toEqual(["arXiv: v2 found", "Unpaywall: failed (HTTP 503)"]);
  });

  it("nothing asked yet: the panel says so", async () => {
    installEngine(makeTable([rowWith(1, { outcome: "NO_OPEN_COPY_LISTED" })]));
    await renderCharting();
    await openTried("STU-001");
    expect(panel()!.querySelector("[data-tried-nothing]")).toHaveTextContent("Nothing was asked for this record yet.");
  });

  it("a row never looked up has no line and no panel", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    expect(rowOf("STU-001").querySelector("[data-last-lookup]")).toBeNull();
    expect(within(rowOf("STU-001")).queryByRole("button", { name: "What was tried" })).toBeNull();
  });
});
