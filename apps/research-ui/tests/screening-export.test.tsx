import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EXPORT_COPY, ScreeningExport } from "@/components/screening-export";
import { HOME_COPY, ScreeningHome } from "@/components/screening-home";
import { SUPPORTED_LOCALES } from "@/i18n";
import { stateCopy } from "@/lib/screening-states";

/**
 * Export and methods (spec 10) in jsdom. The engine is stubbed at `fetch`
 * with the shapes of `GET /ui/publication-status`, `GET /screening/methods`,
 * `GET /screening/export` and `GET /prisma/preview`; the screen builds no file
 * and no paragraph of its own.
 */

const FIXTURES = `${resolve(process.cwd(), "../../tests/fixtures/screening_api")}/`;
const PREVIEW = JSON.parse(readFileSync(`${FIXTURES}prisma_preview.json`, "utf-8")).response.body;
const body = (name: string) => JSON.parse(readFileSync(`${FIXTURES}${name}.json`, "utf-8")).response.body;

const PARAGRAPH =
  "30 records were identified; 0 duplicates were removed; 30 records were screened; 20 were excluded (EX-01: 20); 4 were unclear and went to full-text assessment; 6 were included. One reviewer screened every record. No AI model proposed decisions for this screening.";

const METHODS = {
  generation_id: "GEN-0123456789abcdef0123",
  generation_fingerprint: "sha256:feedface",
  published_at: "2026-11-05T10:00:00Z",
  language: "en",
  paragraph: PARAGRAPH,
  figures: { identified: 30, duplicates_removed: 0, screened: 30, excluded: 20, unclear: 4, included: 6, exclusion_reasons: { "EX-01": 20 } },
  sources: [{ name: "prisma_report.json", path: "literature/prisma_report.json", digest: "sha256:abc" }],
  caveats: [],
  not_stated: ["Queue order: not recorded for this screening."],
};

function status(value: string, extra: Record<string, unknown> = {}) {
  return { shape: "ui07.publication-status-v1", status: value, code: null, generation_id: "GEN-0123456789abcdef0123", outputs: {}, message: "", details: {}, ...extra };
}

const json = (b: unknown, code = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(b), { status: code, headers: { "content-type": "application/json", ...headers } });

