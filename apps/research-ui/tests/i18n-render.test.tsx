import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import LocaleNotFoundBoundary, { LocaleNotFound } from "@/app/[locale]/not-found";
import { EvidenceChain } from "@/components/evidence-chain";
import { LocaleDocument } from "@/components/locale-document";
import { OverviewPage } from "@/components/overview-page";
import { demoEvidence, demoProject } from "@/lib/mock-project";
import {
  DEFAULT_LOCALE,
  LOCALE_METADATA,
  SUPPORTED_LOCALES,
  formatNumber,
  resolveLocale,
  translate,
  type Locale,
} from "@/i18n";
import { CATALOGS } from "@/messages";

/**
 * `LocaleSwitcher` reads the current path with `usePathname()`, a client hook
 * with no meaning outside a running app router. The mock reports the path of the
 * locale under test.
 */
let currentPath = "/en";

vi.mock("next/navigation", () => ({
  usePathname: () => currentPath,
}));

function renderDocument(locale: Locale) {
  currentPath = `/${locale}`;
  return render(
    <LocaleDocument locale={locale}>
      <OverviewPage locale={locale} />
    </LocaleDocument>,
  );
}

/**
 * The `<html>` element the render actually wrote to.
 *
 * React 19 does not render `<html>`/`<head>`/`<body>` inside a container: it
 * applies them to the real document, so `LocaleDocument`'s attributes land on
 * `document.documentElement` even in jsdom — which is the same element a Next
 * server render writes them on. That is measured, not assumed: this helper
 * asserts the attributes are present on the real document element and that they
 * name the locale under test.
 *
 * The attributes are global state that outlives `cleanup()`, so they are removed
 * again after each test. Leaking `lang="ar" dir="rtl"` into the next test in this
 * file would make its result depend on execution order.
 */
function renderedHtml(): Element {
  const html = document.documentElement;
  expect(html, "document.documentElement always exists").not.toBeNull();
  return html;
}

/**
 * The subtree the render actually produced — the scope content assertions in this
 * file use.
 *
 * `LocaleDocument` renders the `<html>`/`<body>` pair, and React 19 does not render
 * those tags inside a container: it applies their attributes to the **real**
 * document element and keeps the pair's children where they were rendered. So the
 * route is reachable both ways — the RTL `container` holds it, and so does
 * `document.body`, one level up — and the measured fact is the one above:
 * `document.documentElement` carries this locale's `lang`/`dir`.
 *
 * `document.body` is the scope used here because it is the scope axe and a browser
 * test use, so an assertion about "what this locale renders" is not quietly
 * narrower than the page. The two guard assertions are load-bearing, not
 * decoration: without them a regression that stopped rendering the page at all
 * would turn the fixture- and selector-isolation tests below into green lines that
 * check nothing.
 */
function renderedBody(): HTMLElement {
  const body = document.body;
  expect(body.querySelector("header"), "the route rendered into document.body").not.toBeNull();
  expect(body.querySelector("main"), "the route rendered into document.body").not.toBeNull();
  return body;
}

afterEach(() => {
  document.documentElement.removeAttribute("lang");
  document.documentElement.removeAttribute("dir");
});

/**
 * Every English chrome string the route renders, as one list of sentences that
 * belong to no message in this locale's catalog.
 *
 * The exclusions are the point of the test, so they are explicit rather than
 * clever:
 *
 * - Every `<bdi>` subtree is dropped. Those are the frozen fixture's own words
 *   (D-I18N-02), which are English in all three documents by design. The
 *   demonstration project is a review of an English-language corpus; pretending
 *   its record titles were translated would be the bug, not the fix.
 * - The brand and the three endonyms are allowed as literals: a proper name and a
 *   language's own name, neither of which is translatable.
 *
 * Everything else must come from a message in this locale's catalog. The
 * comparison is anchored per *sentence* on purpose: a rendered text node is often
 * only a fragment of one message, and a hole stands for a value this scan cannot
 * predict, so each catalog sentence becomes a pattern whose holes are wildcards.
 * A sentence matching no pattern is chrome that exists only in English.
 */
