import { within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { installEngine, makeRow, makeTable, renderCharting, waitingRow } from "./charting-helpers";

/**
 * Spec 03 "Fetched, to confirm (row)" and "Identity result" (M12a Part F): the
 * badge is words and an icon on a plain surface with a dashed muted border; the
 * row leaves the retrieved and to-get counts for "to confirm"; the File column
 * gives size, source and host, version, licence, the identity result in its four
 * forms, the duplicate warning, and Open, Confirm and Discard named with the title.
 */

afterEach(() => vi.unstubAllGlobals());

const rowOf = (id: string) => document.querySelector(`[data-desktop] [data-study-row="${id}"]`) as HTMLElement;

describe("charting.fetch-badge", () => {
  it("shows the badge in words and an icon, dashed and muted, and keeps the earlier status beneath it", async () => {
    installEngine(makeTable([waitingRow(1), makeRow(2)]));
    await renderCharting();
    const badge = rowOf("STU-001").querySelector("[data-badge=fetch-to-confirm]") as HTMLElement;
    expect(badge).toHaveTextContent("Fetched, to confirm");
    expect(badge.querySelector("svg[data-icon]")).not.toBeNull();
    expect(badge.className).toMatch(/\bborder-dashed\b/);
    expect(badge.className).toMatch(/\bborder-ink-muted\b/);
    expect(badge.className).toMatch(/\bbg-leaf\b/);
    expect(badge.className).not.toMatch(/include|brand/);
    expect(rowOf("STU-001").querySelector("[data-badge^=status]")).toHaveTextContent("To get");
    expect(rowOf("STU-002").querySelector("[data-badge=fetch-to-confirm]")).toBeNull();
  });

  it("counts a waiting row only in 'to confirm', never in retrieved or to get", async () => {
    installEngine(makeTable([waitingRow(1), waitingRow(2), makeRow(3)]));
    await renderCharting();
    expect(document.querySelector("[data-counts]")!.textContent).toBe(
      "3 kept · 0 retrieved · 0 not retrieved · 1 to get · 0 included at full text · 0 excluded · 0 charted · 2 to confirm",
    );
  });

  it("says nothing of 'to confirm' when no file waits", async () => {
    installEngine(makeTable([makeRow(1)]));
    await renderCharting();
    expect(document.querySelector("[data-counts]")!.textContent).not.toMatch(/to confirm/);
  });

  it("lists size, source and host (left to right), version, licence and the actions named with the title", async () => {
    installEngine(makeTable([waitingRow(1)]));
    await renderCharting();
    const file = rowOf("STU-001").querySelector("[data-pending-file]") as HTMLElement;
    expect(file.querySelector("[data-fetch-size]")).toHaveTextContent("1.2 MB");
    expect(file.querySelector("[data-fetch-source]")).toHaveTextContent("Found by Unpaywall · europepmc.org");
    expect(within(file.querySelector("[data-fetch-source]") as HTMLElement).getByText("europepmc.org")).toHaveAttribute("dir", "ltr");
    expect(file.querySelector("[data-fetch-version]")).toHaveTextContent("Published version");
    expect(file.querySelector("[data-fetch-licence]")).toHaveTextContent("Licence: cc-by");
    expect(within(file).getByRole("link", { name: "Open the file of Study number 1" })).toHaveAttribute("href", "/api/console/api/v1/charting/records/STU-001/fetched");
    expect(within(file).getByRole("link", { name: "Open the file of Study number 1" })).toHaveAttribute("target", "_blank");
    expect(within(file).getByRole("button", { name: "Confirm the file of Study number 1" })).toBeEnabled();
    expect(within(file).getByRole("button", { name: "Discard the file of Study number 1" })).toBeEnabled();
    // Attaching or pasting a link waits until the file is confirmed or discarded.
    expect(within(rowOf("STU-001")).queryByRole("button", { name: /Attach a PDF|Paste a link/ })).toBeNull();
  });

  it("names each version and a licence not given", async () => {
    const versions = [
      [{ version: "acceptedVersion", version_label: "acceptedVersion" }, "Accepted manuscript"],
      [{ version: "submittedVersion", version_label: "submittedVersion" }, "Submitted version (preprint)"],
      [{ version: "submittedVersion", version_label: "preprint (arXiv v2)", source: "arXiv", licence: "arXiv; licence not given" }, "Preprint (arXiv v2)"],
      [{ version: null, version_label: null }, "Version not given"],
    ] as const;
    installEngine(makeTable(versions.map(([over], i) => waitingRow(i + 1, { ...over }))));
    await renderCharting();
    versions.forEach(([, words], i) => {
      expect(rowOf(`STU-00${i + 1}`).querySelector("[data-fetch-version]")).toHaveTextContent(words);
    });
    expect(rowOf("STU-003").querySelector("[data-fetch-licence]")).toHaveTextContent("Licence not given");
    expect(rowOf("STU-003").querySelector("[data-fetch-source]")).toHaveTextContent("Found by arXiv · europepmc.org");
  });

  it("gives the identity result in four forms, words and an icon each", async () => {
    const forms = [
      ["doi found", "doi", "DOI found in the file"],
      ["title found", "title", "Title found in the file"],
      ["not found: check it", "notFound", "Not found in the file: check it"],
      ["not checked", "notChecked", "Not checked: open it"],
    ] as const;
    installEngine(makeTable(forms.map(([identity], i) => waitingRow(i + 1, { identity }))));
    await renderCharting();
    forms.forEach(([, kind, words], i) => {
      const line = rowOf(`STU-00${i + 1}`).querySelector("[data-identity]") as HTMLElement;
      expect(line).toHaveAttribute("data-identity", kind);
      expect(line).toHaveTextContent(words);
      expect(line.querySelector("svg[data-icon]")).not.toBeNull();
    });
    // "Not found" is the unclear role: text and icon on its soft tint.
    const unclear = rowOf("STU-003").querySelector("[data-identity] [data-role=unclear]") as HTMLElement;
    expect(unclear.className).toMatch(/bg-unclear-soft/);
    // The identity and version hints sit behind the hint button.
    expect(rowOf("STU-001").querySelector("[data-hint-button='charting.fetch.tip.identity']")).not.toBeNull();
    expect(rowOf("STU-001").querySelector("[data-hint-button='charting.fetch.tip.version']")).not.toBeNull();
  });

  it("warns on both rows when the same file waits for another record, naming its title", async () => {
    installEngine(makeTable([waitingRow(1, { duplicate_of: ["STU-002"] }), waitingRow(2, { duplicate_of: ["STU-001"] })]));
    await renderCharting();
    expect(rowOf("STU-001").querySelector("[data-fetch-duplicate]")).toHaveTextContent("The same file is waiting for another record: Study number 2");
    expect(rowOf("STU-002").querySelector("[data-fetch-duplicate]")).toHaveTextContent("The same file is waiting for another record: Study number 1");
  });
});