function engine(routes: Record<string, unknown | (() => Response)> = {}) {
  const all: Record<string, unknown | (() => Response)> = {
    "/api/v1/ui/publication-status": status("CURRENT"),
    "/api/v1/screening/methods": METHODS,
    "/api/v1/screening/prisma/preview": { ...PREVIEW, included: 6, unclear_to_full_text: 4, excluded: { ...PREVIEW.excluded, total: 20 } },
    "/api/v1/screening/export": () =>
      new Response("TY  - JOUR\r\nER  - \r\n", { status: 200, headers: { "content-disposition": 'attachment; filename="golden-screening-GEN-included,unclear.ris"' } }),
    ...routes,
  };
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const parsed = new URL(url, "http://localhost");
      calls.push(`${parsed.pathname}${parsed.search}`);
      const answer = all[parsed.pathname.replace("/api/console", "")];
      if (typeof answer === "function") return (answer as () => Response)();
      if (answer instanceof Response) return answer;
      return answer === undefined ? json({ detail: { code: "NOT_FOUND", message: parsed.pathname } }, 404) : json(answer);
    }),
  );
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("export.states", () => {
  it("shows the published counts, the draft paragraph and the default RIS sets", async () => {
    engine();
    render(<ScreeningExport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Take your screening with you." });
    expect(screen.getByText("Published · current")).toBeInTheDocument();
    expect(screen.getByText("Draft · check before you submit")).toBeInTheDocument();
    expect(screen.getByText(PARAGRAPH)).toBeInTheDocument();
    const counts = screen.getByRole("table", { name: "PRISMA counts of the published screening" });
    expect(within(counts).getByRole("row", { name: "Records identified 30" })).toBeInTheDocument();
    expect(within(counts).getByRole("row", { name: "Unclear, to full text 4" })).toBeInTheDocument();
    expect(screen.getByText("Queue order: not recorded for this screening.")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /RIS/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Included/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Unclear/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Excluded/ })).not.toBeChecked();
    expect(document.querySelector("[data-differs]")).toBeNull();
  });

  it("states that nothing is published yet, and links to Publish, when the status is not CURRENT", async () => {
    const calls = engine({ "/api/v1/ui/publication-status": status("LEGACY_UNVERIFIED") });
    render(<ScreeningExport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Nothing is published yet" });
    expect(screen.getByRole("link", { name: "Go to Publish" })).toHaveAttribute("href", "/en/screening/publish");
    expect(screen.queryByRole("button", { name: "Download" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Copy paragraph" })).toBeNull();
    expect(calls.some((c) => c.startsWith("/api/console/api/v1/screening/methods"))).toBe(false);
  });

  it("refuses a stale publication with its code and a way to Publish, and offers no old generation", async () => {
    engine({ "/api/v1/ui/publication-status": status("STALE", { code: "GENERATION_STALE" }) });
    render(<ScreeningExport locale="en" />);
    await screen.findByRole("heading", { level: 1, name: "Changed since publication" });
    expect(screen.getByText("GENERATION_STALE")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Publish" })).toBeInTheDocument();
    expect(screen.queryByText(PARAGRAPH)).toBeNull();
  });

  it("names the missing file when the engine cannot write the paragraph", async () => {
    engine({
      "/api/v1/screening/methods": () =>
        json({ detail: { code: "METHODS_SOURCE_MISSING", message: "prisma_report.json is missing", details: { missing: "prisma_report.json" } } }, 409),
    });
    render(<ScreeningExport locale="en" />);
    await screen.findByText("METHODS_SOURCE_MISSING");
    expect(screen.getByText("prisma_report.json")).toBeInTheDocument();
  });

  it("says when the current decisions differ from the published ones", async () => {
    engine({ "/api/v1/screening/prisma/preview": { ...PREVIEW, included: 7, unclear_to_full_text: 4, excluded: { ...PREVIEW.excluded, total: 19 } } });
    render(<ScreeningExport locale="en" />);
    expect(await screen.findByText(/Your current decisions differ from the published ones/)).toBeInTheDocument();
  });

  it("has a card for every export refusal code, in every locale", () => {
    for (const code of ["EXPORT_NOT_PUBLISHED", "GENERATION_STALE", "GENERATION_SUPERSEDED", "EXPORT_FORMAT_INVALID", "EXPORT_SOURCE_MISMATCH", "METHODS_SOURCE_MISSING"]) {
      for (const locale of SUPPORTED_LOCALES) expect(stateCopy(locale, code).known, `${code}/${locale}`).toBe(true);
    }
  });
});

describe("methods.language", () => {
  it("keeps the engine's English paragraph in lang=en dir=ltr on an Arabic page", async () => {
    engine();
    render(<ScreeningExport locale="ar" />);
    const paragraph = await screen.findByText(PARAGRAPH);
    expect(paragraph).toHaveAttribute("lang", "en");
    expect(paragraph).toHaveAttribute("dir", "ltr");
    expect(screen.getByRole("button", { name: EXPORT_COPY.ar["methods.copy"] })).toBeInTheDocument();
  });
});

describe("methods.copy", () => {
  it("copies the paragraph verbatim with the button and with c, and announces it", async () => {
    engine();
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    render(<ScreeningExport locale="en" />);
    const paragraph = await screen.findByText(PARAGRAPH);
    fireEvent.click(screen.getByRole("button", { name: "Copy paragraph" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(PARAGRAPH));
    await waitFor(() => expect(document.querySelector("[data-announce]")).toHaveTextContent("Copied"));

    writeText.mockClear();
    fireEvent.keyDown(paragraph, { key: "c" });
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(PARAGRAPH));
  });
});

describe("export.download", () => {
  it("asks the engine for the chosen format and sets, and saves the file under the engine's name", async () => {
    const calls = engine();
    const createObjectURL = vi.fn(() => "blob:x");
    const revokeObjectURL = vi.fn();
    Object.assign(URL, { createObjectURL, revokeObjectURL });
    const clicks: string[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      clicks.push(this.download);
    });
    const user = userEvent.setup();
    render(<ScreeningExport locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Download" }));
    await waitFor(() => expect(clicks).toEqual(["golden-screening-GEN-included,unclear.ris"]));
    expect(calls).toContain("/api/console/api/v1/screening/export?format=ris&set=included%2Cunclear");

    await user.click(screen.getByRole("radio", { name: /CSV/ }));
    expect(screen.getByRole("checkbox", { name: /Excluded/ })).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Download" }));
    await waitFor(() => expect(calls).toContain("/api/console/api/v1/screening/export?format=csv&set=included%2Cunclear%2Cexcluded"));
    expect(revokeObjectURL).toHaveBeenCalled();
  });

  it("disables Download when no set is chosen", async () => {
    engine();
    const user = userEvent.setup();
    render(<ScreeningExport locale="en" />);
    await user.click(await screen.findByRole("checkbox", { name: /Included/ }));
    await user.click(screen.getByRole("checkbox", { name: /Unclear/ }));
    expect(screen.getByRole("button", { name: "Download" })).toBeDisabled();
    expect(screen.getByText("Choose at least one set of records.")).toBeInTheDocument();
  });

  it("shows the engine's refusal when the download is refused", async () => {
    engine({ "/api/v1/screening/export": () => json({ detail: { code: "GENERATION_STALE", message: "changed" } }, 409) });
    const user = userEvent.setup();
    render(<ScreeningExport locale="en" />);
    await user.click(await screen.findByRole("button", { name: "Download" }));
    expect(await screen.findByText("GENERATION_STALE")).toBeInTheDocument();
  });
});

describe("export.i18n", () => {
  it("has every key in every locale", () => {
    const keys = Object.keys(EXPORT_COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) expect(Object.keys(EXPORT_COPY[locale]).sort(), locale).toEqual(keys);
    for (const locale of SUPPORTED_LOCALES) expect(HOME_COPY[locale].exportLink.trim(), locale).not.toBe("");
  });

  it("writes no literal aria-label, title, alt or placeholder (N9)", () => {
    const source = readFileSync(resolve(process.cwd(), "components/screening-export.tsx"), "utf-8");
    expect(source).not.toMatch(/(aria-label|alt|placeholder)="[^"{]/);
    expect(source).not.toMatch(/\stitle="[^"{]/);
  });
});

describe("export.link", () => {
  const HOME = {
    "/api/v1/screening/summary": { ...body("summary_start"), agent_proposed: 0, lanes: { agent: 0, you: 0, second_screener: "PARKED" } },
    "/api/v1/screening/ui/batches": { shape: "ui07.screening-batches-v1", run_id: "RUN-1", count: 0, batches: [], missing: [] },
    "/api/v1/screening/decisions/conflicts": { items: [] },
    "/api/v1/screening/settings": body("settings_default"),
  };

  it("shows Export and methods on the screening home only while the publication is CURRENT", async () => {
    engine({ ...HOME, "/api/v1/ui/publication-status": status("CURRENT") });
    const { unmount } = render(<ScreeningHome locale="en" />);
    expect(await screen.findByRole("link", { name: "Export and methods" })).toHaveAttribute("href", "/en/screening/export");
    unmount();

    vi.unstubAllGlobals();
    engine({ ...HOME, "/api/v1/ui/publication-status": status("STALE", { code: "GENERATION_STALE" }) });
    render(<ScreeningHome locale="en" />);
    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByRole("link", { name: "Export and methods" })).toBeNull();
  });
});