function englishChromeIn(locale: Locale): string[] {
  render(
    <LocaleDocument locale={locale}>
      <OverviewPage locale={locale} />
    </LocaleDocument>,
  );

  const copy = renderedBody().cloneNode(true) as HTMLElement;
  for (const isolated of copy.querySelectorAll("bdi")) {
    isolated.remove();
  }

  const allowedLiterals = new Set(
    [
      CATALOGS[locale]["brand.productName"],
      ...SUPPORTED_LOCALES.map((code) => LOCALE_METADATA[code].endonym),
    ].map((value) => value.trim().toLowerCase()),
  );

  // The catalog is indexed the same way the DOM is read: sentence by sentence,
  // with each hole as a wildcard that may match nothing. A rendered text node is
  // very often only a *fragment* of one message — the prefix of
  // `overview.lastEvent` before its hole, or the second sentence of
  // `shell.authorityStatement` once the splitter cuts at the period — so an
  // anchored per-sentence match is what "this text belongs to this locale's
  // catalog" has to mean. It fails for exactly the case that matters: chrome that
  // exists only in `en.ts`.
  // Each piece is trimmed and whitespace-normalised, and the boundary where a hole
  // was is re-inserted as a wildcard that absorbs the whitespace around it. The
  // wildcard has to absorb *whitespace too*: trimming the pieces would otherwise
  // leave a pattern that cannot match the value that filled the hole, because the
  // single space in front of it would have nowhere to come from.
  const messageSentences = Object.values(CATALOGS[locale]).flatMap((value) =>
    value
      .split(/(?<=[.!?])\s+/)
      .map((sentence) =>
        new RegExp(
          `^${sentence
            .split(/\{[a-zA-Z][a-zA-Z0-9_]*\}/)
            .map((piece) =>
              piece
                .trim()
                .toLowerCase()
                .replace(/\s+/g, " ")
                .replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
            )
            .join("\\s*[\\s\\S]*?\\s*")}$`,
        ),
      ),
  );

  const found: string[] = [];
  const walk = document.createTreeWalker(copy, NodeFilter.SHOW_TEXT);
  for (let node = walk.nextNode(); node; node = walk.nextNode()) {
    for (const raw of (node.textContent ?? "").split(/(?<=[.!?])\s+/)) {
      // Normalised the same way on both sides: lower-cased, whitespace collapsed to
      // single spaces and trimmed. Normalising whitespace keeps a re-wrapped
      // source line from reporting a leak, and it lets a piece that ended just
      // before a hole still match the value that filled it, since the wildcard
      // covers the separator space.
      const sentence = raw.trim().toLowerCase().replace(/\s+/g, " ");
      // Short fragments are punctuation, digits and single words; the catalog
      // comparison below is the real filter and a length floor only keeps
      // whitespace runs out of the report.
      if (sentence.length < 8 || allowedLiterals.has(sentence)) {
        continue;
      }
      if (messageSentences.some((pattern) => pattern.test(sentence))) {
        continue;
      }
      found.push(raw.trim());
    }
  }
  return found;
}

describe("document attributes", () => {
  it("declares the locale's own lang and dir on the html element", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      const html = renderedHtml();

      expect(html.getAttribute("lang"), locale).toBe(LOCALE_METADATA[locale].lang);
      expect(html.getAttribute("dir"), locale).toBe(LOCALE_METADATA[locale].dir);
      expect(html.getAttribute("lang"), locale).toBe(locale);
      unmount();
    }
  });

  it("sets dir=rtl for Arabic and ltr for the Latin scripts", () => {
    // Not "ar is right-to-left": the pair, so a future fourth locale has to be
    // declared explicitly rather than inheriting a default.
    const directions = SUPPORTED_LOCALES.map((locale) => LOCALE_METADATA[locale].dir);
    expect(directions).toEqual(["ltr", "ltr", "rtl"]);

    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      expect(renderedHtml().getAttribute("dir")).toBe(
        locale === "ar" ? "rtl" : "ltr",
      );
      unmount();
    }
  });

  it("renders the document from a resolved locale even when the segment was unsupported", () => {
    // D-I18N-13: the 404 page is still a real document with valid attributes.
    const requested = "de";
    expect(resolveLocale(requested)).toBe(DEFAULT_LOCALE);

    const { unmount } = renderDocument(resolveLocale(requested));
    const html = renderedHtml();
    expect(html.getAttribute("lang")).toBe(DEFAULT_LOCALE);
    expect(html.getAttribute("dir")).toBe("ltr");
    unmount();
  });

  it("keeps every locale's own chrome on screen", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      expect(screen.getByText(CATALOGS[locale]["overview.eyebrow"]), locale).toBeInTheDocument();
      expect(screen.getByText(CATALOGS[locale]["overview.workflowHeading"]), locale).toBeInTheDocument();
      expect(screen.getByText(CATALOGS[locale]["overview.traceHeading"]), locale).toBeInTheDocument();
      expect(screen.getByText(CATALOGS[locale]["overview.asideHeading"]), locale).toBeInTheDocument();
      expect(screen.getByText(CATALOGS[locale]["safety.demoDataLabel"]), locale).toBeInTheDocument();
      unmount();
    }
  });
});

describe("fixture isolation", () => {
  it("keeps every fixture string byte-identical inside a bdi element", () => {
    // D-I18N-02. The frozen demonstration record is not translated, and the
    // elements that hold it are the ones that keep an English string from being
    // reordered inside an Arabic sentence.
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      const scope = renderedBody();

      const expected = [
        demoProject.title,
        demoProject.researchQuestion,
        demoProject.lastEvent,
        ...demoProject.stages.flatMap((stage) => [stage.label, stage.description]),
        ...demoEvidence.flatMap((node) => [node.label, node.detail]),
      ];

      for (const text of expected) {
        const bdi = Array.from(scope.querySelectorAll("bdi")).find(
          (node) => node.textContent === text,
        );
        expect(bdi, `${locale}: ${text.slice(0, 40)}`).not.toBeUndefined();
      }

      // And nothing outside a `<bdi>` carries those strings.
      const outside = scope.cloneNode(true) as HTMLElement;
      for (const isolated of outside.querySelectorAll("bdi")) {
        isolated.remove();
      }
      expect(outside.textContent ?? "").not.toContain(demoProject.title);
      expect(outside.textContent ?? "").not.toContain(demoProject.researchQuestion);

      unmount();
    }
  });

  it("isolates the fixture value inside the translated ledger caption", () => {
    // The one message that mixes the two: a translated prefix and the record's own
    // last event. The `<bdi>` is inside the sentence, not a wrapper around it.
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      const caption = screen.getByText(
        (_content, element) =>
          element?.tagName === "P" &&
          (element.textContent ?? "").includes(demoProject.lastEvent) &&
          (element.textContent ?? "").includes(
            CATALOGS[locale]["overview.lastEvent"].split("{event}")[0]!.trim(),
          ),
      );
      expect(within(caption).getByText(demoProject.lastEvent).tagName).toBe("BDI");
      unmount();
    }
  });

  it("leaves the evidence ordinals as bare formatted text, not bdi", () => {
    // The ordinal is generated by `Intl`, not read out of the record, so it is
    // chrome in every locale: it follows the locale's digits, and it is not
    // isolated. `EvidenceChain` is rendered on its own here so "the ordinals of
    // the evidence trail" cannot be confused with the workflow list's.
    const { container, unmount } = render(<EvidenceChain locale="ar" nodes={demoEvidence} />);
    const items = container.querySelectorAll("li");

    expect(items).toHaveLength(demoEvidence.length);
    for (const [index, item] of Array.from(items).entries()) {
      const ordinal = item.firstElementChild;
      expect(ordinal, `item ${index + 1}`).not.toBeNull();
      expect(ordinal?.tagName, `item ${index + 1} is not an isolation wrapper`).not.toBe("BDI");
      expect(ordinal?.textContent).toBe(formatNumber("ar", index + 1));
      expect(ordinal?.textContent, "Arabic-Indic digits, not Latin").not.toBe(String(index + 1));
    }
    unmount();
  });
});

describe("untranslated-chrome scan", () => {
  it("renders no English-only sentence in the French document", () => {
    expect(englishChromeIn("fr")).toEqual([]);
  });

  it("renders no English-only sentence in the Arabic document", () => {
    expect(englishChromeIn("ar")).toEqual([]);
  });

  it("still detects a real English leak, so the scan is not vacuous", () => {
    // A control: the same scan over a document that genuinely contains an
    // English sentence must report it. Without this, a scan that always returned
    // `[]` would satisfy both assertions above.
    const scan = (html: string): string[] =>
      Array.from(html.matchAll(/>([^<>]{8,})</g)).map((match) => match[1]!.trim());

    const leaked = scan("<p>Latest: Protocol sealed</p>");
    expect(leaked).toContain("Latest: Protocol sealed");
  });
});

describe("locale switcher", () => {
  it("renders one link per shipped locale, each pointing at that locale's path", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      const selector = within(
        screen.getByRole("navigation", { name: CATALOGS[locale]["locale.selectorLabel"] }),
      );
      const links = selector.getAllByRole("link");

      expect(links.map((link) => link.getAttribute("href")), locale).toEqual(
        SUPPORTED_LOCALES.map((code) => `/${code}`),
      );
      expect(
        links.map((link) => link.textContent),
        locale,
      ).toEqual(SUPPORTED_LOCALES.map((code) => LOCALE_METADATA[code].endonym));
      unmount();
    }
  });

  it("marks the current locale and no other", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      const current = Array.from(document.querySelectorAll("[aria-current]")).filter(
        (node) =>
          node.getAttribute("aria-current") === "true" &&
          node.getAttribute("href") === `/${locale}`,
      );
      expect(current, locale).toHaveLength(1);
      unmount();
    }
  });

  it("gives each link the language it switches to", () => {
    renderDocument("en");
    const links = Array.from(document.querySelectorAll("[data-nav-region='locale'] a[href]"));

    expect(links.map((link) => link.getAttribute("lang"))).toEqual([...SUPPORTED_LOCALES]);
    expect(links.map((link) => link.getAttribute("hreflang"))).toEqual([...SUPPORTED_LOCALES]);
  });

  it("offers the selector in the Arabic document too, at every width", () => {
    // D-I18N-11: no breakpoint on the selector. jsdom cannot compute `display`,
    // so the structural claim is that the element carries no responsive class at
    // all; the rendered claim is `tests-browser/locale-switch.spec.ts`.
    const { unmount } = renderDocument("ar");
    const selector = renderedBody().querySelector("[data-nav-region='locale']");

    expect(selector).not.toBeNull();
    expect(selector?.className).not.toMatch(/(^|\s)(sm|md|lg|xl|2xl):/);
    unmount();
  });
});

describe("translated numerals", () => {
  it("formats counts in the locale's own digits", () => {
    // F01/F03. The Arabic-Indic digits are what a real Arabic reader expects,
    // and the assertion is written against the locale's own `Intl` output rather
    // than a literal, so it stays true if the tag ever changes to `ar-SA`.
    expect(formatNumber("en", 143)).toBe(new Intl.NumberFormat("en-US").format(143));
    expect(formatNumber("ar", 143)).toBe(new Intl.NumberFormat("ar-EG").format(143));

    renderDocument("ar");
    expect(screen.getByText(formatNumber("ar", 143))).toBeInTheDocument();
  });

  it("uses grouping off, so a count never wraps mid-number", () => {
    expect(formatNumber("en", 1234)).toBe("1234");
    expect(formatNumber("fr", 1234)).toBe("1234");
  });
});

describe("unsupported-locale 404", () => {
  /**
   * The boundary Next mounts for a refused segment, and the naming component the
   * packet amendment still has to decide where to mount. Both are exercised here
   * rather than only in the browser: the boundary's text is catalog text, and the
   * decision the packet owner owes is a *wiring* decision, not a copy decision.
   */
  it("tells the reader the address has no page, and links back, without claiming a segment", () => {
    render(<LocaleNotFoundBoundary />);

    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveTextContent(CATALOGS.en["notFound.heading"]);
    expect(document.body).toHaveTextContent(CATALOGS.en["notFound.body"]);
    expect(screen.getByRole("link")).toHaveTextContent(
      CATALOGS.en["notFound.backToDefault"],
    );

    // The sentence it drops is the one that names the refused segment, and the
    // boundary never observed that segment. Rendering it anyway would mean
    // inventing a value, so its absence is asserted rather than tolerated.
    expect(document.body.textContent).not.toContain(
      CATALOGS.en["notFound.unsupportedLocale"].replace("{requested}", "").slice(0, 12),
    );
  });

  it("renders in English even when the refused segment was an RTL one", () => {
    render(<LocaleNotFound requested="ar-EG" />);

    expect(document.body).toHaveTextContent(
      CATALOGS.en["notFound.unsupportedLocale"]
        .replace("{requested}", "ar-EG")
        .replace("{available}", "en, fr, ar"),
    );
    expect(document.body.textContent).not.toMatch(
      new RegExp(CATALOGS.ar["notFound.unsupportedLocale"].slice(0, 10)),
    );
  });

  it("refuses an empty segment instead of rendering a template with a hole in it", () => {
    // The reason the boundary above cannot pass `""`: an empty interpolation is
    // a missing message, and `translate` says so rather than emitting one.
    expect(() =>
      translate("en", "notFound.unsupportedLocale", {
        requested: "",
        available: "en, fr, ar",
      }),
    ).toThrow(/requested/i);

    // …and the boundary is therefore not permitted to render the key at all.
    render(<LocaleNotFoundBoundary />);
    expect(document.body.textContent ?? "").not.toMatch(
      /\{\s*(requested|available)\s*\}/,
    );
  });
});

describe("render hygiene", () => {
  it("leaves no element carrying an untranslated locale key as its text", () => {
    for (const locale of SUPPORTED_LOCALES) {
      const { unmount } = renderDocument(locale);
      const text = document.body.textContent ?? "";
      expect(text, locale).not.toMatch(/\b(overview|nav|state|evidenceKind|notFound|shell|a11y|app|locale|workflow)\.[a-zA-Z]/);
      unmount();
      cleanup();
    }
  });
});